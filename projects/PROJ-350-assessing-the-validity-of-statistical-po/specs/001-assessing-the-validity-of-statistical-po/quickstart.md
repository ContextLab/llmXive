# Quickstart: Assessing the Validity of Statistical Power

## Prerequisites

- Python 3.11+
- `pip` or `venv`
- Internet access (for OSF API and package downloads)

## Installation

1.  **Clone the repository** and navigate to the project directory.
    ```bash
    git clone <repo-url>
    cd projects/PROJ-350-assessing-the-validity-of-statistical-po
    ```

2.  **Create a virtual environment**.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**.
    ```bash
    pip install -r code/requirements.txt
    ```
    *Note: `requirements.txt` pins versions of `statsmodels`, `pandas`, `requests`, etc., to ensure reproducibility.*

## Running the Pipeline

The pipeline is executed via the `main.py` script in the `code/` directory.

### Step 1: Data Extraction
Extracts data from OSF for a specified list of study IDs.
```bash
python code/main.py --action extract --ids "study_id_1,study_id_2,..."
```
*Output*: `data/derived/study_records.csv`

### Step 2: Power Calculation
Calculates sensitivity power and power gaps.
```bash
python code/main.py --action calculate
```
*Output*: `data/derived/power_analysis.csv`

### Step 3: Regression Analysis
Runs the regression model and diagnostics.
```bash
python code/main.py --action regression
```
*Output*: `data/derived/regression_results.json`, `figures/residual_plot.png`

### Step 4: Full Pipeline
Runs all steps in sequence (recommended for CI).
```bash
python code/main.py --action full
```

## Verifying Results

1.  **Check Logs**: Review `logs/pipeline.log` for any skipped studies or warnings (e.g., `missing_planned_data`).
2.  **Validate Output**: Ensure `data/derived/power_analysis.csv` contains the `power_gap` column.
3.  **Run Tests**:
    ```bash
    pytest tests/ -v
    ```
    *Tests verify extraction regex, power calculation logic, and VIF diagnostics.*

## Troubleshooting

- **API Rate Limit**: If the script fails with 429, it will automatically retry. If it exhausts retries, check your network or reduce the batch size.
- **Missing Dependencies**: Ensure you activated the virtual environment (`source venv/bin/activate`).
- **Memory Error**: If processing large batches, reduce the `--batch-size` argument in `main.py`.
