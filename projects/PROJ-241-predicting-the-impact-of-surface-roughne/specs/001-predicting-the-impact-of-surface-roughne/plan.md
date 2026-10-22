# Implementation Plan: Predicting the Impact of Surface Roughness on Tribological Properties

**Branch**: `001-predict-tribology` | **Date**: 2026-10-22 | **Spec**: [/specs/001-predict-tribology/spec.md](../specs/001-predict-tribology/spec.md)  
**Input**: Feature specification from `/specs/001-predict-tribology/spec.md`

## Summary
The pipeline will (1) **verify** the existence and column‑completeness of the OpenML dataset (ID 42123) and of the NIST Materials Data Repository; (2) **download** the OpenML dataset (streaming) and retrieve material properties via the Materials Project API (fallback to median imputation); (3) **extract** surface‑roughness descriptors with `pySurf` (or validate existing roughness columns via KS test if raw files are absent); (4) **clean** data using MAD‑based outlier removal, median imputation, and `StandardScaler`; (5) **split** data with a group‑aware train/test split stratified by `pairing_id`; (6) **train** three regressors (OLS, Random Forest, Gradient Boosting) with nested cross‑validation and hyper‑parameter tuning; (7) **evaluate** R², MAE, RMSE on a held‑out test set; (8) **perform** a data‑driven power analysis and select a paired t‑test or Wilcoxon signed‑rank test (Bonferroni‑corrected for two targets); (9) **generate** SHAP value plots, report sign consistency with known physics, and flag any discrepancies; (10) **assemble** a single source of truth JSON (`results.json`) containing all metrics, SHAP rankings, imputation statistics, and checksum manifest.

All steps are CPU‑first, designed to complete within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pySurf`, `shap`, `matplotlib`, `requests`, `statsmodels`, `openml`, `pymatgen` (Materials Project client)  
- **Storage**: CSV/Parquet under `data/`  
- **Testing**: `pytest` with contract validation via `jsonschema`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM) – **CPU‑first**; no GPU required.  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h (SC‑005).  
- **Constraints**: Must satisfy all Constitution principles; must not fabricate unavailable data.  

## Constitution Check
| Principle | Requirement | Status / Action |
|-----------|-------------|-----------------|
| I. Reproducibility | Fixed seeds, deterministic downloads, version‑pinned dependencies | ✅ seeds set (`RANDOM_SEED=42`); `requirements.txt` pins versions |
| II. Verified Accuracy | All external citations must be verified | ❌ OpenML ID 42123 and NIST DOI lack verified URLs; Phase 0 will abort until a verified open source is supplied |
| III. Data Hygiene | Checksums, immutable transformations, no PII | ✅ raw files checksummed; each transformation writes a new file |
| IV. Single Source of Truth | All figures/statistics trace to one data row & code block | ✅ `results.json` serves as SSoT |
| V. Versioning Discipline | Content hashes recorded, timestamps updated | ✅ hashes stored in `state/` by CI framework |
| VI. Numerical Stability & Model Robustness | Stratified splits by material pair, 5‑fold CV, outlier removal, median imputation, target R² ≥ 0.7 | ✅ implemented in Phases 3‑5; R² targets enforced in SC‑001/SC‑002 |
| VII. Interpretability and Feature Attribution | SHAP plots, sign consistency check, statistical significance (p < 0.05) | ✅ SHAP generation (Phase 8) and sign‑consistency logging (FR‑011) |

## Project Structure
```
specs/001-predict-tribology/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── tribology-dataset.schema.yaml
src/
├── pipeline/
│   ├── download.py          # FR‑001, FR‑003
│   ├── extract.py           # FR‑002, FR‑016
│   ├── preprocess.py        # FR‑004, FR‑005, FR‑012, FR‑016
│   ├── split.py             # FR‑014
│   ├── modeling.py          # FR‑006, FR‑007, FR‑015
│   ├── evaluation.py        # FR‑008, FR‑010, SC‑001‑SC‑003
│   └── interpret.py         # FR‑009, FR‑011
tests/
├── contract/
│   └── test_dataset_schema.py
└── unit/
    └── test_preprocess.py
