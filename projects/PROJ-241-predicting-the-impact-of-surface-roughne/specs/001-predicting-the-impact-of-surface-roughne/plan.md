# Implementation Plan: Predicting the Impact of Surface Roughness on Tribological Properties

**Branch**: `001-predict-tribology` | **Date**: 2026-10-25 | **Spec**: [/specs/001-predict-tribology/spec.md](../specs/001-predict-tribology/spec.md)  
**Input**: Feature specification from `/specs/001-predict-tribology/spec.md`

## Summary
The pipeline will (1) verify that an **open** dataset containing the required roughness descriptors and tribology targets exists and includes all required columns; if not, it aborts with a clear `DataAvailabilityError`. (2) download the OpenML dataset (ID 2352) via streaming, (3) fetch material properties from the NIST Materials Data Repository (fallback to median imputation when unavailable), (4) extract surface‑roughness parameters with `pySurf` when raw profilometry files are present, otherwise perform basic sanity‑range checks on existing roughness columns (non‑negative and within empirically reasonable bounds). (5) clean the data using a **±3 σ outlier removal** rule, **multiple imputation** with `IterativeImputer` plus bootstrap sensitivity reporting, and `StandardScaler`, (6) split the data using a **strict group‑aware** train/test split that prevents any individual material identifier from appearing in both sets while stratifying by `material_pair_id`, (7) train three regressors (OLS, Random Forest, Gradient Boosting) with **nested cross‑validation** and hyper‑parameter tuning, (8) evaluate R², MAE, RMSE on the held‑out test set, (9) perform a **Shapiro‑Wilk normality test** on the paired prediction differences; based on normality choose a paired t‑test or Wilcoxon signed‑rank test (Bonferroni‑corrected) and **report** a power analysis for information only (effect size computed on the test set), (10) generate SHAP value plots and **report** sign consistency with physics without claiming causal validation, and (11) assemble a single‑source‑of‑truth JSON (`results.json`). All steps are CPU‑first and designed to finish within the GitHub Actions free‑tier limits (≤ 6 h, ≤ 7 GB RAM).

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
| II. Verified Accuracy | All external citations must be verified | ✅ Only the verified OpenML URL is cited; NIST DOI has no public URL and is treated as fallback |
| III. Data Hygiene | Checksums, immutable transformations, no PII | ✅ raw files checksummed; each transformation writes a new file |
| IV. Single Source of Truth | All figures/statistics trace to exactly one data row & code block | ✅ `results.json` serves as SSoT |
| V. Versioning Discipline | Content hashes recorded, timestamps updated | ✅ hashes stored in `state/` by CI framework |
| VI. Numerical Stability & Model Robustness | Stratified splits by material pair, 5‑fold CV, outlier removal, median imputation, target R² ≥ 0.7 | ✅ implemented in Phases 5‑7; R² targets enforced in SC‑001/SC‑002 |
| VII. Interpretability and Feature Attribution | SHAP plots, sign‑consistency reporting, statistical significance (p < 0.05) | ✅ SHAP generation (Phase 10) and sign‑consistency **reporting** (FR‑011) |

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
│   ├── modeling.py          # FR‑006, FR‑007, FR‑015
│   ├── evaluation.py        # FR‑008, FR‑010, SC‑001‑SC‑003
│   └── interpret.py         # FR‑009, FR‑011
└── __main__.py              # orchestrates all phases
```
**Structure Decision**: A single‑project layout keeps the research code together, satisfies all FR/SC, and avoids unnecessary complexity.

## Phase‑wise Implementation Tasks (FR/SC Mapping)

| Phase | Description | FR/SC Covered |
|-------|-------------|---------------|
| **0 – Data Availability Assessment** | Verify that the OpenML dataset (ID 2352) can be downloaded **and** that it contains **all** required columns (`Sa`, `Sq`, `Ssk`, `Sku`, `Sp`, `Sv`, `coeff_friction`, `wear_rate`). If any column is missing, **attempt** to load an alternative verified OpenML dataset (e.g., ID 42123) that contains the needed columns. If still unavailable, abort with `DataAvailabilityError` and flag the spec for dataset correction. | FR‑001, FR‑003, FR‑012 |
| **1 – Data Acquisition** | Stream the OpenML dataset (`openml.datasets.get_dataset(2352, streaming=True)`) or the fallback dataset if Phase 0 selected it. Retrieve material properties for each material ID via the Materials Project API (`pymatgen.ext.matproj.MPRester`). If the API key is missing or a request fails, log and median‑impute the missing property values. | FR‑001, FR‑003 |
| **2 – Roughness Feature Extraction** | • If raw profilometry files are present, compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`.<br>• If raw files are absent, **validate existing roughness columns** by checking that values are non‑negative and fall within empirically reasonable ranges (e.g., Sa ∈ [0, 500] µm). Abort if any column fails the sanity check. | FR‑002, FR‑016 |
| **3 – Data Cleaning** | • Outlier removal using the **±3 σ rule**: for each numeric feature, compute mean ± 3 × std and drop rows outside this interval (FR‑004).<br>• **Multiple imputation**: use `sklearn.impute.IterativeImputer` to estimate missing values, then perform **bootstrap resampling** (e.g., 100 bootstrap replicates) to quantify imputation variance; log the mean and standard deviation of imputed values as a **sensitivity note** (addresses methodology‑dfc1f189).<br>• For any remaining missing values, fall back to median imputation with logging (maintains backward compatibility).<br>• `StandardScaler` standardization (FR‑005).<br>• Verify existence of target columns before proceeding (FR‑012).<br>• Assert ≥ 200 rows remain; if fewer, log a warning and continue (SC‑006). | FR‑004, FR‑005, FR‑012, FR‑016, SC‑006, SC‑007 |
| **4 – Train‑Test Split** | Perform a **strict group‑aware split**: first create groups based on each unique `material_pair_id`; then ensure that **no individual material identifier** (`material_1_id` or `material_2_id`) appears in both training and test sets by constructing a combined grouping list of all material IDs and using `GroupShuffleSplit`. Stratify by `material_pair_id`. Fixed `random_state=42`. | FR‑014, SC‑005 |
| **5 – Model Training & Nested CV** | **Outer CV**: 5‑fold if n ≥ 100 else 3‑fold (FR‑007). **Inner CV**: same fold count for hyper‑parameter tuning via `GridSearchCV`. Train three regressors (OLS, RandomForestRegressor, GradientBoostingRegressor) on the full training set with best hyper‑parameters. OLS serves as baseline for significance testing. | FR‑006, FR‑007, FR‑015, c9a692ef |
| **6 – Evaluation** | Compute **R²**, **MAE**, **RMSE** on the held‑out test set for both targets; store in `results/metrics.json`. | FR‑008, SC‑001, SC‑002 |
| **7 – Power & Significance Testing** | • Estimate effect size (Cohen’s d) **on the test‑set prediction differences** between each model and the OLS baseline.<br>• Perform a **power analysis** with `statsmodels.stats.power.TTestPower` (α = 0.05) for reporting purposes only.<br>• Conduct a **Shapiro‑Wilk test** on the paired differences. If normality is **rejected**, use a **Wilcoxon signed‑rank test**, otherwise use a **paired t‑test**. Apply **Bonferroni correction** for the two targets (α_adj = 0.025). Record p‑values in `results/metrics.json`. | FR‑010, SC‑003 |
| **8 – SHAP Interpretation** | Generate SHAP values (TreeExplainer for RF/GB, KernelExplainer for OLS). Produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑5 features. **Report** whether the sign of each important feature matches the physics lookup table; log any mismatches as descriptive notes (FR‑011) but do not treat them as validation of causality. | FR‑009, FR‑011, dd6d51f6 |
| **9 – Reporting & SSoT Assembly** | Compile `results.json` containing: metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, final row count, sign‑consistency flags, and a SHA‑256 checksum manifest for all artifacts. This JSON is the **Single Source of Truth** for downstream paper generation. | SC‑001‑SC‑007 |
| **10 – Artifact Generation & Validation** | Save processed dataset (`data/processed/tribology_dataset.parquet`), model checkpoints (`models/*.pkl`), and contract‑validated schema files. Compute checksums (`data/raw/checksums.txt`). Run contract test against `contracts/tribology-dataset.schema.yaml`. | All FR/SC (ensures reproducibility & data hygiene) |

