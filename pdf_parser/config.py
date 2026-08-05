import os
import sys
import json
from typing import Dict, List, Any

# General metadata columns present in all reports
DEFAULT_COLS_GENERAL = {
    "File Name": True,
    "Protocol Type": True,
    "File Size": True,
    "Created Date": True,
    "Created By": True,
    "Last Modify Date": True,
    "Folder Name": True,
    "Folder Path": False,
    "Full Path": False,
    "Has Annotations": True,
    "Has Form Fields": True
}

def get_profiles_path() -> str:
    """Returns the path to pdf_profiles.json next to the executable or script."""
    exe_dir = os.path.dirname(os.path.abspath(sys.argv[0] if sys.argv and sys.argv[0] else __file__))
    return os.path.join(exe_dir, "pdf_profiles.json")

def get_default_profiles() -> List[Dict[str, Any]]:
    """Returns the default profile list representing the 3 built-in layouts."""
    return [
        {
            "name": "SpeedNet",
            "trigger_keywords": ["SpeedNet"],
            "columns": {
                "Einblasdatum": [
                    { "type": "inline", "keys": ["Einblasdatum", "Datum"] },
                    { "type": "next_line", "keys": ["Datum, Startzeit"] }
                ],
                "Firma": [
                    { "type": "next_line", "keys": ["Firma"] },
                    { "type": "inline", "keys": ["Firma"] }
                ],
                "Streckenabschnitt": [
                    { "type": "next_line", "keys": ["Streckenabschnitt / NVt", "Streckenabschnitt/NVt"] },
                    { "type": "inline", "keys": ["Streckenabschnitt"] }
                ],
                "Strecke": [
                    { "type": "regex", "pattern": "Strecke:\\s*([\\d,.]+)", "group": 1 },
                    { "type": "regex", "pattern": "Max\\.Strecke\\(m\\)[:\\s]*\\n?(\\d+)", "group": 1 },
                    { "type": "regex", "pattern": "(?<![a-zA-Z0-9])(\\d{2,5})\\s*m\\b", "group": 1, "pick": "last" },
                    { "type": "regex", "pattern": "Entfernung:\\s*(\\d+)", "group": 1 }
                ],
                "Faserzahl": [
                    { "type": "speednet_positional", "index": 7, "pattern": "Fasern" },
                    { "type": "next_line", "keys": ["Faserzahl"] },
                    { "type": "inline", "keys": ["Faserzahl", "Fasern"] }
                ],
                "Rohrverband": [
                    { "type": "speednet_positional", "index": 4, "pattern": "Rohr" },
                    { "type": "next_line", "keys": ["Rohrverband"] },
                    { "type": "inline", "keys": ["Rohrverband"] }
                ],
                "Rohr or Rohrtyp": [
                    { "type": "speednet_positional", "index": 6, "pattern": "Rohr" },
                    { "type": "next_line", "keys": ["Rohr", "Rohrtyp", "RohrTyp"] },
                    { "type": "inline", "keys": ["Rohr", "Rohrtyp", "RohrTyp"] }
                ],
                "Farbe-Kennung": [
                    { "type": "speednet_positional", "index": 9, "pattern": "Farbe" },
                    { "type": "next_line", "keys": ["Farbe-Kennung", "Farbe/Kennung"] },
                    { "type": "inline", "keys": ["Farbe-Kennung", "Farbe/Kennung"] }
                ],
                "Meterzahlen": [
                    { "type": "regex", "pattern": "Meterzahlen[:\\s]*\\n?\\s*([0-9/ ]+)", "group": 1 },
                    { "type": "regex_combine", "patterns": ["Start-?Zahl\\(m\\)[:\\s]*\\n?(\\d+)", "Ende-?Zahl\\(m\\)[:\\s]*\\n?(\\d+)"], "format": "{0} / {1}" },
                    { "type": "regex_combine", "patterns": ["Start:\\s*(\\d+)\\s*(?:m\\b)?", "Ende:\\s*(\\d+)"], "format": "{0} / {1}" }
                ]
            }
        },
        {
            "name": "Einblas",
            "trigger_keywords": ["Einblas"],
            "columns": {
                "Einblasdatum": [
                    { "type": "inline", "keys": ["Einblasdatum", "Datum"] },
                    { "type": "next_line", "keys": ["Datum, Startzeit"] }
                ],
                "Firma": [
                    { "type": "next_line", "keys": ["Firma"] },
                    { "type": "inline", "keys": ["Firma"] }
                ],
                "Streckenabschnitt": [
                    { "type": "next_line", "keys": ["Streckenabschnitt / NVt", "Streckenabschnitt/NVt"] },
                    { "type": "inline", "keys": ["Streckenabschnitt"] }
                ],
                "Strecke": [
                    { "type": "regex", "pattern": "Strecke:\\s*([\\d,.]+)", "group": 1 },
                    { "type": "regex", "pattern": "Max\\.Strecke\\(m\\)[:\\s]*\\n?(\\d+)", "group": 1 },
                    { "type": "regex", "pattern": "(?<![a-zA-Z0-9])(\\d{2,5})\\s*m\\b", "group": 1, "pick": "last" },
                    { "type": "regex", "pattern": "Entfernung:\\s*(\\d+)", "group": 1 }
                ],
                "Faserzahl": [
                    { "type": "next_line", "keys": ["Faserzahl"] },
                    { "type": "inline", "keys": ["Faserzahl", "Fasern"] }
                ],
                "Rohrverband": [
                    { "type": "next_line", "keys": ["Rohrverband"] },
                    { "type": "inline", "keys": ["Rohrverband"] }
                ],
                "Rohr or Rohrtyp": [
                    { "type": "next_line", "keys": ["Rohr", "Rohrtyp", "RohrTyp"] },
                    { "type": "inline", "keys": ["Rohr", "Rohrtyp", "RohrTyp"] }
                ],
                "Farbe-Kennung": [
                    { "type": "next_line", "keys": ["Farbe-Kennung", "Farbe/Kennung"] },
                    { "type": "inline", "keys": ["Farbe-Kennung", "Farbe/Kennung"] }
                ],
                "Meterzahlen": [
                    { "type": "regex", "pattern": "Meterzahlen[:\\s]*\\n?\\s*([0-9/ ]+)", "group": 1 },
                    { "type": "regex_combine", "patterns": ["Start-?Zahl\\(m\\)[:\\s]*\\n?(\\d+)", "Ende-?Zahl\\(m\\)[:\\s]*\\n?(\\d+)"], "format": "{0} / {1}" },
                    { "type": "regex_combine", "patterns": ["Start:\\s*(\\d+)\\s*(?:m\\b)?", "Ende:\\s*(\\d+)"], "format": "{0} / {1}" }
                ]
            }
        },
        {
            "name": "Hausanschluss",
            "trigger_keywords": ["Hausanschlussprotokoll", "BBND ID"],
            "columns": {
                "BBND ID": [{ "type": "special", "name": "hausanschluss_bbnd_id" }],
                "Anzahl WE": [{ "type": "special", "name": "hausanschluss_anzahl_we" }],
                "Bezeichnung NVt": [{ "type": "special", "name": "hausanschluss_nvt" }],
                "Datum Herstellung Hausanschluss": [{ "type": "special", "name": "hausanschluss_date" }],
                "Bezeichnung Rohrverband": [{ "type": "special", "name": "hausanschluss_rohrverband" }],
                "Farbe": [{ "type": "special", "name": "hausanschluss_farbe" }],
                "Verbundrohr": [{ "type": "special", "name": "hausanschluss_verbundrohr" }],
                "Bild 1": [{ "type": "special", "name": "hausanschluss_bild1" }],
                "Bild 2": [{ "type": "special", "name": "hausanschluss_bild2" }],
                "Bild 3": [{ "type": "special", "name": "hausanschluss_bild3" }],
                "Bild 4": [{ "type": "special", "name": "hausanschluss_bild4" }],
                "Unterschrift": [{ "type": "special", "name": "hausanschluss_signature" }]
            }
        },
        {
            "name": "Standortsicherung",
            "trigger_keywords": ["Baumaße:", "Sch.-"],
            "columns": {
                "Sch.-Nr.": [
                    { "type": "inline", "keys": ["Sch.-Nr.", "Sch.-Nr"] },
                    { "type": "fixed_index", "index": 10 }
                ],
                "Gemeinde": [
                    { "type": "fixed_index", "index": 1 }
                ],
                "Lagebeschreibung": [
                    { "type": "fixed_index", "index": 9 }
                ],
                "Baumaße:": [
                    { "type": "inline", "keys": ["Baumaße", "Baumaße:"] }
                ]
            }
        }
    ]

def load_profiles() -> List[Dict[str, Any]]:
    """Loads profiles from pdf_profiles.json, creating it with defaults if missing."""
    path = get_profiles_path()
    if not os.path.exists(path):
        try:
            defaults = get_default_profiles()
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"profiles": defaults}, f, indent=4, ensure_ascii=False)
            return defaults
        except Exception as e:
            print(f"Error writing default profiles to {path}: {e}")
            return get_default_profiles()
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("profiles", [])
        except Exception as e:
            print(f"Error reading profiles from {path}: {e}")
            return get_default_profiles()

def save_profiles(profiles: List[Dict[str, Any]]):
    """Saves profiles list back to pdf_profiles.json."""
    path = get_profiles_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"profiles": profiles}, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving profiles to {path}: {e}")

def get_column_categories() -> Dict[str, Dict[str, bool]]:
    """Generates the COLUMN_CATEGORIES dict dynamically from default general cols and profiles."""
    categories = {
        "General Info": DEFAULT_COLS_GENERAL
    }
    
    profiles = load_profiles()
    for p in profiles:
        cat_name = p["name"]
        columns_dict = {}
        for col_name in p["columns"].keys():
            columns_dict[col_name] = True
        categories[cat_name] = columns_dict
        
    return categories
