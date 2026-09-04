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

- [ ] T000c-impl [P] Generate `research.md` documenting the Dataset Strategy (Synthetic Curation + Scaling Generation) and Statistical Analysis Plan. **Constraint**: Must define the dataset source path as `data/raw/generated_puzzles.json` (a path definition, not a placeholder file), scaling method (N=10..500), and statistical framework. Must define `complexity_metric` as a tuple of (constraint_count, variable_domain_size). **Dependency**: Requires T000d-impl.
- [ ] T000c-stats-def [P] Define Statistical Analysis Plan parameters in `research.md`. **Constraint**: Must define the two-proportion z-test parameters (alpha=0.05) and power analysis requirements. **Dependency**: Requires T000c-impl.
- [ ] T000d-impl [P] Generate `data-model.md` defining the Statistical Plan and Data Entities. **Constraint**: Must explicitly define the `complexity_metric` mapping to asymptotic complexity for SC-005 and the schema for `Puzzle Instance`. **Dependency**: Requires T000d-def.
- [ ] T000d-def [P] Define the JSON schema structure for puzzle instances in text format. **Constraint**: Must define fields: `constraints` (array of strings), `initial_state` (object), `target_state` (object), `verifier_output` (object with `valid` boolean and `error_code` string), and `metadata` (object with `source_id`, `generation_seed`). Reference `data-model.md` section 2.1 for field definitions. **Dependency**: None.
- [ ] T000d-gen [P] Write the `contracts/dataset.schema.yaml` file from T000d-def definitions. **Constraint**: Must validate the schema against `data-model.md` requirements. **Dependency**: Requires T000d-def.
- [ ] T000d-verify [P] Verify `contracts/dataset.schema.yaml` syntax and schema validity. **Constraint**: Add a unit test `tests/unit/test_schema.py::test_dataset_schema_valid` that validates the YAML file. **Dependency**: Requires T000d-gen.
- [ ] T000b-def [P] Define the JSON schema structure for output files in text format. **Constraint**: Must define schemas for `data/processed/exclusions.json` and `data/processed/distribution_report.json`. Reference `plan.md` section 3.2 for field definitions. **Dependency**: Requires T000d-impl.
- [ ] T000b-gen [P] Write the `contracts/output.schema.yaml` file from T000b-def definitions. **Constraint**: Must validate the schema against `plan.md` requirements. **Dependency**: Requires T000b-def.
- [ ] T000b-verify [P] Verify `contracts/output.schema.yaml` syntax and schema validity. **Constraint**: Add a unit test `tests/unit/test_schema.py::test_output_schema_valid` that validates the YAML file. **Dependency**: Requires T000b-gen.
- [X] T067 [P] [US3] Implement "Pre-Analysis Power Calculation" in `code/analysis/stats.py`. **Constraint**: If the planned sample size (N=10..500) is insufficient, the system MUST log a critical warning (but NOT halt execution, per Spec Assumptions) and proceed. **Rationale**: Prevents the "Underpowered" scenario identified in T049a by enforcing power constraints at the start, not just at the end. **Dependency**: Requires T000d-impl.
- [ ] T067b-verify [P] [US3] Verify "Pre-Analysis Power" check. **Constraint**: Add a test that sets a tiny sample size (e.g., N=5) and confirms the system logs a warning before running the experiment. **Dependency**: Requires T067.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `data/` directory hierarchy: `data/raw`, `data/processed`. **Constraint**: Must verify directories exist and are writable.
- [ ] T001b [P] Create `code/` directory hierarchy: `code/{dataset,symbolic,bes,analysis,utils}`. **Constraint**: Must verify directories exist and are writable.
- [ ] T001c [P] Create `tests/` directory hierarchy: `tests/{unit,integration}`. **Constraint**: Must verify directories exist and are writable.

- [X] T002a [P] Initialize git repository and configure basic `.gitignore` for Python artifacts. **Constraint**: Must include `__pycache__`, `*.pyc`, `.env`, `data/processed/*`, `!data/processed/.gitkeep`.

