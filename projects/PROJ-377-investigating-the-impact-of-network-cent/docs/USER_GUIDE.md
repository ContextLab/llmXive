# User Guide

This guide provides a step-by-step walkthrough for using the llmXive pipeline to analyze network centrality and motor memory consolidation.

## Getting Started

### 1. Setup Environment

Ensure you have Python 3.8+ installed. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

### 2. Configure Data Source

Edit `code/utils/config.py` or create a `config.json` to specify the OpenNeuro dataset ID and local paths.

```python
# Example config snippet
DATASET_ID = "ds000000" # Replace with actual dataset ID
```

### 3. Download Data

Run the download script:

```bash
python code/data/download.py
```

This will download the dataset to `data/raw/`. Ensure you have sufficient disk space.

## Running the Pipeline

The pipeline is designed to run sequentially, but individual modules can be executed independently if needed.

### Step 1: Preprocessing and Behavioral Extraction

```bash
python code/data/preprocess.py
```

**What it does**:
- Runs fMRIPrep on the downloaded data.
- Validates retention rates and behavioral data.
- Extracts motor scores and demographics.
- Logs exclusions.

**Outputs**:
- `data/processed/behavioral/subject_scores.csv`
- `data/processed/logs/exclusion_log.csv`
- `data/processed/behavioral/retention_metrics.json`

### Step 2: Centrality Calculation

```bash
python code/analysis/centrality.py
```

**What it does**:
- Loads connectivity matrices for each subject.
- Computes degree, betweenness, and eigenvector centrality for all AAL3 regions.
- Calculates mean Framewise Displacement (FD).
- Aggregates regional metrics into a global centrality score.

**Outputs**:
- `data/processed/centrality/subject_id_metrics.csv`
- `data/processed/centrality/global_scores.csv`
- `data/processed/behavioral/fd_mean.csv`

### Step 3: Regression Analysis

```bash
python code/analysis/regression.py
```

**What it does**:
- Checks VIF for multicollinearity.
- Decides between Global or PCA-Adjusted model based on VIF.
- Fits linear regression and GAM models.
- Generates scatter plots and non-linearity checks.

**Outputs**:
- `data/processed/regression/linear_model_summary.csv`
- `data/processed/regression/nonlinearity_check.csv`
- `figures/regression_scatter.png`

### Step 4: Validation

```bash
python code/analysis/validation.py
```

**What it does**:
- Performs Freedman-Lane permutation tests (1000 iterations).
- Runs 5-fold cross-validation.
- Compares out-of-sample R² against baseline.

**Outputs**:
- `data/processed/validation/null_distribution.csv`
- `data/processed/validation/permutation_results.json`
- `data/processed/validation/cv_results.json`

### Step 5: Reproducibility Report

```bash
python code/utils/metrics.py
```

**What it does**:
- Aggregates all metrics and checksums.
- Generates the final `reproducibility_report.json`.

## Troubleshooting

### Missing Data

If the pipeline fails due to missing columns in metadata, check the `data/raw/metadata.csv` file. Ensure the dataset ID is correct and the download was successful.

### Memory Errors

If you encounter memory errors, ensure you are using the `optimization_utils` module which enforces `float32` and batch processing. You may also need to increase system RAM or reduce batch size in `config.py`.

### fMRIPrep Errors

fMRIPrep requires Docker or Singularity. Ensure your container runtime is running and properly configured. Check `data/processed/logs/fmriprep.log` for specific error messages.

## Customization

### Changing Model Parameters

Edit `code/utils/config.py` to modify:
- VIF threshold
- Permutation count
- Number of CV folds
- Regional analysis flag

### Adding New Metrics

To add new centrality metrics, extend `code/analysis/centrality.py` and update the output schema in `data/processed/centrality/subject_id_metrics.csv`.

## Best Practices

- **Run Phase 0 First**: Always validate data before proceeding.
- **Check Logs**: Monitor `data/processed/logs/` for warnings and exclusions.
- **Version Control**: Commit changes to `config.py` and code to track analysis iterations.
- **Resource Monitoring**: Use the logging module to track RAM and time usage.

## Support

For issues, consult the `docs/ARCHITECTURE.md` or open an issue on the repository.
