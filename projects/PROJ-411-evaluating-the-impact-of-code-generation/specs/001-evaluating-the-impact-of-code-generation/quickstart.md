# Quickstart: Evaluating the Impact of Code Generation on Code Review Burden

Reproduce the full analysis on a fresh GitHub Actions runner (or locally).

## Prerequisites

- Python 3.11, internet access (HuggingFace downloads), `git`.

## Steps

```bash
git clone <repo-url> && cd <repo>
python -m venv .venv && source .venv/bin/activate
pip install -r code/requirements.txt

# 0. Download + checksum + per-dataset schema mapping (validates against
#    contracts/raw_prs.schema.yaml)
python code/download_data.py

# 1. Provenance classification within the primary population
#    (FR-002, FR-008, FR-010, FR-018) -> classified_prs.csv (intermediate)
python code/classify_provenance.py \
    --input data/raw/prs-v2-sample.parquet \
    --output data/processed/classified_prs.csv

# 2. Metrics (writes the SSoT processed_prs.csv; FR-020)
python code/compute_metrics.py \
    --input data/processed/classified_prs.csv \
    --output data/processed/processed_prs.csv

# 3. Outlier removal + filter variants (sole writer of all filtered files:
#    filtered_prs.csv at IQR 1.5, plus IQR 1.0/2.0 and comment-relaxed variants)
python code/outlier_filter.py --iqr 1.5

# 4. Statistical analysis (power check, pre-specified Mann-Whitney U primary
#    + Welch companion, effect sizes, Bonferroni, mixed-effects model with
#    temporal covariate, chi-square) -> stats_summary.csv
python code/statistical_analysis.py \
    --input data/processed/filtered_prs.csv \
    --results data/results/stats_summary.csv

# 5. Validation: emits a labeling worksheet; computes Cohen's kappa and the
#    pre-planned misclassification response if
#    data/processed/manual_labels.csv (human labels) is committed
python code/validation.py \
    --input data/processed/filtered_prs.csv \
    --report data/results/validation_report.md

# 6. Sensitivity sweep (IQR 1.0/1.5/2.0, comment filter >= 0,
#    source-stratified descriptive comparison)
python code/sensitivity.py --mode full

# 7. Final report (tables, figures, null-result and limitation statements)
python code/report.py \
    --stats data/results/stats_summary.csv \
    --validation data/results/validation_report.md \
    --output report.md
```

## Expected outputs

- `data/processed/processed_prs.csv` — SSoT, written solely by `compute_metrics.py`, conforms to `contracts/processed_prs.schema.yaml`.
- `data/processed/filtered_prs.csv` (plus `filtered_prs_iqrStandard.csv`, `filtered_prs_iqr2.0.csv`, `filtered_prs_relaxed.csv`) — written solely by `outlier_filter.py`.
- `data/results/stats_summary.csv` — conforms to `contracts/statistical_results.schema.yaml`.
- `data/results/sensitivity_report.csv` — IQR sweep, comment-filter sensitivity, and source-stratified results with robustness flags.
- `data/results/validation_report.md` — Cohen's κ and misclassification response, or an explicit pending-validation statement.
- `report.md` + `data/results/figures/` — final tables, figures, null-result statements, and limitations (power, selection bias, misclassification attenuation, missing covariates, temporal confounding, dataset origin, observational framing).