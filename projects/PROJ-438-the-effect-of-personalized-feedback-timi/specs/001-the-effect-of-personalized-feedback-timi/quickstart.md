# Quickstart: The Effect of Personalized Feedback Timing on Skill Acquisition

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions (for CI) or a local environment with sufficient RAM.

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-438-the-effect-of-personalized-feedback-timi
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `statsmodels`, `pandas`, and `numpy` are installed.
    ```bash
    python -c "import statsmodels; import pandas; print('OK')"
    ```

## Running the Pipeline

### 1. Download Data
Download the OULAD dataset and cache it locally.
```bash
python code/download_data.py
```
*Output*: `data/raw/oulad.json` and `data/checksums.txt`.

### 2. Preprocess Data
Filter courses and extract learner records.
```bash
python code/preprocess.py
```
*Output*: `data/processed/courses_filtered.csv`, `data/processed/learner_intervals.csv`.

### 3. Run Analysis
Fit the Cluster-Robust OLS and perform post-hoc tests.
```bash
python code/models.py
```
*Output*: `data/processed/ols_results.csv`.

### 4. Sensitivity Analysis
Run the boundary sweep.
```bash
python code/sensitivity.py
```
*Output*: `data/processed/sensitivity_results.csv`.

### 5. Generate Report
Compile results and literature checks.
```bash
python code/report.py
```
*Output*: `data/processed/final_report.md`.

## Testing

Run the unit tests to verify logic:
```bash
pytest tests/ -v
```

## Troubleshooting
- **Missing Timestamps**: If the pipeline fails due to missing `response_timestamp`, check the `missing_response_flag` in `learner_intervals.csv`. The analysis proceeds with the forum reply proxy if available.
- **Memory Error**: If RAM usage exceeds 7GB, the pipeline will automatically sample to N=5,000 learners (log message: "Sampling to N=5000").
- **Model Convergence**: If the model fails, check for collinearity or insufficient data in specific groups.