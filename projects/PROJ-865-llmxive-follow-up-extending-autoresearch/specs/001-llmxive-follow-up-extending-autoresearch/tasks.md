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

- [X] T007 [Setup] Implement `code/utils/config.py` with environment variables, random seeds, and explicit resource limits: `MAX_CPU_CORES=2`, `MAX_MEMORY_GB=7`, `TIMEOUT_SECONDS=3600`, `BASELINE_TIMEOUT_SECONDS=7200`, `BASELINE_CPU_CORES=4`, `BASELINE_MEMORY_GB=16`, `MAX_STREAMING_ROWS=500`, `EXPECTED_EFFECT_SIZE=0.5`, `DEFAULT_SAMPLE_SIZE=50`, `MODEL_PRIORITY_LIST=["Llama-8B-INT4", "Llama-3-4B-INT4", "TinyLlama-1.1B-INT4"]`, `SPLIT_SEED=12345`. **Constraint**: `MODEL_PRIORITY_LIST` must contain at least one model.

- [X] T007c [Setup] **Implement Resource Watchdog Library**: Implement `code/utils/resource_watchdog.py` as a **Python library module** (not just a CLI wrapper) containing the fallback logic. **Logic**:
 1. **RAM Check**: Monitor RAM via `psutil`.
 2. **Deterministic Model Selection**: Implement a function `select_model(max_memory_gb, max_cpu_cores)` that reads the `MODEL_PRIORITY_LIST` from `code/utils/config.py`. The function checks the RAM requirement of each model against `max_memory_gb` in order.
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

- [X] T005a [US1] **Implement Deterministic Annotation Interface**: Create `code/02_annotation_distillation/annotation_interface.py` that reads `data/derived/failure_cases_raw.json` and writes each entry to `data/derived/annotation_input.jsonl`. Annotators will manually edit this JSONL file (outside CI) to add the `annotated_structural_feature` field (must be one of the enum values). The script records a SHA‑256 hash of the completed file to `data/artifacts/annotation_input_hash.json`. **Action**:
 1. Write the `annotation_input.jsonl` file.
 2. **Manual Step**: A human must edit `data/derived/annotation_input.jsonl` to add the `annotated_structural_feature` field for each row.
 3. **Validation**: Run `code/02_annotation_distillation/validate_annotation_input.py` which checks that every row has a valid `annotated_structural_feature` from the enum. If validation fails, the task exits with code 1.
 **Constraint**: This is the ONLY supported path. No Streamlit app. The CI runner executes the validation script to ensure the file is ready.
 **Dependency**: T036.

- [X] T054 [US1] **Implement Annotation Inter‑Rater Reliability Check**: Create `code/02_annotation_distillation/check_inter_rater.py` that computes Cohen’s Kappa between the two annotator files. If Kappa < 0.6, log a warning but do **not** abort (per plan). **Output**: `data/derived/inter_rater_reliability.json`. **Dependency**: T005a.

- [X] T005b [US1] **Implement Consensus Generation**: Create `code/02_annotation_distillation/generate_consensus.py` that merges two annotator files `annotation_annotator1.jsonl` and `annotation_annotator2.jsonl`. If the `annotated_structural_feature` values match, write the merged record to `data/derived/consensus_labels.json`; otherwise flag for manual resolution. **Output**: `data/derived/consensus_labels.json`. **Dependency**: T005a.

- [X] T005c [US1] **Resolve Disagreements**: Create `code/02_annotation_distillation/resolve_disagreements.py` to load `consensus_labels.json`, drop any records with `null` (disagreement), and write the final labeled dataset to `data/derived/failure_cases_consensus.json`. **Dependency**: T005b.

- [X] T011b [US1] **Artifact Generation & Stratified Split**: Implement `code/02_annotation_distillation/annotate_failures.py` to:
 1. Load `data/derived/failure_cases_consensus.json`.
 2. Validate against `failure_case.schema.yaml` (T006a).
 3. Perform a **stratified** split by `annotated_structural_feature` into `failure_cases_train.json` (majority), `failure_cases_val.json` (minority), `failure_cases_test.json` (minority) using `SPLIT_SEED` from `config.py`.
 4. Write the three files under `data/derived/`.
 5. Log counts per split to `data/artifacts/split_log.json`.
 **Dependency**: T005c, T054, T006a, T050.

- [X] T011c [US1] **Implement Mock Data Generator (Fallback)**: Implement `code/02_annotation_distillation/generate_mock_data.py` to create deterministic mock data if T011b fails or produces empty splits. **Action**:
 1. Generate 50 mock `FailureCase` records with random `task_id`, `raw_error_log`, `ground_truth_resolution`, and `annotated_structural_feature` (from the enum).
 2. Split into train/val/test using `SPLIT_SEED` from `config.py`.
 3. Write to `data/derived/failure_cases_train_mock.json`, `failure_cases_val_mock.json`, `failure_cases_test_mock.json`.
 4. Log a warning that mock data is being used.
 **Constraint**: This task is ONLY executed if T011b fails or produces empty splits. It ensures the pipeline can proceed for testing.
 **Dependency**: T011b (conditional).

- [X] T013 [US1] **Distill Rules with Hard Coverage Requirement**: Implement `code/02_annotation_distillation/distill_rules.py`:
 1. Use `select_model` (T007c) to pick the largest model fitting RAM/CPU.
 2. Verify quantization passed (T043) before loading.
 3. Train on `failure_cases_train.json` (or `failure_cases_train_mock.json` if T011b failed), evaluate on `failure_cases_val.json` (or `failure_cases_val_mock.json`).
 4. **Must achieve ≥ 90 % coverage** of validation patterns; if coverage < 90 %, raise `CoverageError` and abort (hard requirement per FR‑002).
 5. Write `data/derived/rules_library.json` and log model name to `data/artifacts/model_selection.log`.
 **Dependency**: T011b, T011c, T006b, T007c, T043.

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

