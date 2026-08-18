# Tasks: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Input**: Design documents from `/specs/001-symbolic-bes/`
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

## Phase 0: Research & Design (Contracts & Schema)

**Purpose**: Generate design artifacts required by downstream tasks.

- [X] T000a [P] Generate `contracts/dataset.schema.yaml` based on `data-model.md` and `plan.md` requirements. **Constraint**: Must define the exact JSON schema for puzzle instances including fields: `constraints`, `initial_state`, `target_state`, and `verifier_output` format. This task MUST complete before T013a.

- [X] T000b [P] Generate `contracts/output.schema.yaml` based on `plan.md` requirements for experiment logs and analysis results. **Constraint**: Must explicitly define the schema for `data/processed/exclusions.json` (fields: `puzzle_id`, `reason_code`, `timestamp`) and `data/processed/distribution_report.json` (fields: `total_count`, `type_distribution`, `complexity_distribution`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure per implementation plan by executing: `mkdir -p projects/PROJ-884-llmxive-follow-up-extending-self-improvi/{data/raw,data/processed,code/{dataset,symbolic,bes,analysis,utils},tests/{unit,integration}}`. **Constraint**: This task logically creates data and code directories; implementation is split for atomicity but the directory structure is established here.

- [X] T001b Initialize git repository and configure basic `.gitignore` for Python artifacts

- [X] T002a Initialize Python 3.11 virtual environment in `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/`

- [X] T002b Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.0`, `numpy==1.24.0`, `transformers==4.35.0`, `datasets==2.14.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `optimum==1.13.0`, `psutil==5.9.0`. **Constraint**: Use fixed versions from plan.md. Do not attempt to read from `research.md` as its schema is undefined.

- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Constraint**: Must generate `.flake8` and `pyproject.toml` (for black) configuration files to satisfy plan.md testing requirements.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw/` for immutable puzzles, `data/processed/` for logs/results. **Constraint**: Must verify directories exist and are writable.

- [X] T005a [P] [US1] Implement base logging infrastructure in `code/__init__.py` to capture wall-clock time and resource usage; output must be JSON format to `data/processed/experiment.log`. **Constraint**: Must include a verification step: Add a unit test in `tests/unit/test_logging.py::test_log_format_is_json` to validate the output format matches the schema.

- [X] T005b [P] [US1] Implement CPU utilization monitoring in `code/utils/monitor.py` using `psutil` to log `cpu_percent` for every execution step. **Constraint**: This metric is REQUIRED for the energy calculation in T026. Must log at the same frequency as T005a.

- [X] T006 [P] [US1] Setup random seed management utility in `code/utils/seed.py` for reproducibility

- [X] T007 [P] [US1] Create base configuration loader in `code/config.py` to handle experiment parameters (population size, generations)

- [ ] T007b [US1] Initialize `code/config.py` with `DEFAULT_TDP_WATTS` as a placeholder (e.g., 0.0). **Constraint**: This value MUST be overwritten by T007c after calibration. Do not hardcode a static value here. **Dependency**: None.

- [ ] T007c [US1] Implement TDP Calibration Script in `code/utils/calibrate_tdp.py`. **Constraint**: Must run a known workload, measure power draw (or estimate via CPU frequency scaling if power API unavailable), and output `data/processed/calibrated_tdp.json`. **Action**: T007c MUST output `calibrated_tdp.json` with fields: `tdp_watts`, `error_margin`, `confidence_interval`. **Dependency**: Requires T007b. **Note**: Removed [P] flag to prevent parallel execution with T007b.

- [X] T008 Setup error handling framework by creating `code/exceptions.py` defining custom exception classes for `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, and `VERIFIER_ERROR` (to handle internal verifier failures, addressing robustness gap)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Instantiate a dataset of logic/arithmetic puzzles with deterministic Python verifiers capable of validating solution paths without LLMs.

**Independent Test**: Run verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST (TDD), ensure they FAIL before implementation. Do NOT mark as [P] as they must precede implementation.

- [X] T009 [US1] Contract test for `code/dataset/generator.py` in `tests/unit/test_generator.py::test_generator_handles_empty_input`

- [X] T010 [US1] Unit test for `code/dataset/verifier.py` with known valid/invalid solutions in `tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/dataset/generator.py` to create logic puzzles (Sudoku variants, constrained pathfinding) with systematic complexity scaling (N=10..500). **Constraint**: Must support command-line arguments for `N` and `count`.

- [X] T012 [US1] Implement `code/dataset/verifier.py` to execute deterministic validation logic for each puzzle instance, returning boolean validity and specific constraint violation codes (e.g., `DUPLICATE_ROW`, `INVALID_PATH`) within 100ms. **Note**: T012 validates the code, T013a/b generates the data.

- [X] T013a [P] [US1] Implement `code/dataset/validate_and_checksum.py`. **Constraint**: This script MUST accept a directory of raw puzzles, run the verifier, calculate checksums, and output `data/processed/distribution_report.json` with type/complexity distribution stats. Must strictly enforce "Fail Loudly" (no synthetic fallback). **Dependency**: Requires T011 and T012.

- [X] T013b [US1] Execute `code/dataset/generator.py` to produce raw puzzles. **Constraint**: Must run with parameters `--n 50 100 200 500 --count 10 --types sudoku,pathfinding`. **Dependency**: Requires T011.

- [X] T013d [US1] Execute `code/dataset/validate_and_checksum.py` to finalize the dataset and generate `data/processed/distribution_report.json`. **Constraint**: Must update `state/projects/PROJ-884-llmxive-follow-up-extending-self-improvi.yaml` with artifact hashes. **Dependency**: Requires T013a and T013b.

- [ ] T013c [US1] Implement `code/dataset/validate_distribution.py`. **Constraint**: This script MUST read `data/processed/distribution_report.json` (from T013d) and `contracts/dataset.schema.yaml` (from T000b) to verify statistical representativeness and output `data/processed/distribution_validation.json` (fields: `is_valid`, `power_estimate`, `notes`). **Dependency**: Requires T000b (schema) and T013d (data generation artifact). **Note**: Moved after T013d to ensure artifact availability.

- [X] T013e [US1] Execute `code/dataset/validate_distribution.py` to generate `data/processed/distribution_validation.json`. **Constraint**: Must run after T013d. **Dependency**: Requires T013c and T013d.

- [X] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. **Dependency**: Requires T013e.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Evolutionary Search Execution (Priority: P2)

**Goal**: Execute the BES framework where the forward step uses a small CPU-tractable LLM and the backward step is replaced by a symbolic planner.

**Independent Test**: Run the evolutionary loop on a subset of puzzles and verify that the symbolic planner generates sub-goals and the LLM attempts to satisfy them, with the verifier correctly parsing the output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for `code/symbolic/planner.py` with edge cases (non-linear constraints, impossible goals) in `tests/unit/test_symbolic_planner.py::test_planner_handles_nonlinear_constraints`

- [X] T017a [US2] Unit test for `code/symbolic/planner.py` in `tests/unit/test_symbolic_planner.py::test_planner_handles_impossible_goals`.
- [X] T017b [US2] Integration test for the BES loop with a small population in `tests/integration/test_bes_loop.py::test_bes_loop_executes_symbolic_backward_step`.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `code/symbolic/parser.py` to convert puzzle constraints into a formal language parseable by the planner

- [X] T019 [US2] Implement `code/symbolic/planner.py` to generate sub-goal decompositions, including logic to detect and flag `CONTRADICTION_DETECTED` or `PARSE_FAILURE`. **Constraint**: Must include the logic to call the exclusion logger (T019d) directly within this module or via a helper.

- [X] T019d [US2] Implement `code/symbolic/exclusion_logger.py` to write exclusion events to `data/processed/exclusions.json`. **Constraint**: Must strictly adhere to the schema defined in `contracts/output.schema.yaml` (T000b) for `exclusions.json`. Must log `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, `IMPOSSIBLE_GOAL`, and `NON_LINEAR_CONSTRAINT` reasons. **Dependency**: Requires T000b.

- [X] T020 [P] [US2] Generate `code/bes/config.py` with configuration for a small pre-trained LLM (`distilbert-tiny`). **Constraint**: This task is for **configuration file generation ONLY** (no download). Must specify `device='cpu'` and forbid `bitsandbytes` in the config file. **Dependency**: None (config file is static).

- [ ] T021 [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must download and load the model specified in `code/bes/config.py` using `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`, quantized precision) and specify exact Hugging Face model ID `distilbert-tiny` with pinned `revision` hash for reproducibility. Must enforce CPU-only constraints. **Dependency**: Requires T020 to generate config file.

- [X] T022 [P] [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [X] T023 [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [X] T024 [US2] Implement the main BES loop in `code/main.py` to orchestrate forward (LLM) and backward (Symbolic) steps, logging all transitions. **Constraint**: Must explicitly execute the loop across the full complexity scaling range (N=10..500) to generate data for T029a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

**Goal**: Record success rates and computational costs for both symbolic-guided and neural-verifier baselines, applying statistical tests for significance.

**Independent Test**: Feed synthetic success rate data with known differences to the analysis script to verify z-test and t-test accuracy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `code/analysis/stats.py` with synthetic data in `tests/unit/test_stats.py::test_z_test_identifies_significance`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/analysis/metrics.py` to calculate success rates, wall-clock time, and energy consumption (Joules) from execution logs. **Constraint**: Energy formula: `E = config.DEFAULT_TDP_WATTS * (cpu_percent / 100) * wall_clock`. **Dependency**: Must read `cpu_percent` from T005b logs and TDP value from `data/processed/calibrated_tdp.json` (output of T007c). Must fail if `calibrated_tdp.json` is missing.

- [X] T027 [US3] Implement **Mandatory** two-proportion z-test in `code/analysis/stats.py` to compare success rates (as mandated by FR-005) with null hypothesis H0: p1 = p2 and alpha=0.05. **Note**: This is the primary statistical test required by the spec.

- [X] T028a [US3] Implement statistical framework pre-registration logic in `code/analysis/stats.py` to define and log the choice between 'equivalence' (TOST) and 'non-inferiority' frameworks before running tests, satisfying SC-001's pre-registration requirement.

- [ ] T029a [US3] Run Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` across the full complexity scaling range (N=10..500) to generate `data/processed/scaling_raw_logs.json`. **Dependency**: Requires T024 (BES loop logic).

- [ ] T029b [US3] Implement Scalability Analysis. **Constraint**: Perform log-log linear regression on `data/processed/scaling_raw_logs.json` to derive the complexity class (Big-O). Must use `scipy.stats.linregress`. If R^2 < 0.85, flag as 'Inconclusive'. **Output**: Must write `data/processed/scaling_analysis.csv` with columns: `n`, `time`, `complexity_class` (e.g., 'O(n^2)'), `r_squared`, `status` ('PASS', 'FAIL', 'INCONCLUSIVE'). **Dependency**: Requires T029a.

- [ ] T029c [US3] Execute Full Symbolic Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` on the full dataset to generate `symbolic_results.json`. **Note**: Renamed from 'Execute Full Baseline Experiments' to clarify it only runs the symbolic mode. **Dependency**: Requires T024.

- [X] T030a [P] [US3] Implement `code/main.py` entry point script with configurable loop selection (`--mode symbolic | --mode neural_subset`). **Constraint**: For Neural Subset Baseline, must use CPU-optimized `optimum` quantization (no CUDA) and derive 'GPU-hours' metric via the conversion factor defined in T040b. **Note**: This task implements the *script only*; it does not execute it.

- [ ] T030d [US3] Execute Neural Subset Baseline. **Constraint**: Execute `code/main.py` with `--mode neural_subset` on a subset of N=50 puzzles to generate `neural_baseline_results.json`. **Note**: Added to provide a CPU-tractable baseline comparison. **Dependency**: Requires T030a.

- [X] T031a [P] [US3] Implement `code/analysis/stats.py` to write machine-readable results. **Constraint**: Must output `data/processed/stats_results.json` containing p-values, confidence intervals, and test statistics. **Dependency**: Requires T027, T029c, T030d.

- [ ] T031b [US3] Generate final report in `data/processed/final_report.md` (Markdown format) containing sections: Success Rate Comparison, Cost Comparison, Complexity Analysis, and Statistical Significance (p-values). **Note**: Depends on T031a (machine-readable stats) and T029c/T030d (results).

- [X] T037a [US3] Validate `data/processed/exclusions.json` against the schema. **Constraint**: Must verify that the file exists, matches the schema defined in `contracts/output.schema.yaml` (T000b), and contains entries for all symbolic failures logged by T019d. **Dependency**: Requires T019d and T000b.

- [X] T037b [US3] Validate `data/processed/exclusions.json` content integrity. **Constraint**: Must ensure all logged exclusions have a corresponding `reason_code` and `puzzle_id`. **Dependency**: Requires T037a.

- [X] T038 [US3] Implement Power Analysis Check. **Constraint**: Before running T027 (Z-test), calculate statistical power based on N and observed effect size. If power < 0.8, flag the result as "Underpowered" and output a recommendation to increase sample size. **Dependency**: Requires T036 (validated dataset) and T029c/T030d (results).

- [X] T039 [US3] Documentation updates in `README.md`. **Constraint**: Must include sections on: 1) How to run the BES loop, 2) How to interpret results (success rates, p-values), 3) How to handle exclusions (referencing `exclusions.json`). **Dependency**: Requires T031b (Final Report) for context.

