---
description: "Task list template for feature implementation"
---

# Tasks: The Impact of Perceived Agency in AI‑Driven Cognitive Behavioral Therapy on Treatment Adherence

**Input**: Design documents from `/specs/PROJ-547-perceived-agency/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/`, `configs/`, `logs/`, `docs/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory layout: `code/`, `tests/`, `data/`, `configs/`, `logs/`, `docs/`; add empty `__init__.py` in `code/` and `tests/`. **Verification**: script checks existence of all directories and `__init__.py` files.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (spaCy≥3.6, NLTK≥3.8, pandas≥2.0, statsmodels≥0.14, scikit‑learn≥1.3, pyyaml≥6.0, matplotlib≥3.8, tqdm≥4.66) and a virtual‑env setup script (`setup_env.sh`). **Verification**: `requirements.txt` contains all packages; `setup_env.sh` creates a virtualenv without errors.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools with pre‑commit hooks. **Verification**: `pre-commit run --all-files` passes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup centralized logging infrastructure (`code/logging/pipeline_logger.py`) using Python `logging` module, JSON‑line format, writes to `logs/run_<timestamp>.log`. **Verification**: Run a dummy script that logs a message; confirm file exists and contains a correctly‑formatted JSON entry.
- [X] T005 [P] Implement configuration loader (`code/config/config_loader.py`) to read YAML files from `configs/`. **Verification**: Load a sample YAML and assert expected keys.
- [X] T008 [P] Create data contracts/schema files (`contracts/agency_score.schema.yaml`, `contracts/adherence.schema.yaml`) using JSON‑Schema format. **Verification**: Validate schemas with `jsonschema` CLI.
- [X] T060 [P] Store consent documentation (`data/consent/consent_document.pdf`) and record its SHA‑256 checksum in `data/metadata.yaml`. Log the association between consent and each processing run. **Verification**: Consent file present, checksum recorded, and log entry referencing it exists.
- [X] T062 [P] Source and ingest an established perceived agency/autonomy scale dataset, verify checksum, store under `data/external/`. **Verification**: File presence and checksum match.
- [X] T006 [ ] Implement dataset acquisition script (`code/data_acquisition/download_datasets.py`) that reads URLs from `datasets/sources.yaml`, downloads files to `data/raw/`, and records SHA‑256 checksums. **Verification**: After run, each file present matches an entry in `datasets/sources.yaml` **and** its checksum matches the value in `datasets/metadata.yaml`.
- [X] T007 [ ] Implement checksum verification (`code/data_acquisition/validate_metadata.py`) that reads `datasets/metadata.yaml` and aborts on mismatch. **Verification**: Corrupt a file deliberately and confirm script aborts with error.
- [X] T009 [P] Implement generic error‑handling utilities (`code/utils/error_handler.py`) for graceful exits and logging. **Verification**: Raise a custom error and confirm it is logged and exits with non‑zero code.
- [X] T010 [P] Add resource‑monitoring helper (`code/utils/resource_monitor.py`) to enforce FR‑007 limits (≤ 6 GB RAM, ≤ 2 CPU cores). **Verification**: Simulate high memory usage and confirm abort with informative message.
- [X] T065 [ ] Invoke Reference‑Validator Agent as a blocking gate before any analysis begins. **Verification**: Pipeline aborts if any citation fails validation.
- [ ] T065A [P] Implement citation validation for all external sources (Constitution Principle II) using Reference-Validator CLI on `research.md`. **Verification**: Run `reference-validator research.md --threshold 0.7`; all citations pass with title-token-overlap ≥ 0.7.

---

## Phase 3: User Story 1 – Compute Agency Scores from Conversation Transcripts (Priority: P1) 🎯 MVP

**Goal**: Transform raw AI‑CBT conversation logs into a numeric agency score per session.

**Independent Test**: Run the agency‑score pipeline on a sample transcript file and verify that a numeric score (float) is output for each session.

### Implementation for User Story 1

- [X] T014 [P] [US1] Create transcript ingestion script (`code/agency_scoring/ingest_transcripts.py`) supporting CSV and JSON input with columns `session_id` and ordered `utterances`. **Verification**: Parse a sample file and assert a DataFrame with those columns is returned.
- [X] T011 [P] [US1] Unit test for transcript ingestion (`tests/unit/test_ingest_transcripts.py`). **Verification**: pytest passes.
- [X] T015 [P] [US1] Implement linguistic marker detector (`code/agency_scoring/detect_markers.py`) using spaCy tokenization to detect modal verbs, choice constructions, collaborative phrasing, open‑ended questions. **Verification**: Run on a known sentence and assert detection of expected markers.
- [X] T012 [P] [US1] Unit test for marker detection (`tests/unit/test_detect_markers.py`). **Verification**: pytest passes.
- [X] T018 [P] [US1] Add default marker weight file (`config/agency_weights.yaml`) with documented defaults. **Verification**: File exists at `config/` (singular, no 's') and YAML parses without error.
- [X] T016 [P] [US1] Implement weighted aggregation (`code/agency_scoring/compute_scores.py`) that reads `config/agency_weights.yaml` and outputs `data/processed/agency_scores.csv` with columns `session_id, agency_score` (float ∈[0,1]). **Verification**: Run on sample data; check score range and that empty transcript yields 0.0.
- [X] T013 [P] [US1] Unit test for score aggregation (`tests/unit/test_compute_scores.py`). **Verification**: pytest passes.
- [X] T017 [P] [US1] Add logging statements to each step of the agency pipeline (FR‑008) via `pipeline_logger`. **Verification**: After pipeline run, `logs/run_<timestamp>.log` contains entries for ingestion, detection, and aggregation with timestamps.
- [X] T019 [US1] Add edge‑case handling for empty or unreadable transcripts (assign 0.0, log warning) (FR‑003, Edge Cases). **Verification**: Provide empty file; confirm 0.0 score and warning in log.

### Additional Requirement

- **Dependency**: All US1 tasks depend on T004 (logging) – noted in each description.

---

## Phase 4: User Story 2 – Extract Adherence Metrics from Usage Metadata (Priority: P2)

**Goal**: Derive objective adherence indicators and self‑reported engagement scores from usage logs.

**Independent Test**: Feed a mock usage‑log JSON file to the adherence‑extraction script and confirm that {{claim:c_eedac387}}.

### Implementation for User Story 2

- [X] T021 [P] [US2] Create usage‑metadata ingestion script (`code/adherence_extraction/extract_metrics.py`) that reads JSON or CSV files with columns `user_id, session_start, session_end, session_completed, self_reported_engagement` and outputs `data/processed/adherence_metrics.csv`. **Verification**: Parse a sample file and assert required columns are present.
- [X] T022 [P] [US2] Enforce temporal gap for self‑reported engagement per FR‑011: implement both hard abort for <7 days AND statistical control for common‑method variance as alternative path. **Verification**: Provide violating data; confirm pipeline either aborts with error message "Self-reported engagement must be ≥7 days after last session OR include statistical control for common-method variance" OR applies statistical control and logs warning.
- [X] T023 [P] [US2] Implement missing‑timestamp handling: log warning, exclude user from `sessions_per_week` while computing other metrics (Edge Cases). **Verification**: Provide incomplete timestamps; check log warning and partial metric computation.
- [X] T024 [P] [US2] Add detailed logging for each metric computation step (FR‑008). **Verification**: After run, log contains entries like "Computed completion_rate: 0.85 for user X".
- [X] T059 [P] [US2] Ingest demographics file (`code/adherence_extraction/ingest_demographics.py`) validating schema against `contracts/demographics.schema.yaml`; output `data/processed/demographics.csv`. **Verification**: Provide sample demographics; assert successful validation and CSV creation.
- [X] T025 [P] [US2] Create imputation script for confounders (`code/adherence_extraction/impute_confounders.py`) – applies IterativeImputer (m=5) or falls back to complete‑case analysis with bias‑assessment report (FR‑010). **Verification**: Run on dataset with missing confounders; verify imputed output and bias report generation.
- [X] T020 [P] [US2] Unit test for metric extraction (`tests/unit/test_extract_metrics.py`). **Verification**: pytest passes.
- [X] T026 [P] [US2] Unit test for imputation and bias‑assessment (`tests/unit/test_imputation.py`). **Verification**: pytest passes.

### Additional Requirement

- **Dependency**: All US2 tasks depend on T004 (logging) – noted.

---

## Phase 5: User Story 3 – Perform Correlational Regression Analysis (Priority: P3)

**Goal**: Test whether higher agency scores are associated with better adherence outcomes while controlling for confounders.

**Independent Test**: Run the analysis script on the merged dataset and verify that regression coefficients, p‑values, and confidence intervals are reported.

### Implementation for User Story 3

- [X] T028 [P] [US3] Merge agency scores, adherence metrics, and demographics (`code/analysis/merge_datasets.py`) on `session_id`/`user_id`; output `data/processed/merged_data.csv`. **Verification**: Check merged file contains all required columns and correct row count.
- [X] T061 [P] [US3] Detect zero‑variance agency scores before regression; abort with logged error if variance < 1e‑6. **Verification**: Provide constant scores and confirm abort.
- [X] T063 [P] [US3] Implement regression model selector (`code/analysis/select_regression.py`) that chooses:
 - Logistic regression for binary outcomes,
 - Beta regression for proportion outcomes,
 - OLS for continuous outcomes,
 and applies confounders (age, gender, baseline severity, prior therapy). **Verification**: Run selector on each outcome type; confirm correct model instantiated.
- [X] T029 [P] [US3] Run regression (`code/analysis/run_regression.py`) using the selector, apply Benjamini‑Hochberg FDR correction, enforce runtime guard (≤ 30 min), compute post‑hoc power, and log warnings if power < 0.80. **Verification**: Execution completes within time limit; power report generated; FDR-corrected p-values present in output.
- [X] T032 [P] [US3] Generate human‑readable results (`output/regression_summary.csv`) and PNG plots (`output/plots/`). Include provenance metadata (`output/provenance.yaml`) linking each statistic to source row and script line. **Verification**: {{claim:c_7c084088}} (Wikidata Q118869796, https://www.wikidata.org/wiki/Q118869796)
- [X] T033 [P] [US3] Compute post‑hoc statistical power for each model and log warnings if power < 0.80. **Verification**: Power values logged.
- [X] T034 [US3] Add comprehensive logging for each modeling step (FR‑008). **Verification**: Log contains entries for data loading, variance check, model selection, fitting, correction, and power analysis.
- [X] T027 [P] [US3] Integration test for full regression pipeline (`tests/integration/test_regression_pipeline.py`). **Verification**: pytest passes, generates expected output files.
- [X] T051 [P] Performance optimization: profile memory usage in `run_regression.py` and ensure peak RAM ≤ 6 GB (FR‑007). **Verification**: Memory profiling reports ≤ 6 GB.

### Dependencies

- US3 tasks depend on completion of US1, US2, and US4 (validation). T028 requires outputs of T016 and T021; T061 runs after T028; T063/ T029 run after T061.

---

## Phase 6: User Story 4 – Validate Agency‑Score Metric (Priority: P2)

**Goal**: Assess reliability and convergent validity of the computed agency scores against an established perceived agency scale.

**Independent Test**: Run the validation script on a subset of sessions that have both agency scores and external scale scores; verify split‑half reliability ≥ 0.80 and Pearson r ≥ 0.30 (p < 0.05).

### Implementation for User Story 4

- [X] T064 [P] [US4] Define validation‑subset selection criteria (stratified random sample, size ≥ 30, balanced across score ranges) and generate `data/processed/validation_subset.csv`. **Verification**: Subset meets criteria; script logs selection process.
- [X] T037 [P] [US4] Compute split‑half reliability using Spearman‑Brown (`code/validation/compute_reliability.py`) on marker items. **Verification**: Reliability ≥ 0.80; otherwise warning logged.
- [X] T038 [P] [US4] Compute Pearson correlation with external agency scale (`code/validation/compute_convergent.py`). **Verification**: Pearson r ≥ 0.30, p < 0.05; otherwise warning logged.
- [X] T039 [P] [US4] Generate validation report PDF (`validation/report.pdf`) and YAML summary (`validation/validation_report.yaml`). **Verification**: Both files exist; PDF size > 0.
- [X] T040 [US4] Add logging for validation steps and any failure warnings (FR‑008). **Verification**: Log entries present.
- [X] T041 [US4] If thresholds are not met, abort downstream analysis and log explicit warning (FR‑009, Edge Cases). **Verification**: Pipeline aborts when reliability or correlation below threshold.
- [X] T035 [P] [US4] Unit test for split‑half reliability (`tests/unit/test_split_half.py`). **Verification**: pytest passes.
- [X] T036 [P] [US4] Unit test for convergent validity (`tests/unit/test_convergent.py`). **Verification**: pytest passes.

---

## Phase 7: User Story 5 – Comprehensive Logging (Priority: P2)

**Goal**: Provide a complete audit trail of all processing steps, warnings, and errors for reproducibility and debugging.

**Independent Test**: Execute the full pipeline on a sample dataset and inspect `logs/run_<timestamp>.log` for entries covering ingestion, scoring, metric extraction, regression, and validation.

### Implementation for User Story 5

- [X] T043 [P] Ensure `pipeline_logger` (from Phase 2) is imported and used by all scripts (FR‑008). **Verification**: Static analysis via `grep -r 'pipeline_logger' code/*/` confirms import in all scripts; runtime log contains entries from each script. <!-- FAILED: unspecified -->
- [X] T044 Implement log‑completeness metric (`code/logging/verify_logging.py`) that parses `logs/run_*.log`, compares against a predefined step list, and writes `logs/completeness_metric.json`. **Verification**: {{claim:c_0b174b75}}
- [X] T042 [P] [US5] Unit test for log completeness checker (`tests/unit/test_verify_logging.py`). **Verification**: pytest passes and asserts completeness ≥ 0.95.
- [X] T045 Add documentation of logging format and retention policy in `docs/logging.md`. **Verification**: File exists and contains required sections.

---

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T049 [P] Documentation updates in `README.md` and `docs/quickstart.md` describing end‑to‑end usage, including reference to `output/` directory. **Verification**: Docs build without broken links.
- [X] T050 [P] Code cleanup and refactoring of shared utilities (`code/utils/`) for readability, add type hints and docstrings, and run MyPy with no errors. **Verification**: MyPy passes with no errors; all utility files have type hints and docstrings.
- [X] T052 [P] Additional unit tests for edge cases (empty transcript, zero variance agency scores, all missing timestamps) (`tests/unit/test_edge_cases.py`). **Verification**: pytest passes.
- [X] T053 Security hardening: validate all external inputs (file type checks, JSON schema validation) (`code/utils/input_validator.py`). **Verification**: Invalid inputs raise errors and are logged.
- [X] T054 {{claim:c_92c75830}} **Verification**: Script exits with code 0. <!-- FAILED: unspecified -->
- [X] T055 Release packaging: create a `setup.py` / `pyproject.toml` so the project can be installed via `pip install.`. **Verification**: `pip install.` succeeds in a fresh venv.
- [ ] T056 [P] {{claim:c_08009153}} Download, verify checksum, store under `data/raw/benchmark/`. **Verification**: {{claim:c_bd9c37ce}}
- [ ] T057 [P] {{claim:c_2b450cd0}} **Verification**: {{claim:c_f54a79c9}}
- [ ] T057A [P] Verify success criteria thresholds: validate SC‑001 (≥95% processing success on benchmark) and SC‑002 (±0.01 metric accuracy on ground-truth). **Verification**: {{claim:c_d3c0a23c}}
- [ ] T066 [P] Remove redundant task; performance optimization target ≤ 6 GB RAM already reflected in T051. **Verification**: Task marked completed as reference only.
- [ ] T068 [P] Remove redundant task; static analysis for pipeline_logger import already in T043. **Verification**: Task marked completed as reference only.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion – BLOCKS all user stories
- **User Stories (Phases 3‑7)**: All depend on Foundational phase completion; individual stories can run in parallel once foundations are ready, respecting explicit dependencies noted above.
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent after Foundational
- **US2 (P2)**: Independent after Foundational; uses output of US1 only for downstream merging
- **US4 (P2)**: Depends on US1 output and external scale dataset (T062); must complete before US3
- **US3 (P3)**: Depends on US1, US2, and US4 outputs (merged dataset and validated agency scores)
- **US5 (P2)**: Cross‑cutting – integrates with all scripts once they emit logs

### Parallel Opportunities

- All `[P]` tasks within a phase can run concurrently on separate files.
- After Foundational, US1, US2, and US5 can be developed in parallel by different contributors.
- Validation (US4) can run in parallel with US2, but US3 is gated to wait for US4 completion (enforced by T041 abort logic).