# Tasks: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-agenticsts-followup/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-990-llmxive-follow-up-extending-agenticsts-a/`)
- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: pandas, numpy, scikit-learn, pytest, pyyaml)
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `code/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data processing, model training, and validation gates.
**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete.

**Data Flow**: T006 (Parser) -> T014a (Split) -> T007b (Static Proxy) / T008b (Ablation) -> T008c (Sample Check) -> T014 (Validator) -> T009 (Train)

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters. Define `TOKEN_BUDGET=4096`, `MIN_CONTEXT=256` as explicit constants loaded from config or env vars.
- [X] T006 [P] Implement `code/parser.py` to extract per-turn metrics (health, threat, deck size) AND **legal move distributions** from raw trajectory logs in `data/raw/`. **Output**: `data/processed/metrics_with_moves.csv`. **Note**: Must include the probability distribution of available legal moves to support entropy calculation.
- [X] T005 Implement `code/entropy.py` to calculate **Shannon entropy** of the legal move distributions extracted by T006. **Logic**: Calculate $H = -\sum p_i \log(p_i)$. If calculation returns NaN or Inf, return a sentinel value (e.g., `float('inf')`) and **write a warning log to `data/processed/edge_case_warnings.log`** with the exact text: "Warning: NaN/Inf entropy detected at trajectory {id}, turn {turn}". **Input**: `data/processed/metrics_with_moves.csv`. **Depends on**: T006.
- [X] T007 Create `data/processed/` directory structure and schema validation for derived metrics.
- [X] T014a [P] Implement `code/splitter.py` to perform a stratified data split of the **raw** trajectories into FOUR distinct sets: **Train**, **Ablation-Train**, **Validation**, and **Test**. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`, AND `data/processed/validation_set_ids.json`. **Note**: The **Validation set** MUST contain at least 20 trajectories (FR-006) and is distinct from the Ablation-Train set. The **Ablation-Train set** is used exclusively to generate ground-truth utility labels via ablation. The **Test set** is reserved for final baseline/dynamic evaluation. The **Train set** is for model training. This split must occur BEFORE any ablation study. **Constraint**: Assert `len(validation_set) >= 20` and raise error if not. **Output `validation_set_ids.json`** containing the list of trajectory IDs in the validation set to ensure integrity checks in T014. **Depends on**: T006.

### Phase 2b: Sequential Dependencies (Must run after T014a)
- [X] T007b [P] Extend `code/parser.py` to add **static-log-derived utility** extraction (frequency of layer retrieval) from raw trajectory logs as a distinct artifact. **Input**: `data/processed/validation_set.csv` (from T014a). **Output**: `data/processed/static_log_proxy.json` (schema: `{layer_id, retrieval_frequency}`). **Constraint**: Must process ONLY the validation set to prevent data leakage. **Must use the exact same `validation_set.csv` file generated by T014a**. **Note**: Runs AFTER T014a completes; can parallelize with T008b. **Depends on**: T006, T014a.
- [X] T008a [P] Implement `code/ablation.py` (engine function) as a reusable function to run the ablation study on a given dataset file. **Input**: Dataset file path, engine configuration. **Output**: `data/processed/ablation_labels_{dataset_name}.json` (schema: `{layer_id, utility_score}`). **Note**: This function is called by T008 and T008b.
- [X] T008 [US1] Execute ablation study on the **Ablation-Train set** using the function from T008a. **Input**: `data/processed/ablation_train_set.csv` (from T014a). **Output**: `data/processed/ablation_labels_train.json` (schema: `{layer_id, utility_score}`). **Depends on**: T006, T014a, T008a.
- [X] T008b [US1] Execute ablation study on the **Validation set** using the function from T008a. **Input**: `data/processed/validation_set.csv` (from T014a). **Output**: `data/processed/ablation_labels_validation.json`. **Depends on**: T006, T014a, T008a.
- [X] T008c [US1] Implement `code/validator.py` to check sample count. **Logic**: If `n < 300`, **MUST** log a WARNING to `data/processed/edge_case_warnings.log` with the exact text: "Warning: statistical power is marginal (n=298); recommend expanding the dataset", generate `data/processed/fallback_flag.json` with content `{"fallback": true, "reason": "n < 300"}`, and **proceed**. If `n >= 300`, generate `data/processed/fallback_flag.json` with `{"fallback": false}`. **Action**: For n=298 (the actual dataset), this task MUST generate the fallback flag and continue. **Do NOT generate synthetic labels**. **Note**: T014 depends on this output. **Depends on**: T008, T008b, T014a.
- [X] T014 [US1] Implement proxy validation logic in `code/classifier.py`. **Logic**: 
 1. Assert `len(validation_set) >= 20` (raise error if not).
 2. Load `validation_set_ids.json` (from T014a).
 3. **Assert** that the trajectory IDs in `static_log_proxy.json` (from T007b) and `ablation_labels_validation.json` (from T008b) match exactly the IDs in `validation_set_ids.json`. Raise error if mismatch.
 4. Check Pearson correlation (≥ 0.7) between **static log proxy** and ablation utility on the **Validation set**. 
 5. **Output**: `data/processed/proxy_validation_report.json`. 
 6. **Action**: Raise exception if r < 0.7. 
 **Note**: The Validation set is distinct from the Ablation-Train set and serves as the required hold-out set for FR-006. **Depends on**: T007b, T008b, T014a, T008c.
