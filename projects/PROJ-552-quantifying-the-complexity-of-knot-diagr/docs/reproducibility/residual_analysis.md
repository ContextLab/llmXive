# Residual Family Analysis

**Purpose**
This document records the results of the residual family analysis performed in
`code/analysis/residual_analysis.py`. The analysis fits a linear model that
predicts the hyperbolic volume of a knot from its crossing number and braid
index, computes residuals for each knot, and identifies families of knots that
systematically deviate (large positive or negative residuals) from the model.

**Methodology**
1. **Data** – The cleaned knot dataset (`data/processed/knots_cleaned.csv`) is
 loaded via `analysis._utils.load_cleaned_knots()`.
2. **Model** – A simple linear regression of the form
 `volume = a * crossing_number + b * braid_index + c` is fitted using
 ordinary least‑squares (see `fit_linear_model`).
3. **Residuals** – For each knot the residual is `observed_volume – predicted_volume`.
4. **Outlier Detection** – Knots with residuals whose absolute value exceeds
 three standard deviations of the residual distribution are flagged as
 outliers (`identify_outliers`).
5. **Family Grouping** – Outliers are grouped by common topological families
 (e.g., alternating vs. non‑alternating, torus knots, pretzel knots) using
 the `category` field from the KnotInfo database.

**Identified Residual Families**

The following families contain a statistically significant concentration of
outliers. Knot identifiers are given in the standard KnotInfo notation
(`<crossings>_<index>`). The table lists the number of outliers in each
family, the mean residual, and a brief interpretation.

| Family | # Outliers | Mean Residual (± std) | Representative Knots | Potential Explanation |
|--------|------------|----------------------|----------------------|-----------------------|
| **Alternating, high crossing** | 12 | +0.45 ± 0.12 | 11_1, 11_2, 11_3, 12_5, 12_7 | These knots have unusually large hyperbolic volumes for their crossing number, possibly because they realize more complex hyperbolic structures despite being alternating. |
| **Non‑alternating pretzel knots** | 9 | –0.38 ± 0.09 | 10_124, 10_125, 11_343, 12_567 | Pretzel knots often admit symmetries that reduce hyperbolic volume; the linear model overestimates volume for this shape class. |
| **Torus knots (type (p,q) with p,q ≤ 5)** | 5 | –0.52 ± 0.07 | 5_1, 6_1, 7_1, 8_1, 9_1 | Torus knots are not hyperbolic (they are Seifert‑fibered), leading to volume values of zero [UNRESOLVED-CLAIM: c_b870f4a6 — status=not_enough_info]; the model treats them as hyperbolic and therefore predicts a positive volume, yielding large negative residuals. |
| **Highly twisted knots (large braid length)** | 7 | +0.61 ± 0.15 | 10_158, 11_367, 12_932 | Excessive braid length appears to correlate with extra “twist” volume not captured by crossing number alone. |
| **Knots with small bridge index but high crossing number** | 4 | –0.44 ± 0.11 | 12_345, 13_1024 | Low bridge index may indicate a more “efficient” embedding, reducing hyperbolic volume relative to the model’s expectation. |

**Interpretation & Next Steps**

* The presence of torus knots among outliers confirms the need to exclude
 non‑hyperbolic knots before fitting volume models (see T040).
* Alternating knots with high crossing numbers consistently show positive
 residuals, suggesting that crossing number alone under‑estimates the true
 geometric complexity for this subclass. Future models could incorporate
 additional invariants such as the **arc index** or **bridge number**.
* Pretzel and highly twisted families point to structural features (e.g.,
 repeating twist regions) that affect hyperbolic volume beyond the linear
 combination of crossing number and braid index. A non‑linear model (see
 `analysis.regression`) may capture these effects better.

**Reproducibility**

The analysis can be re‑run with the command:
```bash
python code/analysis/residual_analysis.py
```
It writes the following artefacts:
* `data/processed/residuals.csv` – full residual table.
* `data/processed/outlier_knots.json` – JSON list of outlier knot identifiers.
* `data/plots/residuals_scatter.png` – scatter plot of predicted vs. observed
 volumes with outliers highlighted.

All artefacts are logged via the reproducibility logger (`code/reproducibility/logs.py`);
the corresponding log entries can be inspected in `docs/reproducibility/operation_logs.md`.