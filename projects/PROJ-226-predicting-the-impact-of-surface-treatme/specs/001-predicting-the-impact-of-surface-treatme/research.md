# Research: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

## Overview
This research plan outlines how we will answer the core question: *How do surface‑treatment parameters influence polymer adhesion strength?* The approach integrates a reproducible ingestion pipeline, grouped regression modelling, a **nested permutation test** for statistical significance, and SHAP interpretability.

## Dataset Strategy
| Source | Variable Coverage* | Access Method | Verified URL |
|--------|-------------------|---------------|--------------|
| **Open adhesion dataset (to be identified)** | Must contain **all** required predictors (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`) **and** the target `adhesion_strength_mj_m2`. | `datasets.load_dataset("<repo>/<name>", split="train")` **or** `wget`/`curl` for CSV | **None currently verified** – the pipeline will abort at Phase 0 if no such dataset is found (see Plan § Data Availability & Mitigation). |
| **Synthetic generator (testing only)** | Generates all required variables with realistic ranges based on literature. | Custom Python generator (`synthetic_data.generate(...)`). | N/A (synthetic) |

\*Coverage is assessed after download; variables present in < 80 % of rows trigger median imputation per substrate class (FR‑002). Records missing the target are excluded.

### Decision & Rationale
- **Primary choice:** Locate an open dataset that satisfies the full variable list. This respects the non‑fabrication rule and aligns with FR‑001 – FR‑009.  
- **Secondary fallback:** Synthetic data may be used **only** for internal pipeline validation; it **cannot** satisfy SC‑001 (R² ≥ 0.5) or SC‑002 (p < 0.05). Any results derived from synthetic data will be clearly labelled “illustrative” and excluded from the scientific claim.  
- **If no suitable real dataset exists:** The specification must be revised (e.g., broaden FR‑001, adjust the research question). The pipeline will stop after Phase 0 with a clear error prompting the project lead to supply a suitable dataset or approve a scope change.

## Methodology
1. **Ingestion & Validation** – Convert numeric fields to SI units; canonicalise `treatment_type` via a mapping dictionary; validate units using per‑source JSON metadata (FR‑009).  
2. **Missing‑Value Handling** – Median imputation per substrate class (FR‑002). Records lacking the target are dropped.  
3. **Grouped Split** – 70/15/15 split by `pair_id` (FR‑010); exclude groups with < 5 records (FR‑011). `pair_id` is one‑hot encoded and retained as a covariate.  
4. **Model Training** – Grid search ≤ 50 combos across Random Forest, Gradient Boosting, Linear Regression; compute **bootstrapped 95 % CI** for validation R² (10 000 resamples).  
5. **Model Selection** – Choose the model whose **validation R² lower‑CI ≥ 0.5**; if multiple qualify, prefer the simpler model (Linear > RF > GB).  
6. **Nested Permutation Significance Test** – Outer 5‑fold CV → inner CV for hyper‑parameter tuning → after selection, permute the target **within each outer test fold** 1 000 times; derive empirical p‑value.  
7. **SHAP Interpretability** – TreeExplainer for tree models; LinearExplainer or KernelExplainer fallback for linear models (FR‑015). Produce summary plot PNG and feature‑ranking JSON.  
8. **Statistical Rigor** –  
   - **Multiple‑Comparison Correction:** Only one primary outcome (R²) → no correction needed.  
   - **Power Assessment:** Minimum 200 records required; if smaller, report limitation.  
   - **Assumption Checks:** Compute VIF for linear models; flag VIF > 5.  
   - **Confidence Intervals:** 95 % bootstrapped CI for R² (10 000 resamples).  
9. **Report Generation** – Compile JSON and Markdown report containing: validation & test R², RMSE, MAE, 95 % CI, permutation p‑value, top‑3 SHAP features, per‑predictor p‑values (linear coeffs), and the four required visualisations (FR‑014).  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| No open dataset with required variables | Pipeline aborts; no scientific result | Identify alternative open dataset; if impossible, revise FR‑001 and research question. |
| Sparse polymer‑substrate groups → excessive exclusion | Reduced sample size → lower statistical power | Aggregate chemically similar pairs per FR‑011; report effective sample size. |
| High collinearity among treatment parameters | Inflated importance scores, unstable coefficients | Compute VIF; if > 5, report collinearity and rely on SHAP (model‑agnostic) for interpretation. |
| Runtime > 6 h on CI | Job failure | Limit hyper‑parameter combos; use `n_jobs=1`; sample dataset if still too large (document power limitation). |

## Expected Deliverables
- `data/raw/` – original downloaded files (checksumed).  
- `data/cleaned/cleaned.csv` – fully standardized dataset.  
- `data/cleaned/train.csv`, `val.csv`, `test.csv` – grouped split.  
- `models/<model_type>.pkl` – serialized best model artifact.  
- `results/report.json` & `results/report.md` – complete analysis output.  
- `figures/` – PNGs: predicted‑vs‑actual scatter, residual histogram, SHAP summary, parameter‑response curves.  
- `contracts/` – schema files for `TreatmentRecord`, `ModelArtifact`, and `AnalysisResult`.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seeds (`np.random.seed(42)`, `random_state=42`) are fixed; external URLs are immutable; checksums guarantee identical downloads. |
| II. Verified Accuracy | All citations are limited to the verified URLs listed; no unverified sources introduced. |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new CSV; SHA‑256 checksums recorded. |
| IV. Single Source of Truth | All figures/tables are generated directly from the JSON report; no manual transcription. |
| V. Versioning Discipline | Artifact hashes are computed; any change updates the project state file. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid ≤ 50 combos; model acceptance requires validation R² lower‑CI ≥ 0.5 **and** permutation p < 0.05 (or a labeled null result). |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, median imputation per substrate class, canonical treatment taxonomy, and `pair_id` covariate are enforced in Phase 2. |

---
