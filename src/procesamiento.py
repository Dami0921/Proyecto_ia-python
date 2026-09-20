"""
procesamiento.py
Funciones propias del proyecto para procesar los registros de rutas de
recoleccion: convierte horas a minutos y calcula indicadores por ruta.

Entrada:  lista de diccionarios (resultado de cargar_datos.leer_datos)
Salida:   lista de diccionarios con columnas nuevas (datos procesados)
"""

MINUTOS_POR_DIA = 24 * 60


def hora_a_minutos(hora):
    """Convierte un texto 'HH:MM' en minutos desde las 00:00. Ej: '06:30' -> 390."""
    horas, minutos = hora.split(":")
    return int(horas) * 60 + int(minutos)


def diferencia_minutos(hora_inicio, hora_fin):
    """
    Minutos transcurridos entre dos horas 'HH:MM'.
    Si la hora final es menor que la inicial se asume que la ruta cruzo la
    medianoche (util para rutas nocturnas en los datos reales).
    """
    inicio = hora_a_minutos(hora_inicio)
    fin = hora_a_minutos(hora_fin)
    if fin < inicio:
        fin = fin + MINUTOS_POR_DIA
    return fin - inicio


def calcular_indicadores(fila):
    """
    Recibe el registro de UNA ruta (diccionario) y devuelve una copia con
    indicadores nuevos. No modifica el diccionario original.

        - tiempo_traslado_min: minutos entre salir de la base y empezar la ruta
        - duracion_ruta_horas: horas entre el inicio y el fin de la ruta
        - toneladas_por_hora:  productividad de la recoleccion
        - km_por_galon:        rendimiento de combustible

    Los valores se guardan sin redondear; el redondeo se aplica solo al mostrarlos.
    Si un indicador no se puede calcular (division por cero), queda en None.
    """
    nueva = dict(fila)

    traslado = diferencia_minutos(fila["hora_salida_base"], fila["hora_inicio_ruta"])
    duracion_horas = diferencia_minutos(fila["hora_inicio_ruta"], fila["hora_fin_ruta"]) / 60

    nueva["tiempo_traslado_min"] = traslado
    nueva["duracion_ruta_horas"] = duracion_horas

    if duracion_horas > 0:
        nueva["toneladas_por_hora"] = fila["toneladas"] / duracion_horas
    else:
        nueva["toneladas_por_hora"] = None

    if fila["combustible_tanqueado"] > 0:
        nueva["km_por_galon"] = fila["km_recorridos"] / fila["combustible_tanqueado"]
    else:
        nueva["km_por_galon"] = None

    return nueva


def procesar_registros(datos):
    """Aplica calcular_indicadores a cada ruta y devuelve la nueva lista de diccionarios."""
    registros = []
    for fila in datos:
        registros.append(calcular_indicadores(fila))
    return registros


if __name__ == "__main__":
    from cargar_datos import leer_datos

    procesados = procesar_registros(leer_datos())
    for ruta in procesados:
        print(
            "Ruta", ruta["ruta_id"],
            "| duracion:", round(ruta["duracion_ruta_horas"], 2), "h",
            "| t/h:", round(ruta["toneladas_por_hora"], 2),
            "| km/gal:", round(ruta["km_por_galon"], 2),
        )
