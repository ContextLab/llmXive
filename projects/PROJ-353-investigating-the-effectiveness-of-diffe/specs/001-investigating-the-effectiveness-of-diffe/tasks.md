# Tasks: Investigating Loss Functions on Small-World Graphs

**Input**: Design documents from `/specs/001-investigating-loss-functions-small-world/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per plan.md)
- **Data**: `data/raw/`, `data/logs/`, `data/analysis/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/` directories)
- [ ] T002 Initialize Python 3.10 project with `requirements.txt` (pinned `networkx`, `torch`, `scikit-learn`, `statsmodels`, `lifelines`, `numpy`, `pandas`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and SPEC ALIGNMENT that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The order of execution in this phase is strictly serial for the first block (Power Analysis -> Spec Update -> Data Model).

### 2.1: Power Analysis & Spec Alignment (Strict Order)

- [X] T016 [P] **Power Analysis**: Implement `code/power_analysis.py` to run a formal power analysis for detecting a moderate interaction effect ($f^2=0.15$) with power $\ge 0.80$. Output `data/power_analysis_output.json` containing the justified sample size (expected N=110).
- [ ] T011 [P] **Update Spec FR-001 & US-1**: Modify `spec.md` FR-001 and US-1 Acceptance Scenario 1. **Action**: Replace all instances of "50" with "110" (10 per $\beta$ level) in the text.
- [ ] T012 [P] **Update Spec FR-005 & US-2**: Modify `spec.md` FR-005 and US-2 Acceptance Scenario 1. **Action**: Replace all instances of `≥ [deferred]` with `≥ 0.90` in the text.
- [ ] T013 [P] **Update Spec FR-006 & FR-007**: Modify `spec.md` FR-006 and FR-007. **Action**: Replace "Pearson correlation" and "ANCOVA" with "**Tobit Regression**" and "**Cox Proportional Hazards**".
- [ ] T014 [P] **Update Spec FR-008**: Modify `spec.md` FR-008. **Action**: Remove "correlation coefficients" requirement; scope to "Tobit/Cox interaction terms only".
- [ ] T015 [P] **Update Spec SC-003**: Modify `spec.md` SC-003. **Action**: Explicitly define the "flagging" mechanism as a boolean field (`is_significant`) in the `data/analysis_results.json` output.

**Checkpoint**: Spec is now aligned with Plan. Power analysis justifies N=110. Convergence threshold is set to a high value.

### 2.2: Data Model & Contracts

- [ ] T005a [P] **Define Entities**: Draft entity definitions for `SyntheticGraph`, `TrainingRun`, and `AnalysisResult` in `code/data_model_draft.md`.
- [ ] T005b [P] **Write Data Model**: Create `data-model.md` markdown document based on T005a, ensuring N=110 is reflected in examples.
- [ ] T006a [P] **Generate Graph Schema**: Generate `contracts/graph.schema.yaml` from `data-model.md`.
- [ ] T007a [P] **Generate Training Run Schema**: Generate `contracts/training_run.schema.yaml` from `data-model.md`.

### 2.3: Core Code Infrastructure

- [ ] T004 [P] Implement `code/utils.py` with `seed_all()` (random, numpy, torch), `hash_artifact()`, and logging setup. **Note**: Define `CONVERGENCE_THRESHOLD = 0.90 ` as a constant here, derived from the updated spec.
- [ ] T008 [P] Implement `code/models.py` with a 2-layer GCN class (CPU-only, no CUDA dependencies).
- [ ] T009 [P] Implement `code/losses.py` with Cross-Entropy and InfoNCE (temperature $\tau=0.5$, fixed negatives) implementations.
- [ ] T010 [P] Create `code/main.py` orchestrator skeleton with argument parsing and pipeline state management.

**Dependency Note**: T005a, T005b, T006a, T007a must complete before T008 and T009. T016, T011, T012, T013, T014, T015 must complete before T005a.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Graph Generation and Topology Annotation (Priority: P1) 🎯 MVP

**Goal**: Generate a set of Watts-Strogatz graphs with varying $\beta$ (0.0 to 1.0, 10 per level), annotate nodes with community labels from the initial lattice, and validate clustering coefficients.

**Independent Test**: Run `code/data_generation.py` and verify `data/raw/graphs.jsonl` contains 110 entries with correct $\beta$ distribution, measured clustering coefficients within theoretical bounds, and balanced class labels (<80% max).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US1] Unit test for Watts-Strogatz generation logic in `tests/unit/test_generation.py`
- [ ] T018 [P] [US1] Unit test for label annotation and class balance check in `tests/unit/test_generation.py`

### Implementation for User Story 1

- [ ] T019 [US1] Implement `code/data_generation.py` to generate 110 graphs (N=100, 10 per $\beta$ level 0.0-1.0 step 0.1). **Constraint**: Use seeds from `data/power_analysis_output.json` if available, else default.
- [ ] T020 [US1] Implement community label derivation from initial ring lattice (before rewiring) in `code/data_generation.py`.
- [ ] T021 [US1] Add validation logic: detect disconnected components (regenerate/skip) and enforce class balance (<80% max) in `code/data_generation.py`.
- [ ] T022 [US1] Save generated graphs to `data/raw/graphs.jsonl` with metadata (`id`, `beta`, `seed`, `clustering_coeff`, `edge_list`, `labels`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Loss Training and Convergence Tracking (Priority: P2)

**Goal**: Train 2-layer GCN on each graph using Cross-Entropy and InfoNCE. Track per-epoch loss/accuracy, record steps to convergence (high accuracy), and handle censored data (max epochs).

**Independent Test**: Run training on a single graph, verify two models saved, trajectory logs generated, and convergence steps recorded (or censored).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for Cross-Entropy training loop in `tests/unit/test_losses.py`
- [ ] T024 [P] [US2] Unit test for InfoNCE + Linear Probe accuracy calculation in `tests/unit/test_losses.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `code/main.py` pipeline logic to iterate over all graphs and both loss types (total runs proportional to the graph and loss configuration) with sequential execution to manage memory.
- [ ] T026 [US2] Implement `code/train.py` with training loop for Cross-Entropy loss, recording full trajectory and steps to convergence.
- [ ] T027 [US2] Implement `code/train.py` with training loop for InfoNCE loss (encoder only), followed by frozen linear probe evaluation.
- [ ] T028 [US2] Implement convergence logic: record step count when accuracy meets the **`CONVERGENCE_THRESHOLD = 0.90 `** (using the constant defined in T004), or flag as censored at a predetermined maximum epoch limit.
- [ ] T029 [US2] Define the `training_run` JSON schema in `contracts/` to ensure log consistency.
- [ ] T030 [US2] Save per-run results to `data/logs/training_run_{id}_{loss_type}.json` (including trajectory, final metrics, censoring flag).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Interaction Analysis and Reporting (Priority: P3)

