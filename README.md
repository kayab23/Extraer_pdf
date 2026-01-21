# Extractor de Pedimentos - Documentación

## Descripción

Este proyecto permite extraer información estructurada de pedimentos aduanales en PDF, generando un archivo CSV con los campos clave para análisis y control documental.

## Uso rápido

1. Instala dependencias:
   ```
   pip install -r requirements.txt
   ```
2. Ejecuta el extractor:
   ```
   .venv\Scripts\python.exe src\mapear_campos.py
   ```
3. Revisa los resultados en la carpeta `salida/`.

## Estructura de salida

- `salida_pedimentos.json`: Datos estructurados extraídos.
- `salida_pedimentos.csv`: Archivo tabular listo para Excel.

## Campos extraídos
- NUM_PEDIMENTO
- TIPO_CAMBIO
- ADUANA_ES
- ID_FISCAL
- NOMBRE_PROVEEDOR
- VAL_DOLARES
- SEC
- FRACCION
- DESCRIPCION
- IGI

## Notas y recomendaciones
- El campo NOMBRE_PROVEEDOR se limpia automáticamente para eliminar RFC, VAT, ID fiscal y dejar solo la razón social.
- Se recomienda validar el CSV final y revisar manualmente casos atípicos.
- Para agregar nuevos PDFs, colócalos en la carpeta de entrada y vuelve a ejecutar el script.

## Créditos y mejoras
- Mejora y robustez por Fernando Olvera Rendón y GitHub Copilot (GPT-4.1).
