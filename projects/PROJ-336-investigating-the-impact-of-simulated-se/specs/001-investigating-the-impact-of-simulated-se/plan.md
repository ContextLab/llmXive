# Implementation Plan: Investigating the Impact of Simulated Sensory Deprivation on Resting-State Brain Network Dynamics

**Branch**: `001-sensory-deprivation-network-dynamics` | **Date**: 2024-01-15 | **Spec**: `specs/001-sensory-deprivation-network-dynamics/spec.md`
**Input**: Feature specification from `/specs/001-sensory-deprivation-network-dynamics/spec.md`

## Summary

This project implements a CPU-tractable pipeline to analyze resting-state fMRI data. The goal is to quantify changes in brain network topology (modularity, global efficiency, node strength) between pre-deprivation and post-deprivation conditions. The pipeline adheres to strict GitHub Actions free-tier constraints (limited CPU, constrained RAM, limited disk, 6h runtime).

**Critical Dataset Note**: The plan explicitly acknowledges that no dataset in the provided "Verified datasets" block contains confirmed pre/post sensory deprivation scans. The pipeline is designed to halt with a "Dataset Lacks Required Labels" error if no suitable data is found, rather than using an incorrect dataset.

The analysis uses MANOVA followed by univariate tests with FDR correction to handle metric interdependence, and permutation testing to validate findings.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `networkx`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `bids-validator`, `requests`  
**Storage**: Local file system (temporary) under `data/` and `results/`; compressed `.npy` and `.csv` formats.  
**Testing**: `pytest` (unit tests for metric computation, integration tests for pipeline stages).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational Research Pipeline / CLI Tool  
**Performance Goals**: Complete full analysis of a sample subset (n=20 subjects) within 6 hours on CPU-only runner.  
**Constraints**: No GPU/CUDA; memory usage < 7GB; disk usage < 14GB; runtime < 6h.  
**Scale/Scope**: 20-24 subjects, 200-400 ROIs, 2 conditions (pre/post).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action/Notes |
|-----------|-------------------|--------------|
| **I. Reproducibility** | **PASS** | All code in `code/` will pin random seeds (`numpy`, `torch`, `random`). External datasets fetched via canonical OpenNeuro/HF URLs. `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **WARN** | The "Verified datasets" block does not contain a confirmed sensory deprivation dataset. The plan explicitly halts if no suitable data is found. Citations are limited to the verified block or explicitly flagged as "Unverified/Gap". |
| **III. Data Hygiene** | **PASS** | Raw data will be checksummed (SHA256) upon download. Derivations (preprocessed data, metrics) written to new files. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the final report will be generated programmatically from `data/` artifacts. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be tracked with content hashes in `state/`. |
| **VI. Neuroimaging Preprocessing Integrity** | **PASS** | Preprocessing pipeline (motion correction, normalization, bandpass) will be version-locked. Parameters recorded in `code/`. Pre/post conditions processed identically. |
| **VII. Network Neuroscience Statistical Validation** | **PASS** | Plan includes MANOVA, paired t-tests with FDR correction, and permutation testing (≥1,000 iterations) as required. Effect sizes (Cohen's d) will be reported. |

## Project Structure

### Documentation (this feature)

```text
specs/001-sensory-deprivation-network-dynamics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Downloads and validates dataset
│   ├── preprocess.py        # Motion correction, normalization, filtering
│   └── quality_check.py     # Computes FD, excludes subjects, calculates covariates
├── analysis/
│   ├── connectivity.py      # Computes correlation matrices
│   ├── metrics.py           # Computes modularity, efficiency, node strength
│   └── stats.py             # MANOVA, paired t-tests, FDR, permutation testing
├── viz/
│   ├── plot_networks.py     # Degree distributions, heatmaps
│   └── plot_metrics.py      # Pre/post comparisons
├── utils/
│   ├── atlas.py             # Loads Schaefer/AAL atlas
│   └── io.py                # JSON/YAML handling
├── main.py                  # Orchestration script
└── config.py                # Configuration (paths, thresholds)

tests/
├── unit/
│   ├── test_metrics.py
│   └── test_stats.py
└── integration/
    └── test_pipeline.py

requirements.txt
README.md
```

**Structure Decision**: Single project structure with modular `src/` subdirectories for data, analysis, and visualization. This keeps the pipeline simple and maintainable for a research project. Tests are separated into unit and integration.

## Data Flow & Artifact Mapping

| Entity | Generating Script | Output File Format |
|--------|-------------------|--------------------|
| **Subject** (Raw) | `src/data/download.py` | `data/raw/` (NIfTI/JSON) |
| **Subject** (Processed) | `src/data/preprocess.py` | `data/preprocessed/` (NIfTI) |
| **Subject** (FD Metrics) | `src/data/quality_check.py` | `data/quality/` (JSON) |
| **Connectivity Matrix** | `src/analysis/connectivity.py` | `data/connectivity/` (.npy) |
| **Network Metrics** | `src/analysis/metrics.py` | `results/metrics.csv` |
| **Statistical Results** | `src/analysis/stats.py` | `results/stats.csv` |

## Disk Quota Enforcement

To guarantee the 14GB limit:
1.  **Raw Data Deletion**: Raw NIfTI files are deleted immediately after successful preprocessing and checksumming.
2.  **Checkpointing**: Intermediate results are saved at regular intervals. If disk usage approaches a critical threshold, the pipeline halts and logs a warning.
3.  **Compression**: All intermediate arrays are saved as `float32` in `.npy` format. CSVs are compressed with gzip.
4.  **Sampling**: If the full dataset exceeds limits, a subset of subjects (n=20) is selected deterministically.

## Requirements.txt Pinning

As per FR-010 and Constitution Principle I:
-   `requirements.txt` will be generated in `projects/PROJ-336-investigating-the-impact-of-simulated-se/code/` (or root if root is code).
-   Every dependency will be pinned to a specific version (e.g., `nibabel==5.1.0`).
-   The `requirements.txt` is treated as a source artifact; changes require a version bump.

## Sensitivity Analysis

To satisfy SC-005:
-   **Motion Threshold Sweep**: The pipeline will run the exclusion logic with varying thresholds to evaluate sensitivity across different exclusion criteria.
-   **Effect Size Sweep**: Statistical significance will be reported for small, medium, and large Cohen's d thresholds.
-   **Output**: A sensitivity report will be generated showing how the number of significant findings changes with these thresholds.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project adheres to the single-project structure. | N/A |