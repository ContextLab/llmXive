---
description: "Task list template for feature implementation"
---

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

## Phase 0: Critical Spec Amendment (Prerequisite for All Analysis)

**Purpose**: Formally amend the specification to authorize the statistical method and scope required for the feasible run, ensuring Single Source of Truth compliance.

- [ ] T000a [P] **SPEC AMENDMENT DEFINITION**: Define the exact text block to be inserted into `specs/001-llmxive-follow-up-extending-colleague-sk/spec.md` to:
 1. Amend FR-006: Replace "Linear Mixed-Effects Model (LMM)" with "Generalized Linear Mixed Model (GLMM)" to support binary/continuous mixed outcomes.
 2. Amend Assumptions (Scale): Update the assumption regarding sample size from "50 profiles × 200 tasks" to "10 profiles × 50 tasks" (500 combinations × 3 conditions = 1,500 runs) to ensure GLMM convergence within CI limits.
 3. Rationale: The full matrix (a comprehensive set of runs) exceeds the runtime and RAM constraints of the free-tier runner.; the reduced scale is statistically powered for a moderate effect size (Cohen's d) with sufficient random-effect levels.
 **Verification**: Text block is defined and ready for insertion.

- [ ] T000b [P] **SPEC AMENDMENT APPLICATION**: Update `specs/001-llmxive-follow-up-extending-colleague-sk/spec.md` to reflect the changes defined in T000a.
 **Action**: Insert the exact text block from T000a into FR-006 and the Assumptions section.
 **Verification**: `spec.md` reflects the GLMM method and the reduced scale (10 profiles, 50 tasks).
 **Dependency**: Must be the first task executed; ALL downstream tasks (T004c, T028, etc.) depend on this being completed and verified. **This is a hard blocking gate.**

---

## Phase 1: Setup & Specification Alignment (Shared Infrastructure)

**Purpose**: Project initialization, dependency pinning, and configuration setup.

- [X] T001a [P] Create directory structure: `code/`, `data/raw`, `data/interim`, `data/processed`, `tests/unit`, `tests/integration`, `state/projects/PROJ-922`
- [X] T001b [P] Create `code/requirements.txt` pinning: `transformers==4.40.0 `, `torch==2.2.0+cpu `, `{{claim:c_53fa4f89}} (pi, https://en.wikipedia.org/wiki/Pi)`, `statsmodels==0.14.1 `, `pandas==2.2.0 `, `numpy==1.26.0 `, `pytest==8.0.0 `, `pyyaml==6.0.1 `, `sympy==1.12 `, `z3-solver==4.12.0 `, `{{claim:c_4c3c2059}}`, `{{claim:c_5266d6d5}}`
- [X] T002a [P] Create `code/scripts/update_state.py` to calculate checksums for all `data/` artifacts and update `state/projects/.../artifacts.yaml`. **Verification**: Script exists and successfully updates `artifacts.yaml` when run.
- [X] T004 [P] Implement `code/utils/config.py` for seed pinning (global seed=42), path management, and environment configuration.
- [X] T004b [P] [SC-002] Create/Update `code/utils/config.py` to explicitly define `NON_INFERIORITY_MARGIN = 0.05 ` (5 percentage points) as per SC-002. **Justification**: This value is the predefined constant derived from SC-002's requirement for a "small, predefined absolute percentage point threshold". **Verification**: File exists and contains the constant with docstring. **Dependency**: None (Setup phase).
- [X] T004c [P] [FR-006] **SPEC REFERENCE**: Update `code/utils/config.py` to import `GLMM_AUTHORIZED = True` referencing T000b. **Verification**: Config reflects T000b amendment. **Dependency**: T000b (Spec Amendment Application).

---

## Phase 2: Foundational (Blocking Prerequisites & Safety Gates)

**Purpose**: Core infrastructure, data generation, and **mandatory pre-flight safety checks** that MUST complete before ANY user story implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 [P] Implement `code/utils/logging.py` for structured logging (JSON format)
- [X] T038 [P] [FR-030] **SAFETY GATE**: Implement `code/scripts/verify_data_source.py` to validate the existence and integrity of the "expert profiles" source (real or simulated). **Logic**: Must raise an exception if the source is inaccessible or malformed, preventing any downstream data generation. **Dependency**: Must run **before** T006. **Verification**: Script exits 0 only if source is valid.
- [X] T039 [P] [FR-001] **SAFETY GATE**: Implement `code/scripts/cpu_feasibility_check.py` to attempt loading the quantized model with `n_ctx=512` and `n_threads=2` (simulating strictest CI runner). **Logic**: If OOM or timeout occurs, log `OOM_PRE_CHECK` and exit with a clear error message suggesting model size reduction. **Dependency**: Must run **before** T006/T007/T014a. **Verification**: Script exits 0 only if model loads successfully on CPU.
- [X] T006 [P] [FR-002] Implement `code/data_generation/profiles.py` to generate **synthetic expert profiles** (multiple per domain). **Schema**: `{"id": str, "domain": str, "capability_rules": str, "behavior_keywords": [str]}`. **Domains**: coding, math, logic, creative, factual (2 profiles each). **Rules**: Capability rules define heuristic constraints. Behavior keywords define a set of style markers. **Validation Logic**: Must validate that every generated profile contains non-empty `capability_rules` and `behavior_keywords`; if a profile is malformed (missing keys), **skip it, log an error, and proceed** with remaining valid profiles. **Strict Failure**: Raise exception if the internal generator encounters a fatal error (e.g., inability to write to disk) to prevent silent synthetic fallback. **Dependency**: Requires T038 (Source Verification) and T039 (CPU Feasibility) to pass.
- [X] T007 [US1] [FR-002] Implement `code/data_generation/tasks.py` to generate a global pool of **stratified task scenarios** (reused across all profiles). **Domains**: Enforce **exact proportional distribution** based on total 50 tasks: coding ([deferred] = 10 tasks), math ([deferred] = 5 tasks), logic ([deferred] = 5 tasks), creative ([deferred] = 15 tasks), factual ([deferred] = 15 tasks) [UNRESOLVED-CLAIM: c_92ff6f25 — status=not_enough_info]. **Logic**: Must validate that generated tasks do not contain ambiguous context that would prevent deterministic evaluation; if ambiguous, log and flag the specific task as "excluded" from Hallucination Rate calculation. **Verification**: Script logs the actual distribution ratios (e.g., "Distribution: coding=20%, math=10%...") and exits 0 only if ratios match the spec. **Sequential**: Must run **after** T006 to ensure task context compatibility. **Note**: This is a single execution step. **Dependency**: T006. <!-- FAILED: unspecified -->
- [X] T008 [P] [US1] Implement `code/inference/prompts.py` defining three distinct prompt templates with explicit text and placeholders:
 - **Monolithic**: `"[System: You are {domain_expert} who {behavior_keywords}. Task: {task}]"`
 - **Separated Tracks**: `"[System: Capability: {capability_rules}. Behavior: {behavior_keywords}. Task: {task}]"`
 - **Generic Baseline**: `"[System: You are a helpful assistant. Task: {task}]"`
- [X] T009 [P] [US1] Implement `code/inference/engine.py` to load a quantized model (Llama or Phi-3-mini) on CPU-only backend with OOM protection and timeout handling. **Logic**: Must support all 3 conditions.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-tractable LLM inference with decoupled prompt architecture (Priority: P1) 🎯 MVP

**Goal**: Load a small quantized model on CPU and generate responses for all profiles × multiple tasks × conditions (Monolithic, Separated, Generic)

**Independent Test**: The system can be tested by running a single profile-task pair through all three conditions and verifying that the model generates text within 300 seconds without CUDA errors or OOM crashes.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for prompt template generation in `tests/unit/test_prompts.py`
- [X] T011 [P] [US1] Integration test for single inference run in `tests/integration/test_inference_single.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/inference/engine.py` logic to: 1) Load quantized model using `llama-cpp-python` with `device="cpu"`, `n_gpu_layers=0 `; 2) Implement a **strict 300-second timeout handler ** (configurable, default 300s as per spec US-1) and OOM exception catching for CPU runs; 3) Return output string or error code. **Must support all 3 conditions **: Monolithic, Separated Tracks, and Generic Baseline.
- [ ] T014a [US1] Implement `code/scripts/run_inference.py` to execute the full inference pipeline.
 **Algorithm**:
 1. Load profiles from `data/raw/profiles.json` and tasks from `data/raw/tasks.json`.
 2. Initialize `output_list = []`.
 3. **Batch Processing**: Group tasks into batches of appropriate size. (configurable) to manage RAM as per Plan.
 4. For each `batch` in tasks:
 For each `profile` in profiles:
 For each `condition` in ["Monolithic", "Separated", "Generic"]:
 a. Build prompt using `code/inference/prompts.py`.
 b. Call `code/inference/engine.py` with timeout=300s.
 c. If success: append `{profile_id, task_id, condition, latency, success_flag: true, output_text}`.
 d. If timeout/OOM: append `{profile_id, task_id, condition, latency, success_flag: false, output_text: null, error: "timeout"|"oom"}`.
 Write `output_list` to `data/interim/inference_outputs.jsonl` (incremental write per batch).
 5. Finalize file.
 **Scale**: 10 profiles × 50 tasks × **3 conditions ** = **1500 runs**.
 **Verification**: File exists and contains a sufficient number of rows (including failed runs with `status='failure'`). **Dependency**: Requires T006 and T007 completion.
