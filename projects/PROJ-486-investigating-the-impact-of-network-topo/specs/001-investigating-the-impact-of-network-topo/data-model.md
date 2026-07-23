# Data Model: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## Overview

This document defines the data structures, schemas, and transformation logic for the project. The data flow is: **Raw/Simulated Data** → **Processed/Joined Data** → **Analysis Results** → **Visualizations**.

## Entities

### 1. Subject
Represents an individual participant.
*   `subject_id` (str): Unique identifier (e.g., "100101").
*   `atlas_type` (str): Parcellation scheme used ("Schaefer", "AAL", "Power").
*   `data_source` (str): "Real" or "Simulated".

### 2. TopologyMetric
Network properties derived from the connectivity matrix.
*   `subject_id` (str): FK to Subject.
*   `metric_name` (str): "Clustering_Coefficient" or "Characteristic_Path_Length".
*   `value` (float): Calculated metric value.
*   `is_zero_variance` (bool): Flag if variance is 0 across the sample.

### 3. EntrainmentStrength
The dependent variable (Phase-Locking Value).
*   `subject_id` (str): FK to Subject.
*   `entrainment_metric` (float): Phase-Locking Value (0.0 to 1.0).

### 4. CorrelationResult
Output of the statistical analysis.
*   `model_id` (str): Unique ID for the model run.
*   `predictor` (str): "Clustering_Coefficient" or "Characteristic_Path_Length".
*   `coefficient` (float): Standardized beta.
*   `p_value` (float): Raw p-value (or p-value for orthogonalized predictor).
*   `adjusted_p_value` (float): Holm-Bonferroni corrected p-value.
*   `is_significant` (bool): `adjusted_p_value < 0.05`.
*   `vif` (float): Variance Inflation Factor.
*   `collinearity_warning` (bool): True if VIF > 5.
*   `power_warning` (bool): True if N < 30.
*   `r_squared` (float): Model R-squared.

## File Formats

### Raw Input (Simulated or Real)
*   `data/raw/entrainment_metrics.csv`: CSV with `subject_id`, `entrainment_metric`.
*   `data/raw/connectivity_matrices/`: Directory containing `.npy` or `.csv` matrices (simulated or real).

### Processed Data
*   `data/processed/joined_data.csv`: Merged data with `subject_id`, `Clustering_Coefficient`, `Characteristic_Path_Length`, `entrainment_metric`.
*   `data/processed/metric_flags.json`: JSON list of flags for zero-variance metrics.
*   `data/processed/metadata.json`: JSON with run parameters (N, atlas, seed, data_source).
*   `data/processed/correlation_results.csv`: Output of the statistical analysis (schema: `correlation_results.schema.yaml`).
*   `data/processed/sensitivity_results.csv`: Output of sensitivity analysis (schema: `sensitivity.schema.yaml`).

### Visualizations
*   `data/visualizations/scatter_topology_entrainment.png`: Scatter plot with 95% CI.
*   `data/visualizations/sensitivity_bar_chart.png`: Bar chart of absolute differences.

## Transformation Logic

1.  **Load & Validate**:
    *   Check for `entrainment_metrics.csv`. If missing or N < 30 after join, trigger **Simulated Data Fallback**.
    *   Validate columns: `subject_id` (str), `entrainment_metric` (float).
    *   **Error Path**: If validation fails (e.g., non-numeric), **HALT** with "Invalid Entrainment Data".
2.  **Graph Metric Calculation**:
    *   Convert connectivity matrix to `networkx.Graph` (weighted).
    *   Compute `clustering_coefficient` and `characteristic_path_length`.
    *   Check for zero variance; if found, set `is_zero_variance = True` and write to `metric_flags.json`.
3.  **Join**:
    *   Inner join `subject_id` between topology and entrainment data.
    *   Count N. If N < 30, trigger simulation.
4.  **Analysis**:
    *   Fit MLR.
    *   Calculate VIF. If VIF > 5, perform **Orthogonalization**.
    *   Apply Holm-Bonferroni correction.
    *   **Output**: Always report effect sizes (R-squared, betas). If VIF > 5, report orthogonalized betas and note "Collinearity Detected".
5.  **Output**:
    *   Write `correlation_results.csv` and `sensitivity_results.csv`.
    *   Generate PNGs.
    *   Update `state/...yaml` with hashes.