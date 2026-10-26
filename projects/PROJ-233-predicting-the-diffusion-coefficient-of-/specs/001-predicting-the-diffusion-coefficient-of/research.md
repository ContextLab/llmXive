# Research: Predicting the Diffusion Coefficient of Hydrogen in Metals from Compositional and Microstructural Descriptors

## Decision / Rationale

**Compute feasibility (CPU‑first)**: Every named method — XGBoost, Random Forest, OLS, Optuna TPE, SHAP TreeExplainer, bootstrap refits — runs faithfully on a modest multi‑CPU (~7 GB) runner. No GPU escape hatch is needed (spec assumption “No GPU Requirement”). Budgets: inner Bayesian search ≤ 2 h with a 5‑minute grace exit; 1,000 bootstrap refits use **fixed best hyperparameters** to stay within the 6 h job limit (feasibility documented, not a methodological change — hyperparameters are selected once by the nested CV and held fixed across resamples); RAM guard with fixed‑seed 150‑sample fallback (FR‑006).

**Dataset availability — blocking finding**: The spec names the NIST Standard Reference Database and the *Journal of Materials Science* as data sources. Dataset verification found **no verified open, programmatically downloadable source** for hydrogen diffusion coefficients in metals with the required descriptors. Per data‑hygiene and anti‑fabrication rules, the prior draft's synthetic‑dataset approach is **rejected**: a synthetic stand‑in for real measurements would fabricate the study's observations. Consequences:

