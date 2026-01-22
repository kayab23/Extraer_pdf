Pruebas automáticas (pytest)

Objetivo:
- Validar que los PDFs representativos en `PEDIMENTOS 2025/PEDIMENTOS_VALIDOS` sean identificados como pedimentos y que las partidas extraídas contengan los campos requeridos (`FRACCION`, `DESCRIPCION`, `TASA_IGI`).

Instrucciones:
1. Activar el entorno virtual:

```powershell
& .venv\Scripts\Activate.ps1
```

2. Instalar dependencias de pruebas (si no están instaladas):

```powershell
pip install pytest
```

3. Ejecutar las pruebas:

```powershell
pytest -q
```

Notas:
- Las pruebas seleccionan hasta 5 PDFs representativos desde `PEDIMENTOS 2025/PEDIMENTOS_VALIDOS`.
- Si una prueba no obtiene partidas por posición, se marca como "skipped" para indicar que hay que revisar esa extracción en particular.
- Añade o reemplaza PDFs en la carpeta mencionada para ampliar el coverage de pruebas.
