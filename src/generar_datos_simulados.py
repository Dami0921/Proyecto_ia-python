"""
generar_datos_simulados.py
Genera un histórico SIMULADO de rutas de recolección con la misma estructura
de columnas del Excel real de la empresa (Cartago, Valle del Cauca).

IMPORTANTE: los datos son simulados (semilla fija, reproducibles). Ningún nombre,
placa ni observación proviene de la empresa. Sirven para desarrollar y probar el
pipeline; los resultados NO deben generalizarse a la operación real.

Salidas (en la carpeta indicada, por defecto ../data):
  - rutas_simuladas.xlsx : hoja "Rutas" (con fórmulas en las columnas calculadas),
                           "Diccionario" y "Notas".
  - datos_originales.csv : los mismos datos en texto (fechas dd/mm/aaaa, horas H:MM).

Uso:
  python src/generar_datos_simulados.py            # 120 filas, semilla 2026
  python src/generar_datos_simulados.py --filas 150 --semilla 7
"""
import argparse
import csv
import datetime as dt
from pathlib import Path

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# --------------------------------------------------------------------------
# 1. Estructura de columnas: (clave, encabezado, tipo)
#    tipo: 'dato' = valor digitado, 'calc' = fórmula, 'plan' = valor planeado
# --------------------------------------------------------------------------
COLUMNAS = [
    ("fecha", "FECHA", "dato"), ("dia", "DIA", "dato"),
    ("vehiculo", "VEHICULO", "dato"), ("placa", "PLACA", "dato"),
    ("ruta", "RUTA", "dato"), ("apoyo", "APOYO", "dato"),
    ("compactado", "COMPACTADO", "dato"),
    ("kg", "KILOGRAMOS RECOLECTADOS", "dato"), ("kg_plan", "KG PLANEADOS", "plan"),
    ("f_ini", "FECHA DE INICIO DE RUTA", "dato"), ("h_ini", "HORA DE INICIO DE RUTA", "dato"),
    ("f_fin", "FECHA TERMINA RUTA", "dato"), ("h_fin", "HORA TERMINA RUTA", "dato"),
    ("t_ruta", "TIEMPOS DE RUTA", "calc"), ("t_ruta_plan", "T. RUTA PLANEADO", "plan"),
    ("f_sal_rell", "FECHA SALIDA AL RELLENO", "dato"), ("h_sal_rell", "HORA SALIDA AL RELLENO", "dato"),
    ("f_ing_rell", "FECHA DEL INGRESO AL RELLENO", "dato"), ("h_ing_rell", "HORA DEL INGRESO AL RELLENO", "dato"),
    ("f_sal_de_rell", "FECHA DE SALIDA AL RELLENO", "dato"), ("h_sal_de_rell", "HORA DE SALIDA AL RELLENO", "dato"),
    ("t_en_rell", "TIEMPOS EN RELLENO", "calc"),
    ("f_lleg", "FECHA LLEGADA BASE", "dato"), ("h_lleg", "HORA DE LLEGADA A BASE", "dato"),
    ("t_rell", "TIEMPOS RELLENO", "calc"), ("t_transp_plan", "T. TRANSPORTE PLANEADO", "plan"),
    ("ticket", "TICKET DE BASCULA", "dato"), ("conductor", "CONDUCTOR", "dato"),
    ("tripulantes", "TRIPULANTES", "dato"), ("supervisor", "SUPERVISOR", "dato"),
    ("comb", "COMBUSTIBLE", "dato"), ("comb_plan", "COMBUSTIBLE PLANEADO", "plan"),
    ("odo_ini", "ODOMETRO INICIO", "dato"), ("odo_fin", "ODOMETRO FIN", "dato"),
    ("km", "KM RECORRIDOS", "calc"), ("km_plan", "KM PLANEADOS", "plan"),
    ("t_total", "TIEMPO TOTAL", "calc"), ("t_total_plan", "TIEMPO TOTAL PLANEADO", "plan"),
    ("t_extra", "TIEMPOS DEMAS DE LO PLANEADO", "calc"), ("t_improd", "TIEMPO IMPRODUCTIVO", "calc"),
    ("gal_km", "GALON POR KILOMETRO", "calc"), ("km_gal", "KILOMETRO POR GALON", "calc"),
    ("kg_gal", "RENDIMIENTO DE KG/GAL", "calc"), ("ef_carga", "EFICIENCIA EN CARGA", "calc"),
    ("ef_comb", "EFICIENCIA EN COMBUSTIBLE", "calc"), ("ef_tiempo", "EFICIENCIA EN TIEMPO", "calc"),
    ("rend_global", "RENDIMIENTO GLOBAL", "calc"), ("obs", "OBSERVACIONES", "dato"),
]
CLAVES = [c[0] for c in COLUMNAS]
LETRA = {clave: get_column_letter(i + 1) for i, clave in enumerate(CLAVES)}
COLS_FECHA = {"fecha", "f_ini", "f_fin", "f_sal_rell", "f_ing_rell", "f_sal_de_rell", "f_lleg"}
COLS_HORA = {"h_ini", "h_fin", "h_sal_rell", "h_ing_rell", "h_sal_de_rell", "h_lleg"}
COLS_DURACION = {"t_ruta", "t_ruta_plan", "t_en_rell", "t_rell", "t_transp_plan",
                 "t_total", "t_total_plan", "t_extra", "t_improd"}

