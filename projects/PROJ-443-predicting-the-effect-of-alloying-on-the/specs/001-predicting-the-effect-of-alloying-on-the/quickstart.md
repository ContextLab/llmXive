# Quickstart: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

## Prerequisites

-   Python 3.11+
-   `pip`
-   Access to GitHub Actions (for CI execution) or a local environment with 7 GB+ RAM.

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    cd projects/PROJ-443-predicting-the-effect-of-alloying-on-the
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

## Running the Pipeline

The pipeline is executed via the main entry point `code/main.py`.

### Full Pipeline Execution

```bash
python code/main.py --mode full
```

This command performs the following steps sequentially:
1.  **Fetch**: Downloads data from OQMD (using verified URLs).
2.  **Clean**: Normalizes compositions and filters for HEAs (≥5 elements).
3.  **Engineer**: Computes descriptors and applies ILR transformation.
4.  **Train**: Trains RF, GB, and ElasticNet models.
5.  **Evaluate**: Computes metrics, CIs, and permutation tests.
6.  **Report**: Generates `results/report.md` and `results/metrics.yaml`.

### Step-by-Step Execution

To run individual stages:

```bash
# Data Ingestion
python code/main.py --mode fetch

# Feature Engineering
python code/main.py --mode engineer

# Model Training & Evaluation
python code/main.py --mode train

# Interpretability & Reporting
python code/main.py --mode report
```

## Expected Outputs

-   `data/source_metadata.yaml`: Provenance of downloaded datasets.
-   `data/processed/heas_features.parquet`: Cleaned dataset with descriptors.
-   `results/metrics.yaml`: JSON/YAML containing R², RMSE, MAE, CIs, and p-values.
-   `results/plots/`: Directory containing parity plots, SHAP summary plots, and partial dependence plots.
-   `results/report.md`: Final summary with associational disclaimers.

## Troubleshooting

-   **Insufficient Data**: If the pipeline reports "Underpowered Study", check `results/report.md` for the specific sample count and confidence interval widening details.
-   **Circularity Warning**: If a "Potential circularity detected" warning appears, review the `results/report.md` section on Residual Validity.
-   **Memory Errors**: If the process exceeds 7 GB RAM, the pipeline will automatically downsample the dataset. Check logs for the sampling ratio.

## Validation

To verify the installation and data integrity:

```bash
pytest tests/contract/
pytest tests/integration/
```

Ensure all tests pass before proceeding to the research phase.