- [ ] T040a [US3] Implement the "Validated Conversion Factor" logic in `code/analysis/metrics.py` for GPU-hours estimation. **Constraint**: Must load the conversion factor from `data/processed/literature_gpu_factor.json` (produced by Tb) or fallback to the hardcoded 0.0015 with a warning. **Dependency**: Requires T040b.

- [ ] T040b [US3] Document Empirical Calibration Impossibility. **Constraint**: Since the target runner (GitHub Actions) is CPU-only, empirical GPU calibration is impossible. This task MUST document this limitation, cite a literature-based conversion factor (e.g., Green500), and output `data/processed/literature_gpu_factor.json` with the chosen factor and citation. **Action**: Must explicitly state in the output JSON and in the final report (T031b) that the 'GPU-hours' metric is an **Estimated (Literature-Based)** value. **Action**: Must update `plan.md` Constitution Check table to reflect Principle VII as 'PARTIALLY SATISFIED'. **Rationale**: Addresses the "Partially Satisfied" status of Constitution Principle VII by providing a documented, literature-backed approximation rather than an impossible measurement.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [US3] Implement **Optional** Equivalence Testing (TOST) in `code/analysis/stats.py` as a secondary analysis, dependent on T027 results. **Constraint**: Only run if pre-registered in T028a. Must not override the mandatory z-test results from T027.

