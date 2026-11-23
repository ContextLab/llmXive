# Quickstart Guide: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

This guide explains how to run the full pipeline from data download to model visualization for project PROJ-066.

## Prerequisites

- Python 3.10+
- A Unix-like environment (Linux/macOS) or WSL2 on Windows
- At least 15GB free disk space (for raw ChEMBL download and processed artifacts)
- Network access to ftp.ebi.ac.uk (for ChEMBL download)

## Installation

1. Navigate to the project code directory:
 ```bash
 cd projects/PROJ-066-investigating-correlations-between-molec/code
 ```

2. Create a virtual environment and activate it:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
 *Note: Ensure `rdkit`, `scikit-learn`, `pandas`, `matplotlib`, `pyyaml`, and `psutil` are installed.*

## Step 1: Download and Verify ChEMBL 33

The pipeline starts by downloading the ChEMBL 33 database from EBI. This script validates the checksum and extracts the SQLite database.

```bash
python data/download.py
```

**What this does:**
- Connects to `ftp://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_33/`
- Downloads `chembl_33.tar.gz` (or `.zip`) and `chembl_33.sha256`
- Verifies the SHA-256 checksum of the archive
- Extracts the SQLite database to `data/raw/chembl_33.db`
- Updates `state/projects/PROJ-066-investigating-correlations-between-molec.yaml` with the verified checksum and artifact hash

**Expected Output:**
- `data/raw/chembl_33.db` (SQLite database)
- Updated state file with checksum record

**Troubleshooting:**
- If the download fails, check your network connection and firewall settings.
- If the checksum fails, the script will raise an exception and stop. Do not proceed with corrupted data.

## Step 2: Data Preprocessing

This step sanitizes molecules, filters for specific targets (oral bioavailability, Papp, clearance), handles duplicates, samples the dataset, calculates molecular descriptors, and writes the final processed CSV.

```bash
python data/preprocess.py
```

**What this does:**
- **Sanitization**: Uses RDKit to remove salts, fix valences, and exclude invalid structures.
- **Target Filtering**: Keeps only rows matching oral bioavailability, apparent permeability, or clearance.
- **Deduplication**: Resolves duplicate SMILES by retaining the most recent assay date or averaging values.
- **Sampling**: Performs stratified random sampling with memory safety checks (max ~6GB RAM usage).
- **Descriptor Calculation**: Computes TPSA, logP, MW, rotatable bonds, H-bond donors/acceptors, and ring count.
- **Validation**: Validates every row against `contracts/molecule.schema.yaml` before writing.
- **State Update**: Records the hash of `data/processed/molecules_processed.csv` in the state file.

**Expected Output:**
- `data/processed/molecules_processed.csv` (Clean dataset with SMILES, target values, and descriptors)
- Updated state file with artifact hash

**Note:** This step may take several minutes depending on dataset size and system performance.

## Step 3: Model Training

Split the processed data and train Linear Regression and Random Forest models.

```bash
python models/train.py
```

**What this does:**
- Loads `data/processed/molecules_processed.csv`
- Performs a stratified train/test split (seed=42) based on the target variable.
- Trains a Linear Regression model and saves it to `data/processed/model_lr.pkl`.
- Trains a Random Forest model (memory-conscious parameters) and saves it to `data/processed/model_rf.pkl`.
- Generates feature importance rankings and saves them to `data/processed/feature_importance.json`.

**Expected Output:**
- `data/processed/model_lr.pkl`
- `data/processed/model_rf.pkl`
- `data/processed/feature_importance.json`

## Step 4: Model Evaluation and Visualization

Evaluate the trained models, calculate metrics, compare against a baseline, and generate plots.

```bash
python models/evaluate.py
```

**What this does:**
- Loads the test set and trained models.
- Calculates RMSE and Pearson correlation coefficient (r) for both models.
- Computes a mean-predictor baseline RMSE for comparison.
- Generates a scatter plot of predicted vs. experimental values (`data/processed/plot_scatter.png`).
- Generates a bar chart of feature importances (`data/processed/plot_importance.png`).
- Saves a comprehensive metrics summary to `data/processed/metrics_summary.json`.
- Updates the state file with artifact hashes.

**Expected Output:**
- Console output with RMSE and correlation metrics.
- `data/processed/metrics_summary.json`
- `data/processed/plot_scatter.png`
- `data/processed/plot_importance.png`

## Full Pipeline Execution

To run the entire pipeline from scratch (excluding the download step if data already exists), you can chain the commands:

```bash
# 1. Download (only if data/raw/chembl_33.db does not exist)
python data/download.py

# 2. Preprocess
python data/preprocess.py

# 3. Train
python models/train.py

# 4. Evaluate
python models/evaluate.py
```

## Verification

After running the pipeline:
1. Check `data/processed/molecules_processed.csv` to ensure it contains the expected columns (SMILES, experimental value, descriptors) with no missing values.
2. Inspect `data/processed/metrics_summary.json` for the RMSE, r, and baseline comparison values.
3. Open `data/processed/plot_scatter.png` and `data/processed/plot_importance.png` to visualize the results.
4. Verify `state/projects/PROJ-066-investigating-correlations-between-molec.yaml` contains the latest artifact hashes.

## Resource Constraints

The pipeline is designed to run within the following constraints:
- **Memory**: Max ~7GB RAM (with safety checks in sampling and model training).
- **Time**: Max 6 hours for the full pipeline.
- **Disk**: ~15GB required for raw and processed artifacts.

If you encounter memory errors, the `sample_dataset` function in `data/preprocess.py` automatically reduces the sample size to fit within the 6GB safety buffer.

## Troubleshooting

- **RDKit Errors**: If sanitization fails for many molecules, check the logs in `logs/` for specific chemical structure issues.
- **FTP Errors**: If the download fails, ensure your network allows FTP connections to `ftp.ebi.ac.uk`.
- **Memory Errors**: If the pipeline crashes due to memory, verify that no other heavy processes are running and that the `MAX_MEMORY_GB` setting in `utils/config.py` is appropriate for your system.