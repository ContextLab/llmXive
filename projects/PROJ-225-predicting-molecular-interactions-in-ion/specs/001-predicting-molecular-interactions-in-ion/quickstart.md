# Quickstart: Predicting Molecular Interactions in Ionic Liquids

## Prerequisites
- Python 3.11+
- Access to the GitHub Actions runner (or local environment with adequate RAM).
- `git` and `pip`.
- **Local Data**: The `ILThermo` dataset must be provided as `data/raw/ilthermo.csv` with columns: `cation_smiles`, `anion_smiles`, `family_cation`, `family_anion`.

## 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Data Preparation

### Option A: Automated Download (SAPT2023, dft23-full)
Run the ingestion script. It will fetch verified datasets from HuggingFace.
```bash
python code/01_ingest_and_feature_engineering.py --download-sapt
```
*Note: You must manually place `data/raw/ilthermo.csv` before running the full pipeline.*

### Option B: Manual Data Placement
1. Download the verified datasets manually (if needed).
2. Place `data/raw/ilthermo.csv` in the project root.
3. Run:
```bash
python code/01_ingest_and_feature_engineering.py --process-only
```

## 3. Run the Pipeline

Execute the full pipeline (Ingest → Train → Analyze):
```bash
python code/01_ingest_and_feature_engineering.py
python code/02_train_models.py
python code/03_analysis_and_validation.py
```

## 4. Verify Results

Check the output artifacts:
- **Models**: `artifacts/models/` (Should contain 3 JSON files).
- **Reports**: `artifacts/reports/` (MANOVA and Validation reports).
- **Test**: Run the test suite to ensure contract compliance.
```bash
pytest code/tests/ -v
```

## 5. Expected Output

- **Success**: `MAE ≤ 0.5` kcal/mol on test set (if data quality allows).
- **Validation**: `R² ≥ 0.80` against external DFT set (if n ≥ 30).
- **Status**: `research_complete` if all success criteria are met.
- **Failure**: If sample size < 1,000, the pipeline halts with "Insufficient Sample Size".
