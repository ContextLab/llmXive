# Quickstart: Quantifying the Influence of Topological Defects on 2D Material Properties

## Prerequisites
- Python 3.11+
- `pip`
- Access to GitHub Actions (for CI testing) or a local environment with multiple CPU cores.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-209-quantifying-the-influence-of-topological
   ```

2. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Workflow

### Option 1: Local Execution (Development)
Run the full pipeline end‑to‑end:
```bash
# Step 1: Acquire Data (fetches from API, attempts 2022 dataset, or generates synthetic)
python code/01_data_acquisition.py

# Step 2: Process Data (normalization, filtering, checksum recording)
python code/02_data_processing.py

# Step 3: Train Models & Compute Inference
python code/03_modeling.py
python code/04_inference.py
```

### Option 2: Jupyter Notebook
For interactive exploration:
```bash
jupyter notebook code/notebook_analysis.ipynb
```
*Note: The notebook executes the same logic as the scripts but in a cell‑by‑cell manner.*

### Option 3: GitHub Actions (CI)
Push to the `001-quantify-defect-influence` branch to trigger the automated workflow. The job will:
1. Install dependencies.
2. Run all scripts in the prescribed order.
3. Validate outputs against `contracts/` schemas.
4. Fail if runtime > 6 hours or RAM > 7 GB.

## Expected Outputs
- `data/processed/features.csv`: Normalized feature matrix.
- `data/processed/targets.csv`: Normalized target variables.
- `results/models/`: Saved Random Forest models and `model_config.yaml`.
- `results/inference/`: Permutation importance tables, FDR‑adjusted p‑values, sensitivity analysis plots.
- `Validation_Report.json`: Status of external validation (expected: `NO_EXTERNAL_DATA` if no external set is found, or `SYNTHETIC_FALLBACK` if synthetic data was used).