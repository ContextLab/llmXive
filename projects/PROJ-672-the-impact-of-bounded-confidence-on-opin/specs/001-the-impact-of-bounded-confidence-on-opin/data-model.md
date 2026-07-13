# Data Model: The Impact of Bounded Confidence on Opinion Polarization Speed

## 1. Overview

This document defines the data structures for the synthetic network generation, simulation execution, and analysis results. All data is stored in `data/` with a strict separation between raw outputs and processed metrics.

## 2. Entity Definitions

### 2.1 NetworkInstance
Represents a single generated graph.
-   `network_id`: Unique string (e.g., `BA_N500_m2_seed42`).
-   `topology_type`: Enum (`ER`, `BA`, `WS`).
-   `node_count`: Integer (500).
-   `edge_count`: Integer.
-   `assortativity`: Float (Pearson correlation of degrees).
-   `average_path_length`: Float (or NaN if disconnected).
-   `clustering_coefficient`: Float.
-   `rewiring_probability`: Float (only for WS, null otherwise).
-   `seed`: Integer.

### 2.2 SimulationRun
Represents a single execution of the HK model.
-   `run_id`: Unique string.
-   `network_id`: Foreign key to `NetworkInstance`.
-   `epsilon`: Float.
-   `seed`: Integer.
-   `convergence_time`: Integer (iterations to converge).
-   `final_clusters`: Integer (number of opinion clusters at convergence).
-   `status`: Enum (`converged`, `non_converged`, `timeout`).
-   `max_opinion_change`: Float (at final step).

### 2.3 ScalingResult
Represents the fitted parameters for a **single network instance**.
-   `instance_id`: String (Foreign key to NetworkInstance).
-   `topology_type`: Enum.
-   `gamma`: Float (scaling exponent).
-   `epsilon_c`: Float (critical threshold estimate, derived from peak finding).
-   `model_type`: Enum (`power_law`, `exponential`, `inconclusive`).
-   `r_squared`: Float.
-   `aic`: Float (Akaike Information Criterion).
-   `standard_error`: Float.
-   `sample_size`: Integer.

### 2.4 RegressionResult
Represents the output of the multiple linear regression.
-   `metric_name`: String (e.g., "assortativity").
-   `coefficient`: Float.
-   `std_error`: Float.
-   `t_statistic`: Float.
-   `p_value`: Float.
-   `model_r_squared`: Float.
-   `fdr_adjusted_p`: Float (False Discovery Rate adjusted p-value).

### 2.5 SensitivityResult
Represents the output of the sensitivity analysis (FR-008).
-   `topology_type`: Enum.
-   `convergence_threshold`: Float (e.g., 1e-3, 1e-4, 1e-5).
-   `mean_gamma`: Float (average $\gamma$ across instances for this threshold).
-   `std_gamma`: Float.
-   `variation_percent`: Float (variation relative to the baseline threshold).

## 3. File Formats

### 3.1 Raw Simulation Data
-   **Path**: `data/raw/simulations.csv`
-   **Format**: CSV (Comma Separated Values).
-   **Schema**: Matches `SimulationRun` entity.
-   **Constraints**: No headers with special characters; `epsilon` formatted to 3 decimal places.

### 3.2 Processed Metrics
-   **Path**: `data/processed/network_metrics.csv`, `data/processed/scaling_results.csv`, `data/processed/regression_results.csv`, `data/processed/sensitivity_results.csv`
-   **Format**: CSV.
-   **Schema**: Matches corresponding entities.

### 3.3 Checksums
-   **Path**: `data/.checksums.json`
-   **Content**: SHA-256 hashes of all files in `data/raw/` and `data/processed/`.
-   **State Integration**: These hashes are recorded in `state/projects/PROJ-672-the-impact-of-bounded-confidence-on-opin.yaml` under the `artifact_hashes` key.

## 4. Data Lineage

1.  **Generation**: `generate_networks.py` reads config, generates graphs, writes `network_metrics.csv`.
2.  **Simulation**: `simulate_hk.py` reads `network_metrics.csv`, runs HK, appends to `simulations.csv`.
3.  **Analysis**: `analyze_scaling.py` reads `simulations.csv`, fits models per instance, writes `scaling_results.csv` and `regression_results.csv`.
4.  **Sensitivity**: `sensitivity_analysis.py` reads `simulations.csv`, writes `sensitivity_results.csv`.
5.  **Checksum**: `utils/checksums.py` generates `data/.checksums.json` and updates the state file.

## 5. Validation Rules

-   **Range Checks**: $\epsilon \in [0.05, 0.50]$.
-   **Type Checks**: All floats must be finite (no NaN/Inf in `convergence_time`).
-   **Uniqueness**: `run_id` and `instance_id` must be unique.
-   **Referential Integrity**: `network_id` in `simulations.csv` must exist in `network_metrics.csv`.
-   **Model Consistency**: If `model_type` is `power_law`, `r_squared` must be reported; if `exponential`, `aic` must be reported.
