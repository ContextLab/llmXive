# Quickstart Guide: Predicting Molecular Reactivity

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Clone the repository and navigate to the project directory.
2. Create a virtual environment:
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 ```
3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Data Preparation

The USPTO dataset must be downloaded and placed in `data/raw/`.
Ensure `config.yaml` contains a valid `USPTO_URL`.

## Pipeline Execution

Run the full pipeline stages sequentially:

### Stage 1: Ingestion and Filtering
This stage downloads (if URL provided), parses, classifies, and filters the data.
It produces:
- `data/processed/filtered_reactions_full.csv`
- `data/processed/filtered_reactions_clean.csv` (if sample size filtering is active)
- `data/processed/class_exclusion_metadata.json` (T016b artifact)
- `data/processed/target_validation.log`

```bash
python code/src/data/ingestion.py --input data/raw/uspto_subset.parquet --output-full data/processed/filtered_reactions_full.csv --output-clean data/processed/filtered_reactions_clean.csv
```

### Stage 2: Feature Extraction
```bash
python code/src/data/preprocessing.py --input data/processed/filtered_reactions_clean.csv --output data/processed/feature_matrix.parquet
```

### Stage 3: Model Training
```bash
python code/src/modeling/train.py --config code/src/modeling/config.yaml
```

### Stage 4: Evaluation
```bash
python code/src/modeling/evaluate.py --input data/results/cv_results.csv --output data/processed/analysis_report.json
```

## Verification

After running the pipeline, verify the following artifacts exist:
- `data/processed/class_exclusion_metadata.json`
- `data/processed/feature_matrix.parquet`
- `data/models/xgboost_model.json`
- `data/processed/analysis_report.json`

## Testing

Run unit tests:
```bash
pytest code/tests/unit/
```