# Quickstart: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Prerequisites
- Python 3.11+
- `pip`
- At least 7 GB of available RAM
- Internet connection (for dataset download)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `rdkit` is installed from the conda-forge channel if pip installation fails, as it is a complex binary package.*

## Running the Pipeline

The pipeline is executed sequentially via the main script or individual modules.

### 1. Download and Filter Data
```bash
python code/download.py
python code/filter.py
```
*Output*: `data/processed/organophosphates.csv`

### 2. Generate Fingerprints
```bash
python code/fingerprints.py
```
*Output*: `data/processed/morgan_features.parquet`, `data/processed/maccs_features.parquet`

### 3. Split Data
```bash
python code/split.py
```
*Output*: `data/processed/train_indices.csv`, `data/processed/test_indices.csv`

### 4. Train Models
```bash
python code/train.py
```
*Output*: `data/processed/models/`

### 5. Evaluate and Report
```bash
python code/evaluate.py
```
*Output*: `data/processed/results/statistical_report.json`, `data/processed/results/report.md`

## Verification

To verify the installation and data integrity:
```bash
pytest tests/
```
Ensure all tests pass, particularly `test_filter.py` (SMARTS pattern) and `test_fingerprints.py` (bit lengths).

## Troubleshooting

- **Memory Error**: If you encounter a MemoryError, check if the dataset is too large. The script is designed to handle up to 7 GB; if it fails, ensure no other heavy processes are running.
- **SMARTS Filtering Returns 0**: Verify the SMILES column in the raw data is valid. The pattern `[P](=O)([O,SC])[O,SC]` is specific to organophosphates.
- **Tanimoto Split Fails**: If the split cannot achieve Tanimoto < 0.85, the report will indicate "Insufficient Structural Diversity". This is expected if the dataset is small or homogeneous.
