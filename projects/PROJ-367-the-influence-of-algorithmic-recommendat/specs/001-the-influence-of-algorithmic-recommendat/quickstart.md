# Quickstart: The Influence of Algorithmic Recommendations on Exploration vs. Exploitation in Online Learning

## Prerequisites

- Python 3.11 or higher.
- Access to the verified datasets (see `research.md`). **A verified educational dataset is required.**
- A GitHub Actions free-tier runner (2 CPU, ~7 GB RAM) for CI execution.

## Installation

1. Clone the repository and navigate to the project directory.
2. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```
3. Verify the installation by running the unit tests:
   ```bash
   pytest tests/unit/
   ```

## Data Preparation

1. **Download the Dataset**: Use the verified URLs from `research.md` to download the dataset.
   ```bash
   # Example for a Hugging Face dataset
   python -c "from datasets import load_dataset; ds = load_dataset('educational_dataset_name', split='train'); ds.to_parquet('data/raw/dataset.parquet')"
   ```
   *Note: The dataset MUST contain educational course categories. If not, the ingestion script will raise a `DataSchemaError`.*

2. **Checksum Verification**: Record the checksum of the downloaded file in `state/projects/PROJ-367-the-influence-of-algorithmic-recommendat.yaml`.

## Running the Pipeline

1. **Ingestion and Preprocessing**:
   ```bash
   python code/ingestion.py --input data/raw/dataset.parquet --output data/processed/processed_data.csv
   ```
   This step calculates entropy scores directly on raw categories, handles missing data, **excludes users with no baseline history, and validates causal independence.**

2. **Modeling**:
   ```bash
   python code/modeling.py --input data/processed/processed_data.csv --output data/results/model_results.json
   ```
   This step fits the weighted linear regression (with Overlap Weighting fallback) and calculates diagnostics.

3. **Robustness Analysis**:
   ```bash
   python code/robustness.py --input data/processed/processed_data.csv --output data/results/robustness_results.json
   ```
   This step performs the **Residual Permutation Test**. **No sensitivity analysis for semantic thresholds is performed.**

4. **Report Generation**:
   ```bash
   python code/report.py --input data/results/ --output docs/final_report.md
   ```

## Verification

- **Unit Tests**: Run `pytest tests/unit/` to verify entropy calculations and data ingestion.
- **Integration Tests**: Run `pytest tests/integration/` to verify the full pipeline.
- **Reproducibility**: Re-run the pipeline on a fresh runner and compare the output checksums.
- **Runtime Metric**: The pipeline logs the total runtime to the output schema (e.g., `output.schema.yaml`) to satisfy SC-005. If runtime > 6h, a warning is recorded.

## Troubleshooting

- **DataSchemaError**: If the dataset lacks `recommended_categories` or `enrolled_categories`, **or if the dataset is not educational**, the pipeline will stop. Check the dataset schema against the spec.
- **Extreme Weights**: If the PSW model produces extreme weights (>10x median), the system will apply **Overlap Weighting** instead of falling back to standard linear regression. Check the logs for details.
- **Convergence Issues**: If the PSW model fails to converge, the system will apply **Overlap Weighting**. Check the logs for details.
- **No Baseline History**: Users with no prior enrollment history are excluded from the analysis. Check the logs for the count of excluded users.
- **Runtime Warning**: If the pipeline exceeds 6 hours, a warning flag is recorded in the output. The pipeline is designed to be CPU-trivial to avoid this.