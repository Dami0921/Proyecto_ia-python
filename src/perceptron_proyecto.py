"""
perceptron_proyecto.py
Perceptrón con sigmoide, pérdida logarítmica y descenso del gradiente, solo con NumPy.

Problema: clasificar si una ruta será de ALTO TONELAJE (1) o normal (0) usando datos
conocidos ANTES de la ruta.

Cambios respecto al Avance 2 (versión descriptiva):
  1. Datos nuevos: data/datos_limpios.csv (salida de preparacion_datos.py).
  2. División entrenamiento/prueba (75/25): antes se evaluaba con los mismos datos del entrenamiento.
  3. Umbral de alto tonelaje = mediana del ENTRENAMIENTO (antes, de todos los datos: fuga).
  4. Estandarización con media y desviación del ENTRENAMIENTO, aplicada igual a la prueba.
  5. Pesos iniciales pequeños y aleatorios (antes: ceros), con semilla fija.
  6. Entradas conocidas antes de la ruta (antes: km recorridos y duración, que se conocen después).
  7. Métricas en prueba (exactitud, recall, matriz de confusión) y curva de pérdida de entrenamiento y prueba.

Entradas: kg_planeados (tamaño del plan de la ruta) y temporada_alta (1 = dic, ene, jun, jul).
Salidas : graficos/grafico6_perceptron_perdida.png, graficos/grafico7_perceptron_frontera.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RUTA_CSV = BASE / "data" / "datos_limpios.csv"
DIR_GRAFICOS = BASE / "graficos"

SEMILLA = 42
TASA_APRENDIZAJE = 0.1
EPOCAS = 1000
MESES_PICO = [12, 1, 6, 7]       # meses de mayor generación observados en el histórico


def sigmoide(z):
    """Convierte z en una probabilidad entre 0 y 1."""
    return 1 / (1 + np.exp(-z))


def perdida_logaritmica(y, y_hat):
    """Entropía cruzada binaria promedio. El recorte evita log(0)."""
    y_hat = np.clip(y_hat, 1e-12, 1 - 1e-12)
    return -np.mean(y * np.log(y_hat) + (1 - y) * np.log(1 - y_hat))


def dividir(n, proporcion_prueba=0.25, semilla=SEMILLA):
    """Índices aleatorios de entrenamiento y prueba."""
    indices = np.random.default_rng(semilla).permutation(n)
    corte = int(n * (1 - proporcion_prueba))
    return indices[:corte], indices[corte:]


def entrenar(X, y, X_pru, y_pru, tasa=TASA_APRENDIZAJE, epocas=EPOCAS):
    """Descenso del gradiente. Guarda la pérdida de entrenamiento y de prueba en cada época."""
    n = X.shape[0]
    rng = np.random.default_rng(SEMILLA)
    w = rng.normal(0, 0.1, X.shape[1])      # pesos iniciales pequeños y aleatorios
    b = 0.0
    perdida_ent, perdida_pru = [], []
    for _ in range(epocas):
        y_hat = sigmoide(X @ w + b)                              # 1. predicción
        perdida_ent.append(perdida_logaritmica(y, y_hat))        # 2. pérdida (entrenamiento)
        perdida_pru.append(perdida_logaritmica(y_pru, sigmoide(X_pru @ w + b)))  # solo se mide
        error = y_hat - y                                        # 3. gradiente
        w -= tasa * (X.T @ error) / n                            # 4. actualizar pesos (solo con entrenamiento)
        b -= tasa * error.mean()
    return w, b, perdida_ent, perdida_pru


def predecir(X, w, b):
    return (sigmoide(X @ w + b) >= 0.5).astype(int)


def graficar_perdida(perdida_ent, perdida_pru):
    DIR_GRAFICOS.mkdir(exist_ok=True)
    plt.figure(figsize=(8, 4.5))
    plt.plot(perdida_ent, label="Entrenamiento", color="tab:red")
    plt.plot(perdida_pru, label="Prueba", color="tab:blue")
    plt.title("Curva de aprendizaje del perceptrón")
    plt.xlabel("Época")
    plt.ylabel("Pérdida logarítmica")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico6_perceptron_perdida.png", dpi=150)
    plt.close()


def graficar_frontera(X, y, w, b):
    """Frontera de decisión sobre los datos de prueba (variables estandarizadas)."""
    plt.figure(figsize=(8, 5))
    plt.scatter(X[y == 0, 0], X[y == 0, 1], c="tab:blue", s=70, label="Normal (0)")
    plt.scatter(X[y == 1, 0], X[y == 1, 1], c="tab:orange", s=70, label="Alto tonelaje (1)")
    x1 = np.linspace(X[:, 0].min() - 0.5, X[:, 0].max() + 0.5, 100)
    plt.plot(x1, -(w[0] * x1 + b) / w[1], "k--", label="Frontera (z = 0)")
    plt.ylim(X[:, 1].min() - 0.5, X[:, 1].max() + 0.5)
    plt.title("Frontera de decisión en prueba (variables estandarizadas)")
    plt.xlabel("kg planeados (estandarizado)")
    plt.ylabel("Temporada alta (estandarizada)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico7_perceptron_frontera.png", dpi=150)
    plt.close()


def main():
    df = pd.read_csv(RUTA_CSV)
    df["temporada_alta"] = df["mes"].isin(MESES_PICO).astype(int)
    entradas = df[["kg_planeados", "temporada_alta"]].to_numpy(dtype=float)
    toneladas = df["toneladas"].to_numpy()

    # 1. Dividir primero
    i_ent, i_pru = dividir(len(df))
    X_ent, X_pru = entradas[i_ent], entradas[i_pru]

    # 2. Umbral y estandarización con datos de ENTRENAMIENTO únicamente
    umbral = np.median(toneladas[i_ent])
    y_ent = (toneladas[i_ent] > umbral).astype(int)
    y_pru = (toneladas[i_pru] > umbral).astype(int)
    media, desviacion = X_ent.mean(axis=0), X_ent.std(axis=0)
    X_ent = (X_ent - media) / desviacion
    X_pru = (X_pru - media) / desviacion
    print(f"Entrenamiento: {len(y_ent)} filas | prueba: {len(y_pru)} filas")
    print(f"Umbral (mediana de entrenamiento): {umbral:.2f} t")

    # 3. Entrenar
    w, b, perdida_ent, perdida_pru = entrenar(X_ent, y_ent, X_pru, y_pru)

    # 4. Evaluar en prueba
    pred = predecir(X_pru, w, b)
    vp = int(((pred == 1) & (y_pru == 1)).sum())
    vn = int(((pred == 0) & (y_pru == 0)).sum())
    fp = int(((pred == 1) & (y_pru == 0)).sum())
    fn = int(((pred == 0) & (y_pru == 1)).sum())
    print("\nRESULTADOS")
    print(f"  w1 (kg_planeados):    {w[0]:.3f}")
    print(f"  w2 (temporada_alta):  {w[1]:.3f}")
    print(f"  b:                    {b:.3f}")
    print(f"  Pérdida entrenamiento: {perdida_ent[0]:.3f} -> {perdida_ent[-1]:.3f}")
    print(f"  Pérdida prueba:        {perdida_pru[0]:.3f} -> {perdida_pru[-1]:.3f}")
    print(f"  Exactitud entrenamiento: {(predecir(X_ent, w, b) == y_ent).mean():.1%}")
    print(f"  Exactitud prueba:        {(pred == y_pru).mean():.1%}")
    print(f"  Recall prueba (alto):    {vp / (vp + fn):.1%}")
    print(f"  Matriz de confusión prueba [[VN, FP], [FN, VP]]: [[{vn}, {fp}], [{fn}, {vp}]]")

    graficar_perdida(perdida_ent, perdida_pru)
    graficar_frontera(X_pru, y_pru, w, b)
    print("\nGráficos guardados en graficos/.")


if __name__ == "__main__":
    main()