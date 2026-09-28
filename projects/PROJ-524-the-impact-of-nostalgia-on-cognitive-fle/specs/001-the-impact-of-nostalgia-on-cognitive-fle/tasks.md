# Tasks: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Input**: Design documents from `/specs/001-nostalgia-cognitive-fle/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup & Foundational (Contracts & Data Model)

**Purpose**: Project initialization, data model definition, and contract generation.

- [ ] T001 [P] Create all required data directories: `data/raw/`, `data/processed/`, `data/results/`, `data/stimuli/`, `contracts/`, `code/`, `tests/`, `paper/`. **Depends on**: None.

- [X] T002 [P] Create `requirements.txt` with pinned versions for: pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, requests, pytest, black, ruff. **Depends on**: T001.

- [X] T003a [P] Create `pyproject.toml` with an empty `[tool.black]` and `[tool.ruff]` section skeleton. **Depends on**: T002.
- [X] T003b [P] Verify `pyproject.toml` exists and explicitly contains populated `[tool.black]` (with `line-length=88`) and `[tool.ruff]` (with `lint.select = ["E", "F"]`) configuration sections. **Depends on**: T003a.

- [X] T004 [P] Implement `code/utils.py` with checksum (SHA-256) helpers, logging setup, and versioning logic. **Depends on**: T003b.
- [X] T005 [P] Setup `code/reference_validator.py` to validate citations and enforce title overlap ≥ 0.7. **Depends on**: T004. **Note**: Implement Welch's independent samples t-test logic as mandated by Spec FR-002.
- [X] T006 [P] Create base configuration management in `code/config.py` (env vars, paths). **Note**: Do not store runtime flags here. **Depends on**: T004.
- [ ] T007 [P] Setup `contracts/` directory structure (files generated in Phase 1). **Depends on**: T001.

- [ ] T020b-1 [P] **GENERATE DATA MODEL (SKELETON)**: Generate `specs/001-nostalgia-cognitive-fle/data-model.yaml` skeleton with basic structure for entities (Participant, Stimulus, Metric) based on Spec Section 5. **Depends on**: T007.
- [ ] T020b-2 [P] **POPULATE DATA MODEL**: Populate `specs/001-nostalgia-cognitive-fle/data-model.yaml` with specific entities, relationships, and optional fields (MMSE) from the Spec. **Depends on**: T020b-1.
- [ ] T020b-3 [P] **VALIDATE DATA MODEL**: Validate `specs/001-nostalgia-cognitive-fle/data-model.yaml` consistency against the Spec. **Depends on**: T020b-2.
- [ ] T020a-1 [P] **GENERATE CONTRACTS (YAML)**: Generate `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on the Data Model (T020b-3). Validate that `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, and optional `MMSE` are defined. **Depends on**: T020b-3.
- [ ] T020a-2 [P] **VALIDATE CONTRACTS**: Verify `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` contain all required fields defined in T020a-1 and match the Data Model. **Depends on**: T020a-1.
- [ ] T020c [P] **GENERATE QUICKSTART**: Create `specs/001-nostalgia-cognitive-fle/quickstart.md` with installation instructions, dependency installation, and a "Hello World" example to run the ingestion pipeline on a sample dataset. **Depends on**: T002, T003a, T020a-2.

**Checkpoint**: Foundation and Contracts ready - user story implementation can now begin

---

## Phase 2: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest publicly available WCST/Executive Function data and nostalgia stimuli, validate age ≥ 65, and produce a clean, aligned dataframe.

