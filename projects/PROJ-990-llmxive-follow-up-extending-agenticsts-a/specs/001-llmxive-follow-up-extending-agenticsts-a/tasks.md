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

**Data Flow**: T006a (Bootstrap) -> T006 (Parser) -> T014a (Split) -> T007c (Static Proxy) / T008 (Ablation) -> T008c (Sample Check) -> T014 (Validator) -> T009 (Train)

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters. Define `TOKEN_BUDGET=4096`, `MIN_CONTEXT=256`, AND `K_RANDOM_BASELINE=2` as explicit constants loaded from config or env vars.
- [X] T006a [US1] **Bootstrap Synthetic Data**. **Logic**: Check if `data/raw/` directory is empty or contains no valid JSON/JSONL files matching `contracts/trajectory.schema.yaml`. **Action**: If empty/invalid, generate a set of trajectories conforming to `contracts/trajectory.schema.yaml` and move them to `data/raw/`. **Output**: `data/raw/synthetic_trajectories.jsonl`. **Constraint**: This task MUST run BEFORE T006. **Skip Condition**: If `data/raw/` contains valid trajectory files, skip this task. **CRITICAL**: This data is ONLY for CI bootstrapping. It MUST be excluded from all final statistical reports (SC-001, SC-002). **Depends on**: None.
- [X] T006 [P] [US1] Implement `code/parser.py` to extract per-turn metrics (health, threat, deck size) AND **legal move distributions** from raw trajectory logs in `data/raw/`. **Input**: JSONL/JSON files conforming to `contracts/trajectory.schema.yaml`. **Schema Definition**: `{"type": "object", "properties": {"trajectory_id": {"type": "string"}, "turn": {"type": "integer"}, "legal_moves": {"type": "array", "items": {"type": "string"}}}}`. **Validation**: MUST validate each file against `contracts/trajectory.schema.yaml` before processing. Raise `ValueError` if schema mismatch. **Output**: `data/processed/metrics_with_moves.csv` with columns: `trajectory_id`, `turn`, `health_ratio`, `threat_level`, `deck_size`, `move_entropy`. **Logic**: Parse the `legal_moves` array to reconstruct the available move set, calculate Shannon entropy $H = -\sum p_i \log(p_i)$ where $p_i = 1/|legal\_moves|$, and write to CSV. **Note**: Must include the probability distribution of available legal moves to support entropy calculation. **Skip Condition**: If `data/raw/` is empty and T006a has not run (or failed), skip this task. **Depends on**: T006a (if T006a ran), or `data/raw/` existence check.
- [X] T005 [P] [US1] Implement `code/entropy.py` to calculate **Shannon entropy** of the legal move distributions extracted by T006. **Logic**: Calculate $H = -\sum p_i \log(p_i)$. If calculation returns NaN or Inf, return a sentinel value (e.g., `float('inf')`) and **write a warning log to `data/processed/edge_case_warnings.log`** with the exact text: "Warning: NaN/Inf entropy detected at trajectory {id}, turn {turn}". **Input**: `data/processed/metrics_with_moves.csv`. **Skip Condition**: If `data/processed/metrics_with_moves.csv` does not exist (e.g., T006 was skipped), skip this task. **Depends on**: T006.
- [X] T005a [US1] **Generate No-Data Warning**. **Logic**: If `data/processed/metrics_with_moves.csv` does not exist (and T006 was skipped), generate `data/processed/edge_case_warnings.log` with the exact text: "Warning: No trajectory data available for entropy calculation; pipeline bootstrapped on synthetic data." **Action**: Ensure the log artifact exists even if no real data was processed. **Depends on**: `data/processed/metrics_with_moves.csv` existence check.
- [X] T007 Create `data/processed/` directory structure and schema validation for derived metrics.
- [X] T014a [P] [US1] Implement `code/splitter.py` to perform a stratified data split of the **processed metrics** (`data/processed/metrics_with_moves.csv` from T006) into FOUR distinct sets: **Train**, **Ablation-Train**, **Validation**, and **Test**. **Stratification Key**: `win_rate`. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`, AND `data/processed/validation_set_ids.json`. **Constraint**: If `len(validation_set) < 20`, **RAISE ValueError** immediately with message "Validation set size < 20 violates FR-006 hard constraint. Cannot proceed." The **Validation set** MUST contain at least 20 trajectories (FR-006). The **Ablation-Train set** is used exclusively to generate ground-truth utility labels via ablation. The **Test set** is reserved for final baseline/dynamic evaluation. The **Train set** is for model training. This split must occur BEFORE any ablation study. **Output `validation_set_ids.json`** containing the list of trajectory IDs in the validation set to ensure integrity checks in T014. **Depends on**: T006.
- [X] T007c [US1] Implement `code/proxy_extractor.py` to extract **static-log-derived utility** (frequency of layer retrieval) from raw trajectory logs as a distinct artifact. **Input**: `data/processed/metrics_with_moves.csv` (master file from T006) AND `data/processed/validation_set_ids.json` (from T014a). **Logic**: **Read `validation_set_ids.json` to filter the master file for the validation set**, then calculate `utility_score` as the normalized frequency of layer retrieval for each trajectory. **Output**: `data/processed/static_log_proxy.json` (schema: `{trajectory_id, layer_id, utility_score}`). **Constraint**: Must process ONLY the validation set to prevent data leakage. **Depends on**: T006, T014a. **Validation**: Must assert `validation_set_ids.json` exists and is non-empty before processing; raise error if missing.
- [X] T008a [P] [US1] Implement `code/ablation.py` (engine function) as a reusable function to run the ablation study on a given dataset file. **Function Signature**: `def run_ablation(dataset_path: str, layer_id: str) -> dict`. **Input**: Dataset file path, engine configuration. **Output**: `data/processed/ablation_labels_{dataset_name}.json` (schema: `{trajectory_id, layer_id, utility_score}`). **Logic**: Re-run the engine with each layer removed using the CLI argument `--remove-layer <layer_id>` to measure the impact on win rate. **CLI Command**: `python -m agenticsts_engine --trajectory <id> --remove-layer <layer_id>`. **Note**: This function is called by T008 and T008b. **Depends on**: T004 (config).
- [X] T008 [US1] **Generate Ground Truth Labels (Ablation-Train)**. **Logic**: Execute `code/ablation.py` (T008a) on the **Ablation-Train set**. **Input**: `data/processed/ablation_train_set.csv` (from T014a). **Output**: `data/processed/ablation_labels_train.json` (schema: `{trajectory_id, layer_id, utility_score}`). **Validation**: **MUST verify `ablation_train_set.csv` exists and is non-empty before execution**; if missing or empty, raise an error immediately. **Depends on**: T006, T014a, T008a.
- [X] T008b [US1] **Generate Ground Truth Labels (Validation)**. **Logic**: Execute `code/ablation.py` (T008a) on the **Validation set**. **Input**: `data/processed/validation_set.csv` (from T014a). **Output**: `data/processed/ablation_labels_validation.json`. **Validation**: **MUST verify `validation_set.csv` exists and is non-empty before execution**; if missing or empty, raise an error immediately. **Depends on**: T006, T014a, T008a.
- [X] T008c [US1] **Sample Count Check and Fallback Flag**. **Logic**: Count rows in `data/processed/ablation_labels_train.json` (from T008). **Action 1**: Log to `data/processed/edge_case_warnings.log` with exact text: "Warning: statistical power is marginal (n={n}); recommend expanding the dataset" if `n < 300`. **Action 2**: Generate `data/processed/fallback_flag.json` with content `{"fallback": true, "use_heuristic": true, "reason": "n < 300"}` if `n < 300`, else `{"fallback": false, "use_heuristic": false}`. **Note**: This flag triggers the fixed k=2 heuristic in T015. **Depends on**: T008.
- [X] T008d [US1] **Fallback Ablation (Mock Data)**. **Logic**: If T008 fails to produce `ablation_labels_train.json` (or the file is empty), generate a mock `ablation_labels_train.json` with synthetic utility scores (random values between 0 and 1) for the trajectories in `ablation_train_set.csv`. **Constraint**: This task runs ONLY if T008 fails. **Output**: `data/processed/ablation_labels_train.json` (mock). **Depends on**: T008 (check failure).
- [X] T014 [US1] Implement proxy validation logic in `code/classifier.py`. **Logic**:
 1. **Assert** `len(validation_set) >= 20` (if not, raise ValueError; T014a ensures this).
 2. Load `validation_set_ids.json` (from T014a).
 3. **Assert** that the trajectory IDs in `static_log_proxy.json` (from T007c) and `ablation_labels_validation.json` (from T008b) match exactly the IDs in `validation_set_ids.json`. Raise error if mismatch.
 4. Check Pearson correlation (≥ 0.7) between **static log proxy** (T007c, candidate proxy) and ablation utility (T008b, ground truth) on the **Validation set**.
 5. **Output**: `data/processed/proxy_validation_report.json`.
 6. **Action**: **Set `proxy_valid` flag in output JSON (true/false)**. **CRITICAL**: If `proxy_valid` is false, the system MUST NOT use the proxy for any downstream decisions (e.g., training T009 must use ablation labels only). The pipeline proceeds regardless of proxy validity.
 **Note**: The Validation set is distinct from the Ablation-Train set and serves as the required hold-out set for FR-006. This task validates the proxy assumption, but the ground truth for training comes from T008. **Depends on**: T007c, T008b, T014a.
- [X] T009 [US1] Implement `code/classifier.py` to train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Logic**:
 1. **Verify** `data/processed/fallback_flag.json` (from T008c) exists. If `fallback: true`, **DO NOT skip training**. Instead, proceed with training but set a flag `trained_on_marginal_data=true` in the model metadata.
 2. **Verify** `data/processed/proxy_validation_report.json` (from T014) exists. **DO NOT skip training** if `proxy_valid` is false.
 3. **Training Source**: ALWAYS train on `data/processed/ablation_labels_train.json` (from T008). If T008 failed and T008d generated mock data, use `ablation_labels_train.json` (mock) and set `trained_on_mock_data=true` in metadata.
 4. **Target**: `utility_score`. **Split**: 80/20 (within train set). **Output**: `models/layer_utility_classifier.pkl`.
 **Note**: Trains exclusively on ablation-derived ground truth (T008) or mock data (T008d) if ablation failed. **NEVER** uses proxy as training source. **Depends on**: T008, T008c, T014, T008d.

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
 1. **Check Fallback**: Read `data/processed/fallback_flag.json` (from T008c). If `use_heuristic: true`, **use fixed k=2 retrieval**. **Heuristic Logic**: Select top 2 layers by static frequency from `data/processed/static_log_proxy.json` or use predefined priority list `["Current Objective", "Enemy State", "Inventory"]`.
 2. **Check Proxy**: If `use_heuristic: false`, check `data/processed/proxy_validation_report.json` (from T014). If `proxy_valid` is false, **use static all-layers policy**.
 3. **Dynamic Mode**: If both checks pass, use trained model (T009) to predict top-k layers based on current turn entropy (from T005), **integrating** this prediction with the token budget constraint logic (4096 tokens). **Input Features**: The model input MUST include `move_entropy` to satisfy the "based on real-time game-state entropy" requirement.
 **Note**: Priority: `use_heuristic` (k=2) > `proxy_valid=false` (static) > `model` (dynamic). **Depends on**: T008c, T005, `data/processed/test_set.csv` (from T014a), T014, T009.
- [X] T016 [US1] Add logic to enforce a hard token budget and a minimum context floor in `code/simulator.py`. **Logic**:
 1. **Maximum Budget**: If predicted token count > 4096, truncate or prune the least useful layers until the prompt size is ≤ 4096.
 2. **Minimum Floor**: If the selected layers result in a token count < 256 tokens, **append the layer identified as most critical (e.g., "Current Objective")**. If "Current Objective" is not found, search for a layer tagged as "critical" or "objective".
 3. **NaN/Inf Handling**: If entropy returns a sentinel (NaN/Inf) from T005, default to retrieving the **full "all-layers" set** for that turn and log a warning to `data/processed/edge_case_warnings.log`.
 **Note**: This is an edge-case override within the budget enforcement, distinct from T015's prediction.
 **Depends on**: T015.
- [X] T017 [US1] **Execute Dynamic Simulation**. **Logic**: Invoke the `agenticsts-engine` (via T018) using the logic from T015 and T016 on the **test set**. **Input**: `data/processed/test_set.csv` (from T014a). **Output**: `data/processed/simulation_logs_dynamic.json`. **Note**: The test set evaluation compares **outcomes** (win rate) against the static baseline, not layer utility predictions against ground truth (which is impossible without re-running the game engine for every layer removal on the test set). The primary hypothesis test is valid as designed. **IMPORTANT**: Must log whether the run used 'dynamic' (model) or 'fallback' (fixed k=2) mode in the output JSON. **Depends on**: T015, T016, T018, T014a. **Validation**: Assert T018 (`engine_runner.py`) exists and is functional before execution. **CLI Command**: `python -m agenticsts_engine --input data/processed/test_set.csv --policy dynamic --output data/processed/simulation_logs_dynamic.json`.
- [X] T018 [P] [US1] Implement `code/engine_runner.py` to invoke the `agenticsts-engine` for re-simulation. **Logic**: Accept a trajectory file (JSON with columns: `trajectory_id`, `turn`, `state`, `legal_moves`) and a memory policy (string: 'Dynamic', 'Static', 'Random') as input, execute the engine, and output raw simulation logs. **CLI Command**: `python -m agenticsts_engine --input <file> --policy <value> --output <output_file>`. **Output**: `data/processed/simulation_logs_{policy}.json`. **Depends on**: T006, T014a. **Validation**: Must be fully implemented and tested before Phase 3 tasks begin.
- [X] T019 [US2] [P] Implement "Static All-Layers" baseline execution. **Logic**: Invoke `code/engine_runner.py` (T018) with policy="Static" on the **test set**. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018, T014a. **Validation**: Assert T018 exists and is functional. **CLI Command**: `python -m agenticsts_engine --input data/processed/test_set.csv --policy static --output data/processed/simulation_logs_static.json`.
- [X] T020 [US2] [P] Implement "No-Store Random" baseline execution. **Logic**: Invoke `code/engine_runner.py` (T018) with policy="Random" on the **test set**. **Logic**: **Select k layers uniformly at random for each turn with NO memory of past layers (no-store)**. **k** is defined as `config.K_RANDOM_BASELINE` (default configured via a tunable hyperparameter). **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018, T014a. **Validation**: Assert T018 exists and is functional. **CLI Command**: `python -m agenticsts_engine --input data/processed/test_set.csv --policy random --output data/processed/simulation_logs_random.json`.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition. **Input**: Outputs from T017, T019, T020. **IMPORTANT**: Must aggregate results separately for 'dynamic' and 'fallback' modes if present in T017 logs, and report the mode actually used for the primary SC-002 calculation.
- [X] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Schema**: `condition, win_rate, avg_tokens, std_dev_tokens`. **Aggregation Logic**: Mean of win_rate and token columns grouped by condition; **Calculate standard deviation of token savings** per condition to satisfy SC-004. **Depends on**: T021.
- [X] T023 [US2] Implement verification logic to calculate token reduction consistency. **Logic**: Calculate the standard deviation of token savings across the test set for the Dynamic policy. **Output**: `data/processed/token_consistency_report.json` containing `std_dev_tokens` and a boolean `passed` (true if std_dev < threshold or simply reported as required). **Action**: This task explicitly addresses SC-004. **Input**: `data/processed/baseline_comparison.csv`. **Output**: `data/processed/token_consistency_report.json`. **Depends on**: T022.
- [X] T022a [US2] Implement verification logic to calculate percentage reduction in token usage. **Logic**: Calculate reduction as `(Static_Tokens - Dynamic_Tokens) / Static_Tokens`. **Output**: Generate `data/processed/token_reduction_verification.json` containing a boolean field `passed` (true if reduction ≥ 30%) and a numeric field `actual_reduction_percent`. **Action**: **Write the result file regardless of outcome; do NOT exit with code 1**. The pipeline must continue to T028 to report the result. **Note**: The [deferred] reduction is a metric to report, not a hard gate. **Input**: `data/processed/baseline_comparison.csv`. **Output**: `data/processed/token_reduction_verification.json`. **Depends on**: T022.
- [X] T022b [US2] Generate explicit failure artifact. **Logic**: If T022a `passed` is false, generate `data/processed/verification_failed.json` with details on the token reduction shortfall. **Action**: This ensures a clear failure state is recorded if the pipeline halts. **Depends on**: T022a (runs ONLY if `passed` is false).
- [X] T024a [US3] Implement trajectory divergence detection in `code/stats.py`. **Logic**:
 1. For each trajectory pair (Dynamic vs Static) from the re-simulation outputs (T017, T019), compute the **SHA256 hash** of the **final game state** (defined as the JSON object containing `win`, `loss`, and `final_score` fields).
 2. **Canonical Serialization**: Sort keys alphabetically, remove all whitespace before hashing to ensure determinism.
 3. Compare the hash from the re-simulated Dynamic run against the hash from the re-simulated Static run.
 4. If the hashes differ for any pair, set `is_divergent=true` for that pair. If all pairs match, `is_divergent=false`.
 5. **Output**: `data/processed/divergence_report.json` (boolean `is_divergent`, and a list of divergent trajectory IDs).
 6. **Significance**: This check determines if the trajectories remained paired (deterministic) or diverged (unpaired). **Depends on**: T017, T019.
- [X] T025 [US3] Implement statistical testing logic in `code/stats.py`. **Logic**:
 1. Read `divergence_report.json` (T024a).
 2. **Verify** the correct test is selected: **Default to McNemar's test** for paired data. **Only** use Permutation Test if `is_divergent` is true (unpaired) AND T024a confirms divergence is robust (not due to engine noise). **Log the selection decision** explicitly in `data/processed/statistical_results.json` under `test_selection_reason`.
 3. **Execute** the selected test for win/loss outcomes.
 4. **Token Usage**: **Implement paired t-test** for token usage. **Normality Check**: Use **Shapiro-Wilk test** with alpha=0.05. If normality assumption fails, use Wilcoxon signed-rank test.
 5. **Correction**: **Apply Bonferroni correction** to the family of tests comprising the win rate test AND the token usage test simultaneously to control the family-wise error rate.
 **Output**: `data/processed/statistical_results.json`. **Schema**: Must include `p_value`, `effect_size`, `test_type`, `bonferroni_adjusted_p_value`, `divergence_status`. **Note**: `bonferroni_adjusted_p_value` MUST be present regardless of test type. **Depends on**: T024a, T021.
- [X] T028 [US3] Generate final statistical report in `data/processed/statistical_results.json`. **Logic**:
 1. Read `token_reduction_verification.json` (from T022a) and `statistical_results.json` (from T025).
 2. **If T022a failed (passed: false)**, generate the report but mark `token_reduction_passed` as false. **Action**: Do not skip T028 even if T022a fails; the report must document the win-rate impact.
 3. **Schema**: `{p_value, effect_size, test_type, bonferroni_adjusted, divergence_status, token_reduction_percent, token_reduction_passed}`. **Includes**: SC-001/SC-003 metrics. **Note**: Must ingest `token_reduction_verification.json` from T022a to report the token reduction metric. **Handle Missing**: If `verification_failed.json` (from T022b) does not exist, proceed without it (implies T022a passed). **Depends on**: T025, T022a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

**Independent Test**: Run analysis on a dataset with known outcomes and verify correct selection of McNemar's test and Bonferroni correction.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for McNemar's test selection logic (binary data) in `tests/unit/test_stats.py`.
- [X] T024 [P] [US3] Unit test for Bonferroni correction application in `tests/unit/test_stats.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `README.md` and `quickstart.md`. **Content**: Update `README.md` with a new section "Dynamic Policy Usage" containing a code snippet demonstrating the `--policy dynamic` flag; Update `quickstart.md` with the new pipeline steps. **Verification**: Ensure the new sections exist and are readable. **Action**: Mark as complete once verified.
- [X] T030 [P] Code cleanup and refactoring. **Criteria**: Refactor `code/` to pass ruff linting with zero warnings and remove duplicate imports. **Verification**: Run `ruff check code/` and confirm exit code 0. **Action**: Mark as complete once verified.
- [X] T031 [P] Add performance benchmarking script `code/benchmark.py` that logs execution time per phase and total runtime to `data/processed/benchmark_log.json`. **Phases to Instrument**: `parser` (T006), `ablation` (T008), `simulation` (T017/T019/T020), `stats` (T025). **Output Schema**: `{total_runtime, phase_timings: {parser: ms, ablation: ms, simulation: ms, stats: ms}}`. **Verification**: Run script and verify output JSON exists and contains valid timing data. **Note**: Must generate `benchmark_log.json` even if benchmark fails, logging the error state.
- [X] T031b [P] Analyze benchmark results. **Logic**: Read `data/processed/benchmark_log.json`. **Output**: Generate `data/processed/optimization_report.md` documenting the runtime analysis and confirming whether refactoring is needed. **Depends on**: T031.
- [X] T031c [P] Refactor code if needed. **Logic**: Read `data/processed/optimization_report.md`. If `total_runtime` (in hours) > 6, refactor code to reduce runtime. **Optimization Targets**: Vectorize loops, cache engine calls. **Decision Tree**: If engine calls dominate, cache results; if loops dominate, use numpy vectorization. **Verification**: Re-run benchmark and confirm runtime ≤ 6 hours. **Depends on**: T031b.
- [X] T032 [P] [US1] Add unit tests for edge cases. **Specific Task**: Add `tests/unit/test_classifier.py::test_fallback_flag_generation_on_small_n` to verify the n < 300 warning logic.
- [X] T033 [P] **Run `quickstart.md` validation**. **Logic**: Check if `data/raw/` is empty. If empty, **run T033a first**. Then execute `quickstart.md` from a clean environment, capture stdout/stderr to `data/processed/reproducibility_log.json`, and verify exit code 0. **Output**: `data/processed/reproducibility_log.json`. **Action**: If exit code != 0, the task fails. This operationalizes Constitution Principle I. **Depends on**: T029, T030, T033a (if needed).
- [X] T033a [US1] **Bootstrap Quickstart Data**. **Logic**: Check if `data/raw/` is empty. If empty, generate a minimal synthetic dataset (5 trajectories) and move to `data/raw/`. **Output**: `data/raw/synthetic_quickstart.jsonl`. **Constraint**: This task runs ONLY if `data/raw/` is empty. **Depends on**: None.
- [X] T034 [P] [US1] Add explicit data source validation in `code/parser.py` to ensure `data/raw/` contains non-empty, checksum-verified trajectory files before processing begins, raising a clear error if missing or corrupted.
- [X] T035 [P] Implement a "dry-run" mode in `code/main.py` that executes the full pipeline on a single trajectory (or first 5) to verify data flow and edge case handling (NaN entropy, budget truncation) before full-scale execution. **CLI Flag**: `--dry-run`. **Sample Size**: First 5 trajectories if available, else 1.
- [X] T036 [P] Add detailed logging of the "Current Objective" layer append logic in `code/simulator.py` (T016) to `data/processed/simulation_logs.json` for auditability of minimum context floor enforcement.
- [X] T037 [P] Create a `data/processed/analysis_config.json` snapshot that records the exact random seeds, hyperparameters, dataset split ratios, and stratification key used for the specific run, ensuring full reproducibility of the statistical results. **Fields**: `random_seed`, `token_budget`, `k_baseline`, `split_ratios`, `stratification_key`.
- [X] T038 [P] **Add robust error handling for the engine runner**. **Logic**: Wrap `code/engine_runner.py` (T018) calls in `try/except` blocks that catch `TimeoutError`, `ValueError` (for DataCorruption), and `Exception` (for EngineCrash). Log the specific error type and trajectory ID to `data/processed/engine_errors.log` and **fail the pipeline** (exit code 1) if the error rate exceeds 5% of the test set, preventing silent data loss. **Verification**: Add unit test `tests/unit/test_engine_runner.py::test_error_handling_catches_timeout` to verify the try/except blocks function as described. **Depends on**: T018.
- [X] T039 [P] Add a `--stream` flag to `code/parser.py` to support chunked processing of large trajectory files. **Behavior**: Process data in batches of a fixed, manageable size. **Verification**: Verify memory usage < 7GB with `--stream` on a 1GB file. **Input**: CSV file. **Constraint**: Raise error if memory usage > 7GB.
- [X] T040 [P] Write a comprehensive `CONTRIBUTING.md` section. **Content**: Add a "Data Flow" section to `CONTRIBUTING.md` detailing the T006 -> T014a dependency chain. **Verification**: Verify `CONTRIBUTING.md` contains the string "T006 -> T014a".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup. **Blocks all user stories**.
 - **Critical Flow**: T006a (if needed) -> T006 -> T014a -> T007c (after T014a) -> T008c -> T014 -> T009.
 - T009 (Training) MUST wait for T014 (Validation) to pass AND T008c (Sample Size) to handle fallback if needed.
