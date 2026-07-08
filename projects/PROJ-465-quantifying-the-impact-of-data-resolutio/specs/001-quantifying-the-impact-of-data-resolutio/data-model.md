# Data Model: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

## Overview

This document defines the data structures used throughout the pipeline, from raw strain data to final bias metrics. All data is stored in the `data/` directory with checksums recorded.

## Entities

### 1. StrainEvent
Represents a gravitational wave detection event.
- **Attributes**:
  - `event_id`: string (e.g., "GW150914")
  - `original_sampling_rate`: float (Hz)
  - `snr`: float (Signal-to-Noise Ratio)
  - `duration`: float (seconds)
  - `ground_truth_params`: dict (mass_1, mass_2, spin_1, spin_2, etc.)

### 2. ResolutionConfig
Represents a specific data processing state.
- **Attributes**:
  - `sampling_rate`: int (Hz) (e.g., 4096, 2048, 1024)
  - `bit_depth`: int (bits) (e.g., 32, 16)
  - `quantization_method`: string ("float16", "float32")

### 3. PosteriorDistribution
Output of the inference pipeline.
- **Attributes**:
  - `samples`: array (N x D) where D is the number of parameters.
  - `parameters`: list of strings (e.g., ["mass_1", "mass_2", "chi_eff"])
  - `credible_intervals`: dict (param -> [lower, upper])
  - `convergence_status`: string ("converged", "inconclusive")
  - `dlogz`: float (change in log evidence)

### 4. BiasMetric
Comparative analysis result.
- **Attributes**:
  - `event_id`: string
  - `resolution_config`: dict (sampling_rate, bit_depth)
  - `hellinger_distance`: float (0.0 to 1.0)
  - `mass_bias_percentage`: float
  - `spin_bias_percentage`: float
  - `exceeds_threshold`: boolean (True if bias > catalog 90% CI)
  - `truth_source`: string ("catalog", "injected")

## Data Flow

1. **Raw Data**: `data/raw/{event_id}.dat` (GWOSC strain).
2. **Processed Data**: `data/processed/{event_id}_{rate}_{bit}.dat` (downsampled/quantized).
3. **Posterior**: `data/outputs/{event_id}_{rate}_{bit}_posterior.h5` (Bilby output).
4. **Metrics**: `data/outputs/{event_id}_{rate}_{bit}_metrics.json`.
5. **Aggregated**: `data/outputs/summary.csv`.

## Constraints

- **Immutability**: Raw data is never overwritten.
- **Checksums**: Every file in `data/` has a corresponding SHA-256 hash recorded in `state/`.
- **Precision**: All float operations use at least 32-bit precision unless explicitly quantized to 16-bit for the experiment.