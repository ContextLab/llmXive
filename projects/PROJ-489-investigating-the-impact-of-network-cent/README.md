# Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Project ID**: PROJ-489

This project implements an automated scientific pipeline to investigate how network centrality metrics derived from waking-state EEG connectivity influence neural synchrony (measured via Phase Lag Index) across different sleep stages.

## Overview

The pipeline performs the following steps:
1. **Data Acquisition**: Downloads the Sleep-EDF dataset from PhysioNet.
2. **Preprocessing**: Filters EEG signals, removes artifacts using ICA, and segments data into sleep-stage-labeled epochs.
3. **Metric Computation**:
 - Constructs functional connectivity matrices (Theta/Alpha coherence) from waking data.
 - Computes network centrality metrics (Degree, Betweenness, Eigenvector).
 - Calculates Phase Lag Index (PLI) for sleep epochs.
4. **Statistical Analysis**:
 - Performs Linear Mixed Effects (LME) modeling.
 - Applies Benjamini-Hochberg FDR correction for multiple comparisons.
5. **Reporting**: Generates JSON and Markdown reports with statistical findings and effect sizes.

## Quick Start

See [docs/quickstart.md](docs/quickstart.md) for installation and usage instructions.

## Project Structure

```text
.
├── code/ # Python source code
│ ├── analysis.py # Statistical analysis (LME, FDR)
│ ├── config.yaml # Configuration parameters
│ ├── download.py # Data download from PhysioNet
│ ├── loaders.py # EDF and annotation loading
│ ├── main.py # Entry point and logging setup
│ ├── metrics.py # Centrality and PLI computation
│ ├── preprocess.py # Filtering and ICA
│ ├── report.py # Report generation
│ └──...
├── data/
│ ├── raw/ # Raw EDF files (downloaded)
│ ├── processed/ # Cleaned epochs
│ ├── metrics/ # SubjectMetrics.csv
│ └── results/ # Analysis JSON
├── docs/ # Documentation
│ ├── quickstart.md
│ └── data_model_diagram.md
├── reports/ # Final reports
│ └── final_report.md
├── tests/ # Unit and integration tests
│ ├── unit/
│ └── integration/
└── requirements.txt # Python dependencies
```

## Dependencies

- Python 3.11+
- `mne`: EEG processing
- `networkx`: Graph analysis
- `statsmodels`: Linear Mixed Effects
- `scipy`: Signal processing
- `pandas`, `numpy`: Data manipulation
- `pyedflib`: EDF file handling

Install all dependencies via:
```bash
pip install -r code/requirements.txt
```

## Usage

Run the full pipeline validation:
```bash
python code/quickstart_validator.py
```

Or run individual stages:
```bash
python code/download.py # Step 1
python code/preprocess.py # Step 2
python code/metrics.py # Step 3
python code/analysis.py # Step 4
python code/report.py # Step 5
```

## Data Model

Refer to [docs/data_model_diagram.md](docs/data_model_diagram.md) for a detailed entity relationship diagram and data flow description.

## License

This project is for research purposes. The underlying Sleep-EDF dataset is available under the PhysioNet Licensing Agreement.

## Contributing

Please ensure all new code passes the linting (flake8/pylint) and formatting (black) standards defined in the project. Run tests in `tests/` before submitting changes.
