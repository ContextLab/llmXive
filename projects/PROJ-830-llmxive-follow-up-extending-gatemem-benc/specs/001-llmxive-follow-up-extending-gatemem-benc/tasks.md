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

- [X] T001a-1 [P] Create directory `src/` at repository root. **Verification**: `assert os.path.isdir('src')`.
- [X] T001a-2 [P] Create directory `tests/` at repository root. **Verification**: `assert os.path.isdir('tests')`.
- [X] T001a-3 [P] Create directory `data/` at repository root. **Verification**: `assert os.path.isdir('data')`.
- [X] T001a-4 [P] Create directory `contracts/` at repository root. **Verification**: `assert os.path.isdir('contracts')`.
- [X] T001a-5 [P] Create directory `state/` at repository root. **Verification**: `assert os.path.isdir('state')`.
- [X] T001a-6 [P] Create directory `logs/` at repository root. **Verification**: `assert os.path.isdir('logs')`.
- [X] T001a-7 [P] Create directory `templates/` at repository root. **Verification**: `assert os.path.isdir('templates')`.
- [X] T001b [P] Create subdirectories: `src/gatekeeper/`, `src/utils/`, `src/cli/` (with `__init__.py`). **Verification**: `assert all(os.path.isdir(p) for p in ['src/gatekeeper', 'src/utils', 'src/cli'])`.
- [X] T001c [P] Create subdirectories: `tests/contract/`, `tests/integration/`, `tests/unit/`. **Verification**: `assert all(os.path.isdir(p) for p in ['tests/contract', 'tests/integration', 'tests/unit'])`.
- [X] T001d [P] Create subdirectories: `data/raw/`, `data/processed/`, `data/samples/`. **Verification**: `assert all(os.path.isdir(p) for p in ['data/raw', 'data/processed', 'data/samples'])`.
- [X] T002a [P] Create `requirements.txt` at repository root with pinned versions. Include: `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`. **Verification**: `assert os.path.isfile('requirements.txt')`.
- [X] T002b [P] Verify `requirements.txt` contains required packages. **Verification**: `pytest tests/unit/test_requirements.py::test_requirements_content`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools.
- [ ] T037a [P] Create `quickstart.md` in `specs/001-llmxive-follow-up-extending-gatemem-benc/` with initial project setup instructions, dataset download guide, and basic run commands. **Deliverable**: A markdown file in `specs/001-llmxive-follow-up-extending-gatemem-benc/` containing step-by-step instructions for environment setup, dataset fetching, and running the first evaluation. **Dependency**: None. **Verification**: `pytest tests/unit/test_docs.py::test_quickstart_exists`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading (with hardening/streaming), stats logic, rule engine, classifier, and CLI skeleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Generate `contracts/dataset.schema.yaml` defining GateMem episode structure:
 - Define keys: `leak-target`, `roles`, `domains`, `outcome`, `predictors`, `covariates`.
 - Specify types and required fields based on spec.md.
- [X] T004 [P] Validate `contracts/dataset.schema.yaml` exists and is syntactically correct (PyYAML).
- [X] T005a [P] Generate `contracts/results.schema.yaml` defining metric output structure:
 - Define keys: `Access Control`, `Utility`, `Forgetting`, `Latency`, `RAM`, `P-Value`, `Test Statistic`.
 - Specify types and required fields based on spec.md.
