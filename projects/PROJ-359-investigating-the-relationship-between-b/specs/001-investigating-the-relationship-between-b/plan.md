# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Response to Cognitive Training (Pivoted: Baseline Association)

**Branch**: `feature-branch` | **Date**: 2026-06-24 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/investigating-the-relationship-between-b/spec.md`

## Summary

This project implements a reproducible neuroimaging analysis pipeline. **CRITICAL PIVOT**: The original hypothesis (predicting *training response*) is untestable with the available dataset (OpenNeuro ds000277, HCP-1200), which lacks longitudinal training data. The project scope has been pivoted to test the **cross-sectional association** between baseline resting-state functional connectivity (specifically frontoparietal and default mode networks) and **baseline working memory capacity**. The approach involves downloading ds, preprocessing rs-fMRI data with fMRIPrep 23.1.3, extracting network metrics using the Schaefer 400-parcellation, and fitting a linear regression model predicting baseline WM from connectivity metrics, controlling for age and sex. The entire pipeline is constrained to run on a GitHub Actions free-tier runner (CPU-only, ≤7GB RAM, ≤6h) by processing a subset of participants if necessary and using CPU-optimized libraries.

**Scope Change Notice**: The dataset `ds000277` does not contain a cognitive training intervention. The outcome variable is **Baseline WM**, not WM Gain. The study tests for association, not prediction of change.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `pandas`, `networkx`, `bctpy`, `scikit-learn`, `matplotlib`, `requests`, `tqdm`, `statsmodels`. *Note: fMRIPrep is invoked as a subprocess; the plan assumes the CI environment can install its Docker container or binary, but the Python logic relies on CPU-only standard libraries.*  
**Storage**: Local file system (`data/raw`, `data/preprocessed`, `data/derived`); CSV/JSON outputs.  
**Testing**: `pytest` (unit tests for metric extraction, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Data analysis pipeline / CLI tool.  
**Performance Goals**: Complete analysis of N≤85 participants within 6 hours on 2 vCPU.  
**Constraints**: No GPU; strict memory limits (≤7GB RAM); fMRIPrep version 23.1.3; Schaefer 400 parcellation; motion exclusion >0.3mm FD (corrected from 3.0mm).  
**Scale/Scope**: Single dataset (ds000277), ~85 valid participants max.

> **Critical Constraint Note**: The spec assumes `ds000277` contains both rs-fMRI and training data. This is factually incorrect; ds000277 is a cross-sectional HCP release. The plan has pivoted to a baseline-baseline association. If the dataset lacks the required baseline behavioral outcome (WM score), the project will halt with a `FatalError`. The plan does **not** attempt to fabricate training data or use unverified datasets.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Action Required in Plan/Research |
|-----------|-------------------|----------------------------------|
| I. Reproducibility | **Pass** | Plan mandates pinned seeds, checksums, and `requirements.txt`. |
| II. Verified Accuracy | **Conditional Pass** | Dataset URL (ds000277) is NOT in the verified list. Pipeline will flag this as "Unverified Source" but proceed if checksums match. If checksums fail or URL unreachable, pipeline halts with clear error. **Fallback**: If the dataset is unverified, the pipeline will attempt to download but will raise a `RuntimeError` if the checksum cannot be validated against a pre-registered value. |
| III. Data Hygiene | **Pass** | Plan requires checksums for raw data and immutable derivations. |
| IV. Single Source of Truth | **Pass** | **Phase 3.2** explicitly enforces that all figures derive from `data/` CSVs. No hard-coded values. |
| V. Versioning Discipline | **Pass** | Plan includes content hashing logic for artifacts. |
| VI. Neuroimaging Preprocessing Consistency | **Pass** | Plan explicitly mandates fMRIPrep 23.1.3 and Schaefer 400. |
| VII. Motion Artifact Exclusion | **Pass** | Plan includes strict FD > 0.3mm exclusion logic (corrected from 3.0mm) and logging. |

## Project Structure

### Documentation (this feature)

```text
specs/[feature-branch]/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-359-investigating-the-relationship-between-b/
├── data/
│   ├── raw/                 # Downloaded OpenNeuro files (ds000277)
│   ├── preprocessed/        # fMRIPrep outputs (if cached or re-run)
│   ├── derived/             # Connectivity matrices, metrics, regression results
│   └── logs/                # JSON logs for exclusion, runtime
├── code/
│   ├── __init__.py
│   ├── download.py          # FR-001: Dataset download & checksum
│   ├── preprocess.py        # FR-002: Wrapper for fMRIPrep (subprocess)
│   ├── metrics.py           # FR-003, FR-004: Connectivity & Network metrics
│   ├── regression.py        # FR-005: Model fitting & permutation
│   ├── viz.py               # FR-006: Plotting
│   ├── utils.py             # Logging, ID validation (FR-009)
│   └── main.py              # Orchestrator
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with modular scripts. `preprocess.py` is a wrapper script that invokes fMRIPrep as a subprocess, not the preprocessing engine itself.

