# Quick Start Guide

This guide provides step-by-step instructions to set up and run the Statistical Evaluation of Dimensionality Reduction pipeline.

## Prerequisites

- Python 3.9 or higher
- Conda (recommended) or pip
- Snakemake (if running via Snakemake directly)
- At least 8GB RAM recommended for full dataset processing

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd projects/001-statistical-evaluation-of-dimensionality
```

## Step 2: Create the Environment

### Option A: Using Conda (Recommended)

```bash
conda env create -f environment.yml
conda activate stat_dim_eval
```

### Option B: Using pip

```bash
# Generate requirements.txt
python code/scripts/generate_requirements.py

# Install dependencies
pip install -r code/requirements.txt
```

## Step 3: Verify Installation

Run the data gap resolver to verify connectivity and data availability:

```bash
python code/data_gap_resolver.py
```

This will check for raw count matrices for GSE131907, GSE111322, and GSE150728.

## Step 4: Run the Pipeline

### Full Pipeline

Run the main entry point:

```bash
python code/main.py
```

This will:
1. Check data availability
2. Download raw count matrices
3. Preprocess data (QC, HVG selection, sampling)
4. Generate embeddings (PCA, t-SNE, UMAP)
5. Compute geometric metrics
6. Perform clustering and fidelity analysis
7. Fit statistical models
8. Generate reports

### Using Snakemake Directly

```bash
snakemake --cores 4 --use-conda
```

### Dry Run (Test Configuration)

```bash
snakemake --cores 2 --dry-run
```

## Step 5: Review Results

Check the `results/` directory for outputs:

- `results/summary.json`: Overall pipeline status
- `results/data_gap_report.json`: Data availability details
- `results/monitoring.csv`: Resource usage (RAM, time)
- `results/geometry_metrics.csv`: Trustworthiness and LCA scores
- `results/fidelity_metrics.csv`: ARI and NMI scores
- `results/stats_results.json`: Statistical model outputs

## Troubleshooting

### No Data Found

If the pipeline aborts with "No Data", it means no raw count matrices were found for the specified accessions. Check network connectivity and GEO availability.

### Memory Issues

If you encounter memory errors, reduce the number of cores or process datasets individually. The pipeline automatically samples large datasets to stay within memory limits.

### Dependency Errors

Ensure you are using the correct Python version (3.9+) and that all dependencies from `environment.yml` are installed.

## Next Steps

- Read the full documentation in `README.md`
- Review the statistical methodology in `research.md` (once generated)
- Customize parameters in `code/config.py`
- Extend the pipeline with additional embedding methods or metrics

## Support

For issues or questions, please open an issue in the project repository.