# Implementation Plan: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Branch**: `001-neural-correlates-social-exclusion` | **Date**: 2026-07-01 | **Spec**: `specs/001-neural-correlates-social-exclusion/spec.md`
**Input**: Feature specification from `/specs/001-neural-correlates-social-exclusion/spec.md`

## Summary

This project investigates the modulation of Default Mode Network (DMN) functional connectivity dynamics during acute simulated social exclusion (Cyberball task). The technical approach involves downloading preprocessed fMRI data from OpenNeuro (specifically dataset ds000030), extracting BOLD time-series from DMN nodes (PCC, mPFC, angular gyrus), computing condition-specific (Inclusion vs. Exclusion) connectivity strength, and performing non-parametric paired permutation tests. The pipeline enforces strict motion artifact exclusion (>3mm), handles edge cases for insufficient sample size (N < 10), and frames results as associational unless randomization is verified.

**Critical Note**: This plan is currently **BLOCKED** pending the addition of a verified Cyberball dataset source to the project's verified dataset block. Without a verified source, the pipeline will halt gracefully as per the data strategy.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `scipy`, `pandas`, `huggingface_hub`, `scikit-learn`, `matplotlib`, `seaborn`, `nipype`, `nilearn`  
**Storage**: Local filesystem (`data/` for raw/processed, `results/` for outputs)  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM)  
**Project Type**: Scientific data analysis pipeline / CLI  
**Performance Goals**: Process full dataset within 6 hours; memory usage < 7 GB via streaming/chunking.  
**Constraints**: No local GPU; CPU-first execution; strict adherence to OpenNeuro data availability; motion threshold >3mm is a hard exclusion criterion.  
**Scale/Scope**: Single dataset (ds000030); A sample of subjects (depending on QC); DMN nodes; conditions.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Preprocessing Environment**:
The plan utilizes **fMRIPrep** for rigorous preprocessing (slice timing, realignment, normalization, smoothing). fMRIPrep is an external tool requiring a Docker or Singularity container environment; it is **not** installed via `pip`. The `nipype` Python library is used to orchestrate the fMRIPrep container execution and parse outputs. The `preprocessing.py` module will invoke the container with appropriate BIDS inputs and outputs.

**Data Fetching Strategy**:
The system prioritizes fetching data from the **Verified Datasets** block (HuggingFace mirrors). If the specific Cyberball dataset (`ds000030`) is not present in the verified block, the system falls back to the standard OpenNeuro BIDS API via `openneuro-py`. If neither source yields valid task data (Inclusion/Exclusion event markers), the pipeline halts with `ERR_DATA_UNVERIFIED`. No synthetic data or placeholder values are generated.

## Constitution Check

