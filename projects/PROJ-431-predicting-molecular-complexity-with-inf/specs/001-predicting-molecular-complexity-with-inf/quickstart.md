# Quickstart: Predicting Molecular Complexity with Information Theory

## Prerequisites
- Python 3.10+
- Git
- Access to the verified dataset URLs (no authentication required for public HuggingFace datasets).

## 1. Setup Environment

```bash
# Clone the project (assuming standard repo structure)
git clone <repo-url>
cd projects/PROJ-431-predicting-molecular-complexity-with-inf

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Download Data & Verify Schema

The pipeline expects a CSV file in `data/raw/molecules.csv`. Download the verified dataset and convert to CSV if necessary (Parquet to CSV). **Schema Verification**: The pipeline will abort if `smiles`, `logS`, or `logP` are missing.

```bash
# Example: Download and convert the ChEMBL dataset
python -c "
import pandas as pd
from datasets import load_dataset
# Load the verified dataset
ds = load_dataset('fabikru/chembl-2025-randomized-smiles-cleaned-rdkit-descriptors', split='test')
# Convert to CSV (ensure logS and logP columns exist)
df = ds.to_pandas()
# Check for required columns
required = ['smiles', 'logS', 'logP']
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f'Missing required columns: {missing}')
# Filter for columns if necessary
df[['smiles', 'logS', 'logP']].to_csv('data/raw/molecules.csv', index=False)
print('Schema verified: smiles, logS, logP present.')
"
```
*Note: If the dataset columns differ (e.g., `LogS` vs `logS`), adjust the column selection in the script above. The pipeline will abort if the exact names are not found.*

## 3. Run the Pipeline

### Step A: Compute Entropy
```bash
python code/cli.py compute_entropy \
  --input data/raw/molecules.csv \
  --output data/processed/molecules_entropy.csv
```
*Output*: `molecules_entropy.csv` with `atom_entropy`, `bond_entropy`, `molecular_weight`, `atom_count` columns.

### Step B: Train Model (logS)
```bash
python code/cli.py train_model \
  --input data/processed/molecules_entropy.csv \
  --target logS \
  --output-dir results/
```
*Output*: `results/models/ridge_logS.pkl`, `results/reports/logS_metrics.json`.

### Step C: Train Model (logP)
```bash
python code/cli.py train_model \
  --input data/processed/molecules_entropy.csv \
  --target logP \
  --output-dir results/
```
*Output*: `results/models/ridge_logP.pkl`, `results/reports/logP_metrics.json`.

### Step D: Generate Plots
```bash
python code/cli.py plot_correlation \
  --input data/processed/molecules_entropy.csv \
  --property logS \
  --output results/plots/entropy_vs_logS.png

python code/cli.py plot_correlation \
  --input data/processed/molecules_entropy.csv \
  --property logP \
  --output results/plots/entropy_vs_logP.png
```

## 4. Verify Results

- Check `results/reports/*.json` for RMSE and Pearson $r$.
- Ensure Bonferroni-corrected p-values are $< 0.05$ for significant correlations.
- Verify plots in `results/plots/` contain regression lines and $R^2$ annotations.
- **Baseline Comparison**: Confirm that the Entropy model's RMSE is lower than the Null and Size baselines reported in the JSON.