"""Estima el precio histórico de una vivienda a partir de sus características."""

import argparse
import math
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2", required=True, type=float, dest="living_m2")
    parser.add_argument("--habitaciones", required=True, type=int, dest="bedrooms")
    parser.add_argument("--banos", required=True, type=float, dest="bathrooms")
    parser.add_argument("--calidad", required=True, type=int, choices=range(1, 14), dest="grade")
    parser.add_argument("--estado", required=True, type=int, choices=range(1, 6), dest="condition")
    parser.add_argument("--agua", type=int, choices=(0, 1), default=0, dest="waterfront")
    parser.add_argument("--construccion", required=True, type=int, dest="yr_built")
    parser.add_argument("--postal", required=True, dest="zipcode")
    fields = vars(parser.parse_args())
    path = ROOT / "artifacts/modelo_precio.joblib"
    if not path.is_file():
        parser.error("Entrena el modelo primero con python scripts/construir.py.")
    # Usa el modelo generado localmente por scripts/analisis.py.
    model = joblib.load(path)
    known_zips = model.steps[0][1].named_transformers_["zip"].categories_[0]
    if fields["zipcode"] not in known_zips:
        parser.error("Introduce un código postal que aparezca en los datos de entrenamiento.")
    if (not math.isfinite(fields["living_m2"]) or not math.isfinite(fields["bathrooms"])
            or fields["living_m2"] <= 0 or fields["bedrooms"] < 0 or fields["bathrooms"] < 0
            or not 1800 <= fields["yr_built"] <= 2015):
        parser.error("Introduce una superficie positiva, conteos no negativos y un año entre 1800 y 2015.")
    estimate = model.predict(pd.DataFrame([fields]))[0]
    print(f"Precio histórico estimado: USD {estimate:,.0f}")


if __name__ == "__main__":
    main()
