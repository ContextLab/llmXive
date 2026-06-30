# Implementation Plan: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

**Branch**: `001-visual-complexity-pfc` | **Date**: 2023-10-27 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-visual-complexity-pfc/spec.md`

## Summary

This feature implements a computational pipeline to investigate the correlation between quantitative visual complexity metrics (Shannon entropy, fractal dimension) and BOLD signal amplitude in the Dorsolateral Prefrontal Cortex (DLPFC). The approach involves downloading preprocessed fMRI data from OpenNeuro (**ds000248**, a visual task dataset), computing complexity metrics on stimulus frames, convolving these with a canonical Hemodynamic Response Function (HRF), extracting the DLPFC time-series using the AAL atlas, and performing a two-level GLM analysis (Subject-level AR(1) pre-whitened GLM + Group-level t-test) with FDR correction. All operations are constrained to run within GitHub Actions free-tier limits (≤6GB RAM, ≤6h runtime, CPU-only).

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `nibabel`, `numpy`, `scikit-image`, `scipy`, `pandas`, `statsmodels`, `nilearn`, `matplotlib`, `requests`, `tqdm`  
**Storage**: Local filesystem (`data/` for raw/processed files, `data/interim/` for derived metrics)  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline stages)  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Neuroscience Pipeline  
**Performance Goals**: Peak RAM ≤ 6GB, Total Runtime ≤ 6h  
**Constraints**: CPU-only (no GPU/CUDA), memory-batched processing, no external API calls beyond dataset download.  
**Scale/Scope**: Single dataset (ds000248), A small cohort of subjects, Hundreds to thousands of stimulus frames per subject.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Reproducibility Mechanism**: `code/config.py` initializes global seeds for `numpy`, `random`, and `torch` at module load time. All external datasets are fetched from canonical sources using fixed version identifiers.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

1.  **Reproducibility (Principle I)**
    *   **Mapping**: `code/config.py` pins global seeds; `data/` stores checksums of raw downloads; `code/` uses fixed OpenNeuro snapshot `ds000248`.
2.  **Verified Accuracy (Principle II)**
    *   **Mapping**: Citations for ds000248, AAL atlas, and HRF models are validated in `research.md` against primary sources before implementation.
3.  **Data Hygiene (Principle III)**
    *   **Mapping**: Raw data in `data/raw/` is checksummed and immutable. Derived files (complexity metrics, beta-weights) are written to `data/interim/` and `data/results/`.
4.  **Single Source of Truth (Principle IV)**
    *   **Mapping**: All statistical outputs (beta-weights, p-values) are derived from `code/modeling.py` and stored in `data/results/`, referenced by the final report.
5.  **Versioning Discipline (Principle V)**
    *   **Mapping**: Content hashes for all artifacts are recorded in `state/projects/...yaml` upon generation.
6.  **Neuroimaging Data Integrity (Principle VI)**
    *   **Mapping**: Data sourced exclusively from OpenNeuro `ds000248`. Preprocessing (smoothing) applied to copies; original files preserved.
7.  **Computational Resource Management (Principle VII)**
    *   **Mapping**: Subject-wise chunking and memory-batched image processing implemented. Scripts include abort logic if RAM > 6GB.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-complexity-pfc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-228-investigating-the-impact-of-visual-compl/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, constants, seeds, global seed init
│   ├── ingestion.py             # FR-001: Download & verify OpenNeuro ds000248
│   ├── complexity.py            # FR-002: Entropy, Fractal Dim, HRF Conv, Confounds
│   ├── roi_extraction.py        # FR-003: DLPFC extraction, smoothing
│   ├── modeling.py              # FR-004, FR-005: GLM, AR(1), Permutation, VIF
│   └── main.py                  # Pipeline orchestrator
├── data/
│   ├── raw/                     # OpenNeuro downloads (checksummed)
│   ├── interim/                 # Complexity metrics, extracted time-series, beta-weights
│   └── results/                 # JSON results, permutation plots
├── tests/
│   ├── unit/
│   └── integration/
└── requirements.txt
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between data ingestion, processing, and analysis, ensuring reproducibility and minimizing data transfer overhead in the CI environment.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Two-Level GLM (Subject + Group) | Required to handle temporal autocorrelation and non-independence of timepoints (US-3). | Single-level regression on all timepoints violates independence assumptions, inflating Type I error. |
| AR(1) Pre-whitening | Required to correct for temporal autocorrelation within the GLM (US-3). | Standard OLS assumes independent errors, which is false for fMRI time-series. |
| Collinearity Diagnostics (VIF) | Required to handle high correlation between entropy and fractal dimension (US-3). | Multiple regression with collinear predictors yields unstable coefficients. |
| Memory-Batched Processing | Required to stay within 6GB RAM limit (Principle VII). | Processing all subjects/images at once would exceed memory on free-tier runners. |