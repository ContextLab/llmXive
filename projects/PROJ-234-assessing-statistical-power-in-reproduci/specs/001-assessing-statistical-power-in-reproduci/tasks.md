# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, all contract schemas in `contracts/`.  
All tasks are expressed as markdown checklist items following the canonical  

```
- [ ] T### [P?] [USx?] description … with exact artifact paths
```  

Verification steps are indented beneath each headline.  
The list contains **17** substantive tasks (grouped by logical phases) that together implement the complete end‑to‑end audit while satisfying every functional requirement in the specification and respecting the project constitution.

---  

## Phase 1 – Project scaffolding & core configuration  

- [ ] T001 [P] Establish the canonical project directory tree under  
  `projects/PROJ-234-assessing-statistical-power-in-reproduci/` and add placeholder  
  `.gitkeep` files.  

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

  **Verify** – each listed directory exists (`test -d <dir>`), each contains a `.gitkeep`, and the top‑level directory name matches exactly `PROJ-234-assessing-statistical-power-in-reproduci`.

- [ ] T002 [P] Add `requirements.txt` with exact versions and a `config.yaml` that stores runtime limits.  

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
  memory_profiler==0.61.0
  ```  

  `config.yaml` (excerpt):  

  ```yaml
  limits:
    max_runtime_hours: 6
    max_memory_gb: 8
  ```  

  **Verify** – `pip install -r requirements.txt --dry-run` succeeds; `yaml.safe_load("config.yaml")` returns a dict containing both keys under `limits`.

- [ ] T003 [P] Populate the `contracts/` directory with the two schema files required by the spec.  

  ```
  contracts/dataset_metadata.schema.yaml          # supplied in spec
  contracts/power_audit_result.schema.yaml       # supplied in spec (contains $defs for StatisticalParameters & ExtractionAuditReport)
  ```  

  **Verify** – each file parses with `yaml.safe_load` and a minimal valid instance passes `jsonschema.Draft7Validator`.

---  

## Phase 2 – Core utility library (single‑module group)  

- [ ] T004 [P] Implement reusable utilities in `code/utils/` that satisfy all unit‑test expectations.  

  * `api_client.py` – thin wrapper around the OpenML REST API with **exponential‑backoff** for HTTP 429 (configurable `max_retries=5`, `initial_delay=1`, `max_delay=60`) and raises a custom `DataFetchError` on permanent failure.  
  * `oa_checker.py` – `is_open_access(url: str) -> bool` recognises known OA domains (`arxiv.org`, `doi.org/10.`, `pubmedcentral.nih.gov`) and validates the `Content‑Type` header.  
  * `parsers.py` – deterministic regex/NLP helpers:  
    - `extract_sample_size(text: str) -> int` (pattern `r"N\s*=\s*(\d+)"`).  
    - `extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]` (patterns for Cohen’s d, F‑statistics with DOF, odds‑ratio).  
  * All utilities raise `DataFetchError` on failure; **no silent fall‑backs**.  

  **Verify** – run `pytest -q tests/unit/` and confirm that `test_api_client.py`, `test_oa_checker.py`, and `test_parsers.py` all pass, including the check that `api_client.py` implements exponential back‑off and raises `DataFetchError` for a bad URL.

- [ ] T005 [P] Add missing unit‑test `tests/unit/test_dataset_metadata_schema.py` that loads `data/processed/filtered_datasets.json` (or `.csv` if later) and validates every record against `contracts/dataset_metadata.schema.yaml`.  

  **Verify** – the test passes on a correctly‑formatted filtered dataset file; CI fails if any record violates the schema.

- [ ] T006 [P] Add missing unit‑test `tests/unit/test_extraction_metrics.py` that computes precision, recall, and F1 on a validated set of ≥ 60 papers and asserts **precision ≥ 0.9** and **recall ≥ 0.9** (95 % confidence interval lower bound ≥ 0.9).  

  **Verify** – the test passes, guaranteeing compliance with FR‑011 and SC‑005.

---  

## Phase 3 – Data ingestion (US‑1)  

- [ ] T007 [P] Implement `code/01_ingest_openml.py` to fetch, filter, and store OpenML metadata using the wrapper from T004.  

  1. Call `utils.api_client.fetch_top_classification_datasets(limit=50)`.  
  2. Filter **retain rows where `publication_link` is non‑null **OR** `task_id` is non‑null**.  
  3. Write the immutable raw response to `data/raw/openml_raw.json`.  
  4. Write the filtered list to `data/processed/filtered_datasets.json` (each record conforms to `DatasetMetadata` schema).  
  5. Record SHA‑256 checksums for both files in `data/processed/checksum_manifest.json`.  
  6. Emit a concise log `data/ingest.log` with total counts and any skipped entries.  

  **Verify** – `tests/unit/test_dataset_metadata_schema.py` loads `filtered_datasets.json` and validates all records; the file is non‑empty. Additionally, the script must exit with status 0 and the checksum manifest must contain entries for both input and output files.

---  

## Phase 4 – Publication parsing & statistical‑parameter extraction (US‑2)  

- [ ] T008 [P] Implement `code/02_parse_publications.py` to extract N and effect sizes.  

  * Iterate over `data/processed/filtered_datasets.json`.  
  * For each entry:  
    1. Use `utils.oa_checker.is_open_access`; if `False`, record status `"paywalled"` and continue.  
    2. Download full‑text PDF (fallback to abstract) with `requests.get(..., timeout=10)`. Raise `DataFetchError` on any network error.  
    3. Stream the response in ≤ 500 KiB chunks to `utils.parsers.extract_*` functions.  
    4. On successful extraction, emit a JSON object adhering to the **`StatisticalParameters`** definition (found under `$defs` in `power_audit_result.schema.yaml`) and write it **line‑delimited** to `data/processed/statistical_params.jsonl`.  
    5. On failure, record status `"unparseable"` and note the attempted source (`full_text` or `abstract`).  
  * After processing all datasets, write a summary `reports/extraction_audit.json` that conforms to the `ExtractionAuditReport` schema.  

  **Verify** – `tests/unit/test_extracted_params_schema.py` validates each line of `statistical_params.jsonl` against its schema; `tests/unit/test_extraction_metrics.py` (added in T006) confirms precision ≥ 0.9, recall ≥ 0.9, and overall extraction success rate ≥ 0.60.

- [ ] T009 [P] Add unit‑test `tests/unit/test_extracted_params_schema.py` (if not already present) to perform the schema validation described above.  

  **Verify** – the test passes on a correctly‑generated `statistical_params.jsonl`.

---  

## Phase 5 – Power analysis & reference‑power computation (US‑3)  

- [ ] T010 [P] Implement `code/03_compute_observed_power.py` to calculate observed and reference power.  

  1. Read `data/processed/statistical_params.jsonl`.  
  2. Convert any F‑statistics to Cohen’s d using the standard conversion (requires DOF).  
  3. Select the appropriate `statsmodels.stats.power` class:  
     * `TTestIndPower` for Cohen’s d,  
     * `FTestAnovaPower` for ANOVA (f),  
     * `NormalIndPower` (or a logistic‑regression approximation) for odds‑ratio.  
  4. **Observed power** – compute with reported effect size, sample size `N`, α = 0.05.  
  5. **Reference power** – compute with the test‑specific small‑effect benchmark (d = 0.2, f = 0.2, log‑odds ≈ 0.2) using the same `N` and α.  
  6. Clamp any result > 1.0 to 1.0 and log a warning.  
  7. Write line‑delimited results to `data/processed/power_audit_results.jsonl`, each record conforming to `PowerAuditResult` schema (including `reference_power`, `threshold_met`, `test_type`, etc.).  
  8. Aggregate summary statistics (fraction with `reference_power < 0.8`, mean observed power, etc.) into `data/processed/power_summary.json`.  

  **Verify** – `tests/unit/test_compute_power.py` runs the core function on a synthetic record (`N=100, d=0.2`) and asserts observed power ≈ 0.30 ± 0.05 and reference power ≥ 0.8; `tests/unit/test_power_audit_schema.py` validates every line of `power_audit_results.jsonl` against its schema.

---  

## Phase 6 – Visualisation & reporting (FR‑005)  

- [ ] T011 [P] Implement `code/04_generate_report.py` to produce figures, markdown, and machine‑readable summaries.  

  * Using `matplotlib`, generate:  
    - `data/processed/reference_power_histogram.png` (20‑bin histogram of `reference_power`).  
    - `data/processed/observed_power_histogram.png` (20‑bin histogram of `observed_power`).  
  * Assemble a markdown report `data/processed/audit_report.md` containing:  
    - Brief methods recap.  
    - Ingestion summary (counts, OA breakdown).  
    - Extraction statistics (pulled from `reports/extraction_audit.json`).  
    - Power results: embed both PNGs, report the **count** of studies with `reference_power < 0.8`.  
    - Mandatory disclaimer:  
      > “Observed post‑hoc power is a monotone function of the p‑value and should not be used as the sole indicator of study adequacy (Hoenig & Heisey).”  
  * Export a JSON version `data/processed/audit_report.json` mirroring the markdown sections and **including**:  
    - `reference_power_adequacy` (proportion of studies with `reference_power ≥ 0.8`).  
    - `extraction_audit_path: "reports/extraction_audit.json"`.  

  **Verify** – `tests/unit/test_report_contents.py` checks that `audit_report.md` contains the disclaimer text and that both PNG files exist; `tests/unit/test_audit_report_metrics.py` asserts that `audit_report.json` includes the `reference_power_adequacy` field (value ≥ 0) and the correct path to the extraction audit JSON.

---  

## Phase 7 – Reproducible execution & user‑facing documentation  

- [ ] T012 [P] Create a pipeline wrapper script `run_pipeline.sh` and accompanying `docs/quickstart.md`.  

  `run_pipeline.sh` (executable):  

  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  python code/01_ingest_openml.py
  python code/02_parse_publications.py
  python code/03_compute_observed_power.py
  python code/04_generate_report.py
  ```  

  `docs/quickstart.md` must list:  
  1. Prerequisites (`python >=3.11`, `pip install -r requirements.txt`).  
  2. The command `./run_pipeline.sh`.  
  3. Expected location of the final report (`data/processed/audit_report.md`).  
  4. The SHA‑256 checksum of the expected report (computed on a deterministic small‑dataset run).  

  **Verify** – `tests/integration/test_quickstart_checksum.py` runs the wrapper with the environment variable `MAX_DATASETS=5` (causing each script to process only the first five OA entries), computes the SHA‑256 of `audit_report.md`, and asserts it matches the checksum recorded in `quickstart.md`.

