# Quickstart: Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data

## Prerequisites

-   Python 3.11+
-   Git
-   Access to the internet (for dataset download and periodic table data)

## Installation

1.  **Clone and Navigate**:
    ```bash
    cd projects/PROJ-374-predicting-the-influence-of-alloying-on-/code/
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This installs `pandas`, `scikit-learn`, `mendeleev`, `matplotlib`, `requests`, `pyyaml`, `numpy`, and `pytest`.*

## Running the Pipeline

The pipeline consists of four sequential steps. Run them in order.

### Step 1: Ingest, Filter, and Check Retention
Downloads the dataset from DOI 10.1038/sdata.2017.85, filters for target families using stoichiometry parsing, and checks retention rate.
```bash
python 01_ingest_and_clean.py
```
*Output*: `data/processed/cleaned_compositions.csv`  
*Note*: If retention rate < 95%, this script exits with a CRITICAL ERROR and no further steps are run.

### Step 2: Engineer Features
Calculates compositional descriptors (Mean Radius, VEC, Atomic Number Variance, etc.) using `mendeleev` and includes Temperature.
```bash
python 02_engineer_features.py
```
*Output*: `data/processed/final_features.csv`

### Step 3: Train, Evaluate, and Permutation Test
Trains the Gradient Boosting model, performs Repeated CV (if N < 100) or 80/20 split, and runs multiple permutation iterations.
```bash
python 03_train_and_evaluate.py
```
*Output*: `data/processed/model_metrics.json`, `data/processed/predictions.csv`

### Step 4: Visualize, Check Collinearity, and Report
Generates scatter plots, calculates VIF, and produces the final summary report with statistical classification.
```bash
python 04_visualize_and_report.py
```
*Output*: `docs/figures/*.png`, `docs/report.md`

## Verification

To verify the pipeline:
1.  Check that `data/processed/final_features.csv` has no null values in the descriptor columns.
2.  Verify `docs/report.md` contains a "Classification" (Success/Inconclusive/Failure) and a "Permutation p-value".
3.  Ensure all plots in `docs/figures/` have axis labels and that the report includes VIF scores.

## Troubleshooting

-   **Dataset Download Failed**: The DOI 10.1038/sdata.2017.85 may be behind a paywall or blocked in the CI environment. Check the logs for "HTTP 403" or "404". If the raw file is unavailable, the script will exit with `DATA_UNAVAILABLE`.
-   **Retention Rate < 95%**: If the pipeline halts with "SC-005 Violation", check the logs to see which records were filtered out. The dataset may not contain enough valid entries for the target families.
-   **Missing Periodic Data**: If `mendeleev` fails to find an element, the record is skipped. Check `logs/ingestion.log` for warnings.
-   **Memory Error**: If running out of RAM, ensure you are not loading the full dataset (if it exists) into memory. The script defaults to streaming/parsing in chunks if available.