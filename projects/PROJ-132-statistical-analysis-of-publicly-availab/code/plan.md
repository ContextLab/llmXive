# Implementation Plan: Statistical Analysis of Bird Migration and Climate Change

## Project Overview
This project analyzes publicly available bird migration data (eBird) and climate data (NOAA) to investigate correlations between climate change and bird migration patterns.

## Success Criteria & Fallbacks

### SC-001: Statistical Power
- **Target**: Power ≥ 0.80 (POWER_TARGET)
- **Fallback**: If power < 0.80, report effect size estimates with wider confidence intervals and note limitations.

### SC-002: Insufficient Data Handling
- **Target**: ≤ 20% of grid cells flagged as insufficient (INSUFFICIENT_DATA_TARGET)
- **Fallback**: If > 20% cells are insufficient, focus analysis on high-quality regions and document spatial bias.

### SC-003: Model Convergence
- **Target**: ≥ 90% convergence rate (CONVERGENCE_TARGET)
- **Fallback**: If convergence < 90%, simplify model complexity or use alternative estimation methods.

### SC-004: Confidence Interval Width
- **Target**: CI width ≤ 5.0 days (CI_WIDTH_TARGET)
- **Fallback**: If CI width > 5.0, report increased uncertainty and recommend additional data collection.

### SC-005: Runtime Constraint
- **Constraint**: Total pipeline runtime must be < 6 hours on standard CI infrastructure.
- **Optimization**: Use chunked processing, vectorization, and parallel permutation tests where safe.

## Assumption Targets (Numeric Values)

The following concrete values are used throughout the pipeline for validation and decision-making:

- **POWER_TARGET**: 0.80 (Target statistical power for hypothesis tests)
- **INSUFFICIENT_DATA_TARGET**: 0.20 (Maximum acceptable proportion of insufficient data cells)
- **CONVERGENCE_TARGET**: 0.90 (Minimum acceptable GAMM convergence rate)
- **CI_WIDTH_TARGET**: 5.0 (Maximum acceptable confidence interval width in days)

## Data Sources
- **eBird Data**: `vvud/eb-data` (HuggingFace Dataset)
- **Climate Data**: NOAA GHCN-Daily (via verified mirror or direct download)
- **Migratory Species List**: Cornell Lab of Ornithology (CLO)

## Implementation Phases

### Phase 0: Pre-Implementation & Plan Reconciliation
- [X] T050a: Reconcile Tail-Sampling Requirement (FR-002-S removed)
- [X] T050b: Reconcile GP Requirement (Mandatory → Conditional based on Moran's I > 0.15)
- [X] T050c: Update Runtime Budget (5.5h → 6h)
- [X] T001: Define Assumption Targets (POWER_TARGET, INSUFFICIENT_DATA_TARGET, CONVERGENCE_TARGET, CI_WIDTH_TARGET)

### Phase 1: Setup
- Project structure creation
- Dependency management (pyproject.toml, requirements.txt)
- Pre-commit hooks configuration

### Phase 2: Foundational
- Data download and verification (real data only, no synthetic fallbacks)
- Logging configuration
- Core constants and targets definition

### Phase 3: User Story 1 - Data Acquisition and Preprocessing
- Ingest eBird and climate data
- Filter to migratory species
- Aggregate to grid cells
- Compute phenology metrics

### Phase 4: User Story 2 - Phenology-Climate Correlation Modeling
- Fit GAMMs with conditional spatial correction
- Perform permutation tests
- Apply FDR correction

### Phase 5: User Story 3 - Route Shift Analysis
- Compute migration centroids
- Analyze trajectory shifts on Riemannian manifold
- Generate bootstrapped uncertainty intervals

### Phase 6: Orchestration & Validation
- Serialize heavy computations
- Validate success criteria
- Verify runtime budget

## Technical Constraints

- **Memory**: ~7GB RAM available in CI environment
- **Disk**: ~14GB disk space available
- **Runtime**: < 6 hours total
- **Data Integrity**: No synthetic data generation; real data only
- **Reproducibility**: All random operations use SEED=42

## Dependencies

- Python 3.11+
- pandas, numpy, scipy
- statsmodels, pygam
- geomstats (for Riemannian manifold analysis)
- datasets (HuggingFace)
- joblib (for parallelization)
- filelock (for orchestration)

## Execution Order

1. Complete Phase 0 (Plan reconciliation)
2. Complete Phase 1 (Setup)
3. Complete Phase 2 (Foundational)
4. Execute User Stories 1, 2, 3 (can be parallelized)
5. Execute Phase 6 (Orchestration & Validation)

## Notes

- The plan has been reconciled with spec.md to remove FR-002-S and make GP application conditional.
- Runtime budget updated to 6 hours to accommodate heavy permutation tests.
- Assumption targets are now explicitly defined in both plan.md and src/config.py.
