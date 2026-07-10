# Quickstart: Predicting Battery Electrolyte Decomposition Products

## Prerequisites

- Python 3.10+
- Git
- Access to HuggingFace (for dataset download, if required by specific dataset policy, though these are public).

## Installation

1.  **Clone the repository** and navigate to the project directory:
    ```bash
    git clone <repo-url>
    cd projects/PROJ-085-predicting-battery-electrolyte-decomposi
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `requirements.txt` pins specific versions of `pymatgen`, `rdkit`, and `scikit-learn` to ensure CPU compatibility.*

## Running the Pipeline

The pipeline is designed to run end-to-end on a CPU-only runner.

### Step 1: Data Ingestion & Feature Extraction
```bash
python code/data/ingestion.py
python code/data/descriptors.py
python code/data/target_calc.py
```
*Output*: `data/processed/feature_matrix.csv`, `data/processed/targets.csv`.
*Note*: `target_calc.py` uses a hardcoded reaction lookup table for n-values. Molecules without a defined mechanism are excluded.

### Step 2: Model Training & Validation
```bash
python code/models/trainer.py
python code/models/evaluator.py
```
*Output*: `data/processed/model_results.json`, `data/processed/feature_importance_heatmap.png`.
*Note*: The model is trained as a **global model** (all potentials) with `potential_v` as a feature. External validation is skipped due to missing data.

### Step 3: Sensitivity Analysis
```bash
python code/models/evaluator.py --sweep
```
*Output*: `data/processed/sensitivity_analysis.csv`.

## Verification

To verify the pipeline:
1.  Check that `data/processed/feature_matrix.csv` has no missing values and **does not contain the `band_gap` column** (it is dropped for collinearity).
2.  Verify `data/processed/model_results.json` contains an R² score and MAE (internal).
3.  Ensure the `sensitivity_analysis.csv` shows rank stability for top 3 features across thresholds.
4.  Confirm the report flags "External Validation: N/A" due to missing experimental data.

## Troubleshooting

- **Memory Error**: The dataset is automatically sampled to fit available RAM. If you encounter errors, check the `MAX_SAMPLES` constant in `code/utils/constants.py`.
- **Missing Descriptors**: If `pymatgen` fails to parse a structure, the entry is logged and skipped. Check `logs/ingestion.log`.
- **Missing Reaction Mechanism**: If a molecule is not in the hardcoded reaction lookup table, it is excluded. Check `logs/target_calc.log` for excluded entries.
- **Experimental Data Missing**: If the validation step reports "No experimental data found", this is expected. The pipeline will still complete with internal DFT validation.