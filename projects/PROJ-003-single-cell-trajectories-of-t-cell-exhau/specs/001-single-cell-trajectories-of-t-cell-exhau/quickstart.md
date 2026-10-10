# Quickstart: Single-Cell Trajectories of T-Cell Exhaustion

## Prerequisites
- Python 3.11+, R 4.3+ (Seurat v4), Git
- Linux environment with 2 CPU cores and ≥7 GB RAM (or a GitHub Actions free-tier runner)

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
```

## Data Download (Phase 1)

```bash
python code/download_data.py \
  --datasets GSE136103 GSE127465 GSE111075 GSE138852 \
  --output data/raw/
```

Supplementary-file URLs are resolved at run time from the NCBI GEO accession metadata endpoint; no URLs are hard-coded. Per-dataset failures are logged and marked `unavailable` — inspect `logs/download.log`.

## Run the Full Pipeline

```bash
python code/preprocess.py --input data/raw/ --output data/processed/       # Seurat QC (MT-gene fix)
python code/subset_tcells.py --input data/processed/ --output data/processed/
python code/velocity.py --input data/processed/ --output data/processed/   # scVelo, CPU-only
python code/forkpoint.py --input data/processed/ --output data/results/fork_points/
python code/power_analysis.py --input data/processed/ --output data/results/validation/
python code/enrichment.py --input data/results/fork_points/ --output data/results/validation/
python code/validate.py --input data/results/validation/ --output data/results/validation/
python code/report.py --input data/results/validation/ --output data/results/report/
```

Lint evidence (T001): `ruff check . && black --check .` runs in CI and its output is recorded in `logs/lint.txt`.

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/results/fork_points/<dataset>_fork_points.csv` | Ranked fork-point genes (`gene_symbol`, `branch_id`, `timing_rank`; conforms to `fork_point.schema.yaml`). |
| `data/results/validation/power_analysis.json` | Power analysis result (FR-011). |
| `data/results/validation/<dataset>_enrichment.json` | BH-corrected enrichment p-value, bootstrap CI, iteration count (conforms to `validation.schema.yaml`). |
| `data/results/report/final_report.html` | Velocity plot, divergence heatmap, gene table, enrichment statistics, cross-dataset heatmap with bootstrap CIs, runtime/memory table, associational disclaimer. |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Download script exits 1 | Accession metadata unreachable or no supplementary files | Check `logs/download.log`; re-run; the dataset is marked `unavailable` and the run continues — do NOT substitute another source. |
| QC removes zero cells | Gene symbols not loaded (T003 root cause) | Now fixed: features file is loaded and Ensembl→symbol MT map applied; if a dataset genuinely lacks MT annotation, a warning is logged. |
| scVelo fails | Missing spliced/unspliced layers or convergence | Check `logs/velocity.log`; stochastic model with bounded retries; `alignment_status: "failed"` halts only that dataset's cross-dataset validation. |
| No fork-points detected | Divergence threshold too strict | Threshold is configurable; consult `logs/forkpoint.log`. |
| Enrichment step errors | Response labels absent from metadata | The step reports the gap explicitly; validation is restricted to datasets with labels. |

---