- [X] T005 [P] Validate `contracts/results.schema.yaml` exists and is syntactically correct.
- [X] T006a [FR-001] Create `src/utils/data_loader.py` function `fetch_dataset()`:
 - Fetch GateMem dataset from HuggingFace ID `gatekeeper/gatemem` using `config='default'` and `split='test'` with `streaming=True` to handle memory constraints.
 - **Strictly NO synthetic fallback**. If fetch fails (network error, missing file), raise `ConnectionError` immediately and exit with code 1. Log "Critical: Real Data Fetch Failed". **Rationale**: Constitution Principle I (Reproducibility) requires failure on missing data, not substitution.
 - **Checksumming**: Upon successful download, compute SHA256 checksum and write to `state/artifact_hashes.yaml` under key `gatemem_test`.
 - **Validation**: Verify the dataset contains all required variables (`outcome`, `predictors`, `covariates`) before returning. If missing, raise `ValueError`.
 - **Dependency**: None.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_fetch_streaming`.
- [X] T006b [P] [FR-001] Create `src/utils/data_loader.py` function `parse_jsonl()`:
 - Parse JSONL files into episode dictionaries.
 - Handle malformed JSON by logging the line number and skipping the line (recoverable). Do NOT exit.
 - **Dependency**: None.
- [X] T006c [P] [FR-001] Create `src/utils/data_loader.py` function `extract_fields()`:
 - Explicitly extract and load fields: `outcome`, `predictors`, `covariates`, `leak-target`, `roles`, `domains`.
 - Raise `ValueError` if any *required* field is missing from an episode.
 - **Dependency**: None.
- [X] T006d [FR-001] Create `src/utils/data_loader.py` function `validate_episode()`:
 - Validate presence of `outcome`, `predictors`, `covariates`, `leak-target` against `contracts/dataset.schema.yaml`.
 - **Semantic Validation**: At runtime, verify that `domain` values match expected set (medical, office, education, household) and `roles` match expected format. If values are invalid, log "validation error" and exclude episode.
 - **Checksum Verification**: At runtime, verify the checksum in `state/artifact_hashes.yaml` matches the raw data before processing. **Explicitly check if `state/artifact_hashes.yaml` exists and contains the key `gatemem_test`. If missing, log "First run detected: Checksum file missing. Proceeding without verification" and skip check. If file exists but checksum mismatched, raise `ValueError` with message "Checksum mismatch. Data integrity compromised."**
 - **Dependency**: T004, T005, **T006a**. **Note**: This task must be executed after T006a in the pipeline to ensure the checksum file exists. **No [P] tag**.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_validate_episode`.
- [ ] T007 [P] Create `src/utils/profiling.py` for CPU/RAM and wall-clock time instrumentation (using `tracemalloc` or `psutil`):
 - Implement `profile_execution()` function returning a dict with standardized keys: `{'latency_ms': float, 'peak_ram_mb': float}`.
 - **Standardization**: All profiling tasks MUST use this function to ensure identical output keys for Gatekeeper and Baselines.
 - **Verification**: `pytest tests/unit/test_profiling.py::test_profile_execution_returns_dict`.
- [ ] T008a [FR-005] Create `src/utils/stats.py` function `shapiro_wilk_test()`:
 - Implement Shapiro-Wilk normality test (α=0.05) on paired score differences.
 - **Artifact**: Produces `normality_results` dict for T008e/T026a.
 - **Verification**: `pytest tests/unit/test_stats.py::test_shapiro_wilk_returns_p_value`.
- [ ] T008b [FR-005] Create `src/utils/stats.py` function `fit_fixed_effects_glm()`:
 - Implement Fixed-Effects Logistic Regression (GLM) using `statsmodels` with formula `score ~ method + C(Domain)`. **Explicitly state 'Domain' is a fixed effect covariate**.
 - **Secondary Path**: This is the secondary statistical method if LMM is infeasible.
 - **Artifact**: Produces `glm_results` dict for T008e.
 - **Verification**: `pytest tests/unit/test_stats.py::test_fit_glm_returns_dict`.
- [ ] T008c [FR-005] Create `src/utils/stats.py` function `run_post_hoc()`:
 - Implement test selection logic: Use Shapiro-Wilk result to choose between parametric (t-test) or non-parametric (Wilcoxon) post-hoc tests on paired differences.
 - **Artifact**: Produces `post_hoc_results` dict for T008e.
 - **Verification**: `pytest tests/unit/test_stats.py::test_run_post_hoc_returns_dict`.
