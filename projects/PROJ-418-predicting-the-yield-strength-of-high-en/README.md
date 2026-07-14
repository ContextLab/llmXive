# Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

**Project ID:** PROJ-418
**Status:** Research Implementation Pipeline

## Overview

This project implements an automated scientific research pipeline to predict the yield strength of High-Entropy Alloys (HEAs) using compositional descriptors (δ, Δχ, VEC, entropy, melting variance). The pipeline follows a strict research methodology: data acquisition, descriptor engineering, model training (Random Forest, Gradient Boosting, Linear Regression), and rigorous statistical validation (permutation testing, bootstrapping, VIF diagnostics).

## Prerequisites

- Python 3.9+
- pip
- A verified dataset URL for HEA compositions (configured in `code/utils/config.py`)

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd PROJ-418-predicting-the-yield-strength-of-high-en
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Directory Structure

```
.
├── code/ # Source code modules
│ ├── data/ # Data acquisition and processing
│ ├── models/ # Model training and evaluation
│ ├── utils/ # Utilities (logging, config, plots)
│ └──...
├── data/
│ ├── raw/ # Raw downloaded datasets
│ └── processed/ # Processed data with descriptors
├── output/
│ ├── plots/ # Generated visualizations
│ ├── metrics.json # Model performance metrics
│ ├── power_analysis.json # Power analysis results
│ └── report.md # Final research report
├── tests/ # Test suites
├── requirements.txt
├── quickstart.md
└── README.md
```

## Quick Start

See [quickstart.md](./quickstart.md) for step-by-step instructions to run the full pipeline.

### Running the Pipeline

The pipeline is designed to be executed in stages. Ensure all prerequisites (Phase 1 & 2) are met before running user story tasks.

```bash
# Run the full pipeline (requires Phase 1-3 completion)
python code/models/train.py
python code/models/evaluate.py
python code/models/report_generator.py
```

## Configuration

Dataset URLs must be configured in `code/utils/config.py`. The system will fail immediately with `DATA_SOURCE_MISSING` if a verified URL is not found. Do not use placeholder URLs.

## Disclaimer

This project is for research purposes only. All analyses are associational; no causal inference should be drawn. See generated `output/report.md` for specific disclaimers on all visualizations and conclusions.

## License

Research Implementation - Internal Use Only
