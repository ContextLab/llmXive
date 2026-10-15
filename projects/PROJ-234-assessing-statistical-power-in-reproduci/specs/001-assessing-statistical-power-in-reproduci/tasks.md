# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and all contract schemas.  
All tasks are expressed as markdown checklist items following the canonical  

```
- [ ] T### [P?] [USx?] description … with exact artifact paths
```  

Tasks that can run in parallel are marked **[P]**.  Verification steps are
indented beneath each headline.  The list contains 14 substantive tasks that
cover the entire end‑to‑end study while satisfying every scientific requirement
in the specification.

---  

## Phase 1 – Project scaffolding & core configuration  

- [ ] T001 [P] Create the project directory tree and placeholder `.gitkeep` files.  
  ```
  projects/PROJ-001-assessing-statistical-power/
      code/
          __init__.py
          utils/
      data/
          raw/
          processed/
      tests/
          unit/
          integration/
      docs/
      contracts/
  ```  
  **Verify** – each directory exists (`test -d <dir>`) and contains a `.gitkeep` file.

- [ ] T002 [P] Add `requirements.txt` and `config.yaml` with runtime limits.  
  `requirements.txt` (exact versions):  
  ```
  pandas==2.0.3
  scipy==1.11.4
  statsmodels==0.14.1
  requests==2.31.0
  matplotlib==3.8.0
  beautifulsoup4==4.12.2
  numpy==1.26.0
  pyyaml==6.0
  ```  
  `config.yaml` stores limits required by the spec:  
  ```yaml
  limits:
    max_runtime_hours: 6
    max_memory_gb: 7
  ```  
  **Verify** – `pip install -r requirements.txt --dry-run` succeeds; `yaml.safe_load` on `config.yaml` returns a dict with the two keys.

- [ ] T003 [P] Populate `contracts/` with the four JSON‑Schema files required for contract testing.  
  ```
  contracts/dataset_metadata.schema.yaml          # provided in spec
  contracts/power_audit_result.schema.yaml       # provided in spec
  contracts/extracted_params.schema.yaml         # defines StatisticalParameters object
  contracts/report.schema.yaml                   # defines final audit_report.json structure
  ```  
  **Verify** – each file exists, parses without error (`jsonschema.Draft7Validator`), and `yamllint` reports no issues.

---  

## Phase 2 – Core utility library (single module group)  

- [ ] T004 Implement reusable utilities in `code/utils/` and unit‑test them.  
  * `api_client.py` – thin wrapper around the OpenML REST API with exponential‑backoff retry for HTTP 429 (configurable retries, initial delay, max delay).  
  * `oa_checker.py` – function `is_open_access(url: str) -> bool` that recognises known OA domains (`arxiv.org`, `doi.org/10.`, `pubmedcentral.nih.gov`) and validates the `Content‑Type` header.  
  * `parsers.py` – streaming‑friendly extraction helpers:  
    - `extract_sample_size(text: str) -> int` (regex `r"N\s*=\s*(\d+)"`).  
    - `extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]` (regexes for Cohen’s d and F‑statistics, returning metric type and optional DOF).  
  * All utilities raise a custom `DataFetchError` on any failure; no silent fall‑backs.  
  **Unit tests** in `tests/unit/` (`test_api_client.py`, `test_oa_checker.py`, `test_parsers.py`) assert correct retry behaviour, OA detection, and regex extraction on synthetic strings.  
  **Verify** – all unit tests pass (`pytest -q tests/unit`).

---  

## Phase 3 – Data ingestion (User Story 1)  

