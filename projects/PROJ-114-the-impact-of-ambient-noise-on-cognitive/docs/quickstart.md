# Quick Start Guide

## Prerequisites
- Python 3.11+
- pip

## Installation
1. Clone the repository
2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline
1. Prepare raw data in `data/raw/`
2. Run the Snakemake workflow:
 ```bash
 snakemake --cores 1
 ```

## Synthetic Data Generation (for testing)
To generate synthetic data for testing the pipeline:
```bash
python code/generate_synthetic_data.py --output data/raw/synthetic_data.csv --n-participants 100
```

## Validation
Run a dry-run to check the workflow:
```bash
snakemake --dry-run
```