# --------------------------------------------------------------------------
# 2. Parámetros de la simulación (todos inventados)
# --------------------------------------------------------------------------
RUTAS = [  # (código, kg base, km base, minutos de transporte planeados)
    (8001, 8200, 52, 135), (8002, 9100, 58, 140), (8003, 9800, 61, 145), (8004, 10400, 66, 150),
    (8005, 10900, 70, 150), (8006, 11500, 75, 155), (8007, 12200, 82, 160), (8008, 12900, 90, 165),
]
VEHICULOS = [  # (código, placa, odómetro inicial en km)
    (5050, "TXK121", 61200), (5058, "TXK144", 84300), (5062, "TXK208", 12400),
    (5071, "TXL015", 47900), (5115, "TXL077", 9100), (5130, "TXL310", 73500),
]
FACTOR_MES = {1: 1.10, 2: 0.95, 3: 0.97, 4: 1.00, 5: 0.98, 6: 1.06,
              7: 1.10, 8: 1.00, 9: 0.96, 10: 1.02, 11: 1.04, 12: 1.20}  # época del año
FACTOR_DIA = {0: 1.08, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.02, 5: 0.90}      # lunes=0 ... sábado=5
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
CONDUCTORES = ["PEDRO MONTOYA", "WILSON TORO", "EDGAR RAMIREZ", "FABIAN OSPINA", "JHON ARIAS", "MARIO LOZANO"]
AYUDANTES = ["ANDRES", "LUIS", "DIEGO", "KEVIN", "ALEX", "BRAYAN", "OSCAR", "SAMUEL", "DAVID", "CAMILO"]
SUPERVISORES = ["ALEJANDRO", "VIVIANA", "SEBASTIAN"]
OBSERVACIONES = ["TRANCON EN LA VIA AL RELLENO", "ESPERA EN BASCULA", "VIA CERRADA POR OBRAS",
                 "LLUVIA FUERTE EN LA ZONA", "DANO EN EL COMPACTADOR"]
INICIO, FIN = dt.date(2025, 12, 1), dt.date(2026, 11, 4)


def hora(minutos):
    """Minutos desde medianoche -> (fecha_offset, hora)."""
    minutos = int(round(minutos))
    return minutos // 1440, dt.time((minutos % 1440) // 60, minutos % 60)


def sumar(fecha, base_min, minutos):
    """Fecha y hora resultantes de sumar minutos a (fecha, base_min)."""
    desfase, h = hora(base_min + minutos)
    return fecha + dt.timedelta(days=desfase), h


