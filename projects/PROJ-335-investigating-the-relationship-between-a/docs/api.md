# API Documentation: EEG Alpha Oscillations and Working Memory Pipeline

This document describes the command-line interface and parameters for each script in the `code/` directory.

## Common Parameters

Most scripts accept the following common arguments:

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--config` | `-c` | `code/config.yaml` | Path to the YAML configuration file |
| `--verbose` | `-v` | `False` | Enable verbose logging (DEBUG level) |
| `--quiet` | `-q` | `False` | Suppress all output except errors |
| `--output-dir` | `-o` | `data/results` | Directory for output files |

---

## 00_setup_bids.py

**Purpose**: Initialize BIDS-compliant directory structure for the EEG dataset.

**Usage**:
```bash
python code/00_setup_bids.py [--config CONFIG] [--output-dir DIR]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml` containing dataset metadata.
- `--output-dir` (str): Base directory for BIDS structure (default: `data/raw`).

**Outputs**:
- `data/raw/dataset_description.json`: BIDS dataset descriptor.
- `data/raw/participants.tsv`: Participant metadata.
- `data/raw/sub-*/ses-*/`: Subject/session directories.

---

## 01_download_preprocess.py

**Purpose**: Download ds000248 from OpenNeuro, preprocess (filter, ICA, epoch), and extract behavioral scores.

**Usage**:
```bash
python code/01_download_preprocess.py [--config CONFIG] [--force-download]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml`.
- `--force-download`: Re-download dataset even if it exists locally.
- `--no-ica`: Skip ICA artifact removal.
- `--no-filter`: Skip bandpass filtering (1-40 Hz).
- `--epochs-tmin` (float): Start time for epochs (default: -0.2).
- `--epochs-tmax` (float): End time for epochs (default: 0.8).
- `--baseline` (str): Baseline period (e.g., "-0.2,0" or "None").

**Outputs**:
- `data/raw/ds000248/`: Raw downloaded dataset.
- `data/processed/subject-*/epochs.fif`: Preprocessed epochs.
- `data/processed/subject-*/behavioral.csv`: Extracted k-scores/d'.

**Dependencies**: `mne`, `openneuro-py`, `pandas`.

---

## 01_save_epochs.py

**Purpose**: Save preprocessed epochs to HDF5 or NPZ format.

**Usage**:
```bash
python code/01_save_epochs.py [--config CONFIG] [--format {hdf5,npz}]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml`.
- `--format` (str): Output format (`hdf5` or `npz`).
- `--subjects` (str): Comma-separated list of subject IDs (e.g., "01,02,03").
- `--compress`: Enable compression for HDF5.

**Outputs**:
- `data/processed/subject-*/epochs.{hdf5,npz}`.

---

## 02_extract_metrics.py

**Purpose**: Extract alpha-band power and PLV metrics from preprocessed epochs.

**Usage**:
```bash
python code/02_extract_metrics.py [--config CONFIG] [--electrodes ELECTRODES]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml`.
- `--electrodes` (str): Comma-separated list of electrodes (e.g., "F3,F4,P3,P4").
- `--alpha-band` (str): Alpha frequency range (e.g., "8,13").
- `--plv-pairs` (str): Comma-separated electrode pairs (e.g., "F3-P3,F4-P4").
- `--delay-start` (float): Start of delay period (default: 0.0).
- `--delay-end` (float): End of delay period (default: 0.6).

**Outputs**:
- `data/metrics/alpha_power.csv`: Per-subject alpha power values.
- `data/metrics/plv.csv`: Per-subject PLV values for electrode pairs.

**Dependencies**: `mne`, `scipy`, `numpy`.

---

## 02_store_plv.py

**Purpose**: Store PLV metrics from JSON to CSV.

**Usage**:
```bash
python code/02_store_plv.py [--config CONFIG] [--input-json PATH]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml`.
- `--input-json` (str): Path to JSON file containing PLV metrics.
- `--output-csv` (str): Output CSV path (default: `data/metrics/plv.csv`).

**Outputs**:
- `data/metrics/plv.csv`.

---

## 03_correlation_analysis.py

**Purpose**: Perform correlation analysis, VIF, PCA, LOSO cross-validation, and split-half reliability.

**Usage**:
```bash
python code/03_correlation_analysis.py [--config CONFIG] [--fdr-method {bh,by}]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml`.
- `--fdr-method` (str): FDR correction method (`bh` or `by`).
- `--vif-threshold` (float): VIF threshold for collinearity (default: 5.0).
- `--pca-components` (int): Number of PCA components if VIF > threshold.
- `--alpha-power-file` (str): Path to alpha power CSV.
- `--plv-file` (str): Path to PLV CSV.
- `--wm-file` (str): Path to WM capacity CSV.
- `--random-seed` (int): Random seed for LOSO/split-half.

**Outputs**:
- `data/results/correlation_results.json`: Full correlation results.
- `data/results/loso_cv.json`: Leave-one-subject-out cross-validation results.
- `data/results/split_half_reliability.json`: Split-half reliability metrics.

**Dependencies**: `scikit-learn`, `statsmodels`, `pandas`.

---

## 04_threshold_analysis.py

**Purpose**: Evaluate correlation and reliability against predefined thresholds.

**Usage**:
```bash
python code/04_threshold_analysis.py [--config CONFIG] [--r-threshold R] [--reliability-threshold R]
```

**Parameters**:
- `--config` (str): Path to `code/config.yaml`.
- `--r-threshold` (float): Absolute correlation threshold (default: 0.3).
- `--reliability-threshold` (float): Reliability coefficient threshold (default: 0.7).
- `--input-results` (str): Path to correlation results JSON.

**Outputs**:
- `data/results/threshold_results.json`: Threshold evaluation status.

---

## utils/validation.py

**Purpose**: Validation utilities for datasets and metrics.

**Usage**:
```bash
python code/utils/validation.py --check-file PATH --required-columns COLS
```

**Parameters**:
- `--check-file` (str): File to validate.
- `--required-columns` (str): Comma-separated required columns.
- `--check-type` (str): Validation type (`eeg_channels`, `behavioral`, `metrics`).

**Outputs**:
- Exit code 0 on success, 1 on failure.
- Logs validation errors to `data/results/validation_errors.log`.

---

## config.yaml

**Purpose**: Central configuration file for all scripts.

**Location**: `code/config.yaml`

**Structure**:
```yaml
# Dataset
dataset_id: ds000248
bids_root: data/raw

