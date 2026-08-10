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
- [ ] T037a [P] Create `quickstart.md` with initial project setup instructions, dataset download guide, and basic run commands. **Deliverable**: A markdown file in `docs/` or root containing step-by-step instructions for environment setup, dataset fetching, and running the first evaluation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading, stats logic, rule engine, and CLI skeleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Generate `contracts/dataset.schema.yaml` defining GateMem episode structure:
 - Define keys: `leak-target`, `roles`, `domains`, `outcome`, `predictors`, `covariates`.
 - Specify types and required fields based on spec.md.
- [X] T004 [P] Validate `contracts/dataset.schema.yaml` exists and is syntactically correct (PyYAML).
- [X] T005a [P] Generate `contracts/results.schema.yaml` defining metric output structure:
 - Define keys: `Access Control`, `Utility`, `Forgetting`, `Latency`, `RAM`, `P-Value`, `Test Statistic`.
 - Specify types and required fields based on spec.md.
- [X] T005 [P] Validate `contracts/results.schema.yaml` exists and is syntactically correct.
- [ ] T006a [P] Create `src/utils/data_loader.py` function `fetch_dataset()`:
 - Fetch GateMem dataset from HuggingFace/Direct URL.
 - **Strictly NO synthetic fallback**. Raise `ConnectionError` if fetch fails.
- [ ] T006b [P] Create `src/utils/data_loader.py` function `parse_jsonl()`:
 - Parse JSONL files into episode dictionaries.
 - Handle malformed JSON by logging and skipping the line (recoverable).
- [ ] T006c [P] Create `src/utils/data_loader.py` function `extract_fields()`:
 - Explicitly extract and load fields: `outcome`, `predictors`, `covariates`, `leak-target`, `roles`, `domains`.
 - Raise `ValueError` if any *required* field is missing from an episode.
- [ ] T006 [DEPENDS ON T004, T005, T006a, T006b, T006c] Implement validation logic in `src/utils/data_loader.py`:
 - Implement function `validate_episode(episode, schema_path)` that validates presence of `outcome`, `predictors`, `covariates`, `leak-target` against `contracts/dataset.schema.yaml`.
 - **Logic**: If field missing -> Raise `ValueError` with message "Missing required field: {field}". If `leak-target` ambiguous -> Log "validation error" and exclude episode (per T006b logic).
 - **Dependency**: Must run after T004, T005, T006a, T006b, T006c.
- [ ] T007 [P] Create `src/utils/profiling.py` for CPU/RAM and wall-clock time instrumentation (using `tracemalloc` or `psutil`)
- [ ] T008a [P] Create `src/utils/stats.py` function `shapiro_wilk_test()`:
 - Implement Shapiro-Wilk normality test (α=0.05).
 - **Artifact**: Produces `normality_results` dict for T026.
- [ ] T008b [P] Create `src/utils/stats.py` function `fit_lmm()`:
 - Implement Linear Mixed-Effects Model (LMM) using `statsmodels` with formula `score ~ method + (1|Episode_ID) + (1|Domain)`.
 - **Fallback Logic**: If LMM fails due to insufficient data (not singularity), raise `InfeasibleError`. **DO NOT** fallback on `SingularMatrixError` alone; attempt regularization or data checks first.
 - **Artifact**: Produces `lmm_results` dict for T026.
- [ ] T008c [P] Create `src/utils/stats.py` function `run_post_hoc()`:
 - Implement test selection logic: Use Shapiro-Wilk result to choose between parametric (t-test) or non-parametric (Wilcoxon) post-hoc tests.
 - **Artifact**: Produces `post_hoc_results` dict for T026.
- [ ] T008d [P] Create `src/utils/stats.py` function `domain_stratified_analysis()`:
 - Implement domain-stratified analysis with aggregation method (average p-values).
 - **Usage**: Only if LMM is infeasible (per FR-005).
 - **Artifact**: Produces `stratified_results` dict for T026.
- [ ] T008 [DEPENDS ON T008a, T008b, T008c, T008d] [P] Assemble `src/utils/stats.py` orchestration logic:
 - Combine functions into a single pipeline.
 - **Artifact**: Produces `stats_artifact` consumed by T026.
