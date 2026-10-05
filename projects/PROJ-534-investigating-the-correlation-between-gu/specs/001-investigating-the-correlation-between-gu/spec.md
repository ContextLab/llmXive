# Project Specification: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility in Aging

## Overview

This project investigates the statistical relationship between gut microbiome alpha/beta diversity metrics and cognitive flexibility scores in an aging population (age ≥ 65). The study is designed as a **Pipeline Validation Study** using a **Null Hypothesis dataset** to verify the robustness of the analytical pipeline before applying it to real-world data.

## Research Question

How do alpha diversity (Shannon, Simpson, Chao1) and beta diversity (Bray-Curtis, UniFrac) metrics correlate with cognitive flexibility scores in individuals aged 65 and older, after controlling for key covariates?

## Methodology

The study employs a cross-sectional design analyzing synthetic data generated to satisfy a Null Hypothesis (no true correlation between microbiome diversity and cognitive flexibility). This approach allows for:
1. Validation of the entire analytical pipeline.
2. Verification that the pipeline correctly identifies non-significant results when no signal exists.
3. Calibration of statistical power and sensitivity analysis tools.

## Functional Requirements

### FR-001: Data Ingestion (AMENDED)
**Original Requirement**: Ingest UK Biobank 16S and cognitive data.
**Amended Requirement**: Ingest **Synthetic Data** for Pipeline Validation.
**Rationale**: Real UK Biobank data is currently unavailable for this validation phase. The project scope is amended to focus on validating the pipeline logic using a controlled Null Hypothesis dataset. Real data ingestion is deferred until the pipeline is proven robust.

**Implementation Details**:
- Ingest synthetic participant demographics, lifestyle factors, microbiome data, and cognitive scores.
- Data must be generated with a fixed random seed (42) to ensure reproducibility.
- Synthetic data must explicitly model statistical independence between microbiome diversity and cognitive flexibility scores to satisfy the Null Hypothesis.

### FR-002: Covariate Control
The analysis must control for the following specific covariates to rule out confounding:
- Age (continuous)
- Sex (categorical)
- BMI (continuous)
- Dietary Fiber Intake (continuous)
- Antibiotic Use (binary)

**Exclusion**: Socioeconomic Status (SES) and broad Dietary Patterns are explicitly excluded from the regression models to maintain scope control, as per project constraints.

### FR-003: Statistical Analysis
- Calculate Alpha Diversity: Shannon, Simpson, Chao1.
- Calculate Beta Diversity: Bray-Curtis, Weighted UniFrac.
- Perform Correlation Analysis: Pearson or Spearman (auto-switch based on normality tests).
- Perform Linear Regression: Cognitive Flexibility ~ Diversity + Covariates.
- Apply Benjamini-Hochberg correction for multiple comparisons (FDR < 0.05).

### FR-004: Null Hypothesis Validation
The pipeline must demonstrate that when applied to the Null Hypothesis dataset, the resulting p-values for the correlation between diversity and cognitive scores are > 0.05 (non-significant), confirming the pipeline does not produce false positives.

## Assumptions

1. **Data Availability**: Real UK Biobank data is unavailable for the current phase. The project relies on a validated synthetic data generator.
2. **Population**: The synthetic population is modeled to reflect the demographic distribution of individuals aged 65+ in developed nations.
3. **Independence**: In the synthetic Null Hypothesis dataset, microbiome diversity and cognitive flexibility are generated as statistically independent variables.
4. **Computational Resources**: The pipeline is designed to run on CPU-only environments with < 7GB RAM.

## Data Model

### Participant Entity
- `participant_id` (str, PK)
- `age` (int, >= 65)
- `sex` (enum: 'M', 'F')
- `bmi` (float)
- `cognitive_flexibility_score` (float)
- `shannon_diversity` (float)
- `simpson_diversity` (float)
- `chao1` (float)
- `dietary_fiber` (float)
- `antibiotic_use` (bool)

### Analysis Result Entity
- `test_type` (str)
- `metric_name` (str)
- `correlation_coefficient` (float)
- `p_value` (float)
- `adjusted_p_value` (float)
- `confidence_interval` (array[float, float])
- `r_squared` (float)
- `r_squared_baseline` (float)

## Deliverables

1. **Synthetic Dataset**: `data/raw/synthetic_data.csv`
2. **Filtered Cohort**: `data/processed/filtered_cohort.csv`
3. **Diversity Metrics**: `data/processed/diversity_metrics.csv`
4. **Correlation Results**: `data/results/correlation_results.json`
5. **Null Hypothesis Validation Report**: Confirms p > 0.05 for primary correlations.
6. **Power Estimation Report**: `data/results/power_validation_report.json`
7. **Sensitivity Analysis Report**: `data/results/confounding_sensitivity.json`

## Constraints

- **No GPU**: All computations must be CPU-based.
- **No 8-bit Quantization**: Standard floating-point precision required.
- **No Large Models**: Statistical methods only (no deep learning).
- **Reproducibility**: All random seeds must be fixed and documented.
- **Data Integrity**: Synthetic data must be generated programmatically, not manually created.