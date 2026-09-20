"""
config.py
Rutas del proyecto. Se calculan a partir de la ubicación de este archivo,
por lo que funcionan sin importar desde qué carpeta se ejecute el script
(raiz del proyecto, src/ o dentro del contenedor Docker en /app).
"""

from pathlib import Path

DIR_SRC = Path(__file__).resolve().parent
DIR_RAIZ = DIR_SRC.parent
DIR_DATOS = DIR_RAIZ / "data"

RUTA_CSV = DIR_DATOS / "rutas_ejemplo.csv"
RUTA_INFORME = DIR_RAIZ / "informe_proyecto.md"
