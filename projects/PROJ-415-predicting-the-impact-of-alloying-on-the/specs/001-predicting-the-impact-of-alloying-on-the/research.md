# Research: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Scientific Background
Diffusion in solids follows the Arrhenius relation  
\( D = D_0 \exp(-Q/RT) \) where \( Q \) is the activation energy. In FCC metals, alloying alters \( Q \) through lattice strain (size mismatch) and electronic effects. This study focuses on the geometric driver **size mismatch** (\( \Delta r / r_{\text{host}} \)) and its association with the activation-energy shift \( \Delta Q = Q_{\text{alloy}} - Q_{\text{host}} \).

## Spec Gap (flagged for kickback)
FR-001 authorizes only FCC **self**-diffusion rows. Model training (FR-003–FR-005) requires FCC **solute/impurity** diffusion rows for descriptor variance. The spec must be amended (FR-001 + US-1 Scenario 1) to authorize the self/solute split before the training-set extraction is implemented. Until then, the pipeline implements FR-001 as written (self-only) and the solute-row tasks are deferred.

## Dataset Strategy

| Role | Filter Criteria | Source | Availability |
|------|----------------|--------|--------------|
| **Curated Set** (per current FR-001) | `crystal_structure == "FCC"` **and** `diffusion_mode == "self"` | NIST SRD 150 (Diffusion in Solids) | **No verified open URL** in the supplied list; pipeline will attempt to download from a verified mirror if provided via environment variable `NIST_SRD150_URL`. If the URL is missing or the file cannot be fetched, the pipeline aborts with the exact error `"ERROR: No verified real dataset found. Synthetic data is not permitted for this research goal."` |
| **Training Set** (solute/impurity diffusion) — `[SPEC-AMENDMENT-PENDING]` | `crystal_structure == "FCC"` **and** `diffusion_mode` in `["solute","impurity"]` | Same NIST SRD 150 source | Deferred until FR-001 is amended per the Spec Gap above. |

### Data Processing Pipeline
1. **Streaming Load & Availability Check** (`code/data/streaming_loader.py`) – verifies that at least one row satisfies the FR-001 filter; halts otherwise.  
2. **Baseline Extraction** – isolates self-diffusion rows, records `host_element` ↔ `activation_energy_eV` mapping.  
3. **Training Extraction** `[SPEC-AMENDMENT-PENDING]` – isolates solute/impurity rows, drops rows with missing concentration or activation energy, logs exclusions to `errors/missing_data.csv`.  
4. **Merge** – joins training rows with baseline mapping to compute `baseline_shift_eV = activation_energy_eV - Q_host`.  
5. **Atomic Descriptor Join** – enriches each row with host/solute radii, electronegativities, and derived `size_mismatch`, `electronegativity_diff`, `valence_electron_diff`. Missing atomic data trigger exclusion and logging to `errors/missing_atomic_data.csv`.

If the total file size exceeds RAM, `pandas.read_csv(..., chunksize=…)` processes data chunk-wise while accumulating the necessary statistics.

## Feature Engineering
- **Size Mismatch**: \((r_{\text{solute}} - r_{\text{host}}) / r_{\text{host}}\) – computed using `periodictable==0.20.1`.  
- **Electronegativity Difference**: \(|\chi_{\text{solute}} - \chi_{\text{host}}|\) (Pauling scale).  
- **Valence Electron Count Difference**: `abs(VEC_solute - VEC_host)`.  
- **Solute Concentration** (`concentration_at_percent`): retained as a **covariate** in the inferential model (see below); not dropped.  
- **Baseline Shift** (`baseline_shift_eV`) as defined above.  
All features are stored in `data/curated/filtered.csv`, which conforms to `contracts/dataset.schema.yaml`.

## Concentration Handling
Activation energy can vary with solute concentration, so the `size_mismatch` coefficient would conflate solute identity with concentration effects if concentration were ignored. Handling:
1. **Primary inferential model**: multivariate Linear Regression including `concentration_at_percent` as a covariate, so the reported `size_mismatch` coefficient is adjusted for concentration.  
2. **Dilute-limit sensitivity check**: re-fit the same model on the dilute subset (rows with `concentration_at_percent` ≤ 5 at.%); both full-model and dilute-limit coefficients are reported, and any material discrepancy is flagged in the final report.  
3. Concentration distribution is reported descriptively (min/median/max) so reviewers can assess residual confounding.

