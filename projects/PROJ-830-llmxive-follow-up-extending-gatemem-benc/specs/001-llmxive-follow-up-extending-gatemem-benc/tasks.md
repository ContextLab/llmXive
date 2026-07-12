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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `datasets`, `transformers`, `scikit-learn`, `statsmodels`, `pandas`, `pyyaml`, `pytest`, `huggingface_hub`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading, stats logic, rule engine, and CLI skeleton.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `contracts/dataset.schema.yaml` defining GateMem episode structure (leak-target, roles, domains)
- [ ] T005 Implement `contracts/results.schema.yaml` defining metric output structure (Access Control, Utility, Forgetting, Latency)
- [ ] T006 [P] Create `src/utils/data_loader.py` with functions to fetch GateMem dataset from HuggingFace/Direct URL and parse JSONL
- [ ] T006b [US1/US2] [DEPENDS ON T006] Extend `src/utils/data_loader.py` to validate presence of required variables (`outcome`, `predictors`, `covariates`, `leak-target`) against `contracts/dataset.schema.yaml` and raise error if missing
- [ ] T007 [P] Create `src/utils/profiling.py` for CPU/RAM and wall-clock time instrumentation (using `tracemalloc` or `psutil`)
- [ ] T008a [P] Create `src/utils/stats.py` implementing Shapiro-Wilk, LMM (statsmodels) with formula `score ~ method + (1|Domain)`, and paired t-test/Wilcoxon fallback logic
- [ ] T008b [US2] [DEPENDS ON T008a] Extend `src/utils/stats.py` to implement 'domain-stratified analysis' (separate tests per domain) and automatic fallback to paired tests if LMM fails (singular matrix) per Constitution Principle VI
- [ ] T009 [P] Create `src/gatekeeper/pipeline.py` skeleton with entry points: `run_gatekeeper()`, `run_baseline()`, and `main()` for argument parsing
- [ ] T010 Create `tests/contract/test_dataset_schema.py` to validate raw data against `dataset.schema.yaml`
- [ ] T011 Create `tests/contract/test_results_schema.py` to validate output against `results.schema.yaml`
- [ ] T015a [P] Create `src/gatekeeper/rules.py` with regex-based rule engine for role validation and deletion log checking
- [ ] T015b [P] Extend `src/gatekeeper/rules.py` to handle malformed deletion log entries by defaulting to 'deny' and logging anomaly to `logs/deletion_errors.log`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Evaluate Gatekeeper vs. Baseline on Access Control (Priority: P1) 🎯 MVP

**Goal**: Execute Gatekeeper and Baseline pipelines to measure unauthorized information leakage rates.

**Independent Test**: Run automated evaluation on "medical" and "office" domains; verify Access Control scores are output for both configurations.

### Tests for User Story 1

- [ ] T012 [P] [US1] Contract test: Verify `data/processed/access_control_results.json` matches `results.schema.yaml`
- [ ] T013 [P] [US1] Integration test: Run full pipeline on "medical" domain subset and assert Access Control score is calculated

### Implementation for User Story 1

- [ ] T014a [P] [US1] Implement `src/gatekeeper/classifiers.py`: Load frozen DistilBERT intent classifier (CPU-only, default precision) and implement inference wrapper. **Acceptance Criteria**: Verify the model runs on CPU-only runner (no CUDA, memory < 2GB) and logs resource usage. **This verification must pass before T016 can proceed.**
- [ ] T016 [US1] [DEPENDS ON T014a] Implement `src/gatekeeper/pipeline.py` logic: Filter memory access using Classifier + Rules (AND logic) before LLM step, referencing `contracts/dataset.schema.yaml` for data structure.
- [ ] T017 [US1] Implement `src/gatekeeper/pipeline.py` logic: "Retrieval-only" and "Long-Context" baseline execution paths using `templates/prompts.yaml`; output `data/processed/baseline_results.json`. **Acceptance Criteria**: Verify that prompt templates and retrieval parameters are IDENTICAL to the Gatekeeper run.
- [ ] T018 [US1] Implement `src/gatekeeper/metrics.py` function: Calculate Access Control score (unauthorized exposure rate) against ground truth
- [ ] T019 [US1] Implement `src/cli/run_evaluation.py` logic: Execute US1 pipeline with `--domain medical,office` using existing CLI skeleton
- [ ] T020 [US1] Add error handling: Log "validation error" for ambiguous `leak-target` and exclude from calculation; handle model load retry logic
- [ ] T029 [US1/US2] Implement unified sampling logic for failure cases: Select 50 cases (stratified by domain, seed=42) from the combined pool of Access Control and Utility failures. Output to `data/samples/failure_cases.json`. **If a small number of failures exist, output all available. If zero failures exist, create an empty file and log a warning.**

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
- [ ] T026a [US2] Define LMM formula in `src/utils/stats.py`: `score ~ method + (1|Domain)` and implement model fitting logic
- [ ] T026b [US2] [DEPENDS ON T026a] Implement fallback logic in `src/utils/stats.py`: If LMM fails (singular matrix) or data is flat, run paired t-test or Wilcoxon signed-rank test per Constitution Principle VI
- [ ] T026c [US2] [DEPENDS ON T026a] Implement domain-stratified analysis in `src/utils/stats.py`: Run separate tests per domain and aggregate results if LMM is not feasible
- [ ] T027 [US2] Implement `src/cli/run_evaluation.py` logic: Execute US2 pipeline on `--domain education,household` using existing CLI skeleton
- [ ] T028 [US2] [DEPENDS ON T026a, T026b, T026c] Implement `src/cli/run_evaluation.py` logic: Generate paired comparison table (Gatekeeper vs Baseline) for Utility and Forgetting.

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
- [ ] T035 [US3] Implement `src/cli/run_evaluation.py` logic: Aggregate profiling data and calculate percentage reduction in latency/RAM for Gatekeeper vs Baseline
- [ ] T036 [US3] Create final report generator: Output `data/results/final_benchmark_report.md` containing sections: Access Control, Utility, Forgetting, Cost; include tables with headers: Method, Score, StdDev, **Test Statistic**, **Degrees of Freedom**, **Method Used (LMM/Fallback)**, P-Value, Latency (ms), RAM (MB)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T037 [P] Documentation: Update `quickstart.md` with instructions to run the full benchmark suite
- [ ] T038 Code cleanup: Refactor imports and ensure type hinting in `src/` modules
- [ ] T039 [P] Security: Run PII scan on `data/raw/` and `data/processed/` artifacts
- [ ] T040 [P] Run `pytest` for all unit, integration, and contract tests
- [ ] T041 Validate `data/results/final_benchmark_report.md` against `contracts/results.schema.yaml`
- [ ] T042 Verify `data/samples/failure_cases.json` contains exactly 50 entries (or N if N<50) with fixed seed 42

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
- **Statistical Fallback**: If LMM fails (singular matrix) or data is flat, use paired t-tests or Wilcoxon signed-rank tests per Constitution Principle VI.
- **Critical Dependency**: T016 requires T014a completion. T028 requires T026a/b/c completion. T006b requires T006. T008b requires T008a.