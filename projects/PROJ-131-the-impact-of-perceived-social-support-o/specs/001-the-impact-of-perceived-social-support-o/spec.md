# Specification: The Impact of Perceived Social Support on Resilience to Online Harassment

## Overview
This project investigates the buffering effect of perceived social support on mental health outcomes (depression, anxiety, PTSD) following exposure to online harassment. The analysis strictly adheres to the **Revised Approach** (Single-Dataset Analysis) using the Cyberbullying Survey 2021, as mandated by the project Plan to ensure methodological validity.

## 1. Functional Requirements

### FR-001: Data Sources (DEPRECATED)
> **Status**: DEPRECATED per Plan's 'Critical Methodological Pivot'.
> **Original**: The system shall ingest two datasets: Cyberbullying Survey 2021 and GSS 2022.
> **Resolution**: The dual-dataset matching approach was found to introduce confounding. Only the Cyberbullying Survey 2021 is used.

### FR-002: Synthetic Cohort Construction (DEPRECATED)
> **Status**: DEPRECATED per Plan's 'Critical Methodological Pivot'.
> **Original**: The system shall construct a synthetic cohort by matching individuals across datasets.
> **Resolution**: Synthetic cohort construction is methodologically invalid for estimating genuine psychological buffering effects.

### FR-003: Variable Harmonization
The system shall harmonize variables for social support, harassment exposure, and mental health outcomes across the single dataset (Cyberbullying Survey 2021).

### FR-004: Missing Data Handling
The system shall handle missing data using Multiple Imputation by Chained Equations (MICE) for predictor variables, with listwise deletion for critical outcome variables.

### FR-005: Sensitivity Analysis and Stratification
The system shall perform sensitivity analyses to test the robustness of the interaction effect.
1. **Continuous Severity**: Re-fit models using continuous harassment severity instead of binary exposure.
2. **Platform Stratification**: Stratify the analysis by **all available platforms** present in the dataset.
 - **Constraint**: If a platform group has fewer than 2 distinct categories or N < 30, that group must be excluded from stratification and logged as `E-SMALL-N-001`.
 - **Constraint**: The system shall **NOT** arbitrarily truncate the list of platforms to the "top three". All valid platforms meeting the N >= 30 threshold must be included in the stratified analysis.
3. **Comparison**: Compare interaction coefficients from sensitivity runs against the baseline model to assess stability.

### FR-006: Interaction Modeling
The system shall fit OLS regression models with heteroskedasticity-consistent (HC3) standard errors, including an interaction term between Social Support and Harassment Exposure for each mental health outcome.

### FR-007: Uncertainty Quantification
The system shall compute bias-corrected accelerated (BCa) bootstrap confidence intervals (1,000 resamples) for all interaction coefficients.

### FR-008: Multiple Comparison Correction
The system shall apply Benjamini-Hochberg FDR correction across the set of outcome tests (Depression, Anxiety, PTSD).

## 2. User Stories

### US-1: Data Ingestion & Cohort Preparation (DEPRECATED Synthetic Cohort)
> **Status**: MODIFIED. The "Synthetic Cohort" requirement has been removed.
> **Goal**: Ingest the Cyberbullying Survey 2021, harmonize variables, handle missingness, and prepare a clean analysis cohort.
> **Acceptance Criteria**:
> - Dataset ingested from `data/raw/cyberbullying_2021.csv` (or verified source).
> - MICE imputation applied with `m=5`, `max_iter=10`.
> - Output: `data/results/analysis_cohort.csv` with validated schema.

### US-2: Interaction Analysis & Hypothesis Testing
> **Goal**: Fit robust OLS models with interaction terms and compute bootstrapped CIs.
> **Acceptance Criteria**:
> - Models fitted with HC3 SEs.
> - BCa bootstrap CIs computed (1,000 resamples).
> - FDR correction applied.
> - Output: `data/results/regression_results.csv` and `data/results/regression_summary.md`.

### US-3: Sensitivity Analysis & Robustness Checks
> **Goal**: Re-run models with alternative definitions and stratification.
> **Acceptance Criteria**:
> - Continuous severity model fitted.
> - Stratification performed by **all** valid platforms (N >= 30).
> - Output: `data/results/sensitivity_analysis.csv` and coefficient comparison table.

## 3. Success Criteria

### SC-001: Cohort Validity (REVISED)
> **Status**: REVISED for Single-Dataset Approach.
> **Original**: Standardized Mean Difference (SMD) < 0.1 between synthetic cohorts.
> **New Criterion**:
> 1. **Variance Check**: Harassment Exposure must have SD > 0.5 and N > 30 in the analysis cohort.
> 2. **Collinearity Check**: Variance Inflation Factor (VIF) for the model matrix (including interaction) must be < 5.
> 3. **Note**: The SMD check is **inapplicable** to the single-dataset approach and is removed from success criteria.

### SC-002: Model Convergence
All primary and sensitivity models must converge. If convergence fails, the system must fall back to standard OLS (no HCSE) and log `E-NONCONV-001`.

### SC-003: Reproducibility
The pipeline must produce identical results (hash match) when run with the same seed defined in `config/seeds.yaml`.

## 4. Data Dictionary

| Variable | Description | Source |
|:--- |:--- |:--- |
| `social_support` | Perceived Social Support Scale score | Cyberbullying Survey 2021 |
| `harassment_severity` | Continuous severity score of online harassment | Cyberbullying Survey 2021 |
| `harassment_exposure` | Binary indicator of any harassment exposure | Derived from `harassment_severity` |
| `depression` | CES-D total score | Cyberbullying Survey 2021 |
| `anxiety` | GAD-7 total score | Cyberbullying Survey 2021 |
| `ptsd` | PCL-5 total score | Cyberbullying Survey 2021 |
| `age` | Age in years | Cyberbullying Survey 2021 |
| `gender` | Gender identity | Cyberbullying Survey 2021 |
| `education` | Education level | Cyberbullying Survey 2021 |
| `income` | Income bracket | Cyberbullying Survey 2021 |
| `platform` | Primary platform of harassment (if available) | Cyberbullying Survey 2021 |

## 5. Methodological Notes

### The Revised Approach (Single-Dataset)
The initial plan to create a "Synthetic Cohort" by matching the Cyberbullying Survey 2021 with the GSS 2022 was identified as methodologically invalid. Matching across distinct surveys with different sampling frames and question phrasings introduces unmeasured confounding that would invalidate the interaction term (the buffering effect).

The project now strictly uses the **Cyberbullying Survey 2021** alone. This ensures that the interaction between social support and harassment is estimated within a single, consistent population, providing a valid test of the psychological buffering hypothesis without confounding by dataset source.

### Platform Stratification Logic
To avoid selection bias, the analysis includes **all** platforms present in the dataset that meet the minimum sample size requirement (N >= 30). Arbitrary truncation to the "top three" platforms is explicitly prohibited to ensure the robustness of the findings across the full spectrum of user experiences.