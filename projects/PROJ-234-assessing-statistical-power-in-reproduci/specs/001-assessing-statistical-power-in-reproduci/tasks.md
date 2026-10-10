# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets

**Input**: `spec.md`, `plan.md`, `data-model.md`, and all contract schemas.  
All tasks are expressed as markdown checklist items following the canonical  
`- [ ] T### [P?] [USx?] description …` format.  Tasks that can run in parallel
are marked with **[P]**.  User‑story identifiers (**US1**, **US2**, **US3**) are
included where the task directly satisfies a story requirement.  Paths are
relative to the repository root.

---

## Phase 1 – Project scaffolding & core infrastructure

| ID | Parallel? | Story | Description |
|----|-----------|-------|-------------|
| - | - | - | Each task lists its verification steps indented beneath the headline. |

- [ ] **T001** Create the project directory tree and placeholder `.gitkeep` files.  
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
          contract/
      docs/
      contracts/
  ```  
  **Verify** – each directory exists (`test -d <dir>`), and a `.gitkeep` file is present in every empty folder.

- [ ] **T002** Write `requirements.txt` with the exact versions required by the specification:  
  ```
  pandas==2.0.3
  scipy==1.11.4
  statsmodels==0.14.1
  requests==2.31.0
  matplotlib==3.8.0
  pytest==7.4.0
  beautifulsoup4==4.12.2
  numpy==1.26.0
  yaml==0.2.5
  memory_profiler==0.61.0
  ```  
  **Verify** – `pip install -r requirements.txt --dry-run` succeeds without errors.

- [ ] **T003** Add linting and formatting configuration:  
  * `pyproject.toml` with Black settings (`max-line-length = 88`, `target-version = ["py310"]`).  
  * `.flake8` with `max-line-length = 88`.  
  **Verify** – `black --check .` and `flake8 .` both exit with status 0.

- [ ] **T004** Create `config.yaml` that stores the runtime and memory limits required by the spec:  
  ```yaml
  limits:
    max_runtime_hours: 6
    max_memory_gb: 7
  ```  
  **Verify** – file is valid YAML (`python -c "import yaml,sys; yaml.safe_load(open('config.yaml'))"`).

- [ ] **T005** Populate the `contracts/` directory with all schema files required for contract testing:  
  * `dataset_metadata.schema.yaml` (already provided in the spec).  
  * `power_audit_result.schema.yaml` (already provided).  
  * `extracted_params.schema.yaml` – defines `dataset_id`, `sample_size`, `effect_size`, `metric_type`, `degrees_of_freedom`, `source_url`, `status`.  
  * `report.schema.yaml` – defines the final audit‑report JSON structure (summary statistics, counts, file references).  
  **Verify** – each file exists, parses with `jsonschema.Draft7Validator`, and `yamllint` reports no errors.

- [ ] **T006** Implement `code/utils/api_client.py` containing a thin wrapper around the OpenML REST API with exponential‑backoff retry logic for HTTP 429 responses.  
  **Unit test** `tests/unit/test_api_client.py::test_retry_on_429` must simulate a 429 and assert that the backoff occurs and the request eventually succeeds.

- [ ] **T007** Implement `code/utils/oa_checker.py` that determines whether a URL points to an Open‑Access resource (e.g., by inspecting HTTP `Content‑Type` or known OA domains).  
  **Unit test** `tests/unit/test_oa_checker.py::test_oa_status` validates true/false outcomes for a set of known OA and paywalled URLs.

- [ ] **T008** Add a centralized logging configuration module `code/utils/logging_config.py` that configures a file logger (`data/pipeline.log`) with INFO level and a consistent format.  
  **Verify** – import the module in another script and confirm that a test log entry appears in `data/pipeline.log`.

---

## Phase 2 – Data ingestion (User Story 1)

- [ ] **T009** Implement `code/01_ingest_openml.py` that:
  1. Connects to the OpenML API (via `api_client`) and retrieves the **top 50 most‑downloaded classification datasets**.
  2. Filters for entries that have a non‑null `publication_link` **or** a non‑null `task_id`.
  3. Ensures the dataset’s `task_type` is a classification task; non‑classification entries are logged and skipped (satisfies FR‑001 and FR‑009).
  4. Writes the raw response to `data/raw/openml_metadata_raw.json`.
  5. Writes the filtered list to `data/raw/openml_metadata_filtered.json`.
  6. Generates SHA‑256 checksums for both files and stores them in `data/raw/checksums.txt`.
  7. Emits a JSON‑formatted statistics record to `data/ingest.log` (total fetched, filtered, type distribution).  
  **Verification** – a pytest contract test `tests/contract/test_dataset_metadata_schema.py::test_schema` loads `data/raw/openml_metadata_filtered.json` and validates it against `contracts/dataset_metadata.schema.yaml`.

- [ ] **T010** Add a contract test `tests/contract/test_dataset_metadata_schema.py` that imports the JSON schema and asserts the filtered metadata file conforms to it.  
  **Verify** – test passes after `T009` runs.

---

## Phase 3 – Publication parsing & statistical‑parameter extraction (User Story 2)

- [ ] **T011** Implement `code/utils/parsers.py` with robust, **fail‑loudly** extraction utilities:  
  * `extract_sample_size(text: str) -> int` – regex `r"N\s*=\s*(\d+)"`.  
  * `extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]` – regexes for Cohen’s d (`r"Cohen\s*['’]?s?\s*d\s*=\s*([0-9.]+)"`) and F‑statistics (`r"F\((\d+),\s*(\d+)\)\s*=\s*([0-9.]+)"`).  
  * No `try/except` that falls back to synthetic data; any network or parsing failure raises a custom `DataFetchError`.  
  * Streaming support: if a fetched HTML/PDF text exceeds 5 MiB, process it in 500 KiB chunks, feeding each chunk to the regexes without loading the whole document into memory.  
  **Unit tests** in `tests/unit/test_parsers.py` for each regex and for the streaming‑chunk logic (`test_streaming_chunks_does_not_exceed_memory`).

- [ ] **T012** Implement `code/02_parse_publications.py` that iterates over `data/raw/openml_metadata_filtered.json` and, for each dataset:  
  1. Performs **pre‑fetch validation** (skip journals unlikely to report univariate effect sizes; see FR‑007).  
  2. Calls `oa_checker.is_open_access(url)`; if False, records status `"paywalled"` and moves on.  
  3. Downloads the full‑text via `requests.get` (timeout 10 s). On failure, raises `DataFetchError` (no silent fallback).  
  4. Applies the parsers from `T011` to extract `sample_size`, `effect_size`, `metric_type`, and optional `degrees_of_freedom`.  
  5. If extraction fails, marks status `"unparseable"`; if only an abstract is available, retries with the abstract and marks source `"abstract"`.  
  6. Writes a line‑delimited JSON file `data/processed/extracted_params.json` (one object per dataset) respecting the `extracted_params.schema.yaml`.  
  7. Generates `data/processed/extraction_stats.json` summarising success/failure counts.  
  8. Computes the **sensitivity delta** (full‑text success rate – (full‑text + abstract) success rate) and stores it in `data/processed/sensitivity_delta_report.json`.  

  **Verification** – contract test `tests/contract/test_extracted_params_schema.py::test_schema` validates `extracted_params.json` against its schema; unit tests from `T011` cover the regexes and streaming behavior.

---

## Phase 4 – Power & MDES computation (User Story 3)

- [ ] **T013** Implement `code/03_compute_sensitivity.py` that reads `extracted_params.json` and for each entry:  
  1. Converts F‑statistics to Cohen’s d when necessary (using the standard conversion formula).  
  2. Calls `statsmodels.stats.power.TTestIndPower().power(effect_size, nobs1=sample_size, alpha=0.05)` to obtain **observed power**.  
  3. Calls the same class’s `solve_power` method (inverse power) to compute **MDES** for a target power of 0.8 (default) and `alpha=0.05`.  
  4. Clamps observed power to ≤ 1.0, logs a warning if the input effect size caused > 1.0.  
  5. Writes `data/processed/power_audit_results.json` with fields `{dataset_id, observed_power, mdes, threshold_met, status}` matching `power_audit_result.schema.yaml`.  
  6. Calculates aggregate metrics:  
     * `observed_power_below_0.8` fraction (SC‑002).  
     * `mdes_above_0.2` fraction (a secondary MDES adequacy check).  
     * Writes these to `data/processed/success_metrics.json`.  
  7. Derives dataset‑type distribution from the ingestion log and writes `data/processed/type_distribution.json` (binary vs. multi‑class counts).  

  **Verification** – unit test `tests/unit/test_compute_sensitivity.py::test_known_values` runs the functions on synthetic inputs (`N=100, d=0.2`) and asserts observed power ≈ 0.30 ± 0.05 and MDES ≈ 0.25 ± 0.05.

- [ ] **T014** Produce visualisations:  
  * Histogram of **observed power** (`power_histogram.png`).  
  * Histogram of **MDES** (`mdes_histogram.png`).  
  * Save summary statistics (median, IQR) to `data/processed/mdes_summary.json`.  

  **Verify** – files exist and are non‑empty PNGs; JSON contains numeric keys `median`, `iqr`.

---

## Phase 5 – Report generation & hand‑off

- [ ] **T015** Implement `code/04_generate_report.py` that aggregates all JSON artifacts (`power_audit_results.json`, `extraction_stats.json`, `sensitivity_delta_report.json`, `mdes_summary.json`, `success_metrics.json`, `type_distribution.json`) and produces:  
  1. **Markdown report** `data/processed/audit_report.md` with sections: Overview, Ingestion Summary, Extraction Statistics (including sensitivity delta), Dataset Type Distribution, Observed Power Results (embed `power_histogram.png` and fraction < 0.8), MDES Results (embed `mdes_histogram.png` and summary), and a mandatory disclaimer about post‑hoc power.  
  2. **Structured JSON report** `data/processed/audit_report.json` that mirrors the markdown sections (counts, fractions, file names).  

  **Verification** – contract test `tests/contract/test_final_report_schema.py::test_schema` validates `audit_report.json` against `contracts/report.schema.yaml`; a simple grep on `audit_report.md` confirms the disclaimer text is present.

- [ ] **T016** Create `docs/quickstart.md` that documents:  
  * Prerequisites (Python 3.10+, pip).  
  * Installation (`pip install -r requirements.txt`).  
  * Execution command (`./run_pipeline.sh`).  
  * Expected output files and their purpose.  
  * Verification step: after running the script, compute SHA‑256 of `data/processed/audit_report.md` and compare it to the checksum recorded in the quick‑start file.  

  **Verification** – the markdown contains a fenced code block showing the checksum command and the recorded hash.

- [ ] **T017** Add a thin wrapper script `run_pipeline.sh` (executable) that runs the four pipeline stages in order:  
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  python code/01_ingest_openml.py
  python code/02_parse_publications.py
  python code/03_compute_sensitivity.py
  python code/04_generate_report.py
  ```  
  **Verify** – the script is executable (`chmod +x`) and runs without error on a small test subset (see T023).

