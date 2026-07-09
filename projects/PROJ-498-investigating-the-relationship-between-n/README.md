# PROJ-498: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

## Overview

This project investigates the relationship between pre-stimulus frontoparietal neural synchrony (measured via Phase-Locking Value and weighted Phase-Lag Index) and behavioral attention switching costs using EEG data from public task-switching datasets.

**Status**: Active Research Pipeline

**Key Findings**:
- Correlation analysis between synchrony metrics and switching costs
- Permutation testing for statistical significance
- Sensitivity analysis across different pre-stimulus windows
- Trial-level Linear Mixed-Effects modeling

## Project Structure

```
projects/PROJ-498-investigating-the-relationship-between-n/
├── README.md # This file
├── quickstart.md # Getting started guide
├── requirements.txt # Python dependencies (strictly pinned)
├── code/ # Implementation modules
│ ├── config.py # Configuration paths and hyperparameters
│ ├── download.py # OpenNeuro dataset discovery and download
│ ├── preprocess.py # EEG preprocessing pipeline
│ ├── synchrony.py # Synchrony metric computation (PLV/wPLI)
│ ├── analysis.py # Statistical analysis and correlation
│ ├── main.py # Pipeline orchestrator
│ ├── logging_setup.py # Logging infrastructure
│ ├── memory_monitor.py # Memory usage tracking
│ ├── runtime_logger.py # Runtime metrics and timeout handling
│ ├── exclusion_tracker.py # Subject exclusion logging
│ ├── trial_synchrony_export.py # Trial-level data export
│ └── update_state_hashes.py # Artifact hashing and verification
├── data/
│ ├── raw/ # Downloaded raw EEG data (BIDS format)
│ ├── processed/ # Cleaned and epoched data
│ ├── metrics/ # Synchrony metrics, correlation results
│ ├── trial_level/ # Trial-level synchrony and RT data
│ ├── exclusions.csv # Excluded subjects log
│ └── data_gap_report.json # Fallback report if no dataset found
├── logs/
│ └── processing.log # Detailed processing logs
├── tests/
│ ├── unit/ # Unit tests
│ └── integration/ # Integration tests
├── contracts/ # Schema definitions
│ ├── data_gap_report.schema.yaml
│ ├── sensitivity_report.schema.yaml
│ └── trial_level_analysis.schema.yaml
└── results/
 └── results_summary.md # Final results summary with associational framing
```

## Prerequisites

- Python 3.9+
- CPU-only execution (no GPU/CUDA)
- Memory limit: ≤ 6.5 GB peak RSS
- Internet access for OpenNeuro dataset download

## Installation

1. Clone the repository and navigate to the project directory:
 ```bash
 cd projects/PROJ-498-investigating-the-relationship-between-n/
 ```

2. Create a virtual environment and install dependencies:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 pip install -r requirements.txt
 ```

3. Configure linting tools:
 ```bash
 python code/setup_lint_tools.py
 ```

4. Ensure directory structure:
 ```bash
 python code/setup_dirs.py
 ```

## Usage

### Running the Full Pipeline

Execute the complete analysis pipeline:

```bash
python code/main.py
```

This will:
1. Query OpenNeuro for task-switching datasets
2. Download and preprocess EEG data
3. Compute pre-stimulus synchrony metrics (theta and gamma bands)
4. Calculate behavioral switching costs
5. Perform correlation analysis with permutation testing
6. Run sensitivity and trial-level analyses
7. Generate all output artifacts and reports

### Individual Components

- **Data Download**: `python code/download.py`
- **Preprocessing**: `python code/preprocess.py`
- **Synchrony Analysis**: `python code/synchrony.py`
- **Statistical Analysis**: `python code/analysis.py`

## Configuration

Key parameters are defined in `code/config.py`:

- **Bandpass filter**: 1–45 Hz
- **Epoch window**: -1000ms to +2000ms
- **Pre-stimulus baseline**: -1000ms to 0ms
- **Memory limit**: 6.5 GB
- **Timeout**: Several hours (configurable)

## Output Artifacts

| File | Description |
|------|-------------|
| `data/processed/*.fif` | Cleaned, epoched EEG data per subject |
| `data/metrics/synchrony_metrics.csv` | Aggregated PLV/wPLI values per electrode pair |
| `data/metrics/correlation_results.json` | Primary correlation results with p-values |
| `data/metrics/sensitivity_report.json` | Sensitivity analysis across time windows |
| `data/metrics/trial_level_analysis.json` | Trial-level LME model results |
| `data/trial_level/per_trial_synchrony.csv` | Trial-by-trial synchrony and RT data |
| `data/exclusions.csv` | Log of excluded subjects with reasons |
| `logs/processing.log` | Detailed processing log |
| `data/metrics/runtime_log.json` | Pipeline execution timing |
| `results/results_summary.md` | Final summary with associational framing |

## Statistical Methods

### Primary Analysis
- **Metric**: Pearson/Spearman correlation between mean synchrony and switching costs
- **Bands**: Theta (4–7 Hz) and Gamma (30–45 Hz)
- **Correction**: Bonferroni for multiple comparisons
- **Validation**: Permutation testing (subject shuffling)

### Secondary Analysis
- **Model**: Linear Mixed-Effects (RT ~ Synchrony + (1|Subject))
- **Sensitivity**: Repeated for [-600, 0] and [-400, 0] windows

## Data Sources

- **Primary**: OpenNeuro task-switching datasets (dynamically searched)
- **Fallback**: If no dataset found, `data/data_gap_report.json` is generated with `fallback_id: null`

## Quality Control

- **Subject Exclusion**: <10 valid trials/condition OR >50% artifact removal
- **Memory Monitoring**: Peak RSS tracked per subject
- **Timeout Handling**: Pipeline halts if runtime exceeds limit
- **Artifact Verification**: SHA-256 hashes for all outputs

## Limitations and Framing

**Important**: This study is **associational** in nature. Correlations between neural synchrony and behavioral switching costs do not imply causation. All results should be interpreted as statistical associations requiring further experimental validation.

See `results/results_summary.md` for the complete associational framing statement.

## Testing

Run unit tests:
```bash
pytest tests/unit/
```

Run integration tests:
```bash
pytest tests/integration/
```

## Dependencies

See `requirements.txt` for the complete list of strictly pinned dependencies:
- `mne==1.7.0`
- `numpy==1.24.3`
- `scipy==1.11.0`
- `pandas==2.0.0`
- `statsmodels==0.14.0`
- `scikit-learn==1.3.0`
- `pyyaml==6.0.1`
- `openneuro-py==2.2.0`
- `bids-validator==1.12.0`

## Contributing

1. Ensure all tests pass before committing
2. Run linter: `python code/setup_lint_tools.py --run-linting`
3. Format code: `python code/setup_lint_tools.py --run-formatting`
4. Update state hashes after changes: `python code/update_state_hashes.py`

## License

Research project - all data and code subject to open-source research licenses.

## Contact

For questions or issues, refer to the project specification documents in `specs/`.