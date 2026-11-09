# Informe del Proyecto: Optimizacion de Rutas de Recoleccion de Residuos

## Descripcion de los datos
Datos de rutas de recoleccion de residuos, con informacion de toneladas recolectadas, kilometros recorridos y combustible tanqueado por ruta (actualmente datos ficticios de prueba).

## Estadisticas
- Total de registros: 5
- Promedio de toneladas recolectadas: 8.5
- Maximo de toneladas recolectadas: 10.1
- Minimo de toneladas recolectadas: 6.9
- Promedio de kilometros recorridos: 40.24
- Total de combustible tanqueado (galones): 144

## Interpretacion
El promedio de toneladas por ruta indica la carga tipica que maneja cada vehiculo, dato clave para dimensionar la capacidad necesaria. La diferencia entre el maximo y el minimo de toneladas muestra que tan variable es la demanda entre rutas, lo que sustenta la necesidad de un modulo de prediccion de generacion de residuos. El promedio de kilometros y el total de combustible ayudan a estimar costos operativos, informacion que alimentara el modulo de optimizacion de rutas (VRP).
