# Implementation Plan: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Branch**: `001-predict-glass-forming-region` | **Date**: 2023-10-27 | **Spec**: [spec.md](../specs/001-predict-glass-forming-region/spec.md)

## Summary
The project implements a machine learning pipeline to predict the **critical cooling rate (CCR)** of ternary alloy systems. It involves: (1) ingesting experimental alloy data and elemental properties from the Open Quantum Materials Database (OQMD), (2) engineering thermodynamic descriptors (mixing enthalpy, atomic size difference, and electronegativity variance), (3) training a Random Forest regressor with 5-fold cross-validation, (4) performing permutation importance and a sensitivity analysis across physically-grounded thresholds ([50, 100, 150] K/s), and (5) ensuring full reproducibility via SHA-256 hashing and schema validation.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**: 
  - `pandas==2.2.*`, `numpy==1.26.*` (Data processing)
  - `scikit-learn==1.5.*` (Random Forest, CV, Permutation Importance)
  - `datasets==2.19.*` (Hugging Face programmatic access to OQMD)
  - `pyyaml==6.0.*` (Schema validation)
- **Storage**: Flat files (CSV for data, JSON for metrics, PKL for model) under `data/`.
- **Testing**: `pytest` for unit tests of thermodynamic formulas and data filtering.
- **Target Platform**: GitHub Actions (2 CPU, 7GB RAM, 14GB Disk).
- **Compute Budget**: CPU-only. OQMD data will be streamed to fit within RAM limits.
- **Project Type**: Research Analysis Pipeline.

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All stochastic operations use `random_state=42`. Data is fetched from canonical URLs. SHA-256 hashes are recorded for all artifacts. |
| **II. Verified Accuracy** | Only URLs from the "Verified Datasets" block are used for OQMD. The missing CCR dataset URL is flagged as a blocking risk. |
| **III. Data Hygiene** | Raw data is preserved; transformations produce new files. Checksums are recorded in `data/logs/ingestion_hash.txt`. |
| **IV. Single Source of Truth** | All results in the final report are derived from validated CSV/JSON artifacts. |
| **V. Versioning Discipline** | Artifact hashes are recorded; any change in `processed_alloys.csv` triggers a hash update. |
| **VI. Thermodynamic Feature Engineering Integrity** | Descriptors are computed strictly using OQMD elemental properties and standard alloy formulas. |
| **VII. Cross-Validation and Permutation Importance Rigor** | Enforces 80/20 split and 5-fold CV. Permutation importance uses $n=1000$ iterations. |

## Project Structure

### Documentation
```text
specs/001-predict-glass-forming-region/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── processed_alloys.schema.yaml
    ├── metrics.schema.yaml
    ├── feature_importance.schema.yaml
    ├── sensitivity.schema.yaml
    └── model_output.schema.yaml
```

### Source Code
```text
src/
├── data_pipeline/
│   ├── ingestion.py        # OQMD & CCR fetching, filtering, engineering
│   └── validation.py        # Schema validation logic
├── models/
│   ├── trainer.py           # RF Training, 5-fold CV, Stratified Split
│   └── evaluator.py         # Permutation Importance, Sensitivity Analysis
└── utils/
    ├── thermodynamics.py   # Pure functions for descriptors
    └── hashing.py           # SHA-256 utilities
tests/
├── unit/
│   ├── test_thermo.py       # Tests for mixing enthalpy, etc.
│   └── test_filtering.py    # Tests for label/missing data removal
└── contract/
    └── test_schemas.py      # Validates artifacts against YAML contracts
```

**Structure Decision**: Single project structure chosen for simplicity and CI efficiency.

## Phase Mapping

| Phase | Tasks | FR/SC Addressed |
|-------|-------|-----------------|
| **Phase 0: Setup & Validation** | (0.1) Implement `validate_schemas.py` to check YAML syntax. (0.2) Verify connectivity to OQMD verified URLs. | FR-017, SC-007 |
| **Phase 1: Data Ingestion & Engineering** | (1.1) Fetch OQMD elemental properties (streaming) and the experimental CCR dataset; log all download status to `data/logs/processing.log`. (1.2) Filter entries with undefined `glass_forming_label` or missing `critical_cooling_rate` (log to `exclusion_log.txt`, `label_filtering_status.json`, and `processing.log`). (1.3) Compute mixing enthalpy, atomic size difference, and electronegativity variance. (1.4) Validate $N \ge 500$ valid entries; otherwise, raise `ValueError` and log to `empty_dataset_error.log`. (1.5) Write `processed_alloys.csv` and record SHA-256 hash. | FR-001, FR-002, FR-005, FR-009, FR-013, FR-016, FR-018, SC-001, SC-003, SC-005 |
| **Phase 2: Model Training & CV** | (2.1) Implement stratified 80/20 train-test split based on binned CCR. (2.2) Train `RandomForestRegressor` (seed 42) and perform 5-fold CV. (2.3) Calculate mean RMSE, test RMSE, and perform a paired permutation test (10,000 permutations) against the dummy baseline to determine significance (p < 0.05). (2.4) Save `random_forest_model.pkl` and `cv_metrics.json`. | FR-003, FR-008, FR-010, FR-019, SC-002 |
| **Phase 3: Feature Analysis** | (3.1) Perform permutation importance analysis ($n=1000$, seed 42). (3.2) Compute p-values for each descriptor's importance against a shuffled baseline. (3.3) Save `feature_importance.csv`. | FR-004, SC-004 |
| **Phase 4: Sensitivity & Classification** | (4.1) Sweep thresholds $[50, 100, 150]$ K/s. (4.2) For each threshold, train a binary classifier and compute F1-score. (4.3) Apply Bonferroni correction for multiple tests across thresholds. (4.4) Save `sensitivity_report.json`. | FR-015, SC-006 |
| **Phase 5: Final Validation** | (5.1) Run `validate_schemas.py` against all generated artifacts. (5.2) Generate final `model_output.json` with all artifact paths and hashes. | FR-017, SC-007 |
| **Phase 6: Reporting** | (6.1) Document the limitation of using only three descriptors and the potential for bias (e.g., electronic structure). (6.2) Frame all conclusions as associational. | FR-006, FR-007 |

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| **Missing CCR Dataset URL** | Fatal | The "Verified Datasets" block contains no URL for CCR. The pipeline will be built to accept a path/URL, but a verified source must be provided for execution. |
| **RAM Exhaustion** | High | Use `datasets.load_dataset(..., streaming=True)` for OQMD to avoid loading the full database into memory. |
| **Overfitting** | Medium | Use 5-fold CV and report both CV RMSE and held-out test RMSE to detect generalization gaps. |
| **Collinearity** | Medium | Report Pearson correlation between descriptors; if $|r| > 0.8$, the final report will explicitly note the interdependence. |

## Timeline
- **Week 1**: Phase 0 & 1 (Ingestion, Engineering, and $N \ge 500$ verification).
- **Week 2**: Phase 2 & 3 (Training, CV, and Permutation Importance).
- **Week 3**: Phase 4 & 5 (Sensitivity Analysis and Schema Validation).
- **Week 4**: Phase 6 (Final reporting and Limitation documentation).