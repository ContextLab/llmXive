# Implementation Plan: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Branch**: `001-predict-glass-forming-region` | **Date**: 2026-07-26 | **Spec**: `specs/001-predicting-the-glass-forming-region/spec.md`
**Input**: Feature specification from `/specs/001-predicting-the-glass-forming-region/spec.md`

## Summary

This project implements a machine learning pipeline to predict the critical cooling rate (a proxy for glass-forming ability) of ternary alloy systems using thermodynamic descriptors (mixing enthalpy, atomic size mismatch, electronegativity variance) derived from standard periodic table properties. The target variable, `critical_cooling_rate`, is obtained from the **BMG (Bulk Metallic Glass) Database** (a curated experimental dataset), NOT OQMD (which lacks kinetic data). The approach utilizes a Random Forest regressor with 5-fold cross-validation, permutation importance analysis, and sensitivity testing against physically-grounded thresholds. The pipeline adheres to strict data hygiene, reproducibility, and associational framing principles.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: pandas, scikit-learn, numpy, requests, datasets (HuggingFace), pyyaml, pytest, mendeleev  
**Storage**: Local CSV/Parquet files (data/), JSON logs (data/logs/), Pickle models (data/models/)  
**Testing**: pytest (unit tests for feature engineering, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions CPU runner: multiple cores, 7 GB RAM)  
**Project Type**: data-science-pipeline  
**Performance Goals**: Complete full pipeline (ingestion -> modeling -> analysis) within 6 hours on CPU.  
**Constraints**: No GPU acceleration; must handle missing data gracefully; **must validate all data artifacts against contracts in `contracts/`**; must enforce associational framing.  
**Scale/Scope**: Target N ≥ 500 valid alloy records from BMG dataset; 5-fold CV; A sufficient number of permutation iterations.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

1.  **Reproducibility (Principle I)**: The plan mandates pinned `random_state=42` in all splitting and sampling steps. Data sources are fixed URLs (BMG dataset via HuggingFace). The pipeline is designed to be re-runnable end-to-end. **Artifact**: `code/ingestion.py` and `code/modeling.py` enforce `random_state=42`.
2.  **Verified Accuracy (Principle II)**: All citations in `research.md` reference only the verified URLs provided in the input block (BMG dataset). No unverified dataset URLs will be introduced. **Artifact**: `research.md` contains verified URLs only.
3.  **Data Hygiene (Principle III)**: The plan includes checksumming of raw and processed data files (`data/logs/ingestion_hash.txt`). No in-place modification of raw data; derivations create new files. **Artifact**: `code/utils.py` calculates and stores SHA-256 hashes in `data/logs/ingestion_hash.txt`.
4.  **Single Source of Truth (Principle IV)**: All metrics (RMSE, F1, dataset size) will be generated programmatically and stored in `data/models/cv_metrics.json` and `data/models/sensitivity_report.json`. The paper will reference these artifacts, not hand-typed numbers. **Artifact**: `data/models/cv_metrics.json` includes `final_dataset_size`.
5.  **Versioning Discipline (Principle V)**: Artifact hashes will be updated in the project state file upon generation. **Artifact**: `state/projects/PROJ-510-.../state.yaml` updated by `code/utils.py`.
6.  **Thermodynamic Feature Engineering Integrity (Principle VI)**: The plan explicitly defines the formulas for mixing enthalpy, atomic size mismatch, and electronegativity variance using standard periodic table properties (via `mendeleev`). No proxy values will be used. **Artifact**: `code/feature_engineering.py` uses `mendeleev` library for standard properties.
7.  **Cross-Validation and Permutation Importance Rigor (Principle VII)**: The plan enforces 5-fold CV and permutation importance (n=1000) as the primary evaluation metrics. Single-split results will be reported only as secondary checks. **Artifact**: `code/modeling.py` implements 5-fold CV and permutation importance.

## Project Structure

### Documentation (this feature)

