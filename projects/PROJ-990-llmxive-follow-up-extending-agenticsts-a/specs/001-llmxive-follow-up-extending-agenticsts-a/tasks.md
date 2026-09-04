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
- [X] T003a-verify [P] **Verify Schema Existence**. **Logic**: Check that `contracts/trajectory.schema.yaml` exists and is valid YAML. **Action**: If missing or invalid, raise `FileNotFoundError` ("Schema missing; T008 cannot proceed"). **Output**: `contracts/trajectory.schema.yaml` (verified). **Constraint**: Must run before T008. **Depends on**: T003a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data processing, model training, and validation gates.
**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete.

**Data Flow**: T005c (Fetch Manifest) -> T005b (Real Data Ingest) -> T005a (Log Status) -> T006a (Parser) -> T014a (Sample Check) -> T004 (Engine Install) -> T018 (Engine Runner) -> T008 (Ablation) / T008b (Heuristic) -> T008c (Hold-out Ablation) -> T008d (Merge Utility) -> T014 (Validator) -> T009 (Train)

- [X] T005c [P] **Fetch Checksum Manifest**. **Logic**: Fetch `manifest.json` from `https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json` to `data/raw/manifest.json`. **Output**: `data/raw/manifest.json`. **Depends on**: None.
- [X] T005b [US1] **Ingest Real AgenticSTS Trajectories**. **Logic**: Fetch the existing AgenticSTS trajectories from the canonical source using `huggingface-cli`. **Command**: `huggingface-cli download agenticsts/trajectories --repo-type dataset --local-dir data/raw --filename trajectories.jsonl`. **Action**: Download raw JSONL files to `data/raw/`. **Validation**: Verify checksums against `data/raw/manifest.json` fetched in T005c. **Output**: `data/raw/agenticsts_trajectories.jsonl`. **Constraint**: This task MUST run BEFORE T006a. **Skip Condition**: If `data/raw/agenticsts_trajectories.jsonl` already exists and checksums match, skip. **CRITICAL**: If this task fails (network error, checksum mismatch), the pipeline MUST raise `FileNotFoundError` and STOP. No fallback to synthetic data is permitted. **Depends on**: T005c.
- [X] T005a [US1] **Log Data Availability Status**. **Logic**: Check if `data/raw/agenticsts_trajectories.jsonl` exists. **Action**: If missing, write `{"level": "ERROR", "message": "Real data missing; pipeline blocked.", "timestamp": "<ISO8601>"}` to `data/processed/edge_case_warnings.log` and set `PIPELINE_BLOCKED=true` in `data/processed/config_state.json`. **Constraint**: This task runs AFTER T005b to ensure the file existence check happens after the download attempt. **Depends on**: T005b.
- [X] T004 [US1] **Install AgenticSTS Engine**. **Logic**: Install the game engine required for ablation and simulation. **Command**: `pip install agenticsts-engine` OR `git clone <repo> && pip install -e .`. **Output**: Engine available in PATH. **Depends on**: T001.
- [X] T018 [US1/US2] **Implement Engine Runner**. **Logic**: Implement `code/engine_runner.py` to invoke the engine for re-simulation. Provide CLI flags `--mode <dynamic|static|random>` and `--ablate-layer <layer_name>`. **Constraint**: Must be executable before T008 runs. **Depends on**: T004.
- [X] T006a [US1] Implement `code/parser.py` to extract per-turn metrics from raw trajectory logs in `data/raw/`. **Input**: JSONL/JSON files from T005b. **Validation**: MUST validate each file against `contracts/trajectory.schema.yaml` (generated in T003a) before processing. Raise `ValueError` if schema mismatch. **Constraint**: If `data/raw/` is empty or missing, raise `FileNotFoundError` ("Real data missing; pipeline cannot proceed"). **NO** `try/except` blocks that fall back to synthetic data for file I/O. **Merge Logic**: If ablation labels exist (from T008), merge the `utility_delta` column into the output. **Strict Path Check**: MUST only read from `data/raw/`. Ignore `data/fixtures/`. **Output**: `data/processed/metrics_with_moves.csv` (Columns: `trajectory_id`, `turn`, `health_ratio`, `enemy_threat`, `deck_size`, `move_entropy`, `utility_delta` if available). **Depends on**: T005b, T003a-verify.
- [X] T006b [US1] Implement entropy calculation in `code/entropy.py`. **Logic**: Calculate Shannon entropy of the legal move distributions extracted by T006a. **Edge Case Handling**: If calculated entropy is `NaN` or `Infinity`, log a warning to `data/processed/edge_case_warnings.log` and return a sentinel value that triggers the "all-layers" fallback in T015b. **Input**: `data/processed/metrics_with_moves.csv`. **Skip Condition**: If `data/processed/metrics_with_moves.csv` does not exist (e.g., T006a was skipped), skip this task. **Output**: `data/processed/entropy_metrics.csv`. **Depends on**: T006a.
- [X] T014a [US1] Implement data splitting logic in `code/splitter.py`. **Logic**: Split data into train/validation/test sets. **Edge Case Handling**: If training set size `n < 300`, log a WARNING to `data/processed/edge_case_warnings.log` stating "Statistical power marginal (n < 300)" and set `USE_HEURISTIC=true` in `data/processed/config_state.json`. **Input**: `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`, `data/processed/config_state.json`. **Depends on**: T006a.
- [X] T008 [US1] **Generate Ground Truth Labels (Ablation Study - Training Set)**. **Logic**: Run the ablation study on the **training set** to generate utility labels by re-running the game engine with specific layers removed. **Algorithm**: Iterate over each layer defined in `contracts/trajectory.schema.yaml` (verified by T003a-verify): 1. Remove layer from trajectory context. 2. Execute `python code/engine_runner.py --ablate-layer <layer_name> --trajectory <id>`. 3. Record win rate delta vs baseline. 4. Store delta as utility. 5. Aggregate results into `data/processed/ablation_labels_train.json`. **Input**: `data/raw/agenticsts_trajectories.jsonl`, `data/processed/train_set.csv`. **Output**: `data/processed/ablation_labels_train.json`. **Constraint**: If this fails (engine error), the pipeline MUST NOT proceed. The research is invalid without ground truth. **Skip Condition**: If `data/processed/config_state.json` has `USE_HEURISTIC=true` (set by T014a), SKIP this task and proceed to T008b. **Depends on**: T005b, T018, T003a-verify, T014a, T004.
- [X] T008b [US1] **Generate Heuristic Labels (Fallback for n < 300)**. **Logic**: If `USE_HEURISTIC=true` (from T014a), generate labels using a fixed-k=2 heuristic. **Action**: Create `data/processed/heuristic_proxy_labels_train.json` with heuristic labels. **Constraint**: This task runs ONLY if `USE_HEURISTIC=true`. If T008 fails due to engine error (and `USE_HEURISTIC=false`), the pipeline halts. **Output**: `data/processed/heuristic_proxy_labels_train.json`. **Depends on**: T014a.
- [X] T008c [US1] **Generate Ground Truth Labels (Ablation Study - Hold-out Set)**. **Logic**: Run the ablation study on the **hold-out set** (at least 20 trajectories) to generate utility labels for proxy validation. **Algorithm**: Same as T008 but using `data/processed/validation_set.csv` (or a specific hold-out split). **Input**: `data/raw/agenticsts_trajectories.jsonl`, `data/processed/validation_set.csv`. **Output**: `data/processed/ablation_labels_holdout.json`. **Constraint**: Must run if `USE_HEURISTIC=false`. If `USE_HEURISTIC=true`, skip. **Depends on**: T005b, T018, T003a-verify, T014a, T004.
- [X] T008d [US1] **Extract and Merge Ground Truth Utility Labels**. **Logic**: Convert ablation JSON outputs into structured CSVs and merge them with the metrics dataset. **Action**: 1. Load `data/processed/ablation_labels_train.json` (or `heuristic_proxy_labels_train.json` if `USE_HEURISTIC=true`). 2. Load `data/processed/metrics_with_moves.csv` (from T006a). 3. Join on `trajectory_id` and `layer_name`. 4. Output `data/processed/ground_truth_utility_train.csv` (Columns: `trajectory_id`, `layer_name`, `utility_delta`, `features...`). **Input**: `data/processed/ablation_labels_train.json` (or T008b output), `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/ground_truth_utility_train.csv`. **Depends on**: T006a, T008, T008b.
- [X] T014 [US3] **Implement Proxy Validation Logic**. **Logic**:
 1. **Generate Proxy**: Derive `proxy_utility_labels.csv` from `data/processed/metrics_with_moves.csv` (T006a output) by calculating frequency-weighted scores for each layer. **Schema**: Columns `trajectory_id`, `layer_name`, `proxy_utility`.
 2. **Validate**: Load `proxy_utility_labels.csv` and `data/processed/ground_truth_utility_holdout.csv` (from T008d). Join on `trajectory_id` and `layer_name`. Calculate Pearson correlation using `scipy.stats.pearsonr`.
 3. **Gate**: If correlation < 0.7, set `proxy_valid=false` and log warning. **Do NOT trigger heuristic fallback here.** The system MUST rely on the ablation study (ground truth) if the proxy is invalid. Heuristic fallback is only for n<300 (T014a).
 **Constraint**: Validation MUST use the hold-out set of at least 20 trajectories where ground truth is established via ablation (T008c). **Skip Condition**: If `USE_HEURISTIC=true` (from T014a), SKIP this task (heuristic labels do not require proxy validation).
 **Output**: `data/processed/proxy_validation_report.json` containing a boolean `proxy_valid`. **Depends on**: T008c, T008d, T006a.
