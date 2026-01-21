# MEJORAS Y LIMPIEZA DEL PROYECTO

## Resumen de Mejoras Realizadas

1. **Extracción precisa de NOMBRE_PROVEEDOR:**
   - Se mejoró la función para eliminar RFC, VAT, ID fiscal y cualquier código antes o después del nombre, dejando solo la razón social.
   - Se ajustaron los patrones regex para mayor precisión y limpieza.

2. **Procesamiento masivo robusto:**
   - El script procesa todos los PDFs de la carpeta objetivo, maneja errores y genera archivos de salida JSON y CSV.
   - Se documentó el flujo de procesamiento y se mejoró la tolerancia a errores.

3. **Estructura de salida clara:**
   - El CSV final contiene los campos requeridos: archivo, NUM_PEDIMENTO, TIPO_CAMBIO, ADUANA_ES, ID_FISCAL, NOMBRE_PROVEEDOR, VAL_DOLARES, SEC, FRACCION, DESCRIPCION, IGI.
   - Se eliminan duplicados y se normalizan los datos.

4. **Documentación y scripts auxiliares:**
   - Se documentaron los cambios y el flujo de trabajo.
   - Se recomienda validar el CSV final y realizar revisión manual para casos atípicos.

## Limpieza del Proyecto

- Se eliminaron archivos temporales y de prueba innecesarios.
- Se recomienda mantener solo los siguientes archivos y carpetas:
  - `src/` (código fuente)
  - `salida/` (resultados finales)
  - `requirements.txt` (dependencias)
  - `README.md` (instrucciones y resumen)
  - `.gitignore` (excluir archivos temporales, .venv, __pycache__)

## Recomendaciones para el Repositorio

- Agregar README.md con instrucciones de uso, dependencias y ejemplos.
- Incluir un .gitignore adecuado.
- Mantener la documentación de mejoras y limitaciones.
- Validar el CSV antes de uso productivo.

---

Proyecto listo para subir a repositorio.
