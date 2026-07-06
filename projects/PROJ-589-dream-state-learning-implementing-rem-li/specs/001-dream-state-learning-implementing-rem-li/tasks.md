# Tasks: Dream-State Learning: Implementing REM-like Consolidation in Language Models

**Input**: Design documents from `/specs/001-dream-state-learning-implementing-rem-li/`
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

- [ ] T001 Create project structure per implementation plan: create directories `code/`, `tests/`, `data/`, `data/raw/`, `data/checkpoints/`, `data/results/`, `data/logs/`, `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T002 Initialize a Python project compatible with modern runtime environments. with `code/requirements.txt` (torch, transformers, datasets, scikit-learn, accelerate, pytest, scipy) using exact version pins (e.g., `torch==2.0.0`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` for hyperparameters, paths, seed management, and CPU-only device enforcement
- [ ] T005 [P] Implement `code/utils/memory_monitor.py` to track peak RSS via `/proc/self/status` and enforce hard abort (FR-005)
- [X] T005b [P] Implement `code/utils/exceptions.py` defining the custom exception class `DataIntegrityError` for data checksum failures
- [ ] T006 [P] Implement `code/data/loader.py` to download GLUE/SuperGLUE subsets via `datasets` library with SHA-256 checksum verification; MUST abort execution and raise `DataIntegrityError` if checksum mismatch occurs
- [ ] T007 Create `code/models/__init__.py` and initialize DistilBERT/TinyLlama model loader (CPU-optimized, default precision)
- [~] T008 Implement `code/utils/logger.py` for structured logging to `data/logs/` and stdout
- [~] T009 Setup `tests/contract/` schema validation for `training_config.schema.yaml` and `evaluation_result.schema.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Wake/Dream Training Cycle (Priority: P1) 🎯 MVP

**Goal**: Implement the alternating wake/dream training loop with DAE-based consolidation, warm-up, and entropy checks.

**Independent Test**: Run a training job on a single GLUE subset, verify alternating phases, entropy checks, and checkpoint output.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Unit test for warm-up logic (no dream phase in the initial steps) in `tests/unit/test_trainer.py`
- [~] T011 [P] [US1] Unit test for entropy calculation and low-entropy retry logic in `tests/unit/test_trainer.py`
- [~] T012 [P] [US1] Integration test for a multi-step wake/dream cycle on a tiny dataset in `tests/integration/test_training_loop.py`

### Implementation for User Story 1

- [~] T013 [US1] Implement `code/data/augment.py` for DAE masking logic (random token masking consistent with BERT, A moderate mask rate)
- [~] T014 [US1] Implement `code/models/trainer.py` core loop: Wake phase (standard CE on real data)
- [~] T015 [US1] Implement `code/models/trainer.py` Dream phase: Generate masked inputs, reconstruct original tokens (DAE loss), enforce 4: ratio via a `DreamScheduler` class (step counter modulo check)
- [~] T016 [US1] Implement `code/models/trainer.py` Warm-up protocol: Skip dream phase for first steps; raise `RuntimeError` if dream phase is triggered before an initial stabilization period.
- [~] T017 [US1] Implement `code/models/trainer.py` Entropy check: Detect low-entropy outputs (<0.5 bits, calculated as sum(-p*log2(p))), trigger retry up to 3 times with local retry counter increment (not global seed) or discard batch
- [~] T018 [US1] Integrate `memory_monitor` (T005) into the training loop to abort and save checkpoint on OOM
- [~] T019 [US1] Add logging for phase transitions (Wake/Dream), entropy metrics, and warm-up status

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Evaluation Baseline (Priority: P2)

**Goal**: Run a parallel continuous-training baseline and perform statistical comparison.

**Independent Test**: Run baseline script on same seed/data, compare final loss/accuracy, output statistical p-value.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T020 [P] [US2] Unit test for statistical significance calculation (Wilcoxon signed-rank test) in `tests/unit/test_metrics.py`
- [~] T021 [P] [US2] Integration test comparing two dummy models in `tests/integration/test_evaluation.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/eval/metrics.py` for few-shot accuracy calculation on held-out GLUE subsets
- [ ] T023 [US2] Implement `code/models/trainer.py` Baseline mode: Continuous SFT with identical total token count (not just steps) and data tokens as the experimental run
- [ ] T024 [US2] Implement `code/main.py` logic to orchestrate parallel runs (Experimental vs. Baseline) with same seeds (depends on T014-T017 and T023)
- [ ] T025 [US2] Implement statistical analysis: Compute accuracy difference and Wilcoxon signed-rank test (α=0.05) p-value across 5 seeds (per Plan Constitution Principle VII); input data structure is list of 5 accuracy floats per model; use `scipy.stats.wilcoxon`
- [ ] T026 [US2] Implement result reporting: Save comparative report to `data/results/comparison_report.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Constraint Verification (Priority: P3)

