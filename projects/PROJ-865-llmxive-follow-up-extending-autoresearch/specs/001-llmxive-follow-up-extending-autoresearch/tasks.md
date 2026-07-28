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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [Setup] Initialize Project Structure: **Action**: Execute `code/utils/setup_dirs.py` to create the full directory tree (`code/`, `data/`, `data/raw/`, `data/derived/`, `data/artifacts/`, `specs/001-llmxive-followup/contracts/`, `code/01_data_ingestion/`, `code/02_annotation_distillation/`, `code/03_execution/`, `code/04_analysis/`, `code/utils/`, `tests/`). **Verification**: Run `code/utils/verify_dirs.py` to explicitly check for the existence of `.gitkeep` in `data/raw`, `data/derived`, `data/artifacts`, `code/01_data_ingestion`, `code/02_annotation_distillation`, `code/03_execution`, `code/04_analysis`, `code/utils`, `tests`, and `specs/001-llmxive-followup/contracts`. If any are missing, the task FAILS with exit code 1. **Dependency**: None.

- [X] T003 [Setup] Create `requirements.txt` at repository root with pinned versions (pandas, numpy, scikit-learn, statsmodels, pydantic, datasets, torch-cpu, transformers, psutil, scipy)

- [X] T004 [P] [Setup] **Configure Linting and Formatting**: Create `pyproject.toml` at repository root with explicit `[tool.ruff]` and `[tool.black]` sections. **Action**: Write the following content to `pyproject.toml`:
```toml
[tool.ruff]
line-length = 88
target-version = "py310"
ignore = ["E501"]

[tool.black]
line-length = 88
target-version = ['py310']
```
**Artifact**: `pyproject.toml`. **Dependency**: None.

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

- [X] T007 [Setup] Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`, `BASELINE_TIMEOUT_SECONDS=7200`, `BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`, `MAX_STREAMING_ROWS=500`, `EXPECTED_EFFECT_SIZE=0.5`, `DEFAULT_SAMPLE_SIZE=50`, `MODEL_PRIORITY_LIST=["Llama-3-8B-INT4", "Llama-3-4B-INT4", "TinyLlama-1.1B-INT4"]`. **Constraint**: `MODEL_PRIORITY_LIST` must contain at least one model.

- [X] T007c [Setup] **Implement Resource Watchdog Library**: Implement `code/utils/resource_watchdog.py` as a **Python library module** (not just a CLI wrapper) containing the fallback logic. **Logic**:
 1. **RAM Check**: Monitor RAM via `psutil`.
 2. **Deterministic Model Selection**: Implement a function `select_model(max_memory_gb, max_cpu_cores)` that reads the `MODEL_PRIORITY_LIST` from `code/utils/config.py` (defined in T007). The function checks the RAM requirement of each model against `max_memory_gb` in order.
 3. **Fallback Logic**: If a model fits, return it. If the list is exhausted without a match, raise `ResourceLimitExceeded`. If `MODEL_PRIORITY_LIST` is empty, raise `ResourceLimitExceeded` immediately.
 4. **Aggressive Sampling Fallback**: If no model fits within the limit, the function MUST implement 'aggressive sampling' by **reducing the dataset size by [deferred] iteratively** and retrying model selection. If the reduced dataset still exceeds limits, raises `ResourceLimitExceeded`.
 5. **Logging**: Implement a function `log_model_selection(model_name)` to record the selected model in the logs for reproducibility.
 6. **Constraint**: If the selected model exceeds the available system memory during loading, raise a `ResourceLimitExceeded` exception and exit with code 1 (failure).
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

- [X] T036 [US1] **Implement Streaming Data Loader**: Modify `code/01_data_ingestion/download_arc_bench.py` to use `datasets.load_dataset(..., streaming=True)` for the ARC-Bench dataset. **Logic**: Iterate through the dataset in chunks to process the full real dataset without exceeding the system's available memory limit. **Constraint**: If streaming fails (e.g., network error, dataset not found) OR if memory limits are exceeded during processing, the script MUST **exit with code 1 and log "Real data fetch failed; pipeline aborted"** to prevent silent constitution drift. **DO NOT** generate synthetic fallbacks. **Logging**: Log every chunk processed and a final summary of the total rows streamed. **Output**: Write the processed data directly to `data/derived/failure_cases_raw.json` (extracting `task_id`, `raw_error_log`, `ground_truth_resolution`, and `structural_feature` from the source). **Verification**: Verify that `data/derived/failure_cases_raw.json` exists and is non-empty. **Dependency**: T009, T043.

- [X] T050 [US1] **Implement Real Data Source Verification**: Create `code/01_data_ingestion/verify_real_data_source.py` to validate that the ARC-Bench dataset fetched in T036 matches the official checksum and metadata from the `claw-ai-lab/arc-bench` repository. **Logic**:
 1. Attempt to fetch `metadata.json` from the HuggingFace URL.
 2. **Fallback**: If the URL is unreachable (timeout/404), fetch `metadata.json` from a local cache or embedded resource in the repo.
 3. Compare the SHA-256 hash of the downloaded file against the hash provided in the metadata.
 4. If the hash does not match, raise a `DataIntegrityError` and exit with code 1.
 5. **Output**: `data/artifacts/data_source_verification.json` containing the hash, expected hash, and verification status. **Dependency**: T009, T036.

- [X] T011b [US1] [FR-001] **Artifact Generation**: Implement `code/02_annotation_distillation/annotate_failures.py` to read `data/derived/failure_cases_raw.json` (from T036), map the `structural_feature` field from the source data to the `annotated_structural_feature` field, and write the labeled dataset to `data/derived/failure_cases.json`. **Schema**: The JSON MUST be an array of objects with keys: `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"). **Data Splitting**: Implement logic within this script to split `failure_cases.json` into `failure_cases_train.json` ([deferred]), `failure_cases_val.json` ([deferred]), AND `failure_cases_test.json` ([deferred]) using the fixed random seed from `config.py` and **stratified by `annotated_structural_feature`**. **Schema Validation**: Validate output against `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` (T006a) before writing; if validation fails, raise an explicit error and stop. **Output**: Save all three files to `data/derived/`. **Dependency**: T006a, T036, T050.

