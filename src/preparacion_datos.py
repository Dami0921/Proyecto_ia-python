"""
preparacion_datos.py
Limpieza y preparación del histórico de rutas de recolección (Cartago, Valle del Cauca).

Entrada : data/datos_originales.csv  (estructura del Excel de la empresa; datos SIMULADOS)
Salidas : data/datos_limpios.csv     (dataset listo para modelar)
          graficos/*.png             (3 gráficos de análisis con Seaborn)

Criterio de diseño: aquí solo se corrigen errores de digitación y de formato.
Las imputaciones que "aprenden" de los datos (medianas, escalado) NO se hacen aquí,
sino dentro del Pipeline de modelo_proyecto.py y solo con datos de entrenamiento,
para evitar fuga de información (data leakage).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # guarda gráficos sin pantalla (contenedor Docker)
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE = Path(__file__).resolve().parent.parent
RUTA_ORIGINAL = BASE / "data" / "datos_originales.csv"
RUTA_LIMPIO = BASE / "data" / "datos_limpios.csv"
DIR_GRAFICOS = BASE / "graficos"

KG_MAXIMO = 20000          # un camión compactador no carga más de ~20 t en una ruta
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def a_minutos(serie):
    """Convierte texto 'H:MM' (hora o duración) en minutos; vacío -> NaN."""
    partes = serie.str.split(":", expand=True).apply(pd.to_numeric, errors="coerce")
    return partes[0] * 60 + partes[1]


def cargar_datos(ruta=RUTA_ORIGINAL):
    """Lee el CSV original sin modificarlo (las fechas llegan como texto dd/mm/aaaa)."""
    return pd.read_csv(ruta)


def diagnosticar(df):
    """Muestra la evidencia de cada problema de calidad antes de corregirlo."""
    print("=== Diagnóstico de calidad ===")
    print(f"Forma: {df.shape}")
    print(f"Filas completamente duplicadas: {df.duplicated().sum()}")
    print(f"Tickets de báscula repetidos:   {df['TICKET DE BASCULA'].duplicated().sum()}")
    print(f"Viajes de apoyo (APOYO = X):    {(df['APOYO'] == 'X').sum()}")
    print("Valores de DIA:", sorted(df["DIA"].unique()))
    print("Nulos por columna (solo las que tienen):")
    nulos = df.isnull().sum()
    print(nulos[nulos > 0].to_string())
    kg = df["KILOGRAMOS RECOLECTADOS"]
    print(f"Kilogramos: mín {kg.min():,.0f} | mediana {kg.median():,.0f} | máx {kg.max():,.0f}")
    print(df.loc[kg > KG_MAXIMO, ["FECHA", "RUTA", "KILOGRAMOS RECOLECTADOS"]].to_string())


def limpiar_datos(df):
    """Corrige los problemas de calidad documentados. Devuelve el DataFrame y un resumen."""
    resumen = {"filas_originales": len(df)}
    df = df.copy()

    # 1. Filas duplicadas (mismo registro digitado dos veces)
    antes = len(df)
    df = df.drop_duplicates()
    resumen["duplicados_eliminados"] = antes - len(df)

    # 2. Viajes de apoyo: otro tipo de servicio (pocos kg, sin viaje al relleno)
    antes = len(df)
    df = df[df["APOYO"].fillna("") != "X"]
    resumen["apoyos_excluidos"] = antes - len(df)

    # 3. Kilogramos imposibles (error de digitación): se eliminan, la variable objetivo no se imputa
    antes = len(df)
    df = df[df["KILOGRAMOS RECOLECTADOS"] <= KG_MAXIMO]
    resumen["kg_imposibles_eliminados"] = antes - len(df)

    resumen["filas_finales"] = len(df)
    return df.reset_index(drop=True), resumen


def construir_variables(df):
    """Convierte tipos y crea las variables del modelo (sin imputar nada)."""
    fecha = pd.to_datetime(df["FECHA"], format="%d/%m/%Y")
    hora_inicio = a_minutos(df["HORA DE INICIO DE RUTA"])
    limpio = pd.DataFrame({
        "fecha": fecha,
        "mes": fecha.dt.month,
        "dia_semana": fecha.dt.day_of_week,                    # 0 = lunes; reemplaza la columna DIA digitada
        "ruta": df["RUTA"].astype(str),
        "vehiculo": df["VEHICULO"].astype(str),
        "turno_noche": ((hora_inicio >= 18 * 60) | (hora_inicio < 5 * 60)).astype(int),
        "n_tripulantes": df["TRIPULANTES"].str.split("-").str.len(),
        "compactado": df["COMPACTADO"],
        "kg_planeados": df["KG PLANEADOS"],
        "km_planeados": df["KM PLANEADOS"],
        "t_ruta_planeado_min": a_minutos(df["T. RUTA PLANEADO"]),
        "toneladas": df["KILOGRAMOS RECOLECTADOS"] / 1000,
        "km_recorridos": df["KM RECORRIDOS"],
        "tiempo_ruta_min": a_minutos(df["TIEMPOS DE RUTA"]),
        "tiempo_total_min": a_minutos(df["TIEMPO TOTAL"]),
        "combustible_gal": df["COMBUSTIBLE"],
    })
    return limpio


def graficar(df):
    """Tres gráficos de análisis con Seaborn en graficos/."""
    DIR_GRAFICOS.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid")
    nombres_mes = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    # Gráfico 1: estacionalidad (toneladas promedio por mes)
    plt.figure(figsize=(8, 4.5))
    por_mes = df.groupby("mes")["toneladas"].mean().reindex(range(1, 13))
    sns.barplot(x=nombres_mes, y=por_mes.values, color="tab:green")
    plt.axhline(df["toneladas"].median(), color="black", linestyle="--", label="Mediana (umbral)")
    plt.title("Toneladas promedio por mes")
    plt.xlabel("Mes")
    plt.ylabel("Toneladas por ruta")
    plt.legend()
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico1_toneladas_por_mes.png", dpi=150)
    plt.close()

    # Gráfico 2: distribución de toneladas por ruta
    plt.figure(figsize=(8, 4.5))
    orden = sorted(df["ruta"].unique())
    sns.boxplot(data=df, x="ruta", y="toneladas", order=orden, color="tab:green")
    plt.title("Toneladas recolectadas por ruta")
    plt.xlabel("Ruta")
    plt.ylabel("Toneladas")
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico2_toneladas_por_ruta.png", dpi=150)
    plt.close()

    # Gráfico 3: relación duración de la ruta vs toneladas, por turno
    plt.figure(figsize=(8, 4.5))
    sns.scatterplot(data=df, x="tiempo_ruta_min", y="toneladas", hue="turno_noche",
                    palette="Set1", s=60)
    plt.title("Duración de la ruta vs toneladas")
    plt.xlabel("Duración de la ruta (min)")
    plt.ylabel("Toneladas")
    plt.legend(title="Turno noche (1 = sí)")
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico3_duracion_vs_toneladas.png", dpi=150)
    plt.close()
    print(f"Gráficos guardados en {DIR_GRAFICOS.name}/")


def main():
    original = cargar_datos()
    diagnosticar(original)
    limpio, resumen = limpiar_datos(original)
    print("\n=== Resumen de la limpieza ===")
    for clave, valor in resumen.items():
        print(f"{clave}: {valor}")
    df = construir_variables(limpio)
    print("\n=== Dataset limpio ===")
    print(df.dtypes)
    print("Nulos restantes (se imputan dentro del Pipeline, solo con entrenamiento):")
    print(df.isnull().sum()[df.isnull().sum() > 0].to_string())
    print(f"Toneladas: mediana {df['toneladas'].median():.2f} | mín {df['toneladas'].min():.2f} | máx {df['toneladas'].max():.2f}")
    df.to_csv(RUTA_LIMPIO, index=False)
    print(f"\nGuardado: {RUTA_LIMPIO}")
    graficar(df)


if __name__ == "__main__":
    main()