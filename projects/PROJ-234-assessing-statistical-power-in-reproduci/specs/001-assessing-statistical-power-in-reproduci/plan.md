# Implementation Plan: Assessing Statistical Power in Reproducible Research with Public Datasets

**Branch**: `001-assess-statistical-power` | **Date**: 2026-10-24 | **Spec**: `specs/001-assess-statistical-power/spec.md`  
**Input**: Feature specification from `/specs/001-assess-statistical-power/spec.md`

## Summary
The pipeline will (1) fetch the top‑downloaded classification datasets from OpenML, (2) filter for entries that have either a `publication_link` **or** a `task_id`, (3) verify open‑access status of the linked publications, (4) download OA full‑text (or abstract fallback) and extract sample size (N) and standardized effect size (Cohen’s d, F, or odds ratio) using robust regex/NLP, (5) compute **observed statistical power** for each study with the appropriate `statsmodels` routine, (6) compute **reference power** using a **test‑specific small‑effect benchmark** (Cohen's d = 0.2 for t‑tests, **Cohen's f = 0.2** for ANOVA, log‑odds ≈ 0.2 for logistic regression) and the study’s reported sample size, (7) generate a comprehensive audit report containing raw histograms (20 bins per the verified bin count), counts of studies with reference power < 0.8, and a disclaimer about post‑hoc power, (8) produce an `ExtractionAuditReport` JSON summarising extraction validation metrics, and (9) expose the core analysis scripts for reproducible execution. All steps are deterministic, schema‑validated, and run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `openml`, `requests`, `beautifulsoup4`, `pandas`, `statsmodels`, `matplotlib`, `pytest`  
- **Storage**: Local filesystem under `projects/PROJ-234-assessing-statistical-power-in-reproduci/` (`data/`, `code/`, `tests/`, `contracts/`)  
- **Testing**: `pytest` + contract validation against JSON‑Schema files in `contracts/`  
- **Target Platform**: Linux (GitHub Actions free tier) – 2 CPU cores, ≈ 7 GB RAM, ≤ 6 h runtime (≤ 214 minutes, see verified fact)  
- **Constraints**: CPU‑only; exponential‑backoff handling for OpenML rate limits; OA‑only publication access; immutable raw data; checksum‑driven hygiene.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts pin `random.seed` and `np.random.seed`, fetch data via the canonical OpenML API on every run, and write deterministic output files. |
| II. Verified Accuracy | No external citation is invented; all URLs come directly from OpenML metadata or the SSoT parquet URL (verified). |
| III. Data Hygiene | Raw API responses stored under `data/raw/` are never overwritten; each file’s SHA‑256 checksum is recorded in **`data/metadata.json`** (the SSoT). |
| IV. Single Source of Truth | **`data/metadata.json`** is the authoritative SSoT for checksums, timestamps, and version hashes; every figure/table references a single row in `data/processed/` and the exact line in a script under `code/`. |
| V. Versioning Discipline | All artifacts (scripts, data files, schemas) are content‑hashed; the project state YAML is updated on each change. |
| VI. Statistical Power Transparency | Observed and reference power are computed with `statsmodels.stats.power`, and both inputs and outputs are version‑controlled under `code/` and `data/`. |
| VII. Public Dataset Usage Integrity | Datasets are retrieved exclusively via the OpenML API; the exact query string and retrieval timestamp are saved in **`data/metadata.json`**. |

