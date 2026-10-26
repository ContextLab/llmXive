# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas in `contracts/`.  
All tasks are expressed as markdown checklist items following the canonical  

```
- [ ] T### [P?] [USx?] description … with exact artifact paths
```  

Verification steps are indented beneath each headline.  
The list contains **14** substantive tasks (plus verification‑only tasks) that together implement the complete end‑to‑end audit while satisfying every functional requirement in the specification and the project constitution.

---  

## Phase 1 – Project scaffolding & core configuration  

- [ ] T001 Create the correct project directory tree under the canonical project
  path `projects/PROJ-234-assessing-statistical-power-in-reproduci/` and add
  placeholder `.gitkeep` files.  
  ```
  projects/PROJ-234-assessing-statistical-power-in-reproduci/
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
  **Verify** – each directory exists (`test -d <dir>`), each contains a `.gitkeep` file, **and** the top‑level directory name equals `PROJ-234-assessing-statistical-power-in-reproduci`.

- [ ] T002 Add `requirements.txt` with exact versions and a `config.yaml` that stores
  runtime limits.  
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
  **Verify** – `pip install -r requirements.txt --dry-run` succeeds;  
  `yaml.safe_load("config.yaml")` returns a dict containing the two limits.

- [ ] T003 Populate the `contracts/` directory with the two schema files that are
  actually supplied in the specification and referenced by the code.  
  ```
  contracts/dataset_metadata.schema.yaml          # supplied in spec
  contracts/power_audit_result.schema.yaml       # supplied in spec (contains $defs for StatisticalParameters and ExtractionAuditReport)
  ```  
  **Verify** – each file parses without error (`yaml.safe_load`) and a minimal valid
  instance passes `jsonschema.Draft7Validator`.

---  

## Phase 2 – Core utility library (single module group)  

- [ ] T004 Implement reusable utilities in `code/utils/` and ensure unit tests pass.  
  * `api_client.py` – thin wrapper around the OpenML REST API **with exponential‑backoff retry for HTTP 429** (configurable `max_retries`, `initial_delay`, `max_delay`) **and raises a custom `DataFetchError` on permanent failure**.  
  * `oa_checker.py` – `is_open_access(url: str) -> bool` recognises known OA domains
    (`arxiv.org`, `doi.org/10.`, `pubmedcentral.nih.gov`) and validates the
    `Content‑Type` header.  
  * `parsers.py` – extraction helpers:  
    - `extract_sample_size(text: str) -> int` (regex `r"N\s*=\s*(\d+)"`).  
    - `extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]` (regexes for Cohen’s d, F‑statistics, odds‑ratio, returning metric type and optional DOF).  
  * All utilities raise `DataFetchError` on failure; no silent fall‑backs.  
  **Verification** – run `pytest -q tests/unit/` and ensure the three unit tests
  (`test_api_client.py`, `test_oa_checker.py`, `test_parsers.py`) all pass, **including checks that `api_client.py` implements exponential back‑off and raises `DataFetchError`**.

- [ ] T015 Add unit test `tests/unit/test_dataset_metadata_schema.py` that loads
  `data/processed/filtered_datasets.json` and validates every record against
  `contracts/dataset_metadata.schema.yaml`.  
  **Verify** – the test passes, confirming schema conformity of the filtered dataset file.

---  

## Phase 3 – Data ingestion (User Story 1)  

- [ ] T005 Implement `code/01_ingest_openml.py` to fetch, filter, and store OpenML metadata.  
  1. Use `utils.api_client.fetch_top_classification_datasets(limit=50)` to obtain the top‑50 most‑downloaded classification datasets.  
  2. Filter for entries where **`publication_link` is non‑null OR `task_id` is non‑null**.  
  3. Write the raw API response to `data/raw/openml_raw.json` (immutable).  
  4. Write the filtered list to `data/processed/filtered_datasets.json`, each record
     conforming to `contracts/dataset_metadata.schema.yaml`.  
  5. Generate SHA‑256 checksums for both files and append them to
     `data/processed/checksum_manifest.json`.  
  6. Emit a short log `data/ingest.log` with totals.  
  **Verification** – `tests/unit/test_dataset_metadata_schema.py` loads
  `data/processed/filtered_datasets.json` and validates every record against the
  schema; the test must pass. Additionally, the script must produce a **non‑empty**
  `filtered_datasets.json`; failure to do so aborts the pipeline.

---  

## Phase 4 – Publication parsing & statistical‑parameter extraction (User Story 2)  

- [ ] T006 Implement `code/02_parse_publications.py` to extract N and effect sizes.  
  * Iterate over `data/processed/filtered_datasets.json`.  
  * For each entry:  
    1. Call `oa_checker.is_open_access`; if `False`, record status `"paywalled"` and continue.  
    2. Download the full‑text (fallback to abstract) via `requests.get` with a 10 s timeout; raise `DataFetchError` on failure.  
    3. Stream the text in ≤ 500 KiB chunks to the parsers from T004.  
    4. On success, emit a JSON object adhering to the **`StatisticalParameters`** definition inside
       `contracts/power_audit_result.schema.yaml` and write it line‑delimited to
       `data/processed/statistical_params.jsonl`.  
    5. On failure, record status `"unparseable"` and note the attempted source
       (`full_text` or `abstract`).  
  * After the loop, write summary statistics to `reports/extraction_audit.json`
    (conforms to the `ExtractionAuditReport` definition).  
  **Verification** – `tests/unit/test_extracted_params_schema.py` validates each line of
  `statistical_params.jsonl` against its schema; `tests/unit/test_extraction_metrics.py`
  asserts **precision ≥ 0.9** and **recall ≥ 0.9** (SC‑005) and that the extraction success
  rate remains ≥ 0.60.

- [ ] T017 Add unit test `tests/unit/test_extraction_metrics.py` that computes precision
  and recall on a validated set of ≥ 60 papers and checks they meet the 0.9 lower
  bound with 95 % confidence intervals.  
  **Verify** – the test passes, confirming FR‑011 compliance.

---  

## Phase 5 – Power analysis & reference‑power computation (User Story 3)  

- [ ] T007 Implement `code/03_compute_observed_power.py` to calculate observed and reference power.  
  1. Read `data/processed/statistical_params.jsonl`.  
  2. Convert any F‑statistics to Cohen’s d using the standard conversion (requires DOF).  
  3. For each entry, select the appropriate `statsmodels.stats.power` class  
     (`TTestIndPower` for d, `FTestAnovaPower` for ANOVA, `NormalIndPower` for logistic).  
  4. **Compute observed power** using the reported effect size, sample size, and α = 0.05.  
  5. **Compute reference power** using the test‑specific small‑effect benchmark  
     (d = 0.2 for t‑tests, f = 0.2 for ANOVA, log‑odds ≈ 0.2 for logistic) with the same N and α.  
  6. Clamp any power values > 1.0 to 1.0 and log a warning.  
  7. Write results line‑delimited to `data/processed/power_audit_results.jsonl`,
     each record conforming to `contracts/power_audit_result.schema.yaml`.  
  8. Aggregate summary metrics (fraction of studies with `reference_power < 0.8`,
     etc.) to `data/processed/power_summary.json`.  
  **Verification** – `tests/unit/test_compute_power.py` runs the core function on a synthetic
  record (`N=100, d=0.2`) and asserts observed power ≈ 0.30 ± 0.05 and reference power ≥ 0.8;  
  `tests/unit/test_power_audit_schema.py` validates `power_audit_results.jsonl` against its schema.

---  

## Phase 6 – Visualisation & reporting (User Story 3, FR‑005)  

- [ ] T008 Implement `code/04_generate_report.py` to produce figures, markdown, and JSON reports.  
  * Using `matplotlib`, generate:  
    - `data/processed/reference_power_histogram.png` (20‑bin histogram of reference power).  
    - `data/processed/observed_power_histogram.png` (20‑bin histogram of observed power).  
  * Assemble a markdown report `data/processed/audit_report.md` containing:  
    - Brief methodology recap.  
    - Ingestion summary (counts, OA breakdown).  
    - Extraction statistics (from `reports/extraction_audit.json`).  
    - Power results (embed the two histograms, report the count of studies with
      `reference_power < 0.8`).  
    - Mandatory disclaimer:  
      > “Observed post‑hoc power is a monotone function of the p‑value and should not be used as the sole indicator of study adequacy (Hoenig & Heisey).”  
  * Export a machine‑readable version `data/processed/audit_report.json` mirroring the markdown sections and **including**:  
    - `reference_power_adequacy` field with the proportion of studies where `reference_power ≥ 0.8`.  
    - `extraction_audit_path` set to `"reports/extraction_audit.json"`.  
  **Verification** – `tests/unit/test_report_contents.py` checks that `audit_report.md`
  contains the disclaimer text and that both PNG files exist; `tests/unit/test_audit_report_metrics.py` asserts that `audit_report.json`
  includes `reference_power_adequacy` (value ≥ 0) **and** that `extraction_audit_path` correctly points to `reports/extraction_audit.json`, and that the proportion of studies with `reference_power ≥ 0.8` is recorded.

---  

## Phase 7 – Reproducible execution & user‑facing documentation  

- [ ] T009 Create a pipeline wrapper script `run_pipeline.sh` and accompanying
  `docs/quickstart.md`.  
  `run_pipeline.sh` (executable) runs the four stages in order and aborts on any
  non‑zero exit code:  
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  python code/01_ingest_openml.py
  python code/02_parse_publications.py
  python code/03_compute_observed_power.py
  python code/04_generate_report.py
  ```  
  `docs/quickstart.md` lists prerequisites, the `pip install -r requirements.txt`
  step, the command `./run_pipeline.sh`, and the expected SHA‑256 checksum of the
  final markdown report (`data/processed/audit_report.md`).  
  **Verification** – `tests/integration/test_quickstart_checksum.py` runs the wrapper
  with the environment variable `MAX_DATASETS=5` (causing each script to process only
  the first five OA entries), computes the SHA‑256 of `audit_report.md`, and asserts
  it matches the checksum recorded in `quickstart.md`.

