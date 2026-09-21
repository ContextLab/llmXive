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
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (pinned `networkx`, `torch`, `scikit-learn`, `statsmodels`, `lifelines`, `numpy`, `pandas`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and SPEC ALIGNMENT that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The order of execution in this phase is strictly serial for the first block (Power Analysis -> Data Model -> Code).

### 2.1: Power Analysis & Spec Alignment (Strict Order)

**Note**: The `spec.md` is a read-only input artifact. The Plan (`plan.md`) is the active working document. Tasks T011-T015 update the Plan to reflect the corrected methodology (Tobit/Cox, N=110) and flag the Spec for future kickback. **Crucially, T011-T015 are DOCUMENTATION TASKS and DO NOT BLOCK code implementation tasks (T008, T009, T019).** Code tasks depend ONLY on T016 (Power Analysis) and T005b (Data Model).

- [X] T016 [P] **Power Analysis**: Implement `code/power_analysis.py` to run a formal power analysis. **Exact Implementation**: Use `statsmodels.stats.power.SolvePowerFTest2(effect_size=0.15, alpha=0.05, power=0.80, alternative='two-sided')` to calculate the required sample size. Output `data/power_analysis_output.json` containing the justified sample size (expected N=110). **Constraint**: This task MUST run before T019 and T025. **Failure Condition**: If this file is missing, downstream tasks (T019, T025) must fail immediately (or fallback to N=110 as per FR-001).
- [X] T011 [P] **Update Plan Methodology**: Modify `plan.md` to reflect the N=110 sample size derived from T016. **Action**: Read N from `data/power_analysis_output.json`. Replace all instances of "N=50" or "N=[deferred]" with "N=110" in the Summary and Compute Feasibility sections. **Dependency**: Must run after T016 and T005b. **Note**: This is a documentation task; it does NOT block T008/T009.
- [ ] T012 [P] **Update Plan Convergence**: Modify `plan.md` to explicitly define convergence as `≥ 0.90` accuracy or max-epoch censoring. **Action**: Replace any "deferred" thresholds with "0.90".
- [ ] T013 [P] **Update Plan Statistical Methods**: Modify `plan.md` to replace "ANCOVA/Pearson" with "**Tobit Regression**" and "**Cox Proportional Hazards**". **Action**: Add a "Spec Alignment Note" section in `plan.md` stating that `spec.md` FR-006/FR-007 are flagged for kickback. <!-- FAILED: unspecified -->
- [ ] T014 [P] **Update Plan Interaction Focus**: Modify `plan.md` to scope analysis to "Tobit/Cox interaction terms only" and remove "correlation coefficients".
- [ ] T015 [P] **Update Plan Success Criteria**: Modify `plan.md` to explicitly define the `is_significant` flag logic (Bonferroni-corrected min p-value < 0.05) in the Success Criteria section.

**Checkpoint**: Plan is now aligned with the corrected methodology. Power analysis justifies N=110. Convergence threshold is set to 0.90.

### 2.2: Data Model & Contracts

**Note**: Data Model MUST be drafted before Plan Update (T011) to ensure entity definitions are consistent.

- [X] T005a [P] **Define Entities**: Draft entity definitions for `SyntheticGraph`, `TrainingRun`, and `AnalysisResult` in `code/data_model_draft.md`. **Output**: Must produce `code/data_model_draft.md`. **Dependency**: Must run before T011.
- [ ] T005b [P] **Write Data Model**: Create `data-model.md` markdown document based on T005a, ensuring N=110 is reflected in examples. **Dependency**: Must run after T005a.
- [ ] T006a [P] **Generate Graph Schema**: Generate `contracts/graph.schema.yaml` from `data-model.md`.
- [ ] T007 [P] **Generate Training Run Schema**: Generate `contracts/training_run.schema.yaml` from `data-model.md`. **Output**: Must produce `contracts/training_run.schema.yaml`.

### 2.3: Core Code Infrastructure

**Dependency Note**: T005a, T005b, T006a, T007 must complete before T011 (Plan Update). **T011-T015 are parallel documentation tasks and DO NOT block T004, T008, T009.** T004, T008, T009 depend on T005b and T016. T016 must complete before T019 and T025.

- [ ] T004 [P] Implement `code/utils.py` with `seed_all()` (random, numpy, torch), `hash_artifact()`, and logging setup. **Constants**: Define `CONVERGENCE_THRESHOLD = 0.90` and `MAX_EPOCHS = 1000` as constants here. **Note**: These constants are derived from the updated plan (T012) and power analysis (T016). **Dependency**: Must run after T016 and T005b. **[P] Note**: This task is marked [P] but logically depends on T016 output.
- [ ] T008 [P] Implement `code/models.py` with a 2-layer GCN class (CPU-only, no CUDA dependencies). **Dependency**: T005b.
- [ ] T009 [P] Implement `code/losses.py` with Cross-Entropy and InfoNCE implementations (InfoNCE requires a linear probe for evaluation). **Dependency**: T005b.
- [ ] T010 [P] Create `code/main.py` orchestrator skeleton with argument parsing and pipeline state management. **Dependency**: T005b.

**Dependency Note**: T005a, T005b, T006a, T007a must complete before T011 (Plan Update). **T011-T015 are parallel documentation tasks and DO NOT block T008/T009.** T016 must complete before T019 and T025.

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

- [ ] T019 [US1] Implement `code/data_generation.py` to generate N graphs where N is read dynamically from `data/power_analysis_output.json`. **Constraint**: 10 graphs per $\beta$ level 0.0-1.0 step 0.1. Use seeds from power analysis output if available. **Fallback Logic**: If `data/power_analysis_output.json` is missing, default to N=110 (as per FR-001) and log a warning. **Failure Condition**: Do not proceed if N < 110 after fallback.
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

- [ ] T025 [US2] Implement `code/main.py` pipeline logic to iterate over all graphs (read N from `data/power_analysis_output.json`, fallback to N=110 if missing) and both loss types with sequential execution to manage memory. **Constraint**: Must fail if `data/power_analysis_output.json` is missing AND N < 110 after fallback.
- [ ] T026 [US2] Implement `code/train.py` with training loop for Cross-Entropy loss, recording full per-epoch loss/accuracy arrays.
- [ ] T027 [US2] Implement `code/train.py` with training loop for InfoNCE loss (encoder only), followed by frozen linear probe evaluation. **Convergence Steps**: Record the **total cumulative epochs** elapsed (encoder training epochs + linear probe epochs) as `steps_to_convergence`. Record full per-epoch loss/accuracy arrays for the linear probe phase.
- [ ] T028 [US2] Implement convergence logic: record `steps_to_convergence` when accuracy meets `CONVERGENCE_THRESHOLD = 0.90` (using constant from T004), or flag as censored at `MAX_EPOCHS` (1000, using constant from T004). **Constraint**: Do NOT use loss plateau for early stopping; convergence is strictly accuracy-based. Store the full per-epoch trajectory arrays in memory for output.
- [ ] T029 [US2] Define the `training_run` JSON schema in `contracts/` to ensure log consistency. **Note**: This task is covered by T007 in Phase 2.2.
- [ ] T030 [US2] Save per-run results to `data/logs/training_run_{id}_{loss_type}.json`. **Requirement**: The JSON must include a `trajectory` field containing the full list of per-epoch `{loss, accuracy}` objects, not just the final step count. Use `MAX_EPOCHS` (1000) as the censoring limit.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Interaction Analysis and Reporting (Priority: P3)

**Goal**: Perform Tobit Regression and Cox Proportional Hazards analysis to test interaction between $\beta$ and loss type on convergence steps. Apply multiple-comparison correction.

**Independent Test**: Run `code/analyze.py` on mock censored data and verify Tobit/Cox coefficients and interaction p-values are correctly computed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for Tobit regression implementation in `tests/unit/test_analysis.py`
- [ ] T032 [P] [US3] Unit test for Cox PH implementation and interaction term extraction in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analyze.py` to aggregate `data/logs/` into a single DataFrame using the schema defined in T007.
- [ ] T034 [US3] Implement Tobit Regression (`steps ~ loss_type * beta`) handling censored data (FR-005 correction).
- [ ] T035 [US3] Implement Cox Proportional Hazards survival analysis for convergence "time".
- [ ] T036 [US3] Extract interaction term F-statistic/p-value (Tobit) and Hazard Ratio/p-value (Cox).
- [ ] T037 [US3] Implement Bonferroni correction on the interaction p-values from Tobit and Cox models. **Logic**: Use `statsmodels.stats.multitest.multipletests` with `method='bonferroni'`. Calculate `num_tests` dynamically from the list of interaction p-values being corrected (e.g., 2 for Tobit and Cox). **Output**: Update `data/analysis_results.json` to include the `is_significant` field calculated as `True` if the minimum corrected p-value < 0.05, else `False`.
- [ ] T038 [US3] Generate `data/analysis_results.json` with corrected p-values, coefficients, and a boolean `is_significant` flag (SC-003).
- [ ] T039 [US3] Generate final report in `data/report.md` summarizing whether contrastive loss converges faster as $\beta$ increases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T041 Code cleanup and refactoring
- [ ] T043 [P] Profile memory usage of `code/train.py` to ensure < 7GB limit.
- [ ] T044 [P] **Runtime Validation**: Run the full pipeline on the CI runner and **assert total duration < 21600s (6 hours)**. If this fails, the build fails.
- [ ] T045 [P] Additional unit tests in `tests/unit/`
- [ ] T046 Run quickstart.md validation

**Note**: Task T042 (Early Stopping) has been removed as it conflicts with the FR-005 convergence definition.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T016 (Power Analysis) -> T005b (Data Model) -> T004 (Utils) -> T008/T009 (Code).
 - **Parallel Documentation**: T011-T015 (Plan Updates) run in parallel with T004-T010 and DO NOT block them. T011-T015 depend on T016 and T005b.
 - **Strict Serial**: T016 must complete before T019. T005b must complete before T008/T009.
- **User Stories (Phase 3+)**: All depend on Foundational completion.
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
- T016, T005a, T005b, T006a, T007 are strictly serial.
- T004, T008, T009, T010 can run in parallel **after** T005b and T016 complete.
- T011-T015 can run in parallel with T004-T010 (once T016 and T005b complete).
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
Task: "Implement code/data_generation.py to generate N graphs (read from power analysis)"
Task: "Implement community label derivation from initial ring lattice in code/data_generation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Strict Order**: Power Analysis (T016) -> Data Model (T005b) -> Code (T004, T008, T009).
 - **Parallel**: Plan Updates (T011-T015) run in parallel with Code tasks.
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
 - Developer D: Plan Updates (T011-T015) - Parallel with Code
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
- **Constraint**: N is read dynamically from `data/power_analysis_output.json` (default 110 if missing).
- **Constraint**: Convergence threshold is set to 0.90. Max epochs is 1000. No loss-plateau early stopping.
- **Constraint**: Power analysis (T016) MUST run before any sample size is used (with fallback to 110).
- **Constraint**: Full per-epoch trajectory arrays must be stored in `data/logs/` JSON files.