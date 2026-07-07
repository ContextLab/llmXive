# Data Model: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

## Overview

This document defines the data structures for the project, ensuring consistency between the download, processing, inference, and aggregation phases. All data is stored in `data/` (raw/derived) and `results/` (posteriors/metrics).

## Entity Definitions

### 1. StrainEvent
Represents a specific gravitational wave detection.
- `event_id` (string): Unique identifier (e.g., "GW150914").
- `source` (string): "GWOSC" or "Simulated".
- `original_sampling_rate` (int): Original rate in Hz (e.g., 16384).
- `snr` (float): Signal-to-noise ratio.
- `duration` (float): Duration of the analysis window in seconds.
- `ground_truth` (dict): Catalog parameters (mass_1, mass_2, spin_1, spin_2, etc.) OR injected parameters (for simulated).

### 2. ResolutionConfig
Represents a specific data processing state.
- `sampling_rate` (int): Target rate in Hz (4096, 2048, 1024).
- `bit_depth` (int): Target bit depth (16, 32).
- `quantization_method` (string): "round", "truncate", or "nearest".
- `filter_type` (string): "IIR" (for `scipy.signal.decimate`).

### 3. PosteriorDistribution
Output of the `bilby` inference pipeline.
- `parameters` (dict): Keys: `mass_1`, `mass_2`, `spin_1z`, `spin_2z`, etc. Values: list of samples (float).
- `credible_intervals` (dict): Keys: parameter name. Values: tuple `[lower_90, upper_90]`.
- `samples_count` (int): Number of posterior samples.
- `convergence_status` (string): "converged" or "inconclusive".
- `dlogz` (float): Evidence tolerance value from `dynesty`.
- `iterations` (int): Number of nested sampling iterations executed.
- `nlive` (int): Number of live points used.
- `posterior_to_prior_ratio` (float): Ratio of posterior width to prior width.
- `metadata` (dict): Links to `event_id` and `resolution_config`.

### 4. BiasMetric
Result of the comparison analysis.
- `event_id` (string).
- `resolution_config` (ResolutionConfig).
- `hellinger_distance` (float): Value between 0 and 1 (Divergence).
- `consistency_deviation` (float): Absolute deviation from catalog reference estimate (for catalog data).
- `absolute_bias` (float): Absolute bias from injected truth (for simulated data only, null otherwise).
- `exceeds_threshold` (boolean): True if deviation/bias > baseline uncertainty.
- `status` (string): "valid", "inconclusive", "failed".

## Storage Schema

### Raw Data (`data/raw/`)
- Files: `GW150914.h5` (original).
- Format: HDF5 (via `gwpy`).
- Checksum: SHA-256 recorded in `state/`.

### Derived Data (`data/derived/`)
- Files: `GW150914_2048Hz_16bit.h5`.
- Format: HDF5.
- Metadata: Includes `ResolutionConfig` in HDF5 attributes.

### Results (`results/`)
- `posteriors/`: `.h5` files containing `PosteriorDistribution` data.
- `metrics/`: `.json` or `.csv` files containing `BiasMetric` aggregates.

## Data Flow

1. **Download**: `download.py` -> `data/raw/GW150914.h5`.
2. **Process**: `process.py` reads raw, applies `ResolutionConfig`, writes `data/derived/GW150914_XXXX.h5`.
3. **Infer**: `infer.py` reads derived, runs `bilby` (dynesty), writes `results/posteriors/GW150914_XXXX.h5`.
4. **Metric**: `metrics.py` reads posterior + ground truth, writes `results/metrics/GW150914_XXXX.json`.
5. **Aggregate**: `aggregate.py` reads all metrics, writes `results/summary_report.csv`.