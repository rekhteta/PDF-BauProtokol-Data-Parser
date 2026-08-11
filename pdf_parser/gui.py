import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
from typing import Dict, List, Any

from .config import load_profiles, save_profiles, get_column_categories
from .logic import PDFParserLogic

class PDFParserApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Multi-Protocol PDF Parser Suite")
        self.root.geometry("580x400")
        self.root.resizable(False, False)
        
        self._setup_styles()
        
        self.logic = None
        self.current_output_path = None
        
        # Load and configure columns/categories dynamically
        self.column_vars = {}
        self.reload_column_categories()
        
        # Layout Setup
        main_frame = ttk.Frame(self.root, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)

        # Header Title
        title_label = ttk.Label(main_frame, text="PDF Protocol Data Extractor", style="Title.TLabel")
        title_label.pack(anchor="w", pady=(0, 10))

        # Folder Selection Section
        ttk.Label(main_frame, text="Select Folder containing Protocols (PDF):", style="Header.TLabel").pack(anchor="w")
        
        self.frame_folder = ttk.Frame(main_frame)
        self.frame_folder.pack(fill="x", pady=(5, 12))
        
        self.entry_folder = ttk.Entry(self.frame_folder, font=("Segoe UI", 10))
        self.entry_folder.pack(side="left", fill="x", expand=True, ipady=3)
        
        self.btn_browse = ttk.Button(self.frame_folder, text="Browse...", command=self.browse_folder, style="Action.TButton")
        self.btn_browse.pack(side="right", padx=(8, 0))
        
        # Settings Column Selection Button
        self.btn_settings = ttk.Button(main_frame, text="⚙️  Configure Output Columns", command=self.open_settings, style="Secondary.TButton")
        self.btn_settings.pack(fill="x", pady=(0, 10), ipady=2)
        
        # Calibration Tool Button
        self.btn_calibrate = ttk.Button(main_frame, text="🔧  Manage Profiles & Calibration", command=self.open_calibration, style="Secondary.TButton")
        self.btn_calibrate.pack(fill="x", pady=(0, 10), ipady=2)
        
        # Execution Button
        self.btn_analyze = ttk.Button(main_frame, text="🚀  Extract PDF Data to Excel", command=self.start_analysis, style="Primary.TButton")
        self.btn_analyze.pack(fill="x", pady=(0, 8), ipady=4)
        
        # Open Output Folder Button
        self.btn_open_folder = ttk.Button(main_frame, text="📁  Open Output Folder", command=self.open_output_folder, state="disabled", style="Secondary.TButton")
        self.btn_open_folder.pack(fill="x", pady=(0, 10), ipady=2)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 8))
        
        # Status Label
        self.lbl_status = ttk.Label(main_frame, text="Ready", style="Status.TLabel")
        self.lbl_status.pack()

    def reload_column_categories(self):
        """Loads column categories from profiles and merges them dynamically, keeping profile order."""
        categories = get_column_categories()
        
        # Remove categories that are no longer present
        for category in list(self.column_vars.keys()):
            if category not in categories:
                del self.column_vars[category]
                
        # Merge/add and prune columns within each category, maintaining profile order
        for category, fields in categories.items():
            old_vars = self.column_vars.get(category, {})
            new_vars = {}
            
            for col_name, default_val in fields.items():
                if col_name in old_vars:
                    # Keep existing Tkinter variable
                    new_vars[col_name] = old_vars[col_name]
                else:
                    # Create new Tkinter variable
                    new_vars[col_name] = tk.BooleanVar(value=default_val)
            
            self.column_vars[category] = new_vars

    def _setup_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
            
        self.root.configure(bg="#F3F4F6")
        font_family = "Segoe UI"
        
        style.configure(".", font=(font_family, 10), background="#F3F4F6", foreground="#1F2937")
        style.configure("TFrame", background="#F3F4F6")
        style.configure("TLabel", background="#F3F4F6", foreground="#1F2937")
        
        style.configure("Title.TLabel", font=(font_family, 14, "bold"), foreground="#2563EB", background="#F3F4F6")
        style.configure("Header.TLabel", font=(font_family, 10, "bold"), foreground="#4B5563", background="#F3F4F6")
        style.configure("Status.TLabel", font=(font_family, 9, "medium"), foreground="#6B7280", background="#F3F4F6")
        
        style.configure("TEntry", fieldbackground="#FFFFFF", bordercolor="#D1D5DB", lightcolor="#D1D5DB", darkcolor="#D1D5DB", padding=5)
        
        style.configure("Primary.TButton", font=(font_family, 10, "bold"), background="#2563EB", foreground="#FFFFFF", bordercolor="#1D4ED8", lightcolor="#2563EB", darkcolor="#1D4ED8")
        style.map("Primary.TButton",
            background=[("active", "#1D4ED8"), ("disabled", "#E5E7EB")],
            foreground=[("disabled", "#9CA3AF")],
            bordercolor=[("disabled", "#E5E7EB")]
        )
        
        style.configure("Secondary.TButton", font=(font_family, 9, "bold"), background="#FFFFFF", foreground="#4B5563", bordercolor="#D1D5DB", lightcolor="#FFFFFF", darkcolor="#D1D5DB")
        style.map("Secondary.TButton",
            background=[("active", "#F9FAFB"), ("disabled", "#E5E7EB")],
            foreground=[("disabled", "#9CA3AF")],
            bordercolor=[("disabled", "#E5E7EB")]
        )
        
        style.configure("Action.TButton", font=(font_family, 9, "bold"), background="#4B5563", foreground="#FFFFFF", bordercolor="#374151")
        style.map("Action.TButton",
            background=[("active", "#374151"), ("disabled", "#E5E7EB")],
            foreground=[("disabled", "#9CA3AF")]
        )

        style.configure("Horizontal.TProgressbar", thickness=6, troughcolor="#E5E7EB", background="#2563EB", bordercolor="#E5E7EB", lightcolor="#2563EB", darkcolor="#2563EB")

    def _toggle_group(self, var_dict: Dict[str, tk.BooleanVar], state: bool):
        for var in var_dict.values():
            var.set(state)

    def open_settings(self):
        self.reload_column_categories()
        settings_win = tk.Toplevel(self.root)
        settings_win.title("Excel Column Selection")
        settings_win.geometry("640x520")
        settings_win.configure(bg="#F3F4F6")
        settings_win.grab_set() 
        settings_win.resizable(False, False)

        ttk.Label(settings_win, text="Select Columns to Include in Output Excel", style="Title.TLabel").pack(pady=(15, 5))
        ttk.Label(settings_win, text="Check fields to enable, or use All / None buttons.", style="Status.TLabel").pack(pady=(0, 10))
        
        paned = ttk.PanedWindow(settings_win, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=20, pady=5)
        
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        tree_style = ttk.Style(settings_win)
        tree_style.configure("Treeview", font=("Segoe UI", 10), rowheight=26, background="#FFFFFF", fieldbackground="#FFFFFF")
        
        tree = ttk.Treeview(left_frame, show="tree", selectmode="browse")
        tree.pack(fill="both", expand=True)
        
        right_frame = ttk.LabelFrame(paned, text=" Available Fields ")
        paned.add(right_frame, weight=2)
        
        scroll_canvas = tk.Canvas(right_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=scroll_canvas.yview)
        scroll_content = ttk.Frame(scroll_canvas, style="TFrame")
        scroll_content.configure(style="SettingsScroll.TFrame")
        
        style = ttk.Style(settings_win)
        style.configure("SettingsScroll.TFrame", background="#FFFFFF")
        style.configure("SettingsCheck.TCheckbutton", background="#FFFFFF")
        
        scroll_content.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=scroll_content, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def on_category_select(event):
            for widget in scroll_content.winfo_children():
                widget.destroy()
                
            selection = tree.selection()
            if not selection: return
            
            category_name = tree.item(selection[0])["text"]
            if category_name in self.column_vars:
                var_dict = self.column_vars[category_name]
                
                btn_frame = ttk.Frame(scroll_content, style="SettingsScroll.TFrame")
                btn_frame.pack(fill="x", pady=(5, 10))
                
                ttk.Button(btn_frame, text="Select All", width=12, command=lambda: self._toggle_group(var_dict, True), style="Secondary.TButton").pack(side="left", padx=2)
                ttk.Button(btn_frame, text="Clear All", width=12, command=lambda: self._toggle_group(var_dict, False), style="Secondary.TButton").pack(side="left", padx=2)
                
                for name, var in var_dict.items():
                    ttk.Checkbutton(scroll_content, text=name, variable=var, style="SettingsCheck.TCheckbutton").pack(anchor="w", padx=15, pady=4)
        
        tree.bind("<<TreeviewSelect>>", on_category_select)
        
        node_gen = tree.insert("", "end", text="General Info", open=True)
        node_docs = tree.insert("", "end", text="Document Types", open=True)
        for cat in self.column_vars.keys():
            if cat != "General Info":
                tree.insert(node_docs, "end", text=cat)
        
        tree.selection_set(node_gen)
        
        btn_close = ttk.Button(settings_win, text="Apply & Save Settings", command=settings_win.destroy, style="Primary.TButton")
        btn_close.pack(pady=15, ipady=3)

    def open_calibration(self):
        calibration_win = ProfileManagerWindow(self)
        calibration_win.grab_set()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.entry_folder.delete(0, tk.END)
            self.entry_folder.insert(0, folder)

    def update_progress(self, status_text: str, current: int, total: int):
        def _update():
            if total > 0:
                percent = int((current / total) * 100)
                full_status = f"{status_text} ({percent}%)"
                self.progress_var.set((current / total) * 100)
            else:
                full_status = status_text
            self.lbl_status.config(text=full_status)
        self.root.after(0, _update)

    def finish_analysis(self, success: bool, result_msg: str, file_path: str):
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
            
        # Re-aggregate all selected columns from tree selection variables
        self.reload_column_categories()
        selected_cols = []
        for cat_vars in self.column_vars.values():
            for col, var in cat_vars.items():
                if var.get():
                    selected_cols.append(col)
        
        if not selected_cols:
            messagebox.showwarning("Warning", "Please select at least one column in Settings.")
            return

        self.btn_analyze.config(state="disabled")
        self.btn_open_folder.config(state="disabled")
        self.progress_var.set(0)
        
        self.logic = PDFParserLogic(folder, output_file, self.update_progress, self.finish_analysis, selected_cols)
        thread = threading.Thread(target=self.logic.run)
        thread.daemon = True
        thread.start()