---  

## Phase 8 – Performance limits, provenance, and checksum manifest  

- [ ] T010 Add runtime‑ and memory‑limit enforcement to every pipeline script and provide a performance harness.  
  * Each script reads `config.yaml` at start; if wall‑clock time exceeds
    `limits.max_runtime_hours` **or** RSS exceeds `limits.max_memory_gb`, raise
    `RuntimeError` with a clear message.  
  * New module `code/performance_harness.py` runs the full pipeline while measuring
    elapsed seconds (`time.perf_counter()`) and peak RSS (`memory_profiler.memory_usage`);
    results are written to `data/processed/performance_metrics.json` with keys
    `elapsed_seconds`, `peak_rss_gb`, `status`.  
  **Verification** – `tests/unit/test_performance_harness.py` (1) runs on a tiny
  dataset and asserts both limits are respected (SC‑003, SC‑004); (2) deliberately
  lowers `limits.max_memory_gb` and checks that `RuntimeError` is raised; (3)
  sets `limits.max_runtime_hours` to 0 and checks for `RuntimeError`.

- [ ] T011 Maintain a central checksum manifest for provenance.  
  * After each pipeline stage, append an entry to `data/processed/checksum_manifest.json` of the form:  
    ```json
    { "stage": "ingest", "input": "data/raw/openml_raw.json", "output": "data/processed/filtered_datasets.json", "sha256": "<hash>" }
    ```  
  * A unit test `tests/unit/test_checksum_manifest.py` modifies a source file,
    re‑runs the corresponding stage, and asserts that the manifest entry’s `sha256`
    value has changed accordingly.  
  **Verification** – the test must pass.

