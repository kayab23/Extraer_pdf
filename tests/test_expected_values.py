import pandas as pd
import os

CSV = os.path.join(os.path.dirname(__file__), '..', 'salida', 'pedimentos_completo.csv')

EXPECTED_KEYWORDS = [
    'PARTES', 'ACCESORIOS', 'OXIGENOTERAPIA', 'MEZCLADOR', 'OXIGENO', 'HUMIDIFICADOR', 'NEBULIZADOR', 'MASCARILLA'
]


def test_fraccion_90192001_descriptions():
    if not os.path.exists(CSV):
        import pytest
        pytest.skip('CSV de salida no encontrado: ejecutar extracción primero')
    df = pd.read_csv(CSV, encoding='utf-8')
    if 'FRACCION' not in df.columns:
        import pytest
        pytest.skip('CSV no contiene columna FRACCION')
    sel = df[df['FRACCION'].astype(str).str.contains('90192001', na=False)]
    if sel.empty:
        import pytest
        pytest.skip('No hay filas con FRACCION=90192001 en el CSV')
    # Revisar que al menos una descripcion contiene una de las palabras esperadas
    def has_keyword(s):
        if not s or (not isinstance(s, str)):
            return False
        u = s.upper()
        return any(k in u for k in EXPECTED_KEYWORDS)
    matches = sel['DESCRIPCION'].astype(str).apply(has_keyword)
    assert matches.any(), 'Ninguna DESCRIPCION para FRACCION=90192001 contiene las palabras clave esperadas'
