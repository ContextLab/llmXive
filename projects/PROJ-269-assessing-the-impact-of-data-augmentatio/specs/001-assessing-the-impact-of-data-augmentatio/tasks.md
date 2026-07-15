# Tasks: Assessing the Impact of Data Augmentation on Statistical Power in Small Samples

**Input**: Design documents from `/specs/001-assess-augmentation-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-269-assessing-the-impact-of-data-augmentatio/code/`, `data/raw/`, `data/derived/`, `results/`, `tests/`, `contracts/`
- [ ] T001b [P] Create `projects/PROJ-269-assessing-the-impact-of-data-augmentatio/requirements.txt` with pinned versions: pandas, numpy, scikit-learn, imbalanced-learn, scipy, requests, pytest
- [ ] T001c [P] Create `projects/PROJ-269-assessing-the-impact-of-data-augmentatio/code/__init__.py` and `tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/download_data.py`: Fetch a set of verified UCI datasets (Breast Cancer, Ionosphere, Heart Disease) via direct URLs. Save to `data/raw/` and compute SHA256 checksums. **Logic**: If the fetched count is not 3, log a warning indicating the deviation from the original FR-001 intent of 5 datasets. Do not attempt to fetch unverified datasets.
- [ ] T005 [P] Implement `code/subsample.py`: Create stratified subsampling function for N=15, 25, 40. **Target Column Detection**: Look for 'target', then 'class', then 'label', then default to the last column. **Edge Cases**: If class count < 5 for a configuration, skip it, log a warning, and append the skipped configuration details to `data/derived/skipped_configurations.log`.
- [ ] T006 [P] Implement `code/augment.py`: Create functions for Gaussian noise injection, SMOTE, and Random Oversampling using `imbalanced-learn`; ensure no CUDA/GPU dependencies; handle zero-variance samples.
- [~] T008a [P] Define JSON schema for simulation output: Create `contracts/simulation_schema.json` defining the structure for p-value distributions, error rates, and metadata. **Must be valid JSON and exist before T007 runs.**
- [X] T007 [P] Implement `code/simulation.py`: Full implementation of Monte Carlo loop with random seed pinning, configuration management, and a sufficient number of iterations per config to ensure statistical convergence. **Pre-check**: Validate that `contracts/simulation_schema.json` exists and is valid JSON before proceeding. **Logic**: Implement internal helper functions for label permutation (Type I) and mean shift (Type II) within this module; do not rely on external tasks for these functions. **Dependency**: Requires T008a.
- [X] T008b [P] Implement `code/analyze.py`: Implement error rate calculation (Type I/II), KS test wrapper (p-value distributions only), and JSON reporting structure. **Dependency**: Requires T007 output.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Error Rate Estimation (Priority: P1) 🎯 MVP

**Goal**: Establish ground-truth baseline for Type I and Type II error rates using original, non-augmented small-sample datasets.

**Independent Test**: Run simulation on original subsampled datasets (N=15, 25, 40) without augmentation and verify output includes calculated empirical error rates and confidence intervals.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for stratified subsampling logic in `tests/test_subsample.py` (verify class ratio preservation)
- [X] T010 [P] [US1] Integration test for baseline simulation loop in `tests/test_simulation.py` (verify p-value distribution generation)

### Implementation for User Story 1