- [ ] **T018** Verify the quick‑start workflow (Task T016) by executing `./run_pipeline.sh` on the CI runner and confirming that the SHA‑256 hash of `audit_report.md` matches the value recorded in `quickstart.md`.  
  **Verification** – a pytest integration test `tests/integration/test_quickstart.py::test_pipeline_produces_expected_checksum` performs the run and asserts equality.

---

## Phase 6 – Performance, resource limits & robustness

- [ ] **T019** Implement a performance harness script `code/performance_harness.py` that:  
  * Executes the full pipeline while measuring wall‑clock time (`/usr/bin/time -v`).  
  * Profiles peak RSS using `memory_profiler`.  
  * Writes a JSON summary `data/processed/performance_metrics.json` containing `elapsed_seconds`, `peak_memory_gb`, and timestamps.  

  **Verification** – unit test `tests/unit/test_performance_harness.py` runs the harness on a tiny synthetic dataset and asserts that the JSON keys exist and values are numeric.

- [ ] **T020** Add runtime‑ and memory‑limit enforcement to each pipeline script (`01_ingest_openml.py`, `02_parse_publications.py`, `03_compute_sensitivity.py`, `04_generate_report.py`). Each script must read `config.yaml` (Task T004) and abort with a clear error message if the measured wall‑clock time exceeds `max_runtime_hours` or if the process’s RSS exceeds `max_memory_gb`.  

  **Verification** – integration test `tests/integration/test_limit_enforcement.py` monkey‑patches the limits to tiny values and confirms that the scripts raise `RuntimeError` with the expected message.

