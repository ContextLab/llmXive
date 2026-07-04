# Robustness of Confidence Intervals to Differential Privacy Noise

This project investigates how Differential Privacy (DP) noise affects the coverage probability of standard confidence intervals (CIs) for means and regression coefficients.

## Project Structure

```
projects/PROJ-710-robustness-of-confidence-intervals-to-di/
├── code/ # Source code
│ ├── data/ # Data generation and DP noise injection
│ ├── analysis/ # CI construction, GLM analysis, plotting
│ ├── utils/ # Utility functions
│ ├── tests/ # Unit and integration tests
│ └── config.py # Configuration settings
├── artifacts/ # Generated outputs (CSVs, JSONs, plots)
├── requirements.txt # Python dependencies
├── pyproject.toml # Project metadata and tool configuration
└── README.md # This file
```

## Setup

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Verify directory structure:
 ```bash
 bash setup.sh
 ```

## Usage

Refer to `quickstart.md` for the full pipeline execution guide.

## Configuration

Edit `code/config.py` to modify:
- Population and sample sizes
- Epsilon values and noise types
- Random seeds
- Artifact output paths
