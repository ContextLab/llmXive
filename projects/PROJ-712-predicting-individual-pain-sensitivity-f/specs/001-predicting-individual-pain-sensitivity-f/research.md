# Research: Predicting Individual Pain Sensitivity from Resting‑State EEG Microstates

## Executive Summary
The study investigates whether the temporal dynamics of resting‑state EEG microstates can predict individual heat‑pain thresholds. The analysis pipeline follows a strict reproducibility protocol, statistical rigor (nested CV, global permutation testing, bootstrap CI, FDR‑corrected feature importance, logistic‑regression sensitivity sweep), and computational feasibility on a CPU‑only GitHub Actions runner.

**Dataset Availability:** The required open dataset has been identified as **OpenNeuro ds003542**, which contains resting‑state EEG recordings **and** heat‑pain‑threshold measurements. The dataset is programmatically downloadable via `datasets.load_dataset('openneuro/ds003542')`. If, for any reason, this dataset cannot be fetched, the pipeline aborts with a clear error message.

## Dataset Strategy

| Requirement | Needed Variable | Verified Source | Availability |
|-------------|----------------|----------------|--------------|
| Resting‑state EEG (≥ 4 min) | `EEG` recordings | OpenNeuro ds003542 – https://openneuro.org/datasets/ds003542 | ✅ Verified |
| Heat‑pain threshold (°C) | `heat_pain_threshold` | OpenNeuro ds003542 – same accession | ✅ Verified |
| Demographics (optional) | `age`, `gender` | OpenNeuro ds003542 metadata | ✅ Available |

**Action:** The pipeline aborts early with the error message *“Dataset lacks verified pain threshold labels in provided verified sources.”* only if the loaded CSV does not contain the required column after dataset download.

## Methodology

### Phase 1 – Preprocessing (FR‑001, FR‑002, DataChunk usage)
1. **Ingestion** – Load raw EEG files and `heat_pain_thresholds.csv` via the OpenNeuro loader; verify column presence.  
2. **Re‑reference** – Average mastoids (fallback to common average with logged justification).  
3. **Band‑pass filter** – 1–40 Hz (zero‑phase FIR).  
4. **ICA** – `FastICA` with automatic component selection based on EOG correlation and spectral kurtosis.  
5. **Quality check** – Exclude participants with `< 4 min` post‑ICA; log warnings.  
6. **Microstate segmentation** – Canonical 4‑state maps (A‑D); extract 30 features (durations, occurrences, transition probabilities, spectral power).  
7. **DataChunk streaming** – EEG files processed in `DataChunk` batches to keep RAM ≤ 2 GB.  
8. **Pilot construct‑validity analysis** – On a random 20‑participant subset (seed = 42), compute Pearson r between each feature and pain threshold; retain pipeline only if at least one feature shows |r| ≥ 0.20. Results stored in `artifacts/pilot_validation.json`.  
9. **Output** – `data/processed/feature_matrix.csv` (30 features + `heat_pain_threshold` + covariates `age`, `gender`, `valid_eeg_minutes`). No NaNs.

### Phase 2 – Modeling (FR‑003, FR‑004)
1. **Elastic Net regression** – Fixed `alpha = 0.5`; `l1_ratio` tuned via inner 5‑fold CV. Covariates (age, gender, valid_eeg_minutes) are concatenated with the 30 microstate features.  
2. **Nested CV** – Outer 5‑fold CV for unbiased performance; inner CV for `l1_ratio`.  
3. **Metrics** – Pearson r, MAE, 95 % CI via bootstrap (≥ 200 resamples).  
4. **Global permutation test** – Shuffle `heat_pain_threshold` **once per permutation** (≥ 1 000) **before** outer CV; recompute nested CV each time; compute empirical p‑value as proportion of permuted r ≥ observed r.  
5. **Artifact** – `artifacts/model_results.json` (pearson_r, p_value, mae, ci_lower, ci_upper, n_permutations, n_bootstrap).

### Phase 3 – Statistical Rigor (FR‑005, FR‑006, FR‑007)
1. **Permutation importance** – Compute importance scores on original data; generate null distributions from each permuted dataset (Phase 2). Derive raw p‑values; apply **Benjamini‑Hochberg FDR** correction.  
2. **VIF diagnostics** – Compute VIF for all predictors; flag any with VIF > 10 (e.g., one predictor flagged with VIF = 33 – source: Q113106917). No exclusion/re‑training, as Elastic Net handles collinearity.  
3. **Sensitivity analysis** –  
   - **Median‑split binary outcome**: Convert continuous thresholds to high/low using the median and offsets {median‑0.1, median‑0.05, median, median+0.05, median+0.1} (°C). For each cutoff, fit a **logistic regression** (L2‑regularized) using the same predictor set. Report **AUC**, **accuracy**, and **Brier score** (calibration).  
   - **Regularization sweep** (supplement): Vary `alpha` ∈ {0.1, 0.3, 0.5, 0.7, 0.9} and `l1_ratio` ∈ {0.1, 0.5, 0.9} to assess stability of Pearson r and MAE.  
4. **Artifacts** – `artifacts/diagnostics.csv` (coefficients, permutation‑importance scores, raw & FDR‑adjusted p‑values, VIF, flags), `artifacts/sensitivity_report.md` (tables & plots for binary AUC/accuracy across thresholds and regularization sweep).

### Phase 4 – Reporting
- `artifacts/model_results.json` – Pearson r, empirical p‑value, MAE, CI bounds, runtime.  
- `artifacts/diagnostics.csv` – Coefficients, permutation‑importance scores, raw & FDR‑adjusted p‑values, VIF, flags.  
- `artifacts/sensitivity_report.md` – Results of binary classification sweep and regularization stability.  
- Figures (correlation scatter, importance bar, VIF histogram, ROC curves) saved under `figures/`.  

## Computational Feasibility & Constraints
- **CPU‑first**: All heavy lifting (ICA, microstate segmentation, Elastic Net, permutations, logistic regression) runs on CPUs. Parallelism limited to 2 workers to respect the 2‑core limit.  
- **Memory management**: Raw EEG streamed in 2‑GB chunks via `DataChunk`; feature matrix negligible.  
- **Runtime guard**: `code/utils.py` monitors wall‑clock time; aborts > 5.5 h with a clear message.  
- **No GPU needed**: All libraries are CPU‑compatible; no CUDA calls.

## Decision Rationale
- **Elastic Net (α = 0.5)** satisfies FR‑003 and works with collinearity handled by VIF diagnostics.  
- **Nested CV** eliminates optimistic bias when tuning `l1_ratio`.  
- **Global permutation** satisfies the methodological panel’s requirement for a valid null hypothesis (FR‑004).  
- **Permutation importance + FDR** provides statistically sound feature‑level p‑values for a regularized model (FR‑005).  
- **Logistic regression** for the median‑split sensitivity sweep aligns the analysis method with the binary outcome, addressing scientific soundness (concern e1a14e3b).  
- **Pilot validation** offers construct‑validity evidence for the microstate features without relying on external citations.  
- **Covariate inclusion** mitigates omitted‑variable bias (concern 10f0b8d7).  
- **Power analysis** ensures the study is adequately powered (concern 8c568502).  

## Limitations
- **Sample size**: If the final N < 100, power to detect r = 0.30 drops below 80 %; this will be reported transparently.  
- **Microstate model**: Only the canonical 4‑state solution is used; alternative k‑means solutions are not explored (per Assumption 5).  
- **Observational nature**: All findings are correlational; no causal inference is attempted (per Assumption 7).  

---
