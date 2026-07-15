# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets

**Input**: Design documents from `/specs/001-assessing-statistical-power/`
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 Create project directory tree (`mkdir -p projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils projects/PROJ-234-assessing-statistical-power-in-reproduci/data/raw projects/PROJ-234-assessing-statistical-power-in-reproduci/data/processed projects/PROJ-234-assessing-statistical-power-in-reproduci/tests/unit projects/PROJ-234-assessing-statistical-power-in-reproduci/tests/contract projects/PROJ-234-assessing-statistical-power-in-reproduci/docs projects/PROJ-234-assessing-statistical-power-in-reproduci/contracts`) **and verify** each directory exists (`test -d <dir> && echo OK`).
- [X] T002 Initialize Python 3 project with `requirements.txt` containing exactly:
 ```
 pandas==2.0.3
 openml==0.14.2
 statsmodels==0.14.1
 requests==2.31.0
 matplotlib==3.8.0
 pytest==7.4.0
 beautifulsoup4==4.12.2
 ```
 **and verify** installability with a dry‑run (`pip install -r requirements.txt --dry-run`).
- [X] T003 [P] Configure linting by creating `pyproject.toml` with `[tool.black] max-line-length=88 target-version=['py310']` and `.flake8` with `max-line-length=88`. **Verify** by running `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [X] T004 Setup package init files: create `code/__init__.py`, `tests/__init__.py`, `contracts/.gitkeep`, `data/.gitkeep`. **Verify** files exist and are non‑empty (`test -s <file>`).
- [X] T005 [P] Create `contracts/dataset_metadata.schema.yaml` (see spec entities) and **verify** with `yamllint` and a simple schema load test.
- [X] T006 [P] Create `contracts/power_audit_result.schema.yaml` (see spec entities) and **verify** similarly.
- [ ] T007 Implement `code/utils/api_client.py` with OpenML connection and exponential backoff retry logic (handles HTTP 429). **Unit test** `tests/unit/test_api_client.py::test_api_client_retry_on_429` validates backoff.
- [ ] T008 Implement `code/utils/oa_checker.py` to validate Open Access status of publication links (uses DOI content‑type checks). **Unit test** `tests/unit/test_oa_checker.py::test_oa_status` validates behavior.
- [X] T009 Implement logging configuration in `code/utils/logging_config.py` with:
 ```python
 import logging
 logging.basicConfig(
 filename='data/ingest.log',
 level=logging.INFO,
 format='%(asctime)s %(levelname)s %(name)s %(message)s')
 ```
 **Verify** by emitting a test log entry and checking file existence.
- [ ] T009.5 Implement optional auxiliary module `code/05_a_priori_power_analysis.py` providing a CLI `a_priori_power --alpha <float> --effect-size <float> --sample-size <int>` that returns required power. **Note**: This module is not part of core acceptance criteria but satisfies FR‑006 for future use. **Unit test** `tests/unit/test_a_priori_cli.py::test_cli_success` checks exit code 0.
- [ ] T010 Create `contracts/report.schema.yaml` defining final audit report JSON structure (used by later contract tests).

**Checkpoint**: Foundations ready – user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 – Retrieve and Filter Top Public Datasets (Priority: P1) 🎯 MVP

**Goal**: Connect to OpenML API, retrieve top classification datasets, and filter for those with publication links or task IDs.

**Independent Test**: Execute `code/01_ingest_openml.py` and verify `data/raw/openml_metadata_filtered.json` contains a list of entries (max 50) with non‑null `publication_link` **or** `task_id`.

- [ ] T010 [P] [US1] Unit test `tests/unit/test_api_client.py::test_api_client_retry_on_429` (already covered by T007). <!-- FAILED: unspecified -->
- [ ] T011 [P] [US1] Contract test `tests/contract/test_schemas.py::test_dataset_metadata_schema` validates `data/raw/openml_metadata_filtered.json` against `contracts/dataset_metadata.schema.yaml`.
- [X] T012 [US1] Implement `code/01_ingest_openml.py` with function:
 ```python
 def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