- [X] T033 [P] Code cleanup and refactoring of `code/bes/` and `code/symbolic/` modules

- [X] T034 [US1] Implement strict "Fail Loudly" logic in `code/dataset/verifier.py` and `code/dataset/generator.py`. **Requirement**: Remove any `try/except` blocks that silently fallback to synthetic/mock data. If a real puzzle generation step fails or a constraint cannot be parsed, the script MUST raise a specific exception (e.g., `DataGenerationError`) and halt execution, ensuring no synthetic data is ever written to `data/raw/`. **Rationale**: Addresses the fabrication risk where real data fetches fail and are replaced by mock data.

---

## Phase 7: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Address specific concerns raised in prior research-stage reviews regarding robustness, edge cases, and data integrity.

- [ ] T041 [US1] Implement robust handling of "Syntactically Valid but Semantically Nonsensical" LLM outputs. **Constraint**: Modify `code/dataset/verifier.py` to explicitly detect semantic violations (e.g., path jumps, invalid state transitions) that pass syntax checks but fail logical consistency, returning `INVALID_SEMANTIC` error code. **Rationale**: Addresses Edge Case 2 from spec.md to ensure evolutionary pressure remains on validity, not just syntax.

- [ ] T042 [US2] Implement logic to detect and flag "Logically Impossible" sub-goals generated by the symbolic planner. **Constraint**: Modify `code/symbolic/planner.py` to include a lookahead or consistency check that verifies the generated sub-goal sequence does not contradict the current puzzle state. If a contradiction is found, log `IMPOSSIBLE_SUBGOAL` and exclude the instance per FR-006. **Rationale**: Addresses Edge Case 3 from spec.md to prevent the planner from generating dead-end trajectories.

