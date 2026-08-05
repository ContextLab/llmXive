# Quickstart Guide

This guide provides step-by-step instructions to reproduce the full analysis pipeline for exploring the relationship between brain network dynamics and fluid intelligence.

## Prerequisites

Ensure you have the following installed:
- Python 3.11 or higher
- pip
- FSL (FMRIB Software Library)
- AFNI (Analysis of Functional NeuroImages)
- Git

## Step 1: Environment Setup

1. **Clone the Repository**
 ```bash
 git clone <repository-url>
 cd PROJ-216-exploring-the-relationship-between-brain
 ```

2. **Install Dependencies**
 ```bash
 python -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```

3. **Verify System Dependencies**
 Run the dependency check script to ensure FSL and AFNI are available:
 ```bash
 python code/dependency_check.py
 ```
 *Expected Output*: A JSON report indicating which tools are available.

## Step 2: Project Initialization

Create the required directory structure:
```bash
python code/setup_directories.py
```
*Output*: Creates `data/raw`, `data/interim`, `data/processed`, `code/__init__.py`, `tests/unit`, `tests/integration`, and `reports/`.

## Step 3: Data Ingestion

Download the OpenNeuro datasets `ds000224` and `ds000230`. The script prioritizes `ds000224` for Fluid Intelligence scores and enforces a sample limit of N=10 for CI environments.
```bash
python code/download.py
```
*Output*:
- `data/raw/ds000224/`
- `data/raw/ds000230/` (if available)
- `data/processed/subject_list.json`

## Step 4: Preprocessing

Run the preprocessing pipeline to perform motion correction, spatial normalization, and bandpass filtering.
```bash
python code/preprocess.py
```
*Output*:
- Preprocessed NIfTI files in `data/processed/`
- `data/processed/preprocessing_stats.json`
- `data/processed/resource_profile.json`

## Step 5: Graph Metric Computation

Compute functional connectivity matrices and derive graph theoretical metrics.
```bash
python code/aggregate_graph_metrics.py
```
*Output*:
- `data/processed/graph_metrics.csv`
- `data/processed/graph_metric_validation.log`

## Step 6: Statistical Analysis

Perform correlation analysis between graph metrics and Fluid Intelligence scores with Bonferroni correction.
```bash
python code/stats.py
python code/calculate_effect_sizes.py
```
*Output*:
- Updated `data/processed/graph_metrics.csv` (with effect sizes)
- Statistical summary in `reports/`

## Step 7: Visualization and Reporting

Generate scatter plots and the final summary report.
```bash
python code/generate_scatter_plots.py
python code/generate_analysis_resource_profile.py
```
*Output*:
- `figures/scatter_plots/`
- `reports/summary.pdf`
- `data/processed/analysis_resource_profile.json`

## Verification

To verify the entire pipeline:
```bash
pytest tests/integration/test_pipeline.py
```

## Troubleshooting

- **Missing FSL/AFNI**: Install via your package manager or from the official websites.
- **Download Failures**: Ensure network connectivity and check OpenNeuro status.
- **Memory Errors**: The pipeline is optimized for N=10 subjects on 7GB RAM. For larger datasets, increase resources.
