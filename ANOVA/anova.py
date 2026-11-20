import sys

import matplotlib
matplotlib.use("Agg")  # permite guardar gráficas sin pantalla
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.oneway import anova_oneway

ALFA = 0.05
RUTA = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "ventas.csv"

lineas = []


def reportar(texto=""):
    print(texto)
    lineas.append(texto)


# ------------------------------------------------------------------
# 1. Datos
# ------------------------------------------------------------------
df = pd.read_csv(RUTA)
df = df[["zipcode", "price"]].dropna()
df["zipcode"] = df["zipcode"].astype(str)
# El precio está muy sesgado a la derecha; el logaritmo lo acerca a una distribución normal.
df["log_price"] = np.log(df["price"])

grupos = {z: g["log_price"].to_numpy() for z, g in df.groupby("zipcode")}
muestras = list(grupos.values())

reportar("ANOVA: precio de vivienda por zona (código postal)")
reportar("=" * 60)
reportar(f"Ventas analizadas: {len(df):,}")
reportar(f"Zonas (grupos): {len(grupos)}")
reportar(f"Variable dependiente: log(precio)   Factor: zipcode   Alfa = {ALFA}")
reportar()
reportar("Hipótesis")
reportar("  H0: el precio promedio es igual en todas las zonas.")
reportar("  H1: al menos una zona tiene un precio promedio distinto.")
reportar()

# ------------------------------------------------------------------
# 2. Supuestos
# ------------------------------------------------------------------
reportar("Supuesto 1 - Normalidad (Shapiro-Wilk por zona, sobre log(precio))")
p_shapiro = {}
for z, valores in grupos.items():
    if len(valores) >= 3:
        muestra = valores if len(valores) <= 5000 else np.random.default_rng(1).choice(valores, 5000, replace=False)
        p_shapiro[z] = stats.shapiro(muestra).pvalue
no_normales = sum(p < ALFA for p in p_shapiro.values())
reportar(f"  Zonas que NO pasan normalidad (p < {ALFA}): {no_normales} de {len(p_shapiro)}")
residuos = df["log_price"] - df.groupby("zipcode")["log_price"].transform("mean")
reportar(f"  Asimetría de los residuos: {stats.skew(residuos):.3f}  (cercano a 0 = simétrico)")
reportar()

lev = stats.levene(*muestras, center="median")
reportar("Supuesto 2 - Homogeneidad de varianzas (Levene)")
reportar(f"  Estadístico = {lev.statistic:.3f}   p-valor = {lev.pvalue:.3e}")
varianzas_iguales = lev.pvalue >= ALFA
reportar("  Conclusión: " + ("varianzas homogéneas." if varianzas_iguales
                             else "varianzas distintas -> se usa también ANOVA de Welch."))
reportar()

# ------------------------------------------------------------------
# 3. Pruebas
# ------------------------------------------------------------------
anova = stats.f_oneway(*muestras)
welch = anova_oneway(df["log_price"], df["zipcode"], use_var="unequal")
kruskal = stats.kruskal(*muestras)

k, n = len(muestras), len(df)
media_total = df["log_price"].mean()
ss_entre = sum(len(v) * (v.mean() - media_total) ** 2 for v in muestras)
ss_total = ((df["log_price"] - media_total) ** 2).sum()
eta2 = ss_entre / ss_total

reportar("Resultados")
reportar(f"  ANOVA clásico:      F({k - 1}, {n - k}) = {anova.statistic:.2f}   p-valor = {anova.pvalue:.3e}")
reportar(f"  ANOVA de Welch:     F = {welch.statistic:.2f}   p-valor = {welch.pvalue:.3e}")
reportar(f"  Kruskal-Wallis:     H = {kruskal.statistic:.2f}   p-valor = {kruskal.pvalue:.3e}")
reportar("  (Un p-valor mostrado como 0.000e+00 significa p < 0.001: es tan pequeño que no se puede representar.)")
reportar(f"  Tamaño del efecto (eta²): {eta2:.3f}  -> la zona explica el {eta2 * 100:.1f} % de la variación de log(precio)")
reportar()

rechaza = welch.pvalue < ALFA and kruskal.pvalue < ALFA
reportar("Conclusión")
if rechaza:
    reportar(f"  p-valor < {ALFA} en las tres pruebas: se rechaza H0.")
    reportar("  Existen diferencias significativas en el precio de la vivienda entre zonas;")
    reportar("  la ubicación (código postal) influye en el precio.")
else:
    reportar(f"  p-valor >= {ALFA}: no se rechaza H0. No hay evidencia de diferencias entre zonas.")
reportar()

resumen = (df.groupby("zipcode")["price"]
             .agg(ventas="count", promedio="mean", mediana="median")
             .sort_values("promedio", ascending=False))
reportar("Las 5 zonas más caras y las 5 más baratas (precio en USD)")
reportar(resumen.head(5).round(0).to_string())
reportar("...")
reportar(resumen.tail(5).round(0).to_string())

with open("anova_resultados.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lineas))

# ------------------------------------------------------------------
# 4. Gráficas
# ------------------------------------------------------------------
orden = df.groupby("zipcode")["price"].median().sort_values().index
datos = [df.loc[df["zipcode"] == z, "price"] / 1e6 for z in orden]

fig, ax = plt.subplots(figsize=(18, 6))
ax.boxplot(datos, showfliers=False, patch_artist=True,
           boxprops=dict(facecolor="#2a7de1", alpha=0.6), medianprops=dict(color="black"))
ax.set_xticks(range(1, len(orden) + 1))
ax.set_xticklabels(orden, rotation=90, fontsize=8)
ax.set_xlabel("Zona (código postal), ordenadas por mediana")
ax.set_ylabel("Precio (millones USD)")
txt_p = "p < 0.001" if welch.pvalue < 0.001 else f"p = {welch.pvalue:.3f}"
ax.set_title(f"Precio de vivienda por zona - ANOVA de Welch: {txt_p}")
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig("anova_boxplot.png", dpi=150)

fig, ax = plt.subplots(figsize=(6, 6))
stats.probplot(residuos, dist="norm", plot=ax)
ax.set_title("Gráfico Q-Q de los residuos (log del precio)")
ax.set_xlabel("Cuantiles teóricos (normal)")
ax.set_ylabel("Residuos observados")
fig.tight_layout()
fig.savefig("anova_qqplot.png", dpi=150)

print("\nArchivos generados: anova_resultados.txt, anova_boxplot.png, anova_qqplot.png")