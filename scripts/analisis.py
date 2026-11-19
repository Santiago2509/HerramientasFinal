"""Calcula el ANOVA y evalúa dos modelos de precio frente a la mediana."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ["living_m2", "bedrooms", "bathrooms", "grade", "condition", "waterfront", "yr_built"]
FEATURES = [*NUMERIC, "zipcode"]


def anova(sales):
    """Compara los precios de viviendas con 3, 4 o 5 habitaciones."""
    # Usa la primera venta observada de cada propiedad para evitar contar reventas.
    first_sale = sales.sort_values(["sale_date", "sale_id"]).drop_duplicates(subset="id")
    groups = {beds: first_sale.loc[first_sale["bedrooms"].eq(beds), "price"].to_numpy()
              for beds in (3, 4, 5)}
    samples = list(groups.values())
    combined = np.concatenate(samples)
    total_ss = ((combined - combined.mean()) ** 2).sum()
    between_ss = sum(len(s) * (s.mean() - combined.mean()) ** 2 for s in samples)
    # Welch compara las medias aunque las varianzas de los grupos sean distintas.
    standard = stats.f_oneway(*samples)
    welch = stats.f_oneway(*samples, equal_var=False)
    levene = stats.levene(*samples, center="median")
    return {
        "alpha": 0.05,
        "groups": [{"bedrooms": beds, "count": len(s), "mean": float(s.mean()),
                    "median": float(np.median(s))} for beds, s in groups.items()],
        "anova": {"statistic": float(standard.statistic),
                  "p": float(standard.pvalue) if standard.pvalue else None,
                  "pUnderflow": not bool(standard.pvalue)},
        "welch": {"statistic": float(welch.statistic), "p": float(welch.pvalue)},
        "levene": {"statistic": float(levene.statistic), "p": float(levene.pvalue)},
        "etaSquared": float(between_ss / total_ss),
    }


def prediction(sales, model_path):
    """Entrena en unas propiedades y evalúa el error en propiedades distintas."""
    # Agrupa por ID para que una reventa nunca cruce entre entrenamiento y prueba.
    train, test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
                       .split(sales, groups=sales["id"]))
    x_train, x_test = sales.iloc[train][FEATURES], sales.iloc[test][FEATURES]
    y_train, y_test = sales.iloc[train]["price"], sales.iloc[test]["price"]
    metrics = []
    fitted = {}
    for name, estimator in (
        ("Mediana de entrenamiento", DummyRegressor(strategy="median")),
        ("Regresión Ridge", Ridge(alpha=10)),
        ("Bosque aleatorio", RandomForestRegressor(n_estimators=150, min_samples_leaf=3,
                                                   random_state=42, n_jobs=-1)),
    ):
        # Aprende escalas y códigos postales usando solo las filas de entrenamiento.
        encoding = ColumnTransformer([
            ("numeric", StandardScaler(), NUMERIC),
            ("zip", OneHotEncoder(handle_unknown="ignore"), ["zipcode"]),
        ])
        model = make_pipeline(encoding, estimator)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        metrics.append({
            "name": name,
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(root_mean_squared_error(y_test, predictions)),
            "r2": float(r2_score(y_test, predictions)),
        })
        fitted[name] = model
    # Se guarda el modelo con menor error absoluto medio en esta comparación.
    best = min(metrics, key=lambda result: result["mae"])["name"]
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted[best], model_path)
    return {"trainRows": len(train), "testRows": len(test), "features": FEATURES,
            "bestByMae": best, "metrics": metrics}


def main():
    sales = pd.read_csv(ROOT / "data/processed/ventas.csv", dtype={"id": "string", "zipcode": "string"})
    report = {
        "anova": anova(sales),
        "model": prediction(sales, ROOT / "artifacts/modelo_precio.joblib"),
        "pearson": float(sales["living_m2"].corr(sales["price"])),
    }
    # La web lee este resumen del dataset completo sin entrenar en el navegador.
    destination = ROOT / "dist/analisis.json"
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(f"ANOVA de Welch p = {report['anova']['welch']['p']:.3g}")
    print(f"Pearson superficie–precio = {report['pearson']:.3f}")
    for model in report["model"]["metrics"]:
        print(f"{model['name']}: MAE USD {model['mae']:,.0f}, R² {model['r2']:.3f}")


if __name__ == "__main__":
    main()
