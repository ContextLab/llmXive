# Data Model: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## Overview
This document defines the data structures, schemas, and relationships used in the project. All data is stored in `data/` with checksums recorded in `state/`.

## Entities

### 1. GWOSCEvent
Represents a compact binary coalescence detection from GWOSC.
- **Attributes**:
  - `event_id`: String (e.g., "GW150914")
  - `detector_network`: List[String] (e.g., ["LLO", "LHO"])
  - `strain_h_plus`: Float64 Array (time series)
  - `strain_h_cross`: Float64 Array (time series)
  - `timestamp`: Float64 (GPS time)
  - `metadata`: Dict (mass, distance, spin parameters)
  - `checksum`: String (SHA-256)

### 2. CompressionArtifact
Represents the result of applying a compression method to a waveform.
- **Attributes**:
  - `source_event_id`: String
  - `method`: String (e.g., "gzip", "jpeg2000", "quantize_8bit")
  - `level`: Int (compression level or bit-depth)
  - `file_size_original`: Int (bytes)
  - `file_size_compressed`: Int (bytes)
  - `compression_ratio`: Float
  - `reconstruction_mse`: Float (0.0 for lossless)
  - `snr_degradation_db`: Float
  - `checksum`: String

### 3. ParameterPosterior
Represents the posterior distribution from LALInference.
- **Attributes**:
  - `event_id`: String
  - `source_type`: String ("original" or "compressed")
  - `method`: String (if compressed)
  - `parameter`: String ("mass", "distance", "spin")
  - `samples`: Float64 Array (MCMC samples **loaded from LALInference output files (e.g., .txt or .hdf5)**)
  - `kl_divergence`: Float (vs. original)
  - `bias_mae`: Float (vs. ground truth, if injection)
  - `convergence_rhat`: Float (Gelman-Rubin statistic)

### 4. SimulatedInjection
Represents a synthetic signal with known ground truth.
- **Attributes**:
  - `injection_id`: String
  - `true_mass`: Float
  - `true_distance`: Float
  - `true_spin`: Float
  - `theoretical_snr`: Float
  - `measured_bias_mae`: Float
  - `confidence_interval_95`: Tuple[Float, Float]

## Data Flow

1. **Acquisition**: `GWOSCEvent` downloaded from API -> `data/raw/`.
2. **Simulation**: `SimulatedInjection` generated -> `data/raw/`.
3. **Compression**: `GWOSCEvent` + `SimulatedInjection` -> `CompressionArtifact` -> `data/processed/`.
4. **Estimation**: `GWOSCEvent` + `CompressionArtifact` -> LALInference (files) -> `ParameterPosterior` (loaded into memory) -> `data/derived/`.
5. **Analysis**: `ParameterPosterior` + `SimulatedInjection` -> Statistics -> `data/derived/stats.json`.

## Constraints

- **Immutability**: Raw data files are never modified.
- **Checksums**: Every file in `data/` must have a corresponding SHA-256 hash.
- **Schema Validation**: All output files must match the schemas in `contracts/`.
- **Convergence**: Events with `convergence_rhat` > 1.1 are excluded from bias analysis.