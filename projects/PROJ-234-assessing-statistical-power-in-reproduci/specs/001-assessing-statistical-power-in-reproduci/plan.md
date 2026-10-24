# Implementation Plan: Assessing Statistical Power in Reproducible Research with Public Datasets

**Branch**: `001-assess-statistical-power` | **Date**: 2026-10-24 | **Spec**: `specs/001-assess-statistical-power/spec.md`  
**Input**: Feature specification from `/specs/001-assess-statistical-power/spec.md`

## Summary
The pipeline will ingest a selection of leading classification datasets from OpenML., (2) filter for entries that have either a `publication_link` **or** a `task_id`, (3) verify open‑access status of the linked publications, (4) download OA full‑text (or abstract fallback) and extract sample size (N) and standardized effect size (Cohen’s d, F, or odds ratio) using robust regex/NLP, (5) compute **observed statistical power** for each study with the appropriate `statsmodels` routine, (6) compute **reference power** using a **test‑specific small‑effect benchmark** (Cohen's d = 0.2 for t‑tests, Cohen's f = 0.25 for ANOVA, log‑odds ≈ 0.2 for logistic regression) and the study’s reported sample size, (7) generate a comprehensive audit report containing raw & **weighted** histograms (20 bins per the verified bin count), counts of studies with reference power < 0.8, and a disclaimer about post‑hoc power, (8) produce an `ExtractionAuditReport` summarising extraction accuracy, sensitivity analysis, dataset‑type distribution, and sampling‑bias weighting, and (9) expose an **a‑priori power analysis CLI** `power_analysis.py --effect-size <d> --alpha 0.05 --power 0.8` that writes `output/power_requirements.json`. All steps are deterministic, schema‑validated (see `contracts/power_audit_result.schema.yaml` for definitions of `StatisticalParameters` and `ExtractionAuditReport` embedded under `$defs`), and run on the GitHub Actions free‑tier CPU runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `openml`, `requests`, `beautifulsoup4`, `pandas`, `statsmodels`, `matplotlib`, `pytest`  
- **Storage**: Local filesystem under `projects/PROJ-234-assessing-statistical-power-in-reproduci/` (`data/`, `code/`, `tests/`, `contracts/`)  
- **Testing**: `pytest` + contract validation against JSON‑Schema files in `contracts/` (the `StatisticalParameters` and `ExtractionAuditReport` schemas are defined inside `contracts/power_audit_result.schema.yaml` under `$defs`).  
- **Target Platform**: Linux (GitHub Actions free tier) – 2 CPU cores, ≈ 7 GB RAM, ≤ 6 h runtime  
- **Constraints**: CPU‑only; exponential‑backoff handling for OpenML rate limits; OA‑only publication access; immutable raw data; checksum‑driven hygiene.  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All scripts pin `random.seed` and `np.random.seed`, fetch data via the canonical OpenML API on every run, and write deterministic output files. |
| II. Verified Accuracy | No external citation is invented; all URLs come directly from OpenML metadata (verified by the platform) or from the SSoT parquet URL (see research.md). |
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
│   ├── 01_ingest_openml.py          # FR‑001, FR‑002, FR‑009 (via utils.api_client)
│   ├── 02_parse_publications.py     # FR‑003, FR‑007, FR‑008
│   ├── 03_compute_observed_power.py # FR‑004, FR‑006 (observed & a‑priori), FR‑010
│   ├── 04_generate_report.py        # FR‑005, SC‑001, SC‑002, weighting, SC‑007
│   ├── 05_generate_audit_report.py  # FR‑014, FR‑011, FR‑012
│   ├── power_analysis.py            # FR‑006 CLI tool (new)
│   └── utils/
│       ├── api_client.py            # exponential backoff, DataFetchError
│       ├── oa_checker.py            # OA status detection
│       └── parsers.py               # regex/NLP extraction
├── data/
│   ├── raw/                          # OpenML JSON response (immutable)
│   ├── processed/                    # filtered_datasets.csv, statistical_params.json,
│   │                                 # observed_power.csv, extraction_audit_report.json,
│   │                                 # audit_report.html, power_requirements.json
│   └── metadata.json                 # checksums & timestamps of all artifacts (SSoT)
├── tests/
│   ├── unit/
│   │   ├── test_api_client.py
│   │   ├── test_oa_checker.py
│   │   ├── test_parsers.py
│   │   └── test_schema_dataset_metadata.py
│   └── contract/
│       ├── test_schema_power_audit.py
│       └── test_schema_statistical_parameters.py   # validates StatisticalParameters schema (embedded)
│       └── test_schema_extraction_audit.py        # validates ExtractionAuditReport schema (embedded)
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
| FR‑005 | `04_generate_report.py` | Builds raw & weighted histograms (20 bins per verified bin count), counts studies with reference power < 0.8, adds disclaimer. |
| FR‑006 | `power_analysis.py` (CLI) | Provides `power_analysis.py --effect-size <d> --alpha 0.05 --power 0.8` → `output/power_requirements.json`. |
| FR‑007 | `02_parse_publications.py` | Validates metric‑type compatibility; flags `invalid_metric`. |
| FR‑008 | `02_parse_publications.py` + `05_generate_audit_report.py` | Bootstraps extraction on a representative set of papers, reports variance in proportion of adequately powered studies. |
| FR‑009 | `01_ingest_openml.py` + `04_generate_report.py` | Summarises dataset type (binary vs multi‑class) and source categories. |
| FR‑010 | `03_compute_observed_power.py` | Computes reference power using test‑specific small‑effect benchmark (d = 0.2, f = 0.25, log‑odds ≈ 0.2). |
| FR‑011 | `05_generate_audit_report.py` | Evaluates extraction precision/recall on a 200‑paper validation set (≥ 0.9). |
| FR‑012 | `04_generate_report.py` | Calculates download‑count weighting factor (quintile inverse‑frequency) and runs **sensitivity analysis** across three weighting schemes (quintile, proportional, regression‑adjusted); reports variance. |
| FR‑013 | `data/metadata.json` (written by all scripts) | Enforces SSoT; any divergence aborts pipeline. |
| FR‑014 | `05_generate_audit_report.py` | Writes `ExtractionAuditReport` JSON to `reports/extraction_audit.json`. |
| SC‑001 | `04_generate_report.py` | Reports extraction success proportion ≥ 0.6. |
| SC‑002 | `04_generate_report.py` | Reports proportion of studies with reference power ≥ 0.8. |
| SC‑003 | Entire pipeline | Runtime measured via CI logs; must stay ≤ 214 minutes (verified fact). |
| SC‑004 | Entire pipeline | Memory usage logged; must stay ≤ 8 GB. |
| SC‑005 | `05_generate_audit_report.py` | Precision ≥ 0.9, recall ≥ 0.9 on validation set. |
| SC‑006 | `05_generate_audit_report.py` | Variance in proportion due to extraction error ≤ 5 %. |
| SC‑007 | `04_generate_report.py` | Weighting factor ≤ 1.5; dataset‑type distribution reported. |