- [X] T054 [US1] **Implement Annotation Inter-Rater Reliability Check**: Create `code/02_annotation_distillation/check_inter_rater.py` to calculate Cohen's Kappa for the structural feature annotations. **Logic**: If multiple human annotators are used, calculate Kappa directly. If only one human annotator is used (or if the source data has a single label), the script MUST log a warning "Human-in-the-Loop Ground Truth is partial (single annotator)" and proceed without failing the pipeline. The script MUST NOT simulate a second annotator. If Kappa < 0.6 (and multiple annotators exist), the script MUST exit with code 1 and log "Insufficient Human Validation: Kappa < 0.6. Pipeline cannot proceed." **Output**: `data/derived/inter_rater_reliability.json`. **Dependency**: T011b.

- [X] T013 [US1] [FR-002] Implement `code/02_annotation_distillation/distill_rules.py` using a CPU-tractable small model. **Model Selection & Fallback Logic**:
 1. **Deterministic Selection**: Use the `select_model` function from `resource_watchdog.py` (T007c) to select the largest model that fits within 7GB RAM from the list defined in `config.py`.
 2. **Pre-Check**: Verify that T043 (Quantization Verification) has passed. If not, raise an error.
 3. **Logging**: Log the selected model name explicitly to `data/artifacts/model_selection.log` for reproducibility.
 4. **Coverage Check**: Calculate coverage as the **percentage of unique error patterns in `failure_cases_val.json` that match at least one generated rule**. If coverage < 90%, the script MUST **log a warning "Partial Success: Coverage is {coverage}%" and write the rules to `data/derived/rules_library.json`** (do not exit with code 1). **Constraint**: Do NOT fallback to regex-based heuristic distillation.
 5. **Execution**: This task must be executed wrapped by the ResourceWatchdog from T007c.
 6. **Verification**: Run with a synthetic dataset known to yield [deferred] coverage and verify an error exit code to ensure the fallback logic triggers correctly.
 **Output**: Write `data/derived/rules_library.json` containing the generated rules. **Dependency**: T011b, T006b, T007c, T043, T054.

