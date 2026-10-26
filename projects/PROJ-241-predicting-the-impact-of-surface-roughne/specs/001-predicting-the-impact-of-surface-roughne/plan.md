# Implementation Plan: Predicting the Impact of Surface Roughness on Tribological Properties

**Branch**: `001-predict-tribology` | **Date**: 2026-10-25 | **Spec**: [/specs/001-predict-tribology/spec.md](../specs/001-predict-tribology/spec.md)  
**Input**: Feature specification from `/specs/001-predict-tribology/spec.md`

## Summary
The pipeline will (1) **verify** that a suitable open dataset containing the required roughness descriptors and tribology targets is available (Phase 0). If no such dataset is found, the pipeline aborts with a clear `DataAvailabilityError`. (2) download the verified dataset via streaming, (3) retrieve material properties via the Materials Project API (fallback to median imputation), (4) extract surface‑roughness descriptors with `pySurf` (or validate existing columns via a KS test), (5) clean the data (MAD outlier removal, median imputation, `StandardScaler`), (6) split the data using a **strict group‑aware** train/test split that prevents any individual material identifier from appearing in both sets and stratifies by `material_pair_id`, (7) train three regressors (OLS, Random Forest, Gradient Boosting) with nested cross‑validation and hyper‑parameter tuning, (8) evaluate R², MAE, RMSE, (9) perform power analysis and select the appropriate paired significance test (Bonferroni‑corrected), (10) generate SHAP value plots and verify sign consistency with a physics lookup table, and (11) assemble a single source of truth JSON (`results.json`). All steps are CPU‑first and designed to finish within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pySurf`, `shap`, `matplotlib`, `requests`, `statsmodels`, `openml`, `pymatgen` (Materials Project client)  
- **Storage**: CSV/Parquet under `data/`  
- **Testing**: `pytest` with contract validation via `jsonschema`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM) – **CPU‑first**; no GPU required.  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h (SC‑005).  
- **Constraints**: Must satisfy every Constitution principle; must not fabricate unavailable data.

## Constitution Check
| Principle | Requirement | Status / Action |
|-----------|-------------|-----------------|
| I. Reproducibility | Fixed seeds, deterministic downloads, version‑pinned dependencies | ✅ seeds set (`RANDOM_SEED=42`); `requirements.txt` pins versions |
| II. Verified Accuracy | All external citations must be verified | ✅ No unverified external dataset URLs are cited. The plan explicitly notes that **no verified open dataset currently exists**; pipeline aborts with `DataAvailabilityError` until a verified source is supplied. |
| III. Data Hygiene | Checksums, immutable transformations, no PII | ✅ raw files checksummed; each transformation writes a new file |
| IV. Single Source of Truth | All figures/statistics trace to exactly one data row & code block | ✅ `results.json` serves as SSoT |
| V. Versioning Discipline | Content hashes recorded, timestamps updated | ✅ hashes stored in `state/` by CI framework |
| VI. Numerical Stability & Model Robustness | Stratified splits by material pair, 5‑fold CV, outlier removal, median imputation, target R² ≥ 0.7 | ✅ implemented in Phases 5‑7; R² targets enforced in SC‑001/SC‑002 |
| VII. Interpretability and Feature Attribution | SHAP plots, sign consistency check, statistical significance (p < 0.05) | ✅ SHAP generation (Phase 10) and sign‑consistency logging (FR‑011) |

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
│   ├── split.py             # FR‑014 (strict material‑level split)
│   ├── modeling.py          # FR‑006, FR‑007
│   ├── evaluation.py        # FR‑008, FR‑010, SC‑001‑SC‑003
│   └── interpret.py         # FR‑009, FR‑011
└── __main__.py              # orchestrates all phases
tests/
├── contract/
│   └── test_dataset_schema.py
└── unit/
    └── test_preprocess.py
```
**Structure Decision**: A single‑project layout keeps the research code together, satisfies all FR/SC, and avoids unnecessary complexity.

## Phase‑wise Implementation Tasks (FR/SC Mapping)

