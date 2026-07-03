# Quickstart Guide: Network Module Dynamics in Predicting Working Memory

This guide walks you through setting up and running the pipeline to analyze the role of network module dynamics (temporal flexibility) in predicting working memory performance using HCP data (ds001734).

## Prerequisites

- Python 3.11+
- pip
- At least 7GB of available RAM
- Internet connection (for initial data download)

## Installation

1. **Clone the repository** (if not already done):
 ```bash
 git clone <repository-url>
 cd PROJ-383-the-role-of-network-module-dynamics-in-p
 ```

2. **Install dependencies**:
 ```bash
 cd code
 pip install -r requirements.txt
 cd..
 ```

3. **Initialize project directories**:
 ```bash
 python code/initialize_directories.py
 ```
 This creates the necessary folder structure:
 - `code/`
 - `data/raw_fmri`
 - `data/raw_behavior`
 - `data/processed`
 - `data/results`
 - `data/results/plots`

## Running the Pipeline

The pipeline is executed in three main stages corresponding to the user stories.

### Stage 1: Data Ingestion and Preprocessing (User Story 1)

Downloads and preprocesses resting-state fMRI and behavioral data.

```bash
# Validate dataset availability (ds001734)
python code/ingestion/validate_source.py

# Download subject data (default: 100 subjects)
python code/ingestion/download_hcp.py

# Preprocess data: motion scrubbing, regression, and consolidation
python code/ingestion/preprocess.py

# Consolidate cleaned time series with behavioral scores
python code/ingestion/consolidate_data.py
```

**Outputs**:
- `data/processed/scrubbed_timeseries.parquet`
- `data/processed/consolidated_data.parquet`

### Stage 2: Dynamic Flexibility Metric Computation (User Story 2)

Computes temporal flexibility using Multilayer Modularity Optimization.

```bash
# Compute dynamic connectivity and flexibility scores
python code/analysis/dynamic_connectivity.py

# Aggregate and save flexibility scores
python code/analysis/output_flexibility_scores.py
```

**Outputs**:
- `data/processed/flexibility_scores.parquet`

### Stage 3: Statistical Analysis and Reporting (User Story 3)

Performs partial correlation, permutation tests, and sensitivity analysis.

```bash
# Run statistical analysis (partial Spearman correlation, permutation test)
python code/analysis/statistics.py

# Run sensitivity analysis across window lengths
python code/analysis/sensitivity_analysis.py

# Generate final report and visualizations
python code/results/generate_report.py
python code/results/generate_plots.py
```

**Outputs**:
- `data/results/statistical_report.json`
- `data/results/sensitivity_analysis.json`
- `data/results/plots/null_dist.png`
- `data/results/plots/sensitivity_plot.png`

## Verification

Run the test suite to verify the pipeline:

```bash
pytest tests/ -v
```

## Memory Constraints

The pipeline enforces a 7GB RAM limit. If you encounter memory issues:
- Reduce the number of subjects in `download_hcp.py`
- Ensure no other heavy applications are running
- Check logs in `data/logs/` for memory usage events

## Logging

All processing events, exclusions, and memory usage are logged to:
- `data/logs/pipeline.log`
- `data/logs/exclusions.log`

Review these logs to understand subject exclusions (e.g., excessive motion) and resource usage.
