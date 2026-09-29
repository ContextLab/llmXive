# Quickstart Guide

This guide provides a quick start to running the statistical analysis of publicly available chess game data for Elo rating prediction.

## Prerequisites

- Python 3.8+
- pip (Python package installer)

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-283-statistical-analysis-of-publicly-availab
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

To run the full pipeline on a sample dataset, execute the following command:

```bash
python src/main.py --sample
```

### Expected Output

Upon successful completion, the pipeline will print:

```
Pipeline completed successfully
```

The following artifacts will be generated:

- `data/processed/games.parquet`: Processed game records
- `data/results/model_metrics.json`: Model performance metrics
- `data/results/diagnostics.json`: Diagnostic report
- `data/results/`: Diagnostic plots (PNG files)

## Validation

To validate the output against the schema contracts:

```bash
python src/validation/validate_contracts.py --data data/processed/games.parquet
```

## Troubleshooting

- If you encounter a `DataFetchError`, check your internet connection and the Lichess dataset URL.
- If the pipeline fails due to memory issues, reduce the `--sample-size` parameter.
- Ensure all dependencies are installed correctly by running `pip check`.