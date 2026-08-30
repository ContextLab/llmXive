# Quickstart Guide

This guide provides a step-by-step walkthrough to run the PROJ-483 pipeline.

## Step 1: Setup Environment

```bash
# Clone and enter directory
git clone <repo-url>
cd PROJ-483-evaluating-the-robustness-of-common-stat

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Verify Configuration

Ensure `code/config.yaml` exists and contains valid parameters:
```yaml
random_seed: 42
alpha: 0.05
replications: 1000
dependency_strengths: [0.0, 0.3, 0.6, 0.9]
```

## Step 3: Fetch Datasets

Run the data loader to download and validate public datasets:
```bash
python code/run_data_loader.py
```
*Expected Output*:
- Datasets saved to `data/raw/`.
- Checksums saved to `data/manifests/checksums.json`.
- Validation report if any datasets fail checks.

## Step 4: Run the Simulation

Execute the main simulation script:
```bash
python code/main.py
```
*Expected Output*:
- `results/simulation_raw.csv`: Raw p-values from 10,000+ replications.
- `results/aggregated.csv`: Aggregated error rates and power metrics.
- `results/logistic_models.pkl`: Trained logistic regression models.
- `results/edge_case_report.json`: Logs of any edge cases encountered.

## Step 5: Generate Visualizations

Use the provided visualization script (or import `visualizer.py` in a notebook):
```python
import pandas as pd
from visualizer import plot_error_rate_curve

df = pd.read_csv("results/aggregated.csv")
plot_error_rate_curve(df, test_type="t-test", dependency="ar1", save_path="figures/error_rate_ttest_ar1.png")
```

## Step 6: Run Tests

Validate the implementation:
```bash
pytest tests/ -v
```

## Troubleshooting

- **Missing Dependencies**: Ensure all packages in `requirements.txt` are installed.
- **Data Fetch Failures**: Check network connectivity and verify URLs in `data/manifests/datasets.yaml`.
- **Validation Errors**: If `CriticalValidationError` is raised, check `results/validation_report.json` for details on dataset issues.
- **Performance**: For large replications, ensure sufficient RAM. The pipeline is optimized with vectorized NumPy operations.
