# Quickstart: Quantifying Neural Representation Drift

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local environment with 2 CPU cores, 7 GB RAM).

## Installation

1.  Clone the repository and navigate to the project directory.
2.  Install dependencies:
    ```bash
    cd projects/PROJ-171-quantifying-neural-representation-drift-/code
    pip install -r requirements.txt
    ```

## Running the Pipeline

The pipeline is designed to run on **synthetic data** by default, as no verified real-world dataset with the required variables exists.

### 1. Generate Synthetic Data
```bash
python -m code.data_ingestion --mode=synthetic --seed=42 --subjects=20 --days=10
```
*This creates `data/derived/synthetic_data.parquet` with known ground-truth drift parameters.*

### 2. Run Drift Analysis
```bash
python -m code.main --input=data/derived/synthetic_data.parquet --output=data/artifacts/results.json
```
*This executes the full pipeline: unit filtering, RDM computation, drift rate fitting, and correlation analysis.*

### 3. Run Robustness Checks
```bash
python -m code.robustness --input=data/derived/synthetic_data.parquet --metrics="pearson,cosine,mahalanobis"
```
*This sweeps distance metrics and unit stability thresholds.*

## Testing

Run the unit tests to verify the pipeline against synthetic ground truth:
```bash
pytest tests/unit/ -v
```
*Tests verify that the recovered drift rate `b` matches the synthetic ground truth within 5% error.*

## Output Artifacts

- `data/artifacts/results.json`: Final drift rates and correlation statistics.
- `data/artifacts/plots/drift_vs_learning.png`: Visualization of the correlation.
- `data/artifacts/plots/robustness_sweep.png`: Sensitivity analysis plots.
