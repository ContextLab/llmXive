# Implementation Plan: Investigating the Impact of Network Centrality on the Consolidation of Motor Memories

**Branch**: `001-network-centrality-motor-consolidation` | **Date**: 2026-07-08 | **Spec**: `specs/001-network-centrality-motor-consolidation/spec.md`
**Input**: Feature specification from `/specs/001-network-centrality-motor-consolidation/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the association between baseline resting-state fMRI network centrality and motor memory consolidation improvement. The approach involves downloading the **OpenNeuro ds000030** dataset (verified to contain both resting-state fMRI and motor task behavioral data), preprocessing it with **fMRIPrep** (mandatory) with memory-efficient settings to fit within available system RAM, computing graph-theoretic centrality metrics (degree, betweenness, eigenvector) using NetworkX, aggregating these into a global score using a **fixed, a priori set of regions** (AAL regions), and fitting linear regression and Generalized Additive Models (GAM) with **Freedman-Lane permutation testing** (controlling for motion) and cross-validation to validate the findings. The entire pipeline is designed to run on CPU-only GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `networkx`, `scikit-learn`, `statsmodels`, `nilearn`, `pyyaml`, `matplotlib`, `seaborn`, `openneuro-cli` (for raw data fetch)  
**Storage**: Local filesystem (temporary processing), CSV/Parquet artifacts  
**Testing**: `pytest` (contract tests against schemas)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Data Analysis / Research Pipeline  
**Performance Goals**: Complete pipeline execution ≤ 6 hours, peak RAM ≤ 7 GB  
**Constraints**: No GPU, no deep learning training, memory-efficient fMRI preprocessing, CPU-only centrality calculation  
**Scale/Scope**: Target N ≥ 85 subjects (for power), ~90 brain regions, 1000+ permutations  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: The plan enforces pinned random seeds in all stochastic steps (permutation, cross-validation) and mandates fetching data from canonical URLs. The `reproducibility_report.json` will document code versions and data checksums.
- **II. Verified Accuracy**: All dataset citations in `research.md` are restricted to the "Verified datasets" block. **No other URLs will be used.** The implementation strictly enforces the verified list from research.md.
- **III. Data Hygiene**: The pipeline will not modify raw data. All preprocessing steps will output new files with checksums recorded in the state file. Subjects with missing data will be excluded, not imputed.
- **IV. Single Source of Truth**: All figures and statistics in the final report will be generated directly from the `data/` artifacts by the code in `code/`. No hand-typed numbers.
- **V. Versioning Discipline**: The plan includes a mechanism to hash all artifacts and update the project state timestamp upon changes. The specific file path is `state/projects/PROJ-377-investigating-the-impact-of-network-cent.yaml`.
- **VI. fMRI Preprocessing**: **fMRIPrep is REQUIRED.** The plan specifies using `nilearn` or a lightweight wrapper around `fMRIPrep` with strict memory constraints and a fixed atlas (AAL3) to ensure standardization. The "if available" condition is removed; fMRIPrep is mandatory for Principle VI compliance.
- **VII. Statistical Validation**: The plan explicitly includes the permutation test (Freedman-Lane) with a sufficient number of permutations and 5-fold cross-validation as required by the constitution and spec.

## Project Structure

### Documentation (this feature)

```text
specs/001-network-centrality-motor-consolidation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-377-investigating-the-impact-of-network-cent/
├── code/
│   ├── __init__.py
│   ├── data/
│   │   ├── download.py
│   │   └── preprocess.py
│   ├── analysis/
│   │   ├── centrality.py
│   │   ├── regression.py
│   │   └── validation.py
│   ├── utils/
│   │   ├── metrics.py
│   │   └── logging.py
│   ├── main.py
│   └── requirements.txt
├── data/
│   ├── raw/
│   ├── processed/
│   └── artifacts/
├── tests/
│   ├── contract/
│   └── unit/
└── state/
    └── projects/PROJ-377-investigating-the-impact-of-network-cent/
        └── PROJ-377-investigating-the-impact-of-network-cent.yaml
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Download -> Preprocess -> Analyze -> Validate), so a flat `code/` directory with sub-modules for logical separation is sufficient. No separate frontend/backend is needed for this research artifact.

