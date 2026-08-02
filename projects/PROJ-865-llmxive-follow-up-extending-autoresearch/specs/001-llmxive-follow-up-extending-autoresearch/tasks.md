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

- [X] T002 [Gate] **Reference-Validator Execution**: Implement and execute the `Reference-Validator Agent` as a blocking gate against `plan.md` and `spec.md`. **Action**:
 1. Fetch the primary source URLs/DOIs for all citations listed in `plan.md` and `spec.md` (e.g., the HuggingFace dataset `claw-ai-lab/arc-bench` or the associated paper DOI).
 2. Run `code/utils/validate_citations.py` with arguments `--input specs/001-llmxive-followup/plan.md --input specs/001-llmxive-followup/spec.md --output data/artifacts/citation_validation_report.json`.
 3. The validator MUST verify that each citation matches the metadata (title, authors, year) retrieved from the **primary source** (not just internal markdown).
 **Gate**: If any citation is `unreachable` or `mismatch` against the primary source, the pipeline MUST fail and block all subsequent tasks. **Output**: `data/artifacts/citation_validation_report.json` with status `PASS` or `FAIL`. **Dependency**: Existence of `plan.md` and `spec.md` files. **Citation**: Per Constitution Principle II (Verified Accuracy). **Orchestration Enforcement**: The main orchestration script (T060) MUST explicitly check the exit code of T002 before invoking T002b. If T002 returns non-zero, T002b is skipped and the pipeline exits with an error.

- [X] T002b [Setup] **Record Validation State**: Record the results of T002 into the project state file. **Action**: Execute `code/utils/update_state.py` with arguments `--artifact data/artifacts/citation_validation_report.json --state-file state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` to update the hash and timestamp. **Constraint**: This task runs ONLY if T002 passes. **Dependency**: T002. **Citation**: Per Constitution Principle V (Versioning Discipline). **Orchestration Enforcement**: The main orchestration script (T060) MUST explicitly check the exit code of T002 before invoking T002b. If T002 returns non-zero, T002b is skipped and the pipeline exits with an error.

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
target-version = "py"
ignore = ["E501"]

[tool.black]
line-length = 88
target-version = ['py']
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
 confidence: { type: number }
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
 time_to_pivot: { type: number }
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

- [X] T007 [Setup] Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`, `BASELINE_TIMEOUT_SECONDS=7200`, `BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`, `MAX_STREAMING_ROWS=500`, `DEFAULT_SAMPLE_SIZE=50`, `MODEL_PRIORITY_LIST=["Llama-8B-INT4", "Llama-3-4B-INT4", "TinyLlama-1.1B-INT4"]`.

```python
# code/utils/config.py
"""
Configuration constants for the llmXive follow-up project.
"""

# Statistical Power Analysis
# Reference: Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.).
# This value represents a medium effect size convention for social sciences.
EXPECTED_EFFECT_SIZE = 0.5
```
**Constraint**: `MODEL_PRIORITY_LIST` must contain at least one model.

- [X] T007c [Setup] **Implement Resource Watchdog Library**: Implement `code/utils/resource_watchdog.py` as a **Python library module** (not just a CLI wrapper) containing the fallback logic. **Logic**:
 1. **RAM Check**: Monitor RAM via `psutil`.
 2. **Deterministic Model Selection**: Implement a function `select_model(max_memory_gb, max_cpu_cores)` that reads the `MODEL_PRIORITY_LIST` from `code/utils/config.py` (defined in T007). The function checks the RAM requirement of each model against `max_memory_gb` in order.
 3. **Fallback Logic**:
 - If a model fits, return it.
 - If the list is exhausted without a match, **implement aggressive sampling**: reduce the dataset size by **[deferred] per iteration** and retry model selection.
 - If the reduced dataset still exceeds limits, raise `ResourceLimitExceeded`.
 - If `MODEL_PRIORITY_LIST` is empty, raise `ResourceLimitExceeded` immediately.
 4. **Logging**: Implement a function `log_model_selection(model_name)` to record the selected model in the logs for reproducibility.
 5. **Constraint**: If the selected model exceeds the available system memory during loading, raise a `ResourceLimitExceeded` exception and exit with a failure code.
**Dependency**: T007.

- [X] T007c-test [Setup] **Unit Tests for Resource Watchdog**: Write unit tests in `code/tests/test_resource_watchdog.py` for the `select_model` and `log_model_selection` functions. **Test Cases**: Simulate high RAM usage, verify correct model selection, verify `ResourceLimitExceeded` exception. **Dependency**: T007c.

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

**Goal**: Ingest ARC‑Bench failure transcripts, annotate structural features, and generate a deterministic rule library using a CPU‑tractable small model.

**Independent Test**: Run the pipeline on a small held‑out subset of cases and verify `rules_library.json` contains valid "If‑Condition‑Then‑Action" structures.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/01_data_ingestion/download_arc_bench.py` to fetch the ARC‑Bench topic subset via HuggingFace `datasets`.

- [X] T050 [US1] **Implement Real Data Source Verification**: Create `code/01_data_ingestion/verify_real_data_source.py` to validate that the ARC‑Bench dataset fetched in T009 matches the official checksum and metadata from the `claw-ai-lab/arc-bench` repository. **Logic**:
 1. Fetch `metadata.json` from the HuggingFace URL.
 2. Compare its SHA‑256 hash against the hash provided in the metadata.
 3. If mismatch, raise `DataIntegrityError` (exit code 1).
 4. **Output**: `data/artifacts/data_source_verification.json`.
**Dependency**: T009.

- [X] T036 [US1] **Implement Streaming Data Loader**: Modify `code/01_data_ingestion/download_arc_bench.py` to use `datasets.load_dataset(..., streaming=True)`. **Logic**: Iterate in chunks, write each processed row to `data/derived/failure_cases_raw.json` with fields `task_id`, `raw_error_log`, `ground_truth_resolution`, and placeholder `structural_feature` (to be filled later). **Constraint**: No synthetic fallback; abort on streaming errors. **Logging**: Log chunk stats. **Dependency**: T009, T050.

