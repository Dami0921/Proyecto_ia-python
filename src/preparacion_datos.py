"""
preparacion_datos.py
Carga, diagnóstico, limpieza y preparación de datos de rutas de recolección para ML.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Las rutas se calculan desde este archivo, así funciona desde cualquier carpeta
RUTA_CSV = Path(__file__).resolve().parent.parent / "data" / "rutas_clase8.csv"
DIR_DATA = RUTA_CSV.parent
sns.set_theme(style="whitegrid", context="talk")

COLUMNAS_NUMERICAS = ["toneladas", "km_recorridos", "combustible_tanqueado"]


def cargar_datos(ruta_csv):
    """Carga el CSV y retorna un DataFrame (o None si no existe)."""
    try:
        df = pd.read_csv(ruta_csv)
    except FileNotFoundError:
        print(f"Error: no existe '{ruta_csv}'.")
        return None
    print(f"Datos cargados: {df.shape[0]} filas, {df.shape[1]} columnas.")
    return df


def explorar_datos(df):
    """Muestra información general y estadísticas descriptivas."""
    print("\nPRIMERAS 5 FILAS:")
    print(df.head())
    print("\nINFORMACIÓN GENERAL:")
    df.info()
    print("\nESTADÍSTICAS DESCRIPTIVAS:")
    print(df.describe())
    print("\nVALORES NULOS POR COLUMNA:")
    print(df.isnull().sum())
    print(f"\nFILAS DUPLICADAS: {df.duplicated().sum()}")


def diagnosticar_calidad(df):
    """Revisa tipos, categorías, valores imposibles y atípicos (sin modificar nada)."""
    print("\nDIAGNÓSTICO DE CALIDAD")

    # 1. Tipos de datos: fecha y horas llegan como texto
    print("\n1. Tipos de datos (fecha y horas deberían ser fecha/hora):")
    print(df[["fecha", "hora_salida_base", "hora_inicio_ruta", "hora_fin_ruta"]].dtypes)

    # 2. Categorías inconsistentes: espacios o mayúsculas distintas
    print("\n2. Categorías de 'conductor' (valores únicos):")
    print(df["conductor"].value_counts())
    normalizado = df["conductor"].str.strip().str.title()
    print(f"   Sin normalizar: {df['conductor'].nunique()} | "
          f"normalizado: {normalizado.nunique()}")

    # 3. Valores imposibles
    inicio = pd.to_datetime(df["hora_inicio_ruta"], format="%H:%M")
    fin = pd.to_datetime(df["hora_fin_ruta"], format="%H:%M")
    print("\n3. Valores imposibles:")
    print(f"   toneladas <= 0:        {(df['toneladas'] <= 0).sum()}")
    print(f"   km_recorridos <= 0:    {(df['km_recorridos'] <= 0).sum()}")
    print(f"   tripulantes <= 0:      {(df['tripulantes'] <= 0).sum()}")
    print(f"   hora_fin <= hora_ini:  {(fin <= inicio).sum()}")

    # 4. Atípicos con el rango intercuartílico (IQR)
    print("\n4. Atípicos (regla 1.5 x IQR):")
    for columna in COLUMNAS_NUMERICAS:
        q1, q3 = df[columna].quantile([0.25, 0.75])
        iqr = q3 - q1
        atipicos = df[(df[columna] < q1 - 1.5 * iqr) | (df[columna] > q3 + 1.5 * iqr)]
        print(f"   {columna}: {len(atipicos)} atípicos")


def limpiar_datos(df):
    """Elimina duplicados, corrige tipos y categorías, imputa nulos y crea derivadas."""
    df_limpio = df.copy()

    # 1. Duplicados
    antes = len(df_limpio)
    df_limpio = df_limpio.drop_duplicates()
    print(f"Duplicados eliminados: {antes - len(df_limpio)}")

    # 2. Tipos: fecha como datetime
    df_limpio["fecha"] = pd.to_datetime(df_limpio["fecha"], format="%Y-%m-%d")

    # 3. Categorías: quitar espacios y unificar mayúsculas
    df_limpio["conductor"] = df_limpio["conductor"].str.strip().str.title()

    # 4. Nulos: mediana en variables de entrada (no se imputa 'toneladas')
    for columna in ["km_recorridos", "combustible_tanqueado"]:
        mediana = df_limpio[columna].median()
        df_limpio[columna] = df_limpio[columna].fillna(mediana)
        print(f"Nulos de '{columna}' imputados con la mediana: {mediana}")

    # 5. Columnas derivadas
    inicio = pd.to_datetime(df_limpio["hora_inicio_ruta"], format="%H:%M")
    fin = pd.to_datetime(df_limpio["hora_fin_ruta"], format="%H:%M")
    df_limpio["duracion_ruta_min"] = (fin - inicio).dt.total_seconds() / 60
    df_limpio["toneladas_por_km"] = df_limpio["toneladas"] / df_limpio["km_recorridos"]
    print("Columnas 'duracion_ruta_min' y 'toneladas_por_km' creadas.")

    return df_limpio


def tabla_antes_despues(df_original, df_limpio):
    """Tabla comparativa: filas, columnas y nulos antes y después de limpiar."""
    tabla = pd.DataFrame({
        "Antes": [df_original.shape[0], df_original.shape[1],
                  int(df_original.isnull().sum().sum()), int(df_original.duplicated().sum())],
        "Después": [df_limpio.shape[0], df_limpio.shape[1],
                    int(df_limpio.isnull().sum().sum()), int(df_limpio.duplicated().sum())],
    }, index=["Filas", "Columnas", "Nulos (total)", "Duplicados"])
    print("\nTABLA ANTES / DESPUÉS:")
    print(tabla)
    tabla.to_csv(DIR_DATA / "tabla_antes_despues.csv")
    return tabla


def visualizar_datos(df):
    """Genera 3 visualizaciones con Seaborn y las guarda en data/."""

    # 1. Distribución de toneladas recolectadas
    plt.figure(figsize=(8, 5))
    sns.histplot(data=df, x="toneladas", bins=6, kde=True, color="skyblue")
    plt.title("Distribución de Toneladas por Ruta")
    plt.xlabel("Toneladas")
    plt.ylabel("Frecuencia")
    plt.tight_layout()
    plt.savefig(DIR_DATA / "distribucion_toneladas_clase8.png", dpi=150)
    plt.close()

    # 2. Total de toneladas por conductor
    plt.figure(figsize=(9, 6))
    sns.barplot(data=df, x="conductor", y="toneladas", estimator="sum",
                errorbar=None, hue="conductor", palette="viridis", legend=False)
    plt.title("Toneladas Totales por Conductor")
    plt.xlabel("Conductor")
    plt.ylabel("Toneladas")
    plt.tight_layout()
    plt.savefig(DIR_DATA / "toneladas_por_conductor.png", dpi=150)
    plt.close()

    # 3. Relación entre km recorridos y toneladas (entrada vs objetivo)
    plt.figure(figsize=(9, 6))
    sns.scatterplot(data=df, x="km_recorridos", y="toneladas",
                    hue="conductor", s=120)
    plt.title("Km Recorridos vs Toneladas")
    plt.xlabel("Km recorridos")
    plt.ylabel("Toneladas")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(DIR_DATA / "km_vs_toneladas_clase8.png", dpi=150)
    plt.close()

    print("\nGráficos guardados en data/.")


def preparar_ml(df):
    """Prepara el DataFrame para ML: codificación y selección de columnas."""
    df_ml = df.copy()

    # One-Hot Encoding para 'conductor' (variable nominal)
    df_ml = pd.get_dummies(df_ml, columns=["conductor"], prefix="cond", dtype=int)
    print("\nCodificación One-Hot aplicada a 'conductor'.")

    columnas_a_eliminar = [
        "ruta_id",            # identificador, sin valor predictivo
        "fecha",
        "hora_salida_base",
        "hora_inicio_ruta",
        "hora_fin_ruta",
        "toneladas_por_km",   # se calcula con 'toneladas': data leakage
    ]
    df_ml = df_ml.drop(columns=columnas_a_eliminar, errors="ignore")

    print(f"Forma final: {df_ml.shape[0]} filas, {df_ml.shape[1]} columnas.")
    return df_ml


def main():
    df = cargar_datos(RUTA_CSV)
    if df is None:
        return
    explorar_datos(df)
    diagnosticar_calidad(df)

    df_limpio = limpiar_datos(df)
    tabla_antes_despues(df, df_limpio)

    # Dataset limpio para análisis y para el perceptrón
    df_limpio.to_csv(DIR_DATA / "proyecto_limpio.csv", index=False)
    print(f"\nDataset limpio guardado en '{DIR_DATA / 'proyecto_limpio.csv'}'.")

    visualizar_datos(df_limpio)

    df_ml = preparar_ml(df_limpio)
    df_ml.to_csv(DIR_DATA / "rutas_preparadas_ml.csv", index=False)
    print(f"Dataset para ML guardado en '{DIR_DATA / 'rutas_preparadas_ml.csv'}'.")
    print("Proceso completado exitosamente.")


if __name__ == "__main__":
    main()