# Implementation Plan: Statistical Analysis of Urban Noise Pollution (Prototype Validation)

**Branch**: `001-statistical-analysis-urban-noise` | **Date**: 2026-07-06 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-statistical-analysis-urban-noise/spec.md`

## Summary
This feature implements a **methodological prototype** for a reproducible, CPU-constrained statistical pipeline to analyze urban noise pollution. 
**Scope Limitation**: Due to the absence of verified geospatial noise datasets in the project's "Verified datasets" block, this implementation **cannot** perform an empirical analysis of real-world urban noise. Instead, it validates the *pipeline logic* (ingestion, harmonization, spatial modeling, cross-validation) using a **synthetic data proxy**. 
The pipeline ingests synthetic noise/covariate data, harmonizes them into a high-resolution grid, and fits Ordinary Least Squares (OLS) alongside Spatial Lag and Spatial Error models. It strictly adheres to the "Compute Feasibility" constraint (GitHub Actions free tier: limited CPU and RAM) by utilizing `PySAL` for spatial econometrics and `scikit-learn` for validation. The pipeline explicitly addresses spatial autocorrelation, applies Benjamini-Hochberg FDR correction with robust standard errors, and validates model superiority via spatial block permutation tests. 
**Crucial Distinction**: The synthetic data generator uses **stochastic parameters** (not pre-biased values) to ensure the analysis is a true hypothesis test. If the synthetic data lacks spatial dependence, the pipeline will correctly report that OLS is the preferred model. Success Criteria (SC-001 to SC-005) are treated as **Validation Checks** for the pipeline's correctness and statistical soundness. They are **not** design targets to be guaranteed by the data generator.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `geopandas`, `pysal`, `libpysal`, `scikit-learn`, `numpy`, `statsmodels`, `requests`, `pyarrow`, `linearmodels` (for Conley/Cluster-Robust SEs)  
**Storage**: Local filesystem (`data/`, `code/`), GeoParquet for intermediate storage. 
**Data Hygiene**: All files in `data/raw/` and `data/processed/` are checksummed using SHA. Checksums are recorded in the project state file (`state/projects/...yaml`) to satisfy Constitution Principle III (Data Hygiene) and V (Versioning Discipline). Any change to a data file invalidates dependent artifacts.
**Testing**: `pytest` (unit tests for data harmonization, integration tests for model convergence).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline (Prototype).  
**Performance Goals**: Complete full pipeline (ingest, harmonize, model, validate) within 6 hours on 2 CPU cores, <7GB RAM.  
**Constraints**: No GPU; no deep learning; dataset subset to a representative sample of grid cells; strict memory management (chunked processing if necessary).  
**Scale/Scope**: A large number of grid cells (fine resolution) across a simulated study area.

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant (Prototype)** | Random seeds pinned in `code/`. Synthetic data generator is deterministic. `requirements.txt` pins exact versions. *Note: Real-world data fetch is not possible with current verified sources; reproducibility applies to the synthetic pipeline logic.* |
| **II. Verified Accuracy** | **Compliant (Code)** | Citations in `research.md` restricted to the "Verified datasets" block. The synthetic generator is verified against the schema. *Note: No real-world data citations exist; the project is a prototype.* |
| **III. Data Hygiene** | **Compliant** | Raw data (synthetic) preserved in `data/raw/` with SHA-256 checksums. Derived data written to `data/processed/` with new filenames. PII scan logic included. |
| **IV. Single Source of Truth** | **Compliant** | All statistics in the final report generated programmatically from `data/processed/` via `code/`. No hand-typed numbers. |
| **V. Versioning Discipline** | **Compliant** | Artifacts in `data/` and `code/` will be hashed. State file updated on artifact change. |
| **VI. Spatial Autocorrelation** | **Compliant** | Pipeline explicitly calculates Moran's I for residuals of OLS, Lag, and Error models. Model superiority is only claimed if Moran's I reduction >10% and residual I ≤ 0.1. |
| **VII. Multi-Source Integrity** | **Compliant** | Covariates (OSM, WorldPop proxies) validated for spatial alignment (CRS, grid overlay) before merging. |

## Project Structure

### Documentation (this feature)
```text
specs/001-statistical-analysis-urban-noise/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── model_output.schema.yaml
```

### Source Code (repository root)
```text
projects/PROJ-304-statistical-analysis-of-publicly-availab/
├── data/
│   ├── raw/                  # Unmodified downloads (checksummed)
│   └── processed/            # Harmonized GeoParquet, model outputs
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, constants
│   ├── ingestion.py          # FR-001, FR-002: Data download & harmonization
│   ├── preprocessing.py      # Edge cases: IQR filter, imputation logic, Daily Aggregation
│   ├── models.py             # FR-003, FR-004, FR-006, FR-009: OLS, Lag, Error fitting, Robust SEs
│   ├── validation.py         # FR-005, FR-007: Spatial CV, permutation tests
│   └── main.py               # Orchestrator
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to minimize I/O overhead on the CI runner. `code/` contains modular scripts for each FR, orchestrated by `main.py`. `data/` is split into `raw` (immutable) and `processed` (derived).