# --------------------------------------------------------------------------
# 3. Generación de filas
# --------------------------------------------------------------------------
def generar_filas(n_filas, rng):
    n_apoyo = max(1, round(n_filas * 0.09))
    n_normal = n_filas - n_apoyo - 1          # -1 por la fila duplicada que se siembra
    dias_habiles = [INICIO + dt.timedelta(days=i) for i in range((FIN - INICIO).days + 1)
                    if (INICIO + dt.timedelta(days=i)).weekday() != 6]
    usados = set()
    filas = []

    def nueva_fecha_ruta():
        while True:
            f = dias_habiles[rng.integers(len(dias_habiles))]
            ruta = RUTAS[rng.integers(len(RUTAS))]
            if (f, ruta[0]) not in usados:
                usados.add((f, ruta[0]))
                return f, ruta

    for _ in range(n_normal):
        f, (cod, kg_base, km_base, transp_plan) = nueva_fecha_ruta()
        kg = kg_base * FACTOR_MES[f.month] * FACTOR_DIA[f.weekday()] * rng.normal(1, 0.04)
        kg = int(min(max(round(kg, -1), 6800), 14500))
        tripulantes = rng.choice([2, 3, 4], p=[0.3, 0.5, 0.2])
        retraso = 0
        obs = ""
        if rng.random() < 0.14:                                  # incidente que alarga la ruta
            retraso = int(rng.integers(25, 70))
            obs = OBSERVACIONES[rng.integers(len(OBSERVACIONES))]
        t_ruta = 68 + 0.0203 * kg - 7 * (tripulantes - 3) + rng.normal(0, 15) + retraso
        t_ruta = int(max(t_ruta, 120))
        if rng.random() < 0.82:
            inicio_min = int(rng.integers(330, 511))             # turno de día 5:30 - 8:30
        else:
            inicio_min = int(rng.integers(1230, 1411))           # turno de noche 20:30 - 23:30
        f_fin, h_fin = sumar(f, inicio_min, t_ruta)
        sal = inicio_min + t_ruta + int(rng.integers(20, 56))
        ing = sal + int(rng.integers(35, 76))
        sal_rell = ing + int(rng.integers(12, 41))
        lleg = sal_rell + int(rng.integers(40, 76))
        km = int(round(km_base + rng.normal(0, 5)))
        filas.append(dict(
            fecha=f, ruta=cod, apoyo="", kg=kg, compactado=int(round(kg / 204 + rng.normal(0, 3))),
            kg_plan=int(round(kg_base * 1.08, -1)),
            f_ini=f, h_ini=hora(inicio_min)[1], f_fin=f_fin, h_fin=h_fin,
            t_ruta_plan=int(round((68 + 0.0203 * kg_base + 10) / 5) * 5),
            **dict(zip(("f_sal_rell", "h_sal_rell"), sumar(f, 0, sal))),
            **dict(zip(("f_ing_rell", "h_ing_rell"), sumar(f, 0, ing))),
            **dict(zip(("f_sal_de_rell", "h_sal_de_rell"), sumar(f, 0, sal_rell))),
            **dict(zip(("f_lleg", "h_lleg"), sumar(f, 0, lleg))),
            t_transp_plan=transp_plan, tripulantes_n=int(tripulantes),
            comb=round(km / float(np.clip(rng.normal(3.7, 0.35), 2.8, 4.8)), 2),
            comb_plan=round(km_base / 3.6, 2), km=km, km_plan=km_base, obs=obs))

    for _ in range(n_apoyo):                                      # viajes de apoyo: pequeños, sin relleno
        f, (cod, _kg, _km, _t) = nueva_fecha_ruta()
        kg = int(round(rng.uniform(800, 2500), -1))
        inicio_min = int(rng.integers(360, 900))
        t_ruta = int(rng.integers(45, 111))
        f_fin, h_fin = sumar(f, inicio_min, t_ruta)
        filas.append(dict(
            fecha=f, ruta=cod, apoyo="X", kg=kg, compactado=int(round(kg / 97)), kg_plan=0,
            f_ini=f, h_ini=hora(inicio_min)[1], f_fin=f_fin, h_fin=h_fin, t_ruta_plan=0,
            f_sal_rell=None, h_sal_rell=None, f_ing_rell=None, h_ing_rell=None,
            f_sal_de_rell=None, h_sal_de_rell=None, f_lleg=None, h_lleg=None,
            t_transp_plan=None, tripulantes_n=2, comb=round(float(rng.uniform(1.5, 6)), 2),
            comb_plan=0, km=int(rng.integers(4, 23)), km_plan=0, obs=""))

    filas.sort(key=lambda r: (r["fecha"], r["h_ini"]))
    odometro = {v[0]: v[2] for v in VEHICULOS}
    ticket = 17900000
    por_fecha = {}
    for r in filas:
        libres = por_fecha.setdefault(r["fecha"], list(rng.permutation(len(VEHICULOS))))
        v = VEHICULOS[libres.pop() if libres else rng.integers(len(VEHICULOS))]
        r["vehiculo"], r["placa"] = v[0], v[1]
        r["dia"] = DIAS[r["fecha"].weekday()]
        r["odo_ini"] = odometro[v[0]]
        odometro[v[0]] += r["km"]
        r["odo_fin"] = odometro[v[0]]
        ticket += int(rng.integers(20, 200))
        r["ticket"] = ticket
        r["conductor"] = CONDUCTORES[rng.integers(len(CONDUCTORES))]
        r["tripulantes"] = "-".join(rng.choice(AYUDANTES, r.pop("tripulantes_n"), replace=False))
        r["supervisor"] = SUPERVISORES[rng.integers(len(SUPERVISORES))]
    return filas


