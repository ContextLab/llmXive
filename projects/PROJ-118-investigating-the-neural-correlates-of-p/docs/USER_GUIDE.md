# User Guide: Investigating Neural Correlates of Predictive Coding Errors

This guide walks you through using the pipeline to analyze auditory oddball EEG data.

## Step 1: Environment Setup

Ensure you have Python 3.11+ installed.

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Data Download

The pipeline uses the `ds003645` dataset from OpenNeuro.

```bash
python code/download.py
```

**Expected Output:**
- Raw data files in `data/raw/`.
- A log file confirming checksum verification.

**Troubleshooting:**
- If the download fails, check your internet connection and ensure the OpenNeuro URL is correct.
- If you have a private dataset, set `OPENNEURO_API_KEY` in your environment.

## Step 3: Preprocessing

Run the preprocessing pipeline to clean the data.

```bash
python code/preprocess.py
```

**What happens:**
1. Data is subsampled to 32 channels.
2. Bandpass filter (1-30Hz) is applied.
3. ICA removes blink artifacts.
4. Trials with excessive noise are rejected.

**Output:**
- `data/processed/epo_clean.fif` (Cleaned epochs).
- `data/processed/rejected_participants.log` (List of excluded subjects).

**Note:** This step may take 10-30 minutes depending on the number of subjects.

## Step 4: Metric Extraction

Extract MMN amplitude and latency metrics.

```bash
python code/extract.py
```

**Output:**
- `results/metrics.csv` containing:
 - `participant_id`
 - `standard_amplitude`, `deviant_amplitude`
 - `peak_detected` (True/False)
 - `snr`

## Step 5: Statistical Analysis

Perform statistical tests on the extracted metrics.

```bash
python code/stats.py
```

**Output:**
- `results/statistics.json` with p-values, effect sizes, and cluster results.

## Step 6: Visualization

Generate plots of the results.

```bash
python code/viz.py
```

**Output:**
- `results/plots/erp_plot.png`
- `results/plots/topomap.png`

## Interpreting Results

- **Significant MMN:** Look for a negative peak in the difference wave (Deviant - Standard) between 150-250ms.
- **Statistical Significance:** Check `results/statistics.json` for p-values < 0.05 (FDR corrected).
- **Effect Size:** Cohen's d > 0.5 indicates a meaningful effect.

## Configuration

You can modify pipeline parameters in `code/config.yaml`:
- `filter_range`: Frequency range for bandpass filtering.
- `epoch_tmin`, `epoch_tmax`: Time window for epoching.
- `ica_threshold`: Threshold for ICA component rejection.

## Support

For issues, check the logs in `code/logs/` or refer to the `ARCHITECTURE.md` for system details.