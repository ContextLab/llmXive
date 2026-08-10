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

- [X] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T037a [P] Create `quickstart.md` with initial project setup instructions, dataset download guide, and basic run commands. **Deliverable**: A markdown file in `docs/` or root containing step-by-step instructions for environment setup, dataset fetching, and running the first evaluation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading, stats logic, rule engine, and CLI skeleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `contracts/dataset.schema.yaml` defining GateMem episode structure (leak-target, roles, domains, outcome, authorization_boundaries). **Deliverable**: A valid YAML schema file.
- [ ] T005 [P] Create `contracts/results.schema.yaml` defining metric output structure (Access Control, Utility, Forgetting, Latency). **Deliverable**: A valid YAML schema file.
- [X] T010 [P] [DEPENDS ON T004] Create `tests/contract/test_dataset_schema.py` to validate raw data against `dataset.schema.yaml`. **Acceptance**: Test must fail if schema is missing or invalid.
- [X] T011 [P] [DEPENDS ON T005] Create `tests/contract/test_results_schema.py` to validate output against `results.schema.yaml`. **Acceptance**: Test must fail if schema is missing or invalid.
- [ ] T006 [US1/US2] Create `src/utils/data_loader.py` to download GateMem dataset from HuggingFace/Direct URL. **Acceptance**: Save raw JSONL to `data/raw/`, calculate SHA256 checksum, and record checksum in `state/projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc.yaml`. **Must fail loudly if download fails (no synthetic fallback).**
- [ ] T006b [US1/US2] [DEPENDS ON T006] Create function `load_dataset_schema()` in `src/utils/data_loader.py` to load `contracts/dataset.schema.yaml`.
- [ ] T006c [US1/US2] [DEPENDS ON T006b] Create function `validate_dataset_schema()` in `src/utils/data_loader.py`. This function MUST validate loaded data against schema. If missing fields, raise `ValueError` with message "Missing required field: {field_name}". **Acceptance**: Verify error handling for ambiguous `leak-target` by logging "validation error" and excluding from further processing.
- [ ] T006d [US1/US2] [DEPENDS ON T006c] Create function `extract_gatemem_features()` in `src/utils/data_loader.py`. This function MUST extract `leak-target` and `authorization_boundaries` from parsed JSONL and save to `data/processed/episodes.json`. **Acceptance**: Output JSON structure MUST be: `{"episodes": [{"id": str, "domain": str, "leak_target": str, "role": str, "outcome": str, "authorization_boundaries": dict,...}]}`.
- [ ] T007 [P] Create `src/utils/profiling.py` for CPU/RAM and wall-clock time instrumentation (using `tracemalloc` or `psutil`). **Deliverable**: Module with `ProfileContext` class and `log_metrics()` function.
- [ ] T008a [P] Create `src/utils/stats.py` with imports for `scipy.stats` and `statsmodels`.
- [ ] T008b [P] [DEPENDS ON T008a] Implement function `check_normality(data, alpha=0.05)` in `src/utils/stats.py` using `scipy.stats.shapiro`.
- [ ] T008c [P] [DEPENDS ON T008b] Implement function `select_statistical_test(data, method_col, group_col)` in `src/utils/stats.py`. Logic: 1. Run Shapiro-Wilk. 2. If p < 0.05 (non-normal), return 'wilcoxon'. 3. If p >= 0.05 (normal), attempt LMM (`score ~ method + (1|Domain)`). 4. If LMM fails (singular matrix), fallback to domain-stratified Wilcoxon signed-rank (loop over domains, aggregate p-values). **Do NOT use t-test.**
- [ ] T008d [P] [DEPENDS ON T008c] Implement function `fit_lmm(data, formula)` in `src/utils/stats.py` using `statsmodels.formula.api.mixedlm` with 'Domain' as random intercept. Extract p-value and statistic.
- [ ] T009 [P] Create `src/gatekeeper/pipeline.py` skeleton with entry points: `run_gatekeeper()`, `run_baseline()`, and `main()` for argument parsing.
- [ ] T009b [P] [DEPENDS ON T004, T005] Create `src/gatekeeper/pipeline.py` logic to load and validate schemas from `contracts/` at startup.
- [ ] T014a [US1] [DEPENDS ON T006d] Create `src/gatekeeper/classifiers.py`: Load frozen DistilBERT intent classifier (CPU-only, default precision) and implement `predict_intent()` wrapper. **Acceptance Criteria**: Verify the model runs on CPU-only runner (no CUDA) using `tracemalloc` to measure peak RAM for the **total process lifetime**; log result to `logs/memory_profile.log`. **Assert peak memory < 7GB; fail task if exceeded.**
- [ ] T014b [P] [US1/US2] Create `templates/prompts.yaml` containing identical prompt templates for Gatekeeper and Baseline runs. Implement function `load_prompts()` to verify templates are identical for both configurations.
- [ ] T014c [P] [US1/US2] Create function `verify_template_identity()` in `src/gatekeeper/pipeline.py`. This function MUST load `templates/prompts.yaml` and assert that the prompt strings for Gatekeeper and Baseline are byte-for-byte identical. **Acceptance**: Raise `ValueError` if templates differ.
- [ ] T014d [P] Create `templates/report_template.md` with placeholders for: Method, Score, StdDev, Test Statistic, Degrees of Freedom, Method Used (LMM/Fallback), P-Value, Latency (ms), RAM (MB), and a narrative section for Cost Reduction Hypothesis. **Deliverable**: A markdown file with clearly marked placeholders.
- [ ] T014e [P] Create `src/utils/sampling.py` with placeholder functions for failure case sampling.
- [ ] T015a [P] Create `src/gatekeeper/rules.py` with regex-based rule engine for role validation and deletion log checking.
- [ ] T015b [P] Extend `src/gatekeeper/rules.py` to implement function `handle_malformed_deletion(entry)`. This function MUST default to 'deny' for malformed entries, log the anomaly to `logs/deletion_errors.log`, and handle ambiguous `leak-target` by logging "validation error" and excluding from calculation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1) 🎯 MVP