- [ ] T043 [US2] Implement explicit exclusion logging for "Non-Linear" or "Too Complex" constraints that the symbolic parser cannot decompose. **Constraint**: Ensure `code/symbolic/parser.py` raises `PARSE_FAILURE` for non-linear constraints and that `code/symbolic/exclusion_logger.py` (T019d) correctly captures this reason. **Rationale**: Addresses Edge Case 1 from spec.md and FR-006 to ensure the system degrades gracefully rather than crashing.

- [ ] T044 [US3] Enhance `code/analysis/stats.py` to report confidence intervals alongside p-values for the two-proportion z-test. **Constraint**: Calculate and output 95% confidence intervals for the difference in success rates. **Rationale**: Provides richer statistical context beyond binary significance testing, addressing SC-001 and SC-004.

- [ ] T045 [US1] Add a "Sanity Check" task to verify that the generated dataset contains no duplicate puzzle instances. **Constraint**: Implement `code/dataset/validate_uniqueness.py` to hash all puzzle definitions and ensure uniqueness before proceeding to T013d. **Rationale**: Ensures data integrity and prevents artificial inflation of sample size with duplicates.

- [ ] T046 [US2] Implement a "Timeout" mechanism for the LLM forward step to prevent infinite loops in trajectory recombination. **Constraint**: Modify `code/bes/forward_step.py` to enforce a strict time limit (e.g., 5 seconds) per generation attempt. If exceeded, log `TIMEOUT` and discard the candidate. **Rationale**: Ensures the total experiment runtime stays within the 6-hour CI limit and prevents resource starvation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately. **Must complete before Phase 3**.
- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of Phases 3-6 to verify the implementation against the new robustness requirements.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **MUST be completed first** to provide the verifier for US2.
- **User Story 2 (P2)**: Depends on US1 (verifier) and Foundational. Requires the symbolic planner and LLM setup.
- **User Story 3 (P3)**: Depends on US1 and US2 to generate the data logs required for analysis.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Verifiers
- Verifiers before Evolutionary Loop
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for generator in tests/unit/test_generator.py::test_generator_handles_empty_input"
Task: "Unit test for verifier in tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution"

