import os
import glob
import pandas as pd
import pdfplumber

CSV = 'salida/pedimentos_completo.csv'
PDF_ROOT = 'PEDIMENTOS 2025'

pd.set_option('display.max_colwidth',200)

def find_pdf_path(filename):
    # search recursively under PDF_ROOT for a file that endswith filename
    for root, dirs, files in os.walk(PDF_ROOT):
        for f in files:
            if f == filename:
                return os.path.join(root, f)
    # fallback: try matching by basename contains
    for root, dirs, files in os.walk(PDF_ROOT):
        for f in files:
            if filename in f:
                return os.path.join(root, f)
    return None


def inspect_row(row, max_examples=3):
    archivo = str(row.get('Archivo',''))
    fr = str(row.get('FRACCION','')).strip()
    sec = str(row.get('SEC',''))
    num = str(row.get('NUM_PEDIMENTO',''))
    print('\n---')
    print('Archivo:', archivo)
    print('NUM_PEDIMENTO:', num, 'SEC:', sec, 'FRACCION:', fr)
    path = find_pdf_path(archivo)
    if not path:
        print('PDF no encontrado en', PDF_ROOT)
        return
    print('PDF path:', path)
    with pdfplumber.open(path) as pdf:
        found = 0
        for pageno, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            if not words:
                continue
            # normalize tokens
            tokens = [w['text'] for w in words]
            # find occurrences of the fraccion token (exact or contained)
            matches = [w for w in words if fr and fr in w.get('text','')]
            if not matches:
                continue
            for m in matches:
                if found >= max_examples:
                    break
                top = round(m.get('top',0))
                x0 = m.get('x0',0)
                print(f'-- Page {pageno} match at top={top} x0={x0} token="{m.get("text")}"')
                # collect nearby lines within +/-12 points
                lines = {}
                for w in words:
                    t = round(w.get('top',0))
                    lines.setdefault(t, []).append(w)
                nearby_keys = sorted([k for k in lines.keys() if abs(k-top) <= 30])
                for k in nearby_keys:
                    line_txt = ' '.join([ww['text'] for ww in sorted(lines[k], key=lambda z: z['x0'])])
                    print(f'  top={k}: {line_txt}')
                # also print next few lines below (top+1..+120)
                below_keys = sorted([k for k in lines.keys() if k > top and k <= top+120])
                if below_keys:
                    print('  >>> Lines below:')
                    for k in below_keys[:6]:
                        line_txt = ' '.join([ww['text'] for ww in sorted(lines[k], key=lambda z: z['x0'])])
                        print(f'    top={k}: {line_txt}')
                found += 1
            if found >= max_examples:
                break
        if found == 0:
            print('No se encontraron tokens FRACCION en el PDF (busca coincidencias parciales).')


def main(limit=50):
    if not os.path.exists(CSV):
        print('CSV no encontrado:', CSV)
        return
    df = pd.read_csv(CSV, encoding='utf-8')
    # seleccionar filas con DESCRIPCION vacía o NaN
    mask = df['DESCRIPCION'].isna() | (df['DESCRIPCION'].astype(str).str.strip() == '')
    bad = df[mask]
    print('Filas con DESCRIPCION vacía:', len(bad))
    if bad.empty:
        return
    # limitar inspección a las primeras N
    for _, row in bad.iterrows():
        inspect_row(row)
        limit -= 1
        if limit <= 0:
            break

if __name__ == '__main__':
    main()