...
 ```
 Save raw API response to `data/raw/openml_metadata_raw.json`.
- [ ] T013 [US1] In the same script, filter raw metadata where `publication_link` **or** `task_id` is present. Save filtered list to `data/raw/openml_metadata_filtered.json`. **Verify** filter condition explicitly.
- [ ] T014 [US1] Validate filtered data for duplicate `dataset_id`s, keep entry with highest `download_count`, and generate SHA‑256 checksums written to `data/raw/checksums.txt`. **Verify** checksum file exists.
- [~] T015 [US1] Log extraction statistics as JSON to `data/ingest.log`:
 ```json
 {"total_fetched": X, "filtered": Y, "type_distribution": {"binary": A, "multiclass": B}}
 ```
- [~] T016 [US1] Ensure no duplicate IDs remain; raise `ValueError` if any remain after resolution.

**Checkpoint**: US1 functional and independently testable.

---

## Phase 4: User Story 2 – Extract Statistical Parameters via Full‑Text Parsing (Priority: P2)

**Goal**: Parse full‑text (or abstract fallback) to extract sample size (N) and effect sizes (Cohen’s d, F‑statistic).

**Independent Test**: Run `code/02_parse_publications.py` on a known OA subset and verify `data/processed/extracted_params.json` matches schema.

- [X] T018 [P] [US2] Unit test `tests/unit/test_parsers.py::test_regex_patterns` checks regexes for `N=\\d+`, `Cohen's d=\\d+\\.\\d+`, `F\\(\\d+,\\d+\\)=\\d+\\.\\d+`.
- [~] T019 [P] [US2] Contract test `tests/contract/test_schemas.py::test_extracted_params_schema` validates `data/processed/extracted_params.json` against a new schema (`contracts/extracted_params.schema.yaml` – created in T005‑T006).
- [X] T020 [US2] Implement `code/utils/parsers.py` exposing:
 - `extract_sample_size(text: str) -> int`
 - `extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int,int]]]`
 Return includes `metric_type` (`"Cohen's d"` or `"F"`), and for F also `degrees_of_freedom`.
- [~] T021 [US2] Implement `code/02_parse_publications.py` that iterates over `data/raw/openml_metadata_filtered.json`, fetches full‑text (see T022), and writes extracted rows to `data/processed/extracted_params.json`. Use the JSON schema defined in contracts. <!-- ATOMIZE: requested -->
- [~] T022 [US2] Fetch full‑text from `publication_link` using `requests.get` (timeout 10 s). Before download, call `oa_checker.is_open_access(url)`; if False, mark status `"paywalled"` and skip extraction (log accordingly). **Verify** with a mock OA check in unit test.
- [ ] T021.1 [US2] After fetching, validate that the publication actually reports a **univariate** effect size (i.e., metric_type is one of `"Cohen's d"` or `"F"`). If not, log `"insufficient data"` and treat as `"unparseable"` – this satisfies FR‑007.
- [~] T023 [US2] If full‑text fetch fails or is paywalled, attempt abstract retrieval via DOI metadata API; parse using same regexes. Mark source as `"abstract"` if used.
- [~] T024 [US2] Edge‑case handling: for entries where no metric can be extracted, record status `"unparseable"` in the JSON and log a warning; **do not crash**.
- [~] T026 [US2] Save each extracted record with fields:
 `dataset_id, sample_size, effect_size, metric_type, degrees_of_freedom (optional), source_url, status`.
- [ ] T027 [US2] Generate `data/processed/extraction_stats.json` with keys `success_rate`, `failure_reasons` (counts of `"paywalled"`, `"unparseable"`, `"insufficient data"`).
- [ ] T028.1 [US2] Compute sensitivity delta:
 ```
 delta = full_text_success_rate - (full_text_plus_abstract_success_rate)
 ```
 Save as `data/processed/sensitivity_delta_report.json` with fields `full_text_rate`, `combined_rate`, `delta`. This satisfies FR‑008.

**Checkpoint**: US2 functional and independently testable.

---

## Phase 5: User Story 3 – Compute Observed Power, MDES, and Generate Audit Report (Priority: P3)

**Goal**: Calculate observed statistical power **and** Minimum Detectable Effect Size (MDES), report observed‑power fraction < 0.8 (spec) and MDES distribution (plan pivot).

**Independent Test**: Run `code/03_compute_sensitivity.py` on synthetic parameters and verify both power and MDES values; run `code/04_generate_report.py` and check histogram, MDES distribution, and disclaimer presence.

- [~] T029 [P] [US3] Unit test `tests/unit/test_sensitivity.py::test_compute_observed_power_and_mdes` using synthetic input `N=100, d=0.2` expects observed power ≈0.30 (±0.05) and MDES ≈0.25 (±0.05).
- [~] T030 [P] [US3] Contract test `tests/contract/test_schemas.py::test_final_report_schema` validates `data/processed/audit_report.json` against `contracts/report.schema.yaml`.
- [X] T031 [US3] Implement `code/03_compute_sensitivity.py`:
 - Function `compute_observed_power(params: StatisticalParameters) -> float` using `statsmodels.stats.power.TTestIndPower`.
 - Function `compute_mdes(params: StatisticalParameters, alpha: float = 0.05, power: float = 0.8) -> float` (inverse power calculation).
 - Process all entries from `extracted_params.json`, compute both metrics, clamp observed power to ≤ 1.0, and store results.