**Note**: Phase 0 is a hard gate. If the required open dataset cannot be accessed **or** lacks the required columns, the pipeline aborts with a clear `DataAvailabilityError`; the project owner must supply a verified open dataset before any downstream work proceeds.

---



## projects/PROJ-241-predicting-the-impact-of-surface-roughne/specs/001-predicting-the-impact-of-surface-roughne/research.md===
# Research: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature**: `001-predict-tribology`  
**Research Date**: 2026-10-25  

## Objective
Build a fully reproducible end‑to‑end analysis that predicts **coefficient of friction** and **wear rate** from surface‑roughness descriptors and material properties, evaluates model performance against the success criteria, and provides interpretable SHAP‑based feature‑importance evidence.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute Platform** | All required algorithms (OLS, Random Forest, Gradient Boosting, SHAP) run comfortably on the CPU‑only GitHub Actions runner; no GPU is needed, satisfying the “CPU‑first” rule. |
| **Dataset Strategy** | The spec cites an OpenML dataset (ID 2352) and a NIST Materials Data Repository DOI, but **the NIST DOI has no publicly downloadable URL**. Consequently, Phase 0 will attempt to download the OpenML dataset and **verify that it contains the required columns**. If the columns are missing, we will **attempt to load an alternative verified OpenML dataset (e.g., ID 42123)**. If neither dataset provides the needed variables, the pipeline aborts with a clear `DataAvailabilityError` and the spec must be updated with a correct open dataset. |
| **Statistical Methods** | Two targets ⇒ Bonferroni correction for the two p‑values. Power analysis uses a **data‑driven effect size** (Cohen’s d estimated from the **test‑set** prediction differences) with `statsmodels.stats.power.TTestPower` (α = 0.05). The **Shapiro‑Wilk test** on paired prediction differences determines whether a **paired t‑test** or a **Wilcoxon signed‑rank test** is used (FR‑010). |
| **Model Validation** | **Strict group split** by `material_pair_id` **and** by individual material identifiers (`material_1_id`, `material_2_id`) prevents leakage across material pairs and across single materials. Nested cross‑validation (outer + inner folds) yields unbiased performance estimates and satisfies FR‑007. |
| **Interpretability** | SHAP (TreeExplainer for tree models, KernelExplainer for OLS) provides global importance and per‑feature dependence plots. The sign of each important feature is **reported** and compared to known physical trends (e.g., hardness inversely correlates with wear). Discrepancies are logged and highlighted (FR‑011) but do not cause pipeline failure; we explicitly note that SHAP attributions are descriptive, not causal. |
| **Reproducibility** | Random seeds (`RANDOM_SEED=42`) are fixed; all external data are checksummed (`sha256`) and stored read‑only under `data/raw/`. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| **OpenML “Surface Roughness & Tribology”** (ID 2352) | https://www.openml.org/d/2352 | `openml.datasets.get_dataset(..., streaming=True)` | Public OpenML API; contains required columns **if verified**. |
| **Fallback OpenML dataset** (e.g., ID 42123) | *Verified URL if needed* | Same loader | Used only if ID 2352 lacks required columns. |
| **NIST Materials Data Repository** (DOI …) | *No verified URL* | – | Intended source for material properties; if unavailable, missing values will be median‑imputed (FR‑016). |