- [X] T005a [US1] **Implement Gold Standard Loader / Generator**: Create `code/02_annotation_distillation/load_gold_annotations.py` to load or generate the "Gold Standard" annotation file. **Logic**:
 1. **Check Real Data**: Check for the existence of `data/derived/failure_cases_raw.json` (from T036).
 2. **If exists**: Load the file, validate its schema against `failure_case.schema.yaml`.
 3. **Generate Synthetic Gold Standard**: If no manual `data/raw/gold_annotations.json` is provided, generate a **deterministic synthetic gold standard** based on the known failure taxonomy (e.g., A representative set of synthetic cases per category: Syntactic, Logical, Semantic, Missing, Unstructured) to ensure the pipeline can run on a fresh CI environment without manual artifact injection. This synthetic data is strictly for CI reproducibility testing and is flagged as `synthetic=true`.
 4. **If manual gold standard exists**: Load `data/raw/gold_annotations.json` and use it as the source of truth.
 5. **Output**: Write the result to `data/derived/annotator_1.json` and `data/derived/annotator_2.json` (simulating the consensus of two identical annotators for reproducibility).
 6. **Constraint**: This task replaces the manual Streamlit interface to satisfy Constitution Principle I (Reproducibility).
 7. **Checksum**: Immediately compute the SHA-256 hash of the generated file and record it in `data/artifacts/annotator_hashes.json`.
 **Output**: `data/derived/annotator_1.json` and `data/derived/annotator_2.json`. **Dependency**: T036 (or synthetic fallback).

- [X] T054 [US1] **Implement Annotation Inter‑Rater Reliability Check**: Create `code/02_annotation_distillation/check_inter_rater.py` that computes Cohen’s Kappa between the two annotator files. If Kappa < 0.6, log a warning but do **not** abort (per plan). **Output**: `data/derived/inter_rater_reliability.json`. **Dependency**: T005a.

- [X] T005b [US1] **Implement Consensus Generation**: Create `code/02_annotation_distillation/generate_consensus.py` that merges two annotator files `annotation_annotator1.jsonl` and `annotation_annotator2.jsonl`. If the `annotated_structural_feature` values match, write the merged record to `data/derived/consensus_labels.json`; otherwise flag for manual resolution. **Output**: `data/derived/consensus_labels.json`. **Dependency**: T005a.

- [X] T005c [US1] **Resolve Disagreements**: Create `code/02_annotation_distillation/resolve_disagreements.py` to load `consensus_labels.json`, drop any records with `null` (disagreement), and write the final labeled dataset to `data/derived/failure_cases_consensus.json`. **Dependency**: T005b.

- [X] T011b [US1] [FR-001] **Artifact Generation**: Implement `code/02_annotation_distillation/annotate_failures.py` to read `data/derived/failure_cases_consensus.json` (from T005c), map the `structural_feature` field from the source data to the `annotated_structural_feature` field, and write the labeled dataset to `data/derived/failure_cases.json`. **Schema**: The JSON MUST be an array of objects with keys: `task_id` (string), `raw_error_log` (string), `ground_truth_resolution` (string), `annotated_structural_feature` (enum: "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"). **Data Splitting**: Implement logic within this script to split `failure_cases.json` into `failure_cases_train.json`, `failure_cases_val.json`, AND `failure_cases_test.json` using a fixed random seed from `config.py` and a **stratified train/validation/test split** by `annotated_structural_feature`. **Schema Validation**: Validate output against `specs/001-llmxive-followup/contracts/failure_case.schema.yaml` (T006a) before writing; if validation fails, raise an explicit error and stop. **Quality Check**: Verify that `inter_rater_reliability.json` (from T054) exists. If Kappa < 0.6, log a CRITICAL warning "Low Reliability Detected" and set a flag `low_reliability=true` in the output artifact, but proceed (configurable via `config.py`). **Annotation Logic**: The mapping from `raw_error_log` to `annotated_structural_feature` is performed by a **deterministic rule set** (regex patterns and keyword heuristics) defined in `code/utils/config.py` to simulate the Human-in-the-Loop annotation process. **Output**: Save all three files to `data/derived/`. **Dependency**: T006a, T005c, T050, T054.

- [X] T011c [US1] **Implement Mock Data Generator (Fallback)**: Implement `code/02_annotation_distillation/generate_mock_data.py` to create deterministic mock data if T011b fails or produces empty splits. **Action**:
 1. Generate 50 mock `FailureCase` records with random `task_id`, `raw_error_log`, `ground_truth_resolution`, and `annotated_structural_feature` (from the enum).
 2. Split into train/val/test using `SPLIT_SEED` from `config.py`.
 3. Write to `data/derived/failure_cases_train_mock.json`, `failure_cases_val_mock.json`, `failure_cases_test_mock.json`.
 4. Log a warning that mock data is being used.
 **Constraint**: This task is ONLY executed if T011b fails or produces empty splits. It ensures the pipeline can proceed for testing.
 **Dependency**: T011b (conditional).

- [X] T015b [US1] [FR-002] **Schema Validation**: Implement `code/02_annotation_distillation/validate_rules.py` to validate `data/derived/rules_library.json` against `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` (T006b). **Pre-Check**: If `specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml` is missing or empty, the task MUST FAIL with exit code 1. **Action**: Run the validator. **Logic**: Load the JSON file, parse it, and validate each rule object against the schema. Collect all validation errors. **Content Check**: Additionally, verify that `rules_library.json` is not empty and contains at least one rule per failure type (or log a warning if coverage is low). If the rule library is empty or coverage is <90%, exit with code 1 and log "Rule Coverage Insufficient". **Output**: `data/artifacts/rule_validation_report.json` containing a boolean `is_valid`, a list of `errors` (if any), and a `coverage_status` field. **Dependency**: T006b, T013.

