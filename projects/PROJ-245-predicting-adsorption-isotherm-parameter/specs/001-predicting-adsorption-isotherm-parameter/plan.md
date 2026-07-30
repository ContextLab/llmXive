# Implementation Plan: Predicting Adsorption Isotherm Parameters from Molecular Features

**Branch**: `001-predict-adsorption-isotherm-params` | **Date**: 2026-07-18 | **Spec**: []
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

## Summary

This project aims to predict adsorption isotherm parameters (Langmuir capacity, Henry constant) using molecular descriptors calculated from adsorbate structures and adsorbent properties. The approach involves data curation from the NIST Adsorption Database (verified source), followed by training and evaluating machine learning models (Linear Regression, Random Forest, Gradient Boosting). Model interpretation will be conducted via SHAP analysis to identify key drivers of adsorption behavior.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: scikit-learn, RDKit, pandas, numpy, shap, matplotlib
**Storage**: CSV files for data storage and model outputs. No database is required.
**Testing**: pytest for unit and integration tests.
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: library/cli
**Performance Goals**: Full pipeline execution within 4 hours on the CI runner.
**Constraints**: Limited to CPU-based computation. No external GPU services (e.g., Kaggle) are permitted.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **I. Reproducibility:** All dependencies pinned in `requirements.txt`. Random seeds fixed.
* **II. Verified Accuracy:** Citations verified against primary sources.
* **III. Data Hygiene:** Checksummed data, no manual entry. All transformations documented.
* **IV. Single Source of Truth**: All figures/statistics traced to source code & data.
* **V. Versioning Discipline**: Project state tracked with `updated_at` timestamp.
* **VI. Physicochemical Descriptor Integrity**: Descriptors will be *calculated* using RDKit in `code/`. No hardcoded lookups.
* **VII. Physicochemical Plausibility Validation**: Model predictions validated against established principles.

## Project Structure

```text
src/
├── data_processing/
│ ├── dataset_curation.py
│ ├── descriptor_calculation.py
│ └── parameter_fitting.py
├── modeling/
│ ├── model_training.py
│ ├── model_evaluation.py
│ ├── hyperparameter_tuning.py
│ └── cluster_permutation.py
├── interpretation/
│ └── shap_analysis.py
├── utils/
│ └── data_utils.py
└── main.py

tests/
├── test_data_processing.py
├── test_modeling.py
└── test_interpretation.py

contracts/
 └── dataset_schema.yaml # Single source of truth for data validation
```

**Structure Decision**: A modular structure is chosen, separating data processing, modeling, and interpretation into distinct modules for clarity and maintainability. The `contracts/` directory contains `dataset_schema.yaml` as the canonical validation schema.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| T014z hardcoded descriptor lookup | **REMOVED**. FR-001 and Principle VI require calculation via RDKit. | Hardcoded lookups are non-reproducible and violate Principle VI. |
| T035a - missing verified source | **REJECTED**. The plan now relies solely on the verified `nist-adsorption-isotherms` dataset. | Manual curation violates Principle III (Data Hygiene) and Principle I (Reproducibility). Missing data is excluded, not imputed. |
| FABRICATED-RESULT in tasks.md | **REMOVED**. The signal has been deleted from `tasks.md`. | Fabricated metrics violate Principle IV (Single Source of Truth). All results must be derived from real computation on real data. |

## Implementation Phases

### Phase 1: Data Curation & Feature Engineering
1. **Download Data**: Fetch `nist-adsorption-isotherms` and `mof_metadata.json`.
2. **Filter & Fit**: Filter for Type I isotherms. Fit Langmuir/Henry parameters from raw isotherm points.
3. **Calculate Descriptors**: Use RDKit to calculate molecular descriptors.
4. **Merge & Clean**: Join data, normalize units, exclude entries with missing critical metadata.
5. **Validate**: Check against `contracts/dataset_schema.yaml`.

### Phase 2: Model Training & Evaluation
1. **Split**: 80/20 split stratified by `material_id` (no leakage).
2. **Train**: Fit Linear, RF, GB models with 5-fold CV (material-level).
3. **Tune**: Hyperparameter optimization.
4. **Evaluate**: Report R², RMSE, MAE vs Null Model.
5. **Reduced Model**: Train a model using **only** the top 3 features (SC-003).

### Phase 3: Interpretation & Reporting
1. **SHAP Analysis**: Generate SHAP summary plots and partial dependence plots.
2. **Permutation Testing**: Perform cluster-aware permutation tests to generate p-values.
3. **FDR Correction**: Apply Benjamini-Hochberg to p-values.
4. **Report**: Compare findings with `LiteratureConsensusList`.
5. **Benchmark**: Generate `data/benchmarks/runtime_log.json` (FR-009).

### Phase 4: Validation & Output
1. **Plausibility Check**: Validate model drivers against physical principles.
2. **Final Report**: Assemble all results, plots, and logs.
3. **Artifact Generation**: Ensure all outputs match the `contracts/` schemas.