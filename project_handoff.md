# PDF-BauProtokol-Data-Parser: Project Summary & Handoff

This document serves as a comprehensive summary of the project architecture, recent feature additions, and instructions for continuing development in future chat sessions.

## 1. Project Purpose
A desktop application built in Python that automatically parses and extracts tabular and layout-specific data from various PDF construction protocols (e.g., SpeedNet, Einblas, Standortsicherung) and aggregates them into a structured Excel report. 

It features an interactive **Calibration GUI** that allows users to write, test, and save extraction rules (Regex, Inline, Positional, etc.) against visual PDF renders.

## 2. Core Architecture
- **`main.py`**: The entry point. Handles parsing CLI arguments and launching the GUI.
- **`pdf_parser/gui.py`**: The Tkinter-based interface. Features a 3-panel PanedWindow:
  - **Profiles**: List of PDF layout types (e.g., Einblas).
  - **Columns**: Target data points (e.g., Einblasdatum, Strecke).
  - **Calibration**: A two-column setup featuring a visual `fitz` (PyMuPDF) canvas with multi-page support, and a rule editor for testing extractions.
- **`pdf_parser/logic.py`**: The execution engine. Iterates over folders using `concurrent.futures.ThreadPoolExecutor`, applies active rules via `extractors.py`, gathers file metadata, handles specialized rules (like `Hausanschluss`), and outputs a formatted `.xlsx` via `pandas`.
- **`pdf_parser/extractors.py`**: Contains the modular extraction strategies:
  - `InlineExtractor`: Matches labels separated by colons or spaces.
  - `NextLineExtractor`: Finds a label and returns the line beneath it.
  - `RegexExtractor` & `RegexCombineExtractor`: Applies regex logic to grab groups.
  - `SpeedNetPositionalExtractor` & `PositionalExtractor`: Captures data based on split indexes.
- **`pdf_parser/config.py`**: Manages reading and writing `pdf_profiles.json`.
- **`build_exe.py`**: An automated, highly-optimized PyInstaller script that excludes heavy Anaconda dependencies (`scipy`, `sklearn`, `PyQt5`, etc.) to produce a small, fast-building `.exe`.

## 3. Recent Features Implemented
1. **Multi-Page Support**: Users can navigate through multi-page PDFs in the Calibration window. Bounding boxes and text lines automatically reload per page.
2. **Visual Zone Highlighting**: Clicking special visual fields (like `Hausanschluss Bild 1-4`) visually highlights the search zone on the PDF preview canvas.
3. **Advanced Inline Matching**: The `InlineExtractor` now supports both colon-separated (`Label: Value`) and space-separated (`Label Value`) configurations while resisting false positive matches on hyphenated words (e.g., `Rohr-Temperatur`).
4. **File Metadata Extraction**: `logic.py` now leverages `os.path` and native Windows Security APIs / PowerShell to extract `File Size`, `Created Date`, `Last Modify Date`, and `Created By` (File Owner), appending them to the Excel report.
5. **In-Place UI Rule Editing**: Selectable sector headers (`tk.Entry` disguised as labels for easy copying) and in-place rule editing directly populates configuration fields for immediate testing.

## 4. How to Resume Work in a New Chat
When starting a new conversation with an AI assistant, you should provide:
1. **This Summary Document**: Share this markdown file so the AI understands the stack (`Tkinter`, `fitz`, `pandas`), structure, and recent improvements.
2. **The Goal/Request**: Clearly state what needs to be added (e.g., "Add a new specialized extractor for X").
3. **Relevant Files**: Depending on the request, mention which files are relevant:
   - *UI Changes*: Mention `pdf_parser/gui.py`
   - *Extraction Logic/Excel Output*: Mention `pdf_parser/logic.py`
   - *Rule Matching*: Mention `pdf_parser/extractors.py`
   - *Configuration*: Mention `pdf_profiles.json` and `pdf_parser/config.py`

## 5. Potential Next Steps / Future Work
- **Hausanschluss Enhancements**: The visual bounding box checks (using numpy variance) work, but may require threshold tweaking depending on scanner qualities.
- **Custom Scripting**: Allowing users to write lightweight python scripts directly in the GUI instead of just Regex.
- **GUI Theming**: Implementing a modern Tkinter theme (like `sv_ttk` or `CustomTkinter`) for a more premium look.