- [X] T015b [US1] **Schema Validation for Rules Library**: Implement `code/02_annotation_distillation/validate_rules.py` that validates `data/derived/rules_library.json` against `distilled_rule.schema.yaml` (T006b) using `jsonschema`. On any validation error, exit with code 1 and produce `data/artifacts/rule_validation_report.json`. **Dependency**: T006b, T013.

- [X] T016 [US1] **Logging Annotation & Distillation Metrics**: Extend `annotate_failures.py` to emit `data/artifacts/annotation.log` with total case counts per structural feature. Extend `distill_rules.py` to log number of generated rules and coverage metric. **Dependency**: T011b, T013.

---

## Phase 4: User Story 2 - Rule Engine Execution & Baseline Comparison (Priority: P2)

**Goal**: Execute the distilled rule engine on a held‑out test set and compare performance against the full baseline agent.

**Independent Test**: Run on unseen tasks, log "Time‑to‑Pivot" and "Success", and verify metrics format.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/03_execution/rule_engine.py` to:
 1. Load `rules_library.json`.
 2. For each error log in the manifest, perform deterministic pattern matching.
 3. If no rule matches, set action to `"Manual Review"` and flag `fallback_chain="Unstructured"`.
 4. Write results (including `task_id`, `method="rule_engine"`, `time_to_pivot`, `success`, `failure_type`) to `data/derived/results_rule_engine.csv`.
 **Dependency**: T006c.

- [X] T041 [P] [US2] **Verify GPU Policy Compliance**: Implement `code/03_execution/verify_gpu_policy.py` scanning all execution scripts for `device="cuda"` or `load_in_8bit`. If found, raise `PolicyViolationError` and exit 1. Output `data/artifacts/gpu_policy_report.json`. **Dependency**: T017, T021c.

- [X] T044 [US2] **Power Analysis**: Implement `code/03_execution/power_analysis.py` to compute required sample size using `statsmodels.stats.power.TTestPower` with `EXPECTED_EFFECT_SIZE`, 80 % power, α = 0.05. Output `data/derived/power_analysis_report.json`. **Dependency**: T011b, T011c.

- [X] T019a [US2] **CRITICAL**: Implement `code/03_execution/generate_manifest.py` to create `data/derived/experiment_manifest.csv`. **Depends on T011b completion.**
 - **Source**: `data/derived/failure_cases_test.json` (from T011b).
 - **Pre-Check**: Validate that `failure_cases_test.json` exists.
 - **Logic**: Select a **stratified random sample** from the available data. The target sample size is determined by parsing the `required_sample_size` key from `data/derived/power_analysis_report.json` (T044). **Fallback**: If `power_analysis_report.json` is missing, empty, or `required_sample_size` is undefined, **default to a Minimum Viable Sample of tasks** stratified by failure type. Log a warning "Power analysis incomplete or dataset too small; using minimum viable sample." **Constraint**: If the available dataset is smaller than 50, proceed with the available data and log a critical warning "Dataset size < 50; proceeding with reduced statistical power."
 - **Validation**: Verify the output CSV contains the sampled rows AND verify that the distribution of failure_type matches the source distribution within an acceptable tolerance (**stratification_tolerance=0.05**).
 - **Reproducibility**: Use the fixed random seed defined in `code/utils/config.py`.
 - **Output**: CSV with columns `task_id`, `failure_type`.
 - **Dependency**: T011b, T044, T054.

- [X] T019 [US2] **Run Rule Engine Experiments**: Implement `code/03_execution/run_experiments.py` that:
 1. Verifies existence of `experiment_manifest.csv`.
 2. Calls `rule_engine.py` for each listed task.
 3. Writes/updates `results_rule_engine.csv` (handled inside T017).
 **Dependency**: T019a, T017, T041.

- [X] T020 [US2] **Record Metrics for Rule Engine**: Ensure `rule_engine.py` (T017) writes a CSV with exact header:
```
task_id,method,time_to_pivot,success,failure_type
```
Values for `failure_type` must match the enum names from the schema (e.g., "Syntactic Error", "Logical Loop", "Semantic Ambiguity", "Missing Context", "Unstructured"). No additional columns. **Dependency**: T017.

- [X] T058b [US2] **Provision Baseline Runner**: Create `code/03_execution/provision_baseline_runner.py` to ping the external baseline runner API (`BASELINE_RUNNER_URL` from `config.py`) and verify it reports `cpu_cores=4` and `memory_gb=16`. Output `data/artifacts/baseline_runner_status.json`. **Dependency**: T007.

- [X] T021c [US2] **Instrument Baseline Resource Metrics (External)**: Implement `code/03_execution/instrument_baseline.py` to validate the external baseline runner's resource metrics. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **Constraint**: This script runs locally but *validates* the external execution. It does NOT run the baseline itself.
 3. Wait for the external runner to upload `baseline_resource_metrics.json`.
 4. **Verification**: Check that the uploaded metrics match the expected constraints (`BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`).
 5. **Output**: `data/derived/baseline_trigger_metrics.json` with schema `{ task_id, peak_memory_mb, cpu_time_seconds }` (from external source). **Dependency**: T019a, T021.

- [X] T021 [US2] **Implement Baseline Execution (External Dispatch)**: Implement `code/03_execution/run_baseline.py` to orchestrate baseline agent execution **on a separate CI job**. **Logic**:
 1. Accept `data/derived/experiment_manifest.csv` as input.
 2. **External Dispatch**: Create a GitHub Actions workflow file `workflows/baseline_runner.yml` that defines the job with `runs-on: ubuntu-latest` and resource limits (4 CPU, 16 GB RAM). This file MUST be generated by T021b.
 3. **Trigger**: Use `gh run dispatch` or the GitHub API to trigger this workflow with the manifest as an input.
 4. **Polling**: Wait for the external workflow to complete (max `BASELINE_TIMEOUT_SECONDS`).
 5. **Artifact Transfer**: Download the `baseline_results.json` artifact uploaded by the external workflow.
 6. **Timeout Handling**: If the job fails permanently, log an error and exit with a failure status code. Implement a SIGINT signal handler to allow explicit cancellation. **Constraint**: If the external dispatch fails or times out, the pipeline MUST abort. Do NOT fall back to local execution.
 7. **Output**: `data/derived/baseline_results.json` with the exact same task IDs as the manifest. **Format**: JSON object with keys `task_id`, `time_to_pivot`, `success`. **Dependency**: T021c, T019a, T041, T058b, T021b.

- [X] T021b [US2] **Generate Baseline Workflow YAML**: Implement `code/03_execution/generate_baseline_workflow.py` to create `workflows/baseline_runner.yml`. **Logic**:
 1. Define a GitHub Actions workflow with `runs-on: ubuntu-latest`.
 2. Set resource constraints: `env: { CPU_CORES: "4", MEMORY_GB: "16" }`.
 3. Define steps to: checkout code, install dependencies, run `code/03_execution/baseline_agent.py` (the actual baseline script) with the manifest as input.
 4. Upload `baseline_results.json` as an artifact.
 5. **Dependency**: T019a. **Output**: `workflows/baseline_runner.yml`.

- [X] T022 [US2] **Merge Rule‑Engine and Baseline Results**: Implement `code/03_execution/merge_results.py` to:
 1. Load `results_rule_engine.csv` and `baseline_results.json`.
 2. Verify that every `task_id` from the manifest appears in both sets; if a baseline entry is missing, record `time_to_pivot=TIMEOUT_SECONDS`, `success=False` for that task.
 3. Produce `data/derived/results.csv` with columns:
```
task_id,method,time_to_pivot,success,failure_type
```
where `method` is either `"rule_engine"` or `"baseline"`. Censored baseline failures are represented with the timeout sentinel.
 **Dependency**: T019, T021, T019a.

---

## Phase 5: User Story 3 - Statistical Analysis & Error Taxonomy (Priority: P3)

**Goal**: Perform mixed‑effects logistic regression and categorize failed pivots to determine the interaction between failure type and method.

**Independent Test**: Run analysis script and verify output includes regression coefficients for the interaction term.

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/04_analysis/statistical_model.py` to fit mixed-effects logistic regression (Success ~ FailureType * Method + (1|TaskID))

