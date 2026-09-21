---
description: "Task list template for feature implementation"
---

# Tasks: llmXive follow-up: extending "GateMem: Benchmarking Memory Governance in Multi-Principal Shared-Memo"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-gatemem-benc/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Contract tests for dataset and results schemas, integration tests for full pipeline.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `src/` directory structure. **Verification**: `assert os.path.isdir('src')`.
- [X] T001b [P] Create `tests/` directory structure. **Verification**: `assert os.path.isdir('tests')`.
- [X] T001c [P] Create `data/` directory structure. **Verification**: `assert os.path.isdir('data')`.
- [X] T001d [P] Create `contracts/`, `state/`, `logs/`, `templates/` directory structures. **Verification**: `assert all(os.path.isdir(p) for p in ['contracts', 'state', 'logs', 'templates'])`.
- [X] T002a [P] Create `requirements.txt` at repository root with pinned versions. Include: `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`. **Verification**: `assert os.path.isfile('requirements.txt')`.
- [X] T002b [P] Verify `requirements.txt` contains required packages. **Verification**: `pytest tests/unit/test_requirements.py::test_requirements_content`.
- [X] T003a [P] Create `.ruff.toml` at repository root with linting rules (max-line-length=88, select=["E", "F", "I"]). **Verification**: `assert os.path.isfile('.ruff.toml')`.
- [X] T003b [P] Create `tests/unit/test_lint_config.py` to verify `.ruff.toml` exists and is valid. **Verification**: `pytest tests/unit/test_lint_config.py::test_ruff_config_exists`.
- [X] T037a [P] Create `quickstart.md` in `specs/001-llmxive-follow-up-extending-gatemem-benc/` with initial project setup instructions, dataset download guide, and basic run commands. **Deliverable**: A markdown file in `specs/001-llmxive-follow-up-extending-gatemem-benc/` containing step-by-step instructions for environment setup, dataset fetching, and running the first evaluation. **Dependency**: None. **Verification**: `pytest tests/unit/test_docs.py::test_quickstart_exists` AND `assert "dataset download" in content` AND `assert "run commands" in content`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004a [P] Generate `contracts/dataset.schema.yaml` defining GateMem episode structure:
 - Define keys: `leak-target`, `roles`, `domains`, `outcome`, `predictors`, `covariates`.
 - Specify types and required fields based on spec.md.
- [X] T004 [P] Validate `contracts/dataset.schema.yaml` exists and is syntactically correct (PyYAML).
- [X] T005a [P] Generate `contracts/results.schema.yaml` defining metric output structure:
 - Define keys: `Access Control`, `Utility`, `Forgetting`, `Latency`, `RAM`, `P-Value`, `Test Statistic`.
 - Specify types and required fields based on spec.md.
- [X] T005 [P] Validate `contracts/results.schema.yaml` exists and is syntactically correct.
- [X] T006a [FR-001] Create `src/utils/data_loader.py` function `fetch_dataset()`:
 - Fetch GateMem dataset. **CRITICAL**: Do NOT hardcode a specific HuggingFace ID. Read `DATASET_ID` from `src/utils/config.py` or environment variable. **T044 defines the default value for DATASET_ID as 'gate-mem/benchmark-v1'**. If `DATASET_ID` is not set, raise `FileNotFoundError` with message "Dataset ID not configured. Please set DATASET_ID in config.py or env var."
 - **Strictly NO synthetic fallback**. If fetch fails (network error, missing file), raise `ConnectionError` immediately and exit with code 1. Log "Critical: Real Data Fetch Failed". **Rationale**: Constitution Principle I (Reproducibility) requires failure on missing data, not substitution.
 - **Checksumming**: Upon successful download, compute SHA checksum and write to `state/artifact_hashes.yaml` under key `gatemem_test`.
 - **Validation**: Verify the dataset contains all required variables (`outcome`, `predictors`, `covariates`) before returning. If missing, raise `ValueError`.
 - **Dependency**: None.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_fetch_streaming`.
- [X] T006e [FR-001] Create `src/utils/data_loader.py` function `generate_checksum_for_cached_data()`:
 - **Logic**: If `data/raw/` contains GateMem files but `state/artifact_hashes.yaml` is missing or missing the `gatemem_test` key:
 1. Compute SHA checksum of all raw files.
 2. Write to `state/artifact_hashes.yaml`.
 - **Error Handling**: If `state/artifact_hashes.yaml` exists and contains `gatemem_test` but the checksum mismatches the current raw files, raise `ValueError` with message "Checksum mismatch. Data integrity compromised. File may be corrupted."
 - **Dependency**: None.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_generate_checksum_cached`.
