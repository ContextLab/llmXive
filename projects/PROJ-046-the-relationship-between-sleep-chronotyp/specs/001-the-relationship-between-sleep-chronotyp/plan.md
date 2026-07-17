# Implementation Plan: The Relationship Between Sleep Chronotype and Moral Judgement

**Branch**: `feature/chronotype-moral-judgement` | **Date**: 2026-06-29 | **Spec**: `specs/001-the-relationship-between-chronotype-moral-judgement/spec.md`
**Input**: Feature specification from `/specs/001-the-relationship-between-chronotype-moral-judgement/spec.md`

## Summary

This feature implements a reproducible statistical analysis pipeline to test whether individuals with later sleep chronotypes (evening types) exhibit systematically different patterns of moral judgement compared to earlier chronotypes, independent of acute sleep deprivation. The approach involves ingesting CSV data, classifying chronotypes using the Morningness-Eveningness Questionnaire (MEQ) thresholds, performing a Multivariate Analysis of Covariance (MANCOVA) followed by univariate ANCOVAs on Moral Foundations Questionnaire (MFQ) subscales while controlling for sleep quality (PSQI) and acute sleepiness, and generating a comprehensive R-Markdown report with effect sizes, sensitivity analysis, and robustness checks.

**Critical Note on Data & Scientific Integrity**: This pipeline is a **scientific tool** designed to analyze real data. It does **not** generate or validate scientific results using synthetic data for the ANCOVA/MANCOVA steps. The CI runner will execute unit tests on the classification logic (using a synthetic benchmark for SC-001) but will **skip** the statistical analysis phase if the required real data file (containing MEQ, MFQ, PSQI, and Acute Sleepiness) is not present, preventing any fabricated results. No synthetic covariates are used to simulate the covariance structure required for the hypothesis "independent of acute sleep deprivation."

## Technical Context

**Language/Version**: R 4.3+ (via `renv` for reproducibility)  
**Primary Dependencies**: `tidyverse`, `car` (for Anova/VIF), `manova`, `parameters`, `effectsize`, `ggplot2`, `knitr`, `rmarkdown`, `pwr`, `lintr`, `testthat`  
**Storage**: Local CSV/Parquet files in `data/raw/` and `data/processed/`  
**Testing**: `testthat` for unit tests on classification logic; `lintr` for code quality  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, sufficient RAM)  
**Project Type**: Statistical Analysis Pipeline / Research Artifact  
**Performance Goals**: Complete analysis on n=159+ within 6 hours; memory < 7 GB  
**Constraints**: Must run without GPU; must handle missing data gracefully; must enforce Bonferroni correction (α=0.01); must abort if >20% data unusable.  
**Scale/Scope**: Single dataset analysis; MANCOVA + ANCOVAs

A MANCOVA will be conducted alongside a series of ANCOVAs.; A sensitivity sweep will be conducted. The research question, method, and references remain as specified in the original planning document.; final report.  
**Dependency Management**: `renv` is used for R package management. The `renv.lock` file serves the same purpose as `requirements.txt` in Python, ensuring reproducible environments as per Constitution Principle I.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates `renv` lockfile, pinned seeds in `code/`, and automated CI re-runs.
- **II. Verified Accuracy**: All citations (MEQ, MFQ, PSQI) will be validated against the provided `# Verified datasets` block. **No synthetic data is used for scientific validation.** The pipeline only validates the *code* against a synthetic benchmark for classification (SC-001); scientific results require real data.
- **III. Data Hygiene**: Raw data is preserved; transformations produce new files with checksums. PII scan enforced.
- **IV. Single Source of Truth**: All report figures/statistics generated directly from `code/` scripts, not hand-typed.
- **V. Versioning Discipline**: Content hashes tracked in `state/` YAML; artifacts invalidated on change. The `state/PROJ-046...yaml` file will be updated with hashes of `data/` and `code/` artifacts after each run.
- **VI. Psychometric Transparency**: Plan includes explicit recording of MEQ (standardized items, Horne & Östberg) and MFQ (Graham et al.) scoring algorithms and Cronbach's α calculation in `code/measurements.md`. Any simulation logic used *only* for unit tests is documented separately as "Simulation Protocol" to distinguish it from validated instruments.

## Project Structure

### Documentation (this feature)

```text
specs/001-the-relationship-between-chronotype-moral-judgement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── tasks.md             # Phase 2 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-046-the-relationship-between-sleep-chronotyp/
├── data/
│   ├── raw/             # Downloaded raw CSVs/Parquets (immutable)
│   └── processed/       # Cleaned data, classification results
├── code/
│   ├── 01_ingest_classify.R
│   ├── 02_mancova_ancova.R
│   ├── 03_report_render.R
│   ├── 04_lint_check.R
│   ├── measurements.md  # Psychometric scoring details
│   └── renv.lock        # R environment lockfile
├── reports/
│   └── analysis_report.html
├── tests/
│   ├── test-classification.R
│   └── test-ancova.R
├── .github/
│   └── workflows/
│       └── ci.yml       # Automated pipeline
└── README.md
```

**Structure Decision**: Single-project R analysis structure. Chosen for direct alignment with statistical workflow (ingest -> analyze -> report) and ease of `renv` management. No separate backend/frontend required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is strictly defined by the spec (MANCOVA, 5 ANCOVAs, 1 report). | N/A |

