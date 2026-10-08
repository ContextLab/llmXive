# Quickstart Guide

## Prerequisites

- Python 3.11+
- pip
- Virtual environment

## Setup

1. Create virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate # Linux/Mac
 # or.venv\Scripts\activate # Windows
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Configure environment:
 ```bash
 python code/setup_env.py
 ```

## Execution Pipeline

### Step 1: Generate Synthetic Data (US1)

```bash
python code/graph_generator.py --output data/raw/logical_puzzles.jsonl --n 100
python code/perturb_ground_truth.py --input data/raw/logical_puzzles.jsonl --output data/raw/logical_puzzles.jsonl
python code/write_puzzles.py --input data/raw/logical_puzzles.jsonl --output data/raw/logical_puzzles.jsonl
python code/generate_checksums.py --file data/raw/logical_puzzles.jsonl --output data/checksums.txt
```

### Step 2: Execute Reflective Masking (US2)

```bash
python code/rm_executor.py \
 --input data/raw/logical_puzzles.jsonl \
 --output data/processed/execution_log.csv \
 --max-turns 50 \
 --batch-size 5 \
 --device cpu
```

### Step 3: Calculate Execution Metrics (US2)

```bash
python code/execution_metrics.py \
 --puzzles data/raw/logical_puzzles.jsonl \
 --results data/processed/execution_log.csv \
 --output data/processed/execution_log.csv
```

### Step 4: Extended Budget Validation (US2 - T028)

```bash
python code/extended_budget_runner.py \
 --input data/processed/execution_log.csv \
 --puzzles data/raw/logical_puzzles.jsonl \
 --output data/processed/extended_budget_log.csv \
 --max-turns 1000 \
 --device cpu
```

### Step 5: Statistical Analysis (US3)

```bash
python code/analyzer.py \
 --puzzles data/raw/logical_puzzles.jsonl \
 --results data/processed/execution_log.csv \
 --extended-results data/processed/extended_budget_log.csv \
 --output results/statistical_report.md \
 --thresholds 40 50 60
```

## Verification

1. Check file existence:
 ```bash
 ls -la data/raw/logical_puzzles.jsonl
 ls -la data/processed/execution_log.csv
 ls -la data/processed/extended_budget_log.csv
 ls -la results/statistical_report.md
 ```

2. Verify checksums:
 ```bash
 sha256sum -c data/checksums.txt
 ```

3. Run tests:
 ```bash
 pytest tests/ -v
 ```

## Notes

- All scripts must complete successfully before proceeding to the next step.
- The extended budget run (Step 4) is critical for validating convergence behavior.
- Ensure sufficient disk space for intermediate files.