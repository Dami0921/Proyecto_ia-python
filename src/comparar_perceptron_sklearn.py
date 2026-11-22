"""
comparar_perceptron_sklearn.py
Compara el perceptrón hecho a mano (NumPy) con LogisticRegression de Scikit-Learn,
usando exactamente la misma división, el mismo umbral y las mismas entradas.

Idea de la Clase 12: LogisticRegression es "el perceptrón de la clase anterior, hecho por la librería".
Se espera que los pesos tengan los mismos signos y tamaños parecidos. No son idénticos porque
Scikit-Learn aplica por defecto una regularización L2 (C = 1.0) y el perceptrón a mano no.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import perceptron_proyecto as pp


def main():
    df = pd.read_csv(pp.RUTA_CSV)
    df["temporada_alta"] = df["mes"].isin(pp.MESES_PICO).astype(int)
    entradas = df[["kg_planeados", "temporada_alta"]].to_numpy(dtype=float)
    toneladas = df["toneladas"].to_numpy()

    i_ent, i_pru = pp.dividir(len(df))
    umbral = np.median(toneladas[i_ent])
    y_ent = (toneladas[i_ent] > umbral).astype(int)
    y_pru = (toneladas[i_pru] > umbral).astype(int)

    # Perceptrón a mano
    media, desv = entradas[i_ent].mean(axis=0), entradas[i_ent].std(axis=0)
    X_ent = (entradas[i_ent] - media) / desv
    X_pru = (entradas[i_pru] - media) / desv
    w, b, _, _ = pp.entrenar(X_ent, y_ent, X_pru, y_pru)
    pred_mano = pp.predecir(X_pru, w, b)

    # LogisticRegression dentro de un Pipeline (escala solo con entrenamiento)
    modelo = Pipeline([("escalado", StandardScaler()), ("modelo", LogisticRegression())])
    modelo.fit(entradas[i_ent], y_ent)
    pred_sk = modelo.predict(entradas[i_pru])
    reg = modelo.named_steps["modelo"]

    tabla = pd.DataFrame({
        "": ["w1 (kg_planeados)", "w2 (temporada_alta)", "b", "Exactitud prueba", "Recall prueba"],
        "Perceptrón (NumPy)": [f"{w[0]:.3f}", f"{w[1]:.3f}", f"{b:.3f}",
                               f"{accuracy_score(y_pru, pred_mano):.3f}", f"{recall_score(y_pru, pred_mano):.3f}"],
        "LogisticRegression": [f"{reg.coef_[0][0]:.3f}", f"{reg.coef_[0][1]:.3f}", f"{reg.intercept_[0]:.3f}",
                               f"{accuracy_score(y_pru, pred_sk):.3f}", f"{recall_score(y_pru, pred_sk):.3f}"],
    })
    print("Comparación con la misma división y las mismas entradas:\n")
    print(tabla.to_string(index=False))
    print(f"\nPredicciones distintas entre ambos: {(pred_mano != pred_sk).sum()} de {len(y_pru)}")


if __name__ == "__main__":
    main()
