# Quickstart: Predicting Battery Electrolyte Decomposition Products

## Prerequisites

- Python 3.10+
- Git
- Access to HuggingFace (for dataset download, if required by specific dataset policy, though these are public).

## Installation

1. **Clone the repository** and navigate to the project directory:
 ```bash
 git clone <repo-url>
 cd projects/PROJ-085-predicting-battery-electrolyte-decomposi
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

## Running the Pipeline

The pipeline is designed to run end‑to‑end on a CPU‑only runner.

### Step 1: Data Ingestion & Feature Extraction
```bash
python code/data/ingestion.py
python code/data/run_descriptor_pipeline.py
```
*Output*: `data/processed/electrolyte_features.csv`

### Step 2: Binning
```bash
python code/data/run_binning.py
```
*Output*: `data/processed/bins.csv`

### Step 3: Model Training & Validation
```bash
python code/models/run_trainer_wrapper.py
python code/models/evaluator.py
```
*Output*: `data/processed/model_run.json`, `data/validation/evaluation_result.json`

### Step 4: Sensitivity Analysis
```bash
python code/models/evaluator.py --sweep
```
*Output*: `data/processed/sensitivity_analysis.csv`

## Verification

1. Check that `data/processed/electrolyte_features.csv` has no missing values and **does not contain the `band_gap` column** (it is dropped for collinearity).
2. Verify `data/processed/model_run.json` contains R² scores and MAE (internal).
3. Ensure the `sensitivity_analysis.csv` shows rank stability for top 3 features across thresholds.
4. Confirm the report flags "External Validation: N/A" due to missing experimental data.