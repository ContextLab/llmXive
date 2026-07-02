# Implementation Plan: Quantify Dataset Sparsity Impact

**Branch**: `001-quantify-sparsity-impact` | **Date**: 2024-05-22 | **Spec**: `specs/001-quantify-sparsity-impact/spec.md`
**Input**: Feature specification from `/specs/001-quantify-sparsity-impact/spec.md`

## Summary

This feature implements a computational pipeline to quantify how dataset sparsity affects the predictive performance of machine learning models (Gaussian Process Regression and Random Forest) trained on material stability data. The system will ingest DFT-computed formation energy data from a **150k-entry Source Pool**, engineer composition descriptors, generate 7 stratified sparsity subsets from a **Representative Stratified Sample (RSS)** of **[deferred] entries** (drawn from the 150k pool), train models under strict CPU-only constraints, and perform statistical analysis (Linear Mixed-Effects Modeling) to identify performance thresholds. The implementation strictly adheres to the project constitution regarding reproducibility, data hygiene, and uncertainty calibration.

> **Scope Clarification**: The study explicitly measures sparsity impact on a **30k-entry Representative Stratified Sample (RSS)**. The "[deferred]" baseline is this 30k sample, not the full 150k. This avoids extrapolation claims and ensures computational feasibility on CPU-only free-tier runners. The 150k figure represents the **Source Pool** from which the RSS and the Fixed Test Set are drawn.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pymatgen`, `matminer`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `matplotlib`, `requests`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`, `models/`, `results/`)  
**Testing**: `pytest` (unit tests for data ingestion, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, 7 GB RAM)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Full pipeline execution ≤ 6 hours; individual model training ≤ 60 mins per subset; memory usage ≤ 7 GB.  
**Constraints**: No GPU/CUDA; no large-LLM inference; strict adherence to 7 GB RAM limit via **capped sample size (k max for GPR)**; all random seeds pinned.  
**Scale/Scope**: Processing ~150k material entries (**Source Pool**), but training baseline capped at **[deferred] Representative Stratified Sample (RSS)** to ensure CPU feasibility. 7 sparsity levels × 2 models × 3 seeds = 42 training runs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|-----------------------|
| **I. Reproducibility** | **PASS** | All random seeds will be pinned in `code/`. External data fetches will use canonical sources with checksums. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will be limited to the verified datasets block. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Raw data will be stored in `data/raw/` with checksums. Derivations (descriptors, subsets) in `data/processed/`. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All metrics (RMSE, MAE, p-values, CalibrationSlope) will be logged to CSV/JSON in `data/results/` and referenced directly in the paper generation. |
| **V. Versioning Discipline** | **PASS** | `requirements.txt` will pin versions. `state/` will track artifact hashes. |
| **VI. Uncertainty Calibration** | **PASS** | **Phase 3.1** will generate calibration reports (slope, predicted vs. squared residuals) for GPR models and store them in `data/results/calibration/`. |
| **VII. Sparsity-Level Documentation** | **PASS** | **Phase 1.4** will generate `data/metadata/sparsity_<level>_<seed>.json` files for every training run containing seed, percentage, and stratification criteria. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-sparsity-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Schema definitions)
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-458-quantifying-the-impact-of-dataset-sparsi/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_ingestion.py       # FR-001, FR-002
│   ├── test_split.py           # FR-009 (Phase 0.5)
│   ├── sparsity_generation.py  # FR-003 (Phase 1.0)
│   ├── validate_stratification.py # Phase 1.3
│   ├── model_training.py       # FR-004, FR-005
│   ├── statistical_analysis.py # FR-006 (LMM), FR-007, FR-010
│   └── utils/
│       ├── logging.py
│       ├── cpu_constraints.py  # Memory/CPU enforcement
│       └── contract_validator.py # Loads contracts/*.schema.yaml
├── data/
│   ├── raw/                    # Downloaded MP data (checksummed)
│   ├── processed/              # Descriptors, subsets, FIXED TEST SET
│   ├── results/                # Metrics, plots, calibration reports
│   └── metadata/               # Sparsity level definitions (Phase 1.4)
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    └── paper/
```

**Structure Decision**: Single project structure selected to minimize overhead. The `code/` directory contains modular scripts for each major functional requirement. This aligns with the "Computational Research Pipeline" type and ensures easy execution on CI. The `contracts/` directory contains schema definitions loaded by `utils/contract_validator.py` for runtime validation.

## Implementation Phases

### Phase 0: Data Ingestion & Validation
- **Task 0.1**: Download Materials Project data via API (FR-001).
- **Task 0.2**: Generate composition descriptors (FR-002).
- **Task 0.3**: **Create Fixed Test Set** (FR-009): Partition [deferred] of the full dataset into `data/processed/test_set.csv` immediately after ingestion. This set is locked and used for *all* evaluations.

### Phase 0.5: Fixed Test Set Partitioning (FR-009)
- **Task 0.5.1**: Execute `test_split.py` to isolate the `FixedTestSet` from the full 150k source pool.
- **Task 0.5.2**: Verify test set independence (no overlap with training pool).
- **Task 0.5.3**: Log test set ID and checksum to `data/metadata/test_set_metadata.json`.

### Phase 1: Sparsity Generation & Validation
- **Task 1.1**: Cap the training pool at **[deferred] entries** (Representative Stratified Sample) to ensure GPR feasibility on 7GB RAM.
- **Task 1.2**: Generate multiple stratified subsets ([deferred], [deferred], [deferred], [deferred], [deferred], [deferred], [deferred] of the 30k pool) using K-Means on elemental fingerprints (FR-003).
- **Task 1.3**: **Stratification Validation** (New): Compute Jensen-Shannon divergence and KS-test on formation energy distributions between subsets and the 30k pool. Block training if divergence > threshold (JS < 0.05, KS p > 0.05).
- **Task 1.4**: **Metadata Generation** (Constitution VII): Write `data/metadata/sparsity_<level>_<seed>.json` for every subset containing seed, percentage, and stratification criteria.

### Phase 2: Model Training
- **Task 2.1**: Train GPR (RBF kernel, `normalize_y=True`, max a high number of iterations) and Random Forest models (FR-004).
- **Task 2.2**: Perform k-fold Cross-Validation (multiple seeds per level) (FR-005).
- **Task 2.3**: Evaluate on **Fixed Test Set** (not the training subsets) to prevent circular dependency (FR-009).
- **Task 2.4**: Log RMSE, MAE, **Predictive Variance**, and Calibration Slope (FR-005).

### Phase 3: Statistical Analysis & Reporting
- **Task 3.1**: **Uncertainty Calibration** (Constitution VI): Generate calibration slope and predicted vs. squared residuals plots for GPR. Store in `data/results/calibration/`.
- **Task 3.2**: **Sensitivity Analysis** (FR-007): Verify elbow point stability (slope variance < 10%) across adjacent levels.
- **Task 3.3**: **Linear Mixed-Effects Modeling** (FR-010): Use `statsmodels.MixedLM` to handle nested subsamples. Report p-values for sparsity levels.
- **Task 3.4**: Generate Learning Curves and Final Report.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Capped 30k Baseline** | Full 150k GPR is $O(N^3)$ and exceeds 7GB RAM on CPU. | Simple random sampling of 150k would still crash GPR. Sparse GPR approximations are less stable for this specific research question. |
| **LMM instead of ANOVA** | Subsets are nested ([deferred] is subset of [deferred] of 30k), violating ANOVA independence. | Standard ANOVA would produce invalid p-values. LMM correctly models the nested structure. |
| **Stratification Validation** | K-Means stratification must be verified to ensure no chemical bias. | Without validation, performance degradation could be due to missing chemistry, not data volume. |
| **Fixed Test Set** | Prevents data leakage and ensures consistent evaluation. | Using the training subset as test set would bias results. |


## Phase Order & Dependencies

1.  **Ingestion** (Phase 0) must complete before **Test Split** (Phase 0.5).
2.  **Test Split** (Phase 0.5) must complete before **Sparsity Generation** (Phase 1).
3.  **Sparsity Generation** (Phase 1) must complete before **Validation** (Phase 1.3).
4.  **Validation** (Phase 1.3) must pass before **Model Training** (Phase 2).
5.  **Model Training** (Phase 2) must complete before **Statistical Analysis** (Phase 3).
6.  **Calibration Reports** (Phase 3.1) must be generated before **Final Paper** generation.

## Note on Spec Contradictions (Kickback Required)

The following Functional Requirements in `spec.md` contradict the feasible implementation plan and require a kickback to update the spec:
- **FR-006**: Mandates "Repeated Measures ANOVA". The plan uses Linear Mixed-Effects Modeling (LMM) due to nested data structure. **Action**: Update spec to LMM.
- **Assumptions**: Assumes "no authentication barriers" for MP API. The plan requires `MP_API_KEY`. **Action**: Update spec assumption to acknowledge API key requirement.
- **Success Criteria (SC-001)**: Only mentions RMSE and MAE. **Action**: Update to include Predictive Variance and Calibration Slope.
- **FR-007**: Mentions "trend stability" but lacks explicit "slope variance < 10%" metric. **Action**: Update spec to explicitly mandate the <10% threshold.
- **FR-001/FR-003**: Mandate "full dataset" or "150k". The plan uses a 30k RSS baseline. **Action**: Clarify spec to define "[deferred]" as the 30k RSS baseline.
- **FR-009**: The plan correctly implements the Fixed Test Set (Phase 0.5). The previous note claiming a contradiction was a logical error. No kickback needed for FR-009, but the spec's assumption about API access needs correction.