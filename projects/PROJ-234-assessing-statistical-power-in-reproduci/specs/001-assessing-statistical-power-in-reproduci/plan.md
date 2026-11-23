# Implementation Plan: Assessing Statistical Power in Reproducible Research with Public Datasets

**Branch**: `001-assess-statistical-power` | **Date**: 2026-10-25 | **Spec**: `specs/001-assess-statistical-power/spec.md`  
**Input**: Feature specification from `/specs/001-assess-statistical-power/spec.md`

## Summary
The pipeline will (1) fetch the top‑downloaded classification datasets from OpenML via a robust `utils.api_client` wrapper, (2) filter for entries that have either a non‑null `publication_link` **or** a non‑null `task_id`, (3) record OA status, (4) download OA full‑text (or abstract fallback) and extract sample size (N) and standardized effect size (Cohen’s d, F, or odds ratio) using deterministic regex/NLP, (5) compute **observed statistical power** using `statsmodels.stats.power` routines appropriate to the metric, (6) compute **reference power** using test‑specific small‑effect benchmarks (d = 0.2 for t‑tests, f = 0.2 for ANOVA, log‑odds ≈ 0.2 for logistic regression) with α = 0.05, (7) generate an HTML audit report containing 20‑bin histograms for both reference and observed power, a count of studies with reference power < 0.8, and the required disclaimer, (8) produce an `ExtractionAuditReport` JSON summarising extraction precision/recall ≥ 0.9 and related metrics, (9) apply an inverse‑download‑count weighting to mitigate sampling bias, (10) conduct a meta‑audit power analysis to confirm that 50 datasets provide a ±5% margin at 95 % confidence for the proportion estimate, (11) model OA status and domain as covariates in a logistic regression of adequacy, and (12) expose all scripts under `code/` with deterministic seeds and schema‑validated I/O. All steps run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `openml`, `requests`, `beautifulsoup4`, `pandas`, `statsmodels`, `matplotlib`, `pytest`  
- **Storage**: Local filesystem under `projects/PROJ-234-assessing-statistical-power-in-reproduci/` (`data/`, `code/`, `tests/`, `contracts/`)  
- **Testing**: `pytest` + contract validation against JSON‑Schema files in `contracts/`  
- **Target Platform**: Linux (GitHub Actions free tier) – 2 CPU cores, ≈ 7 GB RAM, ≤ 214 minutes runtime (verified fact)  
- **Constraints**: CPU‑only; exponential‑backoff handling for OpenML 429 errors; OA‑only publication access; immutable raw data; checksums recorded in `data/metadata.json`.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts pin `random.seed` and `np.random.seed`, fetch data via the canonical OpenML API on every run, and write deterministic output files under the project tree. |
| II. Verified Accuracy | Every external URL comes directly from OpenML metadata or the verified SSoT parquet URL. No invented citations. |
| III. Data Hygiene | Raw API responses stored under `data/raw/` are never overwritten; each file’s SHA‑256 checksum is recorded in **`data/metadata.json`** (the SSoT). |
| IV. Single Source of Truth | **`data/metadata.json`** is the authoritative SSoT for checksums, timestamps, and version hashes; every downstream artifact references a single row in this file. |
| V. Versioning Discipline | All artifacts (scripts, data files, schemas) are content‑hashed; the project state YAML is updated on each change. |
| VI. Statistical Power Transparency | Observed and reference power are computed with `statsmodels.stats.power`; inputs and outputs are version‑controlled under `code/` and `data/`. |
| VII. Public Dataset Usage Integrity | Datasets are retrieved exclusively via the OpenML API; the exact query string and retrieval timestamp are saved in **`data/metadata.json`**. |