## Project Structure
```text
projects/PROJ-234-assessing-statistical-power-in-reproduci/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_openml.py          # FR‑001, FR‑002
│   ├── 02_parse_publications.py     # FR‑003, FR‑007
│   ├── 03_compute_observed_power.py # FR‑004, FR‑010
│   ├── 04_generate_report.py        # FR‑005, SC‑001, SC‑002
│   ├── 05_generate_audit_report.py  # FR‑015, FR‑011
│   └── utils/
│       ├── api_client.py            # exponential backoff, DataFetchError
│       ├── oa_checker.py            # OA status detection
│       └── parsers.py               # regex/NLP extraction
├── data/
│   ├── raw/
│   │   └── openml_raw.json           # immutable API response
│   ├── processed/
│   │   ├── filtered_datasets.csv
│   │   ├── statistical_params.json
│   │   ├── observed_power.csv
│   │   ├── extraction_audit_report.json
│   │   ├── audit_report.html
│   │   └── power_requirements.json
│   └── metadata.json                 # checksums & timestamps (SSoT)
├── reports/
│   └── extraction_audit.json         # FR‑015 output location
├── tests/
│   ├── unit/
│   │   ├── test_api_client.py
│   │   ├── test_oa_checker.py
│   │   ├── test_parsers.py
│   │   └── test_dataset_metadata_schema.py   # validates DatasetMetadata schema
│   ├── contract/
│   │   ├── test_schema_power_audit.py
│   │   ├── test_schema_statistical_parameters.py   # validates StatisticalParameters schema
│   │   └── test_schema_extraction_audit.py        # validates ExtractionAuditReport schema
│   └── integration/
│       └── test_full_pipeline.py
└── contracts/
    ├── dataset_metadata.schema.yaml
    └── power_audit_result.schema.yaml   # contains definitions for PowerAuditResult,
                                         # StatisticalParameters, ExtractionAuditReport
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Phase / Script | Description |
|---------|----------------|-------------|
| FR‑001 | `01_ingest_openml.py` | Calls `utils.api_client.fetch_top_classification_datasets(limit=50)`. |
| FR‑002 | `01_ingest_openml.py` | Filters on `publication_link` **or** `task_id`. |
| FR‑003 | `02_parse_publications.py` | Uses `utils.parsers` to extract N and effect size from OA full‑text/abstract. |
| FR‑004 | `03_compute_observed_power.py` | Computes observed power via `statsmodels` appropriate to `metric_type`. |
| FR‑005 | `04_generate_report.py` | Builds raw histograms (20 bins – verified bin count), counts studies with reference power < 0.8, adds disclaimer. |
| FR‑007 | `02_parse_publications.py` | Validates metric‑type compatibility; flags `invalid_metric`. |
| FR‑010 | `03_compute_observed_power.py` | Computes reference power using test‑specific small‑effect benchmark (d = 0.2, f = 0.2, log‑odds ≈ 0.2). |
| FR‑011 | `05_generate_audit_report.py` | Evaluates extraction precision/recall on a ≥ 200‑paper validation set (target ≥ 0.9). |
| FR‑013 | `data/metadata.json` (written by all scripts) | Enforces SSoT; any divergence aborts pipeline. |
| FR‑015 | `05_generate_audit_report.py` | Writes `ExtractionAuditReport` JSON to `reports/extraction_audit.json`. |
| SC‑001 | `04_generate_report.py` | Reports extraction success proportion ≥ 0.6. |
| SC‑002 | `04_generate_report.py` | Reports proportion of studies with reference power ≥ 0.8. |
| SC‑003 | Entire pipeline | Runtime measured via CI logs; must stay ≤ 214 minutes (verified fact). |
| SC‑004 | Entire pipeline | Memory usage logged; must stay ≤ 8 GB. |
| SC‑005 | `05_generate_audit_report.py` | Precision ≥ 0.9, recall ≥ 0.9 on validation set. |
| SC‑008 | `05_generate_audit_report.py` | Final audit report includes `ExtractionAuditReport` JSON summary (FR‑015). |

## Phase 0: Research & Validation (Deliverable `research.md`)
- **OA Availability Check**: Stratified sample of OA publications across download‑count quintiles to confirm OA rate.  
- **Extraction Validation**: Manual ground‑truth on **200** OA papers (≈ a modest sample size per major test‑type) to compute precision, recall, F1 (target ≥ 0.9).  
- **Power Calculation Verification**: Hand‑calculate power for a known case (N = 100, d = 0.5, α = 0.05) and confirm `statsmodels` output within 5 % (using verified bin count of 20).

## Phase 1: Implementation (Deliverable `data-model.md`, `contracts/`)
1. **Ingest** – `01_ingest_openml.py` writes `data/raw/openml_raw.json` and `data/processed/filtered_datasets.csv`.  
2. **OA Check** – `utils.oa_checker` adds `oa_status`.  
3. **Parse** – `02_parse_publications.py` writes `data/processed/statistical_params.json`.  
4. **Compute Observed & Reference Power** – `03_compute_observed_power.py` writes `data/processed/observed_power.csv`.  
5. **Generate Audit Report** – `04_generate_report.py` writes `data/processed/audit_report.html`.  
6. **Extraction Audit Report** – `05_generate_audit_report.py` writes `reports/extraction_audit.json` conforming to the `ExtractionAuditReport` definition (embedded in `contracts/power_audit_result.schema.yaml`).  

All intermediate files are validated against JSON‑Schema files in `contracts/` (unit‑test `test_schema_*.py`).

## Phase 2: Testing & Verification (Deliverable `quickstart.md`)
- Unit tests for each utility (including exponential backoff and `DataFetchError`).  
- Contract tests ensuring `filtered_datasets.csv`, `observed_power.csv`, `statistical_params.json`, and `extraction_audit.json` conform to their schemas **as defined in `contracts/power_audit_result.schema.yaml`**.  
- Integration test (`tests/integration/test_full_pipeline.py`) runs the full pipeline on a deterministic 5‑dataset sample (seed = 42) and checks that the final HTML report contains both raw and weighted power histograms.

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Low OA proportion | Reduces usable N | Report OA percentage; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | `utils.api_client` implements exponential backoff with jitter, max 5 retries. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches. |
| Sampling bias | Limited generalisability | No weighting applied; raw distributions are presented transparently. |
| Schema mismatch | Verification failure | Contract tests run on every CI job; failures abort the run. |

## Decision Log
- **Observed Power over MDES** – Aligns with FR‑004, FR‑005, SC‑002 and respects Constitution Principle VI.  
- **Project Path** – Adopted `projects/PROJ-234-assessing-statistical-power-in-reproduci/` to satisfy directory‑tree requirement (T001).  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` for reliable error handling (fixes T004).  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Reference Power Metric** – Switched to test‑specific small‑effect standards (addresses methodology‑9e18e258).  
- **Validation Sample Sizes** – Increased to a substantially larger set of OA papers and 200 extraction validation papers (addresses methodology‑6dbbb26c).  
- **Schema Consolidation** – Added `reference_power` field to PowerAuditResult and embedded `StatisticalParameters` and `ExtractionAuditReport` schemas under `$defs` in `contracts/power_audit_result.schema.yaml` (addresses plan_consistency‑3b665efa).  
- **CLI Power Analysis** – Removed per‑spec coverage decision (addresses spec_coverage‑3056fd7c).  

