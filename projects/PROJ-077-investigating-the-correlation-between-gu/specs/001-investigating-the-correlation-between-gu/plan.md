# Implementation Plan: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

**Branch**: `001-investigating-the-correlation-between-gu` | **Date**: 2026-06-24 | **Spec**: `specs/001-investigating-the-correlation-between-gu/spec.md`
**Input**: Feature specification from `/specs/001-investigating-the-correlation-between-gu/spec.md`

## Summary

This project implements a statistical pipeline to investigate the association between gut microbiome alpha diversity (Shannon index) and cognitive performance (fluid intelligence) using UK Biobank data. The approach involves a **Dual-Path Analysis Strategy**:
1.  **Primary Path**: Correlation between raw alpha diversity (Shannon Index) and fluid intelligence using Spearman rank correlation.
2.  **Secondary Path**: Correlation between CLR-transformed taxa abundances and fluid intelligence using Lasso regression to handle high-dimensional compositional data.

The pipeline includes preprocessing (imputation with Mode for categorical and Median for continuous variables), multivariate linear regression with multicollinearity diagnostics (VIF), and False Discovery Rate (FDR) correction. The implementation is constrained to run on CPU-only CI (GitHub Actions free tier) and strictly adheres to the project constitution regarding reproducibility and data hygiene.

**Critical Note on Spec Compliance**: This plan explicitly identifies methodological errors in the source `spec.md` (FR-003, FR-007, US-2) regarding "CLR-transformed alpha diversity" and "median imputation for sex." The plan implements the *statistically correct* methodology (Raw Shannon, Mode for Sex) and marks the Spec requirements as blocking errors requiring amendment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `pandas`, `numpy`, `scikit-bio`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `scipy`  
**Storage**: Local file system (CSV, PNG, YAML artifacts); raw data assumed pre-downloaded to `data/raw/`  
**Testing**: `pytest` (unit tests for data loading, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, 7GB RAM, 14GB disk)  
**Project Type**: Computational research pipeline / data analysis library  
**Performance Goals**: Complete end-to-end analysis within 6 hours; memory usage < 7GB via hard-coded sample limit (N=50,000) and chunked processing.  
**Constraints**: No GPU; no large language model inference; strict adherence to FR-001 through FR-008 (with methodological corrections noted); all statistical claims must be associational.  
**Scale/Scope**: Processing of UK Biobank subset (hard-coded limit N=50,000) to ensure CI feasibility; generation of primary plots and statistical tables.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Spec Conflict Resolution

The following requirements in `spec.md` are identified as methodologically invalid and are **rejected** in this plan. The plan implements the correct statistical procedure and flags these as blocking errors for the Spec:

| Spec Requirement | Issue | Plan Correction |
|------------------|-------|-----------------|
| **FR-003**: "Apply CLR transformation... before... Spearman rank correlation" | CLR is a multivariate transformation for taxa, not applicable to univariate alpha diversity (Shannon). | **Primary Path**: Shannon calculated on **raw** counts/relative abundances. CLR applied **only** to taxa for Secondary Path. |
| **FR-007**: "Impute... sex... using the median" | Sex is categorical; median imputation produces invalid values (e.g., 1.5). | **Imputation**: **Mode** for Sex; **Median** for continuous (Age, BMI, DQS). |
| **US-2, SC-001**: "CLR-transformed alpha diversity metrics" | Logical contradiction; alpha diversity is a scalar summary. | **Correction**: Correlation uses **raw** Shannon Index. CLR used only for taxa-level analysis. |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Plan |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | `requirements.txt` will pin versions; `random_seed` variable set in `code/analysis.py`; data loading scripts will use deterministic paths. |
| **II. Verified Accuracy** | **FAIL** (Pending) | The Spec assumes UK Biobank data is available, but the `# Verified datasets` block provided in the research context contains **no** verified URLs for UK Biobank microbiome/cognitive data. The pipeline cannot run automatically in CI. Status is FAIL until Spec is amended to allow local data or verified URLs are provided. |
| **III. Data Hygiene** | PASS | Raw data will be stored in `data/raw/` with checksums recorded in `state/`. Derived files (e.g., `data/processed/cleaned.csv`) will be new files, not modifications. |
| **IV. Single Source of Truth** | PASS | Statistical outputs will be generated programmatically; figures will be saved with hashes; no hand-typed statistics in reports. |
| **V. Versioning Discipline** | PASS | Content hashes for all artifacts will be tracked in `state/projects/PROJ-077...yaml`. |
| **VI. Statistical Rigor** | PASS | Plan explicitly includes FDR correction, CLR (for taxa only), Multicollinearity diagnostics (VIF), and Residual Normality Validation (for Secondary Path regression). Primary Path (Spearman) does not require residual tests. |
| **VII. Microbiome Data Provenance** | PASS | Raw OTU/ASV table will be archived; `data/processed/` will contain a `provenance.log` linking derived diversity metrics to raw inputs. |

## Project Structure

### Documentation (this feature)

```text
specs/001-investigating-the-correlation-between-gu/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── input_schema.schema.yaml
│   ├── processed_schema.schema.yaml
│   └── output_schema.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-077-investigating-the-correlation-between-gu/
├── data/
│   ├── raw/                  # Pre-downloaded UK Biobank files (microbiome, cognitive, dietary)
│   └── processed/            # Cleaned CSVs, diversity metrics, transformed data
├── code/
│   ├── __init__.py
│   ├── config.py             # Paths, seeds, hyperparameters, sample_limit=50000
│   ├── data_ingestion.py     # FR-001, FR-007 (Mode for Sex, Median for others), FR-008
│   ├── diversity.py          # FR-002 (Shannon on raw data)
│   ├── transformation.py     # CLR transform for taxa only
│   ├── analysis.py           # FR-004, FR-005 (Spearman, Lasso, VIF, FDR)
│   ├── visualization.py      # FR-006 (Plots)
│   └── main.py               # Orchestration script
├── tests/
│   ├── unit/
│   │   ├── test_data_ingestion.py
│   │   ├── test_diversity.py
│   │   └── test_analysis.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing and statistical analysis, ensuring reproducibility and ease of CI execution. The `code/` directory is organized by functional module to match the User Stories and Functional Requirements.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CLR Transformation (Taxa Only) | Microbiome data is compositional; standard correlation on raw counts is invalid for taxa. | Using raw counts for taxa would violate statistical assumptions. CLR is not applied to Shannon Index (Primary Path). |
| Lasso Regression | High-dimensional taxa data (p > n) causes singular matrices in OLS. | Standard OLS fails; L1 regularization is required for feature selection and stability. |
| Mode Imputation (Sex) | Sex is categorical; median imputation creates invalid values. | Median is mathematically undefined for categorical data. |
| Multicollinearity Check (VIF) | DQS and BMI may be highly correlated, destabilizing coefficients. | Unchecked collinearity leads to uninterpretable regression results. |
| Hard-coded Sample Limit | UK Biobank data may exceed 7GB RAM if all raw sequences are loaded at once. | Loading full dataset risks OOM; hard limit ensures CI feasibility. |
| Dual-Path Analysis | Single metric (Shannon) vs. High-dimensional (Taxa) require different methods. | Conflating them leads to methodological errors (e.g., CLR on Shannon). |