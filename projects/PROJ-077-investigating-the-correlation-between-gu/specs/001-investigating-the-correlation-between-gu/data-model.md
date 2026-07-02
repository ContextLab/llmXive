# Data Model: Investigating the Correlation Between Gut Microbiome Diversity and Cognitive Performance

## Overview

This document defines the data structures, schemas, and transformations used in the analysis pipeline. The data model is designed to be strictly validated against the `contracts/` schemas to ensure data hygiene and reproducibility.

## Entity Definitions

### Participant
An individual in the UK Biobank cohort.
- **Attributes**: `participant_id`, `age`, `sex`, `bmi`, `fluid_intelligence_score`.
- **Constraints**: `participant_id` is unique. `age` > 0. `sex` in {0, 1, 2} (as per UKB coding) or {M, F}.

### MicrobiomeSample
A single microbiome sequencing sample associated with a participant.
- **Attributes**: `participant_id`, `otu_counts` (dict or sparse matrix), `total_reads`.
- **Derived**: `shannon_index` (calculated on **raw** counts), `clr_transformed_counts` (for Secondary Path only).

### CovariateSet
Control variables for regression.
- **Attributes**: `age`, `sex`, `bmi`, `dietary_quality_score` (DQS).
- **Imputation**: 
  - Continuous (`age`, `bmi`, `DQS`): Replaced with **Median**.
  - Categorical (`sex`): Replaced with **Mode**.

### AnalysisResult
Output of the statistical pipeline.
- **Attributes**: `test_type` (correlation/regression), `coefficient`, `std_err`, `p_value`, `q_value`, `n_samples`.

## Data Flow

1.  **Raw Input**:
    - `data/raw/microbiome_counts.csv`: Participant ID x OTU counts.
    - `data/raw/cognitive_data.csv`: Participant ID x Fluid Intelligence.
    - `data/raw/demographics.csv`: Participant ID x Age, Sex, BMI.
    - `data/raw/dietary_data.csv`: (Optional) Raw dietary items for DQS calculation.
2.  **Preprocessing**:
    - Merge on `participant_id`.
    - Filter: Keep only rows where `shannon_index` and `fluid_intelligence_score` are non-null.
    - Impute: **Median** for `age`, `bmi`, `DQS`; **Mode** for `sex`.
    - Transform: 
      - **Primary Path**: No transform for Shannon.
      - **Secondary Path**: CLR on OTU counts.
3.  **Derived Output**:
    - `data/processed/cleaned_data.csv`: Final analysis table.
    - `data/processed/results_correlation.csv`: Spearman correlation stats (Primary Path).
    - `data/processed/results_regression.csv`: Lasso regression stats (Secondary Path).
    - `data/processed/plots/`: PNG files.

## Schema Definitions

See `contracts/` for the formal YAML schemas.

### Input Schema Requirements
- Must contain `participant_id` (string/int).
- Must contain `fluid_intelligence_score` (float/int).
- Must contain at least one OTU column (e.g., `OTU_001`).
- Must contain `age`, `sex`, `bmi` (float/int) OR allow imputation if missing.

### Output Schema Requirements
- `results_correlation.csv`: `metric`, `coefficient`, `p_value`, `q_value`.
- `results_regression.csv`: `predictor`, `coefficient`, `std_err`, `p_value`, `q_value`.

## Assumptions & Limitations

- **Data Format**: Input files are assumed to be CSV with headers.
- **Missingness**: If a participant lacks microbiome data but has cognitive data, they are excluded (US-1, US-2).
- **DQS**: If raw dietary data is missing, DQS cannot be calculated (FR-008). The system will either use a placeholder or flag the column as missing, depending on configuration.
- **Methodological Correction**: The plan explicitly rejects the Spec's requirement for "CLR-transformed alpha diversity" and "median imputation for sex." The data model reflects the **correct** methodology (Raw Shannon, Mode for Sex).