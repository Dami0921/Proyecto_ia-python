"""
perceptron_proyecto.py
Perceptrón con sigmoide, pérdida logarítmica y descenso del gradiente,
implementado solo con NumPy (sin Scikit-Learn).

Problema: clasificar si una ruta de recolección es de ALTO TONELAJE (1) o no (0).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DIR_DATA = Path(__file__).resolve().parent.parent / "data"
RUTA_CSV = DIR_DATA / "proyecto_limpio.csv"

COL_OBJETIVO = "toneladas"          # solo sirve para construir la etiqueta 0/1
COL_ENTRADAS = ["km_recorridos", "duracion_ruta_min"]
TASA_APRENDIZAJE = 0.1
EPOCAS = 1000


def sigmoide(z):
    """Función de activación sigmoide: convierte z en una probabilidad (0 a 1)."""
    return 1 / (1 + np.exp(-z))


def perdida_logaritmica(y, y_hat):
    """Entropía cruzada binaria promedio. El recorte evita log(0)."""
    y_hat = np.clip(y_hat, 1e-12, 1 - 1e-12)
    return -np.mean(y * np.log(y_hat) + (1 - y) * np.log(1 - y_hat))


def estandarizar(X):
    """Estandarización: (x - media) / desviación. Retorna X escalada, media y std."""
    media = X.mean(axis=0)
    desviacion = X.std(axis=0)
    return (X - media) / desviacion, media, desviacion


def entrenar(X, y, tasa=TASA_APRENDIZAJE, epocas=EPOCAS):
    """Descenso del gradiente. Retorna pesos, bias e historial de pérdida."""
    n = X.shape[0]
    w = np.zeros(X.shape[1])
    b = 0.0
    historial = []

    for _ in range(epocas):
        y_hat = sigmoide(X @ w + b)                       # 1. predicción
        historial.append(perdida_logaritmica(y, y_hat))   # 2. pérdida
        error = y_hat - y                                 # 3. gradiente de la pérdida
        w -= tasa * (X.T @ error) / n                     # 4. actualizar pesos
        b -= tasa * error.mean()                          #    y bias
    return w, b, historial


def exactitud(X, y, w, b):
    """Porcentaje de aciertos con umbral 0.5."""
    predicciones = (sigmoide(X @ w + b) >= 0.5).astype(int)
    return (predicciones == y).mean()


def graficar_perdida(historial):
    plt.figure(figsize=(8, 5))
    plt.plot(historial, color="tab:red")
    plt.title("Curva de aprendizaje del perceptrón")
    plt.xlabel("Época")
    plt.ylabel("Pérdida logarítmica")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(DIR_DATA / "curva_aprendizaje_perceptron.png", dpi=150)
    plt.close()


def graficar_frontera(X, y, w, b):
    plt.figure(figsize=(8, 6))
    plt.scatter(X[y == 0, 0], X[y == 0, 1], c="tab:blue", s=90, label="Normal (0)")
    plt.scatter(X[y == 1, 0], X[y == 1, 1], c="tab:orange", s=90, label="Alto tonelaje (1)")
    # La frontera es donde z = 0  ->  x2 = -(w1*x1 + b) / w2
    x1 = np.linspace(X[:, 0].min() - 0.5, X[:, 0].max() + 0.5, 100)
    x2 = -(w[0] * x1 + b) / w[1]
    plt.plot(x1, x2, "k--", label="Frontera de decisión")
    plt.ylim(X[:, 1].min() - 0.5, X[:, 1].max() + 0.5)
    plt.title("Frontera de decisión (variables estandarizadas)")
    plt.xlabel("Km recorridos (estandarizado)")
    plt.ylabel("Duración de ruta (estandarizada)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(DIR_DATA / "frontera_decision_perceptron.png", dpi=150)
    plt.close()


def main():
    df = pd.read_csv(RUTA_CSV)

    # Variable objetivo 0/1: ruta de alto tonelaje si supera la mediana
    umbral = df[COL_OBJETIVO].median()
    y = (df[COL_OBJETIVO] > umbral).astype(int).to_numpy()
    print(f"Umbral (mediana de toneladas): {umbral} t")
    print(f"Rutas: {len(y)} | alto tonelaje (1): {y.sum()} | normal (0): {(y == 0).sum()}")

    X, media, desviacion = estandarizar(df[COL_ENTRADAS].to_numpy(dtype=float))

    w, b, historial = entrenar(X, y)

    print("\nRESULTADOS")
    print(f"  w1 (km_recorridos):     {w[0]:.3f}")
    print(f"  w2 (duracion_ruta_min): {w[1]:.3f}")
    print(f"  b:                      {b:.3f}")
    print(f"  Pérdida inicial: {historial[0]:.3f}")
    print(f"  Pérdida final:   {historial[-1]:.3f}")
    print(f"  Exactitud:       {exactitud(X, y, w, b):.1%}")

    graficar_perdida(historial)
    graficar_frontera(X, y, w, b)
    print("\nGráficos guardados en data/.")


if __name__ == "__main__":
    main()