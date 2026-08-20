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

- [X] T000a-def [P] Define JSON schema for puzzle instances in `contracts/dataset.schema.yaml`. **Constraint**: Must define fields: `constraints`, `initial_state`, `target_state`, and `verifier_output` format. **Dependency**: None.
- [X] T000a-gen [P] Generate `contracts/dataset.schema.yaml` from T000a-def definitions. **Constraint**: Must validate the schema against `data-model.md` requirements. **Dependency**: Requires T000a-def.
- [X] T000b-def [P] Define JSON schema for output files in `contracts/output.schema.yaml`. **Constraint**: Must define schemas for `data/processed/exclusions.json` and `data/processed/distribution_report.json`. **Dependency**: None.
- [X] T000b-gen [P] Generate `contracts/output.schema.yaml` from T000b-def definitions. **Constraint**: Must validate the schema against `plan.md` requirements. **Dependency**: Requires T000b-def.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `data/` directory hierarchy: `data/raw`, `data/processed`. **Constraint**: Must verify directories exist and are writable.
- [X] T001b [P] Create `code/` directory hierarchy: `code/{dataset,symbolic,bes,analysis,utils}`. **Constraint**: Must verify directories exist and are writable.
- [X] T001c [P] Create `tests/` directory hierarchy: `tests/{unit,integration}`. **Constraint**: Must verify directories exist and are writable.

- [X] T002a Initialize git repository and configure basic `.gitignore` for Python artifacts

- [X] T002b Initialize Python virtual environment in `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/`

- [X] T002c Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.0`, `numpy==1.24.0`, `transformers==4.35.0`, `datasets==2.14.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `optimum>=1.13.0,<1.16.0[onnxruntime]`. **Constraint**: Use fixed versions from plan.md. Must specify `optimum[onnxruntime]` for CPU-optimized quantization flags. Do not attempt to read from `research.md` as its schema is undefined.

- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Constraint**: Must generate `.flake8` and `pyproject.toml` (for black) configuration files to satisfy plan.md testing requirements.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw` for immutable puzzles, `data/processed` for logs/results. **Constraint**: Must verify directories exist and are writable.

- [X] T005a-impl [P] [US1] Implement base logging infrastructure in `code/__init__.py` to capture wall-clock time and resource usage; output must be JSON format to `data/processed/experiment.log`. **Constraint**: Must include a verification step: Add a unit test in `tests/unit/test_logging.py::test_log_format_is_json` to validate the output format matches the schema.
- [X] T005a-test [P] [US1] Add unit test for log format in `tests/unit/test_logging.py`. **Constraint**: Must validate JSON structure. **Dependency**: Requires T005a-impl.

- [X] T005b [P] [US1] Implement CPU utilization monitoring in `code/utils/monitor.py` using `psutil` to log `cpu_percent` for every execution step. **Constraint**: Must log at the same frequency as T005a.

- [X] T006 [P] [US1] Setup random seed management utility in `code/utils/seed.py` for reproducibility

- [X] T007 [P] [US1] Create base configuration loader in `code/config.py` to handle experiment parameters (population size, generations). **Constraint**: Must be functional before T007b runs.

- [X] T007b [US1] Initialize `code/config.py` with `DEFAULT_TDP_WATTS` as a placeholder (e.g., 0.0). **Constraint**: This value MUST be overwritten by T008c after calibration. **Dependency**: Requires T007 (implementation) and T008c (to overwrite). **Action**: If T008c is not run, the system MUST log a warning but continue execution. **Verification**: Must add unit test `tests/unit/test_config.py::test_tdp_placeholder_exists` that asserts the key exists AND that its value is non-zero/non-default.

- [X] T008a-impl [US1] Implement TDP Calibration Script in `code/utils/calibrate_tdp.py`. **Constraint**: Must detect the runner's CPU model (e.g., via `platform.machine()` or `lscpu`) and select a TDP value from a pinned lookup table `data/raw/cpu_tdp_map.json` specific to that model class. Must output `data/processed/calibration_run.json` with fields: `workload_type`, `cpu_percent`, `duration`, `estimated_tdp_watts` (derived from pinned table). **Dependency**: None.
- [X] T008a-exec [US1] Execute TDP Calibration Script. **Constraint**: Must run T008a-impl. **Dependency**: Requires T008a-impl.
- [X] T008c [US1] Implement TDP Constant Generation Script in `code/utils/generate_tdp_constant.py`. **Constraint**: Must read `data/processed/calibration_run.json` (from T008a-exec) and generate `data/processed/calibrated_tdp.json` with fields: `tdp_watts`, `source` ("pinned-litterature"), `error_margin`, `confidence_interval`. **Dependency**: Requires T008a-exec. **Verification**: Must add unit test `tests/unit/test_calibrated_tdp.py::test_tdp_constant_valid` that asserts `data/processed/calibrated_tdp.json` exists, `tdp_watts` > 0, and `source` is present.

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

- [X] T014c-impl [P] [US1] Implement `code/dataset/generate_and_validate.py`. **Constraint**: This script MUST accept a directory of raw puzzles, run the verifier, calculate checksums, and output `data/processed/distribution_report.json` with type/complexity distribution stats. Must strictly enforce "Fail Loudly" (no synthetic fallback). **Dependency**: Requires T011 and T012.
- [X] T014c-exec [P] [US1] Execute `code/dataset/generate_and_validate.py`. **Constraint**: Must run with parameters `--n 500 --count 10 --types sudoku,pathfinding`. **Dependency**: Requires T014c-impl.

- [X] T014e-impl [US1] Implement `code/dataset/validate_distribution.py`. **Constraint**: This script MUST read `data/processed/distribution_report.json` (from T014c-exec) and `contracts/dataset.schema.yaml` (from T000a-gen) to verify statistical representativeness and output `data/processed/distribution_validation.json` with fields: `is_valid`, `power_estimate`, `notes`. **Dependency**: Requires T014c-impl.
- [X] T014e-exec [US1] Execute `code/dataset/validate_distribution.py`. **Constraint**: Must run after T014e-impl. **Dependency**: Requires T014e-impl.

- [X] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. The JSON schema MUST be: `{"status": "PASS"|"FAIL", "reason": "string", "distribution_stats": {...}}`. **Dependency**: Requires T014e-exec.
- [X] T036b-verify [P] [US1] Verify `validation_gate.json` schema. **Constraint**: Add a unit test `tests/unit/test_validation_gate.py::test_schema_valid` that asserts the JSON structure matches the required schema. **Dependency**: Requires T036.

- [X] T044a-impl [US1] Implement strict "Fail Loudly" logic in `code/dataset/generator.py`. **Constraint**: Must remove any try/except blocks that catch `DataGenerationError` or similar and substitute mock data. If the puzzle generation fails (e.g., constraint parsing error), the script must raise an exception and halt execution immediately. **Rationale**: Addresses the "Fabrication Gate" requirement. **Dependency**: Requires T011.
- [X] T044b-verify [US1] Verify "Fail Loudly" logic in `code/dataset/generator.py`. **Constraint**: Add a unit test that attempts to generate invalid data and confirms the script halts with an exception. **Dependency**: Requires T044a-impl.

- [X] T045a-impl [US1] Add explicit "Sample Size Declaration" to `code/dataset/generate_and_validate.py`. **Constraint**: The script must output a `sample_size` field in `data/processed/distribution_report.json` and explicitly state the sampling rule (e.g., "First N=200 rows", "Random seed 42") if a subset is used. **Rationale**: Ensures transparency about data representativeness. **Dependency**: Requires T014c-impl.
- [X] T045b-verify [US1] Verify "Sample Size Declaration" in `data/processed/distribution_report.json`. **Constraint**: Add a test to verify the presence and correctness of the `sample_size` field. **Dependency**: Requires T045a-impl.

- [X] T050a-impl [US1] Implement "Fail Loudly" enforcement in `code/dataset/verifier.py`. **Constraint**: Ensure the verifier raises a specific `VerifierError` if the deterministic script fails to execute or returns an unexpected type, preventing silent fallback to "invalid" for system errors. **Rationale**: Addresses the "Fail Loudly" principle for data integrity. **Dependency**: Requires T012.
- [X] T050b-verify [US1] Verify "Fail Loudly" in verifier. **Constraint**: Add a unit test that simulates a verifier script crash and confirms the system raises an exception rather than returning a boolean. **Dependency**: Requires T050a-impl.

- [X] T054a-impl [US1] Implement "Complexity Scaling" validation in `code/dataset/generator.py`. **Constraint**: The generator must output a `complexity_metric` for each puzzle and verify that the distribution of these metrics is continuous across the N=10..500 range. **Rationale**: Ensures SC-005 (Scalability) can be measured. **Dependency**: Requires T011.
- [X] T054b-verify [US1] Verify "Complexity Scaling" distribution. **Constraint**: Add a test that generates a small set and verifies the `complexity_metric` spans the expected range. **Dependency**: Requires T054a-impl.

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

- [X] T019d [US2] Implement `code/symbolic/exclusion_logger.py` to write exclusion events to `data/processed/exclusions.json`. **Constraint**: Must strictly adhere to the schema defined in `contracts/output.schema.yaml` (T000b-gen).
- [X] T019d-verify [US2] Verify exclusion logger schema. **Constraint**: Add a unit test `tests/unit/test_exclusion_logger.py::test_schema_valid` that asserts the JSON structure matches the required schema. **Dependency**: Requires T019d.

- [X] T020 [P] [US2] Generate `code/bes/config.py` with configuration for a small pre-trained LLM (`distilbert-base-uncased`). **Constraint**: This task is for **configuration file generation ONLY** (no download). Must specify `device='cpu'` and forbid `bitsandbytes` in the config file. **Dependency**: None.

- [X] T021b [US2] Download the `distilbert-base-uncased` model artifact to the cache directory *before* executing T021. **Constraint**: This task is for **execution only** (downloading the model). **Dependency**: Requires T020.

- [X] T021 [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must load the model specified in `code/bes/config.py` (default `distilbert-base-uncased`) using `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`, quantized precision) and specify exact Hugging Face model ID from config. Must enforce CPU-only constraints. **Dependency**: Requires T020, T021b.

- [X] T022 [P] [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [X] T023 [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [X] T024a [US2] Implement `code/bes/parameter_generator.py` to generate the list of complexity parameters (N=10..500) for the BES loop. **Constraint**: Must output a JSON list of parameter sets. **Dependency**: None.
- [X] T024b [US2] Implement `code/bes/loop_runner.py` to execute the BES loop for a single parameter set (N). **Constraint**: Must accept parameters from T024a, run the loop, and output a log file for that N. **Dependency**: Requires T024a, T021, T023.
- [X] T024c [US2] Implement `code/bes/result_aggregator.py` to aggregate logs from T024b into a single result file. **Constraint**: Must combine all N-specific logs into `data/processed/bes_results.json`. **Dependency**: Requires T024b.

- [X] T046a-impl [US2] Verify "Real Data" flow in `code/bes/main.py`. **Constraint**: Add a runtime check that asserts `data/processed/distribution_validation.json` (from T036) exists and has `status: PASS` before the BES loop starts. If validation fails, the main loop must exit with a clear error message. **Rationale**: Ensures the evolutionary loop never runs on unverified data. **Dependency**: Requires T024a/b/c and T036.
- [X] T046b-verify [US2] Verify "Real Data" flow check. **Constraint**: Add an integration test that attempts to run the BES loop without valid distribution validation and confirms it halts. **Dependency**: Requires T046a-impl.

- [X] T048a-impl [US2] Implement "Logical Contradiction" detection in `code/symbolic/planner.py`. **Constraint**: The planner MUST implement logic to detect and flag logical contradictions in the generated sub-goals and raise an exception if a contradiction is found. **Rationale**: Addresses the Edge Case in spec.md.
- [X] T048b-verify [US2] Verify "Logical Contradiction" detection. **Constraint**: Add a unit test to `tests/unit/test_symbolic_planner.py` that specifically tests the contradiction detection logic in `code/symbolic/planner.py`.

- [X] T051a-impl [US2] Implement "Sub-goal Consistency" check in `code/symbolic/planner.py`. **Constraint**: Before returning sub-goals, the planner must verify that the union of sub-goals does not logically contradict the initial state or the target state (e.g., via a lightweight SAT check or rule intersection). **Rationale**: Addresses the Edge Case regarding logically impossible sub-goals. **Dependency**: Requires T019.
- [X] T051b-verify [US2] Verify "Sub-goal Consistency". **Constraint**: Add a unit test that feeds a puzzle with an impossible constraint set and confirms the planner flags it as `CONTRADICTION_DETECTED` rather than generating invalid sub-goals. **Dependency**: Requires T051a-impl.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

**Goal**: Record success rates and computational costs for both symbolic-guided and neural-verifier baselines, applying statistical tests for significance.

**Independent Test**: Feed synthetic success rate data with known differences to the analysis script to verify z-test and t-test accuracy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for `code/analysis/stats.py` with synthetic data in `tests/unit/test_stats.py::test_z_test_identifies_significance`

### Implementation for User Story 3

- [X] T040b [US3] Generate Literature-based GPU Conversion Factor. **Constraint**: Since the target runner (GitHub Actions) is CPU-only, empirical GPU calibration is impossible. This task MUST document this limitation and output `data/processed/literature_gpu_factor.json` with a selected conversion factor and citation. The JSON MUST explicitly state that the 'GPU-hours' metric is an *Estimated* value based on literature sources. **Required Keys**: `factor`, `citation_url`, `source_type`, `estimated_gpu_hours_per_cpu_second`.
- [X] T040c [US3] Implement AND run the Validated Conversion Factor logic in `code/analysis/metrics.py`. **Constraint**: This script MUST read `data/processed/literature_gpu_factor.json` (from T040b) and verify that it is not zero before use.

- [X] T027 [US3] Implement `code/analysis/metrics.py` to calculate success rates, wall-clock time, and energy consumption (Joules) from execution logs. **Constraint**: Must read data from the logged CPU-percent and TDP values calculated in Phase 1; any missing or invalid calibration data MUST result in a task failure - no fallback is allowed.

- [X] T027b [US3] Implement two-proportion z-test in `code/analysis/stats.py` to compare success rates (as mandated by FR-005) with null hypothesis H0: p1 = p2 and alpha=0.05. **Note**: This is the primary statistical test required by the spec.

- [X] T028a [US3] Implement statistical framework pre-registration logic in `code/analysis/stats.py` to define and log the choice between 'equivalence' (TOST) and 'non-inferiority' frameworks before running tests, satisfying SC-001's pre-registration requirement.
- [X] T028b [US3] Execute Pre-Registration. **Constraint**: This task MUST write the pre-registration configuration defined in T028a to `data/processed/pre_registration.yaml` before any experiments are run. **Dependency**: Requires T028a.
- [X] T028c-verify [US3] Verify Pre-Registration Artifact. **Constraint**: Add a unit test `tests/unit/test_pre_registration.py::test_pre_registration_exists` that asserts `data/processed/pre_registration.yaml` exists and contains valid framework choice. **Dependency**: Requires T028b.

- [X] T029b-exec [US3] Execute Pilot Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` on a small subset (N=10..50) to profile runtime and memory, including checkpointing for long runs and configurable timeouts. **Dependency**: Requires T024a/b/c (BES loop logic).
- [X] T029b-profile [US3] Profile runtime and memory from Pilot Scaling Experiments. **Constraint**: Analyze logs from T029b-exec to determine memory footprint and runtime per puzzle. **Dependency**: Requires T029b-exec.

