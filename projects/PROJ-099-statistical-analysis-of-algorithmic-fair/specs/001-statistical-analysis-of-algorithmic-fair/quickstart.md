# Quickstart: Fairness Metric Divergence Analysis

## Prerequisites

- Python 3.11+
- pip package manager
- 7 GB+ available RAM
- 14 GB+ available disk space

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   cd projects/PROJ-099-statistical-analysis-of-algorithmic-fair
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r code/requirements.txt
   ```

## Running the Pipeline

### Step 1: Data Acquisition

Download datasets and verify checksums:
```bash
python code/01_data_acquisition.py
```

Expected output:
- Downloaded dataset files in data/raw/
- Checksum verification results
- Exclusion events logged to logs/exclusion.log (if any)

### Step 2: Preprocessing

Preprocess datasets to extract fairness-relevant features:
```bash
python code/02_preprocessing.py
```

Expected output:
- Preprocessed datasets in data/processed/
- Variable verification report
- Sampling applied if datasets exceed 100k rows

### Step 3: Model Training

Train baseline models per dataset:
```bash
python code/03_model_training.py
```

Expected output:
- Trained models in data/processed/models/
- Model performance metrics
- Random seeds logged for reproducibility

### Step 4: Fairness Metric Computation

Compute fairness metrics for each model:
```bash
python code/04_fairness_metrics.py
```

Expected output:
- Fairness metrics in data/analysis/metrics.csv
- 6+ metrics per model

### Step 5: Correlation Analysis

Compute pairwise correlations:
```bash
python code/05_correlation_analysis.py
```

Expected output:
- Correlation matrix in data/analysis/correlations.csv
- Benjamini-Hochberg corrected q-values

### Step 6: Regression Analysis

Fit OLS regression models with dataset characteristics:
```bash
python code/06_regression_analysis.py
```

Expected output:
- Regression results in data/analysis/regression_results.csv
- VIF diagnostics report

### Step 7: Bootstrap Analysis

Perform bootstrap resampling:
```bash
python code/07_bootstrap_analysis.py
```

Expected output:
- Bootstrap confidence intervals in data/analysis/bootstrap_results.csv
- 95% CIs for all correlation coefficients

### Step 8: Metric Selection Guidance

Generate associational guidance output:
```bash
python code/08_metric_guidance.py
```

Expected output:
- Guidance mappings in data/analysis/guidance.csv
- Associational disclaimer included

## Verification

Run tests to verify the pipeline:
```bash
pytest tests/
```

## Expected Artifacts

After successful execution:
- data/raw/*: Raw downloaded datasets
- data/processed/*: Preprocessed datasets
- data/analysis/metrics.csv: Fairness metrics
- data/analysis/correlations.csv: Correlation results
- data/analysis/bootstrap_results.csv: Bootstrap results
- data/analysis/regression_results.csv: Regression results
- data/analysis/guidance.csv: Metric selection guidance (associational only)
- logs/exclusion.log: Exclusion events (if any)

## Troubleshooting

### Dataset Download Fails

If a dataset cannot be downloaded:
1. Check network connectivity
2. Verify the URL in code/utils/dataset_loaders.py
3. Log exclusion event to logs/exclusion.log

### Memory Constraints

If running out of memory:
1. Reduce bootstrap iterations from 1000 to 500
2. Sample datasets to smaller sizes
3. Close other applications

### Time Constraints

If exceeding 6-hour window:
1. Reduce bootstrap iterations
2. Reduce number of models per dataset
3. Log constraint in logs/exclusion.log

## Associational Disclaimer

All outputs from this pipeline include the disclaimer: "Findings are associational only; no causal claims are made." This applies to all regression results, correlation analyses, and guidance outputs.