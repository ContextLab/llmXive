# Implementation Plan: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

**Branch**: `001-predict-cognitive-flexibility-rsfc-variability` | **Date**: 2024-05-21 | **Spec**: `specs/001-predicting-cognitive-flexibility-rsfc-variability/spec.md`

## Summary

This project implements a computational pipeline to test whether inter-individual variability in resting-state functional connectivity (RSFC) predicts performance on cognitive-flexibility tasks. The approach involves ingesting HCP multi-subject data, parcellating fMRI time-series using the Schaefer atlas, computing sliding-window correlation metrics (standard deviation and Shannon entropy), and performing a permutation-based regression analysis controlling for motion and demographics. The analysis is constrained to run on CPU-only CI (limited cores, constrained RAM) by processing data in batches and using optimized numerical libraries.

**Critical Constraint**: The project relies **strictly** on verified datasets. If the verified data sources do not contain the required raw fMRI NIfTI files and specific NIH Toolbox Dimensional Change Card Sort scores, the primary hypothesis test (FR-005) **cannot** be performed. The project will halt at Phase 0 with a "Data Gap" report. No synthetic data will be used to validate the biological hypothesis.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `nibabel`, `scipy`, `networkx`, `tqdm`, `pyyaml`, `nitime`  
**Storage**: Local file system (CSV/Parquet for tabular data, NIfTI for images)  
**Testing**: `pytest` (contract tests, unit tests for metric computation)  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / Data analysis  
**Performance Goals**: Process 1200 subjects within 6 hours; peak RAM < 7GB; no GPU usage.  
**Constraints**: No CUDA; no large-LLM training; strict motion artifact exclusion (Mean FD > 0.2mm); FDR correction for post-hoc tests.  
**Scale/Scope**: A substantial cohort of subjects, Multi-region parcellation

The research question is to determine how spatial resolution influences the identification of functional networks. The method involves applying a data-driven clustering algorithm to neuroimaging data at varying levels of granularity. References include Smith et al. () and Glasser et al. ()., a high-dimensional edge set per subject.

> **Note on Dataset Fit**: The "Verified datasets" block in `research.md` is the sole source of truth. If the verified sources lack the required raw fMRI or behavioral scores, the pipeline will **not** simulate data for the primary analysis. Instead, it will generate a "Data Gap Report" and halt. Synthetic data generation is restricted to unit testing the code structure only, not hypothesis validation.

## Constitution Check

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Random seeds pinned in `code/`; `requirements.txt` pins versions; data fetched from canonical sources. |
| **II. Verified Accuracy** | PASS | All dataset citations restricted to the "Verified datasets" block; **no simulation** used for hypothesis testing. |
| **III. Data Hygiene** | PASS | Checksums recorded in `state/`; raw data immutable; derivations in new files. |
| **IV. Single Source of Truth** | PASS | Figures/stats trace to `data/` rows; no hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Content hashes updated on artifact changes; `updated_at` timestamp managed. |
| **VI. Motion Artifact Control** | PASS | Mean FD included as covariate; subjects with FD > 0.2mm excluded and logged. |
| **VII. Dynamic Connectivity Parameters** | **DEVIATION (Justified)** | **Default (30s) is statistically invalid** for -region atlas (rank deficiency). **A fixed-duration window is employed to segment the temporal data for analysis.** used with explicit justification in `research.md` to ensure sufficient time points (multiple) for stable correlation estimation. |

## Project Structure

### Documentation (this feature)

```text
specs/001-predict-cognitive-flexibility-rsfc-variability/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── main.py              # Entry point for pipeline execution
├── config.py            # Configuration (paths, seeds, parameters)
├── data/
│   ├── __init__.py
│   ├── download.py      # Data ingestion (FR-001)
│   ├── preprocess.py    # Parcellation (FR-002)
│   └── merge.py         # Behavioral merging (US-1)
├── features/
│   ├── __init__.py
│   ├── connectivity.py  # Sliding window & metrics (FR-003, FR-004)
│   ├── null_model.py    # AR-based surrogate validation (FR-008)
│   └── noise_filter.py  # SNR filtering & Motion-Noise Orthogonalization
├── analysis/
│   ├── __init__.py
│   ├── regression.py    # Linear model (FR-005)
│   └── permutation.py   # Permutation test (FR-006)
├── utils/
│   ├── __init__.py
│   ├── motion.py        # Motion exclusion logic (US-1, US-2)
│   └── plotting.py      # Visualization (US-3)
└── tests/
    ├── test_connectivity.py
    ├── test_regression.py
    └── test_contracts.py

data/
├── raw/                 # Downloaded raw data (checksummed)
├── processed/           # Parcellated time-series, merged CSVs, exclusion logs
│   ├── exclusion_log.csv
│   └── final_results.csv
└── results/             # Regression outputs, plots

docs/
└── ...
```

**Structure Decision**: Single project structure selected to minimize overhead and facilitate end-to-end testing on CI. The `code/` directory is split by functional domain (data, features, analysis) to ensure modularity while keeping dependencies minimal.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Sliding Window Complexity** | Required to capture dynamic variability (FR-003). | Static connectivity (single matrix) cannot measure "variability" as defined in the spec. |
| **Permutation Test** | Required for robust p-value estimation without distributional assumptions (FR-006). | Standard parametric t-test assumes normality which may not hold for RSFC metrics; permutation is more robust. |
| **Batch Processing** | Required to fit within 7GB RAM on CI. | Loading all 1200 subjects' time-series at once would exceed memory limits. |
| **PCA Dimensionality Reduction** | Required to preserve network-specific signal (Methodology Concern). | Aggregating to a single scalar destroys localized effects (Type II error). |
| **AR Surrogate Null Model** | Required to avoid tautological validation (Scientific Soundness Concern). | Phase-shuffling preserves variance, making the test trivial. |

## Output Artifacts

The pipeline must produce the following artifacts to satisfy the spec:

1.  **`data/processed/exclusion_log.csv`**: A CSV containing `Total_Subjects`, `Excluded_Motion`, `Excluded_Missing`, `Excluded_Low_SNR`, and `Pro_Processed` (SC-001).
2.  **`data/processed/final_results.csv`**: A single CSV containing `Subject_ID`, `Flexibility_Score`, `Variability_Component_1`...`N`, `Predicted_Score`, `Residual`, `Model_ID` (FR-007, SC-004).
3.  **`data/results/regression_summary.json`**: A JSON file containing `Beta_Variability`, `SE_Variability`, `Pearson_R`, `P_Value`, `Significance_Status`, `FDR_Q_Value` (if applicable), `Covariates` (SC-003, SC-004, FR-009).
