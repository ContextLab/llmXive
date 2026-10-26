# Research: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

## Decision / Rationale

**Compute feasibility (CPU‑first)**: All methods (XGBoost, Random Forest, OLS, Optuna TPE, SHAP TreeExplainer, bootstrap refits) run comfortably on a modest multi‑CPU, moderate‑memory GitHub Actions runner. No GPU escape hatch is needed. The inner Bayesian search is limited to 2 h; 1,000 bootstrap refits use fixed hyperparameters and are parallelised across the two available cores, keeping total wall‑clock < 6 h; RAM guard with a sufficiently large sample fallback ensures memory safety.

**Dataset availability – blocking finding**: The spec cites NIST and a *Journal of Materials Science* dataset, but verification found **no open, programmatically downloadable source** for hydrogen diffusion coefficients with the required descriptors. Fabricating a synthetic dataset would violate the Constitution. Consequently:

- The pipeline is fully implemented and unit‑tested using tiny fixture rows (as required by US‑1 independent tests).  
- Real result‑producing runs **require** a file `data/raw/diffusion_measurements.csv` matching `contracts/dataset.schema.yaml`. If absent, the pipeline aborts with an explicit “no verified data source” error.  
- A **manual‑entry scope correction** (see plan.md) provides a CSV template and provenance‑recording guidelines.

**Methodological rigor**:

- **Nested CV**: 5‑fold outer, inner Bayesian optimization inside each outer training fold; all preprocessing (imputation, scaling) fitted only inside inner folds (FR‑002).  
- **Multiple comparisons**: Holm‑adjusted p‑values for pairwise RMSE/R² comparisons among XGBoost, Random Forest, and linear baseline (FR‑003).  
- **Power**: FR‑009’s a‑priori claim is now verified by a **simulation‑based power analysis** (Monte‑Carlo) confirming ≥ 200 samples give ≥ 0.80 power for detecting interaction effect size *f*² ≥ 0.15 (α = 0.05) and bootstrap CI widths ≤ 0.1. A post‑hoc analysis reports observed `f²_interaction` (derived from the permutation‑based interaction variance share), the minimum detectable `f²` at 0.80 power, and the CI width for the top descriptor, flagging any shortfall.  
- **Causal framing**: Observational data; all importance and interaction statements are explicitly associative.  
- **Collinearity**: Raw temperature is retained **only for the non‑linear models**; the linear baseline uses the reciprocal `inv_temperature`. This respects FR‑008 while eliminating perfect collinearity in the non‑linear models. VIF diagnostics are logged; any predictor with VIF > 5 triggers a warning.  
- **Provenance independence** (FR‑007, Constitution VII): Element property tables are bundled in‑repo and independent of diffusion measurements; proxy formulas are documented as D‑independent; target never participates in imputation or scaling.  
- **Interaction‑variance metric**: Primary SC‑006 metric is **ablation ΔR² share** computed by permuting each descriptor pair in the full non‑linear model on an independent hold‑out set (internal stratified split, due to lack of a verified DOE dataset) and aggregating the loss in R². A secondary SHAP‑interaction magnitude ratio is provided **solely as descriptive context**.  
- **Bootstrap limitation**: Fixed best hyperparameters are used across the 1,000 resamples to respect compute limits; this limitation is documented, and CI widths (SC‑002) are interpreted with the caveat that hyperparameter uncertainty is not captured.  
- **Resource guard**: `guard.py` monitors RAM (6 GB threshold → sampled subset) and wall‑clock (5 h 55 min abort). Graceful termination logs best‑so‑far results and exits with code 0.

**Sample‑size safeguard**: After ingestion, the pipeline checks that **≥ 200** samples are present (required by the a‑priori power analysis). If fewer samples are detected, the run aborts with a clear error explaining that the study would be under‑powered.

## Dataset Strategy

