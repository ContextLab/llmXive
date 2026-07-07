# Quickstart: Neural Correlates of Anticipatory Reward Processing

## Prerequisites

*   Python 3.10+
*   Git
*   Access to the repository.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-517-neural-correlates-anticipatory-reward
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
    *Dependencies include: `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`.*

## Running the Pipeline

### Option A: Run with Synthetic Data (CI/Testing Mode)
This mode generates a synthetic dataset that mimics the expected schema to validate the pipeline logic (FR-001 to FR-010) without needing external data.

```bash
python code/main.py --synthetic --seed 42
```

**Expected Output**:
*   `data/processed/synthetic_features.csv`: The aligned feature matrix.
*   `data/processed/results_summary.json`: Model coefficients and p-values.
*   `data/processed/plot_firing_vs_reward.png`: Scatter plot with regression line.
*   `data/processed/report.txt`: Human-readable summary.

### Option B: Run with Real Data
If you have a real dataset in `data/raw/` (CSV/Parquet), place the files there and run:

```bash
python code/main.py --input-dir data/raw/
```
*Note: The input files must strictly match the schema defined in `contracts/dataset.schema.yaml`.*

## Testing

Run the unit tests to verify data ingestion, model fitting, and validation logic:

```bash
pytest tests/ -v
```

## Verification

To verify the pipeline against the specification:
1.  Check that `data/processed/results_summary.json` contains `p_value_perm` < 0.05 (or > 0.05 for null data).
2.  Verify `data/processed/plot_firing_vs_reward.png` shows the correct axes and confidence intervals.
3.  Confirm `data/processed/report.txt` includes the dispersion parameter and MDES.
