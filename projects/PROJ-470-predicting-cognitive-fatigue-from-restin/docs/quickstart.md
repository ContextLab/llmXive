# Quickstart Guide: Predicting Cognitive Fatigue from Resting-State EEG

## Environment Setup

1. Create and activate a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline consists of six main stages. Run them in order:

### 1. Download Data

Fetch the public EEG dataset with paired fatigue ratings:
```bash
python code/download.py --validate
```
This will:
- Download the dataset to `data/raw/`
- Create `data/raw/download_manifest.json`
- Validate that required variables (eeg_data, fatigue_rating) are present
- Create a sample file for testing

### 2. Preprocess EEG

Apply bandpass filtering (1-40 Hz), notch filter (50 Hz), and artifact rejection:
```bash
python code/preprocess.py
```
This will:
- Read the sample file from `data/raw/download_manifest.json`
- Apply filters and reject artifacts
- Save cleaned data to `data/processed/cleaned_eeg.fif`
- Log exclusions to `data/processed/exclusion_log.csv`

### 3. Extract Features

Calculate Lempel-Ziv complexity and Permutation Entropy:
```bash
python code/features.py
```
This will:
- Read cleaned EEG data
- Compute LZC and PE for each channel/segment
- Save metrics to `data/analysis/complexity_metrics.csv`

### 4. Run Analysis

Compute deltas and correlations:
```bash
python code/analysis.py --all
```
This will:
- Validate input files
- Calculate delta scores (Post - Pre)
- Compute Pearson and Spearman correlations
- Save results to `data/analysis/delta_scores.csv` and `data/analysis/correlation_results.csv`

### 5. Generate Report

Create the final markdown report:
```bash
python code/report.py
```
This will:
- Read all analysis results
- Generate `docs/final_report.md` with tables and statistics

## Verification

After running the full pipeline, verify outputs:
```bash
python tests/unit/test_setup.py
python tests/unit/test_skeleton.py
```

## Troubleshooting

- **Missing dependencies**: Ensure all packages in `code/requirements.txt` are installed.
- **Data not found**: Run `python code/download.py --validate` first.
- **Memory errors**: Monitor usage with `python code/verify_memory.py`.
- **Runtime errors**: Check `data/analysis/resource_usage.json` for diagnostics.