- [~] T032 [US3] For entries with metric_type `"F"` and provided degrees of freedom, convert to Cohen’s d using standard formula before power/MDES calculations. Clamp any power > 1.0 to 1.0 and log a warning.
- [ ] T033 [US3] Save results to `data/processed/power_audit_results.json` with schema:
 `{dataset_id, observed_power, mdes, threshold_met (observed_power≥0.8), status}`.
- [ ] T039.0 [US3] Calculate fraction of studies with observed power < 0.8:
 ```
 observed_power_below_threshold = count(observed_power < 0.8) / total
 ```
 Write to `data/processed/success_metrics.json` under key `observed_power_below_threshold`.
- [ ] T039.1 [US3] Extend `success_metrics.json` to also include MDES‑related metric:
 `mdes_above_threshold = count(mdes > 0.2) / total` (threshold chosen as illustrative). This provides a plan‑aligned success indicator.
- [ ] T036 [US3] Generate MDES distribution histogram (`mdes_histogram.png`) and summary statistics (median, IQR) saved to `data/processed/mdes_summary.json`.
- [X] T034 [US3] Implement `code/04_generate_report.py` to aggregate `power_audit_results.json`, `extraction_stats.json`, `sensitivity_delta_report.json`, and `mdes_summary.json`. Produce histogram `power_histogram.png` (bins=20, color=steelblue) and embed in markdown.
- [ ] T035 [US3] Append mandatory disclaimer at the end of `audit_report.md`:
 ```
 **Disclaimer:** Observed power is a monotone function of the p‑value and should not be used for post‑hoc validation (Hoenig & Heisey).

The research question is to determine whether observed power is appropriate for post‑hoc validation. The method involves a theoretical analysis of the monotonic relationship between observed power and p‑values.
 ```
- [ ] T037 [US3] Assemble final audit report (`data/processed/audit_report.md`) with sections:
 1. Overview
 2. Dataset Ingestion Summary
 3. Extraction Statistics (including sensitivity delta)
 4. Observed Power Results (histogram, fraction < 0.8)
 5. MDES Results (histogram, summary)
 6. Disclaimer
 Ensure all figures are referenced and linked.

**Checkpoint**: All user stories now fully functional and independently testable.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple stories and final validation.

- [ ] T038 [P] Update `docs/constitution.md` with markdown links to `research.md`, `plan.md`, and `quickstart.md` (format `[Research](../research.md)`, etc.).
- [ ] T039.2 [P] Run full‑pipeline integration test (`pytest -m integration`) on a small representative subset (first few filtered datasets). **Success** = exit code 0 and generated `audit_report.md` matches stored checksum.
- [ ] T040 [P] Validate `quickstart.md` by executing the documented CLI steps (`./run_pipeline.sh`) and confirming generated `audit_report.md` checksum equals the value recorded in `quickstart.md`.
- [ ] T041 [P] Refactor `code/utils/`:
 - Extract OA‑check logic to a shared helper.
 - Remove duplicate logging configuration (use `logging_config.py` everywhere).
 - Ensure no circular imports; run `flake8` import‑order check.
- [ ] T042 [P] Run performance harness:
 - Execute pipeline on top datasets while recording wall‑clock time (`/usr/bin/time -v`) and peak RSS via `memory_profiler`.
 - Write results to `data/processed/performance_metrics.json`.
- [ ] T043 [P] Run full pipeline on the 10‑dataset subset; verify all tasks complete without error and that `audit_report.md` is produced.
- [ ] T044 [P] Assert peak RSS < 7 GB using `memory_profiler`; fail with clear message if exceeded.
- [ ] T045 [P] Assert total runtime < 6 h using the time measurement from T042; fail with clear message if exceeded.

**Dependencies & Execution Order**

- Phase 1 → Phase 2 → (US1) → (US2) → (US3) → Phase 6.
- Within Phase 4: T022 (fetch) **must precede** T021.1 (validation).
- Within Phase 5: T031 → T039.0 → T039.1 → T036 → T034 → T035 → T037 (report generation).
- All `[P]` tasks may run concurrently where file‑level independence is guaranteed.

**Parallel Opportunities**

- Phase 1 and Phase 2 tasks marked `[P]` can be executed in parallel.
- After foundational completion, US1 can start while tests for US2 are authored, etc.

**Implementation Strategy**

- MVP: complete Phase 1 → Phase 2 → US1 → validate → proceed to US2 → validate → US3 → validate → Polish.
- Incremental delivery allows early demo of dataset ingestion and extraction before full analysis.

**Verification**

- Each task includes an explicit “verify” clause (file existence, schema validation, unit‑test pass, log entry, checksum) ensuring deterministic CI execution.
- All tasks respect CPU‑only constraints, use only `statsmodels` (CPU), and keep memory < 7 GB.
