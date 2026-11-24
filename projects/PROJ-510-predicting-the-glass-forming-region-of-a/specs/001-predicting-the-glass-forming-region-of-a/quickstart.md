# Quickstart Guide for Glass Forming Region Prediction Pipeline

This guide shows how to run the entire research pipeline from a fresh checkout.

## Prerequisites

- Python 3.9+
- Git
- Internet access (to download the experimental CCR dataset and OQMD elemental properties)

## Setup

1. **Clone the repository**  
   ```bash
   git clone <repo-url>
   cd PROJ-510-predicting-the-glass-forming-region-of-a
   ```

2. **Create a virtual environment and install dependencies**  
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Run the full pipeline

The pipeline can be executed with a single command:

```bash
python -m code.run_all
```

This command runs the following steps in order:

1. **Data ingestion & cleaning** – `code/ingestion.py`  
   Downloads the CCR dataset, streams OQMD elemental properties, filters invalid rows, and writes the cleaned CSV to `data/processed/processed_alloys_raw.csv`.

2. **Feature engineering** – `code/features.py`  
   Computes `mixing_enthalpy`, `atomic_size_mismatch`, and `electronegativity_variance`, producing `data/processed/processed_alloys.csv`.

3. **Model training & cross‑validation** – `code/train.py`  
   Performs a stratified 80/20 split, trains a Random Forest regressor, runs 5‑fold CV, and saves the model and metrics.

4. **Analysis & importance** – `code/analyze.py`  
   Generates permutation importance, collinearity checks, and sensitivity analysis, writing reports to `data/reports/`.

5. **Report generation** – `code/generate_report.py`  
   Compiles a markdown report (`REPORT.md`) summarizing data, model performance, feature importance, and sensitivity results.

6. **Schema validation** – `code/validate_schemas.py`  
   Validates all generated artifacts against their YAML contracts; the script prints “All schemas validated - 0 errors.” when successful.

After the command finishes, you should see the artifacts listed above in the `data/` directory and a `REPORT.md` file at the project root.
