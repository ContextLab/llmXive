# Quickstart: Alpha Oscillations and Working Memory Capacity

## Prerequisites

- Python 3.11+
- Git
- 14 GB free disk space (for dataset download and processing)
- 8 GB RAM minimum (recommended to stay under 7 GB safety margin)

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins `mne`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `statsmodels` to CPU-compatible versions.*

## Running the Pipeline

The pipeline is executed sequentially via three main scripts.

### Step 1: Download and Preprocess
```bash
python code/01_download_preprocess.py --dataset ds000248 --output data/processed
```
- **Action**: Downloads `ds000248` from OpenNeuro, applies 1-40 Hz filter, ICA, and epoching.
- **Validation**: Checks for k-scores/d'. If missing, exits with code 1.
- **Output**: `data/processed/epochs.h5`

### Step 2: Extract Metrics
```bash
python code/02_extract_metrics.py --input data/processed/epochs.h5 --output data/metrics
```
- **Action**: Computes Alpha Power (8-12 Hz) and PLV for frontal-parietal pairs.
- **Output**: `data/metrics/alpha_power.csv`, `data/metrics/plv.csv`

### Step 3: Correlation Analysis
```bash
python code/03_correlation_analysis.py --power data/metrics/alpha_power.csv --plv data/metrics/plv.csv --output data/results
```
- **Action**: Computes partial correlations, VIF checks, PCA (if needed, descriptive only), and FDR correction.
- **Output**: `data/results/correlations.json`, `data/results/reliability.csv`

## Verification

To verify the pipeline:
1. Check `data/results/correlations.json` for `corrected_p` values and `threshold_status`. The `threshold_status` field must be "PASS" if |r| ≥ 0.3, otherwise "FAIL".
2. Ensure `split_half_reliability` in `reliability.csv` is ≥ 0.7. If < 0.7, a warning is logged and `reliability_status` is set to "LOW".
3. Run `pytest tests/` to confirm all unit and integration tests pass.

## Troubleshooting

- **Memory Error**: Reduce the number of trials in `config.yaml` (set `max_trials_per_condition=50`).
- **Missing Behavioral Data**: The script will halt. Verify the dataset ID in `config.yaml` or switch to `ds003474`.
- **Collinearity Warning**: If VIF > 5, the script will automatically run PCA and report component correlations instead of raw metrics.
- **Power Warning**: If N < 30, the script will halt with "INSUFFICIENT POWER".