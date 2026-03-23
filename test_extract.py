import fitz
import json

file_path = r"P:\Alex Berichten\PDF_Parser\Samples_Einblas_Protokoll\LOS29_MFG61_25_02_2026_09_09_23_G6103_DyckerhoffstraÃ_e 3_2502263346.pdf"

def analyze_pdf(path):
    try:
        doc = fitz.open(path)
        page0 = doc[0]
        print("--- RAW TEXT ---")
        print(page0.get_text("text"))
    except Exception as e:
        print(f"Error: {e}")

analyze_pdf(file_path)
