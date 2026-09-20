# Tasks: Co-Evolving Policy Distillation

**Input**: Design documents from `/specs/001-coevolving-policy-distillation/`
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

- [X] T001a [P] Create directory structure: `src/generators`, `src/agents`, `src/analysis`, `src/utils`, `tests/`, `data/`, `data/results/`
- [X] T001b [P] Create empty `__init__.py` files in all `src/` and `tests/` subdirectories
- [X] T001c [P] Initialize Python 3.11 project with dependencies: `sympy`, `networkx`, `numpy`, `scipy`, `statsmodels`, `pytest` in `pyproject.toml`
- [X] T001d [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml` and `.pre-commit-config.yaml`
- [X] T001e [P] Create `.gitignore` for Python and data artifacts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] [Foundational] Implement configuration constants in `src/utils/config.py` to handle seeding, generation counts, and rule evaluation budgets. **Requirement**: Define `VALIDITY_THRESHOLD` (defaulting to a high confidence level), `RULE_EVALUATION_BUDGET`, and `RULES_PER_GENERATION` (integer) constants here. `RULES_PER_GENERATION` must be used to calculate the total target exposure for SC-002.
- [X] T004b [P] [Foundational] Implement total exposure calculation logic in `src/utils/config.py` using `RULES_PER_GENERATION` and the number of generations to calculate the target budget. **Dependency**: Requires T004a to be complete.
- [X] T005 [P] Implement checksum utility in `src/utils/checksums.py` to generate SHA-256 hashes for data artifacts and manage `data/checksums.json`
- [X] T006 [P] Create base abstract agent class in `src/agents/base_agent.py` defining the interface for rule-set management and evaluation
- [X] T007 [P] Implement CLI skeleton in `src/cli.py` (entry point only, no logic) to establish command structure
- [X] T008a [P] Generate `contracts/dataset.schema.yaml` defining the schema for generated proofs and grids, including `id`, `domain`, `rule_set_id`, and `instance_data` fields.
- [X] T008b [P] Generate `contracts/agent_state.schema.yaml` defining the schema for agent state, including `population`, `rule_sets` (with `rule_id`), and `generation_count`.
- [X] T008c [P] Generate `contracts/result.schema.yaml` defining the schema for result metrics, including `forgetting_rate`, `accuracy`, and `rule_retention`.
- [X] T008 [P] Implement schema validators in `tests/contract/` based on the generated contracts (`contracts/dataset.schema.yaml`, `contracts/agent_state.schema.yaml`, `contracts/result.schema.yaml`) to validate `dataset`, `agent_state`, and `result` JSON structures. **Dependency**: Requires T008a-c to be complete.
- [X] T042 [P] [Foundational] Implement "Pilot Power Estimation" in `src/analysis/statistical_tests.py`. **Logic**: Run a pilot simulation (a minimal number of runs per condition) to estimate variance. Calculate the required sample size (N) to achieve power ≥ 0.8 for a medium effect size (Cohen's f = 0.25). **Output**: Generate `data/batch_config.json` containing a dynamic list of unique random seeds (minimum N=30, or higher if variance suggests) to ensure SC-004 is met. **Requirement**: Do NOT abort the project; instead, dynamically adjust the seed list size to meet the power requirement. **Dependency**: Requires T004a, T005, T006, T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Task Environment Generation (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible synthetic datasets of propositional logic proofs and grid-world navigation tasks with distinct rule sets, including held-out test instances.

**Independent Test**: The system can be tested by running the generator script and verifying that the output contains valid logical proofs and navigable grids with unique, identifiable rule signatures for each task domain.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for generated proof validity in `tests/contract/test_dataset_schema.py`
- [X] T010 [P] [US1] Unit test for grid solvability and rule isolation in `tests/unit/test_logic_generation.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement propositional logic proof generator in `src/generators/logic_generator.py` using `sympy` to create valid proofs from parameterized axioms. **Requirement**: Include retry logic with a **bounded retry (max 3 attempts)** for invalid generations. If generation fails after multiple attempts, log a warning and skip that instance. **Verification**: Ensure the implementation includes a log assertion that triggers when the retry limit is reached (e.g., "Retry limit reached for instance X") and a unit test verifies this log message.
- [X] T012 [P] [US1] Implement grid-world navigation generator in `src/generators/grid_generator.py` using `networkx` to create solvable grids with non-overlapping rule sets (e.g., "avoid red", "diagonal paths"). **Requirement**: Include retry logic with a **bounded retry (max 3 attempts)** for invalid generations. If generation fails after a limited number of attempts, log a warning and skip that instance. **Verification**: Ensure the implementation includes a log assertion that triggers when the retry limit is reached (e.g., "Retry limit reached for instance X") and a unit test verifies this log message.
- [X] T013 [US1] Implement held-out test instance generator in `src/generators/test_generator.py`. **Output**: `data/test_instances.json` as a JSON array of objects with keys `id`, `domain`, `rule_set_id`, and `instance_data`. **Requirement**: Ensure instances are strictly separate from the training set by using a **disjoint seed range** (e.g., `TEST_SEED_START` defined in `config.py`, distinct from `TRAIN_SEED_START` used in T011/T012) to guarantee distinct logical axioms or grid configurations, satisfying FR-004 and providing baseline measurement data.
- [X] T014 [US1] Implement data writing logic to save generated training datasets to `data/` (e.g., `data/generated_proofs.json`, `data/generated_grids.json`) with checksums recorded in `data/checksums.json`.
- [X] T015 [US1] Implement validation script `src/analysis/validate_dataset.py`. **Input**: `data/generated_proofs.json`, `data/generated_grids.json`. **Output**: `data/validation_report.json`. **Requirement**: Load `VALIDITY_THRESHOLD` from `config.py` (default a high threshold). Check generated datasets and exit with an error code if validity falls below `VALIDITY_THRESHOLD` for proofs or solvability falls below `VALIDITY_THRESHOLD` for grids.
- [X] T015b [US1] Implement and execute the validation script in `src/cli.py` as a mandatory blocking gate before any training (Phase 4) can commence, ensuring SC-005 is enforced in the pipeline flow and preventing training on invalid data. **Dependency**: Requires T015 to be complete.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Distillation Strategy Execution Engine (Priority: P2)

**Goal**: Execute three distinct agent training conditions (Sequential, Mixed-task, Co-evolving) with strict parity in total data exposure.

**Independent Test**: The system can be tested by running the three conditions in isolation and verifying that the total number of rule evaluations per task is identical across all three runs, while the internal logic of the co-evolving agent successfully exchanges rule-sets between sub-populations.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for rule-evaluation counter parity in `tests/contract/test_result_schema.py`
- [X] T017 [P] [US2] Unit test for bidirectional exchange logic in `tests/unit/test_agent_conditions.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `SequentialAgent` in `src/agents/sequential_agent.py` to train on one task domain block at a time.
- [X] T019 [P] [US2] Implement `MixedAgent` in `src/agents/mixed_agent.py` to train on mixed task domains randomly per generation.
- [X] T020 [P] [US2] Implement `CoevolvingAgent` in `src/agents/coevolving_agent.py` to manage sub-populations and execute **bidirectional rule-set exchanges at every generation step**.
- [X] T021 [US2] Implement selection pressure logic in `src/agents/coevolving_agent.py` to discard non-performing rule-sets and prevent population collapse.
- [X] T022 [US2] Implement `src/utils/parity_checker.py`. **Function**: Provide a `check_and_enforce_parity(budget, current_count)` function that raises `ParityError` immediately if the count exceeds the budget. **Requirement**: Use **integer arithmetic exclusively** to prevent floating-point drift. Integrate this utility into the training loop (T023) to enforce the hard integer cap in real-time. **Dependency**: Requires T004b to be complete.
- [X] T023 [US2] Implement training loop logic in `src/cli.py` (training component only) that utilizes `parity_checker.py` (T022) to ensure exact parity of total rule evaluations across all three conditions (FR-002). **Requirement**: Call `check_and_enforce_parity` at every generation step to fail fast if the budget is exceeded. **Dependency**: Requires T022 to be complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Catastrophic Forgetting Measurement & Analysis (Priority: P3)

**Goal**: Evaluate trained agents on held-out test instances, calculate forgetting rates, and perform statistical comparison (Mixed-Design ANOVA).

**Independent Test**: The system can be tested by taking a pre-trained agent, running it against a held-out test set, and verifying that the calculated forgetting rate is mathematically derived from the difference between initial and final accuracy scores.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US3] Contract test for forgetting metric schema in `tests/contract/test_result_schema.py`
- [X] T025 [P] [US3] Integration test for full statistical analysis pipeline in `tests/integration/test_full_pipeline.py`
- [X] T039b1 [P] [US3] Add unit test `test_anova_significant_diff` in `tests/unit/test_statistical_tests.py` to verify the correct application of Mixed-Design ANOVA and Tukey tests with simulated data where a significant difference exists.
- [X] T039b2 [P] [US3] Add unit test `test_anova_no_diff` in `tests/unit/test_statistical_tests.py` to verify the correct application of Mixed-Design ANOVA and Tukey tests with simulated data where no significant difference exists.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement evaluation logic in `src/analysis/forgetting_metrics.py` to calculate accuracy drop from initial single-task to final multi-task performance. **Input**: `data/test_instances.json` (from T013) and trained agent states from T018-T020. **Output**: `data/results/baseline_metrics.json` and `data/results/final_metrics.json`. **Requirement**: Measure "initial single-task performance" by running agents on held-out instances immediately after single-task training, before multi-task training begins. **Dependency**: Requires T018-T020 (US2) to be functionally complete before execution.
- [X] T027 [P] [US3] Implement statistical analysis module in `src/analysis/statistical_tests.py` using `scipy` and `statsmodels` to perform a **Mixed-Design ANOVA (repeated measures)** followed by post-hoc Tukey tests. **Requirement**: If assumptions for parametric tests are violated, fallback to **Kruskal-Wallis**. Strictly adhere to Constitution Principle VII and FR-006.
- [X] T028 [US3] Implement "Warmup and Feasibility Check" in `src/cli.py`. **Input**: Single run parameters. **Logic**: Execute a single run of each condition and measure wall-clock time. **Output**: Estimate total time for multiple runs per condition. **Requirement**: Abort if estimated time > 5.5 hours (leaving 30 mins buffer for CI overhead) to satisfy SC-004 time constraints.
- [X] T029 [US3] Implement batch runner in `src/cli.py` (orchestration component) to execute multiple independent runs per condition with unique seeds from `data/batch_config.json` (generated by T042), generating the dataset required for SC-004 statistical power. **Dependency**: Requires T028 to confirm feasibility, T042 to provide seeds, and **T023 (Training Loop) to be complete** (stable interface).
- [X] T030 [US3] Implement data aggregation logic to collect results from the batch runner output in `data/results/`. **Input Pattern**: `data/results/run_*/final_metrics.json`. **Metric Key**: `forgetting_rate`. **Requirement**: Verify that the number of runs meets the SC-004 requirement (N ≥ 30) before proceeding to analysis.
- [X] T040 [US3] [P] Implement explicit "Rule-Set Identity Tracker" in `src/analysis/forgetting_metrics.py`. **Requirement**: Extend the metric calculation to not only track accuracy but also maintain a `retained_rule_ids` list per agent, referencing `contracts/agent_state.schema.yaml` for `rule_id` format. The final report must explicitly show the intersection of rule IDs retained from the initial single-task training vs. the final multi-task state, satisfying SC-003 and the requirement to isolate the effect of bidirectional exchange on specific rules (justification: granular tracking is required to distinguish rule-specific retention from generic accuracy). **Dependency**: Must be implemented before T031 and T032.
- [X] T031 [US3] Implement retention rate calculation in `src/analysis/forgetting_metrics.py` to compute and store raw retention rates of **distinct logical rules** for Co-evolving vs Mixed-task conditions (SC-003). **Requirement**: Explicitly trace the **identity of specific rules** from the `RuleSet` entity (e.g., by `rule_id`) to ensure the metric isolates the effect of bidirectional exchange on specific rules, not just generic accuracy. **Dependency**: Requires T040 to be complete.
- [X] T032 [US3] Implement comparison logic in `src/analysis/statistical_tests.py` to compare retention rates between Co-evolving and Mixed-task conditions. **Dependency**: Requires T040 to be complete.
- [X] T044 [US3] [P] Add "Time-Budget Enforcement" in `src/cli.py`. **Requirement**: Implement a hard wall-clock timer that interrupts the batch runner if the total runtime exceeds a predefined threshold, logging the current state and exiting gracefully to ensure the CI job does not exceed the 6-hour limit. **Dependency**: Must be integrated into T029.
- [X] T033 [US3] Implement report generation to output forgetting rates, ANOVA results (p-values), and retention comparisons to `data/results/forgetting_analysis.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Final Validation & Reporting

**Purpose**: Generate required verification artifacts (post-run checksums, power analysis) and ensure all success criteria are met before project completion.

- [X] T045 [P] [US3] Implement a "Reproducibility Audit Script" in `tests/integration/test_reproducibility.py`. **Requirement**: Re-run the entire pipeline with the exact same seeds from `data/batch_config.json` and verify that the checksums in `data/checksums.json` and the final metrics in `data/results/forgetting_analysis.json` are bit-for-bit identical, ensuring the "deterministic seeding" requirement is met.
- [X] T041 [US2] [P] Add a "Post-Run Parity Verification Report" generator in `src/analysis/parity_checker.py`. **Requirement**: After the batch run (T029) completes, aggregate the real-time parity enforcement logs from T022/T023 to generate `data/results/parity_report.json`. This report must **audit and confirm** that the hard integer cap was never violated across all 90+ runs, satisfying the "post-run checksum" requirement of FR-002 and verifying the fail-fast enforcement.
- [X] T048 [US2] [P] Implement "Post-Run Checksum Verification" in `src/analysis/parity_checker.py`. **Requirement**: Perform a final checksum verification of the total rule evaluations across all runs to ensure no floating-point drift occurred during the batch run, as a secondary check to the real-time enforcement.

---

## Phase 7: Robustness & Edge Case Handling (Revision)

**Purpose**: Address specific edge cases and failure modes identified in the specification to ensure the system fails loudly on real data issues and handles logical contradictions gracefully.

- [X] T046 [US1] [P] Enhance `src/generators/logic_generator.py` and `src/generators/grid_generator.py` to implement **strict failure-on-failure** for data loading. **Requirement**: Remove any `try/except` blocks that fall back to `generate_synthetic_*()` or `mock_*()` data when the primary generation logic fails. If a real instance cannot be generated after max retries (3 attempts), **log a warning and skip that instance** (do NOT halt execution), ensuring the "Fabrication Gate" never receives synthetic fallback data and the run continues for reproducibility.
- [X] T047 [US2] [P] Implement "Population Collapse Prevention" in `src/agents/coevolving_agent.py`. **Requirement**: Add a specific logic check after every rule-set exchange (T020) to detect if the average fitness of a sub-population has dropped below a critical threshold (e.g., 50% of initial fitness). If detected, automatically trigger a "reset" or "re-introduction" of high-fitness rules from the previous generation to prevent total population collapse, addressing the edge case where exchange degrades performance.
- [X] T049 [US3] [P] Implement "Edge Case Logging" in `src/cli.py`. **Requirement**: Ensure that all warnings (e.g., "Retry limit reached", "Population collapse detected", "Parity mismatch") are written to a dedicated `data/logs/edge_cases.log` file with timestamps and run IDs, facilitating the analysis of rare failure modes without cluttering standard output.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Final Validation (Phase 6)**: Depends on completion of Phases 1-5
- **Robustness (Phase 7)**: Depends on completion of Phases 1-5; must be completed before final CI run.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the data required by US2 and US3.**
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **Consumes data from US1; produces trained agents for US3.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). **Consumes agents from US2 and test data from US1.** **Note**: While code can be written in parallel, T026 (Evaluation) and T029 (Batch Runner) require the *functional completion* of US2 (T018-T020, T023) to execute.

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
Task: "Contract test for generated proof validity in tests/contract/test_dataset_schema.py"
Task: "Unit test for grid solvability and rule isolation in tests/unit/test_logic_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement propositional logic proof generator in src/generators/logic_generator.py"
Task: "Implement grid-world navigation generator in src/generators/grid_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data validity and checksums)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (ensure parity checks pass)
4. Add User Story 3 → Test independently → Deploy/Demo (verify statistical output)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Agent Training)
 - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with a limited number of cores and constrained memory. No GPU, no 8-bit quantization, no large model loading. Use `sympy`, `networkx`, and `scipy` exclusively.
- **Fabrication Prevention**: T046 ensures that no synthetic fallback data is ever used; the system must fail loudly if real data generation fails.