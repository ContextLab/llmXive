# Quickstart Guide: Predicting Cognitive Fatigue from Resting-State EEG Complexity

This guide walks you through running the full pipeline to analyze cognitive fatigue using resting-state EEG data. The pipeline downloads public data, preprocesses it to remove artifacts, extracts complexity features (Lempel-Ziv complexity and Permutation Entropy), performs statistical analysis, and generates a final report.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- At least 14 GB of free disk space (for dataset and processed files)
- 7 GB+ of available RAM

## Step 1: Environment Setup

Create a virtual environment and install the required dependencies.

```bash
# Navigate to the project root
cd projects/PROJ-470-predicting-cognitive-fatigue-from-restin

# Create a virtual environment
python -m venv code/.venv

# Activate the virtual environment
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Data Download

Download the public EEG dataset containing resting-state recordings and fatigue ratings.

```bash
python code/download.py --validate
```

**Expected Output:**
- Downloads raw data to `data/raw/`
- Generates `data/raw/download_manifest.json`
- Creates `data/raw/sample_eeg.fif` for testing
- Validates dataset variables and participant count

## Step 3: Preprocessing

Apply bandpass filtering (1-40 Hz), notch filter (50 Hz), and artifact rejection.

```bash
python code/preprocess.py
```

**Expected Output:**
- Cleaned EEG data saved to `data/processed/cleaned_eeg.fif`
- Exclusion log saved to `data/processed/exclusion_log.csv`
- Pipeline log saved to `data/processed/pipeline.log`

## Step 4: Feature Extraction

Calculate Lempel-Ziv complexity and Permutation Entropy for each EEG channel.

```bash
python code/features.py
```

**Expected Output:**
- Complexity metrics saved to `data/analysis/complexity_metrics.csv`
- Contains columns: `participant_id`, `channel`, `segment_id`, `lzc_value`, `pe_value`

## Step 5: Analysis

Compute delta scores, correlations, ANCOVA, and Benjamini-Hochberg correction.

```bash
python code/analysis.py
```

**Expected Output:**
- Delta scores saved to `data/analysis/delta_scores.csv`
- Correlation results saved to `data/analysis/correlation_results.csv`
- ANCOVA results saved to `data/analysis/ancova_results.csv`
- Benjamini-Hochberg corrected p-values saved to `data/analysis/bh_corrected_pvalues.csv`
- Sensitivity analysis table saved to `data/analysis/sensitivity_table.csv`
- VIF diagnostics logged to `data/analysis/vif_diagnostics.log`

## Step 6: Report Generation

Generate the final markdown report with all statistical results.

```bash
python code/report.py
```

**Expected Output:**
- Final report saved to `docs/final_report.md`
- Contains sections: Correlation Results, ANCOVA Results, Sensitivity Analysis, VIF Diagnostics

## Verification

To verify the pipeline ran successfully, check that all output files exist:

```bash
# Check for key output files
ls -lh data/processed/cleaned_eeg.fif
ls -lh data/analysis/complexity_metrics.csv
ls -lh data/analysis/delta_scores.csv
ls -lh data/analysis/bh_corrected_pvalues.csv
ls -lh docs/final_report.md
```

## Troubleshooting

- **Download fails**: Ensure you have internet access and that the HuggingFace dataset is accessible.
- **Memory errors**: The pipeline requires at least 7 GB RAM. Close other applications if you encounter memory issues.
- **Missing files**: Verify that each step completed successfully before proceeding to the next step. Check `data/processed/pipeline.log` for error messages.

## Next Steps

After running the pipeline, review `docs/final_report.md` for the complete analysis results. You can also examine the intermediate CSV files in `data/analysis/` for detailed metrics.