- The pipeline is implemented and tested against small, clearly‑labeled hard‑coded fixture rows (the spec's own US‑1 independent tests specify exactly this).  
- Result‑producing runs **require a real input file** at `data/raw/diffusion_measurements.csv` matching `contracts/dataset.schema.yaml`; the pipeline exits non‑zero with an explicit “no verified data source” message if it is absent.  
- A **scope correction** is requested (see plan.md): the spec must name an obtainable open dataset or formally authorize a provenance‑documented manual data‑entry path before this research stage can produce real results.

**Methodological rigor**:  
- **Nested CV** (5‑fold outer, inner Bayesian search inside each outer training fold) gives unbiased performance estimates; all preprocessing fitted inside inner folds only (FR‑002).  
- **Multiple comparisons**: Holm‑adjusted p‑values for pairwise RMSE differences among the three models (FR‑003).  
- **Power**: FR‑009’s a‑priori claim (≥ 200 samples ⇒ power ≥ 0.80 for f² ≥ 0.15, CI widths ≤ 0.1) is now **explicitly verified** by a **simulation‑based power analysis** (Monte‑Carlo) (Phase 8a). A post‑hoc analysis reports the observed effect size `f² = (R²_nl − R²_lin)/(1 − R²_nl)` using `statsmodels.stats.power.FTestPower`; also compute **minimum detectable f²** at 0.80 power given the realized `n`; report the achieved power only for transparency but note its limited inferential value.  
- **Causal framing**: observational data; all importance/interaction findings reported as associations (spec assumption “Methodological Framing”).  
- **Collinearity**: correlation matrix and VIF are computed; raw temperature and its reciprocal `inv_temperature` are perfectly collinear. The linear baseline **uses only `inv_temperature`**; the non‑linear models **include both raw temperature and `inv_temperature`** as predictors per FR‑008, with a logged VIF warning (addresses concerns 20cd3f9a and c2aa6e4f). Related proxies (e.g., free‑volume and grain‑boundary density derived from overlapping processing parameters) are reported descriptively, with no independent‑effect claims (Constitution VI/VII).  
- **Provenance independence** (FR‑007, Constitution VII): element property tables (electronegativity, atomic radius) are bundled in‑repo with cited literature provenance and are independent of any diffusion measurement; proxy formulas are documented as independent of D; the target is excluded from imputation and scaling fits.  
- **Temperature handling**: The pipeline creates a reciprocal temperature feature `inv_temperature = 1 / temperature` (K⁻¹) to respect the Arrhenius relationship of hydrogen diffusion. **Raw temperature is retained as a predictor for the non‑linear models** (XGBoost, Random Forest) while the linear baseline uses only `inv_temperature` (to avoid perfect collinearity).  
- **Interaction‑variance metric**: The primary SC‑006 metric is now **ablation ΔR² share** computed by **refitting a depth‑1 (main‑effects‑only) XGBoost model** on the same training data and evaluating on an independent hold‑out set. The share is `(R²_full − R²_main) / R²_full` and is reported with a bootstrap‑derived 95 % CI. A secondary SHAP‑magnitude ratio (Σ|SHAP interaction| / Σ|SHAP total|) is provided for interpretability, **explicitly labeled as descriptive only**.  
- **Bootstrap limitation**: Bootstrap refits (Phase 5) use the **fixed best hyperparameters** identified in the nested CV to meet FR‑006’s compute budget. This limitation is documented, and confidence‑interval widths (SC‑002) are interpreted with the caveat that hyperparameter‑selection uncertainty is not captured.  
- **Power analysis**: Phase 8 now contains two components: (1) **A‑priori simulation‑based power analysis** (Monte‑Carlo) confirming the ≥ 200‑sample requirement for detecting f² ≥ 0.15 with [deferred] power; (2) **Post‑hoc analysis** reporting observed effect size `f²`, **minimum detectable f²** at 0.80 power, and the 95 % CI width for the top‑ranked descriptor.  
- **External hold‑out**: The interaction‑share on the hold‑out is calculated via **ablation ΔR² share** (refitting a depth‑1 model) and a bootstrap‑derived 95 % CI. The SHAP‑based ratio is reported as a descriptive supplement, with a clear statement that it does **not** constitute a variance decomposition.  
- **Resource guard**: `guard.py` monitors RAM and wall‑clock; if RAM > 6 GB the pipeline logs “Memory limit approached – switching to sampled subset” and proceeds on a reproducible 150‑sample random subset (seed = 42). If wall‑clock > 5 h 55 min the optimization loop exits gracefully, records best‑so‑far results, and exits with code 0.

## Dataset Strategy

| Role | Source | Access Method | Variable Coverage |
|------|--------|---------------|-------------------|
| Primary diffusion data | **No verified open source found** — flagged, not fabricated | Requires a real file at `data/raw/diffusion_measurements.csv` matching `contracts/dataset.schema.yaml`; pipeline refuses to fabricate | Needs `diffusion_coefficient`, composition, processing parameters, `temperature` per row |
| Compositional properties | Bundled element‑property table (literature‑cited values, in‑repo) | Static CSV in `src/pipeline/element_properties.csv` | Electronegativity, atomic radius per element |
| Microstructural proxies | Literature‑derived formulas (documented, D‑independent) | Pure Python functions in `ingest.py` | `free_volume_proxy`, `grain_boundary_density` |
| Test fixtures | Hard‑coded small rows in `tests/data/fixture_rows.csv` | In‑repo | Used **only** for unit/contract tests, never for results; satisfies independent tests |

No dataset URL is cited for the diffusion data because none is verified; none is invented.

## Statistical Methods

- **Target**: `log10(D)` in m²/s (unit harmonization before transform).  
- **Models**: `xgboost.XGBRegressor`, `sklearn.ensemble.RandomForestRegressor`, `sklearn.linear_model.LinearRegression` (baseline). The non‑linear models receive **both raw temperature and its reciprocal** as predictors; the linear baseline receives only `inv_temperature`.  
- **Search**: Optuna `TPESampler` (seed 42), objective = inner‑CV RMSE on log₁₀(D), 2 h budget, graceful exit + grid fallback (`max_depth=6, learning_rate=0.1, n_estimators=200`) on non‑convergence (edge case).  
- **Metrics**: outer‑fold RMSE and R² on log₁₀(D); Holm‑adjusted pairwise comparisons.  
- **SHAP**: `TreeExplainer.shap_interaction_values`; interactions ranked by mean absolute magnitude (descriptive).  
- **Interaction‑variance (primary)**: **ablation ΔR² share** on an independent hold‑out computed by (R²_full − R²_main) / R²_full, where `R²_main` comes from a depth‑1 XGBoost model (main‑effects‑only) trained on the same data. Bootstrap 1,000 resamples yield a 95 % CI.  
- **Bootstrap**: b = 1…1000 resamples; refit full pipeline (imputation, scaling, model) **with fixed best hyperparameters** for feasibility; recompute SHAP interactions; ablation ΔR² for top interactions on held‑out slices; 95 % percentile CIs for top‑5 importances.  
- **External hold‑out**: pre‑CV stratified hold‑out (material‑family stratified, disjoint from folds); evaluate tuned best model; compute ablation ΔR² share with bootstrap CI; report against the ≥ 70 % criterion (FR‑010, SC‑006) as a measured outcome, with explicit CI uncertainty.  
- **Power**: (1) **A‑priori simulation** (Monte‑Carlo) confirming n ≥ 200 yields ≥ 0.80 power for f² ≥ 0.15 (α = 0.05) and CI widths ≤ 0.1. (2) Post‑hoc `f² = (R²_nl − R²_lin)/(1 − R²_nl)` using `statsmodels.stats.power.FTestPower`; also compute **minimum detectable f²** at 0.80 power given the observed n; report achieved power only for transparency but note its limited inferential value. Flag if power < 0.80 or CI > 0.1.  
- **Resource monitoring**: `psutil` RAM poll (6 GB threshold → logged 150‑sample fallback, seed‑controlled); wall‑clock abort at 5 h 55 min, exit code 0 with best‑so‑far results.

## Expected Deliverables

- Tables (produced only once real data is supplied): `model_performance.parquet`, `interaction_terms.parquet`, `bootstrap_ci.parquet`, `external_validation.parquet`, `power_analysis.parquet`.  
- Figures: `rmse_comparison.png`, `shap_interaction_heatmap.png`, `bootstrap_feature_importance_violin.png`, `external_validation_plot.png`, `power_analysis_plot.png`.  
- Summary report mapping each SC to its concrete measurement, plus the explicit data‑availability limitation statement.  
