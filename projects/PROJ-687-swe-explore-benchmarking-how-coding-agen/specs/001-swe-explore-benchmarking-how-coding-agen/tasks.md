# Tasks: Reproduce & Validate: SWE-Explore Benchmarking

**Input**: Design documents from `/specs/001-swe-explore-benchmarking/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `src/benchmarks/`, `src/data/`, `src/tests/`, `contracts/`, `results/`, `tests/fixtures/`, `config/`. Create empty `__init__.py` files in `src/benchmarks`, `src/benchmarks/explorers`, `src/benchmarks/metrics`, `src/benchmarks/utils`, `tests/unit`, `tests/integration`.
- [X] T002 Initialize Python 3.11 project: Create `requirements.txt` with exact dependencies: `pyyaml`, `pandas`, `scikit-learn`, `requests`, `tqdm`, `tiktoken`, `jsonschema`, `datasets`, `pytest`, `scipy`. Create `pyproject.toml` with Python 3.11 constraint.
- [X] T003 [P] Configure linting and formatting: Create `.ruff.toml` with default settings and `pyproject.toml` [tool.black] section with `line-length=88`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/benchmarks/utils/loader.py`: Load `BenchmarkInstance` from HuggingFace `swe-explore/benchmark`. Implement hard-fail with error code 100 and message "Missing ground-truth dataset from SSoT" if dataset cannot be loaded.
- [X] T004.1 Implement hard-fail logic in `src/benchmarks/utils/loader.py`: Ensure the script exits with error code 100 and the exact message "Missing ground-truth dataset from SSoT" when the dataset is inaccessible, as per the Plan's Constitution Check.
- [X] T005 [P] Implement `src/benchmarks/utils/retry.py`: Exponential backoff decorator for API calls (with a configurable retry limit) to handle rate limits for any external calls.
- [X] T006 [P] Implement `src/benchmarks/utils/timeout.py`: Signal-based timeout wrapper (time-limited execution) for single instances.
- [X] T007 Create `src/benchmarks/explorers/base.py`: Abstract `BaseExplorer` class defining the interface.
- [X] T008 Define JSON Schemas in `contracts/explorer_output.schema.yaml` and `contracts/metrics_report.schema.yaml` matching the YAML structures defined in `data-model.md` for `ExplorationTrace` and `MetricsReport` entities respectively.
- [X] T008.1 [P] Create `config/stratification_config.yaml`: Define stratification criteria for `complexity` (easy/medium/hard) and `repo_size` (small/medium/large) buckets to support T028.
- [X] T009 Create `tests/fixtures/mock_instances.json`: Create a list of 1 BenchmarkInstance object with valid `instance_id`, `repository_url`, `branch`, `issue_id`, `issue_description`, and `ground_truth` (list of 1 file_path, start_line, end_line) as per `data-model.md`.

**Tests for Foundational Utilities (Parallel with Setup/Foundational)**

- [X] T010 [P] Unit test for `loader.py` using mock data in `tests/unit/test_loader.py`.
- [X] T011 [P] Unit test for timeout wrapper in `tests/unit/test_timeout.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Minimal Reproduction Run (Priority: P1) 🎯 MVP

**Goal**: Successfully execute the pipeline on a single representative instance using a lightweight, CPU-tractable explorer to verify end-to-end integrity.

**Independent Test**: A CI job runs the reproduction script against one pre-selected repository/issue pair. The job passes only if the script exits with code 0 and generates `results/minimal_run.json` containing a valid ranked list.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for `bm25.py` and `rule_based.py` in `tests/unit/test_explorers.py`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `src/benchmarks/explorers/bm25.py`: CPU-tractable BM25 explorer using `scikit-learn` (no CUDA, no 8-bit quantization).
- [X] T014 [P] [US1] Implement `src/benchmarks/explorers/rule_based.py`: Simple rule-based baseline explorer (keyword matching).
- [X] T015 [US1] Implement `src/benchmarks/metrics/calculator.py`: Implement function `calculate_metrics(trace: ExplorationTrace, instance: BenchmarkInstance) -> MetricsReport`. Calculate Coverage, Ranking Score, and Context-Efficiency using the **fixed 500 token budget** defined in Plan.md. Ensure coverage returns `null` if ground_truth is empty.
- [X] T016 [US1] Implement `src/benchmarks/run.py`: Main entry point with `argparse` CLI supporting `--mode` (smoke_test, batch, metrics_only), `--limit`, and `--input`. Orchestrate: load instance -> run explorer -> calculate metrics -> validate schema -> write JSON to `results/`.
- [X] T017 [US1] Implement schema validation logic in `run.py` using `jsonschema` against `contracts/` artifacts.
- [X] T018 [US1] Add error handling for missing environment variables with clear exit messages (US1 Edge Case).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Metric Calculation & Artifact Generation (Priority: P2)

**Goal**: Compute benchmark core metrics and produce a summary report comparing observed values against theoretical bounds.

**Independent Test**: The system parses output artifacts from US1, runs the metric calculator, and outputs a summary table where metrics are within [0.0, 1.0] or `null`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for `calculator.py` edge cases (empty ground truth) in `tests/unit/test_metrics.py`.
- [X] T020 [P] [US2] Integration test verifying `MetricsReport` JSON structure in `tests/integration/test_metrics_output.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Refine `src/benchmarks/metrics/calculator.py` to strictly enforce [0.0, 1.0] bounds and `null` for empty ground truth.
- [X] T022 [US2] Implement logic in `run.py` to generate `results/minimal_run.json` containing raw traces and calculated metrics.
- [X] T023 [US2] Add logging for metric calculation steps to ensure transparency (US2 Acceptance Scenario 1).
- [X] T024 [US2] Implement graceful skip logic for instances with malformed ground truth (US2 Edge Case).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Full-Scale Reproduction Attempt (Priority: P3)

