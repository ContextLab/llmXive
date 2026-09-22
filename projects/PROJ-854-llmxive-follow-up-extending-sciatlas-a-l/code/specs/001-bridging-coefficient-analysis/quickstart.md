# Quickstart Guide: Bridging Coefficient Analysis

## Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)
- Required packages: `networkx`, `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pyarrow`, `datasets`, `memory-profiler`, `pytest`, `ruff`, `black`

## Installation

1. Create and activate virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # On Windows:.venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Run the Pipeline

The pipeline can be executed step-by-step or end-to-end using the CLI:

```bash
# Run the full pipeline with a sample size of 1000 nodes
python -m src.cli.main --sample-size 1000

# Run individual steps
python -m src.cli.main --step ingest --sample-size 1000
python -m src.cli.main --step embeddings --batch-size 64
python -m src.cli.main --step analysis
python -m src.cli.main --step report
```

For the final dataset generation:
```bash
python code/scripts/save_final_dataset.py
```

## Validation

To validate the pipeline and artifacts:

```bash
python -m src.cli.main --run-validation
```

This will generate a validation report at `artifacts/validation_report.md`.

## Output Artifacts

The pipeline produces the following key artifacts:

- `data/processed/subgraph_with_clusters.parquet`: Processed graph with topological clusters and bridging coefficients
- `data/processed/final_analysis_dataset.parquet`: Final dataset with citations, novelty scores, and all cluster assignments
- `artifacts/results/analysis_report.md`: Final analysis report
- `artifacts/results/statistical_metrics.json`: Statistical metrics and p-values
- `artifacts/results/corrected_pvalues.json`: Multiple-comparison corrected p-values

## Troubleshooting

- If you encounter memory issues, reduce the `--sample-size` parameter
- For embedding speed issues, ensure you're using CPU mode as specified
- Check `artifacts/results/memory_profile.log` for memory usage details