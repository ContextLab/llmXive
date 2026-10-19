# Quickstart: Single-Cell Trajectories of T-Cell Exhaustion

Project: `projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau`

## Prerequisites

- Linux (or a GitHub Actions runner) with 2 CPU cores and >= 7 GB RAM.
- Python 3.11+ (numpy, pandas, scipy, matplotlib, scikit-learn, statsmodels,
 seaborn, pytest, PyYAML, requests are already provided by the platform).
- R 4.3+ with Seurat v4 (optional; the preprocessing wrapper falls back to a
 Scanpy-based implementation when R is unavailable).
- Git.

## Installation

```bash
git clone <repo-url>
cd projects/PROJ-003-single-cell-trajectories-of-t-cell-exhau
python -m venv venv && source venv/bin/activate
pip install -r code/requirements.txt
```

## One-time setup (layout & lint evidence)

```bash
bash code/setup_lint.sh
```

This creates the required directory layout — including `data/results/`
(with a `.gitkeep` placeholder), `data/results/fork_points/`,
`data/results/validation/`, `data/results/report/` and `logs/` — formats the
codebase, and writes the lint evidence (`ruff check.` and
`black --check.`, both required to exit 0) to `logs/lint.txt`.

## Running the full pipeline

The single entry point that orchestrates every stage
(download -> preprocess -> velocity -> fork‑point detection -> power
analysis -> enrichment -> validation -> report) is:

```bash
python -m code.run_all
```

Usage example (from a clean checkout, run from the project root):

```bash
# 1. set up layout and lint evidence
bash code/setup_lint.sh
# 2. run the complete pipeline end‑to‑end
python -m code.run_all
```

`code.run_all` reads the global random seed from `code/config.yaml`
(`seed: 42`), logs each stage to `logs/<stage>.log`, and reproduces
byte‑identical final artifacts under `data/results/`.

## Stage‑by‑stage commands

```bash
# Data download (Phase 1)
python code/download_data.py --datasets GSE136103,GSE127465,GSE111075,GSE138852

# Preprocessing / QC & normalisation (Phase 2)
python code/preprocess.py --input data/raw/ --output data/processed/

# Velocity & pseudotime (Phase 4)
python code/velocity.py --input data/processed/ --output data/processed/

# Fork‑point detection, power analysis, enrichment, validation and the
# final HTML report are invoked by `python -m code.run_all` in the same
# order as the plan (Phases 5‑8).
```

## Expected outputs

| Path | Description |
|------|-------------|
| `data/results/fork_points/<dataset>_fork_points.csv` | Ranked fork‑point genes (`gene_symbol`, `branch_id`, `timing_rank`). |
| `data/results/validation/power_analysis.json` | Power‑analysis result (FR‑011). |
| `data/results/validation/<dataset>_enrichment.json` | BH‑corrected enrichment p‑values, bootstrap CI, iteration count. |
| `data/results/report/final_report.html` | Final report with heatmaps, statistics, and the required observational disclaimer. |

## Configuration (seed pinning)

All scripts read the random seed from `code/config.yaml` (default
`seed: 42`) to guarantee reproducibility. Do not modify this file unless
you need a different seed for a controlled experiment.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ruff`/`black` not found | Linting tools not installed | `bash code/setup_lint.sh` installs them automatically |
| download_data.py exits with error | GEO endpoint temporarily unavailable | Rerun later; the script retries and logs failures to `logs/download.log` |
| scVelo fails or hangs | Missing spliced/unspliced layers | Check `logs/velocity.log`; the dataset is flagged and excluded from cross‑dataset validation |
| Report missing disclaimer | Modified `report.py` | Use the unmodified version; the FR‑009 disclaimer is inserted automatically |