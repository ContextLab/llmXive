# Spec: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging

## Overview

This project investigates the statistical relationship between gut microbiome alpha/beta diversity metrics and cognitive flexibility scores in an aging population. The primary goal is to validate the research pipeline using a Null Hypothesis dataset (synthetic data with known independence) before attempting ingestion of real-world data (e.g., UK Biobank) in future phases.

## Research Question

Does gut microbiome diversity (Shannon, Simpson, Chao1) correlate with cognitive flexibility scores in individuals aged 65+, after controlling for age, sex, BMI, dietary fiber intake, and antibiotic use?

## Functional Requirements

### FR-001: Ingest Synthetic Data for Pipeline Validation
**Amended**: The system shall ingest a synthetic dataset generated to simulate a Null Hypothesis scenario (no correlation between microbiome diversity and cognitive scores).
- **Source**: `data/raw/synthetic_data.csv` (generated via `src/data/synthetic_gen.py`).
- **Constraint**: Real UK Biobank data is currently unavailable. This phase is strictly a "Pipeline Validation Study".
- **Purpose**: To verify that the analysis pipeline correctly returns non-significant results (p > 0.05) when no true effect exists, ensuring the pipeline does not produce false positives.

### FR-002: Covariate Inclusion
The analysis MUST control for the following specific covariates as defined in the data schema:
- `age` (continuous)
- `sex` (categorical: 'M', 'F')
- `bmi` (continuous)
- `dietary_fiber` (continuous, g/day)
- `antibiotic_use` (boolean)
- **Exclusion**: Socioeconomic status (SES) and specific dietary patterns (e.g., Mediterranean score) are explicitly excluded from the current model scope to prevent scope creep and data unavailability issues.

### FR-003: Cohort Filtering
- Filter participants to include ONLY those with `age >= 65`.
- Perform listwise deletion for any rows missing required core metrics (`cognitive_flexibility_score`, `shannon_diversity`) or required covariates.

### FR-004: Statistical Analysis
- Calculate Pearson or Spearman correlation based on normality checks (Shapiro-Wilk).
- Apply Benjamini-Hochberg False Discovery Rate (FDR) correction to all p-values.
- Perform Linear Regression: `Cognitive_Flexibility ~ Diversity + Covariates`.

### FR-005: Non-Normality Handling
- If the cognitive flexibility score distribution is heavily skewed (skewness > 1.0 or Shapiro-Wilk p < 0.05), the system shall log the deviation and switch to non-parametric permutation tests for beta diversity analysis (PERMANOVA) rather than binning.

## Data Model

The system operates on a unified cohort dataframe with the following schema (see `contracts/dataset.schema.yaml`):
- `participant_id`: Unique string identifier.
- `age`: Integer.
- `sex`: Enum ['M', 'F'].
- `bmi`: Float.
- `cognitive_flexibility_score`: Float.
- `shannon_diversity`: Float.
- `simpson_diversity`: Float.
- `chao1`: Float.
- `dietary_fiber`: Float.
- `antibiotic_use`: Boolean.

## Assumptions

1. **Synthetic Data Validity**: The synthetic data generator (`src/data/synthetic_gen.py`) correctly implements the Null Hypothesis by generating independent variables for microbiome diversity and cognitive scores.
2. **Data Availability**: No real UK Biobank or similar large-scale cohort data is available for this specific validation phase.
3. **Compute Constraints**: All analysis must run on CPU with < 7GB RAM.
4. **Covariate Availability**: The specified covariates (age, sex, BMI, fiber, antibiotics) are present in the synthetic dataset.

## Constraints

- **No GPU**: No deep learning or GPU-accelerated libraries.
- **No Fabrication**: The pipeline must not fabricate results; if the Null Hypothesis is true, p-values must be > 0.05.
- **Scope Control**: The regression model MUST NOT include unapproved covariates (e.g., SES, dietary_pattern).

## Deliverables

- `data/raw/synthetic_data.csv`: The generated null-hypothesis dataset.
- `data/processed/filtered_cohort.csv`: The cleaned, age-filtered dataset.
- `data/results/correlation_results.json`: Statistical results including coefficients, p-values, and adjusted p-values.
- `data/results/alpha_diversity_boxplot.png`: Visualization of diversity by cognitive quartile.