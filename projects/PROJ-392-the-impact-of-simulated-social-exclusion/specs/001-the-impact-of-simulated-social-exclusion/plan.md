# Implementation Plan: The Impact of Simulated Social Exclusion on Neural Responses to Reward

**Branch**: `001-social-exclusion-reward-neural` | **Date**: 2024-01-15 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-social-exclusion-reward-neural/spec.md`

## Summary

This feature implements a computational neuroscience pipeline to investigate whether simulated social exclusion (via Cyberball) modulates neural activity in reward regions (ventral striatum, OFC) during subsequent reward anticipation. The approach involves downloading BIDS-formatted fMRI data, performing CPU-tractable preprocessing (slice timing, realignment, normalization, smoothing), extracting ROI beta estimates, and conducting second-level mixed-effects analysis with Bonferroni correction. 

**Critical Design Pivot**: Since no single verified public dataset contains both the Cyberball exclusion paradigm and a subsequent reward task in the same subjects, this plan implements a **Merged Dataset Strategy**. We will merge a verified Exclusion dataset (e.g., ds000246) with a verified Reward dataset (e.g., ds004738 or similar), applying strict confound controls and meta-analytic techniques to handle inter-dataset variability. Synthetic data is **not** used for primary analysis or validation, as it would render the scientific question untestable.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `pandas`, `bids-validator` (via `pybids`), `fmriprep` (CPU-compatible invocation), `nipype` (for pipeline orchestration), `nilearn` (for GLM and visualization).  
**Storage**: Local filesystem (`data/raw-fmri`, `data/processed-fmri`, `data/behavioral`, `data/results`).  
**Testing**: `pytest` (unit tests for data extraction, integration tests for pipeline execution on sample data).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM).  
**Project Type**: Research pipeline / Computational Neuroscience.  
**Performance Goals**: Preprocessing ≤4 hours for ≤20 participants; Total runtime ≤6 hours.  
**Constraints**: No GPU; No CUDA; Memory usage <7 GB; Disk usage <14 GB; All code must be reproducible on fresh runner.  
**Scale/Scope**: Merged datasets (Exclusion + Reward); ≤20 participants per group for initial validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ PASS | All scripts in `code/` will use pinned `requirements.txt`. Random seeds will be set in `code/preprocess` and `code/analysis`. External data fetched via `datasets.load_dataset` or `requests` to verified URLs. |
| **II. Verified Accuracy** | ✅ PASS | Citations in `research.md` and `paper/` will be validated against the "Verified datasets" block in the user message. No fabricated URLs. A 'Verified Accuracy Gate' step is added to the pipeline flow. |
| **III. Data Hygiene** | ✅ PASS | Raw data stored in `data/raw-fmri` unaltered. Checksums recorded in `state/`. Derivations in `data/processed-fmri` with provenance logs. |
| **IV. Single Source of Truth** | ✅ PASS | All figures/stats in reports will be generated programmatically from `data/results` (CSV/JSON), not hand-typed. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts will be hashed; `state/` updated on change. |
| **VI. Neuroimaging Data Integrity** | ✅ PASS | Raw scans in `data/raw-fmri/`; preprocessing in `code/preprocess/`; derived files in `data/processed-fmri/`. **Machine-readable provenance files (YAML/JSON sidecars)** are generated for every preprocessed file. |
| **VII. Behavioral Manipulation Standardization** | ✅ PASS | Exclusion condition labels extracted from `participants.tsv` or task JSON; linked via participant ID. **A `code/manipulation/` directory is added** to store deterministic manipulation scripts and logs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-exclusion-reward-neural/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-392-the-impact-of-simulated-social-exclusion/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── data_download/
│   │   └── download_openneuro.py
│   ├── manipulation/       # [NEW] For behavioral manipulation scripts/logs
│   │   ├── __init__.py
│   │   └── generate_condition_labels.py
│   ├── preprocess/
│   │   ├── __init__.py
│   │   ├── cpu_fmriprep_wrapper.py
│   │   └── run_preprocessing.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── roi_extraction.py
│   │   ├── group_analysis.py
│   │   └── sensitivity_analysis.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── plot_results.py
│   ├── utils/
│   │   ├── checksums.py
│   │   ├── provenance.py
│   │   └── framing_validator.py
│   └── pipeline/
│       └── run_pipeline.py
├── data/
│   ├── raw-fmri/
│   ├── processed-fmri/
│   ├── behavioral/
│   └── results/
├── specs/001-social-exclusion-reward-neural/
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Download → Preprocess → Analyze → Visualize) and fits within a single Python environment. `code/` is organized by functional stage to ensure modularity and testability. **Added `code/manipulation/` and `code/utils/framing_validator.py` to address Constitution and SC requirements.**

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | The scope is constrained to CPU-tractable methods and a single dataset (or merged datasets). No complex microservices or distributed computing is required. | N/A |

## Implementation Phases

### Phase 0: Data Acquisition & Verification
- **Task 0.1**: Download verified Exclusion dataset (e.g., ds000246) and verified Reward dataset (e.g., ds004738) from OpenNeuro.
- **Task 0.2**: Verify dataset contents (Cyberball/MID tasks) and BIDS compliance.
- **Task 0.3**: **Verified Accuracy Gate**: Run Reference-Validator Agent to check all dataset citations against the "Verified datasets" block.

### Phase 1: Preprocessing & Confound Control
- **Task 1.1**: Run CPU-tractable preprocessing (slice timing, realignment, normalization, smoothing).
  - **Constraint**: `fmriprep` invoked with `--nthreads 2 --mem-mb 6000` to respect 7GB RAM limit.
  - **Batching**: Process participants in batches.
- **Task 1.2**: **Provenance Generation**: Create machine-readable YAML sidecars for each preprocessed file recording pipeline version and parameters.
- **Task 1.3**: **Metrics Collection**: Calculate and log 'Preprocessing Completion Rate' (target ≥90%) to `data/results/preprocessing_metrics.json`.
- **Task 1.4**: **Merging & Confound Adjustment**: Harmonize datasets. If merging separate datasets, add 'Dataset ID' as a random effect in the mixed-effects model or match demographics.

### Phase 2: First-Level & ROI Analysis
- **Task 2.1**: Run First-Level GLM with AR(1) pre-whitening for temporal autocorrelation.
- **Task 2.2**: Extract beta estimates from ROIs (Ventral Striatum, OFC) for Anticipation and Receipt events.
- **Task 2.3**: Store results in `data/results/beta_estimates.csv`.

### Phase 3: Second-Level Analysis & Visualization
- **Task 3.1**: Run Second-Level Mixed-Effects Analysis (Two-sample t-test / ANOVA) with Bonferroni correction.
- **Task 3.2**: **SPM Overlay Generation**: Generate statistical parametric maps overlaid on MNI template brain (satisfying FR-007).
- **Task 3.3**: Generate ROI bar plots with error bars and p-value annotations.

### Phase 4: Reporting & Validation
- **Task 4.1**: **Power & Sample Size Reporting**: Generate 'Power Limitations Report' documenting N, power estimates, and recommendation for future studies (≥30 participants) if N < 20 (satisfying FR-010).
- **Task 4.2**: **Framing Validation**: Run `framing_validator.py` to scan final report for causal verbs and ensure associational language (satisfying SC-005).
- **Task 4.3**: Compile final summary report.

### Phase 5: Sensitivity Analysis
- **Task 5.1**: Sweep smoothing kernels (multiple scales) and report consistency of findings.
- **Task 5.2**: Generate sensitivity table and report.

## Risk Management

| Risk | Mitigation |
| :--- | :--- |
| **No single dataset contains both tasks** | **Primary Design**: Merged Dataset Strategy with confound controls. **Fallback**: If no compatible datasets exist, the study is paused or pivots to a meta-analysis of separate studies. **Synthetic data is NOT used.** |
| **Memory overflow on CPU** | Batch processing (subjects), `--mem-mb 6000` flags, and downsampled resolution if necessary. |
| **Inter-dataset variability (scanner differences)** | Include 'Dataset ID' as a random effect in the mixed-effects model. |
| **Power limitations (N < 20)** | Explicitly flag as exploratory; generate Power Limitations Report (Task 4.1). |
| **Causal misinterpretation** | Framing Validation script (Task 4.2) and explicit associational language in all outputs. |

## Performance & Feasibility

- **Runtime**: Preprocessing ≤4 hours (20 subjects, CPU-only). Total pipeline ≤6 hours.
- **Memory**: <7 GB (via `--mem-mb 6000` and batching).
- **Disk**: <14 GB (via selective storage of preprocessed data and results).
- **GPU**: None required. All methods are CPU-tractable.

## Dependencies

- `python>=3.11`
- `nibabel>=5.0.0`
- `numpy>=1.24.0`
- `pandas>=2.0.0`
- `scikit-learn>=1.2.0`
- `scipy>=1.10.0`
- `matplotlib>=3.7.0`
- `nilearn>=0.10.0` (for GLM and visualization)
- `fmriprep>=23.0.0` (CPU-compatible)
- `nipype>=1.8.0`
- `pytest>=7.0.0`
- `pybids>=0.16.0`
- `pyyaml>=6.0.0`