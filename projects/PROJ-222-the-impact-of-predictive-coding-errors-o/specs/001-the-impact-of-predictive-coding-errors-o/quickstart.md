# Quickstart: The Impact of Predictive Coding Errors on Subjective Time Perception

## Prerequisites
- Python 3.11+
- Git
- Docker (optional, for reproducibility)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-222-the-impact-of-predictive-coding-errors-o
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

## Data Acquisition

Run the download script to fetch datasets from the verified sources:
```bash
python code/download.py
```
*Note: This script checks the "Verified datasets" list. If no suitable data is found (Gate 0), it will log a CRITICAL BLOCKER in `data/README.md` and halt.*

## Preprocessing

Compute surprisal metrics and standardize data:
```bash
python code/preprocess.py
```
*Output: Standardized CSV files in `data/processed/`.*

## Statistical Analysis

Fit the Linear Mixed-Effects Model and generate sensitivity analysis:
```bash
python code/analysis.py
```
*Output: Model results in `analysis/results.json` and `analysis/metrics.csv`.*

## Visualization

Generate forest plots and residual diagnostics:
```bash
python code/visualize.py
```
*Output: Plots in `figures/`.*

## Reproducibility (Docker)

Build and run the Docker container:
```bash
docker build -t time-perception-analysis .
docker run --rm time-perception-analysis
```

## Verification

To verify the pipeline:
1.  Check `data/README.md` for dataset exclusion logs or blocker messages.
2.  Ensure `figures/` contains at least one forest plot and one residual plot (if data was valid).
3.  Verify `analysis/results.json` contains effect sizes, p-values, and MDE (if data was valid).
4.  **Important**: If `data/README.md` states "CRITICAL BLOCKER", the project is blocked due to lack of valid data.