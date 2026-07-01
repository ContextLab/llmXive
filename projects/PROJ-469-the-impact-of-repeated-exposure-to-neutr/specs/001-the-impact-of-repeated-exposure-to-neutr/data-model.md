# Data Model: 001-political-news-implicit-bias

## Entity-Relationship Overview

The data model consists of raw survey responses, derived variables, and model outputs.

### Raw Data (`data/raw/`)
- **Source**: Project Implicit Political IAT CSV.
- **Columns**:
  - `participant_id`: Unique identifier.
  - `IAT_D_score`: Implicit bias score (D-score).
  - `political_ideology`: Continuous scale (e.g., 1-7).
  - `news_exposure_freq`: Self-reported frequency (e.g., 1-5).
  - `age`: Numeric.
  - `gender`: Categorical.
  - `education`: Categorical.
  - `...`: Other demographic variables.

### Derived Data (`data/processed/`)
- **Imputed Data**: Result of MICE (5 datasets).
- **Standardized Variables**:
  - `news_exposure_z`: Z-scored `news_exposure_freq`.
  - `ideology_binary`: Binary (0/1) from median split (for sensitivity only).
- **Model Inputs**: Cleaned dataframe with no missing values in key columns.

### Model Outputs (`results/`)
- **Coefficients**: Beta estimates, SE, p-values, CI.
- **Diagnostics**: Imputation retention rate, bootstrap convergence rate.
- **Plots**: Interaction plots, residual plots.

## Data Dictionary

| Variable | Type | Description | Source |
|----------|------|-------------|--------|
| `IAT_D_score` | Float | Implicit Association Test D-score | Raw |
| `political_ideology` | Float | Self-reported political ideology (continuous) | Raw |
| `news_exposure_freq` | Float | Frequency of political news exposure | Raw |
| `news_exposure_z` | Float | Standardized `news_exposure_freq` | Derived |
| `age` | Int | Participant age | Raw |
| `gender` | String | Participant gender | Raw |
| `education` | String | Education level | Raw |
| `interaction_term` | Float | `news_exposure_z` × `political_ideology` | Derived |

## Data Flow

1. **Load**: Read CSV, map columns via codebook.
2. **Validate**: Check for required columns (FR-001).
3. **Impute**: Apply MICE (FR-008).
4. **Transform**: Z-score news exposure, create interaction term.
5. **Model**: Fit linear regression.
6. **Robustness**: Bootstrap, alpha sweep, covariate check.
7. **Report**: Generate PDF/CSV.
