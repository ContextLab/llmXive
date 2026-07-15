# Tasks: llmXive follow-up: extending "From Chatbot to Digital Colleague"

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [X] T001 [P] Create directory structure: `data/raw`, `data/results`, `code`, `tests/unit`, `tests/contract`, `contracts`, `projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/`
- [X] T002 [P] Create `requirements.txt` with **pinned versions** for reproducibility (e.g., `scikit-learn==1.3.0`, `sentence-transformers==2.2.2`, `pandas==2.0.0`, `numpy==1.24.0`, `pytest==7.3.0`, `pyyaml==6.0`, `statsmodels==0.14.0`).
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 [P] Implement `code/config.py` to load random seeds from environment variables `SEED_A` and `SEED_B` with defaults, and verify by running `python -c "from code.config import SEED_A; print(SEED_A)"`.
- [X] T005 [P] Implement `code/config.py` with experiment parameters (seeds loaded from T008, library sizes: 10, 30, 50, 100, overlap levels).
- [X] T006 [P] Implement `code/utils.py` with embedding helpers (CPU-only `sentence-transformers`), cosine similarity metrics, and variance calculation functions.
- [X] T007 [P] Implement `code/logging_config.py` to configure a `logging.Logger` instance that writes to `data/results/experiment_log.csv` (CSV format) with JSON formatting for metadata, and verify by running a test script that writes a log entry and confirms file existence.
- [X] T004 [P] Create `contracts/` directory and define `task.schema.yaml`, `skill.schema.yaml`, and `experiment_log.schema.yaml`. For `experiment_log.schema.yaml`, explicitly define properties: `task_id`, `skill_id`, `success` (bool), `latency` (float), `tokens` (int), `retrieval_precision` (float), `retrieval_diversity` (float), `pruning_risk_count` (int), `library_size` (int), `pruning_enabled` (bool).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Dataset and Skill Library Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a reproducible synthetic environment containing a substantial number of multi-step tasks and a configurable library of 100 overlapping Python "skills" with controlled semantic density.

**Independent Test**: Execute `code/generate_data.py` and verify `data/raw/tasks.json` contains a sufficient number of records with valid ground-truth paths, and `data/raw/skills.json` contains a representative set of skills with calculated pairwise cosine similarities matching the configured overlap level.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for `code/generate_data.py` verifying ground-truth independence (Seed A vs Seed B) in `tests/unit/test_generation.py`
- [X] T010 [P] [US1] Contract test validating `tasks.json` schema against `contracts/task.schema.yaml` in `tests/contract/test_schemas.py`
- [X] T011 [P] [US1] Contract test validating `skills.json` schema and overlap metrics against `contracts/skill.schema.yaml` in `tests/contract/test_schemas.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/generate_data.py` to create **exactly 100 Python functions (skills)** and **exactly 500 multi-step tasks**. **Explicitly validate** that mean pairwise cosine similarity matches thresholds: Low <0.30, Medium >0.50 (and >30% pairs >0.50), High >0.80 (and >30% pairs >0.80). Generate tasks with unique ground-truth solution paths (a small number of deterministic actions) independent of the embedding space.
- [ ] T013 [US1] Implement logic in `code/generate_data.py` to **assign** unique ground-truth solution paths (3-5 skill IDs) to each of the 500 tasks, ensuring this assignment uses a distinct random seed (Seed B) from the skill generation (Seed A) to guarantee independence.
- [ ] T014 [US1] Implement JSON serialization in `code/generate_data.py` to output `data/raw/skills.json` and `data/raw/tasks.json` with embedded metadata (overlap level, seed used). <!-- ATOMIZE: requested -->
- [~] T015 [US1] Implement logic in `code/generate_data.py` to detect mean pairwise similarity >= 0.95. If detected: **set Retrieval Precision to a minimal baseline level**, **implement deterministic tie-breaking logic (random selection with logging)**, log a warning, and ensure the script exits with code 0 while writing `data/raw/skills.json` with a `maximal_overlap_detected: true` flag in metadata.
- [X] T016 [US1] Add memory pressure check in `code/generate_data.py` to detect RAM limits during embedding calculation and fail gracefully with "Memory Limit Exceeded" if > 6 GB.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Agent Execution and Metric Collection (Priority: P2)

**Goal**: Run the minimalistic "Digital Colleague" agent across varying library sizes and record task completion rates, token usage, and latency for each configuration.

