"""Extrae, transforma y carga el CSV de ventas para Power BI y la web."""

import argparse
import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://www.kaggle.com/datasets/harlfoxem/housesalesprediction"
DOWNLOAD = "https://www.kaggle.com/api/v1/datasets/download/harlfoxem/housesalesprediction"
RAW = ROOT / "data/raw/kc_house_data.csv"
CLEAN = ROOT / "data/processed/ventas.csv"
DIST = ROOT / "dist"
SQFT_TO_M2 = 0.09290304
# Columnas numéricas que conserva el CSV limpio.
FIELDS = [
    "price", "bedrooms", "bathrooms", "sqft_living", "sqft_lot", "floors",
    "waterfront", "view", "condition", "grade", "sqft_above", "sqft_basement",
    "yr_built", "yr_renovated", "lat", "long", "sqft_living15", "sqft_lot15",
]
# La web reutiliza los campos calculados en el ETL y omite el ID de propiedad.
WEB_FIELDS = [
    "price", "living_m2", "price_per_m2", "bedroom_group", "bathroom_group",
    "yr_built", "zipcode", "waterfront", "lat", "long", "price_band_order",
]
BANDS = [0, 300_000, 500_000, 750_000, 1_000_000, 1_500_000, float("inf")]
BAND_LABELS = ["< 300 mil", "300 a < 500 mil", "500 a < 750 mil",
               "750 mil a < 1 M", "1 a < 1,5 M", "≥ 1,5 M"]


def download_csv(destination):
    """Extrae del ZIP el CSV original sin modificarlo."""
    with urlopen(DOWNLOAD, timeout=60) as response:
        content = response.read()
    with ZipFile(io.BytesIO(content)) as archive:
        csv = archive.read("kc_house_data.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(csv)


def transform(path):
    """Valida cada transacción, genera columnas de análisis y cuenta las incidencias."""
    # Leemos los identificadores y códigos postales como texto para conservar los ceros iniciales.
    raw = pd.read_csv(path, dtype={"id": "string", "zipcode": "string", "date": "string"})
    missing = sorted(set(["id", "date", "zipcode", *FIELDS]) - set(raw.columns))
    if missing:
        raise ValueError(f"El CSV no contiene estas columnas: {', '.join(missing)}")

    # Dos ventas de la misma propiedad se conservan si difieren en algún campo.
    sales = raw[["id", "date", "zipcode", *FIELDS]].drop_duplicates().copy()
    exact_duplicates = len(raw) - len(sales)
    # Convertimos fechas y números para que los valores ilegibles queden marcados como faltantes.
    sales["sale_date"] = pd.to_datetime(sales.pop("date"), format="%Y%m%dT%H%M%S", errors="coerce")
    sales[FIELDS] = sales[FIELDS].apply(pd.to_numeric, errors="coerce")

    # Comprobamos que cada venta tenga los datos necesarios para el análisis.
    valid_sales = (
        sales["id"].str.fullmatch(r"\d+", na=False)
        & sales["zipcode"].str.fullmatch(r"\d{5}", na=False)
        & sales["sale_date"].notna()
        & sales["price"].gt(0)
        & sales["sqft_living"].gt(0)
        & sales["bedrooms"].ge(0)
        & sales["bathrooms"].ge(0)
        & sales["yr_built"].between(1800, sales["sale_date"].dt.year + 1)
        & sales["waterfront"].isin([0, 1])
        & sales["lat"].between(46, 49)
        & sales["long"].between(-124, -120)
        & np.isfinite(sales[FIELDS]).all(axis=1)
    )
    sales = sales.loc[valid_sales].sort_values(["sale_date", "id"], kind="stable").copy()
    if sales.empty:
        raise ValueError("El CSV no contiene ventas que pasen la validación.")
    # Damos un número a cada transacción, ya que una propiedad puede venderse varias veces.
    sales["sale_id"] = range(1, len(sales) + 1)

    # Pasamos el área a m² para comparar el precio por unidad de superficie entre viviendas.
    sales["living_m2"] = (sales["sqft_living"] * SQFT_TO_M2).round(4)
    sales["price_per_m2"] = (sales["price"] / sales["living_m2"]).round(4)
    # Dejamos marcada la diferencia de año para que se pueda revisar en el CSV limpio.
    sales["built_after_sale_year"] = sales["yr_built"].gt(sales["sale_date"].dt.year)
    # El límite inferior de cada rango está incluido. El superior pasa al siguiente rango.
    sales["price_band"] = pd.cut(sales["price"], BANDS, right=False, labels=BAND_LABELS)
    sales["price_band_order"] = sales["price_band"].cat.codes + 1
    # Creamos etiquetas para que las categorías se lean fácilmente en los gráficos.
    sales["waterfront_label"] = sales["waterfront"].map({0: "Sin frente al agua", 1: "Frente al agua"})
    sales["bedroom_group"] = sales["bedrooms"].clip(upper=6).astype(int).astype(str).replace({"6": "6+"})
    sales["bathroom_group"] = sales["bathrooms"].astype(int).clip(upper=5).astype(str).replace({"5": "5+"})
    sales = sales[["sale_id", "id", "sale_date", "zipcode", *FIELDS, "living_m2", "price_per_m2",
                   "price_band", "price_band_order", "waterfront_label", "bedroom_group", "bathroom_group",
                   "built_after_sale_year"]]
    # Resumimos cuántas filas entraron, se descartaron o quedaron marcadas para revisión.
    metadata = {
        "source": SOURCE,
        "license": "CC0: Public Domain",
        "inputRows": len(raw),
        "exactDuplicates": exact_duplicates,
        "invalidRows": int((~valid_sales).sum()),
        "builtAfterSaleYear": int(sales["built_after_sale_year"].sum()),
        "sales": len(sales),
        "properties": int(sales["id"].nunique()),
        "dateMin": sales["sale_date"].min().date().isoformat(),
        "dateMax": sales["sale_date"].max().date().isoformat(),
        "zipcodes": int(sales["zipcode"].nunique()),
        "priceBands": [{"label": label, "min": minimum}
                       for label, minimum in zip(BAND_LABELS, BANDS)],
    }
    return sales, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source_options = parser.add_mutually_exclusive_group()
    source_options.add_argument("--source", type=Path, help="Ruta a una copia local del CSV original de Kaggle")
    source_options.add_argument("--refresh", action="store_true", help="Vuelve a descargar el CSV oficial")
    args = parser.parse_args()
    source = args.source or RAW
    if args.source is not None and not source.is_file():
        parser.error(f"No se encontró el CSV indicado: {source}")
    if args.refresh or not source.is_file():
        download_csv(source)

    sales, metadata = transform(source)
    # El mismo conjunto de ventas alimenta el CSV de Power BI y el JSON de la web.
    CLEAN.parent.mkdir(parents=True, exist_ok=True)
    DIST.mkdir(parents=True, exist_ok=True)
    sales.to_csv(CLEAN, index=False, date_format="%Y-%m-%d")
    browser_dataset = {
        "metadata": metadata,
        "fields": WEB_FIELDS,
        "rows": sales[WEB_FIELDS].to_numpy().tolist(),
    }
    (DIST / "ventas.json").write_text(
        json.dumps(browser_dataset, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    (CLEAN.parent / "calidad.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
    )
    print(f"{metadata['sales']:,} ventas limpias de {metadata['zipcodes']} códigos postales.")
    print(f"Power BI: {CLEAN.relative_to(ROOT)} | Web: {(DIST / 'ventas.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