- [X] T006b [P] [FR-001] Create `src/utils/data_loader.py` function `parse_jsonl()`:
 - Parse JSONL files into episode dictionaries.
 - Handle malformed JSON by logging the line number and skipping the line (recoverable). Do NOT exit.
 - **Dependency**: None.
- [X] T006c [P] [FR-001] Create `src/utils/data_loader.py` function `extract_fields()`:
 - Explicitly extract and load fields: `outcome`, `predictors`, `covariates`, `leak-target`, `roles`, `domains`.
 - Raise `ValueError` if any *required* field is missing from an episode.
 - **Dependency**: None.
- [X] T006d-1 [P] [FR-001] [T004] Create `src/utils/data_loader.py` function `validate_semantics()`:
 - Validate presence of `outcome`, `predictors`, `covariates`, `leak-target` against `contracts/dataset.schema.yaml`.
 - **Semantic Validation**: At runtime, verify that `domain` values match expected set (medical, office, education, household) and `roles` match expected format.
 - **CRITICAL**: If `leak-target` is ambiguous (undefined role) or required fields are missing, **exclude this episode from the returned list** and log it as a validation error. **MUST write to `logs/edge_cases.log`** with format: `EXCLUDED: episode_id={id}, reason={reason}, raw_content={truncated_raw}`. **Do NOT flag and keep**.
 - **Dependency**: T004.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_validate_semantics_excludes_invalid`.
- [X] T006d-2 [P] [FR-001] Create `src/utils/data_loader.py` function `verify_checksum()`:
 - **Checksum Verification**: At runtime, verify the checksum in `state/artifact_hashes.yaml` matches the raw data files matching glob `data/raw/gatemem_test*.jsonl` before processing using **SHA-256**.
 - **Explicit Check**: If `state/artifact_hashes.yaml` is missing or missing `gatemem_test`, raise `FileNotFoundError` with message "Checksum file missing. Data integrity cannot be verified. Aborting."
 - **Mismatch Handling**: If checksum mismatched, raise `ValueError` with message "Checksum mismatch. Data integrity compromised."
 - **Dependency**: T006a, T006e.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_verify_checksum`.
- [X] T007 [P] Create `src/utils/profiling.py` for CPU/RAM and wall-clock time instrumentation (using `tracemalloc` or `psutil`):
 - Implement `profile_execution()` function returning a dict with standardized keys: `{'latency_ms': float, 'peak_ram_mb': float}`.
 - **Standardization**: All profiling tasks MUST use this function to ensure identical output keys for Gatekeeper and Baselines.
 - **Verification**: `pytest tests/unit/test_profiling.py::test_profile_execution_returns_dict`.
- [X] T008a [FR-005] Create `src/utils/stats.py` function `shapiro_wilk_test()`:
 - Implement Shapiro-Wilk normality test (α=0.05) on paired score differences.
 - **Artifact**: Produces `normality_results` dict for T026a-2.
 - **Verification**: `pytest tests/unit/test_stats.py::test_shapiro_wilk_returns_p_value`.
- [X] T008b [FR-005] Create `src/utils/stats.py` function `fit_fixed_effects_glm()`:
 - Implement Fixed-Effects Logistic Regression (GLM) using `statsmodels` with formula `score ~ method + C(Domain)`. **Explicitly state 'Domain' is a fixed effect covariate**.
 - **Primary Path**: This is the primary statistical method per Plan (N=4 domains).
 - **Artifact**: Produces `glm_results` dict for T008e-1.
 - **Verification**: `pytest tests/unit/test_stats.py::test_fit_glm_returns_dict`.
- [X] T008c [FR-005] Create `src/utils/stats.py` function `run_post_hoc()`:
 - Implement test selection logic: Use Shapiro-Wilk result to choose between parametric (t-test) or non-parametric (Wilcoxon) post-hoc tests on paired differences.
 - **Artifact**: Produces `post_hoc_results` dict for T008e-1.
 - **Verification**: `pytest tests/unit/test_stats.py::test_run_post_hoc_returns_dict`.
- [X] T008d [FR-005] Create `src/utils/stats.py` function `domain_stratified_analysis()`:
 - Implement domain-stratified analysis with aggregation method (average p-values).
 - **Fallback Path**: This is the fallback if GLM fails.
 - **Artifact**: Produces `stratified_results` dict for T008e-1.
 - **Verification**: `pytest tests/unit/test_stats.py::test_domain_stratified_analysis_returns_dict`.
- [X] T008g [FR-005] Create `src/utils/stats.py` function `fit_lmm()`:
 - Implement Linear Mixed-Effects Model (LMM) using `statsmodels` or `linearmixed` with formula `score ~ method + (1|Domain)`.
 - **Tertiary Path**: Only attempt if GLM and Stratified fail (N>=5 domains check).
 - **Artifact**: Produces `lmm_results` dict for T008e-1.
 - **Verification**: `pytest tests/unit/test_stats.py::test_fit_lmm_returns_dict`.
