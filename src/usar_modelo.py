"""
usar_modelo.py
Carga el modelo entrenado (src/modelo_final.joblib) y predice si una ruta tendrá ALTO TONELAJE.

Uso:
    python src/usar_modelo.py                # demo con 3 casos nuevos
    python src/usar_modelo.py --interactivo  # el supervisor digita ruta, mes, día, turno...

Los kg, km y tiempo planeados se toman de la mediana histórica de la ruta elegida
(data/datos_limpios.csv), porque son parámetros del plan de esa ruta.
"""
import argparse
from pathlib import Path

import joblib
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
RUTA_MODELO = BASE / "src" / "modelo_final.joblib"
RUTA_DATOS = BASE / "data" / "datos_limpios.csv"
NOMBRES_DIA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def cargar_modelo():
    if not RUTA_MODELO.exists():
        raise SystemExit("No existe src/modelo_final.joblib. Ejecuta primero: python src/modelo_proyecto.py")
    return joblib.load(RUTA_MODELO)


def plan_por_ruta():
    """Mediana histórica de lo planeado por ruta (kg, km, tiempo)."""
    df = pd.read_csv(RUTA_DATOS, dtype={"ruta": str, "vehiculo": str})
    cols = ["kg_planeados", "km_planeados", "t_ruta_planeado_min"]
    return df.groupby("ruta")[cols].median(), sorted(df["vehiculo"].unique())


def predecir(modelo, casos):
    """Recibe un DataFrame con las columnas del modelo y devuelve la predicción y su probabilidad."""
    X = casos[modelo["columnas"]]
    pipeline = modelo["pipeline"]
    resultado = casos.copy()
    resultado["prob_alto"] = pipeline.predict_proba(X)[:, 1]
    resultado["prediccion"] = ["ALTO" if p == 1 else "normal" for p in pipeline.predict(X)]
    return resultado


def caso(plan, ruta, mes, dia_semana, turno_noche, n_tripulantes, vehiculo):
    p = plan.loc[ruta]
    return {"mes": mes, "dia_semana": dia_semana, "turno_noche": turno_noche,
            "n_tripulantes": n_tripulantes, "kg_planeados": p["kg_planeados"],
            "km_planeados": p["km_planeados"], "t_ruta_planeado_min": p["t_ruta_planeado_min"],
            "ruta": ruta, "vehiculo": vehiculo}


def mostrar(modelo, resultado):
    print(f"\nModelo: {modelo['modelo']} | alto tonelaje = más de {modelo['umbral_toneladas']:.2f} t")
    for _, f in resultado.iterrows():
        print(f"  Ruta {f['ruta']} | mes {int(f['mes']):>2} | {NOMBRES_DIA[int(f['dia_semana'])]:<9} "
              f"| turno {'noche' if f['turno_noche'] else 'día  '} -> {f['prediccion']:<6} "
              f"(probabilidad de alto: {f['prob_alto']:.0%})")


def demo(modelo, plan, vehiculos):
    v = vehiculos[0]
    casos = pd.DataFrame([
        caso(plan, plan.index[0], 12, 0, 0, 3, v),   # diciembre, lunes
        caso(plan, plan.index[0], 5, 5, 0, 3, v),    # mayo, sábado
        caso(plan, plan.index[-1], 1, 0, 0, 3, v),   # enero, lunes
    ])
    mostrar(modelo, predecir(modelo, casos))


def interactivo(modelo, plan, vehiculos):
    print(f"Rutas disponibles: {', '.join(plan.index)} | Vehículos: {', '.join(vehiculos)}")
    while True:
        ruta = input("\nRuta (Enter para salir): ").strip()
        if not ruta:
            break
        if ruta not in plan.index:
            print("  Esa ruta no está en el histórico.")
            continue
        try:
            mes = int(input("Mes (1-12): "))
            dia = int(input("Día de la semana (0=lunes ... 6=domingo): "))
            turno = int(input("Turno noche (0=no, 1=sí): "))
            trip = int(input("Número de tripulantes: "))
        except ValueError:
            print("  Debes digitar números enteros.")
            continue
        veh = input(f"Vehículo [{vehiculos[0]}]: ").strip() or vehiculos[0]
        mostrar(modelo, predecir(modelo, pd.DataFrame([caso(plan, ruta, mes, dia, turno, trip, veh)])))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Predice alto tonelaje en rutas de recolección.")
    ap.add_argument("--interactivo", action="store_true")
    args = ap.parse_args()
    modelo = cargar_modelo()
    plan, vehiculos = plan_por_ruta()
    (interactivo if args.interactivo else demo)(modelo, plan, vehiculos)