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

# 4️⃣ Generate the audit report (HTML) with raw & weighted power histograms,
#    count of studies with power < 0.8, and disclaimer about the post‑hoc power fallacy
python code/04_generate_report.py

# 5️⃣ Produce the extraction audit summary (JSON) containing success metrics,
#    sensitivity delta, and dataset type distribution
python code/05_generate_audit_report.py
```

**Expected outputs**

| Step | Output file | Description |
|------|-------------|-------------|
| 01_ingest_openml.py | `data/raw/openml_raw.json` | Raw OpenML response (immutable). |
| 01_ingest_openml.py | `data/processed/filtered_datasets.csv` | Filtered list with OA status. |
| 02_parse_publications.py | `data/processed/statistical_params.json` | Extracted N & effect sizes. |
| 03_compute_observed_power.py | `data/processed/observed_power.csv` | Observed power per dataset (validated against schema). |
| 04_generate_report.py | `data/processed/audit_report.html` | Histogram of observed power (raw & weighted), counts < 0.8, disclaimer. |
| 05_generate_audit_report.py | `data/processed/extraction_audit_report.json` | Extraction success metrics, sensitivity delta, precision/recall/F1, dataset type distribution. |

## 4. Testing

```bash
pytest tests/
```

- **Unit tests** cover `api_client`, `oa_checker`, and `parsers`.  
- **Contract tests** (`tests/contract/`) validate that `filtered_datasets.csv`, `observed_power.csv`, and `extraction_audit_report.json` conform to the JSON‑Schema files in `contracts/`.  
- **Integration test** (`tests/integration/test_full_pipeline.py`) runs the entire pipeline on a deterministic 5‑dataset sample (seeded) and checks that the final report contains both raw and weighted power histograms.

All tests must pass before committing; CI will enforce this automatically.

## 5. Reproducing Exactly

1. Ensure the random seed is set in each script (`np.random.seed(42)` and `random.seed(42)`).  
2. Delete the `data/processed/` directory (keep `data/raw/` if you want to reuse the API response).  
3. Re‑run the five pipeline commands above.  
4. Verify checksums in `data/metadata.json` match the newly generated files.

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `HTTP 429` from OpenML | Rate limit exceeded | The script already retries with exponential backoff; increase `max_retries` in `utils/api_client.py` if needed. |
| No OA link for a dataset | Publication is paywalled or missing | Entry will be marked `paywalled` and excluded from power calculation; check `data/processed/filtered_datasets.csv`. |
| `test_api_client.py` fails | `DataFetchError` not raised | Updated `api_client.fetch_url` now raises `DataFetchError` after max retries (see T004 fix). |
| Empty `filtered_datasets.csv` | Incorrect filter logic | Filtering now uses `publication_link` **or** `task_id` (fixed for T005). |
| Schema validation error | Output file missing required field | Run `pytest tests/contract/` to see the exact missing field; fix the script to populate it. |
| Missing weighted summary | Weighting step omitted | Ensure `04_generate_report.py` runs after `03_compute_observed_power.py`; it adds weighted calculations automatically. |
| Missing ExtractionAuditReport | No audit JSON generated | Run `05_generate_audit_report.py`; it creates `extraction_audit_report.json` per the data model. |

---