- [ ] T015 [US1] Add logging for inference status (start, progress, completion, failures) in `run_inference.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate outputs against deterministic ground-truth rules (Priority: P2)

**Goal**: Calculate Heuristic Adherence, Style Consistency, and Hallucination Rate using rule-based logic (no LLM judges)

**Independent Test**: The evaluation script can be tested independently by feeding it a known "gold standard" response and a known "hallucinated" response to verify that the metrics match expected binary values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for Heuristic Adherence logic in `tests/unit/test_metrics.py`
- [X] T018 [P] [US2] Contract test for Hallucination detection logic in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/evaluation/validators.py` with specific mapping: Code tasks -> AST parser; Math tasks -> SymPy evaluator; Logic tasks -> Z solver; Creative/Factual -> Regex/NLI checks. **Edge Case**: Must handle inputs from malformed profiles or ambiguous contexts by skipping and logging, consistent with T006/T007. **Ambiguity Handling**: Explicitly log the **reason** for exclusion (e.g., "Ambiguous Context", "Missing Capability Key") when a task is skipped.
- [X] T020 [US2] Implement `code/evaluation/metrics.py` Heuristic Adherence calculation: a binary indicator reflecting whether the task is solved (validator pass) or not..
- [X] T021a [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation (Part 1): Regex extraction of entity-value pairs (`\b(\w+): (\w+)\b`).
- [X] T021b [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation (Part 2): **Multi-hop reasoning check**: Use logic verification (e.g., Z3/SymPy) to validate if inferred facts require multi-step deduction not present in context. **Implementation Note**: This task implements the "rule-based logic verification" and "entailment checks" required by FR-005 by encoding the extracted facts and context into Z3 constraints to verify logical entailment. **Input Format**: Text-to-SMT transformation logic must be defined to convert extracted entity-value pairs into Z3 constraints.
- [X] T021c [US2] Implement `code/evaluation/metrics.py` Hallucination Rate calculation (Part 3): Compare extracted facts against external source traces; if fact not in context OR requires invalid multi-hop inference, increment hallucination counter.
- [X] T022 [US2] Implement `code/evaluation/metrics.py` Style Consistency calculation: 1) Count occurrences of behavior track keywords (from profile) in output; 2) Calculate frequency ratio; 3) Match against structure rules (e.g., "must start with greeting").
- [X] T023 [US2] Implement `code/scripts/evaluate.py` to process `data/interim/inference_outputs.jsonl` and generate `data/interim/evaluation_scores.jsonl` with schema `{profile_id, task_id, condition, heuristic_adherence, hallucination_rate, style_consistency}`. **Verification**: File exists and contains a sufficient number of rows for analysis.
- [X] T024 [US2] Implement sensitivity analysis logic for Style Consistency threshold (FR-008) by **iterating over a range of specific thresholds**, calculating false-positive rates for each, and reporting the variance. **Output**: Save `data/processed/sensitivity_analysis.json` containing the variance in false-positive rates for each threshold.
- [X] T025 [US2] Add error handling for malformed profiles/tasks (skip and log) and ambiguous context (flag as excluded). **Logic**: Implement detection to skip malformed input data (missing capability/behavior keys) and flag ambiguous contexts as excluded from Hallucination Rate calculation to prevent false positives, as required by spec Edge Cases.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate results and perform statistical comparison (Priority: P3)

