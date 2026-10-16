# Implementation Plan: Assessing Statistical Power in Reproducible Research with Public Datasets

**Branch**: `001-assess-statistical-power` | **Date**: 2026-10-15 | **Spec**: `specs/001-assess-statistical-power/spec.md`  
**Input**: Feature specification from `/specs/001-assess-statistical-power/spec.md`

## Summary
The pipeline will (1) ingest the top‑50 classification datasets from OpenML, (2) filter for entries with a non‑null `publication_link` **or** `task_id`, (3) verify Open‑Access status, (4) download OA full‑text (or abstract fallback) and extract sample size (N) and standardized effect size (Cohen’s d, F, or odds ratio) using validated regex/NLP, (5) compute **observed statistical power** for each study with the appropriate `statsmodels` routine (t‑test, ANOVA, or logistic‑regression approximation), (6) produce both **raw** and **quintile‑weighted** power summaries, (7) generate a comprehensive audit report containing a histogram of observed power, a count of studies with power < 0.8, the weighting details, and a mandatory disclaimer about the post‑hoc power fallacy, and (8) output an `ExtractionAuditReport` summarizing extraction success, sensitivity analysis, and dataset representativeness.

All steps are deterministic, produce schema‑validated artifacts, and run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `openml`, `requests`, `beautifulsoup4`, `pandas`, `statsmodels`, `matplotlib`, `pytest`  
- **Storage**: Local filesystem under `projects/PROJ-234-assessing-statistical-power-in-reproduci/` (`data/`, `code/`, `tests/`, `contracts/`)  
- **Testing**: `pytest` + contract validation against JSON‑Schema files in `contracts/`  
- **Target Platform**: Linux (GitHub Actions free tier) – a limited number of CPU cores, ≈ a few GB RAM, ≤ 6 h runtime  
- **Constraints**: CPU‑only, strict OpenML rate‑limit handling via `utils.api_client` (exponential backoff, `DataFetchError`), OA‑only publication access, immutable raw data, checksum‑driven data hygiene.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts pin `random.seed`, fetch data via the canonical OpenML API on every run, and write deterministic output files. |
| II. Verified Accuracy | No external citation is invented; all URLs come directly from OpenML metadata (verified by the platform). |
| III. Data Hygiene | Raw API responses stored under `data/raw/` are never overwritten; each file’s SHA‑256 checksum is recorded in **`data/metadata.json`** (the SSoT). |
| IV. Single Source of Truth | **`data/metadata.json`** is the authoritative SSoT for checksums, timestamps, and version hashes; every figure/table references a single row in `data/processed/` and the exact line in a script under `code/`. |
| V. Versioning Discipline | All artifacts (scripts, data files, schemas) are content‑hashed; the project state YAML is updated on each change. |
| VI. Statistical Power Transparency | Observed power is computed with `statsmodels.stats.power`, and both inputs and outputs are version‑controlled under `code/` and `data/`. |
| VII. Public Dataset Usage Integrity | Datasets are retrieved exclusively via the OpenML API; the exact query string and retrieval timestamp are saved in **`data/metadata.json`**. |

## Project Structure
```text
projects/PROJ-234-assessing-statistical-power-in-reproduci/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── 01_ingest_openml.py          # FR‑001, FR‑002, FR‑009 (uses utils.api_client)
│   ├── 02_parse_publications.py     # FR‑003, FR‑007, FR‑008
│   ├── 03_compute_observed_power.py # FR‑004, FR‑006 (observed & a‑priori power)
│   ├── 04_generate_report.py        # FR‑005, SC‑001, SC‑002, weighting
│   ├── 05_generate_audit_report.py  # generates ExtractionAuditReport (addresses FR‑008, FR‑009)
│   └── utils/
│       ├── api_client.py            # exponential backoff, DataFetchError
│       ├── oa_checker.py            # OA status detection
│       └── parsers.py               # regex/NLP extraction
├── data/
│   ├── raw/                          # OpenML JSON responses (immutable)
│   ├── processed/                    # filtered_datasets.csv, statistical_params.json,
│   │                                 # observed_power.csv, extraction_audit_report.json,
│   │                                 # audit_report.html
│   └── metadata.json                 # checksums & timestamps of all artifacts (SSoT)
├── tests/
│   ├── unit/
│   │   ├── test_api_client.py
│   │   ├── test_oa_checker.py
│   │   ├── test_parsers.py
│   │   └── test_schema_dataset_metadata.py
│   └── contract/
│       └── test_schema_power_audit.py
└── contracts/
    ├── dataset_metadata.schema.yaml
    └── power_audit_result.schema.yaml
```