**Goal**: Ensure the pipeline runs within GitHub Actions free-tier limits (limited CPU, 7GB RAM, 6h).

**Independent Test**: Run full pipeline on local resource-limited environment, verify no OOM and time < 5h.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for memory limit logic in `tests/unit/test_memory_monitor.py`
- [ ] T030 [P] [US3] Integration test for time limit enforcement in `tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/main.py` time monitoring and abort logic if wall-clock > 5 hours (read `MAX_WALL_CLOCK_HOURS` from `config.py`, raise `TimeLimitExceeded`)
- [ ] T032 [US3] Implement `code/main.py` memory monitoring integration with `memory_monitor` (T005) to enforce GB limit
- [ ] T033 [US3] Create `code/scripts/verify_feasibility.sh` to run a dry-run with resource limits

The research question remains: [Research Question]
The method remains: [Method]
References: [References]

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Sensitivity Analysis (Priority: P4)

**Goal**: Sweep temperature hyperparameters as mandated by FR-006 and report variance.

**Independent Test**: Run temperature sweep across a range of values {, 0.7, 0.9}, following a grid search protocol, report variance in final accuracy.

### Implementation for User Story 1 (Sensitivity Extension)

- [ ] T036 [US1] Implement temperature sweep logic in `code/main.py` for dream phase: execute a grid search running the full training pipeline for each temperature value in a set of representative hyperparameters, collect final accuracy for each run, and compute variance using `scikit-learn`'s `var` function
- [ ] T037 [US1] Implement reporting for variance in final accuracy across temperature sweep

**Checkpoint**: Sensitivity analysis complete

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T051 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T052 Code cleanup and refactoring
- [ ] T053 Performance optimization (batching, data loading) across all stories
- [ ] T054 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T055 Security hardening
- [ ] T056 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Sensitivity Analysis (Phase 6)**: Depends on US1 and US2 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for model state and training logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for full pipeline execution
- **Sensitivity Analysis (Phase 6)**: Depends on US1 and US2 completion

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
Task: "Unit test for warm-up logic in tests/unit/test_trainer.py"
Task: "Unit test for entropy calculation in tests/unit/test_trainer.py"

# Launch all implementation for User Story 1 together (after tests):
Task: "Implement code/data/augment.py for DAE masking"
Task: "Implement code/models/trainer.py core loop (Wake/Dream)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (100-step run, entropy check, warm-up)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Baseline comparison)
4. Add User Story 3 → Test independently → Deploy/Demo (Resource verification)
5. Add Phase 6 (Sensitivity Analysis) → Test independently → Deploy/Demo (Hyperparameter robustness)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Loop)
 - Developer B: User Story 2 (Evaluation & Baseline)
 - Developer C: User Story 3 (Resource Limits & Feasibility)
 - Developer D: Phase 6 (Sensitivity Analysis)
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
- **Critical Constraint**: All tasks MUST run on CPU-only CI with a minimal core count and limited RAM.. No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: All data must be real (GLUE/SuperGLUE) via `datasets` library. No fake data generation.
- **Statistical Method**: Primary success criterion uses Wilcoxon signed-rank test (Plan Constitution Principle VII) due to unequal variance; t-test is not used.
- **Warm-up**: Hard constraint enforced by RuntimeError if dream phase triggers before step 10.
- **Sensitivity**: Protocol defined as grid search over {0.5, 0.7, 0.9} with full training runs per temp.