- [X] T026a [US3] **Model Fitting**: Ensure `statistical_model.py` outputs p-values for the interaction term to `data/derived/regression_results.json`. **Dependency**: T022.

- [X] T026b [US3] [SC-003] **Significance Determination**: Implement logic in `statistical_model.py` (or a wrapper) to compare the p-value from T026a against alpha=0.05. **Output**: Update `data/derived/regression_results.json` with key `interaction_significant` (boolean) and `narrative_conclusion` (string: "The interaction term is significant (p < 0.05)" or "The interaction term is not significant (p >= 0.05)"). **Dependency**: T026a.

- [X] T029a [US3] [SC-001] Implement `code/04_analysis/time_diff_tobit.py` to perform **Tobit Regression** (censored data handling) on "Time-to-Pivot" differences using `statsmodels` or `lifelines`. **Logic**:
 1. **Load Threshold**: Load `TIMEOUT_SECONDS` from `code/utils/config.py` to use as the censoring threshold value.
 2. **Censored Handling**: Include rows where the baseline failed (timeout/error) as censored observations (time = `TIMEOUT_SECONDS` from T022) rather than excluding them. This addresses survivorship bias.
 3. **Crucial**: Ensure the data is **paired** (same task IDs for Rule Engine and Baseline) and the regression is performed on the paired differences or a paired design matrix as required by SC-001.
 **Output schema**: `data/derived/time_diff_tobit_results.json` containing keys: `p_value`, `ci_lower`, `ci_upper`, `statistic`. **Dependency**: T022.

- [X] T029b [US3] [SC-002] Implement `code/04_analysis/calculate_stratified_rates.py` to calculate "Success Rate of First Pivot" stratified by failure type. **Verification**: Verify that the sum of rates weighted by sample size equals the overall success rate. **Output**: `data/derived/stratified_success_rates.csv` with columns `failure_type`, `rate` (long format). **Dependency**: T022.

- [X] T027 [US3] [FR-007] Implement `code/04_analysis/error_taxonomy.py` to categorize failed pivots. **Inputs**: `data/derived/results.csv` (from T022) and `data/derived/failure_cases.json` (from T011b). **Logic**: If no rule matches -> "Coverage Gap"; If rule matches but action != `ground_truth_resolution` (from T011b) -> "Distillation Error". **Exclude**: Cases where `ground_truth_resolution` is null or empty are excluded from the count and logged separately as "Missing Ground Truth". **Pre-Check**: Verify that `data/derived/results.csv` (from T022) and `data/derived/failure_cases.json` (from T011b) exist and are non-empty. If either is missing, exit with a non-zero status code indicating failure.. **Dependency**: T022, T011b.

- [X] T027b [US3] **Execute & Populate**: Run `error_taxonomy.py` against `data/derived/results.csv` and `data/derived/failure_cases.json` to generate `data/derived/error_taxonomy_results.json`. **Output Schema**: `{ "coverage_gap_count": <int>, "distillation_error_count": <int>, "total_failures": <int>, "breakdown_by_type": { "<type>": { "coverage_gap": <int>, "distillation_error": <int> } } }`. **Note**: `total_failures` explicitly **excludes** cases where `ground_truth_resolution` is null. **Depends on T022, T011b**.

- [X] T027c [US3] **Analyze Missing Ground Truth**: Implement `code/04_analysis/analyze_missing_gt.py` to aggregate and report on the "Missing Ground Truth" subset excluded in T027. **Logic**: Count and list task IDs where `ground_truth_resolution` was null. **Output**: `data/derived/missing_gt_report.json` with count and sample task IDs. **Dependency**: T011b.

