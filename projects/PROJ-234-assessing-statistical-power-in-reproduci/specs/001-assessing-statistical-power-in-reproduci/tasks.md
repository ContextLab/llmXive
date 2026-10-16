# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas in `contracts/`.  
All tasks are expressed as markdown checklist items following the canonical  

```
- [ ] T### [P?] [USx?] description … with exact artifact paths
```  

Verification steps are indented beneath each headline.  
The list contains **14** substantive tasks that together implement the complete
end‑to‑end audit while satisfying every functional requirement in the
specification and the project constitution.

---  

## Phase 1 – Project scaffolding & core configuration  

- [ ] T001 Create the project directory tree and placeholder `.gitkeep` files.  
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

- [X] T002 Add `requirements.txt` with exact versions and a `config.yaml` that stores runtime limits.  
  `requirements.txt` (excerpt):  
  ```
  pandas==2.2.2
  numpy==1.26.4
  scipy==1.13.0
  statsmodels==0.14.2
  requests==2.32.3
  beautifulsoup4==4.12.3
  pyyaml==6.0.1
  tqdm==4.66.5
  ```  
  `config.yaml` (excerpt):  
  ```yaml
  limits:
    max_runtime_hours: 6
    max_memory_gb: 7
  ```  
  **Verify** – `pip install -r requirements.txt --dry-run` succeeds; `yaml.safe_load("config.yaml")` returns a dict containing `limits.max_runtime_hours` and `limits.max_memory_gb`.

- [X] T003 Populate the `contracts/` directory with the four JSON‑Schema/YAML files required for contract testing.  
  ```
  contracts/dataset_metadata.schema.yaml          # supplied in spec
  contracts/power_audit_result.schema.yaml       # supplied in spec
  contracts/extracted_params.schema.yaml         # defines StatisticalParameters
  contracts/report.schema.yaml                   # defines final audit_report.json structure
  ```  
  **Verify** – each file parses without error (`yaml.safe_load`) and passes `jsonschema.Draft7Validator` against a minimal valid instance.

---  

## Phase 2 – Core utility library (single module group)  

- [ ] T004 Implement reusable utilities in `code/utils/` and unit‑test them.  
  * `api_client.py` – thin wrapper around the OpenML REST API with exponential‑backoff retry for HTTP 429 (configurable `max_retries`, `initial_delay`, `max_delay`).  
  * `oa_checker.py` – `is_open_access(url: str) -> bool` recognises known OA domains (`arxiv.org`, `doi.org/10.`, `pubmedcentral.nih.gov`) and validates the `Content‑Type` header.  
  * `parsers.py` – extraction helpers:  
    - `extract_sample_size(text: str) -> int` (regex `r"N\s*=\s*(\d+)"`).  
    - `extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]` (regexes for Cohen’s d and F‑statistics, returning metric type and optional DOF).  
  * All utilities raise a custom `DataFetchError` on failure; no silent fall‑backs.  
  **Verification** – run `pytest -q tests/unit/` and ensure all three unit tests (`test_api_client.py`, `test_oa_checker.py`, `test_parsers.py`) pass.

---  

## Phase 3 – Data ingestion (User Story 1)  

- [ ] T005 Implement `code/01_ingest_openml.py` to fetch, filter, and store OpenML metadata.
  1. Use `api_client` to request the **top 50 most‑downloaded classification datasets** (`openml.datasets.list` with appropriate filters).  
  2. Filter for entries with a non‑null `publication_link` **or** `task_id`.  
  3. Write the raw API response to `data/raw/openml_metadata_raw.json`.  
  4. Write the filtered list to `data/processed/filtered_datasets.json` (conforms to `contracts/dataset_metadata.schema.yaml`).  
  5. Generate SHA‑256 checksums for both files and append them to `data/processed/checksum_manifest.json`.  
  6. Emit a short log `data/ingest.log` with totals.  
  **Verification** – `tests/unit/test_dataset_metadata_schema.py` loads `data/processed/filtered_datasets.json` and validates each record against `contracts/dataset_metadata.schema.yaml`; the test must pass.

---  

## Phase 4 – Publication parsing & statistical‑parameter extraction (User Story 2)  

