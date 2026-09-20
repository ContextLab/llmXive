# Quickstart Guide

This guide provides the steps to get the PROJ-540 pipeline running immediately.

## 1. Prerequisites

Ensure you have the following installed:
- Python 3.11 or higher
- `pip`

## 2. Installation

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-540-the-influence-of-social-media-doomscroll
pip install -r requirements.txt
```

## 3. Configuration

The pipeline relies on a configuration file or environment variables to locate the dataset.

**Option A: Environment Variables**
```bash
export DOOMSCROLL_DATASET_URL=""
export RANDOM_SEED=42
```

**Option B: config.yaml**
Create a `config.yaml` file in the root directory:
```yaml
dataset_url: ""
seed: 42
```

## 4. Running the Pipeline

Execute the main pipeline script:

```bash
python code/main_pipeline.py
```

**What happens?**
1. **Download**: Fetches the dataset from the configured URL.
2. **Validate**: Checks for required columns (`news_exposure_freq`, `anxiety_score`, etc.).
3. **Clean**: Removes rows with missing values.
 - *Note*: If the remaining sample size $N < 130$, the process halts with a `PowerLimitationError`.
4. **Model**: Fits the OLS regression and calculates correlations.
5. **Validate**: Checks for mathematical coupling and statistical assumptions.
6. **Robustness**: Performs the conditional robustness check.
7. **Visualize**: Generates diagnostic plots and scatter plots.
8. **Report**: Generates `outputs/final_report.md`.

## 5. Verifying Results

After successful execution, check the `outputs/` directory:

- `final_report.md`: The comprehensive research report.
- `regression_results.json`: Detailed statistical coefficients.
- `plot.png`: The primary scatter plot with regression line.
- `diagnostics_residuals.png`: Model diagnostic plots.

## 6. Troubleshooting

### "Data Fetch Failed"
Ensure the `DOOMSCROLL_DATASET_URL` is correct and accessible. The system does not generate synthetic data; it will crash if the real data is missing.

### "Power Limitation Error"
The dataset provided has fewer than 130 valid rows. This is a deliberate safeguard to ensure statistical power. Provide a larger dataset.

### "Mathematical Coupling Detected"
The variables `baseline_anxiety` and `anxiety_score` appear to be derived from the same instrument or time point. Verify your data schema.