## Implementation Phases

### Phase 0: Research & Data Strategy
- **Task**: Verify MEQ and MFQ scoring algorithms (Horne & Östberg, 1976; Graham et al., 2009).
- **Task**: Document Data Collection Protocol for PSQI and Acute Sleepiness (since no real combined dataset exists).
- **Task**: Define MANCOVA and ANCOVA statistical assumptions.

### Phase 1: Data Model & Contracts
- **Task**: Define `ParticipantRecord` schema with all required columns.
- **Task**: Define `AnalysisResult` schema for MANCOVA/ANCOVA output.
- **Task**: Create `contracts/` YAML files for validation.

### Phase 2: Pipeline Implementation
- **Task**: `01_ingest_classify.R`:
  - Ingest CSV.
  - Validate columns.
  - Classify chronotype (MEQ thresholds).
  - **Abort Logic (FR-006)**: If >20% rows unusable (missing MEQ/Acute Sleepiness/MFQ), log error and abort (FR-006).
  - Generate `data/processed/cleaned_data.csv`.
- **Task**: `02_mancova_ancova.R`:
  - **Data Check**: If `cleaned_data.csv` is missing or empty, skip analysis (CI will pass but report will note "No Data").
  - Run MANCOVA (Hotelling's Trace) for overall pattern.
  - If MANCOVA significant, run 5 univariate ANCOVAs with Bonferroni correction.
  - Calculate VIF (must be < 2).
  - Calculate Cohen's d and confidence intervals for significant contrasts.
  - Perform Sensitivity Analysis (alpha: a range of small significance levels).
  - Generate `data/processed/analysis_results.json`.
- **Task**: `03_report_render.R`:
  - Generate R-Markdown report with:
    - Descriptive stats.
    - MANCOVA/ANCOVA tables.
    - Effect sizes.
    - **Sensitivity Matrix** (SC-004): Cross-tabulate significance status for every subscale at a range of corrected alpha levels.
    - Power/Efficiency analysis (Sensitivity for effect size).
- **Task**: `04_lint_check.R`:
  - Run `lintr::lint_dir("code/")`.
  - Ensure cyclomatic complexity < 10.
  - Generate `reports/lint_report.txt`.

### Phase 3: Unit Testing & Benchmarking
- **Task**: Generate `data/benchmark/synthetic_benchmark.csv` with *known* chronotype labels (SC-001).
- **Task**: Run `01_ingest_classify.R` on benchmark.
- **Task**: Verify classification accuracy ≥ 95% (SC-001).
- **Task**: Run `test-classification.R` and `test-ancova.R`.

### Phase 4: CI/CD Configuration
- **Task**: Create `.github/workflows/ci.yml`:
  - Setup R environment.
  - Restore `renv`.
  - Run unit tests.
  - Run linting (T031).
  - Run classification benchmark.
  - **Skip** analysis if `data/raw/study_data.csv` is missing.
  - Generate report (if data present).

### Phase 5: Documentation
- **Task**: Generate `quickstart.md` with installation and usage instructions (T032).
- **Task**: Validate `quickstart.md` against actual pipeline execution.

## Task Mapping to Requirements

| Requirement | Phase | Task |
|-------------|-------|------|
| FR-001 (Ingest) | Phase 2 | `01_ingest_classify.R` |
| FR-002 (Classify) | Phase 2 | `01_ingest_classify.R` |
| FR-003 (ANCOVA/MANCOVA) | Phase 2 | `02_mancova_ancova.R` |
| FR-004 (Effect Sizes) | Phase 2 | `02_mancova_ancova.R` |
| FR-005 (Report) | Phase 2 | `03_report_render.R` |
| FR-006 (Abort >20%) | Phase 2 | `01_ingest_classify.R` (Abort Logic) |
| FR-007 (Acute Sleepiness) | Phase 2 | `01_ingest_classify.R` (Validation) |
| SC-001 (Benchmark) | Phase 3 | Unit Test & Benchmark Generation |
| SC-002 (Accuracy) | Phase 3 | Unit Test |
| SC-003 (Report Sections) | Phase 2 | `03_report_render.R` |
| SC-004 (Sensitivity Matrix) | Phase 2 | `03_report_render.R` |

## Compute Feasibility

- **CPU-First**: All operations are lightweight statistical operations in R.
- **Memory**: Estimated < 500 MB for n=1000.
- **Time**: < 10 minutes for full pipeline on 2 CPU cores.
- **GPU**: Not required.
- **Data Handling**: If real data is large, stream via `data.table::fread` or chunked reading.

## Data Availability & CI Strategy

- **Real Data**: No public dataset contains all required variables (MEQ, MFQ, PSQI, Acute Sleepiness). The pipeline requires the user to provide `data/raw/study_data.csv`.
- **CI Behavior**:
  - If `data/raw/study_data.csv` is **missing**: CI runs unit tests and classification benchmark only. Analysis step is skipped. Report is generated with "No Data" notice.
  - If `data/raw/study_data.csv` is **present**: CI runs full analysis pipeline.
- **Synthetic Data**: Only used for **unit testing** the classification logic (SC-001) with known ground truth. **Never** used for ANCOVA/MANCOVA results.
