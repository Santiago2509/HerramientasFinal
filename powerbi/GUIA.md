# Informe en Power BI Desktop

Power BI es el informe con modelo semántico y medidas DAX. La web presenta un tablero independiente que carga datos del mismo ETL. Si el profesor pide que la web muestre el informe de Power BI dentro de la página, hay que confirmar la modalidad de publicación y los permisos del espacio de trabajo.

## Importación y modelo

1. Ejecutar `python scripts/construir.py` desde la raíz. Genera `data/processed/ventas.csv` con una fila por transacción.
2. En Power BI Desktop, elegir **Obtener datos → Texto/CSV → Transformar datos** y renombrar la consulta como `Ventas`. Usar UTF-8 y coma como delimitador. Forzar `id`, `zipcode`, `price_band`, `bedroom_group` y `bathroom_group` a **Texto**. Para las columnas que usan punto decimal, aplicar **Cambiar tipo → Usar configuración regional → Inglés (Estados Unidos)** si la detección automática falla.
3. Asignar `sale_date` al tipo **Fecha**. Usar entero para `sale_id`, `bedrooms`, `yr_built`, `price_band_order` y `waterfront`. Usar decimal para `price`, `living_m2`, `price_per_m2`, `bathrooms`, `lat` y `long`. Después, elegir **Cerrar y aplicar**.
4. En `Ventas`, ordenar `price_band` por `price_band_order`. Categorizar `lat` como **Latitud**, `long` como **Longitud** y `zipcode` como **Código postal**.
5. Crear una **nueva tabla** con el código de abajo, marcarla como tabla de fechas y vincular `Calendario[Date]` (1) a `Ventas[sale_date]` (*) con filtro de Calendario hacia Ventas.
6. En **Nueva medida**, pegar un bloque a la vez desde [medidas.dax](medidas.dax). Si Power BI está configurado para usar separadores localizados, adapta las comas separadoras de argumentos. Formatear el precio en USD, la proporción como porcentaje y la correlación con tres decimales.

~~~dax
Calendario =
ADDCOLUMNS (
    CALENDAR ( MIN ( Ventas[sale_date] ), MAX ( Ventas[sale_date] ) ),
    "Año", YEAR ( [Date] ),
    "Año-mes", FORMAT ( [Date], "yyyy-MM" )
)
~~~

## Páginas del informe

| Página | Visual | Campos |
| --- | --- | --- |
| Mercado | Tarjetas | Ventas registradas, Precio mediano USD, Precio medio USD y Precio medio por m² USD |
| Mercado | Columnas | Eje price_band, valor Ventas registradas |
| Ubicación | Mapa | Ubicación zipcode, latitud y longitud en promedio, tamaño Ventas registradas, tooltip Precio medio USD y Precio medio por m² USD |
| Ubicación | Barras horizontales | Eje zipcode, valor Precio medio USD, filtro visual Top N = 10 por Precio medio USD |
| Características | Columnas | Ejes bedroom_group y bathroom_group en gráficos separados, valor Precio medio USD, tooltip Ventas registradas |
| Características | Línea | Eje yr_built como año continuo, valor Precio medio USD |
| Características | Dispersión | X living_m2, Y price, detalle sale_id y tarjeta Correlación superficie y precio |
| Características | Columnas | Eje waterfront_label, valor Precio medio USD, tooltip Ventas registradas |
| Estadística | Tablas y notas | Resultados de ANOVA y evaluación del modelo desde dist/analisis.json |

Agregar segmentadores por código postal, rango de precio, habitaciones y frente al agua. Para el mapa, activar Azure Maps si está permitido en la cuenta. Comprobar que las coordenadas representan el contexto del código postal y que los filtros actualizan el conteo y el precio.

Para importar el JSON de análisis en Power Query, usa **Obtener datos → JSON** y expande por separado las listas `anova.groups` y `model.metrics`. Los resultados describen el dataset completo, así que deja esas tablas sin relación con Ventas. Guarda el informe como `Proyecto4-KingCounty.pbix`.

El requisito de casas y apartamentos necesita un campo de tipo de vivienda de otra fuente. Si se aprueba una unión por identificador de propiedad, usar una dimensión de propiedades con relación 1 a muchos hacia Ventas, validar los identificadores y reportar el porcentaje de ventas con tipo conocido.
