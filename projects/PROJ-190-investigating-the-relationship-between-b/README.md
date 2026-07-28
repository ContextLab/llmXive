# Brain Network Efficiency and Fluid Intelligence

This project investigates the relationship between brain network efficiency metrics and fluid intelligence scores using resting-state fMRI data from the Human Connectome Project (HCP).

## Overview

The analysis pipeline:
1. Downloads and preprocesses HCP resting-state fMRI data
2. Computes graph theory metrics (global and frontoparietal efficiency)
3. Performs statistical analysis correlating network efficiency with fluid intelligence
4. Generates a comprehensive report with results and visualizations

## Quickstart

### Prerequisites
- Python 3.11+
- Access to HCP 1200-release data (requires credentials)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

```bash
# Run the full pipeline
python code/main.py

# Or run individual stages
python code/data/download_hcp.py
python code/data/preprocess.py
python code/graph/metrics.py
python code/stats/analysis.py
```

### Project Structure

```
.
├── code/ # Source code
│ ├── config.py # Configuration and paths
│ ├── main.py # Pipeline orchestrator
│ ├── data/ # Data download and preprocessing
│ ├── graph/ # Graph theory computations
│ └── stats/ # Statistical analysis
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── processed/ # Preprocessed data
│ └── results/ # Analysis results
├── tests/ # Unit and integration tests
├── docs/ # Documentation
├── state/ # Pipeline state and checkpoints
├── requirements.txt # Python dependencies
└── README.md # This file
```

## Configuration

Edit `code/config.py` to modify:
- Random seeds for reproducibility
- Data paths
- Analysis thresholds
- HCP credentials (via environment variables)

## License

This project is for research purposes only. HCP data usage is subject to the HCP Data Use Agreement.
