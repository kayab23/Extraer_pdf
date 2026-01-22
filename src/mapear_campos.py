
# Extracción simplificada: solo ID_FISCAL, NOMBRE, VAL_DOLARES

# Funciones de limpieza específicas para normalizar ID y NOMBRE
import typing

def clean_id(raw_id: str) -> str:
    if not raw_id:
        return ""
    s = raw_id.strip()
    # quitar prefijos comunes
    s = re.sub(r"^(FISCAL[:\s]*|RFC[:\s]*|R\.F\.C[:\s]*|ID[:\s]*|ID\.?\s*FISCAL[:\s]*)", "", s, flags=re.IGNORECASE)
    # tomar el primer token que parezca un RFC/ID (alfanumérico, guiones, ampersand)
    m = re.search(r"([A-Z0-9&\-]{6,20})", s.upper())
    if m:
        return m.group(1).strip()
    # fallback: devolver la cadena limpia corta
    return s.split()[0] if s.split() else s

def clean_nombre(raw_nombre: str) -> str:
    if not raw_nombre:
        return ""
    s = raw_nombre.strip()
    # eliminar encabezados repetidos que a veces aparecen dentro del valor
    s = re.sub(r"NOMBRE[,\s]*DENOMINACION O RAZON SOCIAL[:\s]*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"NOMBRE O RAZ\.? SOC\.?[:\s]*", "", s, flags=re.IGNORECASE)
    # cortar en la aparición de secciones/etiquetas que no forman parte del nombre
    cut_patterns = [
        r"RFC[:\s]", r"NUMERO DE SERIE", r"NUMERO DE SERIE DEL CERTIFICADO", r"E\.FIRMA", r"e\.firma",
        r"EL PAGO DE LAS CONTRIBUCIONES", r"SERVICIO DE PAGO", r"APODERADO", r"AGENTE ADUANAL",
        r"ADUANAL", r"CURP[:\s]", r"NUMERO[:\s]", r"NOMBRE O RAZ\. SOC\.", r"AGENCIA NOMBRE",
        r"RFC\s*:", r"RFC\b"
    ]
    earliest = None
    for pat in cut_patterns:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if m:
            pos = m.start()
            if earliest is None or pos < earliest:
                earliest = pos
    if earliest is not None and earliest > 0:
        s = s[:earliest].strip(' ,;:\n')
    # quitar tokens que son claramente códigos al final o principio
    # eliminar secuencias largas de base64 u otros bloques extraños
    s = re.sub(r"[A-Za-z0-9+/=]{40,}", "", s)
    # limpiar espacios redundantes y símbolos finales
    s = re.sub(r"\s{2,}", " ", s).strip(' ,;:\n')
    return s

def extract_id_from_nombre(raw_nombre: str):
    """Si el nombre comienza con un token que parece ID (ej. GB310726243), extraerlo."""
    if not raw_nombre:
        return "", raw_nombre
    s = raw_nombre.strip()
    # buscar token inicial que combine letras (1-3) seguido de dígitos (con espacios/guiones posibles), o token alfanum largo
    m = re.match(r"^([A-Z]{1,3}[\s\-]*[0-9][0-9\s\-]{4,20})\b", s, flags=re.IGNORECASE)
    if not m:
        m = re.match(r"^([A-Z0-9&\-]{6,20})\b", s, flags=re.IGNORECASE)
    if m:
        id_token = re.sub(r"[\s\-]", "", m.group(1).strip())
        rest = s[m.end():].strip(' ,;:')
        return id_token, rest
    return "", raw_nombre

# Extracción precisa: ID_FISCAL y NOMBRE de la cabecera, VAL_DOLARES de la tabla de facturas
def extraer_datos_proveedor_preciso(texto):
    import re
    lines = [l.rstrip() for l in texto.splitlines() if l.strip()]
    idx_cab = -1
    for i, line in enumerate(lines):
        if re.search(r"DATOS DEL PROVEEDOR O COMPRADOR", line, re.IGNORECASE):
            idx_cab = i
            break
    id_fiscal = []
    nombre = []
    etiquetas_idx = -1
    if idx_cab != -1:
        # Buscar la línea de etiquetas
        for j in range(idx_cab+1, min(idx_cab+8, len(lines))):
            l = lines[j]
            if re.search(r"ID[.]:? ?FISCAL", l) and re.search(r"NOMBRE,? ?DENOMINACION O RAZON SOCIAL", l):
                etiquetas_idx = j
                break
    # Extraer ID_FISCAL y NOMBRE de todas las líneas debajo de la cabecera, segmentando por columnas
    if etiquetas_idx != -1:
        etiquetas_line = lines[etiquetas_idx]
        # Buscar posiciones de inicio y fin de cada etiqueta
        etiquetas = [
            ("ID_FISCAL", r"ID[.]:? ?FISCAL"),
            ("NOMBRE", r"NOMBRE,? ?DENOMINACION O RAZON SOCIAL"),
            ("DOMICILIO", r"DOMICILIO")
        ]
        campos = {}
        for idx, (key, pattern) in enumerate(etiquetas):
            m = re.search(pattern, etiquetas_line)
            if m:
                campos[key] = [m.start(), None]
        keys = [k for k in campos]
        for i in range(len(keys)-1):
            campos[keys[i]][1] = campos[keys[i+1]][0]
        if keys:
            campos[keys[-1]][1] = len(etiquetas_line)
        # Palabras clave típicas de domicilio para filtrar
        patrones_domicilio = re.compile(r"CALLE|BLVD|AV\.|SUITE|BUILD|NO\.|STREET|COL\.|EDIFICIO|C\.P\.|PO BOX|NUMERO|NUM\.|APARTADO|DEPARTAMENTO|FLOOR|PISO|BARRIO|URB\.|MZ|LOTE|INT|EXT|ZONA|SECTOR|LOCAL|PLANTA|INTERIOR|EXTERIOR|CITY|CIUDAD|ESTADO|STATE|COUNTRY|PAIS|ZIP|POSTAL|CODIGO|CP|MUNICIPIO|DELEGACION|COLONIA|DIRECCION|DIR\.", re.IGNORECASE)
        k = etiquetas_idx + 1
        lineas_consideradas = 0
        max_lineas = 3
        while k < len(lines) and lineas_consideradas < max_lineas:
            l = lines[k]
            # Si la línea es vacía o parece una nueva sección, detener
            if not l.strip() or re.search(r"CLAVE|NUM\.|FACTURA|VAL\.|PARTIDAS|OBSERVACIONES|PEDIMENTO|ADUANA|TIPO CAMBIO", l, re.IGNORECASE):
                break
            # Evaluar si la línea es mayoritariamente domicilio
            palabras = l.split()
            if palabras:
                palabras_domicilio = [w for w in palabras if patrones_domicilio.search(w)]
                porcentaje_dom = len(palabras_domicilio) / len(palabras)
            else:
                porcentaje_dom = 0
            # Si más del 70% de las palabras son domicilio, detener
            if porcentaje_dom > 0.7:
                break
            def get_col_val(line, campos, key):
                if key not in campos:
                    return ""
                ini, fin = campos[key]
                if ini >= len(line):
                    return ""
                return line[ini:fin].strip()
            val_id = get_col_val(l, campos, "ID_FISCAL")
            val_nom = get_col_val(l, campos, "NOMBRE")
            if val_id:
                id_fiscal.append(val_id)
            if val_nom:
                nombre.append(val_nom)
            k += 1
            lineas_consideradas += 1
    # Unir líneas y limpiar
    import re
    # Buscar la línea de cabecera de etiquetas
    import re
    lines = [l.rstrip() for l in texto.splitlines() if l.strip()]
    idx_cab = -1
    for i, line in enumerate(lines):
        if re.search(r"ID[.]? ?FISCAL.*NOMBRE,? ?DENOMINACION O RAZON SOCIAL.*DOMICILIO.*VINCULACION", line, re.IGNORECASE):
            idx_cab = i
            break
    id_fiscal_str = nombre_str = ""
    if idx_cab != -1 and idx_cab+1 < len(lines):
        etiquetas_line = lines[idx_cab]
        # Buscar posiciones de inicio y fin de cada etiqueta
        etiquetas = [
            ("ID_FISCAL", r"ID[.]? ?FISCAL"),
            ("NOMBRE", r"NOMBRE,? ?DENOMINACION O RAZON SOCIAL"),
            ("DOMICILIO", r"DOMICILIO"),
            ("VINCULACION", r"VINCULACION")
        ]
        campos = {}
        for idx, (key, pattern) in enumerate(etiquetas):
            m = re.search(pattern, etiquetas_line)
            if m:
                campos[key] = [m.start(), None]
        keys = [k for k in campos]
        for i in range(len(keys)-1):
            campos[keys[i]][1] = campos[keys[i+1]][0]
        if keys:
            campos[keys[-1]][1] = len(etiquetas_line)
        # Palabras clave para detectar domicilio o fin de sección
        patron_domicilio = re.compile(r"CALLE|BLVD|AV\.|SUITE|BUILD|NO\.|STREET|COL\.|EDIFICIO|C\.P\.|PO BOX|NUMERO|NUM\.|APARTADO|DEPARTAMENTO|FLOOR|PISO|BARRIO|URB\.|MZ|LOTE|INT|EXT|ZONA|SECTOR|LOCAL|PLANTA|INTERIOR|EXTERIOR|CITY|CIUDAD|ESTADO|STATE|COUNTRY|PAIS|ZIP|POSTAL|CODIGO|CP|MUNICIPIO|DELEGACION|COLONIA|DIRECCION|DIR\.|DRIVE|REINO UNIDO|GRAN BRETAÑA|CHN|SCIENCE|VAL|NB|XINGONG|ABINGDON|CYNON|RUCT|SHENZHEN|UNIDO|LIMITED|LTD\.|CO\.|S\.A\.|ER|EAST|WEST|NORTE|SUR|NORTH|SOUTH", re.IGNORECASE)
        patron_seccion = re.compile(r"NUM\.|CLAVE|FACTURA|OBSERVACIONES|PARTIDAS|DESCARGOS|AGENTE|CURP|RFC|FECHA|MONEDA|VAL\.|TASA|TIPO|PEDIMENTO|OPER|CVE|APODERADO|ADUANAL|DESTINO|USUARIO|COPIA|CERTIFICADO|e\.firma", re.IGNORECASE)
        id_fiscal_parts = []
        nombre_parts = []
        k = idx_cab + 1
        max_lines_collect = 6
        lines_taken = 0
        def get_col_val(line, campos, key):
            if key not in campos:
                return ""
            ini, fin = campos[key]
            if ini >= len(line):
                return ""
            return line[ini:fin].strip()
        while k < len(lines) and lines_taken < max_lines_collect:
            l = lines[k]
            if not l.strip() or patron_seccion.search(l):
                break
            id_val = get_col_val(l, campos, "ID_FISCAL")
            nom_val = get_col_val(l, campos, "NOMBRE")
            # calcular si la columna parece ser domicilio (proporción de palabras clave)
            def porcentaje_dom_segment(seg):
                palabras = seg.split()
                if not palabras:
                    return 0.0
                palabras_dom = [w for w in palabras if patron_domicilio.search(w)]
                return len(palabras_dom) / len(palabras)
            por_nom = porcentaje_dom_segment(nom_val) if nom_val else 0.0
            por_id = porcentaje_dom_segment(id_val) if id_val else 0.0
            # lógica tolerante: concatenar si no es mayoritariamente domicilio
            if nom_val:
                if por_nom < 0.8:
                    nombre_parts.append(nom_val)
                else:
                    # si la columna de nombre es mayoritariamente domicilio, no incluir y continue
                    pass
            if id_val:
                if por_id < 0.9:
                    id_fiscal_parts.append(id_val)
                else:
                    pass
            lines_taken += 1
            k += 1
        id_fiscal_str = " ".join(id_fiscal_parts).replace("  ", " ").strip()
        nombre_str = " ".join(nombre_parts).replace("  ", " ").strip()
        # Post-procesamiento: intentar extraer ID fiscal robusto (dígitos y guiones)
        if id_fiscal_str:
            m_id = re.search(r"\b[0-9\-]{6,}\b", id_fiscal_str)
            if m_id:
                id_fiscal_str = m_id.group(0)
        # Limpiar nombre: si contiene fragmentos de domicilio al final, cortar en la primera palabra clave completa
        m_dom = patron_domicilio.search(nombre_str)
        if m_dom:
            nombre_str = nombre_str[:m_dom.start()].strip(' ,;')
        # Eliminar tokens iniciales que parecen IDs o códigos (ej. '0-06-21-A')
        tokens = nombre_str.split()
        cleaned_tokens = []
        for t in tokens:
            # si el token tiene más dígitos que letras y contiene guiones, considerarlo código y saltarlo
            letters = sum(c.isalpha() for c in t)
            digits = sum(c.isdigit() for c in t)
            if digits > 0 and digits > letters and ('-' in t or len(t) <= 4):
                continue
            cleaned_tokens.append(t)
        nombre_str = ' '.join(cleaned_tokens).strip(' ,;')
        # Si el nombre quedó muy corto, intentar juntar fragmentos posteriores capturados
        if len(nombre_str) < 4 and nombre_parts:
            for part in nombre_parts[1:]:
                nombre_str = (nombre_str + ' ' + part).strip()
                if len(nombre_str) >= 4:
                    break
        id_fiscal_str = clean_id(id_fiscal_str)
        nombre_str = clean_nombre(nombre_str)
        # fallback: si id corto, intentar extraer del nombre
        if (not id_fiscal_str or len(id_fiscal_str) < 4) and nombre_str:
            ext_id, new_nombre = extract_id_from_nombre(nombre_str)
            if ext_id and len(ext_id) > len(id_fiscal_str):
                id_fiscal_str = clean_id(ext_id)
                nombre_str = clean_nombre(new_nombre)
        return id_fiscal_str, nombre_str, ""
def extraer_datos_proveedor(texto):
    """
    Extrae los campos ID. FISCAL, NOMBRE, DOMICILIO, VAL. DOLARES de la sección DATOS DEL PROVEEDOR O COMPRADOR
    considerando estructura multi-columna y multi-línea.
    """
    lines = [l.rstrip() for l in texto.splitlines() if l.strip()]
    idx_cab = -1
    for i, line in enumerate(lines):
        if "DATOS DEL PROVEEDOR O COMPRADOR" in line:
            idx_cab = i
            break
    id_fiscal = nombre = domicilio = val_dolares = ""
    if idx_cab != -1:
        # Buscar la línea de etiquetas (la que contiene todas las etiquetas principales)
        etiquetas_idx = -1
        for j in range(idx_cab+1, min(idx_cab+8, len(lines))):
            l = lines[j]
            if ("ID. FISCAL" in l and "NOMBRE" in l and "DOMICILIO" in l):
                etiquetas_idx = j
                break
        if etiquetas_idx != -1 and etiquetas_idx+1 < len(lines):
            etiquetas_line = lines[etiquetas_idx]
            valores_line = lines[etiquetas_idx+1]
            # Mapear posiciones de inicio de cada etiqueta
            etiquetas = ["ID. FISCAL", "NOMBRE, DENOMINACION O RAZON SOCIAL", "DOMICILIO", "VAL. DOLARES"]
            pos = {}
            for et in etiquetas:
                idx = etiquetas_line.find(et)
                if idx != -1:
                    pos[et] = idx
            # Extraer valores justo debajo de cada etiqueta
            if "ID. FISCAL" in pos:
                id_fiscal = valores_line[pos["ID. FISCAL"]:pos.get("NOMBRE, DENOMINACION O RAZON SOCIAL", None)].strip() if "NOMBRE, DENOMINACION O RAZON SOCIAL" in pos else valores_line[pos["ID. FISCAL"]:].strip()
            if "NOMBRE, DENOMINACION O RAZON SOCIAL" in pos:
                nombre = valores_line[pos["NOMBRE, DENOMINACION O RAZON SOCIAL"]:pos.get("DOMICILIO", None)].strip() if "DOMICILIO" in pos else valores_line[pos["NOMBRE, DENOMINACION O RAZON SOCIAL"]:].strip()
            if "DOMICILIO" in pos:
                domicilio = valores_line[pos["DOMICILIO"]:pos.get("VAL. DOLARES", None)].strip() if "VAL. DOLARES" in pos else valores_line[pos["DOMICILIO"]:].strip()
            if "VAL. DOLARES" in pos:
                val_dolares = valores_line[pos["VAL. DOLARES"]:].split()[0] if len(valores_line[pos["VAL. DOLARES"]:].split()) > 0 else ""
            # Si DOMICILIO es multilinea, unir líneas siguientes que no sean etiquetas ni vacías
            k = etiquetas_idx+2
            while k < len(lines):
                next_line = lines[k]
                # Si la línea contiene otra etiqueta o está vacía, detener
                if ("CLAVE" in next_line or "NUM." in next_line or "FACTURA" in next_line or "VAL." in next_line or not next_line.strip()):
                    break
                domicilio += " " + next_line.strip()
                k += 1
    id_fiscal = clean_id(id_fiscal.strip())
    nombre = clean_nombre(nombre.strip())
    # fallback: si id muy corto, intentar extraer del nombre
    if (not id_fiscal or len(id_fiscal) < 4) and nombre:
        ext_id, new_nombre = extract_id_from_nombre(nombre)
        if ext_id and len(ext_id) > len(id_fiscal):
            id_fiscal = clean_id(ext_id)
            nombre = clean_nombre(new_nombre)
    return id_fiscal, nombre, domicilio.strip(), val_dolares.strip()
import pandas as pd
import re
import pdfplumber
import glob
import os

def extraer_texto_pdf(pdf_path):
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            texto += t + "\n"
    return texto


def extraer_datos_proveedor_por_posicion(pdf_path):
    """Extrae ID_FISCAL y NOMBRE usando coordenadas (más robusto para desbordes y multilíneas)."""
    import math
    claves_seccion = [r"ID", r"FISCAL", r"NOMBRE", r"DOMICILIO"]
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            if not words:
                continue
            # Buscar posibles líneas de cabecera que contengan ID y NOMBRE
            # Agrupar por top (líneas)
            lines = {}
            for w in words:
                top = round(w.get("top", 0))
                lines.setdefault(top, []).append(w)
            for top, wlist in sorted(lines.items()):
                txt = " ".join([w["text"] for w in sorted(wlist, key=lambda x: x["x0"])])
                if re.search(r"ID\.?\s*FISCAL", txt, re.IGNORECASE) and re.search(r"NOMBRE", txt, re.IGNORECASE):
                    # Encontrada la línea de cabecera
                    header_words = sorted(wlist, key=lambda x: x["x0"])  # orden por x
                    # Mapear inicio de columnas por palabras clave
                    cols = {}
                    for w in header_words:
                        ut = w["text"].upper()
                        if "ID" in ut and "FISCAL" in ut or re.search(r"ID\.?", ut):
                            cols["ID_FISCAL"] = w["x0"]
                        if "NOMBRE" in ut:
                            cols["NOMBRE"] = w["x0"]
                        if "DOMICILIO" in ut:
                            cols["DOMICILIO"] = w["x0"]
                        if "VINCULACION" in ut:
                            cols["VINCULACION"] = w["x0"]
                    # Necesitamos al menos ID y NOMBRE
                    if "ID_FISCAL" not in cols or "NOMBRE" not in cols:
                        continue
                    # Determinar límites de cada columna usando los inicios ordenados
                    ordered = sorted([(k, v) for k, v in cols.items()], key=lambda x: x[1])
                    limits = {}
                    for i, (k, x0) in enumerate(ordered):
                        start = x0
                        end = ordered[i+1][1] if i+1 < len(ordered) else float('inf')
                        limits[k] = (start, end)

                    # Recolectar palabras debajo de la cabecera hasta nueva sección
                    collected = {k: [] for k in limits}
                    stop_patterns = re.compile(r"NUM\.|FACTURA|PARTIDAS|OBSERVACIONES|PEDIMENTO|ANEXO|CLAVE", re.IGNORECASE)
                    for w in words:
                        # solo palabras por debajo de la línea de cabecera
                        if w.get("top", 0) <= top:
                            continue
                        if stop_patterns.search(w.get("text", "")):
                            break
                        x0 = w.get("x0", 0)
                        for k, (s, e) in limits.items():
                            if x0 >= s - 1 and x0 < e - 1:
                                collected[k].append((w.get("top", 0), w.get("x0", 0), w.get("text", "")))
                                break

                    # Para cada columna, ordenar por top,y x0 y concatenar respetando líneas
                    def build_col(col_items):
                        if not col_items:
                            return ""
                        col_items_sorted = sorted(col_items, key=lambda x: (round(x[0]), x[1]))
                        # Agrupar por top para preservar saltos de línea
                        byline = {}
                        for topi, x0i, texti in col_items_sorted:
                            keyline = round(topi)
                            byline.setdefault(keyline, []).append((x0i, texti))
                        parts = []
                        for ln in sorted(byline.keys()):
                            seg = " ".join([t for _, t in sorted(byline[ln], key=lambda z: z[0])])
                            parts.append(seg)
                        return " ".join(parts).strip()

                    id_val = build_col(collected.get("ID_FISCAL", []))
                    nombre_val = build_col(collected.get("NOMBRE", []))
                    # limpieza básica
                    id_val = id_val.replace('ID:', '').replace('ID.', '').strip()
                    nombre_val = nombre_val.strip(' ,;')
                    id_val = clean_id(id_val)
                    nombre_val = clean_nombre(nombre_val)
                    # si id corto, intentar extraer id del inicio del nombre
                    if (not id_val or len(id_val) < 4) and nombre_val:
                        ext_id, new_nombre = extract_id_from_nombre(nombre_val)
                        if ext_id and len(ext_id) > len(id_val):
                            id_val = clean_id(ext_id)
                            nombre_val = clean_nombre(new_nombre)
                    return id_val, nombre_val
    return "", ""


def extraer_cabecera_pedimento(texto):
    """
    Extrae NUM.PEDIMENTO, TIPO CAMBIO y ADUANA E/S de la línea principal de cabecera,
    tolerando columnas y espacios variables.
    """
    lines = [l.strip() for l in texto.splitlines() if l.strip()]
    pedimento = tipo_cambio = aduana = ""
    idx_pedimento = -1
    # Buscar la línea que contiene la palabra PEDIMENTO
    for i, line in enumerate(lines):
        if re.search(r"PEDIMENTO", line, re.IGNORECASE):
            idx_pedimento = i
            break
    # Si se encontró la sección PEDIMENTO, buscar datos en las siguientes 5 líneas
    if idx_pedimento != -1:
        for line in lines[idx_pedimento:idx_pedimento+6]:
            if not pedimento:
                m = re.search(r"NUM[\.]?\s*PEDIMENTO\s*:?\s*([\d\s-]+)", line, re.IGNORECASE)
                if m:
                    pedimento = m.group(1).strip()
                else:
                    # Buscar formato alternativo: solo números largos
                    m2 = re.search(r"\b(\d{7,})\b", line)
                    if m2:
                        pedimento = m2.group(1)
            if not tipo_cambio:
                m = re.search(r"TIPO\s*CAMBIO\s*:?\s*([\d.,]+)", line, re.IGNORECASE)
                if m:
                    tipo_cambio = m.group(1)
            if not aduana:
                m = re.search(r"ADUANA[\sE/S]*:?\s*(\d+)", line, re.IGNORECASE)
                if m:
                    aduana = m.group(1)
    return pedimento, tipo_cambio, aduana


def extraer_partidas_por_posicion(pdf_path):
    """Extrae las partidas (SEC, FRACCION, DESCRIPCION, TASA_IGI) usando coordenadas.
    Devuelve lista de dicts: {'SEC','FRACCION','DESCRIPCION','TASA_IGI'}.
    """
    partidas = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words()
                if not words:
                    continue
                # Agrupar por top para formar líneas
                lines = {}
                for w in words:
                    top = round(w.get('top', 0))
                    lines.setdefault(top, []).append(w)
                # Buscar línea de cabecera de partidas
                header_top = None
                header_cols = {}
                for top, wlist in sorted(lines.items()):
                    txt = ' '.join([ww['text'] for ww in sorted(wlist, key=lambda x: x['x0'])]).upper()
                    if 'SEC' in txt and 'FRACCION' in txt and 'DESCRIPCION' in txt:
                        header_top = top
                        # mapear posiciones por palabra
                        for ww in sorted(wlist, key=lambda x: x['x0']):
                            t = ww['text'].upper()
                            if 'SEC' in t:
                                header_cols['SEC'] = ww['x0']
                            if 'FRACCION' in t or 'FRACCIÓN' in t:
                                header_cols['FRACCION'] = ww['x0']
                            if 'DESCRIPCION' in t or 'DESCRIPCIÓN' in t:
                                header_cols['DESCRIPCION'] = ww['x0']
                            if 'TASA' in t or 'IGI' in t or 'TASA_IGI' in t:
                                header_cols['TASA'] = ww['x0']
                        break
                if header_top is None:
                    continue
                # Determinar límites de columnas por orden de x
                ordered = sorted(header_cols.items(), key=lambda x: x[1])
                limits = {}
                for i, (k, x0) in enumerate(ordered):
                    start = x0
                    end = ordered[i+1][1] if i+1 < len(ordered) else float('inf')
                    limits[k] = (start, end)

                # Recolectar palabras por columna para líneas debajo de header
                collected = []
                stop_patterns = re.compile(r'FIN DE PEDIMENTO|\*{4,}|OBSERVACIONES A NIVEL PARTIDA', re.IGNORECASE)
                for top, wlist in sorted(lines.items()):
                    if top <= header_top:
                        continue
                    # si línea indica fin, romper
                    line_txt = ' '.join([ww['text'] for ww in sorted(wlist, key=lambda x: x['x0'])])
                    if stop_patterns.search(line_txt):
                        break
                    # clasificar palabras por columna
                    cols_line = {k: [] for k in limits}
                    for ww in sorted(wlist, key=lambda x: x['x0']):
                        x0 = ww.get('x0', 0)
                        for k, (s, e) in limits.items():
                            if x0 >= s - 1 and x0 < e - 1:
                                cols_line[k].append((x0, ww['text']))
                                break
                    collected.append((top, cols_line))

                # Ahora agrupar por filas completas usando detección de nueva SEC (col SEC no vacía)
                current = None
                for top, cols_line in collected:
                    sec_tokens = cols_line.get('SEC', [])
                    fr_tokens = cols_line.get('FRACCION', [])
                    desc_tokens = cols_line.get('DESCRIPCION', [])
                    tasa_tokens = cols_line.get('TASA', [])
                    sec = ' '.join([t for _, t in sorted(sec_tokens, key=lambda x: x[0])]).strip()
                    fr = ' '.join([t for _, t in sorted(fr_tokens, key=lambda x: x[0])]).strip()
                    desc = ' '.join([t for _, t in sorted(desc_tokens, key=lambda x: x[0])]).strip()
                    tasa = ' '.join([t for _, t in sorted(tasa_tokens, key=lambda x: x[0])]).strip()
                    # detectar inicio de nueva partida: SEC con dígitos o FRACCION presente
                    if sec or fr:
                        # finalizar current
                        if current:
                            # limpiar impuesto incrustado en descripcion antes de anexar
                            if current.get('DESCRIPCION'):
                                d = current['DESCRIPCION']
                                m_igi = re.search(r"\bIGI\s*([0-9]+\.[0-9]{5})\b", d, re.IGNORECASE)
                                m_iva = re.search(r"\bIVA\s*([0-9]+\.[0-9]{5})\b", d, re.IGNORECASE)
                                if m_igi:
                                    current['TASA_IGI'] = m_igi.group(1)
                                    current['DESCRIPCION'] = re.sub(r"\bIGI\s*[0-9]+\.[0-9]{5}\b", "", d, flags=re.IGNORECASE).strip(' ,;')
                                elif m_iva:
                                    # eliminar IVA del texto; preferir IGI si aparece en otra línea
                                    current['DESCRIPCION'] = re.sub(r"\bIVA\s*[0-9]+\.[0-9]{5}\b", "", d, flags=re.IGNORECASE).strip(' ,;')
                            partidas.append(current)
                        current = {'SEC': sec or '', 'FRACCION': fr or '', 'DESCRIPCION': desc or '', 'TASA_IGI': tasa or ''}
                        # si en la misma línea la descripcion trae IGI/IVA, extraerlo ahora
                        if current.get('DESCRIPCION'):
                            d0 = current['DESCRIPCION']
                            m_igi0 = re.search(r"\bIGI\s*([0-9]+\.[0-9]{5})\b", d0, re.IGNORECASE)
                            m_iva0 = re.search(r"\bIVA\s*([0-9]+\.[0-9]{5})\b", d0, re.IGNORECASE)
                            if m_igi0:
                                current['TASA_IGI'] = m_igi0.group(1)
                                current['DESCRIPCION'] = re.sub(r"\bIGI\s*[0-9]+\.[0-9]{5}\b", "", d0, flags=re.IGNORECASE).strip(' ,;')
                            elif m_iva0 and not current.get('TASA_IGI'):
                                # eliminar IVA si no hay IGI
                                current['DESCRIPCION'] = re.sub(r"\bIVA\s*[0-9]+\.[0-9]{5}\b", "", d0, flags=re.IGNORECASE).strip(' ,;')
                    else:
                        # continuación de descripcion
                        if current:
                            if desc:
                                current['DESCRIPCION'] = (current.get('DESCRIPCION', '') + ' ' + desc).strip()
                                # al concatenar, buscar IGI/IVA y extraer
                                dtmp = current['DESCRIPCION']
                                m_igi_c = re.search(r"\bIGI\s*([0-9]+\.[0-9]{5})\b", dtmp, re.IGNORECASE)
                                m_iva_c = re.search(r"\bIVA\s*([0-9]+\.[0-9]{5})\b", dtmp, re.IGNORECASE)
                                if m_igi_c:
                                    current['TASA_IGI'] = m_igi_c.group(1)
                                    current['DESCRIPCION'] = re.sub(r"\bIGI\s*[0-9]+\.[0-9]{5}\b", "", dtmp, flags=re.IGNORECASE).strip(' ,;')
                                elif m_iva_c and not current.get('TASA_IGI'):
                                    current['DESCRIPCION'] = re.sub(r"\bIVA\s*[0-9]+\.[0-9]{5}\b", "", dtmp, flags=re.IGNORECASE).strip(' ,;')
                            if tasa and not current.get('TASA_IGI'):
                                # si hay un token en la columna tasa, preferirlo solo si no existe IGI en descripcion
                                current['TASA_IGI'] = tasa
                if current:
                    partidas.append(current)
    except Exception:
        pass
    return partidas


def extraer_datos_completos(texto):
    # --- 1. Extracción de Cabecera robusta ---
    # Validar que el texto contiene las tres secciones clave
    if not (re.search(r"PEDIMENTO", texto, re.IGNORECASE) and re.search(r"DATOS DEL PROVEEDOR O COMPRADOR", texto, re.IGNORECASE) and re.search(r"PARTIDAS", texto, re.IGNORECASE)):
        return pd.DataFrame([])

    pedimento, tipo_cambio, aduana = extraer_cabecera_pedimento(texto)
    # Intentar extracción por posiciones en el PDF si es posible (más robusta)
    id_fiscal = nombre = ""
    try:
        # `texto` proviene de extraer_texto_pdf; no tenemos el path aquí.
        # La función `procesar_pedimentos_y_generar_csv` intentará usar la versión por posición.
        id_fiscal, nombre, _ = extraer_datos_proveedor_preciso(texto)
    except Exception:
        id_fiscal, nombre = "", ""
    patron_partidas = re.compile(
        r"(\d+)\s+(\d{8}).*?\n"                # SEC y FRACCION
        r"(.*?)\s+\d+\s+\d+\s+[\d.]+\n"        # DESCRIPCION
        r".*?IGI\s+([\d.]+)",                  # Tasa IGI
        re.DOTALL
    )
    resultados = []
    for match in patron_partidas.finditer(texto):
        resultados.append({
            "NUM_PEDIMENTO": pedimento,
            "TIPO_CAMBIO": tipo_cambio,
            "ADUANA": aduana,
            "ID_FISCAL": id_fiscal,
            "NOMBRE_DENOMINACION_O_RAZON_SOCIAL": nombre,
            "SEC": match.group(1),
            "FRACCION": match.group(2),
            "DESCRIPCION": match.group(3).strip(),
            "TASA_IGI": match.group(4)
        })
    return pd.DataFrame(resultados)

def procesar_pedimentos_y_generar_csv(carpeta, archivo_salida_csv):
    resultados = []
    # Solo procesar archivos que contengan 'PEDIMENTO' en el nombre
    pdfs = [f for f in glob.glob(os.path.join(carpeta, '*.pdf')) if 'PEDIMENTO' in os.path.basename(f).upper()]
    for pdf_path in pdfs:
        print(f"Procesando: {os.path.basename(pdf_path)}")
        texto = extraer_texto_pdf(pdf_path)
        # Primero intentar extracción por posición (coord x/y)
        id_fiscal_pos, nombre_pos = extraer_datos_proveedor_por_posicion(pdf_path)
        if id_fiscal_pos or nombre_pos:
            # inyectar estos valores en la extracción completa
            # si hay partidas por posición, usarlas para armar filas con ID/NOMBRE
            partidas = extraer_partidas_por_posicion(pdf_path)
            if partidas:
                pedimento, tipo_cambio, aduana = extraer_cabecera_pedimento(texto)
                resultados_local = []
                for p in partidas:
                    fila = {
                        "NUM_PEDIMENTO": pedimento,
                        "TIPO_CAMBIO": tipo_cambio,
                        "ADUANA": aduana,
                        "ID_FISCAL": id_fiscal_pos,
                        "NOMBRE_DENOMINACION_O_RAZON_SOCIAL": nombre_pos,
                        "SEC": p.get('SEC',''),
                        "FRACCION": p.get('FRACCION',''),
                        "DESCRIPCION": p.get('DESCRIPCION',''),
                        "TASA_IGI": p.get('TASA_IGI','')
                    }
                    resultados_local.append(fila)
                # convertir a df para mantener compatibilidad
                df = pd.DataFrame(resultados_local)
            else:
                df = extraer_datos_completos(texto)
                if not df.empty:
                    df["ID_FISCAL"] = df["ID_FISCAL"].fillna("")
                    df["NOMBRE_DENOMINACION_O_RAZON_SOCIAL"] = df["NOMBRE_DENOMINACION_O_RAZON_SOCIAL"].fillna("")
                    df.loc[:, "ID_FISCAL"] = id_fiscal_pos
                    df.loc[:, "NOMBRE_DENOMINACION_O_RAZON_SOCIAL"] = nombre_pos
        else:
            # intentar extraer partidas por posición aun cuando no se obtuvo ID/NOMBRE por posición
            partidas = extraer_partidas_por_posicion(pdf_path)
            if partidas:
                pedimento, tipo_cambio, aduana = extraer_cabecera_pedimento(texto)
                resultados_local = []
                for p in partidas:
                    fila = {
                        "NUM_PEDIMENTO": pedimento,
                        "TIPO_CAMBIO": tipo_cambio,
                        "ADUANA": aduana,
                        "ID_FISCAL": "",
                        "NOMBRE_DENOMINACION_O_RAZON_SOCIAL": "",
                        "SEC": p.get('SEC',''),
                        "FRACCION": p.get('FRACCION',''),
                        "DESCRIPCION": p.get('DESCRIPCION',''),
                        "TASA_IGI": p.get('TASA_IGI','')
                    }
                    resultados_local.append(fila)
                df = pd.DataFrame(resultados_local)
            else:
                df = extraer_datos_completos(texto)
        for _, row in df.iterrows():
            fila = row.to_dict()
            fila["Archivo"] = os.path.basename(pdf_path)
            resultados.append(fila)
    if resultados:
        df_final = pd.DataFrame(resultados)
        # Post-procesamiento: intentar recuperar IDs truncados (ej. 'GB' en vez de 'GB310726243')
        # permitir dígitos separados por espacios/guiones (ej. 'GB 806 645 523')
        posible_id_pat = re.compile(r"[A-Z]{1,3}[\s\-]*[0-9][0-9\s\-]{4,20}", re.IGNORECASE)
        for idx, row in df_final.iterrows():
            cur_id = str(row.get("ID_FISCAL", "") or "").strip()
            # si el ID no contiene dígitos (p. ej. 'GB' o 'PENLON'), intentar recuperar un RFC/ID numérico desde el PDF
            if cur_id and not re.search(r"\d", cur_id):
                archivo = row.get("Archivo") or ""
                pdf_path = os.path.join(carpeta, archivo) if archivo else None
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        texto_pdf = extraer_texto_pdf(pdf_path)
                        # buscar coincidencias más largas que comiencen con las mismas letras
                        # localizar coincidencias con posición para elegir la más cercana a la cabecera
                        it = list(re.finditer(posible_id_pat, texto_pdf.upper()))
                        if it:
                            header_pos = texto_pdf.upper().find('DATOS DEL PROVEEDOR')
                            candidates = []
                            for m in it:
                                raw = m.group(0)
                                norm = re.sub(r"[\s\-]", "", raw)
                                # calcular longitud de la parte dígito
                                digits_len = len(re.sub(r"\D", "", norm))
                                candidates.append((norm, raw, m.start(), m.end(), digits_len))
                            # elegir candidato más cercano a la cabecera; preferir digit_len razonable (6-12)
                            def score(c):
                                norm, posm, dlen = c
                                dist = abs((header_pos if header_pos!=-1 else 0) - posm)
                                # penalizar dígitos demasiado largos o cortos
                                penalty = 0
                                if dlen < 5 or dlen > 14:
                                    penalty += 100000
                                # prefer candidates starting with cur_id letters
                                if cur_id and norm.startswith(cur_id.upper()):
                                    penalty -= 1000
                                return dist + penalty
                            best = min(candidates, key=score)
                            chosen = best[0]
                            chosen_raw = best[1]
                            chosen_start = best[2]
                            chosen_end = best[3]
                            if chosen and len(chosen) > len(cur_id):
                                df_final.at[idx, "ID_FISCAL"] = chosen
                                # si el nombre actual es muy corto o es un sufijo (LIMITED, LTD, S.A., etc.), reconstruir nombre
                                nombre_actual = str(df_final.at[idx, "NOMBRE_DENOMINACION_O_RAZON_SOCIAL"]) if df_final.at[idx, "NOMBRE_DENOMINACION_O_RAZON_SOCIAL"] is not None else ''
                                sufijos = {"LIMITED", "LTD", "S\.A\.", "SA", "S\.A\. DE C\.V\.", "INC", "LLC"}
                                short_name = len(nombre_actual.strip()) < 6 or any(re.search(rf"^{suf}$", nombre_actual.strip(), re.IGNORECASE) for suf in ["LIMITED","LTD","INC","LLC","S\.A","SA"])
                                if short_name:
                                    try:
                                        # extraer fragmento inmediatamente posterior al match en el PDF
                                        tail = texto_pdf[chosen_end:chosen_end+200]
                                        # cortar en la primera coma o salto de línea
                                        tail_cut = re.split(r",|\n", tail)[0].strip()
                                        # separar en palabras y detener en palabras de parada (lugares/domicilio)
                                        stop_words = {"ABINGDON","SCIENCE","PARK","OXON","C.P.","CP","REINO","UNIDO","CIUDAD","NO","EXT","No.","C\.P\.","OX14","OX"}
                                        words = [w.strip(' ,.;:') for w in tail_cut.split()]
                                        name_parts = []
                                        for w in words:
                                            up = w.upper()
                                            if up in stop_words:
                                                break
                                            name_parts.append(w)
                                            if len(name_parts) >= 4:
                                                break
                                        if name_parts:
                                            nuevo_nombre = " ".join(name_parts).strip(' ,;:')
                                            # si el nuevo nombre empieza con un sufijo (ej. PENLON LIMITED -> starts with PENLON), usarlo
                                            df_final.at[idx, "NOMBRE_DENOMINACION_O_RAZON_SOCIAL"] = nuevo_nombre
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                # Corrección puntual: si ID quedó como palabra (ej. 'PENLON') y nombre es solo sufijo ('LIMITED'),
                # buscar en el PDF la secuencia ID_full + nombre completo y asignar correctamente.
                try:
                    cur_id2 = str(df_final.at[idx, "ID_FISCAL"]) if "ID_FISCAL" in df_final.columns else cur_id
                    cur_name2 = str(df_final.at[idx, "NOMBRE_DENOMINACION_O_RAZON_SOCIAL"]) if "NOMBRE_DENOMINACION_O_RAZON_SOCIAL" in df_final.columns else ''
                    if cur_id2 and not re.search(r"\d", cur_id2) and cur_name2 and re.match(r"^(LIMITED|LTD|INC|LLC|S\.A\.|SA)$", cur_name2.strip(), re.IGNORECASE):
                        # buscar patrón combinado en el texto: ID completo seguido del nombre (hasta coma)
                        pattern = re.compile(r"([A-Z]{1,3}[\s\-]*[0-9][0-9\s\-]{4,20})\s+([A-Z0-9&\- ]{2,80}?\b(?:LIMITED|LTD|INC|LLC|S\.A\.|SA)\b)", re.IGNORECASE)
                        m = pattern.search(texto_pdf)
                        if m:
                            full_id = re.sub(r"[\s\-]", "", m.group(1).upper())
                            full_name = m.group(2).strip(' ,;:\n')
                            # asignar solo si full_id contiene dígitos y parece válido
                            if re.search(r"\d", full_id) and len(re.sub(r"\D", "", full_id)) >= 5:
                                df_final.at[idx, "ID_FISCAL"] = full_id
                                df_final.at[idx, "NOMBRE_DENOMINACION_O_RAZON_SOCIAL"] = full_name
                except Exception:
                    pass
        # Post-procesamiento adicional: normalizar DESCRIPCION y extraer TASA_IGI si aparece incrustada
        for idx, row in df_final.iterrows():
            try:
                desc = str(row.get('DESCRIPCION', '') or '')
                tasa = str(row.get('TASA_IGI', '') or '')
                # buscar IGI explícito en la descripcion
                m_igi = re.search(r"\bIGI\s*([0-9]+\.[0-9]{5})\b", desc, re.IGNORECASE)
                m_iva = re.search(r"\bIVA\s*([0-9]+\.[0-9]{5})\b", desc, re.IGNORECASE)
                if m_igi:
                    df_final.at[idx, 'TASA_IGI'] = m_igi.group(1)
                    # eliminar el token IGI del texto
                    newd = re.sub(r"\bIGI\s*[0-9]+\.[0-9]{5}\b", "", desc, flags=re.IGNORECASE).strip(' ,;')
                    df_final.at[idx, 'DESCRIPCION'] = re.sub(r"\s{2,}", " ", newd).strip()
                else:
                    # si no hay IGI pero hay IVA en la descripcion, quitar IVA del texto
                    if m_iva:
                        newd = re.sub(r"\bIVA\s*[0-9]+\.[0-9]{5}\b", "", desc, flags=re.IGNORECASE).strip(' ,;')
                        df_final.at[idx, 'DESCRIPCION'] = re.sub(r"\s{2,}", " ", newd).strip()
                    # si aun no hay tasa y la columna tasa tiene valor, mantenerla
                    if (not df_final.at[idx, 'TASA_IGI'] or str(df_final.at[idx, 'TASA_IGI']).strip() == '') and tasa:
                        df_final.at[idx, 'TASA_IGI'] = tasa
            except Exception:
                pass
        df_final.to_csv(archivo_salida_csv, index=False, encoding="utf-8")
        print(f"Extracción completada. Archivo generado: {archivo_salida_csv}")

if __name__ == "__main__":
    procesar_pedimentos_y_generar_csv("PEDIMENTOS 2025/PEDIMENTOS_VALIDOS", "salida/pedimentos_completo.csv")
