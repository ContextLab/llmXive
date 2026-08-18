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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure: `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/`, `tests/`, `data/`, `specs/`
- [X] T001b [P] Create empty `__init__.py` files in all code subdirectories (`envs/`, `agents/`, `explanation/`, `analysis/`, `utils/`)
- [X] T001c [P] Create `requirements.txt` with pinned versions: `gymnasium==0.29.1 [UNRESOLVED-CLAIM: c_0e093e30 — status=not_enough_info] `, `transformers==4.36.0 [UNRESOLVED-CLAIM: c_3b63eaa7 — status=not_enough_info] `, `scikit-learn==1.3.2 [UNRESOLVED-CLAIM: c_17eb7a31 — status=not_enough_info] `, `statsmodels==0.14.1 [UNRESOLVED-CLAIM: c_5172b1bd — status=not_enough_info] `, `radon==6.0.1 [UNRESOLVED-CLAIM: c_7383b6ba — status=not_enough_info] `, `{{claim:c_a6bfdf0c}} (pi, https://en.wikipedia.org/wiki/Pi) `, `numpy==1.26.2 [UNRESOLVED-CLAIM: c_f9448162 — status=not_enough_info] `, `pyyaml==6.0.1 [UNRESOLVED-CLAIM: c_c6f69247 — status=not_enough_info] `, `pytest==7.4.3 [UNRESOLVED-CLAIM: c_d2cd730a — status=not_enough_info] `, `pydantic==2.5.2 [UNRESOLVED-CLAIM: c_e7c1f6fe — status=not_enough_info] `, `bitsandbytes==0.41.0 [UNRESOLVED-CLAIM: c_24b20bdd — status=not_enough_info] `, `evopolicygym==v1.2.0 [UNRESOLVED-CLAIM: c_e3373dae — status=not_enough_info]`
- [X] T001d [P] Create `pyproject.toml` with linting (ruff) and formatting (black) configurations
- [X] T001e [P] **Install Dependencies**: Execute `pip install -r requirements.txt`. **Deliverable**: `data/install_log.txt`. **Verification**: 1) Run `pip list` and verify all pinned versions are present. 2) Capture the output and exit code to `data/install_log.txt`. 3) If `evopolicygym==v1.2.0 [UNRESOLVED-CLAIM: c_e3373dae — status=not_enough_info]` is not found, attempt `pip install git+<url>` and fail loudly if both fail. Exit code must be 0. (Depends on T001c)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement base configuration manager for seed management and hyperparameters in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/config.py`
- [X] T005 [P] Setup structured logging infrastructure in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/logging.py`
- [X] T006 [P] Create base environment wrapper extending `gymnasium.Env` for EvoPolicyGym compatibility in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/base_env.py`
- [X] T007 [P] **Generate Rule Schema Artifact**: Create `data/rules_schema.json`. Logic: 1) Attempt to parse `EvoPolicyGym` source code in `envs/` (if available). 2) If source code is not found or parsing fails, **create `data/rules_template.json`** with a sample structure: `{"rule_id": "R001", "logic": {"type": "equals", "field": "state", "value": 1}, "valid_actions": [0, 1]}` for all environments. 3) Serialize to JSON. This file serves as the ground-truth input for the counterfactual generator. (Depends on T001e)
- [X] T008 [P] Implement deterministic random seed pinning utility ensuring reproducibility across runs in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/seed_utils.py`
- [X] T009 [P] Implement logic to separate test set configuration from training/evolution configuration to enforce Constitution Principle VII (Dynamic-Shift Validation Independence) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/utils/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Extension and Dynamic Shift Injection (Priority: P1) 🎯 MVP

**Goal**: Extend existing environments to include "dynamic-shift" modes where reward/transition functions change at a configurable step N (default a majority of budget).

**Independent Test**: Run a static agent on the modified environment and verify that the environment state or reward function changes exactly at the configured step N, causing a measurable performance drop.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for shift trigger logic at step N in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_env_shift.py`
- [X] T011 [P] [US1] Integration test verifying performance drop for non-adaptive agents post-shift in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/tests/test_env_shift.py`

### Implementation for User Story 1

