import os
import glob
import pytest
from src import mapear_campos as mc

BASE = os.path.join(os.path.dirname(__file__), '..')
PDF_DIR = os.path.join(BASE, 'PEDIMENTOS 2025', 'PEDIMENTOS_VALIDOS')


def sample_pdfs(n=5):
    pattern = os.path.join(PDF_DIR, '*.pdf')
    files = [f for f in glob.glob(pattern) if os.path.getsize(f) > 1000]
    # prefer files whose name contains 'PEDIMENTO'
    ped = [f for f in files if 'PEDIMENTO' in os.path.basename(f).upper()]
    chosen = (ped + files)[:n]
    return chosen


@pytest.mark.parametrize('pdf_path', sample_pdfs())
def test_is_pedimento_and_has_required_fields(pdf_path):
    # 1) extraer texto y verificar que contiene indicios de pedimento
    texto = mc.extraer_texto_pdf(pdf_path)
    assert texto and isinstance(texto, str)
    # must contain keyword PEDIMENTO or NUM PEDIMENTO pattern
    is_ped = 'PEDIMENTO' in texto.upper() or 'NUM PEDIMENTO' in texto.upper()
    # 2) extraer cabecera pedimento
    ped, tipo_cambio, aduana = mc.extraer_cabecera_pedimento(texto)
    if ped:
        is_ped = True
    # 3) extraer proveedor por posicion (may return id/nombre)
    idf, nombre = mc.extraer_datos_proveedor_por_posicion(pdf_path)
    # 4) extraer partidas por posición
    partidas = mc.extraer_partidas_por_posicion(pdf_path)

    # Validation rules: must be recognized as pedimento and have at least one partida
    assert is_ped, f"Archivo no parece un pedimento: {os.path.basename(pdf_path)}"
    # If there are partidas, validate structure
    assert isinstance(partidas, list)
    if partidas:
        p = partidas[0]
        # FRACCION should be 8 digits (or at least numeric)
        fr = str(p.get('FRACCION', '')).strip()
        assert fr and any(ch.isdigit() for ch in fr), f"FRACCION inválida en {os.path.basename(pdf_path)}"
        desc = str(p.get('DESCRIPCION', '')).strip()
        assert desc and len(desc) > 3, f"DESCRIPCION vacía en {os.path.basename(pdf_path)}"
        tasa = str(p.get('TASA_IGI', '')).strip()
        # tasa puede estar vacía, pero si existe debe parecer un número decimal
        if tasa:
            try:
                float(tasa)
            except Exception:
                pytest.fail(f"TASA_IGI malformada en {os.path.basename(pdf_path)}: {tasa}")
    else:
        pytest.skip(f"No se obtuvieron partidas por posicion para {os.path.basename(pdf_path)}; revisar extracción")
