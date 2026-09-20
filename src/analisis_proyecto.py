"""
analisis_proyecto.py
Actividad independiente: manejo de archivos y generacion de un informe en
Markdown con estadisticas del proyecto de optimizacion de rutas de residuos.
"""

from cargar_datos import leer_datos
from config import RUTA_CSV, RUTA_INFORME


def calcular_estadisticas(datos):
    """
    Calcula 5 estadisticas basicas a partir de los datos de rutas:
        1. Promedio de toneladas recolectadas
        2. Maximo de toneladas recolectadas
        3. Minimo de toneladas recolectadas
        4. Promedio de kilometros recorridos
        5. Total de combustible tanqueado
    """
    toneladas = []
    for fila in datos:
        toneladas.append(fila["toneladas"])

    kilometros = []
    for fila in datos:
        kilometros.append(fila["km_recorridos"])

    combustible = []
    for fila in datos:
        combustible.append(fila["combustible_tanqueado"])

    # 1. Promedio de toneladas
    suma_toneladas = 0
    for valor in toneladas:
        suma_toneladas = suma_toneladas + valor
    promedio_toneladas = suma_toneladas / len(toneladas)

    # 2 y 3. Maximo y minimo de toneladas
    maximo_toneladas = toneladas[0]
    minimo_toneladas = toneladas[0]
    for valor in toneladas:
        if valor > maximo_toneladas:
            maximo_toneladas = valor
        if valor < minimo_toneladas:
            minimo_toneladas = valor

    # 4. Promedio de kilometros recorridos
    suma_km = 0
    for valor in kilometros:
        suma_km = suma_km + valor
    promedio_km = suma_km / len(kilometros)

    # 5. Total de combustible tanqueado
    total_combustible = 0
    for valor in combustible:
        total_combustible = total_combustible + valor

    estadisticas = {
        "total_registros": len(datos),
        "promedio_toneladas": promedio_toneladas,
        "maximo_toneladas": maximo_toneladas,
        "minimo_toneladas": minimo_toneladas,
        "promedio_km": promedio_km,
        "total_combustible": total_combustible,
    }

    return estadisticas


def generar_informe(estadisticas, archivo_salida):
    """Genera un informe en Markdown con las estadisticas calculadas."""
    archivo = open(archivo_salida, "w", encoding="utf-8")

    archivo.write("# Informe del Proyecto: Optimizacion de Rutas de Recoleccion de Residuos\n\n")

    archivo.write("## Descripcion de los datos\n")
    archivo.write(
        "Datos de rutas de recoleccion de residuos, con informacion de toneladas "
        "recolectadas, kilometros recorridos y combustible tanqueado por ruta "
        "(actualmente datos ficticios de prueba).\n\n"
    )

    archivo.write("## Estadisticas\n")
    archivo.write("- Total de registros: " + str(estadisticas["total_registros"]) + "\n")
    archivo.write("- Promedio de toneladas recolectadas: " + str(round(estadisticas["promedio_toneladas"], 2)) + "\n")
    archivo.write("- Maximo de toneladas recolectadas: " + str(estadisticas["maximo_toneladas"]) + "\n")
    archivo.write("- Minimo de toneladas recolectadas: " + str(estadisticas["minimo_toneladas"]) + "\n")
    archivo.write("- Promedio de kilometros recorridos: " + str(round(estadisticas["promedio_km"], 2)) + "\n")
    archivo.write("- Total de combustible tanqueado (galones): " + str(estadisticas["total_combustible"]) + "\n\n")

    archivo.write("## Interpretacion\n")
    archivo.write(
        "El promedio de toneladas por ruta indica la carga tipica que maneja cada "
        "vehiculo, dato clave para dimensionar la capacidad necesaria. La diferencia "
        "entre el maximo y el minimo de toneladas muestra que tan variable es la "
        "demanda entre rutas, lo que sustenta la necesidad de un modulo de prediccion "
        "de generacion de residuos. El promedio de kilometros y el total de combustible "
        "ayudan a estimar costos operativos, informacion que alimentara el modulo de "
        "optimizacion de rutas (VRP).\n"
    )

    archivo.close()


if __name__ == "__main__":
    datos = leer_datos(RUTA_CSV)
    estadisticas = calcular_estadisticas(datos)
    generar_informe(estadisticas, RUTA_INFORME)
    print("Informe generado correctamente: informe_proyecto.md")