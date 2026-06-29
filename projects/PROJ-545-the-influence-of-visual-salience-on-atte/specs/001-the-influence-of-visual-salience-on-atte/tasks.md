# Tasks: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Input**: Design documents from `/specs/001-visual-salience-aDDM/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `paper/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy, scipy, pandas, opencv-python, scikit-learn, numba)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/data/__init__.py` and `code/models/__init__.py`
- [ ] T005 [P] Create `code/data/download.py` skeleton (do not fetch data yet)
- [ ] T006 [P] Create `code/data/salience.py` skeleton for ITTI/GBVS and text-heuristic computation (FR-002)
- [ ] T007 [P] Create `code/models/addm.py` skeleton for choice-only aDDM implementation (FR-003)
- [ ] T008 [P] Setup `code/main.py` entry point with argument parsing for pipeline stages
- [ ] T009 [P] Configure `pytest` with contract test fixtures for schema validation
- [ ] T010 [P] [FR-008] Create `code/data/preprocess.py` skeleton to handle proxy control variables (lives saved/lost, species, age, gender) for FR-008

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Salience Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest Moral Machine data and compute visual/textual salience scores for every scenario.

**Independent Test**: Run pipeline on a [deferred]-row subset; verify output CSV has `salience_score` (0.0–1.0) for all rows, including text-only fallbacks.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Contract test: Verify `salience_score` column exists and is numeric in `tests/contract/test_salience_schema.py`
- [ ] T012 [P] [US1] Unit test: Verify text-only heuristic returns valid score when image URL is broken in `tests/unit/test_salience_fallback.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/data/download.py`: Fetch Moral Machine CSV, subset to ≤ 50,000 rows using stratified sampling (by outcome and species) with seed=42, save to `data/raw/moral_machine_subset.csv` (FR-001)
- [ ] T014 [P] [US1] Implement `code/data/salience.py`: Visual salience using ITTI/GBVS (OpenCV) for image stimuli, normalize to 0.0–1.0 (FR-002)
- [ ] T015 [US1] Implement `code/data/salience.py`: Text-salience heuristic (word frequency + position) for text-only stimuli, normalize to 0.0–1.0, and implement fallback logic for broken image URLs (FR-002, Edge Case)
- [ ] T016 [US1] Implement `code/data/preprocess.py`: Merge raw data with salience scores (visual/text/fallback) into a single `salience_score` column (0.0–1.0) and output `data/processed/salience_enriched.csv`. Assert max(salience_score) <= 1.0 and min >= 0.0 (US-001, FR-002)
- [ ] T017 [US1] Add logging for salience computation failures and fallback triggers

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - aDDM Simulation and Parameter Fitting (Priority: P2)

**Goal**: Implement choice-only aDDM and fit parameters via grid search on CPU.

**Independent Test**: Run fitting on 5-fold CV split; verify model converges within 30 mins on 2-core CPU and outputs log-likelihood.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test: Verify output JSON contains `log_likelihood`, `drift_rate`, `threshold`, `salience_weight` in `tests/contract/test_addm_output.py`
- [ ] T019 [P] [US2] Unit test: Verify grid search completes without GPU error in `tests/unit/test_addm_cpu_fit.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/models/addm.py`: Choice-only aDDM likelihood function (no RT) using NumPy/SciPy (FR-003)
- [ ] T021 [US2] Implement `code/models/fit.py`: Grid search over salience weights (to 1.0, step 0.1) to be executed on the training set of each fold (FR-004)
- [ ] T022 [US2] Implement `code/models/fit.py`: K-fold cross-validation loop that creates a stratified sample for fitting (SC-002) and orchestrates T021 inside each fold (US-002, SC-002)
- [ ] T023 [US2] Implement `code/models/fit.py`: Retry logic for non-convergence (cap retries at 3); exclude scenario if fails after the limit is reached (Edge Case)
- [ ] T024 [US2] Implement `code/main.py`: Orchestrate fitting stage with progress bar and timeout guard
- [ ] T025 [US2] Save best parameters and log-likelihood to `data/processed/addm_fitted_params.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Comparison and Sensitivity Analysis (Priority: P3)

**Goal**: Compare salience-augmented vs. baseline models and perform sensitivity analysis on thresholds.

**Independent Test**: Run comparison script; verify report includes AIC/BIC differences, p-values (Bonferroni corrected), and sensitivity table for thresholds {0.01, 0.05, 0.10}.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test: Verify sensitivity report contains log-likelihood and AIC for all threshold values in `tests/contract/test_comparison_report.py`
- [ ] T027 [P] [US3] Unit test: Verify VIF calculation flags collinearity > 5.0 in `tests/unit/test_vif_diagnostic.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/analysis/compare.py`: Compute AIC/BIC for baseline vs. salience models (FR-005)
- [ ] T029 [US3] Implement `code/analysis/compare.py`: Perform k-fold cross-validation statistical comparison with Bonferroni correction (apply ONLY if number of tests > 3) (FR-007)
- [ ] T030 [US3] Implement `code/analysis/compare.py`: Sensitivity analysis sweeping decision threshold cutoffs over the specific set {0.01, 0.05, 0.10} and recording AIC/LL variation (FR-005, SC-003)
- [ ] T031 [US3] Implement `code/analysis/diagnostics.py`: Compute VIF for salience vs. proxy control variables (lives saved/lost, species, etc.) (FR-008, SC-004)
- [ ] T032 [US3] Implement `code/analysis/diagnostics.py`: Add collinearity flagging logic (VIF > 5.0) to report
- [ ] T033 [US3] Generate final report `paper/results/comparison_report.md` with associational framing only (FR-006), including a "Limitations" section and explicit discussion of proxy control variables (US-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` and `README.md`
- [ ] T040 Code cleanup and refactoring of `code/data/` and `code/models/`
- [ ] T041 Performance optimization: Ensure grid search runs ≤ 30 mins on 2-core CPU (SC-002)
- [ ] T042 [P] Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T043 Verify all artifacts are checksummed and `updated_at` timestamps updated (Constitution Principle V)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (salience scores)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 output (fitted models)
- **Polish (Final Phase)**: Requires US1, US2, and US3 outputs to perform final validation

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
Task: "Contract test for salience schema in tests/contract/test_salience_schema.py"
Task: "Unit test for salience fallback in tests/unit/test_salience_fallback.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py in code/data/download.py"
Task: "Implement salience.py (visual) in code/data/salience.py"
Task: "Implement salience.py (text) in code/data/salience.py"
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
   - Developer A: User Story 1 (Data)
   - Developer B: User Story 2 (Model)
   - Developer C: User Story 3 (Analysis)
3. Once US1/US2/US3 complete:
   - Team: Polish & Cross-Cutting Concerns
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All tasks must run on a multi-core CPU with sufficient RAM and no GPU.. Do not use 8-bit quantization or CUDA.
- **Constraint Preservation**: Tasks strictly adhere to FR-008 (no 'Voluntary' tags, no 'System 1/2' proxies, no 'Salience Withdrawal' simulations) and specific numeric constraints (thresholds {0.01, 0.05, 0.10}, retry cap 3).