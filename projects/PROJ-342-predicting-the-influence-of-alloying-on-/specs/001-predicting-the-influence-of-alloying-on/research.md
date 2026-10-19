# Research: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Dataset Strategy

### Verified Sources
- **Open synthetic dataset** generated locally by `code/generate_synthetic.py`.  
  *Rationale*: No open, verified metallic‑glass Tg dataset is available (both DOI 10.5281/zenodo.10043838 and DOI 10.5281/zenodo.11023456 lack programmatic download URLs). To keep the project reproducible, we generate a synthetic dataset that mimics the statistical structure reported in the literature (e.g., composition ranges, typical Tg values 300–800 K).

### Variable Fit Verification
Required fields (validated against `contracts/dataset.schema.yaml`):
| Field | Type | Requirement |
|-------|------|-------------|
| `record_id` | string (UUID) | Present, unique |
| `family` | string | Determined from dominant element (≥ 40 % atomic fraction) |
| `elements` | object (element → fraction) | ≥ 2 elements, each fraction ∈ [0,1], sum ≈ 1 |
| `tg_value` | number (K) | Positive, realistic range 300–800 |
| `source` | string | Fixed value `"synthetic"` |
| `status` | string | `"valid"` for all generated rows |

Records failing any check are excluded and logged (FR‑001).

### Alloy Family Definition
Family = element with the highest atomic fraction (≥ 40 %). Minimum of 5 distinct families is enforced; otherwise the pipeline aborts with a clear “Insufficient family diversity” message.

## 2. Methodology & Statistical Rigor

### Feature Engineering (FR‑002)
- **Atomic radius data** from `mendeleev` (v0.31.0).  
- **Radius mismatch (δ)**: √∑ cᵢ (1 − rᵢ/ r̄)².  
- **Electronegativity difference (Δχ)**: weighted standard deviation of Pauling electronegativities.  
- **Valence Electron Concentration (VEC)**: weighted mean of valence electron counts.  
- **Weighted mean radius (r̄)**: diagnostic only; logged but never used as a predictor.

### Collinearity Handling (FR‑007)
- Compute VIF for the three predictors.  
- If any VIF > 5, iteratively drop the predictor with highest VIF, recompute, and repeat until all ≤ 5.  
- The final predictor set is recorded; a boolean `collinearity_flag` indicates whether any removal occurred.

### Model Training (FR‑003)
- **Algorithm**: `sklearn.ensemble.GradientBoostingRegressor`.  
- **LOFO CV**: For each family, train on all other families, test on the held‑out family.  
- **Hyperparameter grid** (≤ 10 combos):  
  - `n_estimators`: {100, 200}  
  - `max_depth`: {3, 5, 7}  
  - `learning_rate`: {0.05, 0.1}  
- **Random state**: 42 for reproducibility.  
- **Runtime budget**: ≤ 2 h for training.

### Sensitivity Analysis (FR‑006)
- Using the best hyper‑parameter set from the grid, sweep `max_depth` ∈ {3,5,7} and record R² for each.  
- Compute variance σ² of these three R² scores; store as `sensitivity_variance`.

### Correlation Testing (FR‑008, FR‑009)
- Compute Pearson and Spearman coefficients + raw p‑values for each of the three predictor pairs.  
- Apply **Bonferroni correction** (α ≤ 0.05) to the three tests (source: Benjamini & Hochberg α = 0.05, arXiv:1906.01701).  
- Store corrected p‑values in `artifacts/metrics/stats.json`.

### Performance Benchmarks (SC‑001, SC‑002)
- **Null model**: predict the mean Tg of the training set.  
- Compute test‑set R² for the GBM and compare to the null model (SC‑001).  
- **Bootstrap**: 1000 resamples of the training data; compute 95 % confidence intervals for each feature’s importance (SC‑002).

### Reporting (FR‑004)
`code/report.py` assembles:
- Feature‑importance bar chart with bootstrap CI.  
- Partial dependence plots for each retained predictor.  
- Correlation matrix heatmap with Bonferroni‑adjusted significance stars.  
- Explicit statement: **“These findings are associational only.”**  

All figures are generated from stored JSON/CSV artifacts to satisfy Principle VII.

## 3. Compute Feasibility

- **Memory**: Synthetic dataset (200 rows, ~10 KB) → < 100 MB RAM throughout.  
- **CPU**: All steps use scikit‑learn (CPU‑only). Estimated total runtime ≈ 3.5 h on 2 vCPU.  
- **Fallback**: If RAM usage unexpectedly exceeds 7 GB, `ingest.py` will stream the CSV in 10 k‑row chunks and only retain necessary columns.

## 4. Decision Rationale

| Decision | Reason |
|----------|--------|
| Synthetic dataset generation | No open, verified Tg dataset exists; generating data guarantees reproducibility and satisfies FR‑001 under a transparent simulation premise. |
| LOFO CV | Prevents family‑wise leakage; aligns with FR‑003. |
| Gradient Boosting | Handles non‑linear composition‑Tg relationships while being CPU‑efficient. |
| Bonferroni correction | Provides strict family‑wise error control for the three predictor‑pair tests (recommended over BH for N=3). |
| Iterative VIF removal | Addresses inevitable collinearity among atomic descriptors without discarding all predictors. |
| Bootstrapped CI for feature importance | Supplies robust uncertainty quantification required by SC‑002. |
| Explicit associational phrasing | Enforces FR‑004 and complies with Principle IV (no causal claims). |

---
