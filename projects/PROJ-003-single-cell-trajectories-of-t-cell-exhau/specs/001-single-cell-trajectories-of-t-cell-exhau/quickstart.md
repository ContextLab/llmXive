# Quickstart: Single-Cell Trajectories of T-Cell Exhaustion

## Prerequisites
- Linux (or GitHub Actions runner) with **2 CPU cores**, **≥7 GB RAM**.  
- Python 3.11+, R 4.3+ (Seurat v4).  
- Git.

## Installation
```bash
git clone <repo-url>
cd projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
```

## Lint Check (Phase 0)
```bash
ruff check . && black --check . | tee logs/lint.txt
```
The log file `logs/lint.txt` is used as evidence for **SC‑001**.

## Step‑by‑Step Pipeline

### 0. Layout & Directory Setup
```bash
# Ensure result directories exist
mkdir -p data/results/fork_points data/results/validation data/results/report
```

### 1. Data Download (Phase 1)
```bash
python code/download_data.py \
  --datasets GSE136103 GSE127465 GSE111075 GSE138852 \
  --output data/raw/
```
- URLs are resolved at run time from the NCBI GEO accession metadata endpoint.  
- Check `logs/download.log` for any `unavailable` datasets.

### 2. Preprocessing (Phase 2)
```bash
python code/preprocess.py --input data/raw/ --output data/processed/
```
- Loads gene symbols, annotates mitochondrial genes using a **curated list** that includes Ensembl IDs **and** symbols prefixed with `MT-`, filters cells >20 % mt reads, log‑normalizes, selects 2 000 HVGs.

### 3. T‑Cell Subsetting (Phase 3)
```bash
python code/subset_tcells.py --input data/processed/ --output data/processed/
```

### 4. Batch‑Effect Correction (Phase 4b)
```bash
python code/batch_correct.py --input data/processed/ --output data/processed/
```
- Applies Harmony integration (CPU) across all datasets to align batch effects before velocity estimation.

### 5. Velocity & Pseudotime (Phase 4)
```bash
python code/velocity.py --input data/processed/ --output data/processed/
```
- Runs scVelo on CPU; runtime and memory are logged (`logs/velocity.log`).

### 6. Fork‑Point Detection & Ranking (Phase 5)
```bash
python code/forkpoint.py --input data/processed/ --output data/results/fork_points/
```

### 7. Power Analysis (Phase 6)
```bash
python code/power_analysis.py --input data/processed/ --output data/results/validation/
```

### 8. Enrichment & Validation (Phase 7)
```bash
python code/enrichment.py --input data/results/fork_points/ --output data/results/validation/
python code/validate.py   --input data/results/validation/ --output data/results/validation/
```

### 9. Reporting (Phase 8)
```bash
python code/report.py --input data/results/validation/ --output data/results/report/
```
The final HTML report appears at `data/results/report/final_report.html`.

## Expected Outputs
| Path | Description |
|------|-------------|
| `data/results/fork_points/<dataset>_fork_points.csv` | Ranked fork‑point genes (`gene_symbol`, `branch_id`, `timing_rank`). |
| `data/results/validation/power_analysis.json` | Power‑analysis result (FR‑011). |
| `data/results/validation/<dataset>_enrichment.json` | BH‑corrected enrichment p‑value, bootstrap CI, iteration count. |
| `data/results/report/final_report.html` | Velocity plots, divergence heatmap, gene table, enrichment stats, runtime/memory table, and the required observational disclaimer. |

## Configuration (Seed Pinning)
All scripts read the random seed from `code/config.yaml` (default `seed: 42`). This ensures reproducibility (Principle I). **Do not modify this file** unless you need a different seed for a controlled experiment.

## Optional GPU Escape Hatch
If the CI environment detects a free Kaggle GPU, the permutation step in `forkpoint.py` will automatically run on CUDA (`device="cuda"`). No code changes are required.

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `download_data.py` exits with error | GEO accession metadata endpoint temporarily unavailable | Rerun later; the script retries up to 5 times and logs failures. |
| QC filter removes zero cells | Mitochondrial gene list missing a gene format | The script now uses a curated list covering Ensembl IDs **and** `MT-` prefixes; ensure the raw `genes.tsv` file is present. |
| scVelo fails or hangs | Missing spliced/unspliced layers or convergence issues | Check `logs/velocity.log`; the script retries with higher regularization; if still failing, the dataset will be flagged `alignment_status: "failed"` and excluded from cross‑dataset validation. |
| No enrichment results | `therapy_response` column was mistakenly used; now the external signature is used exclusively. | Rerun the enrichment step; it will produce results consistent with the cited literature. |
| Report missing disclaimer | Custom modification of `report.py` | The provided script automatically inserts the FR‑009 disclaimer; ensure you are using the unmodified version. |

---



