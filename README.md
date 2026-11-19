# Proyecto 4 · Exploración del mercado inmobiliario

Analizamos las ventas de viviendas de **King County, Washington**, registradas entre el 2 de mayo de 2014 y el 27 de mayo de 2015. El proyecto separa el CSV original, los datos limpios, el análisis y la página web. La web y Power BI usan las mismas ventas y los mismos cálculos del ETL.

## Qué se hizo y hasta dónde llegamos

| Parte | Estado |
| --- | --- |
| ETL | Terminado para el CSV asignado. Valida, ordena y transforma 21.613 ventas. El original y la salida limpia están en GitHub. |
| Página web | Construida y publicada en privado. Incluye filtros, mapa, ranking por código postal, gráficos y los resultados estadísticos. También se puede abrir en local. |
| ANOVA y predicción | Ejecutados en Python. Quedaron los scripts, los resultados y un comando para probar una estimación histórica. |
| Power BI | El CSV limpio, las medidas DAX y la guía están preparados. Falta crear, probar y entregar el archivo .pbix en Power BI Desktop. |
| Requisitos geográficos y tipos de vivienda | El CSV permite analizar códigos postales y propiedades frente al agua. Para distinguir barrios, casas de apartamentos o vista específicamente al mar, faltan campos. Consultar al profesor cómo quiere que se documenten esos casos. |

[Tablero web privado](https://mercado-inmobiliario-king-county.pointysycamore3.chatgpt.site) · [Guía de Power BI](powerbi/GUIA.md) · [Resultados y metodología](docs/METODOLOGIA.md)

## Dónde está cada archivo

| Archivo o carpeta | Para qué sirve |
| --- | --- |
| [data/raw/kc_house_data.csv](data/raw/kc_house_data.csv) | CSV original descargado de Kaggle. Es la entrada del ETL. |
| [data/processed/ventas.csv](data/processed/ventas.csv) | CSV limpio con una fila por venta. Es el archivo que se importa en Power BI. |
| [data/processed/calidad.json](data/processed/calidad.json) | Control de filas, fechas, códigos postales e incidencias. |
| [scripts/etl.py](scripts/etl.py) | Lee el original, limpia y exporta los datos a CSV y JSON. |
| [scripts/analisis.py](scripts/analisis.py) | Calcula ANOVA, correlación y métricas de predicción. |
| [scripts/construir.py](scripts/construir.py) | Ejecuta el ETL y el análisis y prepara la página. |
| [scripts/predecir.py](scripts/predecir.py) | Usa el modelo local para estimar un precio histórico. |
| [web/index.html](web/index.html) · [web/estilos.css](web/estilos.css) · [web/app.js](web/app.js) | Estructura, diseño y filtros de la página. |
| [web/assets/](web/assets/) | Límite geográfico de King County y biblioteca Leaflet. |
| [powerbi/medidas.dax](powerbi/medidas.dax) | Fórmulas que se crean como medidas en Power BI. |
| [requirements.txt](requirements.txt) · [.openai/hosting.json](.openai/hosting.json) | Dependencias de Python y configuración del sitio publicado. |
| dist/ · artifacts/ | Salidas locales generadas. Contienen la web lista para servir y el modelo entrenado. |

## Cómo se limpian y usan los datos

1. **Extraer.** El ETL lee el CSV de `data/raw/`. Se puede volver a descargar el original desde Kaggle con `python scripts/etl.py --refresh`.
2. **Transformar.** Comprueba columnas, fechas, precios, superficies y coordenadas. Mantiene el identificador y el código postal como texto. Convierte la superficie habitable a m², calcula el precio por m² y asigna rangos de precio. El archivo original tiene **cero duplicados exactos**. Se conservan las ventas distintas de una misma propiedad y se marcan **12 registros** cuyo año de construcción figura un año después de la venta.
3. **Cargar.** Guarda el CSV limpio y el informe de calidad en `data/processed/`. Para la web genera `dist/ventas.json` y `dist/analisis.json`. Los precios, conteos y gráficos de ventas salen del CSV asignado. El límite del condado y el mapa base aportan contexto geográfico.

## Cómo abrir la web y regenerar los datos

En GitHub, descarga el proyecto desde **Code → Download ZIP** y descomprímelo, o clona el repositorio. Abre una terminal en la carpeta que contiene este README. Con **Python 3.11 o posterior**, crea un entorno virtual.

~~~bash
python -m venv .venv
~~~

Actívalo en **PowerShell** con `.\.venv\Scripts\Activate.ps1` o en **macOS/Linux** con `source .venv/bin/activate`. Si PowerShell bloquea la activación, usa `.\.venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes.

~~~bash
python -m pip install -r requirements.txt
python scripts/construir.py
python -m http.server 8000 --directory dist
~~~

Abre [localhost:8000](http://localhost:8000). Para actualizar solo el CSV limpio y los datos de ventas de la web, ejecuta `python scripts/etl.py`. Para probar una predicción después de construir el proyecto, ejecuta este ejemplo.

~~~bash
python scripts/predecir.py --m2 180 --habitaciones 3 --banos 2 --calidad 7 --estado 3 --agua 0 --construccion 1990 --postal 98103
~~~

El resultado es una estimación en USD para el mercado de 2014–2015. `calidad` usa la columna `grade` (1–13) y `estado` usa `condition` (1–5).

## Qué falta y cómo terminarlo

| Integrante | Próximo paso | Cómo darlo por terminado |
| --- | --- | --- |
| 1 · Power BI | Importar el CSV limpio, crear el calendario y copiar las medidas DAX. Seguir la [guía de Power BI](powerbi/GUIA.md) para montar las páginas. | Guardar el .pbix y probar los filtros. Sin filtros deben aparecer 21.613 ventas, USD 540.088 de precio medio y USD 2.843 por m². |
| 2 · Web | Probar los filtros, el mapa y el reinicio en móvil y escritorio. Acordar con el equipo cómo dará acceso a la web al profesor. | Comprobar que el evaluador puede abrir el enlace o ejecutar la web en local con las instrucciones de arriba. |
| 3 · Estadística | Explicar qué compara el ANOVA, qué significa el MAE y qué se puede concluir del periodo histórico. Usar los [resultados reproducibles](docs/METODOLOGIA.md). | Redactar una conclusión breve con cifras y limitaciones. Si la rúbrica pide comparar pares de grupos, realizar esa prueba y documentarla. |
| 4 · Entrega | Revisar con el profesor los campos que faltan y preparar el informe o la presentación según la rúbrica. | Entregar el .pbix, la página y los resultados. Incluir el alcance de los códigos postales, el frente al agua y los tipos de vivienda. |

Usen la [lista de los diez requisitos](docs/PENDIENTES.md) para la revisión final. Si el profesor pide que Power BI aparezca dentro de la web, primero hay que publicar el informe y confirmar los permisos de inserción. El tablero actual carga directamente el JSON del ETL.

## Fuentes

- Ventas y variables de vivienda, bajo licencia CC0. [House Sales in King County, USA](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction)
- Límite del condado y mapa base. [TIGERweb, U.S. Census Bureau](https://tigerweb.geo.census.gov/tigerweb/) · [OpenStreetMap](https://www.openstreetmap.org/copyright)
