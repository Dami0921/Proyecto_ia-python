"""
eda_proyecto.py
Analisis Exploratorio de Datos (EDA) del proyecto de optimizacion de rutas de
recoleccion de residuos, usando NumPy y Matplotlib.

Reutiliza:
    - cargar_datos.leer_datos            -> CSV a lista de diccionarios
    - procesamiento.procesar_registros   -> agrega indicadores por ruta
"""

import matplotlib

matplotlib.use("Agg")  # Docker no tiene pantalla: los graficos se guardan como PNG
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

from cargar_datos import leer_datos
from config import DIR_DATOS, RUTA_CSV
from procesamiento import procesar_registros

# Variables numericas que se analizan: nombre de columna -> etiqueta legible
VARIABLES = {
    "toneladas": "Toneladas recolectadas",
    "km_recorridos": "Kilómetros recorridos",
    "combustible_tanqueado": "Combustible tanqueado (galones)",
    "duracion_ruta_horas": "Duración de la ruta (horas)",
    "toneladas_por_hora": "Toneladas por hora",
    "km_por_galon": "Kilómetros por galón",
}

# Con menos registros que este umbral los hallazgos son solo indicativos
MUESTRA_MINIMA = 30

# Etiquetas legibles para las estadisticas
ETIQUETAS_STATS = {
    "media": "Media",
    "mediana": "Mediana",
    "desviacion": "Desviación estándar",
    "minimo": "Mínimo",
    "maximo": "Máximo",
}


# ---------------------------------------------------------------------------
# Preparacion de datos
# ---------------------------------------------------------------------------
def extraer_columna(registros, columna):
    """Devuelve un array de NumPy (float) con los valores de una columna, omitiendo faltantes."""
    valores = []
    for fila in registros:
        valor = fila.get(columna)
        if valor is not None and valor != "":
            valores.append(valor)
    return np.array(valores, dtype=float)


def contar_faltantes(registros):
    """
    Cuenta cuantos valores vacios (None o '') hay por columna.
    Devuelve solo las columnas con faltantes; un diccionario vacio significa
    que los datos estan completos.
    """
    faltantes = {}
    for fila in registros:
        for columna, valor in fila.items():
            if valor is None or valor == "":
                faltantes[columna] = faltantes.get(columna, 0) + 1
    return faltantes


# ---------------------------------------------------------------------------
# Estadisticas con NumPy
# ---------------------------------------------------------------------------
def analizar_variable(valores):
    """
    Estadisticas descriptivas de un array. La desviacion es poblacional
    (np.std con ddof=0, igual que en clase).
    """
    return {
        "media": np.mean(valores),
        "mediana": np.median(valores),
        "desviacion": np.std(valores),
        "minimo": np.min(valores),
        "maximo": np.max(valores),
    }


def analizar_datos(registros):
    """Calcula las estadisticas de todas las variables definidas en VARIABLES."""
    estadisticas = {}
    for columna in VARIABLES:
        valores = extraer_columna(registros, columna)
        if len(valores) > 0:
            estadisticas[columna] = analizar_variable(valores)
    return estadisticas


def calcular_correlacion(x, y):
    """Coeficiente de correlacion de Pearson entre dos arrays (entre -1 y 1)."""
    return float(np.corrcoef(x, y)[0, 1])


def describir_correlacion(r):
    """Traduce r a palabras. Ej: 0.78 -> 'fuerte positiva'."""
    fuerza = abs(r)
    if fuerza >= 0.7:
        intensidad = "fuerte"
    elif fuerza >= 0.4:
        intensidad = "moderada"
    else:
        intensidad = "débil"
    signo = "positiva" if r >= 0 else "negativa"
    return intensidad + " " + signo


def promedio_por_grupo(registros, columna_grupo, columna_valor):
    """
    Promedio de columna_valor para cada valor distinto de columna_grupo.
    Devuelve {valor_grupo: (promedio, cantidad_de_rutas)}.
    """
    grupos = {}
    for fila in registros:
        grupos.setdefault(fila[columna_grupo], []).append(fila[columna_valor])

    resultado = {}
    for grupo, valores in sorted(grupos.items()):
        resultado[grupo] = (float(np.mean(valores)), len(valores))
    return resultado


# ---------------------------------------------------------------------------
# Hallazgos
# ---------------------------------------------------------------------------
def identificar_hallazgos(registros):
    """
    Devuelve una lista de frases con hallazgos calculados a partir de los datos.
    Al estar calculados (no escritos a mano) se actualizan solos cuando se
    cargue el historico real de la empresa.
    """
    hallazgos = []

    toneladas = extraer_columna(registros, "toneladas")
    km = extraer_columna(registros, "km_recorridos")
    duracion = extraer_columna(registros, "duracion_ruta_horas")
    combustible = extraer_columna(registros, "combustible_tanqueado")
    km_galon = extraer_columna(registros, "km_por_galon")

    # 1. Que explica la carga recolectada: distancia y duracion
    r_km = calcular_correlacion(km, toneladas)
    r_dur = calcular_correlacion(duracion, toneladas)
    hallazgos.append(
        "Las toneladas recolectadas tienen correlación "
        + describir_correlacion(r_km) + " con los km recorridos (r = " + str(round(r_km, 2)) + ") y "
        + describir_correlacion(r_dur) + " con la duración de la ruta (r = " + str(round(r_dur, 2)) + ")."
    )

    # 2. Efecto del tamaño de la tripulacion
    por_tripulacion = promedio_por_grupo(registros, "tripulantes", "toneladas")
    if len(por_tripulacion) > 1:
        partes = []
        for tripulantes, (promedio, cantidad) in por_tripulacion.items():
            partes.append(
                str(tripulantes) + " tripulantes: " + str(round(promedio, 2)) + " t (" + str(cantidad) + " rutas)"
            )
        hallazgos.append("Toneladas promedio según tripulación → " + "; ".join(partes) + ".")

    # 3. Consumo de combustible
    cv = np.std(km_galon) / np.mean(km_galon)  # coeficiente de variacion
    r_comb = calcular_correlacion(km, combustible)
    estabilidad = "muy estable" if cv < 0.05 else "variable"
    hallazgos.append(
        "El rendimiento de combustible es " + estabilidad + ": "
        + str(round(float(np.mean(km_galon)), 2)) + " km/galón en promedio (variación de "
        + str(round(float(cv) * 100, 1)) + " %) y el combustible tiene correlación "
        + describir_correlacion(r_comb) + " con los km (r = " + str(round(r_comb, 2)) + ")."
    )

    return hallazgos


