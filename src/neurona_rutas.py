"""
neurona_rutas.py
La neurona de la clase 8 aplicada a datos reales del proyecto de rutas.
Decide si una ruta es de 'alto desempeño' (1) o no (0).
"""
from pathlib import Path

import pandas as pd

RUTA_CSV = Path(__file__).resolve().parent.parent / "data" / "rutas_preparadas_ml.csv"


def escalon(z):
    """Función de activación escalón."""
    return 1 if z >= 0 else 0


def neurona(x1, x2, w1, w2, b):
    """Suma ponderada + escalón."""
    return escalon(w1 * x1 + w2 * x2 + b)


# 1. Entradas binarias derivadas de columnas reales de las rutas
df = pd.read_csv(RUTA_CSV)
df["carga_alta"] = (df["toneladas"] >= df["toneladas"].median()).astype(int)
df["ruta_rapida"] = (df["duracion_ruta_min"] <= df["duracion_ruta_min"].median()).astype(int)
df["alto_desempeno"] = ((df["carga_alta"] == 1) & (df["ruta_rapida"] == 1)).astype(int)

datos = list(zip(df["carga_alta"], df["ruta_rapida"], df["alto_desempeno"]))
print(f"Rutas: {len(datos)} | de alto desempeño: {df['alto_desempeno'].sum()}\n")

# 2. Parámetros iniciales
w1, w2, b = 0.1, 0.1, 0.0
tasa_aprendizaje = 0.1

# 3. Entrenamiento
for epoca in range(50):
    error_total = 0
    for x1, x2, y_real in datos:
        y_pred = neurona(x1, x2, w1, w2, b)
        error = y_real - y_pred
        error_total += abs(error)
        w1 += tasa_aprendizaje * error * x1
        w2 += tasa_aprendizaje * error * x2
        b += tasa_aprendizaje * error
    print(f"Época {epoca + 1:2d} | Error total: {error_total} | "
          f"w1={w1:.2f} w2={w2:.2f} b={b:.2f}")
    if error_total == 0:
        print(f"\nLa neurona aprendió en {epoca + 1} épocas.")
        break

# 4. Prueba final sobre las rutas reales
print("\nPRUEBA FINAL")
for numero, (x1, x2, y_real) in enumerate(datos, start=1):
    y_pred = neurona(x1, x2, w1, w2, b)
    estado = "OK" if y_pred == y_real else "X"
    print(f"  {estado} Ruta {numero:2d} | carga_alta={x1} ruta_rapida={x2} | "
          f"Esperado: {y_real} | Predicho: {y_pred}")