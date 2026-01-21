from src.mapear_campos import procesar_pedimentos_en_carpeta_integral

if __name__ == "__main__":
    procesar_pedimentos_en_carpeta_integral(
        "PEDIMENTOS 2025/PEDIMENTOS_VALIDOS",
        "salida/pedimentos_integral.csv",
        "salida/pedimentos_integral.json"
    )