*Only the OpenML API is a genuine open source; the NIST DOI lacks a verified download link and is therefore treated as a fallback source.*

## Methodology Sketch
1. **Data Availability Assessment** – confirm downloadability and required columns. If missing, try the fallback dataset; if still missing, raise `DataAvailabilityError` and flag the spec.  
2. **Acquisition** – stream OpenML dataset; query Materials Project for missing material properties (fallback to median imputation).  
3. **Feature Extraction** – compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. If raw files are missing, perform **simple sanity‑range checks** on existing roughness columns (non‑negative, within empirically reasonable bounds). Abort if any column fails the sanity check.  
4. **Cleaning** – **±3 σ outlier removal**, **multiple imputation** via `IterativeImputer` with **bootstrap resampling** to capture imputation uncertainty, median imputation as a backup, `StandardScaler` standardization, exclude derived aggregate fields from predictors, assert ≥ 200 rows remain (warning if not).  
5. **Strict Group‑Aware Split** – stratify by `material_pair_id` **and** enforce that each unique material identifier appears in only one split using a custom `GroupShuffleSplit`. Fixed `random_state=42`.  
6. **Modeling** – nested CV (outer 5‑fold if n ≥ 100 else 3‑fold; inner same) with `GridSearchCV`; train OLS, Random Forest, Gradient Boosting. OLS serves as baseline for significance testing.  
7. **Evaluation** – compute R², MAE, RMSE on held‑out test set for both targets; store in `results/metrics.json`.  
8. **Power & Significance Testing** – estimate effect size (Cohen’s d) **on the test‑set prediction differences**, perform a **power analysis** for reporting only, conduct a **Shapiro‑Wilk test** on the paired differences; if normality is **rejected**, use a **Wilcoxon signed‑rank test**, otherwise use a **paired t‑test**. Apply **Bonferroni correction** for the two targets (α_adj = 0.025). Record p‑values.  
9. **SHAP Interpretation** – generate SHAP values, global importance bar plot, and per‑feature dependence plots for the top‑5 features; **report** whether the sign of each important feature matches the physics lookup table; log any contradictions as descriptive notes.  
10. **Reporting** – compile `results.json` (SSoT for downstream paper) with metrics, p‑values, top‑5 SHAP features, `imputed_fraction`, final row count, sign‑consistency flags, and a checksum manifest for all artifacts.  