- [X] T009 [US1] Train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Input**: `data/processed/ground_truth_utility_train.csv` (from T008d). **Output**: `models/layer_utility_classifier.pkl`. **Constraint**: Proceed even if T014 reports `proxy_valid=false`. Use ablation labels regardless of proxy validity. **Dependency Logic**: If `USE_HEURISTIC=true`, depend on T008b directly. If `USE_HEURISTIC=false`, depend on T014 (to ensure validation passed or was skipped). **Depends on**: T008d, T014 (conditional).

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
- [X] T017 [US1] Execute Dynamic Simulation on the test set. **Command**: `python code/main.py --mode dynamic --split test`. **Output**: `data/processed/simulation_logs_dynamic.json`. **Depends on**: T015a, T015b, T015c, T018, T009.
- [X] T019 [US2] [P] Implement "Static All-Layers" baseline execution. **Logic**: Retrieve ALL available memory layers (as defined in `contracts/trajectory.schema.yaml`) for every turn. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018.
- [X] T020 [US2] [P] Implement "No-Store Random" baseline execution. **Logic**: Select exactly k=2 layers uniformly at random from the available set for every turn. **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition.
- [X] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Logic**: Calculate and report token reduction metrics using formula: `(static_tokens - dynamic_tokens) / static_tokens`. **Constraint**: If `token_reduction_pct` < 30, set `threshold_met=false` in `data/processed/build_status.json` but DO NOT exit with code 1. The pipeline must continue to generate statistical evidence. **Schema**: `condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct, threshold_met`. **Depends on**: T017, T019, T020.

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [X] T023a [P] [US3] Unit test for McNemar's test selection logic in `tests/unit/test_stats.py`.

