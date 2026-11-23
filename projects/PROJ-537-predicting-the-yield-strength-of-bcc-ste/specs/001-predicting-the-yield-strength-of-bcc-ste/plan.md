# Implementation Plan: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

**Branch**: `001-predict-yield-strength-bcc` | **Date**: 2026-10-15 | **Spec**: `specs/001-predict-yield-strength-bcc/spec.md`  
**Input**: Feature specification from `/specs/001-predict-yield-strength-bcc/spec.md`

## Summary
The project will (1) fetch **experimental BCC composition & yield‑strength data** from a **verified open MatNavi dataset**, (2) query the **Materials Project API** for DFT elastic constants, (3) merge the two datasets **only on rows where both sources provide non‑null values**, (4) train a **Random Forest** regressor with composition + DFT features and a composition‑only baseline, (5) evaluate performance with **5‑fold outer cross‑validation and 5‑fold inner hyper‑parameter search**, (6) compare models using a **paired t‑test** (with effect size and 95 % CI), (7) compute **statistical power** and report limitations if power < 0.8, (8) conduct **interpretability** (TreeSHAP, permutation importance) and **bootstrap stability** analyses, (9) **validate the merged dataset against `contracts/dataset.schema.yaml`**, (10) **write a single `output.json` that satisfies both `contracts/model_output.schema.yaml` and `contracts/output.schema.yaml`**, and (11) **document all provenance** for reproducibility.

All steps are **deterministically verifiable**:
- Real HTTP calls to the Materials Project API (no mock or fallback).  
- Real download of the experimental CSV from the verified MatNavi URL.  
- If the required experimental column is missing or the merged row count is **< 20**, the pipeline **halts with `ERR_INSUFFICIENT_DATA`** as mandated by FR‑001/FR‑002.  
- No synthetic data is generated at any stage.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scikit-learn==1.5.*`, `shap==0.45.*`, `mp-api==0.41.*`, `pyyaml==6.0.*`, `requests==2.32.*` (all CPU‑only wheels).  
- **Storage**: CSV/Parquet files under `data/` (`raw/`, `intermediate/`, `processed/`, `results/`).  
- **Testing**: `pytest` with contract validation (`jsonschema`).  
- **Target Platform**: Linux GitHub Actions free‑tier runner (2 CPU, ≈7 GB RAM, ≤6 h).  
- **Constraints**: No synthetic data, no GPU, strict API‑call provenance (Constitution VII).

## Constitution Check
| Principle | Requirement | Plan Compliance |
|-----------|-------------|-----------------|
| **I. Reproducibility** | Fixed random seeds; deterministic data fetches. | `np.random.seed(42); random.seed(42)` in `config.py`. All URLs and API parameters are hard‑coded. |
| **II. Verified Accuracy** | All citations must be to verified sources. | Only the verified MatNavi URL and Materials Project API are used. |
| **III. Data Hygiene** | Checksums, immutable raw files, new files for transformations. | `utils/checksums.py` computes SHA‑256 for every file; raw downloads are never overwritten. |
| **IV. Single Source of Truth** | Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. | All metrics are derived from `data/results/output.json`; each metric records the source row IDs. |
| **V. Versioning Discipline** | Content hashes recorded in project state. | `utils/checksums.py` writes hashes to `state/projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste.yaml`. |
| **VI. Statistical Significance** | Null hypothesis, test, p‑value, CI; p < 0.05 threshold. | Paired **t‑test**, 95 % CI for MAE difference, explicit null hypothesis description. |
| **VII. DFT Descriptor Provenance** | DFT data from Materials Project API; log query parameters. | `fetch_dft.py` logs API version, query JSON, and raw response to `data/provenance/dft_queries.jsonl`. |

## Project Structure
```text
specs/001-predict-yield-strength-bcc/
├─ plan.md
├─ research.md
├─ data-model.md
├─ quickstart.md
└─ contracts/
   ├─ dataset.schema.yaml
   ├─ model_output.schema.yaml
   └─ output.schema.yaml

