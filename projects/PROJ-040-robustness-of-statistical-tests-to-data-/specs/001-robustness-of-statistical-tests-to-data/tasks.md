# Tasks: Robustness of Statistical Tests to Data Contamination

**Input**: Design documents from `/specs/001-robustness-contamination/`
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

- [X] T001 Create project structure per implementation plan: `mkdir -p projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/data projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/utils projects/PROJ-040-robustness-of-statistical-tests-to-data-/code/viz projects/PROJ-040-robustness-of-statistical-tests-to-data-/tests projects/PROJ-040-robustness-of-statistical-tests-to-data-/data/raw projects/PROJ-040-robustness-of-statistical-tests-to-data-/data/processed projects/PROJ-040-robustness-of-statistical-tests-to-data-/data/results projects/PROJ-040-robustness-of-statistical-tests-to-data-/docs` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` containing pinned dependencies: numpy==1.26.4, scipy==1.12.0, pandas==2.2.0, matplotlib==3.8.0, requests==2.31.0, pytest==7.4.0
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with black (line-length=88) and ruff (target-version=py311) configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/validation/validate_citations.py` to verify dataset URLs against the "# Verified datasets" block in `plan.md`
- [X] T005 [P] Implement `code/validation/checksum_artifacts.py` to generate content hashes (SHA-256 hex) for scripts (created in T002) and directory structure (created in T006), explicitly updating the YAML state file `state/projects/PROJ-040-robustness-of-statistical-tests-to-data-.yaml` with an `artifact_hashes` map (YAML format, not JSON). Note: This task runs after T006 to ensure directory structure exists.
- [X] T006 [P] Setup directory structure: `data/raw/`, `data/processed/`, `data/results/`, `code/data/`, `code/utils/`, `code/viz/`, `tests/`
- [X] T007 Create base configuration module for random seed (fixed) and memory constraints (RAM check) in `code/utils/config.py` with API: `get_seed() -> int`, `check_memory_limit() -> bool`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Spec Resolution & Alignment (Critical Pre-Implementation)

**Purpose**: Resolve contradictions and deferred values in spec.md before implementation begins