- [X] T023 [US2] Implement verification logic to calculate token reduction consistency. **Output**: `data/processed/token_consistency_report.json` with boolean `passed`. **Logic**: Calculate standard deviation of token savings. Define `mean_savings` as the mean of `abs(static_tokens - dynamic_tokens)` across the test set. If `std_dev < 0.10 * mean_savings`, `passed=true`. Else, `passed=false`. **Depends on**: T022.

- [X] T024 [P] [US3] Verify Paired Status in `code/stats.py`. **Logic**: Confirm that Dynamic and Static runs share the same `trajectory_id` and `initial_state_hash`. **Action**: Compute SHA256 hash of `json.dumps({'initial_state_hash': str, 'trajectory_id': str}, sort_keys=True)` for each trajectory. **Output**: `data/processed/paired_status.json` (boolean `is_paired`).
- [X] T025a [US3] Execute Statistical Tests & Selection Logic. **Logic**: Check `is_paired` from T024. 
  - **If True**: Run McNemar's test on win/loss outcomes.
  - **If False**: 
    - If `n < 1000`: Run Permutation Test (10,000 iterations).
    - If `n >= 1000`: Run Z-test for proportions.
  - Run paired t-test on token usage and apply Bonferroni correction.
  **Output**: `data/processed/mcnemar_results.json` (or permutation/Z-test results) and `data/processed/ttest_results.json`. **Depends on**: T024, T017, T019.
