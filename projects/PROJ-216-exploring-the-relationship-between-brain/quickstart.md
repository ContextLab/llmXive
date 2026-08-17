# Quickstart Guide: Brain Network Dynamics & Fluid Intelligence Pipeline

This guide provides step-by-step instructions to run the `llmXive` pipeline end-to-end, from data ingestion to final statistical reporting, adhering to the N=10 baseline and Fluid Intelligence pivot defined in `specs/amendment-001-fluid-intelligence-n10.md`.

## Prerequisites

- **Python**: 3.11+
- **System Tools**: `fsl` (>=6.0), `afni` (>=21.0), `fslmaths`
- **Dependencies**: Install via `requirements.txt`

## 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Verify system dependencies:

```bash
python code/verify_env.py
```

*Expected Output*: Exit code 0 if FSL/AFNI are found. Exit code 1 with an error message if missing.

## 2. Project Initialization

Create the required directory structure:

```bash
python code/setup_directories.py
```

*Verification*: Check `data/.verify_structure.log` for "OK" entries for all directories.

## 3. Data Ingestion (OpenNeuro)

The pipeline fetches resting-state fMRI data from OpenNeuro `ds000224` (Primary) or `ds000230` (Fallback). It validates the presence of **Fluid Intelligence** scores.

```bash
python code/download.py
```

*Expected Behavior*:
- Downloads data to `data/raw/`.
- Validates metadata for `fluid_intelligence_score`, age, and gender.
- Generates `data/processed/valid_subjects.json`.
- **Halt Condition**: If no valid subjects are found, the script exits with error: "No valid Fluid Intelligence data found".

## 4. Preprocessing Pipeline

Preprocesses the valid subjects using FSL/AFNI for motion correction, normalization, and bandpass filtering.

```bash
python code/run_preprocessing.py
```

*Output*:
- Preprocessed NIfTI files in `data/processed/`.
- `data/processed/preprocessing_stats.json` (Success rates).
- `data/processed/motion_exclusion_log.csv` (Subjects excluded due to motion > 3mm translation or > 2mm rotation).

*Note*: The pipeline enforces the N=10 limit and halts if effective N drops to zero after exclusion.

## 5. Graph Metric Computation

Computes functional connectivity matrices using the 200-ROI Schaefer Atlas and derives graph metrics (Global Efficiency, Clustering Coefficient, Modularity).

```bash
python code/graph_metrics.py
```

*Output*:
- `data/processed/graph_metrics.csv` (Subject ID, Metric Name, Value).
- `data/processed/graph_metric_validation.log` (Anomalies).

## 6. Statistical Analysis

Performs correlation analysis between graph metrics and Fluid Intelligence scores, applying **Bonferroni correction** as mandated by the Constitution and Amendment 001.

```bash
python code/stats.py
```

*Output*:
- `data/processed/correlation_results.csv` (Includes `p_adj_bonferroni`, `cohens_d`, `ci_lower`, `ci_upper`).
- `reports/scatter_metric_vs_fluid.png`.

## 7. Resource Profiling

Generates a resource profile of the analysis run.

```bash
python code/generate_analysis_resource_profile.py
```

*Output*: `data/processed/analysis_resource_profile.json` (Peak RAM, Total Runtime).

## 8. Final Report Generation

Aggregates all results into a summary PDF.

```bash
python code/generate_summary_report.py
```

*Output*: `reports/summary.pdf` containing scatter plots, regression lines, correlation coefficients, and effect sizes.

## Verification Checklist

After running the pipeline, verify the following artifacts exist:

- [ ] `data/processed/valid_subjects.json`
- [ ] `data/processed/preprocessing_stats.json`
- [ ] `data/processed/graph_metrics.csv`
- [ ] `data/processed/correlation_results.csv`
- [ ] `reports/scatter_metric_vs_fluid.png`
- [ ] `reports/summary.pdf`

## Troubleshooting

- **Missing Fluid Intelligence Data**: Ensure the OpenNeuro dataset `ds000224` contains the required sidecar JSON fields. If missing, the pipeline will halt.
- **FSL/AFNI Not Found**: Run `verify_env.py` to diagnose. Install missing tools via system package managers.
- **Zero Valid Subjects**: If motion exclusion removes all subjects, check `data/processed/motion_exclusion_log.csv` for high motion artifacts. The pipeline is designed to halt in this scenario per the N=10 baseline constraints.