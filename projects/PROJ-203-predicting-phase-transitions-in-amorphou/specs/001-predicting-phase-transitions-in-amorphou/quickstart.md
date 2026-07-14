# Quickstart: Predicting Phase Transitions in Amorphous Solids

## Prerequisites

- Python 3.11+
- `pip`
- Access to GitHub Actions (for CI) or a local Linux environment with 7GB+ RAM.
- (Optional) `lammps` binary installed if running simulations locally (not required for the CPU-only CI plan if using a pre-built container or OpenMM).

## Installation

1. **Clone the repository** (or navigate to the project root).
2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/requirements.txt
   ```

## Running the Pipeline

The pipeline is designed to run end-to-end on a CPU-only runner.

### Step 1: Data Preparation
Fetch experimental data (simulated fallback if source unavailable) and generate structural descriptors.
```bash
python projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/data/download.py
python projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/data/simulate.py  # Capped at 30m/composition
python projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/data/extract.py
```

### Step 2: Model Training
Train Random Forest models and perform cross-validation.
```bash
python projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/models/train.py
```
*Note: This step will complete within 2 hours on a 2-CPU runner.*

### Step 3: Analysis & Reporting
Generate SHAP plots, sensitivity analysis, and final metrics.
```bash
python projects/PROJ-203-predicting-phase-transitions-in-amorphou/code/models/evaluate.py
```

## Expected Outputs

- `data/processed/final_dataset.parquet`: Merged dataset.
- `models/tg_regressor.pkl`: Trained regression model.
- `models/crystallization_classifier.pkl`: Trained classification model.
- `docs/reports/metrics.json`: RMSE, ROC-AUC, and feature importance.
- `docs/reports/shap_summary_oxide.png`, `sulfide.png`, `organic.png`: Interpretability plots.

## Troubleshooting

- **Simulation Timeout**: If a composition takes >30m, the script will truncate the trajectory. Check `logs/truncation.log`.
- **Missing Experimental Data**: If $T_g$ is missing for a composition, it is excluded. Check `logs/missing_data.log`.
- **Memory Error**: If RAM > 7GB, reduce the batch size in `config.py` or sample fewer compositions.
