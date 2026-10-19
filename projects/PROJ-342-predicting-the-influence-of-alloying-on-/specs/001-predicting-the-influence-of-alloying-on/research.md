# Research: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## 1. Dataset Strategy

### Verified Sources
- **Primary**: Metallic Glass Database, DOI 10.5281/zenodo.10043838 (Pauly et al.).  
  *Status*: No verified download URL; the pipeline will attempt programmatic retrieval via the `zenodo` Python client. If the DOI is unreachable or the file lacks required columns (`tg_value`, elemental composition), the run aborts with a clear error message. No synthetic fallback is permitted.

### Variable Fit Verification
Required columns:
- `record_id` (string)
- `family` (string)
- `elements` (dict of element → fraction, ≥ 2 entries)
- `tg_value` (numeric, Kelvin)
- `source` (DOI string)

`ingest.py` validates presence and type of each column against `contracts/dataset.schema.yaml`. Records missing any required field are dropped (FR‑001).

### Alloy Family Definition
Family = element with highest atomic fraction **≥ 40 %**. Must have ≥ 5 distinct families for LOFO to be statistically meaningful; otherwise the pipeline halts and reports “Statistical Power Insufficiency”.

## 2. Methodology & Statistical Rigor

### Feature Engineering
- **Radius Mismatch (δ)**: √∑ cᵢ (1 − rᵢ/ r̄)²  
- **Electronegativity Difference (Δχ)**: Standard deviation of Pauling electronegativities weighted by composition.  
- **Valence Electron Concentration (VEC)**: Weighted mean of valence electron counts.  
- **Weighted Mean Radius (r̄)**: Computed for diagnostics only; never used as a predictor (FR‑002).

### Collinearity Handling (FR‑007)
- Compute VIF for the three predictors.  
- If any VIF > 5, iteratively drop the predictor with the highest VIF and recompute until all ≤ 5.  
- Log which predictors were removed; the final model trains on the remaining set.

### Model Training (FR‑003)
- Algorithm: `sklearn.ensemble.GradientBoostingRegressor`.  
- LOFO CV: For each family, train on all other families, test on the held‑out family.  
- Grid search ≤ 10 combos (e.g., `n_estimators` ∈ {100,200}, `max_depth` ∈ {3,5,7}, `learning_rate` ∈ {0.05,0.1}).  
- Runtime budget < 2 h.

### Sensitivity Analysis (FR‑006)
- Sweep `max_depth` ∈ {3,5,7} on the best hyperparameter set.  
- Record R² for each depth; compute variance σ² and report.

### Correlation Testing (FR‑008, FR‑009)
- Compute Pearson & Spearman coefficients + raw p‑values for each of the three predictor pairs.  
- Apply **Bonferroni correction** (α ≤ 0.05) to control family‑wise error (preferred over FDR for N=3).  
- Store corrected p‑values in `artifacts/metrics/stats.json`.

### Performance Benchmarks (SC‑001, SC‑002)
- Compare mean test‑set R² to a null model that always predicts the training‑set mean Tg.  
- Bootstrap 1000 resamples of the training data; compute 95 % confidence intervals for each feature’s importance (SC‑002).

### Reporting (FR‑004)
- `report.py` assembles:
  - Feature‑importance bar chart with bootstrap CI.  
  - Partial dependence plots for each retained predictor.  
  - Correlation matrix heatmap with Bonferroni‑adjusted significance stars.  
  - Explicit statement: **“These findings are associational only.”**  

## 3. Compute Feasibility

- **Memory**: Data ≤ 200 k rows; processed in pandas with < 5 GB RAM.  
- **CPU**: All steps use scikit‑learn (CPU‑only). Estimated total runtime ≈ 4 h on 2 vCPU.  
- **Fallback**: If memory exceeds 7 GB, `ingest.py` will stream the CSV in chunks and retain only necessary columns.

## 4. Decision Rationale

| Decision | Reason |
|----------|--------|
| LOFO CV | Prevents leakage of family‑specific trends; aligns with FR‑003. |
| Gradient Boosting | Captures non‑linear composition‑Tg relationships; efficient on CPU. |
| Bonferroni | Guarantees family‑wise error control for the three hypothesis tests. |
| Iterative VIF removal | Addresses expected collinearity while preserving as many descriptors as possible. |
| No synthetic data | Real Tg values are essential for meaningful predictive modeling; synthetic data would invalidate FR‑001. |
