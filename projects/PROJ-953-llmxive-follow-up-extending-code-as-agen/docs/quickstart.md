# Quick‑Start Guide

This guide walks you through the end‑to‑end execution of the llmXive
follow‑up project on a fresh machine.

## Prerequisites

- Python 3.11 or newer
- Git
- Internet access (to download HuggingFace datasets)
- Sufficient disk space (≈ 2 GB) and RAM (≥ 4 GB recommended)

## Installation

1. **Clone the repository**
 ```bash
 git clone <repo-url>
 cd projects/PROJ-953-llmxive-follow-up-extending-code-as-agen
 ```

2. **Create a virtual environment**
 ```bash
 python -m venv venv
 source venv/bin/activate # Windows: venv\Scripts\activate
 ```

3. **Install pinned dependencies**
 ```bash
 pip install -r requirements.txt
 ```

4. **Log in to HuggingFace** (required for some datasets)
 ```bash
 huggingface-cli login
 ```

## Pipeline Execution

The pipeline is orchestrated via individual scripts located in `code/scripts/`.

### Step 0 – Pilot & Base‑Rate Estimation (optional)

```bash
python scripts/ingest.py --sample-size 100 --mode pilot
```

This creates `data/processed/pilot_stats.json` with an estimated failure rate.

### Step 1 – Ingest Data & Generate Ground Truth

```bash
python scripts/ingest.py --sample-size 500 --timeout 600
```

Outputs:
- `data/raw/swe_bench_agentbench_subset.csv`
- `data/logs/ingest_sample_log.json`
- `data/processed/ground_truth.csv`

### Step 2 – Extract Structural Features

```bash
python scripts/extract_features.py --input data/processed/ground_truth.csv
```

Outputs:
- `data/processed/features.csv`
- `data/graphs/<task_id>.json` (one per task)

### Step 3 – Train Predictive Models & Sensitivity Analysis

```bash
python scripts/train_model.py --input data/processed/features.csv --thresholds 0.01,0.05,0.1
```

Saves:
- `models/logistic_regression.pkl`
- `models/random_forest.pkl`
- `data/processed/threshold_sweep.json`
- `data/processed/model_report.json`

### Step 4 – Generate Research Report

```bash
python scripts/evaluate.py --model models/model.pkl --results data/processed/model_results.csv
```

Produces `reports/summary.md` summarizing findings, safety analysis, and
reduction metrics.

## Validation

Run the full test suite to verify contract compliance:

```bash
pytest -v
```

All tests should pass without errors. [UNRESOLVED-CLAIM: c_427eb613 — status=not_enough_info] If any test fails, inspect the
traceback, fix the underlying script, and re‑run the tests.

## Troubleshooting

- **MemoryError** – Reduce `--sample-size` or enable streaming in `ingest.py`.
- **Timeouts** – Increase `--timeout` or limit the number of tasks processed.
- **Parse Errors** – Check `data/processed/ground_truth.csv` for rows marked
 `status: Unparseable`; they are excluded from feature extraction.
- **Missing Files** – Ensure you have run each preceding step; the scripts
 write their outputs to the paths listed above.

## Next Steps

After a successful run, you can experiment with:

- Different model hyper‑parameters
- Alternative structural metrics (e.g., AST node counts)
- Larger sample sizes (subject to RAM constraints)