- [ ] T013d [US1] **Enforce Environment Count (Adaptive Fail)**: Dynamically discover the existing EvoPolicyGym environments. **Logic**: 1) Import `REGISTRY` using `from evopolicygym.envs import REGISTRY`. 2) Query `REGISTRY.keys()`. 3) If the discovered count is 0, **raise a RuntimeError** with the message "No environments found. Study cannot proceed." 4) If the count is > 0, proceed. 5) If the count is NOT exactly 16, **log a WARNING** to `data/discovered_envs.log` stating "Expected 16 (2607.02440, https://arxiv.org/abs/2607.02440) environments, found {count}. [UNRESOLVED-CLAIM: c_11306f7f — status=verified] Proceeding with available subset." and write the list of available IDs to `data/discovered_envs.json`. **Do NOT** fail if count < 16, but do not proceed if count == 0. (Depends on T001e)
- [ ] T015b [P] [US1] Define schema for `sensitivity_report.csv` with columns: `env_id` (str), `shift_step` (int), `pre_shift_score` (float), `post_shift_score` (float), `drop_rate` (float ratio 0.0-1.0), `p_value` (float). (Depends on T007)
- [X] T013c [P] [US1] Define shift configuration schema and implement parsing logic to enforce the default moderate step N in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py` (Depends on T013d)
- [ ] T013e [P] [US1] **Programmatically Iterate** over the list loaded from `data/discovered_envs.json` (created by T013d) and wrap each with `DynamicShiftEnvironment`. (Depends on T013d)
- [X] T013b [P] [US1] Implement logic to alter reward functions or transition probabilities after `shift_step` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/envs/dynamic_shift_env.py`
- [ ] T013f [P] [US1] **Run Static Agent**: Implement a script to run a static (non-adaptive) agent on the dynamic-shift environments to generate `pre_shift_score` and `post_shift_score` data points. Logic: If `data/discovered_envs.json` is empty, skip execution and write an empty `data/sensitivity_report.csv` with headers only. (Depends on T013e, T015b)
- [ ] T014 [P] [US1] Add logic to calculate p-value for performance drop using data from T013f; if p >= 0.05, **log a failure for that specific environment ID and SKIP it from subsequent evolution runs** (do not halt the entire experiment), and log the error to `data/shift_validation.log`. (Depends on T013f, T015b)
- [ ] T015c [P] [US1] **Populate Sensitivity Report**: Write `data/sensitivity_report.csv` with the results from T013f and T014. (Depends on T013f, T015b, T014)
- [ ] T015a [P] [US1] Create wrapper script to orchestrate the application of `DynamicShiftEnvironment` to the discovered environments in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/main.py`. **Logic**: Must verify `data/sensitivity_report.csv` exists (from T015c) before proceeding. (Depends on T013e, T013f, T015b, T015c)

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

- [X] T020a [P] [US2] Define `CounterfactualExplanation` Pydantic data model in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/validator.py` (Depends on T007)
- [X] T020b [P] [US2] Implement `validate_explanation()` function in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/validator.py` (Depends on T007)
- [X] T021a-Load [P] [US2] **Schema Loading**: Load `data/rules_schema.json` into memory and cache it in `data/derivation_cache.json` (structure: `{rule_id: logic, valid_actions}`). (Depends on T007)
- [ ] T021a-Logic [P] [US2] **Masked Schema Generation**: Implement the logic to create a **masked rule schema** from `data/derivation_cache.json`. Logic: 1) Iterate over the schema. 2) For each rule, retain `rule_id` and `description` (if present), but **remove or mask the `logic` predicate** (the boolean condition). 3) Output the masked schema to `data/masked_schema.json`. This prepares the input for the LLM to reason about the rule's intent without seeing the ground-truth logic. (Depends on T021a-Load)
- [ ] T021a-Reasoning [P] [US2] **LLM Diagnostic Selection**: Implement the LLM inference step to generate the explanation. Logic: 1) Load the trajectory and the `masked_schema.json` (from T021a-Logic). 2) Construct a prompt: "Analyze the trajectory log. Identify the most likely violated Rule ID based on the rule descriptions provided. Output JSON: {rule_id: str, reasoning: str}". 3) Use a lightweight, CPU-quantized model (e.g., `TinyLlama/TinyLlama-1.1B-Chat-v1.0 [UNRESOLVED-CLAIM: c_7dda07fc — status=not_enough_info]` 4-bit quantized via `bitsandbytes`) to analyze the trajectory and **select** the `rule_id`. 4) Output the selected `rule_id` and `reasoning` to `data/llm_selection.json`. **Constraint**: The generation must complete within 30 seconds. If it fails, trigger T023 fallback. **Do NOT** ask the LLM to derive the action. (Depends on T021a-Logic)
- [ ] T023 [P] [US2] Implement fallback mechanism to return a `TemplateExplanation` object **OR a scalar_reward signal** and log fallback event to `data/fallbacks.log` if LLM fails or times out in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py` (TemplateExplanation model: {rule_id: str, suggested_action: str, template: str}; Log format: ISO8601 timestamp, env_id, reason, fallback_type)
- [ ] T021b [P] [US2] **Retrieve Action and Generate Text**: Implement the final generation step. Logic: 1) Load `data/llm_selection.json` (produced by T021a-Reasoning). 2) Retrieve the `correct_action` from the **full** `data/derivation_cache.json` (loaded in T021a-Load) using the `rule_id` selected by the LLM. 3) Generate the final text explicitly stating the violated Rule ID and the retrieved `correct_action`. 4) Return a `CounterfactualExplanation` object. **Constraint**: The entire generation attempt (load + inference) MUST complete within **30 seconds**. If the model fails or exceeds 30s, immediately trigger T023 fallback. **Do NOT** attempt a fallback to a smaller model, as this risks exceeding the 30s threshold. (Depends on T021a-Reasoning, T021a-Load)
- [ ] T021c [P] [US2] **Log Success**: If T021b successfully generates a valid explanation (passes T020b), log the event to `data/success_log.jsonl` with `run_id`, `env_id`, `rule_id`, and `timestamp`. (Depends on T021b)
- [ ] T021d [P] [US2] Implement token counting, truncation, and 'exceeds limit' failure flagging logic for a defined token constraint. in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`. **Logic**: If the generated explanation exceeds 200 tokens, **raise an exception** or return a failure flag. **Do NOT truncate**. The data point MUST be discarded and logged as "token_limit_exceeded" in `data/fallbacks.log` with reason "exceeds_token_limit". (Depends on T021b)
- [ ] T022b [P] [US2] Implement logic to invoke `validate_explanation()` on generator output before returning the explanation in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [ ] T027 [P] [US2] Add logic to suppress generation for successful trajectories (output neutral indicator) in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/explanation/generator.py`
- [ ] T023b [P] [US2] **Checksum Fallback Log**: Compute a SHA-256 checksum of `data/fallbacks.log` after writing and store it in `data/checksums.json` to ensure compliance with Constitution Principle III (Data Hygiene). (Depends on T023)

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

