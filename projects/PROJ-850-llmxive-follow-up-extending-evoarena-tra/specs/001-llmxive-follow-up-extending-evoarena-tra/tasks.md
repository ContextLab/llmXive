# Tasks: EvoMem-Conflict Filtering for Robust LLM Agents

**Input**: Design documents from `/specs/001-evoconflict-filtering/`
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

- [X] T001 [P] Initialize project directory structure: create `src/`, `tests/`, `specs/`, `data/`, `docs/` and their respective subdirectories (`src/agents/`, `src/heuristics/`, `src/data/generators/`, `src/data/benchmarks/`, `src/analysis/`, `src/utils/`, `src/cli/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/001-evoconflict-filtering/contracts/`). <!-- FAILED: unspecified -->
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing **pinned versions** for: `transformers>=4.30.0`, `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `pytest>=7.0.0`, `datasets>=2.14.0`, `tqdm>=4.65.0`, `statsmodels>=0.14.0`, `python-Levenshtein>=0.23.0`
- [X] T003 [P] Create `research.md` in `specs/001-evoconflict-filtering/` to serve as the configuration source. **Deliverable**: Verify `research.md` contains `sample_size: N` key calculated by T003a. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003a [P] Implement power analysis script `src/data/generators/power_analysis.py` to calculate sample size $N$ (Cohen's h = 0.2, Power=0.8, α=0.05). **Output**: Update `research.md` with `sample_size: N`.
- [X] T004 [P] Implement `src/utils/logging.py` for structured logging of context tokens, inference time, and success status
- [X] T005 [P] Create `src/data/generators/synthetic_pairs.py` to generate labeled JSON pairs for conflict detection validation. **Schema**: `{"patch_a": str, "patch_b": str, "is_contradiction": bool}`. **Logic**: Generate "contradiction" pairs by negating a key fact in `patch_b` relative to `patch_a`; generate "non-contradiction" pairs by updating unrelated facts. **Output**: Write generated dataset to `data/raw/synthetic_pairs.json`. **Fallback**: If `research.md` missing, default to N=100 pairs.
- [ ] T006 [P] Create `src/data/benchmarks/terminal_bench_evo.py` to **verify availability** of the `Terminal-Bench-Evo` dataset. **Logic**: Attempt to download from verified canonical sources first. **Only if** download fails or dataset is unavailable, generate a synthetic subset with explicit state patches and version updates. **Output**: Write dataset to `data/raw/terminal_bench_evo.jsonl`. **Fallback**: If `research.md` missing, default to 50 tasks.
- [ ] T007 [P] Create `src/agents/base_agent.py` abstract base class defining the agent interface and retrieval strategy hooks
- [ ] T008 [P] Configure deterministic random seeds in all scripts to ensure reproducible execution
- [ ] T009 [P] Implement `tests/unit/test_synthetic_generator.py` to verify the synthetic dataset generation logic and checksum integrity

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Conflict-Detection Heuristic Implementation (Priority: P1) 🎯 MVP

**Goal**: Implement a CPU-tractable conflict detector using DistilBERT to flag semantic contradictions in memory patches.

**Independent Test**: Run the detector on the synthetic pairs; verify precision/recall ≥ 80% against ground truth.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/heuristics/conflict_detector.py` using `distilbert-base-uncased` (CPU-only, default precision) to compute semantic contradiction scores. **Note**: Spec Assumptions mention a sub-billion parameter model; DistilBERT (a compact transformer model) is selected as a CPU-tractable optimization for the feasibility study to ensure execution within CI limits. Must support loading alternative CPU-tractable models for sensitivity analysis.
- [ ] T013 [US1] Implement threshold logic in `src/heuristics/conflict_detector.py` (softmax > 0.90 = conflict; else non-conflict)
- [ ] T014a [P] [US1] Implement `src/heuristics/conflict_detector.py` sensitivity analysis **threshold interface**: `run_sensitivity_analysis_thresholds(thresholds: list[float])`. **Config**: Use YAML format for threshold configuration. **Output**: Define schema for `data/processed/sensitivity_analysis_thresholds.csv`. **Logic**: Execute analysis across thresholds {0.7, 0.8, 0.9, 0.95} and a defined lower bound (e.g., 0.6) to cover the full range required by FR-008.
- [ ] T014b [US1] Implement `src/heuristics/conflict_detector.py` sensitivity analysis **model size execution logic** to perform the full analysis across model sizes ['distilbert-base-uncased', 'bert-base-uncased'] as required by FR-008. **Output**: Generate `data/processed/sensitivity_analysis_models.csv`. **Note**: This task specifically addresses the requirement to vary model sizes, distinct from threshold variations.
- [ ] T015 [US1] Add error handling in `src/heuristics/conflict_detector.py` to default to safe retrieval mode on timeout or failure (FR-007). **Safe Mode Definition**: Retrieve latest state plus a small number of the most recent non-conflict patches.
- [X] T010 [US1] Unit test `tests/unit/test_conflict_detector.py` for conflict detection logic on static synthetic pairs. **(Depends on T012)**
- [X] T011 [US1] Test fallback behavior in `tests/unit/test_conflict_detector.py::test_fallback_no_conflicts` when no conflicts are detected. **Expectation**: Function must return the latest state plus the 2 most recent non-conflict patches. **(Depends on T012)**
- [~] T016 [US1] Run validation script on synthetic dataset to confirm ≥80% precision/recall baseline before integration

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Agent Execution Pipeline (Priority: P2)