**Independent Test**: The system can be fully tested by running the data loader script on a source dataset containing at least 100 records and verifying the output contains a dataframe with all valid participant records found, matching stimulus IDs, and non-null cognitive metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Contract test for schema validation in `tests/contract/test_dataset_schema.py`. **Depends on**: T020a-2.
- [X] T009 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py`. **Depends on**: T008.

### Implementation for User Story 1

- [ ] T010a [US1] **IMPLEMENT INGESTION LOGIC**: Implement `code/ingestion.py` with functions to fetch data from a **fixed** canonical source (OpenML ID or specific HuggingFace path). **Logic**: The code must attempt to fetch real data; if fetch fails, it must raise an exception (fail loud). **Do NOT include execution logic or fallback generation in this task.** **Depends on**: T004-T007, T020a-2.
- [ ] T010b [US1] **EXECUTE INGESTION & GENERATE ARTIFACT**: Run `code/ingestion.py` (from T010a). **If real fetch succeeds**: Save raw dataset to `data/raw/raw_dataset.csv`. **If real fetch fails**: The script must raise an error (per Constitution Principle III). **Do NOT generate synthetic data here unless explicitly mandated by a separate, distinct task for simulation-only validation.** **Validate schema** of the saved file contains `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`. **Depends on**: T010a.
- [X] T010c [P] [US1] **PIPELINE ORCHESTRATOR**: Implement `code/main.py` to orchestrate the ingestion pipeline. **Depends on**: T010b, T010a.
- [X] T011 [P] [US1] Implement data validation logic in `code/ingestion.py`: filter `age >= 65`, exclude missing `stimulus_type`, log `ERR_MISSING_AGE_FIELD`. **Depends on**: T010b.
- [ ] T012a [P] [US1] **AGE EXCLUSION**: Filter `data/raw/raw_dataset.csv` for `age >= 65`. Write filtered data to `data/processed/cleaned_age_filtered.csv`. Write exclusion count to `data/processed/exclusion_counts.json` with key `ERR_MISSING_AGE_FIELD`. **Depends on**: T010b.
- [ ] T012b [P] [US1] **SCORE EXCLUSION**: Filter `data/processed/cleaned_age_filtered.csv` for non-null `perseverative_errors` and `categories_completed`. Write filtered data to `data/processed/cleaned_score_filtered.csv`. Write exclusion count to `data/processed/exclusion_counts.json` with key `ERR_MISSING_SCORE`. **Depends on**: T012a.
- [ ] T012d [P] [US1] **MMSE FLAG**: **Read from `data/raw/raw_dataset.csv` (the raw input)**. Validate presence of 'MMSE' column. **Check if column exists AND contains at least one non-null value in the *raw* input using `df['MMSE'].notna().any()`**. **Write `has_mmse` (True/False) to `data/processed/mmse_flag.json`**. If column missing OR all null, set `has_mmse=False` and log `ERR_MMSE_MISSING`. If present and non-null, set `has_mmse=True`. **Depends on**: T010b, T012b.
- [ ] T012e [US1] **MMSE EXCLUSION AND ROBUSTNESS PREP**: **Read `has_mmse` from `data/processed/mmse_flag.json`** (produced by T012d). **CRITICAL EXECUTION ORDER**: Ensure T012b -> T012d -> T012e to avoid race conditions.
 - If `has_mmse=True`: Filter `data/processed/cleaned_score_filtered.csv` for `MMSE >= 24` and write to `data/processed/cleaned_dataset.csv` (Primary).
 - If `has_mmse=False`: Copy `data/processed/cleaned_score_filtered.csv` to `data/processed/cleaned_dataset.csv` (Primary).
 - **CRITICAL**: In ALL cases, generate `data/processed/cleaned_dataset_no_mmse.csv` by copying `data/processed/cleaned_score_filtered.csv` (to preserve the pre-MMSE state for sensitivity analysis).
 - Write exclusion counts to `data/processed/exclusion_counts.json`. **Depends on**: T012d, T012b.
- [ ] T012c [P] [US1] **GENERATE EXCLUSION LOG**: Read exclusion counts from `data/processed/exclusion_counts.json` (from T012a, T012b, T012e) and write `data/processed/exclusion_log.json` with keys `ERR_MISSING_AGE_FIELD`, `ERR_MISSING_SCORE`, `ERR_MMSE_IMPAIRED`, and `SIMULATION_FALLBACK` (if applicable). **Ensure file write order: T012a -> T012b -> T012e -> T012c.** **Depends on**: T012a, T012b, T012e.
- [ ] T014a [P] [US1] **GENERATE CLEANED DATASET**: Use `data/processed/cleaned_dataset.csv` (from T012e) as the primary input. **Copy this file to `data/processed/final_cleaned_dataset.csv`**. Columns: `participant_id`, `stimulus_type` (nostalgia/control), `perseverative_errors`, `categories_completed`, `age`. **Depends on**: T012c, T012e.
- [ ] T014b [P] [US1] **VALIDITY METRICS**: Calculate percentage of valid records (age >= 65, non-null metrics, MMSE >= 24 if available) vs total raw input records from `data/raw/raw_dataset.csv`. Write the calculated percentage to `data/processed/validity_metrics.json`. **Depends on**: T012c.
- [ ] T015a [P] [US1] **GENERATE METADATA**: Create `data/raw/metadata.json` with keys `dataset_source`, `validation_study_doi` (if found in source, **set to null if not found**), `stimuli_checksums` (SHA-256 of all files in `data/stimuli/`), and `simulation_mode` (boolean). **If `data/stimuli/` is empty and `simulation_mode=True`, set `stimuli_checksums` to null and log `INFO_SIMULATION_NO_STIMULI`**. **This task MUST run regardless of data fetch success**. **Depends on**: T004, T007.
- [ ] T015 [P] [US1] **STIMULUS INTEGRITY**: **Read `simulation_mode` from `data/raw/metadata.json`** (produced by T015a). **CRITICAL**: T015a must run before T015.
 - **Check**: Verify `data/stimuli/` is non-empty before attempting to read checksums if `simulation_mode` is false. If empty, log `ERR_STIMULUS_EMPTY` and halt.
 - If `simulation_mode=True` AND `data/stimuli/` is empty: Generate placeholder stimuli (random noise) to satisfy schema, set `stimuli_checksums` to their hash, and log `INFO_SIMULATION_NO_STIMULI`. **Do NOT halt**.
 - If `simulation_mode=False`: Validate stimulus files in `data/stimuli/` against `data/raw/metadata.json` checksums. If mismatch, log `ERR_STIMULUS_CORRUPT` and halt. If missing files, log `ERR_STIMULUS_MISSING` and halt.
 - **CRITICAL**: If validation passes (or simulation mode), update `state/state.yaml` `artifact_hashes` with the stimulus checksums. **Depends on**: T015a, T010b.
- [ ] T015b [P] [US1] **STIMULUS VALIDATION**: If `data/raw/metadata.json` contains `validation_study_doi` (and not null), log `INFO_STIMULUS_VALIDATED`. Else, log `WARN_STIMULUS_NO_VALIDATION`. **Depends on**: T015a.
- [ ] T042 [P] [US1] **ENFORCE STREAMING**: Update `code/ingestion.py` to use `datasets.load_dataset(..., streaming=True)` for any dataset > 100MB to ensure RAM compliance on the specified runner. **Depends on**: T010a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Execute statistical comparison of cognitive flexibility metrics between nostalgia and control conditions using Welch's t-test (between-subjects), calculate effect sizes, and apply corrections.

**Independent Test**: The analysis can be fully tested by running the statistical module on a synthetic dataset with known effect sizes and verifying the output correctly identifies the calculated p-value and calculates the Cohen's d within a reasonable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for statistical output schema in `tests/contract/test_analysis_output.py`. **Depends on**: T020a-2.
- [ ] T017 [P] [US2] Integration test for statistical pipeline with synthetic data in `tests/integration/test_analysis.py`. **Depends on**: T016.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/analysis.py` statistical functions: **Welch's independent samples t-test (NOT paired)**. **Input Requirement**: Requires two distinct groups defined by `stimulus_condition` (nostalgia vs control) in the input dataframe. **NOTE: This aligns with spec FR-002 (Welch's t-test) and Plan.md between-subjects design.** The test must be applied to **BOTH** `perseverative_errors` **AND** `categories_completed`. **Depends on**: T014a.
- [ ] T019 [P] [US2] **BONFERRONI CORRECTION**: Implement multiple-comparison correction (Bonferroni) for `perseverative_errors` and `categories_completed`. Use `scipy.stats.multipletests` with `method='bonferroni'` to adjust p-values. Report corrected p-values. **Depends on**: T018.
- [ ] T020 [P] [US2] **EFFECT SIZE**: Calculate and report Cohen's d with 95% confidence intervals for all primary comparisons using `statsmodels.stats.weightstats.tt_ind_solve_power` or `scipy.stats`. **Depends on**: T018.
- [ ] T021 [P] [US2] Calculate statistical power and Minimum Detectable Effect Size (MDES) for the observed effect; **Append power and MDES values to `data/results/statistical_report.json`**. **Depends on**: T020.
- [ ] T022 [P] [US2] Generate `data/results/statistical_report.json` containing p-values, corrected p-values, effect sizes, **power**, **MDES**, and power analysis results. **Depends on**: T019, T020, T021.
- [ ] T023 [P] [US2] **ERROR HANDLING**: Add error handling for cases where variance is zero or sample size is too small (< 10 per group). Implement `try/except` blocks around `scipy.stats` calls. Log `ERR_ZERO_VARIANCE` or `ERR_SMALL_SAMPLE` and skip affected test. **Depends on**: T018.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Sensitivity Analysis and Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis by sweeping significance thresholds and checking robustness against cognitive impairment exclusions.

