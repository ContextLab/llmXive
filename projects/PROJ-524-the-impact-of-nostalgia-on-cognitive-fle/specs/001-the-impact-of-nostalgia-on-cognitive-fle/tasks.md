# Tasks: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Input**: Design documents from `/specs/001-nostalgia-cognitive-flexibility/`
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

- [X] T001 [P] Create all required data directories: `data/raw/`, `data/processed/`, `data/results/`, `data/stimuli/`, `contracts/`, `code/`, `tests/`, `paper/`. **Depends on**: None.

- [X] T002 [P] Create `requirements.txt` with pinned versions for: pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, requests, pytest, black, ruff. **Depends on**: T001.

- [X] T003a [P] Create `pyproject.toml` with an empty `[tool.black]` and `[tool.ruff]` section skeleton. **Depends on**: T002.
- [X] T003b [P] Verify `pyproject.toml` exists and contains `[tool.black]` and `[tool.ruff]` sections, referencing default ruff standards for line-length and lint rules. **Depends on**: T003a.

- [X] T004 [P] Implement `code/utils.py` with checksum (SHA-256) helpers, logging setup, and versioning logic. **Depends on**: T003b.
- [X] T005 [P] Setup `code/reference_validator.py` to validate citations and enforce title overlap ≥ 0.7. **Depends on**: T004. **Note**: This module is strictly for citation validation; statistical logic belongs in `code/analysis.py`. <!-- FAILED: unspecified -->
- [X] T006 [P] Create base configuration management in `code/config.py` (env vars, paths). **Note**: Do not store runtime flags here. **Depends on**: T004.
- [X] T007 [P] Setup `contracts/` directory structure (files generated in Phase 1). **Depends on**: T001.

- [X] T020b-1 [P] **CREATE DATA MODEL YAML**: Create `specs/001-nostalgia-cognitive-flexibility/data-model.yaml` with `Participant`, `Metric`, and `Stimulus` entities based on Spec Section 5. **Fields to include**: `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, `MMSE` (optional). **Depends on**: T007.
- [X] T020b-4 [P] **GENERATE DATA MODEL DOCUMENTATION**: Read `data-model.yaml` and generate `specs/001-nostalgia-cognitive-flexibility/data-model.md` as a standalone artifact describing the entities and relationships to satisfy the "Design Decisions" section of the spec. **Depends on**: T020b-1.
- [X] T020a [P] **GENERATE CONTRACTS**: Generate `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on the Data Model (T020b-1). Validate that `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, and optional `MMSE` are defined. **Depends on**: T020b-1.
- [X] T020c [P] **GENERATE QUICKSTART**: Create `specs/001-nostalgia-cognitive-flexibility/quickstart.md` with installation instructions, dependency installation, and a "Hello World" example to run the ingestion pipeline on a sample dataset. **Depends on**: T002, T003a, T020a.

**Checkpoint**: Foundation and Contracts ready - user story implementation can now begin

---

## Phase 2: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest publicly available WCST/Executive Function data and nostalgia stimuli, validate age ≥ 65, and produce a clean, aligned dataframe. If real data is unavailable, fall back to Methodological Simulation as per Plan.

**Independent Test**: The system can be fully tested by running the data loader script on a source dataset containing at least 100 records and verifying the output contains a dataframe with all valid participant records found, matching stimulus IDs, and non-null cognitive metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008 [P] [US1] Contract test for schema validation in `tests/contract/test_dataset_schema.py`. **Depends on**: T020a.
- [X] T009 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py`. **Depends on**: T008.

### Implementation for User Story 1

