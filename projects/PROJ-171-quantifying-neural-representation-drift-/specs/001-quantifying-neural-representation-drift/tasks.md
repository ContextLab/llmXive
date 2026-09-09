# Tasks: Quantifying Neural Representation Drift During Skill Learning

**Input**: Design documents from `/specs/001-quantify-neural-drift/`
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

- [ ] T001a [P] Create directory structure: `src/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `docs/paper/`
- [ ] T001b [P] Create `.gitignore` rules for `data/` and `__pycache__/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**⚠️ DEFINITIVE IMPLEMENTATION**: T006 and T007 are the definitive implementations for validation and loading. No user-story phase tasks may redefine these files.

- [ ] T004 Setup `data/raw/` and `data/processed/` directory structure with `.gitignore` rules
- [ ] T005 [P] Implement `src/utils/logging.py` for structured logging and progress tracking
- [ ] T006 [P] Setup `src/data/validator.py` to enforce FR-009 (variable presence check). This is the definitive validator; do not redefine in later phases.
- [ ] T007 [P] Implement `src/data/loader.py` using `datasets.load_dataset(..., streaming=True)` for HF ingestion. **Must ensure data is prepared for fine-grained temporal alignment** (FR-001, FR-009). This is the definitive loader; do not redefine in later phases.
- [ ] T008 Configure environment configuration management (`.env` support for dataset IDs)
- [ ] T009 [P] Implement `src/data/preprocessor.py` with full logic:
    - Align neural bins to trial events (high-resolution temporal binning) (FR-001)
    - Filter units present in <80% of sessions (FR-002)
    - Exclude performance-modulated neurons via regression against error signals (FR-003)
    - Implement linear interpolation for missing behavioral logs OR flag subject (US-1 Scenario 3)
    - Generate `NeuralPopulationMatrix` per day and save to `data/processed/neural_matrix_day_{day}.parquet`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Drift Quantification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, process into stable population matrices, and compute the primary drift rate metric `b`.

**Independent Test**: Run on a synthetic dataset with known drift parameters (random rotation of tuning curves) and verify recovered slope `b` matches ground truth within 5% tolerance.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data schemas in `tests/contract/test_schemas.py`
- [ ] T011 [P] [US1] Integration test for synthetic drift recovery in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T014a [US1] Verify `src/data/preprocessor.py` output: Ensure `data/processed/neural_matrix_day_{day}.parquet` files are generated with correct schema (US-1, FR-001, FR-002, FR-003). **Depends on T009 completion.**
- [ ] T014b [US1] Implement linear interpolation for missing behavioral logs in `src/data/preprocessor.py` (US-1 Scenario 3, FR-009). **This is the logic verified by T014c.**
- [ ] T014c [US1] Verify that `src/data/preprocessor.py` correctly implements linear interpolation for missing behavioral logs and flags subjects appropriately (US-1 Scenario 3). **Depends on T014b.**
- [ ] T015 [US1] Implement `src/analysis/rdm.py` to compute pairwise Pearson correlation distances and generate RDM (FR-004). **Note: Implements Pearson distance locally within `rdm.py`; does NOT rely on `src/utils/metrics.py` (extended by T030) to ensure safe parallel execution with T030.**
- [ ] T016 [US1] Implement `src/analysis/drift.py`:
    - **Primary Model**: Fit exponential decay model `d(Δt) = a·exp(−b·Δt) + c` to RDM off-diagonals (Constitution VII). **Note: FR-005 mandates linear, but Constitution VII overrides. A spec change request is required to align FR-005.**
    - **Fallback**: If exponential fit fails (non-convergence), **MUST** fit linear model `a + b·t` to satisfy FR-005 and flag as "non-drifting" if both fail.
    - **Deliverable**: Return `DriftResult` object (schema: `decay_rate: float`, `model_type: str`, `fit_status: str`) and save to `data/results/drift_results.json` (JSON structure: `{"decay_rate": <float>, "model_type": <str>, "fit_status": <str>}`).
