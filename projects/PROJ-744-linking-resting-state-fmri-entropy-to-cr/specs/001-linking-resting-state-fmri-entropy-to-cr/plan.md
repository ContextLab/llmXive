# Implementation Plan: Linking Resting‑State fMRI Entropy to Creative Problem Solving

**Branch**: `001-linking-resting-state-fmri-entropy` | **Date**: 2026-06-25 | **Spec**: `specs/001-linking-resting-state-fmri-entropy/spec.md`
**Input**: Feature specification from `/specs/001-linking-resting-state-fmri-entropy/spec.md`

## Summary
This project implements a computational pipeline to compute Multiscale Sample Entropy (MSE) from pre-processed HCP resting-state fMRI data and test its association with Alternative Uses Test scores. The pipeline strictly adheres to data hygiene, motion exclusion criteria (FD > 0.2mm or < 100 frames), and statistical rigor (Ordinary Least Squares with Robust Standard Errors, Benjamini-Hochberg FDR, and sensitivity analysis on tolerance `r` including surrogate data validation). The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners (limited CPU, 7GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `nibabel`, `scikit-learn`, `statsmodels`, `scipy`, `nilearn`, `tqdm` (all CPU-optimized, no CUDA).  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/logs`).  
**Testing**: `pytest` (unit tests for entropy calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational Research Pipeline / CLI.  
**Performance Goals**: Process full cohort within 6 hours; peak RAM < 7GB.  
**Constraints**: No GPU; strict exclusion logic for motion artifacts; sensitivity analysis must re-compute full multiscale AUC for each `r` value.  
**Scale/Scope**: A large cohort of subjects (HCP), 360 parcels, 7 canonical networks.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Reference / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, random seeds, and deterministic pipeline execution. |
| **II. Verified Accuracy** | **PASS** | Plan restricts dataset citations to the "Verified datasets" block in the prompt; no invented URLs. Phenotype data sourced from verified HCP release. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data, logging exclusions to `missing_data.log` and `motion_exclusions.log`, and preserving raw data unchanged. |
| **IV. Single Source of Truth** | **PASS** | All results trace to `data/processed/entropy_metrics*.csv` and `data/processed/model_results.csv`. |
| **V. Versioning Discipline** | **PASS** | Plan mandates content hashing of artifacts in `state/` and versioned `constitution.md`. |
| **VI. Neuroimaging Data Integrity** | **PASS** | Plan explicitly downloads pre-processed HCP 4-D volumes from OpenNeuro S3 bucket (ds000030), stores in `data/raw`, and logs derivation. |
| **VII. Statistical Modeling Transparency** | **PASS** | Plan mandates OLS with Robust SEs (per Spec US-2), FDR correction, and logging of all model specifications and sensitivity parameters. |

## Project Structure

### Documentation (this feature)

```text
specs/001-linking-resting-state-fmri-entropy/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── entropy_output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, parameters (m, r, scales)
├── data_loader.py       # HCP loading (S3), phenotype merging, motion scrubbing
├── entropy.py           # MSE computation, AUC aggregation, parcel loop
├── models.py            # OLS fitting, robust SEs, FDR correction
├── sensitivity.py       # Sweep logic, RAM/Runtime instrumentation, Surrogate generation
├── utils.py             # Logging, validation helpers
└── main.py              # Orchestration script

tests/
├── test_entropy.py
├── test_models.py
└── test_pipeline.py

data/
├── raw/                 # Downloaded HCP 4-D volumes, phenotypes (checksummed)
├── processed/           # Entropy CSVs, model results, logs
└── logs/                # motion_exclusions.log, missing_data.log, invalid_parcels.log

requirements.txt
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) selected to minimize overhead and ensure all scripts run sequentially in a single environment, fitting the GitHub Actions free-tier constraints.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Sensitivity Sweep (Re-computation)** | FR-005 & SC-002 require re-computing the *full* Multiscale (AUC) profile for `r` ∈ {0.15, 0.20, 0.25}. | A single-scale sensitivity check would violate the definition of MSE and the spec's requirement to validate the "Multiscale" metric. |
| **Motion Exclusion Logic** | Spec Edge Cases require two-tier exclusion: FD > 0.2mm (log) AND < 100 frames (exclude). | A single threshold check would fail to handle subjects with low motion but insufficient time points, violating data quality standards. |
| **RAM Instrumentation** | SC-003 requires peak RAM reporting to validate compute feasibility. | Standard logging does not capture peak memory usage; explicit instrumentation is required to prevent silent OOM failures on the 7GB runner. |
| **Surrogate Validation** | Scientific Soundness requires ensuring entropy captures non-linear structure, not noise. | Single-parameter sweeps are insufficient; phase-randomized surrogates are needed to rule out noise artifacts. |
| **OLS with Robust SEs** | Spec US-2 explicitly states LMM is invalid for cross-sectional data (1 obs/subject); OLS with Robust SEs is the correct approach. | LMM assumes multiple observations per subject; using it here would violate the statistical assumptions of the study design. |