def sembrar_problemas(filas, rng):
    """Defectos típicos de un Excel digitado a mano (para practicar la limpieza)."""
    normales = [i for i, r in enumerate(filas) if r["apoyo"] != "X"]
    elegidos = list(rng.choice(normales, 14, replace=False))
    for i in elegidos[:4]:                                        # combustible sin digitar
        filas[i]["comb"] = None
    for i in elegidos[4:9]:                                       # odómetros vacíos, km digitado a mano
        filas[i]["odo_ini"] = filas[i]["odo_fin"] = None
        filas[i]["km_manual"] = filas[i]["km"]
    for i in elegidos[9:12]:                                      # día escrito distinto
        filas[i]["dia"] = filas[i]["dia"].replace("é", "e").capitalize()
    filas[elegidos[12]]["kg"] *= 10                               # kilogramos con un cero de más
    filas.insert(elegidos[13] + 1, dict(filas[elegidos[13]]))     # fila duplicada (mismo ticket)
    return filas


# --------------------------------------------------------------------------
# 4. Fórmulas del Excel y los mismos cálculos en Python (para el CSV)
# --------------------------------------------------------------------------
def formulas(n):
    """Fórmulas de la fila n (columnas calculadas)."""
    L = LETRA
    return {
        "t_ruta": f'=IF(AND(ISNUMBER({L["h_ini"]}{n}),ISNUMBER({L["h_fin"]}{n})),({L["f_fin"]}{n}+{L["h_fin"]}{n})-({L["f_ini"]}{n}+{L["h_ini"]}{n}),"")',
        "t_en_rell": f'=IF(ISNUMBER({L["h_ing_rell"]}{n}),({L["f_sal_de_rell"]}{n}+{L["h_sal_de_rell"]}{n})-({L["f_ing_rell"]}{n}+{L["h_ing_rell"]}{n}),0)',
        "t_rell": f'=IF(ISNUMBER({L["h_sal_rell"]}{n}),({L["f_lleg"]}{n}+{L["h_lleg"]}{n})-({L["f_sal_rell"]}{n}+{L["h_sal_rell"]}{n}),0)',
        "t_total": f'={L["t_ruta"]}{n}+{L["t_rell"]}{n}',
        "t_total_plan": f'=IF({L["t_ruta_plan"]}{n}>0,{L["t_ruta_plan"]}{n}+{L["t_transp_plan"]}{n},0)',
        "t_extra": f'=IF({L["t_total_plan"]}{n}>0,MAX(0,{L["t_total"]}{n}-{L["t_total_plan"]}{n}),0)',
        "t_improd": f'=IF({L["t_ruta_plan"]}{n}>0,MAX(0,{L["t_ruta"]}{n}-{L["t_ruta_plan"]}{n}),0)',
        "gal_km": f'=IF(AND(ISNUMBER({L["comb"]}{n}),{L["km"]}{n}>0),{L["comb"]}{n}/{L["km"]}{n},"")',
        "km_gal": f'=IF(AND(ISNUMBER({L["comb"]}{n}),{L["comb"]}{n}>0),{L["km"]}{n}/{L["comb"]}{n},"")',
        "kg_gal": f'=IF(AND(ISNUMBER({L["comb"]}{n}),{L["comb"]}{n}>0),{L["kg"]}{n}/{L["comb"]}{n},"")',
        "ef_carga": f'=IF({L["kg_plan"]}{n}>0,{L["kg"]}{n}/{L["kg_plan"]}{n},"")',
        "ef_comb": f'=IF(AND(ISNUMBER({L["comb"]}{n}),{L["comb"]}{n}>0,{L["comb_plan"]}{n}>0),{L["comb_plan"]}{n}/{L["comb"]}{n},"")',
        "ef_tiempo": f'=IF(AND({L["t_total"]}{n}>0,{L["t_total_plan"]}{n}>0),{L["t_total_plan"]}{n}/{L["t_total"]}{n},"")',
        "rend_global": f'=IF(COUNT({L["ef_carga"]}{n}:{L["ef_tiempo"]}{n})=3,AVERAGE({L["ef_carga"]}{n}:{L["ef_tiempo"]}{n}),"")',
    }