- [ ] T008d [FR-005] Create `src/utils/stats.py` function `domain_stratified_analysis()`:
 - Implement domain-stratified analysis with aggregation method (average p-values).
 - **Usage**: Fallback if GLM fails or if hierarchical modeling is required but infeasible.
 - **Artifact**: Produces `stratified_results` dict for T008e.
 - **Verification**: `pytest tests/unit/test_stats.py::test_domain_stratified_analysis_returns_dict`.
- [ ] T008g [FR-005] Create `src/utils/stats.py` function `fit_lmm()`:
 - Implement Linear Mixed-Effects Model (LMM) using `statsmodels` or `linearmixed` with formula `score ~ method + (1|Domain)`.
 - **Primary Path**: This is the primary statistical method per FR-005.
 - **Artifact**: Produces `lmm_results` dict for T008e.
 - **Verification**: `pytest tests/unit/test_stats.py::test_fit_lmm_returns_dict`.
- [ ] T008e [FR-005] Create `src/utils/stats.py` function `run_full_stats_pipeline()`:
 - Implement orchestration logic returning a dict with keys: `[method_used, p_value, test_statistic, fallback_reason]`.
 - **Control Flow**: 1. **Primary**: Try Linear Mixed-Effects Model (LMM) (T008g). 2. If `SingularMatrixError` or infeasible -> Fixed-Effects GLM (T008b). 3. **Secondary**: On success/fallback, perform Normality Check (Shapiro-Wilk on paired differences) -> Wilcoxon/t-test (T008c). 4. **Fallback**: If GLM fails -> Domain-Stratified Analysis (T008d).
 - **Dependency**: T008a, T008b, T008c, T008d, T008g. **No [P] tag**.
 - **Verification**: `pytest tests/unit/test_stats.py::test_full_stats_pipeline_returns_dict`.
- [ ] T008f [DEF] [FR-005] Create `src/utils/stats.py` function `pair_episodes()`:
 - **Definition Only**: Implement logic to match episodes across Gatekeeper and Baseline conditions using `episode_id`.
 - **Requirement**: Input must be two lists of results (Gatekeeper, Baseline) with matching `episode_id` keys. Output must be a paired list of tuples `(gatekeeper_score, baseline_score)`.
 - **Constraint**: If `episode_id` is missing or mismatched, raise `ValueError`.
 - **Artifact**: Produces `paired_data` list for T026a.
 - **Note**: **Definition Only**. This function is defined in Phase 2 but cannot be executed until Phase 3 data is generated. **Tagged [DEF] to indicate it is a definition, not an executable parallel task in Phase 2.** No verification test for this task; verification is in T008f-exec.
 - **Verification**: None (Definition only).
- [X] T009 [P] Create `src/gatekeeper/pipeline.py` skeleton with entry points: `run_gatekeeper()`, `run_baseline()`, and `main()` for argument parsing
- [ ] T015a [FR-002] Create `src/gatekeeper/rules.py` with regex-based rule engine for role validation and deletion log checking:
 - Implement specific regex patterns for role validation (e.g., `r"role:\s*(\w+)"`) and deletion log checking.
 - **Dependency**: None.
- [ ] T015b [P] [FR-002] Modify `src/gatekeeper/rules.py` to add anomaly handling:
 - Handle malformed deletion log entries by defaulting to 'deny'.
 - Log anomaly to `logs/deletion_errors.log`.
 - **Dependency**: Must run after T015a.
