# Sistema inteligente para la planificación y optimización de rutas de recolección y transporte de residuos

Proyecto académico de Inteligencia Artificial — Movilidad y sostenibilidad urbana (Cartago, Valle del Cauca).

## Problemática

Una empresa real de recolección y transporte de residuos sólidos planifica sus rutas de forma
empírica, sin anticipar los cambios en la cantidad de residuos generados durante el año ni
optimizar los recorridos cuando cambian las condiciones del servicio. Esto genera ineficiencias
en el uso de recursos, personal, tiempo y combustible.

## Objetivo

Desarrollar un sistema que apoye la toma de decisiones operativas mediante:

1. Predicción de la generación de residuos (demanda futura por fecha/zona).
2. Optimización de rutas de recolección (minimizar distancia y tiempo — VRP).
3. Predicción de tiempos de viaje por ruta (módulo a evaluar según avance del semestre).

## Datos

- Origen: registros operativos de una empresa real de recolección de residuos (hora de
  salida de base, hora de inicio y fin de ruta, toneladas recolectadas, kilómetros recorridos,
  combustible tanqueado, conductor, tripulantes, entre otros).
- Estado actual: se está trabajando con un conjunto de datos ficticios (data/rutas_ejemplo.csv)
  que replica la estructura real, mientras se integra el histórico completo de la empresa.

## Tecnologías

- Python
- NumPy, Matplotlib
- Docker, Docker Compose
- Git, GitHub

## Estructura del proyecto
Proyecto_ia-python/
├── data/
│ ├── rutas_ejemplo.csv
│ ├── distribucion_toneladas.png
│ └── km_vs_toneladas.png
├── src/
│ ├── main.py
│ ├── cargar_datos.py
│ ├── analisis_proyecto.py
│ └── eda_proyecto.py
├── informe_proyecto.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md


## Ejecución

```bash
docker compose build
docker compose up -d
docker compose exec python bash -c "cd src && python cargar_datos.py"
```

Detener:

```bash
docker compose down
```

## Módulos desarrollados

- **cargar_datos.py**: `leer_datos()` lee un CSV y lo convierte en lista de diccionarios;
  `mostrar_resumen()` calcula total, promedio, máximo y mínimo de una columna.
- **analisis_proyecto.py**: calcula 5 estadísticas (promedio/máximo/mínimo de toneladas,
  promedio de km recorridos, total de combustible) y genera `informe_proyecto.md`.
- **eda_proyecto.py**: Análisis Exploratorio de Datos con NumPy y Matplotlib.

## Análisis Exploratorio de Datos (EDA)

Se realizó un EDA inicial sobre `data/rutas_ejemplo.csv` con NumPy y Matplotlib
(`src/eda_proyecto.py`).

**Variables analizadas:** toneladas recolectadas y kilómetros recorridos por ruta.

**Estadísticas encontradas:**

| Variable | Media | Mediana | Desv. estándar | Mínimo | Máximo |
|---|---|---|---|---|---|
| Toneladas | 8.5 | 8.5 | 1.1 | 6.9 | 10.1 |
| Km recorridos | 40.24 | 40.0 | 3.55 | 35.2 | 45.6 |

**Patrones observados:** con los datos ficticios actuales, las rutas con más
kilómetros recorridos tienden a recolectar más toneladas (relación positiva),
aunque la muestra es muy pequeña (5 registros) para confirmar la tendencia.
No hay valores atípicos evidentes.

**Relevancia para el modelo de IA:** esta relación entre distancia recorrida y
carga recolectada es justamente lo que el módulo de optimización de rutas (VRP)
necesita ponderar al planificar recorridos, y la dispersión de toneladas por
fecha es la señal base que alimentará el módulo de predicción de generación
de residuos una vez se integren los datos históricos reales de la empresa.

Gráficas generadas: `data/distribucion_toneladas.png`, `data/km_vs_toneladas.png`.

## Solución de problemas

**Docker no responde:**

```bash
docker --version
```

## Equipo

- Saray Foronda
- Damian Correa Tusarma

## Entregables

- [x] Código fuente en GitHub, con commits regulares.
- [x] Documentación (README.md).
- [ ] Presentación final con demo.