**Goal**: Run the benchmark on a subset of representative issues using two distinct explorer types (BM25 and Rule-Based) to reproduce the comparative analysis. Note: The "agent-based" explorer is out of scope for this MVP; validation focuses on the qualitative "majority-wins" trend between the two implemented classical methods.

**Independent Test**: The system executes a batch run over multiple instances. It produces a comparative report showing the qualitative "majority-wins" trend (BM25 > Rule-Based in >50% of instances, or vice versa) or documents a deviation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Integration test for batch runner with timeout enforcement in `tests/integration/test_batch_run.py`.
- [X] T026 [P] [US3] Contract test for `ComparativeSummary` output schema in `tests/contract/test_summary_schema.py`.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement batch execution loop in `src/benchmarks/run.py` (`--mode batch --limit 10`).
- [X] T028 [US3] Implement `src/benchmarks/utils/sampler.py`: Implement function `stratified_sample(dataset, n=10)` using `config/stratification_config.yaml` to select instances balancing complexity and repo size.
- [X] T029 [US3] Implement `src/benchmarks/analysis/summary.py`: Implement function `generate_summary(reports: list[MetricsReport]) -> ComparativeSummary`. Calculate descriptive stats (wins/losses) for the qualitative majority-wins criterion. Perform **exploratory** Wilcoxon signed-rank test using `scipy.stats.wilcoxon` (non-confirmatory, for insight only). Output `results/comparative_summary.json`.
- [X] T030 [US3] Implement timeout detection and partial checkpoint saving for batch runs exceeding extended durations: save `results/checkpoint_{timestamp}.json` and exit with code 124.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Update `docs/quickstart.md` with instructions for smoke test vs. batch run.
- [X] T033 Code cleanup and refactoring: Run `ruff check --fix` and `black .` on `src/` and `tests/`. Ensure no linting errors remain.
- [X] T034 Performance optimization for dataset loading: Implement `git clone --depth 1` in `loader.py` and verify load time for 10 instances is < 30s.
- [X] T035 [P] Additional unit tests for retry logic in `tests/unit/test_retry.py`.
- [X] T036 Security hardening: Run `grep -r "api_key\|secret\|token" src/ tests/` and ensure no hardcoded strings are found. Add `.env.example` with placeholder variables.
- [X] T037 Run `quickstart.md` validation: Execute commands in `quickstart.md` in a clean environment. Record success/failure in `results/quickstart_validation.log`.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 implementation for artifact generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for batch orchestration

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Explorers before Services/Orchestration
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for loader.py using mock data in tests/unit/test_loader.py"
Task: "Unit test for timeout wrapper in tests/unit/test_timeout.py"

# Launch all explorers for User Story 1 together:
Task: "Implement src/benchmarks/explorers/bm25.py"
Task: "Implement src/benchmarks/explorers/rule_based.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Explorers)
   - Developer B: User Story 2 (Metrics)
   - Developer C: User Story 3 (Batch/Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks MUST run on CPU-only CI with limited cores and memory. No GPU, no 8-bit models, no large LLMs.