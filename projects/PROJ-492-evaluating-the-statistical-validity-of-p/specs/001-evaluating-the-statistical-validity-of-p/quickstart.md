# Quickstart: Auditing Public A/B Test Summaries

This guide walks a new user through a **complete end‑to‑end run** of the audit pipeline on a small sample corpus (30 URLs) using the default GitHub Actions runner.

## Prerequisites
- GitHub account with permission to run Actions on the repository.
- A CSV file `input/urls.csv` containing a header `url` and a list of public A/B test summary URLs (at least 30 rows).

## Step‑by‑Step

| Step | Command | Expected Outcome |
|------|---------|------------------|
| 1️⃣ Clone the repository | `git clone && cd ab-test-audit` | Repository files appear locally. |
| 2️⃣ Install dependencies (locally) | `python -m venv.venv && source.venv/bin/activate && pip install -r requirements.txt` | All Python packages installed; versions pinned. |
| 3️⃣ Prepare a tiny URL list | Create `input/urls.csv` with a set of reachable URLs. Example: <br>`url<br><br>…` | File ready for the pipeline. |
| 4️⃣ Run the audit locally (optional) | `python -m src.run_audit input/urls.csv output/` | Generates `output/audit_report.json`, `output/summary_report.csv`, `output/bias_report.json`, `output/subgroup_report.json`. |
| 5️⃣ Trigger CI (recommended) | Push a branch containing `input/urls.csv` and open a PR. The workflow `.github/workflows/audit.yml` runs automatically. | CI logs show the pipeline completing within 30 minutes, exit status 0, and artifacts uploaded as CI artifacts. |
| 6️⃣ Inspect results | Download `summary_report.csv` from the CI artifacts or open `output/summary_report.csv` locally. | Columns: `total_summaries`, `inconsistent_count`, `inconsistent_rate`, `bias_adjusted_rate`, `wilson_ci_lower`, `wilson_ci_upper`. |
| 7️⃣ Verify reproducibility | Re‑run the same command (or re‑trigger CI). The `manifest.json` hash values should be identical. | Confirms reproducibility (Constitution I). |

## Runtime Expectations
- **Wall‑clock time**: ≤ 30 minutes for 30 URLs on the default runner (≈ 2 vCPU, 2 GB RAM).
- **Memory usage**: ≤ 1 GB (well under the 2 GB limit).
- **CPU**: No GPU; all libraries are pure‑CPU.

## Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `ERR-001` logged, many URLs missing | Network timeouts or dead URLs | Verify URLs are reachable; remove or replace dead links. |
| Parsing error rate > 5 % | Unexpected HTML structure | Extend `extractor.py` regexes or report to developers. |
| CI job exceeds multiple hours | Corpus too large (> 5 000 URLs) | Subsample or increase `MAX_URLS` in `config.py`. |

## Additional Validation Guarantees
- **Schema Validation**: The CI workflow automatically runs `jsonschema` validation on `output/audit_report.json` (against `audit_record.schema.yaml`) and `output/manifest.json` (against `manifest.schema.yaml`). Any schema violation causes the job to fail, ensuring contract compliance.
- **Contract Checks**: After each major pipeline stage (extraction, audit, manifest creation) the code invokes `jsonschema.validate` to catch structural issues early.

For a complete reference of all command‑line options, see `README.md` in the repository root.

---



