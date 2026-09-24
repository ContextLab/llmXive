# Quickstart Guide

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`
- Dependencies: `networkx`, `scikit-learn`, `sentence-transformers`, `pandas`, `numpy`, `scipy`, `pyarrow`, `datasets`, `memory-profiler`, `pytest`, `ruff`, `black`.

## Setup
1. Clone the repository.
2. Create virtual environment: `python -m venv.venv && source.venv/bin/activate`.
3. Install dependencies: `pip install -e.`.

## Run
Execute the pipeline steps:
```bash
# Step 1: Ingest data (T012)
python code/scripts/ingest_data.py --sample-size 100

# Step 2: Save graph with clusters (T016)
python code/scripts/save_graph_pipeline.py

# Step 3: Compute embeddings and novelty (T020-T022)
python code/scripts/run_novelty_calculation.py

# Step 4: Save final dataset (T024)
python code/scripts/save_final_dataset.py

# Step 5: Statistical analysis (T026-T028)
python code/scripts/save_statistical_metrics.py

# Step 6: Generate report (T029)
python code/scripts/generate_analysis_report.py
```

## Validation
Run the validation script:
```bash
python code/scripts/run_validation.py --run-validation
```

## Sample Size Configuration
Use `--sample-size [REDACTED]` to control the number of nodes in the subgraph.