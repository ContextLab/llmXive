# Quickstart Guide: Predicting Battery Electrolyte Decomposition Products

This guide provides step-by-step instructions to set up the environment, fetch real data, run the full pipeline, and validate results for the **llmXive** battery electrolyte decomposition project.

## Prerequisites

- Python 3.10 or higher
- pip (package manager)
- Git (for cloning the repository)
- A modern web browser for viewing reports

## 1. Setup and Installation

### Clone and Navigate
```bash
git clone <repository-url>
cd PROJ-085-predicting-battery-electrolyte-decomposi
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

### Install Dependencies
Install the required packages defined in `requirements.txt`:
```bash
pip install -r requirements.txt
```

> **Note**: This project requires `pandas`, `scikit-learn`, `rdkit`, `pymatgen`, `datasets` (HuggingFace), `numpy`, `matplotlib`, and `seaborn`.

## 2. Data Fetching

The pipeline is configured to fetch real DFT data from the HuggingFace dataset `materialsproject/mp-dft-electrolytes`.

### Automatic Fetch (Recommended)
The ingestion script (`code/data/ingestion.py`) handles data fetching automatically. When you run the pipeline, it will attempt to download the dataset.

### Manual Verification
To verify data availability manually:
```python
from code.data.ingestion import fetch_dataset_data
# This will attempt to download the dataset
df = fetch_dataset_data()
print(f"Loaded {len(df)} records from HuggingFace.")
```

**Fallback Behavior**: If the HuggingFace fetch fails (e.g., network issues or dataset unavailability), the system will automatically fall back to the local mock CSV at `data/raw/mock_electrolytes.csv` if it exists. **Do not modify this fallback unless you are testing offline scenarios.**

## 3. Running the Pipeline

The pipeline is executed via a series of modular scripts. Run them in the following order to ensure dependencies are met.

### Step 1: Directory Structure & Checksums
Ensures the required folder structure exists and registers checksums.
```bash
python code/data/structure.py
```

### Step 2: Data Ingestion
Fetches and filters electrolyte data (EC, DMC, LiPF6).
```bash
python code/data/ingestion.py
```
*Output*: `data/raw/electrolytes_raw.csv`

### Step 3: Descriptor Extraction
Calculates HOMO, LUMO, band gaps, and geometric features.
```bash
python code/data/descriptors.py
```
*Output*: `data/processed/descriptors.csv`

### Step 4: Target Calculation
Computes decomposition energy ($E_{decomp}$) using reaction stoichiometry.
```bash
python code/data/target_calc.py
```
*Output*: `data/processed/targets.csv`

### Step 5: Data Validation & Splitting
Validates feature matrices and splits data into Train/Val/Held-Out sets.
```bash
python code/data/validation.py
python code/data/split_data.py
```
*Output*: `data/processed/electrolyte_features.csv`, `data/processed/electrolyte_heldout.csv`

### Step 6: Binning (Stratification)
Assigns data to 'Low' (0-2V) and 'High' (4V) potential bins.
```bash
python code/data/binning.py
```
*Output*: `data/processed/bins.csv`

### Step 7: Model Training
Trains a Random Forest Regressor with 5-fold CV and hyperparameter tuning.
```bash
python code/models/trainer.py
```
*Output*: `data/processed/model_run.json`, `data/processed/model.pkl`

### Step 8: Evaluation & Sensitivity Analysis
Calculates internal metrics, permutation importance, and runs sensitivity analysis.
```bash
python code/models/evaluator.py
```
*Output*: `data/validation/sensitivity_report.md`, `data/validation/feature_importance_heatmap.png`

## 4. Expected Outputs

After running the full pipeline, verify the following files exist:

- **Data**:
 - `data/processed/electrolyte_features.csv` (Feature matrix)
 - `data/processed/electrolyte_heldout.csv` (Held-out set)
 - `data/processed/bins.csv` (Stratification bins)
- **Models**:
 - `data/processed/model_run.json` (Training metrics and hyperparameters)
- **Validation**:
 - `data/validation/sensitivity_report.md` (Sensitivity analysis results)
 - `data/validation/feature_importance_heatmap.png` (Feature importance visualization)

## 5. Validation & Reproducibility

### Checksum Verification
Verify data integrity using the checksum tool:
```bash
python code/data/checksum.py --validate-all
```

### Contract Testing
Ensure data schemas match expectations:
```bash
pytest tests/contract/ -v
```

### Reproducibility
To ensure reproducibility, the random seed is fixed in `code/config.py`. Re-running the pipeline should produce identical results (within floating-point tolerance).

## 6. Troubleshooting

- **Dataset Fetch Failed**: Ensure you have internet access. If the HuggingFace dataset `materialsproject/mp-dft-electrolytes` is unavailable, the system will use the fallback `data/raw/mock_electrolytes.csv`.
- **Import Errors**: Verify your virtual environment is active and all dependencies in `requirements.txt` are installed.
- **Memory Issues**: If running on a resource-constrained machine, reduce the dataset size or adjust batch sizes in `code/config.py`.

## 7. Deviation Notice

**Important**: External experimental validation (FR-006, SC-003) could not be fulfilled due to the unavailability of experimental onset potential datasets for the specific electrolytes (EC, DMC, LiPF6). The pipeline uses **Internal DFT Validation** as a fallback. The sensitivity report (`data/validation/sensitivity_report.md`) includes a warning flag regarding this deviation.

For more details, see `docs/research.md`.