**Goal**: Aggregate scores and fit a Generalized Linear Mixed Model (GLMM) to test for significant differences between conditions

**Independent Test**: The analysis pipeline can be tested by running a simulation with synthetic data where the "Separated" condition is known to have a lower hallucination rate, verifying that the GLMM returns a significant fixed effect.

**Note on Spec/Plan Alignment**: FR-006 in spec.md now explicitly mandates a **Generalized Linear Mixed Model (GLMM)** to handle binary/continuous mixed outcomes, aligned with T000b amendment.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026b [P] [US3] Unit test for GLMM fitting logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analysis/stats.py` to load `data/interim/evaluation_scores.jsonl` (Output of T023). **Dependency**: T023. **Input**: T023 output. **Output**: Save `data/interim/aggregated_data.csv`. **Verification**: File exists and contains a substantial number of rows.
- [ ] T028 [US3] [FR-006] Implement `code/analysis/stats.py` GLMM fitting using **`statsmodels`** library.
 **Formula**: `metric ~ condition + (1 | profile_id) + (1 | task_id)`
 **Random Intercepts**: Profile and Task.
 **Metrics**: Heuristic Adherence (binomial), Hallucination Rate (binomial), Style Consistency (gaussian).
 **Implementation**: Use `family=binomial(link='logit')` for binary outcomes and `family=gaussian` for continuous outcomes.
 **CRITICAL**: Must include logic to calculate and output the **non-inferiority margin check** for Style Consistency as per SC-002, using **margin = 0.05** (from `code/utils/config.py`).
 **Output**: Save model summary to `data/processed/glm_results.json` including `p_values`, `effect_sizes`, and `non_inferiority_margin_check`. **Verification**: File exists and contains p-values for fixed effects and the non-inferiority check result. **Dependency**: T000b (Spec Amendment), T004b (Config).
- [ ] T029 [US3] [FR-007] Implement **Holm-Bonferroni** correction for multiple comparisons across metrics (FR-007) for all 3 conditions. **Output**: Update `data/processed/glm_results.json` with `corrected_p_value` field for each metric.
- [X] T030 [US3] Implement `code/analysis/plots.py` to generate figures for the paper. **Output**: Generate `data/processed/figures/effect_sizes.png`, `data/processed/figures/p_values.png`, and `data/processed/figures/confidence_intervals.png`. **Verification**: All three PNG files exist in the directory.
- [ ] T031 [US3] Create `code/scripts/analyze.py` to run the full analysis pipeline and output `data/processed/final_results.csv` (aggregated metrics) and `data/processed/analysis_report.md` (summary of findings). **Verification**: Both files exist and contain expected headers/sections.
- [ ] T032 [US3] Verify that the direction of effect aligns with the hypothesis (Separated < Monolithic for Hallucination Rate) AND verify the **non-inferiority margin** (0.05) for Style Consistency. **Output**: Write `code/scripts/verify_hypothesis.py` that checks `Separated < Monolithic` in `data/processed/glm_results.json` and the non-inferiority check, outputting `data/processed/hypothesis_verification.json` with `status: PASS/FAIL`. **Verification**: JSON file exists with status field.
- [ ] T041 [US3] [FR-006] Implement `code/analysis/stats.py` to calculate the **effective sample size** per random effect level (Profile/Task) after exclusions. If any level has **< 5 observations**, flag the GLMM convergence as "UNRELIABLE" in `data/processed/glm_results.json` **AND** trigger a "CONVERGENCE_FAILURE" report in `data/processed/convergence_report.md`, halting further analysis. **Verification**: Report exists if triggered.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `specs/001-llmxive-follow-up-extending-colleague-sk/quickstart.md`: Add "Setup" section with install commands, "Inference" section with run examples, "Evaluation" section with metric definitions. **Verification**: File contains all three sections with code blocks.
- [X] T034 Code cleanup and refactoring of `code/evaluation/metrics.py`: Refactor to use Strategy Pattern for validators; add unit tests in `tests/unit/test_metrics.py` for edge cases (empty input, null context). **Verification**: Refactored code exists and all new tests pass.
- [X] T035 Performance optimization for inference pipeline: Target metric: reduce latency by calculating (Baseline - New) / Baseline. Method: Implement batch inference in `engine.py` to process a batch of tasks. **Verification**: Benchmark script `tests/benchmark_batch.py` must record the **actual achieved latency reduction percentage** and report it in the output log.
- [ ] T036 [P] Additional unit tests in `tests/unit/` for edge cases: empty input, null context, malformed JSON in `profiles.py` and `tasks.py`. **Verification**: All new tests pass and cover specified edge cases.
- [X] T037 [P] Run `code/scripts/update_state.py` (created in T002a) to update `state/projects/.../artifacts.yaml` checksums. **Verification**: Script exists and successfully updates `artifacts.yaml`.

---

## Phase 7: Review Remediation & Data Integrity (Revision Pass)

**Purpose**: Address specific reviewer concerns regarding data robustness, CPU feasibility, and statistical validity. **Note**: Safety gates (T038, T039) have been moved to Phase 2.

- [X] T042 [US3] [SC-002] Explicitly implement the non-inferiority margin test for Style Consistency as per SC-002, calculating the absolute difference and checking against the predefined margin (0.05) in `code/scripts/verify_hypothesis.py`. **Note**: Logic for this is now also integrated into T028 and T032.

---

## Phase 8: Execution Feedback Remediation (Run-Book Alignment)

**Purpose**: Resolve mismatches between the `quickstart.md` run-book and the actual file structure created by tasks, ensuring all referenced scripts exist.

- [ ] T043 [P] [Execution Feedback] Reconcile run-book vs implementation: Update `quickstart.md` to invoke the **actual** implementation scripts defined in the plan:
 - Replace `code/data/generators/profile_generator.py` with `code/data_generation/profiles.py` (T006).
 - Replace `code/data/generators/task_generator.py` with `code/data_generation/tasks.py` (T007).
 - Replace `code/evaluation/score.py` with `code/scripts/evaluate.py` (T023).
 **Action**: Edit `quickstart.md` to point to these existing paths. Do NOT create wrapper scripts.
 **Verification**: The commands in `quickstart.md` run successfully without `ModuleNotFoundError`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Remediation (Phase 7)**: Depends on completion of US1, US2, and US3 core logic; addresses specific reviewer feedback.
- **Execution Feedback Remediation (Phase 8)**: Can be done in parallel with Phase 6/7, but must be completed before final `quickstart.md` validation.

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

1. Complete Phase 0: Spec Amendment (T000a, T000b)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
- **Scale Note**: This project uses a reduced scale of 10 profiles × 50 tasks × **3 conditions ** = 1,500 runs for CI feasibility, as defined in the Plan's Statistical Power section and authorized by T000b.
- **Revision Note**: Phase 7 tasks address specific reviewer concerns regarding data integrity, CPU feasibility, and statistical power validation.
- **Consolidation Note**: Tasks T007a-T007d have been consolidated into T007 to prevent parallel write conflicts.
- **Spec Alignment Note**: T000b amends the spec to allow GLMM and reduced scale. T004c and T028 reference T000b.
- **Constraint Preservation Note**: All tasks have been updated to explicitly match the specific values and requirements in the spec (e.g., thresholds, conditions, correction methods).
- **Ordering Note**: Safety gates (T038, T039) have been moved to Phase 2 to ensure they run before data generation and inference.
- **Dependency Note**: T014a explicitly consumes artifacts from T006/T007. T027 depends on T023. T028 depends on T000b and T004b.
- **Tagging Note**: All tasks now include explicit FR/SC tags where applicable.
- **Run-Book Alignment Note**: Phase 8 task (T043) updates `quickstart.md` to point to the actual implementation paths, eliminating the need for wrapper scripts.
- **Convergence Note**: T041 handles the "UNRELIABLE" convergence case by halting analysis and generating a failure report.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->