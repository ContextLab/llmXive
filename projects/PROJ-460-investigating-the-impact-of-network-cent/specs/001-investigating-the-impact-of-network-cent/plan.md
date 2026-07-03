# Implementation Plan: Investigating Network Centrality in ASD Resting-State fMRI

**Branch**: `001-investigate-asd-centrality` | **Date**: 2025-01-10 | **Spec**: `specs/001-investigating-the-impact-of-network-cent/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-impact-of-network-cent/spec.md`

## Summary

This project implements a computational pipeline to investigate the impact of network centrality (degree, betweenness, eigenvector) on resting-state functional connectivity in Autism Spectrum Disorder (ASD). The technical approach involves downloading ABIDE fMRI data, preprocessing it with fMRIPrep, parcellating using the Schaefer atlas, computing centrality metrics via NetworkX, and performing statistical group comparisons with FDR correction.

**CRITICAL STATUS**: The scientific analysis pipeline is currently **BLOCKED** due to the absence of a verified real fMRI data source in the project's `# Verified datasets` block. The plan below outlines the required steps **contingent upon** the acquisition of valid ABIDE data. **No synthetic data is permitted for scientific results.**

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `nibabel`, `nilearn`, `networkx`, `scikit-learn`, `pandas`, `numpy`, `scipy`, `fmriprep` (via Docker)
**Storage**: Local file system (`data/raw/`, `data/processed/`), Parquet/CSV for tabular outputs.
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline stages).
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM).
**Project Type**: Computational neuroscience analysis pipeline.
**Performance Goals**: Complete preprocessing and analysis for a subset of participants (or batch processing) within 6 hours; memory usage < 6 GB.
**Constraints**: No GPU access; no large language model inference; fMRIPrep must run in CPU mode; data must be subset to fit RAM.
**Scale/Scope**: A cohort of participants (ASD + Control), ~400 ROIs, Several centrality metrics.

> **Data Dependency Note**: All downstream phases (Preprocessing, Centrality, Statistics, Visualization) are strictly dependent on the successful acquisition of real, raw fMRI data (NIfTI) from a verified source. If no such source is available, the pipeline halts at the Data Acquisition phase. **No scientific results will be generated without real data.**

## Constitution Check

*Gates determined based on `projects/PROJ-460-investigating-the-impact-of-network-cent/.specify/memory/constitution.md`*

| Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All code pinned in `requirements.txt`; random seeds fixed in `code/config.py`; Docker image hash recorded in provenance. |
| **II. Verified Accuracy** | **FAILED** | **Status**: Cannot verify accuracy of results because the required raw fMRI data source is missing from the verified datasets block. **Action**: Pipeline halts until a valid ABIDE source is added. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw/` unchanged; derivations written to new files; checksums recorded in `state/...yaml`. |
| **IV. Single Source of Truth** | **PASS** | All statistics in `paper/` will be generated directly from `data/` outputs via scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes generated for all artifacts; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Neuroimaging Data Integrity** | **FAILED** | **Status**: Raw fMRI scans from ABIDE are not available in the verified list. **Action**: Pipeline cannot preserve or process raw scans until a valid source is provided. |
| **VII. Statistical Rigor** | **FAILED** | **Status**: Statistical tests (t-tests, FDR) are invalid without real biological data. **Action**: Analysis phase is blocked until real data is acquired. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-impact-of-network-cent/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration, seeds, paths
├── provenance.json      # fMRIPrep version, parameters, checksums
├── download.py          # ABIDE data acquisition (BLOCKED if no source)
├── preprocess.py        # fMRIPrep wrapper (CPU mode)
├── analysis/
│   ├── __init__.py
│   ├── centrality.py    # NetworkX metric computation
│   ├── stats.py         # T-tests, FDR, collinearity
│   └── classification.py # Logistic regression, CV
├── viz/
│   └── brain_maps.py    # Nilearn surface visualization
└── tests/
    ├── test_centrality.py
    └── test_stats.py

data/
├── raw/                 # Unmodified ABIDE data
├── processed/           # Preprocessed time series, connectivity matrices
└── outputs/             # Statistical results, figures

requirements.txt
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing and analysis, facilitating the "Single Source of Truth" principle. The `code/` directory contains all executable logic, while `data/` is strictly for artifacts.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Docker-based fMRIPrep** | Essential for standardized, reproducible neuroimaging preprocessing (motion correction, normalization). | Manual preprocessing scripts are error-prone and lack the rigorous quality control of fMRIPrep. |
| **Sensitivity Analysis (Threshold Sweep)** | Required by FR-009 to ensure robustness of findings against arbitrary threshold choices. | Reporting results at a single threshold is scientifically insufficient for network neuroscience. |
| **Collinearity Diagnostics** | Required by FR-010 because centrality metrics are mathematically correlated. | Claiming independent effects would be statistically invalid and misleading. |
| **Real Data Requirement** | Scientific validity requires real biological data. | Synthetic data cannot validate hypotheses about ASD pathology; using it would violate Principle VI and scientific soundness. |

## Data Acquisition Blocker (FR-001, FR-002)

**Current State**: **BLOCKED**
**Reason**: The `# Verified datasets` block does not contain a source for raw resting-state fMRI data (NIfTI files) required by FR-001 and FR-002.
**Resolution Requirement**:
1.  A valid ABIDE data source (e.g., official ABIDE website, verified HuggingFace dataset with raw NIfTI) must be identified and added to the `# Verified datasets` block.
2.  Once added, the `download.py` script will be updated to fetch from this new source.
3.  The pipeline will proceed to preprocessing (FR-002) only after real data is successfully downloaded and checksummed.
4.  **No synthetic data** will be used to bypass this blocker or to generate "illustrative" scientific results.

