# Quickstart Guide: Predicting Phase Transitions in Amorphous Solids

This guide provides step-by-step instructions to run the full machine learning pipeline
for predicting phase transitions in amorphous solids (Pilot Study: N=24 compositions [UNRESOLVED-CLAIM: c_f63ca216 — status=not_enough_info]).

## Prerequisites

- Python 3.9+
- Access to a CPU environment (GPU not required for this pilot)
- Internet connection (for downloading dependencies and real data sources)

## 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd PROJ-203-predicting-phase-transitions-in-amorphou

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## 2. Directory Structure Initialization

The pipeline expects specific directories for data, models, and reports. Run the setup script:

```bash
python code/setup_directories.py
```

This creates:
- `data/raw/`, `data/processed/`, `data/logs/`
- `code/models/`, `code/utils/`, `code/data/`
- `artifacts/models/`, `artifacts/figures/`, `artifacts/reports/`
- `docs/`

## 3. Data Validation

Before running simulations, verify that the literature subset data exists:

```bash
python code/data/validate_literature_subset.py
```

**Note**: This script will fail loudly with `FileNotFoundError` if `data/raw/literature_subset.csv` is missing.
Do not attempt to bypass this check with synthetic data.

## 4. Running the Full Pipeline

Execute the entire pipeline from simulation to model evaluation:

```bash
python code/main.py
```

This single entry point orchestrates:
1. **Data Loading & Validation**: Verifies `literature_subset.csv` and pilot compositions.
2. **Simulation Execution**: Runs MD simulations for 24 pilot compositions [UNRESOLVED-CLAIM: c_5a7295b5 — status=not_enough_info] (with time caps).
3. **Descriptor Extraction**: Calculates RDF, bond-angle variance, and coordination numbers.
4. **Virtual Alignment**: Aligns MD timescales with experimental cooling rates.
5. **Dataset Merging & Labeling**: Combines descriptors with experimental Tg/Tx and creates crystallization labels.
6. **Model Training**: Trains Random Forest regressor (Tg) and classifier (crystallization).
7. **Cross-Validation & Metrics**: Performs k-fold CV and computes RMSE/ROC-AUC.
8. **Interpretability**: Generates SHAP plots, partial dependence plots, and stability reports.
9. **Validation Reports**: Produces null model, permutation, collinearity, and timing reports.

**Expected Runtime**: ≤ 6 hours (enforced by `code/utils/timeout_enforcer.py`).

## 5. Output Artifacts

Upon successful completion, the following artifacts are generated:

### Data
- `data/processed/final_dataset.parquet`: Merged dataset with descriptors, labels, and metadata.
- `data/processed/sensitivity_report.json`: Threshold sensitivity analysis results.
- `data/logs/excluded_rows.log`: Log of excluded compositions with reasons.

### Models
- `models/tg_regressor.pkl`: Trained Random Forest regressor for Tg prediction.
- `models/crystallization_classifier.pkl`: Trained Random Forest classifier.

### Reports & Figures
- `docs/reports/metrics.json`: RMSE, ROC-AUC, and CV scores.
- `docs/reports/confusion_matrix.png`: Confusion matrix for crystallization classification.
- `docs/reports/shap_plots/`: SHAP summary and beeswarm plots per chemical family.
- `docs/reports/interpretability_report.md`: Final report on universal vs. family-specific predictors.
- `docs/reports/null_model_report.json`: Null model and permutation test results.
- `docs/reports/collinearity_report.json`: VIF analysis for predictor collinearity.
- `docs/reports/stability_report.json`: LOO jackknife stability analysis.
- `docs/reports/pipeline_timing.json`: End-to-end timing verification.

## 6. Individual Task Execution

If you need to run specific stages independently:

```bash
# Data Pipeline
python code/data/simulate.py
python code/data/descriptor_utils.py
python code/data/merge.py
python code/data/finalize_dataset.py

# Model Training
python code/models/train.py

# Evaluation & Interpretability
python code/models/generate_metrics_report.py
python code/models/generate_shap_plots.py
python code/models/partial_dependence_analysis.py
python code/models/stability_analysis.py
```

## 7. Troubleshooting

### Missing Data Files
If `validate_literature_subset.py` fails, ensure `data/raw/literature_subset.csv` is present.
This file must be obtained from the verified real data source (Zenodo/NIST) as specified in the project plan.

### Simulation Timeouts
If simulations are truncated, check `data/logs/simulation_times.json` for per-composition timing.
The pipeline enforces a 6-hour wall-clock limit [UNRESOLVED-CLAIM: c_a5b5c8c7 — status=not_enough_info] via `code/utils/timeout_enforcer.py`.

### Model Performance
If RMSE > 15 K or ROC-AUC ≤ 0.7, review `docs/reports/null_model_report.json` and `docs/reports/collinearity_report.json`
to assess statistical validity and predictor quality.

## 8. Verification

To verify the pipeline completed successfully:

```bash
# Check for final dataset
ls -lh data/processed/final_dataset.parquet

# Check for model artifacts
ls -lh models/*.pkl

# Check for required reports
ls -lh docs/reports/*.json docs/reports/*.png docs/reports/*.md
```

All files should be non-empty and contain valid data/figures.

## 9. Next Steps

- Review `docs/reports/interpretability_report.md` for scientific insights.
- Analyze `docs/reports/stability_report.json` for feature stability confidence intervals.
- Consider expanding the pilot to N > 24 compositions for broader validation.

---
*This pipeline implements the pilot study (N=24) as defined in `spec.md` and `plan.md`.
Performance targets (RMSE ≤ 15 K, ROC-AUC > 0.7) are validated via Null Model/Permutation Tests.*