**Goal**: Execute Gatekeeper and Baseline pipelines to measure unauthorized information leakage rates.

**Independent Test**: Run automated evaluation on "medical" and "office" domains; verify Access Control scores are output for both configurations.

### Tests for User Story 1

- [ ] T012 [P] [US1] Contract test: Verify `data/processed/access_control_results.json` matches `results.schema.yaml`
- [ ] T013 [P] [US1] Integration test: Run full pipeline on "medical" domain subset and assert Access Control score is calculated

### Implementation for User Story 1

- [ ] T016 [US1] [DEPENDS ON T014a, T015a, T014b, T014c] Implement `src/gatekeeper/pipeline.py` logic: Filter memory access using Classifier + Rules (AND logic) before LLM step, referencing `contracts/dataset.schema.yaml` for data structure and `templates/prompts.yaml` for prompts.
- [ ] T017 [US1] [DEPENDS ON T014b, T014c] Implement `src/gatekeeper/pipeline.py` logic: "Retrieval-only" and "Long-Context" baseline execution paths using the SAME templates/parameters defined in `templates/prompts.yaml` as the Gatekeeper; output `data/processed/baseline_results.json`. **Acceptance Criteria**: Verify that prompt templates and retrieval parameters are IDENTICAL to the Gatekeeper run by comparing loaded templates.
- [ ] T018 [US1] Implement `src/gatekeeper/metrics.py` function: Calculate Access Control score (unauthorized exposure rate) against ground truth
- [ ] T019 [US1] Implement `src/cli/run_evaluation.py` logic: Execute US1 pipeline with `--domain medical,office` using existing CLI skeleton

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Gatekeeper vs. Baseline on Task Utility (Priority: P2)

**Goal**: Measure task success rates (Utility) and Forgetting compliance to ensure security filters do not degrade performance.

**Independent Test**: Run evaluation on "education" and "household" domains; verify Utility and Forgetting scores are calculated and compared against baselines.

### Tests for User Story 2

