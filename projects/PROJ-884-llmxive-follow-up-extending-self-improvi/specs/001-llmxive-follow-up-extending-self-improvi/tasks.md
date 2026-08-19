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

- [X] T000a [P] Generate `contracts/dataset.schema.yaml` based on `data-model.md` and `plan.md` requirements. **Constraint**: Must define the exact JSON schema for puzzle instances including fields: `constraints`, `initial_state`, `target_state`, and `verifier_output` format. This task MUST complete before T014c.

- [X] T000b [P] Generate `contracts/output.schema.yaml` based on `plan.md` requirements for experiment logs and analysis results. **Constraint**: Must explicitly define the schema for `data/processed/exclusions.json` (fields: `puzzle_id`, `reason_code`, `timestamp`) and `data/processed/distribution_report.json` (fields: `total_count`, `type_distribution`, `complexity_distribution`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `data/` directory hierarchy: `data/raw`, `data/processed`. **Constraint**: Must verify directories exist and are writable.
- [X] T001b [P] Create `code/` directory hierarchy: `code/{dataset,symbolic,bes,analysis,utils}`. **Constraint**: Must verify directories exist and are writable.
- [X] T001c [P] Create `tests/` directory hierarchy: `tests/{unit,integration}`. **Constraint**: Must verify directories exist and are writable.

- [X] T002a Initialize git repository and configure basic `.gitignore` for Python artifacts

- [X] T002b Initialize Python 3.11 virtual environment in `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/`

- [X] T002c Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.0`, `numpy==1.24.0`, `transformers==4.35.0`, `datasets==2.14.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `optimum==1.13.0`, `psutil==5.9.0`. **Constraint**: Use fixed versions from plan.md. Do not attempt to read from `research.md` as its schema is undefined.

- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Constraint**: Must generate `.flake8` and `pyproject.toml` (for black) configuration files to satisfy plan.md testing requirements.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw` for immutable puzzles, `data/processed` for logs/results. **Constraint**: Must verify directories exist and are writable.

- [X] T005a [P] [US1] Implement base logging infrastructure in `code/__init__.py` to capture wall-clock time and resource usage; output must be JSON format to `data/processed/experiment.log`. **Constraint**: Must include a verification step: Add a unit test in `tests/unit/test_logging.py::test_log_format_is_json` to validate the output format matches the schema.

- [X] T005b [P] [US1] Implement CPU utilization monitoring in `code/utils/monitor.py` using `psutil` to log `cpu_percent` for every execution step. **Constraint**: Must log at the same frequency as T005a.

- [X] T006 [P] [US1] Setup random seed management utility in `code/utils/seed.py` for reproducibility

- [X] T007 [P] [US1] Create base configuration loader in `code/config.py` to handle experiment parameters (population size, generations)

- [X] T007b [US1] Initialize `code/config.py` with `DEFAULT_TDP_WATTS` as a placeholder (e.g., 0.0). **Constraint**: This value MUST be overwritten by T008c after calibration. **Dependency**: None.

- [ ] T008a [US1] Implement TDP Calibration Script in `code/utils/calibrate_tdp.py`. **Constraint**: Must run a standard, deterministic workload (e.g., a fixed matrix multiplication) on the current runner and measure power consumption via `psutil` or a similar method to estimate TDP. **Action**: T008a MUST output `data/processed/calibration_run.json` with fields: `workload_type`, `cpu_percent`, `duration`, `estimated_tdp_watts`. **Dependency**: Requires T007b.

- [ ] T008c [US1] Implement TDP Constant Generation Script in `code/utils/generate_tdp_constant.py`. **Constraint**: Must read `data/processed/calibration_run.json` (from T008a) and generate `data/processed/calibrated_tdp.json` with fields: `tdp_watts`, `source` ("calibration"), `error_margin`, `confidence_interval`.  **Action**: THIS TASK MUST FAIL if calibration is unsuccessful or TDP cannot be determined - NO fallback to a constant value. **Dependency**: Requires T008a.

- [X] T008 Setup error handling framework by creating `code/exceptions.py` defining custom exception classes for `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, and `VERIFIER_ERROR` (to handle internal verifier failures, addressing robustness gap)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Instantiate a dataset of logic/arithmetic puzzles with deterministic Python verifiers capable of validating solution paths without LLMs.

**Independent Test**: Run verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [US1] Contract test for `code/dataset/generator.py` in `tests/unit/test_generator.py::test_generator_handles_empty_input`

- [X] T010 [US1] Unit test for `code/dataset/verifier.py` with known valid/invalid solutions in `tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/dataset/generator.py` to create logic puzzles (Sudoku variants, constrained pathfinding) with systematic complexity scaling (N=10..500). **Constraint**: Must support command-line arguments for `N` and `count`.

- [X] T012 [US1] Implement `code/dataset/verifier.py` to execute deterministic validation logic for each puzzle instance, returning boolean validity and specific constraint violation codes (e.g., `DUPLICATE_ROW`, `INVALID_PATH`) within 100ms. **Note**: T012 validates the code, T014c/b generates the data.

- [X] T014c [P] [US1] Implement `code/dataset/generate_and_validate.py`. **Constraint**: This script MUST accept a directory of raw puzzles, run the verifier, calculate checksums, and output `data/processed/distribution_report.json` with type/complexity distribution stats. Must strictly enforce "Fail Loudly" (no synthetic fallback). **Dependency**: Requires T011 and T012.

- [X] T014d [US1] Execute `code/dataset/generate_and_validate.py` to finalize the dataset and generate `data/processed/distribution_report.json`. **Constraint**: Must run with parameters `--n 200 500 --count 10 --types sudoku,pathfinding`. **Dependency**: Requires T011 and T014c.

- [ ] T014e [US1] Implement `code/dataset/validate_distribution.py`. **Constraint**: This script MUST read `data/processed/distribution_report.json` (from T014d) and `contracts/dataset.schema.yaml` (from T000b) to verify statistical representativeness and output `data/processed/distribution_validation.json` with fields: `is_valid`, `power_estimate`, `notes`. **Dependency**: Requires T014c.

- [X] T014f [US1] Execute `code/dataset/validate_distribution.py` to generate `data/processed/distribution_validation.json`. **Constraint**: Must run after T014d. **Dependency**: Requires T014e and T014d.

- [X] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. **Dependency**: Requires T014f.

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

- [X] T019 [US2] Implement `code/symbolic/planner.py` to generate sub-goal decompositions, including logic to detect and flag `CONTRADICTION_DETECTED` or `PARSE_FAILURE`. **Constraint**: Must include the logic to call the exclusion logger directly within this module or via a helper.

- [X] T019d [US2] Implement `code/symbolic/exclusion_logger.py` to write exclusion events to `data/processed/exclusions.json`. **Constraint**: Must strictly adhere to the schema defined in `contracts/output.schema.yaml` (T000b).

- [X] T020 [P] [US2] Generate `code/bes/config.py` with configuration for a small pre-trained LLM (`distilbert-tiny`). **Constraint**: This task is for **configuration file generation ONLY** (no download). Must specify `device='cpu'` and forbid `bitsandbytes` in the config file. **Dependency**: None.

- [X] T021 [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must download and load the model specified in `code/bes/config.py` using `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`, quantized precision) and specify exact Hugging Face model ID `distilbert-tiny` with pinned `revision` hash for reproducibility. Must enforce CPU-only constraints. **Dependency**: Requires T020.

- [X] T021b [US2] Download the `distilbert-tiny` model artifact to the cache directory. **Constraint**: This task is for **execution only** (downloading the model). **Dependency**: Requires T021.

- [X] T022 [P] [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [X] T023 [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [X] T024 [US2] Implement the main BES loop in `code/main.py` to orchestrate forward (LLM) and backward (Symbolic) steps, logging all transitions. **Constraint**: Must explicitly execute the loop across the full complexity scaling range (N=10..500) to generate data for T029b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

**Goal**: Record success rates and computational costs for both symbolic-guided and neural-verifier baselines, applying statistical tests for significance.

**Independent Test**: Feed synthetic success rate data with known differences to the analysis script to verify z-test and t-test accuracy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `code/analysis/stats.py` with synthetic data in `tests/unit/test_stats.py::test_z_test_identifies_significance`

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/analysis/metrics.py` to calculate success rates, wall-clock time, and energy consumption (Joules) from execution logs. **Constraint**: Must read data from the logged CPU-percent and TDP values calculated in Phase 1; any missing or invalid calibration data MUST result in a task failure - no fallback is allowed.

- [X] T027b [US3] Implement two-proportion z-test in `code/analysis/stats.py` to compare success rates (as mandated by FR-005) with null hypothesis H0: p1 = p2 and alpha=0.05. **Note**: This is the primary statistical test required by the spec.

- [X] T028a [US3] Implement statistical framework pre-registration logic in `code/analysis/stats.py` to define and log the choice between 'equivalence' (TOST) and 'non-inferiority' frameworks before running tests, satisfying SC-001's pre-registration requirement.

- [ ] T029b [US3] Run Pilot Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` on a small subset (N=10..50) to profile runtime and memory. **Dependency**: Requires T024 (BES loop logic).

- [ ] T029c [US3] Run Full Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` across the full complexity scaling range (N=10..500) to generate data/processed/scaling_raw_logs.json. The output MUST include timestamps, CPU-percent, and durations for each puzzle attempt. **Dependency**: Requires T024 (BES loop logic).

- [ ] T029d [US3] Execute Scalability Analysis. **Constraint**: Perform log-log linear regression on `data/processed/scaling_raw_logs.json` to derive the complexity class (Big-O). If R^2 < 0.85, assign a complexity class of 'UNKNOWN'.  Output MUST be written to data/processed/scaling_analysis.csv with columns: `n`, `time`, `complexity_class` (e.g., 'O(n)', 'O(n^2)', or 'UNKNOWN'), `r_squared`. **Dependency**: Requires T029e.

- [ ] T029e [US3] Implement Scalability Analysis Logic. **Constraint**: Write the logic for log-log linear regression and complexity class mapping in code/analysis/scaling.py. **Dependency**: None.

- [X] T031a [US3] Implement machine-readable results writing logic in `code/analysis/stats.py`. **Constraint**: Must output `data/processed/stats_results.json` containing p-values, confidence intervals, and test statistics. **Dependency**: Requires T027b, T029d, and T031a

- [X] T031b [US3] Generate final report in `data/processed/final_report.md` (Markdown format) containing sections: Success Rate Comparison, Cost Comparison, Complexity Analysis, and Statistical Significance (p-values). **Constraint**: Must handle partial data scenarios: if energy metrics are missing, mark section as 'Not Available'; if complexity analysis is missing, mark section as 'Not Available'. **Note**: Depends on T031a (machine-readable stats), T029d (complexity) and T027b.

- [X] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. **Dependency**: Requires T014f.

- [X] T037a [US3] Validate `data/processed/exclusions.json` against the schema. **Constraint**: Must verify that the file exists, matches the schema defined in `contracts/output.schema.yaml` (T000b), and contains entries for all symbolic failures logged by T019d. **Dependency**: Requires T019d and T000b.

- [X] T037b [US3] Validate `data/processed/exclusions.json` content integrity. **Constraint**: Must ensure all logged exclusions have a corresponding `reason_code` and `puzzle_id`. **Dependency**: Requires T037a.

- [X] T038 [US3] Implement Power Analysis Check. **Constraint**: Before running T027b (Z-test), calculate statistical power based on N and observed effect size. If power < 0.8, flag the result as "Underpowered" and output a recommendation to increase sample size. **Dependency**: Requires T036 (validated dataset) and T029d/T027b (results).

- [X] T039 [US3] Documentation updates in `README.md`. **Constraint**: Must include sections on: 1) How to run the BES loop, 2) How to interpret results (success rates, p-values), 3) How to handle exclusions (referencing `exclusions.json`). **Dependency**: Requires T031b (Final Report) for context.

- [X] T040b [US3] Generate Literature-based GPU Conversion Factor. **Constraint**: Since the target runner (GitHub Actions) is CPU-only, empirical GPU calibration is impossible. This task MUST document this limitation and output data/processed/literature_gpu_factor.json with a selected conversion factor and citation.  The JSON MUST explicitly state that the 'GPU-hours' metric is an *Estimated* value based on literature sources.

- [X] T040c [US3] Implement AND run the Validated Conversion Factor logic in `code/analysis/metrics.py`. This task now implements the conversion factor loading, and it also runs a basic validation to ensure that the loaded factor is not zero. Dependency: Requires T040b and must be run *before* T027 (Metrics).

- [ ] T030a [US3] Implement `--mode neural_subset` baseline execution, using a GPU for acceleration and reporting actual GPU runtime. **Constraint**: This task MUST require GPU access to measure accurate performance metrics; CPU-only runs are invalid for this task!
- [ ] T031a [US3] Execute the `neural_subset` baseline run with `--mode neural_subset`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [US3] Implement Optional Equivalence Testing (TOST) in `code/analysis/stats.py` as a secondary analysis, dependent on T027b results. **Constraint**: Only run if pre-registered in T028a. Must not override the mandatory z-test results from T027b.

- [X] T033 [P] Code cleanup and refactoring of `code/bes/` and `code/symbolic/` modules

- [X] T034 [US1] Implement strict "Fail Loudly" logic in `code/dataset/verifier.py` and `code/dataset/generator.py`. **Requirement**: Remove any try/except blocks that silently fallback to synthetic/mock data. If a real puzzle generation step fails or a constraint cannot be parsed, the script MUST raise a specific exception (e.g., `DataGenerationError`) and halt execution, ensuring no synthetic data is ever written to `data/raw/`. **Rationale**: Addresses the fabrication risk where real data fetches fail and are replaced by mock data.
