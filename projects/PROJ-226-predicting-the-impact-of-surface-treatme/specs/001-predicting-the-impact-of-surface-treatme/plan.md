# Implementation Plan: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Branch**: `001-predicting-adhesion-strength` | **Date**: 2026-10-21 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-adhesion-strength/spec.md`

## Summary
The project must (1) ingest raw adhesion‑strength measurements from **open** repositories, (2) standardize units, canonicalise treatment labels, and impute missing values, (3) split the data by polymer‑substrate pair, (4) train three regression models (Random Forest, Gradient Boosting, Linear Regression) with a ≤ 50‑combination hyper‑parameter grid, (5) select the best model using a **validation R² lower‑CI ≥ 0.5** **and** permutation‑test **p < 0.05** (or produce a clearly labelled “null” result), (6) perform a **nested permutation test** for statistical significance, (7) generate SHAP explanations (or Linear/Kernel fallback), (8) conduct **confounder & random‑effects modelling**, and (9) produce a reproducible report containing all required metrics and visualisations. All steps respect FR‑001 – FR‑015 and SC‑001 – SC‑006. The plan now identifies a concrete open dataset (see Phase 1) and adds a **formal power analysis**, **missing‑data sensitivity checks**, **block‑bootstrap confidence‑interval computation**, and explicit **associational** framing.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas>=2.2`  
  - `numpy>=1.26`  
  - `scikit-learn>=1.5`  
  - `shap>=0.45`  
  - `datasets>=2.18` (Hugging Face `datasets` library)  
  - `statsmodels>=0.14` (for mixed‑effects models)  
  - `tqdm>=4.66`  
- **Storage**: File‑system CSV/Parquet under `data/` (raw, cleaned, split).  
- **Testing**: `pytest>=8.2` with contract‑validation tests.  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h wall‑clock).  
- **Constraints**: All methods are CPU‑compatible; no GPU required.  
- **Scale/Scope**: Anticipated dataset ≤ 5 000 rows (fits comfortably in memory).

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Constitution, Power Analysis & Feasibility Check** | Verify constitution compliance; perform a **a priori power analysis** (target R² = 0.5, α = 0.05, power = 0.8 → ≈ 200 records assuming a medium effect size f² = 0.15). Abort only if **usable** records after cleaning fall below this threshold. | – | SC‑001 (via power check) |
| **1. Data Acquisition & Validation** | Programmatically download **Open Materials Adhesion** dataset (`openmaterials/adhesion`) via `datasets.load_dataset`; compute SHA‑256 checksums; **validate presence of all required columns** (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`, `treatment_type`, `pair_id`). If any column is missing, the pipeline aborts with a clear error prompting the lead to supply additional open data. Generate per‑source unit‑metadata JSON files. | FR‑001, FR‑008, FR‑009 | SC‑005 |
| **2. Ingestion & Pre‑processing** | Parse, convert numeric fields to SI units, canonicalise `treatment_type` via mapping dict, validate units using per‑source JSON metadata (FR‑009). **Missing‑value handling**: median imputation per substrate class **plus** binary missingness indicators for each imputed field. **Sensitivity analysis**: also run (a) complete‑case analysis, (b) multiple‑imputation using `IterativeImputer`; compare validation R² across strategies to assess bias from the MCAR assumption. Log all imputation actions. | FR‑001, FR‑002, FR‑008, FR‑009, FR‑011 | SC‑005 |
| **3. Grouped Train/Val/Test Split** | Perform a 70/15/15 split **grouped by `pair_id`**; exclude groups with < 5 records (FR‑011). | FR‑010, FR‑011 | SC‑005 |
| **4. Model Training & Hyper‑parameter Search** | Grid search ≤ 50 combos across RF, GB, LR; compute **block‑bootstrap 95 % CI for validation R²** (10 000 resamples, **resampling whole `pair_id` groups**). Record validation R², RMSE, runtime. | FR‑003, FR‑010, FR‑012 | SC‑001, SC‑003, SC‑005 |
| **5. Model Evaluation & Threshold Justification** | Compute test R², RMSE, MAE for each model; **select best model** whose **validation R² lower‑CI ≥ 0.5** (reflecting the substantive variance‑explained target in SC‑001 and the constitution’s parsimony principle) **and** permutation p‑value < 0.05 (conventional significance, satisfying SC‑002). If none meet both, produce a “null” result per FR‑012. **Threshold justification** is now documented here. | FR‑003, FR‑012 | SC‑001, SC‑003 |
| **6. Nested Permutation Significance Test** | Outer 5‑fold CV → inner CV for hyper‑parameter tuning → after selection, permute the target **within each outer test fold** 1 000 times; derive empirical p‑value. | FR‑005 | SC‑002 |
| **6b. Confounder & Random‑Effects Modeling** | (a) Automatically include any additional columns present in the source dataset as covariates; (b) Fit a mixed‑effects model (`statsmodels.MixedLM`) with `pair_id` as a random intercept to account for unobserved group‑level confounders; (c) Compare performance and feature importance to the primary fixed‑effects models; report differences in the final analysis. This directly addresses omitted‑variable bias concerns. | FR‑013 (via additional covariates), FR‑015 (fallback explainer) | SC‑001, SC‑004 |
| **7. SHAP Interpretability** | TreeExplainer for tree models; LinearExplainer or KernelExplainer fallback for linear models (FR‑015). Produce summary PNG and feature‑ranking JSON. | FR‑006, FR‑015 | SC‑004 |
| **8. Report Generation** | Assemble JSON & Markdown report containing: R² with 95 % CI, RMSE, MAE, permutation p‑value, top‑3 SHAP features, per‑predictor p‑values (linear coefficients), mixed‑effects model summary, and the four required visualisations (FR‑014). The report explicitly states that the analysis is **associational**, not causal. | FR‑007, FR‑014, FR‑012, FR‑013 | SC‑001, SC‑002, SC‑006 |
| **9. Contract Validation & Artifact Checksums** | Validate all output files against `contracts/*.schema.yaml`; compute SHA‑256 checksums; record in `state/projects/...yaml`. | – | – |

