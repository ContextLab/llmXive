# Quick Start Guide

This guide provides step-by-step instructions to run the full pipeline for evaluating the correlation between compositional features and predicted formation energy in inorganic materials.

## Step 1: Environment Setup

```bash
# Navigate to project root
cd projects/PROJ-509-evaluating-the-correlation-between-compo

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# Install dependencies
pip install -r code/requirements.txt
```

## Step 2: Data Ingestion (Task T012, T013)

Download and filter the MP-2020.12.1 dataset:

```bash
cd code
python ingest.py
```

**What this does:**
- Downloads the dataset from Zenodo (DOI: 10.5281/zenodo.4053859) [UNRESOLVED-CLAIM: c_2312e986 — status=not_enough_info]
- Filters for inorganic compounds
- Samples by chemical family if dataset exceeds memory threshold
- Outputs: `data/processed/sampled_raw_data.csv`

**Expected output:**
- `data/processed/sampled_raw_data.csv`
- `data/processed/sampling_manifest.json`
- `data/logs/sampling.log`

## Step 3: Descriptor Computation (Task T014, T015, T016, T017)

Compute mean/variance descriptors and handle outliers:

```bash
python descriptors.py
```

**What this does:**
- Loads elemental properties using pymatgen/matminer
- Computes mean and variance for 5 descriptors (electronegativity, radius, valence, melting point, ionization energy)
- Caps outliers at 1st and 99th percentiles of formation energy
- Validates against schema

**Expected output:**
- `data/processed/computed_descriptors.csv`
- `data/logs/outliers.log`

## Step 4: Model Training (Task T020, T021, T022)

Train Random Forest and Gradient Boosting models:

```bash
python train.py
```

**What this does:**
- Performs 80/20 stratified split by Crystal System
- Trains Random Forest (`n_estimators=200`, `max_depth=20`)
- Trains Gradient Boosting (`n_estimators=100`)
- Saves trained models

**Expected output:**
- `data/evaluation/trained_models.pkl`

## Step 5: Model Evaluation (Task T023, T024, T025, T026)

Evaluate models and calculate metrics:

```bash
python evaluate.py
```

**What this does:**
- Calculates R², MAE, RMSE for both models
- Computes Total Variation Distance (TVD) between train/val distributions
- Calculates overfitting ratio
- Saves metrics

**Expected output:**
- `data/evaluation/model_metrics.json`

## Step 6: Feature Importance Analysis (Task T038, T039, T040, T047)

Extract feature importances and perform sensitivity analysis:

```bash
python importance.py
```

**What this does:**
- Extracts RF feature importances
- Calculates permutation importance
- Validates correlation between methods (r ≥ 0.8)
- Ranks features
- Calculates Variance Inflation Factor (VIF)

**Expected output:**
- `data/evaluation/feature_ranking.json`
- `data/evaluation/permutation_importance.json`
- `data/evaluation/vif_scores.json`

## Step 7: Visualization (Task T041, T042)

Generate Partial Dependence Plots:

```bash
python plots.py
```

**What this does:**
- Generates PDPs for top-ranked features
- Saves visualizations

**Expected output:**
- `data/evaluation/pdp_plots/` directory with plot files

## Step 8: Research Summary (Optional)

Generate final research summary:

```bash
python generate_research_summary.py
```

**Expected output:**
- `research.md` with metrics, VIF results, and PDP interpretations

## Full Pipeline Execution

To run all steps in sequence:

```bash
cd code
python run_validation.py
```

This script orchestrates the entire pipeline, ensuring each step completes successfully before proceeding to the next.

## Troubleshooting

### Memory Issues
If you encounter memory errors during descriptor computation:
- The `descriptors.py` script includes chunked processing logic
- Ensure `data/logs/outliers.log` is checked for processing status

### Data Download Failures
If the Zenodo download fails:
- Check your internet connection
- Verify the DOI: 10.5281/zenodo.4053859
- The script will fail loudly rather than using synthetic data

### Missing Dependencies
If import errors occur:
```bash
pip install -r code/requirements.txt --force-reinstall
```

## Validation

To verify all artifacts were created correctly:

```bash
# Check for required output files
ls data/processed/sampled_raw_data.csv
ls data/processed/computed_descriptors.csv
ls data/evaluation/trained_models.pkl
ls data/evaluation/model_metrics.json
ls data/evaluation/feature_ranking.json
ls data/evaluation/pdp_plots/
```

## Next Steps

After completing the pipeline:
1. Review `data/evaluation/model_metrics.json` for model performance
2. Analyze `data/evaluation/feature_ranking.json` for important descriptors
3. Examine PDPs in `data/evaluation/pdp_plots/` for feature relationships
4. Generate `research.md` using `generate_research_summary.py`