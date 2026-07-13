# Research: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

## Domain Context

Recrystallization kinetics in Al alloys result from the competition between stored energy from cold work and pinning by dispersoid‑forming elements (Mn, Si). The key measurable is **time‑to‑peak softening** (`time_to_peak`) recorded in minutes.

## Methodological Rigor

### 1. Feature Engineering
- Interaction terms: `cold_work_pct * mg_wt`, `cold_work_pct * si_wt`, `cold_work_pct * cu_wt`, `cold_work_pct * mn_wt`.  
- **Arrhenius normalization** (`time_to_peak_norm`) is computed *only* for exploratory visualizations; **all predictive modeling uses the raw `time_to_peak`** to avoid target leakage (addresses scientific concerns b4a13f4a & 81e8327f).

### 2. Modeling
- **Algorithm**: `RandomForestRegressor` (CPU‑only, `n_estimators=100`, `random_state=42`).  
- **Data split**: 80/20 train‑test split (seed = 42), stratified by `alloy_series` when possible.  
- **Cross‑validation**: 5‑fold CV on the training set.  
- **Outlier clipping**: Values > 1000 h are capped at the 99th percentile; clipped rows are logged.  
- **Small‑sample guard**: Pipeline aborts if total rows < 50 (insufficient for 5‑fold CV).

### 3. Statistical Significance of Interaction Terms (FR‑005)

Because Random Forests are non‑parametric, a Likelihood Ratio Test is not applicable. We therefore employ a **Permutation Test**:

| Step | Description |
|------|-------------|
| **a. Baseline** | Fit the **Additive Model** (cold work + composition only) and record its 5‑fold CV R². |
| **b. Full** | Fit the **Interaction Model** (additive + interaction terms) and record its 5‑fold CV R². |
| **c. Observed ΔR²** | Compute ΔR² = R²_interaction − R²_additive. |
| **d. Permutations** | For *N* = 1 000 iterations, **independently shuffle each interaction column** while keeping main‑effect columns unchanged, refit the Interaction Model, and record ΔR²ᵢ. |
| **e. Empirical p‑value** | p = ( #{ΔR²ᵢ ≥ ΔR²_observed} + 1 ) / (N + 1). |
| **f. Decision** | Interaction terms are deemed **significant** if p < 0.05. |

This non‑parametric test respects the Random Forest’s nature and provides a valid significance assessment.

### 4. Interpretation & Collinearity (FR‑006)

- **Permutation Importance**: Quantifies each feature’s contribution after permuting its values.  
- **Partial‑Dependence Plots**: Visualize the marginal effect of the top interaction terms on the predicted `time_to_peak`.  
- **Collinearity Note**: Interaction terms are derived from main effects; importance scores are interpreted descriptively, not as independent causal effects. We do not claim causal inference beyond observed associations.

### 5. Edge‑Case Handling
- **Pure Aluminum**: If all alloying‑element columns are zero, interaction terms become zero; the permutation test is reported as “N/A” for this subset.  
- **Outliers**: Handled as described; logs stored in `results/outlier_log.txt`.  
- **Insufficient Data**: Pipeline exits with an informative error; no metrics are produced.

## Expected Outputs

- `results/metrics.json` containing R², MAE, CV statistics, and the permutation‑test p‑value.  
- `results/feature_importance.json` with permutation importance scores.  
- Figures (`results/figures/`) for feature importance, partial dependence, and optional Arrhenius‑normalized exploratory plots.

## References

- Humphreys, F. J., & Hatherly, M. (2004). *Recrystallization and Related Annealing Phenomena*. (Activation energy Q = 140 kJ/mol, Table 4.2). DOI/URL: https://doi.org/10.1016/B978-044452866-0/50009-9  