- [ ] T017 [US1] Add validation and error handling for convergence failures
- [ ] T018 [US1] Add logging for preprocessing steps (unit exclusion counts, alignment stats)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Behavioral Correlation & Hypothesis Testing (Priority: P2)

**Goal**: Correlate drift rates with learning speeds, perform permutation testing, and fit LMM.

**Independent Test**: Provide pre-computed drift rates and learning speeds for synthetic subjects with known correlation (r=0.6) and verify permutation test returns p < 0.05 and LMM detects significant fixed effect.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for correlation output schema in `tests/contract/test_correlation_schema.py`
- [ ] T020 [P] [US2] Integration test for permutation test power in `tests/integration/test_correlation.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `src/analysis/correlation.py` helper to calculate "time to reach success" from behavioral logs (Depends on T016 validated output)
- [ ] T022 [US2] Implement robust regression (Huber) in `src/analysis/correlation.py` as a **preprocessing step ONLY to remove outliers before LMM**. **Do not replace LMM; LMM (T024) is the primary method for FR-006 compliance.** (FR-006, Depends on T016, feeds T024)
- [ ] T023 [US2] Implement permutation test (shuffles) in `src/analysis/correlation.py` to generate null distribution (FR-006)
- [ ] T024 [US2] Implement Linear Mixed-Effects Model (LMM) fitting in `src/analysis/correlation.py` for subject-level random effects (FR-006). **Return `statsmodels.LMEResults` object and save summary to `data/results/lmm_summary.csv`.**
- [ ] T025 [US2] Implement Bonferroni correction logic if multiple metrics tested (FR-007)
- [ ] T026 [US2] Add warning logic for N < 15 subjects (power limitation) (US-2 Acceptance Scenario 3)
- [ ] T027 [US2] Format results with explicit significance labels (e.g., "statistically significant at α=0.05")

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation & Sensitivity Analysis (Priority: P3)

**Goal**: Verify results are not artifacts of metric choice or threshold selection.

**Independent Test**: Run pipeline with 80% threshold, then 70% and 90%, verifying drift trend direction remains consistent.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for robustness output schema in `tests/contract/test_robustness_schema.py`
- [ ] T029 [P] [US3] Integration test for metric variance in `tests/integration/test_robustness.py`

### Implementation for User Story 3

- [ ] T030 [US3] Extend `src/utils/metrics.py` to support Cosine and Mahalanobis distances (FR-007). **Depends on T015 completion.**
- [ ] T031 [US3] Implement `src/analysis/robustness.py` to sweep stability threshold across **{70%, 75%, 80%, [deferred], [deferred]}** (derived from FR-008 and US-3 Acceptance Scenario 2 "representative range"). (FR-008)
- [ ] T032 [US3] Implement logic to re-run drift calculation for each threshold and metric, reporting variance (FR-008)
- [ ] T033 [US3] Implement split-half reliability check (US-3 Acceptance Scenario 3)
- [ ] T034 [US3] Generate plots showing drift rate variation across thresholds and metrics using **matplotlib**. **Save to `docs/paper/fig_sensitivity_thresholds.png`.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Update `README.md` with CLI usage examples and installation instructions
- [ ] T035b [P] Add sensitivity analysis plot and methodology to `docs/paper/`
- [ ] T036 Code cleanup and refactoring of `src/analysis/` modules
- [ ] T037 Performance optimization to ensure <6h runtime and <7GB RAM usage (SC-005)
- [ ] T038 [P] Additional unit tests in `tests/unit/test_rdm.py`, `tests/unit/test_drift.py`
- [ ] T039 Run `quickstart.md` validation and verify synthetic data generation works

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (drift rates)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output (drift rates)

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
Task: "Contract test for data schemas in tests/contract/test_schemas.py"
Task: "Integration test for synthetic drift recovery in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/preprocessor.py (T009)"
Task: "Implement src/analysis/rdm.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently on synthetic data
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
- **Data Constraint**: Ensure `src/data/loader.py` fails loudly if real data fetch fails; do NOT use synthetic fallbacks.
- **Compute Constraint**: Ensure all analysis steps (T014-T034) run within CPU-only constraints (no GPU dependencies).