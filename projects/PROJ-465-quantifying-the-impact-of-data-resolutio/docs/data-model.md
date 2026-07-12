# Data Model Specification

This document defines the core data structures used in the `quantifying-the-impact-of-data-resolution` pipeline.

## Core Entities

The project uses the following dataclasses defined in `code/data/models.py`.

### 1. StrainEvent

Represents a gravitational wave event detected by LIGO/Virgo.

```python
@dataclass
class StrainEvent:
 event_id: str
 gw_osc_id: str
 snr: float
 start_time: float
 end_time: float
 detector: str
 raw_file_path: Path
```

- **event_id**: Unique identifier for the event within this project (e.g., "GW150914").
- **snr**: Signal-to-Noise Ratio. Must be >= 20 for inclusion.
- **raw_file_path**: Path to the downloaded raw strain data file.

### 2. ResolutionConfig

Defines a specific downsampling and quantization configuration.

```python
@dataclass
class ResolutionConfig:
 sample_rate: int # e.g., 4096, 2048, 1024 Hz
 bit_depth: int # e.g., 16, 32
 label: str # Human-readable label (e.g., "2048Hz_16bit")
```

### 3. PosteriorDistribution

Represents the output of a `bilby` inference run.

```python
@dataclass
class PosteriorDistribution:
 event_id: str
 resolution_config: ResolutionConfig
 file_path: Path
 is_inconclusive: bool
 convergence_dlogz: float
 max_iterations: int
 parameters: Dict[str, np.ndarray] # Sampled parameters (mass, spin, etc.)
```

- **is_inconclusive**: True if `dlogz > 0.1` after `max_iterations`.
- **parameters**: Dictionary of parameter names to sample arrays.

### 4. BiasMetric

Represents the calculated bias and divergence for a specific resolution.

```python
@dataclass
class BiasMetric:
 event_id: str
 resolution_config: ResolutionConfig
 hellinger_distance: float
 mass_bias_percent: float
 spin_bias_percent: float
 exceeds_uncertainty: bool
 baseline_90_ci_width: float
```

- **hellinger_distance**: Distance between the downsampled posterior and the baseline posterior.
- **exceeds_uncertainty**: True if the bias exceeds the catalog-reported 90% CI.

## Data Flow

1. **Raw**: `StrainEvent` objects are created from GWOSC downloads.
2. **Derived**: `ResolutionConfig` is applied to `StrainEvent` to create derived strain files.
3. **Inference**: `PosteriorDistribution` is generated from derived strain using `bilby`.
4. **Metrics**: `BiasMetric` is calculated by comparing `PosteriorDistribution` instances.

## File Formats

- **Strain Data**: HDF5 format (`.hdf5`) containing time series data.
- **Posteriors**: HDF5 format (`.hdf5`) containing samples and metadata.
- **Metrics**: JSON format (`.json`) containing aggregated results.
- **Logs**: Text format (`.log`) containing derivation and execution logs.

## Versioning

All derived artifacts include a hash of their input parameters and raw data checksums in their metadata to ensure reproducibility (Constitution V).
