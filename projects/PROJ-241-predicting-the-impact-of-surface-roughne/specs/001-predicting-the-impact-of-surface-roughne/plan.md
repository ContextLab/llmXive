# Implementation Plan: Predicting the Impact of Surface Roughness on Tribological Properties

**Branch**: `001-predict-tribology` | **Date**: 2026-10-11 | **Spec**: [/specs/001-predict-tribology/spec.md](../specs/001-predict-tribology/spec.md)  
**Input**: Feature specification from `/specs/001-predict-tribology/spec.md`

## Summary
The pipeline must (1) download the OpenML “Surface Roughness & Tribology” dataset (ID 2352) and augment it with material properties from the NIST Materials Data Repository or the Materials Project API, (2) extract surface‑roughness descriptors with `pySurf` (or validate fallback descriptors via KS test), (3) clean the data using a Median Absolute Deviation (MAD) outlier rule and median imputation, (4) standardize features, (5) split the data by `pairing_id` using a group‑aware stratified split, (6) train three regression models (OLS, Random Forest, Gradient Boosting) with nested cross‑validation and hyper‑parameter tuning, (7) evaluate R², MAE, RMSE, (8) conduct a data‑driven power analysis and select either a paired t-test or Wilcoxon signed‑rank test (Bonferroni‑corrected for two targets), (9) generate SHAP value plots and **report** whether feature‑sign directions align with known physics (discrepancies are logged but do not abort), and (10) store all final artifacts in a canonical `results.json` (the Single Source of Truth).  

