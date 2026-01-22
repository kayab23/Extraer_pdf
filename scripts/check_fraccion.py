import pandas as pd
pd.set_option('display.max_colwidth',200)
try:
    df = pd.read_csv('salida/pedimentos_completo.csv', encoding='utf-8')
except Exception:
    df = pd.read_csv('salida/pedimentos_completo.csv', encoding='latin-1')
print('Cols:', list(df.columns))
if 'FRACCION' in df.columns:
    filt = df[df['FRACCION'].astype(str).str.contains('90192001', na=False)]
    print('Matches:', len(filt))
    if len(filt):
        cols = ['FRACCION','DESCRIPCION','TASA_IGI']
        existing = [c for c in cols if c in filt.columns]
        print(filt[existing + ['Archivo'] if 'Archivo' in filt.columns else existing].head(20).to_string(index=False))
else:
    filt = df[df.apply(lambda r: r.astype(str).str.contains('90192001').any(), axis=1)]
    print('Matches fallback:', len(filt))
    if len(filt):
        print(filt.head(20).to_string(index=False))