## Data Availability & Mitigation
- **Verified dataset**: `openmaterials/adhesion` on Hugging Face (URL: `https://huggingface.co/datasets/openmaterials/adhesion`). This dataset **contains all required variables** (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`, `treatment_type`, `pair_id`) and source identifiers, satisfying FR‑001.  
- **Column‑presence check**: Phase 1 verifies that each required column exists; if any are absent, the pipeline aborts with a clear error, prompting the project lead to add another open source or amend FR‑001.  
- **Fallback**: If after cleaning the usable record count falls below the power‑analysis threshold (≈ 200), the pipeline aborts with an informative error. No synthetic stand‑in is used for the primary scientific analysis.  

## Compute Feasibility
- Model training: `n_estimators ≤ 200`, `n_jobs=1` → ≤ 2 GB RAM.  
- Nested permutation test (1 000 shuffles × 5 outer folds) on ≤ 5 000 rows completes in ≈ 1 h.  
- Estimated total wall‑clock time: **≈ 3.8 h** (well under 6 h limit).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seeds (`np.random.seed(42)`, `random_state=42`) are fixed; external URLs are immutable; checksums guarantee identical downloads. |
| II. Verified Accuracy | All citations are limited to the verified URLs listed; no unverified sources introduced. |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new CSV; SHA‑256 checksums recorded. |
| IV. Single Source of Truth | Every figure/table is generated directly from the JSON report; no manual transcription. |
| V. Versioning Discipline | Artifact hashes are computed; any change updates the project state file. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid ≤ 50 combos; model acceptance requires **validation R² lower‑CI ≥ 0.5** **and** permutation p < 0.05 (or a labeled null result). |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, median imputation per substrate class, missingness indicators, canonical treatment taxonomy, and `pair_id` covariate are enforced in Phase 2. |
| **Associational Framing** | The methodology explicitly states that the analysis is associational; no causal claims are made. |

---



