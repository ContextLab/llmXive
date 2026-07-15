# PROJ-754: Linking Resting-State fMRI Entropy to Real-World Decision Risk-Taking

## Overview
This project investigates the relationship between resting-state fMRI entropy and real-world decision risk-taking behavior using data from the Human Connectome Project (HCP).

## Project Structure
```
.
├── code/ # Source code
│ ├── config/ # Configuration and environment management
│ ├── data/ # Data acquisition and preprocessing
│ ├── analysis/ # Entropy computation
│ └── stats/ # Statistical modeling
├── data/ # Data storage
│ ├── raw/ # Raw downloaded data
│ ├── cleaned/ # Processed clean datasets
│ └── derived/ # Derived features (entropy, noise variance)
├── tests/ # Test suites
├── reports/ # Generated reports and figures
├── requirements.txt # Python dependencies
├── pyproject.toml # Project metadata and tool config
└── README.md # This file
```

## Setup
1. Create a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
3. Configure environment variables (see `code/config/env_manager.py`):
 ```bash
 export HCP_TOKEN="your_hcp_token_here"
 ```

## Usage
Run the pipeline steps in order:
1. Data download: `python code/data/download_hcp.py`
2. Validation: `python code/data/validate_data.py`
3. Filtering: `python code/data/filter_motion.py`
4. Entropy computation: `python code/analysis/compute_entropy.py`
5. Statistical modeling: `python code/stats/model_fitting.py`

## Testing
Run tests with pytest:
```bash
pytest tests/
```

## Linting & Formatting
```bash
# Check linting
ruff check.
# Fix linting issues
ruff check --fix.
# Check formatting
black --check.
# Format code
black.
```
