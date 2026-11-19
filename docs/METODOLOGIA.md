# Datos, metodología y resultados

## Extracción y limpieza

El dataset House Sales in King County, USA registra ventas en Washington del 2 de mayo de 2014 al 27 de mayo de 2015. El ETL descarga el CSV oficial de Kaggle y valida su esquema, fechas, importes, superficies, coordenadas y campos de agrupación. Mantiene el ID de propiedad y el código postal como texto.

| Control | Resultado |
| --- | ---: |
| Filas de entrada | 21.613 |
| Duplicados exactos | 0 |
| Filas excluidas por validación | 0 |
| Ventas limpias | 21.613 |
| Propiedades distintas | 21.436 |
| Códigos postales | 70 |
| Construcción registrada un año después del año de venta | 12 |

Se conservan las ventas repetidas de una misma propiedad como transacciones distintas. Las 12 filas donde la construcción figura en 2015 y la venta en 2014 se conservan y se marcan para revisión. Los valores atípicos de habitaciones, incluido un registro de 33, se conservan en el CSV. Para el gráfico se agrupan las viviendas de seis o más habitaciones.

La superficie habitable se multiplica por 0,09290304 para pasar de ft² a m². El indicador de precio medio por m² promedia los cocientes precio sobre superficie de cada transacción. El mapa usa el centro medio de las coordenadas de las ventas filtradas de cada código postal.

## Referencias para validar Power BI

Sin filtros, el precio medio es **USD 540.088**, la mediana es **USD 450.000** y el precio medio por m² habitable es **USD 2.843**. Hay **163 ventas frente al agua** de **21.613** (aprox. **0,75 %**). El código postal con mayor precio medio es **98039**, con **50 ventas** y un promedio de **USD 2.160.607**. Pearson entre superficie habitable y precio es **0,702**.

## ANOVA

La hipótesis nula es que los precios medios de viviendas con 3, 4 y 5 habitaciones son iguales. Se toma la primera venta observada por propiedad para que una reventa no aporte una segunda observación. Se calcula el ANOVA clásico, Levene con mediana y ANOVA de Welch. El criterio de decisión es α = 0,05.

| Habitaciones | Propiedades | Precio medio (USD) |
| --- | ---: | ---: |
| 3 | 9.731 | 466.483 |
| 4 | 6.849 | 635.649 |
| 5 | 1.586 | 787.996 |

Levene detectó diferencias de varianza, con **p ≈ 2,56 × 10⁻¹⁶⁴**. Welch dio **F ≈ 660,96** y **p ≈ 1,94 × 10⁻²⁴⁷**, por lo que al menos un grupo difiere en precio medio. El ANOVA clásico dio **F ≈ 825,88** y su p quedó por debajo de la precisión numérica devuelta por SciPy. El eta cuadrado clásico es **0,0834**. El contraste detecta una asociación y deja por estudiar ubicación, calidad y superficie como posibles factores de confusión.

## Modelo de precio histórico

Se usan ocho variables disponibles antes de conocer el precio: superficie habitable, habitaciones, baños, calidad, estado, frente al agua, año de construcción y código postal. La partición aleatoria usa la semilla 42 y agrupa por ID de propiedad para impedir que una reventa quede repartida entre entrenamiento y prueba. Se entrenó con **17.289 ventas** y se evaluó con **4.324**.

| Modelo | MAE (USD) | RMSE (USD) | R² |
| --- | ---: | ---: | ---: |
| Mediana de entrenamiento | 225.269 | 385.665 | −0,065 |
| Ridge | 100.801 | 169.268 | 0,795 |
| Bosque aleatorio | 91.414 | 157.198 | 0,823 |

El bosque aleatorio obtuvo el menor error absoluto medio en esta partición. La evaluación se limita a transacciones históricas de King County. Una partición temporal ayudaría a medir el rendimiento sobre ventas posteriores.
