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

- [X] T001a [P] Create directory structure: `code/`, `data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, `state/projects/PROJ-922`
- [X] T001b [P] Create `code/requirements.txt` pinning: `transformers==4.40.0`, `torch==2.2.0+cpu`, `llama-cpp-python==0.2.70`, `statsmodels==0.14.1`, `pandas==2.2.0`, `numpy==1.26.0`, `pytest==8.0.0`, `pyyaml==6.0.1`, `sympy==1.12`, `z3-solver==4.12.0`, `scikit-learn==1.4.0`, `datasets==2.18.0`
- [X] T002a [P] Create `code/scripts/update_state.py` to calculate checksums for all `data/` artifacts and update `state/projects/.../artifacts.yaml`. **Verification**: Script exists and successfully updates `artifacts.yaml` when run.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/config.py` for seed pinning (global seed=42), path management, and environment configuration
- [X] T005 [P] Implement `code/utils/logging.py` for structured logging (JSON format)
- [X] T006 [P] Implement `code/data_generation/profiles.py` to generate **10 synthetic expert profiles** (reduced scale per Plan). **Schema**: `{"id": str, "domain": str, "capability_rules": str, "behavior_keywords": [str]}`. **Domains**: coding, math, logic, creative, factual (A few profiles each). **Rules**: Capability rules define heuristic constraints. Behavior keywords define a set of style markers. **Validation Logic**: Must validate that every generated profile contains non-empty `capability_rules` and `behavior_keywords`; if a profile is malformed (missing keys), skip it, log an error, and proceed with remaining valid profiles.
- [X] T007 [P] Implement `code/data_generation/tasks.py` to generate a global pool of **50 stratified task scenarios** (reused across all profiles). **Domains**: A balanced set of coding, math, and logic tasks, alongside a larger set of creative/factual tasks.. **Logic**: Must validate that generated tasks do not contain ambiguous context that would prevent deterministic evaluation; if ambiguous, log and flag the specific task as "excluded" from Hallucination Rate calculation. **Dependency**: Requires valid profiles from T006 to ensure task context compatibility.
- [X] T007a [P] [US1] Implement `code/data_generation/tasks.py` (Part 1) to generate **coding tasks** with AST validation. **Edge Case**: Flag ambiguous contexts as excluded.
- [X] T007b [P] [US1] Implement `code/data_generation/tasks.py` (Part 2) to generate **A set of math tasks** with SymPy evaluation. **Edge Case**: Flag ambiguous contexts as excluded.
- [X] T007c [P] [US1] Implement `code/data_generation/tasks.py` (Part 3) to generate **logic tasks** with Z3 satisfiability. **Edge Case**: Flag ambiguous contexts as excluded.
- [X] T007d [P] [US1] Implement `code/data_generation/tasks.py` (Part 4) to generate **creative/factual tasks** with regex extraction. **Edge Case**: Flag ambiguous contexts as excluded. **Note**: This task contributes 20 to the global total of 50.
- [X] T008 [P] [P] Implement `code/inference/prompts.py` defining three distinct prompt templates with explicit text and placeholders:
 - **Monolithic**: `"[System: You are {domain_expert} who {behavior_keywords}. Task: {task}]"`
 - **Separated Tracks**: `"[System: Capability: {capability_rules}. Behavior: {behavior_keywords}. Task: {task}]"`
 - **Generic Baseline**: `"[System: You are a helpful assistant. Task: {task}]"`
- [X] T009 Implement `code/inference/engine.py` to load a quantized model (Llama or Phi-3-mini) on CPU-only backend with OOM protection and timeout handling

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-tractable LLM inference with decoupled prompt architecture (Priority: P1) 🎯 MVP

**Goal**: Load a small quantized model on CPU and generate responses for all profiles × multiple tasks × 3 conditions (Monolithic, Separated, Generic)

