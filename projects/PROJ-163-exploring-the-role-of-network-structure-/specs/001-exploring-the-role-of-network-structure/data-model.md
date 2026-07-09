# Data Model: Exploring the Role of Network Structure in Superconducting Qubit Coupling

## Overview
This document defines the data structures used to ingest, transform, and analyze quantum processor data. All data flows from the raw API JSON to processed CSVs and finally to correlation results.

## Entity Definitions

### 1. QubitDevice
Represents a single quantum processor instance at a specific point in time.
- `device_id` (str): Unique backend name (e.g., "ibmq_manila").
- `backend_type` (str): "public" or "private".
- `chip_generation` (str): Derived generation (e.g., "Eagle", "Falcon", "Hummingbird").
- `timestamp` (datetime): Calibration snapshot time.
- `is_fresh` (bool): True if `timestamp` is within 30 days.

### 2. GraphMetric
Links a device to its computed topological descriptors.
- `device_id` (str): Foreign key to QubitDevice.
- `chip_generation` (str): Redundant denormalization for filtering.
- `metric_name` (str): One of ["avg_shortest_path", "diameter", "clustering_coef", "edge_betweenness", "degree_assortativity", "spectral_gap"].
- `value` (float): The computed metric value.
- `is_finite` (bool): True if value is not NaN/Inf.
- `component_size` (int): Size of the largest connected component (used for filtering).

### 3. PerformanceMetric
Links a device to its empirical performance values.
- `device_id` (str): Foreign key to QubitDevice.
- `metric_name` (str): One of ["T1", "T2", "gate_error", "readout_error", "entanglement_fidelity"].
- `value` (float): The measured value (normalized or raw).
- `unit` (str): e.g., "us", "1e-3", "percent".
- `source_window` (str): "current" (Note: "historical" removed due to static topology).

### 4. CorrelationResult
Stores the outcome of statistical tests.
- `graph_metric` (str): The topological descriptor.
- `performance_metric` (str): The performance indicator.
- `spearman_rho` (float): Correlation coefficient.
- `p_value` (float): Raw p-value.
- `adj_p_value` (float): BH-FDR adjusted p-value.
- `partial_rho` (float): Partial correlation coefficient controlling for `chip_generation` (if applicable).
- `is_significant` (bool): True if `adj_p_value < 0.05`.
- `exclusion_reason` (str): Optional reason (e.g., "missing_data", "disconnected_graph", "chip_family_confound").

### 5. PowerAnalysisResult
Stores the outcome of the power analysis.
- `sample_size` (int): Number of devices (N).
- `number_of_tests` (int): Total correlation tests performed.
- `min_detectable_rho` (float): Minimum detectable effect size at [deferred] power.
- `confidence_interval` (str): 95% CI for observed correlations.

## Data Flow

1.  **Raw Ingestion**: `fetcher.py` writes `data/raw/{device_name}_{timestamp}.json`.
2.  **Transformation**:
    - `graph_builder.py` reads raw JSON, computes metrics, writes `data/processed/graph_metrics.csv`.
    - `fetcher.py` (extended) reads performance data, writes `data/processed/performance_metrics.csv`.
3.  **Analysis**: `stats_engine.py` joins metrics, runs correlations (including partial correlation), performs PCA/Ridge if needed, and writes `data/processed/correlation_results.csv`.
4.  **Power Analysis**: `stats_engine.py` computes MDES and writes `data/processed/power_analysis.csv`.
5.  **Visualization**: `viz.py` reads `correlation_results.csv` to generate plots.

## Constraints & Validation
- **No NaN/Inf**: All numeric fields in `GraphMetric` and `PerformanceMetric` must be finite.
- **Timestamps**: All `timestamp` fields must be valid ISO 8601 strings.
- **Uniqueness**: `device_id` + `metric_name` in `GraphMetric` must be unique.
- **Referential Integrity**: `device_id` in `GraphMetric` must exist in `QubitDevice`.
- **Chip Generation**: `chip_generation` must be a known IBM generation string or "Unknown".