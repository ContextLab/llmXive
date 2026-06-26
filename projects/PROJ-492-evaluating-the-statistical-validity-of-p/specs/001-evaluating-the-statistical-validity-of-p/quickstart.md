# Quickstart: Evaluating the Statistical Validity of Public A/B Test Summaries

## Overview

This guide enables a new user to execute the audit pipeline on a sample corpus of 30 URLs within 30 minutes on the default GitHub Actions runner (per FR-028, SC-028).

## Prerequisites

- Python 3.11+ installed
- Git installed
- (Optional) Docker 20.10+ for containerized execution

## Step 1: Clone the Repository

```bash
git clone
cd ab-test-audit
```

## Step 2: Prepare Input URLs

Create a file `input/urls.csv` with a header `url` and one URL per line:

```csv
url


...
```

**Note**: For full audit, ensure N≥300 URLs (per FR-025). For quickstart test, 30 URLs is sufficient.

## Step 3: Install Dependencies (Local Execution)

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 4: Run the Audit Pipeline

### Option A: Local Execution

```bash
python -m code.main input/urls.csv output/
```

### Option B: Docker Execution (Optional)

```bash
docker build -t ab-audit:latest.
docker run --rm \
 -v $(pwd)/input:/app/input \
 -v $(pwd)/output:/app/output \
 ab-audit:latest./run_audit.sh input/urls.csv output/
```

## Step 5: Monitor Execution

The pipeline performs:
1. URL deduplication
2. HTML extraction (sample sizes, effect sizes, p-values)
3. Statistical reconstruction (z-test, Fisher's, Welch's t-test)
4. Inconsistency detection (|Δp|>0.05 threshold)
5. Prevalence estimation (binomial test, Wilson CI)
6. Bias assessment (domain proportions)
7. Subgroup analysis (Fisher's exact test with Bonferroni)
8. Report generation

**Expected runtime**: 30 minutes for 30 URLs; ~2-3 hours for N=300 corpus.

## Step 6: Verify Output Files

Check that the following files exist in `output/`:

| File | Description |
|------|-------------|
| `audit_report.json` | Per-summary audit results (FR-024) |
| `summary_report.csv` | Aggregate statistics with Wilson CI (FR-024) |
| `bias_report.json` | Domain proportions and bias-adjusted rate (FR-027) |
| `subgroup_report.json` | Per-domain/year prevalence (FR-032) |
| `monte_carlo_validation_report.json` | Statistical test validation (FR-026) |
| `checksums.txt` | File checksums (T076) |
| `manifest.json` | Run manifest with checksums (T077) |

## Step 7: Interpret Results

### Summary Report (summary_report.csv)

```csv
total_summaries,inconsistent_count,inconsistent_rate,bias_adjusted_rate,wilson_ci_lower,wilson_ci_upper
30,5,0.167,0.160,0.072,0.328
```

- `inconsistent_rate`: Proportion of summaries flagged as inconsistent.
- `bias_adjusted_rate`: Domain-weighted adjusted rate (if domain bias detected).
- `wilson_ci_lower`, `wilson_ci_upper`: 95% Wilson confidence interval.

### Audit Report (audit_report.json)

Each record includes:
- `url`: Source URL
- `flag_inconsistent`: True if inconsistent (|Δp|>0.05 or other criteria)
- `diff_abs_p`: Absolute p-value difference
- `notes`: Error codes (ERR-###) if applicable

## Step 8: CI Execution (GitHub Actions)

### Trigger Workflow

```bash
# Push to trigger CI
git add.
git commit -m "Run audit pipeline"
git push origin main
```

### View Results

Navigate to GitHub Actions tab → Select workflow run → View artifacts.

**Expected**: Job completes within 6 hours, exits with status 0, produces `manifest.json` (SC-013).

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Extraction fails (ERR-001) | Check URL accessibility; verify HTML structure |
| Memory exceeds 2GB | Reduce corpus size; process in batches |
| Runtime exceeds 6 hours | Reduce corpus size; optimize extraction parallelization |
| Parsing error rate >5% | Review ERR-### logs; improve extraction robustness |
| Domain dominance (>30%) | Pipeline will subsample; check `bias_report.json` |

## Validation Targets

| Validation | Target | Status Check |
|------------|--------|--------------|
| Extraction accuracy (real-world) | Precision≥85%, Recall≥75% (F1≥0.80) | `output/real_world_validation_report.json` |
| Inconsistency detection (synthetic) | Precision≥90%, Recall≥80% (F1≥0.85) | `output/synthetic_validation_report.json` |
| Monte Carlo validation | |Δp|≤0.005 for all tests | `output/monte_carlo_validation_report.json` |
| CI manifest creation | ≥99% success rate | GitHub Actions logs |

## Support

For issues, file an issue at the repository with:
- Error message (including ERR-### codes)
- Input URL(s) that failed
- Environment details (Python version, OS)
