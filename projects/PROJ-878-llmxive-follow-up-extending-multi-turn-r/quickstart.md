# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- Virtual environment

## Setup

1. Create virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # Linux/Mac
 # or venv\Scripts\activate # Windows
 ```

2. Install dependencies:
 ```bash
 pip install -r code/requirements.txt
 ```

3. Configure environment (e.g., set MODEL_PATH in `.env`):
 ```bash
 python code/setup_env.py
 ```

## Execution Pipeline

### Step 1: Generate Primary Synthetic Dataset (US‑1)

```bash
python code/graph_generator.py \
 --count 500 \
 --depth-min 3 \
 --depth-max 6 \
 --branch-min 1 \
 --branch-max 5 \
 --output data/raw/synthetic_puzzles.jsonl \
 --seed 42
```

This creates `data/raw/synthetic_puzzles.jsonl` containing exactly 500 puzzles
with controlled topology and orthogonalized metrics. It also writes
`data/validation_metrics.json`, `data/checksums_primary.txt`, and
`data/validation_metrics.json` (updated with primary‑only stats).

### Step 2: Generate Auxiliary Dataset (for tipping‑point analysis)

```bash
python code/graph_generator.py \
 --count 200 \
 --depth-min 7 \
 --depth-max 10 \
 --branch-min 1 \
 --branch-max 5 \
 --output data/raw/aux_puzzles.jsonl \
 --seed 123
```

This creates `data/raw/aux_puzzles.jsonl`. After both files exist,
re‑run the validation step to recompute the combined correlation and
update `data/validation_metrics.json`:

```bash
python -c "
import json, hashlib, pathlib, sys
primary = pathlib.Path('data/raw/synthetic_puzzles.jsonl')
aux = pathlib.Path('data/raw/aux_puzzles.jsonl')
if primary.exists() and aux.exists():
 import code.graph_generator as gg
 # Load generated records (the script writes them already; we just recompute metrics)
 # The script's internal functions are reused via a small helper:
 from code.graph_generator import _write_validation_metrics, _write_checksums
 # Load JSONL records
 def load(path):
 recs = []
 with open(path, 'r', encoding='utf-8') as f:
 for line in f:
 recs.append(json.loads(line))
 return recs
 primary_recs = load(primary)
 aux_recs = load(aux)
 _write_validation_metrics(primary_recs, aux_recs, pathlib.Path('data/validation_metrics.json'), 0, 0)
 _write_checksums([primary, aux], pathlib.Path('data/checksums_aux.txt'))
 print('Auxiliary validation metrics and checksums updated.')
else:
 sys.exit('Primary or auxiliary dataset missing.')
"
```

### Step 3: Execute Reflective Masking Loop (US‑2)

```bash
python code/rm_executor.py \
 --input data/raw/synthetic_puzzles.jsonl \
 --output data/processed/execution_log.csv \
 --max-turns 50 \
 --batch-size 5 \
 --device cpu
```

### Step 4: Calculate Execution Metrics (adds path coverage, divergence)

```bash
python code/write_execution_results.py \
 --execution-log data/processed/execution_log.csv \
 --puzzles data/raw/synthetic_puzzles.jsonl \
 --output data/processed/execution_log.csv
```

### Step 5: Extended Budget Validation (US‑2 – T028)

```bash
python code/extended_budget_runner.py \
 --input data/processed/execution_log.csv \
 --puzzles data/raw/synthetic_puzzles.jsonl \
 --output data/processed/extended_budget_log.csv \
 --max-turns 1000 \
 --device cpu
```

### Step 6: Statistical Analysis (US‑3)

```bash
python code/analyzer.py \
 --puzzles data/raw/synthetic_puzzles.jsonl \
 --results data/processed/execution_log.csv \
 --output results/statistical_report.json \
 --thresholds 40 50 60
```

### Step 7: Verify Checksums

```bash
sha256sum -c data/checksums_primary.txt data/checksums_aux.txt
```

## Verification

1. Count primary puzzles:
 ```bash
 wc -l data/raw/synthetic_puzzles.jsonl
 ```
2. Inspect validation metrics:
 ```bash
 cat data/validation_metrics.json
 ```
3. Run unit tests:
 ```bash
 pytest tests/ -v
 ```

## Notes

- All scripts are deterministic given the seed arguments. [UNRESOLVED-CLAIM: c_0a90bf4b — status=not_enough_info]
- The generation script enforces orthogonalization (|r| < 0.2) across the combined dataset. [UNRESOLVED-CLAIM: c_9c7288be — status=not_enough_info]
- If the auxiliary dataset is generated after the primary one, re‑run the validation step (above) to update the combined correlation and checksums.