## Phase Execution Plan

### Phase 0: Research & Data Strategy
*   **Goal**: Identify verified sources for noise data and covariates.
*   **Action**: Map spec requirements to verified datasets. Confirm gap.
*   **Output**: `research.md` (Dataset Strategy, Methodological Rationale, Synthetic Proxy Strategy).

### Phase 0.5: Synthetic Data Generation (NEW)
*   **Goal**: Generate a statistically valid proxy dataset to validate pipeline logic.
*   **Action**: Implement `code/synthetic_data.py` to generate a large-scale set of grid cells with **stochastic** spatial parameters (e.g., Moran's I drawn from a distribution). **Crucially**, parameters are NOT pre-biased to meet Success Criteria.
*   **Output**: `data/raw/synthetic_noise.parquet` (Checksummed).

### Phase 1: Data Model & Contracts
*   **Goal**: Define the schema for the harmonized grid and model outputs.
*   **Action**: Create `data-model.md` and `contracts/*.schema.yaml`.
*   **Output**: Validated YAML schemas for dataset and model results.

### Phase 2: Implementation (Code Generation)
*   **Goal**: Generate Python scripts for ingestion, modeling, and validation.
*   **Action**: Implement FR-001 through FR-010.
    *   **FR-002**: Implement **Daily Aggregation** (calculate mean, median, and high-percentile summary statistics per day per cell). The unit of analysis is `(grid_id, date)`.
    *   **FR-009**: Implement **Conley/Cluster-Robust SEs** using `linearmodels` **BEFORE** BH-FDR correction.
    *   **Edge Case (Weight Matrix)**: Implement **Spatial Weight Matrix Fallback**. Sequence: 1. Queen Contiguity. 2. If failed, K-Nearest Neighbor (K=8). 3. If both failed, log CRITICAL error and **HALT** execution immediately.
    *   **Edge Case (Convergence)**: If Spatial models fail to converge, fallback to OLS. **Crucially**, the system MUST still calculate and report Moran's I for the OLS residuals to satisfy SC-001 comparison requirements.
*   **Output**: `code/` directory with runnable scripts.

### Phase 3: Execution & Validation
*   **Goal**: Run pipeline on CI, verify metrics against SC-001 to SC-005 (as Validation Checks).
*   **Action**: Execute `main.py`, capture logs, generate reports.
*   **Output**: `data/processed/` artifacts, final metrics report.
*   **Validation Logic**: If the synthetic data yields no spatial dependence, the pipeline correctly reports OLS as superior. This is a **valid scientific outcome** and a success for the pipeline logic.

## Risk Mitigation
*   **Memory Constraint (7GB RAM)**: If the full city dataset exceeds limits, the pipeline will automatically sample to a representative subset of grid cells or process in chunks.
*   **Data Availability**: If a specific covariate (e.g., WorldPop) is missing for a cell, the cell is excluded (per spec assumption), and the count is logged.
*   **Convergence Failure**: If Spatial models fail to converge, the system falls back to OLS and logs a critical warning. **Crucially, the system MUST still calculate and report Moran's I for the OLS residuals** to satisfy SC-001 comparison requirements.
*   **Spatial Weight Matrix Failure**: If the primary Queen/Contiguity matrix construction fails, the system defaults to a K-Nearest Neighbor (K=8) matrix. If *both* fail, the system logs a CRITICAL error and halts execution immediately (per Spec Edge Cases).

## Data Integrity & Checksums
*   All files in `data/raw/` and `data/processed/` are checksummed using SHA-256.
*   Checksums are recorded in the project state file (`state/projects/...yaml`) to satisfy Constitution Principle III and V.
*   Any change to a data file invalidates dependent artifacts.