- [X] T009 [P] Create `src/gatekeeper/pipeline.py` skeleton with entry points: `run_gatekeeper()`, `run_baseline()`, and `main()` for argument parsing
- [ ] T015a [P] Create `src/gatekeeper/rules.py` with regex-based rule engine for role validation and deletion log checking
- [ ] T015b [P] Modify `src/gatekeeper/rules.py` to add anomaly handling:
 - Handle malformed deletion log entries by defaulting to 'deny'.
 - Log anomaly to `logs/deletion_errors.log`.
 - **Dependency**: Must run after T015a.
- [ ] T014a [FR-002] [US-1] Create `src/gatekeeper/classifiers.py`:
 - Load frozen DistilBERT intent classifier (Model ID: `distilbert-base-uncased`).
 - **Explicitly enforce CPU execution**: Set `device='cpu'` and `torch.set_default_device('cpu')`. Verify `torch.cuda.is_available()` is False or ignored; do not attempt to move model to CUDA.
 - Implement `run_inference()` function returning `{'inference_time_ms': float, 'peak_ram_mb': float}`.
 - **Retry Logic**: If model load fails (cache corruption), retry once. If retry fails, exit with code 1 and log "Critical: Model Unavailable".
 - **Acceptance Criteria**: Verify the model runs on CPU-only runner (no CUDA, memory within constrained limits) and logs resource usage. **This verification must pass before T016 can proceed.**
- [X] T010 [P] Create `tests/contract/test_dataset_schema.py` to validate raw data against `dataset.schema.yaml`
- [X] T011 [P] Create `tests/contract/test_results_schema.py` to validate output against `results.schema.yaml`
- [X] T001b Create `data/samples/` directory structure (if not created by T001).
- [X] T001c Create `logs/` directory structure (if not created by T001).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 7: Execution & Data Integrity (Revision Pass)

**Purpose**: Address execution feedback regarding data loading, streaming, and error handling to prevent fabrication. **MUST run before Phase 3/4/5.**

- [ ] T043 [P] [US1/US2/US3] **Data Loading Hardening**: Refactor `src/utils/data_loader.py` to:
 - **Remove** any `try/except` blocks that fallback to `generate_synthetic_*()` or `mock_*()` functions.
 - Implement **fail-loud** behavior: if the real dataset fetch (HuggingFace or direct URL) fails, raise a `ConnectionError` or `FileNotFoundError` immediately and exit with code 1.
 - Ensure the script explicitly logs "Critical: Real Data Fetch Failed" before exiting.
 - **Differentiate Errors**: Distinguish between fatal fetch errors (exit 1) and recoverable episode errors (log and exclude, per T006b).
 - **Dependency**: Must be completed before any evaluation task (T017, T027, T033) can run.
- [ ] T044 [P] [US1/US2/US3] **Streaming Implementation**: Refactor `src/utils/data_loader.py` to:
 - Implement `streaming=True` logic using `datasets.load_dataset(..., streaming=True)`.
 - Process data in chunks to ensure memory usage stays < 7 GB.
 - Accumulate statistics online (e.g., running mean, variance) rather than storing the full dataset in RAM.
 - **Explicitly state** the streaming rule (e.g., "Stream all splits, chunk size fixed to a predetermined parameter.") in the code comments.
- [ ] T045 [P] [US1/US2/US3] **Resource Profiling Verification**: Update `src/utils/profiling.py` to:
 - Verify that `tracemalloc` is active before the pipeline starts.
 - Log peak memory usage to `data/processed/profile_logs.json` immediately after each episode.
 - Ensure the logging happens even if the episode fails, to capture the failure point's resource usage.
- [ ] T046 [P] [US1/US2/US3] **Random Seed Enforcement**: Add a global seed setter in `src/main.py`:
 - Set `random.seed(42)`, `numpy.random.seed(42)`, and `torch.manual_seed(42)` (if applicable) at the very start of execution.
 - Verify that all data loading and model inference steps respect this seed.

---

## Phase 3: User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1) 🎯 MVP

**Goal**: Execute Gatekeeper and Baseline pipelines to measure unauthorized information leakage rates.

**Independent Test**: Run automated evaluation on "medical" and "office" domains; verify Access Control scores are output for both configurations.

### Implementation for User Story 1

- [ ] T016 [US1] [DEPENDS ON T009, T014a, T015a] Implement `src/gatekeeper/pipeline.py` logic:
 - Filter memory access using Classifier + Rules (AND logic) before LLM step.
 - Reference `contracts/dataset.schema.yaml` for data structure.
