"""
neuronas_logicas.py
Neuronas artificiales que aprenden las compuertas OR y NOT.
"""
from pathlib import Path

import matplotlib.pyplot as plt

RUTA_GRAFICO = Path(__file__).resolve().parent.parent / "data" / "evolucion_error_logicas.png"


def escalon(z):
    """Función de activación escalón."""
    return 1 if z >= 0 else 0


def neurona(entradas, pesos, b):
    """Suma ponderada de cualquier número de entradas + escalón."""
    z = sum(w * x for w, x in zip(pesos, entradas)) + b
    return escalon(z)


def entrenar(nombre, datos, pesos, b, tasa_aprendizaje=0.1, max_epocas=50):
    """Entrena una neurona y retorna el error total de cada época."""
    print("=" * 60)
    print(f"ENTRENAMIENTO: compuerta {nombre}")
    print("=" * 60)
    print(f"Parámetros iniciales: pesos={pesos}, b={b}\n")

    errores_por_epoca = []
    for epoca in range(max_epocas):
        error_total = 0
        for entradas, y_real in datos:
            y_pred = neurona(entradas, pesos, b)
            error = y_real - y_pred
            error_total += abs(error)
            for i in range(len(pesos)):
                pesos[i] += tasa_aprendizaje * error * entradas[i]
            b += tasa_aprendizaje * error

        errores_por_epoca.append(error_total)
        pesos_txt = ", ".join(f"{w:.3f}" for w in pesos)
        print(f"Época {epoca + 1:2d} | Error total: {error_total} | pesos=[{pesos_txt}] b={b:.3f}")

        if error_total == 0:
            print(f"\nLa neurona aprendió en {epoca + 1} épocas.\n")
            break

    print("PRUEBA FINAL")
    for entradas, y_real in datos:
        y_pred = neurona(entradas, pesos, b)
        estado = "OK" if y_pred == y_real else "X"
        print(f"  {estado} Entrada: {entradas} | Esperado: {y_real} | Predicho: {y_pred}")
    print()

    return errores_por_epoca


# Datos de entrenamiento: (entradas, y_real)
datos_or = [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 1)]
datos_not = [((0,), 1), ((1,), 0)]

errores_or = entrenar("OR", datos_or, pesos=[0.1, 0.1], b=0.0)
errores_not = entrenar("NOT", datos_not, pesos=[0.1], b=0.0)

# Gráfica de la evolución del error de ambas compuertas
plt.figure(figsize=(8, 5))
plt.plot(range(1, len(errores_or) + 1), errores_or, marker="o", color="red", label="OR")
plt.plot(range(1, len(errores_not) + 1), errores_not, marker="s", color="blue", label="NOT")
plt.title("Evolución del Error: compuertas OR y NOT")
plt.xlabel("Época")
plt.ylabel("Error Total")
plt.legend()
plt.grid(True)
plt.savefig(RUTA_GRAFICO, dpi=150)
plt.close()
print(f"Gráfico guardado: {RUTA_GRAFICO}")
