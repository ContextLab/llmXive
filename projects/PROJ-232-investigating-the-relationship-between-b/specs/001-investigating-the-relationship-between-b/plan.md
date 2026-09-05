# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Branch**: `001-brain-music-emotion` | **Date**: 2023-10-27 | **Spec**: `specs/001-investigating-the-relationship-between-b/spec.md`

## Summary

This project investigates the association between resting-state functional connectivity (RSFC) network metrics and individual differences in musical reward sensitivity (measured by the BMRQ). The technical approach involves:
1.  **Data Acquisition**: Retrieving resting-state fMRI and BMRQ behavioral data from **OpenNeuro ds000233** (Music & Emotion), which is the only verified open dataset containing the specific BMRQ instrument required by the spec.
2.  **Preprocessing**: Running `fMRIPrep` in CPU-only mode **OFF-CI** (requires >7 GB RAM). The CI pipeline performs a **dry-run** validation on a single subject or uses pre-computed matrices if available (though ds000233 provides raw NIfTI).
3.  **Feature Extraction**: Parcellating using the Schaefer 200 atlas and computing functional connectivity matrices (Pearson correlation).
4.  **Graph Analysis**: Calculating global (efficiency, modularity) and network-specific metrics using `NetworkX` and `bctpy`, with **Variance Inflation Factor (VIF)** checks for multicollinearity.
5.  **Statistical Modeling**: Partial correlation (controlling for age, sex, FD) and regularized regression (Ridge/Lasso) with FDR correction. **Bootstrap stability analysis** is performed ONLY on the full dataset (off-CI), not on the CI validation sample.

**Critical Feasibility Note**: The spec requires BMRQ scores. The verified open dataset **OpenNeuro ds000233** is confirmed to contain BMRQ. If this dataset is unavailable or lacks BMRQ, the pipeline will **halt** and generate a **Data Gap Report**. **No synthetic data or proxies will be used.**

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `nibabel`, `nilearn`, `fMRIPrep` (via Docker/Singularity wrapper or CPU-optimized build), `networkx`, `bctpy`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `datasets` (Hugging Face), `openneuro-py`.  
**Storage**: 
- **Disk**: ~14-50 GB available on GitHub Actions free-tier (sufficient for raw data caching).
- **RAM**: **7 GB hard limit** for the process. This is the critical bottleneck for `fMRIPrep`.
**Testing**: `pytest` (unit tests for matrix properties, integration tests for pipeline steps).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM).  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline.  
**Performance Goals**: 
- **CI**: Complete pipeline validation (syntax, schema) for N=1 subject within 15 minutes.
- **Off-CI**: Process full dataset (N≈100) on a local machine or cloud instance with >16 GB RAM.
**Constraints**: 
- **fMRIPrep**: Cannot run on CI for N>1 due to RAM limits. Designated as **Off-CI**.
- **Data**: Strict adherence to OpenNeuro ds000233. No proxies.
- **Stability**: Bootstrap stability analysis restricted to full dataset (off-CI).

> **Dataset-variable fit**: Verified OpenNeuro ds000233 contains **BMRQ** scores and **raw rs-fMRI** NIfTI files. This satisfies the spec requirements.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (Principle I)**: Plan includes pinned `requirements.txt`, random seed setting, and explicit data source URLs (OpenNeuro ds000233). *Status: Compliant*.
2.  **Verified Accuracy (Principle II)**: All citations (OpenNeuro, fMRIPrep, Schaefer) will be validated against primary sources. *Status: Compliant*.
3.  **Data Hygiene (Principle III)**: Plan mandates checksumming of downloaded files and immutable raw data storage. *Status: Compliant*.
4.  **Single Source of Truth (Principle IV)**: Analysis scripts will output CSVs/JSONs that serve as the sole source for paper figures. *Status: Compliant*.
5.  **Versioning Discipline (Principle V)**: Artifact hashes will be tracked in `state/`. *Status: Compliant*.
6.  **Neuro-Imaging Preprocessing Standardization (Principle VI)**: Plan mandates fMRIPrep (CPU) + Schaefer atlas (medium-scale parcellation) + bandpass (0.01-0.1 Hz). *Status: Compliant*.
7.  **Behavioral-Neural Data Alignment (Principle VII)**: Plan includes partial correlation controlling for age, sex, FD, and FDR correction. *Status: Compliant*.

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-relationship-between-b/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    └── output.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Fetches OpenNeuro data (streaming)
│   └── preprocess.py        # fMRIPrep wrapper (Off-CI)
├── analysis/
│   ├── connectivity.py      # Time series extraction & correlation
│   ├── graph_metrics.py     # NetworkX/bctpy calculations + VIF check
│   └── stats.py             # Partial correlation, regression, Power Analysis
├── models/
│   └── schemas.py           # Pydantic models for validation
├── utils/
│   └── logging.py           # Reproducibility logging
└── main.py                  # Orchestration script

