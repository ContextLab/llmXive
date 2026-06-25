# Quickstart: 001-eval-ab-test-validity

## Overview

This guide enables a new user to execute the A/B test audit pipeline on a sample corpus of 30 URLs within 30 minutes on the default GitHub Actions runner (FR-028, SC-028).

## Prerequisites

- Python 3.11+ installed locally (or use GitHub Actions runner)
- Git repository cloned to local machine
- Input file `input/urls.csv` with at least 30 URLs

## Step 1: Prepare Input URLs

Create a file `input/urls.csv` with a header `url` and one URL per line:

```csv
url
https://example-engineering-blog.com/ab-test-1
https://another-company.com/experiment-results
...
```

**Minimum**: 30 URLs for quickstart; ≥300 URLs for full audit (FR-025).

## Step 2: Install Dependencies

```bash
cd projects/PROJ-492-evaluating-the-statistical-validity-of-p
pip install -r requirements.txt
```

**requirements.txt** (CPU-only, GitHub Actions compatible):

```txt
requests==2.31.0
beautifulsoup4==4.12.2
pandas==2.1.0
scipy==1.11.3
statsmodels==0.14.0
pyyaml==6.0.1
pytest==7.4.2
```

## Step 3: Run the Audit Pipeline

```bash
python -m code.cli.main --input input/urls.csv --output output/
```

**What happens**:

1. **Extraction**: Fetch each URL, extract sample sizes, effect sizes, p-values (FR-001, FR-002)
2. **Reconstruction**: Compute expected p-values using two-proportion z-test or Welch's t-test (FR-003)
3. **Inconsistency Detection**: Flag entries where reported vs. reconstructed metrics differ >threshold (FR-004)
4. **Domain Bias Assessment**: Compute domain proportions and bias-adjusted rate (FR-027)
5. **Subgroup Analysis**: Per-domain/year prevalence with Fisher's exact test (FR-032)
6. **Export**: Generate `audit_report.json` and `summary_report.csv` (FR-024)

**Expected Runtime**: ~15-30 minutes for 30 URLs (depends on network latency)

## Step 4: Verify Outputs

Check that output files exist:

```bash
ls -la output/
# Expected files:
# - audit_report.json
# - summary_report.csv
# - bias_report.json
# - subgroup_report.json
# - manifest.json
# - checksums.txt
```

**Inspect Results**:

```bash
cat output/summary_report.csv
# Columns: total_summaries, inconsistent_count, inconsistent_rate, bias_adjusted_rate, wilson_ci_lower, wilson_ci_upper
```

```bash
cat output/audit_report.json | python -m json.tool | head -50
# Per-summary flags and computed metrics
```

## Step 5: Run Tests (Optional)

```bash
pytest tests/ -v
```

**Contract Tests**: Validates schemas for `extracted_summary`, `audit_record`, `manifest` (FR-026).

**Monte Carlo Validation**: Verifies statistical test implementations with [deferred] replicates (FR-026, SC-003, SC-026).

## Step 6: Run on GitHub Actions

Create `.github/workflows/audit.yml`:

```yaml
name: A/B Test Audit
on:
  schedule:
    - cron: "0 0 * * *"  # Daily at midnight UTC
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run audit
        run: python -m code.cli.main --input input/urls.csv --output output/
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: audit-results
          path: output/
```

**Expected Runtime**: ≤6 hours (SC-008, FR-009)

## Step 7: Validate Precision/Recall (FR-031, SC-030)

```bash
# Generate synthetic dataset (sufficient records)
python -m code.services.synthetic --output data/synthetic/synthetic_audits.csv --n 10000

# Evaluate inconsistency detection
python -m code.services.validator --input data/synthetic/synthetic_audits.csv --output output/validation_results.json

# Expected: precision ≥90%, recall ≥80%, F1 ≥0.85
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| URL timeout | Increase timeout in extractor.py (default: 30s) |
| Parsing error | Check HTML structure; update extraction rules |
| Memory error | Reduce batch size; stream data instead of loading all at once |
| Monte Carlo validation fails | Check scipy version; ensure [deferred] replicates (FR-026) |
| Domain exceeds [deferred] | Subsample that domain; verify bias-adjusted rate (FR-027) |

## Expected Output Files

| File | Description |
|------|-------------|
| `output/audit_report.json` | Per-summary audit results (FR-024) |
| `output/summary_report.csv` | Aggregate prevalence statistics (FR-024) |
| `output/bias_report.json` | Domain proportions and bias-adjusted rate (FR-027) |
| `output/subgroup_report.json` | Per-domain/year prevalence with Fisher's test (FR-032) |
| `output/manifest.json` | Run metadata, checksums (SC-013) |
| `output/checksums.txt` | SHA256 checksums for all output files (T076) |
