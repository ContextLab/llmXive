# Tasks: llmXive follow-up: extending "AutoResearchClaw"

**Input**: Design documents from `/specs/001-llmxive-followup/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Constitutional Gates

**Purpose**: Mandatory validation steps required by the Project Constitution before any development begins.

- [X] T002 [Setup] **Reference-Validator Execution**: Implement and execute the `Reference-Validator Agent` as a blocking gate against `plan.md` and `spec.md`. **Action**: Run `code/utils/validate_citations.py` with arguments `--input specs/001-llmxive-followup/plan.md --input specs/001-llmxive-followup/spec.md --output data/artifacts/citation_validation_report.json`. **Gate**: If any citation is `unreachable` or `mismatch`, the pipeline MUST fail and block all subsequent tasks. **Output**: `data/artifacts/citation_validation_report.json` with status `PASS` or `FAIL`. **Dependency**: None (runs first).

- [X] T002b [Setup] **Record Validation State**: Record the results of T002 into the project state file. **Action**: Execute `code/utils/update_state.py` with arguments `--artifact data/artifacts/citation_validation_report.json --state-file state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` to update the hash and timestamp. **Constraint**: This task runs ONLY if T002 passes. **Dependency**: T002. **Citation**: Per Constitution Principle V (Versioning Discipline). **Orchestration Enforcement**: The main orchestration script (T060) MUST explicitly check the exit code of T002 before invoking T002b. If T002 returns non-zero, T002b is skipped and the pipeline exits with an error.

---

## Phase 0.5: Human-in-the-Loop Ground Truth Generation

**Purpose**: Generate the multi-annotator consensus required for T054 validation, as the source data is raw transcripts.

- [X] T005a [US1] **Implement Human Annotation Interface**: Create `code/02_annotation_distillation/annotation_interface.py` to load raw failure transcripts and present them to human annotators. **Logic**: Load `data/derived/failure_cases_raw.json` (from T036). Display `raw_error_log` and `ground_truth_resolution`. Prompt annotator to select `annotated_structural_feature` from the enum. **Constraint**: Requires at least 2 distinct annotator sessions per case. **Output**: `data/derived/annotator_1.json` and `data/derived/annotator_2.json` (or more if needed). **Dependency**: T036.

- [X] T005b [US1] **Implement Consensus Generation**: Create `code/02_annotation_distillation/generate_consensus.py` to merge `annotator_1.json` and `annotator_2.json`. **Logic**: If annotations match, record as consensus. If they differ, flag for manual resolution (T005c). **Output**: `data/derived/consensus_labels.json`. **Dependency**: T005a.

- [X] T005c [US1] **Resolve Disagreements**: Create `code/02_annotation_distillation/resolve_disagreements.py` to handle cases where annotators disagree. **Logic**: Load `consensus_labels.json`. For cases with `None` (disagreement), log a warning and exclude from the final dataset (do not exit 1, but document the exclusion). **Output**: `data/derived/failure_cases_consensus.json` (final labeled dataset). **Dependency**: T005b.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [Setup] Initialize Project Structure: **Action**: Execute `code/utils/setup_dirs.py` to create the full directory tree (`code/`, `data/`, `data/raw/`, `data/derived/`, `data/artifacts/`, `specs/001-llmxive-followup/contracts/`, `code/01_data_ingestion/`, `code/02_annotation_distillation/`, `code/03_execution/`, `code/04_analysis/`, `code/utils/`, `tests/`). **Verification**: Run `code/utils/verify_dirs.py` to explicitly check for the existence of `.gitkeep` in `data/raw`, `data/derived`, `data/artifacts`, `code/01_data_ingestion`, `code/02_annotation_distillation`, `code/03_execution`, `code/04_analysis`, `code/utils`, `tests`, and `specs/001-llmxive-followup/contracts`. If any are missing, the task FAILS with an error exit code.. **Dependency**: None.

- [X] T003 [Setup] Create `requirements.txt` at repository root with pinned versions (pandas, numpy, scikit-learn, statsmodels, pydantic, datasets, torch-cpu, transformers, psutil, scipy, lifelines)

- [X] T004 [P] [Setup] **Configure Linting and Formatting**: Create `pyproject.toml` at repository root with explicit `[tool.ruff]` and `[tool.black]` sections. **Action**: Check if `pyproject.toml` exists at the repository root.
 1. If it exists, read the file content. Parse the TOML to extract existing sections. Merge the new `[tool.ruff]` and `[tool.black]` configurations into the existing structure, preserving any other sections. Write the merged content back to the file.
 2. If it does not exist, create a new file with the following content:
```toml
[tool.ruff]
line-length = 88
target-version = "py310"
ignore = ["E501"]