## Implementation Phases & Tasks

### Phase 0: Initialization & Data Acquisition
- **T001**: Create project structure.
  - **Action**: Create directories: `code/`, `data/raw`, `data/processed`, `data/logs`, `tests/`, `docs/`.
  - **Output**: Directory structure.
- **T001b**: Download Raw Data.
  - **Action**: Download pre-processed 4-D fMRI volumes from OpenNeuro/HCP S3 bucket (ds000030) and phenotype data from HCP-1200 release. Verify checksums.
  - **Output**: `data/raw/*.nii.gz`, `data/raw/phenotypes.csv`.
  - **Constraint**: Must fail if download integrity check fails.

### Phase 1: Data Preprocessing & Motion Scrubbing
- **T006**: Load Data.
  - **Action**: Load raw NIfTI volumes and phenotype CSV.
  - **Output**: In-memory dataframes/arrays.
- **T007**: Motion Scrubbing & Exclusion.
  - **Action**: Compute Mean Framewise Displacement (FD).
  - **Action**: Exclude subjects with Mean FD > 0.2mm (log to `motion_exclusions.log`).
  - **Action**: **Exclude subjects with < 100 remaining frames after scrubbing** (log to `missing_data.log`).
  - **Action**: Generate a list of `valid_subjects`.
  - **Output**: List of valid subjects.

### Phase 2: Entropy Computation
- **T013**: Load Valid Subjects.
  - **Action**: Load **scrubbed** time series for **valid subjects only** (from T007).
- **T015**: Parcel-Level Entropy Loop.
  - **Action**: Iterate over valid subjects and 360 parcels.
  - **Action**: Compute Multiscale Sample Entropy (MSE) for a range of coarse-graining scales.
  - **Action**: Aggregate as Area Under the Curve (AUC).
  - **Action**: Handle NaNs: If >10% of parcels are invalid for a subject, **flag the subject for manual review** (log to `invalid_parcels.log`).
  - **Output**: `data/processed/entropy_metrics.csv`.
- **T015c**: Invalid Parcel Flagging.
  - **Action**: Implement specific logic to flag subjects with >10% invalid parcels.
  - **Output**: `invalid_parcels.log`.

### Phase 3: Primary Modeling
- **T022**: Load Merged Data.
  - **Action**: Join `entropy_metrics.csv` with Phenotype data.
  - **Constraint**: Must consume only the **filtered** subject list from T007 (excluding FD > 0.2mm and < 100 frames).
  - **Output**: Merged analysis dataframe.
- **T025**: Sample Size Validation.
  - **Action**: Check if N < 30.
  - **Action**: **If N < 30, halt execution immediately** and log critical warning. Do not proceed to modeling.
  - **Output**: Halt signal or proceed.
- **T026**: Fit OLS Models with Robust SEs.
  - **Action**: Fit **Ordinary Least Squares (OLS)** models with **Robust Standard Errors** (HC1) to test association between entropy and AUT scores, controlling for age, sex, and motion.
  - **Action**: Apply Rank-Based Inverse Normal Transformation (INT) to AUT scores if residuals are skewed.
  - **Action**: Compute FDR-corrected p-values.
  - **Output**: `data/processed/model_results.csv`.

### Phase 4: Sensitivity Analysis
- **T030a**: Re-compute Entropy (Sensitivity).
  - **Action**: **Re-compute Multiscale Sample Entropy (AUC across scales 1-20)** for each `r` value in {0.15, 0.20, 0.25}.
  - **Output**: `data/processed/entropy_metrics_r015.csv`, `entropy_metrics_r020.csv`, `entropy_metrics_r025.csv`.
- **T030b**: Re-model (Sensitivity).
  - **Action**: Fit OLS models for each sensitivity dataset.
  - **Output**: `data/processed/model_results_r*.csv`.
- **T030c**: Surrogate Validation.
  - **Action**: Generate phase-randomized surrogates of fMRI time series.
  - **Action**: Compute entropy and model on surrogates to validate non-linear structure.
  - **Output**: `data/processed/surrogate_results.csv`.
- **T030d**: Instrumentation.
  - **Action**: **Log peak RAM usage and runtime** for each sensitivity sweep iteration.
  - **Output**: `data/processed/sensitivity_metrics.log`.