# Tasks: llmXive follow-up: extending "COLLEAGUE.SKILL: Automated AI Skill Generation via Expert Knowledge Di"

**Input**: Design documents from `/specs/001-llmxive-skill-separation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
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

- [ ] T001a [P] Create directory structure: `code/`, `data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, `state/projects/PROJ-922`
- [ ] T001b [P] Create `code/requirements.txt` pinning: `transformers==4.40.0`, `torch==2.2.0+cpu`, `llama-cpp-python==0.2.70`, `statsmodels==0.14.1`, `pandas==2.2.0`, `numpy==1.26.0`, `pytest==8.0.0`, `pyyaml==6.0.1`, `sympy==1.12`, `z3-solver==4.12.0`, `scikit-learn==1.4.0`, `datasets==2.18.0`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/config.py` for seed pinning (global seed=42), path management, and environment configuration
- [ ] T005 [P] Implement `code/utils/logging.py` for structured logging (JSON format)
- [ ] T006 [P] Implement `code/data_generation/profiles.py` to generate 50 synthetic expert profiles. **Schema**: `{"id": str, "domain": str, "capability_rules": str, "behavior_keywords": [str]}`. **Domains**: coding, math, logic, creative, factual (10 profiles each). **Rules**: Capability rules define heuristic constraints. Behavior keywords define a set of style markers.
- [ ] T007 Implement `code/data_generation/tasks.py` to generate 200 stratified task scenarios (A representative sample of instances per domain.: coding, math, logic, creative, factual). **Logic**: Coding tasks require AST validation; Math tasks require SymPy evaluation; Logic tasks require Z3 satisfiability; Creative/Factual require regex extraction. **Dependency**: Must run AFTER T006 to ensure task pool is stratified against the generated profile domains.
- [ ] T008 [P] Implement `code/inference/prompts.py` defining three distinct prompt templates with explicit text and placeholders:
  - **Monolithic**: `"[System: You are {domain_expert} who {behavior_keywords}. Task: {task}]"`
  - **Separated Tracks**: `"[System: Capability: {capability_rules}. Behavior: {behavior_keywords}. Task: {task}]"`
  - **Generic Baseline**: `"[System: You are a helpful assistant. Task: {task}]"`
- [ ] T009 Implement `code/inference/engine.py` to load a quantized model (Llama-8B-Q4 or Phi-3-mini) on CPU-only backend with OOM protection and timeout handling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-tractable LLM inference with decoupled prompt architecture (Priority: P1) 🎯 MVP

**Goal**: Load a small quantized model on CPU and generate responses for all profiles × multiple tasks × 3 conditions (Monolithic, Separated, Generic)

**Independent Test**: The system can be tested by running a single profile-task pair through all three conditions and verifying that the model generates text within 300 seconds without CUDA errors or OOM crashes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for prompt template generation in `tests/unit/test_prompts.py`
- [ ] T011 [P] [US1] Integration test for single inference run in `tests/integration/test_inference_single.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/inference/engine.py` logic to: 1) Load quantized model using `llama-cpp-python` with `device="cpu"`, `n_gpu_layers=0`; 2) Implement timeout handler (configurable limit) and OOM exception catching for CPU runs; 3) Return output string or error code. **Must support all 3 conditions**: Monolithic, Separated Tracks, and Generic Baseline.
- [ ] T014a [US1] Implement `code/scripts/run_inference.py` to segment workload into parallel jobs (one per condition: Monolithic, Separated, Generic) to fit within 3600s CI limits. Each job processes a batch of tasks (multiple profiles × a fixed number of tasks).
- [ ] T014b [US1] Implement logic in `run_inference.py` to iterate over all profiles, tasks, and conditions using the segmented jobs. Save outputs to `data/interim/inference_outputs.jsonl` with metadata (profile_id, task_id, condition, latency, success_flag).
- [ ] T015 [US1] Add logging for inference status (start, progress, completion, failures) in `run_inference.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate outputs against deterministic ground-truth rules (Priority: P2)

**Goal**: Calculate Heuristic Adherence, Style Consistency, and Hallucination Rate using rule-based logic (no LLM judges)