[tool.black]
line-length = 88
target-version = ['py310']
```
**Artifact**: `pyproject.toml`. **Dependency**: None. **Note**: If `pyproject.toml` exists, merge the configuration sections; do not overwrite the entire file.

- [X] T005 [P] [Setup] **Create.gitignore**: Create or update the root `.gitignore` file to explicitly include rules for `data/raw/`, `data/derived/`, and `data/artifacts/`. **Action**: Append the following lines to `.gitignore`:
```text
data/raw/*
!data/raw/.gitkeep
data/derived/*
!data/derived/.gitkeep
data/artifacts/*
!data/artifacts/.gitkeep
```
**Artifact**: `.gitignore`. **Dependency**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006a [Setup] **Create Schema**: Create `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"). **Content**:
```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
 task_id: { type: string }
 raw_error_log: { type: string }
 ground_truth_resolution: { type: string }
 annotated_structural_feature:
 type: string
 enum:
 - "Syntactic Error"
 - "Logical Loop"
 - "Semantic Ambiguity"
 - "Missing Context"
 - "Unstructured"
required:
 - task_id
 - raw_error_log
 - ground_truth_resolution
 - annotated_structural_feature
```
**Dependency**: None.

- [X] T006b [Setup] **Create Schema**: Create `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` with explicit JSON schema definition: keys `rule_id` (string), `condition_pattern` (string), `pivot_action` (string), `confidence` (float). **Action**: Write the following content to `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml`:
```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
 rule_id: { type: string }
 condition_pattern: { type: string }
 pivot_action: { type: string }
 confidence: { number }
required:
 - rule_id
 - condition_pattern
 - pivot_action
 - confidence
```
**Dependency**: None.

- [X] T006c [Setup] **Create Schema**: Create `specs/001-llmxive-followup/contracts/pivot_attempt.schema.yaml` with explicit JSON schema definition: keys `task_id` (string), `method` (string), `time_to_pivot` (float), `success` (boolean), `failure_type` (string). **Content**:
```yaml
$schema: http://json-schema.org/draft-07/schema#
type: object
properties:
 task_id: { type: string }
 method: { type: string }
 time_to_pivot: { number }
 success: { type: boolean }
 failure_type: { type: string }
required:
 - task_id
 - method
 - time_to_pivot
 - success
 - failure_type
```
**Dependency**: None.

- [X] T007 [Setup] Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`, `BASELINE_TIMEOUT_SECONDS=7200`, `BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`, `MAX_STREAMING_ROWS=500`, `EXPECTED_EFFECT_SIZE=0.5`, `DEFAULT_SAMPLE_SIZE=50`, `MODEL_PRIORITY_LIST=["Llama-8B-INT4", "Llama-3-4B-INT4", "TinyLlama-1.1B-INT4"]`. **Constraint**: `MODEL_PRIORITY_LIST` must contain at least one model.

- [X] T007c [Setup] **Implement Resource Watchdog Library**: Implement `code/utils/resource_watchdog.py` as a **Python library module** (not just a CLI wrapper) containing the fallback logic. **Logic**:
 1. **RAM Check**: Monitor RAM via `psutil`.
 2. **Deterministic Model Selection**: Implement a function `select_model(max_memory_gb, max_cpu_cores)` that reads the `MODEL_PRIORITY_LIST` from `code/utils/config.py` (defined in T007). The function checks the RAM requirement of each model against `max_memory_gb` in order.
 3. **Fallback Logic**: If a model fits, return it. If the list is exhausted without a match, raise `ResourceLimitExceeded`. If `MODEL_PRIORITY_LIST` is empty, raise `ResourceLimitExceeded` immediately.
 4. **Aggressive Sampling Fallback**: If no model fits within the limit, the function MUST implement 'aggressive sampling' by **reducing the dataset size by [deferred] iteratively** and retrying model selection. If the reduced dataset still exceeds limits, raises `ResourceLimitExceeded`.
 5. **Logging**: Implement a function `log_model_selection(model_name)` to record the selected model in the logs for reproducibility.
 6. **Constraint**: If the selected model exceeds the available system memory during loading, raise a `ResourceLimitExceeded` exception and exit with a failure code.
 **Dependency**: T007.

- [X] T007c-test [P] [Setup] **Unit Tests for Resource Watchdog**: Write unit tests in `code/tests/test_resource_watchdog.py` for the `select_model` and `log_model_selection` functions. **Test Cases**: Simulate high RAM usage, verify correct model selection, verify `ResourceLimitExceeded` exception. **Dependency**: T007c.

- [X] T008 [Setup] Implement `code/utils/logging.py` for structured logging of pipeline stages

- [X] T043 [P] [US1] **Validate Model Quantization**: Implement `code/02_annotation_distillation/verify_quantization.py` to ensure the selected model (from T007c) is actually loaded in INT4 precision. **Logic**:
 1. **Invoke Watchdog**: Call `select_model` from `resource_watchdog.py` (T007c) to determine the viable model.
 2. **Iterate & Load**: Attempt to load the first model in `MODEL_PRIORITY_LIST` in INT4. If it fails (OOM or error), attempt the next model in the list.
 3. **Success**: If any model loads successfully in INT4, verify `model.config.quantization_config` or `model.hf_quantizer` is set to INT4.
 4. **Failure**: If *all* models in the list fail to load in INT4, raise an error.
 5. **Output**: `data/artifacts/quantization_verification.json` containing the selected model name and status.
 6. **Constraint**: This task guarantees a valid output file; it only fails if *no* model in the priority list can be loaded in INT4.
 **Dependency**: T007, T007c.

---

## Phase 3: User Story 1 - Failure Mode Annotation & Rule Distillation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest ARC-Bench failure transcripts, annotate structural features, and generate a deterministic rule library using a CPU-tractable small model.

**Independent Test**: Run the pipeline on a small held-out subset of cases and verify `rules_library.json` contains valid "If-Condition-Then-Action" structures.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/01_data_ingestion/download_arc_bench.py` to fetch the ARC-Bench topic subset via HuggingFace `datasets`.

- [X] T050 [US1] **Implement Real Data Source Verification**: Create `code/01_data_ingestion/verify_real_data_source.py` to validate that the ARC-Bench dataset fetched in T009 matches the official checksum and metadata from the `claw-ai-lab/arc-bench` repository. **Logic**:
 1. Attempt to fetch `metadata.json` from the HuggingFace URL.
 2. **Fallback**: If the URL is unreachable (timeout/404), fetch `metadata.json` from a local cache or embedded resource in the repo.
 3. Compare the SHA-256 hash of the downloaded file against the hash provided in the metadata.
 4. If the hash does not match, raise a `DataIntegrityError` and exit with code 1.
 5. **Output**: `data/artifacts/data_source_verification.json` containing the hash, expected hash, and verification status. **Dependency**: T009. **Note**: This task runs BEFORE T036 to ensure data integrity before streaming.

- [X] T036 [US1] **Implement Streaming Data Loader**: Modify `code/01_data_ingestion/download_arc_bench.py` to use `datasets.load_dataset(..., streaming=True)` for the ARC-Bench dataset. **Logic**: Iterate through the dataset in chunks to process the full real dataset without exceeding the system's available memory limit. **Constraint**: If streaming fails (e.g., network error, dataset not found), the script MUST exit with code 1 and log "Streaming Failed: Real data source unavailable. Pipeline cannot proceed." **Constraint**: NO synthetic fallback is allowed. **Logging**: Log every chunk processed and a final summary of the total rows streamed. **Output**: Write the processed data directly to `data/derived/failure_cases_raw.json` (extracting `task_id`, `raw_error_log`, `ground_truth_resolution`, and `structural_feature` from the source). **Verification**: Verify that `data/derived/failure_cases_raw.json` exists, is non-empty, and contains a flag indicating it is real data. **Dependency**: T009, T050, T043.

- [X] T011b [US1] [FR-001] **Artifact Generation**: Implement `code/02_annotation_distillation/annotate_failures.py` to read `data/derived/failure_cases_consensus.json` (from T005c), map the `structural_feature` field from the source data to the `annotated_structural_feature` field, and write the labeled dataset to `data/derived/failure_cases.json`. **Schema**: The JSON MUST be an array of objects with keys: `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"). **Data Splitting**: Implement logic within this script to split `failure_cases.json` into `failure_cases_train.json`, `failure_cases_val.json`, AND `failure_cases_test.json` using a fixed random seed from `config.py` and a **stratified train/validation/test split** by `annotated_structural_feature`. **Schema Validation**: Validate output against `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` (T006a) before writing; if validation fails, raise an explicit error and stop. **Output**: Save all three files to `data/derived/`. **Dependency**: T006a, T005c, T050.

- [X] T054 [US1] **Implement Annotation Inter-Rater Reliability Check**: Create `code/02_annotation_distillation/check_inter_rater.py` to calculate Cohen's Kappa for the structural feature annotations. **Logic**: Read `annotator_1.json` and `annotator_2.json` (from T005a). Calculate Kappa. If Kappa < 0.6, log a warning "Low Inter-Rater Reliability: Kappa < 0.6. Proceeding with caution." but do NOT exit 1. The pipeline can proceed with the consensus labels. **Output**: `data/derived/inter_rater_reliability.json`. **Dependency**: T005a.

- [X] T013 [US1] [FR-002] Implement `code/02_annotation_distillation/distill_rules.py` using a CPU-tractable small model. **Model Selection & Fallback Logic**:
 1. **Deterministic Selection**: Use the `select_model` function from `resource_watchdog.py` (T007c) to select the largest model that fits within 7GB RAM from the list defined in `config.py`.
 2. **Pre-Check**: Verify that T043 (Quantization Verification) has passed. If not, raise an error.
 3. **Logging**: Log the selected model name explicitly to `data/artifacts/model_selection.log` for reproducibility.
 4. **Coverage Check**: If the selected model produces <90% coverage on `data/derived/failure_cases_val.json`, the script MUST fail with an error and exit with code 1. **Constraint**: Do NOT fallback to regex-based heuristic distillation. If coverage is insufficient, the pipeline halts to preserve the 'CPU-tractable small language model' requirement.
 5. **Execution**: This task must be executed wrapped by the ResourceWatchdog from T007c.
 6. **Verification**: Run with a synthetic dataset known to yield [deferred] coverage and verify an error exit code to ensure the fallback logic triggers correctly.
 **Output**: Write `data/derived/rules_library.json` containing the generated rules. **Dependency**: T011b, T006b, T007c, T043, T054.

- [X] T015b [US1] [FR-002] **Schema Validation**: Implement `code/02_annotation_distillation/validate_rules.py` to validate `data/derived/rules_library.json` against `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` (T006b). **Pre-Check**: If `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` is missing or empty, the task MUST FAIL with exit code 1. **Action**: Run the validator. **Output**: `data/artifacts/rule_validation_report.json`. **Dependency**: T006b, T013.

- [X] T016 [US1] Add logging to track annotation counts and rule generation metrics: Extend `annotate_failures.py` to write structured logs to `data/artifacts/annotation.log`. **Metrics**: Log `total_cases`, `syntactic_count`, `semantic_count`, `logical_count`, `missing_count`, `unstructured_count`. **Dependency**: T011b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

**Goal**: Execute the distilled rule engine on a held-out test set and compare performance against the full baseline agent.

**Independent Test**: Run on 10 unseen tasks, log "Time-to-Pivot" and "Success", and verify metrics match expected format.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 3 (US1) completion to access `rules_library.json` and `failure_cases.json`.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/03_execution/rule_engine.py` to parse error logs and execute pivot actions without LLM invocation. **This task must be executed wrapped by the ResourceWatchdog from T007c.** **Logic**:
 1. **Base Logic**: Implement primary rule matching.
 2. **Fallback Strategy**: If no rule matches (Unstructured), implement a secondary "keyword-based" retrieval using the first 50 characters of the error log. Extract keywords, query context index, return top results. Log the fallback chain.
 3. **Output**: Update `data/derived/results_rule_engine.csv` with a new column `fallback_chain`. **Dependency**: T006c.

- [X] T041 [P] [US2] **Verify GPU Policy Compliance**: Implement `code/03_execution/verify_gpu_policy.py` to scan all execution scripts (T017, T021) for `device="cuda"` or `load_in_8bit` flags. **Logic**: If any GPU-specific flags are detected in the rule engine or baseline execution paths (which must run on CPU per FR-004 and Constitution Principle VII), the script MUST raise a `PolicyViolationError` and exit with code 1. **Constraint**: This task acts as a pre-flight check before T019. **Output**: `data/artifacts/gpu_policy_report.json` confirming "PASS" or "FAIL". **Dependency**: T017, T021c.

- [X] T019a [US2] **CRITICAL**: Implement `code/03_execution/generate_manifest.py` to create `data/derived/experiment_manifest.csv`. **Depends on T011b completion.**
 - **Source**: `data/derived/failure_cases_test.json` (from T011b).
 - **Pre-Check**: Validate that `failure_cases_test.json` exists.
 - **Logic**: Select a **stratified random sample** from the available data. The target sample size is determined by parsing the `recommended_sample_size` key from `data/derived/power_analysis_report.json` (T044). **Fallback**: If `power_analysis_report.json` is missing or empty, use `DEFAULT_SAMPLE_SIZE` from `config.py`. If a stratum has fewer than the required sample size, the script MUST sample the maximum available from that stratum and log a warning "Stratification adjusted: Insufficient data in stratum [Type]. Sampled N_max." If the total sample size is insufficient for statistical power (e.g., < 50), the script MUST fail with an error "Insufficient data for stratified sampling. Pipeline cannot proceed."
 - **Validation**: Verify the output CSV contains the sampled rows AND verify that the distribution of failure_type matches the source distribution within an acceptable tolerance (**stratification_tolerance=0.05**).
 - **Reproducibility**: Use the fixed random seed defined in `code/utils/config.py`.
 - **Output**: CSV with columns `task_id`, `failure_type`.
 - **Dependency**: T011b, T044, T054.

- [X] T019 [US2] Implement `code/03_execution/run_experiments.py` to run the rule engine on the tasks listed in `data/derived/experiment_manifest.csv`. **Pre-Check**: Verify `data/derived/experiment_manifest.csv` exists and is non-empty before attempting to load `rules_library.json`. **Logic**: If the manifest is missing, the script MUST exit with a failure code. and a clear error message: "Experiment manifest not found. Ensure T019a (generate_manifest.py) has completed successfully." **Dependency**: T019a, T017, T041.

- [X] T020 [US2] Ensure `run_experiments.py` records "Time-to-Pivot" (seconds), "Success Rate of First Pivot" (binary), and `failure_type` for every task, appending rows to `data/derived/results_rule_engine.csv` with columns: task_id, method, time_to_pivot, success, failure_type. **Stratification**: Metrics MUST be recorded and tagged by `failure_type`. **Dependency**: T006c.

- [X] T058b [US2] **Provision Baseline Runner**: Create `code/03_execution/provision_baseline_runner.py` to verify the existence and configuration of the separate standard-resource runner. **Logic**:
 1. **Ping**: Attempt to connect to the baseline runner API endpoint defined in `config.py` (e.g., `BASELINE_RUNNER_URL`).
 2. **Resource Check**: Query the runner for available resources (CPU, RAM). Verify it matches `BASELINE_CPU_CORES=4` and `BASELINE_MEMORY_GB=16`.
 3. **Failure**: If the runner is unreachable or resources are insufficient, exit with a failure code. and log "Baseline Environment Unreachable: Check runner configuration."
 4. **Success**: Log "Baseline Runner Verified" and create `data/artifacts/baseline_runner_status.json`.
 **Dependency**: T007.

- [X] T021c [US2] **Instrument Baseline Resource Metrics (Local)**: Implement `code/03_execution/instrument_baseline.py` to wrap the *trigger* of the baseline agent execution and capture local resource metrics of the trigger script. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Constraint**: This script runs locally but *triggers* the remote execution. It does NOT run the baseline itself.
 3. Monitor local process `CPU` and `RAM` via `psutil` and log to `data/derived/baseline_trigger_metrics.json`.
 4. **Verification**: Run a dummy process with known memory usage and verify `baseline_trigger_metrics.json` captures the correct `peak_memory_mb`.
 5. **Output**: `data/derived/baseline_trigger_metrics.json` with schema `{ task_id, peak_memory_mb, cpu_time_seconds }`. **Dependency**: T019a.

- [X] T021 [US2] Implement `code/03_execution/run_baseline.py` to orchestrate baseline agent execution on the **separate standard-resource runner**. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Trigger**: Send a POST request to the baseline runner API endpoint (defined in T058b) with the manifest path and resource constraints.
 3. **Polling Loop**: Poll for `data/derived/baseline_results.json` and `data/derived/baseline_resource_metrics.json` on the remote runner (or via a shared artifact store) with exponential backoff. **Constraint**: Do NOT rely on local simulation. The execution must occur on the separate runner.
 4. **Timeout Handling**: If the job fails permanently, log an error and exit with a failure status code. Implement a SIGINT signal handler to allow explicit cancellation.
 5. **Output**: `data/derived/baseline_results.json` with the exact same task IDs as the manifest. **Format**: JSON object with keys `task_id`, `time_to_pivot`, `success`. **Dependency**: T021c, T019a, T041, T058b.

- [X] T022 [US2] [FR-004] **Data Merging**: Implement `code/03_execution/merge_results.py` to merge CI rule-engine logs (`data/derived/results_rule_engine.csv`) with baseline logs (`data/derived/baseline_results.json`) into a single `data/derived/results.csv`, ensuring strict ID matching for paired comparison using the manifest from T019a. **Validation**: Verify that `baseline_results.json` contains all task IDs from the manifest. If a task is missing due to external failure, mark it as 'failed' in `results.csv`. **Handle Failures**: Explicitly **retain** failed baselines in the `time_to_pivot` column with a sentinel value indicating censored data and `success` as `false` for the same task IDs. Do NOT filter out failed baselines. **Dependency**: T021, T019a.

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed-effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 4 (US2) completion to access `data/derived/results.csv`.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/04_analysis/statistical_model.py` to fit mixed-effects logistic regression (Success ~ FailureType * Method + (1|TaskID))

- [X] T026a [US3] **Model Fitting**: Ensure `statistical_model.py` outputs p-values for the interaction term to `data/derived/regression_results.json`. **Dependency**: T022.

- [X] T026b [US3] [SC-003] **Significance Determination**: Implement logic in `statistical_model.py` (or a wrapper) to compare the p-value from T026a against alpha=0.05. **Output**: Update `data/derived/regression_results.json` with key `interaction_significant` (boolean) and `narrative_conclusion` (string: "The interaction term is significant (p < 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value))" or "The interaction term is not significant (p >= 0.05)"). **Dependency**: T026a.

- [X] T029a [US3] [SC-001] Implement `code/04_analysis/time_diff_tobit.py` to perform **Tobit Regression** (censored data handling) on "Time-to-Pivot" differences using `statsmodels` or `lifelines`. **Logic**:
 1. **Load Threshold**: Load `TIMEOUT_SECONDS` from `code/utils/config.py` to use as the censoring threshold value.
 2. **Censored Handling**: Include rows where the baseline failed (timeout/error) as censored observations (time = `TIMEOUT_SECONDS` from T022) rather than excluding them. This addresses survivorship bias.
 3. **Crucial**: Ensure the data is **paired** (same task IDs for Rule Engine and Baseline) and the regression is performed on the paired differences or a paired design matrix as required by SC-001.
 **Output schema**: `data/derived/time_diff_tobit_results.json` containing keys: `p_value`, `ci_lower`, `ci_upper`, `statistic`. **Dependency**: T022.

- [X] T029g [US3] [SC-001] **Imputation for Paired Tests**: Create `code/04_analysis/impute_censored_data.py` to impute censored values in `results.csv` for the purpose of Paired t-test/Wilcoxon. **Logic**:
 1. **Imputation Strategy**: For censored observations (timeout), impute a value based on a survival-based estimator (e.g., mean of uncensored times + margin) or use a multiple imputation approach if available.
 2. **Validation**: Log the imputation method used and the number of imputed values.
 3. **Output**: `data/derived/imputed_results.csv` with filled values.
 **Dependency**: T022.

- [X] T029h [US3] [SC-001] **Paired t-test/Wilcoxon**: Create `code/04_analysis/paired_test.py` to perform **Paired t-test** AND **Wilcoxon signed-rank test** on the imputed "Time-to-Pivot" differences from T029g. **Logic**:
 1. Load `data/derived/imputed_results.csv`.
 2. Perform Paired t-test. If normality fails (Shapiro-Wilk), perform Wilcoxon signed-rank test.
 3. **Output**: `data/derived/time_diff_paired_results.json` containing `p_value`, `statistic`, `test_type`.
 **Dependency**: T029g.

- [X] T029b [US3] [SC-002] Implement `code/04_analysis/calculate_stratified_rates.py` to calculate "Success Rate of First Pivot" stratified by failure type. **Verification**: Verify that the sum of rates weighted by sample size equals the overall success rate. **Output**: `data/derived/stratified_success_rates.csv` with columns `failure_type`, `rate` (long format). **Dependency**: T022.

- [X] T027 [US3] [FR-007] Implement `code/04_analysis/error_taxonomy.py` to categorize failed pivots. **Inputs**: `data/derived/results.csv` (from T022) and `data/derived/failure_cases.json` (from T011b). **Logic**: If no rule matches -> "Coverage Gap"; If rule matches but action != `ground_truth_resolution` (from T011b) -> "Distillation Error". **Exclude**: Cases where `ground_truth_resolution` is null or empty are excluded from the count and logged separately as "Missing Ground Truth". **Pre-Check**: Verify that `data/derived/results.csv` (from T022) and `data/derived/failure_cases.json` (from T011b) exist and are non-empty. If either is missing, exit with a non-zero status code indicating failure.. **Dependency**: T022, T011b.

- [X] T027b [US3] **Execute & Populate**: Run `error_taxonomy.py` against `data/derived/results.csv` and `data/derived/failure_cases.json` to generate `data/derived/error_taxonomy_results.json`. **Output Schema**: `{ "coverage_gap_count": <int>, "distillation_error_count": <int>, "total_failures": <int>, "breakdown_by_type": { "<type>": { "coverage_gap": <int>, "distillation_error": <int> } } }`. **Note**: `total_failures` explicitly **excludes** cases where `ground_truth_resolution` is null. **Depends on T022, T011b**.

- [X] T027c [US3] **Analyze Missing Ground Truth**: Implement `code/04_analysis/analyze_missing_gt.py` to aggregate and report on the "Missing Ground Truth" subset excluded in T027. **Logic**: Count and list task IDs where `ground_truth_resolution` was null. **Output**: `data/derived/missing_gt_report.json` with count and sample task IDs. **Dependency**: T011b.

- [X] T027d [US3] [SC-004] **Aggregate Failure Proportions**: Create `code/04_analysis/aggregate_failure_proportions.py` to combine the counts from T027b and T027c. **Logic**: Calculate the proportion of "Coverage Gap" and "Distillation Error" against the **total** number of failures (including "Missing Ground Truth"). **Output**: `data/derived/failure_proportions.json` with keys `coverage_gap_proportion`, `distillation_error_proportion`, `missing_gt_proportion`. **Dependency**: T027b, T027c.

- [X] T028 [US3] **Ground Truth Arbitration**: Ensure `error_taxonomy.py` uses `ground_truth_resolution` from `failure_cases.json` to arbitrate the categorization of failures (Coverage Gap vs Distillation Error). **Dependency**: T011b.

- [X] T029c [US3] [SC-001] **Execute Time Diff (Tobit)**: Run `time_diff_tobit.py` to generate `data/derived/time_diff_tobit_results.json`. **Dependency**: T029a.

- [X] T029d [US3] [SC-002] **Execute Stratified Rates**: Run `calculate_stratified_rates.py` to generate `data/derived/stratified_success_rates.csv`. **Dependency**: T029b.

- [X] T051 [US3] **Implement Censored Data Visualization**: Create `code/04_analysis/visualize_censored_data.py` to generate a Kaplan-Meier survival curve for "Time-to-Pivot" comparing the Rule Engine vs. Baseline, explicitly marking censored observations (failed tasks). **Logic**: Use `lifelines` to fit Kaplan-Meier estimators for both methods and plot the survival function with confidence intervals. **Output**: `data/derived/km_survival_curve.png` and `data/derived/km_survival_data.csv`. **Dependency**: T022, T029a.

- [X] T053 [US3] **Implement Sensitivity Analysis for Distillation Threshold**: Create `code/04_analysis/sensitivity_distillation.py` to re-run the distillation process (T013) with varying coverage thresholds (85%, 90%, 95%) and measure the impact on the final success rate of the rule engine. **Logic**: Iterate through thresholds, regenerate rules, re-run the rule engine on the test set, and record the success rate. **Output**: `data/derived/distillation_sensitivity.csv` with columns `threshold`, `rule_count`, `success_rate`. **Dependency**: T013, T019a.

- [X] T030a [US3] [SC-005] **Resource Logging (Local)**: Implement `code/04_analysis/aggregate_local_resources.py` to collect local resource logs (from T013, T017) and output `data/derived/local_resource_log.json`. **Output Schema**: `{ "task_id": <string>, "peak_memory_mb": <float>, "cpu_time_seconds": <float> }`. **Dependency**: T013, T017.

- [X] T030c [US3] [SC-005] **Post-Hoc Resource Audit**: Implement `code/04_analysis/post_hoc_resource_audit.py` to calculate the total wall-clock duration of the entire experiment. **Logic**:
 1. **Trigger**: This task is triggered by the CI completion event (post-pipeline), not as a dependency of T060.
 2. **Duration Calculation**: Calculate **total_compute_time_seconds** as the **wall-clock duration** of the entire experiment (from the start of the first task to the end of the last task) using timestamps recorded by T060.
 3. **Constraint**: This task explicitly INCLUDES baseline metrics to ensure the metric reflects the total resource usage of the comparative study as required by SC-005.
 4. **Verification**: Compare `total_compute_time_seconds` against the GitHub Actions free-tier time limit. If exceeded, log a failure status in `data/derived/resource_summary.json` but do NOT exit with code 1 (as the pipeline has already completed).
 **Dependency**: T013, T017, T021, T022. **Output Schema**: `{ "total_compute_time_seconds": <float>, "peak_memory_mb": <float> }`.

- [X] T047 [US3] [SC-003] **Validate Interaction Term Robustness**: Implement `code/04_analysis/validate_interaction.py` to perform a sensitivity analysis on the mixed-effects model by bootstrapping the dataset multiple times and verifying that the interaction term remains significant in >95% of iterations. **Logic**: Use `statsmodels` to fit the model on multiple bootstrap samples. Count iterations where p-value < 0.05. **Output**: `data/derived/interaction_sensitivity.json` containing keys: `total_iterations`, `significant_count`, `percentage_significant`. **Verification**: Verify the JSON contains `percentage_significant` > 0.95. **Dependency**: T026a.

- [X] T029e [US3] [SC-003] [SC-004] [SC-005] **Create Report Template**: Implement `code/04_analysis/templates/report_template.md.j2`. **Template Path**: `code/04_analysis/templates/report_template.md.j2`. **Variables**: `regression_results`, `time_diff_tobit_results`, `time_diff_paired_results`, `stratified_success_rates`, `failure_proportions`, `resource_summary`, `interaction_sensitivity`, `missing_gt_report`. **Structure**: Executive Summary, Methodology, Time-to-Pivot Analysis (SC-001), Success Rate Analysis (SC-002), Error Taxonomy (SC-004), Statistical Significance (SC-003 - MUST include `p_value`, `ci_lower`, `ci_upper`, and `interaction_significant` from T026b), and Conclusion. **Narrative Logic**: If `p_value` < 0.05, write "The interaction term is statistically significant (p < 0.05), indicating that failure structure dictates method viability." Else, write "The interaction term is not statistically significant (p >= 0.05)." **Template Content**:
```markdown
# Final Report: llmXive Follow-up

## Executive Summary
{{ narrative_conclusion }}

## Methodology
...

## Time-to-Pivot Analysis (SC-001)
...

## Success Rate Analysis (SC-002)
...

## Error Taxonomy (SC-004)
...

## Statistical Significance (SC-003)
...

## Conclusion
...
```
**Dependency**: None (creates artifact).

- [X] T029f [US3] [Report] **Generate Final Report**: Execute `code/04_analysis/generate_report.py` with the template from T029e and data from T026b, T029c, T029h, T029d, T027d, T027c, T030a, T047 to produce `data/derived/final_report.md`. **Pre-Check**: Verify that all required input artifacts exist and are non-empty. If any are missing, exit with a non-zero status code.. **Dependency**: T029e, T026b, T029c, T029h, T029d, T027d, T027c, T030a, T047.

- [X] T055 [US3] **Implement Final Report Executive Summary Generator**: Create `code/04_analysis/generate_executive_summary.py` to extract key findings from `data/derived/final_report.md` and generate a one-page summary in `data/derived/executive_summary.md`. **Logic**: Extract the `narrative_conclusion` from T026b, the `interaction_significant` status, the `coverage_gap_count` vs `distillation_error_count` ratio, the `missing_gt_count` from T027c, and the `percentage_significant` from T047. Format these into a concise summary suitable for non-technical stakeholders. **Dependency**: T029f, T026b, T027d, T027c, T047.

- [X] T031 [P] Write `code/tests/test_rule_engine.py` to validate rule matching logic. **Test Cases**: `test_syntactic_error_match` (verify regex match), `test_unstructured_fallback` (verify default behavior), `test_edge_case_empty_log` (verify handling of empty logs). **Input Data**: **Generate mock data within the test script** to ensure determinism without requiring pipeline execution. **Dependency**: T017.

- [X] T032 [P] Write `code/tests/test_pipeline.py` for integration tests of the full data flow

- [X] T033 [P] Update `quickstart.md` with instructions for running the pipeline and baseline: Add a section "Running the Baseline" with steps: 1. Ensure baseline agent is installed. 2. Run `python code/03_execution/run_baseline.py --manifest data/derived/experiment_manifest.csv`. 3. Wait for `data/derived/baseline_results.json`. **Dependency**: T021.

- [X] T034 [P] Run `code/utils/update_state.py` to finalize `state.yaml` with all artifact hashes: Verify `state.yaml` contains updated hashes for all `data/derived/` artifacts and the `updated_at` timestamp is current. **Dependency**: T029f.

- [X] T035a [P] Run `ruff --check` on `code/` and verify exit code 0 (linting pass): If check fails, generate `lint_report.txt` with the error output and exit with code 1.

- [X] T035b [P] Run `black --check` on `code/` and verify exit code 0 (formatting pass): If check fails, generate `lint_report.txt` with the error output and exit with code 1.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T048 [P] **Update State**: Create `code/utils/update_state.py` to calculate SHA-256 hashes of all artifacts in `data/derived/` and `results/`. **File Filter**: Recursively traverse directories, filtering for files with extensions `.json`, `.csv`, `.yaml`. **Hash Calculation**: Include the full relative path in the hash calculation to ensure reproducibility. **Execution**: Run this task after each major phase (US1, US2, US3) and in this final phase. Update `state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` with the new hashes and `updated_at` timestamp.

---

## Revision Tasks: Addressing Analysis Findings

**Purpose**: New tasks added to resolve specific issues identified by the `/speckit.analyze` agent regarding data flow, resource constraints, and data hygiene.

### Data Hygiene & Streaming (FR-001, US-1)

- [X] T050 [US1] **Implement Real Data Source Verification**: (See Phase 3, T050). This task is now integrated into the main flow with explicit failure logic.

### Execution Order & Data Flow (US-2, US-3)

- [X] T019 [US2] **Enforce Manifest Generation Order**: (See Phase 4, T019). The manifest check is now an internal pre-condition of T019.

### Error Taxonomy & Ground Truth (FR-007, US-3)

- [X] T027 [US3] **Validate Ground Truth Integrity**: (See Phase 5, T027). The validation step is now part of the main task.

### External Baseline Integration (US-2)

- [X] T021 [US2] **Implement Baseline Timeout Handling**: (See Phase 4, T021). The timeout handling is now part of the main task.

### Compute Feasibility & GPU Policy (Constitutional Compliance)

- [X] T041 [P] [US2] **Verify GPU Policy Compliance**: (See Phase 4, T041). This task is now a blocking gate before execution.

- [X] T043 [P] [US1] **Validate Model Quantization**: (See Phase 2, T043). This task is now a blocking gate before distillation.

- [X] T047 [P] [US3] **Validate Interaction Term Robustness**: (See Phase 5, T047). This task is now fully implemented with A sufficient number of bootstrap iterations.

- [X] T051 [P] [US3] **Implement Censored Data Visualization**: (See Phase 5, T051). This task is now fully implemented.

- [X] T053 [P] [US3] **Implement Sensitivity Analysis for Distillation Threshold**: (See Phase 5, T053). This task is now fully implemented.

- [X] T054 [P] [US1] **Implement Annotation Inter-Rater Reliability Check**: (See Phase 3, T054). This task is now fully implemented with human-in-the-loop requirement.

- [X] T055 [P] [US3] **Implement Final Report Executive Summary Generator**: (See Phase 5, T055). This task is now fully implemented.

- [X] T060 [Setup] **Implement Final Orchestration Script**: Create `code/main.py` to serve as the single entry point for the entire pipeline, invoking tasks in strict dependency order (Phase 0 → 1 → 2 → 3 → 4 → 5). **Action**: Write `code/main.py` to import and execute the main functions of T002, T001, T007, T009, T050, T036, T005a, T005b, T005c, T011b, T054, T013, T015b, T017, T019a, T019, T020, T021, T022, T025, T026a, T026b, T029a, T029g, T029h, T029b, T027, T027b, T027c, T027d, T029c, T029d, T051, T053, T030a, T047, T029e, T029f, T055. **Rationale**: Resolves the "run-book vs implementation mismatch" identified in T056 by providing a concrete, executable entry point that matches the plan. **Dependency**: All prior tasks.

- [X] T057 [US1] **Enforce Strict Data Flow for Distillation**: Refactor `code/02_annotation_distillation/distill_rules.py` to explicitly verify that `data/derived/failure_cases_train.json` and `data/derived/failure_cases_val.json` exist and contain non-zero rows before attempting model loading. **Rationale**: Previous analysis flagged a potential race condition where distillation might start before the annotation phase fully committed the split files. **Action**: Add a `validate_inputs()` function at the start of the script that checks file existence and row count, raising `FileNotFoundError` with message "Input files missing or empty" and exit code 1 if missing. **Dependency**: T011b.

- [X] T058 [US2] **Add Baseline Execution Pre-flight Check**: (See T058b). This task is now fully implemented.

- [X] T059 [US3] **Validate Censored Data Handling in Visualization**: Update `code/04_analysis/visualize_censored_data.py` to explicitly assert that the input data contains censored observations (failed tasks) and that the Kaplan-Meier estimator correctly handles them. **Action**: Add a check in `visualize_censored_data.py` that counts rows where `time_to_pivot` equals `TIMEOUT_SECONDS` (from `config.py`). If zero censored rows are found, log a warning "No censored data detected; survival curve may be inaccurate." **Rationale**: SC-001 requires handling censored data; this task ensures the visualization logic actually processes such data if it exists. **Dependency**: T022, T029a.

- [X] T061 [US1] **Enforce Streaming-First Data Loading**: Modify `code/01_data_ingestion/download_arc_bench.py` to strictly enforce `streaming=True` as the default behavior for all dataset loads, removing any fallback to `load_dataset` without streaming unless explicitly overridden by a `--full-load` flag. **Rationale**: Prevents accidental OOM errors on large datasets by ensuring the primary path is memory-efficient streaming. **Dependency**: T009, T050.

- [X] T062 [US2] **Implement Paired-Data Integrity Check**: Add a validation step in `code/03_execution/merge_results.py` to verify that every `task_id` in `results_rule_engine.csv` has a corresponding entry in `baseline_results.json` before merging. **Rationale**: Ensures the paired comparison required by SC-001 is valid and prevents silent data loss in the final analysis. **Dependency**: T019a, T021.

- [X] T063 [US3] **Add Sensitivity Analysis for Censoring Threshold**: Implement `code/04_analysis/sensitivity_censoring.py` to re-run the Tobit regression (T029a) with varying `TIMEOUT_SECONDS` thresholds (e.g., 3000s, 3600s, 4200s) to verify the robustness of the Time-to-Pivot difference conclusion. **Rationale**: Validates that the statistical significance of SC-001 is not an artifact of the specific timeout value chosen. **Dependency**: T022, T029a.

- [ ] T064 [US3] **Implement Cross-Validation for Regression Coefficients**: Create `code/04_analysis/cross_validate_regression.py` to perform k-fold cross-validation (k=5) on the mixed-effects model to assess the stability of the interaction term coefficients across different data splits. **Rationale**: Addresses potential overfitting concerns in the statistical model by verifying that the observed interaction effect is consistent across subsets of the data, not just the full sample. **Action**: Split `data/derived/results.csv` into 5 folds, fit the model on 4 folds, test on 1, and aggregate coefficients. Output `data/derived/cross_val_results.json` with mean and std dev of interaction coefficients. **Dependency**: T025, T026a.

- [ ] T065 [US2] **Implement Baseline Failure Mode Analysis**: Create `code/03_execution/analyze_baseline_failures.py` to specifically categorize baseline agent failures (those that timed out or errored) by their `failure_type` from `failure_cases.json`. **Rationale**: Ensures the comparison in SC-001 and SC-002 is not biased by baseline failures that might be systematically related to specific failure types (e.g., baseline failing more on "Semantic Ambiguity"). **Action**: Filter `baseline_results.json` for `success=false`, join with `failure_cases.json` on `task_id`, and calculate failure rates per type. Output `data/derived/baseline_failure_analysis.json`. **Dependency**: T021, T011b.

- [ ] T066 [US1] **Add Rule Coverage Visualization**: Create `code/02_annotation_distillation/visualize_rule_coverage.py` to generate a bar chart showing the distribution of failure types covered by the distilled rules vs. those falling into the "Unstructured" bucket. **Rationale**: Provides a quick visual diagnostic of the rule engine's limitations before execution, helping to identify if certain failure types are systematically under-covered. **Action**: Read `rules_library.json` and `failure_cases_val.json`, calculate coverage per type, and plot using `matplotlib`. Output `data/derived/rule_coverage_chart.png`. **Dependency**: T013, T011b.

- [ ] T067 [US3] **Implement Effect Size Calculation**: Create `code/04_analysis/calculate_effect_size.py` to compute Cohen's d (or equivalent for paired data) for the Time-to-Pivot difference between Rule Engine and Baseline. **Rationale**: While p-values indicate significance, effect sizes quantify the magnitude of the difference, which is crucial for practical interpretation of the research findings (SC-001). **Action**: Use `statsmodels.stats.effect_size` to calculate effect size on paired differences from `data/derived/results.csv`. Output `data/derived/effect_size_results.json`. **Dependency**: T022, T029a. <!-- ATOMIZE: requested -->

- [ ] T068 [US2] **Implement Resource Usage Correlation Analysis**: Create `code/04_analysis/analyze_resource_correlation.py` to investigate if baseline resource usage (CPU/RAM) correlates with failure types or success rates. **Rationale**: Tests the hypothesis that certain failure types might inherently require more resources to resolve, which could explain why the baseline (with more resources) succeeds where the rule engine fails. **Action**: Join `baseline_resource_metrics.json` with `baseline_results.json` and `failure_cases.json`, calculate correlations. Output `data/derived/resource_correlation_report.json`. **Dependency**: T021c, T021, T011b.