---  

## Phase 8 – Performance limits, provenance, and checksum manifest  

- [ ] T013 [P] Add runtime‑ and memory‑limit enforcement to every pipeline script and provide a performance harness.  

  * Each script loads `config.yaml` at start; if wall‑clock time exceeds `limits.max_runtime_hours` **or** RSS exceeds `limits.max_memory_gb`, raise `RuntimeError` with a clear message.  
  * New module `code/performance_harness.py` runs the full pipeline while measuring elapsed seconds (`time.perf_counter()`) and peak RSS (`memory_profiler.memory_usage`). Results are written to `data/processed/performance_metrics.json` with keys `elapsed_seconds`, `peak_rss_gb`, `status`.  

  **Verify** – `tests/unit/test_performance_harness.py` (1) runs on a tiny dataset and asserts both limits are respected (SC‑003, SC‑004); (2) deliberately lowers `limits.max_memory_gb` and confirms a `RuntimeError` is raised; (3) sets `limits.max_runtime_hours` to 0 and confirms a `RuntimeError`.

- [ ] T014 [P] Maintain a central checksum manifest for provenance.  

  * After each pipeline stage, append an entry to `data/processed/checksum_manifest.json` of the form:  

    ```json
    {
      "stage": "ingest",
      "input": "data/raw/openml_raw.json",
      "output": "data/processed/filtered_datasets.json",
      "sha256": "<hash>"
    }
    ```  

  * Provide a unit test `tests/unit/test_checksum_manifest.py` that modifies a source file, re‑runs the corresponding stage, and asserts the manifest entry’s `sha256` value has changed accordingly.  

  **Verify** – the test passes, confirming that the manifest tracks true file hashes.