# ---------------------------------------------------------------------------
# Visualizacion con Matplotlib
# ---------------------------------------------------------------------------
def generar_visualizaciones(registros):
    """Genera 3 graficos (barras, histograma y dispersion) y los guarda como PNG en data/."""
    toneladas = extraer_columna(registros, "toneladas")
    km = extraer_columna(registros, "km_recorridos")

    # 1. Barras: toneladas por ruta, con el promedio como referencia
    etiquetas = []
    for fila in registros:
        etiquetas.append("Ruta " + str(fila["ruta_id"]) + "\n" + str(fila["fecha"])[5:])

    promedio = float(np.mean(toneladas))
    plt.figure(figsize=(9, 5))
    barras = plt.bar(etiquetas, toneladas, color="steelblue", edgecolor="black")
    plt.bar_label(barras, fmt="%.1f")
    plt.axhline(promedio, color="red", linestyle="--", label="Promedio (" + str(round(promedio, 2)) + " t)")
    plt.title("Toneladas recolectadas por ruta")
    plt.xlabel("Ruta (mes-día)")
    plt.ylabel("Toneladas")
    plt.legend()
    plt.grid(True, axis="y", linestyle="--", alpha=0.5)
    plt.savefig(DIR_DATOS / "toneladas_por_ruta.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Histograma: distribucion de toneladas recolectadas
    plt.figure(figsize=(8, 5))
    plt.hist(toneladas, bins="auto", color="orange", edgecolor="black")
    plt.title("Distribución de toneladas recolectadas por ruta (n = " + str(len(toneladas)) + ")")
    plt.xlabel("Toneladas")
    plt.ylabel("Frecuencia (número de rutas)")
    plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))  # conteos enteros
    plt.grid(True, axis="y", linestyle="--", alpha=0.7)
    plt.savefig(DIR_DATOS / "distribucion_toneladas.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 3. Dispersion: km recorridos vs toneladas, con linea de tendencia
    plt.figure(figsize=(8, 6))
    plt.scatter(km, toneladas, color="green", alpha=0.7, s=70, label="Rutas")
    if len(km) >= 3:
        pendiente, intercepto = np.polyfit(km, toneladas, 1)
        r = calcular_correlacion(km, toneladas)
        eje_x = np.linspace(km.min(), km.max(), 50)
        plt.plot(eje_x, pendiente * eje_x + intercepto, "r--",
                 label="Tendencia lineal (r = " + str(round(r, 2)) + ")")
    plt.title("Relación: kilómetros recorridos vs toneladas recolectadas")
    plt.xlabel("Kilómetros recorridos")
    plt.ylabel("Toneladas")
    plt.legend()
    plt.grid(True)
    plt.savefig(DIR_DATOS / "km_vs_toneladas.png", dpi=150, bbox_inches="tight")
    plt.close()

    print("Gráficas guardadas en data/: toneladas_por_ruta.png, "
          "distribucion_toneladas.png, km_vs_toneladas.png")


# ---------------------------------------------------------------------------
# Ejecucion independiente: python eda_proyecto.py
# ---------------------------------------------------------------------------
def imprimir_estadisticas(estadisticas):
    """Muestra las estadisticas en consola de forma legible."""
    for columna, valores in estadisticas.items():
        print("\n" + VARIABLES[columna].upper() + ":")
        for nombre_stat, valor in valores.items():
            print("  " + ETIQUETAS_STATS[nombre_stat] + ": " + str(round(float(valor), 2)))


def main():
    print("=" * 50)
    print("ANÁLISIS EXPLORATORIO DE DATOS (EDA) - PROYECTO DE RUTAS")
    print("=" * 50)

    registros = procesar_registros(leer_datos(RUTA_CSV))
    print("Registros cargados:", len(registros))

    print("Valores faltantes:", contar_faltantes(registros) or "ninguno")

    imprimir_estadisticas(analizar_datos(registros))

    print("\nHALLAZGOS:")
    for numero, hallazgo in enumerate(identificar_hallazgos(registros), start=1):
        print(" " + str(numero) + ". " + hallazgo)
    if len(registros) < MUESTRA_MINIMA:
        print(" Nota: con solo " + str(len(registros)) + " registros estos hallazgos son indicativos, no concluyentes.")

    print("\nGENERANDO VISUALIZACIONES...")
    generar_visualizaciones(registros)


if __name__ == "__main__":
    main()