- [X] T013 [US1] Implement baseline Monte Carlo loop (1,000 iterations per config as per FR-004) in `code/simulation.py` (no augmentation step). **Logic**: Include internal functions for (1) label permutation (shuffle all labels using pinned seed) for Type I error and (2) mean shift (Cohen's d = 0.5) for Type II error. **Target Column**: Use the priority 'target' -> 'class' -> 'label' -> last column for both ground-truth logic and subsampling. **Dependency**: Requires T007 infrastructure.
- [X] T014 [US1] Implement error rate calculation in `code/analyze.py`: Compute proportion of p < 0.05 and bootstrap 95% CIs for baseline results.
- [~] T015 [US1] Save baseline results to `results/[dataset]_[size]_baseline_null.json` and `results/[dataset]_[size]_baseline_alt.json`. **Naming convention**: `[dataset]` = lowercase underscore (e.g., 'breast_cancer'), `[size]` = integer (e.g., '15').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Augmentation Technique Simulation (Priority: P2)

**Goal**: Apply Gaussian noise, SMOTE, and Random Oversampling to subsampled datasets and re-run hypothesis tests.

**Independent Test**: Apply SMOTE to a specific dataset configuration and verify output includes transformed dataset and resulting p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for SMOTE edge case handling (zero variance samples) in `tests/test_augment.py`
- [ ] T017 [P] [US2] Unit test for Gaussian noise injection parameters in `tests/test_augment.py`

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement Gaussian noise injection in `code/augment.py` with configurable standard deviation (default 0.1).
- [ ] T019 [P] [US2] Implement SMOTE augmentation in `code/augment.py` with edge case handling for N < 5 or extreme imbalance.
- [ ] T020 [P] [US2] Implement Random Oversampling in `code/augment.py`.
- [ ] T021 [US2] Integrate augmentation functions into `code/simulation.py` Monte Carlo loop (separate branches for Null and Alt conditions). **Requires T013 (baseline loop) and T018-T020 completion.**
- [ ] T022 [US2] Implement logic to detect and exclude zero-variance synthetic samples before hypothesis testing to prevent division-by-zero.
- [ ] T023 [US2] Save augmented results to `results/[dataset]_[size]_[method]_null.json` and `results/[dataset]_[size]_[method]_alt.json`. **Mandatory**: Distinct files for Null and Alt conditions for each method.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and Threshold Identification (Priority: P3)

**Goal**: Compare empirical error rates between baseline and augmented groups, identify unsafe thresholds, and generate final report.

**Independent Test**: Process results for all configurations and verify summary report lists measured error rates, differences, and fixed design threshold (0.10).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Integration test for comparative analysis logic in `tests/test_analysis.py`
- [ ] T025 [P] [US3] Contract test for final JSON output schema in `tests/contract/test_results_schema.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement KS test wrapper in `code/analyze.py` for supplementary distributional shift diagnostics: **Apply ONLY to p-value distributions** (FR-006). **Constraint**: Input validation must reject any input that is not a list/array of p-values.
- [ ] T027 [US3] Implement comparative analysis logic: Calculate difference in Type I/II error rates between baseline and each augmentation method.
- [ ] T028 [US3] Implement threshold identification logic: Flag configurations where Type I error > 0.10 **AND** compare against baseline error rate to quantify impact (FR-005).
- [ ] T029 [US3] Implement final report generation in `code/analyze.py`: Aggregate results, compute power (1 - Type II), and format output. **Mandatory**: Include fixed design threshold (0.10) value in JSON output (SC-001).
- [ ] T030 [US3] Inject "DISCLAIMER: Findings are associational..." string into **every** result JSON file (baseline and all augmented variants) and summary report as per FR-007. **Mechanism**: Use glob pattern `results/**/*.json` to discover all files. Insert the disclaimer at the JSON key `metadata.disclaimer`.
- [ ] T031 [US3] Create `code/main.py` orchestration script to run full pipeline: Download → Subsample → Baseline → Augment → Analyze → Report. **Must be last task in Phase 5.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Add comprehensive docstrings and type hints to all `code/*.py` modules
- [ ] T033 [P] Add `pytest` fixtures for dataset loading and random seed management
- [ ] T034 [P] Validate computational runtime against a predefined temporal constraint using a sample run of a representative number of iterations.
- [ ] T035 [P] Verify memory usage remains within acceptable limits during the full simulation loop.
- [ ] T036 [P] Update `quickstart.md` with instructions for running the full study
- [ ] T037 [P] Generate `data-model.md` documenting `Dataset Configuration`, `Simulation Run`, and `Error Rate Profile` entities

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (logic before orchestration)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different augmentation techniques (T018, T019, T020) can be implemented in parallel

---

## Parallel Example: User Story 2

```bash
# Launch augmentation implementations in parallel:
Task: "Implement Gaussian noise injection in code/augment.py"
Task: "Implement SMOTE augmentation in code/augment.py"
Task: "Implement Random Oversampling in code/augment.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Baseline only)
4. **STOP and VALIDATE**: Test baseline error rates against theoretical expectations
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Baseline) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Augmentation) → Test independently → Deploy/Demo
4. Add User Story 3 (Analysis) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline logic)
 - Developer B: User Story 2 (Augmentation techniques)
 - Developer C: User Story 3 (Analysis and reporting)
3. Stories complete and integrate in `main.py`

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: Ensure all tasks run on CPU-only CI (no 8-bit quantization, no CUDA, no large models). Use `imbalanced-learn` CPU mode and small sample sizes only.
- **Target Column Priority**: 'target' > 'class' > 'label' > last column (used in T005, T013).
- **Schema Dependency**: T007 requires T008a (schema) to exist before execution.
- **Log File**: Skipped configurations are logged to `data/derived/skipped_configurations.log`.