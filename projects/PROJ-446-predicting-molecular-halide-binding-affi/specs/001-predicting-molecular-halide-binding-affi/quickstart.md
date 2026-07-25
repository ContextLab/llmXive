# Quickstart: Predicting Molecular Halide Binding Affinities

## Prerequisites

- Python 3.11+
- `pip`
- Access to a GitHub Actions runner (or local machine with 7 GB+ RAM).

## Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd projects/PROJ-446-predicting-molecular-halide-binding-affi
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: `requirements.txt` pins `scikit-learn>=1.4.0`, `rdkit`, `pandas`, `numpy`, `requests`, `beautifulsoup4`, `pyyaml`, `seaborn`, `matplotlib`.*

## Running the Pipeline

The pipeline is executed sequentially. Each script depends on the output of the previous one.

### Step 1: Data Ingestion
Attempts to scrape NIST/PubChem. If insufficient data is found, generates simulated data.
```bash
python code/01_data_ingestion.py
```
**Output**: `data/processed/halide_binding_data.csv`

### Step 2: Feature Engineering
Computes RDKit descriptors and fingerprints.
```bash
python code/02_feature_engineering.py
```
**Output**: Updates `data/processed/halide_binding_data.csv` with descriptor columns.

### Step 3: Model Training
Trains Random Forest and Gradient Boosting models with GroupKFold.
```bash
python code/03_model_training.py
```
**Output**: `data/processed/model_runs.json`

### Step 4: Feature Analysis
Performs stability analysis and physical plausibility checks.
```bash
python code/04_feature_analysis.py
```
**Output**: `data/processed/feature_analysis.json`

### Step 5: Statistical Reporting
Generates bootstrap confidence intervals and final report.
```bash
python code/05_statistical_reporting.py
```
**Output**: `data/processed/report.md`

## Verification

To verify the pipeline:
1. Ensure `data/processed/halide_binding_data.csv` exists and contains the `binding_constant` column.
2. Check `data/processed/model_runs.json` for `R²_mean` values.
3. Verify `data/processed/feature_analysis.json` contains `feature_stability` with `CV` scores.
4. Confirm `data/processed/report.md` includes the "Simulated Data Mode" disclaimer if real data was insufficient.

## Troubleshooting

- **Memory Error**: If running locally, ensure you have ≥7 GB RAM. If on GitHub Actions, the job will fail if >7 GB is used.
- **No Data Found**: If the log says "WARNING: Insufficient data", the pipeline automatically switches to simulation. This is expected behavior per FR-011.
- **RDKit Errors**: Ensure `rdkit` is installed via `conda` or `pip` (preferably `pip` for CI compatibility).
