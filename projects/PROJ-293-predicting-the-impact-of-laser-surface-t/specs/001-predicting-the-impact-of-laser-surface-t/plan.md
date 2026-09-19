# Implementation Plan: Predicting the Impact of Laser Surface Texturing on Wear Resistance

**Branch**: `001-predict-lst-wear` | **Date**: 2026-08-22 | **Spec**: `specs/001-predict-lst-wear/spec.md`
**Input**: Feature specification from `/specs/001-predict-lst-wear/spec.md`

## Summary

This project implements a data-driven pipeline to predict the impact of Laser Surface Texturing (LST) parameters on wear resistance. The approach aggregates observational data from multiple open sources (OpenML, Zenodo), standardizes it using a corrected Archard's law normalization (incorporating hardness and explicit unit conversion), and trains regression models (Linear, Random Forest, Gradient Boosting) to identify non-linear functional relationships. Key analysis includes SHAP-based interpretability, leave-one-material-class-out cross-validation (with fallback logic and power warnings) for generalizability, and permutation testing for significance, all executed within CPU constraints on GitHub Actions.

**Critical Constraint**: No synthetic data generation is permitted. If the aggregated dataset size is < 300, the project proceeds with a 'Power Limitation' flag and reduced statistical confidence. If critical LST variables are missing from verified sources, the pipeline halts with `data_insufficiency_error` and reports `validation_target_unavailable` (SC-002).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `scikit-learn`, `shap`, `datasets` (HuggingFace), `pyyaml`, `openml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `models`, `reports`)  
**Testing**: `pytest` (contract tests, unit tests for ingestion/logic)  
**Target Platform**: Linux (GitHub Actions Free Runner: Limited CPU and RAM resources.)  
**Project Type**: Data Science / Computational Materials Science  
**Performance Goals**: Complete full pipeline (ingestion to SHAP) within 6 hours.  
**Constraints**: CPU-only execution (FR-003); no GPU usage; strict memory limits (constrained RAM); no data imputation for predictors (FR-002).  
**Scale/Scope**: Target dataset size ≥300 records (SC-004); minimum 3 material classes for LOO-CV (FR-006).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Verification Detail |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic data fetching from verified URLs (OpenML dataset

The specific value to remove/generalize: 'specific dataset identifier'

Rewritten passage:, Zenodo ID). |
| **II. Verified Accuracy** | PASS | Plan includes a **Dataset Schema Verification Step** and **Unit Conversion Check** to verify the downloaded dataset contains required columns (pulse_duration, power, etc.) and valid units before proceeding. If variables are missing, the system halts with `data_insufficiency_error` and reports `validation_target_unavailable` (SC-002), ensuring content matches the spec's schema. |
| **III. Data Hygiene** | PASS | Plan specifies `data/raw` (immutable) vs `data/processed` (derived) separation. Checksums will be generated for raw files and recorded in `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml`. |
| **IV. Single Source of Truth** | PASS | All metrics in `reports/` will be programmatically generated from `data/processed` and `models/` artifacts. |
| **V. Versioning Discipline** | PASS | Plan includes content hashing for data and model artifacts in `state/projects/PROJ-293-predicting-the-impact-of-laser-surface-t.yaml`. The hash registry path is explicitly referenced. |
| **VI. Numerical Stability** | PASS | Plan explicitly schedules VIF diagnostics (FR-010), feature scaling within CV folds (Constitution Principle VI), and handling of collinear features. |
| **VII. Cross-Material Generalizability** | PASS | Plan mandates Leave-One-Material-Class-Out (LOO-CV) as a primary validation step (FR-006, Constitution Principle VII) with a documented fallback to K-Fold (K=5) if <3 material classes or insufficient samples exist. The plan explicitly acknowledges that with ~300 records, LOO-CV is an *estimation* with high variance, and a 'Statistical Power Warning' will be logged. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-lst-wear/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── feature_importance.schema.yaml
│   ├── model_output.schema.yaml
│   ├── model_report.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_ingest.py          # Data ingestion, standardization, Archard normalization (with hardness correction and unit conversion)
├── 02_preprocess.py      # Missing value handling, VIF check, scaling
├── 03_train.py           # Model training, GridSearchCV, LOO-CV (with fallback)
├── 04_interpret.py       # SHAP analysis, permutation testing, Literature Consensus Check
├── 05_report.py          # Metric aggregation, JSON/CSV report generation
├── requirements.txt      # Pinned dependencies
└── utils/
    ├── schema_map.json   # Column mapping logic
    └── config.py         # Random seeds, paths

data/
├── raw/                  # Immutable downloaded datasets
└── processed/            # Cleaned, normalized, merged datasets

models/
└── best_model.pkl        # Serialized best model

reports/
├── model_report.json     # Metrics, transferability flags, validation status
├── shap_summary.png      # Feature importance plot
└── validation_log.txt    # LOO-CV results and warnings

tests/
├── contract/             # Schema validation tests
├── integration/          # Pipeline end-to-end tests
└── unit/                 # Logic tests (e.g., Archard calc, unit conversion)
```

