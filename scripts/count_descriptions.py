import pandas as pd

df = pd.read_csv('salida/pedimentos_completo.csv', dtype=str)
print('Total rows:', len(df))
for fr in ['90192001','90189099']:
    sub = df[df['FRACCION']==fr]
    empty = sub[(sub['DESCRIPCION'].isna()) | (sub['DESCRIPCION'].str.strip()=='')]
    print(fr + ' total:', len(sub), 'empty DESCRIPCION:', len(empty))

# show a few examples where description is empty for 90192001
sub = df[df['FRACCION']=='90192001']
empty = sub[(sub['DESCRIPCION'].isna()) | (sub['DESCRIPCION'].str.strip=='')]
print('\nSample rows with empty DESCRIPCION (first 5):')
print(empty[['NUM_PEDIMENTO','SEC','FRACCION','DESCRIPCION','Archivo']].head(5).to_string(index=False))