# Launch all models for User Story 1 together:
Task: "Implement code/dataset/generator.py"
Task: "Curate initial dataset in data/raw/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Dataset + Verifier)
4. **STOP and VALIDATE**: Test User Story 1 independently (run verifier on known solutions)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Hybrid Loop)
4. Add User Story 3 → Test independently → Deploy/Demo (Analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Dataset/Verifier)
 - Developer B: User Story 2 (Symbolic/LLM Loop)
 - Developer C: User Story 3 (Analysis/Stats)
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
- **CRITICAL**: All LLM tasks must use CPU-only models (no CUDA, no bitsandbytes).
- **CRITICAL**: All puzzle data must be real or deterministically generated; no fake data.
- **CRITICAL**: The symbolic planner must handle constraint failures gracefully (exclude and log).
- **CRITICAL**: The verifier MUST fail loudly (raise exception) on real data fetch failures; NEVER fall back to synthetic data.
- **CRITICAL**: Phase 7 tasks are mandatory to address the "Fabrication Risk" and "Statistical Power" concerns raised in the initial review.
- **CRITICAL**: T027 (Z-test) is the primary mandated test. T032 (TOST) is optional/secondary.
- **CRITICAL**: T029a/b requires R^2 validation for complexity characterization and must output 'complexity_class' and 'status' fields.
- **CRITICAL**: T030c renamed to 'Execute Full Symbolic Experiments'; T030d added for Neural Subset Baseline.
- **CRITICAL**: T040b documents the impossibility of empirical GPU calibration on CPU runners and updates Plan status.
- **CRITICAL**: T013c now depends on T013d artifact to resolve circular dependency.
- **CRITICAL**: T007b and T007c are sequential (T007b -> T007c) to avoid parallel state mutation.
- **CRITICAL**: T026 reads TDP from `calibrated_tdp.json` and fails if missing.
- **CRITICAL**: T031a generates machine-readable stats before T031b generates the report.
- **CRITICAL**: T021 uses `distilbert-tiny` with `optimum` quantization for CPU feasibility.