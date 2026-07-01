# Implementation Plan: 001-political-news-implicit-bias

**Branch**: `001-political-news-implicit-bias` | **Date**: 2024-05-21 | **Spec**: `spec.md`
**Input**: Feature specification from `/specs/001-the-impact-of-repeated-exposure-to-neutr/spec.md`

## Summary

This feature implements an associational analysis of the impact of self-reported political news exposure on implicit political bias using the Project Implicit dataset. The technical approach involves loading a CSV dataset (with a fallback to user-provided local files), mapping variables via a codebook, handling missing data with Multiple Imputation by Chained Equations (MICE) and a Delta-Adjustment sensitivity check, fitting a linear regression model with an interaction term (News Exposure × Ideology), and performing robustness checks (1000 bootstrap resamples with Monte Carlo SE calculation, alpha sweep, covariate adjustment, and binary ideology split). All results are exported to a PDF report and CSV tables, strictly adhering to CPU-only compute constraints (2 cores, ~7 GB RAM) and framing findings as associational.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `scikit-learn` (for MICE and preprocessing), `statsmodels` (for linear regression and diagnostics), `seaborn`/`matplotlib` (for plotting), `scipy` (for power analysis), `jinja2` (for PDF report generation), `pyyaml` (for schema validation).
**Storage**: Local file system (`data/`, `results/`, `code/`). No external database.
**Testing**: `pytest` (unit tests for data loading, imputation logic, and model output validation).
**Target Platform**: GitHub Actions Free Tier (Linux, 2 CPU, ~7 GB RAM, no GPU).
**Project Type**: Data analysis pipeline / Research artifact generator.
**Performance Goals**: Complete full pipeline (load, impute, model, bootstrap, report) within 6 hours.
**Constraints**: 
- No GPU/CUDA.
- Bootstrap limited to 1000 resamples (per FR-003); stability quantified via Monte Carlo SE.
- Missing data handling halts if >50% missingness in key variables.
- All findings framed as ASSOCIATIONAL.
- **Data Source**: No verified URL exists for the specific "Political IAT" with news exposure variables. The pipeline relies on a user-provided local CSV or a non-verified source. If no data is found, the pipeline halts with a `ValueError`.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. Dependencies pinned in `requirements.txt`. Data fetched from user-provided path or canonical source if available. |
| **II. Verified Accuracy** | **CONDITIONAL** | **Dataset URL is NOT in verified list.** Strategy: Attempt local load from user-provided path. If successful, proceed with analysis but note that "Verified Accuracy" is bypassed. If no data found, raise `ValueError` and halt. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/`. Checksums recorded. Derivations (imputed data) written to new files with provenance. |
| **IV. Single Source of Truth** | **PASS** | Report figures generated programmatically from `results/` CSVs; no hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed; `state.yaml` updated on completion. |
| **VI. Standardized IAT Protocol** | **CONDITIONAL** | **Protocol is standardized ONLY IF the user provides the correct Project Implicit dataset.** Strategy: If user provides a file, the protocol is "User-Defined" and the Constitution check reflects this deviation. If the file matches the Project Implicit schema, standardization is assumed. |
| **VII. Survey Data Integrity** | **PASS** | Raw `news_exposure_freq` preserved; z-scoring creates derived file. |

## Project Structure

### Documentation (this feature)

```text
specs/001-political-news-implicit-bias/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── dataset.schema.yaml
│   └── output.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Paths, seeds, hyperparameters (alpha=0.05, n_boot=1000)
├── data_loader.py       # Load CSV, map codebook, validate columns, handle missing source
├── preprocessing.py     # Z-scoring, MICE imputation, Delta-Adjustment sensitivity, missingness checks
├── models.py            # Linear regression fitting, interaction term handling
├── robustness.py        # Bootstrap (1000), Monte Carlo SE calc, alpha sweep, covariate adjustment, binary split
├── power.py             # Prospective (literature-based) and Retrospective (descriptive) power analysis
├── reporting.py         # Generate PDF and CSV artifacts
└── main.py              # Orchestrator: data -> prep -> model -> robustness -> report

data/
├── raw/                 # User-provided CSV, codebook
└── processed/           # Imputed data, derived variables

results/
├── report.pdf
├── model_summary.csv
└── diagnostics.csv
```

**Structure Decision**: Single project structure (`code/`) selected for simplicity and direct data-to-report flow. No backend/frontend split required for this research artifact.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **MICE Imputation** | Required by FR-008 and US-1 to handle missing data robustly while preserving variance. | Simple mean imputation would bias standard errors and violate FR-008. |
| **Bootstrap (1000 resamples)** | Required by FR-003 to assess stability of interaction effect in observational data. | Single-sample CI would not satisfy robustness requirement for P2. Stability is quantified via Monte Carlo SE to address potential instability. |
| **Alpha Sweep** | Required by FR-004 to test sensitivity to significance thresholds. | Fixed alpha=0.05 would miss robustness insights required by US-2. |
| **Binary Ideology Split** | Required by FR-006 for secondary sensitivity checks. | Continuous-only analysis would miss non-linear effects or threshold behaviors. |
| **Delta-Adjustment Sensitivity** | Required to address MNAR missingness concerns. | MAR-only assumption risks bias if missingness is systematic. |
| **Prospective Power Analysis** | Required by FR-007 to validate design before analysis. | Post-hoc power is tautological and provides no validation. |

## Phase Breakdown

### Phase 0: Research & Data Strategy
- **Task 0.1**: Confirm dataset availability (user-provided or local). If not found, raise `ValueError`.
- **Task 0.2**: Validate variable mapping via codebook.
- **Task 0.3**: Define prospective power analysis parameters (effect size from literature).

### Phase 1: Data Preparation
- **Task 1.1**: Load data and map variables.
- **Task 1.2**: Perform MICE imputation (multiple imputations).
- **Task 1.3**: Perform Delta-Adjustment sensitivity analysis for MNAR.
- **Task 1.4**: Create derived variables (`news_exposure_z`, `ideology_binary`).

### Phase 2: Modeling & Robustness
- **Task 2.1**: Fit primary linear regression (continuous ideology).
- **Task 2.2**: Fit secondary model with binary ideology (FR-006).
- **Task 2.3**: Execute bootstrap (1000 resamples) and calculate Monte Carlo SE.
- **Task 2.4**: Execute alpha sweep across a range of regularization parameters.
- **Task 2.5**: Execute covariate adjustment (age, gender, education).

### Phase 3: Reporting
- **Task 3.1**: Perform prospective power analysis (design validation).
- **Task 3.2**: Calculate retrospective (observed) power (descriptive only).
- **Task 3.3**: Generate PDF report and CSV summaries.
- **Task 3.4**: **Explicitly report** the binary ideology split results alongside the primary model (FR-006).

## Compute Feasibility

- **Environment**: CPU-only (2 cores, 7 GB RAM).
- **Constraints**:
  - No GPU.
  - Bootstrap limited to 1000 resamples (per spec); stability quantified via Monte Carlo SE.
  - A MICE approach with a sufficient number of imputations is CPU-tractable.
  - Linear regression is fast.
- **Mitigation**: If bootstrap exceeds 6 hours, save partial state and report convergence rate.