- [X] T008e-1 [P] [FR-005] **Orchestrate Stats**: Implement `src/utils/stats.py` function `orchestrate_stats()`:
 - **Logic**: Call T008b (GLM) first. If `SingularMatrixError` -> Call T008d (Stratified). If Stratified fails -> Call T008g (LMM).
 - **Dependency**: T008a, T008b, T008c, T008d, T008g.
 - **Artifact**: Produces `model_selection_result` dict.
 - **Verification**: `pytest tests/unit/test_stats.py::test_orchestrate_stats_returns_dict`.
- [X] T009 [P] Create `src/gatekeeper/pipeline.py` skeleton with entry points: `run_gatekeeper()`, `run_baseline()`, and `main()` for argument parsing
- [X] T015a [FR-002] Create `src/gatekeeper/rules.py` with regex-based rule engine for role validation and deletion log checking:
 - Implement specific regex patterns for role validation (e.g., `r"role:\s*(\w+)"`) and deletion log checking.
 - **Dependency**: None.
- [X] T015b [P] [FR-002] Modify `src/gatekeeper/rules.py` to add anomaly handling:
 - Handle malformed deletion log entries by defaulting to 'deny'.
 - **Definition of Malformed**: Any entry failing to match the schema pattern `r"^\[DELETION\]\s*\d{4}-\d{2}-\d{2}\s+\w+\s+\w+$"` (YYYY-MM-DD role status).
 - Log anomaly to `logs/deletion_errors.log` with format: `Anomaly: Malformed entry at line {line_no}: {entry_content}`.
 - **Dependency**: Must run after T015a.
 - **Verification**: `pytest tests/unit/test_rules.py::test_malformed_handling`.
- [X] T014a [FR-002] [US-1] Create `src/gatekeeper/classifiers.py`:
 - **Task**: Load Zero-Shot Intent Classifier using model ID `facebook/bart-large-mnli` (frozen).
 - **Logic**: Implement `run_inference()` function returning `{'inference_time_ms': float, 'peak_ram_mb': float}`.
 - **Zero-Shot Logic**: The classifier must perform zero-shot classification against the `leak-target` schema labels using `pipeline('zero-shot-classification', model='facebook/bart-large-mnli', candidate_labels=['allowed', 'denied'])`. **Explicitly map schema labels to model candidates**.
 - **CPU Enforcement**: Explicitly enforce CPU execution: Set `device='cpu'` and `torch.set_default_device('cpu')`. Do NOT raise an error if CUDA is available; simply force CPU usage to ensure reproducibility on diverse runners.
 - **Profiling Standardization**: Must use `src/utils/profiling.py` (T007) to generate these values to ensure consistent keys.
 - **Retry Logic**: If model load fails (cache corruption), retry once. If retry fails, exit with code 1 and log "Critical: Model Unavailable".
 - **Acceptance Criteria**: Verify the model runs on CPU-only runner (no CUDA, memory within constrained limits) and logs resource usage. **This verification must pass before T016 can proceed.**
 - **Dependency**: None.
 - **Verification**: `pytest tests/unit/test_classifier.py::test_cpu_only_enforcement`.
- [X] T010 [P] Create `tests/contract/test_dataset_schema.py` to validate raw data against `dataset.schema.yaml`
- [X] T011 [P] Create `tests/contract/test_results_schema.py` to validate output against `results.schema.yaml`
- [X] T001b Create `data/samples/` directory structure (if not created by T001).
- [X] T001c Create `logs/` directory structure (if not created by T001).
- [X] T043 [P] Create `templates/prompts.yaml` defining identical prompt templates for Gatekeeper and Baseline configurations:
 - Define keys: `gatekeeper_prompt`, `retrieval_only_prompt`, `long_context_prompt`.
 - Ensure all prompts use identical system instructions and few-shot examples where applicable.
 - **Constraint**: This file is the single source of truth for prompt engineering; any deviation between methods here invalidates the comparison.
 - **Verification**: `pytest tests/unit/test_prompts.py::test_prompts_load_successfully`.
- [X] T044 [P] Create `src/utils/config.py` function `get_llm_singleton()`:
 - **Task**: Implement a singleton pattern for the LLM backbone (e.g., Llama-3-8B) to ensure identical instance usage across Gatekeeper and Baselines.
 - **Logic**: Return a shared LLM instance with a unique `instance_id` exposed for verification.
 - **Config Definition**: **Explicitly define `DATASET_ID = 'gate-mem/benchmark-v1'` in `src/utils/config.py`**. If the environment variable `DATASET_ID` is not set, this default value MUST be used.
 - **Verification**: `pytest tests/unit/test_config.py::test_llm_singleton`.

