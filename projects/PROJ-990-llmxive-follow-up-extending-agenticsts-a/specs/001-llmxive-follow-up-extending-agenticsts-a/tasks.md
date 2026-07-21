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

**Data Flow**: T006 (Parser) -> T014a (Split) -> Parallel (T007b: Static Proxy, T008b: Ablation) -> T008c (Validator) -> T014 (Validate) -> T009 (Train)

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters. Define `TOKEN_BUDGET=4096`, `MIN_CONTEXT=256` as explicit constants loaded from config or env vars.
- [X] T006 [P] Implement `code/parser.py` to extract per-turn metrics (health, threat, deck size) AND **legal move distributions** from raw trajectory logs in `data/raw/`. **Output**: `data/processed/metrics_with_moves.csv`. **Note**: Must include the probability distribution of available legal moves to support entropy calculation.
- [X] T005 [P] Implement `code/entropy.py` to calculate **Shannon entropy** of the legal move distributions extracted by T006. **Logic**: Calculate $H = -\sum p_i \log_2(p_i)$. If calculation returns NaN or Inf, return a sentinel value (e.g., `float('inf')`) and log a warning. **Input**: `data/processed/metrics_with_moves.csv`. **Depends on**: T006.
- [X] T007 Create `data/processed/` directory structure and schema validation for derived metrics.
- [X] T007b [P] Implement `code/parser.py` (extended) to extract **static-log-derived utility** (frequency of layer retrieval) from raw trajectory logs as a distinct artifact. **Input**: `data/processed/validation_set.csv` (from T014a). **Output**: `data/processed/static_log_proxy.json` (schema: `{layer_id, retrieval_frequency}`). **Constraint**: Must process ONLY the validation set to prevent data leakage. **Depends on**: T006, T014a.
- [X] T014a [P] Implement `code/splitter.py` to perform a stratified data split of the **raw** trajectories into FOUR distinct sets: **Train**, **Ablation-Train**, **Validation**, and **Test**. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`. **Note**: The **Validation set** MUST contain at least 20 trajectories (FR-006) and is distinct from the Ablation-Train set. The **Ablation-Train set** is used exclusively to generate ground-truth utility labels via ablation. The **Test set** is reserved for final baseline/dynamic evaluation. The **Train set** is for model training. This split must occur BEFORE any ablation study. **Constraint**: Assert `len(validation_set) >= 20` and raise error if not.
- [X] T008a [P] Implement `code/ablation.py` (engine function) as a reusable function to run the ablation study on a given dataset file. **Input**: Dataset file path, engine configuration. **Output**: `data/processed/ablation_labels_{dataset_name}.json` (schema: `{layer_id, utility_score}`). **Note**: This function is called by T008 and T008b.
- [X] T008 [US1] Execute ablation study on the **Ablation-Train set** using the function from T008a. **Input**: `data/processed/ablation_train_set.csv` (from T014a). **Output**: `data/processed/ablation_labels_train.json` (schema: `{layer_id, utility_score}`). **Depends on**: T006, T014a, T008a.
- [X] T008b [US1] Execute ablation study on the **Validation set** using the function from T008a. **Input**: `data/processed/validation_set.csv` (from T014a). **Output**: `data/processed/ablation_labels_validation.json`. **Depends on**: T006, T014a, T008a.
- [X] T008c [US1] Implement `code/validator.py` to check sample count. **Logic**: If `n < 300`, **MUST** log a WARNING (not error), generate `data/processed/fallback_k2_labels.csv` containing fixed k=2 labels, and **proceed** to T009 (which will use fallback data). If `n >= 300`, proceed to allow classifier training (T009) using ablation labels. **Action**: For n=298 (the actual dataset), this task MUST generate the fallback and continue. **Depends on**: T008, T008b.
- [X] T014 [US1] Implement proxy validation logic in `code/classifier.py`. **Logic**: Assert `len(validation_set) >= 20` (raise error if not). Check Pearson correlation (≥ 0.7) between **static log proxy** (from T007b) and ablation utility (from T008b) on the **Validation set**. **Output**: `data/processed/proxy_validation_report.json`. **Action**: Raise exception if r < 0.7. **Note**: The Validation set is distinct from the Ablation-Train set and serves as the required hold-out set for FR-006. **Depends on**: T007b, T008b, T014a.
- [X] T009 [US1] Implement `code/classifier.py` to train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Input**: `data/processed/ablation_labels_train.json` (ablation-derived ground-truth utility from T008) OR `data/processed/fallback_k2_labels.csv` (from T008c if n < 300). **Target**: `utility_score`. **Split**: 80/20 (within train set). **Output**: `models/layer_utility_classifier.pkl`. **Note**: Trains exclusively on ablation-derived ground truth or fallback. **Condition**: Executes regardless of T008c outcome (using appropriate input). **Depends on**: T008, T008c, T014 (must pass).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

**Independent Test**: Run held-out trajectories through Dynamic, Static, and Random agents; verify variable layer selection, token budget compliance, and outcome logging.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Unit test for entropy calculation edge cases (NaN, Inf, zero moves) in `tests/unit/test_entropy.py`.
- [X] T013 [P] [US1] Unit test for token budget enforcement and minimum context floor in `tests/unit/test_simulator.py`.

### Implementation for User Story 1 (Dynamic Policy)

- [X] T015 [US1] Implement dynamic layer selection logic in `code/simulator.py`. **Logic**: Use trained model (T009) to predict top-k layers based on current turn entropy (from T005), **integrating** this prediction with the token budget constraint logic (4096 tokens). **Depends on**: T009, T005, T014a (test_set).
- [X] T016 [US1] Add logic to enforce a hard token budget and a minimum context floor in `code/simulator.py`. **Logic**:
 1. **Maximum Budget**: If predicted token count > 4096, truncate or prune the least useful layers until the prompt size is ≤ 4096.
 2. **Minimum Floor**: If the selected layers result in a token count < 256 tokens, **append the 'Current Objective' layer** to enforce the minimum context.
 3. **NaN/Inf Handling**: If entropy returns a sentinel (NaN/Inf), default to retrieving the **full "all-layers" set** for that turn and log a warning. **Note**: This is an edge-case override within the budget enforcement, distinct from T015's prediction.
 **Depends on**: T015.
- [X] T017 [US1] **Execute Dynamic Simulation**. **Logic**: Invoke the `agenticsts-engine` (via T018) using the logic from T015 and T016 on the **test set**. **Output**: `data/processed/simulation_logs_dynamic.json`. **Depends on**: T015, T016, T018, T014a.

### Implementation for User Story 2 (Baselines & Aggregation)

**Note**: Baselines (T019, T020) depend on the game engine execution (T018) to generate new outcomes.

- [X] T018 [P] Implement `code/engine_runner.py` to invoke the `agenticsts-engine` for re-simulation. **Logic**: Accept a trajectory file and a memory policy (Dynamic, Static, Random) as input, execute the engine, and output raw simulation logs. **Output**: `data/processed/simulation_logs_{policy}.json`. **Depends on**: T006, T014a.
- [X] T019 [US2] Implement "Static All-Layers" baseline execution. **Logic**: Invoke `code/engine_runner.py` (T018) with policy="Static" on the **test set**. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018, T014a.
- [X] T020 [US2] Implement "No-Store Random" baseline execution. **Logic**: Invoke `code/engine_runner.py` (T018) with policy="Random" on the **test set**. **Logic**: **Select k layers uniformly at random** for each turn (no memory of past layers). **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018, T014a.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition. **Input**: Outputs from T017, T019, T020.
- [X] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Schema**: `condition, win_rate, avg_tokens`. **Aggregation Logic**: Mean of win_rate and token columns grouped by condition.
- [X] T022a [US2] Implement verification logic to calculate percentage reduction in token usage. **Output**: Generate `data/processed/token_reduction_verification.json` containing a boolean field `passed` (true if reduction ≥ 30%) and a numeric field `actual_reduction_percent`. **Action**: Do NOT exit with code 1 if `passed` is false; the pipeline must continue to generate statistical reports. **Input**: `data/processed/baseline_comparison.csv`. **Output**: `data/processed/token_reduction_verification.json`. **Depends on**: T022.

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
 2. **If `is_divergent` is true** (unpaired trajectories): Execute **Permutation Test** (or Z-test) for win/loss outcomes.
 3. **If `is_divergent` is false** (paired/deterministic trajectories): **Implement McNemar's test** for win/loss outcomes explicitly.
 4. **Token Usage**: **Implement paired t-test** for token usage (check normality assumption; if failed, use Wilcoxon signed-rank test).
 5. **Correction**: **Apply Bonferroni correction** to the family of tests comprising the win rate test AND the token usage test simultaneously to control the family-wise error rate.
 **Output**: `data/processed/statistical_results.json`. **Depends on**: T024a, T021.
- [X] T028 [US3] Generate final statistical report in `data/processed/statistical_results.json`. **Schema**: `{p_value, effect_size, test_type, bonferroni_adjusted, divergence_status, token_reduction_percent, token_reduction_passed}`. **Includes**: SC-001/SC-003 metrics. **Note**: Must ingest `token_reduction_verification.json` from T022a to report the token reduction metric. **Depends on**: T025, T022a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `README.md` and `quickstart.md`.
- [ ] T030 Code cleanup and refactoring.
- [ ] T031 [P] Add performance benchmarking script `code/benchmark.py` that logs execution time per phase and total runtime to `data/processed/benchmark_log.json`.
- [ ] T031b [P] **Optimize code based on benchmark results**. **Logic**: If total runtime > 6 hours, refactor code to reduce runtime. **Output**: Generate `data/processed/optimization_report.md` detailing specific changes made and their measured impact on runtime. **Depends on**: T031.
- [ ] T032 [P] Additional unit tests for edge cases (n < 300 warning logic) in `tests/unit/`.
- [ ] T033 Run `quickstart.md` validation to ensure reproducibility.
- [X] T034 [P] Add explicit data source validation in `code/parser.py` to ensure `data/raw/` contains non-empty, checksum-verified trajectory files before processing begins, raising a clear error if missing or corrupted.
- [X] T035 [P] Implement a "dry-run" mode in `code/main.py` that executes the full pipeline on a single trajectory (or first 5) to verify data flow and edge case handling (NaN entropy, budget truncation) before full-scale execution.
- [X] T036 [P] Add detailed logging of the "Current Objective" layer append logic in `code/simulator.py` (T016) to `data/processed/simulation_logs.json` for auditability of minimum context floor enforcement.
- [X] T037 [P] Create a `data/processed/analysis_config.json` snapshot that records the exact random seeds, hyperparameters, and dataset split ratios used for the specific run, ensuring full reproducibility of the statistical results.
- [ ] T039 [P] Add a `--stream` flag to `code/parser.py` to support chunked processing of large trajectory files, ensuring memory usage stays below 7GB even if the raw dataset grows beyond current expectations.
- [ ] T040 [P] Write a comprehensive `CONTRIBUTING.md` section detailing the specific data flow dependencies (T006 -> T014a -> (T007b || T008b) -> T008c -> T014 -> T009) to prevent future implementation order errors.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks all user stories**.
 - **Critical Flow**: T006 -> T014a -> (T007b || T008b) -> T008c -> T014 -> T009.
 - T009 (Training) MUST wait for T014 (Validation) to pass AND T008c (Sample Size) to handle fallback if needed.
- **User Stories (Phase 3)**: Depends on Foundational (Phase 2).
 - T015 (Dynamic Logic) depends on T009 (Model).
 - T017 (Dynamic Execution) depends on T015, T018.
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
- T006, T007b, T014a can run in parallel in Phase 2.
- T019, T020 can run in parallel in Phase 3 (after T018).
- All tests for a user story marked [P] can run in parallel.
- T032, T034, T035, T036, T037, T039, T040 can run in parallel in Phase N.

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
- **Methodology**: Ablation study (T008, T008b) is performed on the **Ablation-Train and Validation sets** (derived from raw data) to generate ground truth. The final classifier (T009) trains exclusively on this ablation-derived ground truth.
- **Review Concerns Addressed**: T034 addresses data source validation; T035 addresses dry-run verification; T036 addresses auditability of minimum context logic; T037 addresses reproducibility of statistical runs; T031/T031b addresses performance benchmarking and optimization with concrete artifacts; T040 addresses documentation of data flow.
- **Key Changes in this Revision**:
 - **T014a**: Split into FOUR sets (Train, Ablation-Train, Validation, Test) to break circular dependency in proxy validation. Explicitly enforces min 20 trajectories in Validation set.
 - **T007b**: Restricted to Validation set to prevent data leakage.
 - **T008b**: Runs on Validation set for proxy ground truth.
 - **T008c**: Logic updated to generate fallback artifact and proceed (not block) if n < 300.
 - **T018**: New task to invoke game engine for baseline simulations.
 - **T017**: New task to Execute Dynamic Simulation (separated from logic implementation T015).
 - **T019/T020**: Updated to depend on T018 and explicitly invoke engine.
 - **T022a**: Removed hard exit code; now records pass/fail state and reduction percentage in JSON.
 - **T025**: Updated to explicitly apply Bonferroni correction to the family of tests (win rate AND token usage) and define test selection logic based on divergence.
 - **T031/T031b**: Split into benchmarking and optimization tasks with concrete deliverables.
 - **T038**: Removed (redundant).
 - **Data Flow**: Corrected to show T006 -> T014a -> Parallel (T007b, T008b).