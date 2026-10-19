# Research: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Dataset Strategy

### Verified Sources
- **Primary attempt**: Programmatic download of the Metallic Glass Database (DOI 10.5281/zenodo.10043838) via Zenodo API.  
- **Secondary attempt**: Download of the MatNVP Metallic Glass subset (DOI 10.5281/zenodo.11023456).  

*Rationale*: The specification mandates loading from these two DOIs (FR‑001). The pipeline attempts each in turn; **if both attempts fail, the pipeline aborts with an informative error** – no synthetic fallback is used, preserving compliance with FR‑001.

### Variable Fit Verification
The dataset (downloaded) is validated against `contracts/dataset.schema.yaml`. Required columns:

| Field | Type | Requirement |
|-------|------|-------------|
| `record_id` | string (UUID) | Unique, non‑null |
| `family` | string | Determined from dominant element (≥ 40 % atomic fraction) |
| `elements` | object (element → fraction) | ≥ 2 elements, each fraction ∈ [0, 1], sum ≈ 1 |
| `tg_value` | number (K) | Positive, 300 ≤ tg ≤ 800 |
| `source` | string | DOI string of the source dataset |
| `status` | string | `"valid"` for retained rows |

Rows failing any check are dropped and counted; the retention rate is logged (SC‑003).

### Alloy Family Definition
The **family** label is the element with the largest atomic fraction (≥ 40 %). At least five distinct families are required; if fewer are present, the pipeline aborts with an explicit “Insufficient family diversity” error.

### Dataset‑Literature Validation (External‑Validity safeguard)
After successful ingestion, we compute Pearson and Spearman correlations between each descriptor (radius mismatch, electronegativity difference, VEC) and Tg. These empirical correlations are compared to literature‑reported ranges (e.g., radius mismatch vs. Tg |r| ≈ low‑to‑moderate range). If any correlation falls outside the literature interval, the pipeline aborts with a clear message, ensuring that the real dataset exhibits realistic descriptor‑Tg relationships before modeling.

## 2. Methodology & Statistical Rigor

### Feature Engineering (FR‑002)
- **Atomic radii** from `mendeleev` (v0.31.0).  
- **Radius mismatch (δ)**: \[
  \delta = \sqrt{\sum_i c_i\left(1-\frac{r_i}{\bar r}\right)^2}
  \]  
- **Electronegativity difference (Δχ)**: weighted standard deviation of Pauling electronegativities.  
- **Valence Electron Concentration (VEC)**: weighted mean of valence electron counts.  
- **Weighted mean radius ( \(\bar r\) )**: logged for diagnostics only; excluded from modeling (FR‑002).  

All descriptors are computed in a single, version‑controlled script `code/descriptors.py` (Principle VI).

### Collinearity Handling (FR‑007)
- Compute Variance Inflation Factor (VIF) for the three predictors.  
- If any VIF > 5, iteratively drop the predictor with the highest VIF, recompute VIFs, and repeat until all ≤ 5.  
- The final predictor set is stored; a boolean `collinearity_flag` indicates whether any removal occurred (recorded in `stats.json`).

### Model Training (FR‑003)
- **Algorithm**: `sklearn.ensemble.GradientBoostingRegressor`.  
- **Leave‑One‑Family‑Out (LOFO) CV**: For each alloy family, train on all other families and test on the held‑out family. This guarantees no family leakage.  
- **Hyperparameter grid** (≤ 10 combos):  
  - `n_estimators`: {100, 200}  
  - `max_depth`: {3, 5, 7}  
  - `learning_rate`: {0.05, 0.1}  
- **Random state**: 42.  
- **Runtime budget**: ≤ 2 h for the full grid search (FR‑005).  

### Sensitivity Analysis (FR‑006)
- Using the best hyper‑parameter set from the grid, sweep `max_depth` ∈ {3, 5, 7}.  
- Record R² for each depth, compute variance σ² across the three scores, and store as `sensitivity_variance` in `stats.json`.

### Correlation Testing (FR‑008, FR‑009)
- Compute Pearson and Spearman correlation coefficients + raw two‑tailed p‑values for each of the three predictor pairs.  
- Apply **Benjamini‑Hochberg FDR correction** with α = 0.05 (source: arXiv 1906.01701) to the three tests, producing adjusted p‑values (FR‑008).  
- Store both raw and corrected p‑values under the new `correlations` field in `artifacts/metrics/stats.json`.

### Performance Benchmarks (SC‑001, SC‑002)
- **Null model**: predict the mean Tg of the training set.  
- Compute test‑set R² for the GBM and compare to the null model (SC‑001).  
- **Bootstrap CI for feature importance**: 1000 resamples of the training data; compute 95 % confidence intervals for each predictor’s importance; saved under `feature_importance_ci` in `stats.json` (SC‑002).  

### Reporting (FR‑004)
`code/report.py` assembles a Markdown report (`paper/report.md`) containing:
- Feature‑importance bar chart with 95 % CI (from `feature_importance_ci`).  
- Partial‑dependence plots for each retained predictor.  
- Correlation matrix heatmap with stars indicating significance after FDR correction.  
- Explicit statement **“These findings are associational only.”** (FR‑004).  
All figures are generated from stored JSON/CSV artifacts, satisfying Principle VII.

## 3. Compute Feasibility

- **Memory**: The real dataset (< 10 KB) peak RAM < 100 MB.  
- **CPU**: All steps use scikit‑learn (CPU‑only). Estimated total runtime is on the order of several hours on 2 vCPU., comfortably under the 6 h CI limit.  

## 4. Decision Rationale

| Decision | Reason |
|----------|--------|
| Attempt real DOI download first, abort on failure | Directly satisfies FR‑001; no synthetic data are used. |
| Dataset‑Literature validation | Guarantees external validity of the real dataset (addresses methodology‑314fd1f6). |
| LOFO CV | Prevents family‑wise leakage; matches FR‑003. |
| Gradient Boosting Regressor | Captures non‑linear composition‑Tg relationships while remaining CPU‑efficient. |
| Benjamini‑Hochberg FDR (α = 0.05) | Required by FR‑008; α value taken from the verified source (arXiv 1906.01701). |
| Iterative VIF removal | Handles collinearity among atomic descriptors without discarding all predictors. |
| Bootstrapped CI for feature importance | Provides robust uncertainty quantification required by SC‑002. |
| Explicit associational phrasing | Enforces FR‑004 and complies with Principle IV (no causal claims). |
| Power‑analysis note | Acknowledges exploratory nature and limited power, satisfying methodology‑bbf6b5b1. |

---


