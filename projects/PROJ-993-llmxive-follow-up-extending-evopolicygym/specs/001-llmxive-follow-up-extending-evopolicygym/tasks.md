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

- [X] T001a [P] Create project directory structure: `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/`, `tests/`, `data/`, `specs/`
- [X] T001b [P] Create empty `__init__.py` files in all code subdirectories (`envs/`, `agents/`, `explanation/`, `analysis/`, `utils/`)
- [X] T001c [P] Create `requirements.txt` with pinned versions: `gymnasium==0.29.1 `, `transformers==4.36.0 `, `scikit-learn==1.3.2 `, `statsmodels==0.14.1 `, `radon==6.0.1 `, `pandas==2.1.4 `, `numpy==1.26.2 `, `pyyaml==6.0.1 `, `pytest==7.4.3 `, `pydantic==2.5.2 `, `bitsandbytes==0.41.0 `, `evopolicygym==<specific-commit-or-version>`
- [X] T001d [P] Create `pyproject.toml` with linting (ruff) and formatting (black) configurations
- [X] T001e [P] **Install EvoPolicyGym**: Add a task to install the specific version/commit of `EvoPolicyGym` required for this feature (e.g., `pip install git+) to ensure the registry is available for dynamic discovery. (Depends on T001c)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement base configuration manager for seed management and hyperparameters in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/config.py`
- [X] T005 [P] Setup structured logging infrastructure in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/logging.py`
- [X] T006 [P] Create base environment wrapper extending `gymnasium.Env` for EvoPolicyGym compatibility in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/base_env.py`
- [X] T007a [P] Define JSON schema contracts for `dynamic_shift_env`, `counterfactual_explanation`, and `evolution_metrics` in `specs/001-llmxive-counterfactual-extension/contracts/` (Full YAML content provided in artifact)
- [X] T007b [P] **Generate Rule Schema Artifact**: Create the `data/rules_schema.json` file containing the ground-truth Rule IDs, logic, and valid actions for all environments. This file MUST be generated programmatically or manually defined to serve as the input for the counterfactual generator and validator. (Depends on T007a)
- [X] T007c [P] **Generate Rules Schema Content**: Populate `data/rules_schema.json` with the specific Rule IDs, logic, and valid actions for the A diverse set of environments to be used by the counterfactual generator. This task ensures a concrete data source exists for validation logic. (Depends on T007a)
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

- [X] T013c [US1] Define shift configuration schema and implement parsing logic to enforce the default moderate step N in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py` (Depends on T007a)
- [X] T013d [US1] **Dynamically Discover** the existing EvoPolicyGym environments by querying the `EvoPolicyGym` registry (e.g., `gymnasium.envs.registration.registry`). This task MUST NOT hardcode IDs but must retrieve the list of available environments programmatically. **It MUST verify that the discovered count matches exactly 16 environments; if not, raise a `ValueError` halting execution.** The task MUST save the discovered list to `data/discovered_envs.json` for downstream tasks. (Depends on T001e, T013c)
- [X] T013e [US1] **Programmatically Iterate** over the list loaded from `data/discovered_envs.json` and wrap each with `DynamicShiftEnvironment`. (Depends on T013d)
- [X] T013b [US1] Implement logic to alter reward functions or transition probabilities after `shift_step` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py`
- [X] T013f [US1] **Run Static Agent**: Implement a script to run a static (non-adaptive) agent on the dynamic-shift environments to generate `pre_shift_score` and `post_shift_score` data points. (Depends on T013e)
- [X] T015b [US1] Define schema for `sensitivity_report.csv` with columns: `env_id` (str), `shift_step` (int), `pre_shift_score` (float), `post_shift_score` (float), `drop_rate` (float ratio 0.0-1.0), `p_value` (float). (Depends on T013f)
- [X] T014 [US1] Add logic to calculate p-value for performance drop using data from T013f; if p >= 0.05, **log a failure for that specific environment ID and SKIP it from subsequent evolution runs** (do not halt the entire experiment), and log the error to `data/shift_validation.log`. (Depends on T015b, T013f)
- [X] T015a [US1] Create wrapper script to orchestrate the application of `DynamicShiftEnvironment` to the discovered environments in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/main.py` (Depends on T013e)
- [X] T015c [US1] Implement logic to populate `sensitivity_report.csv` with sensitivity analysis results (Depends on T013c, T014, T013f, T015b)

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

- [X] T020a [US2] Define `CounterfactualExplanation` Pydantic data model in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/validator.py` (Depends on T007a)
- [X] T020b [US2] Implement `validate_explanation()` function in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/validator.py` (Depends on T007b for schema input)
- [X] T021a [US2] **Deterministic Rule Derivation**: Implement logic to derive the `correct_action` (counterfactual action) by iterating the loaded rule schema (`data/rules_schema.json`) against the trajectory to find the valid action that would have succeeded. This is a deterministic step. **This task MUST write the derived `correct_action` and `rule_id` to `data/derivation_cache.json` for the generation step.** (Depends on T007b)
- [X] T023 [US2] Implement fallback mechanism to return a `TemplateExplanation` object **OR a scalar_reward signal** and log fallback event to `data/fallbacks.log` if LLM fails or times out in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py` (TemplateExplanation model: {rule_id: str, suggested_action: str, template: str}; Log format: ISO8601 timestamp, env_id, reason, fallback_type)
- [X] T021b [US2] Implement lightweight, CPU-quantized LLM inference pipeline using **TinyLlama-Chat-v1.0 (4-bit quantized via bitsandbytes)**. The `generate_explanation()` function MUST:
 1. Load the trajectory and the `correct_action` derived by T021a from `data/derivation_cache.json`.
 2. Generate text explicitly stating the violated Rule ID and the derived `correct_action`.
 3. Return a `CounterfactualExplanation` object. (Depends on T021a, T023)
- [X] T021d [US2] Implement token counting, truncation, and 'exceeds limit' failure flagging logic for a defined token constraint. in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T022 [US2] Implement deterministic rule mapping to ensure output explicitly states violated Rule ID from JSON schema in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [X] T022b [US2] Implement logic to invoke `validate_explanation()` on generator output before returning the explanation in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
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

- [X] T033 [US3] Implement baseline (scalar reward) condition logic and orchestration to run it alongside counterfactual condition in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [X] T034 [US3] Implement policy parser using `radon` to calculate cyclomatic complexity and conditional branch count in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/policy_parser.py`
- [X] T035 [US3] Add error handling to catch syntactically invalid evolved policy code and record as "generation error" in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [X] T032a [US3] Create `EvolutionaryHarness` class to run agents on both baseline and counterfactual conditions with fixed seeds. **Must depend on T013e** to ensure it iterates only over registered environments. **Must ensure policy write is flushed before parsing** (file-existence check with retry loop). (Depends on T021d, T023, T013e, T033)
- [X] T032b [US3] Implement logic to write `data/evolution_results.csv` (columns: `run_id` (int), `seed` (int), `seed_run_id` (str composite key: "seed-run_id"), `condition` (str), `env_id` (str), `score` (float), `pre_shift_score` (float), `drop_rate` (float), `complexity` (float), `branch_count` (int)) after each run. **Must call the parser implementation from T034** to calculate complexity and branch count for the generated policy BEFORE writing the row. **Must include `pre_shift_score` and `drop_rate` to support SC-001**. (Depends on T032a, T034)
- [X] T036 [US3] Implement mixed-effects model analysis using `statsmodels` with formula `score ~ condition + complexity + (1|seed/run_id)` reading from `data/evolution_results.csv` and writing to `data/stats_results.json`. **Must include conditional logic**: if `p_value < 0.05` AND `effect_size > 0`, set `significant` flag to `True`; otherwise `False`. This formula explicitly models the nested "runs within seeds" structure and is the sole source for statistical significance testing. (Depends on T032a, T032b)
- [X] T037 [US3] Create CLI entry point to execute full pipeline with command `python main.py --run-evolution` and output `data/final_results.csv` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/main.py` (CLI args: --seeds, --runs, --envs, --conditions; Output: final_results.csv with aggregated metrics) (Depends on T032a, T036)
- [X] T038 [US3] Aggregate success/failure counts from T021 (timeouts) and T023 (fallbacks) to calculate and report the rate of successful counterfactual explanation generation (SC-004) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/analysis/stats.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038a [P] Write `README.md` with project overview, installation instructions, and CLI usage examples in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/README.md`
- [X] T038b [P] Write `quickstart.md` with step-by-step guide to run a single evolutionary experiment in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/quickstart.md`
- [X] T038c [P] Update `CONTRIBUTING.md` with coding standards and testing guidelines in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/CONTRIBUTING.md`
- [X] T039 [P] Code cleanup and refactoring (reduce cyclomatic complexity of T013b, T021, T032a to <10)
- [X] T040a [P] Implement performance benchmarking script to measure CPU inference time per failure in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/benchmarks/benchmark_inference.py`
- [X] T040b [P] Optimize T021 (LLM inference) to stay within 30s threshold by implementing caching (single-threaded safe) and batch processing (if memory allows, otherwise sequential)
- [X] T041 [P] Additional unit tests in `tests/unit/` covering edge cases (empty trajectories, syntax errors)
- [X] T042a [P] Run `quickstart.md` validation script to ensure all steps execute successfully in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/tests/test_quickstart.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision**: **REMOVED**. All requirements previously deferred to a "Revision" phase have been integrated into Phases 3, 4, and 5 with concrete specifications. No future analysis pass is required to define the work.

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
4. Developer D (or rotation): Execute Polish Phase (N) to refine and optimize.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Phase**: **REMOVED**. All critical requirements (data integrity, execution order, statistical rigor) are now explicitly defined in Phases 3, 4, and 5. No "mandatory" future analysis is required.