- [ ] T002b-create [P] Create Python virtual environment in `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/`. **Constraint**: Must run `python3 -m venv venv` and create the directory structure. **Dependency**: None.
- [ ] T002b-activate [P] Activate the virtual environment. **Constraint**: Must source the venv via `cd projects/PROJ-884-llmxive-follow-up-extending-self-improvi && source venv/bin/activate`. **Dependency**: Requires T002b-create.
- [ ] T002b-verify [P] Verify the virtual environment is active. **Constraint**: Must run `python --version` and confirm it works. **Dependency**: Requires T002b-activate.

- [X] T002c [P] Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.2 `, `numpy==1.26.0 `, `transformers==4.35.0 `, `datasets==2.14.0 `, `pyyaml==6.0.1 `, `pytest==7.4.0 `, `optimum[onnxruntime]>=1.13.0,<1.16.0 `. **Constraint**: Use fixed versions from plan.md. Must specify `optimum[onnxruntime]` for CPU-optimized quantization flags. Do NOT include `bitsandbytes`. **Dependency**: Requires T002b-activate.

- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Constraint**: Must generate `.flake8` and `pyproject.toml` (for black) configuration files to satisfy plan.md testing requirements.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure: `data/raw` for immutable puzzles, `data/processed` for logs/results. **Constraint**: Must verify directories exist and are writable.

- [ ] T005a-impl [P] [US1] Implement base logging infrastructure in `code/__init__.py` to capture wall-clock time and resource usage; output must be JSON format to `data/processed/experiment.log`. **Constraint**: Must produce valid JSON logging code.
- [ ] T005a-test [P] [US1] Add unit test for log format in `tests/unit/test_logging.py`. **Constraint**: Must validate JSON structure. **Dependency**: Requires T005a-impl.

- [X] T005b [P] [US1] Implement CPU utilization monitoring in `code/utils/monitor.py` using `psutil` to log `cpu_percent` for every execution step. **Constraint**: Must log at the same frequency as T005a.

- [X] T006 [P] [US1] Setup random seed management utility in `code/utils/seed.py` for reproducibility

- [X] T007 [P] [US1] Create base configuration loader in `code/config.py` to handle experiment parameters (population size, generations). **Constraint**: Must be functional before T007b runs.

- [X] T007b [P] [US1] Initialize `code/config.py` with `DEFAULT_TDP_WATTS = 65 ` as a safe fallback. **Constraint**: This value MUST be overwritten by T008c after calibration. **Dependency**: Requires T007. **Action**: If T008c is not run, the system MUST log a warning but continue execution. **Verification**: No test required here; verification moved to T008c to avoid circular dependency.

- [ ] T008a-static-data [P] [US1] Generate `data/raw/cpu_tdp_map.json` from a hardcoded mapping of common CPU models to TDP values (derived from public benchmarks like CPU-World API). **Constraint**: The file must contain a JSON object mapping CPU model strings (e.g., "Intel Xeon E-2686 v4") to integer TDP values (e.g., 90). Must use a provided script template to scrape the list from https://www.cpu-world.com/ or a defined mirror. **Dependency**: None.
- [ ] T008a-impl [P] [US1] Implement TDP Calibration Script in `code/utils/calibrate_tdp.py`. **Constraint**: Must detect the runner's CPU model (e.g., via `platform.machine()` or `lscpu`) and select a TDP value from `data/raw/cpu_tdp_map.json` (generated by T008a-static-data). If the CPU model is not found, use the generic fallback (representative nominal power) and log a warning. Must output `data/processed/calibration_run.json` with fields: `workload_type`, `cpu_percent`, `duration`, `estimated_tdp_watts`. **Dependency**: Requires T008a-static-data.
- [ ] T008a-exec [P] [US1] Execute TDP Calibration Script. **Constraint**: Must run T008a-impl. **Dependency**: Requires T008a-impl.
- [ ] T008c [P] [US1] Implement TDP Constant Generation Script in `code/utils/generate_tdp_constant.py`. **Constraint**: Must read `data/processed/calibration_run.json` (from T008a-exec) and `code/config.py` (T007b) to generate `data/processed/calibrated_tdp.json` with fields: `tdp_watts`, `source` ("verified-literature" or "fallback"), `error_margin`, `confidence_interval`, `citation_url`. **Dependency**: Requires T008a-exec and T007b. **Verification**: Must add unit test `tests/unit/test_calibrated_tdp.py::test_tdp_constant_valid` that asserts `data/processed/calibrated_tdp.json` exists, `tdp_watts` > 0, `source` is present, `citation_url` is a valid URL, AND that the `DEFAULT_TDP_WATTS` placeholder in `config.py` has been overwritten.
- [ ] T008c-fallback-verify [P] [US1] Verify the fallback TDP path in the cost calculator. **Constraint**: Add a unit test that simulates a failed calibration (missing `calibration_run.json`) and confirms the system uses the fallback TDP and logs a warning without crashing. **Dependency**: Requires T008c.

- [X] T008 [P] [US1] Setup error handling framework by creating `code/exceptions.py` defining custom exception classes for `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, and `VERIFIER_ERROR` (to handle internal verifier failures, addressing robustness gap)