- [ ] T006 Implement `code/02_parse_publications.py` to extract N and effect sizes.  
  * Iterate over `data/processed/filtered_datasets.json`.  
  * For each entry:  
    1. Call `oa_checker.is_open_access`; if `False`, record status `"paywalled"` and continue.  
    2. Download the full‑text (or abstract if full‑text unavailable) via `requests.get` with a 10 s timeout; raise `DataFetchError` on failure.  
    3. **Validate univariate effect size presence**: Scan text for required univariate metrics (Cohen's d, F, r) before attempting extraction (FR-007).  
    4. Stream the text in ≤ 500 KiB chunks to the parsers from T004.  
    5. On success, emit a JSON object adhering to `contracts/extracted_params.schema.yaml` and write it **line‑delimited** to `data/processed/extracted_params.jsonl`.  
    6. On failure, record status `"unparseable"` and note the attempted source (`full_text` or `abstract`).  
  * After the loop, write summary statistics to `data/processed/extraction_stats.json` (counts of successes, failures, paywalled, abstract‑fallback).  
  * Compute the **sensitivity delta** (full‑text success – (full‑text + abstract) success) and store in `data/processed/sensitivity_delta.json`.  
  **Verification** – `tests/unit/test_extracted_params_schema.py` validates every line of `extracted_params.jsonl` against its schema. Additionally, a test `tests/unit/test_extraction_success.py` asserts that `extraction_stats.json["extraction_success_rate"] >= 0.60` (SC-001).

---  

## Phase 5 – Power analysis & MDES computation (User Story 3)  

- [ ] T007 Implement `code/03_compute_mdes.py` to calculate observed power and MDES.  
  1. Read `data/processed/extracted_params.jsonl`.  
  2. Convert any F‑statistics to Cohen’s d using the standard conversion formula (requires DOF).  
  3. For each entry, select the appropriate `statsmodels.stats.power` class (`TTestIndPower` for d, `FTestAnovaPower` for ANOVA) and:  
     - **Compute observed power** based on the reported N and effect size (FR-004, Constitution Principle VI).  
     - Solve for **MDES** that would achieve the target power `0.8` at `α=0.05`.  
  4. Clamp observed power to ≤ 1.0; emit a warning log if clamping occurs.  
  5. Write results to `data/processed/power_audit_results.jsonl` matching `contracts/power_audit_result.schema.yaml`.  
  6. Aggregate into `data/processed/summary_metrics.json` the following fields:  
     - `fraction_power_lt_0_8` (SC‑002)  
     - `fraction_mdes_le_0_5` (example adequacy threshold)  
     - `dataset_type_distribution` (binary vs. multi‑class, from ingestion metadata).  
  **Verification** – `tests/unit/test_compute_mdes.py` runs the core function on a synthetic record (`N=100, d=0.2`) and asserts: observed power ≈ 0.30 ± 0.05, MDES ≈ 0.25 ± 0.05. A contract test `tests/unit/test_power_audit_schema.py` validates `power_audit_results.jsonl` against its schema.

---  

## Phase 6 – Visualisation & reporting (User Story 3, FR‑005)  

- [ ] T008 Produce figures, the final audit report, and A-Priori tools.  
  * Using `matplotlib`, generate:  
    - `data/processed/power_histogram.png` (observed power distribution).  
    - `data/processed/mdes_histogram.png` (MDES distribution).  
  * Summarise MDES statistics (median, IQR) in `data/processed/mdes_summary.json`.  
  * Implement a lightweight CLI tool `code/utils/apriori_calc.py` that allows users to input desired power, alpha, and effect size to calculate required N (FR-006).  
  * Assemble a markdown report `data/processed/audit_report.md` containing:  
    - Brief methodology.  
    - Ingestion summary (counts, dataset‑type breakdown).  
    - Extraction statistics (including sensitivity delta).  
    - Power results (embed `power_histogram.png`, report `fraction_power_lt_0_8`).  
    - MDES results (embed `mdes_histogram.png`, median/IQR, `fraction_mdes_le_0_5`).  
    - Mandatory disclaimer:  
      > “Observed power is a monotone function of the p‑value and should not be used for post‑hoc validation (Hoenig & Heisey).”  
  * Export a machine‑readable version `data/processed/audit_report.json` mirroring the markdown sections.  
  **Verification** – `tests/unit/test_report_schema.py` validates `audit_report.json` against `contracts/report.schema.yaml`; a grep confirms the disclaimer text appears in `audit_report.md`.

---  

## Phase 7 – Reproducible execution & user‑facing documentation  

- [ ] T009 Create a pipeline wrapper script `run_pipeline.sh` and accompanying `docs/quickstart.md`.  
  `run_pipeline.sh` (executable) runs the four stages in order and aborts on any non‑zero exit code:  
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  python code/01_ingest_openml.py
  python code/02_parse_publications.py
  python code/03_compute_mdes.py
  python code/04_generate_report.py   # (implemented in T008)
  ```  
  `docs/quickstart.md` lists prerequisites, the `pip install -r requirements.txt` step, the command `./run_pipeline.sh`, and the expected SHA‑256 checksum of the final markdown report (`data/processed/audit_report.md`).  
  **Verification** – an integration test `tests/integration/test_quickstart_checksum.py` executes `./run_pipeline.sh` with the environment variable `MAX_DATASETS=5` (causing each script to process only the first five OA entries), computes the SHA‑256 of `audit_report.md`, and asserts it matches the checksum recorded in `quickstart.md`.

---  

## Phase 8 – Performance limits, provenance, and checksum manifest  

- [ ] T010 Add runtime‑ and memory‑limit enforcement to every pipeline script and provide a performance harness.  
  * Each script reads `config.yaml` at start; if wall‑clock time exceeds `limits.max_runtime_hours` **or** RSS exceeds `limits.max_memory_gb`, raise `RuntimeError` with a clear message.  
  * New module `code/performance_harness.py` runs the full pipeline while measuring elapsed seconds (via `time.perf_counter()`) and peak RSS (`memory_profiler.memory_usage`). Results are written to `data/processed/performance_metrics.json` with keys `elapsed_seconds`, `peak_rss_gb`, `status`.  
  **Verification** – `tests/unit/test_performance_harness.py` performs three checks:  
    1. Runs on a tiny dataset and asserts `elapsed_seconds <= config.limits.max_runtime_hours * 3600` and `peak_rss_gb <= config.limits.max_memory_gb` (SC-003, SC-004).  
    2. Deliberately sets `limits.max_memory_gb` to a value below current usage and asserts that the pipeline raises `RuntimeError`.  
    3. Deliberately sets `limits.max_runtime_hours` to 0 and asserts that the pipeline raises `RuntimeError`.

- [ ] T011 Maintain a central checksum manifest for provenance.  
  * After each pipeline stage, append an entry to `data/processed/checksum_manifest.json` of the form:  
    ```json
    { "stage": "ingest", "input": "data/raw/openml_metadata_raw.json", "output": "data/processed/filtered_datasets.json", "sha256": "<hash>" }
    ```  
  * A unit test `tests/unit/test_checksum_manifest.py` modifies a source file, re‑runs the corresponding stage, and asserts that the manifest entry’s `sha256` value has changed accordingly.  
  **Verification** – the test must pass.

---  

## Phase 9 – Constitution & Quality Gates  

- [ ] T012 Refactor `code/utils/` to consolidate OA logic into a single module `code/utils/open_access.py` and update all imports accordingly. Run `flake8` to confirm no circular imports and zero style violations.  
  **Verification** – `flake8 code/` exits with status 0 and a grep for `import oa_checker` shows no remaining references.

- [ ] T013 Implement the Reference-Validator citation gate.  
  * Create a script `code/utils/verify_citations.py` that parses all `.md` and `.json` artifacts for citations/URLs.  
  * Use the Reference-Validator Agent (or a mock of its API) to verify that every external citation is reachable and the title-token-overlap is $\ge 0.7$.  
  * The script must exit with code 1 if any citation is `unreachable` or `mismatch`.  
  **Verification** – run the script against a known "bad" citation file and assert it fails; run against the final report and assert it passes.

- [ ] T014 Implement and verify random seed pinning.  
  * Audit all scripts in `code/` to ensure `np.random.seed()`, `random.seed()`, and any other stochastic libraries are pinned to a constant value (e.g., 42) at the entry point.  
  * Create a test `tests/unit/test_reproducibility.py` that runs a stochastic part of the pipeline twice and asserts the resulting `data/processed/` files are byte-identical.  
  **Verification** – the test must pass.

---  

### Dependency mapping (quick reference)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑002, FR‑009 | T005 |
| FR‑003, FR‑007, FR‑008 | T006 |
| FR‑004, FR‑005, SC‑001, SC‑002 | T006, T007, T008 |
| FR‑006 (a‑priori) | T008 |
| FR‑009 (type distribution) | T007 |
| Contract validation | T003, T004, T005‑T008, T010‑T011 |
| Performance limits (SC-003/4) | T010 |
| Reproducibility (quickstart) | T009 |
| Checksum provenance | T011 |
| Citation Verification (Const II) | T013 |
| Seed Pinning (Const I) | T014 |
| Utils refactor | T012 |

---  

*All tasks are currently unchecked (`[ ]`).  Once a task's verification step passes, the corresponding checkbox can be marked as completed.*