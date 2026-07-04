# Quickstart Guide: Evaluating Statistical Validity of A/B Test Summaries

This guide provides instructions for running the automated audit pipeline on a sample of 30 public A/B test summaries within 30 minutes on a standard GitHub Actions runner (2 vCPU, 7 GB RAM).

## Prerequisites

- Python 3.9+
- Git
- Access to the project repository
- A list of 30 public A/B test summary URLs (provided in `data/sample_urls.csv` or create your own)

## Installation

1. Clone the repository:
 ```bash
 git clone
 cd proj-492-evaluating-statistical-validity
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

Ensure your `input/urls.csv` file contains exactly 30 URLs for this quickstart test. If you need to create one:

```csv
url


#... add 28 more URLs
```

## Execution

Run the full audit pipeline:

```bash
python -m code.src.cli.run_audit --input input/urls.csv --output output/ --timeout 1800
```

**Note:** The `--timeout 1800` flag ensures the process aborts if it exceeds 30 minutes (1800 seconds).

## Expected Outputs

Upon successful completion, the following files will be generated in the `output/` directory:

- `audit_report.json`: Detailed audit records for each URL
- `summary_report.csv`: Aggregated statistics and inconsistency rates
- `manifest.json`: SHA256 checksums of all generated artifacts
- `resource_log.json`: CPU and memory usage metrics

## Performance Expectations

- **Runtime:** ≤ 30 minutes for 30 URLs on a 2 vCPU, 7 GB RAM runner
- **Memory Usage:** ≤ 2 GB peak RAM
- **CPU Usage:** ≤ 2 vCPU cores

## Novice-User Verification Step

To verify the pipeline works correctly on your environment, follow these steps:

1. **Run the pipeline** using the command above.
2. **Check for errors:** Ensure the exit code is 0 and no `ERR-###` codes appear in the logs.
3. **Verify outputs:** Confirm that `output/audit_report.json` contains at least 25 records (allowing for 5 failed fetches/extracts).
4. **Check resource usage:** Open `output/resource_log.json` and verify that `peak_memory_gb` is ≤ 2.0 and `peak_cpu_cores` is ≤ 2.0.
5. **Run the validation script:**
 ```bash
 python -m code.tests.integration.test_quickstart_validation
 ```
 This script will automatically check all the above conditions.

### Written Confirmation Log

After completing the verification, create a file named `verification_log.txt` in the project root with the following content:

```
Verification Log - Quickstart T049
====================================
Date: [YYYY-MM-DD HH:MM:SS]
Environment: [GitHub Actions Runner / Local Machine]
OS: [Linux/Windows/macOS]
Python Version: [X.Y.Z]
Runner Type: [e.g., ubuntu-latest, 2 vCPU, 7 GB RAM]

Results:
- Pipeline Exit Code: [0 or non-zero]
- Records Processed: [N]
- Records Failed: [M]
- Peak Memory (GB): [X.XX]
- Peak CPU Cores: [X.X]
- Total Runtime (seconds): [X]

Verification Status: [PASS/FAIL]
Notes: [Any additional observations or issues encountered]
```

Submit this log as evidence of successful execution.

## Troubleshooting

- **Timeout errors:** If the pipeline exceeds 30 minutes, check for slow network connections or large HTML pages. Consider reducing the number of URLs.
- **Memory errors:** If you encounter `ERR-301`, your environment may not meet the 2 GB RAM limit. Reduce the batch size or upgrade resources.
- **Extraction failures:** If many records fail to extract, verify that the URLs are accessible and the HTML structure matches expected patterns.

## Next Steps

Once verified, you can:
- Scale to larger datasets (100+ URLs)
- Customize the audit thresholds in `src/config.py`
- Integrate with your CI/CD pipeline using `.github/workflows/audit.yml`

For more details, refer to the full documentation in `docs/`.