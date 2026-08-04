# Tasks: llmXive follow-up: extending "Reproducing, Analyzing, and Detecting Reward Hacking in Rubric-Based R"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw`, `data/processed`, `tests/`, `tests/unit`, `tests/integration`, `contracts/`. Create files `requirements.txt`, `.gitignore`, `README.md`, `code/__init__.py`.
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `requests`, `pyyaml`, `jsonschema`, `pytest` in `requirements.txt`
- [X] T003a [P] Configure linting (ruff): Create `.ruff.toml` with rules for E (Error), F (Pyflakes), W (Warning), I (Import), N (Naming) enforcing PEP8 and Google style. **Content**: Write a valid `.ruff.toml` file with `select = ["E", "F", "W", "I", "N"]` and `line-length = 88`.
- [X] T003b [P] Configure formatting (black): Create `pyproject.toml` for Black formatting configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create data directory structure: Create directories `data/raw` and `data/processed` at the repository root.
- [X] T004b [P] Configure.gitignore for data: Update `.gitignore` to exclude `data/raw/*` and `data/processed/*` while keeping the directory structure.
- [X] T005a [P] Create trajectory schema: Create `contracts/trajectory.schema.yaml` defining the schema for `seed_id`, `bias_type`, `timestep`, `J_biased`, `J_unbiased`, `J_gold`. (FR-001, FR-002, Entity: Trajectory) **Content**: Write a valid YAML schema file defining types for all required columns. **Note**: File must exist and be valid YAML.
- [X] T005b [P] Create metrics schema: Create `contracts/metrics.schema.yaml` defining the schema for Precision, Recall, F1-score, p-value, effect_size. (FR-005, SC-001, SC-002) **Content**: Write a valid YAML schema file defining types for all required metrics. **Note**: File must exist and be valid YAML.
- [X] T006 Create base utility module for file I/O and checksumming (`code/utils/io_utils.py`)
- [X] T007 Configure environment configuration management for data paths and hyperparameters (`code/config.py`)
- [X] T017 [US1] Implement edge case handlers for time-series processing in `code/utils/math_utils.py`. **Logic**: 1. Implement `interpolate_missing_timesteps()` using linear interpolation for gaps in the time series. 2. Implement `safe_z_score()` which returns a neutral baseline value if the standard deviation of the window is zero, using a small positive epsilon floor to prevent division by zero. 3. Implement `handle_nan()` to gracefully handle NaN values in sliding window calculations (merged from T024). **Dependency**: Requires T005a (schema) to validate input types. **Sequential Order**: This task MUST be executed after T005a completes. **Note**: This task is NOT parallel with T005a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingest CHERRL Trajectories and Compute Divergence Gap (Priority: P1) 🎯 MVP

**Goal**: Ingest CHERRL logs, compute $G(t)$ and $\Delta G(t)$, and aggregate data across seeds.

