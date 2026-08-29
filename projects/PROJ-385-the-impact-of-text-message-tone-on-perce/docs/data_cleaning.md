# Data Cleaning Methodology

This document outlines the data cleaning procedures implemented in the research pipeline for the study on "The Impact of Text Message Tone on Perceived Emotional Support."

## Overview

Data cleaning is a critical step to ensure the validity and reliability of statistical analyses. The pipeline implements several automated checks to identify and handle data quality issues, including missing values, participant inattention, and data entry errors.

## Listwise Deletion

### Definition

Listwise deletion (also known as complete case analysis) is a method for handling missing data where any participant (row) that has missing values for *any* of the variables required for the primary analysis is excluded from the dataset entirely.

### Implementation in this Pipeline

The listwise deletion process is implemented in `code/03_clean_data.py` and is triggered as part of the data cleaning workflow. The process follows these steps:

1. **Detection**: The script loads the anonymized ratings data (`data/processed/anonymised_ratings.csv`) and checks each participant record for missing values in critical columns (e.g., `rating`, `stimulus_id`, `context`).
2. **Flagging**: Participants with any missing data are flagged. Additionally, participants identified as straight-liners (zero variance in ratings across all stimuli) by the `detect_straight_lining` function are also marked for exclusion.
3. **Exclusion**: All flagged participants are removed from the dataset.
4. **Logging**: A detailed log of excluded participants is saved to `data/processed/excluded_participants.csv`, and a cleaning log is generated for audit purposes.
5. **Output**: The cleaned dataset is written to `data/processed/cleaned_ratings.csv`.

### When to Use Listwise Deletion

Listwise deletion is appropriate in the following scenarios:

- **Missing Completely at Random (MCAR)**: When the probability of missing data is unrelated to any observed or unobserved variables. In this case, listwise deletion yields unbiased estimates, though it reduces statistical power due to sample size reduction.
- **Small Amounts of Missing Data**: When the proportion of missing data is low (typically < 5% of the total sample), the loss of power is minimal, and the simplicity of listwise deletion outweighs the benefits of more complex imputation methods.
- **Exploratory Analysis**: When conducting initial data exploration or when the primary goal is to establish a baseline model with the highest confidence in the observed data points.
- **Strict Validity Requirements**: When the analysis requires that every data point in every variable be verified and no assumptions about missing data mechanisms can be made.

### When NOT to Use Listwise Deletion

- **Missing at Random (MAR) or Missing Not at Random (MNAR)**: If missingness is related to the data itself (e.g., participants with lower ratings are less likely to complete the survey), listwise deletion can introduce significant bias. In these cases, multiple imputation or maximum likelihood estimation methods are preferred.
- **Large Amounts of Missing Data**: If a substantial portion of the sample has missing data, listwise deletion can drastically reduce statistical power and may lead to a non-representative sample.
- **Complex Survey Designs**: When the data structure involves complex weighting or clustering that could be distorted by removing incomplete cases.

### Alternatives Considered

While listwise deletion is the default method implemented in this pipeline for the primary analysis (T016b), the following alternatives are noted for potential future robustness checks:

- **Multiple Imputation (MI)**: Creates multiple complete datasets by imputing missing values based on observed data relationships. This preserves sample size and reduces bias under MAR assumptions.
- **Maximum Likelihood (ML)**: Uses all available data to estimate parameters, handling missing data implicitly during model fitting.
- **Mean/Median Imputation**: Simple replacement of missing values with central tendency measures. Generally discouraged as it reduces variance and can bias relationships, but sometimes used for sensitivity analysis.

### Verification

The effectiveness of the listwise deletion process is verified by:
- Comparing the number of participants before and after cleaning.
- Ensuring the `excluded_participants.csv` file contains valid reasons for exclusion.
- Validating the `cleaned_ratings.csv` against the `rating.schema.yaml` to ensure data integrity.
- Confirming that the pre-analysis guard (`code/99_preanalysis_guard.py`) validates the cleaned data before any statistical modeling proceeds.

## References

- Little, R. J. A., & Rubin, D. B. (2019). *Statistical Analysis with Missing Data* (3rd ed.). Wiley.
- Allison, P. D. (2001). *Missing Data*. Sage Publications.
- Implementation Plan: Phase 2, Step 2.3 (Data Cleaning & Straight-lining Detection).