## Compute Feasibility (Conditional)

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
*   **Bottlenecks**: fMRIPrep is memory intensive.
*   **Mitigation Strategy (Pending Real Data)**:
    *   If real data is acquired, the pipeline will attempt to run fMRIPrep on a **subset** of subjects first to validate memory usage.
    *   If memory constraints are exceeded, the pipeline will process subjects in **batches** or reduce the number of subjects, acknowledging the impact on statistical power.
    *   **Note**: Running fMRIPrep on a large cohort of subjects on a 7GB RAM runner is likely infeasible. The plan will prioritize data integrity over sample size if necessary, or seek alternative compute resources.
    *   **No Synthetic Fallback**: If real data cannot be processed due to compute constraints, the project will report power limitations and halt, rather than simulating data.
*   **Centrality & Stats**: NetworkX and scikit-learn are CPU-tractable for the expected data sizes (400 nodes, ~ subjects).

## Unit Testing vs. Scientific Analysis

*   **Unit Tests**: `code/tests/` may use **mock data** (e.g., small random matrices) to verify that the code logic (e.g., centrality calculation, FDR correction) functions correctly. This is strictly for code validation.
*   **Scientific Analysis**: The main pipeline (`code/download.py`, `code/preprocess.py`, `code/analysis/`) **MUST NOT** execute on mock or synthetic data for the purpose of generating scientific results. If real data is unavailable, the scientific pipeline halts.

## Pipeline Status

*   **Mode**: Code Validation (Mock Data) / Scientific Analysis (Blocked)
*   **Status**: **SCIENTIFIC ANALYSIS BLOCKED**
*   **Reason**: Missing verified real fMRI data source.
*   **Next Steps**:
    1.  Identify and add a verified real fMRI data source to the `# Verified datasets` block.
    2.  Update the `download.py` script to fetch from the new source.
    3.  Re-run the pipeline to generate real scientific results.

## Task List (Pending Data Acquisition)

1.  **Task 0: Acquire Real Data** (Mandatory, Blocks All Others)
    *   Identify a verified source for raw ABIDE fMRI data.
    *   Update `# Verified datasets` block.
    *   Implement `download.py` to fetch and checksum data.
2.  **Task 1: Preprocess Data**
    *   Run fMRIPrep (CPU mode) on acquired data.
    *   Handle memory constraints via batching/subsetting.
3.  **Task 2: Compute Centrality Metrics**
    *   Parcellate data using Schaefer atlas.
    *   Compute degree, betweenness, eigenvector centrality.
4.  **Task 3: Statistical Analysis**
    *   Perform t-tests with FDR correction.
    *   Conduct sensitivity analysis (threshold sweep).
    *   Perform collinearity diagnostics.
5.  **Task 4: Classification & Visualization**
    *   Train logistic regression classifier.
    *   Generate brain surface visualizations.
6.  **Task 5: Reporting**
    *   Generate final report and paper artifacts.