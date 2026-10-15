# Implementation Plan: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Branch**: `001-predicting-adhesion-strength` | **Date**: 2026-10-15 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-adhesion-strength/spec.md`

## Summary
The project must (1) ingest raw adhesion‑strength measurements from open repositories, (2) standardize units, canonicalise treatment labels, and impute missing values, (3) split the data by polymer‑substrate pair, (4) train three regression models (Random Forest, Gradient Boosting, Linear Regression) with a ≤ 50‑combination hyper‑parameter grid, (5) select the best model using a validation‑R² lower‑CI ≥ 0.5, (6) assess statistical significance with a nested 1 000‑shuffle permutation test, (7) generate SHAP explanations (or Linear/Kernel fallback), and (8) produce a reproducible report containing all required metrics and visualisations.  

All steps respect the functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑006). Because the verified dataset list does **not** contain a source with the full variable set, the pipeline includes an explicit abort step (Phase 0) that halts execution with a clear error message until a suitable open dataset is supplied or the specification is revised.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**:  
  - `pandas>=2.2`  
  - `numpy>=1.26`  
  - `scikit-learn>=1.5`  
  - `shap>=0.45`  
  - `datasets>=2.18` (Hugging Face `datasets` library)  
  - `tqdm>=4.66`  
  - `pyyaml>=6.0`  
- **Storage**: File‑system CSV/Parquet under `data/` (raw, cleaned, split).  
- **Testing**: `pytest>=8.2` with contract‑validation tests.  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU cores, ≈ 7 GB RAM, ≤ 6 h wall‑clock).  
- **Constraints**: All methods are CPU‑compatible; no GPU is required.  
- **Scale/Scope**: Anticipated dataset ≤ 5 000 rows (fits comfortably in memory).

## Phase Overview & FR/SC Mapping
| Phase | Description | FR(s) addressed | SC(s) addressed |
|-------|-------------|-----------------|-----------------|
| **0. Constitution & Feasibility Check** | Verify that every principle in the constitution is satisfied; confirm that an open dataset containing **all** required variables exists. Abort with informative error if not. | – | – |
| **1. Data Acquisition & Validation** | Programmatically download verified open datasets; compute SHA‑256 checksums; validate presence of required columns; generate per‑source unit‑metadata JSON. | FR‑001, FR‑008, FR‑009 | SC‑005 |
| **2. Ingestion & Pre‑processing** | Parse CSV/JSON, convert all numeric fields to SI units, canonicalise `treatment_type`, one‑hot encode categorical fields (including `pair_id`), median‑impute per‑substrate‑class, flag low‑coverage fields, write `cleaned.csv`. | FR‑001, FR‑002, FR‑008, FR‑009, FR‑011 | SC‑005 |
| **3. Grouped Train/Val/Test Split** | Perform a 70/15/15 split **grouped by `pair_id`**; exclude groups with < 5 records (FR‑011). | FR‑010, FR‑011 | SC‑005 |
| **4. Model Training & Hyper‑parameter Search** | Grid search ≤ 50 combos across RF, GB, LR; compute **bootstrapped 95 % CI** for validation R² (10 000 resamples); record validation R², RMSE, runtime. | FR‑003, FR‑010, FR‑012 | SC‑001, SC‑003, SC‑005 |
| **5. Model Evaluation** | Compute test R², RMSE, MAE for each model; select best model whose **lower‑CI ≥ 0.5**; if none meet, produce a “null” result (FR‑012). | FR‑003, FR‑012 | SC‑001, SC‑003 |
| **6. Nested Permutation Significance Test** | Outer 5‑fold CV → inner CV for hyper‑parameter tuning → after selection, permute target **within each outer test fold** 1 000 times; derive empirical p‑value. | FR‑005 | SC‑002 |
| **7. SHAP Interpretability** | TreeExplainer for tree models; LinearExplainer or KernelExplainer fallback for linear models (FR‑015); produce summary PNG and feature‑ranking JSON. | FR‑006, FR‑015 | SC‑004 |
| **8. Report Generation** | Assemble JSON & Markdown report containing: R² with 95 % CI, RMSE, MAE, permutation p‑value, top‑3 SHAP features, per‑predictor p‑values (linear coeffs), and the four required visualisations (FR‑014). | FR‑007, FR‑014, FR‑012, FR‑013 | SC‑001, SC‑002, SC‑006 |
| **9. Contract Validation & Artifact Checksums** | Validate all output files against `contracts/*.schema.yaml`; compute SHA‑256 checksums; record in `state/projects/...yaml`. | – | – |

## Data Availability & Mitigation
- **Verified datasets list** (see user message) does **not** contain a dataset with the full variable set (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`).  
- **Result:** Phase 0 will abort with the message:

  ```
  ERROR: No open, programmatically downloadable dataset containing all required variables was found.
  Please supply a suitable dataset URL (and update FR‑001) or revise the functional requirements.
  ```

- **Allowed fallback:** A tiny synthetic generator may be run for code‑path testing only; its results are labelled “illustrative” and are **excluded** from meeting SC‑001 or SC‑002.

## Compute Feasibility
- Model training: `n_estimators ≤ 200`, `n_jobs=1` → ≤ 2 GB RAM.  
- Nested permutation test (1 000 shuffles × 5 outer folds) on ≤ 5 000 rows completes in ≈ 1 h.  
- Estimated total wall‑clock time: **≈ 3.8 h** (well under 6 h limit).  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | Random seeds (`np.random.seed(42)`, `random_state=42`) are fixed; external URLs are immutable; checksums guarantee identical downloads. |
| II. Verified Accuracy | All citations are limited to the verified URLs listed above; no unverified sources are introduced. |
| III. Data Hygiene | Raw files are read‑only; each transformation writes a new file with a timestamped name; SHA‑256 checksums stored in `state/projects/...yaml`. |
| IV. Single Source of Truth | Every figure/table is generated directly from the JSON report; no manual transcription. |
| V. Versioning Discipline | Artifact hashes are computed for all outputs; any change updates the project state file automatically. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid ≤ 50 combos; model acceptance requires **validation R² lower‑CI ≥ 0.5** **and** permutation p < 0.05 (or a labeled null result). |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, per‑substrate‑class median imputation, canonical treatment taxonomy, and `pair_id` covariate enforcement are performed in Phase 2. |

---
