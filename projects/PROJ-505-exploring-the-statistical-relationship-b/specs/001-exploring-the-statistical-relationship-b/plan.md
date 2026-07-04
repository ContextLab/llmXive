# Implementation Plan: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Branch**: `001-solar-wind-composition-geomagnetic` | **Date**: 2026-06-25 | **Spec**: `specs/001-solar-wind-composition-geomagnetic/spec.md`
**Input**: Feature specification from `/specs/001-solar-wind-composition-geomagnetic/spec.md`

## Summary

**Project Status**: Methodology Demonstration & Pipeline Validation (Data Gap).  
**Critical Constraint**: Verified real-world sources for ACE SWICS composition ratios (O/Fe, He/H, C/O) and NOAA Dst/Kp indices are **not available** in the provided "Verified datasets" block.  
**Strategy**: This project implements and validates the **statistical pipeline** (ingestion, alignment, multivariate regression, block permutation, FDR) using **synthetic data** that mimics the expected distributions of the real variables. The scientific hypothesis (whether composition predicts storms) **cannot be tested** with this data. The project's success is defined by the correct execution of the statistical methods and the generation of reproducible code artifacts.

The approach involves:
1.  **Data Gap Handling**: Attempting to fetch real data from CDAWeb/NOAA (expected to fail or return incomplete data).
2.  **Synthetic Data Generation**: Creating a 20-year hourly dataset with realistic bulk parameters and composition ratios to validate the pipeline.
3.  **Statistical Analysis**: Performing multivariate regression, -fold cross-validation, and block permutation tests on the synthetic data to ensure the pipeline correctly identifies signals (if injected) or null results.
4.  **Reporting**: Explicitly documenting the data gap and the limitations of the findings.

All analysis is constrained to run on CPU-only GitHub Actions runners with limited CPU and RAM resources.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy` (all CPU-optimized wheels). No deep learning frameworks required.  
**Storage**: Local CSV/Parquet files in `data/` (synthetic aligned datasets) and `artifacts/` (model outputs).  
**Testing**: `pytest` for unit tests on data ingestion logic and regression metrics; `pytest` integration tests for full pipeline execution on synthetic data.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, 14GB disk).  
**Project Type**: Data analysis CLI / Research pipeline (Methodology Demonstration).  
**Performance Goals**: Complete synthetic data generation and analysis within 6 hours; memory usage < 6GB during peak processing.  
**Constraints**: No GPU usage; no large language models; data is synthetic for pipeline validation.  
**Scale/Scope**: A multi-year period of synthetic hourly solar wind and geomagnetic data; composition ratios; geomagnetic indices.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference |
|-----------|--------|-----------|
| **I. Reproducibility** | **PARTIAL (Pipeline)** | Plan mandates pinned `requirements.txt`, random seeds in code, and re-runnable scripts in `code/`. Reproducibility applies to the *pipeline* using synthetic data, not the scientific hypothesis due to data unavailability. |
| **II. Verified Accuracy** | **PARTIAL (Data Gap)** | Plan restricts dataset citations to the "Verified datasets" block. Since no verified sources for ACE SWICS/NOAA Dst/Kp exist, the plan uses synthetic data. The "Verified Accuracy" gate is satisfied by explicitly documenting the data gap and not fabricating real data citations. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of synthetic data generation parameters and ensures raw synthetic files are never modified in place. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the final output will be generated directly from `code/` artifacts, not hand-typed. |
| **V. Versioning Discipline** | **PASS** | Plan includes content hashes for artifacts in the state file (managed by the runtime/agent). |
| **VI. Composition Data Integrity** | **PARTIAL (Synthetic)** | Plan explicitly separates synthetic data generation from derived ratio calculation. Raw synthetic files are preserved and transformations documented. Real data integrity cannot be satisfied due to data unavailability. |
| **VII. Statistical Validation** | **PASS** | Plan mandates 5-fold CV, permutation tests (A sufficient number of iterations will be performed to ensure convergence and stability in the results.), and VIF checks for multicollinearity as per the spec. These validate the *pipeline*, not the physical hypothesis. |

## Project Structure

### Documentation (this feature)

```text
specs/001-solar-wind-composition-geomagnetic/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-505-exploring-the-statistical-relationship-b/
├── code/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── download_ace.py      # FR-001: Data Gap Handler (Attempt Real -> Fallback Synthetic)
│   │   ├── download_noaa.py     # FR-002: Data Gap Handler (Attempt Real -> Fallback Synthetic)
│   │   ├── generate_synthetic_data.py # Synthetic Data Generator (Primary Data Source)
│   │   └── align.py             # FR-003: Temporal Alignment (Real & Synthetic)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── coupling_functions.py # Derive epsilon/Newell
│   │   ├── regression.py         # FR-004, FR-005, FR-006, FR-011
│   │   ├── cross_validation.py   # FR-007
│   │   ├── permutation_test.py   # FR-008
│   │   └── sensitivity.py        # FR-009, FR-010
│   ├── utils/
│   │   ├── __init__.py
│   │   └── io.py                # Checksums, parquet loading
│   └── main.py                  # Orchestration script
├── data/
│   ├── raw/                     # Downloaded raw files (if any) or synthetic source files
│   ├── processed/               # Aligned hourly datasets (synthetic)
│   └── artifacts/               # Model outputs, CSVs, plots
├── tests/
│   ├── unit/
│   │   ├── test_ingestion.py
│   │   └── test_coupling.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular Python package structure is selected. `ingestion` handles data retrieval (with fallback to synthetic generation) and alignment (FR-001 to FR-003). `analysis` encapsulates the statistical workflow (FR-004 to FR-011). This separation ensures that data hygiene (raw vs. processed) is maintained and that statistical modules can be tested independently. The `utils` module handles I/O and checksumming to satisfy Constitution Principle III.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Block Permutation Test** | Required by FR-008 and US-3 to validate statistical significance against temporal autocorrelation. | Simple random permutation would violate the time-series nature of the data, leading to inflated Type I errors. |
| **Coupling Functions** | Required by FR-004 and US-2 to capture non-linear physics (Akasofu epsilon) before testing composition. | Raw linear sums of velocity/IMF fail to capture the known physics of solar wind-magnetosphere coupling, making the baseline model scientifically invalid. |
| **FDR Correction** | Required by FR-010 to handle multiple hypothesis testing (3 ratios x 2 indices). | Bonferroni correction is overly conservative for this number of tests; FDR balances Type I/II error control better. |
| **Synthetic Data Generation** | Required due to the absence of verified real-world data sources for ACE SWICS and NOAA Dst/Kp. | Proceeding without data would result in an incomplete project. Synthetic data allows for pipeline validation and code correctness testing. |

