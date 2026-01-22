import pandas as pd
import os
pd.set_option('display.max_colwidth',200)
CSV='salida/pedimentos_completo.csv'
if not os.path.exists(CSV):
    print('CSV not found:', CSV)
    raise SystemExit(1)
df = pd.read_csv(CSV, encoding='utf-8')
print('Total rows:', len(df))
print('Columns:', list(df.columns))
for frac in ['90191099','90192001']:
    sel = df[df['FRACCION'].astype(str).str.contains(frac, na=False)]
    print('\nFRACCION', frac, 'matches:', len(sel))
    if not sel.empty:
        display_cols = [c for c in ['NUM_PEDIMENTO','SEC','FRACCION','DESCRIPCION','TASA_IGI','Archivo'] if c in df.columns]
        print(sel[display_cols].head(10).to_string(index=False))
# show some random sample where FRACCION contains 9019
sel2 = df[df['FRACCION'].astype(str).str.contains('9019', na=False)]
print('\nSample 9019... count:', len(sel2))
if len(sel2):
    print(sel2[['NUM_PEDIMENTO','SEC','FRACCION','DESCRIPCION','TASA_IGI','Archivo']].head(20).to_string(index=False))