```
**Structure Decision**: A single‑project layout keeps the research code together and satisfies all FR/SC without unnecessary complexity.

## Phase‑wise Implementation Tasks (FR/SC Mapping)

| Phase | Description | FR/SC Covered |
|-------|-------------|---------------|
| **0 – Data Availability Assessment** | Verify that the OpenML dataset (ID 42123) is reachable, contains all required columns (`Sa`, `Sq`, `Ssk`, `Sku`, `Sp`, `Sv`, `coeff_friction`, `wear_rate`), and that the NIST repository can be accessed (or Material Project API is usable). Abort with `DataAvailabilityError` if any check fails. | FR‑001, FR‑003, FR‑012 |
| **1 – Data Acquisition** | Stream OpenML dataset via `openml.datasets.get_dataset(42123, download_all_files=True, streaming=True)`. Retrieve material properties for each material ID via Materials Project API; if API key missing or request fails, fall back to median imputation (logged). | FR‑001, FR‑003 |
| **2 – Roughness Feature Extraction** | If raw profilometry files are present, compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If missing, verify that existing roughness columns in the OpenML file are statistically comparable to `pySurf`‑derived values using a Kolmogorov‑Smirnov test (p > 0.05); abort if KS test fails. | FR‑002, FR‑016 |
| **3 – Data Cleaning** | • Outlier removal with **MAD rule**: flag rows where \|x – median\| > 3.5 × MAD and drop them.<br>• Median imputation for any remaining missing values (including material properties). Log each imputation event; compute `imputed_fraction` (must be ≤ 0.05) (SC‑007).<br>• Standardize numeric features with `StandardScaler` (FR‑005).<br>• Verify existence of target columns (`coeff_friction`, `wear_rate`) before proceeding (FR‑012).<br>• Assert that ≥ 200 rows remain after cleaning; if fewer, log a warning and continue (SC‑006). | FR‑004, FR‑005, FR‑012, FR‑016, SC‑006, SC‑007 |
| **4 – Train‑Test Split** | Perform **group‑aware split** by `pairing_id` using `GroupShuffleSplit` (80 % train / 20 % test, `random_state=42`). Ensure no material pair appears in both sets. | FR‑014, SC‑005 |
| **5 – Model Training & Nested CV** | **Outer CV**: 5‑fold if n ≥ 100 else 3‑fold (FR‑007). **Inner CV**: same fold count for hyper‑parameter tuning via `GridSearchCV`. Train three regressors (OLS, RandomForestRegressor, GradientBoostingRegressor) on the full training set with best hyper‑parameters. OLS serves as baseline for significance testing. | FR‑006, FR‑007, FR‑015 |
| **6 – Evaluation** | Compute **R²**, **MAE**, **RMSE** on the held‑out test set for both targets; store in `results/metrics.json`. | FR‑008, SC‑001, SC‑002 |
| **7 – Power Analysis & Significance Testing** | Estimate effect size (Cohen’s d) from training data; if insufficient data, fallback to d = 0.5. Use `statsmodels.stats.power.TTestPower` (α = 0.05) to compute power. If power < 0.8 **or** n < 200, select **Wilcoxon signed‑rank test**; otherwise use a **paired t‑test**. Apply **Bonferroni correction** for the two targets (α_adj = 0.025). Record p‑values in `results/metrics.json`. | FR‑010, SC‑003 |
| **8 – SHAP Interpretation** | Generate SHAP values (TreeExplainer for RF/GB, KernelExplainer for OLS). Produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑5 features. **Report** whether the sign of each important feature matches the physics lookup table (e.g., hardness ↘ wear). Log any mismatches (FR‑011) but do not abort. | FR‑009, FR‑011, SC‑004 |
| **9 – Reporting & SSoT Assembly** | Compile `results.json` containing: metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, final row count, any sign‑consistency flags, and a SHA‑256 checksum manifest for all artifacts. This JSON is the **Single Source of Truth** for downstream paper generation. | SC‑001‑SC‑007, FR‑017 |
| **10 – Artifact Generation & Validation** | Save processed dataset (`data/processed/tribology_dataset.parquet`), model checkpoints (`models/*.pkl`), and contract‑validated schema files. Compute checksums (`data/raw/checksums.txt`). Run contract test against `contracts/tribology-dataset.schema.yaml`. | All FR/SC (ensures reproducibility & data hygiene) |

**Note**: Phase 0 is a hard gate. If either the OpenML dataset or the NIST repository cannot be accessed (or the OpenML dataset lacks required columns), the pipeline aborts with a clear error; the project owner must supply an open, verified substitute before any downstream work proceeds.

---
