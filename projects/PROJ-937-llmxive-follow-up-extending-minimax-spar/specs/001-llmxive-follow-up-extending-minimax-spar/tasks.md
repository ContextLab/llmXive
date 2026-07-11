# Tasks: llmXive follow-up: extending "MiniMax Sparse Attention"

**Input**: Design documents from `/specs/001-llmxive-sparse-attention-heuristics/`
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

- [ ] T001 Create project structure per implementation plan: `mkdir -p projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/code/{models,heuristics,data,analysis,utils} projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/tests/{unit,integration} projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/data/{raw,processed}`
- [ ] T002 Create `projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/requirements.txt` containing pinned versions of `llama-cpp-python`, `datasets`, `scipy`, `pandas`, `numpy`, `pytest`
- [ ] T003 [P] Create `projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/pyproject.toml` with `[tool.black]` and `[tool.ruff]` configuration sections

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/data/ruler_loader.py` to download RULER benchmark tasks from ` to `data/raw/`, compute SHA-256 checksums, and record the checksums in `state/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar.yaml`
- [X] T005 [P] Implement `code/utils/logging.py` to capture CPU time, memory footprint, and heuristic-specific timing logs
- [X] T007 [P] Create base entities `Block` and `HeuristicSelector` in `code/models/entities.py` matching MiniMax sparse granularity
- [~] T006 Implement `code/models/mini_max_wrapper.py` to load MiniMax-M3 model from `MiniMaxAI/MiniMax-M3` in frozen mode via `llama-cpp-python` using GGUF quantization to fit within constrained RAM resources, and provide hooks to disable the Index Branch
- [~] T008 Configure environment variable management for model paths and RULER dataset cache in `code/config/__init__.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Heuristic Injection & Baseline Comparison (Priority: P1) 🎯 MVP

**Goal**: Validate that the "Local Gradient Magnitude" heuristic approximates the dense attention baseline on a single RULER task.

**Independent Test**: Execute a single "Needle In A Haystack" task, compare Exact Match scores, and verify the delta is within 2%.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Then implement code. Then run tests.

- [~] T009 [US1] Unit test for `code/heuristics/gradient_magnitude.py` ensuring CPU-only execution and correct gradient calculation in `tests/unit/test_heuristics.py` (Write first, run after T011)
- [~] T010 [US1] Integration test for "Needle In A Haystack" with heuristic injection in `tests/integration/test_ruler_run.py` (Write first, run after T012)

### Implementation for User Story 1

- [~] T011 [US1] Implement "Local Gradient Magnitude" heuristic in `code/heuristics/gradient_magnitude.py` using input gradients via a single backward pass on a small batch (≤4 sequences), explicitly enforce CPU-only execution, detect GPU devices, log an error and halt if GPUs are detected, and handle edge cases (uniform entropy distribution, split needles)
- [~] T012 [US1] Implement `code/main.py` entry point to load the frozen model, disable the Index Branch, and inject the gradient heuristic
- [~] T013 [US1] Implement `code/analysis/metrics.py` to calculate Exact Match and F1 scores from RULER task outputs
- [~] T015 [US1] Add validation logic to `code/analysis/metrics.py` to flag if the accuracy delta exceeds the tolerance threshold
- [~] T014 [US1] Execute the single RULER "Needle In A Haystack" task, compute and log separate 'heuristic_time' and 'inference_time', log the Exact Match score for the dense baseline and the heuristic, and write results to `data/processed/us1_baseline_vs_heuristic.csv` with columns: task_id, baseline_score, heuristic_score, delta, heuristic_time, inference_time
- [~] T015 [US1] Add validation logic to flag if the accuracy delta exceeds the 2% tolerance threshold and write the measured delta value to the output artifact as a reportable metric

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multi-Heuristic Evaluation & Statistical Significance (Priority: P2)

**Goal**: Compare three heuristics (Entropy, Gradient, Recency) against the dense baseline and perform statistical significance testing.

**Independent Test**: Run the full RULER suite (N=50 tasks) for all heuristics and output a TOST equivalence test result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Unit test for `code/analysis/stats.py` TOST implementation in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [~] T017 [P] [US2] Implement "Block Entropy" heuristic in `code/heuristics/block_entropy.py` with edge case handling for uniform distributions
- [~] T018 [P] [US2] Implement "Recency-Weighted Positional Bias" heuristic in `code/heuristics/recency_bias.py` with edge case handling for split needles
- [ ] T020 [US2] Implement `code/analysis/stats.py` to perform the TOST equivalence test (±2% margin), calculate p-values, and ensure a sufficient set of RULER tasks are collected (sampling to ensure representation of both task types) before the test
- [ ] T019 [US2] Extend `code/main.py` to iterate over the RULER suite (specifically "Needle In A Haystack" and "Multi-Hop Retrieval") for all three heuristics and the dense baseline, calling the statistical logic from T020 to collect data
- [ ] T021 [US2] Implement logic to compare CPU time and memory footprint of heuristics vs. dense baseline and log overhead reduction
- [ ] T022 [US2] Generate a summary report containing mean accuracy, TOST p-value, equivalence conclusion, and cost comparison, writing to `data/processed/us2_statistical_summary.json` with keys: mean_accuracy, tost_p_value, equivalence_conclusion, cost_reduction

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Selection Thresholds (Priority: P3)

**Goal**: Sweep the Top-k selection cutoff (k ∈ {small, medium, large}) to verify robustness.

**Independent Test**: Run the best heuristic with three k-values and verify a smooth accuracy degradation curve.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement sensitivity analysis logic in `code/analysis/stats.py` to calculate accuracy drop-off rates between k-values and flag "high sensitivity" if accuracy drop exceeds a notable threshold for a 10-block increase
- [ ] T024 [US3] Extend `code/main.py` to accept a list of k-values and execute the best-performing heuristic across the RULER suite for each k
- [ ] T027 [US3] Generate a sensitivity report (CSV/JSON) visualizing accuracy vs. k-value, writing to `data/processed/us3_sensitivity_curve.csv` with columns: k_value, accuracy, drop_rate

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T028 [P] Create `docs/heuristic_usage.md` covering heuristic usage and RULER execution
- [ ] T029 Code cleanup and refactoring to ensure no GPU devices are detected during heuristic execution
- [ ] T030 Performance optimization to ensure the full RULER suite completes within 6 hours on CPU
- [ ] T032 [P] Execute `bash docs/quickstart.md` and verify exit code 0, logging output to `data/validation_log.txt`

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
Task: "Unit test for gradient_magnitude.py in tests/unit/test_heuristics.py"
Task: "Integration test for Needle In A Haystack in tests/integration/test_ruler_run.py"

# Launch all models for User Story 1 together:
Task: "Implement Local Gradient Magnitude heuristic in code/heuristics/gradient_magnitude.py"
Task: "Implement metrics calculation in code/analysis/metrics.py"
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