# Tasks: llmXive follow-up: extending "Self-Improving Language Models with Bidirectional Evolutionary Search"

**Input**: Design documents from `/specs/001-symbolic-bes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. [UNRESOLVED-CLAIM: c_018388b7 — status=not_enough_info] Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

- [ ] T000c-impl [P] Generate `research.md` documenting the Dataset Strategy (Synthetic Curation + Scaling Generation) and Statistical Analysis Plan. **Constraint**: Must explicitly define the dataset source as `data/raw/curated_logic_v1.json`, scaling method (N=10..500), and statistical framework. Must define `complexity_metric` as a tuple of (constraint_count, variable_domain_size). **Dependency**: None.
- [ ] T000c-stats-def [P] Define Statistical Analysis Plan parameters in `research.md`. **Constraint**: Must define the two-proportion z-test parameters (alpha=0.05 (Wikipedia: Binomial proportion confidence interval, https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval)) and power analysis requirements. **Dependency**: Requires T000c-impl.
- [ ] T000d-impl [P] Generate `data-model.md` defining the Statistical Plan and Data Entities. **Constraint**: Must explicitly define the `complexity_metric` mapping to asymptotic complexity for SC-005 and the schema for `Puzzle Instance`. **Dependency**: Requires T000c-impl.
- [ ] T000a-def [P] Define the JSON schema structure for puzzle instances in text format. **Constraint**: Must define fields: `constraints` (array of strings), `initial_state` (object), `target_state` (object), `verifier_output` (object with `valid` boolean and `error_code` string), and `metadata` (object with `source_id`, `generation_seed`). Reference `data-model.md` section 2.1 for field definitions. **Dependency**: Requires T000d-impl.
- [ ] T000a-gen [P] Write the `contracts/dataset.schema.yaml` file from T000a-def definitions. **Constraint**: Must validate the schema against `data-model.md` requirements. **Dependency**: Requires T000a-def.
- [ ] T000a-verify [P] Verify `contracts/dataset.schema.yaml` syntax and schema validity. **Constraint**: Add a unit test `tests/unit/test_schema.py::test_dataset_schema_valid` that validates the YAML file. **Dependency**: Requires T000a-gen.
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

- [ ] T002b [P] Initialize Python virtual environment in `projects/PROJ-884-llmxive-follow-up-extending-self-improvi/`. **Constraint**: Must use `python3 -m venv.venv` and activate it via `source.venv/bin/activate`. Path relative to repo root. <!-- ATOMIZE: requested -->

- [X] T002c [P] Install dependencies in `requirements.txt` containing: `scikit-learn==1.3.2 `, `numpy==1.26.0 `, `transformers==4.35.0 `, `datasets==2.14.0 `, `pyyaml==6.0.1 `, `pytest==7.4.0 `, `optimum>=1.13.0,<1.16.0[onnxruntime] `. **Constraint**: Use fixed versions from plan.md. Must specify `optimum[onnxruntime]` for CPU-optimized quantization flags. Do NOT include `bitsandbytes`.

- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Constraint**: Must generate `.flake8` and `pyproject.toml` (for black) configuration files to satisfy plan.md testing requirements.

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

- [ ] T007b [P] [US1] Initialize `code/config.py` with `DEFAULT_TDP_WATTS = 65 ` as a safe fallback. **Constraint**: This value MUST be overwritten by T008c after calibration. **Dependency**: Requires T007. **Action**: If T008c is not run, the system MUST log a warning but continue execution. **Verification**: Must add unit test `tests/unit/test_config.py::test_tdp_placeholder_exists` that asserts the key exists AND that its value corresponds to the designated placeholder state.

- [ ] T008a-static-data [P] [US1] Generate `data/raw/cpu_tdp_map.json` from a pre-validated, versioned dataset (referencing a specific DOI). **Constraint**: Must NOT perform any runtime network lookups or literature searches. The file must be generated once from a static source and committed. **Dependency**: None.
- [ ] T008a-impl [P] [US1] Implement TDP Calibration Script in `code/utils/calibrate_tdp.py`. **Constraint**: Must detect the runner's CPU model (e.g., via `platform.machine()` or `lscpu`) and select a TDP value from `data/raw/cpu_tdp_map.json` (generated by T008a-static-data). If the CPU model is not found, use the generic fallback (representative nominal power) and log a warning. Must output `data/processed/calibration_run.json` with fields: `workload_type`, `cpu_percent`, `duration`, `estimated_tdp_watts`. **Dependency**: Requires T008a-static-data.
- [ ] T008a-exec [P] [US1] Execute TDP Calibration Script. **Constraint**: Must run T008a-impl. **Dependency**: Requires T008a-impl.
- [ ] T008c [P] [US1] Implement TDP Constant Generation Script in `code/utils/generate_tdp_constant.py`. **Constraint**: Must read `data/processed/calibration_run.json` (from T008a-exec) and `code/config.py` (T007b) to generate `data/processed/calibrated_tdp.json` with fields: `tdp_watts`, `source` ("verified-literature" or "fallback"), `error_margin`, `confidence_interval`, `citation_url`. **Dependency**: Requires T008a-exec and T007b. **Verification**: Must add unit test `tests/unit/test_calibrated_tdp.py::test_tdp_constant_valid` that asserts `data/processed/calibrated_tdp.json` exists, `tdp_watts` > 0, `source` is present, and `citation_url` is a valid URL.

- [ ] T008 [P] [US1] Setup error handling framework by creating `code/exceptions.py` defining custom exception classes for `PARSE_FAILURE`, `CONTRADICTION_DETECTED`, and `VERIFIER_ERROR` (to handle internal verifier failures, addressing robustness gap)

- [ ] T019d-impl [P] [US2] Implement `code/symbolic/exclusion_logger.py` to write exclusion events to `data/processed/exclusions.json`. **Constraint**: Must strictly adhere to the schema defined in `contracts/output.schema.yaml` (Tb-gen). Must generate a syntactically correct file. **Dependency**: Requires T000b-gen.
- [ ] T019d-verify [P] [US2] Verify exclusion logger schema. **Constraint**: Add a unit test `tests/unit/test_exclusion_logger.py::test_schema_valid` that validates the JSON structure. **Dependency**: Requires T019d-impl.

- [ ] T013 [P] [US2] Implement `code/symbolic/planner.py` to generate sub-goal decompositions, including logic to detect and flag `CONTRADICTION_DETECTED` or `PARSE_FAILURE`. **Constraint**: Must include the logic to call the exclusion logger (T019d-impl) directly within this module or via a helper. **Dependency**: Requires T019d-impl, T008.

- [ ] T018 [P] [US2] Implement `code/symbolic/parser.py` to convert puzzle constraints into a formal language parseable by the planner

- [ ] T020 [P] [US2] Generate `code/bes/config.py` with configuration for a small pre-trained LLM (`distilbert-base-uncased`). **Constraint**: This task is for **configuration file generation ONLY** (no download). Must specify `device='cpu'` and explicitly forbid `bitsandbytes`. Must explicitly mandate `optimum.onnxruntime` for CPU execution. Must define a fallback model (`TinyBERT`) if the primary model exceeds memory limits. **Dependency**: None.

- [ ] T021b-static [P] [US2] Generate `data/raw/model_manifest.json` containing the exact HuggingFace commit hash and file paths for the `distilbert-base-uncased` model. **Constraint**: Must NOT download the model. Must create a static manifest file that pins the exact version to ensure reproducibility. **Dependency**: Requires T020.
- [ ] T021b-cache [P] [US2] Download the `distilbert-base-uncased` model artifact to the cache directory *before* executing T021. **Constraint**: Must use `hf_hub_download` with the `revision` parameter locked to the commit hash in `data/raw/model_manifest.json` (from T021b-static). If download fails, attempt fallback model `TinyBERT`. Must verify the model exists in cache. **Dependency**: Requires T020, T021b-static.

- [ ] T021 [P] [US2] Implement `code/bes/forward_step.py` to perform trajectory recombination guided by symbolic sub-goals. **Constraint**: Must load the model specified in `code/bes/config.py` (default `distilbert-base-uncased`) using `optimum` CPU-optimized inference flags (`device='cpu'`, `torch.no_grad`, `optimum.onnxruntime`). Do NOT force 8-bit quantization unless verified. **Dependency**: Requires T020, T021b-cache.

- [ ] T022 [P] [US2] Implement `code/bes/population.py` to manage the evolutionary population, ensuring memory usage stays under a manageable threshold. **Note**: Must be implemented before T023 if T023 updates population state.

- [ ] T023 [P] [US2] Implement `code/bes/backward_step.py` to integrate the symbolic planner output into the evolutionary loop, replacing the neural verifier

- [ ] T024a [P] [US2] Implement `code/bes/parameter_generator.py` to generate the list of complexity parameters (N=10..500) for the BES loop. **Constraint**: Must output a JSON list of parameter sets. **Dependency**: None.
- [ ] T024b-exec [P] [US2] Implement `code/bes/loop_runner.py` to execute the BES loop for a single parameter set (N). **Constraint**: Must accept parameters from Ta, run the loop, and output a log file for that N. **Dependency**: Requires T024a, T021, T023, T028b.
- [ ] T024c [P] [US2] Implement `code/bes/result_aggregator.py` to aggregate logs from T024b-exec into a single result file. **Constraint**: Must combine all N-specific logs into `data/processed/bes_results.json`. **Dependency**: Requires T024b-exec.

- [ ] T016a [P] [US1] Implement `code/dataset/validate_data_against_contracts.py`. **Constraint**: This script MUST read generated data (from T014c-exec) and `contracts/dataset.schema.yaml` to verify schema compliance. **Dependency**: Requires T000a-gen, T014c-exec.
- [ ] T016b [P] [US1] Implement `code/analysis/validate_logs_against_contracts.py`. **Constraint**: This script MUST read output logs (from T029c-gen) and `contracts/output.schema.yaml` to verify schema compliance. **Dependency**: Requires T000b-gen, T029c-gen.

---

## Phase 3: User Story 1 - Dataset Construction and Symbolic Verification Pipeline (Priority: P1) 🎯 MVP

**Goal**: Instantiate a dataset of logic/arithmetic puzzles with deterministic Python verifiers capable of validating solution paths without LLMs.

**Independent Test**: Run verification scripts on a known set of correct and incorrect solutions to ensure high accuracy in classification before the LLM or evolutionary loop is engaged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for `code/dataset/generator.py` in `tests/unit/test_generator.py::test_generator_handles_empty_input`

- [ ] T010 [P] [US1] Unit test for `code/dataset/verifier.py` with known valid/invalid solutions in `tests/unit/test_verifier.py::test_verifier_rejects_invalid_solution`

### Implementation for User Story 1

- [ ] T044a-impl [P] [US1] Implement strict "Fail Loudly" logic in `code/dataset/generator.py`. **Constraint**: Must remove any try/except blocks that catch `DataGenerationError` or similar and substitute mock data. If the puzzle generation fails (e.g., constraint parsing error), the script must raise an exception and halt execution immediately. **Rationale**: Addresses the "Fabrication Gate" requirement. **Dependency**: Requires T000d-impl.
- [ ] T044b-verify [P] [US1] Verify "Fail Loudly" logic in `code/dataset/generator.py`. **Constraint**: Add a unit test that attempts to generate invalid data and confirms the script halts with an exception. **Dependency**: Requires T044a-impl.

- [ ] T054a-impl [P] [US1] Implement "Complexity Scaling" validation in `code/dataset/generator.py`. **Constraint**: The generator must output a `complexity_metric` for each puzzle and verify that the distribution of these metrics is continuous across the N=10..500 range. **Rationale**: Ensures SC-005 (Scalability) can be measured. **Dependency**: Requires T000d-impl. **Additional Constraint**: Must explicitly verify that `constraint_count` and `variable_domain_size` fields are populated in metadata. **Dependency**: Requires T011c-verify-metrics.
- [ ] T054b-verify [P] [US1] Verify "Complexity Scaling" distribution. **Constraint**: Add a test that generates a small set and verifies the `complexity_metric` spans the expected range. **Dependency**: Requires T054a-impl.

- [ ] T011a-curate [P] [US1] Define the formal language grammar for puzzle constraints in `code/dataset/grammar.py`. **Constraint**: Must explicitly define the parseable constraint types (e.g., equality, inequality, adjacency) and output a schema for validation. **Dependency**: Requires T000d-impl.
- [ ] T011 [P] [US1] Implement `code/dataset/generator.py` to create logic puzzles (Sudoku variants, constrained pathfinding) with systematic complexity scaling (N=10..500). **Constraint**: Must support command-line arguments for `N` and `count`. Must include "Fail Loudly" logic (Ta-impl) and "Complexity Scaling" (T054a-impl). Must enforce metadata population. Must validate constraints against the grammar defined in T011a-curate. **Dependency**: Requires T000d-impl, T044a-impl, T054a-impl, T011a-curate.

- [ ] T011c-verify-metrics [P] [US1] Implement explicit verification of `complexity_metric` fields in `code/dataset/generator.py`. **Constraint**: The generator must validate that `constraint_count` and `variable_domain_size` are present and non-null in the metadata of every generated puzzle. **Dependency**: Requires T011.
- [ ] T011c [P] [US1] Implement enforcement of puzzle metadata in `code/dataset/generator.py`. **Constraint**: The generator must populate the `metadata` field with a valid `source_id`, `generation_seed`, and timestamp for each generated puzzle instance. **Dependency**: Requires T011

- [ ] T012 [P] [US1] Implement `code/dataset/verifier.py` to execute deterministic validation logic for each puzzle instance, returning boolean validity and specific constraint violation codes (e.g., `DUPLICATE_ROW`, `INVALID_PATH`) within 100ms. **Note**: T012 validates the code, T014c/b generates the data.

- [ ] T014c-impl [P] [US1] Implement `code/dataset/generate_and_validate.py`. **Constraint**: This script MUST accept a directory of raw puzzles, run the verifier, calculate checksums, and output `data/processed/distribution_report.json` with type/complexity distribution stats. Must strictly enforce "Fail Loudly" (no synthetic fallback). Must call T019d-impl to log exclusions. Must validate constraints against the grammar (T011a-curate). **Dependency**: Requires T011, T012, T019d-impl, T011a-curate.
- [ ] T014c-parse-check [P] [US1] Implement the formal language validation step in `code/dataset/generate_and_validate.py`. **Constraint**: This task MUST parse the constraints of each generated puzzle against the grammar (T011a-curate) and flag any unparseable items. **Dependency**: Requires T014c-impl, T011a-curate.
- [ ] T014c-exclude [P] [US1] Implement the exclusion mechanism for unparseable puzzle constraints in `code/dataset/generate_and_validate.py`. This task MUST filter out puzzles with invalid or missing constraints before processing further, logging the excluded items to `data/processed/exclusions.json`. **Dependency**: Requires T014c-impl, T014c-parse-check, T019d-impl.
- [ ] T014c-exec [P] [US1] Execute `code/dataset/generate_and_validate.py`. **Constraint**: Must run the script generated in Tc-impl with parameters `--n` a sufficient number of instances `--count` a representative quantity `--types sudoku,pathfinding`. **Dependency**: Requires T014c-impl.

- [ ] T014e-impl [P] [US1] Implement `code/dataset/validate_distribution.py`. **Constraint**: This script MUST read `data/processed/distribution_report.json` (from T014c-exec) and `contracts/dataset.schema.yaml` (from T000a-gen) to verify statistical representativeness and output `data/processed/distribution_validation.json` with fields: `is_valid`, `power_estimate`, `notes`. **Dependency**: Requires T014c-exec.
- [ ] T014e-exec [P] [US1] Execute `code/dataset/validate_distribution.py`. **Constraint**: Must run after Te-impl. **Dependency**: Requires T014e-impl.

- [ ] T050a-impl [P] [US1] Implement "Fail Loudly" enforcement in `code/dataset/verifier.py`. **Constraint**: Ensure the verifier raises a specific `VerifierError` if the deterministic script fails to execute or returns an unexpected type, preventing silent fallback to "invalid" for system errors. **Rationale**: Addresses the "Fail Loudly" principle for data integrity. **Dependency**: Requires T012.
- [ ] T050b-verify [P] [US1] Verify "Fail Loudly" in verifier. **Constraint**: Add a unit test that simulates a verifier script crash and confirms the system raises an exception rather than returning a boolean. **Dependency**: Requires T050a-impl.

- [ ] T066 [P] [US1] Implement explicit "Data Provenance" metadata injection in `code/dataset/generator.py`. **Constraint**: Every generated puzzle file must include a JSON header with `source_id` (e.g., "curated_logic_v"), `generation_seed`, `timestamp`, and `generator_version`. This metadata must be validated by `code/dataset/verifier.py` before processing. **Rationale**: Addresses the "Single Source of Truth" and "Data Hygiene" principles by ensuring every data point is traceable to its exact generation parameters. **Dependency**: Requires T011.
- [ ] T066b-verify [P] [US1] Verify "Data Provenance" metadata. **Constraint**: Add a unit test that generates a puzzle, removes the metadata header, and confirms the verifier rejects the file with a `MISSING_METADATA` error. **Dependency**: Requires T066.

- [ ] T045a-impl [P] [US1] Add explicit "Sample Size Declaration" to `code/dataset/generate_and_validate.py`. **Constraint**: The script must output a `sample_size` field in `data/processed/distribution_report.json` and explicitly state the sampling rule (e.g., "First N=200 rows", "Random seed 42") if a subset is used. **Rationale**: Ensures transparency about data representativeness. **Dependency**: Requires T014c-impl.
- [ ] T045b-verify [P] [US1] Verify "Sample Size Declaration" in `data/processed/distribution_report.json`. **Constraint**: Add a test to verify the presence and correctness of the `sample_size` field. **Dependency**: Requires T045a-impl.

- [ ] T036 [P] [US1] Validate dataset distribution using `data/processed/distribution_validation.json`. **Constraint**: Must generate `data/processed/distribution_validation.json` and verify that the distribution of puzzle types matches the intended ratio and that complexity scaling is continuous. If validation fails, the task MUST fail and halt the pipeline. **Output**: Must generate `data/processed/validation_gate.json` with status `PASS` or `FAIL`. The JSON schema MUST be: `{"status": "PASS"|"FAIL", "reason": "string", "distribution_stats": {...}}`. **Dependency**: Requires T014e-exec, T044b-verify, T054b-verify.
- [ ] T036b-verify [P] [US1] Verify `validation_gate.json` schema. **Constraint**: Add a unit test `tests/unit/test_validation_gate.py::test_schema_valid` that validates the JSON structure matches the required schema. **Dependency**: Requires T036.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: Analysis & Complexity Characterization

**Purpose**: Derive statistical significance and complexity class from experimental results

- [ ] T029d-derive [P] [US3] Implement `code/analysis/complexity_deriver.py`. **Constraint**: Must perform TWO analyses: 1) Theoretical derivation of the Big-O complexity class based on the algorithm's structure (e.g., O(N^2) for nested loops), and 2) Empirical log-log linear regression on the runtime data. The final reported complexity class MUST be the theoretical derivation, with the empirical data used only as a consistency check. **Dependency**: Requires T024c.
- [ ] T029g [P] [US3] Generate `data/processed/complexity_report.json`. **Constraint**: Must report the theoretical complexity class and the empirical fit (R^). If the empirical fit deviates significantly from the theoretical derivation, flag as "DISCREPANCY_DETECTED". **Dependency**: Requires T029d-derive.