- [ ] T008.0 [P] Update spec.md FR-002 to reference the contamination rates that will be determined in `research.md` (e.g., "See research.md for resolved rates") or maintain '[deferred]' if research is pending. Do NOT hardcode specific values [0.01, 0.05, 0.10, 0.20] into the spec. Ensure the spec reflects the research output, not the other way around.
- [ ] T008.0.1 [P] Add a 'Spec Deviation' section to spec.md explicitly documenting that empirical quantities (contamination rates) are deferred to the research phase, aligning with Constitution Principle II.
- [ ] T008.1 [P] Update spec.md FR-003 to reflect dataset substitution (UCI HAR/Wine instead of Iris/Breast Cancer) and explicitly reference the 'Spec Deviation Log' in plan.md. Add a new 'Spec Deviation' section to spec.md detailing this change and update the 'Key Entities' section to reflect the actual datasets used (UCI HAR (2505.06730, https://arxiv.org/abs/2505.06730) [UNRESOLVED-CLAIM: c_4bb2bbc1 — status=verified], UCI Wine).
- [ ] T008.2 [P] Update spec.md User Story 2 acceptance criteria to require 'resampling from a single homogeneous population' instead of 'shuffling labels', aligning with the plan.
- [~]T008.2.1 [P] Update the 'Independent Test' section of User Story 2 in spec.md to replace 'shuffling labels' with 'resampling from a single homogeneous population', ensuring full alignment with the plan.
- [ ] T008.3 [P] Update spec.md FR-007 to mandate 'associational observations' instead of 'causal findings', resolving the internal contradiction.
- [X] T008.3.1 [P] Correct the contradictory phrasing in spec.md FR-007 by changing 'report causal findings' to 'report associational observations', ensuring the spec artifact itself is logically consistent.

---

## Phase 4: User Story 1 - Simulate Contaminated Datasets (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets with controlled levels of Gaussian noise and adversarial outliers from verified UCI sources.

**Independent Test**: Run `code/data/generate_contamination.py` on a single dataset (UCI Wine) and verify output files contain exact outlier counts and noise distributions.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T008 [P] [US1] Write failing unit tests for contamination injection logic in `tests/unit/test_contamination.py` (verify outlier count = `round(* total_rows)`) for T011
- [~] T009 [P] [US1] Write failing unit tests for Gaussian noise distribution in `tests/unit/test_contamination.py` (verify mean/std match spec) for T011

### Implementation for User Story 1

- [~] T010 [P] [US1] Implement `code/data/download_datasets.py` to fetch UCI HAR and UCI Wine via `wget`/`requests` and validate numeric columns
- [~] T011 [US1] Implement `code/data/generate_contamination.py` to inject Gaussian noise and extreme outliers at rates defined in `config.py` (which is populated by `research.md` or defaults) using `numpy`. Do NOT read rates directly from spec.md.
- [~] T012 [US1] Add logic to handle missing values (impute or log warning) and skip non-numeric columns in `code/data/generate_contamination.py`
- [~] T013 [US1] Save contaminated datasets to `data/processed/` with derivation logs and checksums
- [~] T014 [US1] Implement sensitivity analysis sweep for contamination magnitude thresholds (σ to 10σ, step 1σ) in `code/data/generate_contamination.py`, outputting to `data/results/sensitivity.csv` with columns [threshold, false_positive_rate, variation_in_fpr]. Explicitly map 'variation_in_fpr' to SC-005's requirement for 'variation in false-positive rates'.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Execute Monte Carlo Simulation (Priority: P1)

**Goal**: Run Monte Carlo simulations (n=1000 per condition) of standard t-tests and ANOVA on clean and contaminated data to estimate Type I error and power [UNRESOLVED-CLAIM: c_ca8b7e92 — status=not_enough_info] to estimate Type I error and power

**Independent Test**: {{claim:c_6130269b}}

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T015 [P] [US2] Unit test for Monte Carlo loop logic in `tests/unit/test_simulation.py` (verify seed 42 reproducibility)
- [~] T016 [P] [US2] Integration test for Type I error calculation on clean data in `tests/integration/test_simulation_pipeline.py`

### Implementation for User Story 2

- [~] T017 [P] [US2] Implement `code/utils/stats_helpers.py` with functions for standard t-test, ANOVA, and Bonferroni correction
- [~] T018 [US2] Implement `code/data/run_simulation.py` to execute multiple iterations per condition (dataset x contamination rate x magnitude) for UCI HAR and UCI Wine, saving results to `data/results/simulation_results.csv` with columns [dataset, rate, error_rate, power]. Explicitly depend on T014's output (`sensitivity.csv`) for the magnitude parameter sweep.
- [ ] T019 [US2] Implement logic to resample from a single homogeneous population for Type I error (null hypothesis) instead of label shuffling, per spec.md User Story 2. Algorithm: sample with replacement from the pooled data of both groups to ensure a true null hypothesis.
- [ ] T019.1 [US2] Update the 'Independent Test' section of User Story 2 in spec.md to replace 'shuffling labels' with 'resampling from a single homogeneous population', ensuring traceability between spec and code.
- [ ] T020 [US2] Apply memory limit checks and dataset sampling if necessary during simulation execution
- [ ] T021 [US2] Save simulation results (empirical Type I error, power) to `data/results/` as CSV/JSON with metadata, using filename pattern `results_{dataset}_{rate}.csv`
- [ ] T022 [US2] Add logging for iteration progress and memory usage to prevent OOM crashes on free-tier runners

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Compare Standard vs. Robust Estimator Performance (Priority: P2)

**Goal**: Apply robust estimators (trimmed mean, Winsorized mean) to contaminated data and compare error rates/power against standard tests.

**Independent Test**: Compare error inflation of standard t-test vs. trimmed mean t-test on the same contaminated dataset; robust method must show lower error inflation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for trimmed mean and Winsorized mean implementations in `tests/unit/test_robust_estimators.py`
- [ ] T024 [P] [US3] Integration test for power loss calculation on clean data in `tests/integration/test_robust_comparison.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `code/utils/robust_estimators.py` with trimmed mean and Winsorized mean functions compatible with `scipy` t-test
- [ ] T026 [US3] Modify `code/data/run_simulation.py` (or create `run_robust_simulation.py`) to execute robust tests on the same contaminated datasets
- [ ] T027 [US3] Calculate difference in empirical Type I error rates between standard and robust methods for each contamination level
- [ ] T028 [US3] Measure and report percentage power loss of robust methods compared to standard tests on clean data
- [ ] T029 [US3] Implement `code/viz/plot_results.py` to generate visualizations comparing error inflation and power loss across contamination levels, outputting to `docs/figures/error_inflation.png` (line plot) and `docs/figures/power_loss.png` (bar chart)
- [ ] T030 [US3] Ensure all findings are framed as associational observations regarding test behavior. Concrete action: Add a disclaimer string to the report header in `docs/paper_draft.md` and ensure all output text in `code/viz/plot_results.py` uses 'associational' language, avoiding causal claims about data generation (FR-007).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/paper_draft.md` summarizing methodology (Methodology section) and limitations (Limitation section)
- [ ] T032 Code cleanup and refactoring of simulation loops for performance
- [ ] T033 Performance optimization: Parallelize independent Monte Carlo iterations if memory allows
- [ ] T034 [P] Additional unit tests for edge cases (small datasets, high contamination rates) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation to ensure full pipeline execution within 6 hours on free-tier constraints, generating `state/validation_report.json` with `duration` and `status` fields
- [ ] T036 [P] Verify all dataset citations match the "# Verified datasets" block in `plan.md` and update `state/` manifest: Implement a script to compute SHA-256 hashes of downloaded files in `data/raw/`, compare them against the hashes recorded in the `plan.md` verified block, and update `state/projects/PROJ-040-robustness-of-statistical-tests-to-data-.yaml` with a YAML map `artifact_hashes: { "filename": "sha256_hex_string" }` for each verified file.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Spec Resolution (Phase 3)**: Depends on Foundational - CRITICAL for aligning spec and tasks
- **User Stories (Phase 4+)**: All depend on Foundational and Spec Resolution phases completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and Spec Resolution (Phase 3) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) and Spec Resolution (Phase 3) - Depends on US1 data generation
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) and Spec Resolution (Phase 3) - Depends on US1 data and US2 simulation logic

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All Spec Resolution tasks (Phase 3) can run in parallel
- Once Foundational and Spec Resolution phases complete, US1 and US2 can start in parallel (data gen vs stats logic)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1 & 2