code/
├─ __init__.py
├─ config.py                # seeds, API key handling
├─ ingestion/
│  ├─ fetch_experimental.py # download MatNavi CSV
│  ├─ fetch_dft.py          # Materials Project API queries
│  └─ merge_and_filter.py   # join, BCC filter, range handling, schema validation
├─ modeling/
│  ├─ features.py           # one‑hot element encoding, scaling, optional covariates
│  ├─ train.py              # nested CV, baseline vs DFT model
│  └─ evaluate.py           # metrics, paired t‑test, power analysis
├─ interpretability/
│  ├─ shap_analysis.py
│  ├─ permutation_importance.py
│  └─ bootstrap_stability.py
├─ utils/
│  ├─ logging.py
│  └─ checksums.py
├─ main.py                  # orchestrates the pipeline
└─ requirements.txt

data/
├─ raw/
├─ intermediate/
├─ processed/
├─ provenance/
└─ results/
   ├─ output.json
   └─ plots/
      ├─ shap_summary.png
      ├─ perm_importance.png
      └─ stability.png
```

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|------------|------------------------------|
| **Real API calls** (Constitution VII) | Must obtain DFT descriptors from Materials Project, not a static dump. | Using a pre‑downloaded DFT parquet would omit the required provenance log. |
| **No synthetic fallback** (FR‑001/FR‑002) | Spec explicitly forbids mock data. | Bundling a CSV with dummy rows violates the spec and caused the previous verification failure. |
| **Nested CV + Bootstrap** (FR‑004/FR‑007) | Provides unbiased performance estimates and stability metrics on the small dataset. | Simple hold‑out validation would inflate Type I error and miss SC‑004/SC‑005. |
| **Power analysis** (FR‑009) | Required to report limitation when n ≈ 20. | Skipping power analysis would breach SC‑008. |
| **VIF mitigation** (methodology‑ef15bb22) | High collinearity can distort importance scores. | Ignoring VIF would produce misleading interpretations. |

## Implementation Phases

### Phase 0 – Data Ingestion & Validation (Addresses FR‑001, FR‑002, FR‑003)
1. **Download experimental composition & yield strength**  
   - URL: `https://huggingface.co/datasets/matnavi/steel_yield_strength/resolve/main/data/steel_yield_strength.csv` (verified MatNavi dataset).  
   - Parse to extract `formula` and `yield_strength_MPa`. If the column is missing, log a warning and **halt with `ERR_INSUFFICIENT_DATA`** (per spec).  
2. **Query Materials Project API** (`mp-api` client) for each unique `formula`.  
   - Parameters: `fields=["material_id","formula","elasticity","spacegroup.number"]`.  
   - Filter `spacegroup.number == 229`.  
   - Retry up to **3** times with exponential backoff (2 s, 4 s, 8 s). Log each attempt to `data/provenance/dft_queries.jsonl`.  
   - If a composition yields no DFT record after retries, **exclude** it and log a warning.  
3. **Merge** on `formula`; drop rows where any of `yield_strength_MPa`, `shear_modulus_GPa`, or `bulk_modulus_GPa` are null.  
4. **Validate** the merged CSV against `contracts/dataset.schema.yaml`. Abort with `ERR_INSUFFICIENT_DATA` if validation fails or if `len(merged) < 20`.  
5. **Checksum** all raw and merged files; record in `state/...yaml`.

### Phase 1 – Feature Engineering & Collinearity (FR‑001, FR‑003, SC‑001)
1. **One‑hot encode** each element present in `formula`; also compute fractional composition columns (`Fe`, `Cr`, …).  
2. **Optional covariates**: if the experimental dataset includes `testing_temperature_C`, `strain_rate_s_inv`, or `heat_treatment`, add them as numeric features; otherwise log their absence and note as a limitation.  
3. **Scale** DFT descriptors (`StandardScaler`).  
4. **Compute VIF** for all predictors; if any `VIF > 5`, iteratively drop the feature with the highest VIF until all ≤ 5, and record the dropped list. As a sensitivity check, also train a Ridge‑regularized model on the full set.  
5. **Pearson correlation** between `shear_modulus_GPa` and `yield_strength_MPa`; store `r`, `p`, and 95 % CI (SC‑001).

