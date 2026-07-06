# Data Model Specification

## Overview
This document defines the data structures, schemas, and relationships used throughout the pipeline, including updates for methodological corrections.

## Entities

### 1. RawDataset
Metadata for downloaded datasets.
- `dataset_id`: str (e.g., "ds000001")
- `source`: str (e.g., "openneuro", "huggingface")
- `description`: dict (metadata from dataset)
- `variables`: list (e.g., ["stimulus_type", "response_correctness"])

### 2. PreprocessedData
Cleaned and epoched data.
- `subject_id`: str
- `epochs`: array (time series data)
- `events`: array (stimulus markers)
- `bad_channels`: list
- `ica_components`: array

### 3. ExcludedSubjects
List of subjects excluded due to low power or data quality.
- `subject_id`: str
- `reason`: str ("underpowered", "excessive_artifact", "zero_accuracy")
- `trial_count`: int

### 4. AlignedData (Updated for Lagged Alignment)
Merged dataset containing neural and behavioral metrics.
- `subject_id`: str
- `block_id`: int
- `mmn_amplitude`: float (Mean difference wave 150-250ms)
- `accuracy`: float (Behavioral accuracy for the block)
- `analysis_mode`: str ("error_signal" or "stimulus_driven")
- `source_window_start_trial`: int (Start of the 50-trial window used for MMN calculation)
- `learning_phase`: str ("early", "late")

### 5. ModelOutput
Results from the Gaussian LME analysis.
- `model_formula`: str
- `coefficients`: dict (e.g., {"Accuracy": 0.05, "Intercept": 0.02})
- `p_values`: dict (FDR corrected)
- `permutation_p_value`: float
- `robustness_metrics`: dict (sensitivity analysis results)

## Schema Files
- `contracts/aligned_data.schema.yaml`: Defines structure for `AlignedData`.
- `contracts/model_output.schema.yaml`: Defines structure for `ModelOutput`.

## Methodological Corrections
- **Lagged Alignment**: The `AlignedData` entity now includes `source_window_start_trial` to track the 50-trial window (t-50 to t-10) used to calculate the MMN that predicts the accuracy in the subsequent block (t to t+n).
- **Gaussian LME**: The `ModelOutput` entity is structured to support the Gaussian LME model (`MMN ~ Accuracy + (1|Subject)`).
- **Exclusion**: The `ExcludedSubjects` entity is explicitly used to filter subjects with <20 subjects in the cohort or <10 valid trials per block before GLMM fitting.
