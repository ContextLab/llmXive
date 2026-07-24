# Predicting Cognitive Fatigue from Resting-State EEG Complexity

This project implements an automated pipeline to analyze resting-state EEG data to predict cognitive fatigue using complexity metrics (Lempel-Ziv Complexity and Permutation Entropy).

## Overview

The pipeline consists of three main user stories:
1. **Data Retrieval and Preprocessing**: Fetch public EEG datasets, apply bandpass filters (1-40 Hz), remove line noise, and reject artifacts.
2. **Complexity Feature Extraction**: Calculate Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE) for each EEG channel.
3. **Correlation Analysis and Reporting**: Correlate complexity metrics with fatigue scores, apply statistical corrections, and generate a final report.

## Pipeline Parameters

The following parameters control the pipeline behavior. They are defined in `code/config.yaml` and must match the values below.

| Parameter | Value | Description |
|:--- |:--- |:--- |
| `filter_low` | 1 | Lower cutoff frequency for bandpass filter (Hz) |
| `filter_high` | 40 | Upper cutoff frequency for bandpass filter (Hz) |
| `artifact_threshold` | 100 | Amplitude threshold (µV) for artifact rejection |
| `random_seed` | 42 | Seed for reproducibility in random operations |
| `min_participants` | 30 | Minimum number of participants required for valid analysis |
| `notch_freq` | 50 | Frequency for notch filter to remove line noise (Hz) |

## Data Sources

The pipeline relies on real, publicly available EEG datasets. The `code/download.py` script attempts to fetch data from the following sources:
- **Sleep-EDF**: Contains polysomnography data including EEG channels.
- **SHHS (Sleep Heart Health Study)**: Large-scale sleep study data.

**Requirement**: The dataset MUST contain paired pre/post fatigue ratings or baseline fatigue ratings to satisfy the analysis requirements (FR-001). If the metadata inspection fails to find these variables, the pipeline halts with a validation error.

## Statistical Interpretation Guidelines

- **Lempel-Ziv Complexity (LZC)**: Measures the complexity of the EEG signal. Higher values indicate more complex, less predictable signals. We hypothesize that cognitive fatigue reduces signal complexity.
- **Permutation Entropy (PE)**: Measures the randomness of the time series. Lower entropy may indicate a more ordered, fatigued state.
- **Correlation Analysis**: We compute Pearson or Spearman correlations between complexity changes (delta) and fatigue score changes.
- **Multiple Comparisons**: The Benjamini-Hochberg procedure is applied to correct p-values across electrodes to control the False Discovery Rate (FDR).
- **Significance**: Results are reported at p ≤ 0.05 and p ≤ 0.01 thresholds.

## Installation

1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

Run the full pipeline using the quickstart commands:

```bash
python code/download.py
python code/preprocess.py
python code/features.py
python code/analysis.py
python code/report.py
```

## Output Artifacts

- `data/processed/cleaned_eeg.fif`: Preprocessed EEG data.
- `data/processed/lzc_metrics.csv`: Lempel-Ziv Complexity metrics per channel.
- `data/processed/pe_metrics.csv`: Permutation Entropy metrics per channel.
- `data/analysis/sensitivity_table.csv`: Sensitivity analysis results.
- `data/analysis/vif_report.csv`: Collinearity diagnostics.
- `docs/final_report.md`: Final statistical report.
- `logs/exclusion_log.csv`: Log of excluded participants and artifacts.

## License

This project is part of the llmXive automated science pipeline.