# MNE Parameters
filter_band: [1, 40]
alpha_band: [8, 13]
reference: "average_mastoids"

# Epoching
epochs_tmin: -0.2
epochs_tmax: 0.8
baseline: [-0.2, 0]

# Electrodes
alpha_electrodes: [F3, F4, Fz, P3, P4, Pz]
plv_pairs:
 - [F3, P3]
 - [F4, P4]
 - [Fz, Pz]

# Analysis
vif_threshold: 5.0
fdr_method: bh
r_threshold: 0.3
reliability_threshold: 0.7

# Random seeds
random_seed: 42
```

---

## Logging Configuration

All scripts use the logging infrastructure from `code/utils/logging_config.py`.

**Log Output Locations**:
- Console: Standard output/error (INFO level by default).
- File: `data/results/pipeline_{timestamp}.log` (DEBUG level).

**Log Format**:
```
{timestamp} | {level} | {module} | {message}
```

**Environment Variables**:
- `LOG_LEVEL`: Override default log level (e.g., `DEBUG`, `INFO`, `WARNING`).
- `LOG_FILE`: Override default log file path.

---

## Error Codes

| Code | Description |
|------|-------------|
| FR-006 | Missing behavioral measures |
| FR-007 | Missing required electrodes |
| FR-008 | Insufficient power (N < 30) |
| FR-009 | Collinearity detected (VIF > 5) |

---

## Quick Reference

**Full Pipeline**:
```bash
python code/01_download_preprocess.py && \
python code/01_save_epochs.py && \
python code/02_extract_metrics.py && \
python code/03_correlation_analysis.py && \
python code/04_threshold_analysis.py
```

**Debug Mode**:
```bash
export LOG_LEVEL=DEBUG
python code/01_download_preprocess.py --verbose
```