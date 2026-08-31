# Quickstart Guide

This guide explains how to run the full analysis pipeline for the project "The Impact of Predictive Coding Errors on Subjective Time Perception".

## Prerequisites

- Python 3.11+
- Virtual environment (recommended)

## Setup

1. Clone the repository.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```
3. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The pipeline consists of the following steps:

1. **Download and validate datasets**:
 ```bash
 python code/download.py
 ```
 This script downloads datasets from OpenML/HuggingFace, verifies checksums, and filters for required columns.

2. **Preprocess data and compute Markov surprisal**:
 ```bash
 python code/preprocess.py
 ```
 This script loads the downloaded datasets, filters for sequential stimuli, computes Markov surprisal, and saves the results.

3. **Generate standardized output (T017)**:
 ```bash
 python code/generate_standardized_output.py
 ```
 This script creates the final `data/processed/standardized.csv` file with checksums.

4. **Run statistical analysis**:
 ```bash
 python code/analysis.py
 ```
 This script fits linear mixed-effects models, calculates effect sizes, and performs sensitivity analysis.

5. **Generate visualizations**:
 ```bash
 python code/visualize.py
 ```
 This script generates forest plots and residual diagnostic plots.

## Output Files

- `data/processed/standardized.csv`: The final standardized dataset.
- `analysis/results.json`: The results of the statistical analysis.
- `figures/`: Directory containing generated plots.

## Troubleshooting

- If you encounter a `pyarrow` error, ensure you have the correct version of `pyarrow` installed (see `code/requirements.txt`).
- If you encounter a `No datasets were successfully processed` error, check the `data/processed/exclusion_log.json` file for details.

## Reproducibility

To ensure reproducibility, set the random seed in `code/config.py` before running the pipeline.

```python
from config import set_seed
set_seed(42)
```