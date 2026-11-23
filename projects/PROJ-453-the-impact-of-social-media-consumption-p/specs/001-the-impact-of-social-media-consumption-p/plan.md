# Implementation Plan: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

**Branch**: `001-social-media-cognitive-flexibility` | **Date**: 2024-05-21 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-social-media-cognitive-flexibility/spec.md`

## Summary

This project implements an associational analysis to test whether a derived "platform-switching index" predicts performance on cognitive flexibility measures using public survey data. The technical approach involves: (1) downloading and parsing verified public datasets (HILDA, ESS) via programmatic loaders; (2) constructing a `switching_index` from self-reported frequency and platform count; (3) fitting multiple linear regression models with `cognitive_flexibility_score` as the outcome, controlling for age and screen time; and (4) conducting sensitivity analyses and diagnostic checks (VIF, collinearity flags, residualization). The pipeline is designed to run entirely on CPU within GitHub Actions constraints, using `pandas` for data manipulation and `statsmodels` for statistical modeling.

**Critical Constraint**: The analysis is strictly limited to datasets containing validated cognitive flexibility measures (e.g., WCST, Trail Making). If verified data sources lack these variables, the pipeline halts with a "Data Gap" error. No proxy variables (e.g., text complexity, numeracy) will be used to substitute for the outcome, as this violates construct validity.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas>=2.0.0`, `numpy>=1.24.0`, `statsmodels>=0.14.0`, `scikit-learn>=1.3.0`, `pyyaml>=6.0`, `requests>=2.31.0`, `datasets>=2.14.0`, `pytest>=7.0.0`  
**Storage**: Local filesystem (`data/`, `code/`, `results/`); no external database.  
**Testing**: `pytest` (unit tests for data ingestion logic, contract validation, causal language check).  
**Target Platform**: Linux (GitHub Actions runner, CPU cores, ~7 GB RAM).  
**Project Type**: Data analysis pipeline / Research script.  
**Performance Goals**: Complete full pipeline (download, clean, model, visualize) within 6 hours; memory usage < 6 GB.  
**Constraints**: No GPU required; no authentication tokens for data access; strict adherence to associational framing; all outputs reproducible with pinned seeds.  
**Scale/Scope**: Single dataset processing (HILDA or ESS subset); ~k rows expected; Multiple primary models + sensitivity variants.

> **Risk Note**: The `research.md` indicates that the current "Verified datasets" block contains text/essay datasets or metadata files that may not contain the required tabular survey variables. The pipeline includes a **Phase 0: Data Feasibility Check** to explicitly detect this "Data Gap" and halt with a clear error message before attempting to use the `datasets` library for tabular analysis.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Strategy | Status |
|-----------|---------------------|--------|
| **I. Reproducibility** | All random seeds pinned in `code/`. Data fetched from canonical HuggingFace URLs. `requirements.txt` pins versions. | ✅ Planned |
| **II. Verified Accuracy** | Citations in `research.md` restricted to verified dataset URLs. No external claims without primary source verification. | ✅ Planned |
| **III. Data Hygiene** | Raw data checksummed upon download. Derived variables written to new files. PII scan on all commits. | ✅ Planned |
| **IV. Single Source of Truth** | All statistics in `results/` JSON trace to specific rows in `data/` CSV. No hand-typed numbers in paper. | ✅ Planned |
| **V. Versioning Discipline** | Content hashes for artifacts tracked in state file. `updated_at` timestamp on state update. | ✅ Planned |
| **VI. Measurement Independence** | Self-report predictor and objective outcome stored as distinct columns until regression step. **Survey instruments documented with original validation sources in `data/` as required.** | ✅ Planned |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-media-cognitive-flexibility/
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
projects/PROJ-453-the-impact-of-social-media-consumption-p/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest.py           # Download and parse datasets; validates against contracts/dataset.schema.yaml
│   ├── 02_engineer.py         # Compute switching_index, handle missingness, check variable presence
│   ├── 03_model.py            # Fit regression, VIF, sensitivity, residualization; validates against contracts/output.schema.yaml
│   ├── 04_visualize.py        # Generate plots
│   └── utils.py               # Common helpers (logging, checksums, causal language scanner)
├── data/
│   ├── raw/                   # Downloaded raw files (checksummed)
│   └── processed/             # Cleaned CSVs with derived variables
├── results/
│   ├── models/                # JSON model summaries
│   └── figures/               # PNG/PDF plots
└── tests/
    ├── contract/              # Schema validation tests
    └── unit/                  # Logic tests for variable engineering
```

**Structure Decision**: Single project structure selected. The project is a linear data pipeline (Ingest -> Engineer -> Model -> Visualize) without complex backend/frontend separation. This minimizes overhead and aligns with the CPU-first compute constraint.

## Implementation Phases

### Phase 0: Data Feasibility Check
**Goal**: Verify the presence of required variables in the downloaded dataset before proceeding.
- **Task 0.1**: Load raw data.
- **Task 0.2**: Check for `self_reported_switching_frequency` and `cognitive_flexibility_score` (or validated proxy like WCST).
- **Task 0.3**: If missing, **HALT** with error: "Data Gap: Required variable [NAME] not found in verified dataset [URL]. Project cannot proceed per US-1 Scenario 2."
- **Task 0.4**: If present, validate against `contracts/dataset.schema.yaml`.

### Phase 1: Data Ingestion & Engineering
**Goal**: Create a clean dataset with derived variables.
- **Task 1.1**: Download raw data from verified URL (no auth).
- **Task 1.2**: Parse and clean. Handle missing outcomes (exclude rows, log count).
- **Task 1.3**: Compute `switching_index = num_platforms * switching_frequency`.
- **Task 1.4**: Document instrument validation sources in `data/` (Constitution Principle VI).
- **Task 1.5**: Output `data/processed/participants_cleaned.csv`.

### Phase 2: Model Fitting & Diagnostics
**Goal**: Fit regression and perform rigorous diagnostics.
- **Task 2.1**: Check correlation between `switching_index` and `total_screen_time`. If > 0.7, flag "Mathematical Coupling" and run **Residualized Model** (regress switching on screen_time, use residuals as predictor).
- **Task 2.2**: Mean-center `switching_index` and `age` before creating interaction term `switching_index * age` (to reduce multicollinearity).
- **Task 2.3**: Fit OLS model. Compute VIF for all predictors.
- **Task 2.4**: Run Sensitivity Analysis (FR-005) with alternative definitions (`platform_count`, `switching_frequency`).
- **Task 2.5**: Apply Benjamini-Hochberg (FDR) correction to p-values from sensitivity runs (FR-007).
- **Task 2.6**: Validate output against `contracts/output.schema.yaml`.
- **Task 2.7**: **Causal Language Validation**: Programmatically scan `interpretation` string for forbidden terms (causes, leads to, impacts). If found, **FAIL**.

### Phase 3: Visualization & Reporting
**Goal**: Generate publication-ready plots and final report.
- **Task 3.1**: Generate scatter plots with regression lines and 95% CIs.
- **Task 3.2**: Generate stratified plots if interaction is significant.
- **Task 3.3**: Generate sensitivity table.
- **Task 3.4**: Write final JSON report with associational language only.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project scope is contained within a single linear pipeline. | N/A |