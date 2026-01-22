import os
import re
import pdfplumber
import pandas as pd

CSV = 'salida/pedimentos_completo.csv'
BASE = r'PEDIMENTOS 2025/PEDIMENTOS_VALIDOS'
TARGET_FRACCIONES = {'90192001','90189099'}


def print_detailed_context(pdf_path, frac_pat=r'9019\d{3}'):
    print('\n' + '='*80)
    print('File:', pdf_path)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for pnum, page in enumerate(pdf.pages, start=1):
                words = page.extract_words()
                if not words:
                    continue
                # group by rounded top
                lines = {}
                for w in words:
                    top = round(w.get('top',0))
                    lines.setdefault(top, []).append(w)
                tops = sorted(lines.keys())
                # search for fraction token anywhere in line text
                for ti, top in enumerate(tops):
                    line_txt = ' '.join([ww['text'] for ww in sorted(lines[top], key=lambda x: x['x0'])])
                    if re.search(frac_pat, line_txt):
                        print(f"\n-- Page {pnum} | line top={top} contains fraction: {line_txt}")
                        start = max(0, ti-6)
                        end = min(len(tops)-1, ti+6)
                        for t in tops[start:end+1]:
                            print(f"\nline top={t} :")
                            for ww in sorted(lines[t], key=lambda x: x['x0']):
                                print(f"  x0={ww.get('x0',0):7.2f} x1={ww.get('x1',0):7.2f} text='{ww.get('text','')}'")
    except Exception as e:
        print('Error opening', pdf_path, e)


if __name__ == '__main__':
    if not os.path.exists(CSV):
        print('CSV not found:', CSV)
        raise SystemExit(1)
    df = pd.read_csv(CSV, dtype=str)
    # filter problematic rows
    bad = df[df['FRACCION'].isin(list(TARGET_FRACCIONES)) & ((df['DESCRIPCION'].isna()) | (df['DESCRIPCION'].str.strip()==''))]
    if bad.empty:
        print('No problematic rows found for target fracciones')
    files = sorted(set(bad['Archivo'].tolist()))
    if not files:
        print('No files to inspect')
    for f in files:
        path = os.path.join(BASE, f)
        if not os.path.exists(path):
            print('Missing file:', path)
            continue
        print_detailed_context(path)
