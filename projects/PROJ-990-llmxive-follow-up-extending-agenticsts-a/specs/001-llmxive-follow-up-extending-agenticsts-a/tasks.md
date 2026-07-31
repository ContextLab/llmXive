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
- [X] T003a [P] Generate `contracts/trajectory.schema.yaml` defining the trajectory schema (trajectory_id, turn, legal_moves, etc.) as per `data-model.md`.
- [X] T003b [P] **Generate Mock Trajectories**. **Logic**: Create a deterministic, small JSONL file with a set of trajectories matching the schema in `contracts/trajectory.schema.yaml`. **Constraint**: This is ONLY used if `DEV_MODE=true`. **Output**: `data/fixtures/mock_trajectories.jsonl`. **Depends on**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data processing, model training, and validation gates.
**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete.

**Data Flow**: T005b (Real Data Ingest) -> T006a (Parser) -> T006b (Entropy) -> T014a (Split) -> T008 (Ablation) -> T014 (Validator) -> T009 (Train)

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters. Define `TOKEN_BUDGET=4096`, `MIN_CONTEXT=256`, AND `K_RANDOM_BASELINE=2` as explicit constants loaded from config or env vars.
- [X] T005b [US1] **Ingest Real AgenticSTS Trajectories**. **Logic**: Fetch the existing AgenticSTS trajectories from the canonical source: `. **Action**: Download raw JSONL files to `data/raw/`. **Validation**: Verify checksums against `manifest.json` fetched from the same repo. **Output**: `data/raw/agenticsts_trajectories.jsonl`. **Constraint**: This task MUST run BEFORE T006a. **Skip Condition**: If `data/raw/agenticsts_trajectories.jsonl` already exists and checksums match, skip. **CRITICAL**: If this task fails (network error, checksum mismatch), the pipeline MUST raise `FileNotFoundError` and STOP. No fallback to synthetic data is permitted. **Depends on**: None.
- [X] T005c [P] **Fetch Checksum Manifest**. **Logic**: Fetch ` to `data/raw/manifest.json`. **Output**: `data/raw/manifest.json`. **Depends on**: None.
- [X] T005a [US1] **Log Data Availability Status**. **Logic**: Check if `data/raw/agenticsts_trajectories.jsonl` exists. **Action**: If missing, write `{"level": "ERROR", "message": "Real data missing; pipeline blocked.", "timestamp": "<ISO8601>"}` to `data/processed/edge_case_warnings.log` and set `PIPELINE_BLOCKED=true` in `data/processed/config_state.json`. **Constraint**: This task runs ONLY if T005b failed or was skipped due to missing data. **Depends on**: T005b.
- [ ] T006a [US1] Implement `code/parser.py` to extract per-turn metrics from raw trajectory logs in `data/raw/`. **Input**: JSONL/JSON files from T005b. **Validation**: MUST validate each file against `contracts/trajectory.schema.yaml` (generated in T003a) before processing. Raise `ValueError` if schema mismatch. **Constraint**: If `data/raw/` is empty or missing, raise `FileNotFoundError` ("Real data missing; pipeline cannot proceed"). **NO** `try/except` blocks that fall back to synthetic data. **Output**: `data/processed/metrics_with_moves.csv`. **Depends on**: T005b, T003a.
- [ ] T006b [US1] Implement entropy calculation in `code/entropy.py`. **Logic**: Calculate Shannon entropy of the legal move distributions extracted by T006a. **Edge Case Handling**: If calculated entropy is `NaN` or `Infinity`, log a warning to `data/processed/edge_case_warnings.log` and return a sentinel value that triggers the "all-layers" fallback in T015b. **Input**: `data/processed/metrics_with_moves.csv`. **Skip Condition**: If `data/processed/metrics_with_moves.csv` does not exist (e.g., T006a was skipped), skip this task. **Output**: `data/processed/entropy_metrics.csv`. **Depends on**: T006a.
- [ ] T008 [US1] **Generate Ground Truth Labels (Ablation Study)**. **Logic**: Run the ablation study on the training set to generate utility labels by re-running the game engine with specific layers removed. **Algorithm**: Iterate over each layer defined in `contracts/trajectory.schema.yaml`: 1. Remove layer from trajectory context. 2. Execute `code/engine_runner.py --ablate-layer <layer_name>`. 3. Record win rate delta vs baseline. 4. Store delta as utility. 5. Aggregate results into `data/processed/ablation_labels_train.json`. **Input**: `data/raw/agenticsts_trajectories.jsonl`. **Output**: `data/processed/ablation_labels_train.json`. **Constraint**: If this fails, the pipeline MUST NOT proceed with mock data. The research is invalid without ground truth. **Depends on**: T005b, T018. <!-- FAILED: unspecified -->
- [ ] T008d [US1] **Ablation Failure Handling**. **Logic**: If T008 fails to generate ablation labels (due to engine error, not missing data), log a CRITICAL error to `data/processed/edge_case_warnings.log` and generate `data/processed/fallback_flag.json` with `{"fallback": true, "use_heuristic": true, "reason": "Ablation study failed"}`. **Action**: Do NOT generate mock data. The pipeline must either fail or switch to a fixed-k heuristic (k=2) for training. **Constraint**: This task runs ONLY if T008 fails. **Depends on**: T008 (Conditional).
- [ ] T014a [US1] Implement data splitting logic in `code/splitter.py`. **Logic**: Split data into train/validation/test sets. **Edge Case Handling**: If training set size `n < 300`, log a WARNING to `data/processed/edge_case_warnings.log` stating "Statistical power marginal (n < 300)" and automatically set a flag to use the fixed-k heuristic (k=2) defined in T008d. **Input**: `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`. **Depends on**: T006a.
- [ ] T014 [US3] **Implement Proxy Validation Logic**. **Logic**:
 1. **Generate Proxy**: If static logs exist, calculate `proxy_utility` for each layer (frequency-weighted score) and save to `data/processed/proxy_utility_labels.csv`.
 2. **Validate**: Load `proxy_utility_labels.csv` and `data/processed/ablation_labels_train.json`. Join on `trajectory_id` and `layer_name`. Calculate Pearson correlation.
 3. **Gate**: If correlation < 0.7, set `proxy_valid=false` and trigger fallback heuristic path (T008d).
 **Constraint**: Validation MUST use the hold-out set of at least 20 trajectories where ground truth is established via ablation.
 **Output**: `data/processed/proxy_validation_report.json` containing a boolean `proxy_valid`. **Depends on**: T007 (Merged), T008, T014a.
