# Tasks: llmXive follow-up: extending "From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 [P] Create subdirectories: `data/raw`, `data/results`, `code`, `tests/unit`, `tests/contract`, `contracts` (root level). **Note**: Do NOT create the root project directory itself, only subdirectories within the existing repo root.
- [X] T002 [P] Create `requirements.txt` with **pinned versions** for reproducibility (e.g., `scikit-learn==1.3.0`, `sentence-transformers==2.2.2`, `pandas==2.0.0`, `numpy==1.24.0`, `pytest==7.3.0`, `pyyaml==6.0`, `statsmodels==0.14.0`, `scipy==1.11.0`).
- [ ] T003 [P] Create `quickstart.md` with initial placeholder content and installation instructions to satisfy Plan's artifact flow.
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools in `.pre-commit-config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009a [P] Create `contracts/task.schema.yaml` with inline schema definition for tasks (properties: `task_id`, `description`, `ground_truth_path`, `complexity`). **Verification**: Validate that `jsonschema.validate` passes for a sample task object.
- [ ] T009b [P] Create `contracts/skill.schema.yaml` with inline schema definition for skills (properties: `skill_id`, `function_code`, `embedding_vector`, `usage_count`). **Verification**: Validate that `jsonschema.validate` passes for a sample skill object.
- [ ] T009c [P] Create `contracts/experiment_log.schema.yaml` with inline schema definition (properties: `task_id`, `skill_id`, `success`, `latency`, `tokens`, `retrieval_precision`, `retrieval_diversity`, `pruning_risk_count`, `library_size`, `pruning_enabled`, `edge_case`). **Verification**: Validate that `jsonschema.validate` passes for a sample log entry.
- [ ] T007 [P] Implement `code/logging_config.py` to configure a `logging.Logger` instance that writes to `data/results/experiment_log.csv`. **Prerequisite**: T009c. **Instruction**: Use hardcoded column names matching `contracts/experiment_log.schema.yaml` to configure the CSV writer, ensuring column structure matches the contract. **Verification**: Run a test script that writes a log entry and confirms file existence and schema compliance.
- [X] T005a [P] Implement `code/config.py` to **define default SEED_A and SEED_B** (deterministic inline values) AND **load** them from environment variables (overriding defaults if set). **Verification**: Run `python -c "from code.config import SEED_A, SEED_B; print(SEED_A, SEED_B)"` and verify output matches expected structure.
- [X] T005b [P] Implement `code/config.py` to **define default OVERLAP_LEVEL** (string: 'low', 'medium', 'high') and **load** it from environment variables. **Prerequisite**: T005a. **Verification**: Run `python -c "from code.config import OVERLAP_LEVEL; print(OVERLAP_LEVEL)"` and verify output matches expected structure.
- [X] T006 [P] Implement `code/utils.py` with embedding helpers (CPU-only `sentence-transformers`), cosine similarity metrics, and variance calculation functions.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Dataset and Skill Library Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a reproducible synthetic environment containing a substantial number of multi-step tasks and a configurable library of 100 overlapping Python "skills" with controlled semantic density.

**Independent Test**: Execute `code/generate_data.py` and verify `data/raw/tasks.json` contains a sufficient number of records with valid ground-truth paths, and `data/raw/skills.json` contains a representative set of skills with calculated pairwise cosine similarities matching the configured overlap level.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for `code/generate_data.py` verifying ground-truth independence (Seed A vs Seed B) in `tests/unit/test_generation.py`
- [ ] T011 [P] [US1] Contract test validating `tasks.json` schema against `contracts/task.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: T009a.
- [ ] T012 [P] [US1] Contract test validating `skills.json` schema and overlap metrics against `contracts/skill.schema.yaml` in `tests/contract/test_schemas.py`. **Prerequisite**: T009b.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/generate_data.py` to create **exactly 500 multi-step tasks** and **a diverse set of Python functions (skills)**. **Explicitly validate** that mean pairwise cosine similarity matches thresholds: Low <0.30, Medium >0.50 (and >30% pairs >0.50), High >0.80 (and >30% pairs >0.80). **Read OVERLAP_LEVEL from config.py** (T005b) to determine target thresholds. Use `sklearn.metrics.pairwise.cosine_similarity` for validation. Generate tasks with unique ground-truth solution paths (a small number of deterministic actions) independent of the embedding space. **Prerequisite**: T005b.
- [X] T014 [US1] Implement logic in `code/generate_data.py` to **assign** unique ground-truth solution paths (A small set of skill IDs) to each of the 500 tasks, ensuring this assignment uses a distinct random seed (Seed B) from the skill generation (Seed A) to guarantee independence.
- [ ] T015 [US1] Implement JSON serialization in `code/generate_data.py` to output `data/raw/skills.json` and `data/raw/tasks.json` with embedded metadata (overlap level, seed used). **Include checksum generation (SHA-256)** for both files and write `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` (updating the `artifact_hashes` map specifically) with the checksums. **Structure**: `{ 'artifact_hashes': { 'tasks.json': 'sha256...', 'skills.json': 'sha256...' } }`. **Prerequisite**: T013, T014. **Verification**: Verify checksums match and `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` is updated with the correct nested key structure, referencing Constitution Principle V as the source of truth.
- [ ] T017 [US1] Add memory pressure check in `code/generate_data.py` to detect RAM limits during embedding calculation and fail gracefully with "Memory Limit Exceeded" if > 7 GB (matching Plan limits).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Agent Execution and Metric Collection (Priority: P2)

**Goal**: Run the minimalistic "Digital Colleague" agent across varying library sizes and record task completion rates, token usage, and latency for each configuration.

**Independent Test**: Run `code/agent.py` with a fixed subset of tasks and a specific library size; verify `data/results/experiment_log.csv` contains latency, token counts, success/failure flags, and retrieval precision metrics for every run.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for `code/agent.py` verifying retrieval failure handling (missing skill) logs specific error and does not hallucinate in `tests/unit/test_agent.py`
- [X] T020 [P] [US2] Integration test for the full execution loop (A representative set of tasks across multiple configurations) verifying `experiment_log.csv` structure in `tests/integration/test_execution.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/agent.py` retrieval logic using `code/utils.py` to fetch top-k (k=5) skills based on task embedding. **Include `os.fsync()` and `file.flush()` calls** after every log write to prevent race conditions.
- [X] T022 [US2] Implement logging infrastructure in `code/agent.py` to **create** `data/results/experiment_log.csv` with a header row matching the schema defined in T009c. **Prerequisite**: T009c.
- [X] T028 [US2] Implement "Safe Pruning" heuristic in `code/agent.py` that removes skills where `usage_count == 0` AND `min_cosine_similarity < 0.70` **strictly after every N tasks** (read N from `config.py`, default 10). **Explicitly calculate and return `pruning_risk_count`** (skills pruned that had high similarity to ground truth, defined as similarity > 0.70) for use by T023. **CRITICAL**: The trigger is configurable to allow sensitivity analysis. **Verification**: Confirm `pruning_risk_count` is calculated and returned correctly, and the trigger reads from config.
- [X] T023 [US2] Implement calculation of **Retrieval Precision** (Jaccard similarity between top-k retrieved skills and ground-truth set) and **Retrieval Diversity** (inverse of the variance of the cosine similarities of the retrieved skills against the ground-truth set) in `code/agent.py` per FR-006 and SC-002, and **append** these values as new data rows to `data/results/experiment_log.csv` for every task run. **Prerequisite**: T021, T022. **Instruction**: For each task run, calculate the cosine similarities of the top-k retrieved skills against the ground-truth set (aligning each retrieved skill to its nearest ground-truth skill to form a set of k similarity scores), compute the variance of these k scores, and then calculate `1/variance`. **Handle zero-variance case by returning 0.0 or infinity**. **Include `pruning_risk_count`** (calculated by the pruning step within this task) in the same atomic write operation. **Note**: This task reads the schema from T009c to ensure column structure matches. **Verification**: Confirm all metrics (including `pruning_risk_count`) are appended correctly and headers are written once.
- [X] T024 [US2] Implement execution logic in `code/agent.py` to run the retrieved skills and compare output against the ground-truth solution path from `tasks.json`.
- [X] T016 [US2] Add handling for "maximal overlap" edge cases where the agent sets `edge_case: true` and logs `Retrieval Precision = 0.0` to `data/results/experiment_log.csv` (main log) to ensure a single source of truth. **Prerequisite**: T022. **Instruction**: If mean pairwise similarity >= 0.95, set the `edge_case` flag in the log row and record precision as 0.0. **Verification**: Confirm `edge_case` flag exists in tasks.json and zero precision is recorded for edge cases in the main CSV.
- [X] T026 [US2] Add handling for "missing skill" edge cases where the agent fails gracefully, logs the missing skill ID, and records the failure without crashing.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Pruning Heuristic and Threshold Analysis (Priority: P3)

**Goal**: Apply a "Skill Pruning" heuristic to the active library after every few tasks and perform statistical analysis to determine if pruning mitigates performance degradation.

**Independent Test**: Run `code/analyze.py` on the full experiment data; verify output includes p-values for pruning efficacy, the "tipping point" breakpoint, and VIF < 5.0 for predictors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for pruning logic verifying skills with usage=0 and similarity < 0.70 are removed after 10 tasks in `tests/unit/test_pruning.py`
- [X] T030 [P] [US3] Unit test for statistical analysis verifying **Piecewise Linear Regression** output format in `tests/unit/test_analyze.py`

### Implementation for User Story 3

- [ ] T036 [US3] Create `code/run_baseline.py` to run the full experiment set with **pruning disabled** and save results to `data/results/experiment_log_baseline.csv`. **CRITICAL**: This run MUST iterate through the **exact 4 library sizes [10, 30, 50, 100]** as defined in FR-003 to ensure dimensional alignment with the pruning run for SC-003 comparison. **Instruction**: Generate the baseline log file independently. Do NOT perform comparison logic here; comparison is handled in T034. **Verification**: Confirm `experiment_log_baseline.csv` is generated with valid data matching the library sizes [10, 30, 50, 100]. **Prerequisite**: T021, T022, T023, T024, T026, T016.
- [ ] T036b [US3] Create `code/aggregate_baseline.py` to read `data/results/experiment_log_baseline.csv` and aggregate metrics (success rate, avg latency, avg precision) per library size into `data/results/baseline_metrics.json`. **Prerequisite**: T036. **Verification**: Confirm JSON output matches expected aggregation structure.
- [X] T032 [US3] Implement calculation of **Variance Inflation Factor (VIF)** in `code/analyze.py` for predictors "library size" and "semantic overlap" to confirm VIF < 5.0, output VIF values to a log/variable.
- [X] T045 [US3] **PRIMARY ANALYSIS**: Implement **Piecewise Linear Regression** (per Spec FR-005) in `code/analyze.py` to identify the "tipping point" library size (x0). **Calculate x0 by finding the breakpoint of the fitted piecewise linear model** using `statsmodels` or `scipy`. **Output the breakpoint parameter x0 to `data/results/tipping_point.json`**. **Verification**: Confirm x0 is calculated and saved. This is the **primary** method as mandated by the Spec.
- [X] T052 [US3] **Verify SC-004**: Implement a check in `code/analyze.py` that explicitly compares the calculated x0 from T045 (PLR) against the "tipping point" definition in the final report to ensure the success criterion is measured against the Spec's mandated primary method.
- [X] T034 [US3] Generate final report in `code/analyze.py` outputting the tipping point value (from T045), p-value for pruning efficacy, VIF metrics, and **performance recovery delta** (comparing aggregated pruned run metrics from `experiment_log.csv` against baseline metrics from `data/results/baseline_metrics.json`) to `data/results/final_analysis.json`. **Prerequisite**: T023, T036b, T045. **Instruction**: Aggregate pruned run metrics from `experiment_log.csv` directly in this task for comparison.
- [X] T035 [US3] Implement sensitivity analysis logic in `code/analyze.py` to sweep pruning thresholds across a range of **{5, 10, 20} tasks** (per Spec Assumptions) and verify robustness of the tipping point finding by **recalculating the tipping point for each sweep**. **For each sweep, verify VIF < 5.0** to ensure model validity. Output results to `data/results/sensitivity_report.json`. **Prerequisite**: T028, T023, T036, T036b. **Note**: The sweep range {5, 10, 20} is an implementation choice to verify robustness.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Update `README.md` with installation and run instructions.
- [ ] T053 [P] Update `quickstart.md` with end-to-end execution steps.
- [ ] T038 [P] Code cleanup and refactoring to ensure all random seeds are pinned. **Deliverable**: Generate `reproducibility_report.md` listing all pinned seeds and their sources.
- [ ] T039 [P] Performance optimization: Ensure embedding calculation for a scalable set of skills runs within memory constraints. (sample if necessary).
- [ ] T040 [P] Additional unit tests for edge cases in `tests/unit/`. **Specifically**: `test_maximal_overlap_handling` (verifying precision=0.0), `test_memory_limit` (verifying graceful failure), and `test_pruning_config` (verifying configurable interval).

---

## Phase 7: Revision & Analysis Resolution (Post-Review)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical validity, and execution order identified in the analysis phase.

- [ ] T041 [US3] **Statistical Validity**: Refine `code/analyze.py` to explicitly calculate and report the **Variance Inflation Factor (VIF)** for the "library size" and "semantic overlap" predictors. Add a hard assertion or warning if VIF >= 5.0, flagging the model as invalid due to collinearity as per FR-007 and SC-006. (Note: Logic already in T032, this task ensures final report includes it).
- [ ] T042 [US1] **Data Integrity**: Enhance `code/generate_data.py` to include a checksum validation step upon loading generated `tasks.json` and `skills.json`. **Algorithm**: SHA-256. **Storage**: Generate checksums to `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` upon write; validate against `state/projects/PROJ-975-llmxive-follow-up-extending-from-chatbot.yaml` (structure: `{ 'artifact_hashes': { 'tasks.json': 'sha256...', 'skills.json': 'sha256...' } }`) upon load. Raise an error immediately if checksums mismatch. **Verification**: Confirm validation logic works and error is raised on mismatch.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of all User Stories and receipt of analysis feedback

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
- **Compute Feasibility**: All tasks assume CPU-only execution with a limited core count and constrained RAM. No GPU or low-precision quantization is used.
- **Data Integrity**: No fake data generation; all data is synthetic but deterministic and grounded in the specified seeds.
- **Plan Correction Note**: The plan.md currently states "10 library sizes" but the spec mandates 4. This task list adheres to the spec (4 sizes). The plan.md requires a kickback to align with the spec.