**Goal**: Instantiate and run `EvoMem-All` and `EvoMem-Conflict` agents on the task dataset, logging execution metrics.

**Independent Test**: Run a subset of tasks on both agents; verify `EvoMem-Conflict` retrieves fewer patches than `EvoMem-All` and both produce valid logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test `tests/integration/test_agent_pipeline.py::test_context_token_diff` verifying context token counts differ between variants
- [~] T018 [US2] Test that `EvoMem-Conflict` correctly filters non-conflict patches using the heuristic from US1 (Requires T012, T020). **(Depends on T012, T020)**

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/agents/evomem_all.py` to retrieve the last N patches (baseline)
- [ ] T020 [US2] Implement `src/agents/evomem_conflict.py` to retrieve only the latest state + patches flagged as conflicts by US1 heuristic. **Fallback Logic**: If no conflicts are detected, retrieve the latest state plus the 2 most recent non-conflict patches to prevent context starvation (Spec Edge Cases).
- [ ] T021 [US2] Implement `src/agents/evomem_conflict.py` fallback logic to retrieve the latest state plus the 2 most recent non-conflict patches if the conflict detector returns no flags or fails (FR-002, FR-007).
- [ ] T022 [US2] Implement `src/analysis/runner.py` to execute tasks from `Terminal-Bench-Evo` on both agent variants sequentially
- [~] T023 [US2] Ensure `src/analysis/runner.py` logs `task_id`, `agent_variant`, `context_tokens`, `inference_time`, `success_status` to CSV
- [~] T024a [P] [US2] Verify/Retrieve standard GitHub Actions runner time limit from `plan.md` constraints and store in `config.json`.
- [~] T024 [US2] Run the full experiment and verify execution completes within the **retrieved time limit** on CPU (SC-005). **Command**: `python run_experiment.py --config full`. **Verify**: `data/logs/full_run.csv` exists, is non-empty, has correct columns, and `total_time` < [retrieved_limit].

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Reporting (Priority: P3)

**Goal**: Analyze execution logs to calculate accuracy, hallucination rates, and statistical significance.

**Independent Test**: Feed mock CSV with known differences; verify script outputs correct p-value and effect direction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T025 [P] [US3] Unit test `tests/unit/test_stats.py` with mock data to verify statistical test logic and metric calculations <!-- ATOMIZE: requested -->

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `src/analysis/stats.py` to calculate chain-level accuracy and hallucination rates. **Ground Truth**: Use `src/agents/oracle.py` for command execution correctness. **Hallucination Metric**: Calculate **Levenshtein ratio** between LLM state description and ground truth state description; flag if < 0.90. **Note**: Hallucination is defined strictly as state misinterpretation, independent of command correctness.
- [ ] T027 [US3] Implement `src/analysis/stats.py` to perform **Wilcoxon signed-rank test** on accuracy distributions (FR-005, SC-004). **Note**: This implements the Spec's mandatory requirement.
- [ ] T027a [US3] Implement `src/analysis/stats.py::run_mcnemar_test` to perform **McNemar's test** on paired binary accuracy data, as mandated by `plan.md` for methodological validity when data is binary.
- [ ] T027b [US3] Implement `src/analysis/stats.py::select_statistical_test` logic to automatically choose between Wilcoxon (T027) and McNemar (T027a) based on data type (binary vs. continuous) and execute the appropriate test.
- [ ] T028 [US3] Implement `src/analysis/stats.py` to calculate "memory noise" reduction rate (non-conflict patches removed) (FR-006)
- [ ] T029 [US3] Generate final `specs/001-evoconflict-filtering/research_results.md` report. **Content**: Must include p-value, accuracy comparison table, and dataset limitation flags if conflicts are scarce. **Tool**: Use `scripts/generate_report.py` template.
- [ ] T030 [US3] Validate the full pipeline: Data Gen → Heuristic → Agent Run → Stats → Report. **(Depends on T024, T029)**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md` explaining the conflict filtering logic
- [ ] T032 Code cleanup and refactoring of `src/analysis/runner.py` for efficiency
- [ ] T033 [P] Additional unit tests for edge cases (empty conflict list, timeout handling) in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation to ensure reproducibility on a fresh environment
- [ ] T035 Verify checksums for all generated artifacts (datasets, logs) per Constitution Check III. **Tool**: Run `scripts/verify_checksums.py` and update `state/projects/PROJ-850-llmxive-follow-up-extending-evoarena-tra.yaml`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Requires T003a** (Power Analysis) and **T003** (Research.md).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Can start after Foundational.
 - **US2 (P2)**: **Cannot proceed in parallel with US1 implementation**. Must wait for T012 (Conflict Detector) to be merged.
 - **US3 (P3)**: **Cannot proceed in parallel with US2 implementation**. Must wait for T022 (Agent Execution) to produce logs.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T012** (Conflict Detector) to function correctly
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T022** (Agent Execution) to have log data