**Goal**: Perform Tobit Regression and Cox Proportional Hazards analysis to test interaction between $\beta$ and loss type on convergence steps. Apply multiple-comparison correction.

**Independent Test**: Run `code/analyze.py` on mock censored data and verify Tobit/Cox coefficients and interaction p-values are correctly computed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for Tobit regression implementation in `tests/unit/test_analysis.py`
- [ ] T032 [P] [US3] Unit test for Cox PH implementation and interaction term extraction in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analyze.py` to aggregate `data/logs/` into a single DataFrame using the schema defined in T029.
- [ ] T034 [US3] Implement Tobit Regression (`steps ~ loss_type * beta`) handling censored data (FR-005 correction).
- [ ] T035 [US3] Implement Cox Proportional Hazards survival analysis for convergence "time".
- [ ] T036 [US3] Extract interaction term F-statistic/p-value (Tobit) and Hazard Ratio/p-value (Cox).
- [ ] T037 [US3] Apply Bonferroni (Wikidata Q87892954, https://www.wikidata.org/wiki/Q87892954) correction to interaction p-values (FR-008 updated).
- [ ] T038 [US3] Generate `data/analysis_results.json` with corrected p-values, coefficients, and a boolean `is_significant` flag (p < 0.05) (SC-003).
- [ ] T039 [US3] Generate final report in `data/report.md` summarizing whether contrastive loss converges faster as $\beta$ increases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T041 Code cleanup and refactoring
- [ ] T042 [P] **Implement Early Stopping**: Implement early stopping logic in `code/train.py` with **patience=10 epochs ** on loss plateau to optimize runtime and ensure SC-004 compliance.
- [ ] T043 [P] Profile memory usage of `code/train.py` to ensure < 7GB limit.
- [ ] T044 [P] **Runtime Validation**: Run the full pipeline on the CI runner and **assert total duration < 21600s (6 hours)**. If this fails, the build fails.
- [ ] T045 [P] Additional unit tests in `tests/unit/`
- [ ] T046 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T016 (Power Analysis) -> T011-T015 (Spec Updates) -> T005a-T007a (Data Model) -> T004, T008, T009 (Code).
 - **Strict Serial**: T016 must complete before T011. T011-T015 must complete before T005a.
- **Spec Alignment (Phase 3)**: (Merged into Phase 2)
- **User Stories (Phase 4+)**: All depend on Foundational completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational completion - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational completion - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational completion - Depends on US2 training results

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T016, T011-T015, T005a-T007a are strictly serial.
- T004, T008, T009, T010 can run in parallel **after** T005a-T007a complete.
- Once Foundational phase complete, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Watts-Strogatz generation logic in tests/unit/test_generation.py"
Task: "Unit test for label annotation and class balance check in tests/unit/test_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_generation.py to generate 110 graphs "
Task: "Implement community label derivation from initial ring lattice in code/data_generation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Strict Order**: Power Analysis (T016) -> Spec Updates (T011-T015) -> Data Model (T005-T007) -> Code (T004, T008, T009).
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

1. Team completes Setup + Foundational (strictly ordered) together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except where noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All training must run on CPU only (no CUDA, no bitsandbytes).
- **Constraint**: N=110 graphs, 220 training runs total, must complete in < 6 hours.
- **Constraint**: Convergence threshold is fixed at 0.90.
- **Constraint**: Power analysis (T016) MUST run before any sample size is used.