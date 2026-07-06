# Data Model: Quantizing GW Signals

## 1. Overview
This document defines the data structures for the gravitational wave quantization study. All data is stored in HDF5 (for large arrays) and JSON (for metadata/results) to ensure compatibility with PyCBC/Bilby and efficient I/O on the CI runner.

## 2. Entity Definitions

### 2.1 SimulatedWaveform
Represents the ground-truth signal before quantization.
- **Attributes**:
  - `waveform_id`: Unique string identifier (UUID).
  - `params`: Dict containing `mass_1`, `mass_2`, `spin_1z`, `spin_2z`, `luminosity_distance`, `redshift`, `injection_time`.
  - `snr`: Signal-to-Noise Ratio of the injected signal.
  - `sampling_rate`: Float (Hz).
  - `duration`: Float (seconds).
  - `data_float64`: Float64 array (strain time series).

### 2.2 QuantizedSignal
Represents the signal after bit-depth reduction.
- **Attributes**:
  - `waveform_id`: Links to `SimulatedWaveform`.
  - `bit_depth`: Integer (1, 8, 10, 12, 14, 16).
  - `quantization_levels`: Integer ($2^{bit\_depth}$).
  - `data_quantized`: Int16 or Int32 array (discretized strain).
  - `step_size`: Float (amplitude resolution).

### 2.3 ParameterEstimationResult
Represents the output of the inference engine.
- **Attributes**:
  - `waveform_id`: Links to source.
  - `bit_depth`: Integer.
  - `inference_method`: String ("MCMC", "Fisher", "Hybrid").
  - `posteriors`: Dict of parameter names -> array of samples.
  - `mean_params`: Dict of parameter names -> float (mean of posterior).
  - `mse`: Dict of parameter names -> float (MSE vs truth).
  - `convergence_status`: String ("success", "failed", "non-detection").

## 3. Storage Schema

### 3.1 HDF5 Structure (`data/processed/waveforms.h5`)
```text
/
├── waveforms/
│   ├── {waveform_id}/
│   │   ├── params (dataset)
│   │   ├── data_float64 (dataset)
│   │   └── metadata (attributes: snr, injection_time)
│   └── ...
└── quantized/
    ├── {waveform_id}_8bit/
    │   ├── data_quantized (dataset)
    │   └── metadata (attributes: bit_depth, step_size)
    └── ...
```

### 3.2 JSON Structure (`data/results/inference_results.json`)
Array of `ParameterEstimationResult` objects.
```json
[
  {
    "waveform_id": "uuid-1234",
    "bit_depth": 8,
    "inference_method": "MCMC",
    "mean_params": { "chirp_mass": 25.4, "distance": 450.2 },
    "mse": { "chirp_mass": 0.01, "distance": 0.05 },
    "convergence_status": "success"
  }
]
```

## 4. Data Flow
1. **Generation**: `data_generation.py` writes `SimulatedWaveform` to HDF5.
2. **Quantization**: `data_generation.py` reads float64, writes `QuantizedSignal` to HDF5.
3. **Inference**: `inference_engine.py` reads quantized data, writes `ParameterEstimationResult` to JSON.
4. **Analysis**: `analysis.py` reads JSON, computes thresholds, generates plots.
