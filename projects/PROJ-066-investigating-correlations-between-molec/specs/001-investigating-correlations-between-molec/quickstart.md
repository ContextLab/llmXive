# Quickstart: Investigating Correlations Between Molecular Descriptors and Drug-Likeness Scores

## Prerequisites

*   Python 3.10+
*   `git`
*   Access to Hugging Face (free account recommended, though datasets are public).

## Installation

1.  **Clone and Setup**:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-066-investigating-correlations-between-molec/code
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Verify Dependencies**:
    Ensure `rdkit` is installed correctly:
    ```bash
    python -c "from rdkit import Chem; print('RDKit OK')"
    ```

## Running the Pipeline

The pipeline is executed in sequential steps. Each step produces artifacts in `data/` and updates the project state.

### Step 1: Data Acquisition & Preprocessing
Downloads the ChEMBL 33 dataset, validates the file, sanitizes structures, calculates descriptors, and filters for targets.
```bash
python data/download.py --target "bioavailability,permeability,clearance"
python data/preprocess.py --max-samples <variable>
python utils/update_state.py --stage "preprocess"
```
*Output*: `data/processed/molecules_processed.csv`

### Step 2: Model Training
Splits data and trains Linear Regression and Random Forest models.
```bash
python models/train.py --target "bioavailability" --seed 42
python utils/update_state.py --stage "train"
```
*Output*: `data/processed/model_lr_bio.pkl`, `data/processed/model_rf_bio.pkl`

### Step 3: Evaluation & Visualization
Generates metrics and plots.
```bash
python models/evaluate.py --model "rf" --target "bioavailability"
python utils/update_state.py --stage "evaluate"
```
*Output*: `data/plots/pred_vs_exp_bio.png`, `data/plots/feature_importance_bio.png`, `data/processed/metrics_summary.json`

## Verifying Results

1.  **Check Metrics**:
    Look at `data/processed/metrics_summary.json`.
    *   Success Criterion: `pearson_r` >= 0.6 for at least one target.
    *   Success Criterion: `logP` and `TPSA` in top 3 feature importances.

2.  **Visual Inspection**:
    Open `data/plots/pred_vs_exp_bio.png`. Points should cluster around the diagonal line.

## Troubleshooting

* **Memory Error**: If `MemoryError` occurs, reduce `--max-samples` in `preprocess.py` to [deferred].
*   **RDKit Error**: If SMILES sanitization fails, check the log for "Invalid Valence" entries. These molecules are excluded automatically.
*   **Dataset Missing**: If the ChEMBL 33 file is unreachable, the script will exit with a clear error. Ensure internet connectivity.
*   **State Update Failure**: If `update_state.py` fails, check permissions on `state/projects/`.