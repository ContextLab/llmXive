# Implementation Plan: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

**Branch**: `[359-investigating-relationship]` | **Date**: 2026-06-24 | **Spec**: `specs/359-investigating-relationship/spec.md`
**Input**: Feature specification from `specs/359-investigating-relationship/spec.md`

## Summary

This feature implements a cross-sectional analysis pipeline to investigate the relationship between resting-state functional connectivity (frontoparietal and default mode networks) and baseline working memory performance. The system downloads the OpenNeuro `ds` dataset (HCP rs-fMRI release), preprocesses rs-fMRI data with fMRIPrep, extracts network metrics using the Schaefer parcellation, and fits a multiple linear regression model with permutation testing and Holm-Bonferroni correction. The pipeline enforces strict data validation, motion exclusion (mean FD > 0.3mm), and deterministic reproducibility on CPU-only infrastructure.

**Critical Note on Dataset**: The original spec referenced `ds000277` (task-based), but the hypothesis requires resting-state data. The plan switches to a verified rs-fMRI source dataset to ensure data availability.

**Critical Note on Power**: With N=30 and 4 predictors, power is borderline (~0.65 for medium effect). The plan explicitly calculates and reports achieved power. If power < 0.80, results are framed as "exploratory" rather than definitive.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: fMRIPrep (23.1.3), Nilearn, NetworkX, bctpy, scikit-learn, statsmodels, pandas, matplotlib, pyyaml, pymvpa (for PCA)  
**Storage**: Local filesystem (`data/raw/`, `data/preprocessed/`, `data/results/`)  
**Testing**: pytest (unit), integration tests via pipeline execution scripts (validating against `contracts/*.schema.yaml`)  
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7 GB RAM, 14 GB disk)  
**Project Type**: Computational neuroscience pipeline  
**Performance Goals**: Complete valid subset (N ≥ 30) within 24 hours; deterministic reproducibility (SHA-256 hash match)  
**Constraints**: No GPU; strict memory limit (7 GB); motion threshold 0.3 mm (corrected from 3.0 mm); ID matching mandatory  
**Scale/Scope**: ~30-85 participants from ds000278; 400x400 connectivity matrices  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| I. Reproducibility | **PASS** | `RANDOM_SEED` env var (default 42) used in all stochastic steps (permutation, plotting, PCA). fMRIPrep 23.1.3 pinned. Checksums recorded for raw data. |
| II. Verified Accuracy | **PASS** | All citations (fMRIPrep, Schaefer, OpenNeuro ds000278) verified against primary sources. No fabricated URLs. |
| III. Data Hygiene | **PASS** | Raw data preserved in `data/raw/`. Derivations in `data/preprocessed/` and `data/results/`. PII scan enforced. |
| IV. Single Source of Truth | **PASS** | **Explicit Declaration**: `data/results/model_summary.csv` is the Single Source of Truth for all regression results. No hand-typed numbers. |
| V. Versioning Discipline | **PASS** | Content hashes tracked in state file. `updated_at` timestamp updated on artifact change. |
| VI. Neuroimaging Preprocessing Consistency | **PASS** | fMRIPrep.3 used. Schaefer high-resolution parcellation. Pearson correlation matrices. |
| VII. Motion Artifact Exclusion | **PASS** | Mean FD > 0.3 mm exclusion enforced (corrected from 3.0 mm). Exclusion counts logged. Motion metrics saved in `data/motion/`. |

## Project Structure

### Documentation (this feature)

```text
specs/359-investigating-relationship/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-359-investigating-the-relationship-between-b/code/
├── src/
│   ├── __init__.py
│   ├── download.py          # FR-001: Dataset download & checksum
│   ├── preprocess.py        # FR-002: fMRIPrep execution
│   ├── metrics.py           # FR-003, FR-004: Network metric extraction
│   ├── regression.py        # FR-005: Linear regression & permutation
│   ├── visualize.py         # FR-006: PDF report generation
│   └── utils.py             # Logging, ID validation, power analysis
├── tests/
│   ├── contract/
│   │   ├── test_dataset_schema.py       # Validates against contracts/dataset_schema.schema.yaml
│   │   ├── test_pipeline_output.py      # Validates against contracts/pipeline_output.schema.yaml
│   │   ├── test_regression_output.py    # Validates against contracts/regression_output_schema.schema.yaml
│   │   └── test_regression_result.py    # Validates against contracts/regression_result.schema.yaml
│   ├── integration/
│   └── unit/
└── requirements.txt         # Pinned dependencies
```

**Structure Decision**: Single project structure selected. All scripts reside in `code/src/` to ensure isolation and reproducibility within the CI environment.

## Phase 0: Data Validation & Integrity (FR-009, FR-012)

**Goal**: Ensure data validity, ID matching, and behavioral column presence before any processing.

1. **Download**: Fetch `ds000278` (OpenNeuro) and verify checksums.
2. **ID Matching**: Parse participant IDs from rs-fMRI and behavioral data.
   - **ABORT** with exit code 1 if any ID is missing from either source. Log `ID_VALIDATION: FAIL`.
3. **Column Check**: Verify the presence of `nback_dprime` (or `wm_accuracy`) in the behavioral TSV.
   - **ABORT** with exit code 1 if the column is missing. Log `BEHAVIORAL_COLUMN: FAIL`.
4. **Motion Threshold**: Set exclusion threshold to 0.3 mm (corrected from 3.0 mm to match HCP standards).

## Phase 1: Preprocessing & Metric Extraction (FR-002, FR-003, FR-004)

**Goal**: Generate cleaned fMRI data and network metrics.

1. **Preprocess**: Run fMRIPrep 23.1.3.
   - **Memory Constraint**: Run Docker with `--memory g` and fMRIPrep flags `--nprocs [variable] --mem_mb [variable]` to fit available RAM limits..
   - Exclude participants with mean FD > 0.3 mm.
2. **Extract Metrics**: Compute Global Efficiency, Modularity, FPN Strength, DMN Strength.
3. **Log**: Save motion metrics and exclusion counts to `data/logs/pipeline_log.json`.

## Phase 2: Dimensionality Reduction & Power Analysis (FR-010)

**Goal**: Address multicollinearity and verify statistical power.

1. **PCA**: Perform Principal Component Analysis on the four network metrics to extract orthogonal components. This resolves the collinearity risk (FPN/DMN/Global/Modularity are definitionally related).
   - **Contract Validation**: Validate the merged dataset (metrics + demographics) against `contracts/dataset_schema.schema.yaml`.
2. **Power Analysis**: Calculate achieved power for N participants, assuming a medium effect size (Cohen's f2 = 0.15), α = 0.05.
   - **Gate**: If N < 30, abort. If power < 0.80, log a warning and proceed with "exploratory" framing.
   - **Output**: Write `data/results/power_analysis.txt`.

## Phase 3: Regression & Visualization (FR-005, FR-006)

**Goal**: Fit the model and generate reports.

1. **Regression**: Fit linear regression using PCA components (or LASSO fallback) + covariates (Age, Sex).
   - **Contract Validation**: Validate `model_summary.csv` against `contracts/pipeline_output.schema.yaml` and `contracts/regression_output_schema.schema.yaml`.
2. **Permutation**: Run a sufficient number of permutations for p-values.. Apply Holm-Bonferroni correction.
3. **Visualize**: Generate `effect_sizes.pdf`.
   - **Contract Validation**: Validate output against `contracts/regression_result.schema.yaml`.

## Complexity Tracking

No complexity violations detected. The pipeline adheres strictly to the spec and constitution, with added safeguards for memory and statistical power.