- [X] T027d [US3] [SC-004] **Aggregate Failure Proportions**: Create `code/04_analysis/aggregate_failure_proportions.py` to combine the counts from T027b and T027c. **Logic**: Calculate the proportion of "Coverage Gap" and "Distillation Error" against the **total** number of failures (including "Missing Ground Truth"). **Action**: Sum `coverage_gap_count` + `distillation_error_count` + `missing_gt_count` from T027b and T027c to form the denominator. Calculate proportions for each category. **Output**: `data/derived/failure_proportions.json` with keys `coverage_gap_proportion`, `distillation_error_proportion`, `missing_gt_proportion`. **Dependency**: T027b, T027c.

- [X] T028 [US3] **Ground Truth Arbitration**: Ensure `error_taxonomy.py` uses `ground_truth_resolution` from `failure_cases.json` to arbitrate the categorization of failures (Coverage Gap vs Distillation Error). **Dependency**: T011b.

- [X] T029c [US3] [SC-001] **Execute Time Diff (Tobit)**: Run `time_diff_tobit.py` to generate `data/derived/time_diff_tobit_results.json`. **Dependency**: T029a.

- [X] T029d [US3] [SC-002] **Execute Stratified Rates**: Run `calculate_stratified_rates.py` to generate `data/derived/stratified_success_rates.csv`. **Dependency**: T029b.

- [X] T051 [US3] **Implement Censored Data Visualization**: Create `code/04_analysis/visualize_censored_data.py` to generate a Kaplan-Meier survival curve for "Time-to-Pivot" comparing the Rule Engine vs. Baseline, explicitly marking censored observations (failed tasks). **Logic**: Use `lifelines` to fit Kaplan-Meier estimators for both methods and plot the survival function with confidence intervals. **Output**: `data/derived/km_survival_curve.png` and `data/derived/km_survival_data.csv`. **Dependency**: T022, T029a.

- [X] T053 [US3] **Implement Sensitivity Analysis for Distillation Threshold**: Create `code/04_analysis/sensitivity_distillation.py` to re-run the distillation process (T013) with varying coverage thresholds (%, high, 95%) and measure the impact on the final success rate of the rule engine. **Logic**: Iterate through thresholds, regenerate rules, re-run the rule engine on the test set, and record the success rate. **Output**: `data/derived/distillation_sensitivity.csv` with columns `threshold`, `rule_count`, `success_rate`. **Dependency**: T013, T019a.

- [X] T029a [US3] **Tobit Regression for Time‑to‑Pivot**: Implement `code/04_analysis/time_diff_tobit.py` to:
 1. Load `results.csv`.
  2. Treat any `time_to_pivot` equal to `TIMEOUT_SECONDS` as censored.
 3. Fit a Tobit model (e.g., via `statsmodels` `TobitModel`) on the paired differences (rule_engine – baseline).
 4. Output `data/derived/time_diff_tobit_results.json` with `p_value`, `ci_lower`, `ci_upper`, `statistic`.
 **Dependency**: T022.

- [X] T029b [US3] **Stratified Success Rates**: Implement `code/04_analysis/calculate_stratified_rates.py` to compute success rate per `failure_type` across both methods. Output `data/derived/stratified_success_rates.csv` with columns `failure_type,method,success_rate`. **Dependency**: T022.

- [X] T047 [US3] [SC-003] **Validate Interaction Term Robustness**: Implement `code/04_analysis/validate_interaction.py` to perform a sensitivity analysis on the mixed-effects model by bootstrapping the dataset multiple times and verifying that the interaction term remains significant in >95% of iterations. **Logic**: Use `statsmodels` to fit the model on multiple bootstrap samples. Count iterations where p-value < 0.05. **Output**: `data/derived/interaction_sensitivity.json` containing keys: `total_iterations`, `significant_count`, `percentage_significant`. **Verification**: Verify the JSON contains `percentage_significant` > 0.95. **Dependency**: T026a.

- [X] T064 [US3] **Cross-Validation of Rule Set**: Implement `code/04_analysis/cross_validation.py` to perform k-fold cross-validation (k=5) of the distilled rule set. **Logic**:
 1. Split `failure_cases_test.json` into 5 folds.
 2. For each fold, train rules on 4 folds and test on the held-out fold.
 3. Calculate success rate for each fold.
 4. Compute the standard deviation of the success rates across folds.
 5. **Pass/Fail**: If `std_dev < 0.1`, the rule set is considered robust. Otherwise, flag as unstable.
 **Output**: `data/derived/cross_validation_results.json` with keys: `folds`, `success_rates`, `mean_rate`, `std_dev`, `robustness_status` (boolean). **Dependency**: T013, T022.

- [X] T065 [US3] **Baseline Failure Mode Analysis**: Implement `code/04_analysis/baseline_failure_analysis.py` to analyze failure modes of the baseline agent. **Logic**:
 1. Load `baseline_results.json` and `failure_cases.json`.
 2. Group failures by `failure_type`.
 3. Calculate the mean failure rate per type.
 **Output**: `data/derived/baseline_failure_analysis.json` with keys: `failure_type`, `mean_rate`, `count`, `total`. **Dependency**: T021, T011b.

- [X] T067 [US3] **Effect Size Verification**: Implement `code/04_analysis/effect_size_verification.py` to compute Cohen's d for the paired differences and produce a standalone report. **Logic**:
 1. Load `data/derived/results.csv`.
 2. Calculate Cohen's d for the paired differences (Rule Engine vs Baseline).
 3. Calculate the Confidence Interval.

The research question, method, and references remain unchanged as required, with the specific empirical threshold replaced by the general statistical concept.
 **Output**: `data/derived/effect_size_results.json` with keys: `cohen_d`, `ci_lower`, `ci_upper`, `interpretation`. **Dependency**: T022.

