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

- [X] T001 Create project structure per implementation plan:
 - `src/gatekeeper/`, `src/utils/`, `src/cli/` (with `__init__.py` in each)
 - `tests/contract/`, `tests/integration/`, `tests/unit/`
 - `data/raw/`, `data/processed/`, `data/samples/`
 - `contracts/`, `state/`, `logs/`
 - `templates/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` at repository root:
 - Generate file using `pip freeze > requirements.txt` or manually list packages.
 - Pin specific versions (e.g., `datasets==2.14.0`, `transformers==4.35.0`) to ensure reproducibility.
 - Include: `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T037a [P] Create `quickstart.md` with initial project setup instructions, dataset download guide, and basic run commands. **Deliverable**: A markdown file in `docs/` or root containing step-by-step instructions for environment setup, dataset fetching, and running the first evaluation. **Dependency**: None. **Verification**: `pytest tests/unit/test_docs.py::test_quickstart_exists`.

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
- [ ] T006a [FR-001] Create `src/utils/data_loader.py` function `fetch_dataset()`:
 - Fetch GateMem dataset from HuggingFace ID `gatekeeper/gatemem` using `config='default'` and `split='test'` with `streaming=True` to handle memory constraints.
 - **Strictly NO synthetic fallback**. If fetch fails (network error, missing file), raise `ConnectionError` immediately and exit with code 1. Log "Critical: Real Data Fetch Failed". **Rationale**: Constitution Principle I (Reproducibility) requires failure on missing data, not substitution.
 - **Checksumming**: Upon successful download, compute SHA256 checksum and write to `state/artifact_hashes.yaml` under key `gatemem_test`.
 - **Dependency**: None.
 - **Verification**: `pytest tests/unit/test_data_loader.py::test_fetch_streaming`.
- [ ] T006b [P] [FR-001] Create `src/utils/data_loader.py` function `parse_jsonl()`:
 - Parse JSONL files into episode dictionaries.
 - Handle malformed JSON by logging the line number and skipping the line (recoverable). Do NOT exit.
 - **Dependency**: None.
- [ ] T006c [P] [FR-001] Create `src/utils/data_loader.py` function `extract_fields()`:
 - Explicitly extract and load fields: `outcome`, `predictors`, `covariates`, `leak-target`, `roles`, `domains`.
 - Raise `ValueError` if any *required* field is missing from an episode.
 - **Dependency**: None.
- [ ] T006d [P] [FR-001] Create `src/utils/data_loader.py` function `validate_episode()`:
 - Validate presence of `outcome`, `predictors`, `covariates`, `leak-target` against `contracts/dataset.schema.yaml`.
 - **Logic**: If field missing -> Raise `ValueError` with message "Missing required field: {field}". If `leak-target` ambiguous -> Log "validation error" and exclude episode (per T006b logic).
 - **Checksum Verification**: Must verify the checksum in `state/artifact_hashes.yaml` matches the raw data before processing. If mismatch, raise `ValueError`.
 - **Dependency**: T004, T005, T006a, T006b, T006c.
- [ ] T007 [P] Create `src/utils/profiling.py` for CPU/RAM and wall-clock time instrumentation (using `tracemalloc` or `psutil`):
 - Implement `profile_execution()` function returning a dict with standardized keys: `{'latency_ms': float, 'peak_ram_mb': float}`.
 - **Standardization**: All profiling tasks MUST use this function to ensure identical output keys for Gatekeeper and Baselines.
 - **Verification**: `pytest tests/unit/test_profiling.py::test_profile_execution_returns_dict`.
- [ ] T008a [FR-005] Create `src/utils/stats.py` function `shapiro_wilk_test()`:
 - Implement Shapiro-Wilk normality test (α=0.05).
 - **Artifact**: Produces `normality_results` dict for T026.
 - **Verification**: `pytest tests/unit/test_stats.py::test_shapiro_wilk_returns_p_value`.
- [ ] T008b [FR-005] Create `src/utils/stats.py` function `fit_lmm()`:
 - Implement Linear Mixed-Effects Model (LMM) using `statsmodels` with formula `score ~ method + (1|Domain)`. **Explicitly state 'Domain' is the ONLY random intercept**.
 - **Constraint**: Do NOT include `Episode_ID` in the random intercept formula.
 - **Fallback Logic**: If LMM fails due to insufficient data (not singularity), raise `InfeasibleError`. **DO NOT** fallback on `SingularMatrixError` alone; attempt regularization or data checks first.
 - **Artifact**: Produces `lmm_results` dict for T026.
 - **Verification**: `pytest tests/unit/test_stats.py::test_fit_lmm_returns_dict`.
- [ ] T008c [FR-005] Create `src/utils/stats.py` function `run_post_hoc()`:
 - Implement test selection logic: Use Shapiro-Wilk result to choose between parametric (t-test) or non-parametric (Wilcoxon) post-hoc tests.
 - **Artifact**: Produces `post_hoc_results` dict for T026.
 - **Verification**: `pytest tests/unit/test_stats.py::test_run_post_hoc_returns_dict`.
- [ ] T008d [FR-005] Create `src/utils/stats.py` function `domain_stratified_analysis()`:
 - Implement domain-stratified analysis with aggregation method (average p-values).
 - **Usage**: Only if LMM is infeasible (per FR-005).
 - **Artifact**: Produces `stratified_results` dict for T026.
 - **Verification**: `pytest tests/unit/test_stats.py::test_domain_stratified_analysis_returns_dict`.
- [ ] T008e [FR-005] Create `src/utils/stats.py` function `run_full_stats_pipeline()`:
 - Implement orchestration logic returning a dict with keys: `[method_used, p_value, test_statistic, fallback_reason]`.
 - **Fallback Priority**: 1. LMM. 2. Normality Check (Shapiro-Wilk) -> Wilcoxon/t-test. 3. Feasibility Check -> Domain-Stratified Analysis.
 - **Dependency**: T008a, T008b, T008c, T008d.
 - **Verification**: `pytest tests/unit/test_stats.py::test_full_stats_pipeline_returns_dict`.
- [ ] T008f [FR-005] Create `src/utils/stats.py` function `pair_episodes()`:
 - Implement logic to match episodes across Gatekeeper and Baseline conditions using `episode_id`.
 - **Requirement**: Input must be two lists of results (Gatekeeper, Baseline) with matching `episode_id` keys. Output must be a paired list of tuples `(gatekeeper_score, baseline_score)`.
 - **Constraint**: If `episode_id` is missing or mismatched, raise `ValueError`.
 - **Artifact**: Produces `paired_data` list for T026a.
 - **Verification**: `pytest tests/unit/test_stats.py::test_pair_episodes_returns_pairs`.
- [ ] T009 [P] Create `src/gatekeeper/pipeline.py` skeleton with entry points: `run_gatekeeper()`, `run_baseline()`, and `main()` for argument parsing
- [ ] T015a [FR-002] Create `src/gatekeeper/rules.py` with regex-based rule engine for role validation and deletion log checking:
 - Implement specific regex patterns for role validation (e.g., `r"role:\s*(\w+)"`) and deletion log checking.
 - **Dependency**: None.
- [ ] T015b [FR-002] Modify `src/gatekeeper/rules.py` to add anomaly handling:
 - Handle malformed deletion log entries by defaulting to 'deny'.
 - Log anomaly to `logs/deletion_errors.log`.
 - **Dependency**: Must run after T015a.
- [ ] T014a [FR-002] [US-1] Create `src/gatekeeper/classifiers.py`:
 - Load frozen DistilBERT intent classifier (Model ID: `distilbert-base-uncased-finetuned-sst-2-english` as a fallback for intent classification if a specific GateMem model is unavailable). **Explicitly enforce CPU execution**: Set `device='cpu'` and `torch.set_default_device('cpu')`. Verify `torch.cuda.is_available()` is False or ignored; do not attempt to move model to CUDA.
 - Implement `run_inference()` function returning `{'inference_time_ms': float, 'peak_ram_mb': float}`.
 - **Profiling Standardization**: Must use `src/utils/profiling.py` (T007) to generate these values to ensure consistent keys.
 - **Retry Logic**: If model load fails (cache corruption), retry once. If retry fails, exit with code 1 and log "Critical: Model Unavailable".
 - **Acceptance Criteria**: Verify the model runs on CPU-only runner (no CUDA, memory within constrained limits) and logs resource usage. **This verification must pass before T016 can proceed.**
 - **Dependency**: None (Independent of T015a).
 - **Verification**: `pytest tests/unit/test_classifier.py::test_cpu_only_enforcement`.
- [X] T010 [P] Create `tests/contract/test_dataset_schema.py` to validate raw data against `dataset.schema.yaml`
- [X] T011 [P] Create `tests/contract/test_results_schema.py` to validate output against `results.schema.yaml`
- [X] T001b Create `data/samples/` directory structure (if not created by T001).
- [X] T001c Create `logs/` directory structure (if not created by T001).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1) 🎯 MVP

**Goal**: Execute Gatekeeper and Baseline pipelines to measure unauthorized information leakage rates.

**Independent Test**: Run automated evaluation on "medical" and "office" domains; verify Access Control scores are output for both configurations.

### Implementation for User Story 1

- [ ] T016 [US1] [DEPENDS ON T006, T009, T014a, T015a] [FR-002] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement `run_gatekeeper_episode()` function: Filter memory access using Classifier (T014a) + Rules (T015a) (AND logic) before LLM step.
 - **Prompt Templates**: Must load prompt templates from `templates/prompts.yaml` to ensure identical templates with baselines.
 - Reference `contracts/dataset.schema.yaml` for data structure.
 - **Dependency**: T006 (data loading), T009 (skeleton), T014a (classifier), T015a (rules).
 - **Verification**: `pytest tests/integration/test_us1_medical_domain.py`.
- [ ] T017a [US1] [DEPENDS ON T006, T009] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Retrieval-only" baseline execution path.
 - **Enforce identical prompt templates**: Load from `templates/prompts.yaml`.
 - **Enforce identical retrieval parameters, and random seeds** as defined in FR-003 and T016 configuration.
 - **Profiling**: Must use `src/utils/profiling.py` (T007) to log `latency_ms` and `peak_ram_mb` with standardized keys.
 - Create or reference `templates/prompts.yaml` if not existing.
 - **Dependency**: T006, T009.
- [ ] T017b [US1] [DEPENDS ON T006, T009] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Long-Context" baseline execution path.
 - **Enforce identical prompt templates**: Load from `templates/prompts.yaml`.
 - **Enforce identical retrieval parameters, and random seeds**.
 - **Profiling**: Must use `src/utils/profiling.py` (T007) to log `latency_ms` and `peak_ram_mb` with standardized keys.
 - **Dependency**: T006, T009.
- [ ] T017c [US1] [DEPENDS ON T017a, T017b] [FR-003] Implement `src/gatekeeper/pipeline.py` logic:
 - Manage prompt templates and random seeds globally.
 - Output `data/processed/baseline_results.json` with keys: `[method, score, std_dev, latency_ms, peak_ram_mb, episode_id]`.
 - **Explicitly write code to generate this file** and validate output against `contracts/results.schema.yaml`.
 - **Dependency**: T017a, T017b.
 - **Verification**: `pytest tests/contract/test_baseline_results.py`.
- [ ] T018 [US1] [FR-004] Implement `src/gatekeeper/metrics.py` function: `calculate_access_control()`:
 - Calculate Access Control score (unauthorized exposure rate) against ground truth.
 - **Verification**: `pytest tests/unit/test_metrics.py::test_access_control_calculation`.
- [ ] T019 [US1] Implement `src/cli/run_evaluation.py` logic:
 - Execute US1 pipeline with `--domains medical,office` (and support for any domain).
 - Implement generalizable argument parser accepting `--domains` as a comma-separated list.
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

- [ ] T023 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_utility()`:
 - Calculate Utility (task success rate against human-annotated ground truth).
 - **Output**: Must include `episode_id` for pairing.
