# Implementation Plan: Predicting the Impact of Surface Roughness on Tribological Properties

**Branch**: `001-predict-tribology` | **Date**: 2026-10-11 | **Spec**: [/specs/001-predict-tribology/spec.md](../specs/001-predict-tribology/spec.md)  
**Input**: Feature specification from `/specs/001-predict-tribology/spec.md`

## Summary
The feature requires a reproducible pipeline that (1) acquires surface‑roughness measurements and material‑property data, (2) builds a clean, standardized dataset, (3) trains three regression models (OLS, Random Forest, Gradient Boosting) with nested CV‑based hyper‑parameter tuning, (4) evaluates performance against R² ≥ 0.7 targets, (5) conducts statistical significance testing versus a linear baseline, and (6) produces SHAP‑based feature‑importance visualizations that are cross‑checked with known physical trends.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `pySurf`, `shap`, `matplotlib`, `requests`, `statsmodels`, `openml`, `pymatgen` (Materials Project API client)  
- **Storage**: File‑based CSV/Parquet under `data/`  
- **Testing**: `pytest` (unit & contract tests)  
- **Target Platform**: Linux GitHub Actions runner (2 CPU cores, ~7 GB RAM) – all steps are CPU‑first; no GPU required.  
- **Project Type**: Research library / CLI pipeline  
- **Performance Goals**: End‑to‑end runtime ≤ 6 h on the CI runner (Constitution SC‑005).  
- **Constraints**: Must obey all Constitution principles (reproducibility, data hygiene, etc.).  
- **Scale/Scope**: Aim for the full OpenML dataset (≥ 200 rows) if available; otherwise process a verified open substitute.

## Constitution Check
| Principle | Requirement | Status / Action |
|-----------|-------------|-----------------|
| I. Reproducibility | Fixed random seeds, deterministic downloads | ✅ seeds pinned; download URLs validated |
| II. Verified Accuracy | All external citations must be verified | ✅ only verified dataset URLs used (see Research.md) |
| III. Data Hygiene | Checksums, immutable raw files, derivations versioned | ✅ will checksum raw files; each transformation writes new file |
| IV. Single Source of Truth | Every figure/statistic traces to exactly one data row | ✅ **SSoT**: `results/summary.json` is the authoritative source |
| V. Versioning Discipline | Content hashes for artifacts | ✅ will generate hashes in `state/` |
| VI. Numerical Stability & Model Robustness | **Group splits by material identifiers**, CV, outlier removal (±3σ), median imputation | ✅ implemented per FR‑004, FR‑005, FR‑007, FR‑013 with robust methods |
| VII. Interpretability & Feature Attribution | SHAP plots, statistical significance (p < 0.05) | ✅ SHAP generation (FR‑009) and paired test (FR‑010) |

*All principles are satisfied provided the required datasets can be fetched. The lack of a verified OpenML source (FR‑001) is a **data‑gap** that aborts the pipeline before Phase 0; the specification must be revised to point to an open, verified dataset that includes the required roughness descriptors and target variables.*

## Project Structure
```text
specs/001-predict-tribology/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── tribology-dataset.schema.yaml
```
```text
src/
├── pipeline/
│   ├── download.py          # dataset acquisition
│   ├── preprocess.py        # feature extraction, imputation, scaling, robust outlier removal
│   ├── modeling.py          # nested CV, training, hyper‑tuning
│   ├── evaluation.py        # metrics, power analysis, significance tests
│   └── interpret.py         # SHAP analysis
tests/
├── contract/
│   └── test_dataset_schema.py
└── unit/
    └── test_preprocess.py
```
**Structure Decision**: A single‑project layout is sufficient; all research code lives under `src/pipeline/`.

## Phase‑wise Implementation Tasks (maps to FR/SC)