- [ ] T005 Implement `code/01_ingest_openml.py` to fetch, filter, and store OpenML metadata.  
  1. Use `api_client` to request the **top 50 most‑downloaded classification datasets**.  
  2. Filter for entries with a non‑null `publication_link` **or** `task_id`.  
  3. Write the raw API response to `data/raw/openml_metadata_raw.json`.  
  4. Write the filtered list to `data/processed/filtered_datasets.json` (conforms to `contracts/dataset_metadata.schema.yaml`).  
  5. Generate SHA‑256 checksums for both files and append them to `data/processed/checksum_manifest.json`.  
  6. Emit a short log `data/ingest.log` with total fetched, filtered, and classification‑type counts.  
  **Verification** – a contract test `tests/unit/test_dataset_metadata_schema.py` loads `data/processed/filtered_datasets.json` and validates it against the schema; the test must pass.

---  

## Phase 4 – Publication parsing & statistical‑parameter extraction (User Story 2)  

- [ ] T006 Implement `code/02_parse_publications.py` to extract N and effect sizes.  
  * Iterate over `data/processed/filtered_datasets.json`.  
  * For each entry:  
    1. Call `oa_checker.is_open_access`; if `False`, record status `"paywalled"` and continue.  
    2. Download the full‑text (or abstract if full‑text unavailable) via `requests.get` with a 10 s timeout; raise `DataFetchError` on failure.  
    3. Stream the text in ≤ 500 KiB chunks to the parsers from T004.  
    4. On success, emit a JSON object adhering to `contracts/extracted_params.schema.yaml` and write it (line‑delimited) to `data/processed/extracted_params.jsonl`.  
    5. On failure, record status `"unparseable"` and note the attempted source (`full_text` or `abstract`).  
  * After the loop, write summary statistics to `data/processed/extraction_stats.json` (counts of successes, failures, paywalled, abstract‑fallback).  
  * Compute the **sensitivity delta** (full‑text success – (full‑text + abstract) success) and store in `data/processed/sensitivity_delta.json`.  
  **Verification** – a contract test `tests/unit/test_extracted_params_schema.py` validates each line of `extracted_params.jsonl` against its schema; the test must pass.

---  

## Phase 5 – MDES (Minimum Detectable Effect Size) computation (User Story 3)  

- [ ] T007 Implement `code/03_compute_mdes.py` to calculate MDES and related metrics.  
  1. Read `data/processed/extracted_params.jsonl`.  
  2. Convert any F‑statistics to Cohen’s d using the standard conversion formula (requires DOF).  
  3. For each entry, use `statsmodels.stats.power.TTestIndPower` (or `FTestAnovaPower` when appropriate) to:  
     - Compute **observed power** (for reference).  
     - Solve for **MDES** that would achieve the target power `0.8` at `α=0.05`.  
  4. Clamp observed power to ≤ 1.0 and log a warning if clamping occurs.  
  5. Write results to `data/processed/power_audit_results.jsonl` matching `contracts/power_audit_result.schema.yaml`.  
  6. Aggregate:  
     - Fraction of studies with observed power < 0.8 (`SC‑002`).  
     - Fraction with MDES ≤ 0.5 (example adequacy threshold).  
     - Dataset‑type distribution (binary vs. multi‑class) derived from ingestion metadata.  
     Store aggregates in `data/processed/summary_metrics.json`.  
  **Verification** – a unit test `tests/unit/test_compute_mdes.py` runs the core function on a synthetic record (`N=100, d=0.2`) and asserts observed power ≈ 0.30 ± 0.05 and MDES ≈ 0.25 ± 0.05; a contract test `tests/unit/test_power_audit_schema.py` validates the JSONL file against its schema.

---  

## Phase 6 – Visualisation & reporting (User Story 3, FR‑005)  