**Independent Test**: The system can be tested by running a single profile-task pair through all three conditions and verifying that the model generates text within 300 seconds without CUDA errors or OOM crashes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for prompt template generation in `tests/unit/test_prompts.py`
- [X] T011 [P] [US1] Integration test for single inference run in `tests/integration/test_inference_single.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/inference/engine.py` logic to: 1) Load quantized model using `llama-cpp-python` with `device="cpu"`, `n_gpu_layers=0`; 2) Implement a **strict -second timeout handler** (configurable, default 300s as per spec US-1) and OOM exception catching for CPU runs; 3) Return output string or error code. **Must support all 3 conditions**: Monolithic, Separated Tracks, and Generic Baseline.
- [X] T014a [US1] Implement `code/scripts/run_inference.py` to segment workload into parallel jobs (one per condition: Monolithic, Separated, Generic) to fit within 3600s CI limits. Each job processes a batch of tasks (multiple profiles × a fixed number of tasks).
- [X] T014b [US1] Implement logic in `run_inference.py` to iterate over all profiles, tasks, and conditions using the segmented jobs. **Scale**: 10 profiles × 50 tasks × 2 conditions = 1,000 runs. Save outputs to `data/interim/inference_outputs.jsonl` with schema `{profile_id, task_id, condition, latency, success_flag, output_text}`. **Verification**: File exists and contains **1000 rows**.
- [X] T015 [US1] Add logging for inference status (start, progress, completion, failures) in `run_inference.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate outputs against deterministic ground-truth rules (Priority: P2)

**Goal**: Calculate Heuristic Adherence, Style Consistency, and Hallucination Rate using rule-based logic (no LLM judges)

**Independent Test**: The evaluation script can be tested independently by feeding it a known "gold standard" response and a known "hallucinated" response to verify that the metrics match expected binary values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for Heuristic Adherence logic in `tests/unit/test_metrics.py`
- [X] T018 [P] [US2] Contract test for Hallucination detection logic in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/evaluation/validators.py` with specific mapping: Code tasks -> AST parser; Math tasks -> SymPy evaluator; Logic tasks -> Z3 solver; Creative/Factual -> Regex/NLI checks. **Edge Case**: Must handle inputs from malformed profiles or ambiguous contexts by skipping and logging, consistent with T006/T007.
- [X] T020 [US2] Implement `code/evaluation/metrics.py` Heuristic Adherence calculation: 1 if task solved (validator pass), 0 otherwise.
- [X] T021a [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation (Part 1): Regex extraction of entity-value pairs (`\b(\w+): (\w+)\b`).
- [X] T021b [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation (Part 2): **Multi-hop reasoning check**: Use logic verification (e.g., Z3/SymPy) to validate if inferred facts require multi-step deduction not present in context.
- [X] T021c [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation (Part 3): Compare extracted facts against external source traces; if fact not in context OR requires invalid multi-hop inference, increment hallucination counter.
- [X] T022 [US2] Implement `code/evaluation/metrics.py` Style Consistency calculation: 1) Count occurrences of behavior track keywords (from profile) in output; 2) Calculate frequency ratio; 3) Match against structure rules (e.g., "must start with greeting").
- [X] T023 [US2] Implement `code/scripts/evaluate.py` to process `data/interim/inference_outputs.jsonl` and generate `data/interim/evaluation_scores.jsonl` with schema `{profile_id, task_id, condition, heuristic_adherence, hallucination_rate, style_consistency}`. **Verification**: File exists and contains **1000 rows**.
- [X] T024 [US2] Implement sensitivity analysis logic for Style Consistency threshold (FR-008) by **iterating over the a range of significance levels, including a stringent threshold**, calculating false-positive rates for each, and reporting the variance. **Output**: Save `data/processed/sensitivity_analysis.json` containing the variance in false-positive rates for each threshold.
- [X] T025 [US2] Add error handling for malformed profiles/tasks (skip and log) and ambiguous context (flag as excluded). **Logic**: Implement detection to skip malformed input data (missing capability/behavior keys) and flag ambiguous contexts as excluded from Hallucination Rate calculation to prevent false positives, as required by spec Edge Cases.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate results and perform statistical comparison (Priority: P3)

**Goal**: Aggregate scores and fit a Generalized Linear Mixed Model (GLMM) to test for significant differences between conditions

