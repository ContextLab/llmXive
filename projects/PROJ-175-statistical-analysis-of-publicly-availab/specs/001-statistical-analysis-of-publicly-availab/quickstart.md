# Quickstart: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

## Prerequisites

- Python 3.11+
- 7 GB+ RAM available (free-tier GitHub Actions runner)
- Git

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-175-statistical-analysis-of-publicly-availab
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

## Data Preparation

**Note**: This step downloads datasets from verified sources. Ensure you have internet access.

1.  **Run Download Script**:
    ```bash
    python code/data/download.py
    ```
    *This will fetch Recipe1M, FlavorDB (if available via verified link), and Counterfactual data.*

2.  **Run Preprocessing**:
    ```bash
    python code/data/preprocess.py
    ```
    *Generates `data/processed/final_dataset.parquet`.*

## Running the Analysis

1.  **Fit Models**:
    ```bash
    python code/models/fit_logistic.py
    python code/models/fit_bayesian.py
    ```

2.  **Evaluate & Report**:
    ```bash
    python code/evaluation/report.py
    ```
    *Generates `docs/reports/final_results.csv` and calibration plots.*

## Verification

Run the test suite to ensure contract compliance:
```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: The script automatically downsamples. If it fails, check `code/data/preprocess.py` for the sampling ratio.
- **Missing FlavorDB**: If the dataset is not found, the script logs a warning and uses a default similarity of 0.