- [X] T009 [US1] Implement `code/classifier.py` to train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Logic**: 
 1. **Verify** `data/processed/fallback_flag.json` (from T008c) exists. If `fallback: true`, **SKIP training**.
 2. **Verify** `data/processed/proxy_validation_report.json` (from T014) exists and indicates `correlation >= 0.7`. If not, **raise error**.
 3. If checks pass: Train on `data/processed/ablation_labels_train.json` (ablation-derived ground-truth utility from T008). **Target**: `utility_score`. **Split**: 80/20 (within train set). **Output**: `models/layer_utility_classifier.pkl`. 
 **Note**: Trains exclusively on ablation-derived ground truth or skips if fallback is active. **Depends on**: T008, T008c, T014.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

**Independent Test**: Run held-out trajectories through Dynamic, Static, and Random agents; verify variable layer selection, token budget compliance, and outcome logging.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Unit test for entropy calculation edge cases (NaN, Inf, zero moves) in `tests/unit/test_entropy.py`.
- [X] T013 [P] [US1] Unit test for token budget enforcement and minimum context floor in `tests/unit/test_simulator.py`.
- [X] T016a [P] [US1] Verify edge case warning logs. **Logic**: Parse `data/processed/edge_case_warnings.log` to ensure it contains entries for NaN/Inf entropy (from T005) and n<300 warnings (from T008c). **Output**: `data/processed/edge_case_verification.json` with boolean `passed`. **Depends on**: T005, T008c.

### Implementation for User Story 1 (Dynamic Policy)

- [X] T015 [US1] Implement dynamic layer selection logic in `code/simulator.py`. **Logic**: 
 1. Check `fallback_flag.json` (from T008c). If `true`, **use fixed k=2 retrieval** (select top 2 layers by static frequency or predefined priority).
 2. If `false`, use trained model (T009) to predict top-k layers based on current turn entropy (from T005), **integrating** this prediction with the token budget constraint logic (4096 tokens). 
 **Depends on**: T009, T005, T014a (test_set), T008c.
- [X] T016 [US1] Add logic to enforce a hard token budget and a minimum context floor in `code/simulator.py`. **Logic**:
 1. **Maximum Budget**: If predicted token count > 4096, truncate or prune the least useful layers until the prompt size is ≤ 4096.
 2. **Minimum Floor**: If the selected layers result in a token count < 256 tokens, **append the 'Current Objective' layer** to enforce the minimum context.
 3. **NaN/Inf Handling**: If entropy returns a sentinel (NaN/Inf), default to retrieving the **full "all-layers" set** for that turn and log a warning to `data/processed/edge_case_warnings.log`. 
 **Note**: This is an edge-case override within the budget enforcement, distinct from T015's prediction. 
 **Depends on**: T015.
- [X] T017 [US1] **Execute Dynamic Simulation**. **Logic**: Invoke the `agenticsts-engine` (via T018) using the logic from T015 and T016 on the **test set**. **Output**: `data/processed/simulation_logs_dynamic.json`. **Note**: The test set evaluation compares **outcomes** (win rate) against the static baseline, not layer utility predictions against ground truth (which is impossible without re-running the game engine for every layer removal on the test set). The primary hypothesis test is valid as designed. **Depends on**: T015, T016, T018, T014a.

