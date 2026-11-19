# Exploración del mercado inmobiliario de King County

Proyecto 4. Analiza ventas residenciales históricas con un ETL reproducible, un tablero web, medidas DAX para Power BI y un análisis de precios en Python.

## Reproducir el proyecto

Requiere Python 3.11 o posterior. Los comandos se ejecutan desde la raíz del repositorio.

~~~bash
python -m venv .venv
# Linux o macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/construir.py
python -m http.server 8000 --directory dist
~~~

Abre [localhost:8000](http://localhost:8000). La primera ejecución descarga `kc_house_data.csv` de Kaggle. Si la descarga no está disponible, descarga el archivo desde la fuente oficial, descomprímelo en `data/raw/` y vuelve a ejecutar la construcción. Para usar otro archivo local con el mismo esquema, pasa `--source ruta/al/archivo.csv`.

| Salida generada | Uso |
| --- | --- |
| data/processed/ventas.csv | Tabla limpia para Power BI |
| data/processed/calidad.json | Control de filas, fechas y cobertura |
| dist/ | Tablero estático y datos para desplegar como web |
| dist/analisis.json | Grupos del ANOVA, métricas de predicción y correlación |
| artifacts/modelo_precio.joblib | Modelo entrenado por el script |

## Empezar el informe del equipo

- [Guía de Power BI](powerbi/GUIA.md) y [medidas DAX](powerbi/medidas.dax).
- [Metodología y resultados](docs/METODOLOGIA.md).
- [Pendientes y reparto entre cuatro integrantes](docs/PENDIENTES.md).

## Probar una predicción

~~~bash
python scripts/predecir.py --m2 180 --habitaciones 3 --banos 2 --calidad 7 --estado 3 --agua 0 --construccion 1990 --postal 98103
~~~

El resultado está en USD y corresponde al mercado de 2014–2015. `calidad` corresponde a `grade` (1–13) y `estado` a `condition` (1–5).

## Fuentes

- [House Sales in King County, USA](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction), publicado en Kaggle por harlfoxem bajo CC0.
- [TIGERweb del U.S. Census Bureau](https://tigerweb.geo.census.gov/tigerweb/) para el límite simplificado de King County. [OpenStreetMap](https://www.openstreetmap.org/copyright) para las teselas del mapa. [Leaflet](web/assets/leaflet/LICENSE) para la visualización geográfica.