## Phase Plan

### Phase 0: Research & Feasibility (Pre-Implementation)
- **Task 0.1**: Verify dataset content (rs-fMRI + baseline WM scores). If training scores are missing, confirm pivot to baseline association.
- **Task 0.2**: Perform *a priori* power analysis for N=85 to detect r=0.30. Generate `power_analysis.txt`.
- **Task 0.3**: Validate motion threshold (0.3mm) against literature.

### Phase 0.1: Data Validation (New Step for FR-009)
- **Task 0.1.1**: Parse participant metadata from ds000277.
- **Task 0.1.2**: Validate that every participant ID in rs-fMRI data has a corresponding entry in behavioral data.
- **Task 0.1.3**: Raise `FatalError` if any ID is missing from either source.

### Phase 0.5: Power Analysis (For SC-003)
- **Task 0.5.1**: Calculate *a priori* power for N=85 (planned max) to detect r=0.30 at α=0.05.
- **Task 0.5.2**: If N < 85, calculate *achieved* power for actual N.
- **Task 0.5.3**: Write results to `data/derived/power_analysis.txt`.

### Phase 1: Data Ingestion & Preprocessing
- **Task 1.1**: Download ds000277 via HTTP/HTTPS (FR-001). Verify checksums.
- **Task 1.2**: Preprocess rs-fMRI with fMRIPrep 23.1.3 (FR-002).
- **Task 1.3**: Calculate mean FD. Exclude participants with mean FD > 0.3mm (FR-007, corrected).

### Phase 2: Feature Extraction
- **Task 2.1**: Extract ROI time series (Schaefer 400).
- **Task 2.2**: Compute 400x400 correlation matrices (FR-003).
- **Task 2.3**: Calculate Global Efficiency, Modularity, FPN Strength, DMN Strength (FR-004).

### Phase 3: Modeling & Visualization
- **Task 3.1**: Fit OLS regression: `Baseline_WM ~ FPN + DMN + Eff + Mod + Age + Sex`.
- **Task 3.2**: **Single Source of Truth Enforcement**: Ensure plotting script reads only from `data/derived/model_summary.csv`. No hard-coded values.
- **Task 3.3**: **Reproducibility Verification**: Re-run plotting with fixed seed, compare hashes, generate `reproducibility_report.txt` (SC-004).
- **Task 3.4**: Generate `effect_sizes.pdf` and `model_summary.csv` (FR-006).
- **Task 3.5**: Record runtime to `runtime.log` (SC-005) and JSON log (FR-007). **Note**: `runtime.log` is the definitive file for SC-005 compliance.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| fMRIPrep dependency | Required by Constitution Principle VI for consistency. | Using a simpler custom motion correction would violate the "Single Source of Truth" and reproducibility standards for neuroimaging. |
| Permutation Testing | Required by FR-005 for robust inference without normality assumptions. | Standard parametric p-values are insufficient for small N and complex connectivity data; permutation is standard in neuroimaging. |
| Motion Threshold (0.3mm) | Required for scientific validity; 3.0mm is too lenient. | Substantial motion artifacts would invalidate connectivity metrics. |
| Runtime Downsampling | Required to meet SC-005 (6h limit) on CI. | Running full N=85 risks timeout. **Note**: This is a compute constraint, not a statistical fallback. Split-sample validation (SC-001) is a separate statistical strategy. |

## Compute Feasibility (CPU-Only Constraint)

- **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **fMRIPrep**: This is the bottleneck.
  - **Strategy**: Run fMRIPrep on the full N=85. If runtime exceeds 5.5 hours, automatically downsample to N=30 (after motion exclusion) to ensure completion within 6h.
  - **Fallback**: If N < 30 after downsampling, proceed with available N and log a warning that power is insufficient.
- **Network Metrics**: `bctpy` and `networkx` are CPU-optimized and efficient for 400x400 matrices.
- **Regression**: `scikit-learn` OLS and permutation are trivial for N=85.

## Scientific Validity & Causal Claims

- **Original Claim**: Baseline connectivity *predicts* training response.
- **Revised Claim**: Baseline connectivity is *associated with* baseline working memory capacity.
- **Justification**: The dataset ds000277 is cross-sectional. It contains no longitudinal training data. Therefore, the study cannot test for prediction of change. The analysis is strictly correlational.
- **Limitation**: Results cannot be interpreted as causal or predictive of training outcomes.