### Implementation for User Story 2 (Baselines & Aggregation)

**Note**: Baselines (T019, T020) depend on the game engine execution (T018) to generate new outcomes.

- [X] T018 [P] Implement `code/engine_runner.py` to invoke the `agenticsts-engine` for re-simulation. **Logic**: Accept a trajectory file and a memory policy (Dynamic, Static, Random) as input, execute the engine, and output raw simulation logs. **Output**: `data/processed/simulation_logs_{policy}.json`. **Depends on**: T006, T014a.
- [X] T019 [US2] Implement "Static All-Layers" baseline execution. **Logic**: Invoke `code/engine_runner.py` (T018) with policy="Static" on the **test set**. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018, T014a.
- [X] T020 [US2] Implement "No-Store Random" baseline execution. **Logic**: Invoke `code/engine_runner.py` (T018) with policy="Random" on the **test set**. **Logic**: **Select k layers uniformly at random for each turn with NO memory of past layers (no-store)**. **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018, T014a.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition. **Input**: Outputs from T017, T019, T020.
- [X] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Schema**: `condition, win_rate, avg_tokens, std_dev_tokens`. **Aggregation Logic**: Mean of win_rate and token columns grouped by condition; **Calculate standard deviation of token savings** per condition to satisfy SC-004. **Depends on**: T021.
- [X] T023 [US2] Implement verification logic to calculate token reduction consistency. **Logic**: Calculate the standard deviation of token savings across the test set for the Dynamic policy. **Output**: `data/processed/token_consistency_report.json` containing `std_dev_tokens` and a boolean `passed` (true if std_dev < threshold or simply reported as required). **Action**: This task explicitly addresses SC-004. **Input**: `data/processed/baseline_comparison.csv`. **Output**: `data/processed/token_consistency_report.json`. **Depends on**: T022.
- [X] T022a [US2] Implement verification logic to calculate percentage reduction in token usage. **Output**: Generate `data/processed/token_reduction_verification.json` containing a boolean field `passed` (true if reduction ≥ 30%) and a numeric field `actual_reduction_percent`. **Action**: **If `passed` is false, exit with code 1** to enforce SC-002 as a hard gate. The pipeline must halt if the success criterion is not met. **Input**: `data/processed/baseline_comparison.csv`. **Output**: `data/processed/token_reduction_verification.json`. **Depends on**: T022.
- [X] T022b [US2] Generate explicit failure artifact. **Logic**: If T022a exits with code 1, generate `data/processed/verification_failed.json` with details on the token reduction shortfall. **Action**: This ensures a clear failure state is recorded if the pipeline halts. **Depends on**: T022a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

**Independent Test**: Run analysis on a dataset with known outcomes and verify correct selection of McNemar's test and Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for McNemar's test selection logic (binary data) in `tests/unit/test_stats.py`.
- [X] T024 [P] [US3] Unit test for Bonferroni correction application in `tests/unit/test_stats.py`.

### Implementation for User Story 3

- [X] T024a [US3] Implement trajectory divergence detection in `code/stats.py`. **Logic**:
 1. For each trajectory pair (Dynamic vs Static) from the re-simulation outputs (T017, T019), compute the **SHA256 hash** of the final game state (e.g., `final_state_hash`).
 2. Compare the hash from the re-simulated Dynamic run against the hash from the re-simulated Static run.
 3. If the hashes differ for any pair, set `is_divergent=true` for that pair. If all pairs match, `is_divergent=false`.
 4. **Output**: `data/processed/divergence_report.json` (boolean `is_divergent`, and a list of divergent trajectory IDs).
 5. **Significance**: This check determines if the trajectories remained paired (deterministic) or diverged (unpaired). **Depends on**: T017, T019.
- [X] T025 [US3] Implement statistical testing logic in `code/stats.py`. **Logic**:
 1. Read `divergence_report.json` (T024a).
 2. **Verify** the correct test is selected: If `is_divergent` is true (unpaired), select Permutation Test; if false (paired), select McNemar's test. **Log the selection decision** explicitly in `data/processed/statistical_results.json` under `test_selection_reason`.
 3. **Execute** the selected test for win/loss outcomes.
 4. **Token Usage**: **Implement paired t-test** for token usage (check normality assumption; if failed, use Wilcoxon signed-rank test).
 5. **Correction**: **Apply Bonferroni correction** to the family of tests comprising the win rate test AND the token usage test simultaneously to control the family-wise error rate.
 **Output**: `data/processed/statistical_results.json`. **Depends on**: T024a, T021.