**Independent Test**: The analysis pipeline can be tested by running a simulation with synthetic data where the "Separated" condition is known to have a lower hallucination rate, verifying that the GLMM returns a significant fixed effect.

**Note on Spec/Plan Mismatch**: The current `spec.md` (FR-006) mandates a "Linear Mixed-Effects Model (LMM)", while the `plan.md` and implementation tasks mandate a "Generalized Linear Mixed Model (GLMM)" to handle binary outcomes. Task T026a is added to formally update `spec.md`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026a [P] [US3] Implement `code/scripts/update_spec.py` (or manual step) to **update `spec.md` FR-006** to replace "Linear Mixed-Effects Model (LMM)" with "Generalized Linear Mixed Model (GLMM)" and document the rationale for binary outcomes.
- [X] T026b [P] [US3] Unit test for GLMM fitting logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T027 [US3] Implement `code/analysis/stats.py` to load `data/interim/evaluation_scores.jsonl` (Output of T023). **Input**: T023 output. **Dependency**: Verify `data/interim/evaluation_scores.jsonl` exists before proceeding. Aggregate into a DataFrame. **Output**: Save `data/interim/aggregated_data.csv`. **Verification**: File exists and contains **1000 rows**.
- [X] T028 [US3] Implement `code/analysis/stats.py` GLMM fitting with random intercepts for Profile and Task for Heuristic Adherence, Hallucination Rate, and Style Consistency. **Output**: Save model summary to `data/processed/glm_results.json`. **Verification**: File exists and contains p-values for fixed effects.
- [X] T029 [US3] Implement Bonferroni (or Holm-Bonferroni) correction for multiple comparisons across metrics (FR-007) for all 3 conditions. **Output**: Update `data/processed/glm_results.json` with `corrected_p_value` field for each metric.
- [X] T030 [US3] Implement `code/analysis/plots.py` to generate figures for the paper. **Output**: Generate `data/processed/figures/effect_sizes.png`, `data/processed/figures/p_values.png`, and `data/processed/figures/confidence_intervals.png`. **Verification**: All three PNG files exist in the directory.
- [X] T031 [US3] Create `code/scripts/analyze.py` to run the full analysis pipeline and output `data/processed/final_results.csv` (aggregated metrics) and `data/processed/analysis_report.md` (summary of findings). **Verification**: Both files exist and contain expected headers/sections.
- [X] T032 [US3] Verify that the direction of effect aligns with the hypothesis (Separated < Monolithic for Hallucination Rate). **Output**: Write `code/scripts/verify_hypothesis.py` that checks `Separated < Monolithic` in `data/processed/glm_results.json` and outputs `data/processed/hypothesis_verification.json` with `status: PASS/FAIL`. **Verification**: JSON file exists with status field.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `specs/001-llmxive-follow-up-extending-colleague-sk/quickstart.md`: Add "Setup" section with install commands, "Inference" section with run examples, "Evaluation" section with metric definitions. **Verification**: File contains all three sections with code blocks.
- [X] T034 Code cleanup and refactoring of `code/evaluation/metrics.py`: Refactor to use Strategy Pattern for validators; add unit tests in `tests/unit/test_metrics.py` for edge cases (empty input, null context). **Verification**: Refactored code exists and all new tests pass.
- [X] T035 Performance optimization for inference pipeline: Target metric: reduce latency by [deferred] compared to T012 baseline. Method: Implement batch inference in `engine.py` to process a batch of tasks. **Verification**: Benchmark script `tests/benchmark_batch.py` shows [deferred] reduction.
- [X] T036 [P] Additional unit tests in `tests/unit/` for edge cases: empty input, null context, malformed JSON in `profiles.py` and `tasks.py`. **Verification**: All new tests pass and cover specified edge cases.
- [X] T037 [P] Run `code/scripts/update_state.py` (created in T002a) to update `state/projects/.../artifacts.yaml` checksums. **Verification**: Script exists and successfully updates `artifacts.yaml`.

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
- **Scale Note**: This project uses a reduced scale of 10 profiles × 50 tasks × 2 conditions = 1,000 runs for CI feasibility, as defined in the Plan's Statistical Power section.