- [X] T009 [US1] Train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Input**: Ablation labels from T008 or fallback heuristic, if enabled. **Output**: `models/layer_utility_classifier.pkl`. **Depends on**: T014a, T014, T008 (or T008d).
- [X] T018 [P] [US1/US2] **Implement Engine Runner**. **Logic**: Implement `code/engine_runner.py` to invoke the engine for re-simulation. Provide CLI flags `--mode <dynamic|static|random>` and `--ablate-layer <layer_name>`. **Depends on**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
- [X] T012 [P] [US1] Unit test for entropy calculation edge cases in `tests/unit/test_entropy.py`.

### Implementation for User Story 1 (Dynamic Policy)
- [X] T015a [US1] Implement Minimum Context Floor Logic in `code/simulator.py`. **Logic**: Before any selection, check if the calculated context is below `MIN_CONTEXT` (256 tokens). If so, append the "Current Objective" layer immediately. **Output**: Intermediate state with floor applied.
- [X] T015b [US1] Implement Dynamic Layer Selection in `code/simulator.py`. **Logic**: Use the trained model (T009) to predict utility, then select top-k layers based on entropy prediction or fallback heuristic. **Edge Case Handling**: If T006b returned a NaN/Inf entropy sentinel, force selection of the full "all-layers" set. **Input**: State from T015a.
- [X] T015c [US1] Enforce Maximum Token Budget in `code/simulator.py`. **Logic**: Ensure the final prompt size is ≤ 4096 tokens. If exceeded, prune least useful layers. **Input**: State from T015b.
- [ ] T017 [US1] Execute Dynamic Simulation on the test set. **Output**: `data/processed/simulation_logs_dynamic.json`. **Depends on**: T015a, T015b, T015c, T018.
- [ ] T019 [US2] [P] Implement "Static All-Layers" baseline execution. **Logic**: Retrieve ALL available memory layers (as defined in `contracts/trajectory.schema.yaml`) for every turn. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018.
- [ ] T020 [US2] [P] Implement "No-Store Random" baseline execution. **Logic**: Select exactly k=2 layers uniformly at random from the available set for every turn. **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition.
- [ ] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Logic**: Calculate and report token reduction metrics using formula: `(static_tokens - dynamic_tokens) / static_tokens`. **Constraint**: If `token_reduction_pct` < 30, set `threshold_met=false` in `data/processed/build_status.json` but DO NOT exit with code 1. The pipeline must continue to generate statistical evidence. **Schema**: `condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct, threshold_met`. **Depends on**: T017, T019, T020.
- [ ] T023 [US2] Implement verification logic to calculate token reduction consistency. **Output**: `data/processed/token_consistency_report.json` with boolean `passed`. **Logic**: Calculate standard deviation of token savings. If `std_dev < 0.10 * mean_savings`, `passed=true`. Else, `passed=false`. **Depends on**: T022.

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [X] T023a [P] [US3] Unit test for McNemar's test selection logic in `tests/unit/test_stats.py`.

