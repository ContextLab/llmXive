# Quickstart: Statistical Analysis of Publicly Available Climate Model Output Ensembles

## 1. Prerequisites

- Python 3.11+
- Git
- Access to HuggingFace (for dataset download)

## 2. Setup

### 2.1 Clone and Install
```bash
# Navigate to project directory
cd projects/PROJ-231-statistical-analysis-of-publicly-availab

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2.2 Dataset Download
The script `code/ingestion.py` handles downloading. To pre-download the test set:
```bash
python code/ingestion.py --mode download --dataset sungduk/wip_cmip6 --shard test-00000-of-00012
```
*Note: The full dataset will be streamed during the main analysis if available.*

## 3. Running the Pipeline

Execute the full analysis pipeline:
```bash
python code/main.py
```

This will:
1.  Ingest and preprocess data (schema check, spline imputation).
2.  Fit B-spline basis (via Pilot GCV).
3.  Run fPCA.
4.  Perform Leave-One-Out (LOO) Jackknife iterations.
5.  Generate plots and save results to `artifacts/`.
6.  Update the project state file with artifact hashes.

## 4. Verification

Check that the pipeline completed successfully:
```bash
ls -lh artifacts/plots/
cat data/processed/jackknife_metrics.json
```

To run unit tests:
```bash
pytest tests/unit/
```

To run contract tests (schema validation):
```bash
pytest tests/contract/
```

## 5. Troubleshooting

- **Memory Error**: If you encounter OOM, reduce the sample size in `code/config.py` (e.g., `max_ensemble_members = 20`).
- **Missing Variables**: If the dataset lacks `tas` or `pr`, or lacks monthly resolution, the script will exit with a clear error. Check the `data/raw` logs.
- **Jackknife Failure**: If the ensemble has < 10 models, the LOO Jackknife will halt. Increase the ensemble size in the configuration.
- **State Update Error**: If the state file is not updated, check permissions for `state/projects/...yaml`.