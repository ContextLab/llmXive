# Implementation Plan: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

## Overview

This project implements a machine learning pipeline to predict the glass transition temperature (Tg) of metallic glasses based on their chemical composition and atomic descriptors. The pipeline follows strict scientific computing principles, ensuring reproducibility, data integrity, and associational (not causal) interpretations.

## Project Structure

- `code/`: Source code for the pipeline
- `data/raw/`: Raw data fetched from Zenodo
- `data/processed/`: Cleaned and processed data
- `artifacts/models/`: Trained model artifacts
- `artifacts/metrics/`: Performance metrics and analysis results
- `artifacts/reports/`: Final reports and visualizations
- `tests/`: Unit and integration tests
- `specs/001-predict-tg-metallic-glasses/`: Feature specifications and contracts

## User Stories

### US1: Data Ingestion and Validation (P1)
- Load metallic glass datasets from Zenodo using DOIs
- Validate data integrity and schema compliance
- Clean data by removing records with missing Tg or composition
- Track data retention rates and source provenance

### US2: Model Training, Feature Engineering, and Sensitivity Analysis (P2)
- Compute atomic descriptors (radius mismatch, electronegativity difference, VEC)
- Train Gradient Boosting models with Leave-One-Family-Out cross-validation
- Perform hyperparameter optimization via grid search
- Calculate diagnostic metrics (weighted mean radius, null model baseline)
- Enforce resource limits (runtime < 6h, RAM < 7GB)

### US3: Result Interpretation, Reporting, and Statistical Validation (P3)
- Perform correlation analysis with Benjamini-Hochberg FDR correction
- Calculate VIF for collinearity diagnostics (flag only, no dropping)
- Generate partial dependence plots and correlation heatmaps
- Conduct bootstrap stability analysis for feature importances
- Perform sensitivity analysis on model hyperparameters
- Generate final report with associational language enforcement

## Functional Requirements (FR)

- **FR-001**: Data must be fetched from Zenodo DOI 10.5281/zenodo.10043838 (primary) or 10.5281/zenodo.11023456 (fallback). [UNRESOLVED-CLAIM: c_889a5f96 — status=not_enough_info] If both fail, halt with DATA_UNAVAILABLE error.
- **FR-002**: Atomic descriptors (radius mismatch, electronegativity difference, VEC) must be computed using mendeleev==0.31.0. Weighted mean radius is calculated for diagnostics only and excluded from model training.
- **FR-003**: Model training must use GradientBoostingRegressor with Leave-One-Family-Out (LOFO) cross-validation to prevent family-based leakage.
- **FR-004**: All reports must use associational language only. The phrase "These findings are associational only" must appear in the final report.
- **FR-005**: Resource limits: runtime < 6 hours, RAM < 7 GB. Exceeding limits must halt execution gracefully.
- **FR-006**: Sensitivity analysis must sweep max_depth over {3, 5, 7} and report R² variance.
- **FR-007**: VIF analysis must flag predictors with VIF > 5 for diagnostic review but MUST NOT drop any features. The "weighted mean radius" must be explicitly excluded from VIF calculation.
- **FR-008**: Correlation p-values must be adjusted using Benjamini-Hochberg FDR correction (α ≤ 0.05), NOT Bonferroni.
- **FR-009**: Pearson and Spearman correlation coefficients must be calculated between all predictor pairs.

## Security & Compliance (SC)

- **SC-001**: All code must be version controlled with git.
- **SC-002**: Bootstrap resampling (n=1000) must be used to calculate 95% confidence intervals for feature importances. [UNRESOLVED-CLAIM: c_448b88e8 — status=not_enough_info]
- **SC-003**: Data provenance and retention rates must be logged to `data/ingestion_stats.json`.
- **SC-004**: Resource limits must be enforced at runtime via decorator.

## Complexity Tracking

- **Data Ingestion**: Medium complexity - requires API handling, fallback logic, and data validation.
- **Descriptor Computation**: Medium complexity - requires chemical property lookups and vectorized calculations.
- **Model Training**: High complexity - requires LOFO CV implementation, hyperparameter tuning, and resource monitoring.
- **Statistical Analysis**: High complexity - requires FDR correction, VIF diagnostics, and bootstrap resampling.
- **Reporting**: Medium complexity - requires plot generation and text assembly with language constraints.

## FR/SC Coverage Map

| Requirement | Implementation Task(s) | Status |
|-------------|------------------------|--------|
| FR-001 (Zenodo fetch) | T012, T015 | Implemented |
| FR-002 (Descriptors) | T020, T021, T026 | Implemented |
| FR-003 (LOFO CV) | T022, T023 | Implemented |
| FR-004 (Associational) | T049, T050 | Implemented |
| FR-005 (Resource limits) | T025, T008a-d | Implemented |
| FR-006 (Sensitivity) | T037a, T037b | Implemented |
| FR-007 (VIF Flagging) | T035a, T035b | Implemented - **Diagnostic only, no dropping** |
| FR-008 (FDR Correction) | T034 | Implemented - **Benjamini-Hochberg, NOT Bonferroni** |
| FR-009 (Correlations) | T033a, T033b | Implemented |
| SC-001 (Version control) | T001 | Implemented |
| SC-002 (Bootstrap CI) | T036a, T036b | Implemented |
| SC-003 (Provenance) | T012, T016 | Implemented |
| SC-004 (Resource enforcement) | T008a-d, T025 | Implemented |

## Dependencies

- **Python**: >= 3.8
- **mendeleev**: == 0.31.0 (for atomic properties)
- **pandas**, **numpy**, **scikit-learn**, **scipy** (for data processing and ML)
- **requests** (for Zenodo API)
- **pyyaml** (for config)
- **jsonschema** (for validation)
- **matplotlib**, **seaborn** (for plotting)
- **ruff** (for linting)

## Execution Order

1. Phase 1: Setup (T001-T003)
2. Phase 2: Foundational (T004-T008)
3. Phase 3: US1 Data Ingestion (T010-T016)
4. Phase 4: US2 Modeling (T018-T026)
5. Phase 5: US3 Analysis & Reporting (T033-T051, T059-T064)
6. Phase 6: Plan Alignment & Polish (T055-T058)

## Notes

- All tasks marked [P] can run in parallel if independent.
- Phase 5 tasks are blocked until T024 (model) and T026 (descriptors) are complete.
- No GPU/CUDA dependencies; all models run on CPU.
- **Critical Correction**: FR-008 uses Benjamini-Hochberg FDR, not Bonferroni.
- **Critical Correction**: FR-007 flags VIF > 5 but does not drop features; "weighted mean radius" is excluded from VIF calculation.