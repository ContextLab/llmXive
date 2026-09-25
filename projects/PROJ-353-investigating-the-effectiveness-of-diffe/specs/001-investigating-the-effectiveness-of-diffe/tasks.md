# Tasks: Investigating Loss Functions on Small-World Graphs

**Input**: Design documents from `/specs/001-investigating-loss-functions-small-world/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Must run in strict sequence (dependencies on previous tasks in the group)
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

## Phase 0: Research & Setup (Shared Infrastructure)

**Purpose**: Project initialization, documentation, and basic structure

- [ ] T040a [S] **Create Research Documentation**: Create `research.md` in the project root. **Action**: `research.md` must contain the initial research questions and methodology summary. **Constraint**: This is a Phase 0 deliverable as per `plan.md` Project Structure.
- [ ] T001 [P] Create project structure per implementation plan (`code/`, `tests/`, `data/` directories)
- [ ] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pinned `networkx`, `torch`, `scikit-learn`, `statsmodels`, `lifelines`, `numpy`, `pandas`)
- [ ] T040b [P] **Create Quickstart Documentation**: Create `quickstart.md` in the project root. **Action**: `quickstart.md` must contain instructions to run the full pipeline. **Constraint**: This is a Phase 1 deliverable as per `plan.md`.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and SPEC ALIGNMENT that MUST be complete before ANY user story can be implemented.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The order of execution in this phase is strictly serial for the first block (Verification -> Data Model -> Code).

### 1.1: Plan & Spec Alignment (Strict Serial Order)

**Note**: The `spec.md` is the read-only source of truth. The `plan.md` is the active working document. This phase verifies that the Plan already reflects the Spec. No modification tasks are required if the Plan is correct.

- [ ] T011 [S] **Create Validation Script**: Create `scripts/validate_plan.py`. **Action**: The script must assert that `plan.md` contains "N=110", "Tobit Regression", "Cox Proportional Hazards", and "0.90". If values are missing, the script must log a warning to stdout but MUST NOT fail the build. **Constraint**: Do NOT modify `plan.md` or `spec.md`. **Dependency**: None.
- [ ] T004 [S] **Implement `code/utils.py`**: Implement `seed_all()`, `hash_artifact(path: str)`, and constants `CONVERGENCE_THRESHOLD = 0.90`, `MAX_EPOCHS = 1000`, `SAMPLE_SIZE = 110`. **Verification**: Include a unit test `tests/unit/test_utils.py::test_sample_size_is_110` that asserts `utils.SAMPLE_SIZE == 110`. **Dependency**: T011, T005b.

### 1.2: Data Model & Contracts

**Note**: Data Model MUST be drafted before Code. T005a1 creates the file referenced by the Spec as a Phase 1 deliverable.

- [ ] T005a1 [S] **Draft SyntheticGraph Entity**: Create `code/data_model_draft.md`. **Format**: Markdown table with columns: `Entity`, `Attribute`, `Type`, `Description`. Populate with fields from FR-001 (Graph ID, Beta, Clustering Coeff, Node Count). **Dependency**: None.
- [ ] T005a2 [S] **Draft TrainingRun Entity**: Append definition for `TrainingRun` to `code/data_model_draft.md`. **Format**: Same Markdown table. Include fields from FR-005 (Convergence Steps, Censorship Flag, Trajectory). **Dependency**: T005a1.
- [ ] T005a3 [S] **Draft AnalysisResult Entity**: Append definition for `AnalysisResult` to `code/data_model_draft.md`. **Format**: Same Markdown table. Include fields from SC-003 (Tobit p-value, Cox p-value, is_significant). **Dependency**: T005a2.
- [ ] T005b [S] **Write Data Model**: Create `data-model.md` markdown document based on T005a1-T005a3. **Format**: Standard Markdown schema with JSON Schema Draft 7 examples. **Note**: This file is the Phase 1 deliverable referenced by `spec.md`. **Dependency**: T005a1, T005a2, T005a3.
- [ ] T006a [P] **Generate Graph Schema**: Generate `contracts/graph.schema.yaml` from `data-model.md`. **Format**: JSON Schema Draft 7 embedded in YAML. **Dependency**: T005b.
- [ ] T007 [P] **Generate Training Run Schema & Validate**: Generate `contracts/training_run.schema.yaml` from `data-model.md`. **Validation**: Ensure the schema includes the `trajectory` field (list of per-epoch `{loss, accuracy}` objects) as required by Constitution Principle VI and US-2. **Dependency**: T005b.

### 1.3: Core Code Infrastructure

- [ ] T008 [P] Implement `code/models.py` with a 2-layer GCN class (CPU-only). **Dependency**: T005b.
- [ ] T009 [P] Implement `code/losses.py` with Cross-Entropy and InfoNCE implementations. **Dependency**: T005b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Synthetic Graph Generation and Topology Annotation (Priority: P1) 🎯 MVP

**Goal**: Generate a set of Watts-Strogatz graphs with varying $\beta$ (0.0 to 1.0, 10 per level), annotate nodes with community labels from the initial lattice, and validate clustering coefficients.

**Independent Test**: Run `code/data_generation.py` and verify `data/raw/graphs.jsonl` contains a sufficient number of entries with correct $\beta$ distribution, measured clustering coefficients within theoretical bounds, and balanced class labels (<80% max).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T017 [P] [US1] Unit test for Watts-Strogatz generation logic in `tests/unit/test_generation.py`
- [ ] T018 [P] [US1] Unit test for label annotation and class balance check in `tests/unit/test_generation.py`

### Implementation for User Story 1

- [ ] T019 [US1] Implement `code/data_generation.py` to generate N=110 graphs (hardcoded from T004) with $\beta$ levels 0.0 to 1.0 (10 per level). **Constraint**: Use seeds from `code/utils.py` (pinned). **Fallback**: If N != 110, raise error (Spec constraint). **Dependency**: T004.
- [ ] T020 [US1] Implement community label derivation from initial ring lattice (before rewiring) in `code/data_generation.py`.
- [ ] T021 [US1] Add validation logic: detect disconnected components (regenerate/skip) and enforce class balance (<80% max) in `code/data_generation.py`.
- [ ] T022 [US1] Save generated graphs to `data/raw/graphs.jsonl` with metadata (`id`, `beta`, `seed`, `clustering_coeff`, `edge_list`, `labels`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Dual-Loss Training and Convergence Tracking (Priority: P2)

**Goal**: Train a multi-layer GCN on each graph using Cross-Entropy and InfoNCE. Track per-epoch loss/accuracy, record steps to convergence (high accuracy), and handle censored data (max epochs).

**Independent Test**: Run training on a single graph, verify two models saved, trajectory logs generated, and convergence steps recorded (or censored).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for Cross-Entropy training loop in `tests/unit/test_losses.py`
- [ ] T024 [P] [US2] Unit test for InfoNCE + Linear Probe accuracy calculation in `tests/unit/test_losses.py`

### Implementation for User Story 2

- [ ] T025 [US2] Implement `code/main.py` pipeline logic to iterate over all graphs (N=110) and both loss types with sequential execution. **Constraint**: Must use `SAMPLE_SIZE` from `code/utils.py`. **Dependency**: T019, T008, T009.
- [ ] T026 [US2] Implement `code/train.py` with training loop for Cross-Entropy loss, recording full per-epoch loss/accuracy arrays.
- [ ] T027 [US2] Implement `code/train.py` with training loop for InfoNCE loss. **Logic**: Train encoder for up to `MAX_EPOCHS`. **Convergence**: Record `steps_to_convergence` when accuracy $\ge$ `CONVERGENCE_THRESHOLD`. **Measurement**: Implement a linear probe for accuracy measurement as required by Spec US-2. **Censoring**: If `MAX_EPOCHS` reached without convergence, flag `convergence_status` as "censored". **Output**: Save per-run results to `data/logs/training_run_{id}_{loss_type}.json` including `epochs_trained`, `convergence_status`, and `trajectory` (full list of per-epoch `{loss, accuracy}`). **Dependency**: T008, T009, T004.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Interaction Analysis and Reporting (Priority: P3)

**Goal**: Perform Tobit Regression and Cox Proportional Hazards analysis to test interaction between $\beta$ and loss type on convergence steps. Apply multiple-comparison correction.

**Independent Test**: Run `code/analyze.py` on mock censored data and verify Tobit/Cox coefficients and interaction p-values are correctly computed.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for Tobit regression implementation in `tests/unit/test_analysis.py`
- [ ] T032 [P] [US3] Unit test for Cox PH implementation and interaction term extraction in `tests/unit/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analyze.py` to aggregate `data/logs/` into a single DataFrame using the schema defined in T007.
- [ ] T034 [US3] Implement Tobit Regression (`steps ~ loss_type * beta`) handling censored data (FR-005 correction). **Library**: Use `statsmodels.regression.tobit.Tobit`. **Formula**: `steps_to_convergence ~ C(loss_type) * beta`.
- [ ] T035 [US3] Implement Cox Proportional Hazards survival analysis for convergence "time". **Library**: Use `lifelines.CoxPHFitter`. **Formula**: `steps_to_convergence ~ C(loss_type) * beta`.
- [ ] T036 [US3] Extract interaction term F-statistic/p-value (Tobit) and Hazard Ratio/p-value (Cox).
- [ ] T037 [US3] Implement Bonferroni correction. **Logic**: Correct both raw interaction p-values individually by applying a standard multiplicative adjustment. Take the minimum of the two corrected p-values. **Output**: Update `data/analysis_results.json` to include `is_significant` (boolean: true if corrected p-value < 0.05). **Dependency**: T036.
- [ ] T038 [US3] Generate `data/analysis_results.json` with corrected p-values, coefficients, and a boolean `is_significant` flag (SC-003).
- [ ] T039 [US3] Generate final report in `data/report.md` summarizing whether contrastive loss converges faster as $\beta$ increases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 Code cleanup and refactoring
- [ ] T043 [P] Profile memory usage of `code/train.py` to ensure < 7GB limit.
- [ ] T044 [P] **Runtime Validation**: Run the full pipeline on the CI runner and **assert total duration < 21600s (6 hours)**. If this fails, the build fails.
- [ ] T045 [P] Additional unit tests in `tests/unit/`
- [ ] T046 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T011 (Verify) -> T005b (Data Model) -> T004 (Utils).
 - **Parallel Documentation**: T040a (Research) runs in parallel with T001/T002.
 - **Strict Serial**: T005a1 -> T005a2 -> T005a3. T005b must complete before T008/T009. T004 must complete after T011 and T005b.
- **User Stories (Phase 2+)**: All depend on Foundational completion.
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
- T005a1, T005a2, T005a3 are strictly serial (marked [S]).
- T008, T009, T040b can run in parallel **after** T005b and T004 complete.
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
Task: "Implement code/data_generation.py to generate N=110 graphs"
Task: "Implement community label derivation from initial ring lattice in code/data_generation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup & Research
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
 - **Strict Order**: Verify Plan (T011) -> Data Model (T005b) -> Code (T004, T008, T009).
3. Complete Phase 2: User Story 1
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
- [S] tasks = strictly serial dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All training must run on CPU only (no CUDA, no bitsandbytes).
- **Constraint**: N is fixed at 110 (Spec FR-001).
- **Constraint**: Convergence threshold is set to 0.90. Max epochs is set to a sufficiently high limit to ensure convergence. No loss-plateau early stopping.
- **Constraint**: Full per-epoch trajectory arrays must be stored in `data/logs/` JSON files.
- **Constraint**: DO NOT modify `spec.md` directly.
- **Constraint**: InfoNCE accuracy MUST be measured via a linear probe as per Spec US-2.