# Quickstart Guide for PROJ-197

This guide outlines the steps to run the full drought tolerance prediction pipeline.

## Prerequisites

- Python 3.11+
- pip
- Virtual environment (recommended)

## Setup

1. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

## Running the Pipeline

The entire pipeline can be executed with a single command. This script (`code/run_pipeline.py`) orchestrates all tasks from data ingestion to model evaluation and metrics aggregation.

```bash
python code/run_pipeline.py
```

This command will:
1. Initialize directories and logging.
2. Generate or load the phylogenetic distance matrix.
3. Attempt to download TRY data (or use synthetic fallback in Validation Mode).
4. Generate synthetic genomic data if real data is unavailable (Validation Mode).
5. Ingest, merge, and impute the dataset.
6. Split the data into train/test sets.
7. Train RandomForest, XGBoost, and KNN Baseline models.
8. Evaluate models and perform DeLong's test.
9. Compare models and generate the final report.
10. **Aggregate all metrics into `data/logs/metrics.json` (T030)**.

## Output Artifacts

After successful execution, the following files will be available:

- `data/processed/merged_dataset.csv`: The cleaned, merged dataset.
- `data/processed/synthetic_genomics.csv`: Synthetic genomic features (if used).
- `data/processed/synthetic_phylo_matrix.npy`: Phylogenetic distance matrix.
- `data/models/`: Saved model artifacts (`.joblib`).
- `docs/reports/final_analysis.md`: Final analysis report.
- `data/logs/metrics.json`: **Single source of truth for all metrics and logs (T030)**.

## Validation Mode

By default, the pipeline runs in **Production Mode** (`VALIDATION_MODE = False`), meaning it will fail loudly if real data sources are missing. To run in **Validation Mode** (allowing synthetic fallbacks), set the environment variable:

```bash
export VALIDATION_MODE=True
python code/run_pipeline.py
```

Or modify `code/config.py` directly.

## Testing

Run the test suite:
```bash
pytest -q --timeout=1800
```