- [X] T024 [P] [US3] Verify Paired Status in `code/stats.py`. **Logic**: Confirm that Dynamic and Static runs share the same `trajectory_id` and `initial_state_hash`. **Action**: Compute SHA256 hash of `json.dumps({'initial_state_hash': str, 'trajectory_id': str}, sort_keys=True)` for each trajectory. **Output**: `data/processed/paired_status.json` (boolean `is_paired`).
- [X] T025a [US3] Execute Statistical Tests & Selection Logic. **Logic**: Check `is_paired` from T024. If true, run McNemar's test on win/loss outcomes. If false, run Permutation Test or Z-test. Run paired t-test on token usage and apply Bonferroni correction. **Output**: `data/processed/mcnemar_results.json` (or permutation results) and `data/processed/ttest_results.json`. **Depends on**: T024.
- [X] T025b [US3] Execute Paired T-Test & Bonferroni in `code/stats.py`. **Logic**: Run paired t-test on token usage, apply Bonferroni correction. **Output**: `data/processed/ttest_results.json`. **Depends on**: T025a (if not already merged). *Note: Logic merged into T025a for clarity.*

---

## Phase 5: Performance & Validation (Optional/Advanced)

**Goal**: Ensure the pipeline meets performance constraints and statistical power requirements.

- [X] T031c [P] [US1] **Runtime Monitoring**. **Logic**: Monitor total runtime of the simulation phase. **Action**: If `total_runtime` (in hours) > 6, refactor code to enable streaming or reduce batch size. **Output**: `data/processed/runtime_report.json`.
- [X] T039 [P] [US1] **Memory Usage Verification**. **Logic**: Verify memory usage < 7GB with `--stream` on a 1GB file. **Action**: Use `psutil` to monitor peak RSS memory. **Output**: `data/processed/memory_report.json`.
- [X] T044 [P] [US1] **Power Analysis**. **Logic**: Perform power analysis with alpha=0.05, power=0.8, and expected effect size=0.2. **Output**: `data/processed/power_analysis.json`.
- [ ] T050 [P] [US3] **Divergence Check**. **Logic**: Calculate divergence (percentage of trajectories where final state hash differs). Flag if divergence > 10%. **Output**: `data/processed/divergence_report.json`.

---

## Phase 6: Revision & Edge Case Resolution (Addressing Review Concerns)

**Goal**: Resolve specific analysis findings regarding NaN entropy, sample size warnings, and data integrity.
**Note**: Tasks T051, T052, T053, and T054 have been removed as standalone tasks. Their logic has been integrated into upstream tasks (T006b, T014a, T055, T025a respectively) to ensure correct dependency ordering and eliminate invalid parallel tags.
**Note**: T055 has been removed as a standalone task; its logic is now enforced in T005b and T006a.