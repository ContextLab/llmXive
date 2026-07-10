# Quickstart: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

## Prerequisites

- Python 3.10+
- Git
- GB free disk space
- Network access (for dataset download)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repo-url>
   cd projects/PROJ-170-predicting-catalytic-activity-from-elect
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```
   *Note: `requirements.txt` pins versions for reproducibility (Constitution Principle I).*

## Running the Pipeline

The pipeline is executed sequentially. Run the following commands in order:

### Step 1: Download Data
```bash
python code/download_data.py
```
- Downloads a stratified sample of the OC20 dataset.
- Saves to `data/raw/`.
- Generates checksums.

### Step 2: Preprocess & Align
```bash
python code/preprocess.py
```
- Aligns OC20 entries by composition and facet.
- Derives descriptors and performs structure-based KNN imputation.
- Scales features.
- Outputs `data/processed/aligned_dataset.csv`.

### Step 3: Train Models
```bash
python code/train.py
```
- Trains XGBoost and Linear Baseline with nested cross-validation.
- Saves best model to `code/models/`.

### Step 4: Evaluate & Interpret
```bash
python code/evaluate.py
```
- Computes metrics (R², MAE, p-value, alignment rate).
- Generates SHAP plot (`outputs/feature_importance.png`).
- Saves `outputs/metrics.json`.

### Step 5: Generate Report
```bash
python code/report.py
```
- Compiles `outputs/final_report.md` with all findings.

## Verifying Results

- **Check Metrics**: Open `outputs/metrics.json`.
- **Check Plot**: View `outputs/feature_importance.png`.
- **Check Report**: Read `outputs/final_report.md`.

## Troubleshooting

- **Missing Data**: If `download_data.py` fails to download OC20, check network connectivity.
- **Memory Error**: If RAM usage exceeds 7GB, reduce the sample size in `download_data.py` (adjust `SAMPLE_SIZE` constant).
- **KNN Imputation Failure**: If many rows are excluded, check `data/processed/aligned_dataset.csv` for `exclusion_reason`.

## Next Steps

- Review `outputs/final_report.md` for scientific insights.
- Run `pytest tests/` to verify contract compliance.
- Proceed to `research_review` stage if all success criteria are met.