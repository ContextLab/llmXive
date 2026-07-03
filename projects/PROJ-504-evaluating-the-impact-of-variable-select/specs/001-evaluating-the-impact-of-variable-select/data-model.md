# Data Model: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Overview

This document defines the data structures used to represent the simulated datasets, selection results, and aggregated recovery metrics. The model ensures traceability from raw simulation to final statistical comparison, with a focus on avoiding pseudoreplication and selection bias.

## Key Entities

### 1. SimulatedDataset
Represents a single instance of a simulation run. Contains the real predictor matrix, the synthetic outcome, and metadata defining the ground truth.

**Fields**:
*   `dataset_id`: (int) OpenML dataset ID.
*   `dataset_name`: (str) Name of the OpenML dataset.
*   `simulation_id`: (int) Unique ID for this simulation run.
*   `seed`: (int) Random seed used for this specific simulation.
*   `snr_level`: (float) Signal-to-Noise Ratio (e.g., 0.5, 1.0).
*   `sparsity_level`: (float) Proportion of non-zero coefficients (e.g., 0.1, 0.2).
*   `n_features`: (int) Number of predictors ($p$).
*   `n_samples`: (int) Number of observations ($n$).
*   `true_coefficients`: (list[float]) Vector $\beta^*$ of length $p$.
*   `selected_indices_forward`: (list[int]) Indices of variables selected by Forward Stepwise.
*   `selected_indices_backward`: (list[int]) Indices of variables selected by Backward Elimination.
*   `selected_indices_lasso`: (list[int]) Indices of variables selected by LASSO.
*   `selection_threshold_forward`: (float) P-value cutoff used for Forward Stepwise.
*   `selection_threshold_backward`: (float) P-value cutoff used for Backward Elimination.
*   `selection_threshold_lasso`: (float) Lambda value used for LASSO.
*   `recovery_forward`: (float) Selection Recovery Rate for Forward (TP / k).
*   `recovery_backward`: (float) Selection Recovery Rate for Backward.
*   `recovery_lasso`: (float) Selection Recovery Rate for LASSO.
*   `p_values_forward`: (dict[int, float]) Map of feature index to p-value (refitted OLS, **descriptive only**).
*   `p_values_backward`: (dict[int, float]) Map of feature index to p-value (**descriptive only**).
*   `p_values_lasso`: (dict[int, float]) Map of feature index to p-value (**descriptive only**, flagged as biased).
*   `condition_number`: (float) Condition number of $X$.
*   `timestamp`: (str) ISO8601 timestamp of generation.

### 2. PowerMetric (Aggregated)
Aggregated record for statistical comparison. **One row per combination of Dataset, Method, SNR, and Sparsity** (n=10 per group).

**Fields**:
*   `dataset_id`: (int) The dataset this aggregate belongs to.
*   `method`: (str) "Forward", "Backward", "LASSO".
*   `snr_level`: (float) SNR value.
*   `sparsity_level`: (float) Sparsity value.
*   `n_simulations`: (int) Count of simulations aggregated ().
*   `mean_recovery`: (float) Average recovery rate across 1,000 simulations.
*   `std_recovery`: (float) Standard deviation of recovery across simulations.
*   `ci_lower`: (float) Lower bound of 95% CI.
*   `ci_upper`: (float) Upper bound of 95% CI.
*   `test_statistic`: (float) Friedman or Mixed-Effects statistic (if applicable).
*   `p_value_omnibus`: (float) P-value from the omnibus test.
*   `post_hoc_results`: (str) JSON string of pairwise comparisons with Holm correction.

### 3. DatasetMetadata
Record of the raw dataset downloaded from OpenML.

**Fields**:
*   `openml_id`: (int) OpenML dataset ID.
*   `name`: (str) Dataset name.
*   `n_samples`: (int) Number of rows.
*   `n_features`: (int) Number of columns.
*   `target_name`: (str) Name of the target variable.
*   `checksum_md5`: (str) MD5 hash of the downloaded file.
*   `download_url`: (str) Canonical OpenML URL.
*   `status`: (str) "valid", "skipped_collinearity", "skipped_size".

## Data Flow

1.  **Ingestion**: `DatasetMetadata` created upon download.
2. **Simulation**: `SimulatedDataset` created for each run ([deferred] total).
3.  **Aggregation**: `PowerMetric` created by grouping `SimulatedDataset` results **per dataset** (10 aggregates per condition).
4.  **Analysis**: Statistical tests performed on `PowerMetric` (n=10 per group) using Mixed-Effects or Friedman tests.

## Storage Format

*   **Raw/Intermediate**: `data/simulated/simulations_{dataset_id}_{seed}.parquet` (Chunked by dataset to manage memory).
*   **Aggregated**: `results/simulation_results.csv` (Dataset-level aggregates).
*   **Metadata**: `data/raw/datasets.json`.