| Phase | Description | FR/SC Covered |
|-------|-------------|---------------|
| **0 – Data Availability Assessment** | Verify that the OpenML dataset ID 42123 (or an alternative open dataset) is publicly downloadable and contains all required columns. If unavailable, raise a `DataAvailabilityError` and abort. | FR‑001, FR‑003 |
| **1 – Data Acquisition** | • Stream OpenML dataset via `openml.datasets.get_dataset(42123, download_all_files=True, streaming=True)`.  <br>• Query Materials Project API for missing material properties; fallback to median imputation if API key missing or request fails. | FR‑001, FR‑003 |
| **2 – Feature Extraction** | Require raw profilometry files; compute Sa, Sq, Ssk, Sku, Sp, Sv with `pySurf`. **If raw files are missing, abort with an informative error** (no silent fallback). | FR‑002 |
| **3 – Data Cleaning** | • Outlier removal using the **±3σ method** as mandated by FR‑004 (with a diagnostic check of feature skewness; if absolute skewness > 2, emit a warning). <br>• Median imputation for any remaining missing values (FR‑001/FR‑012). <br>• `StandardScaler` on all numeric columns. | FR‑004, FR‑005, FR‑012 |
| **4 – Train‑Test Split** | Perform a **group split** by the combination of `material_1_id` and `material_2_id` using `GroupKFold` (ensuring no material appears in both train and test). Use a fixed random seed (42). Record split metadata. | FR‑006, SC‑005, VI (robustness) |
| **5 – Model Training & Nested CV** | • **Outer CV** (3‑fold if n < 100 else 5‑fold) provides unbiased performance estimates. <br>• **Inner CV** (same fold count) tunes hyper‑parameters via `GridSearchCV`. <br>• Train final models (OLS, Random Forest, Gradient Boosting) on the full training set with best hyper‑parameters. <br>• **Exclude derived fields** (`avg_hardness`, `avg_modulus`, `hardness_modulus_ratio_avg`) from the predictor set to avoid multicollinearity. | FR‑006, FR‑007, FR‑013, scientific_soundness-e7fc04b0 |
| **6 – Evaluation** | Compute R², MAE, RMSE on the held‑out test set for each target (FR‑008). Record metrics in `results/metrics.json`. | FR‑008 |
| **7 – Power Analysis & Significance Test** | Perform power analysis using `statsmodels.stats.power.TTestPower` with **effect size ΔR² = 0.10**, α = 0.05 (two‑tailed). If power < 0.8 **or** n < 200, use **Wilcoxon signed‑rank test**; otherwise use **paired t‑test**. Apply **Bonferroni correction** for the two targets. Record p‑values. The power threshold governs test choice **only**; runtime SC‑005 remains a separate success criterion. | FR‑010, SC‑003 |
| **8 – SHAP Interpretation** | Generate SHAP values (TreeExplainer for RF/GB, KernelExplainer for OLS). Produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑ranked features. Validate directionality against known physics (hardness ↘ wear, etc.); flag any contradictions. | FR‑009, FR‑011, SC‑004 |
| **9 – Reporting** | Assemble a JSON summary (`results/summary.json`) containing metrics, p‑values, top‑5 features, and any flagged discrepancies. This file serves as the **SSoT** for downstream paper generation. | SC‑001, SC‑002, SC‑003, SC‑004 |
| **10 – Artifact Generation** | Save processed dataset (`data/processed/tribology_dataset.parquet`), model checkpoints (`models/*.pkl`), and contract‑validated schema files. All artifacts are checksummed and version‑hashed. | All FR/SC (ensures reproducibility & data hygiene) |

**Note**: Phase 0 is a gating step. If the OpenML dataset cannot be fetched from a verified source **or** does not contain the required columns, the pipeline aborts with a clear error and a “data‑gap” issue is raised for the project owner.

## Complexity Tracking
No constitution violations identified beyond the data‑availability gap (FR‑001). The gap is documented in Phase 0 and will be resolved before proceeding.

---



## projects/PROJ-241-predicting-the-impact-of-surface-roughne/specs/001-predicting-the-impact-of-surface-roughne/research.md
# Research: Predicting the Impact of Surface Roughness on Tribological Properties