- [ ] T014a [FR-002] [US-1] Create `src/gatekeeper/classifiers.py`:
 - **Task**: Load Zero-Shot Intent Classifier using model ID `facebook/distilbert-base-uncased` (frozen).
 - **Logic**: Implement `run_inference()` function returning `{'inference_time_ms': float, 'peak_ram_mb': float}`.
 - **Zero-Shot Logic**: The classifier must perform zero-shot classification against the `leak-target` schema labels (e.g., "allowed", "denied") without fine-tuning.
 - **CPU Enforcement**: Explicitly enforce CPU execution: Set `device='cpu'` and `torch.set_default_device('cpu')`. Do NOT raise an error if CUDA is available; simply force CPU usage to ensure reproducibility on diverse runners.
 - **Profiling Standardization**: Must use `src/utils/profiling.py` (T007) to generate these values to ensure consistent keys.
 - **Retry Logic**: If model load fails (cache corruption), retry once. If retry fails, exit with code 1 and log "Critical: Model Unavailable".
 - **Acceptance Criteria**: Verify the model runs on CPU-only runner (no CUDA, memory within constrained limits) and logs resource usage. **This verification must pass before T016 can proceed.**
 - **Dependency**: None (Independent of T015a).
 - **Verification**: `pytest tests/unit/test_classifier.py::test_cpu_only_enforcement`.
- [X] T010 [P] Create `tests/contract/test_dataset_schema.py` to validate raw data against `dataset.schema.yaml`
- [X] T011 [P] Create `tests/contract/test_results_schema.py` to validate output against `results.schema.yaml`
- [X] T001b Create `data/samples/` directory structure (if not created by T001).
- [X] T001c Create `logs/` directory structure (if not created by T001).
- [ ] T043 [P] [FR-003] Create `templates/prompts.yaml` defining identical prompt templates for Gatekeeper and Baseline configurations:
 - Define keys: `gatekeeper_prompt`, `retrieval_only_prompt`, `long_context_prompt`.
 - Ensure all prompts use identical system instructions and few-shot examples where applicable.
 - **Constraint**: This file is the single source of truth for prompt engineering; any deviation between methods here invalidates the comparison.
 - **Verification**: `pytest tests/unit/test_prompts.py::test_prompts_load_successfully`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1) 🎯 MVP

**Goal**: Execute Gatekeeper and Baseline pipelines to measure unauthorized information leakage rates.

**Independent Test**: Run automated evaluation on "medical" and "office" domains; verify Access Control scores are output for both configurations.

### Implementation for User Story 1

- [ ] T016 [US1] [DEPENDS ON T006, T009, T014a, T015a, T043] [FR-002] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement `run_gatekeeper_episode()` function: Filter memory access using Classifier (T014a) + Rules (T015a) (AND logic) before LLM step.
 - **Prompt Templates**: Must load prompt templates from `templates/prompts.yaml` (T043) to ensure identical templates with baselines.
 - Reference `contracts/dataset.schema.yaml` for data structure.
 - **Output**: Write results to `data/processed/gatekeeper_results.json` with keys: `[episode_id, method, score, latency_ms, peak_ram_mb]`.
 - **Concurrency**: This task must run sequentially or with file locking to avoid race conditions on `data/processed/`.
 - **Dependency**: T006 (data loading), T009 (skeleton), T014a (classifier), T015a (rules), T043 (prompts).
 - **Verification**: `pytest tests/integration/test_us1_medical_domain.py`.
- [ ] T017a [US1] [DEPENDS ON T006, T009, T043] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Retrieval-only" baseline execution path.
 - **Enforce identical prompt templates**: Load from `templates/prompts.yaml` (T043).
 - **Enforce identical retrieval parameters, and random seeds** as defined in FR-003 and T016 configuration.
 - **Profiling**: Must use `src/utils/profiling.py` (T007) to log `latency_ms` and `peak_ram_mb` with standardized keys.
 - **Output**: Write results to `data/processed/baseline_retrieval_results.json`.
 - **Concurrency**: This task must run sequentially or with file locking to avoid race conditions on `data/processed/`.
 - **Dependency**: T006, T009, T043.
 - **Verification**: `pytest tests/contract/test_baseline_retrieval_results.py`.