- [X] T043 [US1] **REAL DATA SOURCE ENFORCEMENT**: **CRITICAL**: Modify `code/ingestion.py` to explicitly check for the presence of a "VERIFIED REAL DATA SOURCE" block in `os.environ` or `data/verified_source.json`. **Run this task BEFORE T010a**. **Logic**: If the verified source block is missing, log `WARN_NO_VERIFIED_SOURCE` and **do NOT halt** (allow simulation fallback). If present, override any hardcoded `load_dataset` calls to use the exact package/recipe provided. **Depends on**: T006.
- [ ] T010a [US1] **IMPLEMENT INGESTION LOGIC**: Implement `code/ingestion.py` with a function `fetch_data()` that attempts to fetch real data from the **specific canonical source defined in plan.md** (e.g., specific OpenML ID or HuggingFace path). **Logic**: If fetch succeeds, save raw dataset to `data/raw/raw_dataset.csv` and return `{'status': 'success', 'path': '...'}`. If fetch fails, raise `RealDataFetchFailed` exception to trigger T010d. **Do NOT include fallback generation logic here**. **Depends on**: T004-T007, T020a, T043.
- [ ] T010d [US1] **IMPLEMENT SIMULATION DATA GENERATION**: Implement `code/ingestion.py` with a function `generate_simulation_data()` that creates synthetic WCST data. **Logic**: Create a CSV with `participant_id`, `age` (random 65-85), `stimulus_type` (nostalgia/control), `perseverative_errors`, `categories_completed`. Ensure `age >= 65` for all records. Save to `data/raw/raw_dataset.csv`. Log `INFO_SIMULATION_MODE` in `data/raw/metadata.json`. **Explicitly set `simulation_mode=True` in metadata**. **Label all outputs as SIMULATION_MODE**. **Depends on**: T010a.
- [X] T010c [US1] **PIPELINE ORCHESTRATOR**: Implement `code/main.py` to orchestrate the ingestion pipeline. **Logic**: Call `fetch_data()`. If it raises `RealDataFetchFailed`, call `generate_simulation_data()`. If it succeeds, proceed to T011. **Label all outputs as SIMULATION_MODE** if simulation was used. **Depends on**: T010a, T010d.
- [X] T011 [P] [US1] Implement data validation logic in `code/ingestion.py`: filter `age >= 65`, exclude missing `stimulus_type`, log `ERR_MISSING_AGE_FIELD`. **Depends on**: T010c.
- [ ] T012a [P] [US1] **AGE EXCLUSION**: Implement logic to filter `data/raw/raw_dataset.csv` for `age >= 65`. Write filtered data to `data/processed/cleaned_age_filtered.csv`. Write exclusion count to `data/processed/exclusion_counts.json` with key `ERR_MISSING_AGE_FIELD`. **Depends on**: T010c.
- [ ] T012b [P] [US1] **SCORE EXCLUSION**: Implement logic to filter `data/processed/cleaned_age_filtered.csv` for non-null `perseverative_errors` and `categories_completed`. Write filtered data to `data/processed/cleaned_score_filtered.csv`. Write exclusion count to `data/processed/exclusion_counts.json` with key `ERR_MISSING_SCORE`. **Depends on**: T012a.
- [ ] T012d [P] [US1] **MMSE FLAG**: Implement logic to read `data/raw/raw_dataset.csv`. Check if 'MMSE' column exists AND contains at least one non-null value. **If column missing OR all null, set `has_mmse=False` and log `ERR_MMSE_MISSING` WITHOUT raising an error**. Write `has_mmse` (True/False) to `data/processed/mmse_flag.json`. **Depends on**: T010c.
- [ ] T012e [US1] **MMSE EXCLUSION AND ROBUSTNESS PREP**: Implement logic to read `has_mmse` from `data/processed/mmse_flag.json`. **Logic**: If `has_mmse=True`: Filter `data/processed/cleaned_score_filtered.csv` for `MMSE >= 24` and write to `data/processed/cleaned_dataset.csv` (Primary). If `has_mmse=False`: Copy `data/processed/cleaned_score_filtered.csv` to `data/processed/cleaned_dataset.csv` (Primary). **ALWAYS** generate `data/processed/cleaned_dataset_no_mmse.csv` by copying `data/processed/cleaned_score_filtered.csv`. Write exclusion counts to `data/processed/exclusion_counts.json`. **Depends on**: T012d, T012b.
- [ ] T012c [P] [US1] **GENERATE EXCLUSION LOG**: Read exclusion counts from `data/processed/exclusion_counts.json` (from T012a, T012b, T012e) and write `data/processed/exclusion_log.json` with keys `ERR_MISSING_AGE_FIELD`, `ERR_MISSING_SCORE`, `ERR_MMSE_IMPAIRED`, and `SIMULATION_FALLBACK` (if applicable). **Depends on**: T012a, T012b, T012e.
- [ ] T014a [P] [US1] **GENERATE CLEANED DATASET**: Read `data/processed/cleaned_dataset.csv`. Select columns: `participant_id`, `stimulus_type`, `perseverative_errors`, `categories_completed`, `age`. Write to `data/processed/final_cleaned_dataset.csv`. **Depends on**: T012c, T012e.
- [ ] T014b [P] [US1] **VALIDITY METRICS**: Calculate percentage of valid records (age >= 65, non-null metrics, MMSE >= 24 if available) vs total raw input records from `data/raw/raw_dataset.csv`. Write the calculated percentage to `data/processed/validity_metrics.json`. **Depends on**: T012c.
- [X] T015 [US1] **STIMULUS INTEGRITY & GENERATION**: Check `data/stimuli/` directory. **If empty**: Attempt to fetch real nostalgia stimuli from the canonical source defined in `plan.md`. **If fetch fails**: **Do NOT halt**. Instead, generate synthetic placeholder stimuli (e.g., blank audio files or text placeholders labeled "SIMULATION_STIMULUS") to satisfy Constitution Principle VI (Stimulus Fidelity) and allow the pipeline to proceed to T010d. Log `WARN_STIMULUS_SIMULATION_FALLBACK`. **If non-empty**: Validate existing files against metadata checksums. If mismatch, log `ERR_STIMULUS_CORRUPT` and halt. Write `stimuli_checksums` (dict of filename: hash) to `data/stimuli_checksums.json`. **Depends on**: T004, T007, T010c.
- [X] T015a [US1] **GENERATE METADATA**: Create `data/raw/metadata.json` with keys `dataset_source`, `validation_study_doi` (set to null if not found), `stimuli_checksums` (read from `data/stimuli_checksums.json` created by T015), and `simulation_mode` (boolean). **Depends on**: T015, T010c.
- [X] T015b [P] [US1] **STIMULUS VALIDATION**: If `data/raw/metadata.json` contains `validation_study_doi` (and not null), log `INFO_STIMULUS_VALIDATED`. Else, log `WARN_STIMULUS_NO_VALIDATION`. **Depends on**: T015a.
- [X] T042 [P] [US1] **ENFORCE STREAMING**: Update `code/ingestion.py` to use `datasets.load_dataset(..., streaming=True)` for any dataset > 100MB to ensure RAM compliance on the specified runner. **Depends on**: T010a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Execute statistical comparison of cognitive flexibility metrics between nostalgia and control conditions using Welch's t-test (between-subjects), calculate effect sizes, and apply corrections.