- [ ] T017a [US1] [DEPENDS ON T006, T009] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Retrieval-only" baseline execution path.
 - **Enforce identical prompt templates, retrieval parameters, and random seeds** as defined in FR-003 and T016 configuration.
 - Create or reference `templates/prompts.yaml` if not existing.
- [ ] T017b [US1] [DEPENDS ON T006, T009] Implement `src/gatekeeper/pipeline.py` logic:
 - Implement "Long-Context" baseline execution path.
 - **Enforce identical prompt templates, retrieval parameters, and random seeds**.
- [ ] T017c [US1] [DEPENDS ON T017a, T017b] Implement `src/gatekeeper/pipeline.py` logic:
 - Manage prompt templates and random seeds globally.
 - Output `data/processed/baseline_results.json`.
- [ ] T018 [US1] Implement `src/gatekeeper/metrics.py` function: Calculate Access Control score (unauthorized exposure rate) against ground truth
- [ ] T019 [US1] Implement `src/cli/run_evaluation.py` logic:
 - Execute US1 pipeline with `--domains medical,office` (and support for any domain).
 - Implement generalizable argument parser accepting `--domains` as a comma-separated list.
- [ ] T020 [US1] Add error handling: Log "validation error" for ambiguous `leak-target` and exclude from calculation; handle model load retry logic

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

- [ ] T023 [P] [US2] Implement `src/gatekeeper/metrics.py` function: Calculate Utility (task success rate against human-annotated ground truth)
- [ ] T024 [P] [US2] Implement `src/gatekeeper/metrics.py` function: Calculate Forgetting (deletion compliance rate for deletion request episodes)
- [ ] T024c [P] [US2] Implement `src/gatekeeper/metrics.py` function: Calculate 'Overall Task Success Rate' (net success including False Positives) - **Supporting Metric**
- [ ] T025 [P] [US2] Implement `src/gatekeeper/metrics.py` function: Calculate False Positive (valid query blocked) and False Negative (leak allowed) rates - **Supporting Metric**
- [ ] T026a [US2] [DEPENDS ON T008a, T008b, T008c, T008d] Implement `src/utils/stats.py` integration:
 - Define LMM formula: `score ~ method + (1|Episode_ID) + (1|Domain)`.
 - Implement model fitting logic with **explicit fallback priority**:
 1. **First**: Attempt LMM.
 2. **Check Normality**: If Shapiro-Wilk fails -> Wilcoxon/t-test.
 3. **Check Feasibility**: If LMM infeasible (data insufficiency) -> Domain-stratified analysis.
 4. **DO NOT** fallback on `SingularMatrixError` alone; attempt regularization first.
 - Implement domain-stratified analysis with aggregation (average p-values).
- [ ] T026b [US2] [DEPENDS ON T026a] [P] [US2] Verify statistical pipeline produces correct output format.
- [ ] T027 [US2] Implement `src/cli/run_evaluation.py` logic: Execute US2 pipeline on `--domain education,household` using existing CLI skeleton
- [ ] T028 [US2] [DEPENDS ON T023, T024, T024c, T025, T026b] Implement `src/cli/run_evaluation.py` logic:
 - Generate paired comparison table (Gatekeeper vs Baseline) for Utility and Forgetting.
 - Ensure T023-25, T026b are completed before this runs.

### Tests for User Story 2 (Post-Implementation)

- [ ] T021 [US2] Contract test: Verify `data/processed/utility_results.json` contains `conditional_utility` and `overall_success` fields
 - File: `tests/contract/test_utility_results.py`
 - Assertion: `assert validate_results(data/processed/utility_results.json, "results.schema.yaml")`
- [ ] T022 [US2] Integration test: Run pipeline on "education" domain and assert Utility score matches expected range against ground truth
 - File: `tests/integration/test_us2_education_domain.py`
 - Assertion: `assert 0.0 <= utility_score <= 1.0`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Profile Computational Cost and Latency (Priority: P3)

**Goal**: Measure wall-clock inference time and peak CPU/RAM usage to verify computational cost reduction.

