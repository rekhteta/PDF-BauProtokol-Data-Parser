import argparse
import sys
import os
import logging
import tkinter as tk

from pdf_parser import setup_logging, PDFParserLogic, PDFParserApp
from pdf_parser.config import get_column_categories

def run_cli(folder: str, output: str, columns: str):
    """Executes the extraction process via Command Line Interface (CLI)."""
    if not os.path.exists(folder):
        print(f"Error: Target folder '{folder}' does not exist.", file=sys.stderr)
        sys.exit(1)
        
    # Resolve columns
    if columns:
        selected_cols = []
        for c in columns.split(","):
            c_clean = c.strip()
            if c_clean and c_clean not in selected_cols:
                selected_cols.append(c_clean)
    else:
        # Default columns selection from config
        selected_cols = []
        for cat_cols in get_column_categories().values():
            for col, active in cat_cols.items():
                if active and col not in selected_cols:
                    selected_cols.append(col)
                    
    if not selected_cols:
        print("Error: No columns selected for output. Process aborted.", file=sys.stderr)
        sys.exit(1)

    print(f"Target folder:    {folder}")
    print(f"Output path:      {output}")
    print(f"Active columns:   {', '.join(selected_cols)}")
    print("-" * 50)

    exit_info = {"success": False, "msg": ""}

    def cli_progress(status_text, current, total):
        if total > 0:
            pct = (current / total) * 100
            sys.stdout.write(f"\rProgress: [{current}/{total}] {pct:.1f}% | {status_text}")
            sys.stdout.flush()
        else:
            print(f"Status: {status_text}")

    def cli_finish(success, msg, file_path):
        sys.stdout.write("\n")
        exit_info["success"] = success
        exit_info["msg"] = msg

    logic = PDFParserLogic(folder, output, cli_progress, cli_finish, selected_cols)
    logic.run()

    if exit_info["success"]:
        print("--------------------------------------------------")
        print(f"Success! Data exported to: {output}")
        sys.exit(0)
    else:
        print("--------------------------------------------------")
        print(f"Failed! Error: {exit_info['msg']}", file=sys.stderr)
        sys.exit(1)

def run_gui():
    """Launches the Tkinter Graphical User Interface (GUI)."""
    root = tk.Tk()
    app = PDFParserApp(root)
    root.mainloop()

def main():
    # Safeguard: ensure sys.stdout and sys.stderr are not None.
    # In windowed PyInstaller executables, they are None, causing print() to raise AttributeError.
    if sys.stdout is None:
        try:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        except Exception:
            pass
    if sys.stderr is None:
        try:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")
        except Exception:
            pass

    # If compiled as a windowed application (--noconsole) but run in CLI mode,
    # attach to the parent cmd/powershell process console to enable stdout/stderr printing.
    if "--cli" in sys.argv and getattr(sys, 'frozen', False):
        is_redirected = False
        if sys.stdout is not None:
            try:
                is_redirected = not sys.stdout.isatty()
            except Exception:
                pass
        
        if not is_redirected and sys.platform.startswith('win'):
            import ctypes
            # AttachConsole(-1) links to parent process console
            if ctypes.windll.kernel32.AttachConsole(-1):
                try:
                    sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="backslashreplace")
                    sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="backslashreplace")
                    # Clear stdout buffer with a newline to separate from shell prompt
                    print()
                except Exception:
                    pass

    # Setup logger channels (info and error log files + console)
    setup_logging()
    
    parser = argparse.ArgumentParser(description="Multi-Protocol PDF Parser Suite - Extract details from PDF protocols to Excel.")
    parser.add_argument("--cli", action="store_true", help="Run in Command Line Interface mode (non-GUI).")
    parser.add_argument("-f", "--folder", type=str, help="Folder containing PDF files (required in CLI mode).")
    parser.add_argument("-o", "--output", type=str, help="Excel output file path (required in CLI mode).")
    parser.add_argument("-c", "--columns", type=str, help="Comma-separated columns to include (optional in CLI mode).")
    
    args = parser.parse_args()
    
    if args.cli:
        if not args.folder or not args.output:
            parser.error("CLI mode (--cli) requires folder path (-f/--folder) and output file path (-o/--output).")
        run_cli(args.folder, args.output, args.columns)
    else:
        run_gui()

if __name__ == "__main__":
    main()
