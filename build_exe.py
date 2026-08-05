import os
import sys
import subprocess

def build_executable():
    """Checks for PyInstaller and builds the single-file executable."""
    print("=" * 60)
    print("Portable Executable Builder for PDF Parser Suite")
    print("=" * 60)
    
    # 1. Verify/Install PyInstaller
    try:
        import PyInstaller
        print(f"[*] PyInstaller is already installed. Version: {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller is not installed. Attempting installation...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("[*] PyInstaller installed successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to install PyInstaller: {e}", file=sys.stderr)
            print("Please run 'pip install pyinstaller' manually and rerun this script.", file=sys.stderr)
            sys.exit(1)

    # 2. Run PyInstaller
    dist_name = "PDFParserSuite"
    entry_point = "main.py"
    
    # Options:
    # --onefile: single portable executable file
    # --noconsole: hide console window when launching GUI
    # --clean: clean PyInstaller cache before building
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        f"--name={dist_name}",
        "--clean",
        "--exclude-module=scipy",
        "--exclude-module=sklearn",
        "--exclude-module=PyQt5",
        "--exclude-module=bokeh",
        "--exclude-module=plotly",
        "--exclude-module=skimage",
        "--exclude-module=jupyterlab",
        "--exclude-module=notebook",
        "--exclude-module=altair",
        "--exclude-module=statsmodels",
        "--exclude-module=astropy",
        "--exclude-module=distributed",
        "--exclude-module=xarray",
        entry_point
    ]
    
    print(f"[*] Running compilation command:\n    {' '.join(cmd)}")
    print("[*] This process might take 1-3 minutes depending on your system.")
    print("-" * 60)
    
    try:
        subprocess.check_call(cmd)
        print("-" * 60)
        print("[*] Build completed successfully!")
        
        exe_path = os.path.join("dist", f"{dist_name}.exe")
        if os.path.exists(exe_path):
            abs_path = os.path.abspath(exe_path)
            print(f"[SUCCESS] Standalone executable created at:\n          {abs_path}")
        else:
            print("[WARNING] Build reported success, but the executable file was not found in 'dist' directory.")
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] PyInstaller compilation failed with code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error during build: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    build_executable()
