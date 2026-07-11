# Tasks: The Impact of Ambient Noise on Cognitive Flexibility in Remote Workers

**Input**: Design documents from `/specs/001-ambient-noise-cognitive-flexibility/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-114-the-impact-of-ambient-noise-on-cognitive/`)
- [ ] T002 Initialize Python 3.11 project with `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `scipy`, `pyyaml`, `snakemake`, `pytest` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup `Snakefile` workflow orchestration
 - [ ] T004.1 [P] Add `Snakefile` rule `preprocess`
 - [ ] T004.2 [P] Add `Snakefile` rule `models`
 - [ ] T004.3 [P] Add `Snakefile` rule `sensitivity`
 - [ ] T004.4 [P] Add `Snakefile` rule `hash_artifacts`
- [ ] T005 [P] Create data directory structure: `data/raw/`, `data/processed/`, `data/results/`
- [X] T006 [P] Implement `code/config.py` to manage noise thresholds (low, high), random seeds, and file paths
- [~] T007 Create base data contracts in `contracts/` (e.g., `analysis_dataset.schema.yaml`, `model_results.schema.yaml`)
- [~] T008 Configure global logging and error handling infrastructure in `code/__init__.py`
- [~] T009 Implement `code/preprocess.py` skeleton <!-- FAILED: unspecified -->
 - [ ] T009.1 [P] [Skeleton] Implement function signature `filter_participants` (depends on T007 schema)
 - [ ] T009.2 [P] [Skeleton] Implement function signature `normalize_reaction_times` (depends on T007 schema)
 - [ ] T009.3 [P] [Skeleton] Implement function signature `aggregate_noise_logs` (depends on T007 schema)
- [~] T010 Implement `code/models.py` skeleton
 - [ ] T010.1 [P] [Skeleton] Implement function signature `fit_linear_mixed_effects`
 - [ ] T010.2 [P] [Skeleton] Implement function signature `likelihood_ratio_test`
 - [ ] T010.3 [P] [Skeleton] Implement function signature `post_hoc_tukey_hsd`
 - [ ] T010.4 [P] [Skeleton] Implement function signature `apply_multiple_comparison_correction`
- [~] T011 Implement `code/robustness.py` skeleton
 - [ ] T011.1 [P] [Skeleton] Implement function signature `replicate_final_score_only`
 - [ ] T011.2 [P] [Skeleton] Implement function signature `sweep_noise_thresholds`
 - [ ] T011.3 [P] [Skeleton] Implement function signature `exclude_extreme_sensitivity`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw decibel logs and task-switching performance data, filter low-quality participants, normalize data, and aggregate noise into bins.

**Independent Test**: Run the Snakemake workflow on a synthetic dataset mimicking the expected structure and verify that participants with <80% valid logging hours or <90% task completion rates are excluded and reaction time outliers are removed.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T012 [P] [US1] Contract test for `data/processed/analysis_dataset.parquet` schema in `tests/test_contracts.py::test_analysis_dataset_schema` using synthetic fixture `fixtures/synthetic_raw_data.csv`
- [~] T013 [P] [US1] Unit test for participant filtering logic in `tests/test_preprocess.py::test_filter_participants_excludes_low_validity` using synthetic fixture `fixtures/low_validity_participants.csv`
- [~] T014 [P] [US1] Unit test for MAD-based outlier removal and log-transformation in `tests/test_preprocess.py::test_normalize_reaction_times_removes_outliers` using synthetic fixture `fixtures/outlier_reaction_times.csv`

### Implementation for User Story 1

- [~] T015 [US1] Implement `code/preprocess.py` function `filter_participants` to exclude logs with <80% valid hours AND <90% task completion rates (FR-001)
- [~] T016 [US1] Implement `code/preprocess.py` function `normalize_reaction_times` using log-transformation and MAD outlier removal where absolute deviation > 3.5 * MAD per participant (FR-003)
- [ ] T017 [US1] Implement `code/preprocess.py` function `aggregate_noise_logs` to calculate average and hourly variability (std dev) for continuous decibel values (FR-002)
- [ ] T017.1 [US1] Implement `code/preprocess.py` function `create_noise_bins` to generate a categorical 'noise_level' column (Low/Moderate/High) from continuous averages based on FR-002 thresholds, ensuring 'noise_sensitivity_score' is passed through to the output (FR-002, US-3)
- [ ] T018 [US1] Add `Snakefile` rule `preprocess` to chain `filter_participants`, `normalize_reaction_times`, `aggregate_noise_logs`, and `create_noise_bins`, outputting to `data/processed/analysis_dataset.parquet`
- [ ] T019 [US1] Add validation step in `Snakefile` to validate the output of T018 (`data/processed/analysis_dataset.parquet`) against the contract defined in T007 (`contracts/analysis_dataset.schema.yaml`)
- [ ] T019.1 [US1] Implement metric calculation task to compute the proportion of retained participants, comparing it against the 'actual recruited sample size' sourced from the metadata file generated during data ingestion, and write the result to `data/results/retention_metrics.json` (SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Primary Statistical Analysis (Priority: P2)

**Goal**: Fit a linear mixed-effects model to test the non-linear relationship between noise levels and cognitive flexibility, including a quadratic term and post-hoc comparisons.

**Independent Test**: Run the analysis on a pre-computed dataset where the relationship is known and verify that the model correctly identifies the non-linear term as significant (p < 0.05) or null as expected.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for `data/results/model_results.parquet` schema in `tests/test_contracts.py::test_model_results_schema` using synthetic fixture `fixtures/synthetic_model_input.csv`
- [ ] T021 [P] [US2] Unit test for LMM convergence and quadratic term significance detection in `tests/test_models.py::test_lmm_convergence_and_significance` using synthetic fixture `fixtures/quadratic_signal_data.csv`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/models.py` function `fit_linear_mixed_effects` with fixed effects (avg noise, noise^2, variability) and random intercepts for participants (FR-004)
- [ ] T023 [US2] Implement `code/models.py` function `likelihood_ratio_test` to compare linear vs. quadratic models (FR-004)
- [ ] T023.1 [US2] Implement metric extraction task to extract Cohen's f² effect size and a confidence interval for the quadratic term, and verify if the interval excludes zero to support the hypothesis (SC-002)
- [ ] T024 [US2] Implement `code/models.py` function `post_hoc_tukey_hsd` to perform pairwise comparisons on the categorical 'noise_level' bin variable (Low/Moderate/High) produced by T017.1 (FR-005)
- [ ] T025 [US2] Implement `code/models.py` function `apply_multiple_comparison_correction` to apply correction to the pairwise p-values from T024 (FR-008), consuming the LRT p-value from T023 for reporting but applying correction only to the set of pairwise comparisons
- [ ] T026 [US2] Add `Snakefile` rule `models` to execute `fit_linear_mixed_effects`, `likelihood_ratio_test`, and `post_hoc_tukey_hsd`, saving results to `data/results/model_results.parquet`
- [ ] T027 [US2] Implement convergence rate calculation in `Snakefile` to aggregate convergence results across primary and sensitivity sweeps, verify the rate meets the ≥95% threshold defined in SC-005, and log the result

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform robustness checks including replicating analysis on final scores only and conducting a sensitivity analysis on noise thresholds.

