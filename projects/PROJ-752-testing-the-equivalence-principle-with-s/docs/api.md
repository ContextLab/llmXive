# API Reference

This document provides an overview of the public API for the PROJ-752 pipeline.

## Configuration

### `config.Config`
The central configuration object loaded from `config.yaml`.

**Attributes**:
- `paths`: Dictionary of file paths.
- `benchmark_values`: Dictionary containing `etvos_limit`.
- `hyperparams`: Dictionary of model hyperparameters.

**Usage**:
```python
from config import get_config
config = get_config()
limit = config.benchmark_values.etvos_limit
```

## Data Ingestion

### `data.ingestion.fetch_satellite_data(satellite_id, year)`
Fetches SLR data for a specific satellite and year.

**Returns**: `bytes` (raw file content).

### `data.ingestion.parse_slr_file(raw_content)`
Parses raw SLR file content into a list of `NormalPoint` objects.

**Returns**: `List[NormalPoint]`

### `data.ingestion.aggregate_satellites(satellite_ids)`
Aggregates data for multiple satellites into a single DataFrame.

**Returns**: `pd.DataFrame`

## Preprocessing

### `data.preprocessing.filter_residuals(df, threshold=0.02)`
Filters out normal points with residuals exceeding the threshold (in meters).

**Returns**: `pd.DataFrame`

### `data.preprocessing.align_time_series(dfs)`
Aligns multiple satellite datasets to a common time grid.

**Returns**: `pd.DataFrame`

## Dynamics & Estimation

### `models.dynamics.DynamicsModel`
Class responsible for computing accelerations (Geopotential, Drag, SRP, Relativity).

**Methods**:
- `compute_acceleration(state, time, metadata)` -> `np.ndarray`

### `models.estimator.separate_fit_satellite(data, params)`
Performs a separate least-squares fit for a single satellite.

**Returns**: `OrbitSolution`

### `models.estimator.run_joint_fit(data_pair, params)`
Performs a joint least-squares fit for a pair of satellites.

**Returns**: `OrbitSolution`

## Analysis

### `analysis.eotvos.compute_eotvos_parameter(ac, g, cov)`
Computes the Eötvös parameter and its confidence interval.

**Returns**: `Tuple[float, Tuple[float, float]]` (eta, ci)

### `analysis.validation.compare_null_vs_alternative(null_sol, alt_sol)`
Performs F-test and BIC comparison between two models.

**Returns**: `ValidationResult`

## Utilities

### `utils.hashing.compute_sha256(filepath)`
Computes the SHA-256 hash of a file.

**Returns**: `str`

### `utils.logging.get_logger(name)`
Returns a configured logger instance.

**Returns**: `logging.Logger`