- [ ] T008 Produce figures and the final audit report.  
  * Using `matplotlib`, generate:  
    - `data/processed/power_histogram.png` (observed power distribution).  
    - `data/processed/mdes_histogram.png` (MDES distribution).  
  * Summarise MDES statistics (median, IQR) in `data/processed/mdes_summary.json`.  
  * Assemble a markdown report `data/processed/audit_report.md` containing:  
    - Overview & methodology brief.  
    - Ingestion summary (counts, type distribution).  
    - Extraction statistics (including sensitivity delta).  
    - Power results (embed `power_histogram.png`, report fraction < 0.8).  
    - MDES results (embed `mdes_histogram.png`, median/IQR, adequacy fraction).  
    - Mandatory disclaimer: “Observed power is a monotone function of the p‑value and should not be used for post‑hoc validation (Hoenig & Heisey).”  
  * Export a machine‑readable version `data/processed/audit_report.json` mirroring the markdown sections.  
  **Verification** – a contract test `tests/unit/test_report_schema.py` validates `audit_report.json` against `contracts/report.schema.yaml`; a quick grep confirms the disclaimer text appears in `audit_report.md`.

---  

## Phase 7 – Reproducible execution & verification  

- [ ] T009 Create user‑facing documentation and a pipeline wrapper.  
  * `docs/quickstart.md` – lists prerequisites, `pip install -r requirements.txt`, the command `./run_pipeline.sh`, and the expected SHA‑256 checksum of `data/processed/audit_report.md`.  
  * `run_pipeline.sh` (executable) runs the four stages in order:  
    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    python code/01_ingest_openml.py
    python code/02_parse_publications.py
    python code/03_compute_mdes.py
    python code/04_generate_report.py   # (generated in T008)
    ```  
  **Verification** – an integration test `tests/integration/test_quickstart_checksum.py` executes `./run_pipeline.sh` on a tiny subset (environment variable `MAX_DATASETS=5`), computes the SHA‑256 of `audit_report.md`, and asserts it matches the value recorded in `quickstart.md`.

---  

## Phase 8 – Robustness, performance limits & provenance  

- [ ] T010 Add runtime‑ and memory‑limit enforcement plus performance harness.  
  * Each pipeline script (`01_…`, `02_…`, `03_…`, `04_…`) reads `config.yaml` and aborts with a clear `RuntimeError` if wall‑clock time exceeds `max_runtime_hours` or RSS exceeds `max_memory_gb`.  
  * New script `code/performance_harness.py` runs the full pipeline while measuring elapsed seconds (via `/usr/bin/time -v`) and peak RSS (`memory_profiler`).  Results are written to `data/processed/performance_metrics.json`.  
  **Verification** – a unit test `tests/unit/test_performance_harness.py` runs the harness on a synthetic tiny dataset and checks that the JSON contains the three required keys with numeric values.

- [ ] T011 Maintain a central checksum manifest.  
  * Every pipeline stage appends an entry to `data/processed/checksum_manifest.json` of the form:  
    ```json
    { "input": "<path>", "output": "<path>", "sha256": "<hash>" }
    ```  
  * A unit test `tests/unit/test_checksum_manifest.py` modifies a source file, re‑runs the relevant stage, and asserts that the manifest entry’s hash changes accordingly.  
  **Verification** – test must pass.

---  

## Phase 9 – Minor clean‑up (optional but recommended)  

- [ ] T012 Refactor `code/utils/` to avoid duplicate code: consolidate OA logic into `code/utils/open_access.py` and ensure all scripts import the unified helper. Run `flake8` to confirm no circular imports.  
  **Verify** – `flake8` exits with status 0 and a grep for `import oa_checker` shows no remaining references.

---  

### Dependency mapping (for quick reference)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑002, FR‑009 | T005 |
| FR‑003, FR‑007, FR‑008 | T006 |
| FR‑004, FR‑005, SC‑001, SC‑002 | T007, T008 |
| FR‑006 (a‑priori) | T008 (report includes MDES) |
| FR‑009 (type distribution) | T007 |
| Contract validation | T003, T004, T005‑T008, T010‑T011 |
| Performance limits | T010 |
| Reproducibility (quickstart) | T009 |
| Checksum provenance | T011 |
| Utils refactor | T012 |

---  

*All tasks are currently unchecked (`[ ]`).  Once a task’s verification step passes, the corresponding checkbox can be marked as completed.*
