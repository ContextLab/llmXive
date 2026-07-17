# Tasks: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [X] T002 [P] Create a `scaffold.py` script in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/utils/scaffold.py` that generates the core directory structure: `code/`, `data/`, `contracts/`, `data/results/`, `docs/`, `state/`, `tests/`, `src/`. The script MUST verify the project root directory exists before creating subdirectories.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/requirements.txt` with pinned versions for `transformers`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `statsmodels`, `accelerate`, `pytest`, `pytest-timeout`, `memory_profiler`. MUST include `torch --index-url to ensure CPU-only compatibility.
- [ ] T006 [P] Configure linting and formatting tools (ruff, black) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/`.
- [ ] T011 [P] Create `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/contracts/output_schema.yaml` containing the full YAML definition for `ReasoningTrace`, `BranchingScore`, and `CorrelationResult` with explicit types, constraints, and required fields:
 - `Reasoning Trace`: `task_id` (str), `tokens` (list), `static_scores` (list), `dynamic_scores` (list)
 - `Branching Score`: `task_id` (str), `position` (int), `score` (float), `type` (str: static/dynamic)
 - `Correlation Result`: `pearson` (float), `spearman` (float), `p_value` (float), `seeds` (list), `inconclusive_flag` (bool)
- [X] T008 [P] Implement preprocessing utility to tokenize traces and align data structures in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/data/preprocess.py` (consumes schema from T011).
- [X] T007 [P] Implement data download utility to fetch GSM8K (dataset ID: `openai/gsm8k`) and MATH (dataset ID: `hendrycks/math`) datasets from verified HuggingFace URLs into `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/data/download.py`.
- [X] T009 [P] Setup configuration management for random seeds, model paths, and hardware constraints (CPU-only enforcement) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/utils/config.py`.
- [X] T010 [P] Implement logging infrastructure and progress bars for long-running tasks in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/utils/logger.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Static Branching Scores (Priority: P1) 🎯 MVP

**Goal**: Compute Static Branching Scores (KL divergence) for a sampled subset of GSM8K/MATH using a frozen model on CPU.

**Independent Test**: Load a small batch of tasks, run static scoring on CPU, verify JSON output of score vectors without CUDA allocation.

### Tests for User Story 1

- [X] T012 [P] [US1] Unit test for probability clamping (floor set to 1e-9) to prevent NaN in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/unit/test_static_score.py`.
- [X] T013 [P] [US1] Integration test for CPU-only inference pass using `microsoft/phi-2` (no CUDA errors) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_static_inference.py`.
- [X] T014 [P] [US1] Contract test verifying output JSON structure matches `contracts/output_schema.yaml` (requires T011 completion) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/contract/test_static_output.py`.

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `compute_kl_divergence` function in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/static_score/compute.py` (handles top-k uniform distribution comparison).
- [X] T016 [US1] Implement `StaticScorer` class in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/static_score/compute.py` (loads `microsoft/phi-2` by default in default precision, CPU device; **MUST implement epsilon smoothing factor of 1e-9** to handle log(0) scenarios as per Spec Edge Cases; fallback to `meta-llama/Llama-3-8B` if specified).
- [ ] T017 [US1] Implement batch processing loop to generate `data/processed/static_scores.json` for the **sampled subset of tasks** (matching the dynamic subset size for alignment). **Requires T016**.
- [ ] T018 [US1] Add logic to monitor timing and enforce exclusion: if a task exceeds a reasonable duration threshold, it MUST be excluded from the dataset, logged as "TIMEOUT_EXCLUDED", and if the exclusion rate exceeds a predefined threshold, the process must exit with code 1 and log "RESOURCE_LIMIT_EXCEEDED".

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Dynamic APPO Branching Scores (Priority: P2)

**Goal**: Generate Dynamic Branching Scores (cumulative binary reward from rollouts) for a representative set of tasks using the APPO algorithm with online rollouts.

**Independent Test**: Run APPO rollout on fixed tasks, verify dynamic score recorded based on policy likelihood gains and binary correctness.

### Tests for User Story 2

