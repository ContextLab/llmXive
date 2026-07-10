# Quickstart: Evaluating the Robustness of Statistical Methods to Common Data Errors

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Access to the verified datasets (URLs are public).

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Pipeline

The pipeline is executed via the main script, which orchestrates data loading, error injection, testing, and visualization.

```bash
# Run the full simulation
python code/main.py

# Run a specific test (e.g., t-test only)
python code/main.py --test t_test
```

## Expected Outputs

- **`data/processed/`**: Contains error-injected versions of the datasets.
- **`results/metrics.json`**: Aggregated metrics (Type I error, CI coverage, bias).
- **`results/plots/`**: Degradation curves (PNG) for each test type.

## Verification

To verify the installation and data integrity:

```bash
# Run unit tests
pytest tests/unit/

# Run integration test (full pipeline on a small subset)
pytest tests/integration/test_full_pipeline.py
```

## Troubleshooting

- **Memory Error**: The pipeline is optimized for standard memory constraints. If issues occur, reduce the number of simulation iterations in `code/config.py`.
- **Dataset Missing**: Ensure you have internet access to download the datasets on the first run. Subsequent runs use the cached `data/raw/` files.
- **Test Failure**: If a specific statistical test fails (e.g., due to small sample size), the pipeline logs a warning and skips that combination. Check `logs/pipeline.log`.
