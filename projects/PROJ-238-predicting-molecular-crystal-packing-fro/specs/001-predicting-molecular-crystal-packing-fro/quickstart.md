# Quickstart: Predicting Molecular Crystal Packing

## Prerequisites

- Python 3.11+
- `pip`
- Access to the internet (for downloading COD data).

## Installation

1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline is executed sequentially:

1. **Ingest and Compute Descriptors**:
   ```bash
   python code/01_ingest_and_descriptors.py --sample-size 1000
   ```
   *This downloads COD CIFs, computes descriptors, handles missing data (imputation/exclusion), and saves `data/processed/descriptors.csv`.*

2. **Train Models**:
   ```bash
   python code/02_train_models.py
   ```
   *This splits data (stratified by packing_coefficient), trains RF, GB, Baseline, and Control models, and saves model artifacts.*

3. **Evaluate and Report**:
   ```bash
   python code/03_evaluate_and_report.py
   ```
   *This generates metrics (with Bonferroni correction), plots, sensitivity report (LOFO), and interaction classification report.*

## Verification

Check `results/metrics.json` for the R² scores and p-values. Ensure the `bonferroni_corrected_p` is < 0.05 to confirm statistical significance. Review `results/sensitivity_report.md` for the LOFO analysis.
