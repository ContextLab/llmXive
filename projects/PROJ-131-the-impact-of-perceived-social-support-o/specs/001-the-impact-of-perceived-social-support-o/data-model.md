# Data Model: The Impact of Perceived Social Support on Resilience to Online Harassment

## Overview
This document defines the data schema, transformations, and validation rules for the project. The data model ensures that all inputs, intermediate states, and outputs are structured, validated, and reproducible.

## Input Schema
The raw dataset (Cyberbullying Survey 2021) must conform to the following schema. Missing columns will cause a pipeline halt.

| Column Name | Type | Description | Required |
|:---|:---|:---|:---|
| `respondent_id` | String | Unique identifier | Yes |
| `social_support` | Float | Perceived social support score | Yes |
| `harassment_severity` | Float | Continuous harassment severity score | Yes |
| `depression` | Float | CES-D total score | Yes |
| `anxiety` | Float | GAD-7 total score | Yes |
| `ptsd` | Float | PCL-5 total score | No (Optional) |
| `platform` | String | Social media platform | Yes |
| `age` | Integer | Age in years | Yes |
| `gender` | String | Gender identity | Yes |
| `education` | String | Education level | Yes |
| `income` | Float | Income level | Yes |

## Transformation Pipeline

### Phase 1: Ingestion & Validation
-   **Action**: Download raw data.
-   **Validation**: Check for presence of all required columns.
-   **Output**: `data/raw/cyberbullying_survey_2021_raw.csv` (or parquet).
-   **Checksum**: MD5/SHA256 recorded in `state/...yaml`.

### Phase 2: Preprocessing
-   **Action**: Handle missing values.
    -   Predictors (`social_support`, `age`, `education`, `income`, etc.): MICE Imputation.
    -   Outcomes (`depression`, `anxiety`, `ptsd`): Listwise deletion.
    -   **Assumption**: Outcomes are MCAR.
-   **Action**: Derive `harassment_exposure` (Binary: `harassment_severity > 0`).
-   **Action**: Encode categorical variables (`platform`, `gender`, `education`) using One-Hot Encoding (or Target Encoding if high cardinality).
-   **Output**: `data/processed/cleaned_dataset.csv`.

### Phase 3: Feature Engineering
-   **Action**: Create interaction term: `harassment_severity * social_support`.
    -   **Critical Step**: **Mean-center** `harassment_severity` and `social_support` before multiplication to reduce multicollinearity.
-   **Action**: Scale predictors (optional, for interpretation).
-   **Output**: `data/processed/features_matrix.csv`.

### Phase 4: Modeling & Output
-   **Action**: Fit OLS models for each outcome (Depression, Anxiety, PTSD).
-   **Action**: Run BCa Bootstrap (1,000 resamples).
    -   **Strategy**: Use cluster-robust bootstrap by `platform` if N per platform >= 30.
-   **Action**: Apply FDR correction.
-   **Output**: `data/processed/model_results.json`.
-   **Output**: `data/processed/figures/` (Interaction plots, CI bars).

## Data Contracts

### Raw Data Contract
-   **Format**: CSV or Parquet.
-   **Encoding**: UTF-8.
-   **Missingness**: Represented as `NaN` or empty string.

### Processed Data Contract
-   **Format**: CSV.
-   **Columns**: All original columns + `harassment_exposure` + interaction terms + imputed values.
-   **Constraints**: No missing values in predictors.

### Output Contract
-   **Format**: JSON.
-   **Structure**:
    -   `model_name`: String
    -   `outcome`: String
    -   `interaction_pvalue`: Float
    -   `interaction_ci_lower`: Float
    -   `interaction_ci_upper`: Float
    -   `fdr_adjusted_pvalue`: Float
    -   `vif_scores`: Dict

## Scoring Algorithm
To ensure construct validity, psychological scales will be computed as follows:
-   **CES-D**: Sum of item scores (0-3). Reverse-code specific items as per standard manual.
-   **GAD-7**: Sum of item scores (0-3). No reverse coding required.
-   **PCL-5**: Sum of item scores (0-4). No reverse coding required.
-   **Social Support**: Sum of item scores (Likert scale). Reverse-code as per instrument manual.
-   **Verification**: The `code/config/scales.yaml` file will explicitly list the column names and reverse-coding logic for each scale.

## Missing Data Mechanism
-   **Predictors**: MICE assumes MAR.
-   **Outcomes**: Listwise deletion assumes MCAR.
-   **Bias Risk**: If outcomes are MNAR (e.g., severe depression leads to non-response), results may be biased. This limitation will be discussed in the final report.
