# Quickstart Guide

## Prerequisites
- Python 3.9+
- pip
- **pyalex>=1.0**
- **sentence-transformers**
- networkx
- scikit-learn
- pandas
- numpy
- scipy
- memory-profiler
- pytest
- ruff
- black

## Installation
```bash
pip install -e.
```

## Run
To run the full analysis pipeline:
```bash
python -m src.cli.main --sample-size 1000
```

Alternatively, run individual steps:
```bash
# Fetch and build subgraph, cluster, and save
python code/scripts/save_graph_pipeline.py

# Generate embeddings and novelty scores (US2)
python code/scripts/save_final_dataset.py

# Run statistical analysis (US3)
python code/scripts/save_statistical_metrics.py --correction-method bh

# Generate report
python code/scripts/generate_analysis_report.py
```

## Validation
```bash
python code/scripts/run_validation.py
```