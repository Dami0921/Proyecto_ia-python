"""
modelo_proyecto.py
Compara modelos de scikit-learn para predecir si una ruta de recolección tendrá ALTO TONELAJE.

Etiqueta : alto_tonelaje = 1 si toneladas > mediana de las toneladas del conjunto de ENTRENAMIENTO.
Variables: solo las conocidas ANTES de salir a la ruta (mes, día, ruta, vehículo, turno, tripulantes,
           kg/km/tiempo planeados). Se excluyen km recorridos, tiempo real y combustible porque
           solo se conocen después de la ruta (serían fuga de información).
Entrada  : data/datos_limpios.csv  (salida de preparacion_datos.py; datos SIMULADOS)
Salidas  : src/modelo_final.joblib, graficos/grafico4_matriz_confusion.png,
           graficos/grafico5_curva_aprendizaje.png
"""
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, classification_report,
                             confusion_matrix)
from sklearn.model_selection import (StratifiedKFold, cross_validate,
                                     learning_curve, train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

BASE = Path(__file__).resolve().parent.parent
RUTA_DATOS = BASE / "data" / "datos_limpios.csv"
RUTA_MODELO = BASE / "src" / "modelo_final.joblib"
DIR_GRAFICOS = BASE / "graficos"

SEMILLA = 42
NUMERICAS = ["mes", "dia_semana", "turno_noche", "n_tripulantes",
             "kg_planeados", "km_planeados", "t_ruta_planeado_min"]
CATEGORICAS = ["ruta", "vehiculo"]
COLUMNAS = NUMERICAS + CATEGORICAS


def crear_pipeline(modelo):
    """Preprocesamiento + modelo. Imputación y escalado se ajustan solo con los datos de entrenamiento."""
    pre = ColumnTransformer([
        ("num", Pipeline([("imputar", SimpleImputer(strategy="median")),
                          ("escalar", StandardScaler())]), NUMERICAS),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
    ])
    return Pipeline([("pre", pre), ("modelo", modelo)])


def cargar():
    df = pd.read_csv(RUTA_DATOS, parse_dates=["fecha"])
    df["ruta"] = df["ruta"].astype(str)        # son códigos, no cantidades
    df["vehiculo"] = df["vehiculo"].astype(str)
    return df


def main():
    df = cargar()
    X, y_ton = df[COLUMNAS], df["toneladas"]

    # 1. Separar PRIMERO; el umbral se calcula solo con entrenamiento (evita fuga)
    X_ent, X_pru, t_ent, t_pru = train_test_split(X, y_ton, test_size=0.25, random_state=SEMILLA)
    umbral = t_ent.median()
    y_ent = (t_ent > umbral).astype(int)
    y_pru = (t_pru > umbral).astype(int)
    print(f"Filas: {len(df)} | entrenamiento {len(X_ent)} | prueba {len(X_pru)}")
    print(f"Umbral de alto tonelaje (mediana de entrenamiento): {umbral:.2f} t")
    print(f"Proporción de clase alta: entrenamiento {y_ent.mean():.2f} | prueba {y_pru.mean():.2f}\n")

    # 2. Comparar modelos con validación cruzada estratificada (solo sobre entrenamiento)
    modelos = {
        "Regresión logística": LogisticRegression(max_iter=1000),
        "Árbol de decisión": DecisionTreeClassifier(max_depth=4, random_state=SEMILLA),
        "Random Forest": RandomForestClassifier(n_estimators=200, random_state=SEMILLA),
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)
    metricas = ["accuracy", "recall", "f1", "roc_auc"]
    filas = []
    for nombre, modelo in modelos.items():
        r = cross_validate(crear_pipeline(modelo), X_ent, y_ent, cv=cv, scoring=metricas)
        filas.append({"modelo": nombre, **{m: r[f"test_{m}"].mean() for m in metricas}})
    tabla = pd.DataFrame(filas).set_index("modelo")
    print("=== Validación cruzada (5 pliegues, promedio) ===")
    print(tabla.round(3).to_string())

    # 3. Elegir por F1 (equilibra detectar rutas altas y no dar falsas alarmas)
    mejor = tabla["f1"].idxmax()
    print(f"\nMejor modelo por F1: {mejor}")
    pipeline = crear_pipeline(modelos[mejor]).fit(X_ent, y_ent)

    # 4. Evaluación final, una sola vez, con el conjunto de prueba
    pred = pipeline.predict(X_pru)
    print("\n=== Evaluación en el conjunto de prueba ===")
    print(classification_report(y_pru, pred, target_names=["normal", "alto"], digits=3))
    print("Matriz de confusión [[VN, FP], [FN, VP]]:")
    print(confusion_matrix(y_pru, pred))

    # 5. Gráficos de evaluación
    DIR_GRAFICOS.mkdir(exist_ok=True)
    ConfusionMatrixDisplay.from_predictions(y_pru, pred, display_labels=["normal", "alto"], cmap="Greens")
    plt.title(f"Matriz de confusión - {mejor} (prueba)")
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico4_matriz_confusion.png", dpi=150)
    plt.close()

    tamanos, ent, val = learning_curve(
        crear_pipeline(modelos[mejor]), X_ent, y_ent, cv=cv, scoring="f1",
        train_sizes=np.linspace(0.2, 1.0, 6), random_state=SEMILLA)
    plt.figure(figsize=(7, 4.5))
    plt.plot(tamanos, ent.mean(axis=1), "o-", label="Entrenamiento")
    plt.plot(tamanos, val.mean(axis=1), "o-", label="Validación cruzada")
    plt.title(f"Curva de aprendizaje - {mejor}")
    plt.xlabel("Filas de entrenamiento")
    plt.ylabel("F1")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(DIR_GRAFICOS / "grafico5_curva_aprendizaje.png", dpi=150)
    plt.close()

    # 6. Guardar el pipeline completo junto con el umbral y las columnas esperadas
    joblib.dump({"pipeline": pipeline, "umbral_toneladas": float(umbral),
                 "columnas": COLUMNAS, "modelo": mejor}, RUTA_MODELO)
    print(f"\nModelo guardado en {RUTA_MODELO}")


if __name__ == "__main__":
    main()