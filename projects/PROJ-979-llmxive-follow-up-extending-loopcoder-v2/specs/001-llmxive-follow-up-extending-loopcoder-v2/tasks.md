# Tasks: llmXive follow-up: extending "LoopCoder-v2: Only Loop Once for Efficient Test-Time Computation Scali"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-loopcoder-v2/`
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

## Model Substitution Note

**CRITICAL**: The spec's `Assumptions` and `FR-001`/`FR-002` mandate `LoopCoder-v2-2B`. However, the `LoopCoder-v2` checkpoint is not verified/available. This project substitutes `LoopCoder-v2-2B` with `CodeLlama-1.3b-Instruct` (CPU validation) and `CodeLlama-3b/7b-Instruct` (GPU full analysis). All success criteria (FR-001/002) are re-baselined for this substitution. The methodology (entropy extraction, convergence tracking) remains identical.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create explicit directory structure: `data/raw`, `data/processed`, `code/src`, `code/tests`, `code/notebooks`, `paper`, `state`, `contracts` in `projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/`
- [ ] T002 Initialize Python project with `transformers`, `torch`, `scikit-learn`, `pandas`, `datasets`, `pytest`, `docker` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/src/data_loader.py` to: (1) fetch HumanEval and MBPP datasets via `datasets.load_dataset`, (2) save raw copies to `data/raw/` with SHA256 checksums in `data/checksums.txt`, (3) apply stratified sampling by difficulty, (4) flag strata with <50 samples as 'underpowered' in `data/processed/strata_log.json`, and (5) save processed splits to `data/processed/`.
- [ ] T005 [P] Create `code/src/entropy.py` stub with function signature for semantic entropy extraction (FR-001)
- [ ] T005c [P] Define FLOPs utility function in `code/src/utils.py`: Implement formula `FLOPs = parameters * sequence_length * k` for baseline calculation (FR-006, SC-002).
- [ ] T006 [P] Create `code/src/inference.py` stub with function signature for iterative refinement execution (FR-002)
- [ ] T007 Define `InputProblem` and `ConvergenceTrajectory` dataclasses in `code/src/models.py`
- [ ] T008 Setup environment configuration for model paths (CodeLlama-1.3b for CPU, CodeLlama-3b/7b for GPU) in `code/.env.example`
- [ ] T009 Implement Docker sandbox configuration for code execution safety in `code/Dockerfile` and `code/docker-compose.yml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Extract initial semantic entropy and track convergence trajectories to compute Spearman correlation.

**Independent Test**: Run `code/src/entropy.py` and `code/src/inference.py` on a stratified sample (N=50 for CPU validation) to produce `data/processed/entropy_results.csv` and `data/processed/convergence_results.csv`, then verify `code/src/analysis.py` computes a non-error correlation coefficient.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for entropy clustering logic in `code/tests/test_entropy.py`
- [ ] T011 [P] [US1] Integration test for end-to-end entropy + convergence pipeline on N=5 sample using mock fixtures in `code/tests/test_analysis.py` (ensure independent of T012/T013 artifacts)

### Implementation for User Story 1

- [ ] T012 [US1] Implement semantic entropy extraction in `code/src/entropy.py`: Generate N=10 samples, cluster by exact code match/execution result, compute Shannon entropy (FR-001). Handle undefined entropy (zero entropy) by assigning `entropy=1e-9` or excluding the sample. **MUST log exclusion count and rate to `data/processed/exclusion_log.json`** (FR-007).
- [ ] T013 [US1] Implement iterative refinement execution in `code/src/inference.py`: Run model for $k \in \mathbb{Z}^+$, detect first correct solution vs reference, record non-convergence events (FR-002, FR-007). **Must run AFTER T012 completes and verifies `data/processed/entropy_results.csv` exists** to prevent data leakage (Principle VI).
- [ ] T013b [US1] Implement sensitivity inference pass in `code/src/inference.py`: Re-run model for $k=4$ on the same dataset to generate trajectory data for sensitivity analysis (SC-004).
- [ ] T014 [US1] Implement data processing pipeline in `code/src/data_loader.py`: Filter datasets, handle strata with <50 samples (flag as underpowered, FR-007), save processed splits. (Note: Logic merged into T004, this task ensures integration with downstream steps).
- [ ] T015 [US1] Implement Spearman correlation calculation in `code/src/analysis.py`: Compute $\rho$ between entropy and convergence step, calculate p-value (FR-003).
- [ ] T016 [US1] Add logging and result serialization to `data/processed/entropy_results.csv` and `data/processed/convergence_results.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Core Correlation Data Generated)

---

## Phase 4: User Story 2 - Dynamic Router Simulation (Priority: P2)

**Goal**: Simulate a lightweight dynamic routing strategy using logistic regression to predict optimal loop counts and evaluate FLOPs savings.

**Independent Test**: Train a logistic regression model on US1 data, apply to test set, and verify reports of prediction accuracy vs random baseline and FLOPs savings vs static $k=2$ baseline with statistical significance testing.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for logistic regression training and prediction in `code/tests/test_analysis.py`
- [ ] T018 [P] [US2] Statistical test validation for non-inferiority vs static baseline in `code/tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement logistic regression router training in `code/src/analysis.py`: Train on entropy proxies to predict optimal $k$ (FR-004). **Dependencies: T012, T013 (raw data generation), NOT T015**.
- [ ] T020 [US2] Implement router evaluation logic: Compare prediction accuracy against random baseline (predict $k=1$) and test significance ($p < 0.05$) (FR-006).
- [ ] T021 [US2] Implement FLOPs estimation and savings calculation: **Use the formula from T005c** (`parameters * sequence_length * k`) to calculate static $k=2$ baseline FLOPs. Compare dynamic router vs static baseline, perform non-inferiority test on accuracy (FR-006, SC-002).
- [ ] T022 [US2] Integrate router simulation results into `data/processed/router_results.csv` and update `code/src/analysis.py` report generation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Router Simulation Complete)

