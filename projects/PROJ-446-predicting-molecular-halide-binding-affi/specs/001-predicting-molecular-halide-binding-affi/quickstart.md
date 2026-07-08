# Quickstart: Predicting Molecular Halide Binding Affinities with Machine Learning

## Prerequisites

- Python 3.11+
- Git
- GitHub CLI (optional, for repo interaction)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-446-predicting-molecular-halide-binding-affi/code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Data Ingestion
```bash
cd projects/PROJ-446-predicting-molecular-halide-binding-affi/code
python 01_data_ingestion.py
```
- Downloads data from NIST/PubChem (or triggers simulation if insufficient).
- **Note**: If no verified data is found, the pipeline switches to "Simulated Data Mode" and logs a warning.
- Outputs: `data/processed/cleaned.csv`.

### Step 2: Feature Engineering
```bash
python 02_feature_engineering.py
```
- Generates ECFP4 fingerprints and RDKit descriptors.
- Outputs: `data/processed/features.csv`.

### Step 3: Model Training
```bash
python 03_model_training.py
```
- Trains RF and GB models with 5-fold cross-validation (host-identity split).
- **Note**: If N < 10 per halide, the training completes but comparative analysis is skipped.
- Outputs: `data/processed/models/`, `data/processed/results/cv_metrics.csv`.

### Step 4: Feature Analysis
```bash
python 04_feature_analysis.py
```
- Computes feature stability, generates partial dependence plots.
- **Note**: In Simulated Data Mode, feature importance will trivially reflect the generation formula.
- Outputs: `data/processed/results/feature_importance.csv`, `figures/`.

### Step 5: Statistical Reporting
```bash
python 05_statistical_reporting.py
```
- Computes bootstrap CIs for performance differences across halides.
- **Note**: If any halide group has <10 measurements, the comparison is aborted and the report states "underpowered".
- Outputs: `docs/paper/report.md`, `data/processed/results/bootstrap_ci.csv`.

## Expected Outputs

- `data/processed/cleaned.csv`: Cleaned dataset.
- `data/processed/features.csv`: Feature matrix.
- `data/processed/models/`: Trained model objects.
- `docs/paper/report.md`: Final report with associational disclaimer.
- `figures/`: Partial dependence plots, feature importance charts.

## Troubleshooting

- **Insufficient Data**: If the pipeline logs "WARNING: Insufficient data", it has switched to simulated data mode. All outputs will be marked "Simulated Data Mode". **Comparative analysis is aborted.**
- **Underpowered Analysis**: If the report states "underpowered", it means N < 10 per halide. No significance testing was performed.
- **RAM Errors**: If training fails due to RAM, reduce dataset size or use smaller descriptor sets.
- **SMILES Parsing Errors**: Check `logs/excluded_records.log` for invalid SMILES.

## Verification

Run the test suite:
```bash
pytest tests/
```
- Verifies data cleaning, model training, and statistical reporting.
