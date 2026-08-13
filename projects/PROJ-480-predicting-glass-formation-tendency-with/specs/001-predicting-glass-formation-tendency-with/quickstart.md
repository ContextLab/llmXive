# Quickstart: Predicting Glass Formation Tendency

## Prerequisites

- Python 3.11+
- `pip` (or `conda`)
- Access to the Figshare dataset () or a local copy.

## 1. Installation

```bash
# Clone the repository
git clone <repo-url>
cd projects/001-predict-glass-formation

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Data Preparation

### Option A: Automated Download (If Figshare API allows)
Run the download script. If authentication is required, the script will prompt for a local file path.
```bash
python src/data/download.py
```

### Option B: Manual Download
1. Download the dataset from Figshare ().
2. Place the file in `data/raw/glass_data.csv`.
3. Run the validation script:
```bash
python src/data/validation.py
```

## 3. Training & Analysis

Execute the full pipeline:
```bash
python src/cli/run_pipeline.py
```

This command will:
1. Ingest and validate data.
2. Compute descriptors.
3. Train the model (Regression or Classification).
4. Run Adaptive Leave-One-Group-Out (LOGO) CV.
5. Perform power analysis and VIF diagnostics.
6. Generate the final report.

## 4. Output Artifacts

After completion, check the following directories:
- `data/processed/`: Cleaned, descriptor-computed dataset.
- `models/`: Trained XGBoost model and artifacts.
- `reports/`: `final_report.md`, `sensitivity_analysis.csv`, `feature_importance.png`.
- `state/`: Checksums and execution logs.

## 5. Verification

Run the test suite to ensure reproducibility:
```bash
pytest tests/
```

## 6. Troubleshooting

- **Error: "Insufficient valid samples"**: Ensure the dataset contains at least 30 valid rows with non-null targets and descriptors.
- **Error: "CircularDataError"**: The target variable is likely derived from the descriptors. Check the data source.
- **Error: "Unknown Element"**: The dataset contains an element not in `pymatgen`. Exclude these rows or update `pymatgen`.