# ─────────────────────────────────────────────────────────────────────────────
# Rule type descriptions shown in the combo dropdown
# ─────────────────────────────────────────────────────────────────────────────
RULE_TYPE_LABELS = {
    "inline":              "inline — value on the SAME line as keyword",
    "next_line":           "next_line — value on the NEXT line below keyword",
    "fixed_index":         "fixed_index — value at a fixed line number",
    "speednet_positional": "speednet_positional — SpeedNet header block by position",
    "regex":               "regex — custom regular expression pattern",
    "regex_combine":       "regex_combine — combine two regex captures (e.g. Start / Ende)",
}
RULE_TYPE_KEYS = list(RULE_TYPE_LABELS.keys())


class ProfileManagerWindow(tk.Toplevel):
    def __init__(self, main_app: PDFParserApp):
        super().__init__(main_app.root)
        self.main_app = main_app
        self.title("Manage Profiles & Calibration")
        self.geometry("1280x720")
        self.configure(bg="#F3F4F6")
        
        self.profiles = load_profiles()
        self.selected_profile_idx = None
        self.selected_column_name = None
        
        self.pdf_lines = []          # cleaned text lines for active page
        self.pdf_line_bboxes = []    # corresponding fitz.Rect for each line (may be None)
        self.loaded_pdf_path = None
        self.current_page_idx = 0
        self.total_pages = 1
        self._pdf_img_tk = None      # keep reference to prevent GC
        self._pdf_page_obj = None    # kept open for click-lookup (closed on next load)
        self._pdf_doc_obj = None
        self._img_scale = 1.0        # scale factor image → PDF coords
        
        self._build_ui()
        self._load_profiles_list()

    def _create_sector_title(self, parent, text: str):
        import tkinter as tk
        title_var = tk.StringVar(value=text)
        entry = tk.Entry(parent, textvariable=title_var, state="readonly",
                         readonlybackground="#F3F4F6", relief="flat", bd=0,
                         font=("Segoe UI", 9, "bold"), fg="#1F2937")
        entry.pack(anchor="w", padx=5, pady=(2, 5))
        return entry

    # --------------------------------------------------------------------------
    # UI Construction
    # --------------------------------------------------------------------------
    def _build_ui(self):
        # 3 Panels PanedWindow
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=15, pady=(15, 5))
        
        # -- Panel 1: Profiles Sidebar --------------------------------------
        left_frame = ttk.LabelFrame(paned, text="")
        paned.add(left_frame, weight=1)
        self._create_sector_title(left_frame, "Profiles")
        
        self.listbox_profiles = tk.Listbox(left_frame, font=("Segoe UI", 10))
        self.listbox_profiles.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox_profiles.bind("<<ListboxSelect>>", self._on_profile_select)
        
        btn_frame_profiles = ttk.Frame(left_frame)
        btn_frame_profiles.pack(fill="x", padx=5, pady=(0, 2))
        ttk.Button(btn_frame_profiles, text="New", command=self._add_profile, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(btn_frame_profiles, text="Clone", command=self._clone_profile, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(btn_frame_profiles, text="Delete", command=self._delete_profile, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        
        move_frame_profiles = ttk.Frame(left_frame)
        move_frame_profiles.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Button(move_frame_profiles, text="^ Move Up", command=self._move_profile_up, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(move_frame_profiles, text="v Move Down", command=self._move_profile_down, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        
        # -- Panel 2: Columns list ------------------------------------------
        center_frame = ttk.LabelFrame(paned, text="")
        paned.add(center_frame, weight=1)
        self._create_sector_title(center_frame, "Columns Configuration")
        
        self.listbox_columns = tk.Listbox(center_frame, font=("Segoe UI", 10))
        self.listbox_columns.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox_columns.bind("<<ListboxSelect>>", self._on_column_select)
        
        # Move Up / Move Down for columns
        move_frame_cols = ttk.Frame(center_frame)
        move_frame_cols.pack(fill="x", padx=5, pady=(0, 2))
        ttk.Button(move_frame_cols, text="^ Up", command=self._move_column_up, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        ttk.Button(move_frame_cols, text="v Down", command=self._move_column_down, style="Secondary.TButton").pack(side="left", fill="x", expand=True, padx=1)
        
        # Add new column
        add_col_frame = ttk.Frame(center_frame)
        add_col_frame.pack(fill="x", padx=5, pady=(0, 2))
        self.entry_new_col = ttk.Entry(add_col_frame, font=("Segoe UI", 9))
        self.entry_new_col.pack(side="left", fill="x", expand=True, ipady=2)
        ttk.Button(add_col_frame, text="+ Add", command=self._add_column, style="Secondary.TButton").pack(side="right", padx=(5, 0))
        
        btn_frame_columns = ttk.Frame(center_frame)
        btn_frame_columns.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Button(btn_frame_columns, text="Remove Column", command=self._remove_column, style="Secondary.TButton").pack(fill="x")

        # -- Panel 3: PDF Calibration ---------------------------------------
        right_frame = ttk.LabelFrame(paned, text="")
        paned.add(right_frame, weight=5)
        self._create_sector_title(right_frame, "Layout Calibration & Rules")

        # Split Right Frame into two sub-columns: left for PDF Image, right for settings
        calib_paned = ttk.PanedWindow(right_frame, orient="horizontal")
        calib_paned.pack(fill="both", expand=True, padx=5, pady=5)
        
        calib_left = ttk.Frame(calib_paned)
        calib_paned.add(calib_left, weight=3)
        
        calib_right = ttk.Frame(calib_paned)
        calib_paned.add(calib_right, weight=2)
        
        # Left Calib column: PDF select & Canvas
        pdf_select_frame = ttk.Frame(calib_left)
        pdf_select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(pdf_select_frame, text="Sample PDF:").pack(side="left", padx=(0, 5))
        
        self.combo_pdfs = ttk.Combobox(pdf_select_frame, state="readonly")
        self.combo_pdfs.pack(side="left", fill="x", expand=True)
        self.combo_pdfs.bind("<<ComboboxSelected>>", self._on_combo_pdf_select)
        
        ttk.Button(pdf_select_frame, text="Browse...", command=self._browse_pdf, style="Secondary.TButton").pack(side="left", padx=5)
        ttk.Button(pdf_select_frame, text="Refresh Folder", command=self._refresh_folder_pdfs, style="Secondary.TButton").pack(side="left")

        # Multi-page Navigation Bar
        page_nav_frame = ttk.Frame(calib_left)
        page_nav_frame.pack(fill="x", padx=5, pady=(2, 4))
        
        self.btn_prev_page = ttk.Button(page_nav_frame, text="◀ Prev Page", command=self._prev_page, style="Secondary.TButton", state="disabled")
        self.btn_prev_page.pack(side="left", padx=2)
        
        self.lbl_page_num = ttk.Label(page_nav_frame, text="Page 1 / 1", font=("Segoe UI", 9, "bold"))
        self.lbl_page_num.pack(side="left", padx=10)
        
        self.btn_next_page = ttk.Button(page_nav_frame, text="Next Page ▶", command=self._next_page, style="Secondary.TButton", state="disabled")
        self.btn_next_page.pack(side="left", padx=2)

        # Alert banner for comments/stamps
        self.lbl_alert = tk.Label(calib_left, text="", bg="#F3F4F6", font=("Segoe UI", 9, "bold"), anchor="w", padx=10, pady=4)
        self.lbl_alert.pack(fill="x", padx=5, pady=2)

        # PDF image viewer
        img_frame = ttk.LabelFrame(calib_left, text="")
        self._create_sector_title(img_frame, "PDF Page Preview (click to select line)")
        img_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas_pdf = tk.Canvas(img_frame, bg="#E5E7EB", cursor="crosshair", highlightthickness=0)
        img_scrollbar_y = ttk.Scrollbar(img_frame, orient="vertical", command=self.canvas_pdf.yview)
        img_scrollbar_x = ttk.Scrollbar(img_frame, orient="horizontal", command=self.canvas_pdf.xview)
        self.canvas_pdf.configure(yscrollcommand=img_scrollbar_y.set, xscrollcommand=img_scrollbar_x.set)
        img_scrollbar_y.pack(side="right", fill="y")
        img_scrollbar_x.pack(side="bottom", fill="x")
        self.canvas_pdf.pack(fill="both", expand=True)
        self.canvas_pdf.bind("<Button-1>", self._on_pdf_canvas_click)

        # Right Calib column: text lines & rules config
        lines_frame = ttk.LabelFrame(calib_right, text="")
        self._create_sector_title(lines_frame, "PDF Text Lines (click to auto-suggest rule)")
        lines_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar_lines = ttk.Scrollbar(lines_frame, orient="vertical")
        scrollbar_lines.pack(side="right", fill="y")
        
        self.listbox_pdf_lines = tk.Listbox(lines_frame, font=("Consolas", 9), selectmode="single", yscrollcommand=scrollbar_lines.set)
        self.listbox_pdf_lines.pack(fill="both", expand=True, padx=5, pady=5)
        self.listbox_pdf_lines.bind("<<ListboxSelect>>", self._on_line_select)
        self.listbox_pdf_lines.bind("<Control-c>", self._copy_selected_pdf_line)
        self.listbox_pdf_lines.bind("<Control-C>", self._copy_selected_pdf_line)
        scrollbar_lines.config(command=self.listbox_pdf_lines.yview)

        lines_action_frame = ttk.Frame(lines_frame)
        lines_action_frame.pack(fill="x", padx=5, pady=(2, 4))
        ttk.Button(lines_action_frame, text="📋 Copy Selected Line", command=self._copy_selected_pdf_line, style="Secondary.TButton").pack(side="left")

        # Right-click Context Menu for Listbox
        self.line_context_menu = tk.Menu(self, tearoff=0)
        self.line_context_menu.add_command(label="📋 Copy Line Text", command=self._copy_selected_pdf_line)
        self.line_context_menu.add_command(label="🎯 Set as Trigger Keyword", command=self._set_trigger_from_pdf)

        def _show_line_context_menu(event):
            idx = self.listbox_pdf_lines.nearest(event.y)
            if idx >= 0:
                self.listbox_pdf_lines.selection_clear(0, tk.END)
                self.listbox_pdf_lines.selection_set(idx)
                self._on_line_select(None, forced_idx=idx)
            self.line_context_menu.post(event.x_root, event.y_root)

        self.listbox_pdf_lines.bind("<Button-3>", _show_line_context_menu)
        self.listbox_pdf_lines.bind("<Button-2>", _show_line_context_menu)

        # Trigger keyword section
        trigger_frame = ttk.LabelFrame(calib_right, text="")
        self._create_sector_title(trigger_frame, "Trigger Keywords")
        trigger_frame.pack(fill="x", padx=5, pady=(5, 2))
        
        ttk.Label(
            trigger_frame,
            text="ℹ  Comma-separated keywords — if ANY appears in the PDF, this profile activates.",
            foreground="#6B7280", font=("Segoe UI", 8)
        ).pack(anchor="w", padx=5, pady=(3, 0))
        
        trigger_row = ttk.Frame(trigger_frame)
        trigger_row.pack(fill="x", padx=5, pady=4)
        self.entry_trigger = ttk.Entry(trigger_row, font=("Segoe UI", 9))
        self.entry_trigger.pack(side="left", fill="x", expand=True, ipady=2)
        ttk.Button(trigger_row, text="Set Selected Line", command=self._set_trigger_from_pdf, style="Secondary.TButton").pack(side="right", padx=(4, 0))
        ttk.Button(trigger_row, text="Auto Detect", command=self._auto_detect_trigger, style="Secondary.TButton").pack(side="right", padx=(4, 0))

        # Rule editor
        rules_frame = ttk.LabelFrame(calib_right, text="")
        self._create_sector_title(rules_frame, "Extraction Rules for selected Column")
        rules_frame.pack(fill="x", padx=5, pady=(2, 5))

        rule_list_row = ttk.Frame(rules_frame)
        rule_list_row.pack(fill="x", padx=5, pady=(5, 0))

        scrollbar_rules = ttk.Scrollbar(rule_list_row, orient="vertical")
        scrollbar_rules.pack(side="right", fill="y")
        self.listbox_rules = tk.Listbox(rule_list_row, height=3, font=("Segoe UI", 9), yscrollcommand=scrollbar_rules.set)
        self.listbox_rules.pack(fill="both", expand=True)
        scrollbar_rules.config(command=self.listbox_rules.yview)
        self.listbox_rules.bind("<<ListboxSelect>>", self._on_rule_select)

        rule_btn_row = ttk.Frame(rules_frame)
        rule_btn_row.pack(fill="x", padx=5, pady=2)
        ttk.Button(rule_btn_row, text="▲ Move Up", command=self._move_rule_up, style="Secondary.TButton").pack(side="left", padx=1)
        ttk.Button(rule_btn_row, text="▼ Move Down", command=self._move_rule_down, style="Secondary.TButton").pack(side="left", padx=1)
        ttk.Button(rule_btn_row, text="Delete Rule", command=self._delete_rule, style="Secondary.TButton").pack(side="left", padx=1)
        self.btn_test_rule = ttk.Button(rule_btn_row, text="▶ Test Rule", command=self._test_selected_rule, style="Secondary.TButton")
        self.btn_test_rule.pack(side="right", padx=1)
        self.lbl_rule_result = ttk.Label(rule_btn_row, text="", foreground="#059669", font=("Segoe UI", 9, "bold"))
        self.lbl_rule_result.pack(side="right", padx=6)

        # Dynamic rule param area
        param_outer = ttk.LabelFrame(rules_frame, text="")
        self._create_sector_title(param_outer, "Add / Edit Rule")
        param_outer.pack(fill="x", padx=5, pady=(2, 5))

        type_row = ttk.Frame(param_outer)
        type_row.pack(fill="x", padx=5, pady=(4, 2))
        ttk.Label(type_row, text="Type:").pack(side="left")
        self.combo_rule_type = ttk.Combobox(
            type_row,
            values=list(RULE_TYPE_LABELS.values()),
            state="readonly", width=46
        )
        self.combo_rule_type.pack(side="left", padx=5, fill="x", expand=True)
        self.combo_rule_type.bind("<<ComboboxSelected>>", self._on_rule_type_change)

        # Container for dynamic param widgets
        self.rule_param_frame = ttk.Frame(param_outer)
        self.rule_param_frame.pack(fill="x", padx=5, pady=(2, 5))

        # Pre-create all possible param widgets (shown/hidden by type)
        self._build_rule_param_widgets()

        rule_action_btn_row = ttk.Frame(param_outer)
        rule_action_btn_row.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Button(rule_action_btn_row, text="✓ Update Selected Rule", command=self._update_rule, style="Secondary.TButton").pack(side="right", padx=2)
        ttk.Button(rule_action_btn_row, text="+ Add New Rule", command=self._add_rule, style="Primary.TButton").pack(side="right", padx=2)

        # ── Footer Actions ─────────────────────────────────────────────────
        footer_frame = ttk.Frame(self)
        footer_frame.pack(fill="x", padx=15, pady=10)
        
        ttk.Button(footer_frame, text="Test Full Profile", command=self._test_extraction, style="Secondary.TButton").pack(side="left", padx=5)
        
        ttk.Button(footer_frame, text="Apply & Save Profiles", command=self._save_and_close, style="Primary.TButton").pack(side="right", padx=5)
        ttk.Button(footer_frame, text="Cancel", command=self.destroy, style="Secondary.TButton").pack(side="right", padx=5)

        # Load PDFs in the selected folder automatically if set
        self._refresh_folder_pdfs()

    # ──────────────────────────────────────────────────────────────────────────
    # Dynamic rule param widgets
    # ──────────────────────────────────────────────────────────────────────────
    def _build_rule_param_widgets(self):
        """Create all possible rule-type-specific param widgets inside self.rule_param_frame."""
        f = self.rule_param_frame

        # — inline / next_line: keyword entry
        self._pw_kw_frame = ttk.Frame(f)
        ttk.Label(self._pw_kw_frame, text="Keyword / Label:").pack(side="left")
        self._pw_kw_entry = ttk.Entry(self._pw_kw_frame, font=("Segoe UI", 9))
        self._pw_kw_entry.pack(side="left", fill="x", expand=True, padx=5, ipady=1)

        # — fixed_index: line number
        self._pw_idx_frame = ttk.Frame(f)
        ttk.Label(self._pw_idx_frame, text="Line Index:").pack(side="left")
        self._pw_idx_var = tk.IntVar(value=0)
        ttk.Spinbox(self._pw_idx_frame, from_=0, to=9999, textvariable=self._pw_idx_var, width=8, font=("Segoe UI", 9)).pack(side="left", padx=5)

        # — speednet_positional: index + pattern
        self._pw_sp_frame = ttk.Frame(f)
        ttk.Label(self._pw_sp_frame, text="Index:").pack(side="left")
        self._pw_sp_idx = tk.IntVar(value=0)
        ttk.Spinbox(self._pw_sp_frame, from_=0, to=999, textvariable=self._pw_sp_idx, width=6, font=("Segoe UI", 9)).pack(side="left", padx=4)
        ttk.Label(self._pw_sp_frame, text="Pattern:").pack(side="left")
        self._pw_sp_pat = ttk.Entry(self._pw_sp_frame, font=("Segoe UI", 9), width=15)
        self._pw_sp_pat.pack(side="left", padx=4, fill="x", expand=True)

        # — regex: pattern + group + pick
        self._pw_re_frame = ttk.Frame(f)
        ttk.Label(self._pw_re_frame, text="Pattern:").pack(side="left")
        self._pw_re_pat = ttk.Entry(self._pw_re_frame, font=("Segoe UI", 9))
        self._pw_re_pat.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Label(self._pw_re_frame, text="Group:").pack(side="left")
        self._pw_re_grp = tk.IntVar(value=1)
        ttk.Spinbox(self._pw_re_frame, from_=0, to=20, textvariable=self._pw_re_grp, width=4, font=("Segoe UI", 9)).pack(side="left", padx=4)
        ttk.Label(self._pw_re_frame, text="Pick:").pack(side="left")
        self._pw_re_pick = ttk.Combobox(self._pw_re_frame, values=["first", "last"], state="readonly", width=6)
        self._pw_re_pick.set("first")
        self._pw_re_pick.pack(side="left", padx=4)

        # — regex_combine: patterns list + format string (two rows)
        self._pw_rc_frame = ttk.Frame(f)
        ttk.Label(self._pw_rc_frame, text="Pattern 1:").grid(row=0, column=0, sticky="w")
        self._pw_rc_p1 = ttk.Entry(self._pw_rc_frame, font=("Segoe UI", 9))
        self._pw_rc_p1.grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Label(self._pw_rc_frame, text="Pattern 2:").grid(row=1, column=0, sticky="w")
        self._pw_rc_p2 = ttk.Entry(self._pw_rc_frame, font=("Segoe UI", 9))
        self._pw_rc_p2.grid(row=1, column=1, sticky="ew", padx=4)
        ttk.Label(self._pw_rc_frame, text="Format:").grid(row=2, column=0, sticky="w")
        self._pw_rc_fmt = ttk.Entry(self._pw_rc_frame, font=("Segoe UI", 9))
        self._pw_rc_fmt.insert(0, "{0} / {1}")
        self._pw_rc_fmt.grid(row=2, column=1, sticky="ew", padx=4)
        self._pw_rc_frame.columnconfigure(1, weight=1)

        # Initially show nothing — wait for type selection
        self._current_param_widget = None

    def _on_rule_type_change(self, event=None):
        """Show the param widgets relevant to the selected rule type."""
        label = self.combo_rule_type.get()
        rtype = next((k for k, v in RULE_TYPE_LABELS.items() if v == label), None)

        if self._current_param_widget:
            self._current_param_widget.pack_forget()
            self._current_param_widget = None

        if rtype in ("inline", "next_line"):
            self._pw_kw_frame.pack(fill="x", expand=True)
            self._current_param_widget = self._pw_kw_frame
        elif rtype == "fixed_index":
            self._pw_idx_frame.pack(fill="x", expand=True)
            self._current_param_widget = self._pw_idx_frame
        elif rtype == "speednet_positional":
            self._pw_sp_frame.pack(fill="x", expand=True)
            self._current_param_widget = self._pw_sp_frame
        elif rtype == "regex":
            self._pw_re_frame.pack(fill="x", expand=True)
            self._current_param_widget = self._pw_re_frame
        elif rtype == "regex_combine":
            self._pw_rc_frame.pack(fill="x", expand=True)
            self._current_param_widget = self._pw_rc_frame

    # ──────────────────────────────────────────────────────────────────────────
    # Profile list helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _load_profiles_list(self):
        self.listbox_profiles.delete(0, tk.END)
        for p in self.profiles:
            self.listbox_profiles.insert(tk.END, p["name"])
        
        # Reset selection states
        self.selected_profile_idx = None
        self.selected_column_name = None
        self.listbox_columns.delete(0, tk.END)
        self.listbox_rules.delete(0, tk.END)

    def _on_profile_select(self, event):
        selection = self.listbox_profiles.curselection()
        if not selection:
            return
        self.selected_profile_idx = selection[0]
        p = self.profiles[self.selected_profile_idx]
        
        # Set trigger keywords in entry
        self.entry_trigger.delete(0, tk.END)
        self.entry_trigger.insert(0, ", ".join(p.get("trigger_keywords", [])))
        
        # Load columns (use ordered dict keys)
        self.listbox_columns.delete(0, tk.END)
        for col_name in p["columns"].keys():
            self.listbox_columns.insert(tk.END, col_name)
            
        self.selected_column_name = None
        self.listbox_rules.delete(0, tk.END)

    def _move_profile_up(self):
        if self.selected_profile_idx is None or self.selected_profile_idx == 0:
            return
        idx = self.selected_profile_idx
        self.profiles[idx], self.profiles[idx - 1] = self.profiles[idx - 1], self.profiles[idx]
        self._reload_profiles_keep_selection(idx - 1)

    def _move_profile_down(self):
        if self.selected_profile_idx is None or self.selected_profile_idx >= len(self.profiles) - 1:
            return
        idx = self.selected_profile_idx
        self.profiles[idx], self.profiles[idx + 1] = self.profiles[idx + 1], self.profiles[idx]
        self._reload_profiles_keep_selection(idx + 1)

    def _reload_profiles_keep_selection(self, new_idx: int):
        self.listbox_profiles.delete(0, tk.END)
        for p in self.profiles:
            self.listbox_profiles.insert(tk.END, p["name"])
        self.listbox_profiles.selection_set(new_idx)
        self.selected_profile_idx = new_idx
        self._on_profile_select(None)

    # ──────────────────────────────────────────────────────────────────────────
    # Column list helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _on_column_select(self, event):
        selection = self.listbox_columns.curselection()
        if not selection or self.selected_profile_idx is None:
            return
        self.selected_column_name = self.listbox_columns.get(selection[0])
        self._load_rules_list()

    def _move_column_up(self):
        selection = self.listbox_columns.curselection()
        if not selection or self.selected_profile_idx is None:
            return
        idx = selection[0]
        if idx == 0:
            return
        p = self.profiles[self.selected_profile_idx]
        keys = list(p["columns"].keys())
        keys[idx], keys[idx - 1] = keys[idx - 1], keys[idx]
        p["columns"] = {k: p["columns"][k] for k in keys}
        self._reload_columns_keep_selection(idx - 1)

    def _move_column_down(self):
        selection = self.listbox_columns.curselection()
        if not selection or self.selected_profile_idx is None:
            return
        idx = selection[0]
        p = self.profiles[self.selected_profile_idx]
        keys = list(p["columns"].keys())
        if idx >= len(keys) - 1:
            return
        keys[idx], keys[idx + 1] = keys[idx + 1], keys[idx]
        p["columns"] = {k: p["columns"][k] for k in keys}
        self._reload_columns_keep_selection(idx + 1)

    def _reload_columns_keep_selection(self, new_idx: int):
        p = self.profiles[self.selected_profile_idx]
        self.listbox_columns.delete(0, tk.END)
        for col_name in p["columns"].keys():
            self.listbox_columns.insert(tk.END, col_name)
        self.listbox_columns.selection_set(new_idx)
        self.selected_column_name = self.listbox_columns.get(new_idx)
        self._load_rules_list()

    def _add_column(self):
        if self.selected_profile_idx is None:
            messagebox.showwarning("Warning", "Select a profile first.")
            return
        col_name = self.entry_new_col.get().strip()
        if not col_name:
            return
        
        p = self.profiles[self.selected_profile_idx]
        if col_name in p["columns"]:
            messagebox.showerror("Error", "Column already exists.")
            return
            
        p["columns"][col_name] = []
        self.entry_new_col.delete(0, tk.END)
        
        # Reload columns and select the new one
        keys = list(p["columns"].keys())
        new_idx = keys.index(col_name)
        self._reload_columns_keep_selection(new_idx)

    def _remove_column(self):
        if self.selected_profile_idx is None or not self.selected_column_name:
            return
        p = self.profiles[self.selected_profile_idx]
        if messagebox.askyesno("Confirm Delete", f"Remove column '{self.selected_column_name}' from profile '{p['name']}'?"):
            del p["columns"][self.selected_column_name]
            self.selected_column_name = None
            self._on_profile_select(None)

    # ──────────────────────────────────────────────────────────────────────────
    # Rules list helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _load_rules_list(self):
        self.listbox_rules.delete(0, tk.END)
        self.lbl_rule_result.config(text="")
        if self.selected_profile_idx is None or not self.selected_column_name:
            return
        
        p = self.profiles[self.selected_profile_idx]
        rules = p["columns"].get(self.selected_column_name, [])
        for rule in rules:
            self.listbox_rules.insert(tk.END, self._rule_label(rule))

    def _rule_label(self, rule: dict) -> str:
        rtype = rule.get("type", "?")
        if rtype in ("inline", "next_line"):
            return f"{rtype}: keys={rule.get('keys', [])}"
        elif rtype == "fixed_index":
            return f"fixed_index: idx={rule.get('index', 0)}"
        elif rtype == "speednet_positional":
            return f"speednet_positional: idx={rule.get('index', 0)}, pattern={rule.get('pattern', '')}"
        elif rtype == "regex":
            pick = rule.get("pick", "first")
            return f"regex[{pick}]: grp={rule.get('group',1)}, /{rule.get('pattern', '')}/"
        elif rtype == "regex_combine":
            return f"regex_combine: {rule.get('patterns', [])} → \"{rule.get('format', '')}\""
        elif rtype == "special":
            return f"special: name={rule.get('name', '')}"
        return str(rule)

    def _on_rule_select(self, event=None):
        self.lbl_rule_result.config(text="")
        selection = self.listbox_rules.curselection()
        if not selection or self.selected_profile_idx is None or not self.selected_column_name:
            return
        
        p = self.profiles[self.selected_profile_idx]
        rules = p["columns"].get(self.selected_column_name, [])
        idx = selection[0]
        if idx >= len(rules):
            return
        rule = rules[idx]
        
        rtype = rule.get("type", "")
        label = RULE_TYPE_LABELS.get(rtype, "")
        if label in self.combo_rule_type["values"]:
            self.combo_rule_type.set(label)
            self._on_rule_type_change()

        if rtype in ("inline", "next_line"):
            keys = rule.get("keys", [""])
            self._pw_kw_entry.delete(0, tk.END)
            self._pw_kw_entry.insert(0, keys[0] if keys else "")
        elif rtype == "fixed_index":
            self._pw_idx_var.set(rule.get("index", 0))
        elif rtype == "speednet_positional":
            self._pw_sp_idx.set(rule.get("index", 0))
            self._pw_sp_pat.delete(0, tk.END)
            self._pw_sp_pat.insert(0, rule.get("pattern", ""))
        elif rtype == "regex":
            self._pw_re_pat.delete(0, tk.END)
            self._pw_re_pat.insert(0, rule.get("pattern", ""))
            self._pw_re_grp.set(rule.get("group", 1))
            self._pw_re_pick.set(rule.get("pick", "first"))
        elif rtype == "regex_combine":
            patterns = rule.get("patterns", ["", ""])
            self._pw_rc_p1.delete(0, tk.END)
            self._pw_rc_p1.insert(0, patterns[0] if len(patterns) > 0 else "")
            self._pw_rc_p2.delete(0, tk.END)
            self._pw_rc_p2.insert(0, patterns[1] if len(patterns) > 1 else "")
            self._pw_rc_fmt.delete(0, tk.END)
            self._pw_rc_fmt.insert(0, rule.get("format", "{0} / {1}"))

    def _copy_selected_pdf_line(self, event=None):
        selection = self.listbox_pdf_lines.curselection()
        if not selection or not self.pdf_lines:
            return
        idx = selection[0]
        if idx < len(self.pdf_lines):
            line_text = self.pdf_lines[idx]
            self.clipboard_clear()
            self.clipboard_append(line_text)
            self.lbl_rule_result.config(text=f"📋 Copied: '{line_text[:30]}...'", foreground="#2563EB")

    def _add_rule(self):
        if self.selected_profile_idx is None or not self.selected_column_name:
            messagebox.showwarning("Warning", "Select a column first.")
            return
        
        label = self.combo_rule_type.get()
        rtype = next((k for k, v in RULE_TYPE_LABELS.items() if v == label), None)
        if not rtype:
            messagebox.showerror("Error", "Select a rule type first.")
            return
            
        p = self.profiles[self.selected_profile_idx]
        rule_dict = {"type": rtype}

        try:
            if rtype in ("inline", "next_line"):
                kw = self._pw_kw_entry.get().strip()
                if not kw:
                    messagebox.showerror("Error", "Keyword / Label is required.")
                    return
                rule_dict["keys"] = [kw]
            elif rtype == "fixed_index":
                rule_dict["index"] = int(self._pw_idx_var.get())
            elif rtype == "speednet_positional":
                rule_dict["index"] = int(self._pw_sp_idx.get())
                rule_dict["pattern"] = self._pw_sp_pat.get().strip()
            elif rtype == "regex":
                pat = self._pw_re_pat.get().strip()
                if not pat:
                    messagebox.showerror("Error", "Regex pattern is required.")
                    return
                rule_dict["pattern"] = pat
                rule_dict["group"] = int(self._pw_re_grp.get())
                rule_dict["pick"] = self._pw_re_pick.get()
            elif rtype == "regex_combine":
                p1 = self._pw_rc_p1.get().strip()
                p2 = self._pw_rc_p2.get().strip()
                if not p1 or not p2:
                    messagebox.showerror("Error", "Both patterns are required for regex_combine.")
                    return
                rule_dict["patterns"] = [p1, p2]
                rule_dict["format"] = self._pw_rc_fmt.get().strip() or "{0} / {1}"
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return
                
        p["columns"][self.selected_column_name].append(rule_dict)
        self._load_rules_list()

    def _update_rule(self):
        selection = self.listbox_rules.curselection()
        if not selection or self.selected_profile_idx is None or not self.selected_column_name:
            messagebox.showwarning("Warning", "Select a rule from the list to update.")
            return
        
        label = self.combo_rule_type.get()
        rtype = next((k for k, v in RULE_TYPE_LABELS.items() if v == label), None)
        if not rtype:
            messagebox.showerror("Error", "Select a rule type first.")
            return
            
        p = self.profiles[self.selected_profile_idx]
        rule_dict = {"type": rtype}

        try:
            if rtype in ("inline", "next_line"):
                kw = self._pw_kw_entry.get().strip()
                if not kw:
                    messagebox.showerror("Error", "Keyword / Label is required.")
                    return
                rule_dict["keys"] = [kw]
            elif rtype == "fixed_index":
                rule_dict["index"] = int(self._pw_idx_var.get())
            elif rtype == "speednet_positional":
                rule_dict["index"] = int(self._pw_sp_idx.get())
                rule_dict["pattern"] = self._pw_sp_pat.get().strip()
            elif rtype == "regex":
                pat = self._pw_re_pat.get().strip()
                if not pat:
                    messagebox.showerror("Error", "Regex pattern is required.")
                    return
                rule_dict["pattern"] = pat
                rule_dict["group"] = int(self._pw_re_grp.get())
                rule_dict["pick"] = self._pw_re_pick.get()
            elif rtype == "regex_combine":
                p1 = self._pw_rc_p1.get().strip()
                p2 = self._pw_rc_p2.get().strip()
                if not p1 or not p2:
                    messagebox.showerror("Error", "Both patterns are required for regex_combine.")
                    return
                rule_dict["patterns"] = [p1, p2]
                rule_dict["format"] = self._pw_rc_fmt.get().strip() or "{0} / {1}"
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        idx = selection[0]
        p["columns"][self.selected_column_name][idx] = rule_dict
        self._load_rules_list()
        self.listbox_rules.selection_set(idx)
        self.lbl_rule_result.config(text=f"✓ Rule updated!", foreground="#059669")

    def _delete_rule(self):
        selection = self.listbox_rules.curselection()
        if not selection or self.selected_profile_idx is None or not self.selected_column_name:
            return
        
        p = self.profiles[self.selected_profile_idx]
        idx = selection[0]
        p["columns"][self.selected_column_name].pop(idx)
        self._load_rules_list()

    def _move_rule_up(self):
        selection = self.listbox_rules.curselection()
        if not selection or self.selected_profile_idx is None or not self.selected_column_name:
            return
        idx = selection[0]
        if idx == 0:
            return
        rules = self.profiles[self.selected_profile_idx]["columns"][self.selected_column_name]
        rules[idx], rules[idx - 1] = rules[idx - 1], rules[idx]
        self._load_rules_list()
        self.listbox_rules.selection_set(idx - 1)

    def _move_rule_down(self):
        selection = self.listbox_rules.curselection()
        if not selection or self.selected_profile_idx is None or not self.selected_column_name:
            return
        idx = selection[0]
        rules = self.profiles[self.selected_profile_idx]["columns"][self.selected_column_name]
        if idx >= len(rules) - 1:
            return
        rules[idx], rules[idx + 1] = rules[idx + 1], rules[idx]
        self._load_rules_list()
        self.listbox_rules.selection_set(idx + 1)

    def _test_selected_rule(self):
        """Test the currently selected rule against the loaded PDF and show the result inline."""
        selection = self.listbox_rules.curselection()
        if not selection or self.selected_profile_idx is None or not self.selected_column_name:
            self.lbl_rule_result.config(text="Select a rule first", foreground="#DC2626")
            return
        if not self.loaded_pdf_path:
            self.lbl_rule_result.config(text="Load a PDF first", foreground="#DC2626")
            return

        p = self.profiles[self.selected_profile_idx]
        rules = p["columns"].get(self.selected_column_name, [])
        rule = rules[selection[0]]

        try:
            import fitz
            with fitz.open(self.loaded_pdf_path) as doc:
                page0_text = doc[0].get_text("text")

            val = self._run_rule(rule, page0_text)
            if val:
                self.lbl_rule_result.config(text=f"✓ {repr(val)}", foreground="#059669")
            else:
                self.lbl_rule_result.config(text="⚠ no match", foreground="#D97706")
        except Exception as e:
            self.lbl_rule_result.config(text=f"Error: {e}", foreground="#DC2626")

    def _run_rule(self, rule: dict, text: str) -> str:
        """Execute a single rule dict against the given text and return the result string."""
        from .extractors import InlineExtractor, NextLineExtractor, PositionalExtractor, SpeedNetPositionalExtractor
        rtype = rule.get("type")
        val = ""
        if rtype == "inline":
            val = InlineExtractor(*rule.get("keys", [])).extract(text)
        elif rtype == "next_line":
            val = NextLineExtractor(*rule.get("keys", [])).extract(text)
        elif rtype == "fixed_index":
            val = PositionalExtractor(rule.get("index", 0)).extract(text)
        elif rtype == "speednet_positional":
            val = SpeedNetPositionalExtractor(rule.get("index", 0), rule.get("pattern", "")).extract(text)
        elif rtype == "regex":
            pattern = rule.get("pattern", "")
            group = rule.get("group", 1)
            pick_last = rule.get("pick", "") == "last"
            if pattern:
                matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
                if matches:
                    m = matches[-1] if pick_last else matches[0]
                    try:
                        val = m.group(group).strip()
                    except IndexError:
                        val = m.group(0).strip()
        elif rtype == "regex_combine":
            patterns = rule.get("patterns", [])
            fmt = rule.get("format", "{0}")
            captured = []
            for pat in patterns:
                m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
                captured.append(m.group(1).strip() if m else "")
            if any(captured):
                try:
                    val = fmt.format(*captured)
                except (IndexError, KeyError):
                    val = " / ".join(c for c in captured if c)
        elif rtype == "special":
            name = rule.get("name", "")
            if name == "strecke_extractor":
                from .extractors import StreckeExtractor
                val = StreckeExtractor().extract(text)
            elif name == "meterzahlen_extractor":
                from .extractors import MeterzahlenExtractor
                val = MeterzahlenExtractor().extract(text)
            elif name.startswith("hausanschluss_") and hasattr(self, "_pdf_doc_obj") and self._pdf_doc_obj:
                from .logic import PDFParserLogic
                dummy_logic = PDFParserLogic("", "", lambda *a: None, lambda *a: None, [])
                haus_data = dummy_logic._extract_hausanschluss(self._pdf_doc_obj, text)
                key_map = {
                    "hausanschluss_bbnd_id": "BBND ID",
                    "hausanschluss_anzahl_we": "Anzahl WE",
                    "hausanschluss_nvt": "Bezeichnung NVt",
                    "hausanschluss_date": "Datum Herstellung Hausanschluss",
                    "hausanschluss_rohrverband": "Bezeichnung Rohrverband",
                    "hausanschluss_farbe": "Farbe",
                    "hausanschluss_verbundrohr": "Verbundrohr",
                    "hausanschluss_bild1": "Bild 1",
                    "hausanschluss_bild2": "Bild 2",
                    "hausanschluss_bild3": "Bild 3",
                    "hausanschluss_bild4": "Bild 4",
                    "hausanschluss_signature": "Unterschrift"
                }
                val = str(haus_data.get(key_map.get(name, ""), ""))
        return val

    # ──────────────────────────────────────────────────────────────────────────
    # PDF Loading & Image Preview
    # ──────────────────────────────────────────────────────────────────────────
    def _refresh_folder_pdfs(self):
        folder = self.main_app.entry_folder.get().strip()
        pdf_files = []
        if folder and os.path.exists(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(".pdf"):
                    pdf_files.append(f)
        
        self.combo_pdfs.config(values=pdf_files)
        if pdf_files:
            self.combo_pdfs.current(0)
            self._on_combo_pdf_select(None)
        else:
            self.combo_pdfs.set("")
            self.listbox_pdf_lines.delete(0, tk.END)
            self.pdf_lines = []
            self.pdf_line_bboxes = []

    def _on_combo_pdf_select(self, event):
        val = self.combo_pdfs.get()
        if val:
            folder = self.main_app.entry_folder.get().strip()
            path = os.path.join(folder, val)
            self._load_pdf(path)

    def _browse_pdf(self):
        f = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if f:
            self._load_pdf(f)
            self.combo_pdfs.set(os.path.basename(f))

    def _load_pdf(self, path: str, page_idx: int = 0):
        self.loaded_pdf_path = path
        self.lbl_rule_result.config(text="")

        # Close any previously held doc safely
        if self._pdf_doc_obj is not None:
            try:
                self._pdf_doc_obj.close()
            except Exception:
                pass
            self._pdf_doc_obj = None
            self._pdf_page_obj = None

        try:
            import fitz
            doc = fitz.open(path)
            if len(doc) == 0:
                self.lbl_alert.config(text="PDF has 0 pages.", fg="#991B1B", bg="#FEE2E2")
                doc.close()
                return

            self._pdf_doc_obj = doc
            self.total_pages = len(doc)
            self.current_page_idx = max(0, min(page_idx, self.total_pages - 1))
            self._load_pdf_page(self.current_page_idx)

        except Exception as e:
            self.lbl_alert.config(text=f"Error reading PDF: {e}", fg="#991B1B", bg="#FEE2E2")

    def _prev_page(self):
        if self.current_page_idx > 0:
            self._load_pdf_page(self.current_page_idx - 1)

    def _next_page(self):
        if self.current_page_idx < self.total_pages - 1:
            self._load_pdf_page(self.current_page_idx + 1)

    def _load_pdf_page(self, page_idx: int):
        if not self._pdf_doc_obj:
            return
        
        doc = self._pdf_doc_obj
        if page_idx < 0 or page_idx >= len(doc):
            return

        self.current_page_idx = page_idx
        page = doc[page_idx]
        self._pdf_page_obj = page

        # Refresh text lines and bounding boxes for active page
        self.listbox_pdf_lines.delete(0, tk.END)
        self.pdf_lines = []
        self.pdf_line_bboxes = []

        import fitz
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                line_text = "".join(s.get("text", "") for s in spans).strip()
                if line_text:
                    bbox = fitz.Rect(line.get("bbox", (0, 0, 0, 0)))
                    self.pdf_lines.append(line_text)
                    self.pdf_line_bboxes.append(bbox)
                    self.listbox_pdf_lines.insert(tk.END, f"[{len(self.pdf_lines)-1}]: {line_text}")

        # Update alert label for this page
        has_annots = any(True for _ in page.annots())
        has_widgets = any(True for _ in page.widgets())
        if has_annots or has_widgets:
            feats = []
            if has_annots: feats.append("Annotations")
            if has_widgets: feats.append("Form Fields")
            self.lbl_alert.config(
                text=f"⚠️ Page {page_idx+1}/{self.total_pages} overrides: {', '.join(feats)}.",
                fg="#92400E", bg="#FEF3C7"
            )
        else:
            self.lbl_alert.config(text=f"✓ Page {page_idx+1}/{self.total_pages} has no manual overrides.", fg="#065F46", bg="#D1FAE5")

        # Update page label and navigation buttons
        self.lbl_page_num.config(text=f"Page {page_idx + 1} / {self.total_pages}")
        self.btn_prev_page.config(state="normal" if page_idx > 0 else "disabled")
        self.btn_next_page.config(state="normal" if page_idx < self.total_pages - 1 else "disabled")

        # Render active page image
        self._render_pdf_image(page)

    def _render_pdf_image(self, page, highlight_bbox=None):
        """Render the PDF page to the canvas. Optionally highlight a bounding box."""
        import fitz
        canvas = self.canvas_pdf
        canvas_w = max(canvas.winfo_width(), 400)

        # Choose scale so the page fits the canvas width
        scale = canvas_w / page.rect.width
        self._img_scale = scale
        mat = fitz.Matrix(scale, scale)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Highlight if requested
        if highlight_bbox:
            # Draw highlight directly on pixmap
            scaled_rect = fitz.Rect(
                highlight_bbox.x0 * scale,
                highlight_bbox.y0 * scale,
                highlight_bbox.x1 * scale,
                highlight_bbox.y1 * scale
            )
            # Draw using PIL for highlight
            try:
                from PIL import Image, ImageDraw
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                draw = ImageDraw.Draw(img, "RGBA")
                draw.rectangle(
                    [scaled_rect.x0, scaled_rect.y0, scaled_rect.x1, scaled_rect.y1],
                    fill=(255, 230, 0, 100), outline=(255, 140, 0, 200), width=2
                )
                import io
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                from PIL import ImageTk
                self._pdf_img_tk = ImageTk.PhotoImage(data=buf.read())
            except ImportError:
                from tkinter import PhotoImage
                self._pdf_img_tk = tk.PhotoImage(data=pix.tobytes("ppm"))
        else:
            try:
                from PIL import Image, ImageTk
                import io
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                self._pdf_img_tk = ImageTk.PhotoImage(data=buf.read())
            except ImportError:
                self._pdf_img_tk = tk.PhotoImage(data=pix.tobytes("ppm"))

        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=self._pdf_img_tk)
        canvas.config(scrollregion=(0, 0, pix.width, pix.height))

    def _on_pdf_canvas_click(self, event):
        """Click on the PDF image → find closest text line → select it."""
        if not self._pdf_page_obj or not self.pdf_line_bboxes:
            return

        # Adjust for scroll offset
        canvas = self.canvas_pdf
        cx = canvas.canvasx(event.x)
        cy = canvas.canvasy(event.y)

        # Convert to PDF coords
        scale = self._img_scale
        px = cx / scale
        py = cy / scale

        import fitz
        click_pt = fitz.Point(px, py)

        # Find the line whose bbox contains the click point (or is closest vertically)
        best_idx = None
        best_dist = float("inf")
        for i, bbox in enumerate(self.pdf_line_bboxes):
            if bbox.contains(click_pt):
                best_idx = i
                break
            # Distance from click to bbox center (y only for near-miss)
            cy_bbox = (bbox.y0 + bbox.y1) / 2
            dist = abs(py - cy_bbox)
            if dist < best_dist and abs(px - (bbox.x0 + bbox.x1) / 2) < 300:
                best_dist = dist
                best_idx = i

        if best_idx is not None:
            self.listbox_pdf_lines.selection_clear(0, tk.END)
            self.listbox_pdf_lines.selection_set(best_idx)
            self.listbox_pdf_lines.see(best_idx)
            self._on_line_select(None, forced_idx=best_idx)
            # Highlight bbox on image
            self._render_pdf_image(self._pdf_page_obj, highlight_bbox=self.pdf_line_bboxes[best_idx])

    def _on_line_select(self, event, forced_idx=None):
        if forced_idx is not None:
            idx = forced_idx
        else:
            selection = self.listbox_pdf_lines.curselection()
            if not selection or not self.pdf_lines:
                return
            idx = selection[0]

        if idx >= len(self.pdf_lines):
            return

        val = self.pdf_lines[idx]

        # Highlight on PDF canvas
        if self._pdf_page_obj and idx < len(self.pdf_line_bboxes):
            self._render_pdf_image(self._pdf_page_obj, highlight_bbox=self.pdf_line_bboxes[idx])

        # Auto-suggest rule type and params only when a column is selected
        if not self.selected_column_name:
            return

        # Heuristics for rule suggestion
        if ":" in val:
            parts = val.split(":", 1)
            self._set_rule_suggestion("inline", kw=parts[0].strip())
        elif idx > 0 and len(self.pdf_lines[idx - 1]) < 40:
            self._set_rule_suggestion("next_line", kw=self.pdf_lines[idx - 1].replace(":", "").strip())
        else:
            self._set_rule_suggestion("fixed_index", index=idx)

    def _set_rule_suggestion(self, rtype: str, kw: str = "", index: int = 0):
        """Pre-fill the rule type combo and param fields with a suggestion."""
        label = RULE_TYPE_LABELS.get(rtype, "")
        if label in self.combo_rule_type["values"]:
            self.combo_rule_type.set(label)
            self._on_rule_type_change()

        if rtype in ("inline", "next_line"):
            self._pw_kw_entry.delete(0, tk.END)
            self._pw_kw_entry.insert(0, kw)
        elif rtype == "fixed_index":
            self._pw_idx_var.set(index)

    # ──────────────────────────────────────────────────────────────────────────
    # Profile CRUD
    # ──────────────────────────────────────────────────────────────────────────
    def _add_profile(self):
        dlg = _SimpleInputDialog(self, title="New Profile", prompt="Enter profile name:")
        name = dlg.result
        if name:
            name = name.strip()
            if any(p["name"].lower() == name.lower() for p in self.profiles):
                messagebox.showerror("Error", "Profile name already exists.")
                return
            
            new_p = {
                "name": name,
                "trigger_keywords": [],
                "columns": {}
            }
            self.profiles.append(new_p)
            self._load_profiles_list()
            idx = len(self.profiles) - 1
            self.listbox_profiles.selection_set(idx)
            self.selected_profile_idx = idx
            self._on_profile_select(None)

    def _clone_profile(self):
        if self.selected_profile_idx is None:
            messagebox.showwarning("Warning", "Select a profile to clone.")
            return
        src = self.profiles[self.selected_profile_idx]
        name = src["name"] + " (Clone)"
        
        import copy
        new_p = copy.deepcopy(src)
        new_p["name"] = name
        
        self.profiles.append(new_p)
        self._load_profiles_list()
        idx = len(self.profiles) - 1
        self.listbox_profiles.selection_set(idx)
        self.selected_profile_idx = idx
        self._on_profile_select(None)

    def _delete_profile(self):
        if self.selected_profile_idx is None:
            return
        p = self.profiles[self.selected_profile_idx]
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{p['name']}'?"):
            self.profiles.pop(self.selected_profile_idx)
            self._load_profiles_list()

    # ──────────────────────────────────────────────────────────────────────────
    # Trigger helpers
    # ──────────────────────────────────────────────────────────────────────────
    def _set_trigger_from_pdf(self):
        selection = self.listbox_pdf_lines.curselection()
        if not selection or not self.pdf_lines:
            messagebox.showwarning("Warning", "Select a line from the PDF Text Lines view first.")
            return
        idx = selection[0]
        val = self.pdf_lines[idx]
        
        curr_trigs = [t.strip() for t in self.entry_trigger.get().split(",") if t.strip()]
        if val not in curr_trigs:
            curr_trigs.append(val)
        self.entry_trigger.delete(0, tk.END)
        self.entry_trigger.insert(0, ", ".join(curr_trigs))
        self._save_trigger_keywords()

    def _auto_detect_trigger(self):
        if not self.pdf_lines:
            return
        candidates = []
        for line in self.pdf_lines[:3]:
            clean = re.sub(r"\d+", "", line).strip()
            if len(clean) > 4:
                candidates.append(clean)
                break
        
        if candidates:
            curr_trigs = [t.strip() for t in self.entry_trigger.get().split(",") if t.strip()]
            for cand in candidates:
                if cand not in curr_trigs:
                    curr_trigs.append(cand)
            self.entry_trigger.delete(0, tk.END)
            self.entry_trigger.insert(0, ", ".join(curr_trigs))
            self._save_trigger_keywords()
            messagebox.showinfo("Success", f"Auto-detected trigger: '{candidates[0]}'")
        else:
            messagebox.showwarning("Warning", "Could not automatically isolate a trigger keyword.")

    def _save_trigger_keywords(self):
        if self.selected_profile_idx is None:
            return
        trigs = [t.strip() for t in self.entry_trigger.get().split(",") if t.strip()]
        self.profiles[self.selected_profile_idx]["trigger_keywords"] = trigs

    # ──────────────────────────────────────────────────────────────────────────
    # Full profile test
    # ──────────────────────────────────────────────────────────────────────────
    def _test_extraction(self):
        if not self.loaded_pdf_path or self.selected_profile_idx is None:
            messagebox.showwarning("Warning", "Please load a sample PDF and select a profile to test.")
            return
        
        self._save_trigger_keywords()
        
        try:
            import fitz
            with fitz.open(self.loaded_pdf_path) as doc:
                page0 = doc[0]
                page0_text = page0.get_text("text")
                
                p = self.profiles[self.selected_profile_idx]
                results = {}
                results["Protocol Type"] = p["name"]
                results["Has Annotations"] = any(True for _ in page0.annots())
                results["Has Form Fields"] = any(True for _ in page0.widgets())
                
                hausanschluss_cache = None
                
                for col_name, rules in p["columns"].items():
                    val = ""
                    for rule in rules:
                        rtype = rule.get("type")
                        if rtype == "special" and rule.get("name", "").startswith("hausanschluss_"):
                            if hausanschluss_cache is None:
                                dummy_logic = PDFParserLogic("", "", lambda *a: None, lambda *a: None, [])
                                hausanschluss_cache = dummy_logic._extract_hausanschluss(doc, page0_text)
                            key_map = {
                                "hausanschluss_bbnd_id": "BBND ID",
                                "hausanschluss_anzahl_we": "Anzahl WE",
                                "hausanschluss_nvt": "Bezeichnung NVt",
                                "hausanschluss_date": "Datum Herstellung Hausanschluss",
                                "hausanschluss_rohrverband": "Bezeichnung Rohrverband",
                                "hausanschluss_farbe": "Farbe",
                                "hausanschluss_verbundrohr": "Verbundrohr",
                                "hausanschluss_bild1": "Bild 1",
                                "hausanschluss_bild2": "Bild 2",
                                "hausanschluss_bild3": "Bild 3",
                                "hausanschluss_bild4": "Bild 4",
                                "hausanschluss_signature": "Unterschrift"
                            }
                            val = hausanschluss_cache.get(key_map.get(rule.get("name", ""), ""), "")
                        else:
                            val = self._run_rule(rule, page0_text)
                        if val:
                            break
                    results[col_name] = val

            # Normalize dates & splits
            if "Einblasdatum" in results:
                raw_date = results["Einblasdatum"]
                if raw_date and not re.search(r"\d{1,2}[.\-/: ]\d{1,2}[.\-/: ]\d{2,4}", raw_date):
                    date_match = re.search(r"(\d{1,2}[.\-/: ]\d{1,2}[.\-/: ]\d{2,4})\s+(\d{1,2}:\d{2}(?::\d{2})?)", page0_text)
                    raw_date = date_match.group(0) if date_match else ""
                dummy_logic = PDFParserLogic("", "", lambda *a: None, lambda *a: None, [])
                results["Einblasdatum"] = dummy_logic._normalize_date(raw_date)
                
            if "Streckenabschnitt" in results:
                sa_text = results["Streckenabschnitt"]
                start_val, ziel_val = "", ""
                if sa_text:
                    clean_text = sa_text.replace('_', ' ').strip()
                    parts = clean_text.split(' ', 1)
                    if len(parts) >= 1:
                        start_val = parts[0].upper()
                    if len(parts) > 1:
                        remainder = parts[1].strip()
                        prep_match = re.match(r'^(?:zu|in|nach|bis|an|richtung)\s+(.+)$', remainder, re.IGNORECASE)
                        ziel_val = prep_match.group(1).upper() if prep_match else remainder.upper()
                results["Start"] = start_val
                results["Ziel"] = ziel_val

            if "Baumaße:" in results:
                if "Baumaße:" in results["Baumaße:"]:
                    results["Baumaße:"] = results["Baumaße:"].replace("Baumaße:", "").strip()

            # Render results window
            test_win = tk.Toplevel(self)
            test_win.title("Test Extraction Results")
            test_win.geometry("520x500")
            test_win.configure(bg="#F3F4F6")
            
            ttk.Label(test_win, text=f"Profile: {p['name']}", style="Title.TLabel").pack(pady=10)
            
            text_area = tk.Text(test_win, font=("Segoe UI", 10), wrap="word", width=60, height=20)
            text_area.pack(padx=15, pady=10, fill="both", expand=True)
            
            for key, val in results.items():
                text_area.insert(tk.END, f"{key}:\n  => {repr(val)}\n\n")
            text_area.config(state="disabled")
            
            ttk.Button(test_win, text="Close", command=test_win.destroy, style="Secondary.TButton").pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error during test", f"An error occurred: {e}")

    # ──────────────────────────────────────────────────────────────────────────
    # Save & close
    # ──────────────────────────────────────────────────────────────────────────
    def _save_and_close(self):
        self._save_trigger_keywords()
        save_profiles(self.profiles)
        self.main_app.reload_column_categories()
        messagebox.showinfo("Success", "Profiles successfully applied and saved!")
        # Close doc handle before destroying window
        if self._pdf_doc_obj is not None:
            try:
                self._pdf_doc_obj.close()
            except Exception:
                pass
            self._pdf_doc_obj = None
        self.destroy()

    def destroy(self):
        if self._pdf_doc_obj:
            try:
                self._pdf_doc_obj.close()
            except Exception:
                pass
        super().destroy()


# ─────────────────────────────────────────────────────────────────────────────
# Simple input dialog (replaces broken filedialog.dialogs.SimpleDialog usage)
# ─────────────────────────────────────────────────────────────────────────────
class _SimpleInputDialog(tk.Toplevel):
    def __init__(self, parent, title="Input", prompt="Enter value:"):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg="#F3F4F6")

        ttk.Label(self, text=prompt, font=("Segoe UI", 10)).pack(padx=20, pady=(15, 5))
        self._entry = ttk.Entry(self, font=("Segoe UI", 10), width=32)
        self._entry.pack(padx=20, pady=5)
        self._entry.focus()

        btn_row = ttk.Frame(self)
        btn_row.pack(pady=12)
        ttk.Button(btn_row, text="OK", command=self._ok, style="Primary.TButton").pack(side="left", padx=5)
        ttk.Button(btn_row, text="Cancel", command=self.destroy, style="Secondary.TButton").pack(side="left", padx=5)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())

        self.wait_window(self)

    def _ok(self):
        self.result = self._entry.get()
        self.destroy()