| Phase | Description | FR/SC Covered |
|-------|-------------|---------------|
| **0 – Data Availability Assessment** | Verify that an **open** dataset containing the required columns (`Sa`, `Sq`, `Ssk`, `Sku`, `Sp`, `Sv`, `coeff_friction`, `wear_rate`) can be programmatically downloaded. If not, raise `DataAvailabilityError` and abort. | FR‑001, FR‑003, FR‑012 |
| **1 – Data Acquisition** | Stream the (as‑yet‑to‑be‑provided) OpenML dataset via `openml.datasets.get_dataset(..., streaming=True)`. Retrieve material properties for each material ID via Materials Project API (`pymatgen.ext.matproj.MPRester`). If the API key is missing or a request fails, log and median‑impute. | FR‑001, FR‑003 |
| **2 – Roughness Feature Extraction** | If raw profilometry files are present, compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If raw files are absent, validate the existing roughness columns in the OpenML file by performing a two‑sample Kolmogorov‑Smirnov test against a small `pySurf`‑derived reference set (p > 0.05). Abort if KS test fails. | FR‑002, FR‑016 |
| **3 – Data Cleaning** | • Outlier removal using **MAD rule**: flag rows where \|x – median\| > 3.5 × MAD and drop them.<br>• Median imputation for any remaining missing values (including material properties); each imputation is logged (SC‑007).<br>• Standardize numeric features with `StandardScaler` (FR‑005).<br>• Verify existence of target columns before proceeding (FR‑012).<br>• Assert ≥ 200 rows remain; if fewer, log a warning and continue (SC‑006). | FR‑004, FR‑005, FR‑012, FR‑016, SC‑006, SC‑007 |
| **4 – Train‑Test Split** | Perform a **strict group‑aware split**: first create groups based on each unique `material_pair_id`; then ensure that **no individual material identifier** (`material_1_id` or `material_2_id`) appears in both training and test sets by constructing a combined grouping list of all material IDs and using `GroupShuffleSplit`. This prevents any leakage across material pairs. Use a fixed random state (`random_state=42`). | FR‑014, SC‑005 |
| **5 – Model Training & Nested CV** | **Outer CV**: 5‑fold if n ≥ 100 else 3‑fold (FR‑007). **Inner CV**: same fold count for hyper‑parameter tuning via `GridSearchCV`. Train three regressors (OLS, RandomForestRegressor, GradientBoostingRegressor) on the full training set with best hyper‑parameters. OLS serves as baseline for significance testing. | FR‑006, FR‑007 |
| **6 – Evaluation** | Compute **R²**, **MAE**, **RMSE** on the held‑out test set for both targets; store in `results/metrics.json`. | FR‑008, SC‑001, SC‑002 |
| **7 – Power Analysis & Significance Testing** | Estimate effect size (Cohen’s d) from training data; if insufficient data, fallback to d = 0.5. Use `statsmodels.stats.power.TTestPower` (α = 0.05) to compute power. If power < 0.8 **or** n < 200, select **Wilcoxon signed‑rank test**; otherwise use a **paired t‑test**. Apply **Bonferroni correction** for the two targets (α_adj = 0.025). Record p‑values in `results/metrics.json`. | FR‑010, SC‑003 |
| **8 – SHAP Interpretation** | Generate SHAP values (TreeExplainer for RF/GB, KernelExplainer for OLS). Produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑5 features. **Report** whether the sign of each important feature matches the physics lookup table (e.g., hardness ↘ wear). Log any mismatches (FR‑011) but do not abort. | FR‑009, FR‑011, SC‑004 |
| **9 – Reporting & SSoT Assembly** | Compile `results.json` containing: metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, final row count, sign‑consistency flags, and a SHA‑256 checksum manifest for all artifacts. This JSON is the **Single Source of Truth** for downstream paper generation. | SC‑001‑SC‑007 |
| **10 – Artifact Generation & Validation** | Save processed dataset (`data/processed/tribology_dataset.parquet`), model checkpoints (`models/*.pkl`), and contract‑validated schema files. Compute checksums (`data/raw/checksums.txt`). Run contract test against `contracts/tribology-dataset.schema.yaml`. | All FR/SC (ensures reproducibility & data hygiene) |

**Note**: Phase 0 is a hard gate. If the required open dataset cannot be accessed **or** lacks the required columns, the pipeline aborts with a clear `DataAvailabilityError`; the project owner must supply a verified open dataset before any downstream work proceeds.

---



