# Quickstart Guide: Evaluating the Statistical Validity of Public A/B Test Summaries

**Target:** Complete audit of 30 URLs within 30 minutes on default GitHub Actions runner (2 vCPU, 7 GB RAM)

**Version:** 1.0.0 | **Last Updated:** 2026-06-27

---

## Overview

This project validates whether publicly available A/B test summaries report statistically consistent results. The pipeline:

1. Ingests URLs from a CSV file
2. Fetches and extracts A/B test metrics (p-values, effect sizes, sample sizes)
3. Reconstructs statistical tests independently
4. Flags inconsistencies exceeding defined thresholds
5. Produces audit artifacts (JSON report, CSV summary, manifest)

---

## Prerequisites

### System Requirements

- Python 3.9 or higher
- 2 GB RAM minimum (7 GB recommended)
- 2 vCPU minimum
- Internet access for URL fetching

### Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

Dependencies include: `requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy`, `statsmodels`, `tqdm`, `pyyaml`, `jsonschema`, `psutil`

---

## Quick Start (30 URLs in ≤30 Minutes)

### Step 1: Prepare Input URLs

Create or verify `input/urls.csv` exists with at least 30 URLs:

```csv
url


...
```

Each row must contain a valid URL pointing to an A/B test summary page.

### Step 2: Run the Pipeline

Execute the main audit driver:

```bash
python code/src/cli/run_audit.py --input input/urls.csv --output output/
```

The pipeline will:
- Deduplicate URLs
- Fetch HTML (with retries and timeout)
- Extract A/B test metrics
- Reconstruct statistical tests
- Validate consistency
- Generate reports

### Step 3: Verify Outputs

After completion, confirm these artifacts exist:

| File | Location | Description |
|------|----------|-------------|
| `audit_report.json` | `output/` | Full audit records with consistency flags |
| `summary_report.csv` | `output/` | Aggregated statistics |
| `manifest.json` | `output/` | SHA256 hashes of all artifacts |
| `power_analysis.json` | `output/` | Sample size analysis results |
| `resource_log.json` | `output/` | CPU/memory usage during execution |

---

## Novice-User Verification Step

**Requirement:** Complete the verification log below and save it as `data/manual_validation/novice_verification_log.csv` to confirm successful execution.

### Verification Checklist

Run through each item and mark completion:

| # | Verification Item | Status | Notes |
|---|-------------------|--------|-------|
| 1 | Python 3.9+ installed and accessible | ☐ | |
| 2 | All dependencies installed via `pip install -r requirements.txt` | ☐ | |
| 3 | `input/urls.csv` exists with ≥30 URLs | ☐ | |
| 4 | Pipeline runs without errors (exit code 0) | ☐ | |
| 5 | `output/audit_report.json` created | ☐ | |
| 6 | `output/summary_report.csv` created | ☐ | |
| 7 | `output/manifest.json` created | ☐ | |
| 8 | Execution time ≤30 minutes | ☐ | |
| 9 | RAM usage ≤2 GB (check `output/resource_log.json`) | ☐ | |
| 10 | No `ERR-###` error codes in logs | ☐ | |

### Written Confirmation Log

Create `data/manual_validation/novice_verification_log.csv` with the following structure:

```csv
verification_id,timestamp,verification_item,status,notes,verifier_name
VER-001,2026-06-27T10:00:00Z,Python version check,pass,"Python 3.10.4",user@example.com
VER-002,2026-06-27T10:00:30Z,Dependencies installed,pass,"All packages installed",user@example.com
...
```

**Required fields:**
- `verification_id`: Unique identifier (VER-001, VER-002, etc.)
- `timestamp`: ISO 8601 format timestamp
- `verification_item`: Description of what was verified
- `status`: `pass` or `fail`
- `notes`: Any relevant details
- `verifier_name`: Name or email of person completing verification

### Confirmation Script

Run this script to auto-generate the verification log:

```bash
python code/src/audit/quickstart_verification.py --output data/manual_validation/novice_verification_log.csv
```

This script will:
1. Check Python version
2. Verify dependencies
3. Confirm input file exists
4. Run a dry-run of the pipeline
5. Record all results in the CSV log

---

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ERR-001` | Missing metric in extraction | Check HTML structure; update extractor regex |
| `ERR-301` | Resource limit exceeded | Reduce batch size; check RAM usage |
| `ERR-800` | Validation thresholds not met | Review synthetic dataset; adjust thresholds |
| `ERR-950` | Constitution principle violation | Review `src/utils/constitution_checker.py` |

### Getting Help

1. Check `output/resource_log.json` for resource usage details
2. Review logs in `logs/audit.log` for error codes
3. Verify `data/provenance_log.csv` contains all URL tracking entries
4. Run `python code/src/cli/run_audit.py --help` for usage information

---

## Next Steps

After successful quickstart:

1. **Full Pipeline:** Increase URL count for production runs
2. **Manual Validation:** See `docs/annotation_protocol.md` for human annotation process
3. **CI Execution:** Review `.github/workflows/audit.yml` for automated runs
4. **Subgroup Analysis:** See `src/audit/subgroup_analysis.py` for domain/year breakdowns

---

## References

- **FR-028:** Quickstart must enable audit of 30 URLs in ≤30 minutes
- **T095b:** Quickstart Docker guide must reproduce environment via `requirements.txt`
- **T095c:** CI must verify all seven Constitution Principles (I-VII)
- **T049b:** Verify Quickstart execution runs on default GitHub Actions runner

---

*This guide satisfies Constitution Principle VII (Provenance): All verification steps are logged with timestamps and verifier identifiers.*