# Data Model: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

## Overview

This document defines the data structures used to represent the harmonized experimental data, the model parameters, and the inference results. All data is stored in `data/` and validated against the schemas in `contracts/`. The `harmonized_dataset.csv` is the Single Source of Truth (SSoT); JSON schemas validate the in-memory representation.

## Entities

### 1. HarmonizedDataset
Represents the unified force-vs-separation data from multiple experiments.

-   **Source**: `data/processed/harmonized_dataset.csv`
-   **Description**: A tabular dataset where each row represents a measurement point at its **exact** separation distance. **No interpolation** is performed.
-   **Attributes**:
    -   `experiment_id`: Identifier for the source experiment (e.g., "eotwash_2021", "review_2023").
    -   `separation_m`: Separation distance in meters (float).
    -   `force_N`: Force measurement in Newtons (float).
    -   `stat_error_N`: Statistical uncertainty in Newtons (float).
    -   `sys_error_N`: Systematic uncertainty in Newtons (float).
    -   `total_error_N`: Combined uncertainty (float, derived).
    -   `original_units_force`: Original unit of force (string, e.g., "dynes").
    -   `original_units_dist`: Original unit of distance (string, e.g., "micrometers").

### 2. CovarianceMatrix
Represents the error structure, implemented as a **diagonal matrix** due to lack of off-diagonal data.

-   **Source**: `data/processed/covariance_matrix.npy`
-   **Description**: A 2D NumPy array of shape $(N, N)$ where $N$ is the total number of data points in `HarmonizedDataset`.
-   **Properties**:
    -   Off-diagonal elements are **0**.
    -   Diagonal elements: $Var(F_i) = \sigma_{stat, i}^2 + \sigma_{sys, i}^2$.
    -   **Sensitivity**: A banded covariance matrix may be generated for sensitivity analysis.

### 3. ModelPosterior
Represents the sampled distribution of parameters from the MCMC run.

-   **Source**: `data/results/mcmc_chains.h5` or `.npy`
-   **Attributes**:
    -   `alpha_samples`: Array of shape $(N_{walkers}, N_{steps})$ containing samples of $\alpha$.
    -   `lambda_samples`: Array of shape $(N_{walkers}, N_{steps})$ containing samples of $\lambda$.
    -   `log_prob`: Array of log-probabilities.
    -   `convergence_metric`: Gelman-Rubin statistic (float).
    -   `n_steps`: Actual number of steps run (up to 5000).

### 4. BayesianEvidence
Represents the computed log-evidence for model comparison.

-   **Source**: `data/results/evidence.json`
-   **Attributes**:
    -   `log_z_newtonian`: Log-evidence for the null model ($\alpha=0$).
    -   `log_z_yukawa`: Log-evidence for the Yukawa model.
    -   `bayes_factor_k`: Calculated $K = \exp(\Delta \ln \mathcal{Z})$.
    -   `interpretation`: String description based on Kass-Raftery scale.

### 5. RobustnessResult
Represents the results of validation tests.

-   **Source**: `data/results/robustness_report.json`
-   **Attributes**:
    -   `test_type`: Type of test (e.g., "leave_one_out", "null_simulation").
    -   `n_simulations`: Number of simulations (for null test).
    -   `false_positive_rate`: Fraction of simulations where Bayes factor > 3.
    -   `cv_limits`: Coefficient of variation of upper limits (for LOO).
    -   `status`: "passed", "failed", or "warning" (e.g., if CV > 0.15).

## Data Flow

1.  **Ingest**: Raw files (`data/raw/*.tar.gz`) $\to$ `download.py`.
2.  **Harmonize**: Raw data $\to$ `harmonize.py` $\to$ `HarmonizedDataset` (CSV) + `CovarianceMatrix` (Numpy).
3.  **Inference**: `HarmonizedDataset` + `CovarianceMatrix` $\to$ `inference.py` $\to$ `ModelPosterior` + `BayesianEvidence`.
4.  **Robustness**: `ModelPosterior` $\to$ `robustness.py` $\to$ Sensitivity reports.

## Validation

All data artifacts must pass the schema validation defined in `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` before being used in downstream analysis or reported in the final paper. The CSV file is the SSoT; the schema validates the in-memory parsed data.