- [ ] T024 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_forgetting()`:
 - Calculate Forgetting (deletion compliance rate for deletion request episodes).
 - **Output**: Must include `episode_id` for pairing.
- [ ] T024c [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_overall_success()`:
 - Calculate 'Overall Task Success Rate' (net success including False Positives) - **Supporting Metric**
 - **Output**: Must include `episode_id` for pairing.
- [ ] T025 [P] [US2] Implement `src/gatekeeper/metrics.py` function: `calculate_fp_fn()`:
 - Calculate False Positive (valid query blocked) and False Negative (leak allowed) rates - **Supporting Metric**
 - **Output**: Must include `episode_id` for pairing.
- [ ] T026a [US2] [DEPENDS ON T008a, T008b, T008c, T008d, T008e, T008f, T023, T024, T024c, T025] [P] [US2] Implement `src/utils/stats.py` integration:
 - Implement `run_statistical_comparison()` function:
 1. **First**: Attempt LMM (T008b).
 2. **Check Normality**: If Shapiro-Wilk fails -> Wilcoxon/t-test (T008c).
 3. **Check Feasibility**: If LMM infeasible (data insufficiency) -> Domain-stratified analysis (T008d).
 4. **DO NOT** fallback on `SingularMatrixError` alone; attempt regularization first.
 - **Pairing**: Must call `pair_episodes()` (T008f) to ensure paired comparison of Gatekeeper vs Baseline scores.
 - Implement domain-stratified analysis with aggregation (average p-values).
 - **Output Schema**: Dict with keys `[method_used, p_value, test_statistic, fallback_reason]`.
 - **Dependency**: T008a, T008b, T008c, T008d, T008e, T008f, T023, T024, T024c, T025.
 - **Verification**: `pytest tests/unit/test_stats.py::test_statistical_comparison_returns_dict`.