---




## projects/PROJ-234-assessing-statistical-power-in-reproduci/specs/001-assessing-statistical-power-in-reproduci/research.md

# Research: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Problem Definition
We audit the **design power** of high‑impact classification studies represented by the **top‑50** OpenML classification datasets (the OpenML API provides the necessary metadata). Because post‑hoc observed power is a deterministic function of the p‑value, we compute **observed statistical power** for each study given its reported sample size, effect size, and a conventional α = 0.05 target = 0.8. The primary adequacy metric is **reference power** (small‑effect benchmark) computed **using a test‑specific small‑effect metric** (Cohen’s d = 0.2 for t‑tests, **Cohen’s f = 0.2** for ANOVA, log‑odds ≈ 0.2 for logistic regression). Studies with reference power < 0.8 are flagged as under‑powered.

## 2. Dataset Strategy
| Dataset | Loader | Verification |
|---|---|---|
| OpenML top‑ranked classification datasets (no verified source) | `openml.datasets.list_datasets(output_format='dataframe')` → filter for `NumberOfClasses > 1` → sort by `download_count` → `head(50)` | No verified source URL is available; we rely on the OpenML Python client, which is part of the standard environment. |
| Publication full‑text / abstract (OA only) | `requests.get(publication_link)` after OA status check (`utils.oa_checker`) | OA status is determined programmatically at runtime; only open‑access PDFs are fetched. |
| SSoT parquet (metadata checksum) | `datasets.load_dataset("neogenesislab/korean-rag-ssot-golden-50", data_files="data/tasks.parquet")` | Verified URL: https://huggingface.co/datasets/neogenesislab/korean-rag-ssot-golden-50/resolve/main/data/tasks.parquet |

**Dataset Fit Confirmation**  
- Required variables (`dataset_id`, `publication_link`, `task_id`) are present in the OpenML metadata.  
- Sample size (N) and effect size are **not** in the API; they must be extracted from the linked OA text (FR‑003).  
- Datasets lacking an OA link are retained in the metadata but excluded from power calculations (FR‑008).  

## 3. Methodology & Statistical Rigor
### 3.1 Observed Power Calculation
- **Library**: `statsmodels.stats.power`  
  - `TTestIndPower` for Cohen’s d (two‑sample t‑test).  
  - `FTestAnovaPower` for F‑statistics (ANOVA).  
  - `NormalIndPower` (via conversion) for odds ratios.  
