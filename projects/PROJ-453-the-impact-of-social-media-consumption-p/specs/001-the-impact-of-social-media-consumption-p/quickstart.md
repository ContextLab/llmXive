# Quickstart: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

## Prerequisites

-   Python 3.11+
-   `pip` or `poetry`
-   Internet access (for dataset download)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-453-the-impact-of-social-media-consumption-p
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

The pipeline is executed in sequential steps.

### Step 1: Data Ingestion & Feasibility Check
Download and parse the dataset. **This step verifies the presence of required variables.**
```bash
python code/01_ingest.py
```
*Output*: `data/processed/participants_cleaned.csv` (or a "Data Gap" error if variables are missing).

### Step 2: Feature Engineering
Compute derived variables (`switching_index`) and document instrument sources.
```bash
python code/02_engineer.py
```
*Output*: Updated `data/processed/participants_cleaned.csv` with derived columns.

### Step 3: Model Fitting & Diagnostics
Fit regression, compute VIF, run sensitivity analysis, and **validate for causal language**.
```bash
python code/03_model.py
```
*Output*: `results/models/regression_summary.json`, `results/models/sensitivity_analysis.json`

### Step 4: Visualization
Generate plots.
```bash
python code/04_visualize.py
```
*Output*: `results/figures/regression_plot.png`, `results/figures/sensitivity_table.png`

## Validation

Run the test suite to ensure contract compliance:
```bash
pytest tests/
```

## Troubleshooting

-   **Missing Data**: If `01_ingest.py` fails with "Data Gap", check the "Verified datasets" block. If the HILDA `meta.json` does not resolve to a full dataset with cognitive measures, the project cannot proceed.
-   **Memory Error**: If `pandas` fails due to RAM, enable streaming mode in `01_ingest.py` (if supported by the loader) or reduce the sample size.
-   **Collinearity Warning**: If VIF > 5 or correlation > 0.7, check `results/models/regression_summary.json` for the `collinearity_flag` and `residualized_model_used`. The script will automatically run the residualized model.
-   **Causal Language Error**: If `03_model.py` fails, it means the generated `interpretation` string contains forbidden terms (e.g., "causes"). Review the model code to ensure associational phrasing.