- [ ] T021 [P] [US2] Contract test: Verify `data/processed/utility_results.json` contains `conditional_utility` and `overall_success` fields
- [ ] T022 [P] [US2] Integration test: Run pipeline on "education" domain and assert Utility score matches expected range against ground truth

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `src/gatekeeper/metrics.py` function: Calculate Utility (task success rate against human-annotated ground truth)
- [ ] T024 [P] [US2] Implement `src/gatekeeper/metrics.py` function: Calculate Forgetting (deletion compliance rate for deletion request episodes)
- [ ] T025 [US2] Implement `src/gatekeeper/metrics.py` function: Calculate False Positive (valid query blocked) and False Negative (leak allowed) rates
- [ ] T026a [US2] [DEPENDS ON T008a, T008b, T008c, T008d] Implement `src/cli/run_evaluation.py` logic: Execute statistical comparison using `select_statistical_test` and `fit_lmm` from T008b/d.
- [ ] T026b [US2] [DEPENDS ON T008d] Implement `src/cli/run_evaluation.py` logic: Generate paired comparison table (Gatekeeper vs Baseline) for Utility and Forgetting using the test selected in T026a.
- [ ] T027 [US2] Implement `src/cli/run_evaluation.py` logic: Execute US2 pipeline on `--domain education,household` using existing CLI skeleton
- [ ] T029 [US1/US2] [DEPENDS ON T018, T023, T024, T014e] Implement function `sample_failure_cases()` in `src/utils/sampling.py`. Logic: Select failure cases (False Positive, False Negative, **Forgetting Violations**). If N > 50, **stratify by domain**; if N <= 50, simple random sample (seed=42). Output to `data/samples/failure_cases.json` with fields: `episode_id`, `domain`, `failure_type`. **If N=0, create empty file and log warning.** **Acceptance**: Verify stratification logic is enforced when N > 50.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Profile Computational Cost and Latency (Priority: P3)

**Goal**: Measure wall-clock inference time and peak CPU/RAM usage to verify computational cost reduction.

**Independent Test**: Execute pipeline with instrumentation; verify logs contain peak RAM (MB) and wall-clock time for both configurations.

### Tests for User Story 3

- [ ] T030 [P] [US3] Contract test: Verify `data/processed/performance_results.json` contains `latency_ms` and `peak_ram_mb` fields
- [ ] T031 [P] [US3] Integration test: Run pipeline on small subset and assert resource logs are generated and non-zero

### Implementation for User Story 3

- [ ] T032 [P] [US3] Integrate `src/utils/profiling.py` into `src/gatekeeper/pipeline.py` to log start/end times and peak memory for each episode
- [ ] T033 [US3] Implement `src/gatekeeper/pipeline.py` logic: Run Baseline (Long-Context) with profiling enabled
- [ ] T034 [US3] Implement `src/gatekeeper/pipeline.py` logic: Run Gatekeeper with profiling enabled
- [ ] T035a [US3] Implement `src/cli/run_evaluation.py` logic: Aggregate profiling data from Gatekeeper and Baseline runs.
- [ ] T035b [US3] [DEPENDS ON T035a] Implement `src/cli/run_evaluation.py` logic: Calculate and report the **percentage difference** (signed) in latency and RAM for Gatekeeper vs Baseline. Output to `data/results/cost_comparison.json`.
- [ ] T036 [US3] Create final report generator: Generate `data/results/final_benchmark_report.md` using `templates/report_template.md`. Format tables with headers: Method, Score, StdDev, Test Statistic, Degrees of Freedom, Method Used (LMM/Fallback), P-Value, Latency (ms), RAM (MB). **Include a narrative section explicitly citing the cost reduction hypothesis and reporting the calculated percentage difference.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T037b [P] Documentation: Update `quickstart.md` with final instructions to run the full benchmark suite, including dataset verification steps.
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
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses `metrics.py` and `stats.py` from Foundation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Uses `profiling.py` from Foundation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before pipeline logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test: Verify data/processed/access_control_results.json matches results.schema.yaml"
Task: "Integration test: Run full pipeline on 'medical' domain subset and assert Access Control score is calculated"

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
- **Constraint**: Dataset must be processed in batches to fit available RAM.
- **Constraint**: Random seeds fixed to ensure reproducibility.
- **Statistical Fallback**: If LMM fails (singular matrix) or data is flat, use domain-stratified Wilcoxon signed-rank tests per Constitution Principle VI. Normality check (Shapiro-Wilk) determines parametric vs non-parametric.
- **Critical Dependency**: T016 requires T014a completion. T026a/b requires T008a/b completion. T006d requires T006c. T008b requires T008a.