```bash
# Launch data generation and stats helper implementation together:
Task: "Implement code/data/generate_contamination.py"
Task: "Implement code/utils/stats_helpers.py"

# Launch tests for both stories together:
Task: "Write failing unit tests for contamination injection logic"
Task: "Write failing unit tests for Monte Carlo loop logic"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: Spec Resolution (CRITICAL - aligns spec and tasks)
4. Complete Phase 4: User Story 1 (Data Generation)
5. Complete Phase 5: User Story 2 (Standard Simulation)
6. **STOP and VALIDATE**: Test standard simulation on clean data and verify Type I error ≈ 0.05
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + Spec Resolution → Foundation ready
2. Add User Story 1 → Test independently → Data ready
3. Add User Story 2 → Test independently → Standard results ready
4. Add User Story 3 → Test independently → Robust comparison ready
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + Spec Resolution together
2. Once Foundational and Spec Resolution are done:
 - Developer A: User Story 1 (Data Download & Contamination)
 - Developer B: User Story 2 (Simulation Engine & Stats)
 - Developer C: User Story 3 (Robust Estimators & Viz)
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
- **Critical Constraint**: All simulations MUST complete within 6 hours on 2 CPU cores, 7GB RAM [UNRESOLVED-CLAIM: c_1fa12f75 — status=not_enough_info] Use sampling if necessary.
- **Critical Constraint**: No GPU usage. Use `numpy`/`scipy` default precision only.
- **Critical Constraint**: All datasets must be from verified UCI/OpenML sources listed in `plan.md`.
- **Critical Constraint**: Spec must be updated before implementation to resolve contradictions and deferred values.