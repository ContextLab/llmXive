# Implementation Plan: Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

**Branch**: `001-neural-mechanisms-adaptive-decision` | **Date**: 2024-05-21 | **Spec**: `specs/001-neural-mechanisms-adaptive-decision/spec.md`
**Input**: Feature specification from `/specs/001-neural-mechanisms-adaptive-decision/spec.md`

## Summary

This project implements a computational neuroscience pipeline to analyze the neural mechanisms of adaptive decision-making using the **OpenNeuro ds003694** dataset. The system ingests **raw fMRI NIfTI files** and behavioral logs, performs full preprocessing (motion correction, normalization, smoothing), and extracts BOLD signals from specific Regions of Interest (ROIs). It then fits a hierarchical Bayesian model to estimate belief-updating rates and correlates these parameters with neural activation patterns using GLM and voxel-wise permutation testing with FDR correction. All steps are designed to run on a CPU-only environment (GitHub Actions free-tier) within 6 hours.

**Scope Confirmation**: The verified dataset (OpenNeuro ds003694) contains raw NIfTI files and behavioral logs, enabling full execution of FR-001 (Raw Preprocessing) and FR-004 (Voxel-wise Inference) as specified. No simulation or fallback to pre-extracted metrics is required.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `scikit-learn`, `nibabel`, `nilearn`, `pymc` (with `numpyro` CPU backend), `pytest`, `pyyaml`, `openneuro-py`, `nipype` (for fMRIPrep wrapper if needed, or custom `nibabel` pipeline)  
**Storage**: Local filesystem (`.nii.gz`, `.parquet`, `.csv`), no external database.  
**Testing**: `pytest` (unit, integration, contract validation).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Research Data Pipeline / Computational Neuroscience Library.  
**Performance Goals**: Runtime ≤ 6 hours on 2 CPU cores; Memory ≤ 6GB peak.  
**Constraints**: No GPU, no CUDA, no 8-bit quantization. Data must be sampled/filtered to fit RAM.  
**Scale/Scope**: Single-cohort analysis; Target N=30 (or full dataset size if <30) for power.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All scripts will pin seeds (`numpy.random.seed`, `pymc.set_seed`). `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` will strictly use the provided "Verified datasets" block (OpenNeuro ds003694). |
| **III. Data Hygiene** | PASS | Raw data (`.nii.gz`) will be preserved; processed outputs will be new files with checksums recorded in `state/`. |
| **IV. Single Source of Truth** | PASS | All figures/stats in the final report will be generated via code from `data/` artifacts. |
| **V. Versioning Discipline** | PASS | `sha256sum` script will compute hashes for `data/` and `code/` artifacts, storing results in `state/artifact_hashes.yaml`. |
| **VI. Neuroimaging Data Integrity** | PASS | Preprocessing parameters (motion, normalization) are documented. ROI extraction limited to dlPFC, VS, ACC. Voxel-wise FDR correction via permutation testing. |
| **VII. Computational Model Validation** | PASS | Hierarchical Bayesian model will be validated on held-out data. Uncertainty intervals (HDI) will be reported. |

## Versioning & Hashing

To satisfy Constitution Principle V:
1. **Tool**: A Python script `code/utils/hash_artifacts.py` will compute `sha256` checksums for all files in `data/raw/`, `data/processed/`, and `code/`.
2. **Storage**: Checksums will be stored in `state/artifact_hashes.yaml` in the format:
   ```yaml
   artifacts:
     data/raw/sub-01_task-social_bold.nii.gz: "abc123..."
     code/preprocessing/roi_extraction.py: "def456..."
   ```
3. **Validation**: The CI pipeline will verify these hashes on every run. Any mismatch invalidates the run and triggers a re-download/re-processing.

## Project Structure

### Documentation (this feature)

```text
specs/001-neural-mechanisms-adaptive-decision/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 6 output (Report generation)
```

### Source Code (repository root)