### Phase 2 – Modeling & Statistical Testing (FR‑004, FR‑005, FR‑009)
1. **Nested CV**:  
   - Outer loop: 5‑fold split (hold‑out test).  
   - Inner loop: 5‑fold grid search for `n_estimators` ∈ {[deferred]}, `max_depth` ∈ {None,10,20}.  
2. **Baseline model**: train on composition‑only (and optional covariates) using the same CV scheme.  
3. **Collect per‑fold MAE & R²** for both models; store in `fold_metrics`.  
4. **Paired t‑test** on the outer‑fold MAE differences → `t_statistic`, `p_value`, 95 % CI for the mean difference, and rank‑biserial effect size.  
5. **Power analysis**: using `statsmodels.stats.power.TTestPower` with observed effect size, α = 0.05, n = number of folds × fold size; compute `power`. If `power < 0.8`, add a warning field (SC‑008).  
6. **Leave‑one‑out CV** as an additional robustness check to assess over‑fitting risk given the small sample size.

### Phase 3 – Interpretability & Sensitivity Analysis (FR‑006, FR‑007, FR‑008)
1. **TreeSHAP** on the final DFT‑enhanced model (full dataset). Export mean absolute SHAP per feature.  
2. **Permutation importance** (10 repeats) → compute mean and standard deviation per feature.  
3. **Bootstrap stability**: resample the full dataset with replacement **10** times; for each bootstrap compute permutation importance; aggregate standard deviations.  
4. **Threshold check**: if `std_dev < 0.05` for `shear_modulus_GPa` and `bulk_modulus_GPa`, set `is_stable: true` (SC‑005).  

### Phase 4 – Reporting & Contract Validation (SC‑002‑SC‑007)
1. Assemble `data/results/output.json` matching both `contracts/model_output.schema.yaml` **and** `contracts/output.schema.yaml`.  
2. Generate plots (`shap_summary.png`, `perm_importance.png`, `stability.png`) and store under `data/results/plots/`.  
3. Run `pytest` contract tests to ensure schema compliance.  

## Risk Assessment & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Materials Project rate‑limit** | API calls may be throttled, causing missing DFT rows. | Exponential backoff + skip after 3 attempts; still log each skip. |
| **Missing experimental yield‑strength column** in the MatNavi dataset. | Cannot satisfy FR‑001 → pipeline aborts. | Early validation step; abort with `ERR_INSUFFICIENT_DATA`. |
| **Low statistical power** (n ≈ 20) | May limit claim of improvement. | Compute and report power; if `<0.8`, explicitly state limitation (SC‑008). |
| **Multicollinearity** between one‑hot composition and DFT descriptors. | Inflated importance scores. | VIF analysis with iterative dropping and Ridge fallback (methodology‑ef15bb22). |
| **Construct validity of DFT features** | DFT descriptors may not capture real‑world defects. | Provide literature justification (methodology‑114e8ca3) and note limitation. |
| **Unrecorded experimental confounds** | Bias in estimated DFT benefit. | Include optional covariates when available; otherwise log as limitation (methodology‑23fd71ba). |
| **Small sample size** | Over‑fitting risk. | Add leave‑one‑out CV as an extra robustness check (methodology‑9b5d0439). |
| **API key missing** | Cannot query Materials Project. | Script aborts with clear error; no synthetic fallback permitted. |
| **Memory overflow** | Unlikely given tiny dataset, but possible with large intermediate objects. | Use `pandas` chunking for merges; keep dataset < 500 MB. |

---



## projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/specs/001-predicting-the-yield-strength-of-bcc-ste/research.md===
# Research: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

## 1. Problem Statement & Research Questions
**Primary Question**: Does incorporating DFT‑derived elastic constants (shear & bulk modulus) improve the prediction of experimental yield strength for BCC Fe‑alloys relative to a composition‑only model?

- **Null Hypothesis (H₀)**: MAE of the DFT‑enhanced Random Forest is **not** lower than that of the composition‑only baseline.  
- **Alternative Hypothesis (H₁)**: MAE of the DFT‑enhanced model is **signistically lower**.

