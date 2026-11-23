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

- [X] T001 [P] Initialize project directory structure: create `src/`, `tests/`, `specs/`, `data/`, `docs/` and their respective subdirectories (`src/agents/`, `src/heuristics/`, `src/data/generators/`, `src/data/benchmarks/`, `src/analysis/`, `src/utils/`, `src/cli/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/001-evoconflict-filtering/contracts/`). **Deliverable**: Run `ls -R src/` and verify exit code 0. Create `.gitkeep` files in all directories.
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` containing **pinned versions** for: `transformers>=4.30.0`, `scikit-learn>=1.3.0`, `pandas>=2.0.0`, `pytest>=7.0.0`, `datasets>=2.14.0`, `tqdm>=4.65.0`, `statsmodels>=0.14.0`, `python-Levenshtein>=0.23.0`
- [X] T003 [P] Create `research.md` in `specs/001-evoconflict-filtering/` to serve as the configuration source. **Schema**: Must include `sample_size: N`, `dataset_strategy`, `model_selection`, and `power_analysis_method` sections. **Deliverable**: Verify `research.md` exists and contains these keys.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003a [P] Implement power analysis script `src/data/generators/power_analysis.py` to calculate sample size $N$ using **Cohen's h** (binary data, MDES=0.2, Power=0.8, α=0.05). **Output**: Update `research.md` with `sample_size: N`.
- [ ] T003b [P] **Kickback Task**: Update `spec.md` (FR-009, SC-006) to replace "Cohen's d" with "Cohen's h" for power analysis, ratifying the methodological change. **Deliverable**: Commit to `spec.md` with note "Ratified: Cohen's h for binary data".
- [X] T004 [P] Implement `src/utils/logging.py` for structured logging of context tokens, inference time, and success status. **Depends on**: T003a (Power Analysis result).
- [X] T005 [P] Create `src/data/generators/synthetic_pairs.py` to generate labeled JSON pairs for conflict detection validation. **Schema**: `{"patch_a": str, "patch_b": str, "is_contradiction": bool}`. **Logic**: Generate "contradiction" pairs by negating a key fact in `patch_b` relative to `patch_a`; generate "non-contradiction" pairs by updating unrelated facts. **Output**: Write generated dataset to `data/raw/synthetic_pairs.json`. **Fallback**: If `research.md` missing, default to N=100 pairs.
- [ ] T006 [P] **Dataset Verification**: Attempt to download `Terminal-Bench-Evo` from HuggingFace ID: `Terminal-Bench-Evo` (or verified canonical source). **Logic**: If download fails, **FAIL LOUDLY** (raise exception, do not fallback). **Deliverable**: If successful, write dataset to `data/raw/terminal_bench_evo.jsonl`. If failed, ensure T006-SYNTH is executed. **Status**: Active.
- [ ] T006-SYNTH [P] **Synthetic Dataset Generation**: Generate a synthetic subset of tasks with version updates and contradictions if T006 fails (or as a guaranteed fallback). **Logic**: Use "Trace-Injection" methodology to create tasks with explicit command/path changes. **Output**: Write dataset to `data/raw/terminal_bench_evo_synthetic.jsonl`. **Deliverable**: File exists and is checksummed.
- [ ] T006b [P] **Synthetic Validation Gate**: If T006-SYNTH is used, implement `src/data/benchmarks/validate_synthetic.py` to verify distribution similarity against real data (if available). **Gate**: T006b MUST pass before T022 can start if synthetic data is used.
- [ ] T007 [P] Create `src/agents/base_agent.py` abstract base class defining the agent interface and retrieval strategy hooks. **Status**: Active (Unblocked).
- [X] T008 [P] Configure deterministic random seeds in all scripts to ensure reproducible execution. **Deliverable**: Verify `seed = 42` is set in `__main__` blocks of all scripts.
- [X] T009 [P] Implement `tests/unit/test_synthetic_generator.py` to verify the synthetic dataset generation logic and checksum integrity

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Conflict-Detection Heuristic Implementation (Priority: P1) 🎯 MVP

**Goal**: Implement a CPU-tractable conflict detector using DistilBERT to flag semantic contradictions in memory patches.

**Independent Test**: Run the detector on the synthetic pairs; verify precision/recall ≥ 80% against ground truth.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `src/heuristics/conflict_detector.py` using `distilbert-base-uncased` (CPU-only, default precision) to compute semantic contradiction scores. **Note**: Spec Assumptions mention a sub-billion parameter model; DistilBERT is selected as a CPU-tractable optimization. Must support loading alternative CPU-tractable models for sensitivity analysis. **Depends on**: T007.
- [ ] T012a [P] [US1] **Model Validation**: Verify T012 model meets constraints: params ≤ 0.5B, inference time ≤ 500ms per pair. **Hard Gate**: If metrics exceed limits, task FAILS and model selection must be revised.
- [ ] T013 [US1] Implement threshold logic in `src/heuristics/conflict_detector.py` (softmax > 0.90 = conflict; else non-conflict)
- [ ] T014a [P] [US1] Implement `src/heuristics/sensitivity_thresholds.py` to execute sensitivity analysis across a range of thresholds. **Output**: Create CSV `data/processed/sensitivity_analysis_thresholds.csv` with columns: `threshold` (float), `precision` (float), `recall` (float), `f1_score` (float), `model_name` (string). **Delimiter**: Comma.
- [ ] T014b [P] [US1] Implement `src/heuristics/sensitivity_models.py` to execute sensitivity analysis across model sizes ['distilbert-base-uncased', 'bert-base-uncased'] and thresholds [0.5, 0.7, 0.9]. **Output**: Create CSV `data/processed/sensitivity_analysis_models.csv` with columns: `model_name` (string), `params` (string), `accuracy` (float), `latency` (float), `threshold_used` (float).
- [ ] T015 [US1] Add error handling in `src/heuristics/conflict_detector.py` to default to safe retrieval mode on timeout or failure (FR-007). **Safe Mode Definition**: Retrieve latest state plus the 2 most recent non-conflict patches.

### Tests for User Story 1 (MUST come after implementation)

- [X] T010 [US1] Unit test `tests/unit/test_conflict_detector.py` for conflict detection logic on static synthetic pairs. **(Depends on T012)**
- [X] T011 [US1] Test fallback behavior in `tests/unit/test_conflict_detector.py::test_fallback_no_conflicts` when no conflicts are detected. **Expectation**: Function must return the latest state plus the 2 most recent non-conflict patches. **(Depends on T012)**
- [ ] T016 [US1] Run validation script on synthetic dataset to confirm ≥80% precision/recall baseline before integration

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Dual-Agent Execution Pipeline (Priority: P2)

**Goal**: Instantiate and run `EvoMem-All` and `EvoMem-Conflict` agents on the task dataset, logging execution metrics.

**Independent Test**: Run a subset of tasks on both agents; verify `EvoMem-Conflict` retrieves fewer patches than `EvoMem-All` and both produce valid logs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Integration test `tests/integration/test_agent_pipeline.py::test_context_token_diff` verifying context token counts differ between variants
- [ ] T018 [US2] Test that `EvoMem-Conflict` correctly filters non-conflict patches using the heuristic from US1 (Requires T012, T020). **(Depends on T012, T020)**

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `src/agents/evomem_all.py` to retrieve the last N patches (baseline). **Depends on**: T007.
- [X] T020 [US2] Implement `src/agents/evomem_conflict.py` to retrieve only the latest state + patches flagged as conflicts by US1 heuristic. **Fallback Logic**: If no conflicts are detected, retrieve the latest state plus a small set of the most recent non-conflict patches to prevent context starvation (Spec Edge Cases). **Depends on**: T007, T012.
- [X] T021 [US2] Implement `src/agents/evomem_conflict.py` fallback logic to retrieve the latest state plus the 2 most recent non-conflict patches if the conflict detector returns no flags or fails (FR-002, FR-007).
- [X] T022 [US2] Implement `src/analysis/runner.py` to execute tasks from `Terminal-Bench-Evo` (or synthetic) on both agent variants sequentially. **Depends on**: T006-SYNTH (guaranteed fallback), T006b (if synthetic), T019, T020.
- [X] T023 [US2] Ensure `src/analysis/runner.py` logs `task_id`, `agent_variant`, `context_tokens`, `inference_time`, `success_status` to CSV
- [ ] T024a [P] [US2] Create `run_experiment.py` at repository root to serve as the main entry point for the experiment. **Logic**: Parse `--config` arguments (e.g., `full`, `test`), load `config.json` if present, and invoke `src/analysis/runner.py`. **Deliverable**: File exists at `./run_experiment.py` and is executable.
- [ ] T024a-SYNTH [P] [US2] **Config Generation**: Create `config.json` at repository root if not present. **Logic**: Set `experiment_limit` to default value (e.g., 6 hours) and `dataset_path` to `data/raw/terminal_bench_evo_synthetic.jsonl` if real data missing. **Deliverable**: `config.json` exists with valid JSON.
- [ ] T024 [US2] Run the full experiment and verify execution completes within the **retrieved time limit** on CPU (SC-005). **Command**: `python./run_experiment.py --config full`. **Verify**: `data/logs/full_run.csv` exists, is non-empty, has correct columns, and `total_time` < [retrieved_limit] (from `./config.json`). **Depends on**: T024a, T024a-SYNTH, T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Reporting (Priority: P3)

**Goal**: Analyze execution logs to calculate accuracy, hallucination rates, and statistical significance.

**Independent Test**: Feed mock CSV with known differences; verify script outputs correct p-value and effect direction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025a [P] [US3] Unit test `tests/unit/test_stats.py::test_mcnemar_binary_data` with mock data `[[0,1], [1,0]]` (discordant pairs). **Expected**: Statistic calculation returns p-value < 0.05 (indicating significant difference). **Verification**: Assert `p_value < 0.05` is True.
- [ ] T025b [P] [US3] Unit test `tests/unit/test_stats.py::test_wilcoxon_continuous_data` with mock data `[1.0, 2.0, 3.0]` vs `[1.5, 2.5, 3.5]`. **Expected**: Statistic calculation returns p-value < 0.05. **Verification**: Assert `p_value < 0.05` is True.
- [ ] T025c [P] [US3] Unit test `tests/unit/test_stats.py::test_auto_select_logic` to verify the function correctly chooses McNemar for binary data (input type: boolean/int 0/1) and Wilcoxon for continuous data (input type: float). **Verification**: Assert correct method selection based on input dtype.
- [ ] T025 [P] [US3] **Unit Test Suite**: Ensure all T025a/b/c tests are implemented and passing. **Deliverable**: `pytest tests/unit/test_stats.py` passes.

### Implementation for User Story 3

- [ ] T027b [P] [US3] **Kickback Task**: Update `spec.md` (FR-005, SC-004) to replace "Wilcoxon signed-rank test" with "McNemar's test" for binary accuracy data, ratifying the methodological change. **Deliverable**: Commit to `spec.md` with note "Ratified: McNemar's test for binary data".
- [ ] T026 [P] [US3] Implement `src/analysis/stats.py` to calculate chain-level accuracy and hallucination rates. **Ground Truth**: Use `src/agents/oracle.py` for command execution correctness. **Hallucination Metric**: Compute **Levenshtein ratio** between LLM state description and ground truth state description; flag if < 0.90. **Logic**: Flag hallucination if **EITHER** (incorrect terminal command execution) **OR** (state similarity < 0.90). **Depends on**: T025.
- [ ] T027 [US3] Implement `src/analysis/stats.py` to perform statistical analysis with **auto-select logic**:
 1. Detect data type (binary vs continuous).
 2. If binary: Perform **McNemar's test** (as per Plan.md correction for binary data).
 3. If continuous: Perform **Wilcoxon signed-rank test** (as per Spec FR-005 for continuous metrics).
 4. Output p-value and boolean significance (p < 0.05). **Note**: This single task implements the correct method based on data type, resolving the spec/plan contradiction. **Implementation Basis**: Proceed based on Plan.md; T027b is a parallel kickback task. **Depends on**: T025.
- [ ] T028 [US3] Implement `src/analysis/stats.py` to calculate "memory noise" reduction rate (non-conflict patches removed) (FR-006)
- [ ] T029 [US3] Generate final `specs/001-evoconflict-filtering/research_results.md` report. **Content**: Must include p-value, accuracy comparison table, and dataset limitation flags if conflicts are scarce. **Command**: `python./scripts/generate_report.py --input data/logs/full_run.csv --output specs/001-evoconflict-filtering/research_results.md --template scripts/report_template.md`.
- [ ] T030 [US3] Validate the full pipeline: Data Gen → Heuristic → Agent Run → Stats → Report. **(Depends on T024, T029)**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md` explaining the conflict filtering logic
- [ ] T032a [P] Code optimization: Reduce peak memory usage in `src/analysis/runner.py` via streaming or batch processing.
- [ ] T032b [P] Code cleanup: Extract `log_metrics` function from `runner.py` to reduce code duplication (target: reduce function lines by [deferred] or extract to < 15 lines) and maintain cyclomatic complexity < 5.
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
- All Foundational tasks marked [P] (T004, T005, T006, T006-SYNTH, T007, T009) can run in parallel (after T003a is done)
- Once Foundational phase completes, T012 (Detector) and T019 (All Agent) can run in parallel, but T020 (Conflict Agent) and T018 (Integration Test) must wait for T012.
- All tests for a user story marked [P] can run in parallel (once the implementation exists).
- Different user stories **cannot** be worked on in parallel by different team members if they share hard dependencies (e.g., US2 depends on US1).

