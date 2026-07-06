# Implementation Plan: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors (Pilot)

**Branch**: `001-explore-pressure-quake-correlation` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-explore-pressure-quake-correlation/spec.md`

## Summary

This project is a **Methodology Validation Pilot**. It investigates whether atmospheric pressure anomalies (derived from NOAA NCEP/NCAR reanalysis data) systematically precede earthquakes of magnitude ≥ 4.0 (from the USGS catalog). Due to the absence of a verified global pressure reanalysis dataset for 2013-2023 in the approved data sources, the **Global Study is currently blocked**. This phase focuses on validating the statistical pipeline (download, interpolation, anomaly calculation, KS/Permutation tests) using verified test datasets. The results will be labeled as "Pilot/Methodology Validation" and will not be generalized to global seismic activity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `scikit-learn`, `requests`, `tqdm`, `pyyaml`  
**Storage**: Local file system (`data/raw`, `data/processed`, `data/interim`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, 14 GB disk)  
**Project Type**: Computational Research / Data Analysis (Pilot)  
**Performance Goals**: Complete full pipeline (download, process, test) on the **verified test dataset** within 6 hours on CPU-only hardware.  
**Constraints**: No GPU; memory usage < 7 GB; disk usage < 14 GB; no causal claims; strict data hygiene (checksums).  
**Scope**: **Pilot only**. Global data (2013-2023) is **blocked** due to missing verified sources. Analysis is limited to the available test data.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action/Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and deterministic data fetching from verified URLs. |
| **II. Verified Accuracy** | **PASS (with Limitation)** | Plan restricts dataset sources to the "# Verified datasets" block. **Note**: The primary global pressure source (FR-001) is missing from verified sources. The plan explicitly acknowledges this gap and proceeds only with available test data. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of raw data, immutable raw storage, and derivation logs. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in the final report will be generated programmatically from `data/processed` artifacts. |
| **V. Versioning Discipline** | **PASS** | Content hashes will be recorded for all data artifacts in the project state file. |
| **VI. Temporal Window Precision** | **PASS** | The 0–48h pre-event window is hardcoded in `code/preprocess.py`. Deviations require a new analysis variant. |
| **VII. Null Result Rigor** | **PASS** | Plan explicitly includes power documentation, effect sizes (Cohen's d), and robustness checks for null results. |

## Project Structure

### Documentation (this feature)

```text
specs/001-explore-pressure-quake-correlation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── earthquake.schema.yaml
│   └── pressure-anomaly.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-252-exploring-the-correlation-between-atmosp/
├── data/
│   ├── raw/                 # Downloaded raw files (checksummed)
│   ├── interim/             # Intermediate alignment/interpolation files
│   └── processed/           # Final analysis-ready CSV/Parquet
├── code/
│   ├── __init__.py
│   ├── download.py          # Fetches NOAA (test) and USGS data
│   ├── preprocess.py        # Interpolation, anomaly calc, filtering, thinning
│   ├── analysis.py          # KS test, permutation, sensitivity
│   └── report.py            # Generates final JSON/Markdown report
├── tests/
│   ├── unit/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen for data science workflows. Separation of `download`, `preprocess`, `analysis`, and `report` ensures modularity and testability while maintaining a linear data pipeline suitable for CI execution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **None** | The project scope is contained within CPU limits and standard statistical libraries. | N/A |

## Requirements Mapping & Gap Analysis

| Requirement | Status | Notes |
| :--- | :--- | :--- |
| **FR-001** (Global Data Download) | **BLOCKED** | No verified source for global NCEP/NCAR 2013-2023. Implementation uses verified test data only. |
| **FR-002** (Interpolation) | **ACTIVE** | Implemented for available test grid data. |
| **FR-003** (Anomaly Calc) | **ACTIVE** | Baseline window: a pre-event period of sufficient duration prior to the event window. Event window: a pre-specified interval leading up to and including the event time. A defined temporal gap is maintained. |
| **FR-004** (Statistical Tests) | **ACTIVE** | KS and Permutation tests implemented. |
| **FR-005** (Associational Framing) | **ACTIVE** | All reports will explicitly state "associational". |
| **FR-006** (Multiple Comparisons) | **ACTIVE** | Benjamini-Hochberg FDR applied. |
| **FR-007** (Sensitivity Analysis) | **ACTIVE** | Cutoff sweep implemented with clean σ calculation. |
| **FR-008** (Validation) | **ACTIVE** | Schema validation implemented. |
| **FR-009** (Ocean Masking) | **ACTIVE** | Implemented. |
| **FR-010** (Missing Data) | **ACTIVE** | Implemented. |
| **FR-011** (Climate Index Stratification) | **DEFERRED** | No verified source for ENSO/PDO. Stratification not performed. |
| **SC-004** (Feasibility) | **ACTIVE** | Measured on test dataset. Global feasibility remains untested. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Task**: Download verified test pressure data and USGS data.
- **Task**: Validate checksums and schema.
- **Task**: Explicitly log the absence of global pressure data.

### Phase 1: Pre-processing
- **Task**: Interpolate pressure grid to 1°.
- **Task**: Thin earthquake catalog to ensure temporal independence (one event per time interval per region).
- **Task**: Calculate anomalies: Baseline (pre-event period), Event (t-48 to t).
- **Task**: Define control windows as fixed-duration UTC intervals in non-event years.

### Phase 2: Statistical Analysis
- **Task**: Run KS test and Permutation test (sufficient iterations for convergence).
- **Task**: Apply FDR correction.
- **Task**: Run sensitivity analysis with clean σ.

### Phase 3: Reporting
- **Task**: Generate report with "Pilot" label.
- **Task**: Document limitations (Global data blocked, no climate stratification).
