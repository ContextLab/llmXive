# Quickstart: Predicting the Elastic Anisotropy of FCC Metals from Composition

## Prerequisites

- Python 3.10+
- `pip`
- (Optional) Materials Project API Key (if public rate limits are hit)

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-371-predicting-the-elastic-anisotropy-of-fcc
    ```

2.  **Create a virtual environment** and install dependencies.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
    *Dependencies*: `pandas`, `scikit-learn`, `mendeleev`, `requests`, `pyyaml`, `pytest`, `matplotlib`.

## Running the Pipeline

The entire pipeline can be executed via the CLI script.

```bash
# Fetch data, compute features, train models, and generate reports
python src/cli/run_pipeline.py
```

### Output

Upon completion, the following artifacts are generated:
- `data/processed/features_materials.csv`: Cleaned dataset with descriptors.
- `data/reports/model_results.json`: Metrics for each model.
- `data/reports/validation_report.json`: Physical consistency and sensitivity analysis.
- `data/reports/paper_report.md`: Human-readable summary.

## Verification

To verify the data pipeline:
```bash
pytest tests/unit/test_ingest.py
pytest tests/unit/test_features.py
```

To verify the full pipeline (integration):
```bash
pytest tests/integration/test_pipeline.py
```

## Troubleshooting

- **API Rate Limits**: If the script fails to fetch data, wait 60 seconds and retry. The script includes built-in retry logic.
- **Missing Dependencies**: Ensure `mendeleev` is installed; it fetches periodic table data on first run.
- **GPU Errors**: The code explicitly enforces CPU usage. If you see CUDA errors, check that `torch` is not being imported (it is not required).
