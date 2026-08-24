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

- [ ] T000c [P] Generate `research.md` documenting the Dataset Strategy (Synthetic Curation + Scaling Generation) and Statistical Analysis Plan. **Constraint**: Must explicitly define the dataset source, scaling method, and statistical framework (TOST, t-test). **Dependency**: None.
- [ ] T000d [P] Generate `data-model.md` defining the Statistical Plan and Data Entities. **Constraint**: Must explicitly define the `complexity_metric` mapping to asymptotic complexity for SC-005. **Dependency**: Requires T000c.
- [ ] T000a-def [P] Define the JSON schema structure for puzzle instances in text format. **Constraint**: Must define fields: `constraints` (array of strings), `initial_state` (object), `target_state` (object), `verifier_output` (object with `valid` boolean and `error_code` string), and `metadata` (object with `source_id`, `generation_seed`). Reference `data-model.md` section 2.1 for field definitions. **Dependency**: None.
- [ ] T000a-gen [P] Write the `contracts/dataset.schema.yaml` file from T000a-def definitions. **Constraint**: Must validate the schema against `data-model.md` requirements. **Dependency**: Requires T000a-def.
- [ ] T000a-verify [P] Verify `contracts/dataset.schema.yaml` syntax and schema validity. **Constraint**: Add a unit test `tests/unit/test_schema.py::test_dataset_schema_valid` that validates the YAML file. **Dependency**: Requires T000a-gen.
- [ ] T000b-def [P] Define the JSON schema structure for output files in text format. **Constraint**: Must define schemas for `data/processed/exclusions.json` and `data/processed/distribution_report.json`. Reference `plan.md` section 3.2 for field definitions. **Dependency**: None.
- [ ] T000b-gen [P] Write the `contracts/output.schema.yaml` file from T000b-def definitions. **Constraint**: Must validate the schema against `plan.md` requirements. **Dependency**: Requires T000b-def.
- [ ] T000b-verify [P] Verify `contracts/output.schema.yaml` syntax and schema validity. **Constraint**: Add a unit test `tests/unit/test_schema.py::test_output_schema_valid` that validates the YAML file. **Dependency**: Requires T000b-gen.
- [ ] T067 [P] [US3] Implement "Pre-Analysis Power Calculation" in `code/analysis/stats.py`. **Constraint**: Before any experimental run, the system must calculate the required sample size to achieve [deferred] power for a medium effect size (Cohen's h = 0.5, fixed constant) at alpha=0.05. If the planned sample size (N=10..500) is insufficient, the system MUST log a critical warning (but NOT halt execution, per Spec Assumptions) and proceed. **Rationale**: Prevents the "Underpowered" scenario identified in T049a by enforcing power constraints at the start, not just at the end. **Dependency**: Requires T000d.
- [ ] T067b-verify [P] [US3] Verify "Pre-Analysis Power" check. **Constraint**: Add a test that sets a tiny sample size (e.g., N=5) and confirms the system logs a warning before running the experiment. **Dependency**: Requires T067.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `data/` directory hierarchy: `data/raw`, `data/processed`. **Constraint**: Must verify directories exist and are writable.
- [ ] T001b [P] Create `code/` directory hierarchy: `code/{dataset,symbolic,bes,analysis,utils}`. **Constraint**: Must verify directories exist and are writable.
- [ ] T001c [P] Create `tests/` directory hierarchy: `tests/{unit,integration}`. **Constraint**: Must verify directories exist and are writable.

- [ ] T002a [P] Initialize git repository and configure basic `.gitignore` for Python artifacts. **Constraint**: Must include `__pycache__`, `*.pyc`, `.env`, `data/processed/*`, `!data/processed/.gitkeep`.

- [ ] T002b [P] Initialize Python virtual environment in `projects/PROJ-llmxive-follow-up-extending-self-improvi/`. **Constraint**: Must use `python3.11 -m venv .venv` and activate it via `source .venv/bin/activate`. Path relative to repo root.

- [ ] T002c [P] Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.0`, `numpy==1.24.0`, `transformers==4.35.0`, `datasets==2.14.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `optimum>=1.13.0,<1.16.0[onnxruntime]`. **Constraint**: Use fixed versions from plan.md. Must specify `optimum[onnxruntime]` for CPU-optimized quantization flags. Do NOT include `bitsandbytes`.

- [ ] T003 [P] Configure linting (flake8/black) and formatting tools. **Constraint**: Must generate `.flake8` and `pyproject.toml` (for black) configuration files to satisfy plan.md testing requirements.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure: `data/raw` for immutable puzzles, `data/processed` for logs/results. **Constraint**: Must verify directories exist and are writable.

- [ ] T005a-impl [P] [US1] Implement base logging infrastructure in `code/__init__.py` to capture wall-clock time and resource usage; output must be JSON format to `data/processed/experiment.log`. **Constraint**: Must produce valid JSON logging code.
- [ ] T005a-test [P] [US1] Add unit test for log format in `tests/unit/test_logging.py`. **Constraint**: Must validate JSON structure. **Dependency**: Requires T005a-impl.

- [ ] T005b [P] [US1] Implement CPU utilization monitoring in `code/utils/monitor.py` using `psutil` to log `cpu_percent` for every execution step. **Constraint**: Must log at the same frequency as T005a.

- [ ] T006 [P] [US1] Setup random seed management utility in `code/utils/seed.py` for reproducibility

- [ ] T007 [P] [US1] Create base configuration loader in `code/config.py` to handle experiment parameters (population size, generations). **Constraint**: Must be functional before T007b runs.

- [ ] T007b [P] [US1] Initialize `code/config.py` with `DEFAULT_TDP_WATTS = 0.0` as a placeholder. **Constraint**: This value MUST be overwritten by T008c after calibration. **Dependency**: Requires T007 (implementation). **Action**: If T008c is not run, the system MUST log a warning but continue execution. **Verification**: Must add unit test `tests/unit/test_config.py::test_tdp_placeholder_exists` that asserts the key exists AND that its value is exactly 0.0 (the placeholder state).

- [ ] T008a-impl [P] [US1] Implement TDP Calibration Script in `code/utils/calibrate_tdp.py`. **Constraint**: Must detect the runner's CPU model (e.g., via `platform.machine()` or `lscpu`) and select a TDP value from a pinned lookup table `data/raw/cpu_tdp_map.json` specific to that model class. The lookup table MUST include a `citation_url` for each TDP value derived from verified primary literature sources. Must output `data/processed/calibration_run.json` with fields: `workload_type`, `cpu_percent`, `duration`, `estimated_tdp_watts` (derived from pinned table). **Dependency**: None.
- [ ] T008a-exec [P] [US1] Execute TDP Calibration Script. **Constraint**: Must run T008a-impl. **Dependency**: Requires T008a-impl.
- [ ] T008c [P] [US1] Implement TDP Constant Generation Script in `code/utils/generate_tdp_constant.py`. **Constraint**: Must read `data/processed/calibration_run.json` (from T008a-exec) and `code/config.py` (from T007b) to generate `data/processed/calibrated_tdp.json` with fields: `tdp_watts`, `source` ("verified-literature"), `error_margin`, `confidence_interval`, `citation_url`. The `citation_url` MUST be verified against a primary source before the artifact is generated. **Dependency**: Requires T008a-exec and T007b. **Verification**: Must add unit test `tests/unit/test_calibrated_tdp.py::test_tdp_constant_valid` that asserts `data/processed/calibrated_tdp.json` exists, `tdp_watts` > 0, `source` is present, and `citation_url` is a valid URL.

- [ ] T008 [P] [US1] Setup error handling framework by creating `code/exceptions.py` defining custom exception classes for `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, and `VERIFIER_ERROR` (to handle internal verifier failures, addressing robustness gap)

- [ ] T019d-impl [P] [US2] Implement `code/symbolic/exclusion_logger.py` to write exclusion events to `data/processed/exclusions.json`. **Constraint**: Must strictly adhere to the schema defined in `contracts/output.schema.yaml` (T000b-gen). Must generate a syntactically correct file. **Dependency**: Requires T000b-gen.
- [ ] T019d-verify [P] [US2] Verify exclusion logger schema. **Constraint**: Add a unit test `tests/unit/test_exclusion_logger.py::test_schema_valid` that asserts the JSON structure matches the required schema. **Dependency**: Requires T019d-impl.

- [ ] T013 [P] [US2] Implement `code/symbolic/planner.py` to generate sub-goal decompositions, including logic to detect and flag `CONTRADICTION_DETECTED` or `PARSE_FAILURE`. **Constraint**: Must include the logic to call the exclusion logger (T019d-impl) directly within this module or via a helper. **Dependency**: Requires T019d-impl, T008.

- [ ] T018 [P] [US2] Implement `code/symbolic/parser.py` to convert puzzle constraints into a formal language parseable by the planner

- [ ] T020 [P] [US2] Generate `code/bes/config.py` with configuration for a small pre-trained LLM (`distilbert-base-uncased`). **Constraint**: This task is for **configuration file generation ONLY** (no download). Must specify `device='cpu'` and explicitly forbid `bitsandbytes`. Must explicitly mandate `optimum.onnxruntime` for CPU execution. **Dependency**: None.

- [ ] T021b [P] [US2] Download the `distilbert-base-uncased` model artifact to the cache directory *before* executing T021. **Constraint**: This task is for **execution only** (downloading the model). Must use `huggingface-cli download distilbert-base-uncased` to fetch the model. **Dependency**: Requires T020.

- [ ] T021 [P] [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must load the model specified in `code/bes/config.py` (default `distilbert-base-uncased`) using `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`, `optimum.onnxruntime`). Do NOT force 8-bit quantization unless verified. **Dependency**: Requires T020, T021b.

- [ ] T022 [P] [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [ ] T023 [P] [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [ ] T024a [P] [US2] Implement `code/bes/parameter_generator.py` to generate the list of complexity parameters (N=10..500) for the BES loop. **Constraint**: Must output a JSON list of parameter sets. **Dependency**: None.
- [ ] T024b [P] [US2] Implement `code/bes/loop_runner.py` to execute the BES loop for a single parameter set (N). **Constraint**: Must accept parameters from T024a, run the loop, and output a log file for that N. **Dependency**: Requires T024a, T021, T023.
- [ ] T024c [P] [US2] Implement `code/bes/result_aggregator.py` to aggregate logs from T024b into a single result file. **Constraint**: Must combine all N-specific logs into `data/processed/bes_results.json`. **Dependency**: Requires T024b.

- [ ] T016a [P] [US1] Implement `code/dataset/validate_data_against_contracts.py`. **Constraint**: This script MUST read generated data (from T014c-exec) and `contracts/dataset.schema.yaml` (from T000a-gen) to verify schema compliance. **Dependency**: Requires T000a-gen, T014c-exec.
- [ ] T016b [P] [US1] Implement `code/analysis/validate_logs_against_contracts.py`. **Constraint**: This script MUST read output logs (from T029c-gen) and `contracts/output.schema.yaml` (from T000b-gen) to verify schema compliance. **Dependency**: Requires T000b-gen, T029c-gen.

---

## Phase 3: User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Instantiate a dataset of logic/arithmetic puzzles with deterministic Python verifiers capable of validating solution paths without LLMs.

**Independent Test**: Run verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for `code/dataset/generator.py` in `tests/unit/test_generator.py::test_generator_handles_empty_input`

- [ ] T010 [P] [US1] Unit test for `code/dataset/verifier.py` with known valid/invalid solutions in `tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/dataset/generator.py` to create logic puzzles (Sudoku variants, constrained pathfinding) with systematic complexity scaling (N=10..500). **Constraint**: Must support command-line arguments for `N` and `count`.

- [ ] T012 [P] [US1] Implement `code/dataset/verifier.py` to execute deterministic validation logic for each puzzle instance, returning boolean validity and specific constraint violation codes (e.g., `DUPLICATE_ROW`, `INVALID_PATH`) within 100ms. **Note**: T012 validates the code, T014c/b generates the data.

- [ ] T014c-impl [P] [US1] Implement `code/dataset/generate_and_validate.py`. **Constraint**: This script MUST accept a directory of raw puzzles, run the verifier, calculate checksums, and output `data/processed/distribution_report.json` with type/complexity distribution stats. Must strictly enforce "Fail Loudly" (no synthetic fallback). **Dependency**: Requires T011 and T012.
- [ ] T014c-exec [P] [US1] Execute `code/dataset/generate_and_validate.py`. **Constraint**: Must run the script generated in Tc-impl with parameters `--n 200 --count 10 --types sudoku,pathfinding`. **Dependency**: Requires T014c-impl.

- [ ] T014e-impl [P] [US1] Implement `code/dataset/validate_distribution.py`. **Constraint**: This script MUST read `data/processed/distribution_report.json` (from T014c-exec) and `contracts/dataset.schema.yaml` (from T000a-gen) to verify statistical representativeness and output `data/processed/distribution_validation.json` with fields: `is_valid`, `power_estimate`, `notes`. **Dependency**: Requires T014c-impl.
- [ ] T014e-exec [P] [US1] Execute `code/dataset/validate_distribution.py`. **Constraint**: Must run after T014e-impl. **Dependency**: Requires T014e-impl.

- [ ] T044a-impl [P] [US1] Implement strict "Fail Loudly" logic in `code/dataset/generator.py`. **Constraint**: Must remove any try/except blocks that catch `DataGenerationError` or similar and substitute mock data. If the puzzle generation fails (e.g., constraint parsing error), the script must raise an exception and halt execution immediately. **Rationale**: Addresses the "Fabrication Gate" requirement. **Dependency**: Requires T011.
- [ ] T044b-verify [P] [US1] Verify "Fail Loudly" logic in `code/dataset/generator.py`. **Constraint**: Add a unit test that attempts to generate invalid data and confirms the script halts with an exception. **Dependency**: Requires T044a-impl.

- [ ] T050a-impl [P] [US1] Implement "Fail Loudly" enforcement in `code/dataset/verifier.py`. **Constraint**: Ensure the verifier raises a specific `VerifierError` if the deterministic script fails to execute or returns an unexpected type, preventing silent fallback to "invalid" for system errors. **Rationale**: Addresses the "Fail Loudly" principle for data integrity. **Dependency**: Requires T012.
- [ ] T050b-verify [P] [US1] Verify "Fail Loudly" in verifier. **Constraint**: Add a unit test that simulates a verifier script crash and confirms the system raises an exception rather than returning a boolean. **Dependency**: Requires T050a-impl.

- [ ] T054a-impl [P] [US1] Implement "Complexity Scaling" validation in `code/dataset/generator.py`. **Constraint**: The generator must output a `complexity_metric` for each puzzle and verify that the distribution of these metrics is continuous across the N=10..500 range. **Rationale**: Ensures SC-005 (Scalability) can be measured. **Dependency**: Requires T011.
- [ ] T054b-verify [P] [US1] Verify "Complexity Scaling" distribution. **Constraint**: Add a test that generates a small set and verifies the `complexity_metric` spans the expected range. **Dependency**: Requires T054a-impl.

- [ ] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must generate `data/processed/distribution_validation.json` and verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. The JSON schema MUST be: `{"status": "PASS"|"FAIL", "reason": "string", "distribution_stats": {...}}`. **Dependency**: Requires T014e-exec, T044a-impl, T054b-verify.
- [ ] T036b-verify [P] [US1] Verify `validation_gate.json` schema. **Constraint**: Add a unit test `tests/unit/test_validation_gate.py::test_schema_valid` that asserts the JSON structure matches the required schema. **Dependency**: Requires T036.

- [ ] T066 [P] [US1] Implement explicit "Data Provenance" metadata injection in `code/dataset/generator.py`. **Constraint**: Every generated puzzle file must include a JSON header with `source_id` (e.g., "curated_logic_v1"), `generation_seed`, `timestamp`, and `generator_version`. This metadata must be validated by `code/dataset/verifier.py` before processing. **Rationale**: Addresses the "Single Source of Truth" and "Data Hygiene" principles by ensuring every data point is traceable to its exact generation parameters. **Dependency**: Requires T011.
- [ ] T066b-verify [P] [US1] Verify "Data Provenance" metadata. **Constraint**: Add a unit test that generates a puzzle, removes the metadata header, and confirms the verifier rejects the file with a `MISSING_METADATA` error. **Dependency**: Requires T066.

- [ ] T045a-impl [P] [US1] Add explicit "Sample Size Declaration" to `code/dataset/generate_and_validate.py`. **Constraint**: The script must output a `sample_size` field in `data/processed/distribution_report.json` and explicitly state the sampling rule (e.g., "First N=200 rows", "Random seed 42") if a subset is used. **Rationale**: Ensures transparency about data representativeness. **Dependency**: Requires T014c-impl.
- [ ] T045b-verify [P] [US1] Verify "Sample Size Declaration" in `data/processed/distribution_report.json`. **Constraint**: Add a test to verify the presence and correctness of the `sample_size` field. **Dependency**: Requires T045a-impl.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Evolutionary Search Execution (Priority: P2)

**Goal**: Execute the BES framework where the forward step uses a small CPU-tractable LLM and the backward step is replaced by a symbolic planner.

**Independent Test**: Run the evolutionary loop on a subset of puzzles and verify that the symbolic planner generates sub-goals and the LLM attempts to satisfy them, with the verifier correctly parsing the output.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for `code/symbolic/planner.py` with edge cases (non-linear constraints, impossible goals) in `tests/unit/test_symbolic_planner.py::test_planner_handles_nonlinear_constraints`

- [ ] T017a [P] [US2] Unit test for `code/symbolic/planner.py` in `tests/unit/test_symbolic_planner.py::test_planner_handles_impossible_goals`.
- [ ] T017b [P] [US2] Integration test for the BES loop with a small population in `tests/integration/test_bes_loop.py::test_bes_loop_executes_symbolic_backward_step`.

- [ ] T015 [P] [US1] Implement specific validation task for non-linear constraints edge case. **Constraint**: Create a dedicated test script `code/dataset/validate_edge_cases.py` that specifically attempts to parse non-linear constraints and verifies that the system logs the failure correctly (as per Edge Cases in spec) rather than crashing. **Dependency**: Requires T018 and T019.

- [ ] T046a-impl [P] [US2] Verify "Real Data" flow in `code/bes/main.py`. **Constraint**: Add a runtime check that asserts `data/processed/distribution_validation.json` (from T036) exists and has `status: PASS` before the BES loop starts. If validation fails, the main loop must exit with a clear error message. **Rationale**: Ensures the evolutionary loop never runs on unverified data. **Dependency**: Requires T036.
- [ ] T046b-verify [P] [US2] Verify "Real Data" flow check. **Constraint**: Add an integration test that attempts to run the BES loop without valid distribution validation and confirms it halts. **Dependency**: Requires T046a-impl.

- [ ] T048a-impl [P] [US2] Implement "Logical Contradiction" detection in `code/symbolic/planner.py`. **Constraint**: The planner MUST implement logic to detect and flag logical contradictions in the generated sub-goals and raise an exception if a contradiction is found. **Rationale**: Addresses the Edge Case in spec.md.
- [ ] T048b-verify [P] [US2] Verify "Logical Contradiction" detection. **Constraint**: Add a unit test to `tests/unit/test_symbolic_planner.py` that specifically tests the contradiction detection logic in `code/symbolic/planner.py`.

- [ ] T051a-impl [P] [US2] Implement "Sub-goal Consistency" check in `code/symbolic/planner.py`. **Constraint**: Before returning sub-goals, the planner must verify that the union of sub-goals does not logically contradict the initial state or the target state (e.g., via a lightweight SAT check or rule intersection). **Rationale**: Addresses the Edge Case regarding logically impossible sub-goals. **Dependency**: Requires T019.
- [ ] T051b-verify [P] [US2] Verify "Sub-goal Consistency". **Constraint**: Add a unit test that feeds a puzzle with an impossible constraint set and confirms the planner flags it as `CONTRADICTION_DETECTED` rather than generating invalid sub-goals. **Dependency**: Requires T051a-impl.

- [ ] T068 [P] [US2] Implement "Symbolic Planner Timeout" enforcement in `code/symbolic/planner.py`. **Constraint**: The planner must run with a strict wall-clock timeout (e.g., a bounded duration per puzzle). If the timeout is exceeded, the planner must log a `TIMEOUT_EXCEEDED` event, exclude the puzzle from the symbolic run, and record the event in `data/processed/exclusions.json`. **Rationale**: Addresses the risk of the symbolic planner hanging on complex constraints (Edge Case in spec) and ensures the BES loop remains within the 6-hour runtime budget. **Dependency**: Requires T019.
- [ ] T068b-verify [P] [US2] Verify "Symbolic Planner Timeout". **Constraint**: Add a unit test that simulates a slow constraint (e.g., infinite loop in mock) and confirms the planner times out and logs the exclusion correctly. **Dependency**: Requires T068.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

**Goal**: Record success rates and computational costs for both symbolic-guided and neural-verifier baselines, applying statistical tests for significance.

**Independent Test**: Feed synthetic success rate data with known differences to the analysis script to verify z-test and t-test accuracy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for `code/analysis/stats.py` with synthetic data in `tests/unit/test_stats.py::test_z_test_identifies_significance`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/analysis/metrics.py` to calculate success rates, wall-clock time, and energy consumption (Joules) from execution logs. **Constraint**: Must read data from the logged CPU-percent and TDP values calculated in Phase 1; any missing or invalid calibration data MUST result in a task failure - no fallback is allowed. **Constraint**: For the neural baseline (T042a-exec), energy must be measured as CPU energy on comparable hardware, not estimated GPU energy. **Dependency**: Requires T008c.

- [ ] T040c [P] [US3] Implement AND run the Validated Conversion Factor logic in `code/analysis/metrics.py`. **Constraint**: This script MUST measure CPU energy for the neural baseline (T042a-exec) on the same hardware as the symbolic run. It MUST NOT use a literature-based GPU conversion factor. **Dependency**: Requires T027.

- [ ] T043a-impl [P] [US3] Update `code/analysis/stats.py` to include the z-test comparison logic. **Constraint**: Must implement the two-proportion z-test comparing symbolic vs. neural success rates. **Dependency**: Requires T027b.
- [ ] T027b [P] [US3] Implement two-proportion z-test in `code/analysis/stats.py` to compare success rates (as mandated by FR-005) with null hypothesis H0: p1 = p2 and alpha=0.05. **Note**: This is the primary statistical test required by the spec. **Dependency**: Requires T043a-impl and T055a-impl.
- [ ] T043b-exec [P] [US3] Execute z-test comparison. **Constraint**: Run the z-test on the aggregated logs from T029c-gen and T042b-gen. **Dependency**: Requires T043a-impl, T029c-gen, T042b-gen.

- [ ] T055a-impl [P] [US3] Implement "Baseline Equivalence" check in `code/analysis/stats.py`. **Constraint**: Before running the z-test, the code must verify that the baseline (neural) and experimental (symbolic) groups were run on the same puzzle subset to ensure a fair comparison. **Rationale**: Addresses the validity of the experimental design. **Dependency**: Requires T027b.
- [ ] T055b-verify [P] [US3] Verify "Baseline Equivalence" check. **Constraint**: Add a test that attempts to run the z-test on mismatched puzzle IDs and confirms the system halts. **Dependency**: Requires T055a-impl.

- [ ] T028a [P] [US3] Implement statistical framework pre-registration logic in `code/analysis/stats.py` to define and log the choice between 'equivalence' (TOST) and 'non-inferiority' frameworks before running tests, satisfying SC-001's pre-registration requirement.
- [ ] T028b [P] [US3] Execute Pre-Registration. **Constraint**: This task MUST write the pre-registration configuration defined in T028a to `data/processed/pre_registration.yaml` before any experiments are run. **Dependency**: Requires T028a.
- [ ] T028c-verify [P] [US3] Verify Pre-Registration Artifact. **Constraint**: Add a unit test `tests/unit/test_pre_registration.py::test_pre_registration_exists` that asserts `data/processed/pre_registration.yaml` exists and contains valid framework choice. **Dependency**: Requires T028b.

- [ ] T029a [P] [US3] Define Pilot Parameters. **Constraint**: Define the specific N range (e.g., N=10..50) and sample size for the Pilot run in `code/bes/pilot_config.json`. **Dependency**: None.
- [ ] T029b-exec [P] [US3] Execute Pilot Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` on the subset defined in T029a to profile runtime and memory, including checkpointing for long runs and configurable timeouts. **Dependency**: Requires T024a/b/c (BES loop logic), T029a.
- [ ] T029b-profile [P] [US3] Profile runtime and memory from Pilot Scaling Experiments. **Constraint**: Analyze logs from T029b-exec to determine memory footprint and runtime per puzzle. **Dependency**: Requires T029b-exec.

- [ ] T029c-exec [P] [US3] Execute Full Scaling Experiments. **Constraint**: Execute `code/main.py` with `--mode symbolic` across the full complexity scaling range (N=10..500) to generate raw logs, including checkpointing and configurable timeouts. The output MUST include timestamps, CPU-percent, and durations for each puzzle attempt. **Dependency**: Requires T024a/b/c (BES loop logic).
- [ ] T029c-gen [P] [US3] Generate `data/processed/scaling_raw_logs.json` from T029c-exec. **Constraint**: Aggregate raw logs from T029c-exec into the final JSON format. **Required Schema**: List of objects with `puzzle_id`, `duration`, `cpu_percent`, `success`, `timestamp`. **Dependency**: Requires T029c-exec.

- [ ] T042a-exec [P] [US3] Execute the neural_baseline run. **Constraint**: Execute `code/main.py` with `--mode neural` on the same subset as T029c-exec to measure CPU time for baseline estimation. **Dependency**: Requires T024a/b/c.
- [ ] T042b-gen [P] [US3] Generate `data/processed/neural_baseline_logs.json` from T042a-exec. **Constraint**: Aggregate raw logs from T042a-exec into the final JSON format. **Required Schema**: List of objects with `puzzle_id`, `duration`, `cpu_percent`, `success`, `timestamp`. **Dependency**: Requires T042a-exec.

- [ ] T029d-exec [P] [US3] Execute Scalability Analysis Script. **Constraint**: Run the analysis script on `data/processed/scaling_raw_logs.json` and `data/processed/neural_baseline_logs.json`. **Dependency**: Requires T029c-gen, T042b-gen.
- [ ] T029d-derive [P] [US3] Derive complexity class from T029d-exec results. **Constraint**: Perform comparative log-log linear regression on BOTH Symbolic and Neural solver slopes using `scipy.stats.linregress` on log-transformed data (X=`complexity_metric`, Y=`duration`) to determine the computational complexity class of the *approach* (SC-005). **Output**: Must output a `complexity_class` string (e.g., 'O(n)', 'O(n^2)') in the final report and in `data/processed/scaling_analysis.json`. If R^2 < 0.85, assign 'UNKNOWN'. **Dependency**: Requires T029d-exec.

- [ ] T029g [P] [US3] Compare solver slopes for complexity class verification. **Constraint**: Compare the slopes of the Symbolic vs. Neural solvers from `data/processed/scaling_raw_logs.json` and `data/processed/neural_baseline_logs.json` to determine the computational complexity class of the *approach* (SC-005). This task must explicitly compare different solvers and output a `complexity_class` string in the final report and `data/processed/scaling_analysis.json` by reading the output from T029d-derive. **Dependency**: Requires T029d-derive, T042b-gen.

- [ ] T031a [P] [US3] Implement machine-readable results writing logic in `code/analysis/stats.py`. **Constraint**: Must output `data/processed/stats_results.json` containing p-values, confidence intervals, and test statistics. **Dependency**: Requires T027b.

- [ ] T031b-impl [P] [US3] Implement report generation logic in `code/analysis/report.py`. **Constraint**: Must handle partial data scenarios: if energy metrics are missing, mark section as 'Not Available'; if complexity analysis is missing, mark section as 'Not Available'. **Dependency**: Requires T031a, T029g, T049a-impl.
- [ ] T031b-gen [P] [US3] Generate final report in `data/processed/final_report.md` (Markdown format). **Constraint**: Must run after T031b-impl. **Dependency**: Requires T031b-impl. Must explicitly include the `complexity_class` string derived from T029g in the final report.

- [ ] T049a-impl [P] [US3] Add "Power Analysis" output to `data/processed/final_report.md`. **Constraint**: The final report must include a section explicitly stating the calculated statistical power for the observed effect size. If power < 0.8, the report must flag the result as "Underpowered" and recommend a larger sample size. **Rationale**: Ensures the statistical conclusion is scientifically defensible. **Dependency**: Requires T027b.
- [ ] T049b-verify [P] [US3] Verify "Power Analysis" output. **Constraint**: Add a test to verify the presence of the power analysis section in the final report. **Dependency**: Requires T049a-impl.

- [ ] T052a-impl [P] [US3] Implement "Statistical Power" calculation in `code/analysis/stats.py`. **Constraint**: The stats module must calculate post-hoc power for the observed effect size using the sample size and variance from the logs. **Rationale**: Ensures the study is not underpowered (SC-001). **Dependency**: Requires T027b.
- [ ] T052b-verify [P] [US3] Verify "Power" calculation. **Constraint**: Add a unit test with known inputs to verify the power calculation matches standard statistical libraries. **Dependency**: Requires T052a-impl.

- [ ] T053a-impl [P] [US3] Implement "Literature Factor" validation in `code/analysis/metrics.py`. **Constraint**: Removed; replaced by direct CPU measurement. **Rationale**: Ensures "Verified Accuracy" (Principle II) by avoiding unverified literature factors. **Dependency**: None.
- [ ] T053b-verify [P] [US3] Verify "Literature Factor" validation. **Constraint**: Add a test that attempts to run analysis with a missing citation field and confirms the process halts. **Dependency**: Requires T053a-impl.

- [ ] T069 [P] [US3] Implement "Energy Measurement Sanity Check" in `code/analysis/metrics.py`. **Constraint**: Before calculating energy, the system must verify that the `cpu_percent` readings are within a plausible range (e.g., 0-100) and that the `duration` is non-zero. If any reading is an outlier (e.g., >1000%), the system must flag the log entry as `CORRUPTED` and exclude it from the final energy calculation. **Rationale**: Prevents garbage-in-garbage-out scenarios where sensor errors or logging bugs produce nonsensical energy values. **Dependency**: Requires T005b, T027.
- [ ] T069b-verify [P] [US3] Verify "Energy Sanity Check". **Constraint**: Add a unit test that injects a log entry with `cpu_percent=2000` and confirms the system flags it as `CORRUPTED` and excludes it from the average. **Dependency**: Requires T069.

- [ ] T056 [P] [US3] Execute Statistical Analysis. **Constraint**: Run all statistical tests (T043b-exec, T029d-derive, T052a-impl) and generate `data/processed/final_analysis_report.json`. **Dependency**: Requires T043b-exec, T029d-derive, T052a-impl.

---

## Phase 6: Results & Report Generation

**Purpose**: Generate final results and reports as required by Plan.md Phase 2.4.

- [ ] T057 [P] [US3] Generate Results and Report. **Constraint**: Generate `data/processed/final_report.md` including all statistical findings, complexity class, and power analysis. **Dependency**: Requires T056, T031b-gen.

- [ ] T035 [P] [US3] Final Review and Artifact Verification. **Constraint**: Verify all required artifacts (`pre_registration.yaml`, `scaling_raw_logs.json`, `calibrated_tdp.json`, `neural_baseline_logs.json`, `final_analysis_report.json`) exist and match schemas before finalizing the project.

---

## Phase 7: Revision & Analysis Resolution

**Purpose**: Address specific concerns raised during the analysis phase to ensure robustness and compliance with data hygiene principles.

- [ ] T060a [P] [US1] Implement end-to-end dataset validation pipeline in `code/dataset/final_validation.py`. **Constraint**: Must run all previous validation tasks (T014e, T036, T044b, T050b, T054b) in sequence and aggregate results into a single `data/processed/final_dataset_validation.json`. **Dependency**: Requires T014e-exec, T036, T044b, T050b, T054b.
- [ ] T060b-verify [P] [US1] Verify final dataset validation pipeline. **Constraint**: Add an integration test that simulates a partial failure in the dataset generation and confirms the pipeline halts with a clear error message. **Dependency**: Requires T060a.

- [ ] T061a [P] [US2] Implement end-to-end BES loop validation in `code/bes/final_loop_validation.py`. **Constraint**: Must run a minimal BES loop (N=10, 1 generation) with both symbolic and neural modes and verify that all outputs match expected schemas. **Dependency**: Requires T024a/b/c, T021, T023.
- [ ] T061b-verify [P] [US2] Verify BES loop validation. **Constraint**: Add an integration test that injects a malformed puzzle into the BES loop and confirms the system handles it gracefully (exclusion vs. crash). **Dependency**: Requires T061a.

- [ ] T062a [P] [US3] Implement final statistical analysis pipeline in `code/analysis/final_analysis.py`. **Constraint**: Must run all statistical tests (T027b, T029d-derive, T049a-impl, T052a-impl) and generate a comprehensive `data/processed/final_analysis_report.json`. **Dependency**: Requires T027b, T029d-derive, T049a-impl, T052a-impl.
- [ ] T062b-verify [P] [US3] Verify final statistical analysis pipeline. **Constraint**: Add an integration test that injects synthetic data with known statistical properties and confirms the pipeline produces the expected results. **Dependency**: Requires T062a.

- [ ] T063 [P] [All] Create final integration test suite in `tests/integration/test_full_pipeline.py`. **Constraint**: Must run T060a, T061a, and T062a in sequence and verify that all intermediate and final artifacts are generated correctly. **Dependency**: Requires T060a, T061a, T062a.

- [ ] T064 [P] [All] Generate final project documentation in `docs/FINAL_REPORT.md`. **Constraint**: Must include a summary of all validation results, statistical findings, and a clear statement of whether the project meets all success criteria (SC-001 to SC-005). **Dependency**: Requires T063.

- [ ] T065 [P] [All] Final review and sign-off. **Constraint**: A human reviewer must verify that all tasks are complete, all tests pass, and all artifacts are present and valid. **Dependency**: Requires T064.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T070 [P] [All] Create "Reproducibility Manifest" generation script in `code/utils/generate_manifest.py`. **Constraint**: This script must run at the end of the experiment, hashing all input data files, code files, and configuration files, and outputting a `MANIFEST.md` with all hashes, the git commit hash, and the exact Python environment version. **Rationale**: Ensures full reproducibility (Constitution Principle I) by providing a single artifact that can verify the exact state of the experiment. **Dependency**: Requires T001, T002c, T011, T021, T027.
- [ ] T070b-verify [P] [All] Verify "Reproducibility Manifest". **Constraint**: Add an integration test that modifies a single line of code after the experiment and confirms the manifest generation fails to match the stored hash. **Dependency**: Requires T070.