*Gates determined based on constitution file*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched via `huggingface_hub` or OpenNeuro API with checksum verification. |
| **II. Verified Accuracy** | **BLOCKED** | **Caveat**: The primary dataset (ds000030) is NOT in the verified dataset block. The pipeline is designed to fail gracefully if a verified source is not found. Status remains BLOCKED until a verified Cyberball dataset URL is added to the verified block. |
| **III. Data Hygiene** | PASS | Raw data preserved in `data/raw/`; checksums recorded; transformations write to new files in `data/processed/`. |
| **IV. Single Source of Truth** | PASS | All statistics derived from `data/processed/` matrices; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Artifact hashes updated in `state/` upon file modification; `updated_at` timestamps managed by agents. |
| **VI. fMRI Motion Artifact Exclusion** | PASS | Hard-coded exclusion logic: `if max_displacement > 3.0: exclude`. Error `ERR_N_INSUFFICIENT` raised if N < 10 post-QC. |
| **VII. State-Dependent Connectivity Quantification** | PASS | Metric defined as **mean signed correlation** of DMN edges per condition (Inclusion/Exclusion), not global resting state. |

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-correlates-social-exclusion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
projects/PROJ-474-neural-correlates-of-simulated-social-ex/
├── code/
│   ├── __init__.py
│   ├── config.py          # Paths, seeds, thresholds (3mm, N=10)
│   ├── data_loader.py     # OpenNeuro/HF download & streaming
│   ├── preprocessing.py   # Motion QC, ROI extraction, nuisance regression (wraps fMRIPrep)
│   ├── connectivity.py    # Correlation matrices, strength metric (signed & absolute)
│   ├── stats.py           # Permutation test, FDR correction
│   ├── edge_analysis.py   # Edge-wise testing (FR-011)
│   ├── viz.py             # Plotting (bar plots, null distributions, sensitivity curves)
│   └── main.py            # Pipeline orchestration
├── data/
│   ├── raw/               # Downloaded NIfTI/JSON (if cached)
│   ├── processed/         # Time-series, matrices, QC logs
│   └── checksums.json     # Integrity records
├── results/
│   ├── figures/           # Generated plots
│   └── report.md          # Final statistical summary
├── tests/
│   ├── test_preprocessing.py
│   ├── test_connectivity.py
│   ├── test_edge_analysis.py
│   └── test_stats.py
└── requirements.txt
```

**Structure Decision**: Single project structure selected. This is a linear scientific pipeline (Download -> QC -> Extract -> Analyze -> Report) rather than a multi-service application. The `code/` directory contains modular scripts for each stage, orchestrated by `main.py`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principle II (Verified Accuracy) | The study requires a specific Cyberball dataset (ds000030) which is not currently in the verified dataset block. | No alternative verified Cyberball dataset is available in the current block. The study cannot proceed without a verified source to avoid fabrication risks. |

## Methodology

### 1. Data Ingestion & Preprocessing (FR-001, FR-002)
- **Download**: Fetch fMRI NIfTI files and JSON sidecars from OpenNeuro (ds000030) via standard API if not in verified block.
- **Preprocessing**: Execute **fMRIPrep** (via Docker container) for slice timing correction, motion realignment, normalization to MNI space, and smoothing.
- **Motion QC**: Calculate framewise displacement (FD) and DVARS from fMRIPrep outputs for each subject.
- **Exclusion**: Exclude subjects with max displacement > 3mm.
- **Condition Segmentation**: Parse events.tsv to identify "Inclusion" and "Exclusion" trial indices.
- **Nuisance Regression**: **Crucial Step**: For all subjects passing QC, regress out motion parameters (and their derivatives) plus FD/DVARS from the BOLD time-series to control for residual motion effects and signal loss. This addresses selection bias concerns by statistically controlling for motion even in retained subjects.

### 2. ROI Extraction (FR-003)
- **Atlas**: Use Harvard-Oxford or AAL atlas.
- **Regions**: PCC (Posterior Cingulate Cortex), mPFC (medial Prefrontal Cortex), Angular Gyrus.
- **Extraction**: Mean BOLD signal from these ROIs for each condition segment (after nuisance regression).

### 3. Connectivity Computation (FR-004, FR-005, FR-011)
- **Edge-wise Calculation**: Compute Pearson correlation for **each individual edge** (PCC-mPFC, PCC-Angular, mPFC-Angular) separately for Inclusion and Exclusion conditions.
- **Primary Metric (Signed)**: Calculate the **mean signed correlation** across all DMN edges for a global summary metric. This preserves directionality (positive vs. negative) and avoids masking opposing effects.
- **Secondary Metric (Absolute)**: Calculate the mean absolute correlation as a descriptive statistic only, acknowledging its limitations.
- **Separation**: Compute separate strength values and edge-wise values for Inclusion and Exclusion.

### 4. Statistical Testing (FR-006, FR-007, FR-008, FR-011)
- **4a. Framing Check**: Read the dataset metadata JSON. If `randomization_verified` is missing or false, set `framing` to "associational" in all output reports.
- **4b. Global Test**: Paired permutation test (subject-level) comparing Inclusion vs. Exclusion **signed** strength.
- **4c. Edge-wise Test**: Perform separate paired permutation tests for each individual edge (3 tests).
- **4d. Correction**: FDR (q ≤ 0.05) applied to the 3 edge-wise p-values.
- **4e. Iterations**: Adaptive (e.g., `min(, 10 * N)`), bounded for CPU feasibility.

### 5. Sensitivity Analysis (SC-005)
- **Iterative Thresholding**: Re-run the QC and analysis pipeline for a range of motion thresholds (e.g., 2.5mm, 3.0mm, 3.5mm, 4.0mm).
- **Curve Generation**: Plot p-values (and effect sizes) against the motion threshold to visualize the stability of the result.
- **Reporting**: Include this curve in the final report to demonstrate robustness.

### 6. Edge Cases & Error Handling
- **N < 10**: Halt with `ERR_N_INSUFFICIENT`.
- **Missing Condition**: Exclude subject from paired analysis.
- **API Failure**: Retry with exponential backoff, then `ERR_DATA_UNAVAILABLE`.
- **No Verified Source**: If the dataset is not in the verified block and OpenNeuro API fails, halt immediately with `ERR_DATA_UNVERIFIED`.
- **No Placeholder Data**: Under no circumstances will synthetic data or hardcoded placeholder values be used. If data is missing, the pipeline halts.

## Compute Feasibility

- **CPU-First**: All operations (correlation, permutation) are CPU-tractable.
- **Memory**: Streaming fMRI data (using `nibabel` with memory mapping) ensures RAM usage stays < 7 GB. fMRIPrep runs in a containerized environment, isolated from the host RAM limit (though the host must have sufficient disk space for intermediate files).
- **Time**: Permutation test (N < 50, 1000 iterations) runs in minutes on a small number of CPU cores. fMRIPrep preprocessing is the most time-consuming step but is optimized via parallel processing where possible.
- **GPU**: Not required. No deep learning models are used.

## Statistical Rigor

- **Multiple Comparisons**: FDR correction applied to edge-wise tests (3 edges).
- **Power**: Acknowledged limitation if N is small; permutation test is robust for small N but power is limited.
- **Causal Claims**: Explicitly avoided; results framed as "associational" per FR-007.
- **Collinearity**: Acknowledged that DMN nodes are highly correlated; mean **signed** correlation is used as a summary metric to avoid independent effect claims on collinear predictors while preserving directionality.
- **Validation**: Statistical significance is assessed via permutation. Biological plausibility is assessed via external benchmarking against literature effect sizes.

## Data Availability & Feasibility

- **Primary Source**: OpenNeuro ds000030 (Cyberball).
- **Verified Status**: **NOT VERIFIED** in the current project block.
- **Execution Path**: The pipeline will attempt to fetch from the verified block first. If not found, it will attempt the standard OpenNeuro API. If the API fetch fails or is not permitted in the CI environment, the pipeline halts with `ERR_DATA_UNVERIFIED`. **No synthetic or placeholder data will be generated.**
- **Fallback**: If no verified Cyberball dataset is available, the study is **blocked** until a verified source is provided.
