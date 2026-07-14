# Quickstart Guide: CPU-Only Execution

## 1. Environment Setup
Ensure you have Python 3.11+ installed.
Install dependencies:
```bash
pip install -r requirements.txt
```

## 2. Data Preparation
The pipeline expects data in `data/raw/`.
If missing, run:
```bash
python code/data/download.py
```

## 3. Running the Pipeline
Execute the main orchestrator:
```bash
python code/main.py
```
This will:
- Stratify the dataset (US1)
- Extract features (US1)
- Solve geometry and warp (US2)
- Compute metrics and ANOVA (US3)
- Generate reports

## 4. Validation (T024)
Verify the entire pipeline ran correctly:
```bash
python code/eval/quickstart_validation_runner.py
```
Expected output: `Overall Status: PASS`

## 5. CPU Constraints
- All operations are CPU-bound.
- Memory limit is set to 8GB by default (configurable in `config.py`).
- Batch processing is automatically triggered if memory usage exceeds 6GB.