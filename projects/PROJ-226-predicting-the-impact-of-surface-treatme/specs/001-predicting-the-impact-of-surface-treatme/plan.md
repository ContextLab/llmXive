# Implementation Plan: Predicting the Impact of Surface Treatments on the Adhesion Strength of Polymers

**Branch**: `001-predicting-adhesion-strength` | **Date**: 2026-10-14 | **Spec**: [spec.md]  
**Input**: Feature specification from `/specs/001-predicting-adhesion-strength/spec.md`

## Summary
The project must ingest heterogeneous adhesion‑strength datasets from public repositories, standardize units and categorical labels, train three regression models (Random Forest, Gradient Boosting, Linear Regression) with a grouped 70/15/15 split, evaluate them via a nested permutation test, and produce SHAP‑based interpretability visualizations. All steps must satisfy the functional requirements (FR‑001 – FR‑015) and success criteria (SC‑001 – SC‑006).  

**Key Challenge:** No open, programmatically downloadable dataset containing the required variables (`plasma_power_w`, `exposure_time_s`, `chemical_concentration_pct`, `polymer_surface_energy`, `substrate_roughness_nm`, `adhesion_strength_mj_m2`) is currently listed in the verified‑datasets block. This limitation must be resolved at the specification level before real scientific claims can be made (see Data Availability & Mitigation).

## Technical Context
- **Language/Version:** Python 3.11  
- **Primary Dependencies:** `pandas>=2.2`, `numpy>=1.26`, `scikit-learn>=1.5`, `shap>=0.45`, `datasets>=2.18`, `tqdm>=4.66`, `pyyaml>=6.0`  
- **Storage:** File‑system CSV/Parquet under `data/` (raw, cleaned, and derived files).  
- **Testing:** `pytest>=8.2` with contract‑validation tests.  
- **Target Platform:** Linux (GitHub Actions free‑tier runner).  
- **Constraints:** Total wall‑clock time ≤ 6 h, RAM ≤ 7 GB, no GPU required (all methods CPU‑compatible).  
- **Scale/Scope:** Anticipated dataset ≤ 5 000 records (fits comfortably on CI runner).

## Phase Overview & FR/SC Mapping
| Phase | Description | Primary FR(s) addressed | Primary SC(s) addressed |
|-------|-------------|--------------------------|--------------------------|
| **0. Constitution & Feasibility Check** | Verify that all principles are satisfied; **perform a dataset variable‑coverage check**. Abort with informative error if any required variable is missing from all available open sources. | – | – |
| **1. Data Acquisition & Validation** | Programmatically download verified open datasets; compute checksums; validate presence of required columns; generate unit‑metadata JSON. | FR‑001, FR‑008, FR‑009 | SC‑005 |
| **2. Ingestion & Pre‑processing** | Parse CSV/JSON, unify units to SI, canonicalize `treatment_type`, one‑hot encode categorical fields **including `pair_id`**, median‑impute per‑substrate‑class, flag low‑coverage fields, generate `cleaned.csv`. | FR‑001, FR‑002, FR‑008, FR‑009, FR‑011 | SC‑005 |
| **3. Train‑Validation‑Test Split** | Perform grouped split by `pair_id` (70/15/15) respecting sparsity rule (exclude groups < 5). | FR‑010, FR‑011 | SC‑005 |
| **4. Model Training & Hyper‑parameter Search** | Grid search ≤ 50 combos across Random Forest, Gradient Boosting, Linear Regression; compute **bootstrapped 95 % CI** for validation R² (10 000 resamples); record validation R², RMSE, runtime. | FR‑003, FR‑010, FR‑012 | SC‑001, SC‑003, SC‑005 |
| **5. Model Evaluation** | Compute test R², RMSE, MAE for each model; select best model by **validation R² lower‑CI ≥ 0.5**; if tie, prefer simpler model. | FR‑003, FR‑012 | SC‑001, SC‑003 |
| **6. Nested Permutation Significance Test** | Outer 5‑fold CV for evaluation; inner CV (as in Phase 4) for hyper‑parameter tuning; after model selection, permute target **within each outer test fold** (1 000 shuffles) to build null distribution for observed R², yielding a p‑value that accounts for model‑selection bias. | FR‑005 | SC‑002 |
| **7. SHAP Interpretability** | Generate SHAP values (TreeExplainer for tree models; LinearExplainer/KernelExplainer for linear models); produce summary plot PNG and feature‑ranking JSON. | FR‑006, FR‑015 | SC‑004 |
| **8. Report Generation** | Assemble JSON and Markdown report containing: R² with 95 % bootstrapped CI, RMSE, MAE, permutation p‑value, top‑3 SHAP features, per‑predictor significance (linear coeff p‑values), all four visualizations. | FR‑007, FR‑014, FR‑012, FR‑013 | SC‑001, SC‑002, SC‑006 |
| **9. Contract Validation & Artifact Checksum** | Validate output files against `contracts/*.schema.yaml`; compute SHA‑256 checksums; record in `state/projects/...yaml`. | – | – |

## Data Availability & Mitigation
- **Verified datasets list** (provided by the user) currently **does not contain** a dataset with the full required variable set.  
- **Result:** The pipeline **cannot** proceed with real data under the existing FR‑001.  
- **Required Action:**  
  1. **Specification revision** is required **before any further execution**: either (a) identify a concrete open dataset that provides *all* required variables and update FR‑001 accordingly, **or** (b) modify the research question and functional requirements to match the variables available in an existing open dataset.  
  2. Until such a revision is made, the pipeline will stop after **Phase 0** with an informative error message prompting the project lead to supply an appropriate dataset or approve a scope change.  
- **Synthetic fallback:** May be used **only** for internal code testing or methodological proof‑of‑concept; **synthetic results are excluded** from meeting SC‑001 (R² ≥ 0.5) or SC‑002 (p < 0.05) and will not be used for the primary scientific analysis.

## Compute Feasibility
- All model training uses `n_estimators ≤ 200` for Random Forest/Gradient Boosting, which fits within ≤ 2 GB RAM on 2‑core CPU.  
- Nested permutation test (1 000 shuffles per outer fold) runs in [deferred] on the test set (< 1 000 records).
- Estimated total wall‑clock time: **≈ 3.8 h** (well below the 6 h CI limit).

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts pin random seeds (`np.random.seed(42)`, `random_state=42`). External data URLs are fixed; checksum verification ensures identical downloads. |
| II. Verified Accuracy | All citations (e.g., to NIST dataset URL) are verified against the provided list. No unverified sources are introduced. |
| III. Data Hygiene | Raw files are stored read‑only; each transformation writes a new CSV with a filename pattern `cleaned_*.csv`. SHA‑256 checksums recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | Every figure/table pulls directly from the JSON report generated in Phase 8; no manual transcription. |
| V. Versioning Discipline | Artifact hashes are computed for every output file; any change updates the project state file automatically. |
| VI. Computational Model Stability and Parsimony | Hyper‑parameter grid limited to ≤ 50 combos; model acceptance requires **validation R² lower‑CI ≥ 0.5** **and** permutation p < 0.05. |
| VII. Material‑Specific Feature Engineering Integrity | Unit conversion, median imputation per substrate class, canonical treatment taxonomy, and `pair_id` covariate are enforced in Phase 2. |