- [ ] T033 [P] [US3] Implement baseline (scalar reward) condition logic and orchestration to run it alongside counterfactual condition in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [ ] T034 [P] [US3] Implement policy parser module using `radon` to calculate cyclomatic complexity and conditional branch count in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/policy_parser.py`
- [ ] T035 [P] [US3] Add error handling to catch syntactically invalid evolved policy code and record as "generation error" in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/agents/evolutionary_harness.py`
- [ ] T032a [P] [US3] Create `EvolutionaryHarness` class to run agents on both baseline and counterfactual conditions with fixed seeds. **Must depend on T013e** to ensure it iterates only over registered environments. **Logic**: 1) Verify `data/sensitivity_report.csv` exists (from T015c). If missing, raise `RuntimeError`. 2) Filter the environment list to include ONLY rows where `p_value < 0.05` AND `drop_rate > 0.0`. If the filtered list is empty, raise `RuntimeError` ("No valid environments found for evolution"). 3) Run evolution. 4) After each run, write `run_id`, `seed`, `condition`, `env_id`, `score`, `pre_shift_score`, `drop_rate` to `data/run_state.json` as a list of objects. **Schema**: `[{"run_id": int, "seed": int, "condition": str, "env_id": str, "score": float, "pre_shift_score": float, "drop_rate": float},...]`. (Depends on T021b, T013e, T033, T034, T015c)
- [ ] T032b [P] [US3] Write `data/evolution_results.csv`. **Logic**: Read `data/run_state.json` (produced by T032a). **Integrate T035**: For each policy file, call the error handling routine from T035. If the policy is syntactically invalid, log the error and **skip** writing this row to the CSV. If valid, call `policy_parser` (T034 module) to get complexity and branch count. Retrieve `pre_shift_score` and `drop_rate` from `data/sensitivity_report.csv` (produced by T015c) matching `env_id`. If a row for `env_id` is missing, default to 0.0 for `drop_rate` and log a warning. Combine all data into a CSV row. Columns: `run_id` (int), `seed` (int), `seed_run_id` (str), `condition` (str), `env_id` (str), `score` (float), `pre_shift_score` (float), `drop_rate` (float), `complexity` (float), `branch_count` (int). (Depends on T032a, T034, T035, T015c)
- [ ] T036 [P] [US3] Implement mixed-effects model analysis using `statsmodels` with formula `score ~ condition + complexity + (1|seed/run_id)` reading from `data/evolution_results.csv`. **Logic**: 1) Verify `data/evolution_results.csv` exists and is not empty. If missing or empty, raise `RuntimeError` ("No real data available for analysis"). **Do NOT** fall back to mock data. 2) Map columns: `condition` -> `condition`, `complexity` -> `complexity`. 3) Handle convergence errors (log warning, flag as failed). 4) **Verify Direction**: Check that the coefficient for the 'counterfactual' condition is **positive** (indicating counterfactual > baseline). If the coefficient is negative, log an error and set `significant` flag to `False`. 5) If `p_value < 0.05` AND `effect_size > 0` AND **coefficient is positive**, set `significant` flag to `True`; otherwise `False`. Write results to `data/stats_results.json`. (Depends on T032b)
- [ ] T037 [P] [US3] Create CLI entry point to execute full pipeline with command `python main.py --run-evolution` and output `data/final_results.csv` in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/main.py` (CLI args: --seeds, --runs, --envs, --conditions; Output: final_results.csv with aggregated metrics) (Depends on T032a, T036)
- [ ] T038a [P] [US3] **Log Parsing**: Parse `data/fallbacks.log` and `data/timeouts.log` using regex to extract counts. Output `data/aggregation_stats.json` with keys `fallback_count`, `timeout_count`, `total_failures`. (No dependencies)
- [ ] T038 [P] [US3] Aggregate success/failure counts to calculate and report the rate of successful counterfactual explanation generation (SC-004). **Logic**: **Pre-flight Check**: Verify `data/success_log.jsonl` and `data/fallbacks.log` exist. If missing, raise `RuntimeError`. Read `data/success_log.jsonl` (from T021c) to get `successful_count`. Read `data/fallbacks.log` and `data/timeouts.log` to get `failure_count`. Calculate rate = `successful_count / (successful_count + failure_count)`. Output to `data/aggregation_stats.json`. (Depends on T038a, T021c)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039a [P] **Refactor T013b**: Refactor `dynamic_shift_env.py` to reduce cyclomatic complexity to <10. **Strategy**: Extract the `shift_logic` function into a helper function `apply_shift_condition(state, step, shift_config)`. (Depends on T013b)
- [ ] T039b [P] **Refactor T021**: Refactor `explanation/generator.py` to reduce cyclomatic complexity to <10. **Strategy**: Identify the `generate_explanation` function as the primary hotspot. Apply the **Extract Method** pattern to split it into three distinct, lower-complexity helper functions: 1) `parse_trajectory_to_log(trajectory)`: Converts raw trajectory data into a structured log string (Complexity target: < 5). 2) `select_violated_rule_id(log, masked_schema)`: Handles the LLM prompt construction and parsing of the `rule_id` selection (Complexity target: < 5). 3) `format_explanation_text(rule_id, action, reasoning)`: Constructs the final natural language string (Complexity target: < 5). Ensure the main function orchestrates these three calls sequentially. (Depends on T021)
- [ ] T039c [P] **Refactor T032a**: Refactor `agents/evolutionary_harness.py` to reduce cyclomatic complexity to <10. **Strategy**: Identify the `run_evolution` function as the primary hotspot. Apply the **Extract Method** pattern with **State Accumulation**. Split it into: 1) `run_single_seed_evolution(seed, env_id, condition)`: Executes a single seed run and returns a dict of results (score, policy path, etc.) (Complexity target: < 5). 2) `aggregate_seed_results(seed_results_list)`: Aggregates the list of dicts into the final `run_state.json` structure (Complexity target: < 5). The main `run_evolution` function should iterate seeds, call `run_single_seed_evolution`, collect results, and then call `aggregate_seed_results`. (Depends on T032a)
- [ ] T038b [P] Write `README.md` with project overview, installation instructions, and CLI usage examples in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/README.md`
- [ ] T038c [P] Write `quickstart.md` with step-by-step guide to run a single evolutionary experiment in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/quickstart.md`
- [ ] T038d [P] Update `CONTRIBUTING.md` with coding standards and testing guidelines in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/CONTRIBUTING.md`
- [ ] T040a [P] Implement performance benchmarking script to measure CPU inference time per failure in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/code/benchmarks/benchmark_inference.py`
- [ ] T040b [P] Optimize T021 (LLM inference) to stay within 30s threshold by implementing caching (single-threaded safe) and batch processing (if memory allows, otherwise sequential)
- [ ] T041a [P] **Add Edge Case Tests**: Add unit tests in `tests/unit/test_edge_cases.py` covering empty trajectories and syntax errors. (Depends on T027, T035)
- [ ] T041b [P] **Add Integration Tests**: Add integration tests in `tests/integration/test_full_pipeline.py` covering the full flow from environment shift to statistical analysis. (Depends on T032a, T036)
- [ ] T042a [P] Run `quickstart.md` validation script to ensure all steps execute successfully in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/tests/test_quickstart.py`

