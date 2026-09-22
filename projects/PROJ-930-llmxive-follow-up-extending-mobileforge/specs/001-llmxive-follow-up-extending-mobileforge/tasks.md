# Tasks: llmXive Follow-up: Extending MobileForge with CPU-Tractable Logic Distillation

**Input**: Design documents from `/specs/002-mobileforge-logic-distillation/`
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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{data/raw,data/processed,data/evaluation,models,utils,tests/unit,tests/integration}` and `touch projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{requirements.txt,README.md}`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinned `torch`, `transformers`, `datasets`, `pandas`, `scikit-learn`, `pytest`, `statsmodels`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `state/` directory for artifact checksums and versioning (Constitution Principle III)
- [ ] T005 [P] Implement `utils/emulator.py`: Headless Android emulator wrapper with 3x retry logic for environment crashes
- [ ] T006 [P] Setup `utils/metrics.py` base classes for "Success Rate" and "Step Efficiency" calculation
- [ ] T007 [P] Create base data entities and schema definitions in `code/data/schema.py` for `ExtractionDataset`, `DistilledModel`, and `EvaluationResult`
- [ ] T008 Configure environment variable management for dataset paths and random seeds (Constitution Principle I)
- [ ] T009 [P] Implement `utils/power_analysis.py` script structure (scaffolding only) for later post-hoc analysis (Constitution Principle IV)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Dataset Construction (Priority: P1) 🎯 MVP

**Goal**: Extract and filter `(UI_state, Corrective_Hint, Action)` triples from MobileForge logs, ensuring "failed-then-success" trajectories and purely linguistic hints.

**Independent Test**: Running `code/utils/extraction.py` against raw logs produces a CSV/JSON with sufficient valid triples (target cited in spec), no nulls in key fields, and zero coordinate-based hints.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for "failed-then-success" filter logic in `code/tests/unit/test_extraction.py`
- [ ] T011 [P] [US1] Unit test for "coordinate-free" hint validation regex in `code/tests/unit/test_extraction.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/utils/extraction.py`: Log parser to extract `(UI_state, Corrective_Hint, Action)` triples
- [ ] T013 [US1] Implement `code/utils/extraction.py`: Filter logic for "initial failure, post-hint success" trajectories
- [ ] T014 [US1] Implement `code/utils/extraction.py`: Hint purity checker to exclude coordinate-based visual grounding (e.g., `[x,y]`)
- [ ] T015 [US1] Create `code/data/raw/` structure and implement `code/data/raw/download_mobileforge.py` to fetch real data from verified HuggingFace source (e.g., `datasets.load_dataset("mobileforge")` or specific verified URL)
- [ ] T016 [US1] Generate `ExtractionDataset` (CSV/Parquet) in `code/data/processed/` with sufficient valid triples (target [deferred] per spec assumption), citing the assumption in spec.md
- [ ] T017 [US1] Implement checksum generation for `ExtractionDataset` in `state/` (Constitution Principle III)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Tractable Model Training (Priority: P2)

**Goal**: Train a lightweight encoder-only model (≤100M params) on CPU to predict action sequences from UI states and hints.

**Independent Test**: Training job on `ubuntu-22.04` runner completes in ≤6 hours, final loss ≤0.5, with no GPU/CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model initialization ensuring CPU-only device mapping in `code/tests/unit/test_train.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/models/train.py`: Initialize DistilBERT-small (or similar ≤100M param) with CPU-only device setting
- [ ] T020 [US2] Implement `code/models/train.py`: Training loop with loss monitoring and convergence check (target final loss ≤0.5)
- [ ] T021 [US2] Implement `code/models/train.py`: Data loading with streaming/chunking to fit ≤7GB RAM constraint
- [ ] T022 [US2] Add explicit assertion/error check to fail loudly if CUDA device is detected (Constitution Principle VI)
- [ ] T023 [US2] Save `DistilledModel` weights and config to `code/models/` upon completion
- [ ] T024 [US2] Log training duration and resource usage to verify ≤6h CPU constraint

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate the distilled model against a TinyLlama baseline on a representative set of unseen AndroidWorld tasks, performing statistical significance testing with a paired design.

**Independent Test**: Evaluation script produces success rate, step efficiency, and a p-value < 0.05 from a paired t-test with power ≥ 0.8.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Integration test for emulator interaction with task execution in `code/tests/integration/test_eval.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/data/evaluation/`: Load 500 unseen, logically disjoint AndroidWorld tasks (streaming if large) from `androidworld` dataset (DOI:10.48550/arXiv.2405.14793) using `datasets.load_dataset("androidworld")`, ensuring task IDs are tracked for pairing
- [ ] T027 [US3] Implement `code/models/eval.py`: Execution loop for `DistilledModel` on the tracked tasks via headless emulator
- [ ] T028 [US3] Implement `code/models/eval.py`: Execution loop for TinyLlama baseline on the **exact same** tracked tasks (same task IDs) to enable pairing
- [ ] T029 [US3] Implement `code/models/eval.py`: "Generic retry" prompt baseline run on the **same** set of tasks for ablation study (Constitution Principle VII), distinct from primary TinyLlama comparison
- [ ] T030 [US3] Implement `code/utils/metrics.py`: Calculate "Success Rate" and "Step Efficiency" for both models, outputting paired results (task_id -> [distilled_score, baseline_score])
- [ ] T031 [US3] Implement `code/utils/metrics.py`: Perform **paired t-test** (or Wilcoxon signed-rank if non-normal) comparing Distilled vs. TinyLlama baseline on the paired results (same task IDs) to satisfy FR-005
- [ ] T032 [US3] Implement `code/utils/power_analysis.py`: Conduct **post-hoc power analysis** using the observed effect size from T030/T031 to confirm N=500 yields ≥0.8 power (FR-007)
- [ ] T033 [US3] Generate `EvaluationResult` report with metrics, p-values, and power analysis in `data/results/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis (Priority: P3)

