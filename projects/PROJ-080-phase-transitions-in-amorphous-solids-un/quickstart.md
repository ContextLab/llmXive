# Quickstart Guide: Phase Transitions in Amorphous Solids

## Prerequisites
- Python 3.9+
- pip

## Setup
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Initialize project structure (Run T001a):
 ```bash
 python code/setup_project_structure.py
 ```

3. (Optional) Configure linting/formatting:
 ```bash
 ruff check code/
 black code/
 ```

## Execution Order
The pipeline follows these phases:

1. **Data Ingestion**:
 ```bash
 python code/data_loader.py
 ```

2. **Preprocessing (US1)**:
 ```bash
 python code/preprocess.py --input-dir data/raw/ --output-dir data/processed/
 ```

3. **Analysis (US2)**:
 ```bash
 python code/analysis.py --input-dir data/processed/ --output-dir data/processed/
 ```

4. **Prediction (US3)**:
 ```bash
 python code/predict.py --input-dir data/processed/ --output-dir data/processed/
 ```

## Verification
Run unit tests:
```bash
pytest tests/unit/ -v
```

## Output Artifacts
After successful execution, check:
- `data/processed/precursor_metrics.csv`
- `data/processed/yield_flags.json`
- `data/processed/permutation_test_results.json`
- `data/processed/prediction_results.json`