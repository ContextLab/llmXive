# Implementation Plan: Cross-Dataset Consistency of Alpha Peak Frequency Estimates in Resting-State EEG

**Branch**: `001-cross-dataset-apf-consistency` | **Date**: 2026-07-30 | **Spec**: `specs/001-cross-dataset-apf-consistency/spec.md`

## Summary

This project implements a reproducible pipeline to quantify the consistency of Alpha Peak Frequency (APF) estimates across three distinct dimensions: dataset source (OpenNeuro), preprocessing pipeline (Standard vs. Alternative), and estimation method (Time-domain vs. Frequency-domain). The system downloads raw EEG data, applies two strict preprocessing pipelines, calculates APF using dual algorithms, and performs variance decomposition via linear mixed-effects modeling with bootstrapped confidence intervals. The implementation prioritizes CPU feasibility on GitHub Actions runners while adhering to strict data hygiene and reproducibility constraints defined in the project constitution.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `mne` (EEG processing), `scikit-learn` (ML), `statsmodels` (Mixed-Effects), `pandas`, `numpy`, `pybids` (BIDS handling), `openneuro-py` (Data download), `matplotlib`, `seaborn`, `scipy`  
**Storage**: Local filesystem (`data/raw`, `data/derivatives`, `data/processed`); BIDS-compliant directory structure.  
**Testing**: `pytest` (Unit/Integration), `pytest-mock` (for download mocks), `numpy.testing` (Numerical checks).  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, ~7GB RAM, ~14GB Disk).  
**Project Type**: Scientific Data Analysis Pipeline / CLI Tool.  
**Performance Goals**: Complete full analysis (3 datasets, 2 pipelines, 2 methods) within 6 hours per job; RAM usage < 6 GB (streaming/sequential processing).  
**Constraints**: No GPU required for standard Welch PSD or FastICA on < 50 subjects; Must handle missing BIDS metadata gracefully; Must stream large datasets if > 1GB to avoid OOM.  
**Scale/Scope**: A selection of OpenNeuro datasets with approximately one hundred subjects total.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | Random seeds pinned in `code/config.py`. External datasets fetched via `openneuro-py` with version locking. `requirements.txt` pins all deps. |
| **II. Verified Accuracy** | ⚠️ FAIL (Mitigated) | No pre-verified URL in block for these specific IDs. Mitigation: Use official `openneuro-py` API as the *only* valid path. System halts with "Data Integrity" error if API fetch fails, preventing fabrication. |
| **III. Data Hygiene** | ✅ PASS | Raw data stored in `data/raw` with SHA256 checksums recorded in `state/`. Derivatives written to `data/derivatives` with distinct filenames. No in-place edits. |
| **IV. Single Source of Truth** | ✅ PASS | All figures/stats in reports generated directly from `data/processed` CSVs by scripts; no manual entry. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts under `data/` and `code/` will carry content hashes. `state/` updated on artifact change. |
| **VI. Cross-Dataset Variance Attribution** | ✅ PASS | Mixed-effects model `APF ~ dataset + pipeline + method + (1|subject) + (1|subject:pipeline) + (method|subject)` explicitly implemented. Variance components for 'dataset', 'pipeline', AND 'estimation_method' (as Algorithmic Bias) reported with bootstrapped CIs. |
| **VII. Standardized Neurophysiological Preprocessing** | ✅ PASS | Two pipelines (A: 1-45Hz, CAR, ICA; B: 0.5-40Hz, Mastoid, No ICA) strictly implemented using `mne` with fixed parameters. Dual APF methods (PSD, Autocorr) implemented with synthetic ground-truth calibration. |

## Project Structure

### Documentation (this feature)

```text
specs/001-cross-dataset-apf-consistency/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── apf_result.schema.yaml
│   └── variance_component.schema.yaml
└── tasks.md             # Future artifact (not generated in this stage)
```

### Source Code (repository root)

```text
code/
├── config.py            # Global settings, seeds, paths
├── download.py          # OpenNeuro fetcher with BIDS validation
├── preprocessing.py     # Pipeline A and B implementations
├── apf_estimator.py     # PSD and Autocorrelation methods + Synthetic GT
├── analysis.py          # Mixed-effects model, bootstrapping, simulation power analysis
├── reporting.py         # Plot generation (Forest, Bar charts, Sensitivity Table)
└── main.py              # Orchestration script

tests/
├── unit/
│   ├── test_preprocessing.py
│   ├── test_apf_estimator.py
│   └── test_analysis.py
├── integration/
│   └── test_pipeline_e2e.py
└── contract/
    └── test_schemas.py

data/
├── raw/                 # Downloaded BIDS data (checksummed)
├── derivatives/         # Preprocessed data (Pipeline A/B)
└── processed/           # APF estimates and model results

state/
└── projects/PROJ-785-...yaml  # Artifact hashes and timestamps
```

