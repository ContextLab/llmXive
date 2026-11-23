# Predicting Plant Stress Response from Publicly Available Proteomic Data

**Project ID**: PROJ-267-predicting-plant-stress-response-from-pu
**Version**: 1.0.0

## Overview

This project implements an automated scientific pipeline to predict plant stress responses (drought, salinity, heat) in Arabidopsis, Rice, and Wheat using publicly available proteomic and transcriptomic data. The pipeline ingests raw data, normalizes and merges protein/gene expression matrices, handles left-censored missing data (LCM) using MinProb imputation, and trains machine learning models (Random Forest, SVR) with rigorous cross-validation strategies.

## Installation

### Prerequisites
- Python 3.9+
- R (version 4.2+) with `biomaRt` package (version 2023-10)
- `imp3` package (optional, for LCM imputation)

### Setup Steps

1. **Clone the repository**:
 ```bash
 git clone <repository-url>
 cd PROJ-267-predicting-plant-stress-response-from-pu
 ```

2. **Install Python dependencies**:
 ```bash
 pip install -r code/requirements.txt
 ```
 *Note: `rpy2` is a critical dependency. If installation fails, the environment is not ready.*

3. **Verify R Environment**:
 Ensure R is installed and `biomaRt` is available:
 ```bash
 R -e "if (!requireNamespace('biomaRt', quietly = TRUE)) install.packages('biomaRt', repos='https://cloud.r-project.org')"
 ```

4. **Initialize Project Directories**:
 Run the setup script to create required folders:
 ```bash
 python code/setup_directories.py
 python code/setup_data_dirs.py
 python code/setup_docs_dir.py
 ```

5. **Verify Data Sources**:
 Before running the pipeline, verify that all citations in `research.md` are valid:
 ```bash
 python code/data_ingestion/verify_sources.py
 ```

## Usage

### Full Pipeline Execution

Run the complete data ingestion and modeling pipeline:

```bash
python code/main.py
```

This script orchestrates:
1. **Data Ingestion**: Downloads raw data from NCBI GEO/ProteomeXchange.
2. **Normalization**: Filters low-abundance proteins and applies LCM (MinProb) imputation.
3. **Merging**: Maps UniProt IDs to Ensembl IDs using `biomaRt`.
4. **Validation**: Runs sanity checks, sample counts, and completeness metrics.
5. **Modeling**: Trains RF/SVR models with 5-fold CV or LOOCV based on sample size.
6. **Evaluation**: Performs cross-stress validation, baseline comparisons, and permutation tests.
7. **Reporting**: Generates plots and runtime metrics.

### Individual Task Execution

You can run specific stages independently:

**Data Ingestion**:
```bash
python code/data_ingestion/pipeline.py
```

**Model Training**:
```bash
python code/modeling/train.py
```

**Generate Reports**:
```bash
python code/reporting/generate_report.py
```

**Run Unit Tests**:
```bash
python -m pytest tests/unit/ -v
```

## Data Sources

All data is sourced from public repositories. The pipeline fetches real data at runtime; no synthetic data is used.

- **NCBI Gene Expression Omnibus (GEO)**: Transcriptomic data for stress conditions.
- **ProteomeXchange Consortium**: Proteomic datasets (UniProt IDs).
- **Ensembl BioMart**: Identifier mapping (UniProt → Ensembl).

*Refer to `research.md` for the complete list of specific dataset IDs and URLs used in this study.*

### Data Directory Structure
- `data/raw/`: Downloaded raw files (TSV, CSV, XML).
- `data/processed/`: Normalized, merged, and imputed matrices.
- `results/`: Model outputs, metrics, and plots.
- `logs/`: Pipeline execution logs and warnings.

## Results

Upon successful execution, the pipeline generates the following artifacts in the `results/` directory:

- **Metrics**:
 - `within_stress_metrics.json`: R² and RMSE per fold for within-stress validation.
 - `cross_stress_metrics.json`: R² and RMSE for cross-stress predictions.
 - `raw_feature_baseline.json`: Baseline performance without stress labels.
 - `shuffle_control.json`: Permutation test results (p-values).
 - `r2_drop.json`: Calculated drops in R² (Cross vs. Within, Raw vs. Within).
 - `data_completeness.json`: Data retention percentage.
 - `runtime_metrics.json`: CPU time and memory usage.

- **Visualizations** (PNG):
 - Scatter plots (Predicted vs. Actual) with regression lines.
 - Cross-stress heatmaps.
 - Feature importance bar charts.

- **Model Artifacts**:
 - Pickled models and checkpoints in `results/checkpoints/`.

### Key Performance Indicators
- **Data Completeness**: % of initial datasets retained after filtering.
- **Within-Stress R²**: Primary metric for model accuracy.
- **Cross-Stress R²**: Generalization capability across stress types.
- **Drop Metrics**: Quantifies the contribution of stress-specific features.

## Configuration

Edit `code/utils/config.py` to modify:
- Random seeds for reproducibility.
- File paths (default: `data/`, `results/`, `logs/`).
- Species and stress constants.
- Reference-validator threshold (default: 0.7).

## Deviation Log

Any deviations from the standard protocol (e.g., missing `imp3` fallback to custom MinProb) are documented in:
- `docs/deviation_log.md`

## Contributing

1. Ensure all code passes linting (`flake8`) and formatting (`black`).
2. Write unit tests for new logic in `tests/unit/`.
3. Verify that no synthetic data is introduced.

## License

[Insert License Information]