### Within Each User Story

- **Implementation (Models/Helpers)** MUST be written before **Tests** can run against them.
- Tests (if included) MUST be written as scaffolding first, but **executed** only after the implementation task (e.g., T012) is complete.
- Services/Agents before Analysis/Reporting
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T006, T009) can run in parallel (after T003a is done)
- Once Foundational phase completes, T012 (Detector) and T019 (All Agent) can run in parallel, but T020 (Conflict Agent) and T018 (Integration Test) must wait for T012.
- All tests for a user story marked [P] can run in parallel (once the implementation exists).
- Different user stories **cannot** be worked on in parallel by different team members if they share hard dependencies (e.g., US2 depends on US1).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Conflict Detector)
4. **STOP and VALIDATE**: Test User Story 1 independently on synthetic pairs
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Dual Agent Run)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Heuristic)
 - Developer B: User Story 2 (Agent Pipeline - All Variant) - *Can start, but Conflict Variant blocked*
 - Developer C: User Story 3 (Stats Framework) - *Can start, but data blocked*
3. Developer B merges User Story 1 (Heuristic) to complete Conflict Variant
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: No task may load models in 8-bit/4-bit or require GPU. All models must run on default precision CPU.
- **CRITICAL**: All data must be real or synthetically generated by code (no hardcoded fake data).
- **CRITICAL**: Statistical analysis uses **Wilcoxon** (Spec FR-005) and **McNemar** (Plan correction) with automatic selection (T027b).
- **CRITICAL**: Hallucination metric is **state misinterpretation (Levenshtein < 0.90)** independent of command execution correctness.
- **CRITICAL**: Fallback logic (FR-002, FR-007) MUST retrieve **latest state plus 2 most recent non-conflict patches**.
- **CRITICAL**: Sensitivity analysis (FR-008) MUST cover both threshold variations (T014a) and model size variations (T014b).