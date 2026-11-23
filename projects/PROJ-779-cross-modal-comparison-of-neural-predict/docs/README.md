# Cross-Modal Comparison of Neural Prediction Error Signals

## Project Overview

This project implements an automated scientific pipeline to compare neural prediction error signals (MMN and VMM) across auditory and visual modalities. The pipeline downloads real EEG data from OpenNeuro, preprocesses it, extracts prediction error metrics, performs source localization, and conducts statistical comparisons.

## Data Source Policy

**CRITICAL: REAL DATA ONLY**

This project strictly adheres to the "Real Data" assumption. All data must originate from **OpenNeuro datasets**:

- **Auditory Oddball**: `ds000246`
- **Visual Oddball**: `ds000117`

**Synthetic data generation is strictly prohibited.** The pipeline is designed to:
1. Fetch real datasets from OpenNeuro using `mne.datasets.fetch_openneuro_dataset()`
2. Validate sampling rates (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard)
3. **HALT immediately** if validation fails or data cannot be fetched
4. **NEVER** fall back to synthetic, mock, or simulated data

Any attempt to use fabricated data will result in:
- Immediate pipeline failure
- Rejection by the execution gate
- Violation of Constitution Principle VII (Validation Independence)

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv.venv && source.venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment: Copy `.env.example` to `.env` and fill in required values

## Usage

Run the full pipeline:
```bash
python code/main.py --stage full_run
```

Run individual stages:
```bash
python code/main.py --stage download_preprocess
python code/main.py --stage extract_metrics
python code/main.py --stage localize_sources
python code/main.py --stage statistical_analysis
```

## Output Artifacts

The pipeline produces the following artifacts:
- `data/processed/cleaned_data.fif`: Preprocessed EEG data
- `data/results/metrics_summary.json`: Peak latency and mean amplitude metrics
- `data/results/sensitivity_analysis.csv`: Source localization sensitivity analysis
- `data/results/bh_corrected_pvalues.json`: Benjamini-Hochberg corrected p-values
- `data/results/reliability.json`: Split-half reliability scores
- `data/results/sc002_compliance.json`: SC-002 compliance check results
- `data/results/final_report.md`: Comprehensive final report

## Constitution Compliance

This project operates under Constitution Principles I-VI. Principle VII (Validation Independence) is currently **under review** via amendment PR (T055b). Until ratified, the pipeline logs a "Compliance Warning" and uses split-half reliability as a proxy measure.

## License

MIT License