### Specific Task Dependencies

- **T004**: Depends on T003a. (Decoupled from T003b).
- **T006-SYNTH**: Mandatory fallback. Runs if T006 fails or as guaranteed source.
- **T022**: Depends on T006-SYNTH (guaranteed data source), T006b (if synthetic), T019, T020.
- **T010, T011**: Depend on T012.
- **T025, T026, T027**: T027 depends on T025. T027b is a parallel kickback task, not a dependency for T027.
- **T024**: Depends on T024a, T024a-SYNTH, T022.

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
- **CRITICAL**: Statistical analysis uses **auto-select logic** (binary -> McNemar, continuous -> Wilcoxon) as defined in T027.
- **CRITICAL**: Hallucination metric is **state misinterpretation (Levenshtein < 0.90) OR command failure**.
- **CRITICAL**: Fallback logic (FR-002, FR-007) MUST retrieve **latest state plus 2 most recent non-conflict patches**.
- **CRITICAL**: Sensitivity analysis (FR-008) MUST cover both threshold variations (T014a) and model size variations (T014b) with specific thresholds [0.5, 0.7, 0.9].
- **CRITICAL**: T006 must FAIL LOUDLY on missing data; T006-SYNTH is the guaranteed fallback.
- **CRITICAL**: T027 proceeds based on Plan.md; T027b is a parallel kickback task.
- **CRITICAL**: T024a-SYNTH creates `config.json` and is a hard dependency for T024.
- **CRITICAL**: T032b target: reduce function lines by [deferred] or extract to < 15 lines.