- [X] T015b [US1] [FR-002] **Schema Validation**: Implement `code/02_annotation_distillation/validate_rules.py` to validate `data/derived/rules_library.json` against `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` (T006b). **Pre-Check**: If `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` is missing or empty, the task MUST FAIL with exit code 1. **Action**: Run the validator. **Output**: `data/artifacts/rule_validation_report.json`. **Dependency**: T006b, T013.

- [X] T016 [US1] Add logging to track annotation counts and rule generation metrics: Extend `annotate_failures.py` to write structured logs to `data/artifacts/annotation.log`. **Metrics**: Log `total_cases`, `syntactic_count`, `semantic_count`, `logical_count`, `missing_count`, `unstructured_count`. **Dependency**: T011b.

- [X] T044 [P] [US3] **Statistical Power Analysis**: Implement `code/04_analysis/power_analysis.py` to calculate the statistical power of the mixed-effects regression given the sample size (N=500) and expected effect size (moderate). **Logic**: Use `statsmodels.stats.power` to estimate power. If power < 0.80, flag the result in the final report as "Low Power" and suggest a larger sample size. **Input**: Raw data availability from T009 (data download) to estimate potential sample size. **Output**: `data/derived/power_analysis_report.json`. **Dependency**: T009. **Note**: This task runs *before* T019a to validate the design.

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

- [X] T041 [P] [US2] **Verify GPU Policy Compliance**: Implement `code/03_execution/verify_gpu_policy.py` to scan all execution scripts (T017, T021) for `device="cuda"` or `load_in_8bit` flags. **Logic**: If any GPU-specific flags are detected in the rule engine or baseline execution paths (which must run on CPU per FR-004 and Constitution Principle VII), the script MUST raise a `PolicyViolationError` and exit with code 1. **Constraint**: This task acts as a pre-flight check before T019. **Output**: `data/artifacts/gpu_policy_report.json` confirming "PASS" or "FAIL". **Dependency**: T017, T021.

- [X] T019a [US2] **CRITICAL**: Implement `code/03_execution/generate_manifest.py` to create `data/derived/experiment_manifest.csv`. **Depends on T011b completion.**
 - **Source**: `data/derived/failure_cases_test.json` (from T011b).
 - **Pre-Check**: Validate that `failure_cases_test.json` exists.
 - **Logic**: Select a **stratified random sample** from the available data. The target sample size is determined by parsing the `recommended_sample_size` key from `data/derived/power_analysis_report.json` (T044). **Fallback**: If `power_analysis_report.json` is missing or empty, use `DEFAULT_SAMPLE_SIZE` from `config.py`. If a stratum has fewer than the required sample size, the script MUST sample the maximum available from that stratum and log a warning "Stratification adjusted: Insufficient data in stratum [Type]. Sampled N_max." If the total sample size is insufficient for statistical power (e.g., < 50), the script MUST fail with an error "Insufficient data for stratified sampling. Pipeline cannot proceed."
 - **Validation**: Verify the output CSV contains the sampled rows AND verify that the distribution of failure_type matches the source distribution within an acceptable tolerance (**stratification_tolerance=0.05**).
 - **Reproducibility**: Use the fixed random seed defined in `code/utils/config.py`.
 - **Output**: CSV with columns `task_id`, `failure_type`.
 - **Dependency**: T011b, T044, T054.

- [X] T019 [US2] Implement `code/03_execution/run_experiments.py` to run the rule engine on the tasks listed in `data/derived/experiment_manifest.csv`. **Pre-Check**: Verify `data/derived/experiment_manifest.csv` exists and is non-empty before attempting to load `rules_library.json`. **Logic**: If the manifest is missing, the script MUST exit with code 1 and a clear error message: "Experiment manifest not found. Ensure T019a (generate_manifest.py) has completed successfully." **Dependency**: T019a, T017, T041.

- [X] T020 [US2] Ensure `run_experiments.py` records "Time-to-Pivot" (seconds), "Success Rate of First Pivot" (binary), and `failure_type` for every task, appending rows to `data/derived/results_rule_engine.csv` with columns: task_id, method, time_to_pivot, success, failure_type. **Stratification**: Metrics MUST be recorded and tagged by `failure_type`. **Dependency**: T006c.