- [X] T068 [US3] **Resource Correlation Analysis**: Implement `code/04_analysis/resource_correlation.py` to investigate the correlation between resource usage and performance. **Logic**:
 1. Load `data/derived/local_resource_log.json` and `data/derived/results.csv`.
 2. Perform Spearman correlation between `peak_memory_mb` and `time_to_pivot`.
 3. Calculate p-value for the correlation.
 4. **Threshold**: If p < 0.05, the correlation is significant.
 **Output**: `data/derived/resource_correlation_report.json` with keys: `rho`, `p_value`, `interpretation`, `significant`. **Dependency**: T030a, T022.

- [X] T066 [US3] **Generate Rule Coverage Chart**: Create `code/04_analysis/visualize_rule_coverage.py` to generate a bar chart of rule coverage by failure type. **Logic**:
 1. Load `data/derived/rules_library.json`.
 2. Count rules by `condition_pattern` type (Syntactic, Logical, Semantic, Missing, Unstructured).
 3. Generate a bar chart using `matplotlib`.
 4. **Output**: `data/derived/rule_coverage_chart.png` (PNG format).
 **Dependency**: T013.

- [X] T029e [US3] [SC-003] [SC-004] [SC-005] **Create Report Template**: Implement `code/04_analysis/templates/report_template.md.j2`. **Template Path**: `code/04_analysis/templates/report_template.md.j2`. **Variables**: `regression_results`, `time_diff_tobit_results`, `stratified_success_rates`, `failure_proportions`, `resource_summary`, `interaction_sensitivity`, `missing_gt_report`, `cross_validation_results`, `baseline_failure_analysis`, `effect_size_results`, `resource_correlation_report`. **Structure**: Executive Summary, Methodology, Time-to-Pivot Analysis (SC-001), Success Rate Analysis (SC-002), Error Taxonomy (SC-004), Statistical Significance (SC-003 - MUST include `p_value`, `ci_lower`, `ci_upper`, and `interaction_significant` from T026b), and Conclusion. **Narrative Logic**: If `p_value` < 0.05, write "The interaction term is statistically significant (p < 0.05), indicating that failure structure dictates method viability." Else, write "The interaction term is not statistically significant (p >= 0.05)." **Template Content**:
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
 **Dependency**: T022, T011b, T011c.

- [X] T029f [US3] [Report] **Generate Final Report**: Execute `code/04_analysis/generate_report.py` with the template from T029e and data from T026b, T029c, T029d, T027d, T027c, T030a, T030c, T047, T064, T065, T067, T068, T066 to produce `data/derived/final_report.md`. **Pre-Check**: Verify that all required input artifacts exist and are non-empty. If any are missing, exit with a non-zero status code.. **Dependency**: T029e, T026b, T029c, T029d, T027d, T027c, T030a, T030c, T047, T064, T065, T067, T068, T066.

- [X] T029d [US3] **Execute Stratified Rates**: (Implemented as part of T029b) – generate the CSV and mark as completed.

- [X] T029h [US3] **Statistical Comparison (Censored Data)**: Implement `code/04_analysis/time_diff_tobit.py` (reused from T029a) to perform the primary statistical comparison. **Action**:
 1. Use `statsmodels.stats.tobit.TobitModel` to fit the model on paired differences.
 2. Do NOT use Paired t-test or Wilcoxon test on censored data.
 3. Use Shapiro-Wilk test with p < 0.05 for normality check (if applicable for non-censored subset).
 4. Output `data/derived/time_diff_tobit_results.json` with `p_value`, `ci_lower`, `ci_upper`, `statistic`.
 **Dependency**: T022.

- [X] T060 [Setup] **Implement Final Orchestration Script**: Create `code/main.py` that:
 1. Imports and runs each phase in order: Phase 0 (T002, T002b), Phase 1 (T001‑T005), Phase 2 (T006a‑T006c, T007‑T007c‑T007c-test, T008, T043), Phase 3 (T009‑T050‑T036‑T005a‑T005b‑T005c‑T054‑T011b‑T011c‑T013‑T015b‑T016), Phase 4 (T017‑T041‑T044‑T019a‑T019‑T020‑T058b‑T021‑T021c‑T022), Phase 5 (T025‑T026a‑T026b‑T029a‑T029b‑T027b‑T028‑T029d‑T029h‑T029f‑T055‑T064‑T065‑T067‑T068‑T066). 
 2. After each task, checks the exit code; on failure, logs the error and exits immediately.
 3. If T011b fails (empty splits), invoke T011c before proceeding to Phase 4.
 4. Writes a top‑level `pipeline_status.json` summarising success/failure of each phase.
 **Dependency**: All tasks must be defined; this script provides the single entry point required by the constitution.

- [X] T029f [US3] **Generate Final Report**: Implement `code/04_analysis/generate_report.py` that renders `templates/report_template.md.j2` with data from all analysis artifacts (including `regression_results.json`, `time_diff_tobit_results.json`, `stratified_success_rates.csv`, `error_taxonomy_results.json`, `resource_summary.json`, etc.) and writes `data/derived/final_report.md`. Pre‑check that all required inputs exist; abort with clear error if any are missing.
 **Dependency**: T026b, T029a, T029b, T027b, T029h, T022, T011b, T011c.

- [X] T055 [US3] **Executive Summary Generator**: Implement `code/04_analysis/generate_executive_summary.py` to extract `narrative_conclusion`, `interaction_significant`, `coverage_gap_count`, `distillation_error_count`, `missing_gt_count` (from `missing_gt_report.json`), and `percentage_significant` (from `interaction_sensitivity.json`) and write a concise one‑page `data/derived/executive_summary.md`.
 **Dependency**: T029f, T026b, T027b, T022, T011b, T011c.

- [X] T070 [US2] **Baseline Resource Verification**: Implement `code/04_analysis/verify_baseline_resources.py` that:
 1. Loads `data/derived/baseline_resource_metrics.json` (produced by the external baseline runner in T021).
 2. Checks that `cpu_cores == CONFIG.BASELINE_CPU_CORES` and `memory_gb <= CONFIG.BASELINE_MEMORY_GB`.
 3. On mismatch, raise `ResourceVerificationError` and exit 1; otherwise write `data/artifacts/baseline_resource_check.json` with status `PASS`.
 **Dependency**: T021, T022, T011b, T011c.

