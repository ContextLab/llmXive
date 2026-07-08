# Tasks: Assessing the Generalizability of Statistical Significance in Pre-Registered Studies

**Input**: Design documents from `/specs/001-assessing-the-generalizability-of-statis/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `projects/PROJ-065-assessing-the-generalizability-of-statis/code/` directory
- [ ] T001b Create `projects/PROJ-065-assessing-the-generalizability-of-statis/data/raw/` and `data/processed/` directories
- [ ] T001c Create `projects/PROJ-065-assessing-the-generalizability-of-statis/outputs/` and `outputs/figures/`, `outputs/reports/` directories
- [ ] T001d Create `projects/PROJ-065-assessing-the-generalizability-of-statis/tests/` directory
- [ ] T001e Initialize `requirements.txt`, `README.md`, and `.gitkeep` files in respective directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] Setup `data/raw/`, `data/processed/`, and `outputs/` directory structure with checksumming logic
- [~] T004 Implement `code/config.py` with paths, random seeds (42), and threshold constants (including `MAX_ITERATIONS=1000`, `ALTERNATIVE_ITERATIONS=1000`, `TIMEOUT_HOURS=6`)
- [~] T005 [P] Implement `code/ingestion.py` skeleton with OSF API client and error handling (429 backoff)
- [~] T006 [P] Implement `code/bootstrap_engine.py` skeleton with stratified resampling logic
- [~] T007 Create `code/meta_analysis.py` skeleton for aggregation and plotting
- [~] T008 Implement `code/main.py` orchestration script
- [~] T010 Implement `record_artifact_hash()` function in `code/main.py` to update `state/projects/PROJ-065-assessing-the-generalizability-of-statis.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Parse Pre-Registered Study Data (Priority: P1) 🎯 MVP

**Goal**: Programmatically download raw datasets from OSF, extract statistical models, and handle missing/corrupted data gracefully.

**Independent Test**: The system fetches 50 pre-registered study data bundles from OSF, parses metadata, and extracts reported p-values into `data/processed/baseline_metrics.csv`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [~] T011 [P] [US1] Unit test for OSF API backoff logic in `tests/unit/test_ingestion.py`
- [~] T012 [P] [US1] Unit test for parsing logic with missing p-value in `tests/unit/test_ingestion.py`
- [~] T013 [P] [US1] Integration test for downloading 3 valid studies in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement OSF API download logic with exponential backoff in `code/ingestion.py`
- [ ] T015 [US1] Implement logic to ingest up to 50 studies from OSF, parse metadata to extract `osf_id`, `discipline`, `original_p_value`, `sample_size`; MUST include logic to detect "ambiguous_model" conditions and implement a selection algorithm to ensure a balanced subset of 3 disciplines (psychology, economics, biology) is included in the final analysis set (min 1 per discipline) in `code/ingestion.py`
- [ ] T016 [US1] Implement logic to flag "missing_p_value" and "ambiguous_model" entries in `code/ingestion.py`
- [ ] T017 [US1] Implement CSV export to `data/processed/baseline_metrics.csv` with SHA-256 checksum in `code/ingestion.py`
- [ ] T018 [US1] Add error handling for 429 errors and corrupted files (skip and log) in `code/ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Bootstrap Resampling and Sensitivity Analysis (Priority: P2)

**Goal**: Run multiple bootstrap iterations for baseline and 5 alternative specs per study, calculating Sampling and Specification Stability Rates.

**Independent Test**: For a single study (N=200), the system completes 1000 baseline iterations and 1000 iterations for each of 5 alternative specs within 10 mins on 2-core CPU, outputting distinct p-value distributions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for stratified bootstrap logic with N=50 in `tests/unit/test_bootstrap.py`
- [ ] T020 [P] [US2] Unit test for zero-variance predictor handling in `tests/unit/test_bootstrap.py`
- [ ] T021 [P] [US2] Integration test for timeout logic (simulate slow study) in `tests/integration/test_bootstrap.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement global runtime feasibility check in `code/main.py` to project total time before starting study loop; MUST use formula: `projected_time = (avg_time_per_study * remaining_studies) + buffer` where `avg_time_per_study` is calculated from the average of the first 3 completed studies in the current run (or 5 mins default if none exist); MUST include logic: "If projected time > 5.5h, reduce iterations to 500 for remaining studies" to ensure 6h limit compliance (requires knowledge of total studies)
- [ ] T026b [US2] Document staged exception for iteration reduction (500 iters if >5.5h) in code comments and docs to acknowledge constitutional requirement in `code/bootstrap_engine.py` and `docs/`
- [ ] T022a [US2] Implement statistical power verification logic in `code/bootstrap_engine.py`: If runtime forces fallback to 500 iterations, run a power analysis simulation on a subset of data to verify 500 iterations yield a confidence interval width < 0.05 for the stability rate; if not, log critical error and abort the study to satisfy SC-001
- [ ] T027 [US2] Implement adaptive subsampling (N > 2000 -> subsample to 2000) in `code/bootstrap_engine.py` as a prerequisite step before resampling
- [ ] T023a [US2] Define and validate the 5 alternative model specifications in `code/bootstrap_engine.py` to ensure FR-003 compliance: 1) Baseline, 2) +Covariate A, 3) +Covariate B, 4) Log-transform Outcome, 5) Remove outliers >3SD; ensure these specific types are generated
- [ ] T022 [US2] Implement stratified bootstrap resampling function (configurable iterations, default 1000) reading from `data/processed/baseline_metrics.csv` in `code/bootstrap_engine.py`; MUST use `config.py` for iteration count to allow adaptive reduction
- [ ] T023 [US2] Implement alternative model specification logic to generate and *persist* p-value distributions for 1000 iterations (configurable) for EACH of 5 alternative specifications (as defined in T023a) in `code/bootstrap_engine.py`
- [ ] T024 [US2] Implement calculation of "Sampling Stability Rate" (baseline) from persisted distributions in `code/bootstrap_engine.py`
- [ ] T025 [US2] Implement calculation of "Specification Stability Rate" (alternative specs) from persisted distributions in `code/bootstrap_engine.py`; MUST aggregate by pooling ALL p-values from all 5 alternative specifications and calculating the percentage < 0.05 (not averaging the 5 rates) to match FR-004
- [ ] T028 [US2] Implement sensitivity sweep logic across representative threshold values {0.01, 0.05, 0.10} that reads *raw p-value distributions* from the in-memory results of T022/T023 to recalculate BOTH Sampling AND Specification Stability Rates for each threshold, outputting `sensitivity_results.csv` with `SensitivityResult` objects in `code/bootstrap_engine.py`
- [ ] T029 [US2] Save per-study results to `data/processed/study_[osf_id]_results.json` with EXPLICIT JSON schema mandating: `baseline_stability_rate`, `alt_specs` (list of 5 objects, each containing `id`, `stability_rate`, `p_value_distribution`), AND `sensitivity_rates` (object containing `sampling_rate_at_0.01`, `sampling_rate_at_0.05`, `sampling_rate_at_0.10`, `specification_rate_at_0.01`, `specification_rate_at_0.05`, `specification_rate_at_0.10`) derived from T028 in `code/bootstrap_engine.py`
- [ ] T026c [US2] Implement memory usage instrumentation in `code/bootstrap_engine.py` and `code/main.py` to log peak RAM usage during bootstrap loops and assert against 6GB limit to satisfy SC-003

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Fragility Indices and Generate Visualizations (Priority: P3)