**Structure Decision**: Single project structure (`code/`, `data/`, `models/`) selected to align with the computational data science workflow. This minimizes overhead for a pipeline that runs sequentially on a single runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Leave-One-Material-Class-Out (LOO-CV)** | Required by Constitution Principle VII and FR-006 to assess generalizability across material classes. | Standard K-Fold CV is insufficient because it does not explicitly test the model's ability to predict *new* material classes, which is the core "virtual prototyping" goal. |
| **Permutation Testing for Significance** | Required by FR-008 to avoid assumptions of independence in feature importance. | Standard p-values from linear models are invalid for non-linear models (RF/GB) and multiple comparisons; permutation is the robust alternative. |
| **VIF Diagnostics** | Required by FR-010 to handle collinearity (e.g., Power vs. Scanning Speed). | Ignoring collinearity would lead to spurious feature importance rankings, violating the "Single Source of Truth" for scientific insight. |
| **Physical Validation Check (SC-002)** | Required by SC-002 to report `validation_target_unavailable` or `physically_inconsistent` if microstructural data is missing or contradicts literature. | A simple error log is insufficient; the system must explicitly set `validation_status` in the output schema to distinguish between a failed validation and an unavailable target. |
| **Unit Conversion Logic** | Required to ensure Archard normalization is physically meaningful. | Without explicit unit conversion, the calculated wear coefficient is dimensionally inconsistent and scientifically invalid. |

## Tasks

- [ ] **T001**: Create directory structure (`code/`, `data/raw`, `data/processed`, `models`, `reports`, `tests/`, `state/`). **Evidence**: Run `ls -R` or script output confirming all directories exist.
- [ ] **T009**: Verify directory creation via `ls` or script output. **Evidence**: Log output showing `data/raw`, `data/processed`, `models`, `reports` exist.
- [ ] **T012**: Implement `02_preprocess.py` to drop records with missing predictors while retaining those missing `contact_load`/`sliding_speed` and setting `normalization_method='raw'`. Output `missing_record_count`. **Evidence**: Script output and a sample of the cleaned CSV showing the flag.
- [ ] **T018**: Implement `03_train.py` with GridSearchCV (≥10 combinations) and 5-fold CV, ensuring no data leakage. **Evidence**: Script output showing the grid search results and the best model parameters.
- [ ] **T031a**: Implement Physical Validation Check in `04_interpret.py` to check for `microstructural_features` column AND perform 'Literature Consensus Check' (compare top 3 SHAP features against known tribological mechanisms). **Evidence**: Code snippet showing the check for the column and the logic to set `validation_status`.
- [ ] **T031b**: Implement reporting logic in `05_report.py` to set `validation_status` in `model_report.json` to one of: 'validated', 'associational_only', 'validation_target_unavailable', or 'physically_inconsistent' based on T031a results. **Evidence**: Sample `model_report.json` showing the `validation_status` field populated correctly when the column is missing.
- [ ] **T039**: Ensure `research.md` contains only static, pre-verified URLs (OpenML 4594, Zenodo 1006980) and no dynamic search logic. **Evidence**: Content of `research.md` showing the static URLs and no search logic.