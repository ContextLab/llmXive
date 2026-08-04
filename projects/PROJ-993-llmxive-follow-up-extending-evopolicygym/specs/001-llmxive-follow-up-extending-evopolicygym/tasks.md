# Tasks: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

**Input**: Design documents from `/specs/001-llmxive-counterfactual-extension/`
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

- [ ] T001 [P] Create project structure per implementation plan in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/`
- [X] T002 [P] Initialize Python project with dependencies: `gymnasium`, `transformers` (CPU-quantized), `scikit-learn`, `statsmodels`, `radon`, `pandas`, `numpy`, `pyyaml` in `requirements.txt`
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement base configuration manager for seed management and hyperparameters in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/config.py`
- [X] T005 [P] Setup structured logging infrastructure in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/logging.py`
- [X] T006 [P] Create base environment wrapper extending `gymnasium.Env` for EvoPolicyGym compatibility in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/base_env.py`
- [ ] T007 [P] Define JSON schema contracts for `dynamic_shift_env`, `counterfactual_explanation`, and `evolution_metrics` in `specs/001-llmxive-counterfactual-extension/contracts/`
- [X] T008 [P] Implement deterministic random seed pinning utility ensuring reproducibility across runs in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/seed_utils.py`
- [X] T009 [P] Implement logic to separate test set configuration from training/evolution configuration to enforce Constitution Principle VII (Dynamic-Shift Validation Independence) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Extension and Dynamic Shift Injection (Priority: P1) 🎯 MVP

**Goal**: Extend 16 existing environments to include "dynamic-shift" modes where reward/transition functions change at a configurable step N (default a majority of budget).

**Independent Test**: Run a static agent on the modified environment and verify that the environment state or reward function changes exactly at the configured step N, causing a measurable performance drop.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for shift trigger logic at step N in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_env_shift.py`
- [X] T011 [P] [US1] Integration test verifying performance drop for non-adaptive agents post-shift in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_env_shift.py`

### Implementation for User Story 1

- [X] T013a [US1] Define shift configuration schema and implement parsing logic to enforce the default moderate step N in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py`
- [X] T013b [US1] Implement logic to alter reward functions or transition probabilities after `shift_step` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py`
- [X] T013c [US1] Implement subclassing logic to programmatically apply `DynamicShiftEnvironment` to the 16 specific existing EvoPolicyGym environments and generate `env_registry.json` listing all 16 dynamic-shift variants in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py`
- [X] T014 [US1] Add warning logging if performance drop on dynamic shift is not statistically significant (p ≥ 0.05) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py`
- [X] T015 [US1] Create wrapper script to orchestrate the application of `DynamicShiftEnvironment` to the 16 environments and generate a static `sensitivity_report.csv` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/main.py` (Depends on T013c)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Counterfactual Explanation Generation Module (Priority: P2)

**Goal**: Implement a CPU-tractable module generating natural language counterfactual failure explanations validated against a rule schema.

**Independent Test**: Feed a synthetic failure trajectory into the module and verify the output explicitly identifies the violated Rule ID and required correction without hallucination.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US2] Unit test for schema validation of generated explanations in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_explanation.py`
- [X] T019 [P] [US2] Integration test for timeout fallback mechanism (time-limited) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_explanation.py`

### Implementation for User Story 2

- [X] T020a [US2] Define `CounterfactualExplanation` Pydantic data model in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/validator.py`
- [X] T020b [US2] Implement `validate_explanation()` function in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/validator.py`
- [X] T021a [US2] Implement logic to load and parse ground-truth environment rules (JSON schema) for the generator in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T021 [US2] Implement lightweight, CPU-quantized LLM inference pipeline with `generate_explanation()` function returning a `CounterfactualExplanation` object in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T021b [US2] Implement token counting, truncation, and 'exceeds limit' failure flagging logic for the -token constraint in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T022 [US2] Implement deterministic rule mapping to ensure output explicitly states violated Rule ID from JSON schema in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T022b [US2] Implement logic to invoke `validate_explanation()` on generator output before returning the explanation in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [ ] T023 [US2] Implement fallback mechanism to return a `TemplateExplanation` object and log fallback event to `data/fallbacks.log` if LLM fails or times out in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T027 [US2] Add logic to suppress generation for successful trajectories (output neutral indicator) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evolutionary Harness and Statistical Analysis Pipeline (Priority: P3)

**Goal**: Execute evolutionary agents on baseline vs. counterfactual conditions, parse policy metrics, and perform mixed-effects model analysis.

**Independent Test**: Run a small-scale simulation with a limited number of runs per group and verify the pipeline produces a CSV of metrics and a valid p-value from the mixed-effects model.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US3] Unit test for `radon` integration calculating cyclomatic complexity in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_stats.py`
- [X] T031 [P] [US3] Integration test for mixed-effects model analysis outputting p-value and effect size in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_stats.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Create `EvolutionaryHarness` class to run agents on both baseline and counterfactual conditions with fixed seeds (Depends on T021 completion) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [X] T033 [US3] Implement baseline (scalar reward) condition logic and orchestration to run it alongside counterfactual condition in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [X] T034 [US3] Implement policy parser using `radon` to calculate cyclomatic complexity and conditional branch count in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/policy_parser.py`
- [X] T035 [US3] Add error handling to catch syntactically invalid evolved policy code and record as "generation error" in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [ ] T036 [US3] Implement mixed-effects model analysis using `statsmodels` with formula handling nested runs within seeds, reading from `data/evolution_results.csv` and writing to `data/stats_results.json` with keys `p_value`, `effect_size`, `model_formula` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/analysis/stats.py`
- [ ] T037 [US3] Create CLI entry point to execute full pipeline with command `python main.py --run-evolution` and output `data/final_results.csv` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/main.py`
- [X] T038 [US3] Aggregate success/failure counts from T021 (timeouts) and T023 (fallbacks) to calculate and report the rate of successful counterfactual explanation generation (SC-004) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/analysis/stats.py`
- [X] T045 [US1/US3] Execute statistical test (t-test or equivalent) to calculate p-value for performance drop verification and write result to `data/shift_validation.json` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/analysis/stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` and `README.md`
- [ ] T039 Code cleanup and refactoring
- [ ] T040 Performance optimization across all stories (ensure CPU inference stays within an acceptable time threshold)
- [ ] T041 [P] Additional unit tests in `tests/unit/`
- [ ] T042 Run quickstart.md validation

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 completion for full harness execution

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
Task: "Unit test for shift trigger logic at step N in projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_env_shift.py"
Task: "Integration test verifying performance drop for non-adaptive agents post-shift in projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_env_shift.py"

# Launch all models for User Story 1 together:
Task: "Create DynamicShiftEnvironment class extending base_env.py in projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py"
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