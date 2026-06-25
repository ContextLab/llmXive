# Quickstart: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview

This guide enables a new user to execute the audit pipeline on a sample corpus of 30 URLs within 30 minutes on the default GitHub Actions runner.

## Prerequisites

- Python 3.11+ installed
- Git installed (for repository access)
- Internet connection (for web scraping and package installation)

## Step 1: Prepare Input URLs

Create a file `data/raw/urls.csv` with a header `url` and a collection of reachable URLs pointing to public A/B test summaries.

**Example `data/raw/urls.csv`**:
```csv
url



...
```

**Requirements**:
- One URL per line
- URLs must point to publicly accessible HTML pages
- Minimum 30 URLs for Quickstart test (FR-028)

## Step 2: Install Dependencies

Clone the repository and install Python dependencies:

```bash
git clone <repository-url>
cd projects/PROJ-492-evaluating-the-statistical-validity-of-p
pip install -r requirements.txt
```

**requirements.txt** includes:
- `requests>=2.31.0`
- `beautifulsoup4>=4.12.0`
- `pandas>=2.0.0`
- `scipy>=1.11.0`
- `statsmodels>=0.14.0`
- `pyyaml>=6.0.0`
- `pytest>=7.4.0`

## Step 3: Run the Audit Pipeline

Execute the audit pipeline with the input URLs:

```bash
python -m code.cli.run_audit --input data/raw/urls.csv --output data/output/
```

**What the pipeline does**:
1. **Deduplication**: Collapses duplicate URLs if any exist
2. **Extraction**: Extracts sample sizes, effect sizes, and p-values from each summary
3. **Inconsistency Detection**: Flags summaries with p-value difference >0.05 or effect size difference >5%
4. **Prevalence Test**: Runs binomial test against baseline 0.05 (FR-005a)
5. **Monte Carlo Validation**: Validates statistical test implementations (FR-026)
6. **Bias Assessment**: Computes domain-weighted bias-adjusted rate (FR-027)
7. **Subgroup Analysis**: Computes prevalence per domain/year with Bonferroni correction (FR-032)
8. **Result Export**: Generates JSON and CSV reports

**Expected Runtime**: ≤30 minutes for 30 URLs on default GitHub Actions runner (FR-028)

## Step 4: Check Resource Usage

The pipeline logs CPU time and memory usage. Ensure the run stays within:
- **Time**: ≤6 hours (FR-009)
- **Memory**: ≤2 GB (FR-009)
- **CPU**: ≤2 vCPUs (FR-009)

**Resource log location**: `data/output/manifest.json` (see `resource_usage` field)

## Step 5: Interpret Results

### Audit Report (JSON)

Open `data/output/audit_report.json` to see per-summary flags:

```json
[
 {
 "url": "",
 "reported_p": 0.042,
 "reconstructed_p": 0.038,
 "flag_inconsistent": false,
 "notes": "Consistent"
 },
...
]
```

### Summary Report (CSV)

Open `data/output/summary_report.csv` for aggregate statistics:

| Column | Description |
|--------|-------------|
| `total_summaries` | Total number audited |
| `inconsistent_count` | Number flagged inconsistent |
| `inconsistent_rate` | Raw inconsistency rate |
| `bias_adjusted_rate` | Domain-weighted adjusted rate |
| `wilson_ci_lower` | Lower bound of 95% CI |
| `wilson_ci_upper` | Upper bound of 95% CI |

### Additional Reports

- `data/output/bias_report.json`: Domain proportions and bias assessment
- `data/output/subgroup_report.json`: Per-domain/year prevalence with Fisher's exact test p-values
- `data/output/manifest.json`: Pipeline metadata and checksums

## Step 6: Validate Results (Optional)

### Contract Tests

Run contract tests to verify data model compliance:

```bash
pytest tests/contract/
```

### Monte Carlo Validation

Verify statistical test implementations:

```bash
python -m code.lib.monte_carlo --replicates 10000
```

**Expected**: Absolute difference between library result and Monte Carlo estimate ≤0.005 (SC-003, SC-026)

### Real-World Validation

If you have a manually annotated validation set, run:

```bash
python -m code.cli.run_audit --validation data/processed/real_world_validation_labels.csv --output data/output/
```

**Expected**: Precision ≥85%, Recall ≥75%, F1 ≥0.80 (SC-031b)

## Troubleshooting

### Parsing Errors

If you see parsing errors (ERR-###), check:
- URLs are reachable (no HTTP 404/403)
- HTML structure is parseable (not JavaScript-heavy)
- Required fields (sample sizes, p-values) are present

Parsing error rate must be ≤5% of total summaries (SC-005).

### Resource Limits

If the pipeline exceeds memory or time limits:
- Reduce input corpus size (start with 30 URLs for Quickstart)
- Check for infinite loops in extraction logic
- Verify no GPU/CUDA dependencies in requirements

### Statistical Test Failures

If Monte Carlo validation fails:
- Check SciPy/statsmodels versions match requirements.txt
- Verify random seeds are pinned (reproducibility requirement)
- Contact project maintainers if discrepancy >0.005

## CI Integration (Optional)

For automated nightly audits, add a GitHub Actions workflow:

```yaml
name: Nightly Audit
on:
 schedule:
 - cron: '0 0 * * *' # Daily at midnight UTC
jobs:
 audit:
 runs-on: ubuntu-latest
 steps:
 - uses: actions/checkout@v3
 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: '3.11'
 - name: Install dependencies
 run: pip install -r requirements.txt
 - name: Run audit
 run: python -m code.cli.run_audit --input data/raw/urls.csv --output data/output/
 - name: Upload artifacts
 uses: actions/upload-artifact@v3
 with:
 name: audit-results
 path: data/output/
```

## Support

For issues or questions:
- Check `quickstart.md` for additional documentation
- Review `research.md` for methodological details
- Consult `plan.md` for implementation architecture