"""
main.py
Script principal del avance de proyecto (primer corte).

Proyecto: Sistema inteligente para la planificación y optimización de rutas
de recolección y transporte de residuos (Cartago, Valle del Cauca).

Flujo:
    1. Cargar el CSV -> lista de diccionarios          (cargar_datos)
    2. Procesar: calcular indicadores por ruta          (procesamiento)
    3. EDA con NumPy: estadísticas y hallazgos          (eda_proyecto)
    4. Gráficos con Matplotlib -> PNG en data/          (eda_proyecto)
    5. Informe en Markdown                              (analisis_proyecto)

Ejecución (desde la raíz del proyecto):
    docker compose exec python python src/main.py
"""

from analisis_proyecto import calcular_estadisticas, generar_informe
from cargar_datos import leer_datos
from config import RUTA_CSV, RUTA_INFORME
from eda_proyecto import (
    MUESTRA_MINIMA,
    analizar_datos,
    contar_faltantes,
    generar_visualizaciones,
    identificar_hallazgos,
    imprimir_estadisticas,
)
from procesamiento import procesar_registros


def main():
    print("=" * 60)
    print("AVANCE DE PROYECTO - OPTIMIZACIÓN DE RUTAS DE RECOLECCIÓN")
    print("=" * 60)

    # 1. Cargar datos: CSV -> lista de diccionarios
    try:
        datos = leer_datos(RUTA_CSV)
        # 2. Procesar: cada diccionario recibe indicadores nuevos
        registros = procesar_registros(datos)
    except FileNotFoundError:
        print("Error: no se encontró el archivo de datos:", RUTA_CSV)
        return
    except (KeyError, ValueError, TypeError) as error:
        print("Error: el CSV no tiene el formato esperado ->", repr(error))
        return

    if len(registros) == 0:
        print("Error: el archivo de datos no tiene registros.")
        return

    print("\n[1-2] DATOS CARGADOS Y PROCESADOS")
    print("  Registros:", len(registros))
    print("  Columnas:", ", ".join(registros[0].keys()))
    print("  Valores faltantes:", contar_faltantes(registros) or "ninguno")

    # 3. EDA con NumPy
    print("\n[3] ESTADÍSTICAS DESCRIPTIVAS (NumPy)")
    imprimir_estadisticas(analizar_datos(registros))

    print("\n    HALLAZGOS")
    for numero, hallazgo in enumerate(identificar_hallazgos(registros), start=1):
        print("  " + str(numero) + ". " + hallazgo)
    if len(registros) < MUESTRA_MINIMA:
        print("  Nota: con solo " + str(len(registros)) + " registros los hallazgos son indicativos, no concluyentes.")

    # 4. Gráficos con Matplotlib
    print("\n[4] VISUALIZACIONES (Matplotlib)")
    generar_visualizaciones(registros)

    # 5. Informe en Markdown
    print("\n[5] INFORME")
    generar_informe(calcular_estadisticas(registros), RUTA_INFORME)
    print("  Informe generado:", RUTA_INFORME.name)

    print("\nAnálisis completado exitosamente.")


if __name__ == "__main__":
    main()
