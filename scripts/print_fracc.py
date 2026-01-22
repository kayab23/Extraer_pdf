import pandas as pd
pd.set_option('display.max_colwidth',200)
try:
    df = pd.read_csv('salida/pedimentos_completo.csv', encoding='utf-8')
except Exception:
    df = pd.read_csv('salida/pedimentos_completo.csv', encoding='latin-1')
mask = df['FRACCION'].astype(str).str.contains('90192001', na=False)
sel = df[mask]
print(sel[['NUM_PEDIMENTO','FRACCION','DESCRIPCION','TASA_IGI','Archivo']].head(50).to_string(index=False))
print('\nTotal matches:', len(sel))
