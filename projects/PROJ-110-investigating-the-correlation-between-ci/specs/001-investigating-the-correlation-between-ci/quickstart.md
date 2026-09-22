# Quickstart: Investigating Circadian Gene Expression & Metabolic Syndrome Risk

This guide walks you through running the full analysis on a fresh GitHub Actions runner (or locally) using the open METSIM muscle RNA‑seq cohort (primary) and GTEx v8 TPM matrices (exploratory).

## Prerequisites
- Python 3.11
- Internet access (to download HF and Zenodo datasets)
- 2 CPU cores, ≥ 6 GB RAM (default GH Actions free tier)

## Setup

```bash
# 1️⃣ Clone the repository
git clone https://github.com/your-org/circadian-metabolic-correlation.git
cd circadian-metabolic-correlation

# 2️⃣ Create a virtual environment and install pinned dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # pins exact versions
```

## Run the Pipeline

```bash
# Execute the end‑to‑end pipeline
python src/pipelines/run_pipeline.py \
    --seed 42 \
    --log-level INFO
```

The script performs the following ordered steps (see `plan.md` for details):

1. **Download METSIM expression (TPM) and phenotype files** – streamed from Zenodo; checksummed and validated against `dataset.schema.yaml`.  
2. **Download GTEx expression & phenotype** – streamed from HuggingFace for exploratory analyses.  
3. **Merge expression with phenotype; exclude donors with any missing ATP‑III variable or PMI > 24 h**; log exclusions.  
4. **Classify MetS status** using ATP‑III criteria (≥ 3 of 5 thresholds).  
5. **Power analyses** for logistic regression, DE, and correlation; results logged.  
6. **Differential expression (ANCOVA)** per tissue with covariate adjustment; hierarchical fallback applied when needed.  
7. **Global Benjamini‑Hochberg correction** across all gene‑tissue tests.  
8. **Gene‑trait correlation** (Spearman or Pearson) with mixed‑effects modeling and global FDR.  
9. **Fit L2‑regularized logistic regression** with 5‑fold CV; compute AUC, DeLong test, odds ratios, VIF diagnostics.  
10. **External validation** on an independent METSIM batch; compute gene‑overlap and AUC‑delta metrics.  
11. **Generate figures** (heatmaps, ROC curves, scatter plots) and summary tables.  
12. **Validate all outputs** against their schema contracts (`contracts/`). Any validation failure aborts the run.

## Expected Outputs

| Directory | Content |
|-----------|---------|
| `data/raw/` | Downloaded METSIM & GTEx parquet files (streamed; not stored permanently). |
| `data/processed/` | Cleaned expression matrix, donor phenotype table, MetS classification, DE results, correlation results, logistic model JSON, validation results. |
| `src/results/figures/` | `de_heatmap.png`, `roc_curve.png`, `gene_trait_scatter_{gene}_{trait}.png`. |
| `state/projects/PROJ-110...yaml` | Checksums, artifact hashes, timestamps (for reproducibility). |

All files are automatically validated; any schema violation aborts the run (see `contracts/`).

## CI Integration (GitHub Actions)

Create `.github/workflows/ci.yml` (included in the repository) with the following minimal workflow to satisfy T060:

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Verify CPU‑only environment
        run: |
          python -c "import torch; assert not torch.cuda.is_available(), 'GPU detected!'" 
      - name: Run pipeline
        run: python src/pipelines/run_pipeline.py --seed 42 --log-level INFO
      - name: Run tests
        run: pytest -q tests/
```

The `Verify CPU‑only environment` step asserts `torch.cuda.is_available() == False`, fulfilling the T060 requirement.

---