- [ ] T019d-impl [P] [US2] Implement `code/symbolic/exclusion_logger.py` to write exclusion events to `data/processed/exclusions.json`. **Constraint**: Must strictly adhere to the schema defined in `contracts/output.schema.yaml` (T000b-gen). Must generate a syntactically correct file. **Dependency**: Requires T000b-gen.
- [ ] T019d-verify [P] [US2] Verify exclusion logger schema. **Constraint**: Add a unit test `tests/unit/test_exclusion_logger.py::test_schema_valid` that validates the JSON structure. **Dependency**: Requires T019d-impl.

- [X] T013 [P] [US2] Implement `code/symbolic/planner.py` to generate sub-goal decompositions, including logic to detect and flag `CONTRADICTION_DETECTED` or `PARSE_FAILURE`. **Constraint**: Must include the logic to call the exclusion logger (T019d-impl) directly within this module or via a helper. **Dependency**: Requires T019d-impl, T008.

- [X] T018 [P] [US2] Implement `code/symbolic/parser.py` to convert puzzle constraints into a formal language parseable by the planner

- [X] T020 [P] [US2] Generate `code/bes/config.py` with configuration for a small pre-trained LLM (`distilbert-base-uncased`). **Constraint**: This task is for **configuration file generation ONLY** (no download). Must specify `device='cpu'` and explicitly forbid `bitsandbytes`. Must explicitly mandate `optimum.onnxruntime` for CPU execution. Must define a fallback model (`TinyBERT`) if the primary model exceeds memory limits. **Dependency**: None.
- [ ] T020b-onnx-convert [P] [US2] Convert the `distilbert-base-uncased` model to ONNX format. **Constraint**: Must use `optimum-cli export onnx` or a script to convert the model from HuggingFace to ONNX format. Must output the ONNX model to a cache directory. **Dependency**: Requires T020.
- [ ] T021b-static [P] [US2] Generate `data/raw/model_manifest.json` containing the exact HuggingFace commit hash and file paths for the `distilbert-base-uncased` model. **Constraint**: Must NOT download the model. Must create a static manifest file that pins the exact version to ensure reproducibility. **Dependency**: Requires T020.
- [ ] T021b-cache [P] [US2] Download the `distilbert-base-uncased` model artifact to the cache directory *before* executing T021. **Constraint**: Must use `hf_hub_download` with the `revision` parameter locked to the commit hash in `data/raw/model_manifest.json` (from T021b-static). If download fails, attempt fallback model `TinyBERT`. Must verify the model exists in cache. **Dependency**: Requires T020, T021b-static.

- [X] T021 [P] [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must load the model specified in `code/bes/config.py` (default `distilbert-base-uncased`) using `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`, `optimum.onnxruntime`). Do NOT force 8-bit quantization unless verified. **Dependency**: Requires T020, T020b-onnx-convert, T021b-cache. <!-- FAILED: unspecified -->

