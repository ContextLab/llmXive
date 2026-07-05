# Quickstart: Predicting Coral Resilience to Thermal Stress

## Prerequisites

- Python 3.11+
- PLINK 2.0 (installed and in PATH)
- Git
- 7 GB+ available RAM (GitHub Actions environment)
- 14 GB+ available disk space

## 1. Clone and Setup

```bash
git clone <repository-url>
cd projects/PROJ-333-predicting-coral-resilience-to-thermal-s
python -m venv venv
source venv/bin/activate
pip install -r code/requirements.txt
```

## 2. Data Preparation

**Important**: The automated download for NCBI BioProject PRJNA292777 may fail if the source is unreachable (as indicated in `research.md`). If the automated step fails, manually download the VCF and metadata files from NCBI and place them in `data/raw/`.

**Critical Note**: The source dataset (PRJNA292777) lacks individual-level survival labels. The pipeline expects either:
1. A metadata file with individual-level continuous thermal tolerance metrics, OR
2. A metadata file with population-level mean survival metrics.

If neither is available, the pipeline will halt with a specific error.

```bash
# Attempt automated download
python code/main.py --step download

# If download fails, manually place files:
# data/raw/prjna292777_variants.vcf
# data/raw/prjna292777_phenotypes.csv (must contain 'population_id' and 'mean_survival' OR 'sample_id' and 'survival')
```

Ensure the phenotype file contains either:
- `population_id` and `mean_survival` (for population-level analysis), OR
- `sample_id` and `survival` (for individual-level analysis, if available).

## 3. Run the Pipeline

Execute the full pipeline:

```bash
python code/main.py --full
```

This will:
1. Download/Verify data.
2. Filter variants (MAF > 0.05, missingness < 10%).
3. Run PCA for stratification.
4. Perform GWAS (Linear or Logistic regression based on phenotype type).
5. Apply FDR correction.
6. Run pathway enrichment (with null model correction).
7. Generate plots and reports.

## 4. Verify Results

Check the output directory:

```bash
ls results/
# Expected:
# - gwas_results.csv
# - manhattan_plot.png
# - qq_plot.png
# - pathway_enrichment.json
# - summary_report.md
```

### Expected Outcomes

- **Success**: `summary_report.md` lists significant SNPs and pathways.
- **Null Result**: `summary_report.md` states "No significant associations found" (valid outcome).
- **Error**: If survival labels are missing or invalid, the script halts with a clear error.

## 5. Troubleshooting

- **Memory Error**: Reduce the dataset size by sampling variants or individuals (see `code/config.py`).
- **PLINK Not Found**: Ensure PLINK 2.0 is installed and added to your system PATH.
- **Missing Data**: If the pipeline cannot find the VCF, manually download it from NCBI and place it in `data/raw/`.
- **Invalid Phenotype**: If the pipeline cannot derive a valid phenotype (individual or population), it will halt. Check `data/raw/prjna292777_phenotypes.csv` for the required columns.