**Data Source Priority**: 
1. Primary: OpenNeuro ds000030 (Verified to contain fMRI + Motor Task).
2. Fetch Method: `openneuro-cli` or direct download of raw BIDS data.
*Note: The generic HuggingFace parquet file is NOT used as the primary source due to lack of behavioral data.*

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The pipeline adheres strictly to the spec's constraints (CPU, 7GB RAM) and uses standard, lightweight libraries. | N/A |

## Implementation Phases

### Phase 0: Data Validation & Feasibility Check
- **Task 0.1**: Download dataset `ds000030` from OpenNeuro.
- **Task 0.2**: **Fatal Feasibility Gate**: Verify presence of required columns (`pre_motor_score`, `post_motor_score`, `age`, `sex`, `subject_id`).
  - **Condition**: If missing, log error "Fatal: Dataset lacks behavioral motor task metrics" and exit. **Do not proceed.**
- **Task 0.3**: Calculate retention rate (subjects with valid data / total subjects in source).
  - **Condition**: If < 80% due to motion artifacts, log warning "Retention < 80%: Proceeding with limitation flag" and **continue**. If < 80% due to missing behavioral data, fail (see Task 0.2).
- **Task 0.4**: **Power Check**: If N < 85, log warning "Underpowered for small effects (r=0.3)" and proceed with caution, but flag in report. (Goal is N>=85).

### Phase 1: Preprocessing & Centrality Calculation
- **Task 1.1**: Run fMRIPrep (mandatory) with memory-efficient settings.
- **Task 1.2**: Extract functional connectivity matrices using AAL3 atlas.
- **Task 1.3**: Calculate centrality metrics (degree, betweenness, eigenvector) for **fixed regions: AAL3 indices 1-10**.
  - **Note**: Do NOT use data-dependent 'top-k' selection. Use the fixed set to avoid bias.
- **Task 1.4**: Calculate Mean Framewise Displacement (FD) for motion control.
- **Task 1.5**: Aggregate global centrality (mean of fixed regions 1-10).
- **Task 1.6**: **VIF Check & Resolution**: Calculate VIF for degree, betweenness, eigenvector.
  - **Condition**: If VIF > 5, switch to PCA components.
  - **Resolution**: Retain the first PCA component (fixed number of components) as the predictor. Set `model_type` to 'PCA-Adjusted' in results.
  - **Bias Control**: The number of components is fixed a priori to avoid data-dependent selection bias in the permutation test.

### Phase 2: Primary Modeling
- **Task 2.1**: Fit Linear Regression: `Improvement ~ Global_Centrality + Age + Sex + Mean_FD`.
- **Task 2.2**: Fit GAM/Polynomial for non-linearity check.
- **Task 2.3**: Compare AIC/BIC.

### Phase 3: Validation
- **Task 3.1**: **Freedman-Lane Permutation Test**: 
  - Permute the **residuals** of the null model (including motion covariates) a sufficient number of times to ensure robust estimation of the null distribution.
  - Calculate empirical p-value. This ensures the null distribution respects the motion confound structure and breaks the link between preprocessing artifacts and outcome.
- **Task 3.2**: K-Fold Cross-Validation (R², RMSE).

### Phase 4: Regional Analysis Fallback (if required by spec)
- **Task 4.1**: If regional analysis is triggered, calculate metrics for all regions.
- **Task 4.2**: Apply Benjamini-Hochberg FDR correction (FR-004.1).

### Phase 5: Reporting
- **Task 5.1**: Generate `reproducibility_report.json` with checksums, wall clock time, and RAM usage.
- **Task 5.2**: Generate figures (scatter plots, permutation histograms).

## Risk Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Missing Behavioral Data** | Fatal | Task 0.2 enforces hard stop. |
| **Memory Overflow** | High | Process in batches. Use `dtype` optimization (float32). |
| **Collinearity** | Medium | Task 1.6 (VIF Check) switches to PCA if VIF > 5. |
| **Dataset Unavailable** | High | Use verified URL. If 404, fail gracefully. |
| **Low Power** | Medium | Task 0.4 reports MDE. Pipeline warns if N < 85. |
| **Motion Confound** | High | Task 1.4 and 3.1 include FD covariate and Freedman-Lane permutation. |
