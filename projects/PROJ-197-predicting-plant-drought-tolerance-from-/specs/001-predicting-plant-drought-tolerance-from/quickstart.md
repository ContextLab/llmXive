# Quickstart: Predicting Plant Drought Tolerance

## Prerequisites

- Python 3.11+
- Git
- Access to a GitHub Actions runner (or local machine for testing)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-197-predicting-plant-drought-tolerance-from-/
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Running the Pipeline

The pipeline is executed via a single entry point script.

1.  **Execute the full pipeline**:
    ```bash
    python code/run_pipeline.py
    ```
    This script will:
    - Download real physiological data (TRY).
    - Generate **synthetic genomic data** and a **synthetic label** (for pipeline validation).
    - Merge and impute.
    - Train models.
    - Evaluate and generate reports.

2.  **View results**:
    - **Metrics**: `data/reports/metrics.json`
    - **Logs**: `data/logs/pipeline.log`
    - **Merged Data**: `data/processed/merged.csv`

## Testing

Run the unit and integration tests:

```bash
pytest tests/
```

## Troubleshooting

- **Data Download Fails**: The pipeline will automatically switch to a synthetic mock dataset if the verified URLs are unreachable. Check `data/logs/pipeline.log` for details.
- **Memory Error**: Unlikely with a limited number of species. If encountered, reduce the number of trees in `code/models/train.py`.
- **Missing Dependencies**: Ensure `requirements.txt` is up to date and installed in the active virtual environment.

## Important Note on Data

This project uses **synthetic genomic data** and a **synthetic target label** because no verified plant genomic data sources are available in the provided dataset list. The results are for **pipeline validation only** and do not represent biological findings.