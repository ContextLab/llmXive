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


# … add at least 28 more …
```

## Step 2: Install Dependencies
```bash
git clone 
cd ab-test-audit
pip install -r requirements.txt
```

## Step 3: Run the Audit
```bash
python -m code.src.audit.run_audit data/input/urls.csv output/
```
The script will:
1. Curate the URL list (`data/curated_urls.csv`).  
2. Download each page and extract required fields into `ABSummary` records.  
3. Reconstruct p‑values/effect sizes.  
4. Flag inconsistencies using the absolute 0.05 p‑value rule.  
5. Perform the binomial prevalence test and sensitivity sweep.  
6. Write `output/audit_report.json`, `output/summary_report.csv`, `output/checksums.txt`, and `output/manifest.json`.

## Step 4: Verify Output
```bash
ls output/
# should show:
# audit_report.json  summary_report.csv  checksums.txt  manifest.json
```
- Open `output/summary_report.csv` in a spreadsheet to see `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `wilson_ci_lower`, `wilson_ci_upper`.  
- Confirm that `output/checksums.txt` contains SHA‑256 hashes for both output files.

## Step 5: Resource Check (automated)
The CI workflow logs `cpu_time_seconds`, `memory_peak_mb`, and total `runtime_seconds` to `output/manifest.json`. Ensure:
- `runtime_seconds` ≤ 1800 (30 min) for the quickstart run.  
- `memory_peak_mb` ≤ 2000 (2 GB).  

If any limit is exceeded, the run fails with a clear error message (SC‑028).

---===END QUICKSTART===---