| Role | Source | Access Method | Variable Coverage |
|------|--------|---------------|-------------------|
| Primary diffusion data | **No verified open source found** – flagged, not fabricated | Requires a real file at `data/raw/diffusion_measurements.csv` matching `contracts/dataset.schema.yaml`; pipeline aborts if missing | Needs `diffusion_coefficient`, composition, processing parameters, `temperature` per row |
| Compositional properties | Bundled element‑property table (literature‑cited values, in‑repo) | Static CSV `src/pipeline/element_properties.csv` | Electronegativity, atomic radius per element |
| Microstructural proxies | Literature‑derived formulas (documented, D‑independent) | Pure Python functions in `ingest.py` | `free_volume_proxy`, `grain_boundary_density` |
| Test fixtures | Hard‑coded rows in `tests/data/fixture_rows.csv` | In‑repo | Used only for unit/contract tests, never for final results |

No dataset URL is cited for the diffusion data because none is verified; none is invented.

## Statistical Methods

- **Target**: `log10(D)` after unit harmonization.  
- **Models**: `xgboost.XGBRegressor`, `sklearn.ensemble.RandomForestRegressor`, `sklearn.linear_model.LinearRegression` (baseline). Non‑linear models receive **raw temperature** as a predictor; the linear baseline receives only `inv_temperature`.  
- **Search**: Optuna TPE (seed 42), objective = inner‑CV RMSE on log₁₀(D), 2 h budget, graceful exit + grid fallback (`max_depth=6, learning_rate=0.1, n_estimators=200`).  
- **Metrics**: outer‑fold RMSE & R² on log₁₀(D); Holm‑adjusted pairwise comparisons.  
- **SHAP**: `TreeExplainer.shap_interaction_values`; interactions ranked by mean absolute magnitude (descriptive).  
- **Interaction‑variance (primary)**: **ablation ΔR² share** on an independent hold‑out computed as  

  \[
  \frac{\displaystyle\sum_{i<j}\bigl(R^{2}_{\text{full}} - R^{2}_{\text{perm}}^{(i,j)}\bigr)}{R^{2}_{\text{full}} - R^{2}_{\text{linear}}}
  \]

 where `R²_perm^{(i,j)}` is obtained by permuting the two descriptors of pair *(i,j)* jointly in the **full** non‑linear model (all other features unchanged). The hold‑out set is a [deferred] stratified internal split (seed = 42) because no verified DOE dataset is available. Bootstrap 1,000 resamples yield a 95 % CI.
- **Bootstrap**: 1,000 resamples; refit full pipeline (imputation, scaling, model) **with fixed best hyperparameters**; recompute SHAP interactions; compute ΔR² for top interactions on hold‑out slices; 95 % percentile CIs for top‑5 feature importances. Parallelised with `joblib.Parallel(n_jobs=2)`.  
- **External hold‑out**: Not available; internal stratified split used (see above). The limitation is explicitly reported.  
- **Power**: (1) **A‑priori simulation** confirming n ≥ 200 yields ≥ 0.80 power for f² ≥ 0.15 and CI widths ≤ 0.1. (2) Post‑hoc `f²_interaction = (ΔR²_interaction_share) / (1 − ΔR²_interaction_share)` using `statsmodels.stats.power.FTestPower`; also compute **minimum detectable f²** at 0.80 power given observed `n`; report achieved power and CI width for the top descriptor, flagging any shortfall.  
- **Resource monitoring**: `psutil` RAM poll (6 GB threshold → sampled subset, seed = 42); wall‑clock abort at 5 h 55 min, exit code 0 with best‑so‑far results.

## Expected Deliverables

- Tables: `model_performance.parquet`, `interaction_terms.parquet`, `bootstrap_ci.parquet`, `external_validation.parquet`, `power_analysis.parquet`.  
- Figures: `rmse_comparison.png`, `shap_interaction_heatmap.png`, `bootstrap_feature_importance_violin.png`, `external_validation_plot.png`, `power_analysis_plot.png`.
