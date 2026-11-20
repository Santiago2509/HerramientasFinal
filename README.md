# Proyecto 4 · Exploración del mercado inmobiliario

Analizamos las ventas de viviendas de **King County, Washington**, registradas entre el 2 de mayo de 2014 y el 27 de mayo de 2015. El proyecto separa el CSV original, los datos limpios, el análisis y la página web. El archivo limpio del ETL se usa para el análisis estadístico y para el informe de Power BI que se muestra en la página.

## Qué se hizo y hasta dónde llegamos

| Parte | Estado |
| --- | --- |
| ETL | Terminado para el CSV asignado. Valida, ordena y transforma 21.613 ventas. El original y la salida limpia están en GitHub. |
| Página web | [web/index5.html](web/index5.html) presenta el proceso, incrusta el informe de Power BI y explica el ANOVA por código postal. |
| ANOVA y predicción | En Python hay un ANOVA por habitaciones, otro por código postal y una evaluación de modelos de predicción del precio histórico. |
| Power BI | El informe publicado está incrustado en la página. La carpeta powerbi guarda la guía y las medidas DAX de referencia. Si piden el archivo editable .pbix, el equipo debe incluirlo en la entrega. |
| Requisitos geográficos y tipos de vivienda | El CSV permite analizar códigos postales y propiedades frente al agua. Para distinguir barrios, casas de apartamentos o vista específicamente al mar, faltan campos. Consultar al profesor cómo quiere que se documenten esos casos. |