## 2. Dataset Strategy
| Data Type | Source | Verified Loader / URL | Notes |
|-----------|--------|-----------------------|-------|
| **Experimental composition & yield strength** | MatNavi “Steel Yield Strength” dataset (open) | `datasets.load_dataset('matnavi/steel_yield_strength')` | Contains `formula` and `yield_strength_MPa`. The pipeline aborts with `ERR_INSUFFICIENT_DATA` if the column is missing or < 20 rows survive merging. |
| **DFT elastic constants** | Materials Project API (via `mp-api`) | Programmatic API call (`mp_api.client.MaterialsProjectClient`) | Queries for `bulk_modulus` and `shear_modulus` and filters `spacegroup.number == 229`. All queries are logged to `data/provenance/dft_queries.jsonl`. |
| **Fallback** | **None** – synthetic data is prohibited. | – | If after merging the row count < 20, the system halts as required by FR‑001/FR‑002. |

### Integration Plan
1. **Fetch experimental file** → `data/raw/experimental.csv`.  
2. **Iterate formulas**, query Materials Project → `data/raw/dft_{formula}.json`.  
3. **Merge** on `formula`; keep only rows where `yield_strength_MPa`, `shear_modulus_GPa`, and `bulk_modulus_GPa` are present.  
4. **Validate** the merged CSV against `contracts/dataset.schema.yaml`. Abort with `ERR_INSUFFICIENT_DATA` if validation fails or if `len(merged) < 20`.  

## 3. Methodology
### 3.1 Feature Engineering
- **Composition features**: one‑hot encoding of each element present, plus fractional composition (derived from the formula).  
- **DFT features**: `shear_modulus_GPa`, `bulk_modulus_GPa` (standardized).  
- **Optional experimental covariates**: testing temperature, strain rate (`strain_rate_s_inv`), and heat‑treatment metadata are added if present; otherwise they are logged as missing and noted as a limitation.  
- **Collinearity mitigation**: compute Variance Inflation Factors (VIF); if any `VIF > 5`, iteratively drop the highest‑VIF predictor and record the dropped list. As a sensitivity check, also train a Ridge‑regularized model on the full feature set.  

### 3.2 Construct Validity of DFT Features
Literature (e.g., Petch & Nabarro, early work; Liu et al., year) demonstrates a strong empirical correlation between shear modulus and yield strength for BCC metals, providing a mechanistic basis for using ideal‑state DFT elastic constants as predictors. Nonetheless, we acknowledge that real alloys contain defects, grain‑size effects, and processing histories not captured by ideal DFT calculations; this limitation is explicitly reported in the final results.

### 3.3 Modeling
- **Algorithm**: `sklearn.ensemble.RandomForestRegressor`.  
- **Validation**: **5‑fold outer × 5‑fold inner** nested cross‑validation to avoid leakage.  
- **Baseline**: same RF hyper‑parameter search but trained on composition features (and optional covariates) only.  

### 3.4 Statistical Testing
- **Metric per outer fold**: MAE and R².  
- **Paired test**: **paired t‑test** on the 5 outer‑fold MAE differences (parametric, as required by FR‑005).  
- **Effect size & CI**: report t‑statistic, p‑value, 95 % confidence interval for the mean MAE difference, and rank‑biserial correlation as an effect‑size analogue.  
- **Power analysis**: using `statsmodels.stats.power.TTestPower` with observed effect size, α = 0.05, and effective sample size (≈ 20‑30). Compute `power`. If `power < 0.8`, add a warning field (SC‑008).  

### 3.5 Interpretability & Sensitivity Analysis
- **TreeSHAP**: global mean absolute SHAP values for all features.  
- **Permutation importance**: 10 repeats; compute mean ± std for each feature.  
- **Bootstrap stability**: resample the full dataset with replacement **10** times; for each bootstrap compute permutation importance; aggregate standard deviations.  
- **Stability threshold**: `std_dev < 0.05` for `shear_modulus_GPa` and `bulk_modulus_GPa` → `is_stable = true`.  

