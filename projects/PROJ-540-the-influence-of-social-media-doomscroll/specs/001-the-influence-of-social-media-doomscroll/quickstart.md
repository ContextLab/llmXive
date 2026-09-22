# Quickstart: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Prerequisites

- Python 3.11+
- Access to a GitHub Actions runner (or local environment with sufficient RAM).
- Network access to Hugging Face or CDC NHANES.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-540-the-influence-of-social-media-doomscroll
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### 1. Data Ingestion and Cleaning

Run the ingestion script to download the dataset, verify the schema, and clean the data.

```bash
python code/ingest.py
```

*Output*: `data/processed/cleaned_data.csv` and `data/raw/checksums.txt`.

*Note*: If the dataset schema is missing required columns, the script will halt with an error.

### 2. Statistical Modeling

Run the modeling script to fit the regression, check assumptions, and perform robustness checks.

```bash
python code/model.py
```

*Output*: `output/results/regression_results.json`, `output/results/diagnostics.json`.

### 3. Visualization

Generate the scatter plot with regression line.

```bash
python code/viz.py
```

*Output*: `output/plots/scatter_regression.png`.

### 4. Full Pipeline

Run the orchestration script to execute all steps in sequence.

```bash
python code/main.py
```

## Verification

- **Check Data**: Ensure `data/processed/cleaned_data.csv` exists and has > 30 rows.
- **Check Results**: Verify `output/results/regression_results.json` contains a `p_value` for `news_exposure_freq`.
- **Check Plots**: Verify `output/plots/scatter_regression.png` displays a regression line and confidence interval.
- **Check Runtime**: Verify `output/results/regression_results.json` contains a `runtime` field ≤ 60 seconds.

## Troubleshooting

- **Error: "Missing required columns"**: The dataset at the provided URL does not contain the necessary variables. Check `research.md` for the list of required columns.
- **Error: "Sample size < 30"**: The dataset has too few valid records after cleaning. The pipeline halts as per FR-002.
- **Error: "VIF > 10"**: Multicollinearity detected. Check `output/results/diagnostics.json` for the specific variable.
- **Error: "Construct Coupling Detected"**: Baseline and outcome anxiety are not distinct. The baseline covariate was dropped.