- [X] T028 [US3] Generate final statistical report in `data/processed/statistical_results.json`. **Schema**: `{p_value, effect_size, test_type, bonferroni_adjusted, divergence_status, token_reduction_percent, token_reduction_passed}`. **Includes**: SC-001/SC-003 metrics. **Note**: Must ingest `token_reduction_verification.json` from T022a to report the token reduction metric. **Depends on**: T025, T022a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `README.md` and `quickstart.md`. **Content**: Update `README.md` with a new section "Dynamic Policy Usage" containing a code snippet demonstrating the `--policy dynamic` flag; Update `quickstart.md` with the new pipeline steps. **Verification**: Ensure the new sections exist and are readable. **Action**: Mark as complete once verified.
- [X] T030 [P] Code cleanup and refactoring. **Criteria**: Refactor `code/` to pass ruff linting with zero warnings and remove duplicate imports. **Verification**: Run `ruff check code/` and confirm exit code 0. **Action**: Mark as complete once verified.
- [X] T031 [P] Add performance benchmarking script `code/benchmark.py` that logs execution time per phase and total runtime to `data/processed/benchmark_log.json`.
- [X] T031b [P] Analyze benchmark results. **Logic**: Read `data/processed/benchmark_log.json`. **Output**: Generate `data/processed/optimization_report.md` documenting the runtime analysis and confirming whether refactoring is needed. **Depends on**: T031.
- [X] T031c [P] Refactor code if needed. **Logic**: If `optimization_report.md` indicates runtime > 6 hours, refactor code to reduce runtime. **Verification**: Re-run benchmark and confirm runtime ≤ 6 hours. **Depends on**: T031b.
- [X] T032 [P] [US1] Add unit tests for edge cases. **Specific Task**: Add `tests/unit/test_classifier.py::test_fallback_flag_generation_on_small_n` to verify the n < 300 warning logic.
- [X] T033 [P] **Run `quickstart.md` validation**. **Logic**: Execute `quickstart.md` from a clean environment, capture stdout/stderr to `data/processed/reproducibility_log.json`, and verify exit code 0. **Output**: `data/processed/reproducibility_log.json`. **Action**: If exit code != 0, the task fails. This operationalizes Constitution Principle I. **Depends on**: T029, T030.
- [X] T034 [P] Add explicit data source validation in `code/parser.py` to ensure `data/raw/` contains non-empty, checksum-verified trajectory files before processing begins, raising a clear error if missing or corrupted.
- [X] T035 [P] Implement a "dry-run" mode in `code/main.py` that executes the full pipeline on a single trajectory (or first 5) to verify data flow and edge case handling (NaN entropy, budget truncation) before full-scale execution.
- [X] T036 [P] Add detailed logging of the "Current Objective" layer append logic in `code/simulator.py` (T016) to `data/processed/simulation_logs.json` for auditability of minimum context floor enforcement.
- [X] T037 [P] Create a `data/processed/analysis_config.json` snapshot that records the exact random seeds, hyperparameters, and dataset split ratios used for the specific run, ensuring full reproducibility of the statistical results.
- [X] T038 [P] **Add robust error handling for the engine runner**. **Logic**: Wrap `code/engine_runner.py` (T018) calls in `try/except` blocks that catch `EngineCrashError`, `TimeoutError`, and `DataCorruptionError`. Log the specific error type and trajectory ID to `data/processed/engine_errors.log` and **fail the pipeline** (exit code 1) if the error rate exceeds 5% of the test set, preventing silent data loss. **Verification**: Add unit test `tests/unit/test_engine_runner.py::test_error_handling_catches_timeout` to verify the try/except blocks function as described. **Depends on**: T018.
- [X] T039 [P] Add a `--stream` flag to `code/parser.py` to support chunked processing of large trajectory files. **Behavior**: Process data in batches of 100 lines at a time. **Verification**: Verify memory usage < 7GB with `--stream` on a 1GB file.
- [X] T040 [P] Write a comprehensive `CONTRIBUTING.md` section. **Content**: Add a "Data Flow" section to `CONTRIBUTING.md` detailing the T006 -> T014a dependency chain. **Verification**: Verify `CONTRIBUTING.md` contains the string "T006 -> T014a".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks all user stories**.
 - **Critical Flow**: T006 -> T014a -> T007b (after T014a) -> T008c -> T014 -> T009.
 - T009 (Training) MUST wait for T014 (Validation) to pass AND T008c (Sample Size) to handle fallback if needed.
