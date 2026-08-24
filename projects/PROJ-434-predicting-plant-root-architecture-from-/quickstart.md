# Quickstart Guide: Predicting Plant Root Architecture from Soil Nutrient Profiles

This guide provides step-by-step instructions to set up the environment, run the data ingestion pipeline, train models, and generate reports for the `PROJ-434` project.

## Prerequisites

- Python 3.9+
- pip
- A modern web browser (for viewing reports)
- (Optional) Git for version control

## 1. Setup Environment

### Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r code/requirements.txt
```

### Configure Environment Variables
Create a `.env` file in the project root (or use the template):
```bash
#.env
RUN_MODE=production
RANDOM_SEED=42
# Add API keys if required by data sources (e.g., TRY database)
# TRY_API_KEY=your_key_here
```

## 2. Directory Structure Setup

Run the setup script to create necessary directories:
```bash
python code/setup_dirs.py
```
This creates:
- `code/` - Source code
- `data/` - Raw and processed data
- `data/raw/` - Original data files
- `data/processed/` - Cleaned and merged datasets
- `data/logs/` - Execution logs
- `tests/` - Test suites
- `artifacts/` - Model outputs and metrics
- `figures/` - Generated plots

## 3. Data Ingestion (User Story 1)

This pipeline fetches real root trait data and soil nutrient data, merges them, and validates the result.

### Run the Ingestion Pipeline
```bash
python code/ingestion/main.py
```
**What it does:**
1. Loads root trait data from verified sources (TRY/SoilGrids).
2. Extracts soil N, P, K, pH values at trait coordinates.
3. Merges datasets and applies species filters (≥10 observations).
4. Validates data quality (match proportion ≥ 0.90).
5. Generates `data/processed/merged_dataset.csv`.

**Expected Output:**
- `data/processed/merged_dataset.csv`
- `data/processed/soil_extracted.csv`
- `data/logs/validation_summary.log`
- `data/logs/species_exclusions.log`

**Note:** If `RUN_MODE=production`, the script will fail if real data cannot be fetched. It will not fall back to synthetic data.

## 4. Model Training (User Story 2)

Train predictive models using Leave-One-Species-Out (LOSO) cross-validation.

### Run Training Script
```bash
python code/modeling/train.py
```
**What it does:**
1. Preprocesses the merged dataset.
2. Trains Model A (Soil-Only) and Model B (Soil+Species).
3. Performs LOSO and Stratified 5-Fold CV.
4. Runs nested permutation tests (1000 iterations).
5. Validates SC-002 compliance (ΔR² ≥ 0.05, p < 0.05).

**Expected Output:**
- `artifacts/model_metrics.json`
- `artifacts/baseline_metrics.json`
- `artifacts/permutation_distributions.json`
- `artifacts/sc002_status.json`
- `artifacts/feature_importance.csv`
- `figures/feature_importance.png`

## 5. Sensitivity Analysis (User Story 3)

Analyze the stability of feature importance rankings across different p-value thresholds.

### Run Sensitivity Analysis
```bash
python code/modeling/sensitivity.py
```
**What it does:**
1. Loads feature importance scores.
2. Sweeps p-value thresholds (0.01, 0.05, 0.10).
3. Tracks top-3 feature stability.
4. Generates a sensitivity report.

**Expected Output:**
- `artifacts/sensitivity_report.md`

## 6. Verification & Testing

### Run Tests
```bash
pytest tests/ -v
```
This runs:
- Contract tests for schema validation.
- Integration tests for geocoding and LOSO logic.
- Unit tests for helper functions.

### Validate End-to-End Reproducibility
Run the `quickstart.md` validation script (if available) or manually re-run steps 3-5 to ensure outputs are consistent.

## Troubleshooting

### Data Fetch Errors
If you see `DataFetchError`, ensure:
- You have internet access.
- API keys (if required) are correctly set in `.env`.
- The `RUN_MODE` is set to `production` (default).

### Missing Dependencies
If imports fail, ensure you activated the virtual environment and ran `pip install -r code/requirements.txt`.

### Memory Issues
The dataset may be large. If you encounter memory errors, consider:
- Using a machine with more RAM.
- Streaming data in chunks (supported by the ingestion scripts).

## Further Reading
- [Research Documentation](specs/001-predict-root-architecture/research.md)
- [Data Model](specs/001-predict-root-architecture/data-model.md)
- [Contracts](specs/001-predict-root-architecture/contracts/)