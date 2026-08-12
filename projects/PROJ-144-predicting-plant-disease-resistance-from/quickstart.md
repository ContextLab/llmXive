# Quick Start Guide

This guide provides a streamlined overview of how to run the full pipeline for predicting plant disease resistance from metabolomic data.

## Prerequisites

- Python 3.11 or higher
- pip
- Git (for cloning the repository)

## Step 1: Clone and Setup

```bash
git clone <repository-url>
cd PROJ-144-predicting-plant-disease-resistance-from
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Verify Data Sources

Before running the pipeline, ensure that valid Metabolomics Workbench Study IDs are available.

```bash
python code/research/verify_studies.py
```

This script will:
- Search for studies containing pre-challenge metabolite profiles and disease-resistance metadata
- Update `research.md` with valid Study IDs (e.g., C-STUDY-XXXX)

**Important**: If no valid studies are found, the pipeline will halt with a `DataUnavailableError`. Do not proceed without valid Study IDs.

## Step 3: Run the Full Pipeline

Execute the pipeline in the following order:

### 3.1 Data Preprocessing

```bash
# Validate temporal consistency of studies
python code/data/validate_temporal.py

# Download, normalize, and batch-correct data
python code/data/run_preprocess.py
```

**Outputs**:
- `data/processed/batch_corrected_matrix.csv`
- `data/processed/labels.csv`

### 3.2 Model Training and Evaluation

```bash
# Train the Random Forest model
python code/modeling/train.py

# Evaluate model performance and perform correlation analysis
python code/modeling/evaluate.py

# Run collinearity diagnostics (VIF)
python code/modeling/collinearity.py

# Generate final metrics and reports
python code/modeling/generate_final_metrics.py
python code/modeling/generate_associational_report.py
```

**Outputs**:
- `results/metrics.json`
- `results/shap_analysis.json`

### 3.3 Biological Interpretation

```bash
# Interpret model and map metabolites to pathways
python code/modeling/interpret.py

# Save pathway results
python code/modeling/save_pathway_results.py

# Visualize pathway importance
python code/modeling/visualize_pathways.py
```

**Outputs**:
- `results/pathway_analysis.json`
- `results/pathway_barplot.png`

## Step 4: Verify Outputs

Ensure all expected artifacts have been generated:

```bash
# Check data artifacts
ls -l data/processed/

# Check result artifacts
ls -l results/

# Check state artifacts
cat state/artifact_hashes.yaml
```

## Step 5: Run Tests (Optional)

```bash
pytest tests/ -v
```

## Troubleshooting

### Data Unavailable Error

If you encounter a `DataUnavailableError`, it means no valid Metabolomics Workbench studies were found. Verify that:
- The Metabolomics Workbench API is accessible
- `research.md` contains valid Study IDs
- The studies contain both pre-challenge metabolite profiles and disease-resistance metadata

### Memory Issues

The pipeline is designed to run on the CI free-tier (≤7GB RAM). If you encounter memory issues:
- Ensure you are using the latest version of the code
- Check that you are not running multiple processes simultaneously
- Consider reducing the dataset size by filtering studies

### Dependency Errors

If you encounter import errors:
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Verify your Python version is 3.11 or higher

## Next Steps

- Review the generated `results/metrics.json` and `results/shap_analysis.json` for model performance
- Examine `results/pathway_barplot.png` for biological insights
- Read the full documentation in `README.md` for detailed explanations of each step

## Support

For issues or questions, please open an issue in the repository.