- [X] T019 [P] [US2] Contract test for dynamic score output structure (aligned with static) (requires T011 completion) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/contract/test_dynamic_output.py`.
- [X] T020 [P] [US2] Integration test for rollout simulation (no training, inference only) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_appo_rollout.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement stratified random sampling of a representative set of tasks from GSM8K/MATH based on difficulty (stratify by problem length/token count into bins: `tokens < 50`, `50 <= tokens <= 100`, `tokens > 100`) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/dynamic_score/run_appo.py`.
- [X] T022 [US2] Implement `run_appo_rollout` function in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/dynamic_score/run_appo.py` (uses APPO algorithm to execute **online rollouts** on the stratified random subset of exactly 50 tasks generated by T021, ensuring exact task ID alignment; **MUST NOT use pre-trained inference only**). **Requires T021**.
- [X] T023 [US2] Implement cumulative binary reward calculation (1 for correct, 0 for incorrect) as defined in Plan's Critical Methodological Clarifications in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/dynamic_score/run_appo.py`.
- [X] T024 [US2] Generate `data/processed/dynamic_scores.json` with aligned task IDs and decision points.
- [ ] T025 [US2] Handle failure cases: record negative likelihood gain or failure state when policy fails to find solution.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Significance Testing (Priority: P3)

**Goal**: Align scores, compute correlations, run permutation tests (target a sufficient number of iterations, with a minimum threshold), and generate residual analysis.

**Independent Test**: Feed dummy datasets with r=1.0, verify output reports r≈1.0 and p-value < 0.05.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for alignment logic (truncation/exclusion <80% overlap) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/unit/test_alignment.py`.
- [X] T027 [P] [US3] Unit test for permutation test timeout handling and "inconclusive" flagging in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/unit/test_permutation.py`.
- [ ] T028 [P] [US3] Integration test for full correlation pipeline with known dummy data, running **[deferred] iterations** per seed across **n=3 seeds** to validate timeout and p-value stability in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_correlation_pipeline.py`.

### Implementation for User Story 3

- [ ] T029b [US3] Implement Dynamic Time Warping (DTW) algorithm for sequence alignment in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py` as mandated by FR-003. **Output**: `data/processed/dtw_alignment_matrix.json`.
- [ ] T029 [US3] Implement `align_scores` function in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py` (handles token position alignment using DTW output from T029b; **Requires T017, T024, T029b**).
- [ ] T030 [US3] Implement Pearson and Spearman correlation calculation **AND** the **Ljung-Box test for autocorrelation** on residual error distribution in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py`.
- [ ] T031 [US3] Implement Permutation Test with hard timeout (5.5h) and **target of [deferred] iterations** (minimum 5,000); **MUST complete minimum 5,000 iterations before timeout check**; if [deferred] iterations complete before timeout, report full p-value; if timeout triggers before [deferred] but after [deferred], set inconclusive=True and report partial p-value; if timeout triggers before [deferred], fail with error in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py`. **Requires T029, T030**.
- [ ] T032 [US3] Implement **Ljung-Box test logic** for residual error distribution to validate the "random noise" assumption (SC-005) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/residuals.py`.
- [ ] T034 [US3] Generate Residual Analysis Report (visualization + summary) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/data/results/residual_report.md` containing Ljung-Box test results only.
- [ ] T035 [US3] Output final `data/results/correlation_results.csv` with coefficients, p-values, and stability flags.
- [ ] T035b [US3] Implement verification logic to assert that the correlation coefficient meets the SC-001 threshold (>0.7) and flag the result as "feasible" or "infeasible" in the output artifact.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including `quickstart.md` for CPU-only execution.
- [ ] T037 [P] Add memory profiling code to `code/static_score/compute.py` and `code/dynamic_score/run_appo.py` using `memory_profiler` with `@profile` decorator to verify memory usage <7 GB peak.
- [ ] T038 [P] Add memory check assertion using `memory_profiler` to verify <7 GB peak usage in `code/static_score/compute.py` and `code/dynamic_score/run_appo.py` in test suite.
- [ ] T039 Performance optimization for static inference and permutation test loops.
- [ ] T040 [P] Additional unit tests for edge cases (numerical instability, trace length mismatches) in `tests/unit/`.
- [ ] T041 Run quickstart.md validation to ensure end-to-end reproducibility on free-tier CI.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 and US2 for alignment

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
Task: "Contract test for static output in tests/contract/test_static_output.py"
Task: "Integration test for static inference in tests/integration/test_static_inference.py"

# Launch all implementation for User Story 1 together:
Task: "Implement compute_kl_divergence in code/static_score/compute.py"
Task: "Implement StaticScorer class in code/static_score/compute.py"
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
- **Critical Constraint**: All model loading must explicitly use `device="cpu"` and default precision (no 8-bit/4-bit quantization).
- **Critical Constraint**: Permutation tests must respect the 5.5h timeout and flag "inconclusive" if not completed, but MUST meet the minimum 5,000 iteration count and target [deferred].
- **Critical Constraint**: Dynamic score generation is limited to a manageable number of tasks to meet the runtime constraint.
- **Critical Constraint**: T022 must execute online rollouts, not inference only.
- **Critical Constraint**: T029/T029b must implement DTW as per FR-003.