**Independent Test**: Run ingestion on a small subset of CHERRL logs and verify output CSV contains $G(t)$ and $\Delta G(t)$ columns with correct math.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for $G(t)$ calculation logic in `tests/unit/test_ingestion_math.py`
- [X] T011 [P] [US1] Unit test for $\Delta G(t)$ derivative logic in `tests/unit/test_ingestion_math.py`
- [X] T013b [P] [US1] Unit test for download validation logic in `tests/unit/test_download_validation.py`. **Logic**: Verify that the validation function correctly validates the CHERRL repository source (HuggingFace/CHERRL-repo), handles invalid sources by raising the correct error, and exits with code 2. This is a unit test of the validation logic with mocked network calls. **Assertion**: Assert that a valid source returns success and an invalid source triggers the specific error message.
- [X] T012 [US1] Integration test for multi-seed aggregation in `tests/integration/test_ingestion_pipeline.py`. **Logic**: Run the full aggregation pipeline on a small set of mock logs. **Assertions**: Assert merged CSV has expected row count, assert `seed_id` distribution matches input, assert `G(t)` and `dG(t)` columns exist and are numeric.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `download_cherrl_logs.py` to fetch real data. **Logic**: 1. Fetch data from the verified CHERRL repository artifacts using HuggingFace `datasets.load_dataset('cherrl-repo/logs', split='train')`. 2. **Fail Loud**: If fetch fails or the source does not match the verified data URL, log "ERROR: Data source unreachable or mismatch" and exit with code 2 (data_missing). **NO MOCK MODE**: Do not implement a `--mock-mode` flag. The pipeline must fail if real data is missing. 3. **Deliverable**: Save extracted logs to `data/raw/cherrl_logs/`. This ensures the pipeline halts visibly if data is missing in production.
- [X] T014 [US1] Implement `code/ingestion.py` to load logs and compute $G(t) = |J_{\text{biased}} - J_{\text{unbiased}}|$ (FR-001). **Dependency**: Requires T013 to complete successfully and produce raw logs. **Validation**: Must verify T013 output exists before processing.
- [X] T015 [US1] Implement `code/ingestion.py` to compute $\Delta G(t)$ (discrete derivative), rolling z-score (FR-002), and handle edge cases. **Logic**: Calculate rolling z-score with a sliding window of W=20 timesteps, **requiring a minimum of 5 samples** to compute the standard deviation. Use `linear interpolation` for missing timesteps (T017). If variance of $G(t)$ is zero, set z-score to 0 (using epsilon=1e-9 floor for division). **Dependency**: Requires T014 and **T017** to be completed. **Specific Calls**: Must use `interpolate_missing_timesteps` and `safe_z_score` from `code/utils/math_utils.py`.
- [ ] T016 [US1] Implement aggregation logic to merge multiple seed logs into `data/processed/trajectories_divergence.csv` preserving `seed_id` and `bias_type`. **Schema**: Output must contain columns: `seed_id`, `bias_type`, `timestep`, `J_biased`, `J_unbiased`, `J_gold`, `G_t`, `dG_t`. **Dependency**: Requires T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Detect Hacking via Statistical Thresholding (Priority: P2)

**Goal**: Implement the detector module to flag "hacked" timesteps based on z-score and rate-of-change thresholds.

**Independent Test**: Feed a synthetic dataset with a known spike and verify the detector flags the spike while ignoring noise.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for z-score thresholding logic in `tests/unit/test_detector.py`
- [X] T019 [P] [US2] Unit test for $\Delta G(t)$ dynamic thresholding logic in `tests/unit/test_detector.py`
- [X] T020 [P] [US2] Integration test with synthetic spike data in `tests/integration/test_detector_pipeline.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/detector.py` to calculate sliding window z-score ($W=20$, min 5 samples) per FR-002, reading from `data/processed/trajectories_divergence.csv`. **Dependency**: Requires T016 (aggregated data).
- [ ] T025a [US2] Identify contaminated windows (FR-009). **Logic**: 1. Read `data/processed/trajectories_divergence.csv`. 2. Identify contiguous segments where the **duration** of elevated $G(t)$ (above global median) exceeds the sliding window size (W=20). 3. Store the indices of these segments in a temporary list or DataFrame. **Dependency**: Requires T016.
- [ ] T025b [US2] Generate `is_contaminated` mask. **Logic**: 1. Create a boolean column `is_contaminated` in the DataFrame. 2. Set `True` for all timesteps belonging to the contaminated segments identified in T025a. 3. Set `False` otherwise. **Dependency**: Requires T025a.
- [ ] T025c [US2] Apply mask to baseline calculation. **Logic**: 1. Ensure the `is_contaminated` column is present and correct. 2. Prepare the DataFrame for T022. **Dependency**: Requires T025b.
- [X] T022 [US2] Implement logic in `code/detector.py` to flag "hacked" if $z(G(t)) > 3.0$ OR if $\Delta G(t)$ exceeds a dynamic threshold. **Config**: Use the fixed threshold k=3.0 as defined in FR-003 for the z-score component. **Baseline**: Calculate baseline noise floor as the standard deviation of the **preceding 100 timesteps** (or all available if <100) using the corrected baseline from T025c, **consuming the `is_contaminated` column from T025c to skip contaminated indices**. **Dependency**: Requires T016 (aggregated data) and **T025c (contaminated window mask)** to calculate the baseline.
- [ ] T023 [US2] Generate `data/processed/trajectories_labeled.csv` by appending `hacked_label` column to the US1 output, preserving separation of concerns (FR-001 vs FR-003). **Schema**: `hacked_label` must be a boolean column (True/False). **Dependency**: Requires T022.
- [Note: T024 has been merged into T017 to handle NaN values in `code/utils/math_utils.py`. T024 is removed from the task list.]

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluate Generalization and Statistical Significance (Priority: P3)

