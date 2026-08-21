# Analysis Methodology: Gut Microbiome and Circadian Rhythm

## 1. Introduction

This document details the statistical methods used to investigate the associational links between gut microbiome composition and circadian rhythm disruption. All analyses are framed as **associational**; no causal inferences are drawn.

## 2. Data Preprocessing

### 2.1. Cohort Definition
- **Sources**: American Gut Project (AGP) 16S rRNA data and Open Humans sleep metadata.
- **Merging**: Join on `Participant ID`. If no matches are found, the pipeline logs a warning and proceeds with available data (N=0 check).
- **Filtering**: Exclude participants with missing sleep or microbiome data.
- **Outlier Capping**: Sleep duration <2h or >16h is capped at the 1st and 99th percentiles respectively.
- **Imputation**: Missing covariates (BMI, age, antibiotic history) are imputed using median (continuous) or mode (categorical).

### 2.2. Diversity Metrics
- **Alpha Diversity**: Shannon and Simpson indices calculated from the BIOM table.
- **Beta Diversity**: Bray-Curtis dissimilarity matrix calculated for ordination and PERMANOVA.

## 3. Statistical Analysis

### 3.1. Correlation Analysis
- **Method**: Spearman rank correlation (primary) and Pearson correlation (secondary) between diversity metrics and sleep variables (duration, quality, chronotype).
- **Correction**: Benjamini-Hochberg False Discovery Rate (FDR) correction applied to all p-values to control for multiple testing.

### 3.2. Distance-based Redundancy Analysis (dbRDA)
- **Purpose**: Screen for non-linear relationships between sleep variables (continuous) and beta diversity.
- **Implementation**: Uses the `skbio` library for distance matrix handling.

### 3.3. Generalized Linear Models (GLM)
- **Purpose**: Adjust for confounders (age, BMI, diet type, medication, antibiotic history).
- **Limitation**: The "diet timing" variable required by FR-004 is unavailable in AGP. "Diet type" is used as a substitute per the project plan. This deviation is explicitly documented in the final report.

### 3.4. PERMANOVA
- **Purpose**: Test for differences in beta diversity across categorical sleep groups.
- **Constraint**: Used *only* for categorical variables. Continuous variables are analyzed via dbRDA.

## 4. Robustness Validation

### 4.1. Bootstrap Resampling
- **Iterations**: 1000 bootstrap resamples.
- **Output**: 95% Confidence Intervals (CIs) for the top 5 correlations.
- **Negative Results**: CIs that include zero are explicitly reported as valid negative results, correcting the flaw in SC-002.
- **Sample Size Constraint**: If N < 40, resampling is skipped, and the status is recorded in `validation_status.json`.

### 4.2. Sensitivity Analysis
- **Thresholds**: Significance thresholds swept over [0.01, 0.05, 0.1].
- **Output**: `sensitivity_report.csv` showing the variation in the count of significant taxa.

## 5. Reporting Standards

- **Language**: All findings are described as "associational," "linked," or "correlated." Terms like "cause," "effect," or "mechanism" are avoided.
- **Transparency**: All limitations (e.g., missing diet timing data) are explicitly stated in the report.
- **Reproducibility**: Random seeds are managed via `code/utils/seeding.py` to ensure reproducible results.

## 6. Compliance

- **FR-004**: Diet timing data unavailability acknowledged; diet type used as proxy.
- **FR-008**: All findings framed as associational.
- **SC-002**: Bootstrap CIs including zero treated as valid negative results.
- **SC-003**: Sensitivity thresholds strictly [0.01, 0.05, 0.1].
