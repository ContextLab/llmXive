# Quickstart Guide: Statistical Validity of Public A/B Tests

This guide walks you through running the full audit pipeline on a small set of **30 URLs** within **30 minutes** on the default GitHub Actions runner (2 vCPU, 7 GB RAM), as required by FR-028.

## Prerequisites

- Python 3.9+ installed
- `pip` available
- Internet connection (to fetch URLs)
- At least 2 GB free disk space

## Step 1: Clone and Setup

```bash
git clone <repository-url>
cd PROJ-492-evaluating-the-statistical-validity-of-p
pip install -r requirements.txt
```

## Step 2: Prepare Input Data

Create a file `input/urls.csv` containing exactly 30 public A/B test summary URLs.
Example format:

```csv
url


...
```

> **Note:** Ensure the URLs are accessible and contain extractable A/B test metrics (p-values, effect sizes, sample sizes).

## Step 3: Run the Pipeline

Execute the audit driver script:

```bash
python -m code.src.cli.run_audit --input input/urls.csv
```

This command:
1. Ingests and deduplicates URLs
2. Fetches HTML with retries
3. Extracts A/B test summaries
4. Reconstructs statistical tests
5. Validates inconsistencies
6. Computes prevalence and bias-adjusted rates
7. Generates `output/audit_report.json`, `output/summary_report.csv`, and `output/manifest.json`

## Step 4: Verify Execution Time

The pipeline must complete within **30 minutes** for 30 URLs.
Check `output/resource_log.json` for wall-clock time and resource usage:

```bash
cat output/resource_log.json
```

Verify that:
- `wall_clock_seconds` ≤ 1800
- `peak_memory_mb` ≤ 2048
- `cpu_vcpu` ≤ 2

## Step 5: Novice-User Verification Step

To confirm the guide is usable by a novice, perform the following verification:

1. Run the pipeline as described above.
2. Ensure all output files exist:
 - `output/audit_report.json`
 - `output/summary_report.csv`
 - `output/manifest.json`
 - `output/resource_log.json`
3. Confirm no errors are logged (check `logs/audit.log` for `ERR-###` codes).
4. Write a **confirmation log** file `docs/verification_log.txt` with the following content:

```text
Verification Date: <YYYY-MM-DD HH:MM:SS>
User: <your-name>
Status: SUCCESS | FAILURE
Notes: <brief description of execution, any warnings, or errors>
Output Files Present:
 - audit_report.json: YES | NO
 - summary_report.csv: YES | NO
 - manifest.json: YES | NO
 - resource_log.json: YES | NO
Execution Time: <seconds>
Peak Memory: <MB>
```

> **Requirement:** This verification log must be updated for every new environment or major dependency change to ensure reproducibility (Constitution Principle I).

## Troubleshooting

- **ERR-001 to ERR-099**: Extraction errors (missing fields, malformed HTML). Check `logs/audit.log`.
- **ERR-301**: Resource limit exceeded. Reduce input size or increase runner resources.
- **ERR-800**: Synthetic validation thresholds not met. Re-run synthetic dataset generation (T026).
- **ERR-801**: Monte-Carlo validation failed. Check `src/audit/monte_carlo_validation.py` logs.

## Next Steps

- Expand to full corpus (≥300 URLs) for production validation.
- Review `docs/statistical_methodology.md` for reconstruction logic.
- Consult `docs/data_provenance.md` for artifact tracking.

## References

- FR-028: Quickstart execution on 30 URLs within 30 minutes
- Constitution Principle I: Reproducibility and verification
- Constitution Principle VII: Provenance and auditability