**Goal**: Evaluate detector performance against ground truth ($J_{\text{gold}}$ drops) and perform statistical significance testing.

**⚠️ GATE**: Wait for Phase 3 completion (T014/T015 verified) before attempting T032a/T032b/T031.

**Independent Test**: Run evaluation on a pre-labeled test set and verify confusion matrix, F1-scores, and p-value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for ground-truth derivation logic ($J_{\text{gold}}$ drops) in `tests/unit/test_ground_truth.py`
- [X] T027 [P] [US3] Unit test for independence check (Pearson correlation) in `tests/unit/test_ground_truth.py`
- [X] T028 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `tests/unit/test_evaluation.py`
- [X] T029 [P] [US3] Unit test for baseline generation logic in `tests/unit/test_evaluation.py`
- [X] T030 [P] [US3] Integration test for full evaluation pipeline in `tests/integration/test_evaluation_pipeline.py`

### Implementation for User Story 3

- [ ] T032a [US3] Implement `code/ground_truth.py` to check Pearson correlation for $J_{\text{unbiased}}$ vs $J_{\text{gold}}$ (FR-006). **Logic**: If correlation is **strictly greater than** `CORRELATION_THRESHOLD` (default a high positive magnitude, defined in `code/config.py`), **raise SystemExit(1)** and log "ERROR: Independence check failed (J_unbiased vs J_gold). Pipeline halted." **Deliverable**: If passed, write `data/processed/independence_check_status.json` with status "ok". **Do not** write a status file if failed; halt immediately. **Dependency**: Requires T014, T015 (data ingestion).
- [~] T032b [US3] Implement `code/ground_truth.py` to check Pearson correlation for $J_{\text{biased}}$ vs $J_{\text{gold}}$ (FR-008). **Logic**: If correlation is **strictly greater than** `CORRELATION_THRESHOLD` (default 0.8), **raise SystemExit(1)** and log "ERROR: Independence check failed (J_biased vs J_gold). Pipeline halted." **Deliverable**: If passed, write `data/processed/independence_check_status.json` with status "ok". **Do not** write a status file if failed; halt immediately. **Dependency**: Requires T014, T015 (data ingestion).
- [ ] T031 [US3] Implement `code/ground_truth.py` to derive labels from $J_{\text{gold}}$ drops (≥0.1 decrease over 50 steps, sustained 3 steps) per FR-004. **Traceability**: The fixed-step window is defined in **FR-004**. **Edge Case Logic**: Use `linear interpolation` for missing timesteps. If the running mean window is not fully available at the start of the trajectory, compute the mean over the available steps. **Dependency**: Requires T032a and T032b to complete successfully (i.e., not halt) and produce `data/processed/independence_check_status.json`. **Logic**: If the pipeline has not halted (meaning independence checks passed), proceed with label generation.
- [ ] T033-Pre [US3] Define Baseline Configuration. **Logic**: Edit `code/config.py` to define `BASELINE_SAMPLE_FRACTION` (float, 0.0-1.0) and `BASELINE_SEED` (int). **Requirement**: These values MUST be explicitly set by the researcher before T033 runs. If missing, T033 will fail.
- [ ] T033 [US3] Implement `code/evaluation.py` to generate a "Stratified Random Baseline". **Logic**: Sample timesteps uniformly stratified by rubric type (Lexical, Format, Tone, Self-praise) using `BASELINE_SAMPLE_FRACTION` from `code/config.py`. **Config Requirement**: The task must read `BASELINE_SAMPLE_FRACTION` and `BASELINE_SEED` from `code/config.py`. If the value is missing or `None`, raise `RuntimeError` with message "MISSING_CONFIG: BASELINE_SAMPLE_FRACTION is required and must be explicitly defined by the researcher" and exit with code 1. **Seed Requirement**: Use a pinned random seed defined in `code/config.py` as `BASELINE_SEED`. **Error Handling**: If `BASELINE_SEED` is missing from config, raise `RuntimeError` with message "MISSING_CONFIG: BASELINE_SEED required for reproducibility" and exit with code 1. **Output**: A binary label set for the baseline.
- [ ] T034a [US3] Implement `code/evaluation.py` to perform a **Wilcoxon signed-rank test** (Primary, per FR-005) comparing the detector's F1-scores against the **Stratified Random Baseline** (generated in T033). **Inputs**: F1-scores from detector and baseline across all seeds. **Output**: Report p-value and effect size. **Dependency**: Requires T033 (baseline generation).
- [ ] T035 [US3] Implement `code/evaluation.py` to check SC-003 (F1 std dev ≤ 0.15). **Logic**: Calculate the standard deviation of F1-scores across rubric types. If the standard deviation exceeds 0.15, **flag the study as FAILED** in the final report (T038). **Action**: Record the std dev and the "FAILED" status in `data/processed/metrics.csv`. **Dependency**: Requires T034a.
- [ ] T037 [US3] Implement sensitivity analysis for ground-truth drop threshold (FR-007). **Logic**: Sweep the values defined in `code/config.py` as `SENSITIVITY_THRESHOLDS` (e.g., a representative range of low-magnitude thresholds) and report variation in F1-scores. **Output**: Save results to `data/processed/sensitivity_analysis.csv` with columns: `rubric_type`, `threshold`, `f1_score`, `precision`, `recall`. **Dependency**: Requires T031 (ground truth labels).
- [ ] T038 [US3] Generate final `data/processed/metrics.csv` and evaluation report with p-values, F1 scores, and sensitivity analysis results. **Schema**: `metrics.csv` must contain columns: `metric_name`, `value`, `p_value`, `effect_size`. **Report Format**: Generate a Markdown (Wikidata Q107380638, https://www.wikidata.org/wiki/Q107380638) report (`data/processed/evaluation_report.md`) summarizing the findings, including any "FAILED" flags from T035. **Dependency**: Requires T034a, T035, and T037.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T040b [P] Refactor `code/config.py` into classes: Organize constants into classes `DataConfig`, `ModelConfig`, and `EvalConfig` with docstrings.
- [X] T041 [P] Implement sequential seed processing in `code/main.py` to ensure memory safety and runtime < 4 hours (process seeds one by one if needed). **Note**: This logic is integrated into the main pipeline loop, not a separate task.
- [ ] T042 [P] Additional unit tests for edge cases (missing data, zero variance) in `tests/unit/`
- [ ] T043 Run quickstart.md validation and verify all artifacts are checksummed

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
- **User Story 2 (P2)**: Depends on US1 (requires $G(t)$ data)
- **User Story 3 (P3)**: Depends on US1 and US2 (requires divergence data and ground truth labels)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion (T013) MUST precede math computation (T014)
- Ground truth derivation (T031) MUST be preceded by Independence Checks (T032a/T032b)
- Independence check (T032a/T032b) MUST run before any ground truth is used for metrics
- Contaminated window exclusion (T025a -> T025b -> T025c) MUST run before Flagging Logic (T022)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T017 which is sequential to T005a
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (if dependencies allow, e.g., US2/US3 can start once US1 data format is known)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for G(t) calculation logic in tests/unit/test_ingestion_math.py"
Task: "Unit test for dG(t) derivative logic in tests/unit/test_ingestion_math.py"

# Launch implementation tasks (sequential dependency):
Task: "Download CHERRL logs to data/raw/cherrl_logs/" (T013)
Task: "Implement ingestion logic to compute G(t) and dG(t)" (T014, T015)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion + Divergence)
4. **STOP and VALIDATE**: Test ingestion on real data and verify $G(t)$ calculation
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Implement detector logic → Test independently → Deploy/Demo
4. Add User Story 3 → Implement evaluation and statistical tests → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Detector Logic) - can start once T013 (download) is done
 - Developer C: User Story 3 (Evaluation) - can start once T031 (ground truth logic) is defined
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Ensure all data download tasks (T013) validate the source against the verified dataset URLs in the plan's input block (CHERRL repository, HuggingFace) before fetching. No fake data generation is allowed.
- **CRITICAL**: Ensure T032a (independence check) and T032b run BEFORE T031 (ground truth generation) to prevent circular validation. T032a must check J_unbiased vs J_gold and T032b must check J_biased vs J_gold. Both must **halt the pipeline** (exit code 1) if correlation > 0.8.
- **CRITICAL**: If SC-003 fails (F1 std dev > 0.15), T035 must mark the study as **FAILED** in the report.
- **CRITICAL**: T034a must use the Wilcoxon signed-rank test as the primary method per FR-005, comparing against the Stratified Random Baseline generated in T033.
- **CRITICAL**: T013 must implement a "fail loud" strategy for real data (exit code 2) and **DO NOT** support mock mode.
- **CRITICAL**: T022, T032a, and T032b must load empirical constants (multiplier, correlation threshold) from `code/config.py` rather than hardcoding them, to defer empirical specifics as per Spec Assumptions.
- **CRITICAL**: T025a, T025b, T025c must implement FR-009 to exclude contaminated windows where hacking event duration exceeds the sliding window size, preventing suppression of the z-score baseline. T025c must run before T022.
- **CRITICAL**: T037 must implement FR-007 sensitivity analysis to validate robustness across rubric types by sweeping the drop threshold over the values defined in `code/config.py` as `SENSITIVITY_THRESHOLDS`.
- **CRITICAL**: T033 and T034a must use a pinned random seed from `code/config.py` (`BASELINE_SEED`). If the seed is missing, the task must raise an error and exit.
- **CRITICAL**: T033 must use a fixed sample fraction defined in `code/config.py` (`BASELINE_SAMPLE_FRACTION`) with **NO default value**; the researcher must explicitly define it (via T033-Pre).
- **CRITICAL**: T017 must implement linear interpolation for missing timesteps, epsilon floor (1e-9) for zero variance, and NaN handling (merged from T024).
- **CRITICAL**: T040a has been removed as redundant (utils already split in plan). T040b remains for config refactoring.
- **CRITICAL**: T017 has been moved to Phase 2 to align with US1 dependencies and is now sequential to T005a.
- **CRITICAL**: T015 explicitly mandates the "min 5 samples" constraint for rolling z-score calculation.
- **CRITICAL**: T025a/b/c explicitly details the algorithm for contaminated window exclusion (identify segments > 20 steps, mask from baseline) and outputs the mask as a DataFrame column, NOT a separate JSON file.
- **CRITICAL**: T037 explicitly defines the output schema columns (rubric_type, threshold, f1_score, precision, recall) and references the config key for sweep values.
- **CRITICAL**: T033 explicitly defines the baseline logic as "sample timesteps uniformly stratified by rubric type" and requires `BASELINE_SAMPLE_FRACTION` in `code/config.py` with NO default value.
- **CRITICAL**: T038 explicitly defines the schema for `metrics.csv` and the format of the evaluation report.
- **CRITICAL**: T024 has been merged into T017 to handle NaN values in `code/utils/math_utils.py`.
- **CRITICAL**: T041 logic is now part of `code/main.py` and not a separate task.
- **CRITICAL**: T022 is marked [ ] because it depends on T025 (contaminated window mask) which is also [ ]. T022 cannot be complete until T025 is implemented.
- **CRITICAL**: T015 is marked [ ] because it depends on T017 (edge case handlers) which is also [ ]. T015 cannot be complete until T017 is implemented.