tests/
├── contract/
│   └── test_schemas.py      # Validates JSON/YAML outputs
├── integration/
│   └── test_pipeline.py     # End-to-end small run (N=1)
└── unit/
    └── test_metrics.py      # Graph metric correctness

requirements.txt
```

**Structure Decision**: Single project structure chosen to minimize overhead for a computational pipeline. Separation of `data`, `analysis`, and `utils` ensures modularity and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is constrained by CI limits (N=1 validation). No complex architecture is needed. | N/A |

## Implementation Phases

### Phase 1: Data Acquisition & Validation (FR-001)
1.  **Task 1.1: Verify BMRQ Availability**: Download metadata from OpenNeuro ds000233. Check for `BMRQ` column in behavioral data.
    - **Success**: Proceed.
    - **Failure**: Generate `data_gap_report.md` listing missing variables and **halt**.
2.  **Task 1.2: Download Data**: Stream raw rs-fMRI NIfTI and behavioral CSV. Compute checksums.
3.  **Task 1.3: Preprocessing (Off-CI)**: Execute `fMRIPrep` on local/GPU environment. CI runs a **dry-run** (N=1) to verify script logic.

### Phase 2: Feature Extraction (FR-002, FR-003, FR-004)
1.  **Task 2.1: Parcellation**: Extract time series using Schaefer 200 atlas.
2.  **Task 2.2: Connectivity**: Compute Pearson correlation matrices (200x200). Validate symmetry/diagonal.
3.  **Task 2.3: Graph Metrics**: Calculate global efficiency, modularity, participation coefficient, network-specific efficiencies.
4.  **Task 2.4: Multicollinearity Check**: Compute VIF for all predictors. If VIF > 5, apply PCA or remove redundant predictors.

### Phase 3: Statistical Modeling (FR-005, FR-006)
1.  **Task 3.1: Power Analysis**: Calculate achieved power for N subjects and effect size r=0.20. Report if Power < 0.80.
2.  **Task 3.2: Partial Correlation**: Correlate metrics with BMRQ, controlling for age, sex, FD. Apply FDR correction.
3.  **Task 3.3: Regularized Regression**: Fit Ridge/Lasso with 5-fold CV.
4.  **Task 3.4: Stability Analysis (Off-CI)**: Run 1000 bootstrap iterations on full dataset to assess metric stability.

### Phase 4: Reporting
1.  **Task 4.1: Generate Results**: Output `analysis_results.csv` and `data_gap_report.md` (if applicable).
2.  **Task 4.2: Visualization**: Generate scatter plots and network diagrams.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **fMRIPrep RAM Exceeded** | Designated as Off-CI. CI only validates code logic. |
| **BMRQ Missing** | Task 1.1 halts pipeline and generates Data Gap Report. No proxies. |
| **Multicollinearity** | VIF check and PCA fallback implemented in Task 2.4. |
| **Low Power** | Task 3.1 explicitly calculates and reports achieved power. |
| **Synthetic Data** | **Strictly prohibited**. Pipeline halts if real data is missing. |
| **Stability on N=1** | Bootstrap skipped for CI (N=1). Only run on full dataset (Off-CI). |