**Feature**: `001-predict-tribology`  
**Research Date**: 2026‑10‑11  

## Objective
Create a reproducible end‑to‑end analysis that predicts coefficient of friction and wear rate from surface‑roughness descriptors and material properties, evaluates model performance against predefined success criteria, and supplies interpretable feature‑importance evidence.

## Decision / Rationale
| Decision | Rationale |
|----------|-----------|
| **Compute Platform** | All algorithms (OLS, Random Forest, Gradient Boosting, SHAP) run comfortably on the CPU‑only GitHub Actions runner. No GPU is required; we therefore stay on the CPU path for full reproducibility. |
| **Dataset Strategy** | The spec demands the OpenML dataset ID 42123 and material properties from the NIST Materials Data Repository. No verified download URL for either source is present in the “Verified datasets” block, and the OpenML catalogue does not contain a dataset with the required columns. Consequently, the pipeline **first performs a Data‑Availability Assessment (Phase 0)**. If the dataset cannot be fetched, the pipeline aborts with a clear “data‑gap” error and the project owner must provide an alternative open, verified dataset that includes the required roughness descriptors and target variables. |
| **Statistical Methods** | Since we evaluate two targets, we apply **Bonferroni correction** to the two p‑values (model vs baseline for each target). Power analysis uses `statsmodels.stats.power.TTestPower` with **effect size ΔR² = 0.10**, α = 0.05 (two‑tailed). If power < 0.8 **or** n < 200, we use the **Wilcoxon signed‑rank test** per FR‑010. The power threshold governs test choice **only**; runtime SC‑005 remains a separate success metric. |
| **Model Validation** | **Group‑split** by `material_1_id` + `material_2_id` ensures no material appears in both train and test sets (Constitution VI). Nested CV (outer + inner folds) provides unbiased performance estimates and prevents optimistic bias. |
| **Interpretability** | SHAP (TreeExplainer for RF/GB, KernelExplainer for OLS) will produce global importance plots and per‑feature dependence plots. We will compare the sign of each SHAP mean effect with known physical expectations (e.g., hardness ↘ wear rate). Discrepancies will be logged and highlighted. |
| **Reproducibility** | Random seeds (`numpy`, `sklearn`) are set to a fixed value for reproducibility. All external data are checksummed (`sha256`) and stored under `data/raw/`. |

## Dataset Strategy
| Source | Verified URL | Loader | Notes |
|--------|--------------|--------|-------|
| **OpenML “Surface Roughness & Tribology”** (ID 42123) | *None provided in verified list* | `openml.datasets.get_dataset(42123, download_all_files=True, streaming=True)` | Public OpenML API; will be attempted. If unavailable, pipeline aborts with “data‑gap”. |
| **NIST Materials Data Repository** | *None provided in verified list* | – | No verified source; material properties will be fetched via the Materials Project API when possible; otherwise median‑imputed. |
| **Materials Project API** | Requires API key (not publicly available) | `pymatgen.ext.matproj.MPRester` | Attempted; if key missing or request fails, fallback to median imputation. |

*Only the OpenML API is considered a genuine open source; the other two are noted as unavailable.*