**Goal**: Verify robustness of results against "inconsistency tolerance" threshold variations.

**Independent Test**: Sweeping threshold across {0.01, 0.05, 0.1} results in success rate variance ≤ 5%.

### Implementation for User Story 4

- [ ] T034 [P] [US4] Implement `code/models/eval.py`: Sensitivity sweep logic for "inconsistency tolerance" thresholds across a range of low-to-moderate values.
- [ ] T035 [US4] Implement `code/utils/metrics.py`: Variance calculation for success rates across swept thresholds
- [ ] T036 [US4] Generate `SensitivityReport` in `data/results/` confirming variance ≤ 5% (SC-005)
- [ ] T037 [US4] Generate `AblationReport` comparing "hint" input vs. "generic retry" baseline performance (using results from T029)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `README.md` and `docs/`
- [ ] T039 Code cleanup and refactoring of `code/utils/`
- [ ] T040 Performance optimization for data streaming and model inference
- [ ] T041 [P] Additional unit tests for edge cases (empty logs, emulator crashes) in `code/tests/unit/`
- [ ] T042 Run `quickstart.md` validation and update if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US1 (P1)**: Must complete before US2 (Training needs dataset) and US3 (Evaluation needs model)
  - **US2 (P2)**: Must complete before US3 and US4 (Evaluation needs model)
  - **US3 (P3)**: Can run in parallel with US4 once US2 is complete
  - **US4 (P3)**: Can run in parallel with US3 once US2 is complete
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (Dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (Tasks) and US2 (Model)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (Model) and US3 (Metrics logic)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
  - **US1** must run first (blocks US2)
  - Once **US1** completes, **US2** can start
  - Once **US2** completes, **US3** and **US4** can run in parallel
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for 'failed-then-success' filter logic in code/tests/unit/test_extraction.py"
Task: "Unit test for 'coordinate-free' hint validation regex in code/tests/unit/test_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement code/utils/extraction.py: Log parser to extract triples"
Task: "Create code/data/raw/ structure and implement download script"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Extraction)
4. **STOP and VALIDATE**: Verify sufficient valid triples extracted with no coordinate hints.
5. Deploy/demo data pipeline if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate dataset quality
3. Add User Story 2 → Train model on CPU → Verify convergence
4. Add User Story 3 → Evaluate on unseen tasks → Validate statistical significance (paired t-test)
5. Add User Story 4 → Run sensitivity analysis → Validate robustness
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Extraction) - **Must finish first**
   - Developer B: User Story 2 (Model Training) - **Can start as soon as US1 data is ready**
3. Once US1 and US2 are complete:
   - Developer C: User Story 3 (Evaluation)
   - Developer D: User Story 4 (Sensitivity)
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
- **Critical Data Constraint**: All data loaders MUST fail loudly on missing real data; no synthetic fallbacks allowed.
- **Critical Compute Constraint**: All training must be explicitly CPU-only; any CUDA usage must trigger an immediate failure.