---

## Phase 3: User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1) 🎯 MVP

**Goal**: Execute Gatekeeper and Baseline pipelines to measure unauthorized information leakage rates.

**Independent Test**: Run automated evaluation on "medical" and "office" domains; verify Access Control scores are output for both configurations.

### Implementation for User Story 1

- [X] T016 [US1] [DEPENDS ON T006, T009, T014a, T015a, T043, T044] [FR-002] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement `run_gatekeeper_episode()` function: Filter memory access using Classifier (T014a) + Rules (T015a) (AND logic) before LLM step.
 - **Prompt Templates**: Must load prompt templates from `templates/prompts.yaml` (T043) to ensure identical templates with baselines.
 - **LLM Backbone**: Must use the shared LLM instance from T044.
 - Reference `contracts/dataset.schema.yaml` for data structure.
 - **Output**: Write results to `data/processed/gatekeeper_results.json` with keys: `[episode_id, method, score, latency_ms, peak_ram_mb]`.
 - **Concurrency**: This task must run sequentially or with file locking to avoid race conditions on `data/processed/`.
 - **Dependency**: T006 (data loading), T009 (skeleton), T014a (classifier), T015a (rules), T043 (prompts), T044.
 - **Verification**: `pytest tests/integration/test_us1_medical_domain.py`.
- [X] T017a [US1] [DEPENDS ON T006, T009, T043, T044] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Retrieval-only" baseline execution path.
 - **Enforce identical prompt templates**: Load from `templates/prompts.yaml` (T043).
 - **Enforce identical retrieval parameters, and random seeds** as defined in FR-003 and T016 configuration.
 - **LLM Backbone Verification**: Must use the shared LLM instance from T044. **Verify: Log LLM instance ID and assert match with Gatekeeper run log**.
 - **Profiling**: Must use `src/utils/profiling.py` (T007) to log `latency_ms` and `peak_ram_mb` with standardized keys.
 - **Output**: Write results to `data/processed/baseline_retrieval_results.json`. **Schema**: `[episode_id, method, score, latency_ms, peak_ram_mb]`.
 - **Concurrency**: This task must run sequentially or with file locking to avoid race conditions on `data/processed/`.
 - **Dependency**: T006, T009, T043, T044.
 - **Verification**: `pytest tests/contract/test_baseline_retrieval_results.py`.
- [X] T017b [US1] [DEPENDS ON T006, T009, T043, T044] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Long-Context" baseline execution path.
 - **Enforce identical prompt templates**: Load from `templates/prompts.yaml` (T043).
 - **Enforce identical retrieval parameters, and random seeds**.
 - **LLM Backbone Verification**: Must use the shared LLM instance from T044. **Verify: Log LLM instance ID and assert match with Gatekeeper run log**.
 - **Profiling**: Must use `src/utils/profiling.py` (T007) to log `latency_ms` and `peak_ram_mb` with standardized keys.
 - **Output**: Write results to `data/processed/baseline_longcontext_results.json`. **Schema**: `[episode_id, method, score, latency_ms, peak_ram_mb]`.
 - **Concurrency**: This task must run sequentially or with file locking to avoid race conditions on `data/processed/`.
 - **Dependency**: T006, T009, T043, T044.
 - **Verification**: `pytest tests/contract/test_baseline_longcontext_results.py`.
