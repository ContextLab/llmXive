# Quickstart Guide: Evaluating Statistical Validity of A/B Test Summaries

This guide enables a novice user to execute the audit pipeline on a sample of **30 URLs** within **30 minutes** on the default GitHub Actions runner environment (2 vCPU, 7 GB RAM), satisfying **FR-028**.

## Prerequisites

- Python 3.9 or higher
- `pip` package manager
- Internet access to fetch HTML pages
- ~500MB disk space for raw HTML and output artifacts

## Installation

1. Clone the repository:
 ```bash
 git clone <repository-url>
 cd PROJ-492-evaluating-the-statistical-validity-of-p
 ```

2. Create and activate a virtual environment:
 ```bash
 python -m venv venv
 source venv/bin/activate # On Windows: venv\Scripts\activate
 ```

3. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

## Configuration

Ensure the input file `input/urls.csv` contains at least 30 URLs to be audited.
The file format is a simple CSV with a header `url` and one URL per row.

Example `input/urls.csv`:
```csv
url


...
```

If you do not have a custom list, you can use the provided sample:
```bash
cp data/sample_urls.csv input/urls.csv
```

## Execution

Run the full audit pipeline using the driver script:

```bash
python -m code.src.cli.run_audit
```

This command performs the following steps automatically:
1. **Monte-Carlo Validation**: Verifies statistical reconstruction accuracy (aborts if error > 0.005).
2. **Ingestion**: Reads and deduplicates URLs.
3. **Fetching**: Downloads HTML pages with retry logic.
4. **Extraction**: Parses A/B test metrics (p-values, effect sizes, sample sizes).
5. **Reconstruction**: Recalculates statistical tests from raw metrics.
6. **Validation**: Compares reported vs. reconstructed values to flag inconsistencies.
7. **Reporting**: Generates `output/audit_report.json`, `output/summary_report.csv`, and `output/manifest.json`.

### Expected Runtime
- **30 URLs**: ~5–15 minutes (depends on network latency and page load times).
- **Resource Limits**: The script monitors CPU and RAM usage. It will abort with `ERR-301` if limits are exceeded.

## Output Artifacts

Upon successful completion, the following files will be generated in the `output/` directory:

- `audit_report.json`: Detailed audit records for each URL.
- `summary_report.csv`: Aggregate statistics (inconsistency rates, bias-adjusted rates).
- `manifest.json`: SHA256 checksums of all generated artifacts.
- `resource_log.json`: Peak CPU and memory usage statistics.

## Novice-User Verification Step

To confirm successful execution and compliance with the 30-minute constraint:

1. **Check Exit Code**: Ensure the command finished with exit code `0`.
 ```bash
 echo $?
 # Should output: 0
 ```

2. **Verify Output Files**: Confirm the presence of required artifacts.
 ```bash
 ls -l output/audit_report.json output/summary_report.csv output/manifest.json
 ```

3. **Review Runtime**: Check `output/resource_log.json` for the `wall_clock_seconds` field.
 ```bash
 python -c "import json; d=json.load(open('output/resource_log.json')); print(f\"Runtime: {d['wall_clock_seconds']}s\")"
 ```
 The value must be **≤ 1800 seconds** (30 minutes).

4. **Confirmation Log**:
 Create a file `docs/verification_log.txt` in this directory containing:
 - The date and time of execution.
 - The number of URLs processed.
 - The total wall-clock time.
 - A statement confirming that all exit codes were 0 and no `ERR-###` codes (other than expected warnings) were logged.

 Example content for `verification_log.txt`:
 ```text
 Date: 2026-06-27 14:30:00 UTC
 URLs Processed: 30
 Wall-Clock Time: 642 seconds
 Status: SUCCESS
 Verification: All exit codes were 0. No critical errors (ERR-800, ERR-801, ERR-301) detected.
 ```

## Troubleshooting

- **Timeout Errors**: If fetching times out, increase the timeout in `src/config.py` or check network connectivity.
- **Memory Limit Exceeded**: If you see `ERR-301`, reduce the batch size or run on a machine with more RAM.
- **Missing Dependencies**: Re-run `pip install -r requirements.txt` and ensure no errors occurred.

## Next Steps

For a full-scale audit, replace `input/urls.csv` with your complete corpus and ensure your CI environment (GitHub Actions) has sufficient resources. Refer to `docs/STATISTICAL_METHODOLOGY.md` for details on the statistical tests used.