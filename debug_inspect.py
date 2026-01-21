from src.mapear_campos import extraer_texto_pdf
p='PEDIMENTOS 2025/PEDIMENTOS_VALIDOS/2. PEDIMENTO.pdf'
try:
    texto=extraer_texto_pdf(p)
    lines=[l for l in texto.splitlines() if l.strip()]
    for i,l in enumerate(lines[:300]):
        if 'DATOS DEL PROVEEDOR' in l.upper() or 'ID' in l.upper() or 'RFC' in l.upper():
            print(i+1, l)
    # also print a window around first occurrence of 'PENLON' or 'GB'
    for i,l in enumerate(lines[:300]):
        if 'PENLON' in l.upper() or 'GB' in l.upper() or '310726' in l:
            start=max(0,i-5)
            end=min(len(lines), i+5)
            print('\n--- context around line', i+1, '---')
            for j in range(start,end):
                print(j+1, lines[j])
            break
    # also run extractor helpers
    from src.mapear_campos import extraer_datos_proveedor_por_posicion, extraer_datos_proveedor_preciso, extraer_datos_proveedor
    print('\n-- extraer_datos_proveedor_por_posicion --')
    print(extraer_datos_proveedor_por_posicion(p))
    print('\n-- extraer_datos_proveedor_preciso --')
    print(extraer_datos_proveedor_preciso(texto))
    print('\n-- extraer_datos_proveedor (texto) --')
    print(extraer_datos_proveedor(texto))
    import re
    pat = re.compile(r"[A-Z]{1,3}[\s\-]*[0-9][0-9\s\-]{4,20}", re.IGNORECASE)
    matches = pat.findall(texto)
    print('\n-- posibles matches ID en texto (raw) --')
    for m in matches:
        print('RAW:', m, 'NORM:', re.sub(r"[\s\-]", "", m))
except Exception as e:
    print('Error:', e)