- [ ] T026b [US2] [DEPENDS ON T026a] [P] [US2] Verify statistical pipeline produces correct output format.
- [ ] T027 [US2] Implement `src/cli/run_evaluation.py` logic: Execute US2 pipeline on `--domain education,household` using existing CLI skeleton
- [ ] T028a [US2] [DEPENDS ON T023, T024, T024c, T025] Implement `src/cli/run_evaluation.py` logic:
 - Generate individual result files for Utility, Forgetting, etc.
- [ ] T028b [US2] [DEPENDS ON T028a] Implement `src/cli/run_evaluation.py` logic:
 - Aggregate individual metric results into `data/processed/combined_metrics.json`.
 - **Requirement**: Must merge all metric outputs into a single JSON file keyed by `episode_id` to enable downstream sampling and statistical pairing.
 - **Dependency**: T028a.
- [ ] T029a [US2] [DEPENDS ON T028b] [P] [US2] Implement failure case sampling logic:
 - Select a sample of cases (stratified by domain and failure_type) with a fixed random seed.
 - **Logic**: Filter results from `data/processed/combined_metrics.json` for failures (False Positive + False Negative + Forgetting Violations).
 - **Definition**: 'False Positive' = valid query blocked; 'False Negative' = leak allowed; 'Forgetting Violation' = deletion compliance < 100% (per FR-007).
 - If **total failure count** N > 50, use `random.sample` with stratification by domain (ensure proportional representation). If N <= 50, use simple random sampling (select all).
 - Output to `data/samples/failure_cases.json`.
 - **If a small number of failures exist, output all available. If zero failures exist, create an empty file and log a warning.**
 - **Dependency**: T023, T024, T024c, T025, T028b.
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