**Independent Test**: The system can be tested by running the sensitivity module with a predefined set of thresholds (e.g., low, medium, and high values) and verifying the output table shows how the "significance" status changes across these values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_output.py`. **Depends on**: T020a-2.
- [ ] T025 [P] [US3] Integration test for sensitivity analysis pipeline in `tests/integration/test_sensitivity.py`. **Depends on**: T024.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement sensitivity sweep in `code/analysis.py`: test thresholds including **explicitly: 0.01, 0.04, 0.05, 0.06, 0.10**. **Depends on**: T022.
- [ ] T027a [P] [US3] **MMSE ROBUSTNESS DATA PREP**: **Read from `data/processed/cleaned_dataset.csv` (Primary, with MMSE) and `data/processed/cleaned_dataset_no_mmse.csv` (Robustness, without MMSE)**. **CRITICAL LOGIC**: If `has_mmse=False`, the Primary and Robustness datasets are identical. In this case, **SKIP** the robustness comparison and log `WARN_MMSE_MISSING`. **Depends on**: T012e.
- [ ] T027b [P] [US3] **MMSE ROBUSTNESS ANALYSIS**: **Only if T027a did not skip**: Re-run analysis (T018 logic, but independent) on `data/processed/cleaned_dataset_no_mmse.csv` (output of T027a/T012e). Write results to `data/results/robustness_report.json`. **Note: This is a sensitivity check comparing with and without MMSE exclusion**. **Depends on**: T027a.
- [ ] T027c [P] [US3] **COMPARE ROBUSTNESS**: **Only if T027a did not skip**: Explicitly compare the results of the primary analysis (T022, with MMSE) vs. the robustness analysis (T027b, without MMSE). Generate `data/results/sensitivity_comparison.json` highlighting any differences in significance or effect size. **Depends on**: T022, T027b.
- [ ] T028 [P] [US3] **SENSITIVITY REPORT**: Generate `data/results/sensitivity_report.json` with significance status per threshold and subset comparison. **Depends on**: T026, T027c.
- [ ] T029 [P] [US3] **BORDERLINE FLAG**: Add logic to flag "sensitive to threshold choice" if p-value falls in the range **0.04 <= p <= 0.06** (using float comparison tolerance 1e-9). Output a binary flag `is_sensitive_to_threshold` in `data/results/sensitivity_report.json`. **Depends on**: T028.
- [ ] T030 [P] [US3] **FINAL SENSITIVITY SUMMARY**: Update final report to include sensitivity analysis summary and stability metrics. **Depends on**: T028, T029.
- [ ] T041 [P] [US3] **STRENGTHEN ROBUSTNESS**: Ensure the sensitivity analysis in `code/analysis.py` explicitly logs the "borderline" range (0.04-0.06) and outputs the binary flag `is_sensitive_to_threshold` in `data/results/sensitivity_report.json` as required by FR-005. **Depends on**: T026.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T031a [P] **README INSTALLATION**: Update `README.md` with installation instructions, dependencies, and usage examples. **Depends on**: T002, T020c.
- [ ] T031b [P] **API DOCS**: Add API docs for `code/ingestion.py` and `code/analysis.py` functions. **Depends on**: T018, T010a.
- [ ] T032a [P] **REFACTOR ANALYSIS**: Refactor `code/analysis.py` to reduce cyclomatic complexity to < 10. **Method**: Extract data cleaning logic into `clean_data()` function in `code/ingestion.py` and split `run_analysis()` into `compute_stats()` and `generate_report()`. **Depends on**: T022.
- [ ] T032b [P] **REFACTOR INGESTION**: Refactor `code/ingestion.py` to improve modularity and error handling. **Method**: Split `fetch_data()` and `validate_schema()` into separate modules. **Depends on**: T010a.
- [ ] T033a [P] [US1] Unit test: `test_cleaning_filters_age` in `tests/unit/test_cleaning.py`. **Depends on**: T011.
- [ ] T033b [P] [US1] Unit test: `test_cleaning_filters_mmse` in `tests/unit/test_cleaning.py`. **Depends on**: T012e.
- [ ] T033c [P] [US2] Unit test: `test_welch_ttest` in `tests/unit/test_analysis.py`. **Depends on**: T018.
- [ ] T033d [P] [US3] Unit test: `test_sensitivity_sweep` in `tests/unit/test_sensitivity.py`. **Depends on**: T026.
- [ ] T034 [P] Run `code/reference_validator.py` to validate all citations in the final report. **Depends on**: T036b.
- [ ] T035a [P] **RUNTIME MONITORING LOG GENERATION**: Generate `data/results/runtime_log.json` artifact for runtime warnings. **Do NOT update spec.md**. **Depends on**: T035b.
- [ ] T035b [P] **RUNTIME MONITORING**: Implement runtime monitoring logic: **In `code/main.py`, wrap the execution in a timer using `time.time()` at start and end. If total runtime > 21600 seconds (6 hours), log warning `WARN_TIMEOUT` to `data/results/runtime_log.json` (as defined in T035a) and CONTINUE TO COMPLETION** (per FR-007). Verify the warning is logged and execution proceeds. **Depends on**: T004, T035a.
- [ ] T036a [P] **EXTRACT CITATION**: Parse source metadata from `data/raw/metadata.json` (from T015a) to extract `validation_study_doi`. **Read `data/raw/metadata.json`. If `validation_study_doi` key is missing or null, set `doi` to `null`, log `WARN_NO_DOI_FOUND`, and set `verification_status` to 'skipped' in the report.** **CRITICAL**: T015a must run before T036a to ensure `metadata.json` exists. **Depends on**: T015a.
- [ ] T036b [P] **VERIFY CITATION**: Run `code/reference_validator.py` on extracted DOI (from T036a) to verify against primary source (format/existence check). **If `doi` is null (from T036a), log `INFO_SKIPPED_VERIFICATION` and proceed without failing.** **Depends on**: T036a.
- [ ] T036c [P] **GENERATE PAPER**: Generate `paper/001_results.md` including verified citation status (from T036b), scientific validity status (from T015a), and **Stimulus Integrity status (from T015)**. **Depends on**: T036b, T015a, T015.
- [ ] T037 [P] Update `state/state.yaml` with final artifact hashes and timestamps. **Depends on**: T036c.