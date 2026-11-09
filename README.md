# Sistema inteligente para la planificación y optimización de rutas de recolección de residuos

Proyecto final de Inteligencia Artificial — Ingeniería de Sistemas.

- **Grupo 04:** Damián Correa Tusarma y Saray Foronda Restrepo
- **Docente:** Jhon James Cano Sánchez
- **Contexto:** servicio de recolección y transporte de residuos en Cartago, Valle del Cauca.

## 1. Problema y objetivo
La generación de residuos aumenta en ciertas épocas del año y algunas rutas se sobrecargan. El objetivo es
**predecir, antes de salir a la ruta, si tendrá ALTO TONELAJE** (más toneladas que la mediana histórica) para
que el supervisor pueda reasignar vehículos o redefinir rutas con anticipación.

## 2. Datos
- **Fuente:** el histórico real de la empresa no estaba disponible para el proyecto. Se generó un conjunto
  **SIMULADO** (120 registros, `src/generar_datos_simulados.py`, semilla 2026) que **conserva la estructura
  real de 48 columnas** del Excel de seguimiento (rutas, vehículos, tripulación, kilogramos, tiempos, combustible).
- Se sembraron errores típicos de digitación para practicar la limpieza.
- **Importante:** los resultados validan el método, **no** el desempeño real de la empresa. Con datos reales
  deben repetirse el entrenamiento y la evaluación.
- Archivos: `data/rutas_simuladas.xlsx` (con fórmulas), `data/datos_originales.csv` (entrada),
  `data/datos_limpios.csv` (salida de la preparación).

### Limpieza (`src/preparacion_datos.py`)
| Problema | Decisión |
|---|---|
| 1 fila duplicada | Se elimina |
| 11 viajes de apoyo (`APOYO = X`) | Se excluyen: son otro servicio |
| 1 valor de 98.700 kg (cero de más) | Se elimina; la variable objetivo no se imputa |
| Día escrito de formas distintas | Se recalcula desde la fecha |
| Nulos en combustible | Se imputan dentro del `Pipeline`, solo con datos de entrenamiento |

Resultado: 120 → **107 filas**.

## 3. Decisiones de diseño
- **Etiqueta:** `alto_tonelaje = 1` si las toneladas superan la **mediana del conjunto de entrenamiento**.
- **Sin fuga de datos (data leakage):** se divide primero (75 % entrenamiento, 25 % prueba); umbral, imputación
  y escalado se calculan solo con entrenamiento.
- **Variables conocidas antes de la ruta:** mes, día de la semana, ruta, vehículo, turno, tripulantes y kg, km y
  tiempo planeados. No se usan km recorridos, tiempo real ni combustible, porque solo se conocen después.

## 4. Estructura del proyecto
```
├── data/            datos (originales, limpios y simulados)
├── graficos/        gráficos de análisis y evaluación (PNG)
├── docs/            informe y presentación
├── src/
│   ├── generar_datos_simulados.py
│   ├── preparacion_datos.py     limpieza + 3 gráficos de análisis
│   ├── perceptron_proyecto.py   perceptrón con NumPy
│   ├── modelo_proyecto.py       modelos scikit-learn, validación cruzada, joblib
│   ├── usar_modelo.py           predicción de casos nuevos
│   └── modelo_final.joblib      modelo entrenado
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## 5. Cómo ejecutar (Docker)
```bash
git clone https://github.com/Dami0921/Proyecto_ia-python.git
cd Proyecto_ia-python
docker compose up -d --build
docker compose exec python python src/preparacion_datos.py
docker compose exec python python src/perceptron_proyecto.py
docker compose exec python python src/modelo_proyecto.py
docker compose exec python python src/usar_modelo.py
```
Modo interactivo (demo en vivo):
```bash
docker exec -it ia_python python src/usar_modelo.py --interactivo
```
Los gráficos se guardan en `graficos/`. Para regenerar los datos simulados:
`docker compose exec python python src/generar_datos_simulados.py`.

## 6. Resultados
### Modelos de scikit-learn (validación cruzada de 5 pliegues sobre el entrenamiento)
| Modelo | Exactitud | Recall | F1 | ROC-AUC |
|---|---|---|---|---|
| Regresión logística | 0.875 | 0.850 | 0.871 | 0.922 |
| Árbol de decisión | 0.838 | 0.825 | 0.837 | 0.830 |
| **Random Forest** | 0.888 | 0.850 | **0.881** | 0.936 |

El mejor por F1 es **Random Forest**. En el conjunto de prueba (27 filas): exactitud 0.778, matriz de confusión
`[[9, 1], [5, 12]]` (5 rutas altas no detectadas).

### Perceptrón con NumPy
Entradas: `kg_planeados` y `temporada_alta` (dic, ene, jun, jul). Pesos: w1 = 2.915, w2 = 1.653, b = -0.015.
Exactitud: 88.8 % en entrenamiento y 88.9 % en prueba; matriz de confusión en prueba `[[12, 3], [0, 12]]`.

### Gráficos
| Archivo | Contenido |
|---|---|
| `grafico1_toneladas_por_mes.png` | Estacionalidad |
| `grafico2_toneladas_por_ruta.png` | Toneladas por ruta |
| `grafico3_duracion_vs_toneladas.png` | Duración vs toneladas (descriptivo) |
| `grafico4_matriz_confusion.png` | Evaluación del mejor modelo |
| `grafico5_curva_aprendizaje.png` | Curva de aprendizaje |
| `grafico6_perceptron_perdida.png` | Pérdida del perceptrón |
| `grafico7_perceptron_frontera.png` | Frontera de decisión |

## 7. Limitaciones
- Datos simulados: no representan el desempeño real de la empresa.
- Conjunto de prueba pequeño (27 filas): la exactitud de prueba es inestable; se prefiere la validación cruzada.
- El Random Forest sobreajusta (F1 de entrenamiento = 1.0); más datos o limitar la profundidad podrían mejorarlo.
- La etiqueta es global, por lo que el modelo depende mucho de qué ruta se trata.
- La temporada alta del perceptrón proviene de la simulación y debe verificarse con datos reales.

## 8. Cambios respecto al Avance 2
Datos nuevos, división entrenamiento/prueba, umbral y escalado calculados solo con entrenamiento, pesos
iniciales aleatorios, entradas conocidas antes de la ruta y métricas en prueba. [Completar con la
retroalimentación recibida del docente.]

## 9. Equipo y contribuciones
[Completar: quién hizo qué.] El repositorio se administró desde la cuenta de Damián Correa, según lo acordado
con el docente.

## 10. Uso de inteligencia artificial
**Herramienta:** Claude (Anthropic), asistente de IA generativa.

**Tareas en que se usó:** explicar conceptos (neurona, perceptrón, descenso del gradiente, métricas); guiar la
configuración de WSL, Docker y Git; depurar errores; escribir y revisar código (preparación de datos,
perceptrón, modelos de scikit-learn, uso del modelo); generar el conjunto de datos simulado y su
script; y apoyar la redacción de la documentación.

**Verificación:** el código se ejecutó en el contenedor Docker, las cifras se compararon con la salida y los
gráficos se revisaron. El grupo puede explicar cada decisión y es responsable de todo lo entregado.

**Referencia (APA 7):** Anthropic. (2026). *Claude* (versión de noviembre de 2026) [Modelo de lenguaje de gran
tamaño]. https://claude.ai