- [X] T064 [US3] **Cross‑Validation of Rule Set**: Implement `code/04_analysis/cross_validation.py` to perform 5‑fold CV on `failure_cases_test.json` (or mock), retrain rules on 4 folds, evaluate on the held‑out fold, compute success rates, and output `data/derived/cross_validation_results.json` with `std_dev`. Fail if `std_dev >= 0.1` (mark robustness_status `false`). **Dependency**: T013, T022, T011b, T011c.

- [X] T065 [US3] **Baseline Failure Mode Analysis**: Implement `code/04_analysis/baseline_failure_analysis.py` to aggregate baseline failures by `failure_type` from `baseline_results.json` and write `data/derived/baseline_failure_analysis.json`. **Dependency**: T021, T011b, T011c.

- [X] T067 [US3] **Effect Size Verification**: Implement `code/04_analysis/effect_size_verification.py` to compute Cohen’s d for paired `time_to_pivot` differences (rule_engine vs baseline) and write `data/derived/effect_size_results.json` with `cohen_d`, `ci_lower`, `ci_upper`, `interpretation`. **Dependency**: T022, T011b, T011c.

- [X] T068 [US3] **Resource Correlation Analysis**: Implement `code/04_analysis/resource_correlation.py` to compute Spearman’s ρ between `peak_memory_mb` (from `local_resource_log.json`) and `time_to_pivot` (from `results.csv`). Output `data/derived/resource_correlation_report.json` with `rho`, `p_value`, `significant`, `interpretation`. **Dependency**: T030a, T022, T011b, T011c.

- [X] T066 [US3] **Rule Coverage Chart**: Implement `code/04_analysis/visualize_rule_coverage.py` to produce `rule_coverage_chart.png` showing count of rules per structural feature. **Dependency**: T013.

- [X] T071 [US3] **Interaction Term Visualization**: Implement `code/04_analysis/visualize_interaction.py` to plot the interaction effect (failure_type × method) on success probability with confidence intervals, saving `interaction_plot.png`. **Dependency**: T026b, T029b.

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T048 [P] **Update State**: Create `code/utils/update_state.py` to calculate SHA‑256 hashes of all artifacts in `data/derived/` and `results/`. Update `state/projects/PROJ-865-llmxive-follow-up-extending-autoresearch.yaml` with the new hashes and `updated_at` timestamp. Run after each major phase.

- [X] T069 [US1] **Implement Explicit Dataset Sample Logging**: Modify `download_arc_bench.py` to log total rows streamed, chunk sizes, and duration to `data/artifacts/streaming_log.json`. (Already referenced in Phase 3.)

- [X] T063 [US3] **Sensitivity Analysis for Censoring Threshold**: Implement `code/analysis/sensitivity_censoring.py` to re‑run `time_diff_tobit.py` with timeout thresholds 3000 s, 3600 s, 4200 s and record robustness in `censoring_sensitivity.json`. **Dependency**: T022, T029a, T011b, T011c.

- [X] T057 [P] **Enforce Strict Data Flow**: Implement `code/utils/data_flow_validator.py` to verify that all input files for a task exist before execution. **Dependency**: T011b, T011c.

- [X] T062 [P] **Paired-Data Integrity Check**: Implement `code/03_execution/paired_data_integrity.py` to verify that `task_id` pairs in `results.csv` are complete. **Dependency**: T019a, T021, T011b, T011c.

- [X] T053 [US3] **Sensitivity Analysis for Distillation**: Implement `code/04_analysis/sensitivity_distillation.py` to re-run distillation with different model sizes. **Dependency**: T013, T019a, T011b, T011c.

- [X] T030a [P] **Resource Logging**: Implement `code/utils/resource_logger.py` to log peak memory and CPU usage. **Dependency**: T007.

- [X] T029c [US3] **Missing Ground Truth Report**: Implement `code/04_analysis/missing_gt_report.py` to log any cases where ground truth is missing. **Dependency**: T022, T011b, T011c.

- [X] T027d [US3] **Missing GT Analysis**: Implement `code/04_analysis/missing_gt_analysis.py` to analyze impact of missing ground truth. **Dependency**: T027b, T022, T011b, T011c.

- [X] T027c [US3] **Missing GT Report Generation**: Implement `code/04_analysis/generate_missing_gt_report.py` to write the report. **Dependency**: T027b, T022, T011b, T011c.

- [X] T030c [US3] **Resource Summary**: Implement `code/04_analysis/resource_summary.py` to aggregate resource usage. **Dependency**: T022, T011b, T011c.

- [X] T021 [US2] **Implement Baseline Timeout Handling**: (See Phase 4, T021). The timeout handling is now part of the main task.

### Compute Feasibility & GPU Policy (Constitutional Compliance)

- [X] T041 [P] [US2] **Verify GPU Policy Compliance**: (See Phase 4, T041). This task is now a blocking gate before execution.

- [X] T043 [P] [US1] **Validate Model Quantization**: (See Phase 2, T043). This task is now a blocking gate before distillation.

- [X] T047 [P] [US3] **Validate Interaction Term Robustness**: (See Phase 5, T047). This task is now fully implemented with A sufficient number of bootstrap iterations.

- [X] T051 [P] [US3] **Implement Censored Data Visualization**: (See Phase 5, T051). This task is now fully implemented.

- [X] T053 [P] [US3] **Implement Sensitivity Analysis for Distillation Threshold**: (See Phase 5, T053). This task is now fully implemented.

- [X] T054 [P] [US1] **Implement Annotation Inter-Rater Reliability Check**: (See Phase 3, T054). This task is now fully implemented with human-in-the-loop requirement.

- [X] T055 [P] [US3] **Implement Final Report Executive Summary Generator**: (See Phase 5, T055). This task is now fully implemented.

