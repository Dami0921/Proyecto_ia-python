
"""
cargar_datos.py
Actividad complementaria: procesamiento de un archivo CSV usando
listas, diccionarios y funciones.

Proyecto: Sistema inteligente para la planificación y optimización de rutas
de recolección y transporte de residuos.
"""

import csv

from config import RUTA_CSV


def convertir_numero(valor):
    """
    Recibe un texto y trata de convertirlo en número.
    Si el texto tiene un punto, se intenta convertir a float (decimal).
    Si no tiene punto, se intenta convertir a int (entero).
    Si no se puede convertir (por ejemplo, es un nombre), se deja como texto.
    """
    if valor == "":
        return valor

    if "." in valor:
        try:
            return float(valor)
        except ValueError:
            return valor
    else:
        try:
            return int(valor)
        except ValueError:
            return valor


def leer_datos(ruta_archivo=RUTA_CSV):
    """
    Lee un archivo CSV y lo convierte en una lista de diccionarios.

    Cada fila del CSV se convierte en un diccionario, y todas esas
    filas se guardan en una lista. Ejemplo del resultado:

    [
        {"ruta_id": 1, "conductor": "Juan Perez", "toneladas": 8.5},
        {"ruta_id": 2, "conductor": "Carlos Ruiz", "toneladas": 9.2},
    ]

    Si el archivo no existe se lanza FileNotFoundError (quien llama decide
    como manejarlo). Se usa utf-8-sig para que tambien funcione con CSV
    exportados desde Excel, que suelen traer una marca BOM al inicio.
    """
    lista_datos = []

    with open(ruta_archivo, mode="r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            diccionario = {}
            for clave in fila:
                valor_texto = fila[clave]
                diccionario[clave] = convertir_numero(valor_texto)
            lista_datos.append(diccionario)

    return lista_datos


def mostrar_resumen(datos, columna):
    """
    Muestra un resumen del conjunto de datos:
        - Cantidad total de registros
        - Promedio de la columna indicada
        - Valor máximo de la columna indicada
        - Valor mínimo de la columna indicada
    """
    total = len(datos)
    print("Total de registros:", total)

    # Sacamos solo los valores de la columna que nos interesa
    valores = []
    for fila in datos:
        valores.append(fila[columna])

    # Calculamos el promedio sumando todo y dividiendo por la cantidad
    suma = 0
    for valor in valores:
        suma = suma + valor
    promedio = suma / len(valores)

    # Buscamos el máximo y el mínimo comparando uno por uno
    maximo = valores[0]
    minimo = valores[0]
    for valor in valores:
        if valor > maximo:
            maximo = valor
        if valor < minimo:
            minimo = valor

    print("Columna analizada:", columna)
    print("Promedio:", round(promedio, 2))
    print("Máximo:", maximo)
    print("Mínimo:", minimo)


if __name__ == "__main__":
    datos = leer_datos(RUTA_CSV)
    mostrar_resumen(datos, "toneladas")
