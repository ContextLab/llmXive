# Quickstart Guide: Statistical Validity Audit Pipeline

**Project**: PROJ-492 - Evaluating the Statistical Validity of Public A/B Test Summaries
**Goal**: Audit a corpus of public A/B test summaries for statistical consistency.
**Target**: Process **30 URLs** within **30 minutes** on a standard GitHub Actions runner (2 vCPU, 7 GB RAM).

## Prerequisites

- Python 3.9+
- `pip`
- Network access to fetch URLs (if running locally)
- A text editor for the verification log

## 1. Environment Setup

Clone the repository and install dependencies:

```bash
git clone <repository-url>
cd PROJ-492-evaluating-the-statistical-validity-of-p
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Prepare Input Data

Create a file named `input/urls.csv` containing exactly **30 valid URLs** of public A/B test summaries.
Ensure the file has a header row: `url`.

```csv
url


... (up to 30 rows)
```

*Note: If you do not have 30 real URLs ready, use the provided synthetic generator to create a valid test input:*
```bash
python code/src/audit/synthetic.py --count 30 --output input/urls.csv
```

## 3. Run the Audit Pipeline

Execute the main driver script. This orchestrates ingestion, fetching, extraction, reconstruction, validation, and reporting.

```bash
python code/src/cli/run_audit.py --input input/urls.csv --output output/
```

### Expected Runtime
- **Target**: < 30 minutes for 30 URLs.
- **Resource Limits**: The pipeline enforces a RAM limit of 2 GB and CPU usage consistent with 2 vCPUs. If these limits are exceeded, the script will abort with `ERR-301`.

## 4. Verify Outputs

Upon successful completion (exit code 0), verify the following artifacts exist in the `output/` directory:

- `audit_report.json`: Detailed audit records for each URL.
- `summary_report.csv`: Aggregated statistics (inconsistency rates, bias-adjusted rates).
- `manifest.json`: SHA256 checksums of all generated artifacts.
- `resource_log.json`: Peak CPU and memory usage statistics.

## 5. Novice-User Verification Step

To ensure reproducibility and compliance with FR-028, **you must complete this verification step**:

1. **Record Execution Time**: Note the start and end time of the pipeline run.
2. **Check Resource Log**: Open `output/resource_log.json` and confirm `peak_memory_gb` < 2.0.
3. **Confirm Output Integrity**: Run the following command to verify the manifest:
 ```bash
 python code/src/utils/manifest.py --validate output/manifest.json
 ```
4. **Write Confirmation Log**: Create a file named `docs/verification_log.md` (or append to this file) with the following content:

---
### Verification Log for Quickstart (T049)

**Date**: `[YYYY-MM-DD]`
**User**: `[Your Name/ID]`
**Input URLs Count**: `[Number, e.g., 30]`
**Start Time**: `[HH:MM:SS]`
**End Time**: `[HH:MM:SS]`
**Total Duration**: `[MM:SS]` (Must be < 30 minutes)
**Peak Memory (GB)**: `[Value from resource_log.json]` (Must be < 2.0)
**Manifest Valid**: `[Yes/No]`

**Confirmation Statement**:
> "I, `[Your Name]`, confirm that the pipeline successfully processed the specified number of URLs within the 30-minute time limit and resource constraints. All required output artifacts were generated and validated."

**Signature**: ____________________
---

## Troubleshooting

- **ERR-301**: Resource limit exceeded. Reduce input size or check for memory leaks.
- **ERR-801**: Monte-Carlo validation failed on startup. This indicates a statistical library issue; do not proceed.
- **Network Errors**: Ensure your environment allows outbound HTTPS requests to the target domains.

## Next Steps

Once verified, proceed to **User Story 2** (Summary Report Generation) for deeper analysis or **User Story 3** (Export Audit Results) for integration.