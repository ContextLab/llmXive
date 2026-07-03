# Quickstart: Identifying Predictive Biomarkers of Chemotherapy Response

## Prerequisites

- **Python**: 3.11+
- **R**: 4.3+ (with `DESeq2`, `edgeR`, `sva`, `GEOquery`, `TCGAbiolinks` packages)
- **Conda**: Recommended for environment management.
- **Hardware**: CPU-only (a small number of cores, 7GB RAM). No GPU required.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone <repo-url>
   cd projects/PROJ-135-identifying-predictive-biomarkers-of-che
   ```

2. **Create Conda Environment**:
   ```bash
   conda create -n chemo-biomarker python=3.11 r-base=4.3
   conda activate chemo-biomarker
   ```

3. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   # requirements.txt includes: pandas, numpy, scikit-learn, rpy2, statsmodels, biopython, requests, scipy
   ```

4. **Install R Dependencies** (via `renv` or `conda-forge`):
   ```r
   # Inside R or via conda
   if (!require("BiocManager", quietly = TRUE))
       install.packages("BiocManager")
   BiocManager::install(c("DESeq2", "edgeR", "sva", "GEOquery", "TCGAbiolinks"))
   ```

## Data Acquisition

The pipeline automatically downloads data from verified HuggingFace mirrors and runs the **Data Feasibility Gate**.

```bash
python code/data_acquisition.py
```

**Expected Output**:
- `data/raw/TCGA/*.h5` (RNA-seq counts)
- `data/raw/GEO/*.csv` (Microarray data)
- `data/checksums.json` (Artifact hashes - generated immediately)

*Note: If specific GEO IDs (GSE25055, GSE42752) are not available in the verified mirrors, the script will fallback to available GEO datasets with response labels and log a warning.*

## Preprocessing

Harmonize identifiers and normalize data using **Quantile Normalization** for cross-platform alignment.

```bash
python code/preprocessing.py
```

**Steps**:
1. Map Ensembl/Entrez to HGNC.
2. Filter low-expression genes (CPM < 1).
3. Apply DESeq2 VST (RNA-seq) and Log2 (Microarray).
4. Apply **Quantile Normalization** to align GEO and TCGA data.
5. Limit analysis to top **[deferred]** most variable genes.

**Output**:
- `data/processed/normalized_expression.parquet`
- `data/processed/metadata.json`

## Differential Expression & Meta-Analysis

Identify cross-tumor biomarkers.

```bash
python code/differential_expression.py
python code/meta_analysis.py
```

**Output**:
- `results/de_results/*.csv`
- `results/meta_analysis/gene_panel.csv`

## Model Training & Validation

Train a **Pan-Cancer** elastic-net model with **Nested CV** (feature selection inside).

```bash
python code/modeling.py
python code/validation.py
```

**Output**:
- `results/models/*.pkl`
- `results/validation/auc_metrics.csv`
- `results/summary.md`

## Verification

Run contract tests to ensure schema compliance.

```bash
pytest tests/contract/
```

## Troubleshooting

- **Memory Error**: Ensure you are not loading the full TCGA dataset. The script automatically subsets to the top **[deferred]** variable genes.
- **R Package Errors**: Ensure `rpy2` is correctly configured and R packages are installed in the active environment.
- **Data Not Found**: Check `results/summary.md` for the list of actually used datasets if the requested GEO IDs were unavailable.
- **Timeout**: If the pipeline exceeds a predefined time threshold, it will halt automatically. Consider reducing the gene limit further or increasing compute resources.