# Pipeline Parameters Reference

This document defines all configurable parameters used in the cognitive fatigue prediction pipeline.
These parameters control data filtering, artifact rejection, feature extraction, and statistical analysis.

## Configuration File

All parameters are defined in `code/config.yaml`. The pipeline loads these values at startup.

```yaml
# code/config.yaml
pipeline:
 name: "cognitive-fatigue-resting-state"
 version: "1.0.0"

filtering:
 filter_low: 1 # Lower bound for bandpass filter (Hz)
 filter_high: 40 # Upper bound for bandpass filter (Hz)
 notch_freq: 50 # Line noise frequency (Hz)
 notch_width: 2 # Width of notch filter (Hz)

artifact_rejection:
 amplitude_threshold: 100 # Max amplitude in microvolts (µV)
 min_segment_length: 120 # Minimum segment length in seconds
 reject_channels: [] # List of channels to always reject (empty = auto-detect)

feature_extraction:
 lzc_binary_threshold: 0.5 # Threshold for binarization in LZC
 pe_embedding_dim: 3 # Embedding dimension for Permutation Entropy
 pe_time_delay: 1 # Time delay for Permutation Entropy
 chunk_size: 5000 # Number of samples per processing chunk (streaming)

analysis:
 correlation_method: "spearman" # "pearson" or "spearman"
 p_value_threshold: 0.05 # Significance threshold for uncorrected p-values
 fdr_method: "benjamini_hochberg" # Method for multiple comparison correction
 sensitivity_thresholds:
 - 0.01
 - 0.05
 - 0.10

paths:
 data_raw: "data/raw"
 data_processed: "data/processed"
 data_results: "data/results"
 logs: "logs"
 figures: "figures"
 reports: "docs"

random_seed: 42 # Global random seed for reproducibility
```

## Parameter Descriptions

### Filtering Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filter_low` | float | 1.0 | Lower cutoff frequency for bandpass filter. Removes slow drifts and DC offset. |
| `filter_high` | float | 40.0 | Upper cutoff frequency for bandpass filter. Removes high-frequency noise and muscle artifacts. |
| `notch_freq` | float | 50.0 | Frequency of the notch filter to remove line noise (50Hz in Europe, 60Hz in US). |
| `notch_width` | float | 2.0 | Width of the notch filter band in Hz. |

### Artifact Rejection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `amplitude_threshold` | float | 100.0 | Maximum allowed amplitude in microvolts. Epochs exceeding this are rejected. |
| `min_segment_length` | int | 120 | Minimum duration in seconds for a valid EEG segment. |
| `reject_channels` | list | [] | Manually specified channels to exclude. Leave empty for automatic detection. |

### Feature Extraction Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `lzc_binary_threshold` | float | 0.5 | Threshold for converting continuous EEG signals to binary sequences for LZC calculation. |
| `pe_embedding_dim` | int | 3 | Dimension of the embedding vector for Permutation Entropy. Higher values increase complexity. |
| `pe_time_delay` | int | 1 | Time delay between elements in the embedding vector for Permutation Entropy. |
| `chunk_size` | int | 5000 | Number of samples to process at once during streaming to manage memory usage. |

### Analysis Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `correlation_method` | string | "spearman" | Statistical method for correlation: "pearson" (linear) or "spearman" (monotonic). |
| `p_value_threshold` | float | 0.05 | Threshold for statistical significance before multiple comparison correction. |
| `fdr_method` | string | "benjamini_hochberg" | Method for False Discovery Rate correction across electrodes. |
| `sensitivity_thresholds` | list | [0.01, 0.05, 0.10] | List of p-value thresholds for sensitivity analysis. |

### Paths

All paths are relative to the project root (`projects/PROJ-470-predicting-cognitive-fatigue-from-restin/`).

| Parameter | Default | Description |
|-----------|---------|-------------|
| `data_raw` | "data/raw" | Directory for downloaded raw EEG data. |
| `data_processed` | "data/processed" | Directory for preprocessed data and intermediate metrics. |
| `data_results` | "data/results" | Directory for final analysis outputs (CSV, JSON, figures). |
| `logs` | "logs" | Directory for exclusion and rejection logs. |
| `figures` | "figures" | Directory for generated plots and visualizations. |
| `reports` | "docs" | Directory for final reports and documentation. |

### Reproducibility

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `random_seed` | int | 42 | Global seed for all random operations (numpy, pandas, mne). |
