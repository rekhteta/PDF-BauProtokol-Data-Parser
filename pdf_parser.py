import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import datetime
import logging
import threading
import pandas as pd
import subprocess
import fitz  # PyMuPDF
import numpy as np
import re

# Setup Logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_parser_error.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class PDFParserLogic:
    """
    Business Logic for extracting data from PDF files.
    Routes to specific protocol extractors based on PDF text.
    """
    def __init__(self, target_folder, output_excel_path, progress_callback, finish_callback):
        self.target_folder = target_folder
        self.output_excel_path = output_excel_path
        self.progress_callback = progress_callback
        self.finish_callback = finish_callback

    def run(self):
        try:
            self._analyze()
        except Exception as e:
            logging.error("Fatal error during PDF analysis", exc_info=True)
            self.finish_callback(False, str(e), None)
            
    def _analyze(self):
        data = []
        
        self.progress_callback("Identifying PDF files...", 0, 0)
        
        pdf_files = []
        for root, dirs, files in os.walk(self.target_folder):
            for f in files:
                if f.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, f))
            
        total_items = len(pdf_files)
        if total_items == 0:
            self.finish_callback(False, "No PDF files found in the selected folder.", None)
            return

        processed_count = 0
        
        for file_path in pdf_files:
            file_name = os.path.basename(file_path)
            try:
                # Open PDF with PyMuPDF
                doc = fitz.open(file_path)
                if len(doc) == 0:
                    continue
                    
                page0_text = doc[0].get_text("text")
                
                # Routing Logic
                extraction_result = {}
                if "Hausanschlussprotokoll" in page0_text or "BBND ID" in page0_text:
                    extraction_result = self._extract_hausanschluss(doc, page0_text)
                    extraction_result["Protocol Type"] = "Hausanschlussprotokoll"
                elif "Einblas" in page0_text:
                    extraction_result = self._extract_einblas(doc, page0_text)
                    extraction_result["Protocol Type"] = "Einblas-Protokoll"
                else:
                    extraction_result["Protocol Type"] = "Unknown Format"
                    
                # Add metadata
                extraction_result["File Name"] = file_name
                extraction_result["Full Path"] = file_path
                
                data.append(extraction_result)
                doc.close()
                
            except Exception as e:
                logging.error(f"Error parsing PDF: {file_path}", exc_info=True)
                data.append({
                    "File Name": file_name,
                    "ERROR": "Failed to read content",
                    "Full Path": file_path
                })

            processed_count += 1
            if processed_count % 5 == 0 or processed_count == total_items:
                self.progress_callback(f"Processed {processed_count} of {total_items} PDFs", processed_count, total_items)
        
        # Save to Excel
        try:
            if not data:
                self.finish_callback(False, "No data extracted.", None)
                return
                
            # Pandas will automatically handle the massive mix of different dictionary keys
            df = pd.DataFrame(data)
            
            # Put File Name and Protocol Type at the front
            cols = list(df.columns)
            if "File Name" in cols: cols.remove("File Name")
            if "Protocol Type" in cols: cols.remove("Protocol Type")
            final_cols = ["File Name", "Protocol Type"] + cols
            df = df[final_cols]
            
            df.to_excel(self.output_excel_path, index=False)
            self.finish_callback(True, "Success", self.output_excel_path)
        except Exception as e:
            logging.error("Failed writing Excel file", exc_info=True)
            self.finish_callback(False, f"Target file might be open or read-only:\n{str(e)}", None)

    def _extract_hausanschluss(self, doc, text_p0):
        """Advanced logic imported from previous ATGY project."""
        results = {}
        try:
            page0 = doc[0]
            widgets = {w.field_name: w.field_value for w in page0.widgets()}
            
            results["BBND ID"] = widgets.get("ID", "")
            results["Anzahl WE"] = widgets.get("Dropdown1", "")
            results["Bezeichnung NVt"] = widgets.get("Text9", "")
            results["Datum Herstellung Hausanschluss"] = widgets.get("Date1", "")
            results["Bezeichnung Rohrverband"] = widgets.get("Text10", "")
            
            # Farbe Logic
            found_farbe = ""
            active_color_row_y = -1
            for w in page0.widgets():
                if w.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                     if w.field_value in ["Yes", "On", "True", "1"]:
                         if w.rect.x0 > 450:
                             active_color_row_y = (w.rect.y0 + w.rect.y1) / 2
                             break
                             
            if active_color_row_y != -1:
                search_r = fitz.Rect(400, active_color_row_y - 10, 600, active_color_row_y + 10)
                txt_in_row = page0.get_text("text", clip=search_r).lower()
                colors = ["grau", "orange", "braun", "schwarz", "blau", "rot", "gelb", "weiß", "weiss", "violett", "türkis", "rosa"]
                for c in colors:
                    if c in txt_in_row:
                        found_farbe = c
                        break
            results["Farbe"] = found_farbe if found_farbe else "grau"
            
            # Verbundrohr Logic
            import re
            verbund_match = re.search(r"(\d+x\d+(?:mm)?)", text_p0)
            results["Verbundrohr"] = verbund_match.group(1) if verbund_match else "12x10mm"

            # Image & Signature Checks
            zones = {
                 "Bild 1": fitz.Rect(60, 335, 310, 520),
                 "Bild 2": fitz.Rect(315, 335, 555, 520),
                 "Bild 3": fitz.Rect(60, 545, 310, 730),
                 "Bild 4": fitz.Rect(315, 545, 555, 730),
                 "Unterschrift": fitz.Rect(170, 750, 310, 775)
            }
            img_results = {}
            for key, rect in zones.items():
                if rect.x1 > page0.rect.width: rect.x1 = page0.rect.width
                if rect.y1 > page0.rect.height: rect.y1 = page0.rect.height
                
                sub_pix = page0.get_pixmap(clip=rect, dpi=72)
                raw_bytes = list(sub_pix.samples)
                
                if not raw_bytes:
                    has_content = False
                else:
                    std_dev = np.std(raw_bytes)
                    if key == "Unterschrift":
                        has_content = std_dev > 25.0 
                    else:
                        has_content = std_dev > 45.0
                img_results[key] = has_content

            results["Bild 1"] = img_results["Bild 1"]
            results["Bild 2"] = img_results["Bild 2"]
            results["Bild 3"] = img_results["Bild 3"]
            results["Bild 4"] = img_results["Bild 4"]
            results["Unterschrift"] = img_results["Unterschrift"]
            
        except Exception as e:
            results["Extractor Exception"] = str(e)
            
        return results

    def _extract_einblas(self, doc, text_p0):
        """Logic for Einblas-Protokoll extraction using flexible regex patterns."""
        results = {}
        try:
            # 1. Datum / Einblasdatum
            # Updated to include ':' as a valid date separator (found in some formats)
            datum_match = re.search(r"(?:Einblasdatum|Datum).*?(\d{2,4}[-.:]\d{2}[-.:]\d{2,4}(?:\s*[\d:]+)?)", text_p0, re.DOTALL | re.IGNORECASE)
            results["Einblasdatum"] = datum_match.group(1).strip() if datum_match else ""

            # 2. Streckenabschnitt
            strecke_abs_text = ""
            strecke_abschnitt_match = re.search(r"Streckenabschnitt\s*/?\s*NVt\s*[:\s]*\n?([^\n]+)", text_p0, re.IGNORECASE)
            if strecke_abschnitt_match:
                strecke_abs_text = strecke_abschnitt_match.group(1).strip()
            
            results["Streckenabschnitt"] = strecke_abs_text
            
            # Sub-splitting Streckenabschnitt into Start and Ziel based on user's new logic
            start_val = ""
            ziel_val = ""
            if strecke_abs_text:
                # Clean: Replace underscore with space and lowercase
                clean_text = strecke_abs_text.replace('_', ' ').strip()
                # Split at the first space (the first separator)
                parts = clean_text.split(' ', 1)
                
                if len(parts) >= 1:
                    start_val = parts[0].upper() # IDs like G6102 should be uppercase
                if len(parts) > 1:
                    ziel_val = parts[1].lower() # Values like "zum schützenplatz" should be lowercase
            
            results["Start"] = start_val
            results["Ziel"] = ziel_val

            # 3. Strecke (Länge)
            strecke_match = re.search(r"(?:Max\.)?Strecke(?:\(m\))?[:\s]*\n?(\d+)", text_p0, re.IGNORECASE)
            results["Strecke"] = strecke_match.group(1).strip() if strecke_match else ""

            # 4. Faserzahl
            # Priority 1: Label then Number (e.g., "Faserzahl\n24")
            faser_match = re.search(r"Faserzahl[:\s]*\n?(\d+)", text_p0, re.IGNORECASE)
            if not faser_match:
                # Priority 2: Cable pattern like "1x12" or "1x24"
                # Use word boundary \b to ensure we don't match "10x7"
                faser_match = re.search(r"\b1\s*x\s*(\d+)", text_p0, re.IGNORECASE)
            
            # Priority 3: Specific Gabocom layout (number between "SNR" and "Prelube")
            if not faser_match:
                faser_match = re.search(r"SNR.*?\n?(\d+)\s*\n\s*Prelube", text_p0, re.DOTALL | re.IGNORECASE)
                
            results["Faserzahl"] = faser_match.group(1).strip() if faser_match else ""

        except Exception as e:
            results["Extractor Exception"] = str(e)
            
        return results


class PDFParserApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Protocol PDF Parser Suite")
        self.root.geometry("550x250")
        self.root.resizable(False, False)
        
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
            
        self.logic = None
        self.current_output_path = None
        
        ttk.Label(self.root, text="Select Folder containing PDFs:").pack(pady=(15, 5), anchor="w", padx=20)
        self.frame_folder = ttk.Frame(self.root)
        self.frame_folder.pack(fill="x", padx=20)
        
        self.entry_folder = ttk.Entry(self.frame_folder)
        self.entry_folder.pack(side="left", fill="x", expand=True)
        # Default placeholder path
        self.entry_folder.insert(0, "")
        
        self.btn_browse = ttk.Button(self.frame_folder, text="Browse...", command=self.browse_folder)
        self.btn_browse.pack(side="right", padx=(5, 0))
        
        self.btn_analyze = ttk.Button(self.root, text="Extract PDF Data to Excel", command=self.start_analysis)
        self.btn_analyze.pack(fill="x", padx=20, pady=(20, 5), ipady=5)
        
        self.btn_open_folder = ttk.Button(self.root, text="📁 Open Output Folder", command=self.open_output_folder, state="disabled")
        self.btn_open_folder.pack(fill="x", padx=20, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        
        self.lbl_status = ttk.Label(self.root, text="Ready", foreground="gray")
        self.lbl_status.pack()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_folder.delete(0, tk.END)
            self.entry_folder.insert(0, folder)

    def update_progress(self, status_text, current, total):
        def _update():
            self.lbl_status.config(text=status_text)
            if total > 0:
                self.progress_var.set((current / total) * 100)
        self.root.after(0, _update)

    def finish_analysis(self, success, result_msg, file_path):
        def _finish():
            self.btn_analyze.config(state="normal")
            self.progress_var.set(100 if success else 0)
            if success:
                self.current_output_path = file_path
                self.btn_open_folder.config(state="normal")
                self.lbl_status.config(text="Extraction complete!", foreground="green")
                messagebox.showinfo("Success", f"PDF data saved to:\n{file_path}")
            else:
                self.btn_open_folder.config(state="disabled")
                self.lbl_status.config(text="Error occurred.", foreground="red")
                messagebox.showerror("Error", f"An error occurred:\n{result_msg}\n\nCheck pdf_parser_error.log for details.")
        self.root.after(0, _finish)

    def open_output_folder(self):
        if self.current_output_path and os.path.exists(self.current_output_path):
            try:
                subprocess.Popen(f'explorer /select,"{os.path.normpath(self.current_output_path)}"')
            except Exception:
                messagebox.showerror("Error", "Could not open folder.")

    def start_analysis(self):
        folder = self.entry_folder.get().strip()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Save extracted data as"
        )
        
        if not output_file: 
            return
            
        self.btn_analyze.config(state="disabled")
        self.btn_open_folder.config(state="disabled")
        self.progress_var.set(0)
        
        self.logic = PDFParserLogic(folder, output_file, self.update_progress, self.finish_analysis)
        thread = threading.Thread(target=self.logic.run)
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFParserApp(root)
    root.mainloop()