## Methodology Sketch
1. **Data Acquisition** – Phase 0 verifies downloadability; Phase 1 streams the OpenML dataset.  
2. **Feature Extraction** – Requires raw profilometry files; `pySurf` computes Sa, Sq, Ssk, Sku, Sp, Sv. **If raw files are missing, the pipeline aborts with an informative error** (no silent fallback).  
3. **Material Property Retrieval** – For each `material_id`, query Materials Project; if no response, log and impute median.  
4. **Cleaning** – **Outlier removal using the ±3σ method** (as mandated by FR‑004) with a diagnostic skewness check; if |skewness| > 2, a warning is logged. <br>• Median imputation for any remaining missing values. <br>• `StandardScaler` on all numeric columns.  
5. **Splitting** – **Group split** by material identifiers (`material_1_id` + `material_2_id`) using `GroupKFold` (ensuring no leakage). Random seed = 42.  
6. **Modeling** – **Nested cross‑validation**: outer CV (3‑fold if n < 100 else 5‑fold) for unbiased performance; inner CV (same fold count) for hyper‑parameter tuning via `GridSearchCV`. Train OLS, Random Forest, Gradient Boosting on the full training set with best hyper‑parameters. **Exclude derived fields** (`avg_hardness`, `avg_modulus`, `hardness_modulus_ratio_avg`) from the predictor set.  
7. **Evaluation** – Compute R², MAE, RMSE on held‑out test set for each target. Record metrics in `results/metrics.json`.  
8. **Power & Significance** – Power analysis (effect size = 0.10, α = 0.05) → choose paired t‑test if power ≥ 0.8 and n ≥ 200, otherwise Wilcoxon signed‑rank test. Apply **Bonferroni correction** for the two targets; store p‑values.  
9. **SHAP Interpretation** – Generate SHAP values, produce global importance bar plot (`figures/shap_importance.png`) and per‑feature dependence plots for the top‑5 features. Validate directionality against known physics (hardness ↘ wear, etc.); flag any contradictions.  
10. **Reporting** – Assemble a JSON summary (`results/summary.json`) containing metrics, p‑values, top‑5 features, and any flagged discrepancies. This file serves as the **SSoT** for downstream paper generation.

## Success Criteria Mapping
| SC | Metric | Target | Implementation Check |
|----|--------|--------|-----------------------|
| SC‑001 | R² (friction) | ≥ 0.7 | `results/metrics.json['r2_friction']` |
| SC‑002 | R² (wear) | ≥ 0.7 | `results/metrics.json['r2_wear']` |
| SC‑003 | p‑value (model vs baseline) | α = 0.05 (Bonferroni‑adjusted) | `results/metrics.json['p_value']` |
| SC‑004 | # of features with mean |SHAP| > 0.01 | Count in SHAP summary |
| SC‑005 | Total runtime | ≤ 6 h | Measured via CI logs; abort if exceeded |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Data‑gap (OpenML unavailable)** | Blocking – cannot proceed to modeling. | Early gate (Phase 0) aborts with clear error; request alternative open dataset or provide verified URL. |
| **Materials Project API key missing** | Missing material properties → imputation may degrade performance. | Median imputation fallback, log missing‑rate; if > 30 % missing, flag for dataset revision. |
| **Insufficient sample size (< 200)** | Power < 0.8, may force non‑parametric test; R² targets harder to meet. | Issue warning; proceed with Wilcoxon; note limitation in `results/summary.json`. |
| **Collinearity among roughness descriptors** | Inflated variance, misleading SHAP directionality. | Compute VIF; if VIF > 5, report collinearity in `results/summary.json` and avoid interpreting individual coefficients. |

---



## projects/PROJ-241-predicting-the-impact-of-surface-roughne/specs/001-predicting-the-impact-of-surface-roughne/quickstart.md
# Quickstart: Predicting Tribological Properties from Surface Roughness

This guide walks you through running the full analysis on a fresh GitHub Actions runner (or locally on Linux/macOS). **Prerequisite:** a publicly reachable OpenML dataset ID 42123 and optional Materials Project API key (set as `MATERIALS_PROJECT_API_KEY` env var). If the dataset cannot be fetched, the pipeline will stop with a clear “data‑gap” error.

