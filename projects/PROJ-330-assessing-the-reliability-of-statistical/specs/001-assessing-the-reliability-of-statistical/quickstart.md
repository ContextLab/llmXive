# Quick Start Guide

This guide walks you through setting up and running the genomic significance reliability pipeline.

## 1. Environment Setup

### Python Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### R Setup

```bash
# Initialize R environment with required packages
source code/scripts/setup_env.sh
```

Ensure R 4.3+ is installed with the following packages:
- DESeq2
- edgeR
- limma

## 2. Data Preparation

The pipeline supports datasets from GEO, TCGA, and ENCODE. A manifest file (`data/manifest.json`) defines available datasets.

### Creating a Default Manifest

If no manifest exists, generate one:
```bash
python -c "from src.data_loader import create_default_manifest; create_default_manifest()"
```

### Fetching a Dataset

To download a specific dataset:
```bash
python -c "from src.data_loader import fetch_dataset; fetch_dataset('GSE12345')"
```

Replace `'GSE12345'` with a valid GEO accession or dataset ID from your manifest.

## 3. Running the Analysis

### Full Pipeline Execution

The main entry point orchestrates the entire workflow:

```bash
python code/main.py --dataset GSE12345
```

### Individual Components

#### Stability Analysis (User Story 1)

```bash
python code/main.py --analysis stability --dataset GSE12345
```

This calculates Pearson correlation of log2 fold-changes between the full dataset and stratified subsets.

#### Permutation Testing (User Story 2)

```bash
python code/main.py --analysis permutation --dataset GSE12345 --iterations 1000
```

Generates empirical null distributions using Fixed-Dispersion Wald Perturbation.

#### Cross-Dataset Benchmarking (User Story 3)

```bash
python code/scripts/generate_cross_dataset_visualization.py
```

Aggregates results from multiple datasets and generates comparative visualizations.

## 4. Output Artifacts

Results are saved to the `artifacts/` directory:

- `stability_metrics.json`: Effect size correlations and stability scores
- `pvalue_inflation.json`: Parametric vs. empirical p-value comparisons
- `bland_altman.png`: Bland-Altman plot visualization
- `cross_dataset_comparison.png`: Repository-level metric comparisons
- `state.yaml`: Artifact hashes and versioning information

## 5. Troubleshooting

### Insufficient Samples

Datasets with fewer than 20 samples are automatically skipped with a warning.

### Missing Batch Metadata

If batch metadata is unavailable, samples are randomly stratified.

### R Script Errors

Ensure R packages are installed and the `RSCRIPT_PATH` environment variable is correctly set.

### Memory Limits

Permutation tasks respect the 6-hour time limit and minimum 100 iteration requirement. Adjust `TIME_LIMIT_SECONDS` in `code/src/config.py` if needed.

## 6. Validation

Run the validation script to ensure all components are functioning:

```bash
pytest code/tests/
```

## 7. Spec Corrections Applied

- **FR-006**: Stability calculations now use ALL genes (not just significant genes) to avoid Winner's Curse.
- **FR-004**: Fixed-Dispersion Wald Perturbation is used for permutation testing to meet runtime constraints.
- **KS Test**: P-value threshold corrected to p > 0.05 (not D < 0.05) for uniform distribution verification.