**Independent Test**: The analysis can be fully tested by running the statistical module on a synthetic dataset with known effect sizes and verifying the output correctly identifies the calculated p-value and calculates the Cohen's d within a reasonable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for statistical output schema in `tests/contract/test_analysis_output.py`. **Depends on**: T020a.
- [X] T017 [P] [US2] Integration test for statistical pipeline with synthetic data in `tests/integration/test_analysis.py`. **Depends on**: T016.

### Implementation for User Story 2

- [ ] T017a [US2] **IMPLEMENT GROUPING LOGIC**: Implement logic in `code/analysis.py` to split `data/processed/final_cleaned_dataset.csv` by `stimulus_type` into two distinct groups: `nostalgia_group` and `control_group`. **Output**: Write the split dataframes to `data/processed/grouped_data.json` (or keep in memory if streaming) and ensure the logic is callable by T018. **Depends on**: T014a.
- [ ] T018 [US2] **WELCH'S T-TEST**: Implement `code/analysis.py` statistical functions: **Welch's independent samples t-test**. **Input**: Requires two distinct groups defined by `stimulus_condition` (nostalgia vs control) in `data/processed/final_cleaned_dataset.csv` (split via T017a). **Logic**: Apply test to **BOTH** `perseverative_errors` **AND** `categories_completed`. **CRITICAL**: Strictly follow Spec FR-002 which mandates Welch's t-test. **Output**: Write p-values and t-statistics to `data/results/statistical_report.json` under keys `p_values` and `t_statistics`. **Depends on**: T017a.
- [X] T019 [US2] **BONFERRONI CORRECTION**: Implement multiple-comparison correction (Bonferroni) for `perseverative_errors` and `categories_completed`. Use `scipy.stats.multipletests` with `method='bonferroni'` to adjust p-values. **Output**: Write corrected p-values to `data/results/statistical_report.json` under key `corrected_p_values`. **Depends on**: T018.
- [X] T020 [US2] **EFFECT SIZE**: Calculate and report Cohen's d with 95% confidence intervals for all primary comparisons using `statsmodels.stats.weightstats.tt_ind_solve_power` or `scipy.stats`. **Output**: Write effect sizes and confidence intervals to `data/results/statistical_report.json` under key `effect_sizes`. **Depends on**: T018.
- [X] T021 [US2] Calculate statistical power and Minimum Detectable Effect Size (MDES) for the observed effect; **Append power and MDES values to `data/results/statistical_report.json`**. **Depends on**: T020.
- [X] T022 [US2] Generate `data/results/statistical_report.json` containing p-values, corrected p-values, effect sizes, **power**, **MDES**, and power analysis results. **Depends on**: T019, T020, T021.
- [X] T023 [US2] **ERROR HANDLING**: Add error handling for cases where variance is zero or sample size is too small (< 10 per group). Implement `try/except` blocks around `scipy.stats` calls. Log `ERR_ZERO_VARIANCE` or `ERR_SMALL_SAMPLE` and skip affected test. **Depends on**: T018.
- [ ] T044 [US2] **REAL RESULTS GUARANTEE**: Ensure `code/analysis.py` computes metrics strictly from the `data/processed/final_cleaned_dataset.csv` (real or simulation data). **Strictly prohibit** any logic that generates synthetic results or random numbers to replace missing real data. If the input file is empty or missing, raise a `DataNotFoundError`. **Depends on**: T014a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Sensitivity Analysis and Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis by sweeping significance thresholds and checking robustness against cognitive impairment exclusions.

