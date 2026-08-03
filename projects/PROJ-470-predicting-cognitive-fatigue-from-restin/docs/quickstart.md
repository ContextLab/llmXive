# Quickstart Guide: Predicting Cognitive Fatigue from Resting-State EEG

## Prerequisites
- Python 3.11+
- Virtual environment activated

## Installation
1. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Pipeline Execution
Run the pipeline in the following order:

1. **Download Data**
 ```bash
 python code/download.py
 ```
 This step validates the dataset for required fatigue ratings and downloads the raw EEG data.

2. **Preprocess EEG**
 ```bash
 python code/preprocess.py
 ```
 Applies bandpass filter (1-40 Hz) and notch filter (50 Hz) to remove artifacts and line noise.
 Output: `data/processed/cleaned_eeg.fif`

3. **Extract Features**
 ```bash
 python code/features.py
 ```
 Calculates Lempel-Ziv Complexity and Permutation Entropy for each channel.
 Outputs: `data/processed/lzc_metrics.csv`, `data/processed/pe_metrics.csv`

4. **Enforce Sample Size Constraint**
 ```bash
 python code/check_sample_size.py
 ```
 Validates that at least 30 participants are present in the feature dataset.
 Exits with code 1 if N < 30.

5. **Run Analysis**
 ```bash
 python code/analysis.py
 ```
 Performs correlation analysis between complexity metrics and fatigue scores.
 Outputs: `data/analysis/correlation_results.csv`, `data/analysis/sensitivity_table.csv`

6. **Generate Report**
 ```bash
 python code/report.py
 ```
 Compiles results into `docs/final_report.md`.

## Verification
- Check `data/processed/participant_exclusion_log.csv` for excluded participants.
- Verify `logs/exclusion_log.csv` for artifact rejection reasons.
- Ensure `docs/final_report.md` contains correlation coefficients, p-values, and confidence intervals.