```text
projects/PROJ-011-neural-mechanisms-underlying-adaptive-de/
├── data/
│   ├── raw/             # Raw fMRI (NIfTI) and behavioral logs (OpenNeuro)
│   ├── processed/       # Preprocessed fMRI, ROI time-series, behavioral matrices
│   └── models/          # Saved model parameters (pickle/h5)
├── code/
│   ├── __init__.py
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── data_validation.py  # Verify OpenNeuro assets
│   │   ├── motion_correction.py # Motion correction (fMRIPrep wrapper or custom)
│   │   ├── normalization.py     # Spatial normalization
│   │   ├── smoothing.py         # Spatial smoothing
│   │   └── roi_extraction.py    # Extract from preprocessed volumes
│   ├── modeling/
│   │   ├── __init__.py
│   │   ├── belief_updater.py  # Hierarchical Bayesian model (pymc/numpyro)
│   │   └── validation.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── glm_analysis.py
│   │   └── permutation_test.py
│   ├── utils/
│   │   ├── io.py
│   │   ├── hashing.py
│   │   └── config.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular sub-packages (`preprocessing`, `modeling`, `analysis`) to ensure separation of concerns and testability. This aligns with the requirement for a reproducible pipeline where each step can be validated independently.

## Complexity Tracking

> No violations detected. The complexity is driven by the multi-stage pipeline (Validation -> Preprocessing -> Modeling -> Analysis) which is necessary to satisfy FR-001 through FR-006 under data constraints.

## Phase Breakdown (Mapping to FR/SC)

| Phase | Step | FR/SC Mapped | Description |
| :--- | :--- | :--- | :--- |
| **P0** | Data Acquisition & Raw Preprocessing | FR-001, SC-001 | Download OpenNeuro ds003694. **Preprocess** raw NIfTI (motion correction, normalization, smoothing). Extract motion parameters from logs. Exclude participants if motion > 3mm (SC-001). |
| **P1** | ROI Extraction | FR-001, SC-001 | Extract BOLD signals from dlPFC, VS, ACC from preprocessed volumes. Compute discrepancy regressors. |
| **P2** | Behavioral Modeling | FR-002, SC-002, SC-007 | Fit Hierarchical Bayesian model (pymc/numpyro) for belief updating (alpha). **Target N=30**. Validate on held-out data. Monitor convergence (R-hat < 1.01). |
| **P3** | Neural-Behavioral Correlation | FR-003, FR-005, SC-003 | GLM analysis of feedback discrepancy. Partial correlation of neural activation vs. alpha (with LOSO cross-validation to avoid tautology). Control for confounds (motion, global signal). |
| **P4** | Voxel-Wise Inference | FR-004, SC-004 | Permutation testing (1000 perms) with FDR correction **across full brain volume** (voxel-wise). |
| **P5** | Sensitivity Analysis | FR-006, SC-005 | Sweep updating thresholds; report stability of correlation coefficients. |
| **P6** | Reporting & Tasks | SC-001..005 | Generate final stats, figures, `tasks.md`, and validation reports. |

## Compute Feasibility Strategy

- **Memory**: Data will be loaded in chunks. fMRI volumes will be masked to ROI masks immediately after loading to reduce dimensionality.
- **CPU**: `pymc` with `numpyro` backend (CPU). **Target N=30**. MCMC: 4 chains, 2000 samples (total 8000 draws) to ensure convergence (R-hat < 1.01) within 6h.
- **Parallelism**: Python `multiprocessing` will be used for participant-level loops (P1, P2, P5), limited to 2 workers to avoid OOM on 7GB RAM.
- **Fallback**: If a participant's model fails to converge after 3 restarts (Edge Case), they are excluded and logged (FR-002).
- **Power**: Target N=30 provides [deferred] power to detect r=0.3 at alpha=0.05. If dataset N < 30, power limitation is explicitly reported.
- **Preprocessing**: Use lightweight `nibabel`/`nilearn` pipelines for motion correction and normalization to fit within 6h. Avoid heavy `fMRIPrep` if possible; use simplified spatial normalization if necessary.

## Data Availability & Validation (P0)

- **Source**: OpenNeuro ds003694 (Social Feedback fMRI).
- **Validation**: A script `code/preprocessing/data_validation.py` will verify the presence of:
  1. Raw NIfTI files (`*_bold.nii.gz`) for all participants.
  2. Behavioral logs with `private_belief`, `social_feedback`, `choice`.
  3. Motion logs (framewise displacement) or ability to calculate from raw data.
- **Action**: If any required asset is missing, the participant is excluded, and the exclusion reason is logged for SC-001.

## Statistical Rigor Addendum

- **Multiple Comparisons**: FDR correction applied across the **full brain volume** in P4.
- **Power**: Target N=30. If N < 30, power analysis is reported.
- **Causal Claims**: Study is observational. Claims framed as **associational**.
- **Collinearity**: Partial correlation controls for input discrepancy magnitude. **Cross-validation (LOSO)** used to ensure neural-behavioral link is not spurious.
- **Confound Control**: GLM includes motion parameters, their derivatives, and CompCor (aCompCor) components to control for physiological noise and motion residuals. Global signal regression is considered if data permits.
- **Tautology Mitigation**: The correlation between `alpha` (behavioral) and `beta_discrepancy` (neural) is controlled for the input discrepancy signal and validated via LOSO to ensure the link is not driven by the shared input.

## Versioning Discipline

- Every file in `data/` is checksummed with `sha256sum`.
- Checksums are stored in `state/artifact_hashes.yaml`.
- `data_hash` in `Participant` entity links to the specific version of the raw data used.