- [ ] T022 [P] [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [ ] T023 [P] [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [ ] T024a [P] [US2] Implement `code/bes/parameter_generator.py` to generate the list of complexity parameters (N=10..500) for the BES loop. **Constraint**: Must output a JSON list of parameter sets. **Dependency**: None.
- [ ] T024b-exec [P] [US2] Implement `code/bes/loop_runner.py` to execute the BES loop for a single parameter set (N). **Constraint**: Must accept parameters from Ta, run the loop, and output a log file for that N. **Dependency**: Requires T024a, T021, T023, T028b, T011-scaling-exec.
- [ ] T024c [P] [US2] Implement `code/bes/result_aggregator.py` to aggregate logs from T024b-exec into a single result file. **Constraint**: Must combine all N-specific logs into `data/processed/bes_results.json`. **Dependency**: Requires T024b-exec.

- [ ] T016a [P] [US1] Implement `code/dataset/validate_data_against_contracts.py`. **Constraint**: This script MUST read generated data (from T014c-exec) and `contracts/dataset.schema.yaml` to verify schema compliance. **Dependency**: Requires T000d-gen, T014c-exec.
- [ ] T016b [P] [US1] Implement `code/analysis/validate_logs_against_contracts.py`. **Constraint**: This script MUST read output logs (from T029c-gen) and `contracts/output.schema.yaml` to verify schema compliance. **Dependency**: Requires T000b-gen, T029c-gen.

---

## Phase 3: User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Instantiate a dataset of logic/arithmetic puzzles with deterministic Python verifiers capable of validating solution paths without LLMs.

**Independent Test**: Run verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for `code/dataset/generator.py` in `tests/unit/test_generator.py::test_generator_handles_empty_input`

- [ ] T010 [P] [US1] Unit test for `code/dataset/verifier.py` with known valid/invalid solutions in `tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution`

### Implementation for User Story 1

- [ ] T011a-curate [P] [US1] Define the formal language grammar for puzzle constraints in `code/dataset/grammar.py`. **Constraint**: Must explicitly define the parseable constraint types (e.g., equality, inequality, adjacency) and output a schema for validation. **Dependency**: Requires T000d-impl.
- [ ] T011-impl [P] [US1] Implement `code/dataset/generator.py` to create logic puzzles (Sudoku variants, constrained pathfinding) with systematic complexity scaling (N=10..500). **Constraint**: Must support command-line arguments for `N` and `count`. Must include "Fail Loudly" logic (raise exception on failure, no synthetic fallback) and "Complexity Scaling" validation (verify `complexity_metric` distribution). Must enforce metadata population (`source_id`, `generation_seed`). Must validate constraints against the grammar defined in Ta-curate. **Dependency**: Requires T000d-impl, T011a-curate.
- [ ] T011c-verify-metrics [P] [US1] Implement explicit verification of `complexity_metric` fields in `code/dataset/generator.py`. **Constraint**: The generator must validate that `constraint_count` and `variable_domain_size` are present and non-null in the metadata of every generated puzzle. **Dependency**: Requires T011-impl.
- [ ] T011c [P] [US1] Implement enforcement of puzzle metadata in `code/dataset/generator.py`. **Constraint**: The generator must populate the `metadata` field with a valid `source_id`, `generation_seed`, and timestamp for each generated puzzle instance. **Dependency**: Requires T011-impl

- [ ] T012-impl [P] [US1] Implement `code/dataset/verifier.py` to execute deterministic validation logic for each puzzle instance, returning boolean validity and specific constraint violation codes (e.g., `DUPLICATE_ROW`, `INVALID_PATH`) within 100ms. **Note**: T012-impl validates the code, T014c/b generates the data. **Dependency**: Requires T011-impl.

- [ ] T012-gen-verifier [P] [US1] Generate the deterministic Python verification script artifact for each puzzle instance in `data/raw/`. **Constraint**: For every puzzle generated by T011, this task MUST generate a corresponding `.py` file (e.g., `puzzle_001_verify.py`) that contains the specific validation logic for that puzzle's constraints. This script must be self-contained and executable without the LLM. **Dependency**: Requires T011-impl, T012-impl. Must iterate over the generated subset files (puzzles_N*.json, etc.) and generate corresponding verifier scripts for each.

- [ ] T014c-impl [P] [US1] Implement `code/dataset/generate_and_validate.py`. **Constraint**: This script MUST accept a directory of raw puzzles, run the verifier, calculate checksums, and output `data/processed/distribution_report.json` with type/complexity distribution stats. Must strictly enforce "Fail Loudly" (no synthetic fallback). Must call T019d-impl to log exclusions. Must validate constraints against the grammar (T011a-curate). **Dependency**: Requires T011-impl, T012, T019d-impl, T011a-curate.
- [ ] T014c-filter [P] [US1] Implement the formal language validation and exclusion mechanism in `code/dataset/generate_and_validate.py`. **Constraint**: This task MUST parse the constraints of each generated puzzle against the grammar (T011a-curate), flag any unparseable items, and filter them out before processing further, logging the excluded items to `data/processed/exclusions.json`. **Dependency**: Requires T014c-impl, T011a-curate.
- [ ] T014c-exec [P] [US1] Execute `code/dataset/generate_and_validate.py`. **Constraint**: Must run the script generated in Tc-impl with parameters `--n` a sufficient number of instances `--count` a representative quantity `--types sudoku,pathfinding`. **Dependency**: Requires T014c-impl.

- [ ] T011-scaling-gen [P] [US1] Generate specific N=10, N=100, N=500 dataset subsets. **Constraint**: Must run T011-impl with specific N values to generate distinct files: `puzzles_N10.json`, `puzzles_N100.json`, `puzzles_N500.json`. **Dependency**: Requires T011-impl, T014c-filter.
- [ ] T011-scaling-exec [P] [US1] Execute the scaling generation. **Constraint**: Must run T011-scaling-gen for N=10, N=100, N=500. **Dependency**: Requires T011-scaling-gen, T014c-filter.

- [ ] T014e-impl [P] [US1] Implement `code/dataset/validate_distribution.py`. **Constraint**: This script MUST read `data/processed/distribution_report.json` (from T014c-exec) and `contracts/dataset.schema.yaml` (from T000d-gen) to verify statistical representativeness and output `data/processed/distribution_validation.json` with fields: `is_valid`, `power_estimate`, `notes`. **Dependency**: Requires T014c-exec.
- [ ] T014e-exec [P] [US1] Execute `code/dataset/validate_distribution.py`. **Constraint**: Must run after Te-impl. **Dependency**: Requires T014e-impl.

- [ ] T050a-impl [P] [US1] Implement "Fail Loudly" enforcement in `code/dataset/verifier.py`. **Constraint**: Ensure the verifier raises a specific `VerifierError` if the deterministic script fails to execute or returns an unexpected type, preventing silent fallback to "invalid" for system errors. **Rationale**: Addresses the "Fail Loudly" principle for data integrity. **Dependency**: Requires T012-impl.
- [ ] T050b-verify [P] [US1] Verify "Fail Loudly" in verifier. **Constraint**: Add a unit test that simulates a verifier script crash and confirms the system raises an exception rather than returning a boolean. **Dependency**: Requires T050a-impl.

- [ ] T066 [P] [US1] Implement explicit "Data Provenance" metadata injection in `code/dataset/generator.py`. **Constraint**: Every generated puzzle file must include a JSON header with `source_id` (e.g., "curated_logic_v"), `generation_seed`, `timestamp`, and `generator_version`. This metadata must be validated by `code/dataset/verifier.py` before processing. **Rationale**: Addresses the "Single Source of Truth" and "Data Hygiene" principles by ensuring every data point is traceable to its exact generation parameters. **Dependency**: Requires T011-impl.
- [ ] T066b-verify [P] [US1] Verify "Data Provenance" metadata. **Constraint**: Add a unit test that generates a puzzle, removes the metadata header, and confirms the verifier rejects the file with a `MISSING_METADATA` error. **Dependency**: Requires T066.

- [ ] T045a-impl [P] [US1] Add explicit "Sample Size Declaration" to `code/dataset/generate_and_validate.py`. **Constraint**: The script must output a `sample_size` field in `data/processed/distribution_report.json` and explicitly state the sampling rule (e.g., "First N=200 rows", "Random seed 42") if a subset is used. **Rationale**: Ensures transparency about data representativeness. **Dependency**: Requires T014c-impl.
- [ ] T045b-verify [P] [US1] Verify "Sample Size Declaration" in `data/processed/distribution_report.json`. **Constraint**: Add a test to verify the presence and correctness of the `sample_size` field. **Dependency**: Requires T045a-impl.

- [ ] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must generate `data/processed/distribution_validation.json` and verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. The JSON schema MUST be: `{"status": "PASS"|"FAIL", "reason": "string", "distribution_stats": {...}}`. **Dependency**: Requires T014e-exec, T044b-verify, T054b-verify.
- [ ] T036b-verify [P] [US1] Verify `validation_gate.json` schema. **Constraint**: Add a unit test `tests/unit/test_validation_gate.py::test_schema_valid` that validates the JSON structure matches the required schema. **Dependency**: Requires T036.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Hybrid Evolutionary Search Execution (Priority: P2)

**Goal**: Execute the BES framework with symbolic backward step and LLM forward step.

**Independent Test**: Run the evolutionary loop on a subset of puzzles and verify that the symbolic planner successfully generates sub-goals and the LLM attempts to satisfy them.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018a [P] [US2] Unit test for `code/symbolic/planner.py` in `tests/unit/test_planner.py::test_planner_handles_contradiction`

### Implementation for User Story 2

- [ ] T025a-prefilter [P] [US2] Implement `code/bes/prefilter.py` to exclude items with `PARSE_FAILURE` from the BES loop. **Constraint**: This task MUST read the dataset and the `exclusions.json` file (from T014c-filter) and produce a filtered dataset that excludes any item flagged with `PARSE_FAILURE` before it enters the evolutionary loop. **Output**: Must output `data/processed/filtered_dataset.json`. **Dependency**: Requires T014c-filter, T019d-impl.
- [ ] T025 [P] [US2] Implement `code/bes/evolutionary_loop.py` to orchestrate the forward (LLM) and backward (Symbolic) steps. **Constraint**: Must handle the case where the symbolic planner returns `CONTRADICTION_DETECTED` by excluding the instance and logging to `exclusions.json`. **Dependency**: Requires T025a-prefilter, T021, T023, T019d-impl.
- [ ] T026 [P] [US2] Implement `code/bes/mutation_operator.py` to apply mutations to candidate solutions based on symbolic sub-goals. **Constraint**: Must ensure mutations are syntactically valid according to the grammar (T011a-curate). **Dependency**: Requires T025, T011a-curate.
- [ ] T027 [P] [US2] Implement `code/bes/crossover_operator.py` to recombine candidate solutions using the LLM. **Constraint**: Must use the `forward_step` module (T021) to guide recombination. **Dependency**: Requires T025, T021.
- [ ] T028 [P] [US2] Implement `code/bes/fitness_evaluator.py` to score candidates using the deterministic verifier (T012). **Constraint**: Must enforce a timeout per evaluation. **Dependency**: Requires T012, T025.
- [ ] T029 [P] [US2] Implement `code/bes/termination_condition.py` to stop the loop based on max generations or convergence. **Constraint**: Must log the termination reason. **Dependency**: Requires T025.
- [ ] T024d-neural-run [P] [US2] Implement `code/bes/neural_baseline_runner.py` to execute the BES loop with the neural-verifier baseline variant. **Constraint**: Must use the same parameter sets (N) as T024b-exec but replace the symbolic planner with the neural verifier. Must output `data/processed/neural_baseline_results.json`. **Dependency**: Requires T024a, T021, T028, T029.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Performance Measurement and Statistical Analysis (Priority: P3)

**Goal**: Record success rates and costs, apply statistical tests.

**Independent Test**: Run analysis on synthetic logs with known differences to verify z-test and t-test accuracy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029a [P] [US3] Unit test for `code/analysis/stats.py` in `tests/unit/test_stats.py::test_z_test_significance`

### Implementation for User Story 3

- [ ] T029a-impl [P] [US3] Implement `code/analysis/stats.py` with two-proportion z-test and t-test functions. **Constraint**: Must use `scipy.stats` or `statsmodels`. Must return p-values and effect sizes. **Dependency**: Requires T024c, T024d-neural-run.
- [ ] T029a-compare [P] [US3] Execute the statistical comparison between symbolic-guided and neural-verifier baseline. **Constraint**: Must read `data/processed/bes_results.json` (symbolic) and `data/processed/neural_baseline_results.json` (neural) and apply the two-proportion z-test to compare success rates and t-test for cost. **Dependency**: Requires T029a-impl, T024c, T024d-neural-run.
- [ ] T029b-impl [P] [US3] Implement `code/analysis/cost_calculator.py` to compute wall-clock time and energy (Joules) from logs. **Constraint**: Must use the calibrated TDP from `data/processed/calibrated_tdp.json`. **Dependency**: Requires T008c, T024c, T008c-fallback-verify.
- [ ] T029b-neural-energy [P] [US3] Implement energy calculation for the neural-verifier baseline. **Constraint**: Must read `data/processed/neural_baseline_results.json` and apply the calibrated TDP to calculate energy in Joules for the baseline variant. **Dependency**: Requires T029b-impl, T024d-neural-run.
- [ ] T029b-gpu-estimate [P] [US3] Implement the "validated conversion factor" to estimate GPU-hours from CPU runtime. **Constraint**: Must calculate the GPU-hours for the neural baseline based on the CPU runtime and a known conversion factor (e.g., from literature or benchmark). **Dependency**: Requires T029b-neural-energy.
- [ ] T029c-gen [P] [US3] Generate `data/processed/statistical_report.json`. **Constraint**: Must contain success rates, p-values, cost comparisons, and a conclusion on statistical significance (p < 0.05). **Dependency**: Requires T029a-compare, T029b-impl, T029b-neural-energy, T029b-gpu-estimate.
- [ ] T029d-empirical [P] [US3] Implement `code/analysis/complexity_empirical.py`. **Constraint**: Must perform empirical log-log linear regression on the runtime data (N vs time) from `data/processed/bes_results.json` (columns: N, time) to characterize the computational complexity class. **Dependency**: Requires T024c.
- [ ] T029d-theory [P] [US3] Implement `code/analysis/complexity_theory.py`. **Constraint**: Must perform theoretical derivation of the Big-O complexity class based on the algorithm's structure (e.g., polynomial time for nested loops). **Dependency**: Requires T024c.
- [ ] T029g [P] [US3] Generate `data/processed/complexity_report.json`. **Constraint**: Must report the empirical complexity class (from Td-empirical) as the final reported metric, and the theoretical complexity class (from Td-theory) for comparison. If the empirical fit deviates significantly from the theoretical derivation, flag as "DISCREPANCY_DETECTED". **Dependency**: Requires T029d-empirical, T029d-theory.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] [All] Run end-to-end integration test for the full BES loop on a small dataset (N=10). **Constraint**: Must verify that the pipeline runs from data generation to statistical report without errors. **Dependency**: Requires T036, T029g.
- [ ] T031 [P] [All] Update `README.md` with execution instructions and parameter explanations. **Constraint**: Must include examples for running the pilot and full experiment.
- [ ] T032 [P] [All] Add `pytest` coverage report generation to CI workflow. **Constraint**: Must enforce a minimum coverage threshold for core modules.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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