## 4. Compute Feasibility
- **Hardware**: 2 CPU cores, ≈7 GB RAM, ≤6 h runtime (GitHub Actions free tier).  
- **Memory**: Full merged dataset expected ≤ 200 KB (≈20–50 rows), trivial for Random Forest.  
- **Runtime Estimate**:  
  - Data download & merge: < 2 min.  
 - Nested CV (5 × 5 = 25 fits) + hyper‑parameter grid: [deferred].
 - SHAP (TreeExplainer on ≤ 50 samples): [deferred].
 - Bootstrap (10 × permutation): ≈ 10 min.  
  - Total < 1 h, well within limits.  

## 5. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **No yield‑strength column** in the MatNavi dataset. | Early validation step; abort with `ERR_INSUFFICIENT_DATA`. |
| **Materials Project rate‑limit** | Exponential backoff + skip after 3 attempts; still log each skip. |
| **Low statistical power** (n ≈ 20) | Compute and report power; if `<0.8`, explicitly state limitation (SC‑008). |
| **Multicollinearity** | VIF analysis with iterative dropping and Ridge fallback (methodology‑ef15bb22). |
| **Construct validity of DFT features** | Provide literature justification and note limitation (methodology‑114e8ca3). |
| **Unrecorded experimental confounds** | Include optional covariates when available; otherwise log as limitation (methodology‑23fd71ba). |
| **Small sample size** | Add leave‑one‑out CV as an extra robustness check (methodology‑9b5d0439). |
| **API key missing** | Script aborts with clear error; no synthetic fallback permitted. |
| **Memory overflow** | Use `pandas` chunking for merges; keep dataset < 500 MB. |

---



## projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/specs/001-predicting-the-yield-strength-of-bcc-ste/data-model.md===
# Data Model: Predicting the Yield Strength of BCC Steels from Density Functional Theory

## 1. Entity Overview
| Entity | Description | Primary Key |
|--------|-------------|-------------|
| **ExperimentalRecord** | Raw experimental entry (composition + optional yield strength). | `formula` |
| **DFTRecord** | DFT elastic constants fetched from Materials Project. | `material_id` |
| **UnifiedRecord** | Merged, filtered row used for modeling. | `formula` |

## 2. Schema Definitions

### 2.1 `dataset.schema.yaml` (merged dataset)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Unified BCC Steel Dataset Schema"
description: "Schema for the merged dataset containing experimental yield strength and DFT descriptors."
type: "object"
properties:
  formula:
    type: "string"
    description: "Chemical formula of the alloy (e.g., Fe0.95Cr0.05)."
  yield_strength_MPa:
    type: "number"
    description: "Experimental yield strength in MPa."
    minimum: 0
  shear_modulus_GPa:
    type: "number"
    description: "DFT Shear Modulus in GPa."
    minimum: 0
  bulk_modulus_GPa:
    type: "number"
    description: "DFT Bulk Modulus in GPa."
    minimum: 0
  space_group:
    type: "integer"
    description: "Crystal space group number (must be 229 for BCC)."
    enum:
      - 229
  element_fractions:
    type: "object"
    description: "Map of elemental fractions."
    additionalProperties:
      type: "number"
      minimum: 0
      maximum: 1
  uncertainty_flag:
    type: "boolean"
    description: "True if the original yield strength was a range."
  # Optional experimental covariates (may be absent)
  testing_temperature_C:
    type: "number"
    description: "Testing temperature in Celsius."
  strain_rate_s_inv:
    type: "number"
    description: "Strain rate during the test (1/s)."
  heat_treatment:
    type: "string"
    description: "Heat‑treatment descriptor (e.g., 'annealed')."
required:
  - formula
  - yield_strength_MPa
  - shear_modulus_GPa
  - bulk_modulus_GPa
  - space_group
  - element_fractions
  - uncertainty_flag
