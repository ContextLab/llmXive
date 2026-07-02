# Implementation Plan: The Relationship Between Sleep Chronotype and Moral Judgement

**Branch**: `feature/chronotype-moral-judgement` | **Date**: 2026-06-29 | **Spec**: `specs/chronotype-moral-judgement/spec.md`
**Input**: Feature specification from `specs/chronotype-moral-judgement/spec.md`

## Summary

This feature implements a statistical analysis pipeline to investigate the associational relationship between sleep chronotype (Morningness-Eveningness) and moral foundation scores, controlling for acute sleepiness and chronic sleep quality. The approach involves ingesting a **single, pre-merged** CSV file containing MEQ, MFQ, PSQI, and acute sleepiness data, classifying participants into chronotype groups, performing five separate ANCOVAs with Bonferroni correction, calculating effect sizes, and generating a reproducible R-Markdown report with sensitivity analysis.

**Critical Data Constraint**: The pipeline **MUST** abort if the input data does not contain all required columns (`MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`) for the same participant records. No synthetic data generation or simulation of missing covariates is permitted for the primary analysis, as this would invalidate the scientific hypothesis.

## Technical Context

**Language/Version**: R 4.3+ (via `renv`).
**Primary Dependencies**: `tidyverse`, `lme4`, `car` (for ANOVA/VIF), `effectsize`, `pwr`, `rmarkdown`, `knitr`, `data.table`.
**Storage**: Local CSV files in `data/`; derived artifacts in `data/derived/`.
**Testing**: `testthat` for unit tests; `lintr` for code style; `renv` for dependency reproducibility.
**Target Platform**: GitHub Actions free-tier runner (Ubuntu, 2 CPU, 7GB RAM).
**Project Type**: Computational research pipeline.
**Performance Goals**: Complete analysis and report generation within 6 hours on CPU-only runner.
**Constraints**: No GPU; memory usage < 6GB; strict adherence to Bonferroni correction (α=0.01); **ABORT** if required columns are missing or >20% of rows are unusable.
**Scale/Scope**: Single dataset ingestion; A series of hypothesis tests will be conducted to address the research question using the established method, drawing on the cited references.; report generation.

