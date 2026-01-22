import pdfplumber
import os
import re

BASE = r"PEDIMENTOS 2025/PEDIMENTOS_VALIDOS"
FILES = [
    "2. PEDIMENTO 25 47 1840 5002207.pdf",
    "1840-2207-2025.pdf",
    "3264_470_5000027_pedimento.pdf",
]

PATTERNS = [
    r"NO ES LA DESCRIPCION",
    r"ESTO NO ES LA DESCRIPCION",
    r"GUIA",
    r"ORDEN EMBARQUE",
    r"SERIES:",
    r"RFC:",
    r"E\.FIRMA",
    r"NUMERO DE SERIE",
    r"04026002",
    r"90259001",
]


def inspect_file(path):
    print(f"\n--- Inspecting: {path}")
    with pdfplumber.open(path) as pdf:
        for pnum, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            if not words:
                continue
            lines = {}
            for w in words:
                top = round(w.get('top', 0))
                lines.setdefault(top, []).append(w)
            tops = sorted(lines.keys())
            for idx, top in enumerate(tops):
                line_txt = ' '.join([ww['text'] for ww in sorted(lines[top], key=lambda x: x['x0'])])
                for pat in PATTERNS:
                    if re.search(pat, line_txt, re.IGNORECASE):
                        print(f"\nMatch pattern '{pat}' | Page {pnum} | top={top}\nContext:")
                        start = max(0, idx-6)
                        end = min(len(tops)-1, idx+6)
                        for t in tops[start:end+1]:
                            line_tokens = sorted(lines[t], key=lambda x: x['x0'])
                            token_str = ' | '.join([f"({int(tt['x0'])},{int(tt['x1'])}):{tt['text']}" for tt in line_tokens])
                            mark = '>>' if t==top else '  '
                            print(f" {mark} top={t}: {token_str}")
                        break


if __name__ == '__main__':
    for f in FILES:
        path = os.path.join(BASE, f)
        if not os.path.exists(path):
            print(f"File not found: {path}")
            continue
        inspect_file(path)