- [X] T021c [US2] **Instrument Baseline Resource Metrics**: Implement `code/03_execution/instrument_baseline.py` to wrap the baseline agent execution and capture resource metrics. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Constraint**: Run on **Standard Resources** (4 CPU, 16 GB RAM) via `resource_watchdog.py` (T007c) by **explicitly passing** `BASELINE_CPU_CORES=4` and `BASELINE_MEMORY_GB=16` to the watchdog function, overriding the global defaults. **Note**: This is a description of the standard environment, not a hard-coded limit that prevents execution. The baseline is expected to run on a more powerful environment than the rule engine.
 3. Monitor process `CPU` and `RAM` via `psutil` and log to `data/derived/baseline_resource_metrics.json`.
 4. **Verification**: Run a dummy process with known memory usage and verify `baseline_resource_metrics.json` captures the correct `peak_memory_mb`.
 5. **Output**: `data/derived/baseline_resource_metrics.json` with schema `{ task_id, peak_memory_mb, cpu_time_seconds }`. **Dependency**: T019a.

- [X] T021 [US2] Implement `code/03_execution/run_baseline.py` to orchestrate baseline agent execution. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Mode Selection**: Invoke `instrument_baseline.py` (T021c) with the enforced **Standard Resource** constraints (4 CPU, 16 GB RAM) on the **local runner**.
 3. **CI Job Execution**: **DO NOT** rely on local simulation. Instead, this script MUST trigger a **separate CI job** (e.g., via GitHub Actions API or a dedicated runner) to execute the baseline agent on standard resources. **Constraint**: Do NOT rely on external runners. The simulation must enforce the resource limits locally.
 4. **Polling Loop**: Poll for `data/derived/baseline_results.json` and `data/derived/baseline_resource_metrics.json` with exponential backoff. **Constraint**: Do NOT enforce an arbitrary timeout that blocks data collection; the process must wait for the job to complete or fail permanently.
 5. **Timeout Handling**: If the job fails permanently, log an error and exit with a failure status code. Implement a SIGINT signal handler to allow explicit cancellation.
 6. **Output**: `data/derived/baseline_results.json` with the exact same task IDs as the manifest. **Format**: JSON object with keys `task_id`, `time_to_pivot`, `success`. **Dependency**: T021c, T019a, T041.

- [X] T022 [US2] [FR-004] **Data Merging**: Implement `code/03_execution/merge_results.py` to merge CI rule-engine logs (`data/derived/results_rule_engine.csv`) with baseline logs (`data/derived/baseline_results.json`) into a single `data/derived/results.csv`, ensuring strict ID matching for paired comparison (required for SC-001 and SC-002) using the manifest from T019a. **Validation**: Verify that `baseline_results.json` contains all task IDs from the manifest. If a task is missing due to external failure, mark it as 'failed' in `results.csv`. **Handle Failures**: Explicitly **retain** failed baselines in the `time_to_pivot` column with a sentinel value of `-1.0` (censored data) and `success` as `false` for the same task IDs. Do NOT filter out failed baselines. **Pre-Check**: Verify that `data/derived/results_rule_engine.csv` and `data/derived/baseline_results.json` exist and are non-empty. If either is missing, exit with code 1. **Dependency**: T021, T019a.

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed-effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

