# Quickstart Guide: Predicting the Impact of Cold Work on Recrystallization Kinetics

This guide provides a 5-step execution process to run the full pipeline from data generation to model evaluation.

## Prerequisites

- Python 3.8+
- pip
- Required packages (see `requirements.txt`)

## Step 1: Setup Project Structure

Ensure all required directories exist:

```bash
python code/setup_project_structure.py
python code/setup_data_dirs.py
```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Run the Full Pipeline

Execute the entire pipeline from data generation to evaluation:

```bash
python code/main.py --step all
```

Alternatively, run individual steps:

```bash
# Generate synthetic data
python code/main.py --step generate

# Ingest and validate data
python code/main.py --step ingest

# Engineer features
python code/main.py --step engineer

# Finalize dataset
python code/main.py --step finalize

# Train model
python code/main.py --step train

# Evaluate model
python code/main.py --step evaluate
```

## Step 4: Verify Outputs

Check that the following artifacts were created:

- `data/raw/synthetic_baseline.csv` - Generated synthetic data
- `data/processed/validated.csv` - Validated and cleaned data
- `data/processed/engineered_features.csv` - Features with interaction terms
- `data/processed/final_dataset.csv` - Final dataset ready for modeling
- `artifacts/models/kinetic_model.pkl` - Trained model
- `artifacts/reports/training_metrics.json` - Model performance metrics
- `artifacts/reports/statistical_significance.json` - Statistical test results
- `artifacts/reports/shap_interaction_report.json` - SHAP analysis results

## Step 5: Review Results

Examine the generated reports to understand:

- Model performance (MAE, R²)
- Statistical significance of interaction terms
- Key features driving recrystallization kinetics

## Troubleshooting

- If you encounter import errors, ensure you're running from the project root.
- If data files are missing, run `python code/main.py --step all` to regenerate everything.
- For memory issues, reduce dataset size in `config.py`.