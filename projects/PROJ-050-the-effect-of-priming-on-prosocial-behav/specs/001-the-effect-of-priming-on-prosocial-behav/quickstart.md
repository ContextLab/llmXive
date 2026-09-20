# Quickstart: The Effect of Priming on Prosocial Behavior (Association Study)

## Prerequisites

- Python 3.11+
- `pip`
- Access to GitHub Actions (for CI execution) or a local environment with internet access.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-050-the-effect-of-priming-on-prosocial-behav
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

## Execution Steps

### Step 1: Data Ingestion
Run the ingestion script to fetch, filter, and anonymize data.
```bash
python code/01_ingest.py
```
- **Output**: `data/processed/anonymized.csv`, `data/processed/raw_counts.json`.
- **Note**: This step may take time depending on the dataset size. It uses streaming to stay within memory limits.

### Step 2: Scoring & Validation
Run the scoring script to compute sentiment and keyword counts.
```bash
python code/02_score.py
```
- **Output**: `data/processed/scored.csv`, `data/annotations/validation_report.json`.
- **Note**: This step includes the validation logic for the N=200 sample.

### Step 3: Statistical Analysis
Run the analysis script to fit the GLMM.
```bash
python code/03_analyze.py
```
- **Output**: `artifacts/results.json`, `artifacts/figures/glmm_plot.png`.
- **Success Check**: The script will exit with code 0 only if the model converges and `p-value < 0.05`. Otherwise, it will report the specific failure (convergence or significance).

### Step 4: Verification
Run the test suite to ensure all unit tests pass (including T011, T012, T015b).
```bash
pytest tests/
```

## Troubleshooting

- **Convergence Failure**: If the GLMM fails to converge, check the data for outliers or try reducing the sample size (if N is too large) or increasing the number of iterations in `code/03_analyze.py`.
- **Data Fetching Errors**: If the HuggingFace dataset is unavailable, check the `research.md` for alternative verified sources or ensure internet connectivity.
- **Memory Errors**: If you encounter OOM errors, ensure `streaming=True` is used in the ingestion step and that no intermediate dataframes are duplicated in memory.