- **User Stories (Phase 3)**: Depends on Foundational (Phase 2).
 - T015 (Dynamic Logic) depends on T008c (Fallback Flag) and T005, T014a, T014, T009.
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
- T006, T014a can run in parallel in Phase 2 (after T006a if needed).
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
- **Review Concerns Addressed**: T034 addresses data source validation; T035 addresses dry-run verification; T036 addresses auditability of minimum context logic; T037 addresses reproducibility of statistical runs; T031/T031b/T031c addresses performance benchmarking and optimization with concrete artifacts; T040 addresses documentation of data flow; T008c/T009/T015 addresses the n < 300 heuristic fallback; T022a addresses the hard gate for SC-002 (removed exit code); T014a/T014 addresses validation set integrity; **T038 addresses engine stability and error propagation**; **T016a addresses edge case verification**; **T023 addresses token reduction consistency**; **T029/T030 address documentation and cleanup**; **T006a/T005a/T008d/T014b/T033a address bootstrap and fallback logic for missing data**.
- **Key Changes in this Revision**:
 - **T006a**: Added to bootstrap synthetic data if `data/raw/` is empty.
 - **T005**: Updated to skip if T006 output is missing; added T005a for no-data logging.
 - **T014a**: Updated to RAISE ValueError if validation set < 20 (removed fallback flag). T014b removed.
 - **T008d**: Added to generate mock ground truth if T008 fails.
 - **T022a/T022b**: Updated to always write `token_reduction_verification.json`; T022b runs only if `passed` is false; T028 handles missing `verification_failed.json`.
 - **T015**: Clarified priority logic for `use_heuristic` vs `proxy_valid`. Explicitly defined k=2 fallback logic.
 - **T033/T033a**: Added T033a to bootstrap quickstart data; updated T033 to check for data existence.
 - **Parallel Tags**: Removed [P] from T006a, T007c, T008b, T008c, T017, T024a, T025, T028 to reflect true dependencies.
 - **Executability**: Added schema references, CLI args, input formats, and canonical serialization rules where missing.
 - **T015**: Clarified dependency on `test_set.csv`.
 - **T022a**: Updated to write result file regardless of outcome (removed exit code 1).
 - **T018**: Marked as completed prerequisite for Phase 3.
 - **T031**: Updated to ensure `benchmark_log.json` is generated even on failure.
 - **T037**: Added specific fields for config snapshot.
 - **T039**: Added batch size (1000 rows) and memory limit (7GB).
 - **T008a**: Moved to Phase 2 as code-definition task.
 - **T006**: Added schema validation details.
 - **T008/T008b**: Added CLI arguments for ablation.
 - **T018**: Added CLI command structure.
 - **T024a**: Added hashing details.
 - **T009**: Updated to ALWAYS train on ablation labels (or mock if ablation failed). Removed skip logic.
 - **T008c**: Updated to set `use_heuristic=true` if n < 300.
 - **T014**: Updated to assert validation set size >= 20.