**⚠️ NOTE**: T026a (Statistical Comparison) CANNOT run in parallel with T024 (Forgetting Calculation) as it depends on its output.

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
 - Aggregate profiling data from Gatekeeper and Baseline runs.
 - **Calculate percentage reduction** in latency and RAM for Gatekeeper vs Baseline.
 - Output aggregated data to `data/processed/performance_results.json`.
- [ ] T036 [US3] Create final report generator:
 - Create `src/cli/generate_report.py` script.
 - Output `data/results/final_benchmark_report.md`.
 - Include sections: Access Control, Utility, Forgetting, Cost.
 - Include tables with headers: Method, Score, StdDev, **Test Statistic**, **P-Value**, **Method Used (LMM/Fallback)**, Latency (ms), RAM (MB).
 - **Conditional Logic**: If method is parametric (t-test/LMM), include **Degrees of Freedom**. If non-parametric (Wilcoxon), include **N (sample size)** instead.
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
- All Foundational tasks marked [P] (T004, T005, T006a-d, T007, T008a-f) can run in parallel (within Phase 2) **BUT** T006 and T008 must wait for their components.
- All user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **WARNING**: In Phase 4, T026a (Statistical Comparison) CANNOT run in parallel with T024 (Forgetting Calculation) or T023 (Utility) as it depends on their outputs.

### Parallel Example: User Story 1

```bash
# Launch all models/utilities for User Story 1 together:
Task: "Implement src/gatekeeper/classifiers.py: Load frozen DistilBERT intent classifier"
Task: "Implement src/gatekeeper/rules.py: Implement regex-based rule engine"
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
- **Constraint**: All models must run on CPU-only (DistilBERT default precision); no low-bit quantization or CUDA usage.
- **Constraint**: Dataset must be processed in batches or streamed to fit available RAM.
- **Constraint**: Random seeds fixed to ensure reproducibility.
- **Statistical Fallback**: If LMM fails (insufficient data) or normality fails, use paired t-tests or Wilcoxon signed-rank tests per Constitution Principle VI. **DO NOT** fallback on `SingularMatrixError` alone.
- **Critical Dependency**: T016 requires T014a and T015a completion. T026a requires T023, T024, T008f. T006 requires T004/T005/T006a-d. T008 requires T008a-f. T017/T027/T033 require T006.
- **Data Integrity**: **T006a/b/c/d** include strict fail-loud, streaming, and checksum logic. Synthetic fallbacks are strictly prohibited.
- **Plan Note**: The Plan Summary (plan.md) currently states "LMM with 'Episode ID' and 'Domain' as random intercepts". This contradicts Spec FR-005 which requires only 'Domain'. This is flagged for plan.md kickback to resolve the contradiction.