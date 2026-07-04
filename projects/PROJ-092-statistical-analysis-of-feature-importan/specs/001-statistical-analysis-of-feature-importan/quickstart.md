# Quickstart: Feature Importance Drift Analysis

## Prerequisites

- Python 3.11+
- `pip`
- Access to the UCI Electricity Load Diagrams dataset (download script included).

## Installation

1. **Clone the repository** and navigate to the project directory.
   ```bash
   git clone <repo-url>
   cd projects/PROJ-092-statistical-analysis-of-feature-importan
   ```

2. **Create a virtual environment** and install dependencies.
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The entire analysis is orchestrated via `code/main.py`.

```bash
python code/main.py
```

### What happens?
1. **Download**: Fetches the dataset from UCI (or fails if unreachable).
2. **Preprocess**: Imputes missing values and splits into 30-day windows.
3. **Train**: Trains a Random Forest on each window and computes importance.
4. **Analyze**: Calculates Spearman correlations and runs the block permutation test.
5. **Output**: Generates `outputs/drift_metrics.csv` and `outputs/global_stats.json`.

## Verifying Results

1. **Check the logs**: Ensure no "Model Failure" errors exceed 50% of windows.
2. **Inspect outputs**:
   ```bash
   cat outputs/global_stats.json
   head outputs/drift_metrics.csv
   ```
3. **Run Tests**:
   ```bash
   pytest tests/
   ```

## Troubleshooting

- **"Data Source Unreachable"**: The UCI archive might be down. Check your internet connection or the UCI website.
- **"Model Failure"**: If many windows fail ($R^2 < 0.8$), the data might be too noisy or the window size too small. Check `code/preprocess.py` for imputation issues.
- **Memory Error**: The dataset is small, but if you modify the window size to be very large, you may hit RAM limits. Reduce window size or increase RAM.
