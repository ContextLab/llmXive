# Research: Investigating Neural Signatures of Predictive Processing in Visual Illusions

## Overview
We test whether individual precision‑weighting parameters (λ) estimated from a hierarchical predictive‑coding model on a Müller‑Lyer illusion predict susceptibility (β) to a structurally distinct Ponzo illusion. The workflow proceeds through three stages: (1) data ingestion & validation, (2) model fitting, (3) susceptibility scoring, and (4) cross‑illusion prediction with rigorous resampling and diagnostics.

## Dataset Strategy
| Role | Dataset | Verified URL | Loader | Required Columns |
|------|---------|--------------|--------|------------------|
| Training (Müller‑Lyer) | OpenNeuro parquet shard (part of `clane9/openneuro-fslr64k`) | ` | `datasets.load_dataset(..., streaming=False)` | `subject_id`, `trial_id`, `stimulus_length`, `response_length`, `stimulus_parameters` |
| Test (Ponzo) | Ponzo illusion dataset (HuggingFace) | `https://huggingface.co/datasets/psychology/ponzo_illusion/resolve/main/data/ponzo.parquet` | same as above | `subject_id`, `trial_id`, `arrow_angle`, `depth_cue`, `perceived_length` |
| SusceptibilityScore | Computed internally (no external source) | – | – | – |

*If any required column is absent, the ingestion step aborts with an informative error (fulfilling FR‑001).*

## Methodology

### 1. Data Ingestion & Cleaning
1. **Download** the two parquet files via `datasets.load_dataset`.  
2. **Checksum verification**: SHA‑256 of each file is compared to the hash stored in `state/projects/PROJ-406‑investigating‑neural‑signatures‑of‑predi.yaml`.  
3. **Column validation**: The script asserts the presence of all required columns; missing columns cause a clean exit with error code 1.  
4. **Missing‑value handling**: Rows with `NaN` in any critical field (`response_length` or `perceived_length`) are dropped; a warning with the count is logged.  
5. **Export** cleaned CSVs: `data/clean/clean_muller_lyer.csv` and `data/clean/clean_ponzo.csv`.  

### 2. Hierarchical Predictive‑Coding Model (Training)
* **Model**: Bayesian observer with a single precision parameter λ per subject, shared log‑normal hyper‑prior.  
* **Likelihood**: Gaussian noise on the perceived length given stimulus length.  
* **Optimization**: `scipy.optimize.minimize` (L‑BFGS‑B) with bounds `[0.01, 10.0]`.  
* **Convergence criteria**: gradient norm < 1e‑6, log‑likelihood improvement > 1e‑4, no NaN/Inf.  
* **Outputs** (`precision_parameters.csv`): `subject_id`, `lambda`, `log_likelihood`, `aic`, `bic`.  

### 3. Ponzo Susceptibility Scoring (Test)
* **Generative model**: `perceived_length = true_length * (1 + β * cue_effect) + ε`.  
* **Estimation**: Ordinary Least Squares per subject (closed‑form).  
* **Outputs** (`ponzo_susceptibility.csv`): `subject_id`, `beta`, `r2`.  

### 4. Cross‑Illusion Prediction & Validation
1. **Power analysis** – Using `statsmodels.stats.power.NormalIndPower` with assumed effect size *r*≈0.30, α = 0.05, target power = 0.80. Required N is reported; if actual paired N < required, the pipeline aborts with a clear message and falls back to a Bayesian correlation estimate.  
2. **Confound regression** – Linear regression of λ and β on available demographics (age, gender) **and** trial count per subject and within‑subject response standard deviation. Residuals are retained for the primary correlation.  
3. **Linearity diagnostics** – (a) scatter plot of λ vs. β residuals, (b) Pearson *r* and two‑tailed p‑value, (c) Spearman ρ, (d) OLS residual analysis (Durbin‑Watson, visual inspection). If strong non‑linearity is detected, the Spearman result is reported alongside Pearson.  
4. **Merge** – Join `precision_parameters.csv` and `ponzo_susceptibility.csv` on `subject_id`; subjects missing from either side are excluded (log count).  
5. **Primary Pearson correlation** – Compute r, p‑value on residuals.  
6. **Bootstrap CI** – 1000 resamples of the matched subject pairs; derive 95 % CI for r.  
7. **Shuffled‑ID control** – Randomly permute subject IDs in the Ponzo table 1000 times; recompute r each time → null distribution centered at 0.  
8. **Null model validation** – Fit a Ponzo‑specific predictive‑coding model (independent λ′) and compare AIC/BIC against the domain‑general λ model; store `null_model_aic` and `null_model_bic` in the merged results.  
9. **Diagnostics** – Generate (a) scatter plot of λ vs. β residuals, (b) histogram of bootstrap r values, (c) residuals plot for the Ponzo model. Save as PNGs.  
10. **Output JSON** – `outputs/correlation_results.json` containing r, p_value, ci_lower, ci_upper, n_subjects, and a flag indicating whether the linearity check passed.

### Edge‑Case Handling
| Situation | Response |
|-----------|----------|
| Download error (e.g., 404) | Abort with clear message; suggest manual download to `data/raw/`. |
| Missing required columns | Abort; list missing columns. |
| Subject present only in one dataset | Exclude from merged analysis; log exclusion count. |
| Model non‑convergence for a subject | Record subject ID in `fit_diagnostics.csv`; exclude from correlation. |
| Bootstrap or permutation fails (e.g., insufficient subjects) | Log warning and skip that step, noting the limitation. |

## Compute Rationale
All heavy computation (MLE, OLS, bootstrap, permutations) uses NumPy/SciPy on CPU. Estimated runtime on a typical GitHub Actions runner is well within the allowed time limit. No GPU resources are needed.

## Expected Deliverables
- `data/clean/clean_muller_lyer.csv` & `data/clean/clean_ponzo.csv` (validated against schemas).  
- `data/derived/precision_parameters.csv` (λ estimates).  
- `data/derived/ponzo_susceptibility.csv` (β scores).  
- `data/merged/merged_results.csv` (joined table, includes null‑model AIC/BIC).  
- `outputs/correlation_results.json`.  
- Diagnostic PNGs (`scatter.png`, `bootstrap_hist.png`, `fit_residuals.png`).  
- SHA‑256 checksums for every artifact recorded in the project state file.  

---