## Data Availability & Limitations

**Critical Data Gap**: The "Verified datasets" block does not contain verified sources for ACE SWICS composition ratios (O/Fe, He/H, C/O) or NOAA Dst/Kp indices.
- **ACE SWICS**: No verified URL found. The `ij5/ace` HuggingFace dataset may contain bulk parameters but likely lacks specific SWICS composition ratios.
- **WIND Spacecraft**: No verified URL found. The OpenML "wind.csv" dataset is meteorological and irrelevant.
- **NOAA Dst/Kp**: No verified URL found. The listed NOAA buoy datasets are oceanographic and irrelevant.

**Mitigation Strategy**:
1.  **Attempt Real Fetch**: The ingestion scripts (`download_ace.py`, `download_noaa.py`) will attempt to fetch data from the specified sources (CDAWeb/NOAA) using standard HTTP requests.
2.  **Fallback to Synthetic**: If the real fetch fails (expected) or returns incomplete data, the system will automatically switch to `generate_synthetic_data.py` to create a synthetic dataset with realistic distributions.
3.  **Explicit Documentation**: All outputs will clearly label the data as synthetic and state that the scientific hypothesis cannot be tested.

**Impact on Success Criteria**:
- SC-001, SC-002, SC-003, SC-004: These criteria will be evaluated on the synthetic data to validate the *pipeline*. The project will not claim to have answered the scientific question about real solar wind composition.

## Compute Feasibility

* **Data Size**: 20 years of hourly data $\approx [deferred]$ rows. This fits easily in 7GB RAM.
*   **Compute**: Linear regression and permutation tests (A sufficient number of iterations) on 175k rows are CPU-tractable. No GPU required.
*   **Runtime**: Estimated < 1 hour on a standard CPU.
*   **Subsampling**: Not required for the 20-year hourly dataset. Subsampling is only a contingency for future higher-resolution data or if the synthetic generator produces excessive data.