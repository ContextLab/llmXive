# Quickstart Guide: Interdisciplinary Bridging Coefficient Analysis

## Prerequisites

- Python 3.9+
- `pip install -r requirements.txt`
- **Data Access**: The pipeline requires access to OpenAlex data via `pyalex`.
 - Install: `pip install pyalex>=1.0`
 - Install: `pip install sentence-transformers`
- Ensure you have write permissions to `data/` and `artifacts/`.

## Installation

1. Clone the repository.
2. Install dependencies:
 ```bash
 pip install -e.
 ```
3. Verify installation:
 ```bash
 python -c "import src; print('Installation OK')"
 ```

## Running the Pipeline

The full analysis pipeline consists of several stages. You can run them individually or all at once.

### Option 1: Run Full Pipeline (Recommended for Validation)

Execute the main script with a sample size:
```bash
python -m src.cli.main --sample-size 1000
```

### Option 2: Run Individual Stages

1. **Ingest Data**:
 ```bash
 python code/scripts/save_graph_pipeline.py
 ```
 *Output*: `data/processed/subgraph_with_clusters.parquet`

2. **Compute Embeddings & Novelty**:
 (Handled automatically by the main script or `save_final_dataset.py`)

3. **Save Final Dataset**:
 ```bash
 python code/scripts/save_final_dataset.py
 ```
 *Output*: `data/processed/final_analysis_dataset.parquet`

4. **Run Statistical Analysis**:
 ```bash
 python code/scripts/save_statistical_metrics.py --correction-method bh
 ```
 *Output*: `artifacts/results/statistical_metrics.json`, `artifacts/results/corrected_pvalues.json`

5. **Generate Report**:
 ```bash
 python code/scripts/generate_analysis_report.py
 ```
 *Output*: `artifacts/results/analysis_report.md`

### Validation Mode

Run the validation suite to check artifacts:
```bash
python code/scripts/run_validation.py
```
*Output*: `artifacts/validation_report.md`

## Expected Artifacts

After a successful run, you should find:

- `data/processed/subgraph_with_clusters.parquet`
- `data/processed/final_analysis_dataset.parquet`
- `artifacts/results/analysis_report.md`
- `artifacts/results/statistical_metrics.json`
- `artifacts/results/corrected_pvalues.json`
- `artifacts/results/binned_analysis.json`
- `artifacts/validation_report.md`

## Troubleshooting

- **OpenAlex Unreachable**: Check your internet connection. The API is free but requires network access.
- **Memory Errors**: Reduce `--sample-size` if you encounter memory issues.
- **Import Errors**: Ensure you are running from the project root and `pip install -e.` was successful.