**Independent Test**: Modify threshold values in the configuration and verify that the output reports how the headline rates (e.g., inconsistency or significance rates) change across the sweep.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for `data/results/sensitivity_results.parquet` schema in `tests/test_contracts.py::test_sensitivity_results_schema` using synthetic fixture `fixtures/synthetic_sensitivity_input.csv`
- [ ] T029 [P] [US3] Unit test for threshold sweep logic (40, 45, 50dB and 60, 65, 70dB) in `tests/test_robustness.py::test_sweep_noise_thresholds_logic` using synthetic fixture `fixtures/threshold_sweep_data.csv`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/robustness.py` function `replicate_final_score_only` to run analysis using only final task-switching scores (controlling for baseline) (FR-007)
- [ ] T031 [US3] Implement `code/robustness.py` function `sweep_noise_thresholds` to iterate over fixed sets of lower and upper decibel ranges including representative low values and a representative set of mid-range values. and report significance variation (FR-006)
- [ ] T032 [US3] Implement `code/robustness.py` function `exclude_extreme_sensitivity` to re-run analysis excluding participants with extreme self-reported noise sensitivity, consuming the preprocessed dataset from T018 which contains the 'noise_sensitivity_score' column (US-3, not FR-006)
- [ ] T033 [US3] Add `Snakefile` rule `sensitivity` to execute `replicate_final_score_only` and `sweep_noise_thresholds`, saving results to `data/results/sensitivity_results.parquet`
- [ ] T034 [US3] Add `Snakefile` rule `hash_artifacts` to compute SHA-256 hashes of `data/processed/`, `data/results/` and update `state.yaml` (Constitution Principle V)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates: Update `docs/quickstart.md` with synthetic data generation steps and add `docs/api/preprocess.md` with function signatures; verify `quickstart.md` contains a working `snakemake --dry-run` command
- [ ] T036 Run `ruff check code/` and fix all reported errors; verify `ruff check code/` returns exit code 0
- [ ] T037 Performance optimization: Refactor `code/models.py` to use batch processing if needed; run `Snakefile` on N=150 synthetic data and record execution time in `data/results/perf_metrics.json` ensuring it completes within 6 hours
- [ ] T038 [P] Additional unit tests for edge cases: Add `tests/test_preprocess.py::test_filter_participants_handles_empty_input` and `tests/test_models.py::test_lmm_convergence_failure_handling`
- [ ] T039 Run `Snakefile` dry-run and full execution on synthetic data to validate end-to-end pipeline
- [ ] T040 [P] Run quickstart.md validation: Execute the commands in `docs/quickstart.md` on a fresh environment; verify all commands complete without error and produce the expected `data/processed/analysis_dataset.parquet` file

---

## Phase 7: Data Acquisition & Validation (Critical for Real-World Execution)

**Goal**: Establish a reliable, real-world data source and validation pipeline to replace synthetic data for final research execution, ensuring compliance with "Real data + real results only" rules.

**Independent Test**: Successfully download a real dataset (or verified public subset) and run the full pipeline without synthetic data generation, producing a `data/raw/` directory with checksummed, real-world files.

- [ ] T041 [P] [Data] Identify a real, publicly available dataset source (e.g., UCI, Kaggle) for ambient noise and task-switching metrics, then implement `code/data_fetch.py` to download it to `data/raw/`, handle network errors, and validate file integrity against source checksums.
- [ ] T042 [Data] Implement `code/data_fetch.py` to download the real dataset (or a representative sample if the full set is too large) from the identified source, ensuring the script handles network errors and validates file integrity (checksums) against the source's provided hash.
- [ ] T043 [Data] Create a validation task in `Snakefile` that runs on the downloaded real data to verify it matches the schema defined in T007 (`contracts/analysis_dataset.schema.yaml`) before allowing `preprocess` to run.
- [ ] T044 [Data] Update `docs/research.md` to explicitly cite the source of the real data used, including the URL, access date, and any specific version or subset identifier.
- [ ] T045 [Data] Add a task to generate a "data provenance report" in `data/results/data_provenance.json` that logs the source URL, file size, row count, and checksum of the real data used for the analysis.
- [ ] T046 [Data] Update `specs/001-ambient-noise-cognitive-flexibility/spec.md` Assumptions section to formally document the deviation from the "mobile app/Prolific" source to the identified public dataset, ensuring Single Source of Truth compliance.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Acquisition (Phase 7)**: Can run in parallel with Phase 2/3 but must complete before the final research execution; T043 must pass before T018 can run on real data.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`data/processed/analysis_dataset.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 results (`data/results/model_results.parquet`)

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
- Data acquisition (Phase 7) can proceed in parallel with implementation of US1/US2/US3 using synthetic data

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for `data/processed/analysis_dataset.parquet` schema in `tests/test_contracts.py::test_analysis_dataset_schema`"
Task: "Unit test for participant filtering logic in `tests/test_preprocess.py::test_filter_participants_excludes_low_validity`"

# Launch all models for User Story 1 together:
Task: "Implement `filter_participants` in `code/preprocess.py`"
Task: "Implement `normalize_reaction_times` in `code/preprocess.py`"
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
 - Developer D: Data Acquisition (Phase 7)
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
- **Critical Reminder**: Do not fabricate data. All analysis tasks must eventually consume real data from the source identified in T041. Synthetic data is for pipeline validation only.