- [ ] T017b [US1] [DEPENDS ON T006, T009, T043] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Long-Context" baseline execution path.
 - **Enforce identical prompt templates**: Load from `templates/prompts.yaml` (T043).
 - **Enforce identical retrieval parameters, and random seeds**.
 - **Profiling**: Must use `src/utils/profiling.py` (T007) to log `latency_ms` and `peak_ram_mb` with standardized keys.
 - **Output**: Write results to `data/processed/baseline_longcontext_results.json`.
 - **Concurrency**: This task must run sequentially or with file locking to avoid race conditions on `data/processed/`.
 - **Dependency**: T006, T009, T043.
 - **Verification**: `pytest tests/contract/test_baseline_longcontext_results.py`.
- [ ] T017c [US1] [DEPENDS ON T017a, T017b] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Manage prompt templates and random seeds globally.
 - Output `data/processed/baseline_results.json` with keys: `[method, score, std_dev, latency_ms, peak_ram_mb, episode_id]`.
 - **Explicitly write code to generate this file** and validate output against `contracts/results.schema.yaml`.
 - **Dependency**: T017a, T017b.
 - **Note**: This task must wait for T017a and T017b to complete before aggregating outputs.
 - **Verification**: `pytest tests/contract/test_baseline_results.py`.
- [ ] T018 [US1] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_access_control()`:
 - Calculate Access Control score (unauthorized exposure rate) against ground truth.
 - **Verification**: `pytest tests/unit/test_metrics.py::test_access_control_calculation`.
- [ ] T019 [US1] Implement `src/cli/run_evaluation.py` logic:
 - Execute US1 pipeline with `--domains medical,office` (and support for any domain).
 - Implement generalizable argument parser accepting `--domains` as a comma-separated list.
 - **Dependency**: T016, T017c, T018.
- [ ] T020 [US1] [REMOVED: Logic merged into T006d]

### Tests for User Story 1 (Post-Implementation)

- [ ] T012 [US1] Contract test: Verify `data/processed/access_control_results.json` matches `results.schema.yaml`
 - File: `tests/contract/test_access_control_results.py`
 - Assertion: `assert validate_results(data/processed/access_control_results.json, "results.schema.yaml")`
- [ ] T013 [US1] Integration test: Run full pipeline on "medical" domain subset and assert Access Control score is calculated
 - File: `tests/integration/test_us1_medical_domain.py`
 - Assertion: `assert score > 0.0`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Gatekeeper vs. Baseline on Task Utility (Priority: P2)

**Goal**: Measure task success rates (Utility) and Forgetting compliance to ensure security filters do not degrade performance.

**Independent Test**: Run evaluation on "education" and "household" domains; verify Utility and Forgetting scores are calculated and compared against baselines.

### Implementation for User Story 2

- [ ] T023 [P] [US2] [DEPENDS ON T016, T017c] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_all_metrics()`:
 - Calculate Utility, Access Control, and Forgetting for **EVERY test episode** in a single pass using results from T016 and T017c.
 - **Output**: Write a unified results file `data/processed/unified_metrics.json` containing all metrics for all episodes, keyed by `episode_id`.
 - **Dependency**: T016 (Gatekeeper results), T017c (Baseline results).
 - **Verification**: `pytest tests/unit/test_metrics.py::test_all_metrics_calculation`.
- [ ] T023a [P] [US2] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_conditional_utility()`:
 - Calculate Conditional Utility (task success rate among queries allowed by the Gatekeeper).
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [ ] T023b [P] [US2] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_overall_success()`:
 - Calculate 'Overall Task Success Rate' (net success including False Positives) - **Supporting Metric**
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [ ] T024 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_forgetting()`:
 - Calculate Forgetting (deletion compliance rate for deletion request episodes).
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [ ] T025 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_fp_fn()`:
 - Calculate False Positive (valid query blocked) and False Negative (leak allowed) rates - **Supporting Metric**
 - **Output**: Must include `episode_id` for pairing.
 - **Dependency**: T023.
