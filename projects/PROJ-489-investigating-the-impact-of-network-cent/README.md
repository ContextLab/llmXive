# llmXive: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

## Overview

This project implements a research pipeline to investigate the relationship between network centrality metrics (computed from waking EEG connectivity) and neural synchrony (computed from sleep EEG epochs). The pipeline automates data acquisition, preprocessing, metric computation, statistical analysis, and report generation.

## Key Features

- **Automated Data Download**: Fetches Sleep-EDF dataset from PhysioNet.
- **Preprocessing**: Band-pass filtering, ICA artifact removal, and epoching.
- **Network Analysis**: Computes degree, betweenness, and eigenvector centrality using NetworkX.
- **Synchrony Metrics**: Calculates Phase Lag Index (PLI) and global coherence.
- **Statistical Modeling**: Linear Mixed Effects (LME) models with Benjamini-Hochberg FDR correction.
- **Memory Profiling**: Ensures peak RAM usage stays below 4 GB.
- **Comprehensive Reporting**: Generates JSON and Markdown reports with significance flags and limitations.

## Installation

1. Clone the repository:
 ```bash
 git clone
 cd llmXive-sleep-synchrony
 ```

2. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Usage

Run the full pipeline:

```bash
python code/main.py
```

This will execute all stages in sequence and output results to `data/results/` and `reports/`.

For detailed usage instructions, see [docs/quickstart.md](docs/quickstart.md).

## Project Structure

```
.
├── code/ # Source code
│ ├── main.py # Entry point with memory profiling
│ ├── download.py # Data acquisition
│ ├── preprocess.py # Signal preprocessing
│ ├── metrics.py # Centrality and synchrony computation
│ ├── analysis.py # Statistical analysis (LME, FDR)
│ └── report.py # Report generation
├── data/
│ ├── raw/ # Downloaded EDF files
│ ├── processed/ # Cleaned data
│ ├── metrics/ # Computed metrics
│ └── results/ # Analysis outputs
├── tests/ # Unit and integration tests
├── docs/ # Documentation
└── reports/ # Final reports
```

## Data Model

See [docs/data_model.md](docs/data_model.md) for a detailed description of the data structures and file formats.

## Validation

Run the quickstart validator to ensure the pipeline is working correctly:

```bash
python code/quickstart_validator.py
```

## Requirements

- Python 3.11+
- Memory: 4 GB RAM (enforced by pipeline)
- CPU: 2 vCPU (estimated runtime < 4 hours)

## Dependencies

- `mne`: EEG processing
- `networkx`: Network analysis
- `statsmodels`: LME modeling
- `scipy`: Signal processing
- `pandas`, `numpy`: Data manipulation
- `pyedflib`: EDF file handling

## License

MIT License

## Contributing

Contributions are welcome! Please read the contribution guidelines before submitting pull requests.
