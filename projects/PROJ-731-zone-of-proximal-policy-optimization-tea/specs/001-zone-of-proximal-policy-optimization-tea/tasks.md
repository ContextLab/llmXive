# Tasks: Zone of Proximal Policy Optimization

**Input**: Design documents from `/specs/001-zone-of-proximal-policy-optimization/`
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

- [ ] T001a [P] Create `code/` directory and `code/__init__.py`
- [ ] T001b [P] Create `code/requirements.txt`
- [ ] T001c [P] Create `code/train_ppo.py` (empty placeholder)
- [ ] T001d [P] Create `code/eval_benchmarks.py` (empty placeholder)
- [ ] T001e [P] Create `code/reward.py` (empty placeholder)
- [ ] T001f [P] Create `code/data_loader.py` (empty placeholder)
- [ ] T001g [P] Create `tests/` directory structure (`unit/`, `integration/`, `contract/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (torch-cpu, transformers, datasets, accelerate, scikit-learn, pandas, numpy, pytest, scipy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading and reward logic.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement seed pinning utilities in `code/utils/seeds.py` to ensure reproducibility across all scripts
- [ ] T005 Implement structured logging and metrics tracking in `code/utils/logging.py` (JSONL format, step metadata)
- [ ] T006 Create `PromptBufferMetadata` schema and validation logic in `code/data_loader.py`
- [ ] T007 Implement `generate_checksums.py` script in `code/scripts/` to create `data/checksums.json`
- [ ] T008 Setup directory structure for `data/prompts/{0k,10k,50k,200k}`, `results/training_logs`, `results/benchmarks`, `results/analysis`
- [ ] T009 Implement memory-safe model loading utility in `code/utils/model_loader.py` (CPU-only, dynamic memory fallback)
- [ ] T013a [P] [US1] Implement logic for the **0k baseline condition**: Create `data/prompts/0k/prompts.jsonl` as an empty file and ensure the data loader explicitly handles this condition without attempting to fetch data or fallback. (FR-002)
- [ ] T013b [P] [US1] Implement data loader to fetch `openassistant/oasst1` (split='train'), verify size >= 10,000, shuffle randomly (`dataset.shuffle(seed=SEED)`), select first [deferred] rows, save to `data/prompts/10k/prompts.jsonl`. Abort if size < 10k. (FR-002)
- [ ] T013c [P] [US1] Implement data loader to fetch `openassistant/oasst1` (split='train'), verify size >= 50,000, shuffle randomly (`dataset.shuffle(seed=SEED)`), select first [deferred] rows, save to `data/prompts/50k/prompts.jsonl`. Abort if size < 50k. (FR-002)
- [ ] T013d [P] [US1] Implement data loader to fetch `openassistant/oasst1` (split='train'), verify size >= 200,000, shuffle randomly (`dataset.shuffle(seed=SEED)`), select first [deferred] rows, save to `data/prompts/200k/prompts.jsonl`. Abort if size < 200k. (FR-002)
- [ ] T014 [P] [US1] Implement `code/reward.py` to compute binary correctness reward (0/1) based on reference match (FR-003). **Input**: (prompt: str, response: str, reference: str). **Output**: 0.0 or 1.0 (float). **Constraint**: This is the *sole reward signal*. The KL-penalty (in T015) is a *loss regularization term*, NOT a reward signal.
- [ ] T014b [P] [US1] Implement missing exemplar handling in `code/reward.py`: Detect if reference is null/missing, return 0.0, and log the missing-exemplar rate. (US-1 Edge Case)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core PPO Training Loop with Variable Prompt Sizes (Priority: P1) 🎯 MVP

**Goal**: Execute PPO training with four prompt-size conditions (0k, 10k, 50k, 200k) and log metrics, respecting 6h/GB RAM limits.

**Independent Test**: Can be fully tested by executing a single training run with one prompt-size condition (e.g., 10k prompts) and verifying that benchmark scores are logged at regular intervals during PPO training.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for correctness reward calculation (0/1 match) in `tests/unit/test_reward.py`
- [ ] T011 [P] [US1] Contract test for training run output schema in `tests/contract/test_schemas.py`
- [ ] T012 [US1] Integration test for training loop flow with memory fallback in `tests/integration/test_training_loop.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/train_ppo.py` with clipped-surrogate loss (clip_range=0.2) and KL-penalty (kl_coef=0.1) as a **loss regularization term** (not a reward signal). **Hyperparameters**: lr=1e-5, batch_size=8, mini_batch_size=4. **Model**: GPT-NeoX-125M. **Constraints**: Must handle 6h time limit (save checkpoint and exit gracefully) and enforce memory constraints (fail run if >7GB, do not sample dynamically). **Consume reward function from T014/T014b**. **Note**: This task includes the 6h time limit and memory constraint logic; separate tasks T016/T017 were removed to ensure atomicity.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Benchmark Evaluation at Regular Intervals (Priority: P2)

**Goal**: Evaluate student model on lambada_openai, truthful_qa, and mmlu at regular intervals and record accuracy metrics on CPU.

**Independent Test**: Can be tested by running evaluation on a fixed checkpoint across all three benchmarks and verifying that exact-match or accuracy scores are computed and stored.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for benchmark output schema in `tests/contract/test_schemas.py`
- [ ] T021 [P] [US2] Unit test for retry logic on dataset access failure in `tests/unit/test_data_loader.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/eval_benchmarks.py` to load `lambada_openai` (default), `truthful_qa` (config='generation'), and `mmlu` (split='test') via HuggingFace Datasets. **Metric**: Accuracy (fraction of exact matches).
- [ ] T023 [US2] Implement evaluation logic for each benchmark suite (accuracy/exact-match).
- [ ] T024 [US2] Add retry logic for dataset access failures. **Must log failure state and final outcome if retries exhausted. If retries exhausted, return error code and ensure the calling training loop catches this and continues to the next step (graceful degradation).**
- [ ] T025 [US2] Modify `code/train_ppo.py` (created in T015) to inject evaluation calls at regular intervals. **Dependency**: T015 (base loop) must exist; T025 modifies T015.
- [ ] T026 [US2] Ensure evaluation runs within A fixed duration per suite on CPU (optimize batch size if needed).
- [ ] T027 [US2] Append results to `results/benchmarks/` with step count and seed metadata (FR-005).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis for Diminishing Returns (Priority: P3)

**Goal**: Log raw data (performance curves) to enable post-hoc statistical testing for diminishing returns and non-linear trends.

**Independent Test**: Can be tested by providing synthetic performance-per-step data across 4 conditions and verifying that the logged data structure allows for the computation of performance curves and variance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for analysis data schema in `tests/contract/test_schemas.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Create aggregation script `code/scripts/aggregate_results.py` to merge all training logs and benchmark results.
- [ ] T030 [US3] Implement logging of performance curves to `results/analysis/curves.csv`. **Schema**: Columns must be `step` (int), `seed` (int), `prompt_size` (str), `benchmark_name` (str), `accuracy` (float), `average_correctness_reward` (float, mean of 0/1), `kl_divergence` (float). **Mode**: Append. Ensure data structure supports piecewise-linear regression. (FR-006, FR-007)
- [ ] T034 [US3] Implement orchestration logic to run **multiple independent seeds per prompt-size condition**. Calculate Coefficient of Variation (CV) on final benchmark scores to verify SC-005 (CV < 0.05). Generate summary statistics (mean, variance) per condition.
- [ ] T033 [US3] Document the non-parametric statistical approach (Kendall's Tau, Kruskal-Wallis) in `research.md` for the planned analysis.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T036 Code cleanup and refactoring for memory efficiency
- [ ] T037 Performance optimization for CPU-only evaluation (batching, precision)
- [ ] T038 [P] Additional unit tests for edge cases (missing exemplars, convergence failures) in `tests/unit/`
- [ ] T039 Run quickstart.md validation to ensure all tasks are executable in order

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1's training loop for checkpoints
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 & US2 for data aggregation

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
Task: "Contract test for training run output schema in tests/contract/test_schemas.py"
Task: "Integration test for training loop flow with memory fallback in tests/integration/test_training_loop.py"

# Launch data loading tasks (T013a-d) in parallel:
Task: "Create empty buffer file for 0k condition"
Task: "Fetch 10k subset from openassistant/oasst1 (shuffled)"
Task: "Fetch 50k subset from openassistant/oasst1 (shuffled)"
Task: "Fetch 200k subset from openassistant/oasst1 (shuffled)"
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
- **Critical Constraint**: All tasks must run on CPU-only runners with minimal core counts and limited memory. No GPU, no 8-bit/4-bit quantization requiring CUDA.
- **Data Integrity**: All dataset downloads must use real, reachable URLs (e.g., HuggingFace `datasets.load_dataset`). No synthetic/fake data generation tasks.
- **Version Control**: All prompt buffers must be pre-verified and checksummed. No runtime-sampled subsets.