- [ ] T008f-exec [US2] [DEPENDS ON T023, T017c] [FR-005] Implement `src/utils/stats.py` function `pair_episodes()`:
 - **Executable Task**: Implement logic to match episodes across Gatekeeper and Baseline conditions using `episode_id`.
 - **Input**: Must be the unified results from T023 and baseline results from T017c.
 - **Output**: Produces `paired_data` list for T026a/b.
 - **Constraint**: If `episode_id` is missing or mismatched, raise `ValueError`.
 - **Dependency**: T023, T017c.
 - **Verification**: `pytest tests/unit/test_stats.py::test_pair_episodes_executable`.
- [ ] T026a [US2] [DEPENDS ON T008a, T008b, T008c, T008d, T008g, T008f-exec, T023] [P] [US2] Implement `src/utils/stats.py` integration:
 - Implement `run_statistical_comparison()` function:
 1. **First**: Attempt Linear Mixed-Effects Model (LMM) (T008g) as primary method per FR-005.
 2. **Catch InfeasibleError**: If LMM fails (singularity/data insufficiency), fallback to Fixed-Effects GLM (T008b).
 3. **Normality Check**: If LMM/GLM succeeds, check normality of paired differences -> Wilcoxon/t-test (T008c).
 4. **Fallback**: If GLM fails -> Domain-Stratified Analysis (T008d).
 - **Pairing**: Must call `pair_episodes()` (T008f-exec) to ensure paired comparison of Gatekeeper vs Baseline scores. **Input: List of Dicts with keys [episode_id, score, method].**
 - **Output Schema**: Dict with keys `[method_used, p_value, test_statistic, fallback_reason]`.
 - **Dependency**: T008a, T008b, T008c, T008d, T008g, **T008f-exec**, T023. **No [P] tag**.
 - **Verification**: `pytest tests/unit/test_stats.py::test_statistical_comparison_returns_dict`.
- [ ] T026b [US2] [DEPENDS ON T008f-exec] [P] [US2] Implement primary statistical validation for binary outcomes:
 - Implement `run_mcnemar_test()` function for paired binary outcomes (Access Control only) as the **Primary** test per Plan Summary and Complexity Tracking.
 - **Output**: Dict with keys `[test_statistic, p_value, method]`.
 - **Dependency**: **T008f-exec**.
 - **Verification**: `pytest tests/unit/test_stats.py::test_mcnemar_test_returns_dict`.
- [ ] T027 [US2] Implement `src/cli/run_evaluation.py` logic: Execute US2 pipeline on `--domain education,household` using existing CLI skeleton
- [ ] T028a [US2] [DEPENDS ON T023] Implement `src/cli/run_evaluation.py` logic:
 - Generate individual result files for Utility, Conditional Utility, Forgetting, etc.
 - **Note**: T023 already produces unified_metrics.json; this task extracts subsets if needed for reporting.
- [ ] T028b [US2] [DEPENDS ON T028a] Implement `src/cli/run_evaluation.py` logic:
 - Aggregate individual metric results into `data/processed/combined_metrics.json`.
 - **Requirement**: Must merge all metric outputs into a single JSON file keyed by `episode_id` to enable downstream sampling and statistical pairing.
 - **Dependency**: T028a.
- [ ] T029a [US2] [DEPENDS ON T023] [P] [US2] Implement failure case sampling logic:
 - Select a sample of cases with a **fixed random seed (42)**.
 - **Logic**: Filter results from `data/processed/unified_metrics.json` for failures (False Positive + False Negative + Forgetting Violations).
 - **Definition**: 'False Positive' = valid query blocked; 'False Negative' = leak allowed; **'Forgetting Violation' = deletion_request=True AND deletion_success=False**.
 - If **total failure count** N > 50, use `random.seed(42)` and `random.sample` with **stratification by domain** (ensure proportional representation). If N <= 50, use **simple random sample** (select all).
 - Output to `data/samples/failure_cases.json`.
 - **If a small number of failures exist, output all available. If zero failures exist, create an empty file and log a warning.**
 - **Dependency**: T023.
 - **Verification**: `pytest tests/unit/test_failure_sampling.py::test_sampling_logic_stratified` and `pytest tests/unit/test_failure_sampling.py::test_sampling_logic_seed_42`.
