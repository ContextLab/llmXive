# Data Model: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Overview

This document defines the data structures used throughout the pipeline, ensuring type safety and reproducibility. All data is stored in NumPy `.npy` (matrices) and JSON (metadata/profiles) formats.

## Data Entities

### 1. Subject Metadata
**Format**: JSON
**Location**: `data/processed/{subject_id}_meta.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `subject_id` | string | HCP Subject ID (e.g., "100001") |
| `status` | string | "complete", "skipped", "error" |
| `reason` | string | (Optional) Reason for skip/error |
| `seed` | integer | Random seed used (42) |

### 2. Structural Connectome (Binary)
**Format**: NumPy `.npy` (uint8)
**Shape**: `(100, 100)`
**Location**: `data/processed/{subject_id}_structural.npy`
**Description**: Binary adjacency matrix derived from DWI tractography, parcellated to a standard atlas and thresholded at a fixed density. `1` = connection, `0` = no connection. Diagonal = 0.

### 3. Structural Connectome (Weighted)
**Format**: NumPy `.npy` (float32)
**Shape**: `(100, 100)`
**Location**: `data/processed/{subject_id}_structural_weighted.npy`
**Description**: Weighted adjacency matrix derived from DWI tractography (streamline count). Used for Global Efficiency calculation. Diagonal = 0.

### 4. Functional Connectome (Correlation)
**Format**: NumPy `.npy` (float64)
**Shape**: `(100, 100)`
**Location**: `data/processed/{subject_id}_rsfc.npy`
**Description**: Pearson correlation matrix of BOLD time-series. Values in `[-1, 1]`.

### 5. Global Metrics
**Format**: JSON
**Location**: `data/processed/{subject_id}_metrics.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `global_efficiency` | float | Global efficiency of **weighted** (unthresholded) structural graph |
| `mean_degree` | float | Average node degree (structural, binary) |
| `rsfc_strength` | float | Mean absolute correlation of rsFC matrix |
| `network_density` | float | Density of the binary structural graph (used as control variable) |

### 6. Motif Profile
**Format**: JSON
**Location**: `data/processed/{subject_id}_motifs.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `motif_z_scores` | object | Key: motif_id (e.g., "M1"), Value: float (median z-score) or null (if failed) |
| `motif_z_scores_raw` | object | Key: motif_id, Value: object (keys: "[deferred]", "[deferred]", "[deferred]") with float values |
| `null_model_params` | object | `iterations`: 100, `method`: "maslov_sneppen" |
| `computation_time` | float | Seconds taken |
| `threshold_density` | array | List of thresholds used: [0.1, 0.2, 0.3] |
| `null_model_failed` | array | List of motif_ids where null model failed to converge (excluded from analysis) |

### 7. Analysis Results (Aggregate)
**Format**: CSV or JSON
**Location**: `results/analysis_results.csv`

| Field | Type | Description |
| :--- | :--- | :--- |
| `motif_id` | string | Motif identifier |
| `correlation_type` | string | "pearson" or "spearman" |
| `r_value` | float | Partial correlation coefficient |
| `p_value_raw` | float | Raw p-value |
| `p_value_corrected` | float | FDR-corrected p-value |
| `significant` | boolean | True if `p_value_corrected` < 0.05 |
| `empirical_p` | float | Permutation test p-value |
| `n_permutations` | integer | Number of permutations (sufficient for convergence) |
| `control_variable` | string | "network_density" |
| `vif` | float | Variance Inflation Factor for control variable (if calculated) |

### 8. Power Analysis
**Format**: JSON
**Location**: `results/power_analysis.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `n_subjects` | integer | 50 |
| `alpha_adjusted` | float | FDR-adjusted alpha |
| `power` | float | Target power (sufficient to detect the hypothesized effect) |
| `detectable_r` | float | Minimum detectable Pearson r (two-tailed) |
| `test_type` | string | "two-tailed" |
