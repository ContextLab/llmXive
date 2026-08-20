# Quickstart Guide: Brain Network Dynamics and Fluid Intelligence Pipeline

This guide provides step-by-step instructions to run the entire analysis pipeline end-to-end, from data ingestion to final report generation.

**Prerequisites**
- Python 3.11+
- FSL (>= 6.0) and AFNI (>= 21.0) installed and in PATH
- Git (for cloning the repository)
- Internet connection (for downloading OpenNeuro datasets)

## 1. Environment Setup

### Install Dependencies
Ensure you are in the project root directory.
```bash
pip install -r requirements.txt
```

### Verify System Tools
Run the environment verification script to ensure FSL and AFNI are available.
```bash
python code/verify_env.py
```
*Expected Output*: If all tools are found, the script exits with code 0. If missing, it exits with code 1 and lists the missing tools.

### Initialize Project Structure
Create the necessary directory hierarchy and log file.
```bash
python code/setup_directories.py
```
*Verification*: Check that `data/.verify_structure.log` exists and contains `OK` for all required directories (`data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, `reports`).

## 2. Data Ingestion (User Story 1)

### Download and Validate Data
The pipeline will attempt to download the primary dataset (`ds000224`) from OpenNeuro. If Fluid Intelligence scores are missing, it will fall back to `ds000230`.

```bash
python code/download.py
```

*Key Behaviors*:
- Fetches data from OpenNeuro.
- Validates the presence of `fluid_intelligence_score` in `participants.tsv`.
- Enforces the N=10 sample limit as per `specs/amendment-001-fluid-intelligence-n10.md`.
- Writes `data/processed/valid_subjects.json`.
- **Halts** with error "No valid Fluid Intelligence data found" if no subjects pass validation.

### Preprocessing Pipeline
Preprocess the downloaded fMRI data (motion correction, normalization, bandpass filtering).

```bash
python code/run_preprocessing.py
```

*Output*: `data/processed/preprocessing_stats.json` containing success rates and logs.
*Note*: This step requires FSL/AFNI to be installed.

### Motion Artifact Detection
Detect and exclude subjects with excessive motion.

```bash
python code/motion_detection.py
```

*Output*: `data/processed/motion_exclusion_log.csv` and `data/processed/motion_exclusion.log`.

## 3. Graph Metric Computation (User Story 2)

### Acquire Schaefer Atlas
Ensure the Schaefer atlas (200 ROIs) is available in `data/external/`.

```bash
# (If not already present, download manually or via script if integrated)
# The pipeline assumes the atlas is at data/external/schaefer_200.txt
```

### Compute Connectivity and Graph Metrics
Generate correlation matrices and compute global efficiency, clustering coefficient, and modularity.

```bash
python code/graph_metrics.py
```

*Output*: `data/processed/graph_metrics.csv` containing metrics for each subject.
*Validation*: `data/processed/graph_metric_validation.log` will list any anomalies.

## 4. Statistical Analysis and Reporting (User Story 3)

### Correlation Analysis
Perform correlation analysis between graph metrics and Fluid Intelligence scores with Bonferroni correction.

```bash
python code/stats.py
```

*Output*: `data/processed/correlation_results.csv` containing p-values, Bonferroni-corrected p-values, and effect sizes.

### Generate Visualizations
Create scatter plots of metrics vs. Fluid Intelligence.

```bash
python code/generate_scatter_plots.py
```

*Output*: `reports/scatter_metric_vs_fluid.png`.

### Generate Summary Report
Aggregate all results into a final PDF report.

```bash
python code/generate_summary_report.py
```

*Output*: `reports/summary.pdf` containing plots, coefficients, and preprocessing success rates.

## 5. Resource Profiling

### Monitor Resource Usage
Run the resource monitor to profile RAM and runtime.

```bash
python code/execute_resource_monitor.py
```

*Output*: `data/processed/resource_profile.json` and `data/processed/analysis_resource_profile.json`.

## Verification Checklist

After running the full pipeline, verify the following artifacts exist:
- `data/.verify_structure.log` (Directory creation log)
- `data/processed/valid_subjects.json` (Validated subject list)
- `data/processed/preprocessing_stats.json` (Preprocessing success rate)
- `data/processed/motion_exclusion_log.csv` (Motion exclusion log)
- `data/processed/graph_metrics.csv` (Computed graph metrics)
- `data/processed/correlation_results.csv` (Statistical results)
- `reports/scatter_metric_vs_fluid.png` (Scatter plot)
- `reports/summary.pdf` (Final report)
- `data/processed/analysis_resource_profile.json` (Resource usage stats)

## Troubleshooting

- **Missing Fluid Intelligence Data**: If the pipeline halts with "No valid Fluid Intelligence data found", check the `participants.tsv` files in the downloaded datasets or ensure the fallback dataset (`ds000230`) contains the required scores.
- **FSL/AFNI Errors**: Ensure the tools are installed and their paths are added to your system `PATH` environment variable. Run `python code/verify_env.py` to confirm.
- **Memory Issues**: If you encounter memory errors, reduce the number of subjects in `config.yaml` (though the target is N=10) or ensure sufficient RAM is available.