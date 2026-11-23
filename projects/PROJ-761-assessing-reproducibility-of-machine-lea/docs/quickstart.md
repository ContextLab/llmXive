# Quick Start Guide: Reproducibility Pipeline

This guide walks you through running the full reproducibility assessment on a single example paper.

## Step 1: Setup Environment

Ensure you have Python 3.11 and install dependencies:

```bash
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

## Step 2: Prepare the Manifest

Create a `data/manifest.yaml` file. Here is an example entry:

```yaml
papers:
 - doi: ""
 dataset_name: "example_reaction_yield"
 reported_metrics:
 mae: 0.15
 r2: 0.85
 spearman_rho: 0.78
 url: ""
 supplementary_pattern: "*_supp.csv"
```

## Step 3: Ingest Data

Run the ingestion script to fetch and validate data:

```bash
python code/ingest.py
```

**Expected Output**:
- Processed data saved to `data/processed/`
- Validation logs in `artifacts/logs/`

If the dataset is missing required variables (SMILES, yield, covariates), check `artifacts/logs/failure_log.json` for details.

## Step 4: Reproduce Models

Execute the model runner to train models and compute metrics:

```bash
python code/model_runner.py
```

**Expected Output**:
- `artifacts/reports/repro_results.json` containing:
 - `mae`, `r2`, `spearman_rho` (reproduced)
 - `deviation_index` (S)
 - `max_metric_std` (from sensitivity analysis)
 - Flags for model substitution or data gaps

## Step 5: Statistical Analysis

Run the statistical module to compare results across studies:

```bash
python code/stats.py
```

**Expected Output**:
- `artifacts/reports/stat_summary.json` with t-test p-values, LME variance components, and I² heterogeneity.
- Bland-Altman plots saved to `artifacts/plots/` (e.g., `mae_bland_altman.png`).

## Step 6: Generate Guidelines

Produce the community checklist:

```bash
python code/guidelines.py
```

**Expected Output**:
- `artifacts/reports/reproducibility_checklist.md` with actionable recommendations based on identified failure modes.

## Verifying Results

After running the full pipeline, verify the following artifacts exist:

- `artifacts/reports/repro_results.json`
- `artifacts/reports/stat_summary.json`
- `artifacts/reports/reproducibility_checklist.md`
- `artifacts/plots/*.png`

## Next Steps

- Add more papers to `data/manifest.yaml` for larger-scale meta-analysis.
- Customize the tolerance delta (δ) in `code/stats.py` for stricter equivalence testing.
- Review `docs/README.md` for detailed API documentation.
