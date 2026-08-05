import fitz
import os
import logging
import re
from pdf_parser.config import load_profiles

# Mock callbacks
def progress(msg, current, total):
    pass

def finish(success, msg, path):
    pass

# Setup basic logging
logging.basicConfig(level=logging.ERROR)

def run_test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profiles = load_profiles()

    test_configs = [
        {
            "dir": "Samples/Samples_Einblas_Protokoll",
            "profile_name": "Einblas",
            "fields": ["Strecke", "Faserzahl", "Farbe-Kennung", "Rohr or Rohrtyp"]
        },
        {
            "dir": "Samples/Samples_Standortsicherung_Protokoll",
            "profile_name": "Standortsicherung",
            "fields": ["Sch.-Nr.", "Gemeinde", "Lagebeschreibung", "Baumaße:"]
        }
    ]

    for config in test_configs:
        samples_dir = os.path.join(base_dir, config["dir"])
        if not os.path.exists(samples_dir):
            print(f"Skipping {config['profile_name']}: directory not found")
            continue

        print(f"\n--- Testing {config['profile_name']} (Dynamic Profile) ---")
        files = [f for f in os.listdir(samples_dir) if f.lower().endswith('.pdf')]
        
        # Find the matching profile dict
        profile = next((p for p in profiles if p["name"] == config["profile_name"]), None)
        if not profile:
            print(f"Error: Profile '{config['profile_name']}' not found in pdf_profiles.json!")
            continue

        header = f"{'File Name':<40} | " + " | ".join([f"{f:<15}" for f in config["fields"]])
        print(header)
        print("-" * len(header))

        for f in sorted(files):
            path = os.path.join(samples_dir, f)
            try:
                with fitz.open(path) as doc:
                    page0 = doc[0]
                    text0 = page0.get_text("text")
                    
                    # Extract fields using the dynamic rules from the profile
                    data = {}
                    for col_name in config["fields"]:
                        rules = profile["columns"].get(col_name, [])
                        val = ""
                        for rule in rules:
                            rtype = rule.get("type")
                            if rtype == "inline":
                                from pdf_parser.extractors import InlineExtractor
                                val = InlineExtractor(*rule.get("keys", [])).extract(text0)
                            elif rtype == "next_line":
                                from pdf_parser.extractors import NextLineExtractor
                                val = NextLineExtractor(*rule.get("keys", [])).extract(text0)
                            elif rtype == "fixed_index":
                                from pdf_parser.extractors import PositionalExtractor
                                val = PositionalExtractor(rule.get("index", 0)).extract(text0)
                            elif rtype == "speednet_positional":
                                from pdf_parser.extractors import SpeedNetPositionalExtractor
                                val = SpeedNetPositionalExtractor(rule.get("index", 0), rule.get("pattern", "")).extract(text0)
                            elif rtype == "special":
                                name = rule.get("name")
                                if name == "strecke_extractor":
                                    from pdf_parser.extractors import StreckeExtractor
                                    val = StreckeExtractor().extract(text0)
                                elif name == "meterzahlen_extractor":
                                    from pdf_parser.extractors import MeterzahlenExtractor
                                    val = MeterzahlenExtractor().extract(text0)
                            if val:
                                break
                        data[col_name] = val
                    
                    row = f"{f[:38]:<40} | " + " | ".join([f"{str(data.get(field, '')): <15}" for field in config["fields"]])
                    print(row)
            except Exception as e:
                print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    run_test()
