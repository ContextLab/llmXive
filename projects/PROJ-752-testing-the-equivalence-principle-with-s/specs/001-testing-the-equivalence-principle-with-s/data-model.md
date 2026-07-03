# Data Model: Testing the Equivalence Principle with Satellite Laser Ranging

## Overview

This document defines the data structures, schemas, and relationships used throughout the project. All data artifacts must conform to these definitions to ensure reproducibility and contract validation.

## Entities

### 1. NormalPoint

Represents a single Satellite Laser Ranging observation.

*   **timestamp**: ISO 8601 string (e.g., `2026-01-01T12:00:00Z`).
*   **range**: Float (meters).
*   **satellite_id**: String (e.g., `LAGEOS-1`, `ETALON-2`).
*   **station_id**: String (e.g., `7110`).
*   **quality_flag**: Integer (0=Good, 1=Outlier, 2=Low Confidence).
*   **residual**: Float (meters, **post-fit residual**). *Note: This field is computed in the `processed` stage after the orbit fit, not present in raw data.*

### 2. OrbitSolution

Represents the result of a weighted least-squares orbit determination fit (Joint Fit).

*   **satellite_pair**: List of two strings (e.g., `["LAGEOS-1", "LAGEOS-2"]`).
*   **epoch**: ISO 8601 string.
*   **orbital_elements**: Dictionary (semi-major axis, eccentricity, inclination, etc. for both satellites).
*   **non_gravitational_acceleration**: Dictionary (drag coefficient $C_D$, SRP coefficient $C_R$, etc. for both satellites).
*   **differential_parameter**: Float ($\\eta$ or $a_c$).
*   **covariance_matrix**: List of lists (float).
*   **chi_squared**: Float.
*   **residuals_rms**: Float (meters).
*   **converged**: Boolean.

### 3. EotvosResult

Represents the final test outcome for a satellite pair.

*   **satellite_pair**: List of two strings (e.g., `["LAGEOS-1", "LAGEOS-2"]`).
*   **differential_acceleration**: Float (m/s²).
*   **eta**: Float (Eötvös parameter).
*   **eta_lower_ci**: Float (95% CI lower bound).
*   **eta_upper_ci**: Float (95% CI upper bound).
*   **p_value**: Float.
*   **z_score**: Float.
*   **geopotential_model**: String (e.g., `GGM05C`).
*   **sensitivity_data**: List of dictionaries (Z-scores for alternative models).
*   **adjusted_p_value**: Float (after multiple-comparison correction).
*   **status**: String (`"Significant"`, `"Unreliable"`, `"Constrained"`).
*   **benchmark_comparison**: Dictionary (reference value, target precision, actual width).

## Data Flow

1.  **Raw Data**: Downloaded from source (Verified URL) -> `data/raw/*.parquet`.
2.  **Processed Data**: Filtered, aligned, and **orbit fitted** -> `data/processed/*.csv` (includes computed `residual` field).
3.  **Orbit Solutions**: Estimated via `models/estimator.py` (Joint Fit) -> `data/results/orbit_solutions/*.json`.
4.  **Final Results**: Aggregated via `analysis/eotvos.py` -> `data/results/eotvos_results.csv`.

## Contracts

See `contracts/` directory for YAML schemas:
*   `normal_point.schema.yaml`: Validates raw/processed SLR data.
*   `orbit_solution.schema.yaml`: Validates orbit determination output.
*   `eotvos_result.schema.yaml`: Validates final statistical results.
