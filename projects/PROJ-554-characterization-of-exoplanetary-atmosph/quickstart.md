# Quickstart Guide: Exoplanetary Atmosphere Characterization Pipeline

This guide provides instructions for running the complete pipeline to characterize exoplanetary atmospheres.

## Prerequisites

- Python 3.9+
- pip
- Required packages (see `requirements.txt`)

## Installation

```bash
# Create virtual environment
python -m venv code/.venv
source code/.venv/bin/activate # On Windows: code\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

The pipeline can be run in stages or all at once using `code/main.py`:

```bash
# Run all stages
python code/main.py --stage all

# Run individual stages
python code/main.py --stage download
python code/main.py --stage retrieval
python code/main.py --stage analysis
```

## Manual Stage Execution

Alternatively, you can run each stage manually:

```bash
# Stage 1: Download data
python code/download.py --output data/raw

# Stage 2: Run retrieval
python code/retrieval.py --input data/raw --output data/processed

# Stage 3: Analysis
python code/analysis.py --input data/processed/analysis_dataset.csv --output results
```

## Output Files

The pipeline produces the following outputs:

- `data/raw/metadata.csv`: Raw metadata from NASA Exoplanet Archive
- `data/processed/retrieval_results.csv`: Water abundance retrievals
- `data/processed/analysis_results.json`: Statistical analysis results
- `results/plots/*.png`: Diagnostic plots
- `results/*.md`: Reports and summaries

## Troubleshooting

If you encounter errors:

1. Check that all dependencies are installed: `pip check`
2. Verify data directories exist: `ls data/raw data/processed results`
3. Check log files: `cat logs/*.log`
4. Ensure network connectivity for NASA Exoplanet Archive API

## Data Integrity

All data is fetched programmatically from the NASA Exoplanet Archive. No static data files are included in the repository.