def minutos(f, h):
    return None if h is None else (f.toordinal() * 1440 + h.hour * 60 + h.minute)


def calcular(r):
    """Mismos cálculos que las fórmulas, en minutos / números (para el CSV)."""
    c = {}
    c["t_ruta"] = minutos(r["f_fin"], r["h_fin"]) - minutos(r["f_ini"], r["h_ini"])
    c["t_en_rell"] = (minutos(r["f_sal_de_rell"], r["h_sal_de_rell"]) - minutos(r["f_ing_rell"], r["h_ing_rell"])
                      if r["h_ing_rell"] is not None else 0)
    c["t_rell"] = (minutos(r["f_lleg"], r["h_lleg"]) - minutos(r["f_sal_rell"], r["h_sal_rell"])
                   if r["h_sal_rell"] is not None else 0)
    c["km"] = (r["odo_fin"] - r["odo_ini"]) if r.get("odo_ini") is not None else r["km_manual"]
    c["t_total"] = c["t_ruta"] + c["t_rell"]
    plan = (r["t_ruta_plan"] + r["t_transp_plan"]) if r["t_ruta_plan"] > 0 else 0
    c["t_total_plan"] = plan
    c["t_extra"] = max(0, c["t_total"] - plan) if plan > 0 else 0
    c["t_improd"] = max(0, c["t_ruta"] - r["t_ruta_plan"]) if r["t_ruta_plan"] > 0 else 0
    comb = r["comb"]
    ok = comb is not None and comb > 0
    c["gal_km"] = comb / c["km"] if ok and c["km"] > 0 else None
    c["km_gal"] = c["km"] / comb if ok else None
    c["kg_gal"] = r["kg"] / comb if ok else None
    c["ef_carga"] = r["kg"] / r["kg_plan"] if r["kg_plan"] > 0 else None
    c["ef_comb"] = r["comb_plan"] / comb if ok and r["comb_plan"] > 0 else None
    c["ef_tiempo"] = plan / c["t_total"] if c["t_total"] > 0 and plan > 0 else None
    efs = [c["ef_carga"], c["ef_comb"], c["ef_tiempo"]]
    c["rend_global"] = sum(efs) / 3 if all(e is not None for e in efs) else None
    return c


