# Data Model: Investigating the Validity of the Equipartition Theorem in Driven Granular Systems

## Overview
This document defines the data structures used for ingestion, processing, and output. All data is stored as CSV or JSON for portability and version control.

## Core Entities

### 1. ParticleState (Raw/Ingested)
Represents the state of a single particle at a specific timestamp.
- **Source**: `data/raw/particle_tracking.csv`
- **Fields**:
  - `timestamp` (float): Time in seconds.
  - `particle_id` (int): Unique identifier.
  - `x`, `y`, `z` (float): Position in meters.
  - `theta` (float): Orientation angle in radians.
  - `material` (str): "steel", "glass", "polymer".
  - `mass` (float): Mass in kg (can be derived from material if not present).
  - `moment_of_inertia` (float): $I$ in kg·m².

### 2. EnergySample (Derived)
Computed energy values for a single particle at a single timestamp.
- **Source**: `data/derived/energy_samples.csv`
- **Fields**:
  - `timestamp` (float)
  - `particle_id` (int)
  - `E_trans` (float): Translational kinetic energy (J).
  - `E_rot` (float): Rotational kinetic energy (J).
  - `E_pot` (float): Potential energy (J).
  - `E_vib_residual` (float): Diagnostic residual (Total - E_trans - E_rot - E_pot), NOT used for hypothesis testing.
  - `material` (str)
  - `driving_frequency` (float): Hz (from synchronized log).

### 3. EnergyDistribution (Aggregated)
Aggregated statistics for a specific group (Material + Frequency).
- **Source**: `artifacts/distributions.json`
- **Fields**:
  - `group_id` (str): e.g., "steel_10Hz".
  - `material` (str)
  - `frequency` (float)
  - `n_samples` (int)
  - `mean_E_trans` (float)
  - `mean_E_rot` (float)
  - `mean_E_ratio` (float): $\mu_{E_{rot}} / \mu_{E_{trans}}$.
  - `excess_kurtosis_E_trans` (float)
  - `excess_kurtosis_E_rot` (float)
  - `distribution_data` (list): Raw energy values for KS test (Lilliefors).

### 4. StatisticalResult
Outcome of hypothesis tests.
- **Source**: `artifacts/stats_results.json`
- **Fields**:
  - `test_id` (str)
  - `group_id` (str)
  - `test_type` (str): "RatioTest", "KS_Lilliefors", "ChiSq", "Regression".
  - `statistic_value` (float)
  - `p_value_raw` (float)
  - `p_value_corrected` (float) (FDR adjusted)
  - `is_significant` (bool)
  - `rejection_flag` (bool) (True if $H_0$ rejected).

### 5. RegressionResult
Outcome of linear regression analysis.
- **Source**: `artifacts/regression_results.json`
- **Fields**:
  - `model_id` (str)
  - `dependent_variable` (str): "excess_kurtosis" or "energy_ratio".
  - `slope` (float)
  - `intercept` (float)
  - `r_squared` (float)
  - `slope_p_value` (float)
  - `slope_t_stat` (float)
  - `model_fit_quality` (str): "Good", "Poor", "Inconclusive".

## Data Flow

1. **Raw CSV** -> `ingestion.py` -> **EnergySample** (Filtered/Sampled).
2. **EnergySample** -> `stats.py` -> **EnergyDistribution** (Binned).
3. **EnergyDistribution** -> `stats.py` -> **StatisticalResult**.
4. **StatisticalResult** + **EnergySample** -> `regression.py` -> **RegressionResult**.
5. **All Results** -> `paper/` generation scripts.
