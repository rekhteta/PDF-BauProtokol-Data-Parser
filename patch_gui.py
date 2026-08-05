import os
import locale
import chardet

def get_file_encoding(filepath):
    with open(filepath, 'rb') as f:
        rawdata = f.read()
    return chardet.detect(rawdata)['encoding']

def patch_gui():
    filepath = 'p:/Alex Berichten/PDF_Parser/pdf_parser/gui.py'
    try:
        import chardet
        enc = get_file_encoding(filepath)
    except:
        enc = 'mbcs'
    
    print(f"Detected encoding: {enc}")
    
    with open(filepath, 'r', encoding=enc, errors='replace') as f:
        content = f.read()
    
    # 1. Patch update_progress
    old_update = """    def update_progress(self, status_text: str, current: int, total: int):
        def _update():
            self.lbl_status.config(text=status_text)
            if total > 0:
                self.progress_var.set((current / total) * 100)
        self.root.after(0, _update)"""
    
    new_update = """    def update_progress(self, status_text: str, current: int, total: int):
        def _update():
            if total > 0:
                percent = int((current / total) * 100)
                full_status = f"{status_text} ({percent}%)"
                self.progress_var.set((current / total) * 100)
            else:
                full_status = status_text
            self.lbl_status.config(text=full_status)
        self.root.after(0, _update)"""
    
    if old_update in content:
        content = content.replace(old_update, new_update)
        print("Patched update_progress")
    
    # 2. Add _create_sector_title
    old_build_ui_call = """        self._build_ui()
        self._load_profiles_list()"""
        
    new_build_ui_call = """        self._build_ui()
        self._load_profiles_list()

    def _create_sector_title(self, parent, text: str):
        import tkinter as tk
        title_var = tk.StringVar(value=text)
        entry = tk.Entry(parent, textvariable=title_var, state="readonly",
                         readonlybackground="#F3F4F6", relief="flat", bd=0,
                         font=("Segoe UI", 9, "bold"), fg="#1F2937")
        entry.pack(anchor="w", padx=5, pady=(2, 5))
        return entry"""
    
    if old_build_ui_call in content:
        content = content.replace(old_build_ui_call, new_build_ui_call)
        print("Patched _build_ui_call")
    
    # 3. Patch LabelFrames
    replacements = [
        ('left_frame = ttk.LabelFrame(paned, text=" Profiles ")', 
         'left_frame = ttk.LabelFrame(paned, text="")\n        self._create_sector_title(left_frame, "Profiles")'),
         
        ('center_frame = ttk.LabelFrame(paned, text=" Columns Configuration ")',
         'center_frame = ttk.LabelFrame(paned, text="")\n        self._create_sector_title(center_frame, "Columns Configuration")'),
         
        ('right_frame = ttk.LabelFrame(paned, text=" Layout Calibration & Rules ")',
         'right_frame = ttk.LabelFrame(paned, text="")\n        self._create_sector_title(right_frame, "Layout Calibration & Rules")'),
         
        ('img_frame = ttk.LabelFrame(calib_left, text=" PDF Page Preview (click to select line) ")',
         'img_frame = ttk.LabelFrame(calib_left, text="")\n        self._create_sector_title(img_frame, "PDF Page Preview (click to select line)")'),
         
        ('lines_frame = ttk.LabelFrame(calib_right, text=" PDF Text Lines (click to auto-suggest rule) ")',
         'lines_frame = ttk.LabelFrame(calib_right, text="")\n        self._create_sector_title(lines_frame, "PDF Text Lines (click to auto-suggest rule)")'),
         
        ('trigger_frame = ttk.LabelFrame(calib_right, text=" Trigger Keywords ")',
         'trigger_frame = ttk.LabelFrame(calib_right, text="")\n        self._create_sector_title(trigger_frame, "Trigger Keywords")'),
         
        ('rules_frame = ttk.LabelFrame(calib_right, text=" Extraction Rules for selected Column ")',
         'rules_frame = ttk.LabelFrame(calib_right, text="")\n        self._create_sector_title(rules_frame, "Extraction Rules for selected Column")'),
         
        ('param_outer = ttk.LabelFrame(rules_frame, text=" Add / Edit Rule ")',
         'param_outer = ttk.LabelFrame(rules_frame, text="")\n        self._create_sector_title(param_outer, "Add / Edit Rule")')
    ]
    
    for old_s, new_s in replacements:
        if old_s in content:
            content = content.replace(old_s, new_s)
            print(f"Patched frame: {old_s.split('=')[0].strip()}")
        
    # 4. Update _run_rule to handle hausanschluss special rules
    old_special = """        elif rtype == "special":
            name = rule.get("name", "")
            if name == "strecke_extractor":
                from .extractors import StreckeExtractor
                val = StreckeExtractor().extract(text)
            elif name == "meterzahlen_extractor":
                from .extractors import MeterzahlenExtractor
                val = MeterzahlenExtractor().extract(text)
        return val"""
        
    new_special = """        elif rtype == "special":
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
        return val"""
        
    if old_special in content:
        content = content.replace(old_special, new_special)
        print("Patched _run_rule")
    
    with open(filepath, 'w', encoding=enc, errors='replace') as f:
        f.write(content)

    print("GUI patched successfully.")

if __name__ == '__main__':
    patch_gui()
