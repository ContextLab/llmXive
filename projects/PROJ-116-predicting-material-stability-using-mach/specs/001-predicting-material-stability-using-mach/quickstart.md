# Quickstart: Predicting Material Stability using Machine Learning and DFT Calculations

## Prerequisites
- Python 3.11+
- 7 GB RAM available (for CI or local run)
- Internet connection (to download OQMD data)

## Installation

1. **Clone the repository** and navigate to the project directory.
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

The pipeline consists of four sequential steps. Execute them in order:

### Step 1: Download and Filter Data
Downloads the OQMD dataset, filters for Li-rich rock-salt structures (topological criteria), and validates structural data integrity.
```bash
python code/download_data.py
```
*Output*: `data/processed/filtered_oqmd.parquet`

### Step 2: Feature Engineering
Computes Magpie and local coordination features, aggregates them into fixed-size vectors, and calculates VIF for collinearity.
```bash
python code/feature_engineering.py
```
*Output*: `data/processed/featurized_data.parquet`

### Step 3: Train Models
Trains the baseline and augmented Gradient Boosting models.
```bash
python code/train_baseline.py
python code/train_augmented.py
```
*Output*: `data/models/baseline_model.pkl`, `data/models/augmented_model.pkl`, `outputs/baseline_results.csv`, `outputs/comparison_metrics.json`

### Step 4: Evaluate and Analyze
Calculates metrics, performs sensitivity analysis, runs permutation tests, and generates plots (including Near-Hull specific metrics).
```bash
python code/evaluate.py
```
*Output*: `outputs/sensitivity_analysis.csv`, `outputs/figures/`, `outputs/logs/`

## Expected Outputs

- **baseline_results.csv**: Predicted formation energies and MAE/RMSE for the baseline model.
- **comparison_metrics.json**: Delta in MAE and R² between baseline and augmented models, including p-value from permutation test.
- **sensitivity_analysis.csv**: Classification metrics (Recall, Precision, F1) across thresholds 0.04, 0.05, 0.06 eV/atom, specifically for the Near-Hull cohort.
- **figures/**: Feature importance plots (SHAP/Permutation), ROC curves (overall and Near-Hull), and VIF analysis plots.

## Troubleshooting

- **Memory Error**: If the process exceeds 7 GB RAM, the script will attempt to sample the data. Ensure no other heavy processes are running.
- **Missing OQMD Data**: Verify internet connection. The script will retry failed downloads.
- **Structural Data Missing**: If `download_data.py` cannot find structural data for a material ID, it will log the exclusion and proceed.
- **Convex Hull Failure**: If `pymatgen` fails for a specific composition, it will be excluded from classification metrics but retained in regression analysis (logged in `outputs/logs/`).