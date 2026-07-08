# Quickstart: Evaluating the Sensitivity of Regression Models to Outlier Removal Strategies

## Prerequisites

- Python 3.11+
- `pip`

## Installation

1.  **Clone the repository** (or navigate to the project directory).
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` will pin `ucimlrepo`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn`, `requests`.*

## Running the Pipeline

### Full Analysis (15 Datasets)
Run the main script to execute the full sensitivity analysis:
```bash
python code/main.py --datasets 15 --strategies all
```
*This will download a set of UCI regression datasets, run the IQR/Z-score/Cook's pipeline (using Union logic), perform the Wilcoxon Signed-Rank and Paired t-tests, and generate `outputs/report.pdf`.*

### MVP Mode (California Housing Only)
Run the MVP test case:
```bash
python code/main.py --datasets california_housing --strategies iqr
```
*This downloads only the California Housing dataset, runs Raw vs. IQR (Union logic), and outputs a CSV summary.*

### Sensitivity Sweep
Run the IQR multiplier sweep:
```bash
python code/main.py --datasets 5 --sweep iqr
```
*This runs the analysis on multiple datasets with IQR multipliers spanning a range of values.*

## Output Artifacts

- `outputs/results.json`: Machine-readable metrics for all datasets and strategies.
- `outputs/report.pdf`: Visualization (boxplots of R²/RMSE changes, statistical test results).
- `data/raw/`: Downloaded raw datasets (checksummed).
- `data/processed/`: Preprocessed datasets.

## Troubleshooting

- **Network Error**: The pipeline has built-in retry logic (a limited number of retries, a fixed backoff interval). If a dataset fails, it is skipped and logged.
- **Memory Error**: If RAM usage exceeds a high threshold, the pipeline will exit. This is unlikely with UCI datasets but can happen if a very large dataset is selected.
- **No Continuous Features**: If a dataset has no continuous features, IQR/Z-score are skipped, and a warning is logged.