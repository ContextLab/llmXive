# Tasks: Investigating the Validity of the Inverse‑Square Law at Sub‑Millimeter Scales

**Input**: Design documents from `/specs/001-investigating-the-inverse-square-law/`
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

- [ ] T001-A Create root project directory `projects/PROJ-191-investigating-the-validity-of-the-invers/`
- [ ] T001-B Create `code/`, `tests/`, `data/`, and `docs/` directories within the project root
- [ ] T001-C Create nested directories: `code/data/`, `code/models/`, `code/inference/`, `code/robustness/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/contract/`, `tests/integration/`
- [ ] T002 Initialize Python 3.11 project with dependencies (`code/requirements.txt`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement versioning utility for atomic state updates in `code/utils/versioning.py`
- [ ] T005 [P] Setup logging infrastructure and configuration management in `code/config.py`
- [ ] T006 Create base data models for `HarmonizedDataset` in `code/data/loaders.py`
- [ ] T007 Setup directory structure for `data/raw/`, `data/processed/`, and `data/results/` (ensure `mkdir -p` logic or parent creation)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Download raw force-vs-separation data from arXiv, convert to SI units, align on a common grid, and construct a full covariance matrix.

**Independent Test**: Execute `code/data/download.py` and `code/data/harmonize.py` against the provided arXiv URLs; verify output is a single CSV/JSON file containing aligned force data, separation distances, and a valid positive-definite covariance matrix with no missing values in the micro-scale range..

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. T010-T012 must fail before T013-A/T013-B can proceed.**

- [ ] T010 [P] [US1] Unit test for SI unit conversion logic in `tests/unit/test_harmonize.py`
- [ ] T011 [P] [US1] Contract test for data schema validation in `tests/contract/test_harmonized_dataset.py`
- [ ] T012 [P] [US1] Integration test for end-to-end download and harmonization in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T013-A [US1] Implement `code/data/download.py` to fetch arXiv 2021 supplements, verify checksums, and prepare for validation
- [ ] T013-B [US1] Implement `code/data/download.py` extension to fetch arXiv 2023 review calibration curves, verify checksums, and prepare for validation
- [ ] T013-VAL [US1] **Sequential Dependency**: Ensure `code/data/download.py` triggers the Reference-Validator Agent after download and halts if validation fails (no [P] tag)
- [ ] T014 [P] [US1] Implement unit conversion and grid alignment in `code/data/harmonize.py`
- [ ] T015 [US1] Implement **full** covariance matrix construction (statistical + systematic) in `code/data/harmonize.py` ensuring the output `HarmonizedDataset` retains the full matrix as per FR-002
- [ ] T015-TRANS [US1] Implement conversion logic to generate a **block-diagonal/banded approximation** of the full covariance matrix for use in likelihood evaluation (T022), while preserving the original full matrix in the dataset
- [ ] T016 [US1] Implement fallback logic for bootstrap resampling if < 3 independent runs are found
- [ ] T017 [US1] Add error handling for missing URLs, redirects, and non-overlapping separation ranges

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Bayesian Model Inference (Priority: P2)

**Goal**: Run `emcee` MCMC to estimate posteriors for α and λ, and `dynesty` nested sampling to compute Bayesian evidence for model comparison.

**Independent Test**: Run `code/inference/mcmc.py` and `code/inference/nested.py` on the harmonized dataset; verify output includes posterior samples, Bayes factor, and MCMC convergence (Gelman-Rubin < 1.01) within the prescribed CPU time limit.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for Yukawa force model implementation in `tests/unit/test_physics.py`
- [ ] T019 [P] [US2] Unit test for log-likelihood function with banded covariance in `tests/unit/test_likelihood.py`
- [ ] T020 [P] [US2] Integration test for MCMC convergence detection in `tests/integration/test_mcmc_diagnostics.py`
- [ ] T025-TEST [US2] Unit test for injection-recovery logic (FR-008) in `tests/unit/test_injection_recovery.py`
- [ ] T026-TEST [US2] Unit test for null-simulation baseline logic (FR-009) in `tests/unit/test_null_simulation.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement Newtonian and Yukawa-modified force models in `code/models/physics.py`
- [ ] T022 [US2] Implement log-likelihood function using the **block-diagonal/banded approximation** of the covariance matrix in `code/models/likelihood.py`
- [ ] T023 [US2] Implement `emcee` runner with a **dynamic step loop**: start at a sufficient number of steps, check Gelman-Rubin; if ≥ 1.01, extend in batches until convergence or a hard cap of [deferred] steps is reached (per FR-003)
- [ ] T024 [US2] Implement `dynesty` nested sampler for Newtonian and Yukawa models in `code/inference/nested.py`
- [ ] T025 [US2] Implement injection-recovery test (FR-008) to validate pipeline accuracy
- [ ] T026 [US2] Implement null-simulation test (FR-009) to establish false-positive baseline
- [ ] T027 [US2] Add runtime monitoring and automatic subsampling logic to enforce 6-hour limit (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform leave-one-experiment-out cross-validation and systematic uncertainty inflation tests to ensure result stability.

**Independent Test**: Run `code/robustness/cross_val.py` and `code/robustness/uncertainty.py`; verify that Bayes factors and % credible intervals for α remain stable (shifts < 10-15%) across all iterations.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for leave-one-out logic in `tests/unit/test_cross_val.py`
- [ ] T029 [P] [US3] Integration test for uncertainty inflation stability in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement leave-one-experiment-out cross-validation loop in `code/robustness/cross_val.py`
- [ ] T031 [US3] Implement systematic uncertainty inflation test in `code/robustness/uncertainty.py`
- [ ] T032 [US3] Implement parallel execution of robustness iterations using `multiprocessing`
- [ ] T033 [US3] Implement logic to compare variation in credible upper limits across iterations against the **15% threshold** (SC-003); if variation > 15%, **flag the result as unstable and log a critical error**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Generate visualization plots for posteriors and Bayes factors in `code/utils/plotting.py`
- [ ] T035-A [P] Update `README.md` with project overview, prerequisites, and high-level run command
- [ ] T035-B [P] Update `docs/quickstart.md` with detailed pipeline execution instructions, data paths, and troubleshooting
- [ ] T036 Run full pipeline end-to-end validation and verify `state/projects/PROJ-191...yaml` updates correctly
- [ ] T037 [P] Optimize likelihood evaluation speed (banded covariance tuning) if runtime > 2.5 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately. **T001-A, T001-B, T001-C must run sequentially** to ensure parent directories exist.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on harmonized data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on inference results from US2

### Within Each User Story

- **TDD Flow**: Test tasks (e.g., T010-T012, T025-TEST, T026-TEST) MUST be written and **FAIL** before their corresponding implementation tasks (T013-T017, T025, T026) are executed, even if marked [P].
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] (except T001-A/B/C which are sequential) can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SI unit conversion logic in tests/unit/test_harmonize.py"
Task: "Contract test for data schema validation in tests/contract/test_harmonized_dataset.py"
Task: "Integration test for end-to-end download and harmonization in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch arXiv supplements..."
Task: "Implement unit conversion and grid alignment in code/data/harmonize.py"
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

- [P] tasks = different files, no dependencies (unless explicitly sequential for TDD or directory creation)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence