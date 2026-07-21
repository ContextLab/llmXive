# Tasks: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Input**: Design documents from `/specs/001-exploring-the-correlation-between-atmosp/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY to ensure reproducibility and validation.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and documentation scaffolding.

- [X] T001 Create project structure per `specs/001-exploring-the-correlation-between-atmosp/plan.md`: `mkdir -p data/{raw,interim,processed} code tests docs`
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas, numpy, scipy, scikit-learn, requests, tqdm, pyyaml)
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools
- [X] T004b [P] Create `docs/deviations.md` with a header, table of contents, and formal structure to document scope reductions (e.g., FR-001 global data block, FR-011 climate index deferment) as required by Constitution Principle II.
- [X] T004c [P] Create `docs/quickstart.md` as a Phase 1 output (per plan.md) to ensure it exists before T035 validation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Dependencies**: T008 must be completed before T009. T025b must be completed before T025. T004b must be completed before T011b and T025b. Note: T004b is parallel-safe, but T011b and T025b depend on its completion.

- [X] T008 Create base data validation schemas in `contracts/` (earthquake.schema.yaml, pressure-anomaly.schema.yaml) with required fields: magnitude, depth, lat, lon, timestamp, pressure, anomaly, window_label.
 - **earthquake.schema.yaml**: Define properties for magnitude (float), depth (float), lat (float), lon (float), timestamp (ISO8601), event_id (string).
 - **pressure-anomaly.schema.yaml**: Define properties for event_id (string), pressure_value (float), anomaly_value (float), window_type (string: 'event'|'control'), timestamp (ISO8601).
- [X] T008b [P] Create sample data fixture `tests/fixtures/sample_earthquake.yaml` containing at least one valid earthquake record and one valid pressure anomaly record matching the schemas in T008. This file is required for T009 contract testing.
- [X] T011b Create a formal deviation record in `docs/deviations.md` for FR-001 (Global Data Download Blocked), explicitly stating the absence of verified global NOAA NCEP/NCAR sources, the fallback to verified test data only, and the verification logic required to confirm this state. **(Dependency: T004b)**
- [X] T025b Create a formal deviation record in `docs/deviations.md` for FR-011 (Climate Index Stratification Deferred), explicitly stating the absence of verified ENSO/PDO data sources, the use of date-matching as a proxy, and the verification step planned in T025. **(Dependency: T004b)**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download verified test pressure data and USGS earthquake catalog, align them spatially/temporally, and produce a clean analysis-ready dataset.

**Independent Test**: The script MUST exit with code 0. The output CSV row count MUST match the expected count of earthquakes in the 2018 Alaska subset (N=12) within a 1% tolerance. The output MUST contain a validation report confirming all required fields are present. **New**: The script MUST also verify that the global NOAA NCEP/NCAR download is explicitly blocked and log this state, referencing the deviation record in `docs/deviations.md`.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. T009 depends on T008. T010 depends on T008 and T011 (structure).**

- [X] T009 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`: Validate `earthquake.schema.yaml` and `pressure-anomaly.schema.yaml` against sample data at `tests/fixtures/sample_earthquake.yaml`; assert failure if required fields (magnitude, depth, lat, lon, timestamp) are missing. Assert failure with message "Sample data file not found: tests/fixtures/sample_earthquake.yaml" if the file does not exist. (Dependency: T008, T008b)
- [X] T010 [P] [US1] Integration test for download pipeline in `tests/integration/test_download_pipeline.py`: Fetch USGS test data from `https://earthquake.usgs.gov/fdsnws/event/1/query` (2018 Alaska subset); assert row count equals 12 (±1%). (Dependency: T008, T011 structure)

### Implementation for User Story 1

