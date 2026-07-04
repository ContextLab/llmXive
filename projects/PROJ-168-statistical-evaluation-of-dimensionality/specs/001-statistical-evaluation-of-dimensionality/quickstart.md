# Quickstart: Statistical Evaluation of Dimensionality Reduction Techniques on Gene Expression Data

## Prerequisites

- **Python**: 3.10+
- **Conda/Mamba**: Recommended for environment management.
- **Git**: For cloning the repository.
- **Internet Access**: To download datasets from GEO.

## Installation

1. **Clone the repository**:
 ```bash
 git clone
 cd 001-gene-regulation
 ```

2. **Create the environment**:
 ```bash
 conda env create -f environment.yml
 conda activate gene-regulation
 ```

3. **Verify dependencies**:
 ```bash
 python -c "import scanpy; import umap; import leidenalg; import statsmodels; print('All imports successful')"
 ```

## Running the Pipeline

### Full Run (Recommended)

Execute the full Snakemake workflow:

```bash
snakemake --cores 2 --use-conda
```

- **Cores**: 2 (matches GitHub Actions limit).
- **Conda**: Automatically creates isolated environments for each rule.

### Dry Run (Validation)

To check the workflow without executing:

```bash
snakemake --dry-run
```

### Resource Monitoring

The pipeline automatically logs resource usage. To view logs after execution:

```bash
cat logs/resource_usage.log
```

### Individual Steps

If you wish to run a specific step:

```bash
# Download and preprocess (with deterministic sampling)
snakemake data/processed/GSE131907_hvg.csv

# Generate embeddings
snakemake data/processed/GSE131907_umap_embedding.csv

# Run statistical model (or descriptive mode if <2 datasets)
snakemake data/results/model_summary.csv
```

## Expected Outputs

- **Data**: `data/processed/` (filtered matrices, embeddings).
- **Metrics**: `data/results/{accession}_metrics.csv`.
- **Model**: `data/results/model_summary.csv` (coefficients, p-values, F-statistics) OR `data/results/descriptive_report.md` if <2 datasets.
- **Logs**: `logs/` (download errors, QC warnings, resource usage).

## Troubleshooting

- **Memory Error**: If you encounter `MemoryError`, the pipeline automatically samples cells. If this fails, reduce `max_cells` in `code/config.py`.
- **Download Failure**: If GEO download fails, check the `logs/download_errors.log` and verify the accession ID.
- **Model Convergence**: If the LMM fails to converge, the pipeline logs a warning and attempts a simplified model (removing random effects) or reverts to Descriptive Mode.
- **Descriptive Mode**: If the pipeline runs in descriptive mode, it will generate a report instead of a model summary. This is expected if <2 verified datasets are found (e.g., only GSE131907 is available).

## Reproducibility

To ensure reproducibility:
- Always run with `--use-conda`.
- Do not modify `environment.yml` without updating the version hash in `state/`.
- Use `snakemake --rerun-incomplete` to resume interrupted runs.
- **Deterministic Sampling**: The `random_state` for cell sampling is fixed per dataset accession, ensuring identical results across runs.