**Independent Test**: Run `code/agent.py` with a fixed subset of tasks and a specific library size; verify `data/results/experiment_log.csv` contains latency, token counts, success/failure flags, and retrieval precision metrics for every run.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for `code/agent.py` verifying retrieval failure handling (missing skill) logs specific error and does not hallucinate in `tests/unit/test_agent.py`
- [X] T018 [P] [US2] Integration test for the full execution loop (500 tasks × 1 config) verifying `experiment_log.csv` structure in `tests/integration/test_execution.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/agent.py` retrieval logic using `code/utils.py` to fetch top-k (k=5) skills based on task embedding.
- [X] T022 [US2] Implement logging infrastructure in `code/agent.py` to **create** `data/results/experiment_log.csv` with a header row matching the schema defined in T004.
- [X] T021 [US2] Implement calculation of **Retrieval Precision** (Jaccard similarity between top-k retrieved skills and ground-truth set) and **Retrieval Diversity** (inverse of the variance of the cosine similarities of the top-k retrieved skills against the ground-truth set) in `code/agent.py` per FR-006 and SC-002, and **append** these values as new data rows to `data/results/experiment_log.csv` for every task run.
- [X] T020 [US2] Implement execution logic in `code/agent.py` to run the retrieved skills and compare output against the ground-truth solution path from `tasks.json`.
- [X] T023 [US2] Create `code/run_experiment.py` to iterate through library sizes (various magnitudes, including small, medium, and large) and call `agent.py`, aggregating results into `data/results/metrics.json`.
- [~] T024 [US2] Add handling for "missing skill" edge cases where the agent fails gracefully, logs the missing skill ID, and records the failure without crashing.
- [X] T027 [US2] Implement "Safe Pruning" heuristic in `code/agent.py` that removes skills where `usage_count == 0` AND `min_cosine_similarity < 0.70` after every 10 tasks, per FR-004. **Explicitly log the count of pruned skills that had high similarity to ground truth to `experiment_log.csv`**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Pruning Heuristic and Threshold Analysis (Priority: P3)

**Goal**: Apply a "Skill Pruning" heuristic to the active library after every 10 tasks and perform statistical analysis to determine if pruning mitigates performance degradation.

**Independent Test**: Run `code/analyze.py` on the full experiment data; verify output includes p-values for pruning efficacy, the "tipping point" breakpoint, and VIF < 5.0 for predictors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for pruning logic verifying skills with usage=0 and similarity < 0.70 are removed after 10 tasks in `tests/unit/test_pruning.py`
- [X] T026 [P] [US3] Unit test for statistical analysis verifying Logistic Regression output format in `tests/unit/test_analyze.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement logic in `code/agent.py` to count skills removed with high similarity to ground truth and append a `pruning_risk_count` column to `data/results/experiment_log.csv` for every periodic batch of tasks.
- [~] T036 [US3] Create `code/run_baseline.py` to run the full experiment set (library sizes ranging from small to large) with **pruning disabled** and save results to `data/results/experiment_log_baseline.csv` to satisfy SC-003 performance recovery comparison.
- [X] T030 [US3] Implement `code/analyze.py` to load `data/results/experiment_log.csv` and perform **Piecewise Linear Regression with a single breakpoint** (per FR-005, SC-004) to identify the "tipping point" library size where success rate declines. **Calculate x0 (tipping point) by finding the breakpoint parameter**. Output the breakpoint parameter x0 to a log/variable.
- [X] T039 [US3] Implement **Logistic Regression with a Quadratic Term** (per Plan: Methodological Correction, See Plan: Methodological Correction) in `code/analyze.py` to identify the "tipping point" library size where success rate declines. **Calculate x0 (tipping point) by finding the inflection point (derivative = 0) of the fitted logistic curve**. Output the breakpoint parameter x0 to a log/variable and verify it is included in the final report.
- [X] T031 [US3] Implement calculation of **Variance Inflation Factor (VIF)** in `code/analyze.py` for predictors "library size" and "total redundancy" to confirm VIF < 5.0, output VIF values to a log/variable.
- [~] T032 [US3] Generate final report in `code/analyze.py` outputting the tipping point value, p-value for pruning efficacy, and VIF metrics to `data/results/final_analysis.json`.
- [~] T040 [US3] Implement sensitivity analysis logic in `code/analyze.py` to sweep pruning thresholds across a range of **{5, 10, 20} tasks** (per Spec Assumptions) and verify robustness of the tipping point finding. Output results to `data/results/sensitivity_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T034 [P] Update `README.md` with installation and run instructions.
- [~] T036 [P] Update `quickstart.md` with end-to-end execution steps.
- [~] T037 [P] Code cleanup and refactoring to ensure all random seeds are pinned and dependencies are reproducible.
- [~] T038 [P] Performance optimization: Ensure embedding calculation for 100 skills runs within memory constraints (sample if necessary).
- [~] T039 [P] Additional unit tests for edge cases (maximal overlap, memory limits) in `tests/unit/`.
- [~] T041 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility on a clean environment. <!-- FAILED: unspecified -->

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data generation (US1) for inputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on execution logs (US2) for analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 (Data Gen) and US2 (Agent) can start in parallel (US2 depends on US1 data, but code can be written in parallel)
- All tests for a user story marked [P] can run in parallel
- Models/Utils within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for generate_data.py verifying ground-truth independence"
Task: "Contract test validating tasks.json schema"
Task: "Contract test validating skills.json schema"

# Launch all models/utils for User Story 1 together:
Task: "Implement code/generate_data.py for skills"
Task: "Implement code/generate_data.py for tasks"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Generation)
4. **STOP and VALIDATE**: Test Data Generation independently
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
 - Developer A: User Story 1 (Data Gen)
 - Developer B: User Story 2 (Agent Execution) - can start coding logic while waiting for data
 - Developer C: User Story 3 (Analysis) - can start coding logic while waiting for results
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
- **Compute Feasibility**: All tasks assume CPU-only execution with a limited core count and constrained RAM. No GPU or 8-bit quantization is used.
- **Data Integrity**: No fake data generation; all data is synthetic but deterministic and grounded in the specified seeds.