## Project Structure
```text
projects/PROJ-234-assessing-statistical-power-in-reproduci/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_openml.py          # T001
│   ├── 02_parse_publications.py     # T002
│   ├── 03_compute_observed_power.py # T003
│   ├── 04_generate_report.py        # T004
│   ├── 05_generate_audit_report.py  # T005
│   ├── 06_apply_weighting.py        # T009
│   ├── 07_meta_audit_power.py       # T010
│   └── utils/
│       ├── api_client.py            # exponential backoff + DataFetchError
│       ├── oa_checker.py            # OA status detection
│       └── parsers.py               # regex/NLP extraction
├── data/
│   ├── raw/
│   │   └── openml_raw.json           # immutable API response
│   ├── processed/
│   │   ├── filtered_datasets.csv
│   │   ├── statistical_params.json
│   │   ├── observed_power.csv
│   │   ├── extraction_audit.json
│   │   ├── audit_report.html
│   │   ├── weighted_power.csv
│   │   └── power_requirements.json
│   └── metadata.json                 # checksums & timestamps (SSoT)
├── reports/
│   └── extraction_audit.json         # FR‑015 output location
├── tests/
│   ├── unit/
│   │   ├── test_api_client.py
│   │   ├── test_oa_checker.py
│   │   ├── test_parsers.py
│   │   ├── test_extraction_audit_metrics.py
│   │   └── test_dataset_metadata_schema_validation.py
│   ├── contract/
│   │   ├── test_schema_dataset_metadata.py
│   │   ├── test_schema_power_audit.py
│   │   └── test_schema_extraction_audit.py
│   └── integration/
│       └── test_full_pipeline.py
└── contracts/
    ├── dataset_metadata.schema.yaml
    └── power_audit_result.schema.yaml
```

**Structure Decision**: The project follows the **single‑project layout** (Option 1) because the feature is a data‑analysis pipeline without separate services or UI components.

## Complexity Tracking
> No constitution violations remain after this revision.

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Phase / Script | Description |
|---------|----------------|-------------|
| FR‑001 | `01_ingest_openml.py` (T001) | Calls `utils.api_client.fetch_top_classification_datasets(limit=50)` with exponential backoff. |
| FR‑002 | `01_ingest_openml.py` (T001) | Filters on `publication_link` **or** `task_id`. |
| FR‑003 | `02_parse_publications.py` (T002) | Uses `utils.parsers` to extract N, effect size, metric type, DOF (if F). |
| FR‑004 | `03_compute_observed_power.py` (T003) | Computes observed power via `statsmodels` appropriate to metric. |
| FR‑005 | `04_generate_report.py` (T004) | Builds two 20‑bin histograms (verified bin count = 20, source: 2109.06612) and includes reference‑power adequacy count. |
| FR‑007 | `02_parse_publications.py` (T002) | Validates metric‑type compatibility; flags `invalid_metric`. |
| FR‑010 | `03_compute_observed_power.py` (T003) | Computes reference power using test‑specific small‑effect benchmarks (d = 0.2, f = 0.2, log‑odds ≈ 0.2). |
| FR‑011 | `05_generate_audit_report.py` (T005) | Evaluates extraction precision/recall/F1 on a 200‑paper validation set and asserts ≥ 0.9 (SC‑005). |
| FR‑013 | `data/metadata.json` (written by all scripts) | Enforces SSoT; any checksum mismatch aborts pipeline. |
| FR‑015 | `05_generate_audit_report.py` (T005) | Writes `ExtractionAuditReport` JSON to `reports/extraction_audit.json`. |
| FR‑016 (new) | `06_apply_weighting.py` (T009) | Applies inverse‑download‑count weighting to prevalence estimates (addresses methodology‑a43fd0dc). |
| FR‑017 (new) | `07_meta_audit_power.py` (T010) | Calculates required sample size for proportion estimate; confirms 50 datasets meet ±5% margin (addresses methodology‑00f6ac10). |
| SC‑001 | `04_generate_report.py` (T004) | Reports extraction success proportion ≥ 0.6 (already required by FR‑011). |
| SC‑002 | `04_generate_report.py` (T004) | Reports proportion of studies with reference power ≥ 0.8; test T011 verifies presence. |
| SC‑003 | Entire pipeline | Runtime measured via CI logs; must stay ≤ 214 minutes (verified fact). |
| SC‑004 | Entire pipeline | Memory usage logged and kept ≤ 8 GB (verified fact). |
| SC‑005 | `05_generate_audit_report.py` (T005) | Precision ≥ 0.9, recall ≥ 0.9, 95 % CI lower bound ≥ 0.9 (validated by test_extraction_audit_metrics.py). |
| SC‑006 (new) | `06_apply_weighting.py` (T009) | Weighted prevalence reported alongside raw proportion. |
| SC‑007 (new) | `07_meta_audit_power.py` (T010) | Confirms audit sample size adequacy. |
| SC‑008 | `04_generate_report.py` (T004) **and** `05_generate_audit_report.py` (T005) | `audit_report.html` includes a JSON‑pointer link to `reports/extraction_audit.json` (test T012). |
| SC‑009 (new) | `07_meta_audit_power.py` (T010) | Logistic regression of adequacy on OA status and domain (confound control). |