- [ ] **T021** Write an integration test `tests/integration/test_full_pipeline_small_subset.py` that:  
  1. Limits the ingestion step to the first **5** filtered datasets (by passing an environment variable `MAX_DATASETS=5`).  
  2. Executes the entire pipeline via `./run_pipeline.sh`.  
  3. Checks that `audit_report.md` exists, is non‑empty, and its SHA‑256 matches a pre‑computed reference checksum stored in `tests/integration/expected_audit_report.sha256`.  

  **Verification** – the test passes on the CI runner, proving end‑to‑end reproducibility on a tractable subset.

---

## Phase 7 – Polish & cross‑cutting clean‑up

- [ ] **T022** Refactor `code/utils/` to eliminate duplicate code:  
  * Move OA‑check logic from `oa_checker.py` into a shared helper `code/utils/open_access.py`.  
  * Ensure all scripts import `logging_config` and use the same logger instance.  
  * Run `flake8` import‑order check to confirm no circular imports.  

  **Verification** – `flake8` passes, and a grep for `import oa_checker` shows no remaining references.

- [ ] **T023** Update `docs/constitution.md` with markdown links to the key artifacts (`research.md`, `plan.md`, `quickstart.md`) to satisfy the constitution‑check requirement.  

  **Verification** – the file contains the three links and `markdown-link-check` (if run) reports no broken links.

- [ ] **T024** Ensure all intermediate artifacts are recorded in a central checksum manifest: `data/processed/checksum_manifest.json`. Each pipeline step (ingest, parse, compute, report) appends entries of the form `{ "input": "<path>", "output": "<path>", "sha256": "<hash>" }`.  

  **Verification** – a unit test `tests/unit/test_checksum_manifest.py` modifies a source file, reruns the relevant step, and asserts that the corresponding manifest entry’s hash changes.

---

### Dependency mapping (for reference)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑002, FR‑009 | T009 |
| FR‑003, FR‑007, FR‑008 | T011, T012 |
| FR‑004, FR‑005, SC‑001, SC‑002 | T013, T014 |
| FR‑006 (a‑priori capability) | T009 (provides data) + T015 (report) |
| FR‑009 (type distribution) | T013 |
| Contract validation | T005, T010, T018, T030 |
| Performance limits | T019, T020 |
| Reproducibility (quickstart) | T016, T017, T018 |
| Memory‑profile & limit enforcement | T019, T020 |
| Documentation & constitution | T023, T022 |

--- 

*All tasks above are unchecked (`[ ]`) to indicate they still need to be implemented and verified.  Once a task passes its verification step, the checkbox can be marked as completed.*
