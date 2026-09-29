# Tasks: Phase Transitions in Amorphous Solids Under Shear Stress

**Input**: Design documents from `/specs/001-phase-transitions-in-amorphous-solids/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `data/raw`, `data/processed`, `code`, `tests/unit`, `tests/integration`, `specs/contracts` in `projects/PROJ-phase-transitions-in-amorphous-solids/`. Specifically create files: `specs/contracts/trajectory.schema.yaml`, `specs/contracts/precursor_metrics.schema.yaml`, `specs/contracts/analysis_results.schema.yaml`.
- [X] T002 Initialize Python project with dependencies (`requirements.txt`: numpy, scipy, pandas, h5py, scikit-learn, matplotlib, datasets, tqdm)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils.py` with global `SEED = 42` and streaming helpers for HDF5/Parquet
- [X] T007 Create base data schema definitions in `specs/contracts/` (trajectory.schema.yaml, precursor_metrics.schema.yaml) with explicit validation rules for particle count and data types.
- [X] T008 Configure logging infrastructure to capture warnings for indeterminate trajectories (US1) using Python's `logging` module with file handlers.
- [X] T009 Setup environment configuration for dataset source verification (HuggingFace `amorphous-silicon-shear-trajectories`) including verified URL and checksum validation logic.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Precursor Detection Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw MD trajectory data, compute $D^2_{min}$ and local shear strain, and identify the yielding timestep.

**Independent Test**: Process a single small trajectory (≤ 10,000 steps) and verify the output CSV contains per-particle $D^2_{min}$ and a flagged yielding index.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for Falk-Langer $D^2_{min}$ calculation in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Integration test for stress-drop detection logic in `tests/unit/test_preprocess.py`
- [X] T012 [US1] Integration test for "indeterminate" flagging when stress drop is ambiguous in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 1

- [X] T013a [US1] Implement `code/preprocess.py`: Create streaming loader function for HDF5/Parquet files. **MUST enforce FR-006**: Check particle count; if > 100k, raise an explicit `ValueError` and exit. No synthetic fallbacks.
- [X] T014a [US1] Implement `code/preprocess.py`: Implement neighbor list builder for particle proximity calculation
- [X] T014b [US1] Implement `code/preprocess.py`: Implement Falk-Langer $D^2_{min}$ calculation loop for every particle (FR-001)
- [X] T015a [US1] Implement `code/preprocess.py`: Implement stress-strain curve extraction from trajectory data
- [X] T015b [US1] Implement `code/preprocess.py`: Implement drop detection over timesteps to identify yielding onset (FR-002). **Constraint**: MUST identify the *first* significant stress drop (>5% decrease) and halt detection after this point. Do not detect multiple events.
- [X] T015c [US1] **STRICT ENFORCEMENT**: Implement logic to ensure ONLY the first significant stress drop is flagged as the yielding onset. **Constraint**: If multiple drops occur, ignore subsequent ones. This task replaces the removed T037 to strictly adhere to FR-002's single-yield requirement. **Dependency**: T015b.
- [X] T016 [US1] Implement `code/preprocess.py`: Flag datasets as "indeterminate" if no sharp stress peak is found and log warnings
- [X] T036 [P] [US1] Implement robust error handling in `code/preprocess.py` for corrupted or incomplete trajectory files (missing frames, NaN values)
- [X] T038 [P] [US1] Add numerical stability checks in `code/preprocess.py` to detect and handle NaN/Infinity values in $D^2_{min}$ calculations (e.g., due to neighbor list issues)
- [X] T039 [P] [US1] **STRICT ENFORCEMENT**: Implement a "fail loud" policy in data loading: raise explicit `RuntimeError` on real data fetch failure; **NO synthetic fallbacks allowed**. **Constraint**: Must not catch exceptions that lead to synthetic data generation. This task is a prerequisite for T017 to ensure data integrity.
- [X] T040 [P] [US1] Add unit tests for edge cases: corrupted files, missing frames, NaN values in `tests/unit/test_preprocess.py`
- [X] T017 [US1] Write output artifacts: `data/processed/precursor_metrics.csv` (per-particle $D^2_{min}$) and `data/processed/yield_flags.json` (yielding timestep). **Dependency**: T015a, T015b, T015c, T016, T039.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compare $D^2_{min}$ distributions between brittle and ductile trajectories to identify structural precursors.

**Independent Test**: Run analysis on two labeled datasets (brittle, ductile) and verify output includes KS-test statistic and p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for shear-band aggregation logic in `tests/unit/test_analysis.py`
- [X] T019 [P] [US2] Unit test for **Kolmogorov-Smirnov (KS) test** implementation in `tests/unit/test_analysis.py`. **Note**: The spec (FR-003) mandates KS-test on shear-band aggregated data. This test must verify the KS-test logic. **Dependency**: T021.
- [X] T020 [P] [US2] Integration test for "Power Limitation" warning when sample size < 30 in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 2