**⚠️ DEPENDENCY**: This phase MUST wait for Phase 4 (US2) completion to access `data/derived/results.csv`.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/04_analysis/statistical_model.py` to fit mixed-effects logistic regression (Success ~ FailureType * Method + (1|TaskID))

- [X] T026a [US3] **Model Fitting**: Ensure `statistical_model.py` outputs p-values for the interaction term to `data/derived/regression_results.json`. **Dependency**: T022.

- [X] T026b [US3] [SC-003] **Significance Determination**: Implement logic in `statistical_model.py` (or a wrapper) to compare the p-value from T026a against alpha=0.05. **Output**: Update `data/derived/regression_results.json` with key `interaction_significant` (boolean) and `narrative_conclusion` (string: "The interaction term is significant (p < 0.05)" or "The interaction term is not significant (p >= 0.05)"). **Dependency**: T026a.

- [X] T029a [US3] [SC-001] Implement `code/04_analysis/time_diff_test.py` to perform **Tobit Regression** (censored data handling) on "Time-to-Pivot" differences using `statsmodels` or `lifelines`. **Logic**: Include rows where the baseline failed (timeout/error) as censored observations (time = -1.0 from T022) rather than excluding them. This addresses survivorship bias. **Crucial**: Ensure the data is **paired** (same task IDs for Rule Engine and Baseline) and the regression is performed on the paired differences or a paired design matrix as required by SC-001. **Justification**: Tobit Regression is selected over t-test/Wilcoxon because SC-001 requires handling censored data (infinite/undefined steps), which standard tests cannot process. **Output schema**: `data/derived/time_diff_results.json` containing keys: `p_value`, `ci_lower`, `ci_upper`, `statistic`. **Dependency**: T022.

- [X] T029b [US3] [SC-002] Implement `code/04_analysis/calculate_stratified_rates.py` to calculate "Success Rate of First Pivot" stratified by failure type. **Verification**: Verify that the sum of rates weighted by sample size equals the overall success rate. **Output**: `data/derived/stratified_success_rates.csv` with columns `failure_type`, `rate` (long format). **Dependency**: T022.

- [X] T027 [US3] [FR-007] Implement `code/04_analysis/error_taxonomy.py` to categorize failed pivots. **Inputs**: `data/derived/results.csv` (from T022) and `data/derived/failure_cases.json` (from T011b). **Logic**: If no rule matches -> "Coverage Gap"; If rule matches but action != `ground_truth_resolution` (from T011b) -> "Distillation Error". **Exclude**: Cases where `ground_truth_resolution` is null or empty are excluded from the count and logged separately as "Missing Ground Truth". **Pre-Check**: Verify that `data/derived/results.csv` (from T022) and `data/derived/failure_cases.json` (from T011b) exist and are non-empty. If either is missing, exit with code 1. **Dependency**: T022, T011b.

- [X] T027b [US3] **Execute & Populate**: Run `error_taxonomy.py` against `data/derived/results.csv` and `data/derived/failure_cases.json` to generate `data/derived/error_taxonomy_results.json`. **Output Schema**: `{ "coverage_gap_count": <int>, "distillation_error_count": <int>, "total_failures": <int>, "breakdown_by_type": { "<type>": { "coverage_gap": <int>, "distillation_error": <int> } } }`. **Note**: `total_failures` explicitly **excludes** cases where `ground_truth_resolution` is null. **Depends on T022, T011b**.

- [X] T027c [US3] **Analyze Missing Ground Truth**: Implement `code/04_analysis/analyze_missing_gt.py` to aggregate and report on the "Missing Ground Truth" subset excluded in T027. **Logic**: Count and list task IDs where `ground_truth_resolution` was null. **Output**: `data/derived/missing_gt_report.json` with count and sample task IDs. **Dependency**: T011b.

- [X] T028 [US3] **Ground Truth Arbitration**: Ensure `error_taxonomy.py` uses `ground_truth_resolution` from `failure_cases.json` to arbitrate the categorization of failures (Coverage Gap vs Distillation Error). **Dependency**: T011b.

- [X] T029c [US3] [SC-001] **Execute Time Diff**: Run `time_diff_test.py` to generate `data/derived/time_diff_results.json`. **Dependency**: T029a.

- [X] T029d [US3] [SC-002] **Execute Stratified Rates**: Run `calculate_stratified_rates.py` to generate `data/derived/stratified_success_rates.csv`. **Dependency**: T029b.

- [X] T051 [US3] **Implement Censored Data Visualization**: Create `code/04_analysis/visualize_censored_data.py` to generate a Kaplan-Meier survival curve for "Time-to-Pivot" comparing the Rule Engine vs. Baseline, explicitly marking censored observations (failed tasks). **Logic**: Use `lifelines` to fit Kaplan-Meier estimators for both methods and plot the survival function with confidence intervals. **Output**: `data/derived/km_survival_curve.png` and `data/derived/km_survival_data.csv`. **Dependency**: T022, T029a.

- [X] T053 [US3] **Implement Sensitivity Analysis for Distillation Threshold**: Create `code/04_analysis/sensitivity_distillation.py` to re-run the distillation process (T013) with varying coverage thresholds (85%, 90%, 95%) and measure the impact on the final success rate of the rule engine. **Logic**: Iterate through thresholds, regenerate rules, re-run the rule engine on the test set, and record the success rate. **Output**: `data/derived/distillation_sensitivity.csv` with columns `threshold`, `rule_count`, `success_rate`. **Dependency**: T013, T019a.

- [X] T030a [US3] [SC-005] **Resource Logging (Local)**: Implement `code/04_analysis/aggregate_local_resources.py` to collect local resource logs (from T013, T017) and output `data/derived/local_resource_log.json`. **Output Schema**: `{ "task_id": <string>, "peak_memory_mb": <float>, "cpu_time_seconds": <float> }`. **Dependency**: T013, T017.

- [X] T030b [US3] [SC-005] **Resource Logging (Entire Experiment)**: Implement `code/04_analysis/aggregate_external_resources.py` to collect local resource logs (from T013, T017) AND baseline metrics (from T021) and produce `data/derived/resource_summary.json` containing total compute time and peak memory for the **entire experiment**. **Logic**: Calculate **total_compute_time_seconds** as the **wall-clock duration** of the entire experiment (from the start of the first task to the end of the last task) to accurately reflect CI time limits. **Constraint**: This task explicitly INCLUDES baseline metrics to ensure the metric reflects the total resource usage of the comparative study as required by SC-005. **Verification**: Compare `total_compute_time_seconds` against the GitHub Actions free-tier time limit.. If exceeded, log a failure status and **exit with code 1**, blocking the pipeline. **Dependency**: T013, T017, T021, T044. **Output Schema**: `{ "total_compute_time_seconds": <float>, "peak_memory_mb": <float> }`.

- [X] T047 [US3] [SC-003] **Validate Interaction Term Robustness**: Implement `code/04_analysis/validate_interaction.py` to perform a sensitivity analysis on the mixed-effects model by bootstrapping the dataset multiple times and verifying that the interaction term remains significant in >95% of iterations. **Logic**: Use `statsmodels` to fit the model on multiple bootstrap samples.. Count iterations where p-value < 0.05. **Output**: `data/derived/interaction_sensitivity.json` containing keys: `total_iterations`, `significant_count`, `percentage_significant`. **Verification**: Verify the JSON contains `percentage_significant` > 0.95. **Dependency**: T026a.

- [X] T029e [US3] [SC-003] [SC-004] [SC-005] **Create Report Template**: Implement `code/04_analysis/templates/report_template.md.j2`. **Template Path**: `code/04_analysis/templates/report_template.md.j2`. **Variables**: `regression_results`, `time_diff_results`, `stratified_success_rates`, `error_taxonomy_results`, `resource_summary`, `interaction_sensitivity`, `missing_gt_report`. **Structure**: Executive Summary, Methodology, Time-to-Pivot Analysis (SC-001), Success Rate Analysis (SC-002), Error Taxonomy (SC-004), Statistical Significance (SC-003 - MUST include `p_value`, `ci_lower`, `ci_upper`, and `interaction_significant` from T026b), and Conclusion. **Narrative Logic**: If `p_value` < 0.05, write "The interaction term is statistically significant (p < 0.05), indicating that failure structure dictates method viability." Else, write "The interaction term is not statistically significant (p >= 0.05)." **Dependency**: None (creates artifact).

- [X] T029f [US3] [Report] **Generate Final Report**: Execute `code/04_analysis/generate_report.py` with the template from T029e and data from T026b, T029c, T029d, T027b, T027c, T030b, T047 to produce `data/derived/final_report.md`. **Pre-Check**: Verify that all 8 required input artifacts (`regression_results.json`, `time_diff_results.json`, `stratified_success_rates.csv`, `error_taxonomy_results.json`, `resource_summary.json`, `interaction_sensitivity.json`, `missing_gt_report.json`, `report_template.md.j2`) exist and are non-empty. If any are missing, exit with code 1. **Dependency**: T029e, T026b, T029c, T029d, T027b, T027c, T030b, T047.

- [X] T055 [US3] **Implement Final Report Executive Summary Generator**: Create `code/04_analysis/generate_executive_summary.py` to extract key findings from `data/derived/final_report.md` and generate a one-page summary in `data/derived/executive_summary.md`. **Logic**: Extract the `narrative_conclusion` from T026b, the `interaction_significant` status, the `coverage_gap_count` vs `distillation_error_count` ratio, the `missing_gt_count` from T027c, and the `percentage_significant` from T047. Format these into a concise summary suitable for non-technical stakeholders. **Dependency**: T029f, T026b, T027b, T027c, T047.

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

- [X] T044 [P] [US3] **Statistical Power Analysis**: (See Phase 3, T044). This task is now fully implemented and runs before the experiment.

- [X] T047 [P] [US3] **Validate Interaction Term Robustness**: (See Phase 5, T047). This task is now fully implemented with 100 bootstrap iterations.

- [X] T051 [P] [US3] **Implement Censored Data Visualization**: (See Phase 5, T051). This task is now fully implemented.

- [X] T053 [P] [US3] **Implement Sensitivity Analysis for Distillation Threshold**: (See Phase 5, T053). This task is now fully implemented.

- [X] T054 [P] [US1] **Implement Annotation Inter-Rater Reliability Check**: (See Phase 3, T054). This task is now fully implemented with human-in-the-loop requirement.

- [X] T055 [P] [US3] **Implement Final Report Executive Summary Generator**: (See Phase 5, T055). This task is now fully implemented.

- [X] T060 [Setup] **Implement Final Orchestration Script**: Create `code/main.py` to serve as the single entry point for the entire pipeline, invoking tasks in strict dependency order (Phase 0 → 1 → 2 → 3 → 4 → 5). **Action**: Write `code/main.py` to import and execute the main functions of T002, T001, T007, T009, T036, T050, T011b, T054, T013, T015b, T017, T019a, T019, T020, T021, T022, T025, T026a, T026b, T029a, T029b, T027, T027b, T027c, T029c, T029d, T051, T053, T030a, T030b, T047, T029e, T029f, T055. **Execution Logic**: The script MUST execute tasks sequentially. **Enforcement**: For T002, the script MUST check the exit code; if non-zero, it MUST skip T002b and exit. For all other tasks, if any returns a non-zero exit code, the script MUST stop immediately and report the failure. **Dependency**: All prior tasks.

- [X] T057 [US1] **Enforce Strict Data Flow for Distillation**: Refactor `code/02_annotation_distillation/distill_rules.py` to explicitly verify that `data/derived/failure_cases_train.json` and `data/derived/failure_cases_val.json` exist and contain non-zero rows before attempting model loading. **Rationale**: Previous analysis flagged a potential race condition where distillation might start before the annotation phase fully committed the split files. **Action**: Add a `validate_inputs()` function at the start of the script that checks file existence and row count, raising `FileNotFoundError` with message "Input files missing or empty" and exit code 1 if missing. **Dependency**: T011b.

- [X] T058 [US2] **Add Baseline Execution Pre-flight Check**: Insert a new task before T021 to verify that the local runner environment is reachable and configured with `BASELINE_CPU_CORES=4` and `BASELINE_MEMORY_GB=16`. **Action**: Create `code/03_execution/verify_baseline_env.py` which attempts a lightweight "ping" or resource query to the local environment. If the runner is unreachable or resource constraints are not met, the script MUST exit with code 1 and log "Baseline Environment Unreachable: Check runner configuration." **Rationale**: Ensures the baseline comparison (FR-004) does not fail silently due to environment misconfiguration. **Dependency**: T021c.

- [X] T059 [US3] **Validate Censored Data Handling in Visualization**: Update `code/04_analysis/visualize_censored_data.py` to explicitly assert that the input data contains censored observations (failed tasks) and that the Kaplan-Meier estimator correctly handles them. **Action**: Add a check in `visualize_censored_data.py` that counts rows where `time_to_pivot` equals `TIMEOUT_SECONDS` (from `config.py`). If zero censored rows are found, log a warning "No censored data detected; survival curve may be inaccurate." **Rationale**: SC-001 requires handling censored data; this task ensures the visualization logic actually processes such data if it exists. **Dependency**: T022, T029a.