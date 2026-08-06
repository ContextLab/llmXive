# Implementation Plan: Statistical Analysis of Publicly Available Bird Migration Patterns and Climate Change

## Project Overview
This project analyzes the correlation between bird migration patterns and climate change using publicly available eBird and NOAA data.

## Success Criteria & Fallbacks

### SC-001: Statistical Power
- **Target**: POWER_TARGET = 0.80
- **Measurement**: Post-hoc power analysis using `statsmodels`
- **Fallback**: If power < 0.80, report insufficient sample size and recommend data expansion.

### SC-002: Data Sufficiency
- **Target**: INSUFFICIENT_DATA_TARGET = 0.20
- **Measurement**: Proportion of grid cells with count < 5
- **Fallback**: If > 20% of cells are insufficient, exclude those cells from modeling and report.

### SC-003: Model Convergence
- **Target**: CONVERGENCE_TARGET = 0.90
- **Measurement**: Proportion of GAMM fits that converge successfully
- **Fallback**: If convergence rate < 90%, simplify model structure or increase regularization.

### SC-004: Confidence Interval Width
- **Target**: CI_WIDTH_TARGET = 5.0
- **Measurement**: Average width of 95% confidence intervals for phenology shifts
- **Fallback**: If CI width > 5.0, report high uncertainty and recommend more data or longer time series.

### SC-005: Runtime Constraint
- **Constraint**: MAX_RUNTIME_HOURS = 6.0
- **Measurement**: Total pipeline execution time
- **Fallback**: If runtime exceeds 6 hours, optimize chunked processing or reduce permutation iterations.

## Reconciled Requirements

### FR-002: Tail Sampling
- **Status**: REMOVED. The "Tail-Preserving Stratified Sampling" (FR-002-S) requirement has been removed to align with spec integrity.
- **Action**: No special tail sampling is performed; standard aggregation is used.

### FR-004: Spatial Correction
- **Requirement**: Conditional Gaussian Process (GP) based on Moran's I diagnostics.
- **Logic**:
 1. Fit base GAMM model.
 2. Compute Moran's I on residuals.
 3. IF Moran's I > 0.15: Re-fit with GP random effect.
 4. ELSE: Proceed with base model.
- **Note**: The "mandatory a priori" requirement has been changed to "conditional" to match spec.

## Execution Order
1. Phase 0: Pre-Implementation & Plan Reconciliation (T050a, T050b, T050c, T001)
2. Phase 1: Setup (T002, T003a, T003b, T004)
3. Phase 2: Foundational (T005, T006, T007, T009, T010, T051a, T051, T011, T011a, T057a, T058a, T047)
4. Phase 3: User Story 1 (T014, T015a, T015, T017a, T017b, T016, T018)
5. Phase 4: User Story 2 (T023, T023b, T024, T025a, T025b, T025c, T027a, T027b, T027c, T042)
6. Phase 5: User Story 3 (T030, T031, T032a, T032b, T033, T033a)
7. Phase 6: Orchestration & Validation (T045, T046, T043, T044)
8. Phase N: Polish (T036, T037, T038a, T038b, T039a1, T039a2, T039b1, T039b2, T040a, T040b, T040c, T041a, T041b, T041c)

## Runtime Budget
- **Total Budget**: < 6 hours (SC-005)
- **Estimate**: Optimized pipeline with chunked processing and parallelization targets < 6h.

## Dependencies
- Python 3.11+
- pandas, numpy, scipy, statsmodels, pygam, geomstats, datasets, filelock, joblib, pytest, black, ruff