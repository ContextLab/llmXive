# Data Model: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

## Overview

This document defines the data structures, schemas, and transformations used in the pipeline. All data is stored in local files (`data/`) and loaded into Pandas DataFrames or NumPy arrays during processing.

## Core Entities

### 1. Subject
Represents a single participant.
- **Attributes**: `subject_id` (str), `diagnosis` (str: "ADHD" or "Control"), `adhd_rs_total` (float), `adhd_rs_inattention` (float), `adhd_rs_hyperactivity` (float), `fd_mean` (float), `volumes_post_scrub` (int), `scrub_fraction` (float).
- **Constraints**: `volumes_post_scrub` >= 100. `adhd_rs_total` must be present for regression analysis.

### 2. Parcel
Represents a region of interest in the Schaefer 200 atlas.
- **Attributes**: `parcel_index` (int: 0-199), `parcel_name` (str).
- **Derived**: `entropy_value` (float).

### 3. FeatureMatrix
The primary input for modeling.
- **Shape**: (N_subjects, 200 + 50 + 1).
- **Columns**: `subject_id`, `parcel_01`...`parcel_200` (Entropy), `pca_comp_01`...`pca_comp_50` (Connectivity), `scrub_fraction` (Covariate).
- **Handling**: Missing values (zero variance parcels) are imputed with the median entropy of that parcel across the cohort (FR-009).

### 4. ConnectivityMatrix (Baseline)
- **Shape**: (N_subjects, 200, 200).
- **Processing**: Flattened to [deferred] features, then reduced to **50 PCA components** (retaining >95% variance) to ensure non-tautological comparison.
- **Storage**: `connectivity_pca_features.csv` (N_subjects, 50).

### 5. ModelOutput
- **Attributes**: `model_type` (str), `metric` (str: "r", "AUC"), `mean_score` (float), `std_score` (float), `p_value` (float), `ci_lower` (float), `ci_upper` (float), `p_value_nested_test` (float).

## Data Flow

1.  **Raw Data**: NIfTI files (4D) + Phenotypic CSV (from OpenNeuro ds000305).
2.  **Preprocessed**: Scrubbed time series -> **Truncate to N=120** -> SD Calculation -> Entropy Calculation.
3.  **Features**: Entropy matrix (N x 200) + Connectivity PCA matrix (N x 50) + `scrub_fraction` covariate.
4.  **Models**: Cross-validated metrics + Permutation p-values + Nested Model Test p-values.
5.  **Reports**: JSON/CSV summaries + Plots (PNG) + `motion_confound_report.json`.

## Storage Strategy

- **Raw**: `data/raw/*.nii.gz`, `data/raw/phenotype.csv`
- **Processed**: `data/processed/subject_entropy_features.csv`, `data/processed/connectivity_pca.csv`
- **Derived**: `data/derived/model_metrics.json`, `data/derived/permutation_results.csv`, `data/derived/motion_confound_report.json`, `data/derived/significant_parcels.csv`
- **Logs**: `exclusions.log` (FR-007)

## Assumptions

- All NIfTI files are in MNI space and aligned with the Schaefer 200 atlas.
- Phenotypic data is clean and matches subject IDs in the imaging data.
- No PII is stored in the processed data files.