# Quickstart: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

## Prerequisites

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.11+
- **System Tools**: `bwa`, `freebayes`, `plink2`, `samtools`, `dwgsim` (or similar read simulator) (via `apt` or `conda`)
- **Memory**: 7 GB RAM (minimum)
- **Disk**: 14 GB free space

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd <project-dir>
    ```

2.  **Create and activate virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies**:
    ```bash
    pip install -r code/requirements.txt
    ```

4.  **Install system dependencies** (if running locally, not CI):
    ```bash
    # Ubuntu/Debian example
    sudo apt-get update
    sudo apt-get install bwa freebayes plink samtools
    # Optional: Install a read simulator if not using pre-generated fastq
    # conda install -c bioconda dwgsim
    ```
    *Note: In GitHub Actions, these are installed via the workflow YAML.*

## Running the Pipeline

The pipeline is executed via the main driver script.

### Step 1: Data Generation / Download
The pipeline will attempt to download real data first. If that fails (due to missing sources), it generates synthetic data.

```bash
python code/01_download.py
# If download fails, this script triggers code/00_generate_synthetic_data.py
# and code/00_generate_simulated_fastq.py automatically.
```

*Output: `data/raw/synthetic_vcf.vcf`, `data/raw/phenotypes.csv`, `data/raw/simulated_reads.fastq`*

### Step 2: Alignment & Variant Calling
```bash
bash code/02_align_call.sh
```
*This step runs `bwa mem` on the simulated (or real) FASTQ and `FreeBayes` to generate the VCF. This satisfies FR-002 even with synthetic data.*

### Step 3: GWAS Analysis
```bash
bash code/03_gwas.sh
```
*Executes PLINK logistic regression with PCA covariates, Bonferroni correction, and threshold sensitivity analysis.*

### Step 4: Machine Learning Validation
```bash
python code/04_ml_validation.py
```
*Runs LASSO logistic regression, computes PRS, and calculates AUC.*

### Step 5: Annotation (Optional)
```bash
python code/05_annotation.py
```
*Attempts to map SNPs to genes via Ensembl Bees API (will fail gracefully if API is down).*

## Expected Output

- `data/processed/gwas_results.tsv`: GWAS summary statistics (with Bonferroni and FDR columns).
- `data/processed/lasso_metrics.json`: AUC, coefficients, and PRS stats.
- `data/processed/power_analysis.txt`: Power calculation results (includes calculated power value).
- `output/report.md`: Summary of findings (explicitly framed as "Pipeline Validation").

## Troubleshooting

- **Error: `ERR_SAMPLE_SIZE_INSUFFICIENT`**: The dataset contains a limited number of colonies. Add more data or adjust the synthetic generation parameters.
- **Error: `ERR_POWER_INSUFFICIENT`**: The calculated power for the target effect size is < 20%. The study is underpowered.
- **Error: `ERR_VARROA_COVARIATE_MISSING`**: A significant proportion of colonies lack Varroa mite counts. Check data quality.
- **Runtime > 6 hours**: Reduce `--n_snps` in the data generation step or increase the MAF threshold for pruning.
- **SSL Certificate Error**: The system attempted to download real data but failed SSL verification. It has fallen back to synthetic data generation.

## Verification

To verify the pipeline works correctly:

1.  Run the pipeline.
2.  Check `data/processed/power_analysis.txt` for the calculated power value.
3.  Check `data/processed/lasso_metrics.json` for an AUC value.
4.  If AUC < 0.75, the system should have flagged "low predictive power" (as per `US-3`).
5.  Verify `data/processed/gwas_results.tsv` contains the injected "signal" SNPs with `bonferroni_q` < 0.05 (if the signal strength was sufficient).
