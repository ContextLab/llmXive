# Quickstart: Evaluating the Impact of Code Generation on Code Review Burden

Reproduce the full analysis on a fresh GitHub Actions runner (or locally).

## Prerequisites
- Python 3.11
- Internet access (to query the GitHub REST API and download auxiliary datasets)
- Git

## Steps

```bash
# Clone the repository
git clone <repo-url> && cd <repo>

# Create a virtualenv
python -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r code/requirements.txt

# 0. Download raw PR data from GitHub (respects rate limits) and verify checksums
python code/download_data.py --repo-list code/repo_list.txt --output data/raw/

# 1. Classify provenance (FR‑002, FR‑008, FR‑010 modified handling)
python code/classify_provenance.py \
    --input data/raw/combined_prs.json \
    --output data/processed/classified_prs.csv

# 2. Compute metrics and create the SSoT (FR‑020)
python code/compute_metrics.py \
    --input data/processed/classified_prs.csv \
    --output data/processed/processed_prs.csv

# 3. Outlier removal & filter variants (FR‑003, FR‑006, FR‑014)
python code/outlier_filter.py \
    --input data/processed/processed_prs.csv \
    --iqr 1.5   # produces filtered_prs_iqr1.5.csv, plus 1.0/2.0 and relaxed variants

# 4. Statistical analysis (power, normality, tests, mixed‑effects, Bonferroni)
python code/statistical_analysis.py \
    --input data/processed/filtered_prs_iqr1.5.csv \
    --results data/results/stats_summary.csv

# 5. Validation (Cohen's κ) – independent sample from auxiliary known‑LLM datasets
python code/validation.py \
    --aux-dataset prs-eth/AGBD \
    --output data/results/validation_report.md

# 6. Sensitivity analyses (IQR sweep, comment‑filter, source‑stratified, selection‑bias)
python code/sensitivity.py --mode full

# 7. Assemble final report
python code/report.py \
    --stats data/results/stats_summary.csv \
    --validation data/results/validation_report.md \
    --output report.md
```

## Expected Outputs

| Path | Description |
|------|-------------|
| `data/processed/processed_prs.csv` | Single Source of Truth (SSoT); conforms to `contracts/processed_prs.schema.yaml`. |
| `data/processed/filtered_prs_iqr1.5.csv` (and variants) | Filtered datasets for primary analysis and sensitivity checks. |
| `data/results/stats_summary.csv` | Statistical test results; conforms to `contracts/statistical_results.schema.yaml`. |
| `data/results/sensitivity_report.csv` | IQR & comment‑filter sweep results, robustness flags. |
| `data/results/validation_report.md` | Cohen’s κ from independent auxiliary dataset, misclassification response. |
| `data/results/group_source_contingency.csv` | Contingency table of provenance × source (required for FR‑018). |
| `report.md` + `data/results/figures/` | Final manuscript‑ready report with tables, box‑plots, and limitation statements. |

If **no LLM‑generated PRs** are detected after classification, step 4 will emit a descriptive summary instead of hypothesis‑test rows, and the final report will contain a clear limitation statement. All files are written under the `data/` hierarchy as required by the plan and contracts.

---



```bash
# Recorded command for reproducibility
python code/download_data.py --repo-list code/repo_list.txt --output data/raw/
```

```bash
# Recorded command for reproducibility
python code/download_data.py --repo-list code/repo_list.txt --output data/raw/
```

```bash
# Recorded command for reproducibility
python code/download_data.py --repo-list code/repo_list.txt --output data/raw/
```