**Structure Decision**: Single Python project structure selected to minimize overhead and ensure tight integration between download, processing, and analysis steps on a constrained CI runner. No separate frontend/backend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Dual Preprocessing Pipelines** | Required by US-1 to isolate pipeline variance. | Single pipeline would fail to address the core research question regarding methodological artifacts. |
| **Dual APF Estimation Methods** | Required by US-2 to validate biomarker robustness. | Single method cannot distinguish algorithm-specific bias from true signal variance. |
| **Mixed-Effects Modeling** | Required by US-3 to handle nested data (subjects within datasets) and decompose variance. | ANOVA would fail to account for the random effect of subject ID, inflating Type I error. |
| **Bootstrapping** | Required by FR-005 and SC-003 for robust CI estimation on non-normal variance components. | Asymptotic CIs are unreliable for small sample sizes and complex variance structures. |
| **Simulation-based Power Analysis** | Required by Methodology Panel to correctly estimate power for variance components. | Standard fixed-effect power analysis is invalid for detecting variance > 0 in mixed models. |

## Implementation Phases

### Phase 0: Data Acquisition & Validation
1.  **Download**: Use `openneuro-py` to fetch ds, ds003392, ds003775.
2.  **Pre-check**: Verify each dataset contains 'eeg' files and ≥20 subjects. Skip and log if not.
3.  **Checksum**: Generate SHA256 for all raw files.

### Phase 1: Preprocessing
1.  **Pipeline A**: Bandpass (1-45Hz), Notch (50/60Hz), CAR, ICA (remove EOG components).
2.  **Pipeline B**: Bandpass (0.5-40Hz), Notch (50/60Hz), Mastoid, No ICA.
3.  **Validation**: Ensure no NaNs, verify line noise attenuation.

### Phase 2: APF Estimation & Calibration
1.  **Synthetic Ground Truth**: Generate a synthetic signal with a known peak frequency.. Run both methods to calculate absolute error (Accuracy).
2.  **Real Data**: Run PSD and Autocorr on all preprocessed data.
3.  **Consistency Check**: Calculate |APF_psd - APF_autocorr| for each subject. Flag if > 0.5 Hz.

### Phase 3: Variance Decomposition
1.  **Model**: Fit `APF ~ dataset_source + pipeline_type + estimation_method + (1|subject_id) + (1|subject_id:pipeline) + (estimation_method|subject_id)`.
2.  **Interpretation**: Report 'Dataset Source' as 'Between-Study Heterogeneity (Confounded)'. Report 'Method' as 'Algorithmic Bias'.
3.  **Bootstrapping**: A sufficient number of resamples will be used to construct confidence intervals...

### Phase 4: Sensitivity & Power Analysis
1.  **Sensitivity**: Iterate alpha band bounds (Lower: below a critical threshold; Upper: 13.5). Calculate delta mean APF for each. Output 'Sensitivity Table'.
2.  **Power**: Simulate multiple datasets with known variance components (dataset=0.4, pipeline=0.1, residual=0.5). Fit model. Calculate % of simulations where pipeline variance is significant. Report achieved power.

### Phase 5: Reporting
1.  **Validation**: Check SC-002 (Consistency % ≤ 0.5Hz) and SC-003 (Power ≥ 0.80). Output Pass/Fail status.
2.  **Visuals**: Forest plot, Variance Bar Chart, Sensitivity Table.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Dataset Missing Subjects** | High (Power analysis fails) | Pre-check skips dataset. If < 2 datasets remain, halt. |
| **BIDS Metadata Incomplete** | High (Cannot determine sampling rate) | Pre-check validates BIDS. If `sampling_frequency` missing, skip subject. |
| **No Alpha Peak Found** | Medium (Missing data) | Flag as "Indeterminate". Exclude from mean but report count. |
| **RAM Exceeded** | High (CI Job Fail) | Sequential processing: Process Dataset 1 -> Delete -> Dataset 2. |
| **API Fetch Failure** | High (No Data) | System halts with "Data Integrity" error. No fabrication. |