---

## Phase 5: User Story 3 - Statistical Robustness & Sensitivity Analysis (Priority: P3)

**Goal**: Ensure findings are robust to multiple comparisons and convergence definition sensitivity.

**Independent Test**: Re-run correlation analysis with Bonferroni/Holm-Bonferroni correction and sweep convergence thresholds ($k \in \{2, 3, 4\}$) to verify stability of correlation coefficients.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for multiple-comparison correction implementation in `code/tests/test_robustness.py`
- [ ] T024 [P] [US3] Sensitivity analysis sweep validation in `code/tests/test_robustness.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement multiple-comparison correction in `code/src/robustness.py`: **Explicitly implement the Holm-Bonferroni algorithm** and apply it to p-values across difficulty strata (FR-005, US-003).
- [ ] T026 [US3] Implement sensitivity analysis loop in `code/src/robustness.py`: **Re-run inference logic for k=4 (using T013b data)** and sweep convergence threshold $k \in \{3, 4\}$ (additional to primary k=1,2,3 run). Compute variation in $\rho$ (SC-004).
- [ ] T027 [US3] Generate robustness report summarizing adjusted p-values and threshold stability in `data/processed/robustness_report.json`.

**Checkpoint**: All user stories should now be independently functional (Robustness Validated)

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T028 [P] Finalize `paper/draft.md` with generated results, ensuring all stats trace to `data/processed/` files (Principle IV)
- [ ] T029 Run full validation suite on CPU (N=50) to verify pipeline within 6-hour limit (Assumption: Compute feasibility)
- [ ] T030 Update `quickstart.md` with instructions for CPU validation vs GPU full analysis modes
- [ ] T031 [P] Add `state/projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2.yaml` with content hashes
- [ ] T032 Run quickstart.md validation to ensure reproducibility
- [ ] T033 [P] Implement resource monitoring in `code/src/utils.py`: Capture and log total runtime, RAM usage, and GPU memory usage for the full dataset run. Save to `data/processed/resource_metrics.json` (SC-005).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **Critical Data Flow**: `code/src/entropy.py` (T012) MUST complete and write `data/processed/entropy_results.csv` BEFORE `code/src/inference.py` (T013, T013b) or `analysis.py` (T015) can run.
  - **Critical Data Flow**: `convergence_results.csv` (T013) MUST exist before Router Simulation (T019) and Robustness (T025, T026).
  - **Sensitivity Flow**: T026 requires T013b (k=4 inference) to be completed.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Depends on US1 data generation (T012, T013 completion).
- **User Story 3 (P3)**: Depends on US1 data generation (T012, T013, T013b completion).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading (T004) before Entropy/Inference (T012, T013)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006, T005c) can run in parallel
- Once Foundational phase completes, US2 and US3 can start in parallel (both depend only on US1 data, not each other)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch data loading and model stubs in parallel:
Task: "Implement data processing pipeline in code/src/data_loader.py"
Task: "Create code/src/entropy.py stub"
Task: "Create code/src/inference.py stub"

# Once data is ready, run entropy and inference in parallel (if hardware allows):
Task: "Implement semantic entropy extraction in code/src/entropy.py"
Task: "Implement iterative refinement execution in code/src/inference.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Core Correlation)
4. **STOP and VALIDATE**: Test US1 independently on CPU (N=50)
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
   - Developer A: User Story 1 (Data generation & Correlation)
   - Developer B: User Story 2 (Router Simulation) - *Can start once T012/T013 are done*
   - Developer C: User Story 3 (Robustness) - *Can start once T012/T013/T013b are done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks must run on free CPU-only CI for validation (T002, T012, T013 with N=50, CodeLlama-1.3b). Full analysis (N=full, GPU) is a separate mode.
- **Critical Constraint**: Never fabricate data. Use real HumanEval/MBPP datasets via `datasets` library.
- **Critical Constraint**: Entropy extraction (T012) must not run convergence loops; strict separation of predictor (entropy) and target (convergence) is required by Principle VI.
- **Model Substitution**: CodeLlama models are used instead of LoopCoder-v2-2B due to availability. Success criteria are re-baselined accordingly.