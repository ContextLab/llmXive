# Tasks: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-appo-agentic/`
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

- [ ] T001 [P] Create the project root directory: `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/`
- [ ] T002 [P] Create core subdirectories: `code/`, `data/`, `tests/` inside the project root
- [ ] T003 [P] Create analysis subdirectories: `contracts/`, `data/results/` inside the project root
- [ ] T004 [P] Create documentation subdirectories: `docs/`, `state/` inside the project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Initialize Python 3.11 project with `transformers`, `torch`, `datasets`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `statsmodels`, `accelerate`, `pytest`, `pytest-timeout` in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/requirements.txt`
- [ ] T006 [P] Configure linting and formatting tools (ruff, black) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/`
- [ ] T011 [P] Create base schema definitions in YAML format in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/contracts/` with exact fields:
    - `Reasoning Trace`: `task_id`, `tokens`, `static_scores`, `dynamic_scores`
    - `Branching Score`: `task_id`, `position`, `score`, `type` (static/dynamic)
    - `Correlation Result`: `pearson`, `spearman`, `p_value`, `seeds`, `inconclusive_flag`
    **Dependency**: T011 must be completed before T008, T014, and T017 can be written.
- [ ] T008 [P] Implement preprocessing utility to tokenize traces and align data structures in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/data/preprocess.py` (consumes schema from T011)
- [ ] T007 [P] Implement data download utility to fetch GSM8K (dataset ID: `openai/gsm8k`) and MATH (dataset ID: `hendrycks/math`) datasets from verified HuggingFace URLs into `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/data/download.py`
- [ ] T009 [P] Setup configuration management for random seeds, model paths, and hardware constraints (CPU-only enforcement) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/utils/config.py`
- [ ] T010 [P] Implement logging infrastructure and progress bars for long-running tasks in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/utils/logger.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Static Branching Scores (Priority: P1) 🎯 MVP

**Goal**: Compute Static Branching Scores (KL divergence) for a sampled subset of GSM8K/MATH using a frozen model on CPU.

**Independent Test**: Load a small batch of tasks, run static scoring on CPU, verify JSON output of score vectors without CUDA allocation.

### Tests for User Story 1

- [ ] T012 [P] [US1] Unit test for probability clamping (floor set to a small positive value) to prevent NaN in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/unit/test_static_score.py`
- [ ] T013 [P] [US1] Integration test for CPU-only inference pass using `microsoft/phi-2` (no CUDA errors) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_static_inference.py`
- [ ] T014 [P] [US1] Contract test verifying output JSON structure matches `contracts/output_schema.yaml` (requires T011 completion) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/contract/test_static_output.py`

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement `compute_kl_divergence` function in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/static_score/compute.py` (handles top-k uniform distribution comparison)
- [ ] T016 [US1] Implement `StaticScorer` class in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/static_score/compute.py` (loads `microsoft/phi-2` by default in default precision, CPU device; fallback to `meta-llama/Llama-3-8B` if specified)
- [ ] T017 [US1] Implement batch processing loop to generate `data/processed/static_scores.json` for the sampled subset
- [ ] T018 [US1] Add logic to monitor timing and log warnings if >5 mins per task (do not fail the task if >5 mins, per Edge Cases)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Dynamic APPO Branching Scores (Priority: P2)

**Goal**: Generate Dynamic Branching Scores (cumulative binary reward from rollouts) for a representative set of tasks using pre-trained APPO policy.

**Independent Test**: Run APPO rollout on fixed tasks, verify dynamic score recorded based on policy likelihood gains and binary correctness.

### Tests for User Story 2

- [ ] T019 [P] [US2] Contract test for dynamic score output structure (aligned with static) (requires T011 completion) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/contract/test_dynamic_output.py`
- [ ] T020 [P] [US2] Integration test for rollout simulation (no training, inference only) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_appo_rollout.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement stratified random sampling of a representative set of tasks from GSMK/MATH based on difficulty (stratify by problem length/token count into short/medium/long bins) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/dynamic_score/run_appo.py`
- [ ] T022 [P] [US2] Implement `run_appo_rollout` function in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/dynamic_score/run_appo.py` (uses pre-trained fine-tuned policy, consumes the stratified random subset of 500 tasks generated by T021, ensuring exact task ID alignment)
- [ ] T023 [US2] Implement cumulative binary reward calculation (1 for correct, 0 for incorrect) as defined in Plan's Critical Methodological Clarifications in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/dynamic_score/run_appo.py`
- [ ] T024 [US2] Generate `data/processed/dynamic_scores.json` with aligned task IDs and decision points
- [ ] T025 [US2] Handle failure cases: record negative likelihood gain or failure state when policy fails to find solution

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Significance Testing (Priority: P3)

**Goal**: Align scores, compute correlations, run permutation tests (n=3, timeout 5.5h, 10k iterations), and generate residual analysis.

**Independent Test**: Feed dummy datasets with r=1.0, verify output reports r≈1.0 and p-value < 0.05.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for alignment logic (truncation/exclusion <80% overlap) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/unit/test_alignment.py`
- [ ] T027 [P] [US3] Unit test for permutation test timeout handling and "inconclusive" flagging in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/unit/test_permutation.py`
- [ ] T028 [P] [US3] Integration test for full correlation pipeline with known dummy data, running **[deferred] iterations per seed** across **n=3 seeds** to validate timeout and p-value stability in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/tests/integration/test_correlation_pipeline.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `align_scores` function in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py` (handles token position alignment, truncate to length of shorter trace, exclude if overlap < 80%)
- [ ] T030 [US3] Implement Pearson and Spearman correlation calculation in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py`
- [ ] T031 [US3] Implement Permutation Test with hard timeout (5.5h), early stopping (p-value stable <0.001), **n=3 seed runs**, and **[deferred] iterations per run** (targeting the count required by Constitution Principle VI); if timeout triggers before [deferred] iterations, set inconclusive=True in result object and report partial p-value in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py`
- [ ] T032 [US3] Implement Linear Mixed-Effects Model (LMM) with **task_id as random effect** using `statsmodels` as secondary validation (primary analysis is permutation test) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/correlation.py`
- [ ] T033 [US3] Implement reasoning pattern classifier (fine-tuned BERT on GSM8K labels, e.g., `bert-base-uncased` fine-tuned on GSM8K reasoning labels with taxonomy: arithmetic, algebra, geometry, other) including a validation step for Verified Accuracy (must achieve >85% accuracy on held-out GSM8K set; block execution if not met) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/code/analysis/residuals.py`
- [ ] T034 [US3] Generate Residual Analysis Report (visualization + summary) in `projects/PROJ-861-llmxive-follow-up-extending-appo-agentic/data/results/residual_report.md`
- [ ] T035 [US3] Output final `data/results/correlation_results.csv` with coefficients, p-values, and stability flags

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `docs/` including `quickstart.md` for CPU-only execution
- [ ] T037 [P] Add memory profiling code to T017 and T024 to verify memory usage <7 GB peak
- [ ] T038 [P] Add memory check assertion to verify <7 GB peak usage in test suite
- [ ] T039 Performance optimization for static inference and permutation test loops
- [ ] T040 [P] Additional unit tests for edge cases (numerical instability, trace length mismatches) in `tests/unit/`
- [ ] T041 Run quickstart.md validation to ensure end-to-end reproducibility on free-tier CI

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
- **Critical Constraint**: Permutation tests must respect the 5.5h timeout and flag "inconclusive" if not completed.
- **Critical Constraint**: Permutation tests MUST target 10,000 iterations per seed run as per Constitution Principle VI.