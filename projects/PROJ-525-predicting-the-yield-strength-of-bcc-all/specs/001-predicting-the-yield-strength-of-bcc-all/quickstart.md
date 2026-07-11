# Quickstart: Predicting Yield Strength of BCC Alloys

## Prerequisites

- Python 3.11+
- Git
- GitHub Actions (for CI) or Local Environment

## Installation

1. **Clone the repository**:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-525-predicting-the-yield-strength-of-bcc-all
 ```

2. **Create a virtual environment**:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. **Install dependencies**:
 ```bash
 pip install -r requirements.txt
 ```

## Data Setup (Critical)

**Note**: The MPEA database does not have a verified programmatic URL. You must manually download it.

1. **Download the MPEA dataset**:
 - Go to the DOI: `
 - Download the CSV/Excel file containing the alloy data.
 - Rename it to `mpea_raw.csv` (or the format expected by the script).
 - **Important**: Do not pre-filter or clean the data. The pipeline expects the raw file.

2. **Place the file**:
 - Move the file to `data/raw/mpea_raw.csv`.

3. **Verify**:
 - Ensure the file contains columns for `crystal_structure`, `yield_strength`, and elemental compositions.
 - Ensure the file is the **raw** version (contains non-BCC phases, missing values, etc.).

## Running the Pipeline

### 1. Data Download & Filtering
```bash
python code/01_download.py
```
- **Output**: `data/processed/bcc_filtered.csv`
- **Action**: Filters for BCC phase, normalizes compositions, excludes missing data.
- **Check**: If N < 80, the pipeline halts with a warning.

### 2. Feature Engineering
```bash
# Option A: Scalar Descriptors
python code/02_engineer.py --method descriptors

# Option B: ILR Transformation
python code/02_engineer.py --method ilr
```
- **Output**: `data/processed/features_descriptors.csv` or `features_ilr.csv`
- **Note**: Run these separately. Do not combine features.

### 3. Model Training & Validation
```bash
python code/03_train.py --features features_descriptors.csv --method rf,gb,ridge
```
- **Output**: `data/processed/model_results.json`
- **Action**: Repeated K-Fold CV (K ≥ 2, 10 reps) + Bootstrapping (1000 resamples).

### 4. Evaluation & Reporting
```bash
python code/04_evaluate.py
```
- **Output**: `data/processed/performance_report.csv`, `data/processed/feature_importance.png`
- **Action**: Calculates Spearman stability, MAE vs uncertainty, and Friedman/Nemenyi test.

## Testing

Run the test suite:
```bash
pytest tests/
```

## Troubleshooting

- **Error: "Data Scarcity Warning"**: The filtered dataset has fewer than 80 BCC alloys. Check the raw data source.
- **Error: "Missing Element Reference"**: The dataset contains an element not in the `periodictable` library. Check for typos.
- **Error: "No Verified Source"**: If you are running on CI without the manual data file, the pipeline will fail. Ensure `data/raw/` is populated.
- **Error: "Circular Validation Warning"**: The dataset contains yield strength values derived from CALPHAD using the same parameters as the predictor. These rows are flagged or excluded.