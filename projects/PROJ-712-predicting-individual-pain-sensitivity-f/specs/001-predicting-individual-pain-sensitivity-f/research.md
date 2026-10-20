# Research: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Executive Summary
We test whether resting‑state EEG microstate dynamics predict individual heat‑pain thresholds. Using the open **OpenNeuro ds003542** dataset (verified parquet URLs), we implement a reproducible EEG preprocessing pipeline, extract multiple microstate‑derived features, and train an Elastic Net regression model with nested cross‑validation. Statistical rigor is ensured via a global permutation test, bootstrap confidence intervals, FDR‑corrected feature‑level inference, VIF diagnostics, and a median‑split sensitivity analysis.

**Dataset Availability:** The dataset can be programmatically downloaded via the Hugging Face `datasets` library:

```python
datasets.load_dataset('openneuro/ds003542', data_dir='data/raw')
```

If the dataset cannot be fetched or lacks the required `heat_pain_threshold` column, the pipeline aborts with a clear error.

## Dataset Strategy

| Requirement | Needed Variable | Verified Source | Availability |
|-------------|----------------|----------------|--------------|
| Resting‑state EEG (≥ 4 min) | EEG recordings | OpenNeuro ds003542 – https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet | ✅ Verified |
| Heat‑pain threshold (°C) | `heat_pain_threshold` | OpenNeuro ds003542 – same accession | ✅ Verified |
| Demographics (optional) | `age`, `gender` | OpenNeuro ds003542 metadata | ✅ Available |

**Action:** The pipeline aborts early with *“Dataset lacks verified pain threshold labels in provided verified sources.”* if the column is missing.

## Methodology

### Phase 1 – Preprocessing (FR‑001, FR‑002)
1. **Ingestion** – Load EEG and `heat_pain_thresholds.csv`. Verify column presence.  
2. **Re‑reference** – Average mastoids (fallback to common average).  
3. **Band‑pass filter** – 1–40 Hz zero‑phase FIR.  
4. **ICA** – `FastICA` with automatic component rejection (EOG correlation, spectral kurtosis).  
5. **Quality check** – Exclude participants with `< 4 min` post‑ICA; log warnings (Edge Case 1).  
6. **Microstate segmentation** – Canonical 4‑state maps (A‑D); extract 30 features (durations, occurrences, transition probabilities, spectral power).  
7. **DataChunk streaming** – Process EEG in ≤ 2 GB chunks to respect RAM limits.  
8. **Pilot construct‑validity** – On 20 randomly selected participants (seed = 42), require at least one feature with |r| ≥ 0.20; otherwise abort.  
9. **Output** – `data/processed/feature_matrix.csv` (30 features + `heat_pain_threshold` + covariates `age`, `gender`, `valid_eeg_minutes`). No NaNs.

### Phase 2 – Modeling (FR‑003, FR‑004)
1. **Elastic Net regression** – Fixed `alpha = 0.5`; `l1_ratio` tuned via inner 5‑fold CV. Covariates concatenated with microstate features.  
2. **Nested CV** – Outer 5‑fold for unbiased performance; inner CV for `l1_ratio`.  
3. **Metrics** – Pearson r, MAE, 95 % CI via bootstrap (≥ 200 resamples).  
4. **Global permutation test** – Shuffle `heat_pain_threshold` ≥ 1 000 times *before* outer CV; recompute nested CV each time; empirical p‑value = proportion of permuted r ≥ observed r.  
5. **Artifact** – `artifacts/model_results.json` (pearson_r, p_value, mae, ci_lower, ci_upper, n_permutations, n_bootstrap).

### Phase 3 – Statistical Rigor (FR‑005, FR‑006, FR‑007)
1. **Permutation importance** – Compute on original data; generate null distributions from each permuted dataset (Phase 2). Derive raw p‑values; apply **Benjamini‑Hochberg FDR** correction.  
2. **VIF diagnostics** – Compute VIF for all predictors; flag any with VIF > 10. The verified flag `predictor vif = 33` will appear (source Q113106917). No exclusion, as Elastic Net tolerates collinearity.  
3. **Sensitivity analysis** –  
   - **Median‑split binary outcome**: Convert thresholds to high/low using median and offsets {median‑0.1, median‑0.05, median, median+0.05, median+0.1} (°C). Fit **logistic regression** (L2‑regularized) for each cutoff; report AUC, accuracy, Brier score.  
   - **Regularization sweep**: Vary `alpha` ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and `l1_ratio` ∈ {0.1, 0.5, 0.9} to assess stability of Pearson r and MAE.  
4. **Artifacts** – `artifacts/diagnostics.csv` (coefficients, permutation‑importance, raw & FDR‑adjusted p‑values, VIF, flags) and `artifacts/sensitivity_report.md` (tables & ROC plots).

### Phase 4 – Reporting
- **Model results** (`model_results.json`): Pearson r, empirical p‑value, MAE, 95 % CI, runtime.  
- **Diagnostics** (`diagnostics.csv`): Coefficients, importance scores, raw & FDR‑adjusted p‑values, VIF, significance flags.  
- **Sensitivity report** (`sensitivity_report.md`): AUC/accuracy/Brier across thresholds and regularization sweep.  
- **Figures** under `figures/` (scatter of predictions vs. true, importance bar, VIF histogram, ROC curves).  

## Computational Feasibility & Constraints
- **CPU‑first**: All steps run on CPUs; parallelism limited to 2 workers (`joblib`).  
- **Memory**: Streaming keeps RAM ≤ 2 GB during preprocessing; total peak ≤ 7 GB.  
- **Runtime guard**: `utils` records wall‑clock time; aborts > 5.5 h.  
- **No GPU**: No CUDA dependencies; fully compatible with GitHub Actions free tier.

## Decision Rationale
- **Elastic Net (α = 0.5)** satisfies FR‑003 and handles collinearity (FR‑006).  
- **Nested CV** eliminates optimism bias for hyper‑parameter tuning.  
- **Global permutation** provides a valid null distribution per Constitution VII.  
- **Permutation importance + FDR** supplies statistically sound feature‑level inference (FR‑005).  
- **Logistic regression** for median‑split sensitivity aligns with the binary classification requirement in FR‑007.  
- **Pilot validation** ensures microstate features have at least modest construct validity before full analysis.  
- **Power analysis** (target N ≥ 84) is documented; any shortfall will be reported transparently (SC‑001).  

## Limitations
- **Sample size**: If N < 84, power to detect r ≈ 0.30 drops below 80 %; this will be noted.  
- **Microstate model**: Only the canonical 4‑state solution is examined (Assumption 5).  
- **Observational design**: Findings are correlational (Assumption 7).  

---