additionalProperties: false
```

### 2.2 `output.schema.yaml` (final results)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Output Schema"
description: "Schema for the final metrics and analysis results."
type: "object"
properties:
  metrics:
    type: "object"
    description: "Performance metrics for both models."
    properties:
      r2_rf:
        type: "number"
        description: "R-squared for the Random Forest with DFT features."
      mae_rf:
        type: "number"
        description: "Mean Absolute Error for the Random Forest with DFT features."
      r2_baseline:
        type: "number"
        description: "R-squared for the composition-only baseline."
      mae_baseline:
        type: "number"
        description: "Mean Absolute Error for the composition-only baseline."
      p_value:
        type: "number"
        description: "P-value from the paired **t-test** (not Wilcoxon)."
      power:
        type: "number"
        description: "Statistical power (1 - β) of the test."
      null_hypothesis:
        type: "string"
        description: "Statement of the null hypothesis."
    required:
      - r2_rf
      - mae_rf
      - r2_baseline
      - mae_baseline
      - p_value
      - power
      - null_hypothesis
  correlation_analysis:
    type: "object"
    description: "Pearson correlation between shear modulus and yield strength."
    properties:
      r_value:
        type: "number"
      p_value:
        type: "number"
      confidence_interval_95:
        type: "array"
        items:
          type: "number"
    required:
      - r_value
      - p_value
      - confidence_interval_95
  feature_importance:
    type: "object"
    description: "Top‑5 SHAP features and permutation importance statistics."
    properties:
      top_5_shap:
        type: "array"
        description: "Top 5 features by mean absolute SHAP value."
        items:
          type: "object"
          properties:
            feature:
              type: "string"
            importance:
              type: "number"
          required:
            - feature
            - importance
      permutation_std:
        type: "array"
        description: "Standard deviation of permutation importance across 10 bootstraps."
        items:
          type: "object"
          properties:
            feature:
              type: "string"
            std_dev:
              type: "number"
          required:
            - feature
            - std_dev
    required:
      - top_5_shap
      - permutation_std
  stability_analysis:
    type: "object"
    description: "Bootstrap stability metrics."
    properties:
      sample_sizes:
        type: "array"
        description: "Sample sizes tested (full dataset with replacement)."
        items:
          type: "integer"
      std_dev_dft_descriptors:
        type: "array"
        description: "Standard deviation of importance for DFT descriptors."
        items:
          type: "number"
      is_stable:
        type: "boolean"
        description: "True if std_dev < 0.05 for key DFT descriptors."
    required:
      - sample_sizes
      - std_dev_dft_descriptors
      - is_stable
  multicollinearity:
    type: "object"
    description: "Variance Inflation Factor (VIF) scores for features."
    properties:
      vif_scores:
        type: "object"
        additionalProperties:
          type: "number"
        description: "VIF score for each feature."
      max_vif:
        type: "number"
        description: "Maximum VIF observed."
    required:
      - vif_scores
      - max_vif
  data_validation:
    type: "object"
    description: "Data validation results."
    properties:
      row_count:
        type: "integer"
        description: "Total number of valid rows in the merged dataset."
      min_threshold_met:
        type: "boolean"
        description: "True if row_count ≥ 20."
    required:
      - row_count
      - min_threshold_met
required:
  - metrics
  - correlation_analysis
  - feature_importance
  - stability_analysis
  - multicollinearity
  - data_validation
additionalProperties: false
```

## 3. Data Flow Diagram (Logical)
1. **Raw download** → `data/raw/experimental.csv` (experimental)  
2. **API query** → per‑formula JSON files in `data/raw/dft/`  
3. **Merge & filter** → `data/intermediate/merged.csv` (validated against `dataset.schema.yaml`)  
4. **Feature engineering** → `data/processed/features.npy` (numpy array)  
5. **Model training & evaluation** → `data/results/output.json` (validated against `output.schema.yaml`)  
6. **Plots** → `data/results/plots/` (PNG files referenced only in the paper).

---



## projects/PROJ-537-predicting-the-yield-strength-of-bcc-ste/specs/001-predicting-the-yield-strength-of-bcc-ste/quickstart.md===
# Quickstart: Predicting the Yield Strength of BCC Steels from Density Functional Theory

## Prerequisites
- **Python 3.11** (or newer)  
- **Materials Project API key ** (free registration at <https://materialsproject.org>)  
- Internet access (for downloading the experimental dataset and querying the Materials Project API)  

## Installation
```bash
# 1. Clone the repository
git clone 
cd PROJ-537-predicting-the-yield-strength-of-bcc-ste

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install a pinned dependencies 
```bash
pip {
     </    ..  </   ...



```

