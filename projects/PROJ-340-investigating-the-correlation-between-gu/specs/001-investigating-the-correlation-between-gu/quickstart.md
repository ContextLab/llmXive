# Quickstart: Gut Microbiome-Sleep Architecture

## Prerequisites

- Python 3.11+
- Git
- GitHub Account (for CI execution)

## Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-340-investigating-the-correlation-between-gu
    ```

2.  **Create Virtual Environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Pipeline

### Option 1: Synthetic Data (Default)
Run the pipeline with generated data to validate the implementation.
```bash
python code/main.py --mode synthetic
```
- **Expected Output**: `data/results/correlation_results.csv`, `data/results/vif_report.json`, `data/results/sensitivity_analysis.json`.
- **Duration**: < 5 minutes.

### Option 2: Real Data (If Available)
Place a valid CSV file at `data/raw/real_data.csv` and run:
```bash
python code/main.py --mode real
```
- **Note**: If `data/raw/real_data.csv` is missing, the pipeline will abort with a "RealDataFetchError" (per T081/T082).

## Verification

1.  **Check Timing**: Ensure `data/results/timing_evidence.json` shows execution time < 6 hours.
2.  **Check Validation**: Ensure `data/results/validation_failure_report.json` does not exist (indicating success).
3.  **Check Results**: Open `data/results/correlation_matrix.json` to verify `p_value_adjusted` and `is_significant` columns.
4.  **Check Causality**: Ensure all reports contain "Associational Finding:" and no causal language.

## CI/CD Execution

The pipeline runs automatically on `ubuntu-latest` via GitHub Actions:
1.  Push changes to `001-gut-microbiome-sleep-architecture`.
2.  Wait for the `analysis.yml` workflow to complete.
3.  Check "Actions" tab for logs and artifacts.

## Troubleshooting

- **"Missing Variable" Error**: Check `data/raw/synthetic_data.csv` (or real data) for required columns defined in `contracts/dataset_schema.yaml`.
- **"Power Limitation" Warning**: The sample size (N) is too small to detect the target effect size (r=0.3). Increase N in the synthetic generator or acknowledge the limitation in the report.
- **"Perfect Multicollinearity"**: Two predictors are linearly dependent. The system will flag this and exclude one from VIF calculation.
- **"CLR Transformation Failed"**: Ensure the data sum constraint is valid (no zero-sum rows).