- [X] T018 [US1] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_access_control()`:
 - Calculate Access Control score (unauthorized exposure rate) against ground truth.
 - **Verification**: `pytest tests/unit/test_metrics.py::test_access_control_calculation`.
- [X] T019 [US1] Implement `src/cli/run_evaluation.py` logic:
 - Execute US1 pipeline with `--domains medical,office` (and support for any domain).
 - Implement generalizable argument parser accepting `--domains` as a comma-separated list.
 - **Dependency**: T016, T017a, T017b, T018.
- [X] T020 [US1] [REMOVED: Logic merged into T006d]

### Tests for User Story 1 (Post-Implementation)

- [X] T012 [US1] Contract test: Verify `data/processed/access_control_results.json` matches `results.schema.yaml`
 - File: `tests/contract/test_access_control_results.py`
 - Assertion: `assert validate_results(data/processed/access_control_results.json, "results.schema.yaml")`
- [X] T013 [US1] Integration test: Run full pipeline on "medical" domain subset and assert Access Control score is calculated
 - File: `tests/integration/test_us1_medical_domain.py`
 - Assertion: `assert score > 0.0`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Gatekeeper vs. Baseline on Task Utility (Priority: P2)

**Goal**: Measure task success rates (Utility) and Forgetting compliance to ensure security filters do not degrade performance.

**Independent Test**: Run evaluation on "education" and "household" domains; verify Utility and Forgetting scores are calculated and compared against baselines.

### Implementation for User Story 2

- [X] T023 [US2] [DEPENDS ON T016, T017b] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_all_metrics()`:
 - Calculate Utility, Access Control, and Forgetting for **EVERY test episode** in a single pass using results from T016 and T017b.
 - **Clarification**: This task operates on the **raw results** from T016 and T017b (which contain `episode_id`). It does NOT depend on T026a-1 (pair_episodes). It calculates metrics per episode and outputs a unified file.
 - **Output**: Write a unified results file `data/processed/unified_metrics.json` containing all metrics for all episodes, keyed by `episode_id`. **MUST include boolean flags**: `is_false_positive`, `is_false_negative`, `forgetting_violation`. **MUST include 'domain' field**.
 - **Dependency**: T016 (Gatekeeper results), T017b (Baseline results). **Note: T023 must run AFTER T017b to ensure baseline results exist. T023 does NOT depend on T026a-1.**
 - **Verification**: `pytest tests/unit/test_metrics.py::test_all_metrics_calculation`.
- [X] T023a [P] [US2] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_conditional_utility()`:
 - Calculate Conditional Utility (task success rate among queries allowed by the Gatekeeper).
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [X] T023b [P] [US2] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_overall_success()`:
 - Calculate 'Overall Task Success Rate' (net success including False Positives) - **Supporting Metric**
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [X] T024 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_forgetting()`:
 - Calculate Forgetting (deletion compliance rate for deletion request episodes).
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [X] T025 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_fp_fn()`:
 - Calculate False Positive (valid query blocked) and False Negative (leak allowed) rates - **Supporting Metric**
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [X] T026a-1 [US2] [DEPENDS ON T016, T017b] [FR-005] Implement `src/utils/stats.py` function `pair_episodes()`:
 - **Executable Task**: Implement logic to match episodes across Gatekeeper and Baseline conditions using `episode_id`.
 - **Input**: Raw results from T016 and T017b.
 - **Output Schema**: Produces `paired_data` list with items: `{'episode_id': str, 'score': float, 'method': str ('gatekeeper' or 'baseline'), 'domain': str}`.
 - **Constraint**: If `episode_id` is missing or mismatched, raise `ValueError`.
 - **Dependency**: T016, T017b. **Note**: This is the single source of truth for pairing logic.
 - **Verification**: `pytest tests/unit/test_stats.py::test_pair_episodes_executable`.
- [X] T026a-2 [US2] [DEPENDS ON T026a-1, T023] [FR-005] Implement `src/utils/stats.py` function `run_statistical_comparison()`:
 - **Task**: Implement `run_statistical_comparison()` logic.
 1. **Join Data**: Merge `paired_data` (from T026a-1) with `unified_metrics` (from T023) on `episode_id`. **Ensure 'domain' is available from T023**.
 2. **Primary Model Fit**: Attempt Fixed-Effects GLM (T008b) for Access Control and Utility.
 3. **Primary Fallback**: If GLM fails (singularity/data insufficiency), run **Domain-Stratified Analysis** (T008d).
 4. **Tertiary Fallback**: If Stratified Analysis fails, run LMM (T008g).
 5. **Normality Check**: **MUST** perform Shapiro-Wilk (T008a) on paired differences *before* selecting post-hoc test.
 - **Input**: **Paired data from T026a-1** and **Unified metrics from T023**.
 - **Output Schema**: Dict with keys `[method_used, p_value, test_statistic, fallback_reason, normality_p_value]`.
 - **Dependency**: T008a, T008b, T008d, T008g, **T026a-1**, T023.
 - **Verification**: `pytest tests/unit/test_stats.py::test_statistical_comparison_returns_dict`.
- [X] T026a-3 [US2] [DEPENDS ON T026a-2] [FR-005] Implement `src/utils/stats.py` function `run_post_hoc_test()`:
 - **Task**: Select and run post-hoc test based on Normality Check result from T026a-2.
 - **Logic**: If `normality_p_value > 0.05` -> t-test; Else -> Wilcoxon (T008c).
 - **Output**: Dict with keys `[test_statistic, p_value, method]`.
 - **Dependency**: **T026a-2**, T008a.
 - **Verification**: `pytest tests/unit/test_stats.py::test_post_hoc_selection_logic`.