## Model Strategy

| Model | Purpose | Library | Hyper-parameter Grid | Validation |
|-------|---------|---------|----------------------|------------|
| Random Forest | Accurate prediction of \( \Delta Q \) | `sklearn.ensemble.RandomForestRegressor` | `max_depth` [3-10], `n_estimators` [50-200] | Nested CV (default) or 80/20 hold-out if \(N<50\) |
| Gradient Boosting | Complementary non-linear predictor | `sklearn.ensemble.GradientBoostingRegressor` | Same grid as RF | Same validation as RF |
| Linear Regression | Infer statistical significance of `size_mismatch` | `statsmodels.OLS` (multivariate: `size_mismatch`, `electronegativity_diff`, `valence_electron_diff`, `concentration_at_percent`) | No hyper-params | Bootstrapped 95 % CI and p-value (10,000 resamples) |

All models are trained on CPU only; total grid-search runtime on ≤ 500 rows is expected < 15 min.

## Statistical Rigor & Validation

1. **Performance Metrics** – R², RMSE, MAE computed on the held-out test set for RF & GB.  
2. **Baseline Comparison** – R² must exceed 0.0 (better than mean predictor) per SC-001; RMSE vs. the mean-predictor is also reported for context.  
3. **Linear Coefficient Significance** – Bootstrap with 10,000 resamples (sampling with replacement, stratified by host metal if possible). The **bootstrap p-value** is computed by percentile inversion of the two-sided bootstrap distribution: `p = 2 * min(frac(coef* <= 0), frac(coef* >= 0))`, where `coef*` are the 10,000 resampled coefficients (the same resample set used for the 95 % percentile CI). Significance requires p < 0.05 AND the 95 % CI excluding zero → **SC-002**.  
4. **Threshold Sensitivity** – Sweep thresholds 0.45 – 0.55 eV (step 0.01 eV). For each threshold compute classification rate (fraction of alloys with `baseline_shift_eV` > threshold). Compute **Stability Index** = `std(classification_rates) / (max_threshold - min_threshold)`. Must satisfy ≤ 0.05 1/eV → **SC-003**.  
5. **Multiple-Comparison** – The inferential model is **multivariate** (four predictors). A single coefficient (`size_mismatch`) is the pre-registered primary hypothesis; its p-value is interpreted at α = 0.05 without correction. The remaining coefficients (electronegativity_diff, valence_electron_diff, concentration) are reported as **descriptive** associations and are not interpreted as confirmatory tests; if any are promoted to confirmatory status in future work, a Holm–Bonferroni correction across the tested family will be applied.  
6. **Power Considerations** – If the dataset contains < 50 rows, the plan switches to a strict 80/20 split and notes limited statistical power in the final report.  
7. **Inference Framing** – The data are observational; all relationships are reported as **associational**, not causal.

## Compute Feasibility (CPU-First)

- **Hardware**: GitHub Actions `ubuntu-latest` (2 CPU cores, ~7 GB RAM).  
- **Memory**: Streaming loader keeps peak RAM < 500 MB even for the full raw file.  
- **Runtime**: Estimated total ≤ 2 CPU-hours; well under the 6-hour CI budget.  
- **GPU Escape Hatch**: Not required; no CUDA-only methods are used.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No verified NIST SRD 150 URL | Fatal – pipeline halts per FR-001 | Explicit check with clear error; future provision of a verified mirror will enable the run. |
| Spec not amended for solute rows | Training deferred | Kickback flag; no implementation against the current spec. |
| Dataset < 50 rows | Low statistical power | Switch to 80/20 split, report limitation, do not claim strong inference. |
| Single host metal | Stratification impossible | Fall back to random split; log warning. |
| Missing atomic radii/electronegativity | Row exclusion | Log to `errors/missing_atomic_data.csv`; continue with remaining rows. |
| R² < 0.1 for RF/GB | Possible null result | Save model, flag "Low Predictive Power" in report (valid outcome). |
| Missing baseline for a host | Fatal per FR-006 | Halt with precise error message; user must supply missing baseline data. |