- [X] T025b [US3] Execute Paired T-Test & Bonferroni in `code/stats.py`. **Logic**: Run paired t-test on token usage, apply Bonferroni correction. **Output**: `data/processed/ttest_results.json`. **Depends on**: T025a (if not already merged). *Note: Logic merged into T025a for clarity.*
- [X] T026 [US3] **Generate Success Criteria Report**. **Logic**: Aggregate results from T022, T025a, T025b. **Action**: Create `data/processed/success_criteria_report.json` mapping SC-001 to SC-004 to pass/fail status. **Constraint**: If ANY Success Criterion (SC-001 to SC-004) is false, the script MUST exit with code 1 (FAIL). **Output**: `data/processed/success_criteria_report.json`. **Depends on**: T022, T025a.

---

## Phase 5: Performance & Validation (Optional/Advanced)

**Goal**: Ensure the pipeline meets performance constraints and statistical power requirements.

- [X] T031c [P] [US1] **Runtime Monitoring**. **Logic**: Monitor total runtime of the simulation phase. **Action**: If `total_runtime` (in hours) > 6, refactor code to enable streaming or reduce batch size. **Output**: `data/processed/runtime_report.json`.
- [X] T039 [P] [US1] **Memory Usage Verification**. **Logic**: Verify memory usage < 7GB with `--stream` on a 1GB file. **Action**: Use `psutil` to monitor peak RSS memory. **Output**: `data/processed/memory_report.json`.
- [X] T044 [P] [US1] **Power Analysis**. **Logic**: Perform power analysis with alpha=0.05, power=0.8, and expected effect size=0.2. **Output**: `data/processed/power_analysis.json`.
- [X] T050 [P] [US3] **Divergence Check**. **Logic**: Calculate divergence (percentage of trajectories where final state hash differs). Flag if divergence > 10%. **Output**: `data/processed/divergence_report.json`.

---

## Phase 6: Revision & Edge Case Resolution (Addressing Review Concerns)

**Goal**: Resolve specific analysis findings regarding NaN entropy, sample size warnings, and data integrity.

- [X] T051 [US1] **Enforce Strict Data Fallback Policy**. **Logic**: Run static analysis on `code/parser.py`, `code/entropy.py`, `code/ablation.py` to detect `try/except` blocks. **Action**: Refactor to raise `FileNotFoundError` for missing files. **Exception**: Allow `try/except` for specific edge cases like NaN handling in T006b (returning sentinel values). **Constraint**: This task addresses the "Loader must FAIL LOUDLY" rule. **Output**: Refactored code files. **Depends on**: T001.
- [X] T052 [US1] **Implement Streaming Data Ingestion**. **Logic**: Refactor `code/parser.py` (T006a) to support streaming large trajectory files if `data/raw/agenticsts_trajectories.jsonl` exceeds available RAM. **Action**: Use `ijson` or `datasets.load_dataset(..., streaming=True)` to iterate line-by-line, accumulating metrics without loading the full file. **Constraint**: Ensure the pipeline does not crash on large inputs. **Output**: Updated `code/parser.py` supporting streaming. **Depends on**: T006a.
- [X] T053 [US3] **Formalize Statistical Power Reporting**. **Logic**: Enhance `data/processed/power_analysis.json` (T044) to explicitly state the sample size `n`, the achieved power for the observed effect size, and the limitation if `n < 300`. **Action**: If `n < 300`, append a warning to the final report stating "Statistical power marginal; results should be interpreted with caution." **Output**: Updated `data/processed/power_analysis.json` and `data/processed/final_report.md`. **Depends on**: T014a, T044.
- [X] T054 [US3] **Verify Trajectory Pairing Integrity**. **Logic**: Enhance `code/stats.py` (T024) to strictly verify that Dynamic and Static runs originate from the *exact same* initial state hash before running McNemar's test. **Action**: If any trajectory pair has mismatched initial states, exclude it from the paired test and log it to `data/processed/paired_status.json` under `excluded_trajectories`. **Constraint**: Prevents invalid statistical conclusions from diverging trajectories. **Output**: Updated `data/processed/paired_status.json` with exclusion list. **Depends on**: T017, T019, T024.
