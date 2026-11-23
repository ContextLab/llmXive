# Data Model Documentation

This document describes the core data structures, file formats, and artifact definitions used in the `PROJ-465` project. It aligns with the `data-model.md` requirements and the implementation in `code/data/models.py`.

## 1. Core Entities

The project uses the following dataclasses defined in `code/data/models.py`:

### 1.1 `StrainEvent`

Represents a gravitational wave event and its raw strain data.

```python
@dataclass
class StrainEvent:
 event_id: str
 gwosc_id: str
 start_time: float
 end_time: float
 snr: float
 data_path: Path
 metadata: Dict[str, Any]
```

- **`event_id`**: Unique identifier for the event (e.g., "GW150914").
- **`gwosc_id`**: ID used by the GWOSC API.
- **`snr`**: Signal-to-Noise Ratio, fetched from the GWOSC catalog.
- **`data_path`**: Path to the raw strain data file (`.hdf5` or `.txt`).

### 1.2 `ResolutionConfig`

Defines a specific downsampling and quantization configuration.

```python
@dataclass
class ResolutionConfig:
 sampling_rate: int # e.g., 4096, 2048, 1024
 bit_depth: int # e.g., 16, 32
 downsample_factor: int
 quantization_type: str # "float16", "float32"
```

- **`sampling_rate`**: Target sampling rate in Hz.
- **`bit_depth`**: Simulated storage bit depth.
- **`downsample_factor`**: Ratio of original rate to target rate.

### 1.3 `PosteriorDistribution`

Represents the output of the Bayesian inference step.

```python
@dataclass
class PosteriorDistribution:
 event_id: str
 resolution_config: ResolutionConfig
 samples: np.ndarray # Shape: (n_samples, n_parameters)
 parameters: List[str]
 metadata: Dict[str, Any]
 is_inconclusive: bool
 posterior_width_ratio: float # Posterior width / Prior width
```

- **`is_inconclusive`**: `True` if the `dynesty` sampler failed to converge (`dlogz > 0.1`).
- **`posterior_width_ratio`**: Used to filter out events where the posterior is > 50% of the prior width.

### 1.4 `BiasMetric`

Stores the calculated bias and divergence metrics for a specific resolution.

```python
@dataclass
class BiasMetric:
 event_id: str
 resolution_config: ResolutionConfig
 hellinger_distance: float
 mass_bias: float
 spin_bias: float
 catalog_ci_90: float
 exceeds_ci: bool
 is_inconclusive: bool
```

- **`exceeds_ci`**: `True` if the bias magnitude exceeds the catalog-reported 90% confidence interval.
- **`catalog_ci_90`**: The 90% CI width scaled from catalog uncertainties (1σ * 1.645).

## 2. File Formats

### 2.1 Strain Data (`data/raw/`)

- **Format**: HDF5 (`.hdf5`) or plain text (`.txt`).
- **Content**: Time series of strain data with metadata.
- **Checksum**: A `.sha256` file is generated for each raw data file to ensure integrity.

### 2.2 Derived Data (`data/derived/`)

- **Format**: HDF5 (`.hdf5`).
- **Content**: Downsampled and quantized strain data.
- **Structure**:
 ```
 data/derived/
 └── <event_id>/
 ├── 4096Hz_float32.hdf5
 ├── 2048Hz_float16.hdf5
 └──...
 ```

### 2.3 Posterior Files (`results/posteriors/`)

- **Format**: JSON (`.json`).
- **Content**: Posterior samples, parameter names, and metadata.
- **Example**:
 ```json
 {
 "event_id": "GW150914",
 "resolution": {
 "sampling_rate": 2048,
 "bit_depth": 32
 },
 "samples": [[...], [...],...],
 "parameters": ["mass_1", "mass_2", "chi_eff",...],
 "metadata": {
 "is_inconclusive": false,
 "posterior_width_ratio": 0.35,
 "convergence_dlogz": 0.05
 }
 }
 ```

### 2.4 Metrics Files (`results/metrics/`)

- **Format**: CSV (`.csv`) and JSON (`.json`).
- **CSV Content**:
 - `event_id`, `sampling_rate`, `bit_depth`, `hellinger_distance`, `mass_bias`, `spin_bias`, `catalog_ci_90`, `exceeds_ci`, `is_inconclusive`.
- **JSON Content**: Aggregation reports and summary tables.

## 3. Artifact Integrity

All generated artifacts are checksummed using SHA-256. The `code/utils/hash_artifact.py` module provides utilities to:
- Compute hashes for files and strings.
- Save and load hash manifests.
- Verify artifact integrity against stored hashes.

**Manifest Format**:
```json
{
 "version": "1.0",
 "artifacts": {
 "GW150914_2048Hz_float16.hdf5": "sha256:abc123...",
 "GW150914_metrics.csv": "sha256:def456..."
 }
}
```

## 4. Logging and Derivation

Derivation parameters (e.g., downsampling factor, quantization type) are logged using the `DerivationAdapter` in `code/utils/logging_config.py`. Logs are stored in `logs/` and include:
- Timestamp
- Event ID
- Resolution configuration
- Any warnings (e.g., missing segments, convergence failures)

## 5. Conventions

- **Paths**: All paths are relative to the project root.
- **Units**: Sampling rates in Hz, masses in solar masses, spins dimensionless.
- **Confidence Intervals**: 90% CI is calculated as 1σ * 1.645 (standard normality assumption).
- **Inconclusive Handling**: Events flagged "inconclusive" are excluded from the denominator in majority-rule calculations but counted as "bias exceeded" in threshold analysis.

## 6. References

- **Spec**: `specs/001-quantify-gw-resolution-impact/spec.md`
- **Plan**: `plan.md`
- **Code**: `code/data/models.py`, `code/analysis/metrics.py`, `code/analysis/aggregate.py`