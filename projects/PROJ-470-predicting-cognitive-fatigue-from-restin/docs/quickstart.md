# Quickstart Guide: Predicting Cognitive Fatigue from Resting-State EEG

This guide walks you through the complete pipeline for analyzing cognitive fatigue.

## 1. Environment Setup

Ensure you have Python 3.11+ installed.

```bash
# Create virtual environment
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Data Download

Fetch the public EEG dataset containing resting-state recordings and fatigue ratings.

```bash
python code/download.py --validate
```

This will:
- Download data to `data/raw/`
- Generate `data/raw/download_manifest.json`
- Create a sample file for testing

## 3. Preprocessing

Apply bandpass filtering (1-40 Hz), notch filter (50 Hz), and artifact rejection.

```bash
python code/preprocess.py
```

Outputs:
- `data/processed/cleaned_eeg.fif`
- `data/processed/exclusion_log.csv`

## 4. Feature Extraction

Calculate Lempel-Ziv Complexity (LZC) for each channel.

```bash
python code/features.py
```

Output:
- `data/analysis/complexity_metrics.csv`

## 5. Analysis

Calculate deltas, correlations, ANCOVA, and Benjamini-Hochberg correction.

```bash
python code/analysis.py
```

Outputs:
- `data/analysis/delta_scores.csv`
- `data/analysis/correlation_results.csv`
- `data/analysis/ancova_results.csv`
- `data/analysis/bh_corrected_pvalues.csv`

## 6. Sensitivity Analysis

Generate sensitivity table at p<=0.05 and p<=0.01 thresholds.

```bash
python code/sensitivity_analysis.py
```

Output:
- `data/analysis/sensitivity_table.csv`

## 7. Collinearity Diagnostics (Optional)

Check VIF for ANCOVA predictors.

```bash
python code/collinearity.py
```

## 8. Report Generation

Generate the final markdown report.

```bash
python code/report.py
```

Output:
- `docs/final_report.md`