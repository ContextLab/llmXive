# Quickstart Guide: Evaluating Statistical Validity of A/B Test Summaries

**Target**: Execute the audit pipeline on a sample of 30 URLs within 30 minutes.
**Requirement**: FR-028 (Execution Time) & Constitution Principle I (Reproducibility).

## Prerequisites

1. **Python Environment**: Python 3.9+ installed.
2. **Dependencies**: Install the project requirements.
3. **Input Data**: A CSV file containing at least 30 URLs to audit.

## Step 1: Environment Setup

Create a virtual environment and install dependencies to ensure reproducibility (Constitution Principle I).

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Prepare Input Data

Create a file named `input/urls.csv` in the project root. It must contain a header row `url` and at least 30 valid URLs pointing to A/B test summaries.

**Example `input/urls.csv`:**
```csv
url


... (add 28 more URLs)
```

> **Note**: If you do not have 30 specific URLs, you may use the provided synthetic dataset generator for testing purposes, but for a real audit, replace these with actual public URLs.

## Step 3: Execute the Pipeline

Run the main audit driver script. This script orchestrates ingestion, fetching, extraction, reconstruction, validation, and reporting.

```bash
python -m code.src.cli.run_audit --input input/urls.csv --output output/
```

**Expected Behavior:**
- The script will process URLs sequentially.
- It will fetch HTML, extract metrics, and perform statistical reconstruction.
- It will generate `output/audit_report.json`, `output/summary_report.csv`, and `output/manifest.json`.
- **Time Limit**: The process should complete for 30 URLs in under 30 minutes on a standard runner (2 vCPU, 7GB RAM). If it exceeds this, check network latency or increase the timeout in `.github/workflows/audit.yml`.

## Step 4: Verify Output

Ensure the following artifacts exist in the `output/` directory:
- `audit_report.json`: Detailed results for each URL.
- `summary_report.csv`: Aggregated statistics.
- `manifest.json`: SHA256 checksums of all artifacts.
- `resource_log.json`: CPU/Memory usage logs (if resource monitoring is enabled).

## Novice-User Verification Step

To satisfy Constitution Principle I and FR-028, a novice user must verify the environment setup and execution.

**Instructions for the Novice User:**
1. Clone the repository.
2. Follow Step 1 to create the virtual environment.
3. Follow Step 2 to create the `input/urls.csv` file (copy the example content).
4. Follow Step 3 to run the pipeline.
5. Confirm that the script exits with code 0.
6. Confirm that `output/summary_report.csv` exists and is not empty.

**Written Confirmation Log:**
Once the above steps are successfully completed, the user must create a file named `docs/verification_log.txt` (or update this section in a PR) with the following content:

```text
[NOVICE USER VERIFICATION LOG]
Date: YYYY-MM-DD
User: [Name/Identifier]
Environment: [OS, Python Version]

1. Virtual Environment Created: [YES/NO]
2. Dependencies Installed: [YES/NO]
3. Input File Created: [YES/NO]
4. Pipeline Executed Successfully: [YES/NO]
5. Output Files Generated: [YES/NO]
6. Execution Time: [HH:MM:SS]

Comments:
[Any issues encountered or observations about the process]
```

**Submission:**
Commit the `docs/verification_log.txt` file to the repository to close the verification loop.

## Troubleshooting

- **Timeout Errors**: If the pipeline times out, ensure the URLs are accessible. Some domains may block automated requests.
- **Missing Fields**: If extraction fails for many URLs, check the `output/audit_report.json` for `ERR-001` to `ERR-099` codes and review `docs/error_codes.md`.
- **Memory Errors**: If RAM usage exceeds 2GB, reduce the batch size or optimize the dataset. The `resource_monitor` module will log this as `ERR-301`.

## References

- **FR-028**: Execution time constraint.
- **Constitution Principle I**: Reproducibility and deterministic seeds.
- **Constitution Principle VII**: Data provenance and verification.