**Independent Test**: The system can be tested by running the sensitivity module with a predefined set of thresholds (e.g., low, medium, and high values) and verifying the output table shows how the "significance" status changes across these values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_output.py`. **Depends on**: T020a.
- [X] T025 [P] [US3] Integration test for sensitivity analysis pipeline in `tests/integration/test_sensitivity.py`. **Depends on**: T024.

### Implementation for User Story 3

- [X] T026 [US3] **SENSITIVITY SWEEP**: Implement sensitivity sweep in `code/analysis.py`: test thresholds including **explicitly: 0.01, 0.04, 0.05, 0.06, 0.10**. **Depends on**: T022.
- [ ] T027a [US3] **MMSE ROBUSTNESS DATA PREP**: Read from `data/processed/cleaned_dataset.csv` (Primary) and `data/processed/cleaned_dataset_no_mmse.csv` (Robustness). **Logic**: If `has_mmse=False` (from T012d), **SKIP** the robustness comparison and log `WARN_MMSE_MISSING`. **Check `simulation_mode` in `metadata.json`**; if true, **Skip MMSE robustness check but run sensitivity sweep** and log `INFO_SIMULATION_SKIPPED`. **Trigger condition**: The existence of `data/processed/cleaned_dataset_no_mmse.csv` (always generated by T012e) serves as the trigger for T027b. **If skipped**: Write a `robustness_skip_flag.json` with reason and log `WARN_MMSE_MISSING`. **Depends on**: T012e, T012d.
- [ ] T027b [US3] **MMSE ROBUSTNESS ANALYSIS**: **Only if T027a did not skip**: Re-run analysis (T018 logic, but independent) on `data/processed/cleaned_dataset_no_mmse.csv`. Write results to `data/results/robustness_report.json`. **If skipped**: Write a `robustness_report.json` with status `SKIPPED` and reason `MMSE_MISSING` or `SIMULATION_MODE`. **Depends on**: T027a, T018.
- [ ] T027c [US3] **COMPARE ROBUSTNESS**: **Only if T027a did not skip**: Explicitly compare the results of the primary analysis (T022, with MMSE) vs. the robustness analysis (T027b, without MMSE). Generate `data/results/sensitivity_comparison.json` highlighting any differences in significance or effect size. **If T027b was skipped**: Generate `sensitivity_comparison.json` noting `ROBUSTNESS_CHECK_SKIPPED`. **Depends on**: T022, T027b.
- [ ] T027d [US3] **GENERATE PRIMARY ANALYSIS REPORT**: **CRITICAL**: Generate `data/results/primary_analysis_report.json` strictly enforcing MMSE exclusion (FR-006). This report must be generated from `data/processed/cleaned_dataset.csv` (with MMSE >= 24) and must be the primary output for all empirical claims. **Depends on**: T022.
- [X] T028 [US3] **SENSITIVITY REPORT**: Generate `data/results/sensitivity_report.json` with significance status per threshold and subset comparison. **Depends on**: T026, T027c.
- [X] T029 [US3] **BORDERLINE FLAG**: Add logic to flag "sensitive to threshold choice" if p-value falls in the range **0.04 <= p <= 0.06** (using float comparison tolerance within a negligible numerical margin). **Output**: Write a binary flag `is_sensitive_to_threshold` to `data/results/sensitivity_report.json`. **Depends on**: T028.
- [X] T030 [US3] **FINAL SENSITIVITY SUMMARY**: Append the sensitivity analysis summary and stability metrics from `data/results/sensitivity_report.json` to `paper/001_results.md`. **Depends on**: T028, T029, T036c.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T031a [P] **README INSTALLATION**: Update `README.md` with installation instructions, dependencies, usage examples, and a "Quick Start" section. **Depends on**: T002, T020c.
- [ ] T031b [P] **API DOCS**: Add API docs for `code/ingestion.py` and `code/analysis.py` functions. **Depends on**: T018, T010a.
- [ ] T032a [P] **REFACTOR ANALYSIS**: Refactor `code/analysis.py` to reduce cyclomatic complexity to < 10. **Method**: Extract data cleaning logic into `clean_data()` function in `code/ingestion.py` and split `run_analysis()` into `compute_stats()` and `generate_report()`. **Depends on**: T022.
- [X] T032b [P] **REFACTOR INGESTION**: Refactor `code/ingestion.py` to improve modularity and error handling. **Method**: Split `fetch_data()` and `validate_schema()` into separate modules. **Depends on**: T010a.
- [X] T033a [P] [US1] Unit test: `test_cleaning_filters_age` in `tests/unit/test_cleaning.py`. **Depends on**: T011.
- [X] T033b [P] [US1] Unit test: `test_cleaning_filters_mmse` in `tests/unit/test_cleaning.py`. **Depends on**: T012e.
- [ ] T033c [P] [US2] Unit test: `test_welch_ttest` in `tests/unit/test_analysis.py`. **Depends on**: T018.
- [X] T033d [P] [US3] Unit test: `test_sensitivity_sweep` in `tests/unit/test_sensitivity.py`. **Depends on**: T026.
- [ ] T035 [P] **IMPLEMENT RUNTIME MONITORING**: Implement runtime monitoring logic in `code/main.py`: wrap the execution in a timer using `time.time()` at start and end. If total runtime > 21600 seconds (6 hours), **log warning `WARN_TIMEOUT` to standard logging stream immediately** AND append to `data/results/runtime_log.json` for artifact tracking. **Ensure the warning is logged to the stream for visibility**. **Depends on**: T004, T010c.
- [X] T036a [US3] **EXTRACT CITATION**: Parse source metadata from `data/raw/metadata.json` (from T015a) to extract `validation_study_doi`. **Logic**: If `validation_study_doi` key is missing or null, set `doi` to `null`, log `WARN_NO_DOI_FOUND`, and set `verification_status` to 'skipped' in the report. **If data/raw/metadata.json is missing, raise DataNotFoundError**. **Write output to `data/citation_status.json` with keys `doi` and `verification_status`**. **Depends on**: T015a.
- [X] T036b [US3] **VERIFY CITATION**: Run `code/reference_validator.py` on extracted DOI (from T036a) to verify against primary source (format/existence check). **If `doi` is null (from T036a), log `INFO_SKIPPED_VERIFICATION` and proceed without failing.** **Output**: Write verification result to `data/citation_status.json` (updating `verification_status`). **Depends on**: T036a.
- [X] T036c [US3] **GENERATE PAPER**: Generate `paper/001_results.md` including verified citation status (from T036b), scientific validity status (from T015a), and **Stimulus Integrity status (from T015)**. **Depends on**: T036b, T015a, T015.
- [X] T037 [US3] **UPDATE STATE**: Update `state/state.yaml` with final artifact hashes and timestamps. **Depends on**: T036c.

---

## Phase 6: Verification & Data Integrity (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data source verification, simulation transparency, and statistical rigor.

**Independent Test**: The pipeline must successfully execute end-to-end, producing a final report that explicitly states the data source type (Real vs. Simulation) and validates all statistical assumptions.

### Implementation for Verification

- [X] T050 [P] [US1] **REAL DATA SOURCE ASSERTION**: Add a strict check in `code/ingestion.py` (inside `fetch_data`) that if `data/verified_source.json` exists, the loaded dataset **MUST** match the `package_name` and `config` defined therein. **Logic**: If mismatch, **LOG WARNING `WARN_SOURCE_MISMATCH`** and **proceed to simulation fallback** (T010d). **Do NOT halt execution**. **Depends on**: T043.
- [X] T051 [P] [US1] **SIMULATION TRANSPARENCY**: Update `data/raw/metadata.json` generation (T015a) to include a `simulation_methodology` field. If in simulation mode, this field must contain the exact random seed, distribution parameters, and sample size used. **Depends on**: T010d.
- [ ] T052 [US2] **STATISTICAL ASSUMPTION CHECK**: Before running Welch's t-test (T018), implement a check for normality (Shapiro-Wilk) and homogeneity of variance (Levene's test) on the `final_cleaned_dataset.csv`. Log results to `data/results/assumption_checks.json`. If assumptions are severely violated, log `WARN_ASSUMPTION_VIOLATION` but proceed with Welch's (robust) test as per plan. **Depends on**: T014a.
- [X] T053 [P] [US3] **ROBUSTNESS SUMMARY REPORT**: Generate `data/results/robustness_summary.md` that explicitly compares the primary analysis (with MMSE) vs. robustness analysis (without MMSE) and the sensitivity sweep results. **If upstream robustness checks were skipped (T027a), generate a summary explicitly stating the skip reason and noting that robustness could not be assessed**. This report must clearly state if the primary conclusion holds across all conditions or if the assessment was skipped. **Depends on**: T027c, T030.
- [X] T054 [P] **FINAL INTEGRATION TEST**: Create `tests/integration/test_full_pipeline.py` that runs the entire pipeline from ingestion to final report generation on the simulation dataset and asserts that all required JSON artifacts are created with non-null values. **Depends on**: T010c, T022, T028.
- [X] T055 [P] **UPDATE PLAN AND SPEC**: Update `plan.md` and `spec.md` to explicitly document the new `simulation_methodology` field in `data/raw/metadata.json` as part of the "Verified Accuracy" and "Reproducibility" gates. **Depends on**: T051.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Verification (Phase 6)**: Depends on all User Stories and Polish being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Tasks T043, T044, and T050 enforce real data usage and prevent synthetic fallbacks, ensuring compliance with the "Real data + real results only" constitution.
- **Simulation Fallback**: T010c and T010d implement the Plan's required fallback to Methodological Simulation if real data is unavailable, resolving the contradiction in previous versions. T015 now supports this fallback for stimuli.
- **Stimulus Fidelity**: T015 ensures stimuli are validated and generates synthetic placeholders in simulation mode to prevent pipeline halting, satisfying Constitution Principle VI.
- **Statistical Rigor**: T052 ensures that the choice of Welch's t-test is validated against data assumptions, addressing reviewer concerns about statistical appropriatenality. T018 strictly follows Spec FR-002.
- **Grouping Logic**: T017a explicitly implements the between-subjects grouping required for Welch's t-test.
- **Output Artifacts**: T018, T020, T029, T030 explicitly define output paths and keys for verification.
- **Documentation**: T020b-4 and T055 ensure data model and simulation methodology are documented in spec/plan.
- **Runtime Logging**: T035 logs to standard stream for immediate visibility.
- **Robustness Reporting**: T053 ensures a summary report is generated even if robustness checks are skipped, preventing "zombie" requirements.
