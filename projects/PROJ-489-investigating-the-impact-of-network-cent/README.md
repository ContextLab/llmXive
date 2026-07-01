# llmXive: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

This project implements an automated science pipeline to analyze the relationship between network centrality (from waking EEG connectivity) and neural synchrony (from sleep EEG) using the Sleep-EDF dataset.

## Overview

The pipeline performs the following steps:
1. **Data Acquisition**: Downloads the Sleep-EDF dataset from PhysioNet.
2. **Preprocessing**: Filters, cleans (ICA), and segments EEG data into sleep-stage-labeled epochs.
3. **Metric Computation**: Calculates network centrality (degree, betweenness, eigenvector) and neural synchrony (Phase Lag Index).
4. **Statistical Analysis**: Fits Linear Mixed-Effects (LME) models with FDR correction.
5. **Reporting**: Generates JSON and Markdown reports with results and diagnostics.

## Features

- **Automated Data Download**: Fetches real data from PhysioNet via MNE-Python.
- **Robust Preprocessing**: Band-pass filtering, ICA artifact removal, and epoching.
- **Network Analysis**: Computes functional connectivity and centrality metrics using NetworkX.
- **Synchrony Metrics**: Calculates Phase Lag Index (PLI) for sleep epochs.
- **Statistical Rigor**: LME models, Shapiro-Wilk diagnostics, and Benjamini-Hochberg FDR correction.
- **Comprehensive Reporting**: JSON results and Markdown summaries with significance flags.

## Requirements

- Python 3.11+
- Dependencies listed in `code/requirements.txt` (mne, networkx, statsmodels, scipy, pandas, numpy, pyedflib).

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd <project-directory>
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Quickstart

See [`docs/quickstart.md`](docs/quickstart.md) for step-by-step instructions.

## Project Structure

```
.
├── code/ # Source code
│ ├── main.py # Entry point
│ ├── download.py # Data acquisition
│ ├── preprocess.py # Preprocessing
│ ├── metrics.py # Centrality & synchrony
│ ├── analysis.py # Statistical analysis
│ ├── report.py # Report generation
│ └──...
├── data/
│ ├── raw/ # Raw EDF files
│ ├── processed/ # Preprocessed epochs
│ ├── metrics/ # SubjectMetrics.csv
│ └── results/ # Analysis JSON
├── tests/ # Test suite
├── docs/ # Documentation
│ ├── quickstart.md
│ └── data_model.md
└── README.md
```

## Usage

### Run the Full Pipeline

```bash
python code/main.py
```

### Run Individual Stages

```bash
# Download and preprocess
python code/download.py
python code/preprocess.py

# Compute metrics
python code/metrics.py

# Analyze and report
python code/analysis.py
python code/report.py
```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Configuration

Edit `code/config.yaml` to adjust:
- Filter cutoffs (default: 0.5–45 Hz)
- ICA thresholds
- Frequency bands (theta, alpha)
- Random seed
- Output directories

## Output Artifacts

- `data/processed/`: Cleaned EEG epochs.
- `data/metrics/SubjectMetrics.csv`: Centrality and synchrony scores.
- `data/results/analysis_results.json`: Statistical results.
- `reports/final_report.md`: Human-readable summary.

## Data Model

See [`docs/data_model.md`](docs/data_model.md) for entity relationships and schema.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Implement your changes (follow task IDs in `tasks.md`).
4. Run tests and linting.
5. Submit a pull request.

## License

[Add license information here]

## Acknowledgments

- Sleep-EDF dataset from PhysioNet.
- MNE-Python for EEG processing.
- NetworkX for graph analysis.
- statsmodels for LME modeling.

## Contact

For questions or issues, please open an issue on the repository.
