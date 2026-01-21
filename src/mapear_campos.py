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


def extraer_datos_completos(texto):
    # --- 1. Extracción de Cabecera robusta ---
    pedimento, tipo_cambio, aduana = extraer_cabecera_pedimento(texto)

    # --- 2. Extracción de Proveedor ---
    id_match = re.search(r"(\d{11})", texto)
    id_fiscal = id_match.group(1) if id_match else ""
    nombre_proveedor = ""
    if id_fiscal:
        nombre_match = re.search(rf"{id_fiscal}\s+(.+)", texto)
        if nombre_match:
            nombre_proveedor = nombre_match.group(1).strip()

    # --- 3. Extracción de Partidas (Estructura Multilínea) ---
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
            "PROVEEDOR": nombre_proveedor,
            "SEC": match.group(1),
            "FRACCION": match.group(2),
            "DESCRIPCION": match.group(3).strip(),
            "TASA_IGI": match.group(4)
        })
    return pd.DataFrame(resultados)

def procesar_pedimentos_y_generar_csv(carpeta, archivo_salida_csv):
    resultados = []
    pdfs = glob.glob(os.path.join(carpeta, '*.pdf'))
    for pdf_path in pdfs:
        print(f"Procesando: {os.path.basename(pdf_path)}")
        texto = extraer_texto_pdf(pdf_path)
        df = extraer_datos_completos(texto)
        for _, row in df.iterrows():
            fila = row.to_dict()
            fila["Archivo"] = os.path.basename(pdf_path)
            resultados.append(fila)
    if resultados:
        df_final = pd.DataFrame(resultados)
        df_final.to_csv(archivo_salida_csv, index=False, encoding="utf-8")
        print(f"Extracción completada. Archivo generado: {archivo_salida_csv}")

if __name__ == "__main__":
    procesar_pedimentos_y_generar_csv("PEDIMENTOS 2025/PEDIMENTOS_VALIDOS", "salida/pedimentos_completo.csv")