---

## Phase N+1: Revision & Robustness (Post-Analysis Fixes)

**Goal**: Address specific concerns raised by `analyze` regarding data integrity, execution order, and statistical rigor.

### Implementation for Revision Concerns

- [ ] T046 [US1] **Dynamic Shift Validation**: Add a check in T014 to ensure that the `drop_rate` calculated for an environment is not 0.0. If `drop_rate` is 0.0, log a specific warning to `data/shift_validation.log` indicating that the shift configuration for `env_id` may be too subtle to cause a performance drop, and exclude that environment from the final analysis set. (Depends on T013f, T014)
- [ ] T047 [US2] **Token Limit Enforcement**: Refactor T021d to strictly enforce a token limit. If the generated explanation exceeds 200 tokens, the task MUST immediately raise an exception, set a `truncated` flag in the output object, and log the event to `data/truncation_log.jsonl`. The task MUST NOT return an untruncated explanation. (Depends on T021b)
- [ ] T048 [US3] **Data Integrity Check**: Add a validation step in T036 to verify that `data/evolution_results.csv` contains at least one row per condition (baseline and counterfactual) before running the mixed-effects model. If a condition is missing, raise `RuntimeError` with a clear message indicating which condition is missing. (Depends on T032b)
- [ ] T049 [US2] **Schema Consistency Check**: Add a pre-flight check in T021a-Logic to verify that the `rule_id` found in the trajectory matches an entry in the cached schema. If a mismatch is found, log an error to `data/schema_mismatch.log` and skip that trajectory step rather than crashing. (Depends on T021a-Load)
- [ ] T050 [US1] **Shift Point Verification**: Add a unit test in `tests/unit/test_shift_point.py` to verify that the shift occurs exactly at the configured step N (default approximately half) and not at a random step. (Depends on T013c)
- [ ] T051 [US3] **Complexity Metric Validation**: Add a check in T034 to ensure that `radon` returns a valid numeric complexity score. If `radon` fails to parse a policy (e.g., due to syntax errors), log the error and assign a default complexity score of -1, then flag the row in `data/evolution_results.csv` for exclusion in T036. (Depends on T034)
- [ ] T052 [US2] **LLM Timeout Robustness**: Refactor T021b to use `signal.alarm` (on Linux) or `threading.Timer` (cross-platform) to enforce the 30s timeout strictly. If the timeout fires, immediately kill the process/thread and trigger T023 fallback without waiting for the model to finish. (Depends on T021b, T023)
- [ ] T053 [US3] **Statistical Power Check**: Add a check in T036 to calculate the minimum detectable effect size given the sample size in `data/evolution_results.csv`. If the sample size is too small to detect a meaningful effect (e.g., power < 0.8), log a warning to `data/power_analysis.log` and flag the results as "underpowered". (Depends on T036)
- [ ] T054 [US1] **Environment Discovery Logging**: Ensure that T013d logs the exact list of discovered environment IDs to `data/discovered_envs.log` in addition to writing `data/discovered_envs.json`, to facilitate debugging if the list changes unexpectedly. (Depends on T013d)
- [ ] T055 [US2] **Fallback Reason Logging**: Refactor T023 to log the specific reason for the fallback (e.g., "timeout", "schema_validation_failed", "model_error") to `data/fallbacks.log` instead of just "fallback". This will allow for better analysis of failure modes. (Depends on T023)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N+1)**: Depends on `analyze` report and completion of Phases 1-5

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
5. Developer E (or rotation): Execute Revision Phase (N+1) to address `analyze` findings.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Revision Phase**: Tasks in Phase N+1 are mandatory to address `analyze` findings regarding data integrity, execution order, and statistical rigor.