```text
specs/001-predicting-the-glass-forming-region-of-a/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── sensitivity.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-510-predicting-the-glass-forming-region-of-a/
├── code/
│   ├── __init__.py
│   ├── ingestion.py           # Data download, filtering, logging, hash calculation
│   ├── feature_engineering.py # Thermodynamic calculations, unit tests
│   ├── modeling.py            # RF training, CV, permutation importance, t-test
│   ├── analysis.py            # Sensitivity analysis, collinearity checks, associational framing check
│   ├── utils.py               # Logging, config loading, hash verification
│   └── validate_schemas.py    # Contract validation
├── data/
│   ├── raw/                   # Downloaded BMG subsets
│   ├── processed/             # Feature-engineered CSVs
│   ├── models/                # Saved models, metrics JSONs
│   └── logs/                  # Error logs, exclusion logs, hashes
├── tests/
│   ├── unit/
│   │   └── test_features.py   # Unit tests for thermodynamic formulas
│   └── integration/
│       └── test_pipeline.py   # End-to-end pipeline validation
├── config.yaml                # Configuration for paths, thresholds
└── requirements.txt           # Pinned dependencies
```

**Structure Decision**: A single-project structure is selected to minimize overhead for a data-science pipeline. The separation of `code/`, `data/`, and `tests/` ensures clear boundaries between logic, artifacts, and verification, satisfying the reproducibility and data hygiene principles.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope (ternary alloy prediction) is well-bounded and fits within the CPU constraints using standard ML libraries. | N/A |

## Phase Breakdown

### Phase 0: Research & Data Strategy
- **Task**: Verify BMG dataset contains `critical_cooling_rate` and ternary alloy entries.
- **Task**: Define thermodynamic formulas and validate against literature.
- **Output**: `research.md`.

### Phase 1: Data Modeling & Contracts
- **Task**: Define `AlloyRecord`, `ModelMetrics`, `SensitivityReport` entities.
- **Task**: Create JSON schemas for `dataset`, `model_output`, `sensitivity_report`.
- **Task**: Define `random_state=42` and threshold values (low, medium, and high) in contracts.
- **Output**: `data-model.md`, `contracts/*.schema.yaml`.

### Phase 2: Implementation & Validation
- **Task (T008)**: Implement `ingestion.py` to download BMG data, filter, and log exclusions. **Add error handling**: Catch fetch failures and write to `data/logs/fetch_error.log`.
- **Task (T010a, T010b)**: Implement `tests/unit/test_features.py` with `test_mixing_enthalpy` and `test_size_mismatch` unit tests.
- **Task (T016a)**: Generate `data/processed/processed_alloys.csv` with at least 500 valid rows.
- **Task (T020)**: Implement `code/modeling.py` to load `processed_alloys.csv`, split with `random_state=42`, `test_size=0.2`.
- **Task (T021)**: Generate `data/models/cv_metrics.json` including `final_dataset_size`, `valid_entry_count`, `mean_cv_rmse`, `p_value_baseline`.
- **Task (T021a)**: Explicitly implement and log the **two-sided t-test** against the dummy regressor to calculate `p_value_baseline` (SC-002).
- **Task (T022)**: Save trained Random Forest model to `data/models/random_forest_model.pkl`.
- **Task (T023)**: Implement validation step to check if any top-2 feature has p < 0.05 (SC-004) and log the result.
- **Task (T037)**: Execute `validate_schemas.py` and log validation results.
- **Task (T047)**: Calculate SHA-256 hash of `processed_alloys.csv` and store in `data/logs/ingestion_hash.txt`.
- **Task (T050)**: Implement empty dataset error handling in `ingestion.py` (raise `ValueError`, write to `data/logs/empty_dataset_error.log`).
- **Task (T051)**: Implement label filtering in `ingestion.py` and write to `data/logs/exclusion_log.txt` and `data/logs/label_filtering_status.json`.
- **Task (T052)**: Implement `analysis.py` to enforce associational framing (scan output text for causal verbs) and verify SC-004 (p < 0.05 for top-2 feature).
- **Output**: `code/*.py`, `data/processed/*.csv`, `data/models/*.json`.

### Phase 3: Reporting
- **Task**: Generate `cv_metrics.json` with `final_dataset_size` and `p_value_baseline`.
- **Task**: Generate `sensitivity_report.json` with `rmse_variance` and `collinearity_flags`.
- **Task**: Write paper sections referencing artifacts, ensuring associational framing.
- **Output**: Final report/paper.

## Contracts & Validation

All generated data files (`data/processed/*.csv`, `data/models/*.json`) MUST be validated against the schemas in `contracts/` before being considered final. The `validate_schemas.py` script (Task T037) will enforce this.