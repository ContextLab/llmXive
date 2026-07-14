# Data Model: The Impact of Bounded Confidence on Opinion Polarization Speed

## Overview

This document defines the data structures for network generation, simulation execution, and analysis results. All data is stored in CSV or Parquet formats to ensure compatibility with Python data stacks and checksum verification.

## Entity Definitions

### 1. NetworkInstance
Represents a single generated graph.
-   `network_id`: Unique identifier (UUID).
-   `topology_type`: Enum {`er`, `ba`, `ws`}.
-   `node_count`: Integer (500).
-   `edge_count`: Integer.
-   `assortativity`: Float (Pearson correlation of degrees).
-   `average_path_length`: Float.
-   `clustering_coefficient`: Float.
-   `rewiring_prob`: Float (only for `ws`, else null).
-   `seed`: Integer (random seed used for generation).

### 2. SimulationRun
Represents a single execution of the HK model.
-   `run_id`: Unique identifier (UUID).
-   `network_id`: FK to `NetworkInstance`.
-   `epsilon`: Float (confidence threshold).
-   `seed`: Integer (random seed for initial opinions).
-   `convergence_time`: Integer (iterations to converge).
-   `status`: Enum {`converged`, `non_converged`}.
-   `final_clusters`: Integer (number of opinion clusters at end).
-   `timestamp`: ISO8601.

### 3. ScalingResult
Represents the fitted parameters for a single network instance.
-   `network_id`: FK to `NetworkInstance`.
-   `topology_type`: Enum.
-   `gamma`: Float (scaling exponent).
-   `epsilon_c`: Float (critical threshold estimate).
-   `r_squared`: Float.
-   `standard_error`: Float.
-   `n_points`: Integer (number of $\epsilon$ points used in fit).

### 4. RegressionResult
Represents the outcome of the multiple linear regression.
-   `metric_name`: String (e.g., "assortativity").
-   `coefficient`: Float.
-   `p_value`: Float.
-   `adjusted_r_squared`: Float.
-   `model_type`: String (e.g., "A", "B").

### 5. SensitivityResult
Represents the outcome of the sensitivity analysis (FR-008).
-   `metric_name`: String (e.g., "convergence_threshold").
-   `threshold_value`: Float (e.g., 1e-3, 1e-4, 1e-5).
-   `gamma_estimate`: Float.
-   `variation_percent`: Float (variation from baseline).

## File Layout

```text
data/
├── raw/
│   ├── networks/
│   │   ├── er_001.csv
│   │   ├── ba_001.csv
│   │   └── ...
│   └── simulations/
│       ├── sim_00001.csv
│       └── ...
├── processed/
│   ├── scaling_fits.csv
│   ├── regression_summary.csv
│   └── sensitivity_analysis.csv
└── checksums.json
```

## Data Flow

1.  **Generation**: `generate_networks.py` creates `NetworkInstance` records and writes to `data/raw/networks/`.
2.  **Simulation**: `simulate_hk.py` reads networks, runs HK, writes `SimulationRun` records to `data/raw/simulations/`.
3.  **Analysis**: `analyze_scaling.py` aggregates simulations, fits power laws (per network instance), runs regression, writes `ScalingResult` and `RegressionResult` to `data/processed/`.
4.  **Sensitivity**: `run_sensitivity.py` sweeps convergence thresholds, writes `SensitivityResult` to `data/processed/sensitivity_analysis.csv`.

## Integrity Constraints

-   **Immutability**: Files in `data/raw/` are never overwritten. New runs append or create new files with timestamps.
-   **Checksums**: Every file in `data/` must have a corresponding entry in `checksums.json` (SHA-256).
-   **Schema Validation**: All CSVs must match the column definitions above.