- [X] T019a [US2] **Generate Experiment Manifest**: Implement `code/03_execution/generate_manifest.py` to:
 1. Load `failure_cases_test.json` (or `failure_cases_test_mock.json` if T011b failed).
 2. Read `required_sample_size` from `power_analysis_report.json`; if missing, abort with clear error.
 3. Perform a **stratified random sample** (by `annotated_structural_feature`) of the requested size using `SPLIT_SEED` from `config.py`. If the dataset is smaller than the required size, use all available rows and log a warning.
 4. Write `data/derived/experiment_manifest.csv` with columns `task_id`, `failure_type`.
 **Dependency**: T011b, T011c, T044.

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

- [X] T021 [US2] **Execute Baseline on Standard Resources**: Implement `code/03_execution/run_baseline.py` that:
 1. Sends the `experiment_manifest.csv` to the external baseline runner via its REST API (`POST /run`).
 2. The runner executes the full AutoResearchClaw agent on a separate runner with **standard resources** (4 CPU, 16 GB RAM) and returns a JSON array of results.
 3. Save the returned array to `data/derived/baseline_results.json`.
 4. The runner also returns a resource‑usage summary saved as `data/derived/baseline_resource_metrics.json`.
 **Constraint**: No local multiprocessing limits; execution must be remote to satisfy FR‑004 and Constitution Principle VII.
 **Dependency**: T058b.

- [X] T021c [US2] **Instrument Baseline Trigger Metrics**: Implement `code/03_execution/instrument_baseline.py` that records the local request latency, peak memory of the client process, and writes `data/derived/baseline_trigger_metrics.json`. **Dependency**: T019a.

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

- [X] T025 [US3] Implement `code/04_analysis/statistical_model.py` to fit a mixed‑effects logistic regression:
  - Formula: `success ~ failure_type * method + (1|task_id)`
  - Use `statsmodels` (`MixedLM`) or `pymer4`.
  - Output `data/derived/regression_results.json` containing at least:
    - `interaction_p_value`
    - `method_coefficients` (dict)
    - `failure_type_coefficients` (dict)
 **Dependency**: T022.

- [X] T026a [US3] **Model Fitting**: (Implemented above as part of T025) – now explicitly outputs `regression_results.json` with the required fields. **Dependency**: T022.

- [X] T026b [US3] **Significance Determination**: Extend `statistical_model.py` (or a wrapper) to:
 1. Read `interaction_p_value` from `regression_results.json`.
 2. Set `interaction_significant` = `true` if `p < 0.05` else `false`.
 3. Add `narrative_conclusion` string:
    - If significant: `"The interaction term is statistically significant (p < 0.05), indicating that failure structure dictates method viability."`
    - Else: `"The interaction term is not statistically significant (p >= 0.05)."`
 4. Write back to `regression_results.json` with keys exactly `interaction_p_value`, `interaction_significant`, `narrative_conclusion`.
 **Dependency**: T026a.

- [X] T029a [US3] **Tobit Regression for Time‑to‑Pivot**: Implement `code/04_analysis/time_diff_tobit.py` to:
 1. Load `results.csv`.
  2. Treat any `time_to_pivot` equal to `TIMEOUT_SECONDS` as censored.
 3. Fit a Tobit model (e.g., via `statsmodels` `TobitModel`) on the paired differences (rule_engine – baseline).
 4. Output `data/derived/time_diff_tobit_results.json` with `p_value`, `ci_lower`, `ci_upper`, `statistic`.
 **Dependency**: T022.

- [X] T029b [US3] **Stratified Success Rates**: Implement `code/04_analysis/calculate_stratified_rates.py` to compute success rate per `failure_type` across both methods. Output `data/derived/stratified_success_rates.csv` with columns `failure_type,method,success_rate`. **Dependency**: T022.

- [X] T027b [US3] **Execute Error Taxonomy**: Implement `code/04_analysis/error_taxonomy.py` to:
 1. Load `results.csv` and `failure_cases.json` (the full labeled set).
 2. For each failed pivot (`success=False`):
    - If no rule matched (recorded as `"fallback_chain"` containing `"Unstructured"`), count as `"Coverage Gap"`.
    - Else if a rule matched but `pivot_action` differs from `ground_truth_resolution`, count as `"Distillation Error"`.
 3. Produce `data/derived/error_taxonomy_results.json` with exact schema:
```json
{
  "coverage_gap_count": <int>,
  "distillation_error_count": <int>,
  "total_failures": <int>,
  "breakdown_by_type": {
    "<failure_type>": {
      "coverage_gap": <int>,
      "distillation_error": <int>
    },
    ...
  }
}
```
 **Dependency**: T022, T011b, T011c.

- [X] T028 [US3] **Ground‑Truth Arbitration**: Ensure `error_taxonomy.py` loads `failure_cases.json` and uses its `ground_truth_resolution` field to decide whether a mismatched action is a Distillation Error. Document this step explicitly. **Dependency**: T022, T011b, T011c.

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

- [X] T047 [US3] **Final Metrics Aggregation**: Implement `code/04_analysis/aggregate_final_metrics.py` to combine all metrics. **Dependency**: T029f, T026b, T027b, T022, T011b, T011c.