- [ ] T029b [US2] [DEPENDS ON T029a] [P] [US2] Create unit test for failure case sampling:
 - File: `tests/unit/test_failure_sampling.py`
 - Assertion: Verify `data/samples/failure_cases.json` exists, contains correct count (N or 50), and is stratified correctly if N > 50.
 - **Verification**: `pytest tests/unit/test_failure_sampling.py::test_sampling_logic`.

### Tests for User Story 2 (Post-Implementation)

- [ ] T021 [US2] Contract test: Verify `data/processed/utility_results.json` contains `conditional_utility` and `overall_success` fields
 - File: `tests/contract/test_utility_results.py`
 - Assertion: `assert validate_results(data/processed/utility_results.json, "results.schema.yaml")`
- [ ] T022 [US2] Integration test: Run pipeline on "education" domain and assert Utility score matches expected range against ground truth
 - File: `tests/integration/test_us2_education_domain.py`
 - Assertion: `assert 0.0 <= utility_score <= 1.0`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

**⚠️ NOTE**: T026a (Statistical Comparison) CANNOT run in parallel with T023/T024 (Metric Calculation) as it depends on their output.

---

## Phase 5: User Story 3 - Profile Computational Cost and Latency (Priority: P3)

**Goal**: Measure wall-clock inference time and peak CPU/RAM usage to verify computational cost reduction.

**Independent Test**: Execute pipeline with instrumentation; verify logs contain peak RAM (MB) and wall-clock time for both configurations.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Integrate `src/utils/profiling.py` into `src/gatekeeper/pipeline.py` to log start/end times and peak memory for each episode
- [ ] T033a [US3] [DEPENDS ON T006, T009, T007] Implement `src/gatekeeper/pipeline.py` logic: Run Baseline (Long-Context) with profiling enabled
 - **Constraint**: Must use `src/utils/profiling.py` (T007) to ensure `latency_ms` and `peak_ram_mb` keys match Gatekeeper output.
- [ ] T034 [US3] Implement `src/gatekeeper/pipeline.py` logic: Run Gatekeeper with profiling enabled
 - **Constraint**: Must use `src/utils/profiling.py` (T007) to ensure `latency_ms` and `peak_ram_mb` keys match Baseline output.
- [ ] T035 [US3] Implement `src/cli/run_evaluation.py` logic:
 - Aggregate profiling data from Gatekeeper and Baseline runs into a comparative JSON structure (`data/processed/performance_comparison.json`).
 - **Calculate percentage reduction** in latency and RAM for Gatekeeper vs Baseline. **Handle negative reductions explicitly**: If Gatekeeper is slower, report as "increase" or negative percentage to avoid misinterpretation.
 - **Output**: Must produce a specific comparative JSON structure with keys `[method, latency_ms, peak_ram_mb, latency_reduction_pct, ram_reduction_pct]` to be consumed by T036.
 - Output aggregated data to `data/processed/performance_results.json`.
