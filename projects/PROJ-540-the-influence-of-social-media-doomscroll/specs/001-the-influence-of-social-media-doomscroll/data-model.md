# Data Model: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Overview

This document defines the data schemas and transformation logic required to ingest raw survey data and produce the analysis-ready dataset for the regression model.

## Entities

### 1. RawSurveyResponse
Represents the raw data row as downloaded from the source.
- **Source**: Parquet/CSV from verified URL.
- **Validation**: Must contain at least one column mapping to news frequency and one to anxiety.

### 2. CleanedSurveyResponse
The analysis-ready record after missing data handling and type casting.
- **Filtering**: Listwise deletion applied if `news_exposure_freq` or `anxiety_score` is null.
- **Threshold**: If resulting $N < 30$, the pipeline halts.

### 3. RegressionOutput
The structured output of the statistical model.
- **Fields**: Coefficients, P-values, R-squared, Diagnostic Metrics.

## Variable Mapping

| Analytical Variable | Raw Column Name (Expected) | Type | Description |
| :--- | :--- | :--- | :--- |
| `news_exposure_freq` | `news_freq` (or similar) | Numeric (1-5) | Frequency of negative news consumption. |
| `anxiety_score` | `anxiety_total` (or similar) | Numeric | Outcome anxiety score. |
| `baseline_anxiety` | `trait_anxiety` (or similar) | Numeric | Baseline/trait anxiety measure. |
| `age` | `age` | Integer | Participant age. |
| `gender` | `gender` | Categorical | Participant gender. |
| `social_media_engagement` | `sm_engagement` | Numeric | Total social media usage time/frequency. |

## Transformation Logic

1.  **Ingestion**: Load raw file.
2.  **Mapping**: Rename columns to analytical variable names. If a column is missing, log error and halt.
3.  **Cleaning**:
    -   Drop rows where `news_exposure_freq` OR `anxiety_score` is null.
    -   Log count of dropped rows.
    -   Check $N$. If $N < 30$, raise `PowerLimitationError`.
4.  **Type Casting**: Ensure numeric columns are float/int, categorical are string/category.
5.  **Output**: Save `data/processed/analysis_data.csv`.

## Output Schema

The final output of the `model.py` step will be a JSON object containing:
- `model_results`: Dictionary of coefficients.
- `diagnostics`: Dictionary of assumption checks.
- `metadata`: N, R-squared, Proxy flags.
