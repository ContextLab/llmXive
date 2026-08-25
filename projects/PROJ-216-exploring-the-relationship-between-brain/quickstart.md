# Quickstart Guide: Exploring the Relationship Between Brain Network Dynamics and Fluid Intelligence

This guide provides step-by-step instructions to run the full pipeline end-to-end, from data ingestion to final report generation, adhering to the amended specifications (Fluid Intelligence, N=10 baseline, Bonferroni correction).

## Prerequisites

1. **Python Environment**: Python 3.11+
2. **System Dependencies**: FSL (>=6.0) and AFNI (>=21.0) must be installed and available in your `PATH`.
3. **Hardware**: A machine with at least 16GB RAM recommended for processing N=10 subjects.

## Installation

1. **Clone the repository** and navigate to the project root.
2. **Create a virtual environment** (optional but recommended):
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```
3. **Install Python dependencies** listed in `requirements.txt`:
 ```bash
 pip install -r requirements.txt
 ```
4. **Verify system tools** are available:
 ```bash
 python code/verify_env.py
 ```
 If this script fails, install the missing FSL/AFNI tools before proceeding.

## Configuration

Ensure `config.yaml` is correctly set up. The default configuration targets the OpenNeuro dataset `ds000224` with a limit of `n_subjects: 10` as per the ratified amendment `specs/amendment-001-fluid-intelligence-n10.md`.

```bash
cat config.yaml
```

## Step-by-Step Execution

Run the following commands in order. Each step generates artifacts required by the subsequent step.

### 1. Setup Directories
Initialize the required directory structure.
```bash
python code/setup_directories.py
```
*Output*: Creates `data/raw`, `data/interim`, `data/processed`, `data/external`, `tests/unit`, `tests/integration`, `reports`.

### 2. Download and Validate Data
Fetch resting-state fMRI data from OpenNeuro and validate the presence of Fluid Intelligence scores.
```bash
python code/download.py
```
*Output*:
- `data/processed/valid_subjects.json`: List of subjects with valid Fluid Intelligence scores.
- `data/raw/`: Downloaded BIDS dataset.
- *Note*: If no valid Fluid Intelligence data is found, the script will halt with an error.

### 3. Preprocess fMRI Data
Run motion correction, spatial normalization, and bandpass filtering on valid subjects.
```bash
python code/run_preprocessing.py
```
*Output*:
- `data/processed/preprocessed_*.nii.gz`: Cleaned BOLD time series.
- `data/processed/preprocessing_stats.json`: Success rate and subject counts.
- `data/processed/motion_exclusion_log.csv`: Log of excluded subjects due to motion artifacts.

### 4. Generate Graph Metrics
Compute functional connectivity matrices and derive graph theoretical metrics (Global Efficiency, Clustering Coefficient, Modularity).
```bash
python code/graph_metrics.py
```
*Output*:
- `data/processed/graph_metrics.csv`: Aggregated metrics per subject.
- `data/processed/graph_metric_validation.log`: Log of any anomalous values.

### 5. Statistical Analysis
Perform correlation analysis between graph metrics and Fluid Intelligence scores using Bonferroni correction.
```bash
python code/stats.py
```
*Output*:
- `data/processed/correlation_results.csv`: Correlation coefficients, p-values (adjusted), and effect sizes.

### 6. Visualization and Reporting
Generate scatter plots and the final summary report.
```bash
python code/generate_scatter_plots.py
python code/generate_summary_report.py
```
*Output*:
- `reports/scatter_metric_vs_fluid.png`: Visualizations of correlations.
- `reports/summary.pdf`: Comprehensive report including preprocessing stats, correlations, effect sizes, and confidence intervals.

### 7. Resource Profiling (Optional)
Generate a profile of the computational resources used during the analysis.
```bash
python code/generate_analysis_resource_profile.py
```
*Output*:
- `data/processed/analysis_resource_profile.json`: Peak RAM and runtime statistics.

## Reproducibility

To ensure full reproducibility of results:
1. Pin the versions of all dependencies in `requirements.txt`.
2. Use the exact `config.yaml` settings.
3. Ensure the same version of FSL and AFNI are used.
4. The random seeds for any stochastic processes (e.g., Louvain modularity) should be fixed if non-deterministic behavior is observed (check `code/graph_metrics.py`).

## Troubleshooting

- **Missing Fluid Intelligence Data**: If the download step fails, ensure the primary dataset (`ds000224`) or fallback (`ds000230`) contains the required `participants.tsv` with `fluid_intelligence_score`.
- **Motion Exclusion**: If too many subjects are excluded, check `data/processed/motion_exclusion_log.csv`. The pipeline requires at least N=1 valid subject to proceed.
- **FSL/AFNI Errors**: Verify installation paths and environment variables (`$FSLDIR`, `$AFNI_HOME`) are correctly set.

## Governance

This pipeline operates under the authority of `specs/amendment-001-fluid-intelligence-n10.md`, which overrides the original specification regarding Fluid Intelligence focus, Bonferroni correction, and the N=10 baseline.