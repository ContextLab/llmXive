# Research: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Objective
Develop a reproducible, CPU‑only machine‑learning pipeline that predicts the continuous **critical cooling rate (CCR)** of ternary alloy systems from three thermodynamic descriptors derived strictly from the Open Quantum Materials Database (OQMD). The study must quantify predictive performance, rank descriptor importance, and assess robustness to physically‑grounded CCR thresholds **[50, 100, 150] K/s**.

## Dataset Strategy
| Role | Source | Access Method | Variables Provided | Notes |
|------|--------|---------------|--------------------|-------|
| **Elemental properties** | OQMD (periodic‑table subset) | `datasets.load_dataset("materials-toolkits/oqmd", revision="v1.0.0", streaming=True)` | atomic radius, electronegativity, formation enthalpy per element | Verified URL in the Constitution “Verified Datasets” table. |
| **Experimental alloy CCR** | Open Glass‑Formability dataset (HuggingFace) | `datasets.load_dataset("materials-project/glass_formability")` | composition, CCR (continuous) | Open, programmatic download; must contain ≥ 500 valid ternary entries after filtering. No synthetic dataset is used; the pipeline aborts if insufficient data. |

## Feature Engineering (US‑1)
1. **Parse compositions** → extract constituent elements and stoichiometric fractions.  
2. **Thermodynamic descriptors** (per VI):  
   - *Mixing Enthalpy*: Σ_i x_i H_i – H_mix (standard alloy thermodynamics).  
   - *Atomic Size Mismatch*: √( Σ_i x_i (r_i – r̄)² ).  
   - *Electronegativity Variance*: √( Σ_i x_i (χ_i – χ̄)² ).  
3. **Validation**: tolerance ±0.01 against hand‑computed examples (US‑1‑4).  
4. **Filtering**: exclude rows with missing elemental data; log to `data/logs/exclusion_log.txt`.  
5. **Empty‑dataset guard**: raise `RuntimeError("Insufficient experimental CCR data (≥ 500 rows required).")` and write to `data/logs/empty_dataset_error.log` if the filtered set is too small.  

All descriptors are stored in `data/processed/processed_alloys.csv` and validated against `contracts/processed_alloys.schema.yaml`.

## Modeling (US‑2)
- **Train‑Test Split**: stratified 80/20 split (`random_state=42`, `test_size=0.2`) stratified by binned CCR to respect FR‑008 (no element family > 30 %).  
- **Model**: `RandomForestRegressor(n_estimators=500, random_state=42, n_jobs=2)`.  
- **Cross‑Validation**: 5‑fold CV on the training set; compute RMSE per fold, mean RMSE, and variance.  
- **Test Evaluation**: Predict on held‑out test set, compute RMSE.  
- **Associational Framing**: All claims are labeled as *associational* per FR‑006.

### Statistical Rigor
- **Power analysis**: Using the observed standard deviation of CCR (to be computed after ingestion) a detectable RMSE reduction of 30 K/s corresponds to an effect size d ≈ 0.5. With N = 500, α = 0.05, a two‑sided t‑test attains **[deferred]** power > 0.9, satisfying SC‑001. The exact variance will be reported after data loading.  
- **Null comparison**: Dummy regressor predicting the training‑set mean CCR; two‑sided paired t‑test (α = 0.05) required for SC‑002.  

## Evaluation Rigor
- **Permutation Importance**: `sklearn.inspection.permutation_importance` with `n_permutations=1000`, `random_state=42`. Empirical p‑value = proportion of permutations with higher importance. Top‑2 features must have p < 0.05 (SC‑004).  
- **Sensitivity Analysis**: Sweep CCR thresholds **[50, 100, 150] K/s**; for each compute **RMSE** (primary hypothesis). Apply **Bonferroni correction** across the three RMSE tests (α ≈ 0.0167). Optionally compute binary F1‑score (exploratory, no correction). Stability criterion: RMSE variance ≤ 0.01 K/s across thresholds (or ≤ 5 % for F1) (SC‑003).  

## Collinearity Check
- Compute Pearson correlation matrix of the three descriptors.  
- **Pre‑registered rule**: If any |r| > 0.8, drop the descriptor with lower a priori theoretical relevance (electronegativity variance) **before** any model fitting. Re‑run the model to verify stability (addresses CE39A1E8).  

## Risks & Contingencies
- **No open experimental CCR dataset**: Phase 0 aborts with a clear error; synthetic fallback is *not* used (addresses FR‑001).  
- **Large OQMD files**: Streamed loading keeps memory ≤ 2 GB.  
- **Training time**: `n_estimators` capped at 500, `n_jobs=2`; if runtime > 4 h, automatically reduce to 200 trees (fallback).  

## Timeline (aligned with Phase mapping)
| Week | Milestone |
|------|-----------|
| 1 | Contract dry‑run, download OQMD & experimental CCR dataset, ingestion, checksum generation (Phase 0‑1). |
| 2 | Train‑test split, Random Forest fit, CV, model serialization, checksum update (Phase 2). |
| 3 | Permutation importance, sensitivity sweep, schema validation for all contracts (Phase 3‑5). |
| 4 | Limitations discussion (FR‑007), quickstart authoring, final artifact archiving, hash finalisation (Phase 6). |

## Deliverables
- `data/processed/processed_alloys.csv` (schema‑validated).  
- `data/models/random_forest_model.pkl` and `data/models/cv_metrics.json`.  
- `data/reports/feature_importance.csv`, `data/reports/sensitivity_report.json`.  
- `quickstart.md`.  
- Contract validation logs confirming zero errors (SC‑006).  

## Limitations (FR‑007)
Only three thermodynamic descriptors are employed. Additional predictors (e.g., electronic structure, processing history) are omitted and may introduce bias; this limitation is explicitly discussed in the final report (Phase 6‑1).  