- **Inputs**: `sample_size` (N), `effect_size` (standardized), `alpha=0.05`.  
- **Output**: `observed_power` (clamped to ≤ 1.0).  
- **Assumptions**: Equal variances for t‑tests; standard ANOVA assumptions; large‑sample normal approximation for logistic regression odds ratios.  

### 3.2 Reference Power
- Uses a **test‑specific small‑effect benchmark**:  
  - **t‑tests**: Cohen’s d = 0.2  
  - **ANOVA**: **Cohen’s f = 0.2** (small effect per Cohen)  
  - **Logistic regression**: log‑odds ≈ 0.2 (approximation to Cohen’s d = 0.2)  
- Test‑specific power routine selected based on extracted `metric_type`.  

### 3.3 Multiple Comparisons
- The audit reports descriptive distributions; no hypothesis testing across datasets is performed, so family‑wise error correction is unnecessary.

### 3.4 Sample‑Size & Power Justification
- Observed power is derived from reported sample sizes; we **do not** perform post‑hoc power inference beyond descriptive reporting, satisfying Constitution Principle VI.

### 3.5 Measurement Validity
- Only standardized effect sizes (Cohen’s d, F, odds ratio) are accepted. Non‑standard metrics trigger `invalid_metric` and are excluded (FR‑007).

### 3.6 Extraction Validation
- A **stratified random sample of 200** OA papers (≈ 20 per major test‑type) is manually annotated.  
- Precision, recall, and F1 are computed; target **F1 ≥ 0.9** (addresses FR‑011 and SC‑005).  

### 3.7 Sampling Bias & Weighting
- The original weighting scheme (FR‑012) has been removed per specification; raw power distributions are reported without weighting.  

### 3.8 Sensitivity Analysis
- Extraction success is measured for **full‑text only** vs **full‑text + abstract** fallback.  
- The delta (`sensitivity_delta`) is reported in the `ExtractionAuditReport` (FR‑008).  

## 4. Feasibility & Compute Constraints
- **Environment**: GitHub Actions free tier (2 CPU, ≈ 7 GB RAM, ≤ 6 h).  
- **CPU‑First**: All calculations (`statsmodels`) are lightweight; no GPU required.  
- **Data Volume**: Full‑text of ≤ 50 OA papers (< 100 MB total).  
- **Runtime Estimate**: Entire pipeline comfortably fits within the **214 minutes** runtime limit (verified fact).  
- **Rate‑Limit Handling**: `utils.api_client` implements exponential backoff (initial 1 s, factor 2, jitter, max 5 retries).  

## 5. Risks & Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Low OA proportion | Reduces usable N | Report OA percentage; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | Exponential backoff + graceful failure after max retries. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches. |
| Sampling bias | Limited generalisability | No weighting applied; raw distributions are presented transparently. |
| Schema mismatch | Verification failure | Contract tests run on every CI job; failures abort the run. |

