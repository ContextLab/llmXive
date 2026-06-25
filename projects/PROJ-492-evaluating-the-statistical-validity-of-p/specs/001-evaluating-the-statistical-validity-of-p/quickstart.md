# Quickstart: Evaluating the Statistical Validity of Public A/B Test Summaries

## Prerequisites
- **Docker** (recommended) or a local Python 3.11 environment.  
- GitHub account with permission to trigger the repository workflow.  

## Step‑by‑Step

### 1. Clone the Repository
```bash
git clone https://github.com/yourorg/ab-test-audit.git
cd ab-test-audit
```

### 2. Build the Docker Image (optional but ensures reproducibility)
```bash
docker build -t ab-audit:latest .
```

### 3. Prepare the Input URL List
Create `input/urls.csv` with a header `url` and one URL per line, e.g.:

```csv
url
https://example.com/blog/2023/ab-test-1
https://another.com/engineering/ab-test-42
...
```

> **Tip:** The file can be as large as you like; the pipeline will process it in parallel while respecting the 2‑CPU limit of the GitHub Actions runner. The realistic target is up to **[deferred]** URLs to stay within the 6‑hour CI window (see performance notes in `plan.md`).

### 4. Run the Audit Pipeline

#### Using Docker (recommended)
```bash
docker run --rm \
  -v "$(pwd)/input:/app/input" \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/data:/app/data" \
  ab-audit:latest \
  ./run_audit.sh input/urls.csv output/
```

#### Using Local Python (if you prefer)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./run_audit.sh input/urls.csv output/
```

The script will:
1. Download each URL (checksums stored under `data/raw/`).  
2. Extract required metrics into `data/processed/extracted.csv`.  
3. Reconstruct p‑values/effect sizes.  
4. Flag inconsistencies per **FR‑004**.  
5. Perform the binomial prevalence test (**FR‑005a**) with post‑hoc power assessment.  
6. Conduct a sensitivity analysis on the FR‑004 thresholds.  
7. Write `output/audit_report.json` (the **Single Source of Truth** for per‑summary results) and `output/summary_report.csv` (aggregate summary).

### 5. Inspect the Results
- **Detailed per‑summary audit**: `output/audit_report.json` – each entry follows `audit_record.schema.yaml`.  
- **Aggregate summary**: `output/summary_report.csv` – columns:  
  `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `wilson_ci_lower`, `wilson_ci_upper`.  

Open the CSV in any spreadsheet program or view it directly:

```bash
head output/summary_report.csv
```

### 6. Verify Compliance (Automated Tests)
Run the contract‑based test suite to ensure outputs match schemas and success criteria:

```bash
pytest -q
```

All tests should pass, confirming:
- Extraction accuracy ≥ 95 % on the **≥ 100**‑item validation set (`SC‑001`).  
- Inconsistency‑detection precision ≥ 90 % (`SC‑014`).  
- Parsing‑error rate ≤ 5 % (`SC‑005`).  
- CI‑compatible runtime ≤ 6 h (`SC‑008`).  

### 7. CI Execution (Optional)
The repository includes a GitHub Actions workflow (`.github/workflows/audit.yml`). Push a branch with an updated `input/urls.csv` and the workflow will automatically run the full pipeline, producing the same artifacts under the `artifact/` section of the workflow run.

---

