# Data Model: Exploring the Impact of Data Imputation Methods on Causal Inference

## Overview

This document defines the data structures, schemas, and relationships used throughout the simulation study. All data artifacts are stored in `data/` with checksums recorded in the project state.

## Entity Definitions

### 1. SyntheticDataset
Represents a single generated instance of the SCM.
- **Attributes**:
  - `run_id`: Unique identifier (UUID).
  - `seed`: Integer random seed.
  - `sample_size`: Integer (N=1000).
  - `true_ate`: Float (Ground truth $\tau$).
  - `beta_mnar`: Float (MNAR parameter $\beta$).
 - `alpha_mnar`: Float (Tuned intercept for [deferred] missingness).
  - `missing_rate`: Float (Observed missingness rate, target 0.2).
  - `data_path`: Relative path to CSV file in `data/raw/`.
- **File Format**: CSV (`data/raw/synth_{run_id}.csv`).

### 2. ImputationResult
Represents the output of an imputation method applied to a `SyntheticDataset`.
- **Attributes**:
  - `run_id`: Link to `SyntheticDataset`.
  - `method`: String ("mean", "knn", "mice").
  - `imputed_data_path`: Relative path to CSV in `data/processed/`.
  - `convergence_status`: Boolean (True if converged, False if failed).
  - `missing_rate`: Float (Should be 0.0).
- **File Format**: CSV (`data/processed/imputed_{run_id}_{method}.csv`).

### 3. CausalEstimate
Represents the final ATE calculation for a specific imputation method and estimator.
- **Attributes**:
  - `run_id`: Link to source.
  - `imputation_method`: String.
  - `estimator_type`: String ("ipw", "psm").
  - `estimated_ate`: Float.
  - `standard_error`: Float.
  - `bias`: Float ($|\hat{\tau} - \tau_{true}|$).
  - `rmse`: Float.
  - `ci_lower`: Float (95% CI lower bound).
  - `ci_upper`: Float (95% CI upper bound).
  - `coverage`: Boolean (True if CI contains `true_ate`).
  - `interaction_flag`: Boolean (True if IPW/PSM bias divergence > 10%).
- **Storage**: Aggregated in `data/results/simulation_summary.csv`.

## Schema Definitions

### Input Schema: Synthetic Dataset (CSV)
| Column | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique run identifier |
| `treatment` | int | Binary treatment (0/1) |
| `outcome` | float | Continuous outcome (NaN if missing) |
| `confounder_1` | float | Continuous confounder |
| `confounder_2` | float | Continuous confounder |
| `missing_indicator` | int | 1 if missing, 0 otherwise |

### Output Schema: Simulation Summary (CSV)
| Column | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique run identifier |
| `beta_mnar` | float | MNAR parameter for this run |
| `true_ate` | float | Ground truth ATE |
| `imputation_method` | string | mean, knn, or mice |
| `estimator_type` | string | ipw or psm |
| `estimated_ate` | float | Calculated ATE |
| `bias` | float | Absolute bias |
| `rmse` | float | Root Mean Squared Error |
| `ci_lower` | float | 95% CI Lower |
| `ci_upper` | float | 95% CI Upper |
| `coverage` | boolean | 1 if CI covers true_ate |
| `interaction_flag` | boolean | 1 if IPW/PSM bias divergence > 10% |

## Data Flow

1.  **Generation**: `simulate.py` → `data/raw/synth_{run_id}.csv`
2.  **Imputation**: `impute.py` → `data/processed/imputed_{run_id}_{method}.csv`
3.  **Estimation**: `estimate.py` → In-memory `CausalEstimate` objects.
4.  **Aggregation**: `analyze.py` → `data/results/simulation_summary.csv`.
5.  **Visualization**: `visualize.py` → `data/results/plots/*.png`.
