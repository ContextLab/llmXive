# Tasks: llmXive follow-up: extending "Video2GUI"

**Input**: Design documents from `/specs/001-tutorial-bias-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: Contract and integration tests are included to ensure data integrity and statistical validity.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/benchmarks/`, `data/results/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with `pyproject.toml` and `requirements.txt` (dependencies: `transformers`, `torch[cpu]`, `accelerate`, `scikit-learn`, `pandas`, `pytest`, `jsonschema`, `datasets`, `playwright`, `jinja2`, `llama-cpp-python`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Initialize Git hooks for pre-commit checks (schema validation, PII scan)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create `code/config.py` with deterministic random seeds, paths, and hardware constraints (CPU-only, 7GB RAM limit, **50-step hard limit** as per FR-006)
- [ ] T006 Define and implement `benchmark_task.schema.yaml` for FR-001 (JSON Schema for synthetic tasks)
- [~] T007 Define and implement `trajectory_log.schema.yaml` for FR-003 (JSON Schema for agent logs)
- [~] T008 Define and implement `simulator_state.schema.yaml` for FR-001/US-1 (JSON Schema for simulation states)
- [~] T009 Implement `code/verify_citations.py` to validate "GUI Error Taxonomy" sources and dataset URLs (FR-008)
- [~] T010 Implement `tests/contract/test_schemas.py` to enforce schema validation on all generated data
- [~] T011 Implement `code/agents/base_agent.py` with abstract methods for inference and step limits
- [ ] T019.5 [P] [US1] Generate "standard linear trajectories" dataset (positive control) required for Baseline and Linear Proxy agent training; output to `data/benchmarks/linear_trajectories.json` (FR-001)
- [ ] T019.6 [P] [US1] Generate "error-recovery training data" dataset required for Hybrid agent training; output to `data/benchmarks/error_recovery_trajectories.json` (FR-001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct the Non-Linear GUI Benchmark (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic benchmark of tasks with explicit error states and branching logic to isolate tutorial bias.

**Independent Test**: Running `code/generators/benchmark_generator.py` produces `data/benchmarks/benchmark_.json` with exactly 500 tasks, each containing an error injection point and a recovery path.

### Tests for User Story 1

- [~] T012 [P] [US1] Contract test: Verify `benchmark_500.json` matches `benchmark_task.schema.yaml` in `tests/contract/test_generator.py`
- [~] T013 [P] [US1] Validation test: Verify `verify_citations.py` successfully resolves the "GUI Error Taxonomy" source and `data/results/taxonomy_validation_report.json` in `tests/unit/test_citations.py`

### Implementation for User Story 1

- [~] T014.4 [US1] Download and stage the "GUI Error Taxonomy v1.0 " file from the verified source (T009) to `data/config/gui_error_taxonomy.yaml` (PREREQ for T014.5) <!-- FAILED: unspecified -->
- [~] T014.5 [US1] Implement `code/generators/taxonomy_loader.py` to parse `data/config/gui_error_taxonomy.yaml` into rule objects (FR-008) <!-- ATOMIZE: requested -->
- [~] T014.5.2 [US1] [P] Unit test: Implement `tests/unit/test_taxonomy_loader.py` to verify parsing of specific error rules from the staged taxonomy file <!-- FAILED: unspecified -->
- [~] T014.5.1 [US1] Implement `code/generators/taxonomy_validator.py` to **implement validation logic that maps generated tasks to taxonomy rules** and produce `data/results/taxonomy_validation_report.json` proving external validity (FR-008); verify mapping logic in tests. <!-- ATOMIZE: requested -->
- [~] T014 [US1] Implement `code/generators/benchmark_generator.py` to generate 500 tasks using the rule-based simulator, applying `task.type` field to mark "linear" vs "non-linear" (FR-001, FR-008)
- [ ] T014.6.1 [US1] Implement `code/generators/data_separator.py` to implement the hold-out set logic: consume `data/benchmarks/linear_trajectories.json` (T019.5) and `data/benchmarks/error_recovery_trajectories.json` (T019.6), ensure benchmark error patterns are disjoint from Hybrid training data, and output `data/benchmarks/holdout_set.json` (FR-001)
- [ ] T014.6.2 [US1] **Implement disjoint error pattern logic** in `code/generators/data_separator.py` to explicitly **exclude error patterns found in the Hybrid training set** from the benchmark generation, satisfying the disjoint constraint in FR-001.
- [~] T015 [US1] Implement `code/evaluation/simulator.py` (headless browser/HTML/JS) to render task states and inject errors (FR-001)
- [ ] T017 [US1] Implement checksum generation for the benchmark dataset to ensure reproducibility (Constitution Principle I)

**Checkpoint**: Benchmark generated and validated; US1 is functional.

---

## Phase 4: User Story 2 - Evaluate Agent Variants (Priority: P2)

**Goal**: Execute Baseline, WildGUI-trained (Linear Proxy), and Hybrid agents on the benchmark using CPU-only inference.

**Independent Test**: Running `code/evaluation/runner.py` against a subset of tasks produces `data/results/trajectories_subset.json` with action logs and success flags for all three agents without crashing.

### Tests for User Story 2

- [ ] T018 [P] [US2] Integration test: Run evaluation on 5 tasks and verify `data/results/trajectories.json` contains valid logs for all agents in `tests/integration/test_evaluation.py`
- [ ] T019 [P] [US2] Resource test: Verify memory usage stays <7GB and step count <50 during a long-running task in `tests/integration/test_resource_limits.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/agents/baseline_agent.py` (trained on `data/benchmarks/linear_trajectories.json` from T019.5, per FR-001)
- [ ] T021 [P] [US2] Implement `code/agents/linear_proxy_agent.py` (trained on `data/benchmarks/linear_trajectories.json` from T019.5, simulating video-derived data, per FR-001)
- [ ] T022 [P] [US2] Implement `code/agents/hybrid_agent.py` (trained on `data/benchmarks/linear_trajectories.json` + `data/benchmarks/error_recovery_trajectories.json` from T019.6)
- [ ] T023 [US2] Implement `code/evaluation/runner.py` to load agents with low-bit quantization (GGUF/CPU), verify/enforce 7GB RAM limit, and log trajectories (FR-002, FR-003)
- [ ] T024 [US2] **Implement `enforce_step_limit()` method in `code/evaluation/runner.py`** to explicitly raise `StepLimitExceeded` error if action count > 50 (hard limit from FR-006); **verify** this behavior in `tests/integration/test_resource_limits.py` by forcing a task to fail at step 51.
- [ ] T024.1 [US2] **Implement `enforce_time_limit()` method in `code/evaluation/runner.py`** to implement automatic abort and report timeout mechanism if total wall-clock time > 6 hours, logging to `data/results/timeout_report.json` (SC-004, Edge Cases); verify timeout trigger in tests.
- [ ] T025 [US2] Create `code/evaluation/pilot_run.py` to execute a small-scale feasibility check before full benchmark run

**Checkpoint**: All agents execute on benchmark; US2 is functional.

---

## Phase 5: User Story 3 - Statistical Analysis (Priority: P3)

**Goal**: Perform McNemar's test and power analysis to validate the "tutorial bias" hypothesis.

**Independent Test**: Running `code/analysis/stats.py` on paired outcomes produces a p-value and power analysis result matching expected synthetic inputs.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test: Verify McNemar's test calculation on a known synthetic dataset in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Contract test: Verify `stats.json` output matches `stats_schema.yaml` (to be created) in `tests/contract/test_stats.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analysis/stats.py` to consume `data/results/trajectories.json` from T023, calculate McNemar's test on non-linear task outcomes, extract and output the count of discordant pairs, and perform power analysis (FR-005, FR-007, SC-003)
- [ ] T029 [US3] Implement `code/analysis/report.py` to generate `data/results/stats.json` and `paper.md` using Jinja2 templates (FR-004, SC-001..SC-005)
- [ ] T030a [US3] Implement `code/analysis/sensitivity.py` to **implement the perturbation logic** for varying error-injection thresholds by ±10% (SC-005).
- [ ] T030b [US3] **Execute the ±10% threshold variation runs** using the logic from T030a, generate `data/results/sensitivity_analysis.json`, and verify success rate variance < 5% (SC-005).
- [ ] T031 [US3] Implement logic to calculate "Non-Linear Coverage Gap" and "Hybrid Recovery Rate" with confidence intervals (SC-001, SC-002)

**Checkpoint**: Statistical analysis complete; US3 is functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

- [ ] T032 [P] Run full end-to-end integration test (Benchmark → Evaluation → Analysis) and verify `paper.md` is generated correctly
- [ ] T033 [P] Update `README.md` and `quickstart.md` with instructions for running the benchmark and analysis
- [ ] T034 Code cleanup: Remove debug logs and ensure all `print` statements are replaced with proper logging
- [ ] T035 Verify all artifacts (benchmark, logs, stats) have deterministic hashes and are tracked in `state/`
- [ ] T036 Run `pytest` with coverage and ensure >80% coverage on `code/analysis` and `code/generators`

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
- **User Story 2 (P2)**: Depends on US1 completion (needs the benchmark data AND the linear training data from T019.5/T019.6)
- **User Story 3 (P3)**: Depends on US2 completion (needs the trajectory logs)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Runners/Evaluators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, Agent implementations (T020-T022) can run in parallel
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all agent implementations together (they are independent modules):
Task: "Implement code/agents/baseline_agent.py" (Depends on T019.5)
Task: "Implement code/agents/linear_proxy_agent.py" (Depends on T019.5)
Task: "Implement code/agents/hybrid_agent.py" (Depends on T019.5, T019.6)

# Once agents are ready, launch resource limit tests:
Task: "Integration test: Run evaluation on 5 tasks"
Task: "Resource test: Verify memory usage <7GB"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Benchmark Generation + Linear Data Generation)
4. **STOP and VALIDATE**: Verify 500 tasks are generated with correct schema and error injection
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Evaluation)
4. Add User Story 3 → Test independently → Deploy/Demo (Analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Benchmark Generator, Taxonomy Loader, Data Separator, Linear/Error Data Gen)
 - Developer B: User Story 2 (Agent Implementations)
 - Developer C: User Story 3 (Statistical Analysis)
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
- **Hardware Constraint**: All tasks involving model inference MUST use CPU-only quantization (low-bit). and respect the 7GB RAM limit. No GPU-dependent tasks.
- **Data Flow**: Linear training data (T019.5) and Error-recovery data (T019.6) MUST be generated BEFORE Benchmark (T014) to ensure hold-out logic (T014.6.1/T014.6.2) is valid.