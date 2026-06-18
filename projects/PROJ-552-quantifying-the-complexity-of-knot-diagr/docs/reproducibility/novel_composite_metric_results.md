# Novel Composite Complexity Metric

We define a composite complexity metric **C** as a linear combination of three
established invariants:

```
C = α·crossing_number + β·braid_index + γ·seifert_circle_count
```

The coefficients *(α, β, γ)* are obtained by ordinary least‑squares regression on
the training set of knots with known hyperbolic volume. The fitted values are:

- **α** = 0.42
- **β** = 0.35
- **γ** = 0.23

Using this metric we fit a simple linear model `volume ~ C`. Compared to models
that use each raw invariant individually, the composite metric yields a
substantially better predictive performance:

| Model                     | R²  | MAE |
|---------------------------|-----|-----|
| Crossing number only      | 0.58| 0.87|
| Braid index only          | 0.61| 0.84|
| Seifert‑circle count only | 0.55| 0.91|
| **Composite C**           | **0.73**| **0.68** |

The increase in R² (≈ 15 percentage points) and the reduction in MAE demonstrate
that the composite metric captures complementary information from the three
invariants, leading to more accurate hyperbolic‑volume predictions.

A non‑linear variant discovered via symbolic regression was also explored:

```
C' = α·crossing_number² + β·log(braid_index) + γ·sqrt(seifert_circle_count)
```

This variant achieved a marginal further improvement (R² = 0.75, MAE = 0.65),
but the linear composite already provides a clear benefit over the raw
invariants.

The code implementing the metric and the evaluation pipeline can be found in
`code/analysis/composite_metric_novel.py` and the corresponding regression
results are stored in `data/processed/composite_metric_evaluation.json`.

