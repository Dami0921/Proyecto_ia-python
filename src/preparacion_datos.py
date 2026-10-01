"""
preparacion_datos.py
Carga, limpieza y preparación de datos de rutas de recolección para ML.
"""
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# La ruta se calcula desde este archivo, así funciona desde cualquier carpeta
RUTA_CSV = Path(__file__).resolve().parent.parent / "data" / "rutas_clase8.csv"

DIR_DATA = RUTA_CSV.parent
sns.set_theme(style="whitegrid", context="talk")

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


def limpiar_datos(df):
    """Imputa nulos y crea columnas derivadas."""
    df_limpio = df.copy()

    # 1. Imputar nulos con la mediana (solo variables de entrada, no 'toneladas')
    for columna in ["km_recorridos", "combustible_tanqueado"]:
        mediana = df_limpio[columna].median()
        df_limpio[columna] = df_limpio[columna].fillna(mediana)
        print(f"Nulos de '{columna}' imputados con la mediana: {mediana}")

    # 2. Columna derivada: duración de la ruta en minutos
    inicio = pd.to_datetime(df_limpio["hora_inicio_ruta"], format="%H:%M")
    fin = pd.to_datetime(df_limpio["hora_fin_ruta"], format="%H:%M")
    df_limpio["duracion_ruta_min"] = (fin - inicio).dt.total_seconds() / 60
    print("Columna 'duracion_ruta_min' creada.")

    # 3. Columna derivada: rendimiento de recolección
    df_limpio["toneladas_por_km"] = df_limpio["toneladas"] / df_limpio["km_recorridos"]

    print("Columna 'toneladas_por_km' creada.")

    return df_limpio

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

    # 3. Relación entre km recorridos y toneladas
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

    # 1. One-Hot Encoding para 'conductor' (variable nominal)
    df_ml = pd.get_dummies(df_ml, columns=["conductor"], prefix="cond", dtype=int)
    print("\nCodificación One-Hot aplicada a 'conductor'.")

    # 2. Eliminar columnas que no sirven como variables de entrada
    columnas_a_eliminar = [
        "ruta_id",            # identificador, no tiene significado predictivo
        "fecha",              # texto; si se necesita, se derivan mes o día de semana
        "hora_salida_base",   # texto; su información útil ya está en duracion_ruta_min
        "hora_inicio_ruta",
        "hora_fin_ruta",
        "toneladas_por_km",   # se calcula con 'toneladas' (el objetivo): data leakage
    ]
    df_ml = df_ml.drop(columns=columnas_a_eliminar, errors="ignore")
    print("Columnas no útiles eliminadas.")

    print("\nDATAFRAME LISTO PARA MACHINE LEARNING (primeras 5 filas):")
    print(df_ml.head())
    print(f"\nForma final: {df_ml.shape[0]} filas, {df_ml.shape[1]} columnas.")

    return df_ml

def main():
    df = cargar_datos(RUTA_CSV)
    if df is None:
        return
    explorar_datos(df)
    df_limpio = limpiar_datos(df)
    visualizar_datos(df_limpio)
    df_ml = preparar_ml(df_limpio)

    ruta_salida = DIR_DATA / "rutas_preparadas_ml.csv"
    df_ml.to_csv(ruta_salida, index=False)
    print(f"\nDataset preparado guardado en '{ruta_salida}'.")
    print("Proceso completado exitosamente.")


if __name__ == "__main__":
    main()