import pandas as pd
import re

df = pd.read_csv('salida/pedimentos_completo.csv', header=None, encoding='utf-8', dtype=str)
# ensure enough columns
if df.shape[1] < 4:
    print('Unexpected columns:', df.shape)
else:
    for i,row in df.iterrows():
        val = row[3] if 3 in row.index else ''
        col3 = str(val) if not pd.isna(val) else ''
        col3 = col3.strip()
        if col3 and re.fullmatch(r"[A-Za-z]{1,3}", col3):
            print(i+1, list(row[:10]))
