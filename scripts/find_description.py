import pandas as pd
pd.set_option('display.max_colwidth',200)
try:
    df = pd.read_csv('salida/pedimentos_completo.csv', encoding='utf-8')
except Exception:
    df = pd.read_csv('salida/pedimentos_completo.csv', encoding='latin-1')
phrase = 'PARTES Y/O ACCESORIOS PARA APARATOS DE OXIGENOTERAPIA'
mask = df['FRACCION'].astype(str).str.contains('90192001', na=False)
matches = df[mask]
found = matches[matches['DESCRIPCION'].astype(str).str.upper().str.contains(phrase)]
print('FRACCION matches:', len(matches))
print('Exact-phrase matches:', len(found))
if len(found):
    cols = [c for c in ['NUM_PEDIMENTO','FRACCION','DESCRIPCION','Archivo'] if c in found.columns]
    print(found[cols].to_string(index=False))
else:
    # show some sample descriptions to inspect
    print(matches[['NUM_PEDIMENTO','FRACCION','DESCRIPCION','Archivo']].head(20).to_string(index=False))