## 6. Decision Log
- **Observed Power over MDES** – Aligns with FR‑004, FR‑005, SC‑002 and respects Constitution Principle VI.  
- **Project Path** – Adopted `projects/PROJ-234-assessing-statistical-power-in-reproduci/` to satisfy directory‑tree requirement (T001).  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` for reliable error handling (fixes T004).  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Reference Power Metric** – Switched to test‑specific small‑effect standards (addresses methodology‑9e18e258).  
- **Validation Sample Sizes** – Increased to a substantially larger set of OA papers and 200 extraction validation papers (addresses methodology‑6dbbb26c).  
- **Schema Consolidation** – Added `reference_power` field to PowerAuditResult and embedded `StatisticalParameters` and `ExtractionAuditReport` schemas under `$defs` in `contracts/power_audit_result.schema.yaml` (addresses plan_consistency‑3b665efa).  
- **CLI Power Analysis** – Removed per‑spec coverage decision (addresses spec_coverage‑3056fd7c).  

---




## projects/PROJ-234-assessing-statistical-power-in-reproduci/specs/001-assessing-statistical-power-in-reproduci/data-model.md

# Data Model: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Overview
All pipeline artifacts are stored under `projects/PROJ-234-assessing-statistical-power-in-reproduci/data/` and validated against JSON‑Schema files in `contracts/`. Immutable raw files reside in `raw/`; derived files in `processed/`. The **Single Source of Truth (SSoT)** for checksums, timestamps, and version hashes is `data/metadata.json`.

## 2. Entity Definitions

### 2.1 DatasetMetadata
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | OpenML identifier. |
| `name` | string | Human‑readable dataset name. |
| `download_count` | integer | Number of downloads on OpenML. |
| `publication_link` | string \| null | URL to primary publication (may be null). |
| `task_id` | integer \| null | Associated task ID (may be null). |
| `task_type` | string \| null | e.g., “Binary Classification”. |
| `class_distribution` | object \| null | Distribution of classes if available. |
| `downloaded_at` | string (date‑time) | ISO‑8601 timestamp of retrieval. |
| `oa_status` | string (`open_access` | `paywalled` | `no_link`) | Open Access status of the publication link. |
| `status` | string (`active` | `archived` | `unparseable`) | Pipeline status. |

### 2.2 StatisticalParameters
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | FK to `DatasetMetadata`. |
| `sample_size` | integer | Total N reported in the paper. |
| `effect_size` | number | Cohen’s d, F, or odds ratio (standardized). |
| `metric_type` | string (`Cohen's d` | `F` | `odds_ratio`) | Type of effect size. |
| `degrees_of_freedom` | object \| null | `{ "num": int, "den": int }` for F‑statistics. |
| `validation_status` | string (`valid` | `invalid_metric` | `ambiguous`) | Extraction quality flag. |
| `extraction_pass` | string (`full_text` | `abstract`) | Which source yielded the match. |
| `extraction_confidence` | string (`high` | `medium` | `low`) | Confidence based on match length. |
| `source_text_snippet` | string | Raw snippet that triggered extraction. |

### 2.3 PowerAuditResult
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | FK to `DatasetMetadata`. |
| `observed_power` | number (0‑1) | Observed statistical power from reported effect size. |
| `reference_power` | number (0‑1) | Power computed with the **test‑specific small‑effect benchmark** (d = 0.2, f = 0.2, log‑odds ≈ 0.2). |
| `target_power` | number | Power level used for a priori checks (default 0.8). |
| `threshold_met` | boolean | `True` if reference_power ≥ 0.8 (primary adequacy criterion). |
| `status` | string (`success` | `paywalled` | `unparseable` | `skipped`) | Outcome of the calculation. |
| `alpha` | number | Significance level used (default 0.05). |
| `test_type` | string (`t-test` | `anova` | `logistic`) | Statistical test assumed. |
| `weighted_power` | number (0‑1) \| null | Power after applying quintile weighting (optional). |
| `extraction_audit_report_path` | string | Path to the `ExtractionAuditReport` JSON (currently `reports/extraction_audit.json`). |

### 2.4 ExtractionAuditReport
| Field | Type | Description |
|---|---|---|
| `total_datasets` | integer | Number of datasets retrieved from OpenML. |
| `oa_count` | integer | Datasets with OA links. |
| `paywalled_count` | integer | Datasets with paywalled links. |
| `extraction_success_full_text` | integer | Successful extractions from full‑text. |
| `extraction_success_abstract` | integer | Successful extractions from abstract fallback. |
| `sensitivity_delta` | number | Difference in success rates (full – abstract). |
| `extraction_success_rate` | number (0‑1) | `successes / oa_count`. |
| `precision` | number (0‑1) | Precision on the validation set of papers. |
| `recall` | number (0‑1) | Recall on the validation set of papers. |
| `f1_score` | number (0‑1) | F1 on the validation set of papers. |

## 3. Data Flow Diagram
1. **Ingest** → `data/raw/openml_raw.json` (immutable).  
2. **Filter & OA Check** → `data/processed/filtered_datasets.csv` (validated against `DatasetMetadata` schema).  
3. **Parse** → `data/processed/statistical_params.json` (validated against `StatisticalParameters` schema).  
4. **Observed Power Compute** → `data/processed/observed_power.csv` (validated against `PowerAuditResult` schema, includes `reference_power`).  
5. **Extraction Audit Report** → `reports/extraction_audit.json` (conforms to `ExtractionAuditReport` definition).  
6. **Report** → `data/processed/audit_report.html` (visual + summary).  

All files have SHA‑256 checksums recorded in `data/metadata.json`.

## 4. Constraints
- **Immutability**: Files under `data/raw/` are never overwritten.  
- **Checksums**: Every artifact’s checksum is recorded; any mismatch fails CI.  
- **No PII**: OpenML metadata is assumed clean; no personal data is stored.  
- **OA‑Only**: Paywalled PDFs are not fetched; such entries are flagged `paywalled`.  

