# Data Model: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

## 1. Overview

This document defines the data entities, schemas, and relationships for the compression impact study. The model supports the generation of synthetic injections, the application of compression, and the storage of parameter estimation results.

## 2. Entity Definitions

### 2.1 SyntheticInjection
Represents a synthetic CBC signal injected into real noise.
-   **injection_id**: Unique identifier (string).
-   **detectors**: List of detector names (e.g., `["H1", "L1"]`).
-   **timestamp**: UTC timestamp of the event (float).
-   **strain_data**: Time series of strain data (numpy array, float64).
-   **true_parameters**: Dictionary of known injection parameters (mass, spin, distance, etc.).
-   **metadata**: Additional event info (source, file path, SNR).

### 2.2 CompressionArtifact
Represents the result of applying a compression method to a SyntheticInjection.
-   **artifact_id**: Unique identifier (string).
-   **source_injection_id**: Reference to SyntheticInjection.
-   **method**: Compression method (e.g., "gzip", "quantization_8bit", "wavelet_90").
-   **level**: Compression level or quality parameter (int/float).
-   **original_size**: File size in bytes (int).
-   **compressed_size**: File size in bytes (int).
-   **mse**: Mean Squared Error (float).
-   **snr_degradation**: SNR loss in dB (float).
-   **file_path**: Path to the compressed file.

### 2.3 ParameterPosterior
Represents the posterior distribution from PE.
-   **posterior_id**: Unique identifier (string).
-   **source_injection_id**: Reference to SyntheticInjection.
-   **source_artifact_id**: Reference to CompressionArtifact (or "original").
-   **parameter_type**: Type of parameter (e.g., "mass1", "distance", "chi_eff").
-   **true_parameter_value**: The known ground truth value for this parameter (float).
-   **samples**: Array of posterior samples (float32/float64).
-   **credible_interval_90**: Tuple (lower, upper) (float).
-   **bias_estimate**: Absolute difference `|Posterior_Mean - True_Parameter_Value|` (float).
-   **convergence_status**: String ("Converged", "Inconclusive", "Failed").

## 3. Data Flow

1.  **Injection**: `SyntheticInjection` created from `LALSimulation` + GWOSC noise.
2.  **Compression**: `CompressionArtifact` created from `SyntheticInjection` + method.
3.  **PE**: `ParameterPosterior` created from `CompressionArtifact` (or original) via `Bilby`/`Dynesty`.
4.  **Analysis**: Aggregation of `ParameterPosterior` to compute `Delta_Bias`.

## 4. Storage Layout

```text
data/
├── raw/
│   └── gwosc_noise/
│       └── ...
├── interim/
│   ├── injections/
│   │   └── injection_001.h5
│   └── compressed/
│       └── injection_001_gzip_l9.h5
└── processed/
    └── posteriors/
        ├── injection_001_original.h5
        └── injection_001_compressed.h5
```