# Research: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

## 1. Problem Statement & Research Questions
**Primary Question**: Does incorporating DFT‑derived elastic constants (shear & bulk modulus) improve the prediction of experimental yield strength for BCC Fe‑alloys relative to a composition‑only model?

- **Null Hypothesis (H₀)**: MAE of the DFT‑enhanced Random Forest is **not** lower than that of the composition‑only baseline.  
- **Alternative Hypothesis (H₁)**: MAE of the DFT‑enhanced model is **significantly lower**.

## 2. Dataset Strategy
| Data Type | Source | Verified Loader / URL | Notes |
|-----------|--------|-----------------------|-------|
| **Experimental composition & yield strength** | MatNavi “Steel Yield Strength” dataset (open) | `datasets.load_dataset('matnavi/steel_yield_strength')` | Contains `formula` and `yield_strength_MPa`. The pipeline aborts with `ERR_INSUFFICIENT_DATA` if the column is missing or < 20 rows survive merging. |
| **DFT elastic constants** | Materials Project API (via `mp-api`) | Programmatic API call (`mp_api.client.MaterialsProjectClient`) | Queries for `bulk_modulus` and `shear_modulus` and filters `spacegroup.number == 229`. All queries are logged to `data/provenance/dft_queries.jsonl`. |
| **Fallback** | **None** – synthetic data is prohibited. | – | If after merging the row count < 20, the system halts as required by FR‑001/FR‑002. |

### Integration Plan
1. **Fetch experimental file** → `data/raw/experimental.csv`.  
2. **Iterate formulas**, query Materials Project → `data/raw/dft_{formula}.json`.  
3. **Merge** on `formula`; keep only rows where `yield_strength_MPa`, `shear_modulus_GPa`, and `bulk_modulus_GPa` are present.  
4. **Validate** the merged CSV against `contracts/dataset.schema.yaml`. Abort with `ERR_INSUFFICIENT_DATA` if validation fails or if `len(merged) < 20`.  

## 3. Methodology
### 3.1 Feature Engineering
- **Composition features**: one‑hot encoding of each element present, plus fractional composition (derived from the formula).  
- **DFT features**: `shear_modulus_GPa`, `bulk_modulus_GPa` (standardized).  
- **Optional experimental covariates**: testing temperature, strain rate, and heat‑treatment metadata are added if present; otherwise they are logged as missing and noted as a limitation.  
- **Collinearity mitigation**: compute Variance Inflation Factors (VIF); if any VIF > 5, iteratively drop the highest‑VIF predictor and record the dropped list. As a sensitivity check, train a Ridge‑regularized model on the full feature set.  

### 3.2 Modeling
- **Algorithm**: `sklearn.ensemble.RandomForestRegressor`.  
- **Validation**: **5‑fold outer × 5‑fold inner** nested cross‑validation to avoid leakage.  
- **Baseline**: same RF hyper‑parameter search but trained on composition features (and optional covariates) only.  

### 3.3 Statistical Testing
- **Metric per outer fold**: MAE and R².  
- **Paired test**: **paired t‑test** on the 5 outer‑fold MAE differences (parametric, as required by FR‑005).  
- **Effect size & CI**: report t‑statistic, p‑value, 95 % confidence interval for the mean MAE difference, and rank‑biserial correlation as an effect‑size analogue.  
- **Power analysis**: using `statsmodels.stats.power.TTestPower` with observed effect size, α = 0.05, and effective sample size (≈ 20‑30). If `power < 0.8`, the output includes a warning field.  

### 3.4 Construct Validity of DFT Features
Literature (e.g., Petch & Nabarro, early work; Liu et al., 2020) demonstrates a strong empirical correlation between shear modulus and yield strength for BCC metals., providing a mechanistic basis for using ideal‑state DFT elastic constants as predictors. Nonetheless, we acknowledge that real alloys contain defects, grain‑size effects, and processing histories not captured by ideal DFT calculations; this limitation is explicitly reported in the final results.

### 3.5 Interpretability & Sensitivity Analysis
- **TreeSHAP**: global mean absolute SHAP values for all features.  
- **Permutation importance**: 10 repeats; compute mean ± std for each feature.  
- **Bootstrap stability**: 10 bootstrap resamples of the full dataset; recompute permutation importance; report standard deviation per feature.  
- **Stability threshold**: `std_dev < 0.05` for `shear_modulus_GPa` and `bulk_modulus_GPa` → `is_stable = true`.  

## 4. Compute Feasibility
- **Hardware**: 2 CPU cores, ≈7 GB RAM, ≤6 h runtime (GitHub Actions free tier).  
- **Memory**: Full merged dataset expected ≤ 200 KB (≈20–50 rows), trivial for Random Forest.  
- **Runtime Estimate**:  
  - Data download & merge: < 2 min.  
 - Nested CV (5 × 5 = 25 fits) + hyper‑parameter grid: [deferred].
 - SHAP (TreeExplainer on ≤ 50 samples): [deferred].
  - Bootstrap (several × permutation): ≈ brief runtime.  
  - Total < 1 h, well within limits.  

## 5. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **No yield‑strength column** in the MatNavi dataset. | Early validation step; abort with `ERR_INSUFFICIENT_DATA`. |
| **Materials Project rate‑limit** | Exponential backoff + skip after 3 attempts; still log each skip. |
| **Low statistical power** (n ≈ 20) | Compute and report power; if `<0.8`, explicitly state limitation (SC‑008). |
| **Multicollinearity** between one‑hot composition and DFT descriptors. | VIF analysis with iterative dropping and Ridge fallback (methodology‑ef15bb22). |
| **Construct validity of DFT features** | Provide literature justification and note limitation (methodology‑114e8ca3). |
| **Unrecorded experimental confounds** | Include optional covariates when available; otherwise log as limitation (methodology‑23fd71ba). |
| **Small sample size** | Add leave‑one‑out CV as an extra robustness check (methodology‑9b5d0439). |

---