- **User Stories (Phase 3)**: Depends on Foundational (Phase 2).
 - T015 (Dynamic Logic) depends on T009 (Model) and T008c (Fallback Flag).
 - T017 (Dynamic Execution) depends on T015, T018, T014a.
 - T019/T020 (Baselines) depend on T018.
 - T021 (Aggregation) depends on T017, T019, T020.
- **Statistical (Phase 4)**: Depends on Phase 3 (Aggregation results).
 - T024a (Divergence) depends on T017/T019.
 - T025 (Testing) depends on T024a.
 - T028 (Final Report) depends on T025, T022a.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models/Utilities (Entropy, Parser) before services (Simulator, Classifier).
- Services before analysis scripts.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- T006, T014a can run in parallel in Phase 2.
- T007b and T008b can run in parallel **after** T014a completes.
- T019, T020 can run in parallel in Phase 3 (after T018).
- All tests for a user story marked [P] can run in parallel.
- T032, T034, T035, T036, T037, T038, T039, T040 can run in parallel in Phase N.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - Ensure T014 (Validation) passes before T009 (Training).
 - Handle T008c sample size check.
3. Complete Phase 3: User Story 1 (Dynamic Policy)
4. **STOP and VALIDATE**: Test Dynamic Policy against Static Baseline on a small subset.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!).
3. Add User Story 2 (Baselines) → Test independently → Deploy/Demo.
4. Add User Story 3 (Statistical) → Test independently → Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Dynamic Policy).
 - Developer B: User Story 2 (Baselines - T019, T020).
 - Developer C: User Story 3 (Statistical Analysis).
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Verify tests fail before implementing.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence.
- **Critical Constraint**: All tasks must run on CPU-only CI with limited cores and memory. No GPU models or 8-bit quantization.
- **Data Integrity**: All analysis tasks must use real trajectory data from `data/raw/` or `data/processed/`. No synthetic data generation for results.
- **Methodology**: Ablation study (T008, T008b) is performed on the **Ablation-Train and Validation sets** (derived from raw data) to generate ground truth. The final classifier (T009) trains exclusively on this ablation-derived ground truth. If n < 300, the system defaults to a fixed k=2 heuristic (T015) instead of training.
- **Review Concerns Addressed**: T034 addresses data source validation; T035 addresses dry-run verification; T036 addresses auditability of minimum context logic; T037 addresses reproducibility of statistical runs; T031/T031b/T031c addresses performance benchmarking and optimization with concrete artifacts; T040 addresses documentation of data flow; T008c/T009/T015 addresses the n < 300 heuristic fallback; T022a addresses the hard gate for SC-002; T014a/T014 addresses validation set integrity; **T038 addresses engine stability and error propagation**; **T016a addresses edge case verification**; **T023 addresses token reduction consistency**; **T029/T030 address documentation and cleanup**.
- **Key Changes in this Revision**:
 - **T005**: Updated to write warnings to `edge_case_warnings.log`.
 - **T007b**: Clarified as extending T006; removed [P] to reflect T014a dependency and moved to Phase 2b.
 - **T008c**: Updated to log specific warning text and ensure T014 depends on it.
 - **T009**: Updated to explicitly verify T014 and T008c outputs.
 - **T016a**: Added to verify edge case logs.
 - **T020**: Clarified "no-store" requirement.
 - **T022/T023**: Added std_dev calculation to satisfy SC-004.
 - **T025**: Added verification of test selection logic.
 - **T029/T030**: Marked complete with concrete deliverables.
 - **T031b/T031c**: Split into analysis and refactoring tasks.
 - **T032/T038/T039/T040**: Added specific file/function names and verification steps.
 - **Data Flow**: Corrected to show T006 -> T014a -> T007b/T008b.