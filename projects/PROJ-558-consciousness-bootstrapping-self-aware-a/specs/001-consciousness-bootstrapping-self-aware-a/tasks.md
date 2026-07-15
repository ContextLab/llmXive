# Tasks: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

**Input**: Design documents from `/specs/001-consciousness-bootstrapping-self-aware-a/`
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

- [ ] T001a [P] Create directory structure: `projects/PROJ-558-consciousness-bootstrapping-self-aware-a/` with subdirs `data/raw`, `data/processed`, `code`, `tests`, `artifacts`, `artifacts/results`
- [ ] T001b [P] Create `__init__.py` files for `code`, `code/models`, `code/training`, `code/evaluation`, `code/analysis`, `code/utils`
- [ ] T001c [P] Initialize Python 3.11 project with `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn` in `requirements.txt`
- [ ] T001d [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `data_loader.py` to fetch the 'arXiv' subset of the Pile dataset via HuggingFace `datasets` API, concatenate tokens, and truncate to the first tokens (config key: `config.TOKEN_LIMIT`), saving to `data/raw/pile_arxiv_truncated.json` with checksum in `data/manifest.json`. **Note**: This task is strictly for TRAINING data.
- [ ] T004b [P] Implement `data_loader.py` (additional function) to fetch GSM8K and MMLU datasets via HuggingFace `datasets` API, saving to `data/raw/gsm8k.json` and `data/raw/mmlu.json` with checksums in `data/manifest.json`. **Note**: This task is strictly for EVALUATION data.
- [~] T005 [P] Implement `config.py` to manage hyperparameters (seed, batch size, recursion depth=2, learning rate, token_limit=100000) and enforce CPU-only execution constraints
- [~] T006 [P] Create base `ModelCheckpoint` and `EvaluationResult` dataclasses in `code/models/` and `code/evaluation/`
- [X] T007 [P] Implement `base_llama.py` wrapper for a small transformer (<300M params) in `code/models/base_llama.py`
- [X] T008 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Train Self-Referential Model (Priority: P1) 🎯 MVP

**Goal**: Construct a TinyLlama-based model with temporal recursive self-attention and train it on a sampled Pile subset to produce recursive and baseline checkpoints.

**Independent Test**: The training pipeline executes on GitHub Actions CPU runner, produces two checkpoints, and completes within 120 minutes without OOM.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These are **Test Definition** tasks. They create the test file content. The CI runner executes these tests **AFTER** the implementation tasks (T011-T015) are merged.

- [X] T009 [P] [US1] **Definition**: Create unit test file `tests/unit/models/test_recursive_attention.py` with test cases: `test_shape_consistency` (checks output shape matches input), `test_attention_mask_propagation` (checks mask handling). (Expected to fail initially)
- [ ] T010 [P] [US1] **Definition**: Create unit test file `tests/unit/training/test_loss_functions.py` with test cases: `test_joint_loss_computation` (checks loss calculation with dummy tensors), `test_confidence_proxy_logic` (checks majority vote logic). (Expected to fail initially)

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `recursive_llama.py` with temporal recursive self-attention module (FR-001) in `code/models/recursive_llama.py`
- [~] T012 [P] [US1] Implement `loss_functions.py` with joint loss (cross-entropy + confidence-prediction). **CRITICAL**: The confidence-prediction loss must use a proxy derived from internal generation: generate multiple internal paths for the training batch, compute majority vote correctness, and use this binary signal to train the confidence head. This aligns with spec.md FR-002 and Assumptions.
- [ ] T013 [US1] Implement `train.py` script to train both recursive and baseline models with fixed seeds (US-01) in `code/training/train.py`
- [ ] T014 [US1] Add validation to `train.py` to prevent recursion depth > 2. **MUST** implement hard-fail: if OOM or depth violation occurs, log error and exit with non-zero code. **MUST NOT** automatically reduce depth.
- [ ] T015 [US1] Add logging for training progress and OOM detection in `code/training/train.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Meta-Cognitive Metrics (Priority: P2)

**Goal**: Run trained models against benchmarks to measure self-consistency, error detection, and uncertainty calibration.

**Independent Test**: Evaluation script ingests checkpoints, generates predictions, and outputs a JSON with raw metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for self-consistency majority vote logic (tie-breaking rule) in `tests/unit/evaluation/test_metrics.py` (Test: `test_majority_vote_tie_break`)
- [ ] T017 [P] [US2] Unit test for Brier score and ECE calculation in `tests/unit/evaluation/test_metrics.py` (Test: `test_brier_score_calc`, `test_ece_calc`)

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `metrics.py` to calculate self-consistency, ROC-AUC, Brier score, and ECE (FR-003, FR-004) in `code/evaluation/metrics.py`
- [ ] T019 [US2] Implement `run_benchmarks.py` to generate **a set of reasoning paths per question for the Self-Consistency benchmark subset** (FR-003) and run MMLU/GSM8K (US-02) in `code/evaluation/run_benchmarks.py`
- [ ] T020 [US2] Implement logic to produce 'shuffled-attention' control dataset for isolation of temporal recursion effects (US-02) in `code/evaluation/run_benchmarks.py`
- [ ] T021 [US2] Add contract validation to ensure output JSON matches `EvaluationResult` schema in `code/evaluation/run_benchmarks.py`
- [ ] T022 [US2] Add logging for benchmark execution and metric aggregation in `code/evaluation/run_benchmarks.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Sensitivity Testing (Priority: P3)

**Goal**: Perform paired t-tests across multiple seeds and sensitivity analysis to determine statistical significance.

**Independent Test**: Analysis script processes evaluation outputs, performs tests, and generates a report with p-values and plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for paired t-test and Bonferroni correction logic in `tests/unit/analysis/test_stats.py` (Test: `test_paired_ttest`, `test_bonferroni_correction`)

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `stats.py` to perform paired t-tests, Cohen's d, confidence intervals, and Bonferroni correction (FR-005, FR-007) in `code/analysis/stats.py`
- [ ] T024b [US3] Implement logic in `stats.py` to calculate and report the **percentage difference in self-consistency scores** between recursive and baseline models as required by spec.md SC-001. Output this to `artifacts/results/statistical_report.json`.
- [ ] T025 [US3] Implement sensitivity analysis sweep for confidence thresholds across the discrete set **{0.4, 0.5, 0.6}** (FR-006) and output results to `artifacts/results/sensitivity_analysis.csv` with columns `threshold, false_positive_rate, false_negative_rate` in `code/analysis/stats.py`
- [ ] T026 [US3] Implement report generation to output `StatisticalReport` with p-values, effect sizes, confidence intervals, and sensitivity plots (US-03) in `code/analysis/stats.py`
- [ ] T027 [US3] Add logic to exclude invalid seeds (non-converged confidence loss) from statistical comparison (Edge Case) in `code/analysis/stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` including the new statistical report format
- [ ] T038 [P] Run `ruff check` and `black --check` on the entire `code/` directory; CI must fail if any lint/format errors exist
- [ ] T039 [P] Run memory profiling on the training script (`train.py`) with max batch size; verify peak RSS < 7GB and log result to `artifacts/results/memory_profile.log`
- [ ] T040 [P] Additional unit tests for the new statistical metrics in `tests/unit/analysis/test_stats.py`
- [ ] T041 [P] Run `quickstart.md` validation to ensure all artifacts are generated correctly

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

- **Test Definition** (T009, T010, etc.) MUST be written before implementation tasks to define the interface.
- **Implementation** (T011-T015, etc.) MUST follow.
- **Test Execution** (CI runner) MUST run after implementation is merged.
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
# Launch all Test Definition tasks for User Story 1 together:
Task: "Create unit test file tests/unit/models/test_recursive_attention.py"
Task: "Create unit test file tests/unit/training/test_loss_functions.py"

# Launch all Implementation tasks for User Story 1 together:
Task: "Implement recursive_llama.py with temporal recursive self-attention module"
Task: "Implement loss_functions.py with joint loss using self-consistency proxy"
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
 - Developer A: User Story 1 (Training)
 - Developer B: User Story 2 (Evaluation)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and memory. No GPU, no 8-bit quantization.
- **Scope Note**: The "Reviewer Concerns" (Turing, Socrates, Krakauer, etc.) and associated metrics (e.g., "Metabolic Cost Proxy", "Value-Judgment Proxy", "Pre-Generation Prediction") mentioned in `plan.md` are **OUT OF SCOPE** for this implementation. `spec.md` does not contain Functional Requirements (FRs) or Success Criteria (SCs) for these philosophical operationalizations. Consequently, no tasks exist to implement them. The project scope is strictly limited to the measurable metrics defined in `spec.md` (self-consistency, calibration, error detection) as per the "Assumptions" section of `spec.md`.
- **Plan Contradiction Note**: `plan.md` mentions "Teacher-Student Distillation" and "Pre-computed Teacher Labels" as a complexity tracking item. However, `spec.md` FR-002 and Assumptions mandate a self-consistency proxy derived from internal generation. Tasks T011-T015 implement the `spec.md` requirement (internal proxy), effectively superseding the `plan.md` complexity tracking item which is now considered out of scope.
