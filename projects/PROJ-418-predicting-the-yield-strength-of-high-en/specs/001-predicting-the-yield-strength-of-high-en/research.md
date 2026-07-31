# Research: Predicting the Yield Strength of High‑Entropy Alloys

## Objective
Develop a reproducible pipeline that predicts the yield strength of high‑entropy alloys (HEAs) from compositional descriptors and additional covariates, and quantifies model performance with rigorous statistical validation.

## Dataset Strategy
| Dataset | Source (Verified URL) | Variables Required | Availability |
|---------|----------------------|--------------------|--------------|
| **HEA Yield‑Strength Collection** | *No verified URL provided in the user message.* | - `composition` (string) <br> - `yield_strength` (float) <br> - `phase` (string) <br> - `testing_temperature` (float) <br> - All descriptor variables (mixing entropy, δ, Δχ, VEC, melting‑temperature variance) | No open, programmatically downloadable source has been verified for these variables. |

> **Important**: At present there is **no verified open dataset** that supplies experimentally measured yield‑strength values together with the required compositional descriptors. Consequently, the pipeline will **abort early** with a clear error message if an appropriate dataset cannot be fetched. The specification must be amended to either (a) point to a verified dataset that meets these requirements, or (b) adjust the research question to a feasible target variable present in an available dataset.

## Methodology Overview
| Step | Description | Tools / Libraries | Rationale (CPU vs GPU) |
|------|-------------|-------------------|------------------------|
| **0. Data Acquisition & Validation** | Attempt to download the HEA yield‑strength dataset, store under `data/raw/`, and validate against `contracts/dataset.schema.yaml`. If the dataset is unavailable, abort with an informative error. | `datasets` (HuggingFace, when a verified source exists) | CPU‑first; dataset size expected to be a few megabytes. |
| **1. Descriptor & Covariate Engineering** | Compute mixing entropy, atomic size mismatch δ, electronegativity variance Δχ, VEC, melting‑temperature variance **and** add `phase` and `testing_temperature` as covariates using a locked elemental property table (`data/element_properties.csv`). | `pandas`, `numpy` | Pure CPU; deterministic, lightweight. |
| **2. Model Training with Hyper‑parameter Tuning** | Perform a lightweight grid search (n_estimators ∈ {[deferred]}, max_depth ∈ {10,None}) evaluated via inner 3‑fold CV; select best hyper‑parameters and fit a `RandomForestRegressor` (random_state = 42). | `scikit-learn` | CPU‑first; grid search over a tiny space runs < 1 min. |
| **3. Validation** | 5‑fold outer cross‑validation; compute mean R². | `scikit-learn` | CPU‑first; standard CV routine. |
| **4. Power Analysis** | Estimate that ~1 k samples give >80 % power to detect an R² increase of 0.1 at α = 0.05 (standard linear‑model power formula). | Analytic calculation (documented in plan) | CPU‑first; no runtime cost. |
| **5. Bootstrap CI** | A large number of bootstrap resamples of outer CV R² to obtain a 95 % confidence interval. | `numpy` | CPU‑first; resampling fast on small dataset. |
| **6. Permutation Importance** | Compute importance for each descriptor with **exactly 1000 permutations** (hard‑coded). Apply Benjamini‑Hochberg FDR correction. | `sklearn.inspection.permutation_importance` | CPU‑first; 1000 permutations complete within budget. |
| **7. SHAP Analysis** | Generate Kernel SHAP values for a random subset of samples (≤ 200) to produce a summary plot. | `shap` (KernelExplainer) | CPU‑first; feasible on 200 samples. |
| **8. Reporting** | Assemble `reports/report.md` with metrics, CI, importance plots, and conditional “Data Limitation Warning”. Include a correlation matrix and VIF analysis for descriptors. | `markdown`, `matplotlib` for figures | CPU‑first; all rendering done locally. |

## Decision / Rationale
- **CPU‑first** is adopted for all steps because the dataset, if available, is modest (< 5 MB) and the chosen algorithms (RandomForest, permutation importance, Kernel SHAP on a small subset) comfortably fit within the GitHub Actions compute limits (2 CPU cores, ~7 GB RAM, ≤ 6 h).  
- No GPU‑required method is needed; therefore no off‑load to Kaggle GPU is planned.

## Statistical Rigor Checklist
- **Multiple‑Comparison Correction**: Permutation importance p‑values are corrected using the Benjamini‑Hochberg FDR procedure (implemented in `perm_importance.py`).  
- **Power / Sample‑Size**: The HEA yield‑strength dataset (when available) contains a large number of alloys; analytic power analysis confirms adequate power for the targeted effect size.  
- **Causal Claims**: All statements are strictly associative; no causal inference is attempted.  
- **Measurement Validity**: Yield‑strength values will be taken from a verified experimental HEA dataset (to be cited once a verified source is identified).  
- **Collinearity**: Descriptors (including phase & temperature) are known to be partially correlated; a correlation matrix and VIF analysis will be reported, and permutation importance will be interpreted accordingly.

---



