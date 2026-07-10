# Data Model: The Impact of Perceived Social Support on Resilience to Online Harassment

## 1. Overview
This document defines the data structures used throughout the analysis pipeline. The data flow follows: `Raw Input` → `Analysis Cohort` → `Regression Results`.

**Note**: The "Synthetic Cohort" concept has been replaced with "Analysis Cohort" to reflect the single-dataset methodology.

## 2. Entity Definitions

### 2.1 Raw Input Entity
This entity represents the raw data as ingested from the source file (Cyberbullying Survey).
*   **Note**: The actual raw data file is not included in this repository; the schema below describes the *expected* structure.

### 2.2 Analysis Cohort (Primary Analysis Unit)
The central entity for analysis. Derived from a single source dataset.
*   **Key**: `respondent_id` (String/Int)
*   **Attributes**:
    *   `age`: Integer
    *   `gender`: String (Categorical)
    *   `education`: Integer (Years or Level)
    *   `income`: Integer (Bracket ID)
    *   `social_support_score`: Float (Standardized score)
    *   `harassment_exposure`: Float (Binary 0/1 or Continuous Severity)
    *   `depression_score`: Float (CES-D total)
    *   `anxiety_score`: Float (GAD-7 total)
    *   `ptsd_score`: Float (PCL-5 total, or `null` if unavailable)
    *   `platform_type`: String (Categorical, or `null` if not applicable)

### 2.3 Regression Results
Output of the statistical modeling phase.
*   **Key**: `model_id` (String: e.g., `depression_binary`, `anxiety_continuous`)
*   **Attributes**:
    *   `outcome_variable`: String
    *   `exposure_type`: Enum (`binary`, `continuous`)
    *   `interaction_coefficient`: Float ($\beta_3$)
    *   `interaction_se`: Float (Standard Error)
    *   `interaction_pvalue`: Float
    *   `interaction_ci_lower`: Float ([deferred] BCa)
    *   `interaction_ci_upper`: Float ([deferred] BCa)
    *   `fdr_adjusted_pvalue`: Float

## 3. Data Lineage
1.  **Ingestion**: Raw CSV → `data/harmonized/cyber_clean.csv`
2.  **Scoring**: `data/harmonized/` → `data/processed/scores.csv` (Adds mental health totals)
3.  **Cohort Construction**: `data/processed/scores.csv` → `data/analysis/analysis_cohort.csv`
4.  **Analysis**: `data/analysis/analysis_cohort.csv` → `results/regression_results.csv`

## 4. Data Quality Rules
*   **Missing Values**: Critical predictors (`social_support_score`, `harassment_exposure`, `depression_score`) must not be `NaN`. Rows with missing values in these fields are dropped (listwise deletion).
*   **Range Checks**:
    *   `depression_score`: Must be within valid range for CES-D (e.g., 0-60).
    *   `anxiety_score`: Must be within valid range for GAD-7 (e.g., 0-21).
*   **Balance Check**: Not applicable (Single dataset). Instead, **VIF Check**: Variance Inflation Factor for predictors must be < 5 to ensure stable interaction estimates.