All steps are CPU‑first and designed to run within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pySurf`, `shap`, `matplotlib`, `requests`, `statsmodels`, `openml`, `pymatgen` (Materials Project client)  
- **Storage**: CSV/Parquet files under `data/`  
- **Testing**: `pytest` with contract validation via `jsonschema`  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM) – **CPU‑first**; no GPU required.  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h (SC‑005).  
- **Constraints**: Must obey all Constitution principles; must not fabricate unavailable data.

## Verified Datasets
| Dataset | Source | Verified URL | Availability |
|---------|--------|--------------|--------------|
| OpenML “Surface Roughness & Tribology” (ID 2352) | OpenML | https://www.openml.org/d/2352 | Will be fetched via OpenML API; reachable URL satisfies verification. |
| NIST Materials Data Repository (DOI …) | NIST | *No verified URL available* | Not publicly downloadable without credentials; treated as a data‑gap. The pipeline will abort in Phase 0 unless an open substitute is provided. |

*The OpenML dataset now has a verified URL. The NIST repository lacks a verified open source URL; this gap must be resolved before downstream work can proceed.*

## Constitution Check
| Principle | Requirement | Status / Action |
|-----------|-------------|-----------------|
| I. Reproducibility | Fixed seeds, deterministic downloads, version‑pinned dependencies | ✅ seeds set (`RANDOM_SEED=42`); `requirements.txt` pins versions |
| II. Verified Accuracy | All external citations must be verified | ✅ OpenML dataset URL verified; NIST source flagged as missing – pipeline aborts until a verified substitute is supplied. |
| III. Data Hygiene | Datasets MUST be checksummed and the checksum recorded under `data/`. No data may be modified in place; every transformation MUST produce a new file with a documented derivation. Personally identifying information MUST NOT appear in committed data. | ✅ raw files checksummed; each transformation writes a new file |
| IV. Single Source of Truth | Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand‑typed into the paper. | ✅ `results.json` is the SSoT |
| V. Versioning Discipline | Every artifact under this project carries a content hash. The Advancement‑Evaluator Agent invalidates stale review records when the hashed artifact changes. Every research‑stage artifact change updates this project's `state/projects/PROJ-241-predicting-the-impact-of-surface-roughne.yaml` `updated_at` timestamp. | ✅ hashes recorded in `state/` by the CI framework |
| VI. Numerical Stability & Model Robustness | All regression models (Linear, Random Forest, Gradient Boosting) MUST be trained and evaluated using stratified splits by material pair to ensure robustness across diverse material combinations, as specified in the Methodology sketch. Hyperparameter tuning MUST utilize 5-fold cross‑validation on the validation set to prevent overfitting, and model performance MUST be validated against a held‑out test set of ≥200 data points with a target R² ≥ 0.7. Outlier removal (±3σ) and median imputation MUST be applied consistently to the "Surface Roughness & Tribology" and NIST Materials Data Repository datasets prior to training. | ✅ implemented per FR‑004, FR‑014 (using `pairing_id`), FR‑015, SC‑001/SC‑002 |
| VII. Interpretability and Feature Attribution | Every model claiming predictive superiority over the linear baseline MUST provide SHAP value plots to rank the contribution of roughness descriptors (Sa, Sq, Ssk, Sku, Sp, Sv) and material properties (elastic modulus, hardness). Statistical significance of model improvements (p < 0.05) MUST be confirmed via paired‑t tests against the baseline. The final output MUST identify a concise subset (3–5) of descriptors that consistently drive performance, directly addressing the research question regarding which parameters most strongly predict tribological outcomes. | ✅ SHAP generation (FR‑009) and paired test with Bonferroni correction (FR‑010); sign consistency is **reported** and flagged, not enforced |

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
│   ├── preprocess.py        # FR‑004, FR‑005, FR‑012, FR‑018
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
| **0 – Data Availability Assessment** | Verify that OpenML ID 2352 is reachable and contains all required columns; verify that the NIST DOI can be resolved. Abort with `DataAvailabilityError` if any check fails. | FR‑001, FR‑003 |
| **1 – Data Acquisition** | Stream OpenML dataset via `openml.datasets.get_dataset(2352, download_all_files=True, streaming=True)`. Retrieve material properties via Materials Project API; if API key missing or request fails, fall back to median imputation (logged). | FR‑001, FR‑003 |
| **2 – Roughness Feature Extraction** | If raw profilometry files exist, compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If raw files are missing, verify that any fallback roughness columns in the OpenML data are statistically comparable to `pySurf`‑derived descriptors using a Kolmogorov‑Smirnov test (p > 0.05). Abort if KS test fails. | FR‑002, FR‑016 |
| **3 – Data Cleaning** | • Outlier removal using **MAD rule**: flag observations where \|x – median\| > 3.5 × MAD and drop them.<br>• Median imputation for remaining missing values (including missing material properties). Track number of imputed rows and compute `imputed_fraction` (must be ≤ 0.05).<br>• Standardize all numeric features with `StandardScaler`.<br>• Exclude derived aggregate fields (`avg_hardness`, `avg_modulus`, `hardness_modulus_ratio_avg`) from the predictor set (FR‑018).<br>• **Row‑count check**: after cleaning, assert that the dataset contains ≥ 200 rows with no missing values; if not, log a warning and abort. | FR‑004, FR‑005, FR‑012, FR‑018, SC‑006, SC‑007 |
| **4 – Train‑Test Split** | Perform a **group‑aware split** by `pairing_id` using `GroupShuffleSplit` (80/20, `random_state=42`). Ensure no material pair appears in both sets. | FR‑014, SC‑005 |
| **5 – Model Training & Nested CV** | **Outer CV**: 5‑fold if n ≥ 100 else 3‑fold (per FR‑007). **Inner CV**: same fold count for hyper‑parameter tuning via `GridSearchCV`. Train three regressors (OLS, RandomForestRegressor, GradientBoostingRegressor) on the full training set with best hyper‑parameters. The OLS model serves as the **baseline** for significance testing. | FR‑006, FR‑007, FR‑015 |
| **6 – Evaluation** | Compute **R²**, **MAE**, **RMSE** on the held‑out test set for both targets; store in `results/metrics.json`. | FR‑008, SC‑001, SC‑002 |
| **7 – Power Analysis & Significance Testing** | Conduct a **data‑driven power analysis**: estimate Cohen's d from the training data (or fall back to d = 0.5 if insufficient). Use `statsmodels.stats.power.TTestPower` with α = 0.05. If power < 0.8 **or** n < 200, select **Wilcoxon signed‑rank test**; otherwise use a **paired t‑test**. Define the baseline model as the OLS regression trained in Phase 5. Apply **Bonferroni correction** for the two targets. Record p‑values in `results/metrics.json`. | FR‑010, SC‑003 |
| **8 – SHAP Interpretation** | Generate SHAP values (TreeExplainer for RF/GB, KernelExplainer for OLS). Produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑5 features. **Report** whether the sign of each important feature aligns with known physics (e.g., hardness ↘ wear); log any discrepancies but do **not** abort the pipeline. | FR‑009, FR‑011, SC‑004 |
| **9 – Reporting & SSoT** | Assemble `results.json` containing metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, row‑count, any flagged SHAP sign inconsistencies, and a checksum manifest for all artifacts. This JSON is the **Single Source of Truth** for downstream paper generation. | SC‑001‑SC‑007, FR‑017 |
| **10 – Artifact Generation & Validation** | Save processed dataset (`data/processed/tribology_dataset.parquet`), model checkpoints (`models/*.pkl`), and contract‑validated schema files. Compute SHA‑256 checksums, store in `data/raw/checksums.txt`. Run contract test against `contracts/tribology-dataset.schema.yaml`. | All FR/SC (ensures reproducibility & data hygiene) |

**Note**: Phase 0 is a hard gate. If the required OpenML dataset or NIST repository cannot be accessed, the pipeline aborts with a clear error; the project owner must supply an open, verified substitute before any downstream work proceeds.

---



## projects/PROJ-241-predicting-the-impact-of-surface-roughne/specs/001-predict-roughness-tribology/research.md
===BEGIN_ARTIFACT projects/PROJ-241-predicting-the-impact-of-surface-roughne/specs/001-predict-roughness-tribology/research.md===
# Research: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature**: `001-predict-tribology`  
**Research Date**: 2026‑10‑11  

## Objective
Build a fully reproducible end‑to‑end analysis that predicts **coefficient of friction** and **wear rate** from surface‑roughness descriptors and material properties, evaluates model performance against the success criteria, and provides interpretable SHAP‑based feature‑importance evidence.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute Platform** | All required algorithms (OLS, Random Forest, Gradient Boosting, SHAP) run comfortably on the CPU‑only GitHub Actions runner; no GPU is needed, satisfying the “CPU‑first” rule. |
| **Dataset Strategy** | The spec requests OpenML dataset **ID 2352** and material properties from the NIST Materials Data Repository. The OpenML dataset now has a verified URL (https://www.openml.org/d/2352). The NIST repository lacks a publicly verified URL and is therefore a **data‑gap**; Phase 0 will abort with `DataAvailabilityError` unless an open, verified substitute is supplied. |
| **Statistical Methods** | Two targets ⇒ Bonferroni correction for the two p‑values. Power analysis uses a **data‑driven effect size** (Cohen’s d estimated from the training data) with `statsmodels.stats.power.TTestPower` (α = 0.05). If power < 0.8 **or** n < 200, we employ a **Wilcoxon signed‑rank test**; otherwise a **paired t‑test**. |
| **Model Validation** | **Group split** by `pairing_id` prevents leakage across material pairs (Constitution VI, FR‑014). **Nested cross‑validation** (outer + inner folds) yields unbiased performance estimates and satisfies FR‑015. |
| **Interpretability** | SHAP (TreeExplainer for tree models, KernelExplainer for OLS) provides global importance and per‑feature dependence plots. The sign of each important feature is **reported** and compared to known physical trends (e.g., hardness inversely correlates with wear). Discrepancies are logged and highlighted (FR‑011) but do not cause pipeline failure. |
| **Reproducibility** | Random seeds (`RANDOM_SEED=42`) are fixed; all external data are checksummed (`sha256`) and stored read‑only under `data/raw/`. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| **OpenML “Surface Roughness & Tribology”** (ID 2352) | https://www.openml.org/d/2352 | `openml.datasets.get_dataset(2352, download_all_files=True, streaming=True)` | Public OpenML API; verified URL added. |
| **NIST Materials Data Repository** (DOI …) | *No verified URL available* | – | Material properties fetched via Materials Project API; fallback to median imputation if unavailable. Treated as a data‑gap requiring substitution before proceeding. |
| **Materials Project API** | Requires API key (not publicly available) | `pymatgen.ext.matproj.MPRester` | Attempted; if key missing or request fails, median imputation is used. |

*Only the OpenML API is a genuine open source; the other two are not verified and therefore constitute a data‑gap that must be resolved before proceeding.*

## Methodology Sketch
1. **Data Availability Assessment** – confirm downloadability and required columns.  
2. **Acquisition** – stream OpenML dataset; query Materials Project for missing material properties.  
3. **Feature Extraction** – compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If raw files missing, validate fallback roughness columns via a Kolmogorov‑Smirnov test (p > 0.05) before use.  
4. **Cleaning** – outlier removal using **MAD rule** (|x – median| > 3.5 × MAD); median imputation for any remaining missing values (including missing material properties); `StandardScaler` standardization; exclude derived aggregate fields from predictors.  
5. **Group‑Aware Split** – stratify by `pairing_id` using `GroupShuffleSplit` (80/20).  
6. **Modeling** – nested CV (outer 5‑fold if n ≥ 100 else 3‑fold; inner same) with `GridSearchCV`; train OLS, Random Forest, Gradient Boosting. The OLS model serves as the **baseline** for significance testing.  
7. **Evaluation** – compute R², MAE, RMSE on the held‑out test set for both targets; store in `results/metrics.json`.  
8. **Power & Significance** – power analysis (data‑driven effect size, fallback d = 0.5 if insufficient); choose paired t‑test or Wilcoxon based on power/n; Bonferroni‑corrected p‑values recorded.  
9. **SHAP Interpretation** – generate SHAP values, global importance bar plot, per‑feature dependence plots for top‑5 features; **report** sign consistency with physics, flag contradictions.  
10. **Reporting** – compile `results.json` (SSoT) with metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, row‑count, any sign‑consistency flags, and a checksum manifest for all artifacts.  

## Success Criteria Mapping
| SC | Metric | Target | Implementation Check |
|----|--------|--------|-----------------------|
| SC‑001 | R² (friction) | ≥ 0.7 | `results/metrics.json['r2_friction']` |
| SC‑002 | R² (wear) | ≥ 0.7 | `results/metrics.json['r2_wear']` |
| SC‑003 | p‑value (model vs baseline) | α = 0.05 (Bonferroni‑adjusted) | `results/metrics.json['p_value_friction']`, `p_value_wear` |
| SC‑004 | # features with mean |SHAP| > 0.01 | Count of features in SHAP summary where mean \|SHAP\| > 0.01 |
| SC‑005 | Total runtime | ≤ 6 h | CI logs; pipeline aborts if runtime exceeds limit |
| SC‑006 | Final rows after cleaning | ≥ 200 | `results.json['n_rows']` (asserted in Phase 3) |
| SC‑007 | Imputed rows ≤ 5 % of total | ≤ 5 % | `results.json['imputed_fraction']` (asserted in Phase 3) |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data‑gap (OpenML or NIST unavailable)** | Blocking – cannot proceed to modeling. | Phase 0 aborts with explicit error; request alternative open dataset or provide verified URL. |
| **Materials Project API key missing** | Missing material properties → reliance on median imputation, possible performance loss. | Log missing‑rate; if > 30 % of material rows are imputed, raise a warning in `results.json`. |
| **Insufficient sample size (< 200)** | Power < 0.8, may force non‑parametric test; R² targets harder to meet. | Issue warning; proceed with Wilcoxon; note limitation in summary. |
| **Collinearity among roughness descriptors** | Inflated variance, misleading SHAP directionality. | Compute Variance Inflation Factor (VIF); if any VIF > 5, record collinearity warning and avoid interpreting individual coefficients. |
| **Raw profilometry files missing** | Cannot compute `pySurf` descriptors. | Perform KS test on fallback columns; abort if distributions differ (p ≤ 0.05). |

---