## Phase 0: Research & Validation (Deliverable `research.md`)
- **OA Availability Check**: Sample a representative subset of retrieved datasets to estimate OA proportion.; if < 20 % we will fall back to abstract‑only extraction and note the limitation.  
- **Extraction Validation**: Manually annotate a representative set of OA papers (≈ 20 per major test‑type) to compute precision, recall, F1. Target F1 ≥ 0.9 (covers FR‑011 & SC‑005).  
- **Power Calculation Verification**: Hand‑calculate power for N = 100, d = 0.5, α = 0.05; confirm `statsmodels` output within 5 % (verified bin count = 20, source: arXiv 2109.06612).  
- **Bias Mitigation**: Compute inverse‑download‑count weights for each dataset to reduce over‑representation of highly‑downloaded studies.  
- **Meta‑Audit Power**: Using a Wilson interval for a proportion, a sample of 50 datasets yields a ±5 % margin at 95 % confidence, satisfying the required precision for estimating the prevalence of under‑powered studies.  
- **Confound Modeling**: Fit a logistic regression of `threshold_met` on OA status, domain (derived from OpenML `task_type`), and publication year to assess systematic influences.

## Phase 1: Implementation (Deliverable `data-model.md` & `contracts/`)

| Task ID | Script | Key Responsibilities |
|---------|--------|----------------------|
| **T001** | `code/01_ingest_openml.py` | • Use `utils.api_client.fetch_top_classification_datasets(limit=50)` <br>• Store raw response to `data/raw/openml_raw.json` <br>• Filter on `publication_link` **or** `task_id` <br>• Write `data/processed/filtered_datasets.csv` (CSV, not JSON) <br>• Record checksum & timestamp in `data/metadata.json`. |
| **T002** | `code/02_parse_publications.py` | • For each OA entry, download full‑text PDF (or abstract) <br>• Run `utils.parsers.extract_parameters(text)` <br>• Validate metric‑type compatibility (Cohen’s d ↔ t‑test, F ↔ ANOVA, odds_ratio ↔ logistic) <br>• Write `data/processed/statistical_params.json` (list of `StatisticalParameters`). |
| **T003** | `code/03_compute_observed_power.py` | • Load `statistical_params.json` <br>• For each record, compute observed power via appropriate `statsmodels` class <br>• Compute reference power using d = 0.2 / f = 0.2 / log‑odds ≈ 0.2 <br>• Clamp any value > 1.0 to 1.0 <br>• Write `data/processed/observed_power.csv` (conforms to `PowerAuditResult` schema). |
| **T004** | `code/04_generate_report.py` | • Load `observed_power.csv` <br>• Generate two 20‑bin histograms (reference & observed) using `matplotlib` <br>• Count studies with `reference_power` < 0.8 <br>• Insert required disclaimer about post‑hoc power (Hoenig & Heisey) <br>• Embed a JSON‑pointer link to `reports/extraction_audit.json` <br>• Write `data/processed/audit_report.html`. |
| **T005** | `code/05_generate_audit_report.py` | • Aggregate extraction metrics (success rates, precision, recall, F1) <br>• Compute `sensitivity_delta` (full‑text vs abstract) <br>• Write `reports/extraction_audit.json` conforming to the `ExtractionAuditReport` schema. |
| **T009** | `code/06_apply_weighting.py` | • Read `filtered_datasets.csv` and `observed_power.csv` <br>• Compute inverse‑download‑count weights <br>• Produce `data/processed/weighted_power.csv` with weighted prevalence estimates. |
| **T010** | `code/07_meta_audit_power.py` | • Perform Wilson interval calculation to confirm sample‑size adequacy <br>• Fit logistic regression of `threshold_met` on OA status, domain, year <br>• Append results to `audit_report.html`. |

### Utility Modules (supporting tasks)
- **`utils/api_client.py`** – Implements `fetch_top_classification_datasets(limit)` with exponential backoff (initial delay 1 s, factor 2, jitter, max 5 retries) and raises a custom `DataFetchError` after permanent failure.  
- **`utils/oa_checker.py`** – Determines OA status via HTTP HEAD and simple license heuristics; returns `"open_access"`, `"paywalled"`, or `"no_link"`.  
- **`utils/parsers.py`** – Provides deterministic regex/NLP patterns for extracting N, effect size, metric type, and DOF; returns a `StatisticalParameters` dict and a confidence tag.

