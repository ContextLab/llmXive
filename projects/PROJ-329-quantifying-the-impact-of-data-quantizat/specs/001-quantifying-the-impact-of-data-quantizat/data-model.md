# Data Model: Quantizing GW Signals

## 1. Overview
Defines canonical data structures stored as HDF5 (large arrays) and JSON (metadata, results). All files are validated against the JSON‑Schema contracts in `contracts/`.

## 2. Entity Definitions

### 2.1 SimulatedWaveform
| Field | Type | Description |
|-------|------|-------------|
| `waveform_id` | string (UUID) | Unique identifier |
| `params` | object | `mass_1`, `mass_2`, `spin_1z`, `spin_2z`, `luminosity_distance` |
| `snr` | number | Injected SNR |
| `sampling_rate` | number | Hz |
| `duration` | number | Seconds |
| `data_float64` | float64 array | Strain time series (baseline) |
| `bit_depth` | integer | 0 for baseline (float64) |
| `fsr` | number | Fixed full‑scale range used for quantization |
| `step_size` | number | Quantization step size (derived from FSR and bit depth) |
| `data_quantized` | int16/int32 array (optional) | Quantized strain (present only for bit depths > 0) |

### 2.2 ParameterEstimationResult
| Field | Type | Description |
|-------|------|-------------|
| `waveform_id` | string | Links to the source waveform |
| `bit_depth` | integer | null for float64 baseline |
| `inference_method` | string | `"MCMC"` (uniform across all SNR ranges) |
| `mean_params` | object | Posterior means for `chirp_mass`, `spin`, `distance` |
| `mse` | object | Per‑parameter MSE vs. truth (`chirp_mass`, `spin`, `distance`) |
| `convergence_status` | string | `"success"`, `"failed"`, or `"non-detection"` |
| `snr` | number | Injected SNR |
| `delta` | object | Per‑parameter Δₖ = E_quant,ₖ − E_inst,ₖ (null for baseline) |

## 3. Storage Schema

### 3.1 HDF5 (`data/processed/waveforms.h5`)
```
/
├── waveforms/
│   └── {waveform_id}/
│       ├── params            (JSON‑encoded attribute)
│       ├── data_float64      (dataset)
│       └── metadata          (attributes: snr, sampling_rate, duration)
└── quantized/
    └── {waveform_id}_{bit_depth}bit/
        ├── data_quantized    (dataset)
        └── metadata          (attributes: step_size, fsr, bit_depth)
```

### 3.2 JSON (`data/results/inference_results.json`)
Array of objects conforming to `contracts/result.schema.yaml`. Each entry contains:
- Baseline result (`bit_depth: null`) and quantized result (`bit_depth = N`).
- Per‑parameter MSE and Δₖ.
- Convergence status and SNR.

## 4. Data Flow
1. **Generation** (`src/data_generation.py`) → writes float64 baseline and all quantized groups to HDF5.  
2. **Checksumming** (`src/utils.compute_checksums`) → records SHA‑256 hashes in `state/projects/PROJ-329-quantizing-the-impact-of-data-quantizat.yaml`.  
3. **Inference** (`src/inference_engine.py`) → reads each dataset, runs Bilby MCMC, writes JSON results with MSE and Δₖ.  
4. **Analysis** (`src/analysis.py`) → aggregates Δₖ within SNR bins, fits curves, identifies crossover SNR, outputs plots and a CSV summary with 95 % CI from the 10‑run reproducibility study.

---
