# Quickstart: The Impact of Musical Training on Functional Connectivity in Adolescent Brains

## 1. Prerequisites
- Python 3.11+
- ~a few GB free RAM
- Git

## 2. Installation
```bash
git clone <REPO_URL>
cd projects/PROJ-056-the-impact-of-musical-training-on-functi
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## 3. Running the Pipeline

### 3.1 Synthetic Verification Mode (default)
```bash
python code/main.py --mode synthetic --n-subjects 100 --seed 42
```
Generates a mock cohort, computes connectivity and network metrics, runs all statistical tests, and writes results under `data/processed/`.

Individual stages can be run directly:
```bash
python code/data/run_synthetic_generator.py --n-subjects 100 --seed 42
```

### 3.2 Real‑Data Mode (when a verified dataset becomes available)
```bash
python code/main.py --mode real --data-path /path/to/verified/dataset
```
If no path is supplied, the pipeline exits gracefully with a "data source unavailable" message and a JSON status file.

### 3.3 Smoke test
```bash
python code/run_quickstart_test.py
```
Runs the quickstart commands end‑to‑end and validates that all expected output files are generated.

## 4. Verify Outputs
```bash
pytest tests/
```