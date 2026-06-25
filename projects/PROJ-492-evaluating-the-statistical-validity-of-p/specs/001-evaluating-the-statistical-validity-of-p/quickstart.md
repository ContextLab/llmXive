# Quickstart: Evaluating the Statistical Validity of Public A/B Test Summaries

**Goal**: Run the audit pipeline on a sample corpus of 30 URLs within 30 minutes on the default GitHub Actions runner (Ubuntu-latest, Python 3.11+).

## Prerequisites

- Python 3.11+ installed
- Git installed
- Access to a GitHub repository (for CI) or local execution
- Sample corpus of 30 public A/B test summary URLs (one per line)

## Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/ab-test-audit.git
cd ab-test-audit
```

## Step 2: Create Input File

Create a file `input/urls.csv` with a header `url` and 30 URLs (one per line):

```csv
url
https://example.com/ab-test-summary-1
https://example.com/ab-test-summary-2
...
```

**Tip**: For testing, use known public A/B test summaries from engineering blogs (e.g., Optimizely, Airbnb, Netflix) or create synthetic summaries with known ground-truth values.

## Step 3: Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**requirements.txt** (pinned versions for reproducibility):
```
scipy>=1.11.0
pandas>=2.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
pyyaml>=6.0.0
pytest>=7.4.0
statsmodels>=0.14.0
```

## Step 4: Run the Audit Pipeline

```bash
python code/cli/main.py --input input/urls.csv --output output/
```

**Expected runtime**: 15–30 minutes for 30 URLs (includes HTML fetch, extraction, statistical reconstruction, inconsistency detection, and report generation).

**Output files**:
- `output/audit_report.json` - Per-summary audit results
- `output/summary_report.csv` - Aggregate inconsistency rates
- `output/bias_report.json` - Domain proportions and bias-adjusted rate
- `output/subgroup_report.json` - Subgroup prevalence and Fisher's exact test results
- `output/manifest.json` - Pipeline execution metadata

## Step 5: Verify Results

### Check Audit Report

```bash
python -c "import json; data = json.load(open('output/audit_report.json')); print(f\"Processed: {len(data)} summaries\"); print(f\"Inconsistent: {sum(1 for r in data if r['flag_inconsistent'])}\")"
```

### Check Summary Report

```bash
cat output/summary_report.csv
```

Expected columns: `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`.

### Check Manifest

```bash
python -c "import json; data = json.load(open('output/manifest.json')); print(f\"Status: {data['status']}\"); print(f\"Duration: {data['end_time']} - {data['start_time']}\")"
```

## Step 6: Run Contract Tests

```bash
pytest tests/contract/ -v
```

Expected: All contract tests pass (schema validation for `extracted_summary`, `audit_record`, `manifest`).

## Step 7: Run Unit Tests

```bash
pytest tests/unit/ -v
```

Expected: All statistical test implementations validated (Monte Carlo difference ≤0.01).

## Step 8: Run Integration Tests

```bash
pytest tests/integration/ -v
```

Expected: Full pipeline executes successfully on sample corpus.

## Expected Runtime & Resource Usage

| Metric | Expected Value | Limit |
|--------|----------------|-------|
| Runtime (30 URLs) | 15–30 minutes | ≤6 hours |
| Memory peak | ≤500 MB | ≤2 GB |
| CPU usage | ≤1 vCPU | ≤2 vCPUs |
| Disk output | <10 MB | ≤14 GB |

## Troubleshooting

### HTML Extraction Fails

**Symptom**: `extraction_status` = "failed" in audit report.

**Solution**: Check `output/error_log.json` for error codes (ERR-###). Common causes:
- URL unreachable (ERR-001): Verify URL is public and accessible.
- HTML parsing error (ERR-002): Check if page structure changed; update extraction regex.
- Missing field (ERR-003): Summary may not contain required metrics; entry flagged as "missing metric".

### Statistical Test Fails

**Symptom**: `reconstructed_p` = null in audit record.

**Solution**: Check `notes` field for explanation. Common causes:
- Insufficient sample size for z-test: Use Fisher's exact test fallback (cell count ≤5).
- Continuous outcome without standard deviation: Cannot reconstruct t-test; entry flagged as "missing metric".

### CI Job Exceeds Time Limit

**Symptom**: GitHub Actions job times out after 6 hours.

**Solution**:
- Reduce corpus size (e.g., 30 URLs for CI, 300+ for production).
- Implement caching for repeated URL fetches.
- Increase timeout in workflow file (if allowed).

## Next Steps

1. **Scale to Production Corpus**: Increase `input/urls.csv` to 300+ URLs for statistically significant prevalence estimate (FR-025).
2. **Customize Extraction**: Modify `code/extraction/html_parser.py` to support additional source domains.
3. **Extend Analysis**: Add subgroup dimensions (e.g., industry, company size) to `code/analysis/subgroup_analyzer.py`.
4. **Deploy as Service**: Wrap CLI in FastAPI for programmatic access (future enhancement).