[Informe en Power BI](https://app.powerbi.com/view?r=eyJrIjoiZWEyYThkOTctYWEyNi00ODIzLWE4NDMtZDYxYTgxY2EzOWUyIiwidCI6IjhkMzY4MzZlLTZiNzUtNGRlNi1iYWI5LTVmNGIxNzc1NDI3ZiIsImMiOjR9) · [Guía de Power BI](powerbi/GUIA.md) · [Resultados y metodología](docs/METODOLOGIA.md)

## Qué hay en cada carpeta

| Carpeta | Archivos y función |
| --- | --- |
| [data/raw/](data/raw/) | [kc_house_data.csv](data/raw/kc_house_data.csv) es el archivo original de Kaggle y la entrada del ETL. |
| [data/processed/](data/processed/) | [ventas.csv](data/processed/ventas.csv) es el CSV limpio para Power BI. [calidad.json](data/processed/calidad.json) resume fechas, filas, cobertura e incidencias. |
| [scripts/](scripts/) | [etl.py](scripts/etl.py) limpia y exporta los datos con Python y pandas. [analisis.py](scripts/analisis.py) calcula el ANOVA por habitaciones y evalúa modelos de predicción. [predecir.py](scripts/predecir.py) estima un precio histórico. [construir.py](scripts/construir.py) ejecuta el ETL y el análisis y copia la página a dist/. |
| [ANOVA/](ANOVA/) | [anova.py](ANOVA/anova.py) compara el logaritmo del precio entre códigos postales. [anova_resultados.txt](ANOVA/anova_resultados.txt) guarda los resultados. [anova_boxplot.png](ANOVA/anova_boxplot.png) muestra la distribución por zona y [anova_qqplot.png](ANOVA/anova_qqplot.png) ayuda a revisar la normalidad de los residuos. [ventas.csv](ANOVA/ventas.csv) es una copia del CSV limpio. |
| [powerbi/](powerbi/) | [GUIA.md](powerbi/GUIA.md) describe la importación y el armado del informe. [medidas.dax](powerbi/medidas.dax) contiene las fórmulas de referencia. |
| [web/](web/) | [index5.html](web/index5.html) es la página de presentación con el informe incrustado. [app.js](web/app.js), [estilos.css](web/estilos.css) y [assets/](web/assets/) contienen el código, los estilos y los recursos del tablero web anterior, incluido el mapa. |
| [docs/](docs/) | [METODOLOGIA.md](docs/METODOLOGIA.md) explica la limpieza y el análisis. [PENDIENTES.md](docs/PENDIENTES.md) revisa los diez requisitos del proyecto. |

En la raíz, este README es el manual principal. [requirements.txt](requirements.txt) lista las dependencias del flujo de Python. [.gitignore](.gitignore) y [.gitattributes](.gitattributes) configuran cómo Git maneja los archivos. Al ejecutar la construcción se generan dist/ y artifacts/ con la web, los JSON y el modelo entrenado.

## Cómo se limpian y usan los datos

1. **Extraer.** El ETL lee el CSV de `data/raw/`. Se puede volver a descargar el original desde Kaggle con `python scripts/etl.py --refresh`.
2. **Transformar.** Comprueba columnas, fechas, precios, superficies y coordenadas. Mantiene el identificador y el código postal como texto. Convierte la superficie habitable a m², calcula el precio por m² y asigna rangos de precio. El archivo original tiene **cero duplicados exactos**. Se conservan las ventas distintas de una misma propiedad y se marcan **12 registros** cuyo año de construcción figura un año después de la venta.
3. **Cargar.** Guarda el CSV limpio y el informe de calidad en `data/processed/`. El informe de Power BI usa el CSV limpio y la página muestra sus gráficos.

## Cómo abrir la web y ejecutar el ETL

En GitHub, descarga el proyecto desde **Code → Download ZIP** y descomprímelo, o clona el repositorio. Abre una terminal en la carpeta que contiene este README. Con **Python 3.11 o posterior**, crea un entorno virtual.

~~~bash
python -m venv .venv
~~~

Actívalo en **PowerShell** con `.\.venv\Scripts\Activate.ps1` o en **macOS/Linux** con `source .venv/bin/activate`. Si PowerShell bloquea la activación, usa `.\.venv\Scripts\python.exe` en lugar de `python` en los comandos siguientes.

~~~bash
python -m pip install -r requirements.txt
python scripts/construir.py
~~~

Para regenerar solo los datos limpios, ejecuta `python scripts/etl.py`.

### Abrir la página

Desde la raíz, ejecuta `python -m http.server 8000 --directory web` y abre [localhost:8000/index5.html](http://localhost:8000/index5.html). El informe incrustado requiere conexión a Internet.

### Probar una predicción

Después de ejecutar `python scripts/construir.py`, prueba este ejemplo.

~~~bash
python scripts/predecir.py --m2 180 --habitaciones 3 --banos 2 --calidad 7 --estado 3 --agua 0 --construccion 1990 --postal 98103
~~~

El resultado es una estimación en USD para el mercado de 2014–2015. `calidad` usa la columna `grade` (1–13) y `estado` usa `condition` (1–5).

## Cómo presentar el proyecto

1. **Pregunta y datos.** «¿Cómo se relacionan la ubicación y las características de una vivienda con su precio de venta? Para responder, analizamos 21.613 ventas de King County, Washington, de 2014 a 2015».
2. **Limpieza.** Muestra el CSV original y el limpio. Explica que programaron el ETL en Python con pandas. Usa dos ejemplos, convertir la superficie de pies cuadrados a m² y calcular el precio por m².
3. **Power BI.** Abre el informe incrustado. Muestra la tarjeta de **USD 2.843 por m²**, el mapa o el ranking y un filtro. Explica que DAX calcula los indicadores a partir del CSV limpio.
4. **ANOVA.** Muestra el diagrama de cajas por código postal. Explica que Welch detectó diferencias entre zonas (p < 0,001). El **53 %** corresponde a la variación del **logaritmo del precio** asociada al código postal en la muestra.
5. **Predicción.** Muestra el gráfico de precio real frente a precio estimado en Power BI. Explica que el modelo estima un precio a partir de las características de la vivienda.
6. **Cierre.** Resume un hallazgo, por ejemplo que en la muestra las viviendas frente al agua tienen un precio medio mayor. Aclara que los códigos postales se usan para agrupar zonas y que el CSV no distingue casas de apartamentos ni identifica vistas al mar.

Antes de exponer, comprueben que el informe carga y que los filtros funcionan. Si la entrega pide el archivo editable, tengan a mano el .pbix que usaron para publicar el informe. Usen la [lista de los diez requisitos](docs/PENDIENTES.md) para la revisión final.

## Fuentes

- Ventas y variables de vivienda, bajo licencia CC0. [House Sales in King County, USA](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction)
- Límite del condado y mapa base. [TIGERweb, U.S. Census Bureau](https://tigerweb.geo.census.gov/tigerweb/) · [OpenStreetMap](https://www.openstreetmap.org/copyright)
