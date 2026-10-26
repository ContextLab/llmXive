# Quickstart: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Prerequisites
- Python 3.11 or newer
- `git`
- Internet access (for OpenML API and OA publications)
- GitHub Actions free‑tier runner (for CI validation) – optional for local runs

## 2. Installation

```bash
# Clone the repository (replace <repo-url> with the actual URL)
git clone <repo-url>
cd projects/PROJ-234-assessing-statistical-power-in-reproduci

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install pinned dependencies
pip install -r code/requirements.txt
```

## 3. Running the Full Pipeline

All scripts are designed to be run sequentially from the project root:

```bash
# 1️⃣ Ingest OpenML metadata and filter (uses utils.api_client with exponential backoff)
python code/01_ingest_openml.py

# 2️⃣ Check OA status, download OA texts, then extract N & effect size
python code/02_parse_publications.py

# 3️⃣ Compute observed statistical power (appropriate test per metric)
python code/03_compute_observed_power.py

# 4️⃣ Generate the audit report (HTML) with raw power histograms,
#    count of studies with reference power < 0.8, and disclaimer about the post‑hoc power fallacy
python code/04_generate_report.py

# 5️⃣ Produce the extraction audit summary (JSON) containing success metrics,
#    sensitivity delta, and precision/recall/F1 (written to reports/extraction_audit.json)
python code/05_generate_audit_report.py

# 6️⃣ Apply inverse‑download‑count weighting to obtain weighted prevalence estimates
python code/06_apply_weighting.py

# 7️⃣ Run meta‑audit power analysis and confound regression
python code/07_meta_audit_power.py
```

**Expected outputs**

| Step | Output file | Description |
|------|-------------|-------------|
| 01_ingest_openml.py | `data/raw/openml_raw.json` | Raw OpenML response (immutable). |
| 01_ingest_openml.py | `data/processed/filtered_datasets.csv` | Filtered list with OA status (CSV). |
| 02_parse_publications.py | `data/processed/statistical_params.json` | Extracted sample sizes and effect sizes. |
| 03_compute_observed_power.py | `data/processed/observed_power.csv` | Observed **and** reference power per dataset (validated against schema). |
| 04_generate_report.py | `data/processed/audit_report.html` | Histogram of raw power (a set of bins, per verified bin count), count < 0.8, disclaimer, and JSON‑pointer link to `reports/extraction_audit.json`. |
| 05_generate_audit_report.py | `reports/extraction_audit.json` | Extraction success metrics, sensitivity delta, precision/recall/F1 (validated against the embedded `ExtractionAuditReport` schema in `contracts/power_audit_result.schema.yaml`). |
| 06_apply_weighting.py | `data/processed/weighted_power.csv` | Weighted prevalence estimates (inverse‑download‑count). |
| 07_meta_audit_power.py | (updates) `data/processed/audit_report.html` | Adds meta‑audit power justification and confound regression results. |

## 4. Testing

```bash
pytest tests/
```

- **Unit tests** cover `api_client`, `oa_checker`, and `parsers`.  
- **Extraction precision/recall test** (`tests/unit/test_extraction_audit_metrics.py`) asserts that both precision **≥ 0.9** and recall **≥ 0.9** (addresses SC‑005).  
- **Contract tests** validate that `filtered_datasets.csv`, `observed_power.csv`, `statistical_params.json`, and `extraction_audit.json` conform to their schemas **as defined in `contracts/power_audit_result.schema.yaml`** (the file now contains definitions for `StatisticalParameters` and `ExtractionAuditReport`).  
- **Integration test** (`tests/integration/test_full_pipeline.py`) runs the entire pipeline on a deterministic 5‑dataset subset (seed = 42) and asserts:
  1. `filtered_datasets.csv` is non‑empty.  
  2. `observed_power.csv` contains both `observed_power` and `reference_power` columns.  
  3. `audit_report.html` contains the 20‑bin histograms, the disclaimer, and the reference‑power adequacy count.  
  4. The HTML includes a JSON‑pointer link to `reports/extraction_audit.json`.  
  5. Test `test_report_contains_reference_power_metric.py` (part of the integration suite) confirms the presence of the reference‑power adequacy metric.

All tests must pass; CI will abort on any failure.

## 5. Reproducing Exactly

1. Ensure the random seed is set in each script (`np.random.seed(42)` and `random.seed(42)`).  
2. Delete the `data/processed/` directory (keep `data/raw/` if you want to reuse the API response).  
3. Re‑run the seven pipeline commands above.  
4. Verify checksums in `data/metadata.json` match the newly generated files.

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `HTTP 429` from OpenML | Rate limit exceeded | The script already retries with exponential backoff; increase `max_retries` in `utils/api_client.py` if needed. |
| No OA link for a dataset | Publication is paywalled or missing | Entry will be marked `paywalled` and excluded from power calculation; check `data/processed/filtered_datasets.csv`. |
| `test_api_client.py` fails (no `DataFetchError`) | `api_client` missing proper backoff/error handling | Updated `api_client.py` now raises `DataFetchError` after max retries (see T004 fix). |
| Empty `filtered_datasets.csv` | Incorrect filter logic | Filtering now uses `publication_link` **or** `task_id`. |
| Schema validation error | Output file missing required field | Run `pytest tests/contract/` to see the exact missing field; fix the script to populate it. |
| Missing weighted summary | Weighting step omitted | Weighting has been added (T009) and reported in the final HTML. |
| Missing `extraction_audit.json` | Audit step not executed | Run `05_generate_audit_report.py`; it creates the JSON per the data model. |

---

