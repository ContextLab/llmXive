# Quickstart: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

This guide walks you through the end-to-end execution of the HEA yield strength prediction pipeline.

## Prerequisites

*   Python 3.11+
*   Git
*   Access to the internet (to download datasets)

## Step 1: Environment Setup

1.  Clone the repository and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-418-predicting-the-yield-strength-of-high-en
    ```

2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r code/requirements.txt
    ```

3.  Ensure `__init__.py` files exist in `code/` and `tests/` subdirectories:
    ```bash
    touch code/__init__.py
    touch code/data/__init__.py
    touch code/models/__init__.py
    touch code/stats/__init__.py
    touch code/utils/__init__.py
    touch tests/__init__.py
    touch tests/unit/__init__.py
    touch tests/integration/__init__.py
    touch tests/contract/__init__.py
    ```

## Step 2: Data Acquisition

Run the data fetching script. This will download the HEA dataset from the configured Zenodo source (DOI: 10.5281/zenodo.3935596) and verify the bundled elemental properties.

```bash
python code/main.py --stage fetch
```

*Expected Output*: A log message reporting the number of raw records downloaded and the path to the saved file.
*Note*: If the Zenodo source is unreachable, the script will fail with "Verified Source Unreachable".

## Step 3: Descriptor Engineering

Calculate the five compositional descriptors and filter the dataset.

```bash
python code/main.py --stage process
```

*Expected Output*:
*   `data/processed/processed_hea.csv` created.
*   Log showing the count of single-phase, room-temperature alloys.
*   Log showing the number of excluded rows (missing data or wrong phase/temp).

## Step 4: Model Training & Evaluation

Train Random Forest, Gradient Boosting, and OLS models.

```bash
python code/main.py --stage train
```

*Expected Output*:
*   Cross-validation logs.
*   `output/metrics.json` generated with R², MAE, RMSE for all models.
*   Runtime should be < 3 hours.

## Step 5: Statistical Validation

Run permutation tests, bootstrap resampling, and VIF analysis.

```bash
python code/main.py --stage validate
```

*Expected Output*:
*   `output/stability.json` with bootstrap confidence intervals.
*   `output/report.md` containing the final analysis, p-values, and the mandatory disclaimer.

## Step 6: Verification

Check that all required artifacts exist:

```bash
ls data/raw/
ls data/processed/
ls output/
cat output/metrics.json
cat output/report.md
```

**Validation Log**: The `output/report.md` must contain the string "Associational analysis only; no causal inference" and a "Collinearity Warning" section if any VIF > 10.

## Troubleshooting

*   **Missing Element Properties**: If the script fails due to a missing element, ensure the bundled `data/raw/elemental_properties.csv` contains the required element.
*   **Dataset Download Failure**: If the Zenodo source is unreachable, the pipeline fails. Check network connectivity.
*   **Runtime Exceeded**: If the training step exceeds 3 hours, reduce the number of trees in `code/models/train.py` (e.g., from 200 to 100) and re-run.