## 1. Clone the repository and install dependencies
```bash
git clone https://github.com/your-org/tribology-prediction.git
cd tribology-prediction
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Set optional environment variables
```bash
export MATERIALS_PROJECT_API_KEY="your_api_key_here"   # optional
export RANDOM_SEED=42
```

## 3. Run the pipeline
```bash
python -m src.pipeline.run_all
```
`run_all` orchestrates the phases defined in `plan.md`:
1. **download** – streams OpenML dataset (Phase 0 & 1).  
2. **preprocess** – feature extraction, robust **±3σ** outlier removal, imputation, scaling (Phase 2‑3).  
3. **modeling** – nested cross‑validation, hyper‑parameter tuning, final model training (Phase 5).  
4. **evaluation** – metrics, power analysis, significance testing (Phase 6‑7).  
5. **interpret** – SHAP visualizations and directionality checks (Phase 8).

## 4. Inspect results
- Metrics: `results/metrics.json`
- SHAP plot: `figures/shap_importance.png`
- Summary JSON (ready for paper stage): `results/summary.json` **(the project's SSoT for results)**
- Checksums for raw files: `data/raw/checksums.txt`

## 5. Running unit / contract tests
```bash
pytest -q
```
All tests must pass; the contract test validates that `data/processed/tribology_dataset.parquet` satisfies `contracts/tribology-dataset.schema.yaml`.

## 6. Expected runtime
On the CI runner the full pipeline should complete well within the allocated time limit (SC‑005). If the dataset exceeds available memory, the pipeline automatically streams rows and never loads the entire file into RAM.

**Important:** If the OpenML dataset cannot be downloaded (no verified URL), the script will raise `DataAvailabilityError` and exit with a non‑zero error status. In that case, contact the project owner to provide a verified open dataset URL or adjust the specification accordingly.

---



## projects/PROJ-241-predicting-the-impact-of-surface-roughne/specs/001-predicting-the-impact-of-surface-roughne/contracts/tribology-dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Tribology Experiment Dataset"
description: "Schema for the processed tribology dataset used in the prediction pipeline."
type: object
additionalProperties: false
required:
  - experiment_id
  - pairing_id
  - material_1_id
  - material_2_id
  - Sa
  - Sq
  - Ssk
  - Sku
  - Sp
  - Sv
  - elastic_modulus_1
  - elastic_modulus_2
  - hardness_1
  - hardness_2
  - hardness_modulus_ratio_1
  - hardness_modulus_ratio_2
  - coeff_friction
  - wear_rate
properties:
  experiment_id:
    type: string
    description: "UUID for the experiment."
    pattern: "^[0-9a-fA-F-]{36}$"
  pairing_id:
    type: string
    description: "Identifier linking the two materials."
  material_1_id:
    type: string
    description: "Materials Project or NIST identifier for material 1."
  material_2_id:
    type: string
    description: "Materials Project or NIST identifier for material 2."
  Sa:
    type: number
    description: "Arithmetic mean surface height (µm)."
  Sq:
    type: number
    description: "Root‑mean‑square height (µm)."
  Ssk:
    type: number
    description: "Skewness of surface height distribution."
  Sku:
    type: number
    description: "Kurtosis of surface height distribution."
  Sp:
    type: number
    description: "Maximum peak height (µm)."
  Sv:
    type: number
    description: "Maximum valley depth (µm)."
  elastic_modulus_1:
    type: number
    description: "Elastic modulus of material 1 (GPa)."
  elastic_modulus_2:
    type: number
    description: "Elastic modulus of material 2 (GPa)."
  hardness_1:
    type: number
    description: "Hardness of material 1 (HV)."
  hardness_2:
    type: number
    description: "Hardness of material 2 (HV)."
  hardness_modulus_ratio_1:
    type: number
    description: "Hardness divided by elastic modulus for material 1."
  hardness_modulus_ratio_2:
    type: number
    description: "Hardness divided by elastic modulus for material 2."
  coeff_friction:
    type: number
    description: "Measured coefficient of friction (dimensionless)."
  wear_rate:
    type: number
    description: "Wear rate (mm³ N⁻¹ m⁻¹)."
  avg_hardness:
    type: number
    description: "Mean hardness of the two materials."
  avg_modulus:
    type: number
    description: "Mean elastic modulus of the two materials."
  hardness_modulus_ratio_avg:
    type: number
    description: "Mean hardness‑to‑modulus ratio across the pair."