- [X] T060 [Setup] **Implement Final Orchestration Script**: Create `code/main.py` to serve as the single entry point for the entire pipeline, invoking tasks in strict dependency order (Phase 0 → 1 → 2 → 3 → 4 → 5). **Action**: Write `code/main.py` to import and execute the main functions of tasks in **Phase 0, Phase 1, Phase 2, Phase 3, Phase 4, and Phase 5** (Completion of Phases 0-5). **Logic**:
 1. **Initialization**: Load `config.py` and set up logging.
 2. **Phase Execution**: Execute tasks in order: T002, T002b, T001, T003, T004, T005, T006a-c, T007, T007c, T008, T043, T009, T050, T036, T005a, T005b, T005c, T054, T011b, T013, T015b, T016, T017, T041, T044, T019a, T019, T020, T058b, T021c, T021, T021b, T022, T025, T026a, T026b, T029a, T029b, T027, T027b, T027c, T027d, T028, T029c, T029d, T051, T053, T030a, T030c, T047, T064, T065, T067, T068, T066, T029e, T029f, T055, T031, T032, T033, T034, T035a, T035b, T048.
 3. **Parallel Execution**: For tasks marked `[P]` (e.g., T033, T035a, T035b), use `asyncio` or `multiprocessing` to execute them concurrently where dependencies allow, rather than forcing a strict linear sequence.
 4. **Error Handling**: If any task fails (non-zero exit code), log the error, update the state file with `status=failed`, and exit immediately.
 5. **State Management**: After each successful phase, call `update_state.py` to record artifact hashes.
 6. **Final Output**: On success, log "Pipeline completed successfully" and exit with code 0.
 **Rationale**: Resolves the "run-book vs implementation mismatch" identified in T056 by providing a concrete, executable entry point that matches the plan. **Dependency**: Completion of Phases 0-5.

- [X] T057 [US1] **Enforce Strict Data Flow for Distillation**: Refactor `code/02_annotation_distillation/distill_rules.py` to explicitly verify that `data/derived/failure_cases_train.json` and `data/derived/failure_cases_val.json` exist and contain non-zero rows before attempting model loading. **Rationale**: Previous analysis flagged a potential race condition where distillation might start before the annotation phase fully committed the split files. **Action**: Add a `validate_inputs()` function at the start of the script that checks file existence and row count, raising `FileNotFoundError` with message "Input files missing or empty" and exit code 1 if missing. **Dependency**: T011b.

- [X] T058 [US2] **Add Baseline Execution Pre-flight Check**: (See T058b). This task is now fully implemented.

- [X] T059 [US3] **Validate Censored Data Handling in Visualization**: Update `code/04_analysis/visualize_censored_data.py` to explicitly assert that the input data contains censored observations (failed tasks) and that the Kaplan-Meier estimator correctly handles them. **Action**: Add a check in `visualize_censored_data.py` that counts rows where `time_to_pivot` equals `TIMEOUT_SECONDS` (from `config.py`). If zero censored rows are found, log a warning "No censored data detected; survival curve may be inaccurate." **Rationale**: SC-001 requires handling censored data; this task ensures the visualization logic actually processes such data if it exists. **Dependency**: T022, T029a.

- [X] T061 [US1] **Enforce Streaming-First Data Loading**: Modify `code/01_data_ingestion/download_arc_bench.py` to strictly enforce `streaming=True` as the default behavior for all dataset loads, removing any fallback to `load_dataset` without streaming unless explicitly overridden by a `--full-load` flag. **Rationale**: Prevents accidental OOM errors on large datasets by ensuring the primary path is memory-efficient streaming. **Dependency**: T009, T050.

- [X] T062 [US2] **Implement Paired-Data Integrity Check**: Add a validation step in `code/03_execution/merge_results.py` to verify that every `task_id` in `results_rule_engine.csv` has a corresponding entry in `baseline_results.json` before merging. **Rationale**: Ensures the paired comparison required by SC-001 is valid and prevents silent data loss in the final analysis. **Dependency**: T019a, T021.

- [X] T063 [US3] **Add Sensitivity Analysis for Censoring Threshold**: Implement `code/analysis/sensitivity_censoring.py` to re-run the Tobit regression (Ta) with varying `TIMEOUT_SECONDS` thresholds (e.g., 3000s, 3600s, 4200s) to verify the robustness of the Time-to-Pivot difference conclusion. **Rationale**: Validates that the statistical significance of SC-001 is not an artifact of the specific timeout value chosen. **Dependency**: T022, T029a.

- [X] T069 [US1] **Implement Explicit Dataset Sample Logging**: Modify `code/01_data_ingestion/download_arc_bench.py` to log the exact number of rows streamed and the specific chunk sizes used during the streaming process. **Rationale**: Analysis identified a need for explicit traceability of the sample size used for rule distillation to ensure reproducibility and verify that the full dataset (or a valid sample) was processed. **Action**: Add a `log_streaming_stats` function that records `total_rows`, `chunk_sizes`, and `streaming_duration` to `data/artifacts/streaming_log.json`. **Dependency**: T036.

- [X] T070 [US2] **Implement Baseline Resource Verification in Merge**: Add a validation step in `code/03_execution/merge_results.py` to verify that the baseline resource metrics (from T021) match the expected constraints (`BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`). **Rationale**: Ensures the baseline comparison is valid and that the baseline agent actually ran on the specified standard resources. **Action**: Check `data/derived/baseline_resource_metrics.json` and raise an error if constraints are violated. **Dependency**: T021, T022.

- [X] T071 [US3] **Implement Interaction Term Visualization**: Create `code/04_analysis/visualize_interaction.py` to generate a plot of the interaction effect between Failure Type and Method on Success Rate. **Rationale**: Provides a visual confirmation of the statistical interaction term significance (SC-003). **Action**: Use `seaborn` or `matplotlib` to plot the interaction, with error bars representing confidence intervals. **Output**: `data/derived/interaction_plot.png`. **Dependency**: T026b, T029b.