**Independent Test**: The evaluation script can be tested independently by feeding it a known "gold standard" response and a known "hallucinated" response to verify that the metrics match expected binary values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for Heuristic Adherence logic in `tests/unit/test_metrics.py`
- [ ] T018 [P] [US2] Contract test for Hallucination detection logic in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/evaluation/validators.py` with specific mapping: Code tasks -> AST parser; Math tasks -> SymPy evaluator; Logic tasks -> Z3 solver; Creative/Factual -> Regex/NLI checks.
- [ ] T020 [US2] Implement `code/evaluation/metrics.py` Heuristic Adherence calculation: 1 if task solved (validator pass), 0 otherwise.
- [ ] T021 [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation: 1) Regex extraction of entity-value pairs (`\b(\w+): (\w+)\b`); 2) **Multi-hop reasoning check**: Use logic verification (e.g., Z3/SymPy) to validate if inferred facts require multi-step deduction not present in context; 3) Compare extracted facts against external source traces; if fact not in context OR requires invalid multi-hop inference, increment hallucination counter.
- [ ] T022 [US2] Implement `code/evaluation/metrics.py` Style Consistency calculation: 1) Count occurrences of behavior track keywords (from profile) in output; 2) Calculate frequency ratio; 3) Match against structure rules (e.g., "must start with greeting").
- [ ] T023 [US2] Implement `code/scripts/evaluate.py` to process `data/interim/inference_outputs.jsonl` and generate `data/interim/evaluation_scores.jsonl`.
- [ ] T024 [US2] Implement sensitivity analysis logic for Style Consistency threshold (FR-008) by sweeping the threshold over a set of values (e.g., low to moderate magnitudes) and reporting the variance in false-positive rates to ensure robustness. **Output**: Save `data/processed/sensitivity_analysis.json` containing the variance in false-positive rates for each threshold.
- [ ] T025 [US2] Add error handling for malformed profiles/tasks (skip and log) and ambiguous context (flag as excluded).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate results and perform statistical comparison (Priority: P3)

**Goal**: Aggregate scores and fit a Generalized Linear Mixed Model (GLMM) to test for significant differences between conditions

**Independent Test**: The analysis pipeline can be tested by running a simulation with synthetic data where the "Separated" condition is known to have a lower hallucination rate, verifying that the GLMM returns a significant fixed effect.

**Note on Spec/Plan Mismatch**: The current `spec.md` (FR-006) mandates a "Linear Mixed-Effects Model (LMM)", while the `plan.md` and implementation tasks mandate a "Generalized Linear Mixed Model (GLMM)" to handle binary outcomes. This discrepancy requires a formal specification revision (outside the scope of this tasks file) to update FR-006. The tasks below implement GLMM as per the Plan.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for GLMM fitting logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analysis/stats.py` to load `data/interim/evaluation_scores.jsonl` (Output of T023). **Input**: T023 output. **Dependency**: Verify `data/interim/evaluation_scores.jsonl` exists before proceeding. Aggregate into a DataFrame.
- [ ] T028 [US3] Implement `code/analysis/stats.py` GLMM fitting with random intercepts for Profile and Task for Heuristic Adherence, Hallucination Rate, and Style Consistency. **Note**: This implements GLMM as per the Plan; Spec FR-006 (LMM) is currently out of sync and requires external revision.
- [ ] T029 [US3] Implement Bonferroni (or Holm-Bonferroni) correction for multiple comparisons across metrics (FR-007) for all 3 conditions.
- [ ] T030 [US3] Implement `code/analysis/plots.py` to generate figures for the paper (effect sizes, p-values, confidence intervals).
- [ ] T031 [US3] Create `code/scripts/analyze.py` to run the full analysis pipeline and output `data/processed/final_results.csv` and `data/processed/analysis_report.md`.
- [ ] T032 [US3] Verify that the direction of effect aligns with the hypothesis (Separated < Monolithic for Hallucination Rate).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `specs/001-llmxive-follow-up-extending-colleague-sk/quickstart.md`: Add "Setup" section with install commands, "Inference" section with run examples, "Evaluation" section with metric definitions.
- [ ] T034 Code cleanup and refactoring of `code/evaluation/metrics.py`: Refactor to use Strategy Pattern for validators; add unit tests for edge cases (empty input, null context).
- [ ] T035 Performance optimization for inference pipeline: Target metric: reduce latency by a significant margin via batching. Method: Implement batch inference in `engine.py` to process multiple tasks at a time.
- [ ] T036 [P] Additional unit tests in `tests/unit/` for edge cases
- [ ] T037 Run `scripts/update_state.py` to update `state/projects/.../artifacts.yaml` checksums

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires outputs from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires outputs from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Validators before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T007 which depends on T006)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for prompt templates in tests/unit/test_prompts.py"
Task: "Integration test for single inference run in tests/integration/test_inference_single.py"

# Launch all models for User Story 1 together:
Task: "Create profiles.py in code/data_generation/profiles.py"
Task: "Create tasks.py in code/data_generation/tasks.py"
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
   - Developer A: User Story 1 (Inference)
   - Developer B: User Story 2 (Evaluation)
   - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T007 which depends on T006)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence