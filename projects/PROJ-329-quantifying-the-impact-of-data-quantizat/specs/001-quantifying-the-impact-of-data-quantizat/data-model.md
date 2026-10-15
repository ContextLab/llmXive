# Data Model: Quantizing GW Signals

## 1. Overview
Defines the canonical data structures stored as HDF5 (large arrays) and JSON (metadata, results). All schemas are validated against the contracts in `contracts/`.

## 2. Entity Definitions

### 2.1 SimulatedWaveform
| Field | Type | Description |
|-------|------|-------------|
| `waveform_id` | string (UUID) | Unique identifier |
| `params` | object | `mass_1`, `mass_2`, `spin_1z`, `spin_2z`, `luminosity_distance` (see schema) |
| `snr` | number | Injected SNR |
| `sampling_rate` | number | Hz |
| `duration` | number | seconds |
| `data_float64` | float64 array | Strain time series (baseline, float64 precision) |

### 2.2 QuantizedSignal
| Field | Type | Description |
|-------|------|-------------|
| `waveform_id` | string | Links to SimulatedWaveform |
| `bit_depth` | integer | 1, 8, 10, 12, 14, 16 |
| `quantization_levels` | integer | \(2^{\text{bit\_depth}}\) |
| `data_quantized` | int16/int32 array | Discretized strain |
| `step_size` | number | Amplitude resolution (FSR / \(2^{N-1}\)) |
| `fsr` | number | Fixed full‑scale range used |

### 2.3 ParameterEstimationResult
| Field | Type | Description |
|-------|------|-------------|
| `waveform_id` | string | Source waveform |
| `bit_depth` | integer | Quantization depth (or null for float64 baseline) |
| `inference_method` | string | `"MCMC"` (uniform across all SNR ranges) |
| `mean_params` | object | Posterior means for `chirp_mass`, `spin`, `distance` |
| `mse` | object | MSE per parameter vs truth (computed separately for each) |
| `convergence_status` | string | `"success"`, `"failed"`, `"non-detection"` |
| `snr` | number | Injected SNR (copied from SimulatedWaveform) |
| `delta` | object | Per-parameter Δ_k = E_quant,k − E_inst,k (computed using float64 baseline for same waveform) |

## 3. Storage Schema

### 3.1 HDF5 (`data/processed/waveforms.h5`)
```
/
├── waveforms/
│   └── {waveform_id}/
│       ├── params            (dataset, JSON‑encoded)
│       ├── data_float64      (dataset)
│       └── metadata          (attributes: snr, sampling_rate, duration)
└── quantized/
    └── {waveform_id}_{bit_depth}bit/
        ├── data_quantized    (dataset)
        └── metadata          (attributes: step_size, fsr, bit_depth)
```

### 3.2 JSON (`data/results/inference_results.json`)
Array of `ParameterEstimationResult` objects (conforms to `contracts/result.schema.yaml`). Each result includes:
- Inference results for the quantized signal
- Inference results for the float64 baseline (same waveform, bit_depth=null)
- Per-parameter MSE for both quantized and baseline
- Per-parameter Δ_k computed as E_quant,k − E_inst,k (using the baseline result for the same waveform)

## 4. Data Flow
1. **Generation** (`data_generation.py`) → writes SimulatedWaveform (float64) & QuantizedSignal to HDF5 for all 6 bit depths.  
2. **Checksumming** (`utils.compute_checksums`) → records SHA‑256 in `state/projects/PROJ-329-quantifying-the-impact-of-data-quantizat.yaml`.  
3. **Inference** (`inference_engine.py`) → reads quantized datasets and float64 baseline, runs MCMC on both, writes JSON results with per-parameter MSE and Δ_k.  
4. **Analysis** (`analysis.py`) → reads JSON, aggregates Δ_k within SNR bins using median, fits curves, identifies crossover SNR, outputs plots & summary CSV with confidence intervals from multiple runs.

---