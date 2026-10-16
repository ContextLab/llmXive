# Quickstart: The Impact of Visual Motion on Perceived Agency in Virtual Interactions

## Prerequisites
- Python 3.11 or newer
- `git` and internet access (to download datasets)
- Virtual environment tool (`venv` or `conda`)

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd projects/PROJ-531-the-impact-of-visual-motion-on-perceived

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate

# 3. Install pinned dependencies
pip install -r code/requirements.txt
```

## Running the Full Pipeline

The pipeline is orchestrated by a single Bash wrapper that respects task dependencies:

```bash
bash run_pipeline.sh
```

**Note:** This project runs in **synthetic‑only mode**. See the [Scope and Ethics Declaration](docs/scope.md) for details on why no real human data are used.

## Verifying Success Criteria

| Success Criterion | Artifact | How to Verify |
|-------------------|----------|---------------|
| SC‑001 (≥ 100 complete observations) | `modeling_config.json` → `sc001_pass` | `cat data/processed/modeling_config.json \| jq.sc001_pass` |
| SC‑002 (5‑fold CV metrics) | `model_metrics.json` → `cross_validation_metrics` | Contains `r2_mean`, `r2_std`, `rmse_mean`. |
| SC‑003 (Multiple‑comparison control) | `model_metrics.json` → `statistical_significance` (corrected) | Verify corrected p‑values ≤ 0.05 only after Bonferroni/BH. |
| SC‑004 (VIF < 5) | `vif_report.json` → `vif_pass` | `true`. |
| SC‑005 (Visualization clarity) | `visualization_report.json` → `average_rating` | Must be ≥ 4.0. |
| FR‑013 (Instrument validity) | `download_status.json` → `instrument_valid` | `true` for real data; synthetic instrument always true. |
| FR‑014 (Power analysis) | `modeling_config.json` → `power_pass` | `true`. |

If any check fails, the pipeline logs a clear warning; the user can adjust parameters (e.g., increase synthetic N) and re‑run.

## Troubleshooting

- **“Insufficient sample size”** – Check `modeling_config.json` for `sc001_pass`. If `false`, consider increasing synthetic N or locating a larger real dataset.
- **“Collinearity detected (VIF ≥ 5)”** – The OLS model will drop offending predictors; review `vif_report.json` for details.
- **“Instrument invalid”** – The DOI lookup failed or citation count < 10 **or** Cronbach's α < 0.70; the pipeline will fall back to synthetic data.
- **“Visualization rating below threshold”** – Adjust `visualization.py` parameters (e.g., increase figure DPI, add axis labels) and re‑run.

All logs are stored under `logs/` for reproducibility.

## Documentation

- Project scope and ethics: [docs/scope.md](docs/scope.md)
