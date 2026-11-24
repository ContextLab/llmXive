# Data Model: Quantizing GW Signals

## 1. Overview
Defines canonical data structures stored as HDF5 (large arrays) and JSON (metadata, results). All files are validated against the JSON‑Schema contracts in `contracts/`. Validation steps are explicitly performed after generation and after inference (see `src/utils.py`).

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
| `bit_depth` | integer | 0 for baseline (float64) or 1‑16 for quantized signals |
| `fsr` | number | Fixed full‑scale range used for quantization |
| `step_size` | number | Quantization step size (derived from FSR and bit depth) |
| `data_type` | string | `"float64"` for baseline, `"quantized"` for quantized signals |
| `data_quantized` | int16/int32 array (optional) | Quantized strain (present only for bit depths > 0) |

### 2.2 ParameterEstimationResult
| Field | Type | Description |
|-------|------|-------------|
| `waveform_id` | string | Links to the source waveform |
| `bit_depth` | integer | null for float64 baseline |
| `inference_method` | string | `"MCMC"` (uniform MCMC across all SNR ranges) |
| `mean_params` | object | Posterior means for `chirp_mass`, `spin`, `distance` |
| `mse` | object | Per‑parameter MSE vs. truth (`chirp_mass`, `spin`, `distance`) |
| `convergence_status` | string | `"success"`, `"failed"`, or `"non-detection"` |
| `snr` | number | Injected Signal‑to‑Noise Ratio |
| `delta` | object | Per‑parameter Δₖ = E_quant,ₖ − E_inst,ₖ (null for baseline) |
| `data_type` | string | `"float64"` for baseline results, `"quantized"` for quantized results |

## 3. Storage Schema

### 3.1 HDF5 (`data/processed/waveforms.h5`)
```
/
├── waveforms/
│   └── {waveform_id}/
│       ├── params            (JSON‑encoded attribute)
│       ├── data_float64      (dataset)
│       └── metadata          (attributes: snr, sampling_rate, duration, data_type)
└── quantized/
    └── {waveform_id}_{bit_depth}bit/
        ├── data_quantized    (dataset)
        └── metadata          (attributes: step_size, fsr, bit_depth, data_type)
```

### 3.2 JSON (`data/results/inference_results.json`)
Array of objects conforming to `contracts/result.schema.yaml`. Each entry contains:
- Baseline result (`bit_depth: null`) and quantized result (`bit_depth = N`).
- Per‑parameter MSE and Δₖ.
- Convergence status and SNR.

All transformations produce new files; original raw PSD and generated waveforms remain unchanged, satisfying the Data Hygiene principle.

---
