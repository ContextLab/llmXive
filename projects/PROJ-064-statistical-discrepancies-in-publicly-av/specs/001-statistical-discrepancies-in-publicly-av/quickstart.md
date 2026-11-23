# Quickstart: Statistical Discrepancies in Publicly Available Election Data

## Prerequisites

- Python 3.11+
- Git
- Access to a HuggingFace account (optional, for large datasets)
- GitHub Actions Free Tier (for CI execution)

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd projects/PROJ-064-statistical-discrepancies-in-publicly-av
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Running the Pipeline

### 1. Data Ingestion

Run the ingestion script to download or generate data.
*Note: If no verified real dataset is found, the script defaults to 'Synthetic Data Fallback' mode.*

```bash
python code/ingestion.py --source "synthetic" --state "CA"
```

This will:
- Generate synthetic election data (or download if `--source "real"` and URL provided).
- Calculate checksums.
- Generate `data/processed/unified_election_data.parquet`.

### 2. Discrepancy Calculation

Calculate discrepancies between precinct sums and county totals.

```bash
python code/discrepancy_calc.py --input data/processed/unified_election_data.parquet --output data/processed/discrepancies.parquet
```

### 3. Statistical Simulation & Analysis

Run the Monte Carlo simulation (10,000 iterations) and statistical tests.

```bash
python code/simulation.py --input data/processed/discrepancies.parquet --iterations 10000 --seed 42
python code/analysis.py --input data/processed/null_distributions.json --threshold 0.005
```

### 4. Visualization

Generate histograms, Q-Q plots, and sensitivity reports.

```bash
python code/viz.py --input data/processed/analysis_results.json --output-dir docs/plots
```

## Testing

Run the unit tests to verify the pipeline:

```bash
pytest tests/unit/ -v
```

Run the integration test (requires data download):

```bash
pytest tests/integration/test_pipeline.py -v
```

## Troubleshooting

- **Memory Error**: If the simulation fails due to memory, reduce the `--iterations` count or ensure `streaming=True` is used in `ingestion.py`.
- **Data Not Found**: If the script fails to find the dataset, check `config.py` for the `DATASET_SOURCE` flag. It will default to synthetic data if no real source is verified.
- **NB Fit Failure**: If the Negative Binomial fit fails, the script will automatically switch to the Parametric Bootstrap model. Check the logs for `NB_FIT_FAILED` warnings.
- **Reproducibility**: Use `--verify-reproducible` flag to check seed consistency and checksums.

## Output Artifacts

- `data/processed/unified_election_data.parquet`: Cleaned, unified dataset.
- `data/processed/discrepancies.parquet`: Discrepancy calculations.
- `data/processed/null_distributions.json`: Simulated null distribution.
- `data/processed/analysis_results.json`: Final statistical results.
- `docs/plots/`: Generated visualizations (histograms, Q-Q plots).