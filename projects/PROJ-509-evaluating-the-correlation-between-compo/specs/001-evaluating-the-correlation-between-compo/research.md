# Research: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

## Overview

This research document details the methodology, data strategy, and statistical rigor for evaluating the correlation between compositional features and formation energy in inorganic materials. The primary goal is to identify which elemental properties (electronegativity, atomic radius, valence electrons, melting point, and ionization energy) are most predictive of formation energy using tree-based ensemble methods.

## Dataset Strategy

### Data Source

The primary dataset is the **Materials Project MP-2020.12.1** release.

*   **Verified Count**: A large set of inorganic compounds (Source: Q47604, https://www.wikidata.org/wiki/Q47604).
*   **Primary Source**: Zenodo mirror (programmatic download).
*   **Fallback Source**: `matminer`'s built-in `mp_formation` dataset (accessed via `pymatgen`/`matminer` without external API keys).
*   **Final Fallback**: Explicit error if both sources are unreachable. No fabricated URLs.

### Data Preprocessing

1.  **Filtering**: Retain only inorganic compounds (`is_inorganic=True`).
2.  **Completeness**: Remove entries with missing `formation_energy_per_atom` or `composition` data.
3.  **Elemental Properties**: Join with a local reference table of elemental properties. Entries with missing elemental properties will be excluded and logged.
4.  **Outlier Handling**: Formation energy values will be capped at the 1st and 99th percentiles **only if** more than 1% of the data falls outside these bounds. The number of capped values will be logged. This preserves metastable phases unless they are statistical noise.

### Stratification

*   **Method**: Stratified split by **Chemical Family**.
*   **Rationale**: Ensures similar distributions of compositional diversity in training and validation sets.
*   **Threshold**: 80/20.
*   **Note**: Chemical Family is used as a proxy for compositional diversity within structural classes.

### Statistical Rigor & Methodology

*   **Model Selection**:
    *   Random Forest Regressor: Parameters: `n_estimators=200`, `max_depth=20`. Rationale: Robust to non-linear relationships and feature interactions.
    *   Gradient Boosting Regressor: Parameters: `n_estimators=100`. Rationale: High predictive accuracy benchmark.
*   **Hardware**: CPU-only (scikit-learn).

### Evaluation Metrics

*   R² (Coefficient of Determination): Primary metric.
*   MAE (Mean Absolute Error): Interpretability.
*   RMSE (Root Mean Squared Error): Sensitivity to large errors.
*   Overfitting Check: `train_r2 / val_r2`. If `val_r2 <= 0`, the ratio is set to null and a "Model Failure" flag is logged.

### Feature Importance & Sensitivity

*   Tree-Based Importance: Extracted from Random Forest.
*   Permutation Importance: Calculated to validate ranking stability. Method: **Spearman correlation** (primary) and Pearson (robustness check) between tree-based and permutation importances. Threshold: r ≥ 0.8 indicates stable ranking. Note: Permutation importance is a consistency check, not a ground truth validation. Physical plausibility checks will be performed on top features.
*   Accumulated Local Effects (ALE) Plots: Generated for the top 3 features to visualize marginal effects. ALE is used instead of PDPs because it correctly handles correlated features.
*   Collinearity Check: Variance Inflation Factor (VIF) will be computed. If VIF > 10, the feature is flagged as "physically collinear" rather than an error, as elemental properties are inherently correlated by atomic structure. Features will be retained if scientifically meaningful.

### Multiple Comparison Correction

*   Protocol: Bonferroni correction will be applied when comparing the two models (RF vs. GB) or when testing multiple hypotheses. For the descriptive ranking of 5 descriptors, correction is not applied, but this is explicitly noted as a limitation in the interpretation.

### Sample Size & Power

*   Dataset Size: A verified collection of compounds.
*   Power Analysis: For a regression with 5 predictors, N=12,500 provides >99% power to detect a small effect size (f²=0.02) at α=0.05. This is sufficient for the study.

## Compute Feasibility

*   CPU-First: All methods are CPU-tractable.
*   Memory: 12,500 rows fit comfortably within 7 GB RAM. Chunked reading is used for robustness.
*   Time: Estimated runtime < 6 hours on a 2-core CPU.
*   GPU Escape Hatch: Not required.

## References

*   Materials Project: Verified count 12,500 (Q47604).
*   Methodology: Scikit-learn documentation.
*   Feature Engineering: `matminer` documentation.