- [X] T029c-exec [US3] Execute Full Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` across the full complexity scaling range (N=10..500) to generate raw logs, including checkpointing and configurable timeouts. The output MUST include timestamps, CPU-percent, and durations for each puzzle attempt. **Dependency**: Requires T024a/b/c (BES loop logic).
- [X] T029c-gen [US3] Generate `data/processed/scaling_raw_logs.json` from T029c-exec. **Constraint**: Aggregate raw logs from T029c-exec into the final JSON format. **Required Schema**: List of objects with `puzzle_id`, `duration`, `cpu_percent`, `success`, `timestamp`. **Dependency**: Requires T029c-exec.

- [X] T042a-exec [US3] Execute the neural_baseline run. **Constraint**: Execute `code/main.py` with `--mode neural` on the same subset as T029c-exec to measure CPU time for baseline estimation. **Dependency**: Requires T024a/b/c.
- [X] T042b-gen [US3] Generate `data/processed/neural_baseline_logs.json` from T042a-exec. **Constraint**: Aggregate raw logs from T042a-exec into the final JSON format. **Required Schema**: List of objects with `puzzle_id`, `duration`, `cpu_percent`, `success`, `timestamp`. **Dependency**: Requires T042a-exec.

- [X] T029d-exec [US3] Execute Scalability Analysis Script. **Constraint**: Run the analysis script on `data/processed/scaling_raw_logs.json` and `data/processed/neural_baseline_logs.json`. **Dependency**: Requires T029c-gen, T042b-gen.
- [X] T029d-derive [US3] Derive complexity class from T029d-exec results. **Constraint**: Perform comparative log-log linear regression on BOTH Symbolic and Neural solver slopes to determine the computational complexity class of the *approach* (SC-005). If R^2 < 0.85, assign 'UNKNOWN'. **Dependency**: Requires T029d-exec.

- [X] T029g [US3] Compare solver slopes for complexity class verification. **Constraint**: Compare the slopes of the Symbolic vs. Neural solvers from `data/processed/scaling_raw_logs.json` and `data/processed/neural_baseline_logs.json` to determine the computational complexity class of the *approach* (SC-005). This task must explicitly compare different solvers. **Dependency**: Requires T029d-derive, T042b-gen.

- [X] T031a [US3] Implement machine-readable results writing logic in `code/analysis/stats.py`. **Constraint**: Must output `data/processed/stats_results.json` containing p-values, confidence intervals, and test statistics. **Dependency**: Requires T027b, T029g.

- [X] T031b-impl [US3] Implement report generation logic in `code/analysis/report.py`. **Constraint**: Must handle partial data scenarios: if energy metrics are missing, mark section as 'Not Available'; if complexity analysis is missing, mark section as 'Not Available'. **Dependency**: Requires T031a, T029g.
- [X] T031b-gen [US3] Generate final report in `data/processed/final_report.md` (Markdown format). **Constraint**: Must run after T031b-impl. **Dependency**: Requires T031b-impl.

- [X] T049a-impl [US3] Add "Power Analysis" output to `data/processed/final_report.md`. **Constraint**: The final report must include a section explicitly stating the calculated statistical power for the observed effect size. If power < 0.8, the report must flag the result as "Underpowered" and recommend a larger sample size. **Rationale**: Ensures the statistical conclusion is scientifically defensible. **Dependency**: Requires T027b and T031b-gen.
- [X] T049b-verify [US3] Verify "Power Analysis" output. **Constraint**: Add a test to verify the presence of the power analysis section in the final report. **Dependency**: Requires T049a-impl.

- [X] T052a-impl [US3] Implement "Statistical Power" calculation in `code/analysis/stats.py`. **Constraint**: The stats module must calculate post-hoc power (1-β) for the observed effect size using the sample size and variance from the logs. **Rationale**: Ensures the study is not underpowered (SC-001). **Dependency**: Requires T027b.
- [X] T052b-verify [US3] Verify "Power" calculation. **Constraint**: Add a unit test with known inputs to verify the power calculation matches standard statistical libraries. **Dependency**: Requires T052a-impl.

- [X] T053a-impl [US3] Implement "Literature Factor" validation in `code/analysis/metrics.py`. **Constraint**: The code must explicitly check that the `literature_gpu_factor.json` contains a valid DOI or URL before using the conversion factor, failing loudly if missing. **Rationale**: Ensures "Verified Accuracy" (Principle II). **Dependency**: Requires T040b.
- [X] T053b-verify [US3] Verify "Literature Factor" validation. **Constraint**: Add a test that attempts to run analysis with a missing citation field and confirms the process halts. **Dependency**: Requires T053a-impl.

- [X] T055a-impl [US3] Implement "Baseline Equivalence" check in `code/analysis/stats.py`. **Constraint**: Before running the z-test, the code must verify that the baseline (neural) and experimental (symbolic) groups were run on the same puzzle subset to ensure a fair comparison. **Rationale**: Addresses the validity of the experimental design. **Dependency**: Requires T027b.
- [X] T055b-verify [US3] Verify "Baseline Equivalence" check. **Constraint**: Add a test that attempts to run the z-test on mismatched puzzle IDs and confirms the system halts. **Dependency**: Requires T055a-impl.

- [X] T035 [US3] Final Review and Artifact Verification. **Constraint**: Verify all required artifacts (`pre_registration.yaml`, `scaling_raw_logs.json`, `literature_gpu_factor.json`, `calibrated_tdp.json`, `neural_baseline_logs.json`) exist and match schemas before finalizing the project.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T015 [US1] Implement specific validation task for non-linear constraints edge case. **Constraint**: Create a dedicated test script `code/dataset/validate_edge_cases.py` that specifically attempts to parse non-linear constraints and verifies that the system logs the failure correctly (as per Edge Cases in spec) rather than crashing. **Dependency**: Requires T018 and T019.

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific concerns raised during the analysis phase to ensure robustness and compliance with data hygiene principles.

- [X] T043a-impl [US3] Update `code/analysis/stats.py` to include the z-test comparison logic. **Constraint**: Must implement the two-proportion z-test comparing symbolic vs. neural success rates. **Dependency**: Requires T027b.
- [X] T043b-exec [US3] Execute z-test comparison. **Constraint**: Run the z-test on the aggregated logs from T029c-gen and T042b-gen. **Dependency**: Requires T043a-impl, T029c-gen, T042b-gen.
