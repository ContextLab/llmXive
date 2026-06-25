# Quickstart: Auditing Public A/B Test Summaries

This guide enables a newcomer to run the full audit on a sample corpus of **30 URLs** within **30 minutes** on the default GitHub Actions runner (or locally on a comparable machine).

## Prerequisites
| Item | Minimum Version |
|------|-----------------|
| Python | 3.11 |
| Git | any |
| Internet access | required to fetch URLs |

All Python dependencies are listed in `requirements.txt`.

## Step‑by‑Step

1. **Clone the repository**
 ```bash
 git clone
 cd ab-test-audit
 ```

2. **Create a Python virtual environment and install dependencies**
 ```bash
 python -m venv.venv
 source.venv/bin/activate
 pip install -r requirements.txt
 ```

3. **Prepare the input URL list**
 ```csv
 # input/urls.csv
 url

 Connection refused"))]
 …
 ```
 Include **30** reachable URLs (the file must have a header `url`). A ready‑made sample file `sample_urls_30.csv` is provided in the repo.

4. **Run the audit pipeline**
 ```bash
./run_audit.sh input/urls.csv output/
 ```
 - The script downloads each page, extracts metrics, reconstructs statistics, flags inconsistencies, performs prevalence testing, and writes artefacts to `output/`.
 - Runtime on CI: well under the half‑hour target for the tested URLs.

5. **Inspect the results**
 - **JSON detailed report**: `output/audit_report.json` (one record per URL).
 - **CSV summary**: `output/summary_report.csv` (columns: `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`).
 - **Bias report**: `output/bias_report.json` (domain proportions, weighted rate).
 - **Checksums**: `output/checksums.txt` (SHA‑256 of each artefact).

6. **Validate reproducibility (optional)**
 ```bash
 pytest -q tests/contract/
 ```
 All contract tests should pass (exit code 0). The `manifest.json` file will list the hashes of the generated artefacts.

7. **Run the synthetic validation (optional, longer)**
 ```bash
./run_synthetic_validation.sh output/
 ```
 Generates `synthetic_validation_report.json` containing precision/recall/F1 metrics (must meet SC‑030).

## Expected Resource Usage
- **CPU**: ≤ 2 vCPUs (observed approximately one vCPU on CI).
- **Memory**: ≤ 1.6 GB peak.
- **Disk**: < 500 MB for all outputs (well within the 14 GB limit).

If the job exceeds the limits, the CI step will be killed and the failure will be reported (fulfills **SC‑008**).

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Many `ERR-***` entries in logs | URLs dead or HTML format unexpected | Verify URLs; ensure they point to HTML pages containing the required metrics. |
| `Parsing error rate > 5 %` | Input list contains many malformed pages | Remove problematic URLs or increase sample size to meet **SC‑005**. |
| CI job times out > 6 h | Input corpus > 5 000 URLs without subsampling | Use the built‑in domain subsampling (FR‑027) or split the run into multiple CI jobs. |

---