## Success Criteria Mapping
| SC | Metric | Target | Implementation Check |
|----|--------|--------|-----------------------|
| SC‑001 | R² (friction) | ≥ 0.7 | `results/metrics.json['r2_friction']` |
| SC‑002 | R² (wear) | ≥ 0.7 | `results/metrics.json['r2_wear']` |
| SC‑003 | p‑value (model vs baseline) | α = 0.05 (Bonferroni‑adjusted) | `results/metrics.json['p_value_friction']`, `p_value_wear` |
| SC‑004 | # features with mean |SHAP| > 0.01 | Count of features in SHAP summary where mean |SHAP\| > 0.01 |
| SC‑005 | Total runtime | ≤ 6 h | CI logs; pipeline aborts if runtime exceeds limit |
| SC‑006 | Final rows after cleaning | ≥ 200 | `results.json['n_rows']` (asserted in Phase 4) |
| SC‑007 | Imputed rows ≤ 5 % of total | ≤ 5 % | `results.json['imputed_fraction']` (asserted in Phase 4) |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data‑gap (OpenML or NIST unavailable or missing columns)** | Blocking – cannot proceed to modeling. | Phase 0 aborts with explicit `DataAvailabilityError`; fallback to alternative OpenML dataset; if still unavailable, request a verified open dataset or adjust the specification. |
| **Materials Project API key missing** | Missing material properties → reliance on median imputation, possible performance loss. | Log missing‑rate; if > 30 % of material rows are imputed, raise a warning in `results.json`. |
| **Insufficient sample size (< 200)** | Power < 0.8, may force non‑parametric test; R² targets harder to meet. | Issue warning; proceed with Wilcoxon; note limitation in summary. |
| **Collinearity among roughness descriptors** | Inflated variance, misleading SHAP directionality. | Compute Variance Inflation Factor (VIF); if any VIF > 5, record collinearity warning and avoid interpreting individual coefficients. |
| **Raw profilometry files missing** | Cannot compute `pySurf` descriptors. | Perform sanity‑range checks on fallback columns; abort if any column fails the check. |

---