**Goal**: Aggregate stability rates, calculate meta-analysis metrics (I²), and generate forest plots.

**Independent Test**: The system processes 10 completed study result files and generates `outputs/reports/summary_report.pdf` with forest plot and I² statistic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for I² heterogeneity calculation in `tests/unit/test_meta_analysis.py`
- [ ] T031 [P] [US3] Unit test for forest plot generation with mock data in `tests/unit/test_meta_analysis.py`

### Implementation for User Story 3

- [ ] T031b [US3] Load and validate JSON schema generated by T029 (including `alt_specs` and `sensitivity_rates` keys) before aggregation to ensure artifact-flow continuity in `code/meta_analysis.py`
- [ ] T032 [US3] Implement aggregation logic to calculate mean/median stability rates across studies in `code/meta_analysis.py`
- [ ] T033 [US3] Implement random-effects model meta-analysis and I² calculation in `code/meta_analysis.py`
- [ ] T034 [US3] Implement forest plot generation with confidence intervals. in `code/meta_analysis.py` (using matplotlib/seaborn)
- [ ] T035 [US3] Implement histogram generation for p-value stability rates in `code/meta_analysis.py`
- [ ] T036 [US3] Implement logic to highlight fragile findings (>50% stability < 80%) in `code/meta_analysis.py`
- [ ] T037 [US3] Generate `outputs/reports/summary_report.pdf` containing all plots and tables in `code/meta_analysis.py`
- [ ] T038 [US3] Export summary statistics table to `data/processed/summary_stats.csv` in `code/meta_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, usage examples)
- [ ] T040 [P] Refactor `code/bootstrap_engine.py` to extract stratified sampling logic into a separate function `stratified_resample()` and ensure 100% test coverage for the new function
- [ ] T041 [P] Implement `multiprocessing.Pool` in `code/main.py` to process studies in batches of variable size; verify total runtime reduction without exceeding available system RAM peak memory usage
- [ ] T042 [P] Additional unit tests for edge cases (empty datasets, single study) in `tests/unit/`
- [ ] T043 Security hardening (validate OSF input data types)
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end pipeline execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 to run effectively
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires results from US2 to run effectively
 *Note: While US2/US3 can be coded in parallel, they cannot produce valid results until upstream data is ready.*

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
Task: "Unit test for OSF API backoff logic in tests/unit/test_ingestion.py"
Task: "Unit test for parsing logic with missing p-value in tests/unit/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement OSF API download logic with exponential backoff in code/ingestion.py"
Task: "Implement metadata parsing to extract osf_id, discipline, original_p_value, sample_size in code/ingestion.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (download 50 studies, extract p-values)
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
 - Developer A: User Story 1 (Ingestion)
 - Developer B: User Story 2 (Bootstrap Engine)
 - Developer C: User Story 3 (Meta Analysis)
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
- **CPU Feasibility**: All bootstrap tasks must use stratified sampling on N<=2000 and configurable iterations (default 1000, fallback 500 with power verification) to fit within 6h/2CPU limits. No GPU usage allowed.
- **Data Integrity**: All tasks must use real OSF data or synthetic data with pinned seeds. No fabrication.