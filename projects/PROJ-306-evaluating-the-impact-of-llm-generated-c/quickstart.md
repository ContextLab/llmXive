# Quickstart Guide

## Prerequisites

- Python 3.8+
- Virtualenv

## Setup

1. Create and activate virtualenv:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

2. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

3. Set environment variables (optional):
 ```bash
 export LLM_API_KEY="your_key_here"
 ```

## Execution Flow

### 1. Initialize Directories and Load Data
```bash
python code/setup_directories.py
python code/dataset_loader.py
python code/test_transformer.py
```

### 2. Run Generation and Coverage (US1)
```bash
python code/main.py --num-tasks 100 --output-dir data/processed
```

### 3. Run Statistical Analysis (US2)
```bash
python code/analyzer.py --coverage-dir data/coverage_reports --output-dir data/processed
python code/sensitivity_analyzer.py --coverage-dir data/coverage_reports --output data/processed/sensitivity_report.csv
```

### 4. Run Stratification and Visualization (US3)
```bash
python code/visualizer.py --coverage-dir data/coverage_reports --catalog data/benchmarks/processed/catalog.json --output-dir outputs
python code/stratifier.py --input outputs/annotated_tasks.json --output-dir outputs
```

## Validation

Run the validation script to ensure all artifacts are present:
```bash
python code/task_t050_validate_quickstart.py
```

## Expected Artifacts

- `data/benchmarks/processed/catalog.json`
- `data/processed/stats_summary.csv`
- `data/processed/corrected_pvalues.csv`
- `data/processed/sensitivity_report.csv`
- `outputs/coverage_by_pattern_*.png`
- `outputs/stratified_*.csv`