# Implementation Plan: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

**Branch**: `001-quantify-topology-confinement` | **Date**: 2026-07-26 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-magnetic-field/spec.md`

## Summary

This project quantifies the relationship between magnetic field topology (island width, resonant surface density) and plasma energy confinement time ($\tau_E$) using DIII-D public archives. The approach involves retrieving pre-reconstructed EFIT and diagnostic data via HTTP/MDSplus, calculating topological metrics (specifically counting rational surfaces $q=m/n$), and performing a Spearman rank correlation with bootstrap confidence intervals. Due to the small sample size (N=5-10), the primary decision logic is Bayesian (Bayes Factor), with frequentist p-values reported as secondary metrics. The pipeline is constrained to a runtime of approximately half a workday and moderate memory on a CPU-only GitHub Actions runner, prioritizing open, streamable data sources or open substitutes for any access-gated requirements. If the DIII-D archive is unavailable, the run will fail.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `matplotlib`, `requests`, `pyyaml`, `bayesian-stats` (or custom implementation)
**Storage**: Local file system (`data/raw/`, `data/processed/`) for CSV/Parquet artifacts; no database.
**Testing**: `pytest` (unit tests for metric calculation, integration test for pipeline flow).
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM, ~14 GB Disk).
**Project Type**: Data Analysis Pipeline / CLI Tool.
**Performance Goals**: Process 5-10 discharges; 1000 bootstrap iterations; total runtime < 6h.
**Constraints**: Must run on CPU; no local GPU; strict memory limits; data must be reproducible from public sources.
**Scale/Scope**: Single-shot analysis of multiple discharges; output includes 1 CSV, 1 plot, 1 summary report.

> **Dataset Strategy Note**: The spec cites the "DIII-D public MDSplus archive". Per the "Verified datasets" block, no direct URL for MDSplus is verified. The plan assumes the `wget` command targets the standard DIII-D public gateway (as per Assumption in spec). If the archive is unreachable, the pipeline will fail gracefully (FR-001) and *not* attempt to load alternative data sources.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action / Reference |
|-----------|--------|--------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/utils/random.py`. Data fetch scripts use checksum verification. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` and `plan.md` will be validated against the "Verified datasets" block. No fabricated URLs. |
| **III. Data Hygiene** | PASS | `data/raw/` will contain checksummed archives. `data/processed/` will contain derived CSVs. No in-place modification. |
| **IV. Single Source of Truth** | PASS | Every figure, statistic, or interpretation in the paper MUST trace back to exactly one row in this project's `data/` and one block in this project's `code/`. Derived numbers MUST NOT be hand-typed into the paper. |
| **V. Versioning Discipline** | PASS | Artifact hashes recorded in `state/...yaml`. Content hashes used for invalidation. |
| **VI. Archival Data Provenance** | PASS | Datasets MUST be retrieved directly from the DIII-D public MDSplus archive. No non-archival sources are used.|
| **VII. Statistical Rigor** | PASS | Spearman correlation + 1000 bootstrap iterations implemented; explicit acknowledgement of power limitations due to small sample size; Bayesian re-analysis strategy included as primary decision logic. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-topology-confinement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-332-quantifying-the-impact-of-magnetic-field/
├── code/
│   ├── main.py                  # Entry point; wires limits wrapper
│   ├── utils/
│   │   ├── limits.py            # Timeout/Memory guard (wired in main)
│   │   ├── random.py            # Seed management
│   │   └── io.py                # Data loading/saving helpers
│   ├── data/
│   │   ├── retrieval.py         # MDSplus/HTTP fetcher (US1)
│   │   ├── parsing.py           # EFIT/Island parsing (US1)
│   │   └── topology.py          # Resonant surface density calc (US2)
│   ├── analysis/
│   │   ├── correlation.py       # Spearman + Bootstrap (US3)
│   │   └── viz.py               # Plot generation (US3)
│   └── reports/
│       └── summary.py           # Final report generation (SC-005)
├── data/
│   ├── raw/                     # Downloaded archives (checksummed)
│   └── processed/               # unified_analysis.csv, plots
├── tests/
│   ├── unit/
│   │   ├── test_topology.py
│   │   └── test_limits.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── .github/
    └── workflows/
        └── ci.yml               # Runs main.py with resource limits
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Retrieve -> Parse -> Calculate -> Analyze -> Report), making a monolithic `code/` directory with modular sub-packages efficient for the small scope.

## Phases & Tasks

### Phase 0: Setup & Environment
*   **T001**: Initialize git repository and create directory structure (`code/`, `data/`, `tests/`, `contracts/`).
*   **T002**: Create `requirements.txt` with pinned versions (`numpy`, `pandas`, `scipy`, `matplotlib`, `requests`, `pyyaml`, `pytest`).
*   **T003**: Configure GitHub Actions workflow (`.github/workflows/ci.yml`) with 6h timeout and 7GB RAM limits.

### Phase 1: Data Model & Contracts
*   **T004**: Define `contracts/dataset.schema.yaml` based on `data-model.md`.
    *   **Output**: `contracts/dataset.schema.yaml`
    *   **Tags**: `[FR-001]`, `[US1]`
*   **T005**: Define `contracts/output.schema.yaml` based on `data-model.md`.
    *   **Output**: `contracts/output.schema.yaml`
    *   **Tags**: `[FR-004]`, `[US3]`
*   **T006**: **Implement global timeout and memory wrapper in `code/utils/limits.py`**.
    *   **Algorithm**: Create a decorator or context manager that wraps the main execution function, enforcing the 6h runtime and 7GB RAM limits defined in FR-007.
    *   **Output**: `code/utils/limits.py`
    *   **Tags**: `[FR-007]`
*   **T007**: **Wire `limits.py` into `code/main.py` and CI workflow**.
    *   **Input**: `code/utils/limits.py` (from T006).
    *   **Logic**: Import and apply the limit wrapper to the `main()` function in `code/main.py`. Update `.github/workflows/ci.yml` to ensure the runner environment respects these limits.
    *   **Output**: Updated `code/main.py`, updated `.github/workflows/ci.yml`.
    *   **Tags**: `[FR-007]`
    *   **Dependency**: Must be completed before T014.

### Phase 2: Data Retrieval & Parsing (US1)
*   **T014**: **Implement parsing logic to convert MDSplus time-series data into a single structured DataFrame.**
    *   **Input**: Raw data files from `code/data/retrieval.py`; `contracts/dataset.schema.yaml` (from T004).
    *   **Algorithm**:
        1.  Retrieve EFIT, island, and tau_e data.
        2.  **Calculate `resonant_surface_density`**: Count rational surfaces (q=m/n) per unit minor radius from the EFIT q-profile. (Algorithm: Scan q-profile for integer crossings; count unique m/n ratios; divide by minor radius).
        3.  **Retrieve `island_width`**: Fetch pre-calculated value from `islands` tree.
        4.  **Validate**: Ensure `island_width` and `tau_e` are present; exclude invalid rows.
        5.  **Output**: `unified_analysis.csv` containing `discharge_id`, `island_width`, `resonant_surface_density`, `tau_e`, `mode`, `valid`, `confinement_deviation`.
    *   **Constraint**: Output MUST match `contracts/dataset.schema.yaml`.
    *   **Tags**: `[FR-001]`, `[FR-002]`, `[US1]`
    *   **Dependency**: Must be completed after T004 (schema) and T007 (limits).

### Phase 3: Statistical Analysis (US3)
*   **T027**: **Implement Spearman correlation and Bootstrap CI.**
    *   **Input**: `unified_analysis.csv` (from T014).
    *   **Logic**: Calculate Spearman $\rho$; perform 1000 bootstrap iterations for 95% CI. Calculate Bayes Factor (BF10) for the correlation.
    *   **Output**: `correlation_results.json` (contains `correlation_coefficient`, `p_value`, `ci_lower`, `ci_upper`, `effect_size_magnitude`, `bayes_factor`, `sample_size`).
    *   **Tags**: `[FR-004]`, `[FR-005]`, `[US3]`
*   **T028**: **Implement Hypothesis Flagging (Bayesian Logic).**
    *   **Input**: `correlation_results.json` (from T027).
    *   **Logic**: Set `hypothesis_supported` = True if `bayes_factor` > 3 (indicating moderate evidence for association) AND `correlation_coefficient` < -0.5. (Note: Frequentist p-value < 0.05 is reported but not the primary decision rule due to low power).
    *   **Output**: `hypothesis_flags.json`.
    *   **Tags**: `[SC-001]`, `[SC-002]`
*   **T029**: **Implement Visualization.**
    *   **Input**: `unified_analysis.csv` (from T014).
    *   **Logic**: Generate scatter plot (`topology_vs_confinement.png`).
    *   **Tags**: `[FR-006]`, `[US3]`

### Phase 4: Reporting
*   **T030**: **Generate final summary report.**
    *   **Input**: `correlation_results.json` (from T027) and `hypothesis_flags.json` (from T028).
    *   **Logic**: Compile results into `summary_report.md`.
    *   **Requirement**: **Unconditionally report `effect_size_magnitude` (|r|) for ALL valid datasets**, regardless of statistical significance or hypothesis support (SC-005).
    *   **Output**: `summary_report.md`.
    *   **Tags**: `[SC-005]`, `[US3]`

## Testing Strategy

*   **Unit Tests**:
    *   `test_topology.py`: Verify `resonant_surface_density` calculation against known q-profiles.
    *   `test_limits.py`: Verify timeout and memory wrappers.
*   **Integration Tests**:
    *   `test_pipeline.py`: Run full pipeline on mock data; verify `unified_analysis.csv` schema and `summary_report.md` content.
*   **Acceptance Criteria**:
    *   US1: `unified_analysis.csv` contains 5-10 rows with all required columns (including `resonant_surface_density`).
    *   US3: `summary_report.md` contains `effect_size_magnitude` for all results.
    *   FR-007: Pipeline aborts if limits exceeded.