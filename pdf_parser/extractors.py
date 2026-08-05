import re
from typing import Dict, List, Any

class FieldExtractor:
    """Base class for PDF field extraction."""
    def extract(self, text: str) -> str:
        raise NotImplementedError

class NextLineExtractor(FieldExtractor):
    """Value is on the next non-empty line after the label."""
    def __init__(self, *label_variants: str):
        self.variants = label_variants
        self.regexes = [
            re.compile(rf"\b{re.escape(lbl)}\b[:\s]*\n\s*([^\n:]+)", re.IGNORECASE)
            for lbl in label_variants
        ]

    def extract(self, text: str) -> str:
        for regex in self.regexes:
            match = regex.search(text)
            if match:
                val = match.group(1).strip()
                # Label Guard: reject if it looks like a label (is in our known keywords)
                lower_val = val.lower().rstrip(':')
                keywords = ["bezeichnung", "hersteller", "kabel", "rohr", "meterzahlen", "gleitmittel", "kompressor", "wetter", "ort", "bemerkungen", "firma", "einbläser", "faserzahl", "rohrtyp", "farbe/kennung", "farbe-kennung"]
                if lower_val in keywords:
                    continue
                return val
        return ""

class InlineExtractor(FieldExtractor):
    """Value is on the same line as the label."""
    def __init__(self, *label_variants: str):
        self.regexes = [
            re.compile(rf"\b{re.escape(lbl)}\b\s*(?::\s*|\s+)(\S[^\n]*)", re.IGNORECASE)
            for lbl in label_variants
        ]

    def extract(self, text: str) -> str:
        for regex in self.regexes:
            match = regex.search(text)
            if match:
                return match.group(1).strip()
        return ""

class FallbackExtractor(FieldExtractor):
    """Tries multiple extractors and returns the first non-empty result."""
    def __init__(self, *extractors: FieldExtractor):
        self.extractors = extractors

    def extract(self, text: str) -> str:
        for ex in self.extractors:
            val = ex.extract(text)
            if val:
                return val
        return ""

class SpeedNetPositionalExtractor(FieldExtractor):
    """Special handling for SpeedNet layout where values are in a block at the top."""
    def __init__(self, index: int, label_pattern: str):
        self.index = index
        self.label_pattern = label_pattern

    def extract(self, text: str) -> str:
        if "SpeedNet" not in text:
            return ""
        # The block is usually before "Einblas - Protokoll"
        parts = re.split(r"Einblas\s*-\s*Protokoll", text, flags=re.IGNORECASE)
        if len(parts) < 1:
            return ""
        block_lines = [line.strip() for line in parts[0].split("\n") if line.strip()]
        if len(block_lines) > self.index:
            val = block_lines[self.index]
            # Simple check if this isn't a known label
            if ":" not in val and not re.search(self.label_pattern, val, re.IGNORECASE):
                return val
        return ""

class MeterzahlenExtractor(FieldExtractor):
    """Handles various Meterzahlen formats."""
    def extract(self, text: str) -> str:
        # Standard: Meterzahlen:\n6067 / 4561
        m1 = re.search(r"Meterzahlen[:\s]*\n?\s*([0-9/ ]+)", text, re.IGNORECASE)
        if m1 and m1.group(1).strip() and "/" in m1.group(1):
            return m1.group(1).strip()
        
        # Start/End labels: Start-Zahl(m) 2415
        ms = re.search(r"Start-?Zahl\(m\)[:\s]*\n?(\d+)", text, re.IGNORECASE)
        me = re.search(r"Ende-?Zahl\(m\)[:\s]*\n?(\d+)", text, re.IGNORECASE)
        if ms and me:
            return f"{ms.group(1)} / {me.group(1)}"
            
        # Gabocom alt: Start: 3108 | Ende: 2662
        m_alt = re.search(r"Start:\s*(\d+)\s*(?:m\b)?\s*(?:\||[\n\s])\s*Ende:\s*(\d+)", text, re.IGNORECASE)
        if m_alt:
            return f"{m_alt.group(1)} / {m_alt.group(2)}"
            
        return ""

class StreckeExtractor(FieldExtractor):
    """Prioritizes reliable summary Strecke sources."""
    def extract(self, text: str) -> str:
        # P1: Explicit summary label "Strecke: 459"
        m = re.search(r"(?:^|\n)Strecke:\s*([\d,.]+)", text, re.IGNORECASE | re.MULTILINE)
        if m: return m.group(1).replace(",", ".")
        # P2: Max.Strecke(m)
        m = re.search(r"Max\.Strecke\(m\)[:\s]*\n?(\d+)", text, re.IGNORECASE)
        if m: return m.group(1)
        # P3: Standalone "NNNm" marker (often in Gabocom footer)
        # We look for a 3-5 digit number followed by 'm' that is NOT adjacent to other letters
        matches = re.findall(r"(?<![a-zA-Z0-9])(\d{2,5})\s*m\b", text)
        if matches: 
            # In Gabocom layouts, the actual distance is often the LAST 'm' match on the summary page
            return matches[-1]
        # P4: Entfernung label (last resort as it's often misaligned with Metrierung)
        m = re.search(r"Entfernung:\s*(\d+)", text, re.IGNORECASE)
        if m: return m.group(1)
        return ""

class PositionalExtractor(FieldExtractor):
    """Value is at a specific index in the newline-split text."""
    def __init__(self, index: int):
        self.index = index

    def extract(self, text: str) -> str:
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if 0 <= self.index < len(lines):
            return lines[self.index]
        return ""