- [X] T021 [US2] Aggregate $D^2_{min}$ values to shear bands using **k-means clustering (k=3)** with seed=42 (from `utils.py`) to account for spatial autocorrelation and ensure Numerical Determinism (Constitution Principle VII). **Output**: CSV with columns `shear_band_id`, `mean_D2_min`, `particle_count`. **Dependency**: T017.
- [X] T022 [US2] **MANDATORY**: Perform a **two-sample Kolmogorov-Smirnov (KS) test** to compare brittle vs. ductile distributions of shear-band mean $D^2_{min}$ values. **Rationale**: FR-003 mandates this test. The aggregation to shear bands (T021) accounts for spatial autocorrelation as required by the spec. **Output**: `data/processed/ks_test_results.json` containing the observed statistic, p-value, and metadata framing the result as an "associational finding". **Dependency**: T021.
- [X] T023 [US2] Check sample size (N ≥ 30). If < 30, halt and report "Power Limitation" warning (US2 Acceptance)
- [X] T024 [US2] **MANDATORY ENFORCEMENT**: **Enforce** Bonferroni correction (FR-005) to the KS-test p-values. **Logic**: The system MUST automatically detect if more than one hypothesis test is performed (e.g., across strain rates/temperatures) and MUST enforce the correction on all generated p-values. **Output**: `data/processed/corrected_p_values.json`. **Dependency**: T022.
- [X] T025 [US2] Generate output artifacts: `data/processed/ks_test_results.json` (statistic, p-value), `data/processed/histograms.png` (overlay of distributions), and `data/processed/significance_report.json` (final p-value vs alpha=0.05 pass/fail). **Dependency**: T024. **Note**: This task MUST explicitly compare the corrected p-value against the alpha=0.05 threshold and write a pass/fail determination to the report, satisfying SC-002.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Threshold Validation (Priority: P3)

**Goal**: Validate a specific $D^2_{min}$ threshold for predicting time-to-failure and perform sensitivity analysis.

**Independent Test**: Apply derived threshold to held-out validation set and verify FPR/FNR and F-score are reported correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_predict.py`
- [X] T027 [P] [US3] Integration test for confusion matrix generation in `tests/integration/test_full_pipeline.py`

### Implementation for User Story 3

- [X] T028a [US3] Derive the base threshold value from US1/US2 outputs. **Algorithm**: Select the D_min value that maximizes F1-score on the training set. **Dependency**: T025.
- [X] T028a-bis [US3] **MANDATORY**: Perform a hold-out split on the dataset to create a validation set. **Output**: `data/processed/validation_set_indices.json`. **Dependency**: T017, T025. **Note**: This explicitly satisfies SC-001 by defining the set against which F-score is measured. The split must occur after US1 and US2 outputs are fully processed.
- [X] T028b [US3] Define 'time-to-failure' as an independent ground truth (total strain at catastrophic failure)
- [X] T029 [US3] Sweep $D^2_{min}$ threshold over the specific range: `{threshold - 0.05, threshold, threshold + 0.05}` as mandated by FR-004. **Output**: Generate intermediate data structure and `data/processed/sensitivity_table.csv` containing the sweep results. **Dependency**: T028a.
- [X] T030 [US3] Calculate False Positive Rate (FPR), False Negative Rate (FNR), **True Positives (TP), True Negatives (TN), and F-score (F1)** for each threshold step. **MANDATORY**: Generate `data/processed/sensitivity_table.csv` containing the full sweep results (threshold, FPR, FNR, F1) to satisfy FR-004's requirement for a comparative table. **Dependency**: T028a-bis.
- [X] T031 [US3] Generate output artifacts: `data/processed/p prediction_results.json` (confusion matrix, F-score, FPR, FNR), `data/processed/sensitivity_table.csv`. **Dependency**: T030.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Performance & Validation (Cross-Cutting)

**Purpose**: Ensure the pipeline meets runtime and memory constraints on the target CI environment.

- [X] T032a [P] [SC-004] Implement `code/metrics.py`: Runtime instrumentation wrapper to measure execution time
- [X] T033a [P] [SC-005] Implement `code/metrics.py`: Peak memory tracking logic
- [X] T035 [SC-004, SC-005] Execute full pipeline on GitHub Actions runner to verify runtime and memory constraints. **Requirement**: Must run only after T017, T025, T031 are complete. **Requirement**: Must invoke instrumentation logic from T032a/T033a to capture metrics. **Dependency**: T017, T025, T031, T032a, T033a.
- [X] T032b [P] [SC-004] Implement `code/metrics.py`: Time-limit check and reporting logic using metrics from T035. **Note**: [P] applies only to relationship with T033b (they can run in parallel with each other), but both are strictly sequential after T035 completion. **Dependency**: T035.
- [X] T033b [P] [SC-005] Implement `code/metrics.py`: GB limit check and reporting logic using metrics from T035. **Note**: [P] applies only to relationship with T032b (they can run in parallel with each other), but both are strictly sequential after T035 completion. **Dependency**: T035.
- [X] T034 [P] Generate `data/processed/performance_report.json` with all measured outcomes

**Dependencies**: T032b and T033b depend on T035 output; T035 depends on T032a and T033a being implemented AND T017, T025, T031 being complete.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 output** (`precursor_metrics.csv` from T017). T021, T022 require T017 completion.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US1 and US2 outputs**. T028a requires T025 completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Ensure `code/preprocess.py` fails loudly if real data fetch fails; no synthetic fallbacks allowed (T039).
- **Memory Safety**: All data loading must use streaming/chunking to stay under available RAM constraints.
- **Execution Order**: T032a/T033a must be completed before T035; T035 must be completed before T032b/T033b. T017 must be completed before T021/T022; T025 must be completed before T028a.
- **Constraint Preservation**: All statistical tests must strictly adhere to the spec (KS-test in T022) and Constitution Principle VII (k-means k=3).
- **Critical Dependencies**: T017 requires T015b and T039 to be complete. T030 requires T028a-bis to be complete.
- **Note on T037**: Task T037 (multi-yield detection) has been removed as it contradicted FR-002's single-yield requirement. T015c now handles the single-yield constraint.