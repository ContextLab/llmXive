# Quickstart: Assessing Dataset Imbalance Effects on Materials Property Predictions

## Prerequisites
- Python 3.11+
- Git
- Access to GitHub Actions runner (or local machine with 7 GB+ RAM).

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-756-assessing-dataset-imbalance-effects-on-m
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Data Ingestion
Download and merge OQMD and AFLOW data.
```bash
python code/ingestion.py --output data/raw/merged_raw.parquet
```
*Note: If Materials Project API key is set in `MP_API_KEY` env var, it will attempt to fetch MP data.*

### Step 2: Descriptor Computation & Imbalance Analysis
Compute Magpie descriptors and calculate ImbalanceScores.
```bash
python code/descriptors.py --input data/raw/merged_raw.parquet --output data/processed/processed.parquet
python code/imbalance.py --input data/processed/processed.parquet --output results/imbalance_metrics.json
```

### Step 3: Baseline Training
Train models on skewed data.
```bash
python code/training.py --input data/processed/processed.parquet --strategy skewed --output artifacts/models/baseline/
```

### Step 4: Resampling & Re-training
Apply resampling and retrain.
```bash
python code/resampling.py --input data/processed/processed.parquet --output data/processed/balanced.parquet
python code/training.py --input data/processed/balanced.parquet --strategy balanced --output artifacts/models/balanced/
```

### Step 5: Evaluation & SHAP
Compare performance and analyze feature importance.
```bash
python code/evaluation.py --baseline artifacts/models/baseline/ --balanced artifacts/models/balanced/ --output results/comparison_report.csv
python code/shap_analysis.py --models artifacts/models/ --output results/shap_comparison.json
```

## Expected Outputs
- `results/imbalance_metrics.json`: Convex Hull Volume and Gini scores.
- `results/comparison_report.csv`: MAE, RMSE, R² for skewed vs. balanced models.
- `results/shap_comparison.json`: Feature rank shifts and distortion metrics.

## Troubleshooting
- **API Errors**: Check `logs/ingestion.log` for retry attempts.
- **Memory Error**: Ensure the dataset was sampled to < 5 GB. Reduce `--sample-size` in `ingestion.py`.
- **Resampling Failure**: Check `logs/resampling.log` for fallback to Cost-Sensitive Learning.