# Quickstart Guide: Alpha Oscillations and Working Memory Capacity

This guide provides step-by-step instructions to run the full analysis pipeline for investigating the relationship between alpha oscillations and working memory capacity using the ds000248 dataset.

## Prerequisites

- Python 3.9+
- pip
- At least 20GB of free disk space (for raw and processed EEG data)
- 16GB+ RAM recommended for full dataset processing

## Setup

1. **Clone the repository**
 ```bash
 git clone <repository-url>
 cd PROJ-335-investigating-the-relationship-between-a
 ```

2. **Install dependencies**
 ```bash
 pip install -r code/requirements.txt
 ```

3. **Configure the environment**
 The project uses `code/config.yaml` for parameters. Verify or edit settings:
 ```bash
 cat code/config.yaml
 ```
 Key settings include:
 - `dataset_id`: OpenNeuro dataset identifier (default: ds000248)
 - `alpha_band`: Frequency range for alpha power analysis (default: 8-13 Hz)
 - `filter_band`: Bandpass filter range (default: 1-40 Hz)
 - `random_seed`: Reproducibility seed

## Execution Pipeline

Run the following scripts in order. Each script produces outputs required by the next stage.

### Step 1: Download and Preprocess EEG Data
Fetches ds000248 from OpenNeuro, applies bandpass filtering (1-40 Hz), performs ICA artifact removal, and extracts behavioral scores.
```bash
python code/01_download_preprocess.py
```
**Outputs:**
- `data/raw/`: Raw BIDS dataset
- `data/processed/`: Cleaned, epoched data (HDF5/NPZ)
- `data/results/power_status.json`: Power analysis results

### Step 2: Extract Metrics
Computes alpha-band power from frontal/parietal electrodes and Phase Locking Values (PLV) between frontal-parietal pairs.
```bash
python code/02_extract_metrics.py
```
**Outputs:**
- `data/metrics/alpha_power.csv`: Alpha power per subject
- `data/metrics/plv.csv`: PLV metrics per subject

### Step 3: Correlation Analysis
Performs VIF checks, partial correlations, FDR correction, LOSO cross-validation, and split-half reliability analysis.
```bash
python code/03_correlation_analysis.py
```
**Outputs:**
- `data/results/correlation_results.json`: Statistical findings
- `data/results/robustness_metrics.json`: Reliability scores

### Step 4: Threshold Evaluation
Evaluates results against significance thresholds (|r| ≥ 0.3, reliability ≥ 0.7).
```bash
python code/04_threshold_analysis.py
```
**Outputs:**
- `data/results/threshold_results.json`: Pass/Fail status

### Step 5: Generate Report
Compiles all findings into a final markdown report.
```bash
python code/05_generate_report.py
```
**Outputs:**
- `data/results/analysis_report.md`: Final analysis summary

## Validation

To verify the pipeline integrity:

1. **Check log files** for errors:
 ```bash
 tail -f data/results/*.log
 ```

2. **Run unit tests** (if available):
 ```bash
 pytest tests/unit/ -v
 ```

3. **Verify output files exist**:
 ```bash
 ls -lh data/processed/*.npz
 ls -lh data/metrics/*.csv
 ls -lh data/results/*.json
 ```

## Troubleshooting

- **Missing Behavioral Measures**: If the pipeline halts with "ERROR: Missing behavioral measures", ensure the dataset contains the required columns (k-scores/d') in the events file.
- **Insufficient Power**: If N < 30, the pipeline will halt with "INSUFFICIENT POWER".
- **Memory Errors**: Reduce `batch_size` in `code/config.yaml` or use a subset of subjects.
- **Network Issues**: The download step requires access to OpenNeuro (s3). Ensure no firewall blocks S3 traffic.

## Notes

- This pipeline is designed for the ds000248 dataset. Modifying `dataset_id` in `config.yaml` requires manual validation of BIDS structure compatibility.
- All statistical claims are associational; causal inference is not supported.