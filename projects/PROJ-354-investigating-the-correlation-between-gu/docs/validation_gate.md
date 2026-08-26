# Validation Gate Documentation

## Overview
This document describes the validation gates implemented in the pipeline to ensure data quality, methodological correctness, and reproducibility.

## Gate 1: Power Analysis (T019)
**Purpose**: Validate that the study has sufficient statistical power before processing real data.

**Method**:
- Generate synthetic dataset with expected effect size (β=0.1)
- Calculate theoretical power
- Run simulation to validate power calculation

**Gate Criteria**:
- Calculated power ≥ 0.8
- Required sample size ≤ available sample size
- Explicit PASS/FAIL statement in report

**Output**: `results/validation/power_report.json`

## Gate 2: Instrument Citation Validation (T024a)
**Purpose**: Verify that cognitive instrument citations are accurate and from primary sources.

**Method**:
- Validate each citation against primary literature
- Generate validation report with citation details
- Enforce citation validity in analysis code

**Gate Criteria**:
- All citations verified against primary sources
- Report generated with validation details
- Analysis code enforces validated citations

**Output**: `results/validation/instrument_citation_report.md`

## Gate 3: Data Integrity (T005)
**Purpose**: Ensure data files are complete and uncorrupted.

**Method**:
- Compute SHA256 checksums for all data files
- Validate checksums after download
- Mask PII in processed data

**Gate Criteria**:
- All checksums match
- PII successfully masked
- Data integrity validation passes

**Output**: `data/raw/checksums.json`, `results/validation/data_integrity_report.json`

## Gate 4: Cohort Retention (T016)
**Purpose**: Document cohort filtering and retention rates.

**Method**:
- Track exclusion counts for each filtering step
- Calculate retention rates
- Generate retention log

**Gate Criteria**:
- Retention rate ≥ 50% (or documented justification for lower)
- All exclusion reasons documented
- Retention log generated

**Output**: `data/processed/cohort_retention_log.json`

## Gate 5: Age Group Validation (T015.5)
**Purpose**: Verify age group derivation is correct.

**Method**:
- Derive age groups from continuous age
- Validate distribution across groups
- Generate validation report

**Gate Criteria**:
- Age group cutoff correctly applied
- Distribution documented
- Validation report generated

**Output**: `results/validation/age_group_check.json`

## Gate 6: Confounder Validation (T020c)
**Purpose**: Ensure all required confounders are present and properly handled.

**Method**:
- Validate presence of all confounders from FR-004
- Check for missing values
- Ensure proper encoding

**Gate Criteria**:
- All confounders present
- Missing values handled appropriately
- Validation passes

**Output**: Included in analysis logs

## Gate 7: Multiple Testing Correction (T021)
**Purpose**: Verify Benjamini-Hochberg correction is correctly applied.

**Method**:
- Apply BH correction to all p-values
- Validate adjusted p-value ordering
- Check FDR control

**Gate Criteria**:
- BH correction correctly applied
- Adjusted p-values properly ordered
- FDR controlled at α=0.05

**Output**: `results/associations/main_effects.parquet` with adjusted p-values

## Gate 8: Model Selection (T030c)
**Purpose**: Select final model based on convergence and stability.

**Method**:
- Compare Lasso vs Ridge convergence
- Evaluate stability metrics
- Select optimal model

**Gate Criteria**:
- Convergence achieved for selected model
- Stability metrics acceptable
- Selection justified

**Output**: `results/sensitivity/model_selection_report.json`

## Gate Execution Order
1. Power Analysis (T019) - Must pass before data download
2. Instrument Validation (T024a) - Must pass before analysis
3. Data Integrity - After download, before preprocessing
4. Cohort Retention - After preprocessing
5. Age Group Validation - After age group derivation
6. Confounder Validation - Before analysis
7. Multiple Testing Correction - During analysis
8. Model Selection - After analysis, before final reporting

## Failure Handling
If any gate fails:
1. Log detailed error information
2. Stop pipeline execution
3. Generate failure report
4. Require manual intervention to proceed
