# Quickstart Guide: Evaluating Statistical Validity of A/B Test Summaries

**Target**: Execute the audit pipeline on a sample of **30 URLs** within **30 minutes** on the default GitHub Actions runner (2 vCPU, 7 GB RAM).

**FR-028 Compliance**: This guide ensures the pipeline is lightweight enough for rapid validation while maintaining statistical rigor.

---

## 1. Prerequisites

Ensure you have the following installed:
- Python 3.9+
- `pip`
- A text editor (for the verification log)

If you are running locally, create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Prepare the Input Data

The pipeline requires an input CSV file containing the URLs to audit.

1. Create the input directory if it doesn't exist:
 ```bash
 mkdir -p input
 ```

2. Create `input/urls.csv` with a header `url` and exactly **30 valid A/B test summary URLs**.
 *Example content (replace with real URLs):*
 ```csv
 url


... (add 28 more)
 ```

> **Note**: For this quickstart, use a small, curated list of 30 URLs to ensure the 30-minute timeout is met.

## 3. Execute the Pipeline

Run the main audit driver script. This script orchestrates ingestion, fetching, extraction, reconstruction, validation, and reporting.

```bash
python -m code.src.cli.run_audit --input input/urls.csv --output output --quickstart
```

**Expected Behavior**:
- The script will log progress to the console.
- It will fetch HTML, extract metrics, and perform statistical reconstruction.
- It will automatically enforce resource limits (CPU ≤ 2 vCPU, RAM ≤ 2 GB) as per FR-009.
- Upon completion, it will generate:
 - `output/audit_report.json`
 - `output/summary_report.csv`
 - `output/manifest.json`

**Timing Constraint**:
- The process should complete in **< 30 minutes** for 30 URLs.
- If the process exceeds this time, check the `output/resource_log.json` for bottlenecks or network latency issues.

## 4. Verify Results

1. **Check Exit Code**: Ensure the script exited with code 0.
2. **Inspect Output**: Open `output/summary_report.csv` to confirm columns exist (`total_summaries`, `inconsistent_count`, etc.).
3. **Review Manifest**: Verify `output/manifest.json` contains SHA256 hashes for all generated artifacts.

## 5. Novice-User Verification Step (Required)

To confirm successful execution and compliance with FR-028, you must generate a **written confirmation log**.

1. Create a file named `docs/quickstart_verification_log.txt` in the project root.
2. Fill in the following template with your actual run data:

```text
=========================================
QUICKSTART VERIFICATION LOG
=========================================
Date: [YYYY-MM-DD HH:MM:SS]
User: [Your Name/ID]

Input File: input/urls.csv
Number of URLs Processed: [Count, e.g., 30]

Execution Time: [Start Time] to [End Time]
Total Duration: [Duration in minutes]

Resource Limits Observed:
- Max CPU Usage: [e.g., 1.2 vCPU]
- Max RAM Usage: [e.g., 1.1 GB]

Output Artifacts Generated:
- [ ] output/audit_report.json
- [ ] output/summary_report.csv
- [ ] output/manifest.json

Verification Status:
- Script Exit Code: [0 or Non-Zero]
- All 7 Constitution Principles Checked: [Yes/No]

Notes:
[Any issues encountered or observations]

Signature: _________________________
=========================================
```

3. **Commit this log**: Add `docs/quickstart_verification_log.txt` to your version control to prove the pipeline was successfully executed by a novice user.

## Troubleshooting

- **ERR-301**: Resource limit exceeded. Check `output/resource_log.json`.
- **ERR-800**: Synthetic validation failed. Ensure `data/synthetic/` files are present.
- **Network Timeout**: Increase retry limits in `src/config.py` if running on unstable connections.

## Next Steps

For full-scale analysis, refer to `docs/README_FULL.md` and increase the input URL count. Ensure you have sufficient compute resources for larger corpora.