- [X] T026b [US2] [DEPENDS ON T026a-1] [US2] Implement secondary statistical validation for binary outcomes:
 - Implement `run_mcnemar_test()` function for paired binary outcomes (Access Control only) as the **Secondary** test per Plan Summary.
 - **Output**: Dict with keys `[test_statistic, p_value, method]`.
 - **Dependency**: **T026a-1**.
 - **Verification**: `pytest tests/unit/test_stats.py::test_mcnemar_test_returns_dict`.
- [X] T027 [US2] Implement `src/cli/run_evaluation.py` logic: Execute US2 pipeline on `--domain education,household` using existing CLI skeleton
- [X] T028a [US2] [DEPENDS ON T023] Implement `src/cli/run_evaluation.py` logic:
 - Generate individual result files for Utility, Conditional Utility, Forgetting, etc.
 - **Note**: T023 already produces unified_metrics.json; this task extracts subsets if needed for reporting.
- [X] T028b [US2] [DEPENDS ON T028a] Implement `src/cli/run_evaluation.py` logic:
 - Aggregate individual metric results into `data/processed/combined_metrics.json`.
 - **Requirement**: Must merge all metric outputs into a single JSON file keyed by `episode_id` to enable downstream reporting. **Note**: T029a depends on T023 directly, not T028b.
 - **Dependency**: T028a. **No [P] tag**.
 - **Verification**: `pytest tests/contract/test_combined_metrics.py`.
- [X] T029a [US2] [DEPENDS ON T023] Implement failure case sampling logic:
 - Select a sample of cases with a **fixed random seed**.
 - **Logic**: Filter results from `data/processed/unified_metrics.json` for failures. **Definition of Failure**: `is_false_positive == True` OR `is_false_negative == True` OR `forgetting_violation == True`. **Include Forgetting Violations**.
 - **Requirement**: T023 output MUST include 'domain' field.
 - Calculate N = total failure count.
 - **Sampling Condition**: If N > 0: Proceed to sample.
 - **Stratification Condition**: If N > 50, apply **proportional stratification by domain** (strata_size = total_sample * (stratum_count / total_count)). If N <= 50, use simple random sampling of all N entries.
 - Output to `data/samples/failure_cases.json`.
 - **Dependency**: T023.
 - **Verification**: `pytest tests/unit/test_failure_sampling.py::test_sampling_logic_stratified` and `pytest tests/unit/test_failure_sampling.py::test_sampling_logic_seed_42` and `assert len(data) == min(N, 50)`.
- [X] T029b [US2] [DEPENDS ON T029a] [P] Create unit test for failure case sampling:
 - File: `tests/unit/test_failure_sampling.py`
 - Assertion: Verify `data/samples/failure_cases.json` exists, contains correct count (min(N, 50)), and is stratified correctly if N > 50. Ensure a fixed random seed was used.

### Tests for User Story 2 (Post-Implementation)

- [X] T021 [US2] Contract test: Verify `data/processed/utility_results.json` contains `conditional_utility` and `overall_success` fields
 - File: `tests/contract/test_utility_results.py`
 - Assertion: `assert validate_results(data/processed/utility_results.json, "results.schema.yaml")`
- [X] T022 [US2] Integration test: Run pipeline on "education" domain and assert Utility score matches expected range against ground truth
 - File: `tests/integration/test_us2_education_domain.py`
 - Assertion: `assert 0.0 <= utility_score <= 1.0`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Profile Computational Cost and Latency (Priority: P3)

**Goal**: Measure wall-clock inference time and peak CPU/RAM usage to verify computational cost reduction.

**Independent Test**: Execute pipeline with instrumentation; verify logs contain peak RAM (MB) and wall-clock time for both configurations.

### Implementation for User Story 3

- [X] T032 [P] [US3] Integrate `src/utils/profiling.py` into `src/gatekeeper/pipeline.py` to log start/end times and peak memory for each episode
- [X] T033a [US3] [DEPENDS ON T006, T009, T007] Implement `src/gatekeeper/pipeline.py` logic: Run Baseline (Long-Context) with profiling enabled
 - **Constraint**: Must use `src/utils/profiling.py` (T007) to ensure `latency_ms` and `peak_ram_mb` keys match Gatekeeper output.
 - **Dependency**: T017b (Long-Context baseline implementation).
- [X] T034 [US3] Implement `src/gatekeeper/pipeline.py` logic: Run Gatekeeper with profiling enabled
 - **Constraint**: Must use `src/utils/profiling.py` (T007) to ensure `latency_ms` and `peak_ram_mb` keys match Baseline output.
