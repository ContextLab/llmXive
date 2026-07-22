# Data Model: The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## 1. Overview
This document defines the data structures used in the project. All data flows from raw datasets to processed features, then to analysis results, and finally to the output schema.

## 2. Raw Data Sources

### 2.1 OpenNeuro MEG/EEG
- **Source**: `
- **Format**: Parquet (streamed)
- **Key Fields**: `trial_id`, `timestamp`, `sensor_data`, `condition`
- **Processing**: Filtered to a mid-frequency band; phase extracted.

### 2.2 CLUTRR Benchmark
- **Source**: `
- **Format**: Parquet
- **Key Fields**: `story`, `question`, `answer`, `family_size`
- **Processing**: Sampled to a representative set of examples; split by seed.

### 2.3 PLV Reference
- **Source**: `
- **Format**: JSON
- **Key Fields**: `signal`, `phase`, `frequency`
- **Processing**: Used for validation of PLV calculation.

## 3. Intermediate Data Structures

### 3.1 ActivationTimeSeries
- **Description**: Raw output of attention heads during forward pass.
- **Shape**: `(batch_size, num_layers, num_heads, seq_len)`
- **Type**: `numpy.ndarray` (float32)
- **Storage**: Temporary in-memory; written to disk as `.npy` if needed.

### 3.2 SpectralFeatures
- **Description**: Power Spectral Density (PSD) and Phase Locking Value (PLV) for each activation time-series.
- **Fields**:
 - `frequency_band`: str (e.g., "30-50Hz")
 - `psd`: array (power values)
 - `plv`: float (phase locking value)
 - `snr`: float (signal-to-noise ratio)
- **Storage**: `data/processed/spectral_features_{seed}.json`

### 3.3 BenchmarkResult
- **Description**: Performance metrics for CLUTRR/bAbI.
- **Fields**:
 - `accuracy`: float
 - `f1_score`: float
 - `seed`: int
- **Storage**: `data/processed/benchmark_result_{seed}.json`

## 4. Output Schema

### 4.1 Final Results
- **Description**: Aggregated results for all seeds and frequencies.
- **Fields**:
 - `frequency`: int (Hz)
 - `mean_snr`: float
 - `mean_plv`: float
 - `p_value`: float (corrected)
 - `significance`: bool
- **Storage**: `data/final/results_summary.json`

### 4.2 Statistical Report
- **Description**: Detailed statistical analysis including permutation test results.
- **Fields**:
 - `null_distribution`: array (permutation results)
 - `observed_value`: float
 - `p_value`: float
 - `correction_method`: str (e.g., "bonferroni")
- **Storage**: `data/final/statistical_report.json`

## 5. Data Hygiene & Versioning

- **Checksums**: All raw data files will be checksummed (SHA256) and recorded in `state/...yaml`.
- **Derivations**: No raw data is modified in place. All transformations produce new files.
- **PII**: No PII is present in the datasets (anonymized MEG, synthetic CLUTRR).