> **Data Availability Note**: The spec assumptions note that existing public datasets (OSF, HuggingFace) lack the required combination of MEQ, MFQ, PSQI, and acute sleepiness data. Consequently, this pipeline is designed to **require** a user-provided merged dataset (e.g., from primary data collection via Prolific) or a specific merged file provided by the researcher. The pipeline will not attempt to merge disjoint datasets or simulate missing values.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action / Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/analysis.R`. Dependencies pinned via `renv`. |
| **II. Verified Accuracy** | **Compliant** | No fabricated URLs. The plan explicitly acknowledges the lack of a verified merged dataset and requires user-provided data. No synthetic data is used for scientific claims. |
| **III. Data Hygiene** | **Compliant** | Raw data checksummed. Derived data versioned. No in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | Report figures/tables generated directly from `data/processed/` via `code/`. |
| **V. Versioning Discipline** | **Compliant** | Content hashes for data/code recorded in `state/`. |
| **VI. Psychometric Transparency** | **Compliant** | MEQ and MFQ scoring algorithms documented in `code/measurements.md`. Cronbach's α reported. |

## Project Structure

### Documentation (this feature)

```text
specs/chronotype-moral-judgement/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-046-the-relationship-between-sleep-chronotyp/
├── data/
│   ├── raw/             # User-provided merged CSV (must contain all required columns)
│   └── processed/       # Merged, cleaned, and classified data
├── code/
│   ├── 01_ingest.R      # Data loading, validation, and ABORT logic if columns missing
│   ├── 02_classify.R    # Chronotype labeling logic
│   ├── 03_analysis.R    # ANCOVA, effect sizes, power analysis, sensitivity sweep
│   ├── 04_report.Rmd    # Report generation template
│   ├── 05_validate_report.R # Script to verify report content (SC-003)
│   ├── 06_benchmark_accuracy.R # Script to generate benchmark and test 95% accuracy (SC-001)
│   ├── 07_regression_test.R # Script to compare p-values against reference (SC-002)
│   └── measurements.md  # Instrument scoring details
├── tests/
│   └── test-classify.R  # Unit tests for chronotype logic
└── renv.lock            # Dependency lockfile
```

**Structure Decision**: Single-project R structure with clear separation of ingestion, classification, analysis, and reporting steps. Explicit validation scripts added to meet Success Criteria.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | The scope is linear and well-defined (ingest -> classify -> analyze -> report). | No complex architecture required. |

## Implementation Phases

### Phase 0: Data Ingestion & Validation (FR-001, FR-006, FR-007)
1.  **Task**: Implement `code/01_ingest.R`.
2.  **Logic**:
    *   Load raw CSV.
    *   Verify presence of ALL required columns: `MEQ_score`, `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity`, `PSQI`, `acute_sleepiness`, `age`, `sex`.
    *   **ABORT** execution with a clear error message if any column is missing.
    *   Check for missing `acute_sleepiness` values. Flag rows.
    *   Calculate exclusion rate. **ABORT** if >20% of rows are unusable (FR-006).
    *   Log all validation warnings.
    *   Save cleaned data to `data/processed/cleaned_data.csv`.

### Phase 1: Chronotype Classification (FR-002, SC-001)
1.  **Task**: Implement `code/02_classify.R`.
2.  **Logic**:
    *   Apply thresholds: `MEQ >= 59` -> "morning", `MEQ <= 41` -> "evening", else "intermediate".
    *   Flag rows with `NA` or non-numeric `MEQ_score`.
    *   **Task (SC-001)**: Implement `code/06_benchmark_accuracy.R` to generate a synthetic benchmark dataset with known labels, run the classifier, and verify ≥95% accuracy.
3.  **Output**: `data/processed/classified_data.csv` with `chronotype` column.

### Phase 2: Statistical Analysis (FR-003, FR-004, SC-002)
1.  **Task**: Implement `code/03_analysis.R`.
2.  **Logic**:
    *   Run separate ANCOVAs

The research question, method, and references remain unchanged as per the planning document requirements.: `MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`.
    *   Apply Bonferroni correction (α=0.01).
    *   Calculate Cohen's d and 95% CI for significant contrasts.
    *   Calculate VIFs; warn if >2.
    *   **Task (SC-002)**: Implement `code/07_regression_test.R` to generate a "reference R script" output and compare pipeline p-values with ≤0.01 tolerance.
3.  **Output**: `data/derived/ancova_results.csv` and `data/derived/effect_sizes.csv`.

### Phase 3: Reporting & Sensitivity (FR-005, SC-003, SC-004)
1.  **Task**: Implement `code/04_report.Rmd`.
2.  **Logic**:
    *   Generate descriptive tables.
    *   Include ANCOVA tables with adjusted p-values.
    *   Include effect size tables.
    *   Include G*Power summary.
    *   **Task (SC-004)**: Generate sensitivity analysis table for alpha_corrected ∈ {0.01, 0.0125, 0.015}, listing significance status for every MFQ subscale contrast.
    *   **Task (SC-003)**: Implement `code/05_validate_report.R` to parse the generated report and verify presence of all required sections.
3.  **Output**: `reports/chronotype_moral_analysis.html` (or PDF).

## Risk Management

| Risk | Mitigation |
| :--- | :--- |
| **Missing Data** | Pipeline aborts immediately if required columns are missing. No fallback to simulation. |
| **High Exclusion Rate** | Pipeline aborts if >20% of rows are unusable. |
| **Collinearity** | VIF calculated; warning issued if >2. |
| **Low Group Balance** | Alert issued if >70% in intermediate group. |
| **No Verified Merged Dataset** | Documented as a critical blocker. Pipeline requires user-provided merged data. |