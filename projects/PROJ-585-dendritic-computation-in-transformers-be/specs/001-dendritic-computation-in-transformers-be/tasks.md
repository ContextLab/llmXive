# Tasks: Dendritic Computation in Transformers: Beyond Point Neurons

**Input**: Design documents from `/specs/001-dendritic-computation-in-transformers/`
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

- [ ] T001a Create source directories: `mkdir -p code/models code/data code/experiments code/config code/tests` and create `__init__.py` files in `code`, `models`, `data`, `experiments`, `config`, `tests`.
- [ ] T001b Create data and artifacts directories: `mkdir -p artifacts/logs artifacts/checkpoints artifacts/results state data/raw data/processed`.
- [ ] T002 Initialize Python 3.11 project: Create `requirements.txt` with pinned versions (torch==2.x, datasets==2.x, scikit-learn==1.x, pandas==2.x, numpy==1.x, pytest==8.x) and verify `pip install -r requirements.txt` succeeds.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/config/config.yaml` with required keys: `learning_rate` (float), `batch_size` (int), `dendritic_thresholds` (list of 3 floats: low, moderate, high), `cpu_timeout` (int, 21600 seconds), and `num_seeds` (int, 3-5).
- [ ] T005 [P] Implement `code/models/utils.py` with FLOP counter and parameter matcher
- [ ] T006 [P] Setup `code/data/loaders.py` to fetch GLUE SST-2 via HuggingFace `datasets` with checksum verification
- [ ] T007 Create base `code/models/transformer_base.py` standard point-neuron baseline
- [ ] T008 Implement gradient clipping utility and timeout handler in `code/experiments/utils.py`
- [ ] T009 Setup `state/artifact_hashes.yaml` and `data/checksums.manifest` for data hygiene

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Implement and Match Baseline Architectures (Priority: P1) 🎯 MVP

**Goal**: Implement matched baseline and dendritic variants with identical parameter counts and FLOPs.

**Independent Test**: Instantiate both models with a fixed seed, run a forward pass on dummy data, and verify parameter/FLOP match via `validate_arch.py`.

### Implementation for User Story 1

- [ ] T013 [US1] Create `code/experiments/validate_arch.py` to calculate and log FLOPs/Params for both models
- [ ] T011 [P] [US1] Implement `code/models/transformer_dendritic.py` with compartmentalized units (local nonlinearities, plateau gating) and explicitly define the dendritic update rule (state vector, nonlinear integration) within the class. Include docstrings for `local_nonlinearities`, `plateau_gating`, and `calcium_modulation`.
- [ ] T015 [US1] Add structural validation logic to ensure the dendritic architecture is distinct from standard point-neuron MLPs (focus on structural difference, not specific logical calculus checks).
- [ ] T014 [US1] Implement logic to adjust linear projection width in dendritic model to compensate for gating overhead (ensuring <1% FLOP diff) - depends on T013 output and T011 implementation.
- [ ] T016 [US1] Add logging for exact parameter counts and FLOP breakdowns (linear vs. nonlinear ops)

### Tests for User Story 1

- [ ] T010a [P] [US1] Create `tests/test_architecture.py` with failing assertions for FLOP/Param matching (Expected failure: ImportError or FileNotFoundError if T013/T011 not present).
- [ ] T010b [US1] Implement validation logic in `tests/test_architecture.py` to assert FLOP/Param matching once T013 and T011 are complete. Specifically: run `pytest tests/test_architecture.py` and assert `abs(param_count_baseline - param_count_dendritic) / param_count_baseline < 0.001` and `abs(flop_count_baseline - flop_count_dendritic) / flop_count_baseline < 0.01`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate on Standard Benchmarks (Priority: P2)

**Goal**: Train both models on GLUE sentiment analysis with a fixed CPU timeout and record metrics.

**Independent Test**: Run training script on CPU, verify hard stop at 6h, and confirm logs contain accuracy/loss curves.

### Tests for User Story 2

- [ ] T017 [P] [US2] Integration test for timeout mechanism in `tests/test_training.py`

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/experiments/train.py` main loop with a SIGALRM signal handler that raises a TimeoutError after 6 hours (21600 seconds) to enforce a hard stop within the training loop.
- [ ] T019 [US2] Integrate gradient clipping (threshold ≤ 1.0) and log clipping frequency for stability
- [ ] T020 [US2] Implement logging for accuracy and loss curves at regular intervals
- [ ] T021 [US2] Add checkpoint saving logic for both models to enable downstream probing
- [ ] T022 [US2] Ensure training uses real SST-2 data (no synthetic/fake data) and records data source checksums
- [ ] T023 [US2] Implement logic to compare time-series learning curves (area under curve) as per edge case requirements

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Hierarchical Feature Probing and Statistical Analysis (Priority: P3)

**Goal**: Probe intermediate layers, perform statistical tests, and validate robustness.

**Independent Test**: Run probing script on saved checkpoints, generate p-values/effect sizes, and verify JSON/CSV output.

### Tests for User Story 3

- [ ] T024 [P] [US3] Unit test for statistical analysis functions in `tests/test_analyze.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `code/experiments/probe.py` to train linear classifiers on intermediate layer representations for multiple random seeds as required for statistical power.
- [ ] T027 [US3] Implement `code/experiments/analyze.py` with Wilcoxon signed-rank or paired t-tests
- [ ] T028 [US3] Implement multiple-comparison correction (Bonferroni or Benjamini-Hochberg) for per-layer tests
- [ ] T029 [US3] Implement FR-007 sensitivity analysis: Sweep the `dendritic_thresholds` config key targeting the *local nonlinear dendritic branches* parameter (as defined in Constitution Principle VI) and report variance in probing accuracy.
- [ ] T030 [US3] Add logic to measure "sample efficiency" defined as steps to reach a substantial fraction of the baseline model's final accuracy, using the baseline's final accuracy as the reference point.
- [ ] T031 [US3] Add logic to measure "hierarchical feature detection" (area under accuracy-vs-depth curve)
- [ ] T033 [US3] Add output to `artifacts/results/` including p-values, effect sizes, and stability metrics (effect size stability across sensitivity sweeps as per SC-004).
- [ ] T034 [US3] Verify probing tasks use real SST-2 derived features, not synthetic placeholders

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` and `README.md` (including model docstrings for dendritic mechanisms). **Note**: Tasks T035-T039 (Rule-Space Enumeration, Mutual Information, Reviewer Analogies) were removed as they are out of scope per spec.md and plan.md. Documentation must map to existing FRs/SCs only.
- [ ] T041 Code cleanup and refactoring
- [ ] T042 Performance optimization across all stories (ensure CPU efficiency)
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 models being defined
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 checkpoints being available

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
# Launch all models for User Story 1 together:
Task: "Implement code/models/transformer_dendritic.py with compartmentalized units"
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
   - Developer A: User Story 1 (Architecture)
   - Developer B: User Story 2 (Training)
   - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All training and analysis must run on CPU-only hardware (2 cores, 7GB RAM) within 6 hours. No GPU, no low-bit quantization, no large models.
- **Data Integrity**: All tasks involving data must use real datasets (GLUE SST-2) fetched via verified URLs. No synthetic data generation.
- **Scope Control**: Do not implement "rule-space enumeration" or "Wolfram review" tasks; they are out of scope. Focus strictly on FR-007 sensitivity analysis.
- **Review Compliance**: Documentation updates in Phase N (T040) will address standard model documentation requirements, but specific reviewer analogies (Kandel, von Neumann, Wolfram) are not implemented as separate artifacts.