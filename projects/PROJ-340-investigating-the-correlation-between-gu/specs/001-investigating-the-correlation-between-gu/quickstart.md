# Quickstart: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (for CI validation) or a local environment with 7GB+ RAM.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-340-investigating-the-correlation-between-gu
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

Since no verified real-world dataset is available in the provided list, the pipeline defaults to generating a **synthetic dataset** for validation.

1. **Generate Synthetic Data** (Optional, for testing):
   ```bash
   python code/ingest.py --mode synthetic --output data/raw/synthetic_data.csv
   ```

2. **Run the Full Analysis**:
   ```bash
   python code/main.py --input data/raw/synthetic_data.csv --output data/results/
   ```

   *Note: If you have a real dataset, replace `--input` with the path to your CSV.*

## Expected Output

- `data/results/correlation_results.json`: The main correlation matrix.
- `data/results/diagnostics.json`: VIF, Power, and Sensitivity analysis.
- `data/results/report.txt`: Human-readable summary (associational framing only).

## Verification

To verify the pipeline on a CI runner:
```bash
# This command runs the test suite which includes the data ingestion check
# and the full pipeline execution time limit check.
pytest tests/integration/test_pipeline.py -v
```

## Troubleshooting

- **Error: "Dataset-variable fit check failed"**: Ensure your input CSV contains all required sleep metrics (e.g., `rem_duration_min`, `sws_duration_min`).
- **Error: "Memory Limit Exceeded"**: Reduce the number of taxa in the input data. The pipeline is optimized for < 500 taxa.
- **Warning: "Underpowered"**: The sample size `N` is too small to detect an effect of `r=0.3` with [deferred] power. The pipeline will still run but will flag this limitation.
