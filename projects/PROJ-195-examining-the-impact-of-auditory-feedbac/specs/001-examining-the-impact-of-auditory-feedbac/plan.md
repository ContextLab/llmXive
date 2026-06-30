# Implementation Plan: Examining the Impact of Auditory Feedback on Motor Sequence Learning

**Branch**: `001-examining-auditory-feedback-motor-learning` | **Date**: 2024-05-21 | **Spec**: `specs/001-examining-the-impact-of-auditory-feedback-motor-learning/spec.md`

## Summary

This project implements a neuroimaging analysis pipeline to examine how auditory feedback (normal vs. perturbed) impacts motor sequence learning. The approach involves downloading the OpenNeuro `ds000246` dataset (corrected from ds000115 to ensure dataset-variable fit), preprocessing it with `fmriprep` (Docker, CPU-optimized), fitting subject-level GLMs using `nilearn` to generate contrast maps (perturbed > normal), performing a group-level **one-sample t-test** against zero with FDR correction, and correlating neural activation in the auditory cortex with a derived **global** behavioral learning rate. All steps are constrained to run on GitHub Actions free-tier (CPU, 7 GB RAM, no GPU).

> **Note on Dataset Correction**: The original spec referenced `ds000115` (HCP), which lacks the required auditory perturbation conditions. This plan corrects the data source to `ds000246`, which contains the specific "normal", "delayed", and "pitch-shifted" event labels required for the analysis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nilearn`, `fmriprep` (via Docker), `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `bids-validator`  
**Storage**: Local filesystem (BIDS structure), temporary Docker volumes  
**Testing**: `pytest` (unit tests for data loading, GLM logic; integration tests for pipeline steps on subset)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational neuroscience / Data analysis pipeline  
**Performance Goals**: End-to-end runtime ≤ 6 hours for available subset; memory usage ≤ 6 GB per `fmriprep` process.  
**Constraints**: No GPU; strict RAM limits for `fmriprep`; dataset must be subset if full size exceeds available disk capacity.  
**Scale/Scope**: Single dataset (`ds000246`), A subset of subjects will be recruited, with the final sample size determined during the implementation phase., voxel-wise GLM, group-level one-sample t-test.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | PASS | `requirements.txt` pins versions; random seeds set in code; Docker image tag recorded. |
| **II. Verified Accuracy** | PASS | Citations in `research.md` validated against primary source (OpenNeuro ds000246). Verified URL exists. |
| **III. Data Hygiene** | PASS | SHA256 checksums computed for downloaded data; no in-place modifications; PII scan enforced. |
| **IV. Single Source of Truth** | PASS | All figures/stats trace to `data/` and `code/`; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | PASS | Content hashes tracked in `state/`; `updated_at` timestamps updated on artifact change. |
| **VI. Neuroimaging Data Standards** | PASS | BIDS structure enforced; `fmriprep` Docker used; preprocessing log version-controlled. |
| **VII. Statistical Analysis Transparency** | PASS | `stats_config.yaml` encodes GLM/One-Sample t-test parameters; ROI definitions in `roi_masks/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-examining-the-impact-of-auditory-feedback-motor-learning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-195-examining-the-impact-of-auditory-feedbac/
├── code/
│   ├── __init__.py
│   ├── download.py          # FR-001: OpenNeuro download & checksum
│   ├── preprocess.py        # FR-002: fmriprep orchestration (Docker)
│   ├── glm_first_level.py   # FR-003: Subject-level GLM
│   ├── glm_group.py         # FR-004: Group one-sample t-test & FDR
│   ├── behavior.py          # FR-005: RT extraction & learning rate
│   ├── correlation.py       # FR-006: Brain-behavior correlation
│   ├── viz.py               # FR-007: Statistical maps & scatter plots
│   └── utils.py             # QC checks, BIDS helpers
├── data/
│   ├── raw/                 # Downloaded OpenNeuro data
│   ├── derivatives/         # fmriprep outputs
│   └── processed/           # Contrast maps, behavioral CSVs
├── roi_masks/
│   └── auditory_cortex.nii.gz
├── stats_config.yaml        # VII: Thresholds, correction method
├── preprocessing.log        # VI: Deviation log
├── requirements.txt         # I: Dependency pins
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

**Structure Decision**: Single project structure chosen for streamlined data flow (download → preprocess → analyze → viz). No separate frontend/backend required as this is a batch analysis pipeline.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed all principles. | N/A |

## Phase Plan & FR/SC Mapping

### Phase 0: Research & Data Validation
- **FR-001**: Download `ds000246` (subset if >14GB), verify SHA256.
- **FR-002**: Validate `fmriprep` Docker image compatibility with 6GB RAM limit.
- **Event Label Validation**: **Hard Stop** if `normal`, `delayed`, or `pitch-shifted` event labels are missing in `events.tsv`. (Addresses Plan Consistency concern).
- **SC-005**: Estimate runtime for subset (≤6h).

### Phase 1: Preprocessing Pipeline
- **FR-002**: Run `fmriprep` with `--nprocs 2 --mem-mb 6000`.
- **Edge Case**: Skip subjects with motion >2mm (log to `preprocessing.log`).
- **SC-001**: Track % of subjects successfully preprocessed.

### Phase 2: First-Level GLM
- **FR-003**: Fit GLM per subject; define `perturbed` = `delayed` ∪ `pitch-shifted`.
- **Sensitivity Analysis**: If N permits, run separate regressors for `delayed` and `pitch-shifted` to test construct validity.
- **FR-005**: Extract RTs from events; compute **global** learning rate slope (RT over ALL trials) to ensure independence from condition labels. (Addresses Scientific Soundness concern).
- **SC-004**: Calculate Cohen's d for contrast maps.

### Phase 3: Group Analysis
- **FR-004**: **One-sample t-test** on contrast maps (perturbed > normal) against zero; apply FDR (q<0.05). (Addresses Methodology concern on paired vs one-sample).
- **Edge Case**: If no clusters survive FDR, report null result with uncorrected map and effect sizes. This is a valid outcome, not a failure. (Addresses Plan Consistency concern).
- **SC-002**: Check if at least one cluster survives OR if global p < 0.10 (pilot adjustment) OR report effect size. (Addresses Power concern).

### Phase 4: Brain-Behavior & Visualization
- **FR-006**: Correlate auditory cortex activation (ROI mean beta from `perturbed > normal` contrast) with **global** learning rate proxy. (Addresses Construct Validity concern).
- **FR-007**: Generate scatter plots and thresholded statistical maps.
- **SC-003**: Report correlation direction, magnitude, and % CI. Treat strict p < 0.05 as exploratory given low N. (Addresses Power concern).

## Computational Feasibility & Risk Mitigation

- **Memory**: `fmriprep` strictly limited to 6GB; subjects processed sequentially to avoid OOM.
- **Disk**: If full dataset >14GB, download only a subset of initial subjects (verified via `ds000246` size).
- **Runtime**: GLM and group analysis use `nilearn` (CPU-optimized); no GPU training.
- **Fallback**: If `fmriprep` fails, pipeline logs error and proceeds to next subject; final report includes exclusion list.

## Spec-Root Cause Flag

**Action Required**: The source `spec.md` still references `ds000115` in FR-001, User Story 1, and Assumptions. This contradicts the corrected implementation plan using `ds000246`. The `spec.md` must be updated to reflect the correct dataset source to satisfy the "Single Source of Truth" principle.