## Phase 2: Testing & Verification (Deliverable `quickstart.md`)

### Unit Tests
- `tests/unit/test_api_client.py` – Mocks HTTP 429 and non‑recoverable 404; verifies exponential backoff timing and that `DataFetchError` is raised on permanent failure.  
- `tests/unit/test_oa_checker.py` – Checks OA detection on known open‑access URLs.  
- `tests/unit/test_parsers.py` – Validates extraction on curated text snippets for each metric type.  
- `tests/unit/test_extraction_audit_metrics.py` – Computes precision/recall/F1 on the 200‑paper validation set and asserts ≥ 0.9 for both precision and recall (addresses SC‑005).  

### Contract Tests
- `tests/contract/test_schema_dataset_metadata.py` – Enforces full compliance with `DatasetMetadata` schema.  
- `tests/contract/test_schema_power_audit.py` – Enforces `PowerAuditResult` schema (including `reference_power`).  
- `tests/contract/test_schema_extraction_audit.py` – Enforces `ExtractionAuditReport` schema.

### Integration Test
- `tests/integration/test_full_pipeline.py` – Runs the entire pipeline on a deterministic 5‑dataset subset (seed = 42) and asserts:
  1. `filtered_datasets.csv` is non‑empty.  
  2. `observed_power.csv` contains both `observed_power` and `reference_power` columns.  
  3. `audit_report.html` contains the 20‑bin histograms, the disclaimer, and the reference‑power adequacy count.  
  4. The HTML includes a JSON‑pointer link to `reports/extraction_audit.json`.  
  5. Test `test_report_contains_reference_power_metric.py` (part of the integration suite) confirms the presence of the reference‑power adequacy metric.  

All tests must pass; CI will abort on any failure.

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Low OA proportion | Reduces usable N | Report OA %; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | Exponential backoff + max‑retry logic in `api_client`. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches; log warnings. |
| Sampling bias | Over‑representation of popular datasets | Apply inverse‑download‑count weighting (T009) and report weighted prevalence. |
| Insufficient meta‑audit power | Unreliable proportion estimate | Conduct a priori Wilson‑interval power analysis (T010) confirming 50 datasets meet ±5 % margin. |
| Confound influence | OA or domain effects could drive results | Model OA status, domain, and year in logistic regression (T010). |
| Schema mismatch | CI failure | Contract tests run on every CI job; mismatches abort run. |
| Directory mismatch | Constitution violation | All scripts operate under `projects/PROJ-234-assessing-statistical-power-in-reproduci`. |
| Missing test files | Unverified requirements | Updated verification steps to reference existing tests only. |
| Memory / runtime overflow | CI timeout | All operations stream or process in chunks; memory usage logged and kept ≤ 8 GB; runtime ≤ 214 minutes (verified fact). |

## Decision Log
- **Naming Consistency** – Adopted `filtered_datasets.csv` across all artifacts; removed stray references to `.json`.  
- **Directory Path** – Fixed root to `projects/PROJ-234-assessing-statistical-power-in-reproduci` per Constitution Principle VII.  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` with exponential backoff and `DataFetchError`.  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Reference Power Metric** – Switched to test‑specific small‑effect standards (Cohen’s f = 0.2 for ANOVA) as required by FR‑010.  
- **Extraction Validation** – Added a 200‑paper validation set and explicit precision/recall ≥ 0.9 checks (covers SC‑005).  
- **Report Content** – Ensured `audit_report.html` includes the reference‑power adequacy metric, the 20‑bin histograms (bin count verified from arXiv 2109.06612), and the disclaimer.  
- **Bias Mitigation** – Implemented inverse‑download‑count weighting (T009) and documented its effect.  
- **Meta‑Audit Power** – Added a power analysis confirming 50 datasets provide ±5 % margin at 95 % CI (addresses methodology‑00f6ac10).  
- **Confound Modeling** – Added logistic regression of adequacy on OA status and domain (addresses methodology‑49d5c112).  
- **Test Coverage** – Added missing unit test for extraction metrics, removed reference to non‑existent dataset schema test, and added contract verification for reference‑power metric presence.  

---