- [ ] T036 [US3] Create final report generator:
 - Create `src/cli/generate_report.py` script.
 - Output `data/results/final_benchmark_report.md`.
 - Include sections: Access Control, Utility, Forgetting, Cost.
 - Include tables with headers: Method, Score, StdDev, **Test Statistic**, **P-Value**, **Method Used (LMM/GLM/Fallback/McNemar's)**, Latency (ms), RAM (MB).
 - **Conditional Logic**: If method is parametric (t-test/GLM), include **Degrees of Freedom**. If non-parametric (Wilcoxon), include **N (sample size)**. If McNemar's, include **Chi-Square Statistic**.
 - Use `tabulate` library for formatting; round floating-point numbers to a standard level of precision.
 - Reference `contracts/results.schema.yaml` for formatting.
 - **Verification**: `pytest tests/integration/test_report_generation.py`.

### Tests for User Story 3 (Post-Implementation)

- [ ] T030 [US3] Contract test: Verify `data/processed/performance_results.json` contains `latency_ms` and `peak_ram_mb` fields
 - File: `tests/contract/test_performance_results.py`
 - Assertion: `assert validate_results(data/processed/performance_results.json, "results.schema.yaml")`
- [ ] T031 [US3] Integration test: Run pipeline on small subset and assert resource logs are generated and non-zero
 - File: `tests/integration/test_us3_small_subset.py`
 - Assertion: `assert peak_ram_mb > 0 and latency_ms > 0`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T037 [P] Documentation: Update `quickstart.md` with instructions to run the full benchmark suite
- [ ] T038 Code cleanup: Refactor imports and ensure type hinting in `src/` modules
- [ ] T039 [P] Security: Run PII scan on `data/raw/` and `data/processed/` artifacts
- [ ] T040 [P] Run `pytest` for all unit, integration, and contract tests
- [ ] T041 Validate `data/results/final_benchmark_report.md` against `contracts/results.schema.yaml`
- [ ] T042 [P] Add `tests/contract/test_failure_cases.py` to verify schema and count of `data/samples/failure_cases.json`.
 - Verify `data/samples/failure_cases.json` contains exactly 50 entries (or N if N<50). **N is defined as the total count of identified failure cases (False Positives + False Negatives + Forgetting Violations) from the results JSON.** **If N > 50, verify entries are stratified by domain.** Ensure a fixed random seed was used.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Uses `metrics.py` and `stats.py` from Foundation
- **User Story 3 (P3)**: Can start after Foundational - Uses `profiling.py` from Foundation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (or run after implementation to verify)
- Models/Utilities before pipeline logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T006a-c, T007, T008a-d, T008g) can run in parallel (within Phase 2) **BUT** T006d and T008e must wait for their components. T008f is [DEF].
- All user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **WARNING**: In Phase 4, T026a (Statistical Comparison) CANNOT run in parallel with T023/T024 (Metric Calculation) as it depends on their outputs.

### Parallel Example: User Story 1

```bash
# Launch all models/utilities for User Story 1 together:
Task: "Implement src/gatekeeper/classifiers.py: Load Zero-Shot DistilBERT Intent Classifier"
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
- [DEF] tasks = function definitions that cannot be executed until later phases (e.g., T008f)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Constraint**: All models must run on CPU-only (DistilBERT Zero-Shot); no low-bit quantization or CUDA usage.
- **Constraint**: Dataset must be processed in batches or streamed to fit available RAM.
- **Constraint**: Random seeds fixed to ensure reproducibility.
- **Statistical Fallback**: Primary method is LMM (FR-005). If infeasible, use Fixed-Effects GLM. If GLM fails, use Domain-Stratified Analysis. Normality checks determine post-hoc test (t-test/Wilcoxon). **McNemar's Test is the Primary test for binary outcomes (Access Control)**.
- **Critical Dependency**: T016 requires T014a and T015a completion. T026a requires T023, T008f-exec. T006 requires T004/T005/T006a-d. T008 requires T008a-g. T017/T027/T033 require T006.
- **Data Integrity**: **T006a/b/c/d** include strict fail-loud, streaming, and checksum logic. Synthetic fallbacks are strictly prohibited.
- **Plan Note**: The Plan Summary (plan.md) has been corrected to state "Fixed-Effects GLM" as secondary, with LMM as primary (attempt first, fallback if invalid).
- **Prompt Integrity**: T043 ensures prompt consistency across Gatekeeper and Baselines, a prerequisite for valid comparison (FR-003).