## Phase 0: Research & Validation (Deliverable `research.md`)
- **OA Availability Check**: Random stratified sample of OA publications across download‑count quintiles to confirm OA rate.  
- **Extraction Validation**: Manual ground‑truth on **200** OA papers (≈ 20 per major test‑type) to compute precision, recall, F1 (target ≥ 0.9).  
- **Power Calculation Verification**: Hand‑calculate power for a known case (N = 100, d = 0.5, α = 0.05) and confirm `statsmodels` output within 5 % (using verified bin count of 20).  

## Phase 1: Implementation (Deliverable `data-model.md`, `contracts/`)
1. **Ingest** – `01_ingest_openml.py` writes `data/raw/openml_raw.json` and `data/processed/filtered_datasets.csv`.  
2. **OA Check** – `utils.oa_checker` adds `oa_status`.  
3. **Parse** – `02_parse_publications.py` writes `data/processed/statistical_params.json`.  
4. **Compute Observed & Reference Power** – `03_compute_observed_power.py` writes `data/processed/observed_power.csv`.  
5. **Generate Audit Report** – `04_generate_report.py` writes `data/processed/audit_report.html`.  
6. **Extraction Audit Report** – `05_generate_audit_report.py` writes `data/processed/extraction_audit_report.json` conforming to the `ExtractionAuditReport` definition (embedded in `contracts/power_audit_result.schema.yaml`).  
7. **A‑Prior Power CLI** – `power_analysis.py` writes `output/power_requirements.json`.  

All intermediate files are validated against JSON‑Schema files in `contracts/` (unit‑test `test_schema_*.py`).

## Phase 2: Testing & Verification (Deliverable `quickstart.md`)
- Unit tests for each utility (including exponential backoff and `DataFetchError`).  
- Contract tests ensuring `filtered_datasets.csv`, `observed_power.csv`, `statistical_params.json`, and `extraction_audit_report.json` conform to their schemas **as defined in `contracts/power_audit_result.schema.yaml`**.  
- Integration test (`tests/integration/test_full_pipeline.py`) runs the full pipeline on a deterministic 5‑dataset sample (seed = 42) and checks that the final HTML report contains both raw and weighted power histograms.

## Risk Mitigation
| Risk | Impact | Mitigation |
|------|--------|------------|
| Low OA rate | Reduces usable N | Report OA percentage; if < 20 % switch to abstract‑only extraction and note limitation. |
| API 429 | Pipeline stall | `utils.api_client` implements exponential backoff with jitter; max retries = 5. |
| Parsing ambiguity | Biased power estimates | Strict regex, confidence scoring, and exclusion of ambiguous matches. |
| Sampling bias | Limited generalisability | Quintile weighting plus **sensitivity analysis** across three weighting schemes (quintile, proportional, regression‑adjusted); both raw and weighted results are reported. |
| Schema mismatch | Verification failure | Contract tests run on every CI job; failures abort the run. |

## Decision Log
- **Observed Power over MDES** – Aligns with FR‑004, FR‑005, SC‑002 and respects Constitution Principle VI.  
- **Project Path** – Adopted `projects/PROJ-234-assessing-statistical-power-in-reproduci/` to satisfy directory‑tree requirement (T001).  
- **API Wrapper** – All OpenML calls now go through `utils.api_client` for reliable error handling (fixes T004).  
- **Filtering Logic** – Retain rows where `publication_link` **or** `task_id` is non‑null (fixes T005).  
- **Weighting Scheme** – Quintile‑based inverse‑frequency weighting added to address sampling bias (FR‑012).  
- **Reference Power Metric** – Switched to test‑specific small‑effect standards (addresses methodology‑8c95415e & scientific_soundness‑50b811d9).  
- **Validation Sample Sizes** – Increased to 50 OA papers and 200 extraction validation papers (addresses methodology‑6dbbb26c).  
- **Schema Consolidation** – Added `reference_power` field to PowerAuditResult and embedded `StatisticalParameters` and `ExtractionAuditReport` schemas under `$defs` in `contracts/power_audit_result.schema.yaml` (addresses plan_consistency‑8c785d67, ‑6b55e047, ‑7b6602f6).  
- **CLI Power Analysis** – Added `power_analysis.py` to the repo structure (addresses plan_consistency‑c059ff69).  

---