**Independent Test**: Execute pipeline with instrumentation; verify logs contain peak RAM (MB) and wall-clock time for both configurations.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Integrate `src/utils/profiling.py` into `src/gatekeeper/pipeline.py` to log start/end times and peak memory for each episode
- [ ] T033 [US3] [DEPENDS ON T043, T044] Implement `src/gatekeeper/pipeline.py` logic: Run Baseline (Long-Context) with profiling enabled
- [ ] T034 [US3] Implement `src/gatekeeper/pipeline.py` logic: Run Gatekeeper with profiling enabled
- [ ] T035 [US3] Implement `src/cli/run_evaluation.py` logic:
 - Aggregate profiling data from Gatekeeper and Baseline runs.
 - **Calculate percentage reduction** in latency and RAM for Gatekeeper vs Baseline.
 - Output aggregated data to `data/processed/performance_results.json`.
- [ ] T036 [US3] Create final report generator:
 - Output `data/results/final_benchmark_report.md`.
 - Include sections: Access Control, Utility, Forgetting, Cost.
 - Include tables with headers: Method, Score, StdDev, **Test Statistic**, **Degrees of Freedom**, **Method Used (LMM/Fallback)**, **P-Value**, Latency (ms), RAM (MB).
 - Use `tabulate` library for formatting; round floating-point numbers to a standard level of precision.
 - Reference `contracts/results.schema.yaml` for formatting.

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

- [ ] T029 [P] [US1/US2] Implement unified sampling logic for failure cases:
 - Select a sample of cases (stratified by domain and failure_type) with a fixed random seed.
 - **Logic**: If **total dataset** N > 50, use `sklearn.model_selection.train_test_split` with `stratify=`. If N <= 50, use simple random sampling.
 - **Failure Definition**: 'False Positive' = valid query blocked; 'False Negative' = leak allowed (per FR-007).
 - Output to `data/samples/failure_cases.json`.
 - **If a small number of failures exist, output all available. If zero failures exist, create an empty file and log a warning.**
- [ ] T037 [P] Documentation: Update `quickstart.md` with instructions to run the full benchmark suite
- [ ] T038 Code cleanup: Refactor imports and ensure type hinting in `src/` modules
- [ ] T039 [P] Security: Run PII scan on `data/raw/` and `data/processed/` artifacts
- [ ] T040 [P] Run `pytest` for all unit, integration, and contract tests
- [ ] T041 Validate `data/results/final_benchmark_report.md` against `contracts/results.schema.yaml`
- [ ] T042 Verify `data/samples/failure_cases.json` contains exactly 50 entries (or N if N<50). **N is defined as the total count of identified failure cases (False Positives + False Negatives + Forgetting Violations) from the results JSON.** **If N > 50, verify entries are stratified by domain.** Ensure a fixed random seed was used.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Integrity (Phase 7)**: **MUST run immediately after Phase 2**. Blocks Phases 3, 4, 5.
- **User Stories (Phase 3+)**: All depend on Foundational + Data Integrity completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Data Integrity - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational + Data Integrity - Uses `metrics.py` and `stats.py` from Foundation
- **User Story 3 (P3)**: Can start after Foundational + Data Integrity - Uses `profiling.py` from Foundation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (or run after implementation to verify)
- Models/Utilities before pipeline logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T006a, T006b, T006c, T007, T008a-d) can run in parallel (within Phase 2)
- All Phase 7 data integrity tasks can run in parallel
- Once Foundational + Phase 7 are done, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

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
3. **Complete Phase 7: Data Integrity** (Ensure no synthetic fallbacks, enable streaming)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (Access Control metric)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. **Complete Phase 7: Data Integrity** → Safe execution environment
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo (Utility/Forgetting)
5. Add User Story 3 → Test independently → Deploy/Demo (Cost profiling)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. **Team completes Phase 7 (Data Integrity) together** to ensure safety
3. Once Foundational + Phase 7 are done:
 - Developer A: User Story 1 (Access Control)
 - Developer B: User Story 2 (Utility/Forgetting)
 - Developer C: User Story 3 (Profiling)
4. Stories complete and integrate independently

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
- **Critical Dependency**: T016 requires T014a completion. T028 requires T026b completion. T006 requires T004/T005/T006a/T006b/T006c. T008 requires T008a-d. T017/T027/T033 require T043/T044.
- **Data Integrity**: **T043 and T044 are mandatory** before any data processing tasks. Synthetic fallbacks are strictly prohibited.