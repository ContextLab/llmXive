# Quickstart: Evaluating the Statistical Consistency of Public A/B Test Summaries

## Overview
Run the full audit on a small sample (≥ 30 URLs) in ≤ 30 minutes on the default GitHub Actions runner.

## Prerequisites
- Python 3.11+
- `pip`
- Git

## Step 1: Prepare Input URLs
Create `data/input/urls.csv` with a header `url` and at least 30 reachable URLs:

```csv
url
https://example.com/ab-test-1
https://example.com/ab-test-2
# … add at least 28 more …
```

## Step 2: Install Dependencies
```bash
git clone https://github.com/your-org/ab-test-audit.git
cd ab-test-audit
pip install -r requirements.txt
```

## Step 3: Run the Audit
```bash
python -m src.cli.run_audit \
  --input data/input/urls.csv \
  --output output/
```
The script will:
1. Download each URL and extract the required fields.  
2. Reconstruct p‑values/effect‑sizes.  
3. Flag inconsistencies (absolute 0.05 p‑value rule).  
4. Perform the binomial prevalence test and bias adjustment.  
5. Write `output/audit_report.json` and `output/summary_report.csv`.  

## Step 4: Verify Output
```bash
ls output/
# should show:
# audit_report.json  summary_report.csv  checksums.txt
```
- Open `output/summary_report.csv` in a spreadsheet to see `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, and the Wilson CI bounds.  
- Confirm that `output/checksums.txt` contains SHA‑256 hashes for both output files.  

## Step 5: Resource Check (automated)
The CI workflow logs `cpu_time_seconds`, `memory_peak_mb`, and total `runtime_seconds` to `output/manifest.json`. Ensure:
- `runtime_seconds` ≤ 1800 (30 min) for the quickstart run.  
- `memory_peak_mb` ≤ 2000 (2 GB).  

If any of these limits are exceeded, the run fails with a clear error message.

---