- [X] T035 [US3] Implement `src/cli/run_evaluation.py` logic:
 - Aggregate profiling data from Gatekeeper and Baseline runs into a comparative JSON structure (`data/processed/performance_comparison.json`).
 - **Calculate percentage reduction** in latency and RAM for Gatekeeper vs Baseline. **Handle negative reductions explicitly**: If Gatekeeper is slower, report as "increase" or negative percentage to avoid misinterpretation.
 - **Output**: Must produce a specific comparative JSON structure with keys `[method, latency_ms, peak_ram_mb, latency_reduction_pct, ram_reduction_pct]` to be consumed by T036.
 - Output aggregated data to `data/processed/performance_results.json`.
- [X] T036 [US3] Create final report generator:
 - Create `src/cli/generate_report.py` script.
 - Output `data/results/final_benchmark_report.md`.
 - Include sections: Access Control, Utility, Forgetting, Cost.
 - Include tables with headers: Method, Score, StdDev, **Test Statistic**, **P-Value**, **Method Used (GLM/McNemar's/Fallback)**, Latency (ms), RAM (MB).
 - **Conditional Logic**: If method is parametric (t-test/GLM), include **Degrees of Freedom**. If non-parametric (Wilcoxon), include **N (sample size)**. If McNemar's, include **Chi-Square Statistic**.
 - Use `tabulate` library for formatting; round floating-point numbers to a standard level of precision.
 - Reference `contracts/results.schema.yaml` for formatting.
 - **Verification**: `pytest tests/integration/test_report_generation.py`.

### Tests for User Story 3 (Post-Implementation)

- [X] T030 [US3] Contract test: Verify `data/processed/performance_results.json` contains `latency_ms` and `peak_ram_mb` fields
 - File: `tests/contract/test_performance_results.py`
 - Assertion: `assert validate_results(data/processed/performance_results.json, "results.schema.yaml")`
- [X] T031 [US3] Integration test: Run pipeline on small subset and assert resource logs are generated and non-zero
 - File: `tests/integration/test_us3_small_subset.py`
 - Assertion: `assert peak_ram_mb > 0 and latency_ms > 0`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T037b [P] Documentation: Update `quickstart.md` with instructions to run the full benchmark suite
- [X] T038a [P] Run `mypy --strict src/` to check type hints. **Verification**: `assert mypy_exit_code == 0`.
- [X] T038b [P] Fix any type errors reported by T038a. **Verification**: `assert mypy_exit_code == 0` after fixes.
- [X] T039 [P] Security: Run PII scan on `data/raw/` and `data/processed/` artifacts
- [X] T040 [P] Run `pytest` for all unit, integration, and contract tests
- [X] T041 Validate `data/results/final_benchmark_report.md` against `contracts/results.schema.yaml`
- [X] T042 [P] Add `tests/contract/test_failure_cases.py` to verify schema and count of `data/samples/failure_cases.json`.
 - Verify `data/samples/failure_cases.json` contains a representative subset of failure cases, bounded by a small constant upper limit. **N is defined as the total count of identified failure cases (False Positives + False Negatives + Forgetting Violations) from the results JSON.** **If N > 50, verify entries are stratified by domain.** Ensure a fixed random seed was used.

---

## Phase 7: Revision & Review Resolution

**Purpose**: Address specific concerns raised during the research-stage review regarding statistical validity and data integrity.

### Revision Concerns

- [X] T045-EXEC [P] [Review] **Resolve Ambiguity in Statistical Methodology**: Update `src/utils/stats.py` and `plan.md` to explicitly clarify the primary vs. secondary statistical tests.
 - **Action**: Ensure `orchestrate_stats()` (T008e-1) clearly prioritizes **Fixed-Effects GLM** for continuous/ordinal outcomes (Utility, Access Control scores) with 'Domain' as a fixed effect covariate (per Plan's N=4 constraint).
 - **Action**: Ensure **McNemar's Test** is implemented strictly as the **secondary** test for paired *binary* outcomes (e.g., Success/Failure per episode) and is not conflated with the GLM.
 - **Action**: Verify `plan.md` Complexity Tracking table correctly reflects that Wilcoxon is invalid for binary data and that GLM is preferred over LMM if sample size is small (N=4 domains).
 - **Implementation**: Modify `src/utils/stats.py` to enforce GLM-first logic in `orchestrate_stats()` (T008e-1).
 - **Verification**: `pytest tests/unit/test_stats.py::test_glm_priority` (asserts GLM is attempted first and fallback logic is correct).

- [X] T046-EXEC [P] [Review] **Resolve Data Integrity & Streaming Constraints**: Update `src/utils/data_loader.py` to explicitly handle large GateMem datasets without synthetic fallbacks.
 - **Action**: Modify `src/utils/data_loader.py` function `fetch_dataset()` (T006a) to implement streaming logic using `datasets.load_dataset(..., streaming=True)` to process episodes in chunks, ensuring RAM usage stays <7GB.
 - **Action**: Add explicit error handling in `validate_semantics()` (T006d-1) to log and skip episodes with ambiguous `leak-target` annotations (per Edge Cases in spec.md) rather than failing the run, while maintaining a strict "Fail Loud" policy for missing required fields.
 - **Action**: Verify that no `try/except` block in the data loader falls back to `generate_synthetic_*()` or mock data. If fetch fails, the script must exit with code 1.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_streaming_no_synthetic_fallback`.

- [X] T047-EXEC [P] [Review] **Resolve Prompt & LLM Consistency**: Update `src/gatekeeper/pipeline.py` and `templates/prompts.yaml` to guarantee strict parity between Gatekeeper and Baseline runs.
 - **Action**: Ensure `run_gatekeeper_episode()` (T016) and `run_baseline_episode()` (T017a/b) both load prompts *exclusively* from `templates/prompts.yaml` (T043) without hardcoding strings.
 - **Action**: Add a runtime check in `src/cli/run_evaluation.py` (T019/T027) to assert that the LLM instance ID (from T044) is identical across all pipeline runs for a single execution. **Assertion**: `assert llm_id_gatekeeper == llm_id_baseline`.
 - **Verification**: `pytest tests/integration/test_prompt_consistency.py` (asserts prompt hash match and LLM ID match).

- [X] T049 [P] [Review] **Implement Robust Error Logging for Edge Cases**: Enhance logging for ambiguous `leak-target` and malformed deletion logs to ensure manual review is possible.
 - **Action**: Extend `src/gatekeeper/rules.py` and `src/utils/data_loader.py` to write detailed context (episode_id, raw content, specific error reason) to `logs/edge_cases.log` whenever an exclusion or default action occurs.
 - **Action**: Ensure `logs/edge_cases.log` is included in the final artifact bundle for manual audit.
 - **Rationale**: Spec.md Edge Cases require specific handling for ambiguous roles and malformed logs; logging ensures traceability without failing the run.
 - **Dependency**: T015a, T015b, T006d-1.
 - **Verification**: `pytest tests/unit/test_logging.py::test_edge_case_logging`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on initial implementation (Phases 3-6) and review feedback

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Uses `metrics.py` and `stats.py` from Foundation
- **User Story 3 (P3)**: Can start after Foundational - Uses `profiling.py` from Foundation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before pipeline logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T006a-c, T007, T008a-d, T008g) can run in parallel (within Phase 2) **BUT** T006d-1, T006d-2, and T008e-1 must wait for their components.
- All user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **WARNING**: In Phase 4, T026a-2 (Statistical Comparison) CANNOT run in parallel with T023/T024 (Metric Calculation) as it depends on their outputs.

### Parallel Example: User Story 1

```bash
# Launch all models/utilities for User Story 1 together:
Task: "Implement src/gatekeeper/classifiers.py: Load Zero-Shot BART Intent Classifier"
Task: "Implement src/gatekeeper/rules.py: Implement regex-based rule engine"
Task: "Create templates/prompts.yaml: Define identical prompt templates"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Access Control metric)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Utility/Forgetting)
4. Add User Story 3 → Test independently → Deploy/Demo (Cost profiling)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Access Control)
 - Developer B: User Story 2 (Utility/Forgetting)
 - Developer C: User Story 3 (Profiling)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Constraint**: All models must run on CPU-only (BART Zero-Shot); no low-bit quantization or CUDA usage.
- **Constraint**: Dataset must be processed in batches or streamed to fit available RAM.
- **Constraint**: Random seeds fixed to ensure reproducibility.
- **Statistical Fallback**: Primary method is Fixed-Effects GLM (Plan's requirement for N=4). If infeasible, use **Domain-Stratified Analysis**. If Stratified fails, use LMM. Normality checks determine post-hoc test (t-test/Wilcoxon). **McNemar's Test is the Secondary test for binary outcomes (Access Control)**.
- **Data Integrity**: **T006a/b/c/d-1/d-2** include strict fail-loud, streaming, and checksum logic. Synthetic fallbacks are strictly prohibited.
- **Prompt Integrity**: T043 ensures prompt consistency across Gatekeeper and Baselines, a prerequisite for valid comparison (FR-003).
- **LLM Integrity**: T044 ensures a shared LLM instance across Gatekeeper and Baselines to prevent configuration drift.
- **Model Integrity**: T014a explicitly enforces BART-Large-MNLI as per FR-002 and Plan Summary.
- **Revision Integrity**: T045-T047 explicitly address research-stage review concerns regarding statistical validity, data streaming, and prompt consistency.
- **Edge Case Logging**: T049 ensures transparency for excluded/ambiguous data points.