- [X] T011a [US1] Implement `code/download.py` to fetch **verified test pressure data** and **USGS 2018 Alaska subset** (M≥4.0, depth≤70km) from `https://earthquake.usgs.gov/fdsnws/event/1/query`. **Explicitly check for absence of global NOAA NCEP/NCAR source (FR-001)**, confirm that the global 2013-2023 download is blocked, reference the deviation record in `docs/deviations.md` (T011b), and log this state. **Do NOT attempt to fetch global data**. Process only the 2018 Alaska subset (N=12) as test data. This implements the **Pilot Scope** of FR-001. (Dependency: T011b)
- [X] T012 [US1] Implement checksumming and raw data immutability checks in `code/download.py`
- [X] T013 [US1] Implement `code/preprocess.py` to interpolate a coarse pressure grid to a finer resolution and extract nearest grid points for earthquake epicenters.
- [X] T014 [US1] Implement logic in `code/preprocess.py` to calculate daily pressure anomalies using a left-censored **30-day** moving average, explicitly EXCLUDING the period immediately preceding the event window (t-N to t-0) from the moving average calculation to prevent bias; **verify the 30-day duration against `code/config.py` and ensure it matches the spec's 'sufficient duration' requirement**. (Dependency: T007)
- [X] T015 [US1] Implement filtering in `code/preprocess.py` to exclude ocean-masked events (interpolation reliability < 95%) and events with missing pressure data within the initial observation window
- [X] T016 [US1] Implement deduplication logic in `code/preprocess.py` based on unique USGS event ID, retaining most recent revision
- [ ] T017 [US1] Generate master dataset `data/processed/master_dataset.csv` pairing every earthquake with its pressure anomaly and control window label. **Implementation**: Read from the processed intermediate files, apply filters, and write to CSV. **Verification**: Assert row count equals the expected count from the loaded test dataset configuration (dynamic, not hardcoded), validate schema against `contracts/earthquake.schema.yaml` and `contracts/pressure-anomaly.schema.yaml`, and generate checksum `data/processed/master_dataset.csv.sha256`. (Dependency: T016)
- [ ] T017b [US1] Verification test for T017: Assert that `data/processed/master_dataset.csv` row count matches the expected count (N=12 for 2018 Alaska subset) within 1% tolerance, conditional on 'Pilot Mode' flag referencing `docs/deviations.md`. (Dependency: T017)
- [ ] T018 [US1] Implement validation report generator in `code/preprocess.py` to output JSON report of missing variables if validation fails (FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Association Analysis (Priority: P2)

**Goal**: Perform Kolmogorov–Smirnov and permutation tests to determine if pressure anomalies in pre-earthquake windows differ significantly from control windows, framing results as associational evidence.

**Independent Test**: The analysis can be tested by running the statistical module on the prepared dataset. The output JSON MUST contain a p-value < 0.05 if and only if the observed test statistic is strictly greater than the 95th percentile of the **[deferred]** permuted statistics.

### Tests for User Story 2 (MANDATORY) ⚠️

- [X] T019 [P] [US2] Unit test for KS test calculation in `tests/unit/test_statistics.py`
- [X] T020 [P] [US2] Integration test for permutation test convergence in `tests/integration/test_permutation.py`
- [X] T022b [P] [US2] Unit test for null hypothesis generation in `tests/unit/test_null_hypothesis.py`: Verify that the permutation test correctly shuffles labels and generates a null distribution matching SC-001 criteria.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/analysis.py` to perform two-sample Kolmogorov–Smisnov test on event vs. control window anomalies
- [ ] T022 [US2] Implement permutation test in `code/analysis.py` with a sufficient number of iterations to generate null distribution of the test statistic. **Verification**: Ensure convergence by checking that the p-value stabilizes within 1% over the last 1000 iterations. (Dependency: T021)
- [X] T023 [US2] Implement p-value calculation logic comparing observed statistic to the 95th percentile of the permuted null array. **Output**: Write results to `data/processed/p_value_calc.json` with keys: `observed_statistic`, `p_value`, `null_distribution_count`. **Test**: Assert `p_value` is a float between 0 and 1. **Verification**: Assert `p_value == (count(null_stats > observed) + 1) / (len(null_stats) + 1)`. (Dependency: T022)
- [ ] T024 [US2] Calculate effect size (Cohen's d) for significant results in `code/analysis.py`
- [X] T025 [US2] Implement stratification of control windows by matching month/day across non-event years (basic date matching only). **Explicitly state** that this is a staged simplification of FR-011 (Climate Index Stratification) due to missing ENSO/PDO data sources. **Verification**: Include a step to compare date-matched vs. climate-index-matched distributions in a small pilot subset to confirm scientific validity of the proxy, as required by Plan.md Gap Analysis. Verify that the 'Verified Datasets' block is checked for missing ENSO/PDO sources and label the fallback as 'unverified' in output artifacts, as documented in `docs/deviations.md` (T025b). (Dependency: T025b)
- [X] T026 [US2] Generate `data/processed/statistical_results.json` containing p-values, effect sizes, and explicit "associational" framing (FR-005). **Schema**: Must contain keys: `p_value`, `effect_size`, `framing`, `test_method`. **Validation**: Assert all keys are present and `framing` equals "associational". (Dependency: T023, T024)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Validate primary findings across magnitude thresholds, geographic regions, and anomaly definition cutoffs to ensure robustness.

**Independent Test**: The robustness module can be tested by executing the stratified analysis loop. The system MUST output separate p-values and effect sizes for each subset. The system MUST vary the cutoff by multiples of the background standard deviation (σ).

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T027 [P] [US3] Unit test for sensitivity analysis sweep in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement robustness checks in `code/analysis.py` to stratify by magnitude (4.0–5.0, >5.0) and region (Pacific Ring of Fire vs. others)
- [ ] T029 [US3] Implement sensitivity analysis in `code/analysis.py` sweeping the anomaly cutoff over a range of multiples of σ, where σ is the background pressure standard deviation
- [ ] T030 [US3] Implement Benjamini-Hochberg False Discovery Rate (FDR) correction in `code/analysis.py` for the family-wise error rate across multiple tests (FR-006)
- [X] T031 [US3] Generate `data/processed/robustness_report.json` containing p-values, effect sizes, and significance rates for all subsets and sensitivity sweeps. **Verification**: Assert presence of keys: `magnitude_subsets`, `region_subsets`, `sensitivity_sweep`. **Validation**: Check that `magnitude_subsets` contains entries for both 4.0–5.0 and >5.0, and `sensitivity_sweep` contains entries for 0.5σ, 1.0σ, 1.5σ. (Dependency: T028, T029, T030)
- [X] T032 [US3] Compile final report in `docs/pilot_report.md` explicitly labeling findings as "Pilot/Methodology Validation", documenting limitations (Global data blocked, no climate stratification), including full statistical power documentation (permutation p-values, effect sizes, robustness checks) for any result (positive or null) as required by Constitution Principle VII, and referencing `docs/deviations.md` (T025b). (Dependency: T026, T031)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. **Dependencies**: T033, T034, T035 depend on T032 completion.

- [X] T033 [P] Documentation updates in `README.md`, `docs/quickstart.md`, and `docs/` regarding pilot limitations and deviation records
- [ ] T034 Code cleanup and refactoring for memory efficiency on CPU-only runners. **Metric**: Peak RAM usage must be < 6GB. **Verification**: Run `python -m memory_profiler code/main.py` using the full `data/processed/master_dataset.csv` as input and assert peak memory < 6GB in output log. (Dependency: T032)
- [X] T035 Run quickstart.md validation to ensure full pipeline execution on the test dataset within 6 hours, and document that global dataset feasibility remains unverified per plan.md. **Command**: `timeout python code/main.py`. **Artifact**: Log file `logs/quickstart_validation.log` must contain "Pipeline completed successfully within 6 hours". (Dependency: T032)
- [X] T036 [P] Additional unit tests for ocean masking and missing data exclusion logic in `tests/unit/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T008** must be complete before **T009**
 - **T004b** must be completed before **T011b** and **T025b** (T004b is parallel-safe, but T011b/T025b depend on it)
 - **T025b** must be completed before **T025**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories must proceed in priority order (P1 → P2 → P3) due to data dependencies
 - **T017** must be complete before **T021** and **T022**
 - User Story 2 cannot start until User Story 1 produces `data/processed/master_dataset.csv`
 - **T022** must be complete before **T023**
 - User Story 3 cannot start until User Story 2 produces `data/processed/statistical_results.json`
 - **T031** must be complete before **T032**
- **Polish (Phase 6)**: Depends on T032 (Report) completion. **T032 must be complete before T033, T034, T035.** Once T032 is complete, T033, T034, and T035 can run in parallel.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 completion (requires `data/processed/master_dataset.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 completion (requires `data/processed/statistical_results.json`)

### Within Each User Story

- Tests (MANDATORY) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004b, T008b) can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start
- User Story 2 and 3 MUST wait for their respective upstream artifacts (no parallel start with predecessor stories)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories CANNOT be worked on in parallel by different team members due to strict data-flow dependencies
- **Phase 6**: T033, T034, T035 can run in parallel once T032 is complete.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for download pipeline in tests/integration/test_download_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Create base data validation schemas in contracts/"
Task: "Implement logging infrastructure in code/utils/logging.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories; ensure T008, T004b, T011b are done)
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
 - (Wait for US1 completion)
 - Developer B: User Story 2
 - (Wait for US2 completion)
 - Developer C: User Story 3
3. Stories complete and integrate sequentially due to data dependencies

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Deviation Management**: All scope reductions (FR-001, FR-011) are documented in `docs/deviations.md` (T004b, T011b, T025b) and referenced in implementation tasks (T011a, T025) and final report (T032).
- **Quickstart**: `docs/quickstart.md` is created in Phase 1 (T004c) to align with plan.md outputs.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T037 Reconcile run-book vs implementation for `code/report.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/report.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