---  

## Phase 9 – Constitution & quality‑gate tasks  

- [ ] T012 Refactor OA logic into a single module `code/utils/open_access.py` and update all imports accordingly.  
  **Verification** – `flake8 code/` exits with status 0 and a grep for
  `import oa_checker` shows no remaining references.

- [ ] T013 Implement the Reference‑Validator citation gate.  
  * Create script `code/utils/verify_citations.py` that parses all `.md` and `.json`
    artifacts for URLs, queries the Reference‑Validator Agent (or a mock) to ensure
    each external citation is reachable and has title‑token overlap ≥ 0.7.  
  * The script exits with code 1 on any failure.  
  **Verification** – run the script against a deliberately bad citation file and
  assert it fails; run it against the final `audit_report.md` and assert it passes.

- [ ] T014 Ensure random‑seed pinning and reproducibility.  
  * Audit all scripts in `code/` to call `np.random.seed(42)`, `random.seed(42)`,
    and any other stochastic library seeds at entry.  
  * Add test `tests/unit/test_reproducibility.py` that runs a stochastic part of the
    pipeline twice and asserts the resulting `data/processed/` files are byte‑identical.  
  **Verification** – the test must pass.

---  

### Dependency mapping (quick reference)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑002   | T005 |
| FR‑003, FR‑007   | T006 |
| FR‑004, FR‑010   | T007 |
| FR‑005, SC‑001, SC‑002 | T008 |
| FR‑011           | T006 (extraction audit) & T017 |
| FR‑013           | T005, T006, T007, T008 (all write to SSoT) |
| FR‑015           | T006 (produces `extraction_audit.json`) |
| SC‑003, SC‑004   | T010 |
| SC‑005           | T006 (precision/recall ≥ 0.9) |
| Constitution I‑VII | T012‑T014 |
| Performance limits | T010 |
| Checksum provenance | T011 |
| Quickstart reproducibility | T009 |
| Directory layout | T001 |
| Contracts availability | T003 |
| Utils implementation | T004 |
| Missing test for schema validation | T015 |
| Missing test for extraction metrics | T017 |

---  

*All tasks are currently unchecked (`[ ]`).  Once a task's verification step passes,
the corresponding checkbox can be marked as completed.*  