---  

## Phase 9 – Constitution‑compliant housekeeping  

- [ ] T015 [P] Refactor OA logic into a single module `code/utils/open_access.py` and update all imports (replace any lingering `oa_checker` imports).  

  **Verify** – `flake8 code/` exits with status 0 and a `grep -R "oa_checker"` returns no results.

- [ ] T016 [P] Implement the Reference‑Validator citation gate.  

  * Script `code/utils/verify_citations.py` parses all `.md` and `.json` artifacts in the project, extracts external URLs, queries a mock Reference‑Validator endpoint to ensure each citation is reachable and has title‑token overlap ≥ 0.7.  
  * The script exits with code 1 on any failure.  

  **Verify** – run the script against a deliberately bad citation file and assert it fails; run it against the final `audit_report.md` and assert it passes.

- [ ] T017 [P] Ensure deterministic random‑seed pinning across the entire code base.  

  * At the top of every script in `code/` add:  

    ```python
    import random, numpy as np
    random.seed(42)
    np.random.seed(42)
    ```  

  * Add test `tests/unit/test_reproducibility.py` that runs a stochastic part of the pipeline twice (e.g., shuffling the filtered dataset list) and asserts the resulting `data/processed/filtered_datasets.json` files are byte‑identical.  

  **Verify** – the test passes, guaranteeing reproducibility.

---  

### Dependency mapping (quick reference)

| Spec requirement | Satisfying task(s) |
|------------------|--------------------|
| FR‑001, FR‑002   | T007 |
| FR‑003, FR‑007   | T008 |
| FR‑004, FR‑010   | T010 |
| FR‑005, SC‑001, SC‑002 | T011 |
| FR‑011, SC‑005   | T008 + T006 |
| FR‑013           | T007, T008, T010, T011 (all write to SSoT) |
| FR‑015           | T008 (writes `reports/extraction_audit.json`) |
| SC‑003, SC‑004   | T013 |
| SC‑009 (confound modeling) – not required for minimal study, omitted |
| Constitution I‑VII | T015‑T017 |
| Performance limits | T013 |
| Checksum provenance | T014 |
| Quickstart reproducibility | T012 |
| Missing unit tests | T005, T006, T009, T015, T016, T017 (added/updated) |

---  

*All tasks are currently unchecked (`[ ]`).  Once a task’s verification step passes, the corresponding checkbox may be marked as completed.*