def hmm(m):
    return "" if m is None else f"{int(round(m)) // 60}:{int(round(m)) % 60:02d}"


# --------------------------------------------------------------------------
# 5. Escritura de Excel y CSV
# --------------------------------------------------------------------------
def escribir_excel(filas, ruta_xlsx, semilla):
    wb = Workbook()
    ws = wb.active
    ws.title = "Rutas"
    fuente = Font(name="Arial", size=9)
    verde = PatternFill("solid", fgColor="1E7B1E")
    azul = PatternFill("solid", fgColor="9DC3E6")
    for j, (clave, titulo, tipo) in enumerate(COLUMNAS, start=1):
        c = ws.cell(row=1, column=j, value=titulo)
        c.fill = azul if tipo == "plan" else verde
        c.font = Font(name="Arial", size=9, bold=True, color="1F3864" if tipo == "plan" else "FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(j)].width = 28 if clave in ("tripulantes", "obs") else 13
    ws.row_dimensions[1].height = 45
    for i, r in enumerate(filas, start=2):
        f = formulas(i)
        for j, clave in enumerate(CLAVES, start=1):
            if clave == "km":                                      # fórmula, o digitado si faltan odómetros
                v = (f'={LETRA["odo_fin"]}{i}-{LETRA["odo_ini"]}{i}'
                     if r.get("odo_ini") is not None else r["km_manual"])
            elif clave in f:
                v = f[clave]
            else:
                v = r.get(clave)
            if clave in ("t_ruta_plan", "t_transp_plan") and v is not None:
                v = v / 1440                                       # minutos -> fracción de día (formato hora)
            c = ws.cell(row=i, column=j, value=v)
            c.font = fuente
            if clave in COLS_FECHA:
                c.number_format = "dd/mm/yyyy"
            elif clave in COLS_HORA:
                c.number_format = "h:mm"
            elif clave in COLS_DURACION:
                c.number_format = "[h]:mm"
            elif clave in ("kg", "kg_plan", "odo_ini", "odo_fin", "ticket"):
                c.number_format = "#,##0;-#,##0;\"-\"" if clave != "ticket" else "0"
            elif clave in ("comb", "comb_plan", "gal_km", "km_gal", "kg_gal"):
                c.number_format = "0.00"
            elif clave.startswith("ef_") or clave == "rend_global":
                c.number_format = "0.0%"
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNAS))}{len(filas) + 1}"

    d = wb.create_sheet("Diccionario")
    d.append(["Columna", "Letra", "Tipo", "Unidad / formato", "Origen"])
    unidades = {"kg": "kilogramos", "comb": "galones", "km": "km", "odo_ini": "km acumulados"}
    for clave, titulo, tipo in COLUMNAS:
        unidad = unidades.get(clave, "fecha dd/mm/aaaa" if clave in COLS_FECHA else
                              "hora h:mm" if clave in COLS_HORA else "duración [h]:mm" if clave in COLS_DURACION else "")
        origen = {"dato": "Digitado", "calc": "Fórmula", "plan": "Planeado (valor digitado)"}[tipo]
        d.append([titulo, LETRA[clave], tipo, unidad, origen])
    d.append([])
    d.append(["Supuestos sobre las fórmulas (deducidos de capturas del Excel real; verificar):"])
    for t in ["TIEMPOS DE RUTA = (fecha y hora fin) - (fecha y hora inicio).",
              "TIEMPOS EN RELLENO = salida del relleno - ingreso al relleno.",
              "TIEMPOS RELLENO = llegada a base - salida al relleno (verificado con 2 filas reales).",
              "TIEMPO TOTAL = TIEMPOS DE RUTA + TIEMPOS RELLENO (verificado con 2 filas reales).",
              "TIEMPO TOTAL PLANEADO = T. RUTA PLANEADO + T. TRANSPORTE PLANEADO (supuesto).",
              "TIEMPOS DEMAS DE LO PLANEADO = max(0, TIEMPO TOTAL - TIEMPO TOTAL PLANEADO) (supuesto).",
              "TIEMPO IMPRODUCTIVO = max(0, TIEMPOS DE RUTA - T. RUTA PLANEADO) (supuesto).",
              "EFICIENCIA EN CARGA = kg / kg planeados; EN COMBUSTIBLE = planeado / real; EN TIEMPO = planeado / real (supuestos).",
              "RENDIMIENTO GLOBAL = promedio de las tres eficiencias (supuesto).",
              "COMPACTADO: significado por confirmar con la empresa; aquí es un conteo proporcional a los kg.",
              "APOYO = 'X' marca viajes de apoyo (pocos kg, sin viaje al relleno)."]:
        d.append([t])
    for col, w in zip("ABCDE", (34, 8, 8, 22, 28)):
        d.column_dimensions[col].width = w
    for fila in d.iter_rows():
        for c in fila:
            c.font = Font(name="Arial", size=10, bold=(c.row == 1))

    n = wb.create_sheet("Notas")
    for linea in [
        "DATOS SIMULADOS - no provienen de la empresa.",
        f"Generados con src/generar_datos_simulados.py (semilla {semilla}); nombres, placas y observaciones inventados.",
        "Estacionalidad simulada: más toneladas en diciembre, enero, junio y julio; lunes más cargado que sábado.",
        "Defectos sembrados a propósito para practicar la limpieza: combustible vacío (4 filas), odómetros vacíos con km",
        "digitado a mano (5), día escrito distinto (3), kilogramos con un cero de más (1), fila duplicada (1) y viajes de",
        "apoyo (APOYO = X). Las columnas calculadas son fórmulas; Excel las recalcula al abrir.",
        "Los resultados de los modelos con estos datos validan el método, no la operación real de la empresa.",
    ]:
        n.append([linea])
    n.column_dimensions["A"].width = 120
    for fila in n.iter_rows():
        for c in fila:
            c.font = Font(name="Arial", size=10, bold=(c.row == 1))
    wb.save(ruta_xlsx)