**Schema Availability**  
The schemas for `StatisticalParameters` and `ExtractionAuditReport` are defined within `contracts/power_audit_result.schema.yaml` under `$defs`. Contract tests reference these embedded definitions, satisfying the requirement that all intermediate files are validated against schemas in `contracts/`.

---




## projects/PROJ-234-assessing-statistical-power-in-reproduci/specs/001-assessing-statistical-power-in-reproduci/quickstart.md

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
#    count of studies with power < 0.8, and disclaimer about the post‑hoc power fallacy
python code/04_generate_report.py

# 5️⃣ Produce the extraction audit summary (JSON) containing success metrics,
#    sensitivity delta, and precision/recall/F1 (written to reports/extraction_audit.json)
python code/05_generate_audit_report.py
```

**Expected outputs**

| Step | Output file | Description |
|------|-------------|-------------|
| 01_ingest_openml.py | `data/raw/openml_raw.json` | Raw OpenML response (immutable). |
| 01_ingest_openml.py | `data/processed/filtered_datasets.csv` | Filtered list with OA status. |
| 02_parse_publications.py | `data/processed/statistical_params.json` | Extracted N & effect sizes. |
| 03_compute_observed_power.py | `data/processed/observed_power.csv` | Observed (and reference) power per dataset (validated against schema). |
| 04_generate_report.py | `data/processed/audit_report.html` | Histogram of raw power (20 bins, per verified bin count), count < 0.8, disclaimer. |
| 05_generate_audit_report.py | `reports/extraction_audit.json` | Extraction success metrics, sensitivity delta, precision/recall/F1 (validated against the embedded `ExtractionAuditReport` schema in `contracts/power_audit_result.schema.yaml`). |

## 4. Testing

```bash
pytest tests/
```

- **Unit tests** cover `api_client`, `oa_checker`, and `parsers`.  
- **Contract tests** validate that `filtered_datasets.csv`, `observed_power.csv`, `statistical_params.json`, and `extraction_audit.json` conform to their schemas **as defined in `contracts/power_audit_result.schema.yaml`** (the file now contains definitions for `StatisticalParameters` and `ExtractionAuditReport` under `$defs`).  
- **Integration test** (`tests/integration/test_full_pipeline.py`) runs the full pipeline on a deterministic 5‑dataset sample (seed = 42) and checks that the final report contains both raw and weighted power histograms.

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
| `test_api_client.py` fails (no `DataFetchError`) | `api_client` missing proper backoff/error handling | Updated `api_client.py` now raises `DataFetchError` after max retries (see T004 fix). |
| Empty `filtered_datasets.csv` | Incorrect filter logic | Filtering now uses `publication_link` **or** `task_id` (fixed for T005). |
| Schema validation error | Output file missing required field | Run `pytest tests/contract/` to see the exact missing field; fix the script to populate it. |
| Missing weighted summary | Weighting step omitted | Weighting has been removed per spec; raw power histograms are reported. |
| Missing `extraction_audit.json` | Audit step not executed | Run `05_generate_audit_report.py`; it creates the JSON per the data model. |

---




## projects/PROJ-234-assessing-statistical-power-in-reproduci/specs/001-assessing-statistical-power-in-reproduci/contracts/dataset_metadata.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "DatasetMetadata"
description: "Schema for OpenML dataset metadata extracted during ingestion."
type: "object"
properties:
  dataset_id:
    type: "integer"
    description: "Unique OpenML identifier."
  name:
    type: "string"
    description: "Human-readable dataset name."
  download_count:
    type: "integer"
    description: "Number of times downloaded."
  publication_link:
    type:
      - "string"
      - "null"
    description: "URL to the primary publication (may be null)."
  task_id:
    type:
      - "integer"
      - "null"
    description: "Associated task ID (may be null)."
  task_type:
    type:
      - "string"
      - "null"
    description: "e.g., 'Binary Classification', 'Multi-class'."
  class_distribution:
    type:
      - "object"
      - "null"
    description: "Distribution of classes if available."
  downloaded_at:
    type: "string"
    format: "date-time"
    description: "ISO 8601 timestamp of retrieval."
  oa_status:
    type: "string"
    enum:
      - "open_access"
      - "paywalled"
      - "no_link"
    description: "Open Access status of the publication link."
  status:
    type: "string"
    enum:
      - "active"
      - "archived"
      - "unparseable"
    description: "Status of the dataset entry."
required:
  - "dataset_id"
  - "name"
  - "download_count"
  - "downloaded_at"
  - "oa_status"
  - "status"
additionalProperties: false


## projects/PROJ-234-assessing-statistical-power-in-reproduci/specs/001-assessing-statistical-power-in-reproduci/contracts/power_audit_result.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "PowerAuditResult"
description: "Schema for the final calculated observed power audit results, including reference power and embedded definitions for related entities."
type: "object"
properties:
  dataset_id:
    type: "integer"
    description: "FK to DatasetMetadata."
  observed_power:
    type: "number"
    minimum: 0.0
    maximum: 1.0
    description: "Observed statistical power calculated from reported effect size."
  reference_power:
    type: "number"
    minimum: 0.0
    maximum: 1.0
    description: "Power computed with the test‑specific small‑effect benchmark (d = 0.2, f = 0.2, log‑odds ≈ 0.2)."
  target_power:
    type: "number"
    description: "Power level used for a priori checks (default 0.8)."
  threshold_met:
    type: "boolean"
    description: "True if reference_power ≥ 0.8 (primary adequacy criterion)."
  status:
    type: "string"
    enum:
      - "success"
      - "paywalled"
      - "unparseable"
      - "skipped"
    description: "Status of the calculation."
  alpha:
    type: "number"
    description: "Significance level used (default 0.05)."
  test_type:
    type: "string"
    enum:
      - "t-test"
      - "anova"
      - "logistic"
    description: "Type of statistical test performed."
  weighted_power:
    type: "number"
    minimum: 0.0
    maximum: 1.0
    description: "Power after applying quintile weighting (optional)."
required:
  - "dataset_id"
  - "observed_power"
  - "reference_power"
  - "target_power"
  - "threshold_met"
  - "status"
  - "alpha"
  - "test_type"
additionalProperties: false

$defs:
  StatisticalParameters:
    title: "StatisticalParameters"
    description: "Schema for extracted statistical parameters from publications."
    type: "object"
    properties:
      dataset_id:
        type: "integer"
        description: "FK to DatasetMetadata."
      sample_size:
        type: "integer"
        description: "Total N reported in the paper."
      effect_size:
        type: "number"
        description: "Cohen's d, F, or odds ratio (standardized)."
      metric_type:
        type: "string"
        enum:
          - "Cohen's d"
          - "F"
          - "odds_ratio"
        description: "Type of effect size."
      degrees_of_freedom:
        type: "object"
        nullable: true
        properties:
          num:
            type: "integer"
          den:
            type: "integer"
        required:
          - "num"
          - "den"
        description: "Degrees of freedom for F‑statistics."
      validation_status:
        type: "string"
        enum:
          - "valid"
          - "invalid_metric"
          - "ambiguous"
        description: "Extraction quality flag."
      extraction_pass:
        type: "string"
        enum:
          - "full_text"
          - "abstract"
        description: "Which source yielded the match."
      extraction_confidence:
        type: "string"
        enum:
          - "high"
          - "medium"
          - "low"
        description: "Confidence based on match length."
      source_text_snippet:
        type: "string"
        description: "Raw snippet that triggered extraction."
    required:
      - "dataset_id"
      - "sample_size"
      - "effect_size"
      - "metric_type"
    additionalProperties: false

  ExtractionAuditReport:
    title: "ExtractionAuditReport"
    description: "Schema for the JSON audit report summarising extraction performance and dataset characteristics."
    type: "object"
    properties:
      total_datasets:
        type: "integer"
      oa_count:
        type: "integer"
      paywalled_count:
        type: "integer"
      extraction_success_full_text:
        type: "integer"
      extraction_success_abstract:
        type: "integer"
      sensitivity_delta:
        type: "number"
      extraction_success_rate:
        type: "number"
        minimum: 0.0
        maximum: 1.0
      precision:
        type: "number"
        minimum: 0.0
        maximum: 1.0
      recall:
        type: "number"
        minimum: 0.0
        maximum: 1.0
      f1_score:
        type: "number"
        minimum: 0.0
        maximum: 1.0
    required:
      - "total_datasets"
      - "oa_count"
      - "paywalled_count"
      - "extraction_success_full_text"
      - "extraction_success_abstract"
      - "sensitivity_delta"
      - "extraction_success_rate"
      - "precision"
      - "recall"
      - "f1_score"
    additionalProperties: false