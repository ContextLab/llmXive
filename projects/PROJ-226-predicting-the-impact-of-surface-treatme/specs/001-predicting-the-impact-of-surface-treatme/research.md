# Research: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

## Overview
This research plan outlines how to answer the core question: *How do surface‑treatment parameters influence polymer adhesion strength?* The approach combines a reproducible ingestion pipeline, supervised regression modeling, a **nested permutation test** to guard against selection bias, and SHAP interpretability.

## Dataset Strategy
| Source | Variable Coverage* | Access Method | Verified URL |
|--------|-------------------|---------------|--------------|
| **Open adhesion dataset (to be identified)** | Must contain all required predictor variables plus the target `adhesion_strength_mj_m2`. | `datasets.load_dataset("<repo>/<name>", split="train")` or `wget`/`curl` for CSV | **None currently verified** – the pipeline will abort with an informative error if no suitable dataset is supplied (see Data Availability & Mitigation in `plan.md`). |
| **Synthetic generator (proof‑of‑concept only)** | Generates all required variables with realistic ranges based on literature values. | Custom Python generator (`synthetic_data.generate(...)`). | N/A (synthetic) |

\*Coverage is assessed after initial download; variables present in < 80 % of rows trigger median‑imputation per substrate class (FR‑002). Records missing the target are excluded.

### Decision & Rationale
- **Primary choice:** Locate an open dataset that satisfies the full variable list. This respects the non‑fabrication rule and aligns with FR‑001–FR‑009.  
- **Secondary fallback:** Synthetic data may be used **only** for internal testing of the pipeline; it **cannot** be used to satisfy SC‑001 (R² ≥ 0.5) or SC‑002 (p < 0.05). Any results derived from synthetic data will be labeled as illustrative and excluded from scientific claims.  
- **If no suitable real dataset exists:** The specification must be revised (see concern `data_resources-e608a2ee`). The pipeline will abort after Phase 0 with a clear error prompting the project lead to provide an appropriate dataset or adjust the research question.

## Methodology
1. **Ingestion & Validation** – Convert all numeric fields to SI units; canonicalize `treatment_type` via a mapping dictionary; validate units using per‑source JSON metadata (FR‑009).  
2. **Missing‑Value Handling** – Median imputation per substrate class (FR‑002). Records lacking the target are dropped.  
3. **Grouped Split** – 70/15/15 split by `pair_id` to avoid leakage (FR‑010). Sparse groups (< 5) are excluded (FR‑011). `pair_id` is one‑hot encoded and retained as a covariate in all models.  
4. **Model Training** – Grid search ≤ 50 combos across:
   - `RandomForestRegressor` (n_estimators 100‑200, max_depth 10‑None)
   - `GradientBoostingRegressor` (learning_rate 0.01‑0.1, n_estimators 100‑200)
   - `LinearRegression` (no hyper‑params)  
   For each model, compute **bootstrapped confidence interval** for validation R² (10 000 resamples).  
5. **Model Selection** – Choose the model whose **lower bound of the validation R² CI ≥ 0.5**; if multiple qualify, prefer the simpler model (Linear > RF > GB).  
6. **Nested Permutation Significance Test** – Perform 5‑fold outer CV; within each outer training fold run the full hyper‑parameter search (inner CV). After selecting the best model, permute the target **within each outer test fold** multiple times, recompute R², and derive an empirical p‑value that accounts for the entire model‑selection pipeline.  
7. **SHAP Interpretability** –  
   - Tree models → `shap.TreeExplainer` (CPU).  
   - Linear model → `shap.LinearExplainer`; if fails, fallback to `shap.KernelExplainer` (FR‑015).  
   Produce summary plot PNG and feature‑ranking JSON (FR‑006).  
8. **Statistical Rigor** –  
   - **Multiple‑Comparison Correction:** Only one primary outcome (R²) is tested, so no correction needed.  
   - **Power Assessment:** Minimum 200 records required; if dataset smaller, report limitation.  
   - **Assumption Checks:** Linear model coefficients examined for multicollinearity (VIF > 5 flagged).  
   - **Confidence Intervals:** 95 % bootstrapped CI for R² (10 000 resamples).  
9. **Report Generation** – Compile JSON and Markdown report containing:
   - Validation & test R², RMSE, MAE  
   - 95 % CI for R² (both validation and test)  
   - Permutation p‑value (nested)  
   - Top‑3 SHAP features  
   - Per‑predictor p‑values (where linear model applicable) (FR‑013)  
   - All four required visualizations (FR‑014)  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open dataset with required variables | Blocked ingestion, no real scientific claim | Identify alternative open dataset; if impossible, revise FR‑001 and research question (spec change). |
| Sparse polymer‑substrate groups causing excessive exclusion | Reduced sample size → lower power | Aggregate chemically similar pairs per FR‑011; report effective sample size. |
| High collinearity among treatment parameters | Inflated importance scores | Compute VIF; if > 5, report collinearity and rely on SHAP (model‑agnostic) for interpretation. |
| Runtime > 6 h | CI job failure | Limit hyper‑parameter combos; use `n_jobs=1`; sample dataset if still too large (document power limitation). |

## Expected Deliverables
- `data/raw/` – original downloaded files (checksumed).  
- `data/cleaned/cleaned.csv` – fully standardized dataset.  
- `models/<model_type>.pkl` – serialized best model artifact.  
- `results/report.json` & `results/report.md` – complete analysis output.  
- `figures/` – PNG files: predicted‑vs‑actual scatter, residual histogram, SHAP summary, parameter‑response curves.  
- `contracts/` – schema files for dataset, model artifact, and analysis result (see `contracts/` directory).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seeds are pinned (`np.random.seed(42)`, `random_state=42`). |
| II. Verified Accuracy | All citations are verified against the provided list; no unverified sources introduced. |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new CSV; SHA‑256 checksums recorded. |
| IV. Single Source of Truth | All figures/tables are generated directly from the JSON report; no manual transcription. |
| V. Versioning | Artifact hashes computed; any change updates the project state file. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid ≤ 50 combos; model acceptance requires validation R² lower‑CI ≥ 0.5 **and** permutation p < 0.05. |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, median imputation per substrate class, canonical treatment taxonomy, and `pair_id` covariate are enforced in Phase 2. |