def escribir_csv(filas, ruta_csv):
    with open(ruta_csv, "w", newline="", encoding="utf-8") as archivo:
        w = csv.writer(archivo)
        w.writerow([c[1] for c in COLUMNAS])
        for r in filas:
            calc = calcular(r)
            fila = []
            for clave, _titulo, _tipo in COLUMNAS:
                v = calc[clave] if clave in calc else r.get(clave)
                if clave in COLS_FECHA:
                    v = v.strftime("%d/%m/%Y") if v else ""
                elif clave in COLS_HORA:
                    v = v.strftime("%H:%M") if v else ""
                elif clave in COLS_DURACION:
                    v = hmm(v)
                elif isinstance(v, float):
                    v = round(v, 4)
                fila.append("" if v is None else v)
            w.writerow(fila)


def main():
    p = argparse.ArgumentParser(description="Genera datos simulados de rutas de recolección.")
    p.add_argument("--filas", type=int, default=120)
    p.add_argument("--semilla", type=int, default=2026)
    p.add_argument("--salida", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    a = p.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.semilla)
    filas = sembrar_problemas(generar_filas(a.filas, rng), rng)
    escribir_excel(filas, a.salida / "rutas_simuladas.xlsx", a.semilla)
    escribir_csv(filas, a.salida / "datos_originales.csv")
    print(f"{len(filas)} filas simuladas -> {a.salida}")


if __name__ == "__main__":
    main()
