"""
eda_proyecto.py
Actividad independiente: Analisis Exploratorio de Datos (EDA) del proyecto
de optimizacion de rutas de recoleccion de residuos, usando NumPy y Matplotlib.
"""

import csv
import numpy as np
import matplotlib.pyplot as plt


def cargar_datos(archivo_csv):
    """
    Lee el CSV de rutas y devuelve:
        - un array de NumPy con las columnas numericas de interes
          (toneladas y km_recorridos)
        - la lista completa de registros (como diccionarios)
    """
    registros = []

    archivo = open(archivo_csv, "r", encoding="utf-8")
    lector = csv.DictReader(archivo)

    for fila in lector:
        registros.append(fila)

    archivo.close()

    toneladas = []
    kilometros = []
    for fila in registros:
        toneladas.append(float(fila["toneladas"]))
        kilometros.append(float(fila["km_recorridos"]))

    # Armamos una matriz de 2 columnas: [toneladas, km_recorridos]
    datos_numericos = np.array([toneladas, kilometros]).T

    print("Datos cargados correctamente:", len(registros), "registros.")
    return datos_numericos, registros


def analizar_datos(datos_numericos):
    """Calcula media, mediana, desviacion, minimo y maximo de cada variable."""
    toneladas = datos_numericos[:, 0]
    kilometros = datos_numericos[:, 1]

    estadisticas = {
        "toneladas": {
            "media": np.mean(toneladas),
            "mediana": np.median(toneladas),
            "desviacion": np.std(toneladas),
            "minimo": np.min(toneladas),
            "maximo": np.max(toneladas),
        },
        "km_recorridos": {
            "media": np.mean(kilometros),
            "mediana": np.median(kilometros),
            "desviacion": np.std(kilometros),
            "minimo": np.min(kilometros),
            "maximo": np.max(kilometros),
        },
    }

    return estadisticas


def generar_visualizaciones(datos_numericos):
    """Genera un histograma y un grafico de dispersion, guardados como PNG."""
    toneladas = datos_numericos[:, 0]
    kilometros = datos_numericos[:, 1]

    # 1. Histograma: distribucion de toneladas recolectadas
    plt.figure(figsize=(8, 5))
    plt.hist(toneladas, bins=5, color="orange", edgecolor="black")
    plt.title("Distribucion de toneladas recolectadas por ruta")
    plt.xlabel("Toneladas")
    plt.ylabel("Frecuencia")
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.savefig("../data/distribucion_toneladas.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Dispersion: toneladas vs kilometros recorridos
    plt.figure(figsize=(8, 6))
    plt.scatter(kilometros, toneladas, color="green", alpha=0.7)
    plt.title("Relacion: Kilometros recorridos vs Toneladas recolectadas")
    plt.xlabel("Kilometros recorridos")
    plt.ylabel("Toneladas")
    plt.grid(True)
    plt.savefig("../data/km_vs_toneladas.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("Graficas guardadas: data/distribucion_toneladas.png, data/km_vs_toneladas.png")


def main():
    print("=" * 50)
    print("ANALISIS EXPLORATORIO DE DATOS (EDA) - PROYECTO DE RUTAS")
    print("=" * 50)

    datos_numericos, registros = cargar_datos("../data/rutas_ejemplo.csv")

    estadisticas = analizar_datos(datos_numericos)

    print("\nESTADISTICAS DESCRIPTIVAS:")
    print("-" * 40)
    for variable, valores in estadisticas.items():
        print("\n" + variable.upper() + ":")
        for nombre_stat, valor in valores.items():
            print("  " + nombre_stat.capitalize() + ": " + str(round(valor, 2)))

    print("\nGENERANDO VISUALIZACIONES...")
    generar_visualizaciones(datos_numericos)

    print("\nAnalisis completado exitosamente.")


if __name__ == "__main__":
    main()