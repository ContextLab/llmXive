# Implementation Plan: Investigating the Impact of Early Life Stress on Hippocampal Subfield Volumes

**Branch**: `001-gene-regulation` | **Date**: 2025-01-15 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a statistical analysis pipeline to investigate the association between Early Life Stress (measured by ACE scores) and Hippocampal Subfield Volumes (CA3, DG, subiculum) using the ABCD Study Release. The approach involves acquiring phenotypic and imaging data, preprocessing (filtering, normalization, Inverse Normal Transformation for ACE), fitting linear mixed-effects models (LMM) with family-level random effects, applying Bonferroni correction for the three primary subfields, and conducting robustness checks via **cluster-level** permutation tests and sensitivity analyses. All findings will be framed as associational. The CA3:DG ratio is treated as a descriptive, exploratory outcome and excluded from multiple comparison correction.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn` (for preprocessing utilities), `pyyaml`, `requests`, `joblib`  
**Storage**: Local file system (CSV, TSV, YAML); no database required.  
**Testing**: `pytest` (contract tests, unit tests for data transformations, integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).  
**Project Type**: Computational Neuroscience / Data Analysis Pipeline  
**Performance Goals**: Total runtime ≤ 6 hours; primary modeling ≤ 45 minutes; permutation tests ≤ 3 hours.  
**Constraints**: CPU-only execution (no GPU/CUDA); memory footprint < 7 GB; strict adherence to ABCD Study data usage policies; no causal claims.  
**Scale/Scope**: Single cohort analysis (ABCD Release); primary subfield models + 1 exploratory ratio model (descriptive).  
**Statistical Rigor**: Cluster-level permutation for LMM robustness; Inverse Normal Transformation (INT) for ACE scores; residualization strategy for collinearity.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail & Artifact Reference |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/config.py` (line 12). Data fetched from canonical ABCD source (verified via checksums in `code/data/acquisition.py`). `requirements.txt` pins all dependencies. |
| **II. Verified Accuracy** | **PASS** | All citations in `research.md` and `paper/` will be validated against primary sources. Title overlap ≥ 0.7 enforced by Reference-Validator. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/` with MD5 checksums recorded in `state/projects/PROJ-160-investigating-the-impact-of-early-life-s.yaml`. Transformations produce new files in `data/processed/` via `code/data/preprocessing.py`. PII scan enforced. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in reports trace to `data/processed/` and `code/`. No hand-typed numbers in `paper/`. `code/analysis/results.py` generates all summary stats. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. State file updated on artifact changes. `code/config.py` version string matches spec version. |
| **VI. Statistical Correction** | **PASS** | Bonferroni correction (p < 0.0167) applied for 3 subfields only. **Cluster-level** permutation tests (5,000) implemented for robustness in `code/analysis/robustness.py`. Ratio model excluded from correction. |
| **VII. Imaging Data Integrity** | **PASS** | Volumes sourced from Freesurfer-derived ABCD Release. Poor quality flags excluded in `code/data/preprocessing.py`. ICV normalization mandatory. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-160-investigating-the-impact-of-early-life-s/
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, constants
│   ├── data/
│   │   ├── acquisition.py    # FR-001: Download & verify
│   │   ├── preprocessing.py  # FR-002, FR-003, FR-011: Filter, Normalize, INT
│   │   └── loaders.py        # Data loading utilities
│   ├── analysis/
│   │   ├── modeling.py       # FR-004, FR-005, FR-006: LMM fitting
│   │   ├── robustness.py     # FR-007, FR-008, FR-009: Cluster Permutation, Sensitivity
│   │   └── results.py        # Aggregation & reporting (AnalysisResult entity)
│   └── main.py               # Orchestration script
├── data/
│   ├── raw/                  # Downloaded ABCD files (checksummed)
│   └── processed/            # Cleaned, normalized datasets
├── tests/
│   ├── contract/             # Schema validation tests (tests/test_contracts.py)
│   ├── integration/          # Pipeline end-to-end tests (tests/test_robustness.py)
│   └── unit/                 # Transformation logic tests (tests/test_preprocessing.py)
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure (`code/`, `data/`, `tests/`) chosen for a linear, single-cohort analysis pipeline. This minimizes overhead and aligns with the "script-based" nature of the statistical workflow.

## Test Coverage Matrix

| Requirement / Story | Test Category | Test File / Contract | Description |
| :--- | :--- | :--- | :--- |
| **FR-001** (Download) | Integration | `tests/integration/test_acquisition.py` | Verifies MD5 checksum and file existence. |
| **FR-002** (Filter) | Unit | `tests/unit/test_preprocessing.py` | Verifies exclusion of missing ACE/poor quality. |
| **FR-003** (Normalize) | Unit | `tests/unit/test_preprocessing.py` | Verifies ICV division and precision. |
| **FR-004** (LMM) | Integration | `tests/integration/test_modeling.py` | Verifies model fit and formula. |
| **FR-005** (Bonferroni) | Unit | `tests/unit/test_results.py` | Verifies p-value correction logic. |
| **FR-006** (Ratio) | Unit | `tests/unit/test_modeling.py` | Verifies ratio calculation (descriptive). |
| **FR-007** (Permutation) | Integration | `tests/integration/test_robustness.py` | Verifies cluster-level permutation logic. |
| **FR-008** (Sensitivity) | Unit | `tests/unit/test_robustness.py` | Verifies alpha sweep logic. |
| **FR-009** (ICV Restriction) | Unit | `tests/unit/test_robustness.py` | Verifies subsetting and effect change. |
| **FR-010** (Associational) | Contract | `contracts/model_results.schema.yaml` | Schema enforces `interpretation` field. |
| **FR-011** (INT) | Unit | `tests/unit/test_preprocessing.py` | Verifies INT transformation logic. |
| **US-1** (Data Acq) | Integration | `tests/integration/test_acquisition.py` | End-to-end download and filter. |
| **US-2** (Modeling) | Integration | `tests/integration/test_modeling.py` | End-to-end model fit and correction. |
| **US-3** (Robustness) | Integration | `tests/integration/test_robustness.py` | End-to-end permutation and sensitivity. |
| **Contracts** | Contract | `tests/test_contracts.py` | Validates `dataset.schema.yaml` and `model_results.schema.yaml`. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Cluster-Level Permutation** | Required for LMM validity. Permuting individual ACE scores breaks the exchangeability assumption of the random intercept (family_id), leading to anti-conservative p-values. | Individual-level permutation is statistically invalid for clustered data and would produce scientifically unsound robustness checks. |
| **Inverse Normal Transformation (INT)** | ACE scores are ordinal counts ranging from zero to ten with high zero-inflation. Log-transformation distorts the relationship and is inappropriate for discrete data. INT ensures linearity assumptions are met without arbitrary thresholding. | Log-transformation is statistically invalid for zero-heavy ordinal counts and would bias effect size interpretation. |
| **Residualization Strategy** | Age and scanner site are often correlated (cohort effects). If VIF > 5, standard errors inflate, risking Type II errors. Pre-specified residualization (regressing ACE on age/site) or centering controls this design flaw. | Post-hoc "caution" is insufficient for rigorous neuroimaging analysis; a design control is required to ensure stable estimates. |
| **Ratio Exclusion from Correction** | The CA3:DG ratio is algebraically dependent on the primary outcomes. Including it in Bonferroni correction would be overly conservative; excluding it requires explicit justification as a descriptive metric. | Treating the ratio as a standard hypothesis test without correction inflates FWER; treating it as a 4th test to correct is statistically questionable due to dependency. |

## Edge Case Handling

- **Data Download Failure**: `code/data/acquisition.py` will retry times with exponential backoff. If it fails, the pipeline exits with a clear error code and checksum mismatch report.
- **Extreme ACE Outliers**: Participants with ACE > 3 SD are flagged in `data/processed/` but not automatically excluded unless specified by FR-002 (missing/poor quality). Sensitivity analysis (FR-009) will assess impact.
- **Missing Subfield Volumes**: Participants with missing CA3/DG/Subiculum data are excluded during the specific model fit (FR-004), reducing N for that specific model.
- **Multicollinearity**: `code/analysis/modeling.py` calculates VIF. If VIF > 5 for any covariate, the model automatically switches to the residualization strategy (regressing ACE on the collinear covariate) before fitting the LMM.
- **Permutation Timeout**: If the 5,000 cluster permutations exceed the 6-hour limit, the `joblib` parallelization will be scaled back, and a warning logged. The pipeline will report the partial result but flag it as incomplete.

## Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (multi-core CPU, ~7 GB RAM).
- **Memory**: The ABCD phenotypic CSV is large., and the imaging stats file is larger. However, loading only the required columns (ACE, Age, Sex, Site, FamilyID, CA3, DG, Subiculum, ICV) into a Pandas DataFrame will easily fit in 7 GB RAM.
- **Runtime**:
  - Data Download/Filter: < 15 mins.
  - Primary LMM: < 10 mins.
 - **Cluster Permutation (x 3 models)**: This is the bottleneck. On 2 CPUs, [deferred] fits might take several hours.
    - *Mitigation*: The plan uses `joblib` with `n_jobs=2` and pre-computed design matrices. The cluster-level permutation reduces the number of unique shuffles compared to individual-level, aiding speed.
- **No GPU**: All operations are linear algebra (CPU native). No deep learning.

## Data Fit & Limitations

- **Variable Availability**: The ABCD Study release contains all required variables.
- **Collinearity**: Age and Scanner Site may be correlated. The plan includes a pre-specified residualization strategy if VIF > 5.
- **ACE Distribution**: ACE scores are often skewed. The plan uses Inverse Normal Transformation (INT) instead of log1p to meet linearity assumptions.
- **Causal Inference**: The study is observational. The plan strictly frames results as **associational** (FR-010). No causal claims will be made.
- **Ratio Model**: The CA3:DG ratio is treated as descriptive only, acknowledging algebraic dependency and non-additive error structure.