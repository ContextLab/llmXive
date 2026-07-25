# Quickstart Guide

## Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

## Execution Order

### 1. Setup & Download
```bash
python code/setup_project_structure.py
python code/data/download.py
python code/data/derive_gt.py
```

### 2. Data Curation
```bash
python code/data/curate.py
python code/data/validate_hard.py
```

### 3. Agent Execution
```bash
# Baseline
python code/agent/run_baseline.py --input data/results/locked_hard_subset.jsonl --output data/results/baseline_logs.jsonl

# Iterative
python code/agent/iterative.py --input data/results/locked_hard_subset.jsonl --output data/results/iterative_logs.jsonl --max-turns 3
```

### 4. Analysis & Metrics
```bash
# Generate Final Metrics
python code/analysis/generate_final_metrics.py

# Plotting
python code/analysis/plots.py --input data/results/final_metrics.json --output docs/figures/
```

### 5. Full Pipeline (Optional)
```bash
python code/main.py --max-hours 6
```

## Validation
Verify outputs:
- `data/curated/hard_subset.jsonl`
- `data/results/baseline_logs.jsonl`
- `data/results/iterative_logs.jsonl`
- `data/results/final_metrics.json`
- `docs/figures/coverage_hist.png`