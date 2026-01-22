import pdfplumber
import os
import re

BASE = r"PEDIMENTOS 2025/PEDIMENTOS_VALIDOS"
FILES = [
    "2. PEDIMENTO CIE05097-25MZ.pdf",
    "2. Pedimento PCSA 250398.pdf",
    "2. PEDIMENTO PCSA 250915.pdf",
    "Muestra de las rectificaciones de Pedimentos Flexicare 3.pdf",
    "2. PEDIMENTO PCSA 250924.pdf"
]

def extract_near_fraction(pdf_path, frac_re=r"9019\d{3}"):
    with pdfplumber.open(pdf_path) as pdf:
        for pnum, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            if not words:
                continue
            lines = {}
            for w in words:
                top = round(w.get('top',0))
                lines.setdefault(top, []).append(w)
            tops = sorted(lines.keys())
            for top in tops:
                txt = ' '.join([ww['text'] for ww in sorted(lines[top], key=lambda x: x['x0'])])
                for m in re.finditer(frac_re, txt):
                    token = m.group(0)
                    print(f"\n-- File: {os.path.basename(pdf_path)} | Page: {pnum} | top={top} token={token}")
                    # print window of +/-6 lines
                    idx = tops.index(top)
                    start = max(0, idx-6)
                    end = min(len(tops)-1, idx+6)
                    print("Context lines:")
                    for t in tops[start:end+1]:
                        line_txt = ' '.join([ww['text'] for ww in sorted(lines[t], key=lambda x: x['x0'])])
                        marker = '>>' if t==top else '  '
                        print(f" {marker} top={t}: {line_txt}")

if __name__ == '__main__':
    for f in FILES:
        path = os.path.join(BASE, f)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
        extract_near_fraction(path)