## Mapping of Functional & Success Criteria to Plan Phases
| FR / SC | Phase / Script | Description |
|---------|----------------|-------------|
| FR‑001 | `01_ingest_openml.py` | Calls `utils.api_client.fetch_top_classification_datasets(limit=50)`. |
| FR‑002 | `01_ingest_openml.py` | Filters on `publication_link` **or** `task_id`. |
| FR‑003 | `02_parse_publications.py` | Uses `utils.parsers` to extract N and effect size from OA full‑text/abstract. |
| FR‑004 | `03_compute_observed_power.py` | Computes observed power via `statsmodels.stats.power` appropriate to the extracted `metric_type`. |
| FR‑005 | `04_generate_report.py` | Builds histogram of observed power, counts studies with power < 0.8, includes weighted summary, and adds disclaimer. |
| FR‑006 | `03_compute_observed_power.py` (CLI flag) | Provides `compute_apriori_power(sample_size, target_power=0.8)` for future study design. |
| FR‑007 | `02_parse_publications.py` | Validates that extracted `metric_type` is among allowed types; otherwise marks `invalid_metric`. |
| FR‑008 | `02_parse_publications.py` + `04_generate_report.py` | Computes sensitivity delta between full‑text‑only and full‑text + abstract extraction and reports it. |
| FR‑009 | `01_ingest_openml.py` + `04_generate_report.py` | Summarizes dataset type distribution (binary vs multi‑class) and source categories. |
| SC‑001 | `04_generate_report.py` | Reports extraction success rate; must be ≥ 0.6 (checked in report). |
| SC‑002 | `04_generate_report.py` | Reports proportion of studies with observed power < 0.8. |
| SC‑003 | Entire pipeline | Runtime measured via CI logs; must stay < 6 h. |
| SC‑004 | Entire pipeline | Memory usage logged; must stay < 7 GB. |

## Phase 0: Research & Validation (Deliverable `research.md`)
- **OA Availability Check**: Random sample of a modest number of OpenML datasets (expected OA consistent with literature).  
- **Extraction Validation**: Stratified random sample of **15** OA papers (A modest number per download‑count quintile). Compute **precision, recall, and F1** against manually verified ground truth; target **F1 ≥ 0.9**.  
- **Power Calculation Verification**: Confirm that observed power computed by `statsmodels` matches hand‑calculated examples (e.g., N = 100, d = 0.5, α = 0.05 → power ≈ 0.78).  

## Phase 1: Implementation (Deliverable `data-model.md`, `contracts/`)
1. **Ingest** – `01_ingest_openml.py` writes `data/raw/openml_raw.json` and `data/processed/filtered_datasets.csv`.  
2. **OA Check** – `utils.oa_checker` adds `oa_status`.  
3. **Parse** – `02_parse_publications.py` writes `data/processed/statistical_params.json`.  
4. **Compute Observed Power** – `03_compute_observed_power.py` writes `data/processed/observed_power.csv`.  
5. **Generate Audit Report** – `04_generate_report.py` writes `data/processed/audit_report.html` (raw and weighted power histograms, threshold counts, disclaimer).  
6. **Extraction Audit Report** – `05_generate_audit_report.py` writes `data/processed/extraction_audit_report.json` conforming to the `ExtractionAuditReport` entity defined in `data-model.md`.  

All intermediate files are validated against JSON‑Schema files in `contracts/` (unit‑test `test_schema_*.py`).

## Phase 2: Testing & Verification (Deliverable `quickstart.md`)
- Unit tests for each utility (including exponential backoff and `DataFetchError`).  
- Contract tests ensuring that `filtered_datasets.csv`, `observed_power.csv`, and `extraction_audit_report.json` conform to their schemas.  
- Integration test (`tests/integration/test_full_pipeline.py`) runs the full pipeline on a deterministic **seeded multiple‑dataset sample** and checks that the final report contains both raw and weighted power histograms.

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Low OA rate | Reduces usable N | Report OA percentage; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | `api_client` implements exponential backoff with jitter; max retries = 5. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches. |
| Sampling bias | Limited generalizability | Quintile weighting produces weighted summaries; both raw and weighted results are reported. |
| Schema mismatch | Verification failure | Contract tests run on every CI job; failures abort the run. |

## Decision Log
- **Observed Power over MDES** – Aligns with FR‑004, FR‑005, SC‑002 and avoids the scientifically unsound MDES ≤ 0.5 proxy (Constitution Principle VI).  
- **Project Path** – Adopted `projects/PROJ-234-assessing-statistical-power-in-reproduci/` to satisfy verifier’s directory‑tree requirement (T001).  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` for reliable error handling (T004).  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Weighting Scheme** – Quintile‑based inverse‑frequency weighting added to address sampling bias (methodology‑637bfdc4).  

---


