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
- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: pandas, numpy, scikit-learn, pytest, pyyaml, ijson, datasets). **Action**: Ensure `ijson` and `datasets` are included to support streaming tasks.
- [X] T003 [P] Configure linting and formatting tools (ruff/black) in `code/` and `tests/`
- [X] T003a [P] Generate `contracts/trajectory.schema.yaml` defining the trajectory schema (trajectory_id, turn, legal_moves, etc.) as per `data-model.md`.
- [X] T003a-verify [P] **Verify Schema Existence**. **Logic**: Check that `contracts/trajectory.schema.yaml` exists and is valid YAML. **Action**: If missing or invalid, raise `FileNotFoundError` ("Schema missing; T008 cannot proceed"). **Output**: `contracts/trajectory.schema.yaml` (verified). **Constraint**: Must run before T008. **Depends on**: T003a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data processing, model training, and validation gates.
**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete.

**Data Flow**: T005c (Fetch Manifest) -> T005b (Real Data Ingest) -> T005a (Log Status) -> T006a (Parser) -> T014a (Sample Check) -> T004 (Engine Install) -> T018 (Engine Runner) -> T008 (Ablation) / T008c (Hold-out Ablation) -> T008d (Merge Utility) / T008e (Merge Hold-out) -> T014 (Validator) -> T009 (Train)

- [X] T005c [P] **Fetch Checksum Manifest**. **Logic**: Fetch `manifest.json` from `https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json` to `data/raw/manifest.json`. **Output**: `data/raw/manifest.json`. **Depends on**: None.
- [X] T005b [US1] **Ingest Real AgenticSTS Trajectories**. **Logic**: Fetch the existing AgenticSTS trajectories from the canonical source using `huggingface-cli`. **Command**: `huggingface-cli download agenticsts/trajectories --repo-type dataset --local-dir data/raw --filename trajectories.jsonl`. **Action**: Download raw JSONL files to `data/raw/`. **Validation**: Verify checksums against `data/raw/manifest.json` fetched in T005c. **Output**: `data/raw/agenticsts_trajectories.jsonl`. **Constraint**: This task MUST run BEFORE T006a. **Skip Condition**: If `data/raw/agenticsts_trajectories.jsonl` already exists and checksums match, skip. **CRITICAL**: If this task fails (network error, checksum mismatch), the pipeline MUST raise `FileNotFoundError` and STOP. No fallback to synthetic data is permitted. **Depends on**: T005c.
- [X] T005a [US1] **Log Data Availability Status**. **Logic**: Check if `data/raw/agenticsts_trajectories.jsonl` exists. **Action**: If missing, write `{"level": "ERROR", "message": "Real data missing; pipeline blocked.", "timestamp": "<ISO8601>"}` to `data/processed/edge_case_warnings.log` and set `PIPELINE_BLOCKED=true` in `data/processed/config_state.json`. **Constraint**: This task runs AFTER T005b to ensure the file existence check happens after the download attempt. **Depends on**: T005b.
- [X] T004 [US1] **Install AgenticSTS Engine**. **Logic**: Install the game engine required for ablation and simulation. **Command**: `pip install agenticsts-engine` OR `git clone <repo> && pip install -e.`. **Output**: Engine available in PATH. **Depends on**: T001.
- [X] T018 [US1/US2] **Implement Engine Runner**. **Logic**: Implement `code/engine_runner.py` to invoke the engine for re-simulation. Provide CLI flags `--mode <dynamic|static|random>` and `--ablate-layer <layer_name>`. **Constraint**: Must be executable before T008 runs. **Depends on**: T004.
- [X] T006a [US1] Implement `code/parser.py` to extract per-turn metrics from raw trajectory logs in `data/raw/`. **Input**: JSONL/JSON files from T005b. **Validation**: MUST validate each file against `contracts/trajectory.schema.yaml` (generated in T003a) before processing. Raise `ValueError` if schema mismatch. **Constraint**: If `data/raw/` is empty or missing, raise `FileNotFoundError` ("Real data missing; pipeline cannot proceed"). **NO** `try/except` blocks that fall back to synthetic data for file I/O. **Output**: `data/processed/metrics_with_moves.csv` (Columns: `trajectory_id`, `turn`, `health_ratio`, `enemy_threat`, `deck_size`, `move_entropy`, `layer_name`). **Depends on**: T005b, T003a-verify.
- [X] T006b [US1] Implement entropy calculation in `code/entropy.py`. **Logic**: Calculate Shannon entropy of the legal move distributions extracted by T006a. **Edge Case Handling**: If calculated entropy is `NaN` or `Infinity`, log a warning to `data/processed/edge_case_warnings.log` and return a sentinel value that triggers the "all-layers" fallback in T015b. **Input**: `data/processed/metrics_with_moves.csv`. **Skip Condition**: If `data/processed/metrics_with_moves.csv` does not exist (e.g., T006a was skipped), skip this task. **Output**: `data/processed/entropy_metrics.csv`. **Depends on**: T006a.
- [X] T014a [US1] Implement data splitting logic in `code/splitter.py`. **Logic**: Split data into train/validation/test sets. **Edge Case Handling**:
 1. **Sample Size Warning**: If training set size `n < 300`, log a WARNING to `data/processed/edge_case_warnings.log` stating "Statistical power marginal (n < 300)" but DO NOT set `USE_HEURISTIC=true` or skip ablation. Proceed with ablation study.
 2. **Homogeneity Check**: After ablation (T008/T008c), if the variance of `utility_delta` in the training set is zero or near-zero (< 1e-6), log a CRITICAL warning "Data homogeneity detected; ablation labels contain no signal." and set `USE_HEURISTIC=true`.
 3. **Hold-out Validation**: Ensure `len(validation_set) >= 20`. If not, raise `ValueError` ("Hold-out set too small for FR-006 validation; adjust split ratio.").
 **Input**: `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`, `data/processed/config_state.json`. **Depends on**: T006a.
- [X] T008 [US1] **Generate Ground Truth Labels (Ablation Study - Training Set)**. **Logic**: Run the ablation study on the **training set** to generate utility labels by re-running the game engine with specific layers removed. **Algorithm**: 1. Parse `contracts/trajectory.schema.yaml` using `yaml.safe_load`, extract keys from `properties.layers`, and iterate over this list. 2. For each layer: a. Remove layer from trajectory context. b. Execute `python code/engine_runner.py --ablate-layer <layer_name> --trajectory <id>`. c. Record win rate delta vs baseline: `utility_delta = baseline_win_rate - ablated_win_rate`. d. Store `utility_delta` as a float in JSON. 3. Aggregate results into `data/processed/ablation_labels_train.json`. **Implementation File**: `code/ablation.py`. **Input**: `data/raw/agenticsts_trajectories.jsonl`, `data/processed/train_set.csv`. **Output**: `data/processed/ablation_labels_train.json`. **Constraint**: If this fails (engine error), the pipeline MUST NOT proceed. The research is invalid without ground truth. **Depends on**: T005b, T018, T003a-verify, T014a, T004.
- [X] T008-verify [US1] **Validate Ablation Output (Training)**. **Logic**: Check that `data/processed/ablation_labels_train.json` exists and contains at least one entry. **Action**: If missing or empty, raise `FileNotFoundError` ("Ablation study failed to produce ground truth; pipeline blocked."). **Constraint**: Must run before T008d. **Depends on**: T008.
- [X] T008c [US1] **Generate Ground Truth Labels (Ablation Study - Hold-out Set)**. **Logic**: Run the ablation study on the **hold-out set** (at least 20 trajectories) to generate utility labels for proxy validation. **Algorithm**: Same as T008 but using `data/processed/validation_set.csv` (or a specific hold-out split). **Implementation File**: `code/ablation.py`. **Input**: `data/raw/agenticsts_trajectories.jsonl`, `data/processed/validation_set.csv`. **Output**: `data/processed/ablation_labels_holdout.json`. **Constraint**: Must run. **Depends on**: T005b, T018, T003a-verify, T014a, T004.
- [X] T008c-verify [US1] **Validate Ablation Output (Hold-out)**. **Logic**: Check that `data/processed/ablation_labels_holdout.json` exists and contains at least 20 entries. **Action**: If missing or too small, raise `ValueError` ("Hold-out ablation failed; proxy validation cannot proceed."). **Constraint**: Must run before T008e. **Depends on**: T008c.
- [X] T008d [US1] **Extract and Merge Ground Truth Utility Labels (Train)**. **Logic**: Convert ablation JSON outputs into structured CSVs and merge them with the metrics dataset. **Action**: 1. Load `data/processed/ablation_labels_train.json`. 2. Load `data/processed/metrics_with_moves.csv` (from T006a). 3. **Aggregate**: For each `trajectory_id` and `layer_name`, average the `utility_delta` values across all turns to produce a single `utility_delta` per layer per trajectory. 4. Join on `trajectory_id` and `layer_name`. 5. Output `data/processed/ground_truth_utility_train.csv` (Columns: `trajectory_id`, `layer_name`, `utility_delta`, `features...`). **Input**: `data/processed/ablation_labels_train.json`, `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/ground_truth_utility_train.csv`. **Depends on**: T006a, T008, T008-verify.
- [X] T008d-verify [US1] **Validate Ground Truth Utility Format**. **Logic**: Check that `data/processed/ground_truth_utility_train.csv` contains the `utility_delta` column. **Action**: Verify that `utility_delta` is numeric (float) for all rows. If any row has a non-numeric `utility_delta`, raise `ValueError` ("Invalid utility_delta format; ablation calculation failed."). **Output**: `data/processed/ground_truth_utility_train.csv` (verified). **Constraint**: Must run before T009. **Depends on**: T008d.
- [X] T008e [US1] **Extract and Merge Ground Truth Utility Labels (Hold-out)**. **Logic**: Convert hold-out ablation JSON outputs into structured CSVs for proxy validation. **Action**: 1. Load `data/processed/ablation_labels_holdout.json`. 2. Load `data/processed/metrics_with_moves.csv` (from T006a). 3. **Aggregate**: Average `utility_delta` per `trajectory_id` and `layer_name`. 4. Join on `trajectory_id` and `layer_name`. 5. Output `data/processed/ground_truth_utility_holdout.csv`. **Input**: `data/processed/ablation_labels_holdout.json`, `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/ground_truth_utility_holdout.csv`. **Depends on**: T006a, T008c, T008c-verify.
- [X] T014 [US3] **Implement Proxy Validation Logic**. **Logic**:
 1. **Generate Proxy**: Derive `proxy_utility_labels.csv` from `data/processed/metrics_with_moves.csv` (T006a output) by calculating frequency-weighted scores for each layer. **Schema**: Columns `trajectory_id`, `layer_name`, `proxy_utility`.
 2. **Validate**: Load `proxy_utility_labels.csv` and `data/processed/ground_truth_utility_holdout.csv` (from T008e). Join on `trajectory_id` and `layer_name`. Calculate Pearson correlation using `scipy.stats.pearsonr`.
 3. **Gate**: If correlation < 0.7, set `proxy_valid=false` and log warning. **Do NOT trigger heuristic fallback here.** The system MUST rely on the ablation study (ground truth) if the proxy is invalid.
 **Constraint**: Validation MUST use the hold-out set of at least 20 trajectories where ground truth is established via ablation (T008c). **Output**: `data/processed/proxy_validation_report.json` containing a boolean `proxy_valid`. **Depends on**: T008e, T008d, T006a.
- [X] T014-verify [US3] **Validate Proxy Report**. **Logic**: Check that `data/processed/proxy_validation_report.json` exists and contains the `proxy_valid` boolean. **Action**: If missing or invalid format, raise `FileNotFoundError` ("Proxy validation report missing; pipeline blocked."). **Constraint**: Must run before T009. **Depends on**: T014.
- [X] T009 [US1] Train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Input**: `data/processed/ground_truth_utility_train.csv` (from T008d-verify). **Output**: `models/layer_utility_classifier.pkl`. **Constraint**: Proceed even if T014 reports `proxy_valid=false`. Use ablation labels regardless of proxy validity. If `USE_HEURISTIC=true` (from T014a), use a fixed-k=2 heuristic instead. **Dependency Logic**: Depends on T008d-verify and T014. **Depends on**: T008d-verify, T014-verify.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
- [X] T012 [P] [US1] Unit test for entropy calculation edge cases in `tests/unit/test_entropy.py`.

### Implementation for User Story 1 (Dynamic Policy)
- [X] T015a [US1] Implement Minimum Context Floor Logic in `code/simulator.py`. **Logic**: Before any selection, check if the calculated context is below `MIN_CONTEXT` (256 tokens). If so, append the "Current Objective" layer immediately. **Output**: Intermediate state with floor applied.
- [X] T015b [US1] Implement Dynamic Layer Selection in `code/simulator.py`. **Logic**: Use the trained model (T009) to predict utility, then select top-k layers based on entropy prediction or fallback heuristic. **Edge Case Handling**: If T006b returned a NaN/Inf entropy sentinel, force selection of the full "all-layers" set. **Input**: State from T015a.
- [X] T015c [US1] Enforce Maximum Token Budget in `code/simulator.py`. **Logic**: Ensure the final prompt size is ≤ 4096 tokens. If exceeded, prune least useful layers. **Logging Requirement**: For each trajectory, write a JSON line to `data/processed/pruning_logs.jsonl` with the following schema: `{"trajectory_id": "<id>", "initial_tokens": <int>, "selected_layers": ["<layer1>", ...], "final_tokens": <int>, "layers_pruned": ["<layer1>", ...], "pruning_reason": "<string>"}`. **Pruning Reason Logic**: If `final_tokens > 4096`, set `pruning_reason` to "Budget Exceeded: <excess> tokens over limit". If layers were pruned due to low utility, set `pruning_reason` to "Low Utility Pruning". **Input**: State from T015b. **Output**: `data/processed/pruning_logs.jsonl`. **Depends on**: T015a, T015b.
- [X] T017 [US1] Execute Dynamic Simulation on the test set. **Command**: `python code/main.py --mode dynamic --split test`. **Output**: `data/processed/simulation_logs_dynamic.json`. **Depends on**: T015a, T015b, T015c, T018, T009.
- [X] T019 [US2] [P] Implement "Static All-Layers" baseline execution. **Logic**: Retrieve ALL available memory layers (as defined in `contracts/trajectory.schema.yaml`) for every turn. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018.
- [X] T020 [US2] [P] Implement "No-Store Random" baseline execution. **Logic**: Select exactly k=2 layers uniformly at random from the available set for every turn. **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018.
- [X] T021-verify [US2] **Verify Seed Consistency**. **Logic**: Read `simulation_logs_dynamic.json`, `simulation_logs_static.json`, and `simulation_logs_random.json`. Extract `seed` values and compare against `code/config.py` pinned seeds. **Action**: If seeds mismatch or are missing, raise `ValueError` ("Simulation seeds inconsistent; reproducibility compromised."). **Output**: `data/processed/seed_verification.json`. **Depends on**: T017, T019, T020.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition.
- [X] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Logic**: Calculate and report token reduction metrics using formula: `(static_tokens - dynamic_tokens) / static_tokens`. **Constraint**: If `token_reduction_pct` < 30, set `threshold_met=false` in `data/processed/build_status.json` but DO NOT exit with code 1. The pipeline must continue to generate statistical evidence. **Schema**: `condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct, threshold_met`. **Depends on**: T017, T019, T020.
- [X] T022a [US2] **Generate Per-Trajectory Token Savings**. **Logic**: Read `simulation_logs_dynamic.json` and `simulation_logs_static.json`. Calculate `savings = static_tokens - dynamic_tokens` for each `trajectory_id`. **Output**: `data/processed/token_savings_per_trajectory.csv` (Columns: `trajectory_id`, `static_tokens`, `dynamic_tokens`, `savings`). **Constraint**: Required for T023 standard deviation calculation. **Depends on**: T017, T019.

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [X] T023a [P] [US3] Unit test for McNemar's test selection logic in `tests/unit/test_stats.py`.

- [X] T023 [US2] Implement verification logic to calculate token reduction consistency. **Output**: `data/processed/token_consistency_report.json` with boolean `passed`. **Logic**: Calculate standard deviation of token savings from `data/processed/token_savings_per_trajectory.csv` (T022a). Define `mean_savings` as the mean of `savings` column. If `std_dev < 0.10 * mean_savings`, `passed=true`. Else, `passed=false`. **Depends on**: T022a.

- [X] T024 [P] [US3] Verify Paired Status in `code/stats.py`. **Logic**: Confirm that Dynamic and Static runs share the same `trajectory_id` and `initial_state_hash`. **Action**: Compute SHA256 hash of `json.dumps({'initial_state_hash': str, 'trajectory_id': str}, sort_keys=True)` for each trajectory. **Output**: `data/processed/paired_status.json` (boolean `is_paired`, list `valid_trajectory_ids`, list `excluded_trajectory_ids`). **Depends on**: T017, T019.

- [X] T025a [US3] **Verify Trajectory Pairing Integrity & Generate Exclusion List**. **Logic**: Read `data/processed/paired_status.json` (from T024). **Action**: 
 1. **Check Pairing**: If `is_paired` is true, proceed to McNemar's test. 
 2. **Handle Divergence**: If `is_paired` is false, DO NOT raise an error. Instead, log a warning to `data/processed/edge_case_warnings.log` stating "Trajectory divergence detected; switching to fallback statistical test." 
 3. **Generate Exclusion List**: Create `data/processed/exclusion_report.json` containing `is_paired` (bool), `valid_trajectory_ids` (list), `excluded_trajectory_ids` (list), and `divergence_rate` (float: len(excluded)/total). 
 4. **Enable Fallback**: Signal that the pipeline should proceed with a Permutation Test or Z-test for the unpaired data. 
 **Output**: `data/processed/exclusion_report.json`. **Constraint**: This task MUST NOT abort the pipeline. It MUST generate the exclusion list to allow T025b to proceed with the appropriate test. **Depends on**: T024.

- [X] T025a-verify [US3] **Verify Exclusion Filter Application**. **Logic**: Read `data/processed/exclusion_report.json` (from T025a) and `data/processed/test_set.csv` (from T014a). **Action**: 
 1. Confirm that `excluded_trajectory_ids` from the report are a subset of `test_set.csv` IDs.
 2. Confirm that the `valid_trajectory_ids` list matches the intersection of `test_set.csv` IDs and `valid_trajectory_ids` from the report.
 3. If `is_paired` is false, verify that the number of excluded IDs matches the `divergence_rate` calculation.
 **Output**: `data/processed/exclusion_verification.json` (boolean `filter_verified`). **Constraint**: This task MUST run BEFORE T025b to ensure the exclusion list is correctly applied to the dataset. **Depends on**: T025a.

- [X] T025b [US3] **Execute Statistical Tests (Paired or Unpaired)**. **Logic**: Read `data/processed/exclusion_report.json` (from T025a) and `data/processed/exclusion_verification.json` (from T025a-verify).
 1. **Case A (Paired)**: If `is_paired` is true, run McNemar's test on win/loss outcomes for all trajectories. Run paired t-test on token usage from `data/processed/token_savings_per_trajectory.csv` (T022a). Apply Bonferroni correction.
 2. **Case B (Unpaired)**: If `is_paired` is false, **filter** the input datasets (win/loss and token usage) to include ONLY `valid_trajectory_ids` from the exclusion report. Run a Permutation Test (or Z-test if n > 30) on this **filtered** set to compare win rates and token usage. This addresses FR-005 by handling diverging trajectories via fallback tests on the valid subset.
 **Output**: `data/processed/mcnemar_results.json` (if Case A) OR `data/processed/permutation_results.json` (if Case B). Also write `data/processed/statistical_test_summary.json` indicating which test was used and the p-values. **Constraint**: This task MUST always write result artifacts, even if the test fails (write error details). **Depends on**: T025a, T025a-verify, T017, T019, T022a.

- [X] T025c [US3] **Analyze Divergence Metrics**. **Logic**: Read `data/processed/exclusion_report.json` (from T025a). Calculate the divergence rate and the impact of divergence on the dataset (e.g., % of trajectories lost). **Output**: `data/processed/divergence_analysis.json` containing `divergence_rate`, `impact_assessment` (string), and `recommendation` (string). **Constraint**: Required for FR-005 to report on the handling of diverging trajectories. **Depends on**: T025a.

- [X] T026 [US3] **Generate Success Criteria Report**. **Logic**: Aggregate results from T022, T023, T025b, T025c. **Action**: Create `data/processed/success_criteria_report.json` mapping SC-001 to SC-004 to pass/fail status. **Constraint**: If ANY Success Criterion (SC-001 to SC-004) is false, the script MUST exit with code 1 (FAIL). **Output**: `data/processed/success_criteria_report.json`. **Depends on**: T022, T023, T025b, T025c.

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

- [X] T051 [US1] **Enforce Strict Data Fallback Policy**. **Logic**: Run static analysis on `code/parser.py` (line 20-40), `code/entropy.py` (line 15-30), `code/ablation.py` (line 10-50) to detect `try/except` blocks. **Action**: Refactor to raise `FileNotFoundError` for missing files. **Exception**: Allow `try/except` for specific edge cases like NaN handling in T006b (returning sentinel values). **Constraint**: This task addresses the "Loader must FAIL LOUDLY" rule. **Output**: Refactored code files. **Depends on**: T001.
- [X] T052 [US1] **Implement Streaming Data Ingestion**. **Logic**: Refactor `code/parser.py` (T006a) to support streaming. **Action**: Use `ijson` (installed in T002) or `datasets.load_dataset(..., streaming=True)` to iterate line-by-line, accumulating metrics without loading the full file. **Constraint**: Although the dataset is small, this is implemented to demonstrate robustness and adhere to Data Hygiene principles. **Raw Data Materialization**: Ensure the raw file is fully downloaded and checksummed before streaming processing begins. **Output**: Updated `code/parser.py` supporting streaming. **Depends on**: T006a, T002.

- [X] T053 [US3] **Formalize Statistical Power Reporting**. **Logic**: Enhance `data/processed/power_analysis.json` (T044) to explicitly state the sample size `n`, the achieved power for the observed effect size, and the limitation if `n < 300`. **Action**: If `n < 300`, append a warning to the final report stating "Statistical power marginal; results should be interpreted with caution." **Output**: Updated `data/processed/power_analysis.json` and `data/processed/final_report.md`. **Depends on**: T014a, T044.
- [X] T054 [US3] **Verify Exclusion List Integrity**. **Logic**: Verify that the `excluded_trajectory_ids` in `data/processed/exclusion_report.json` (from T025a) match the mismatched hashes in `data/processed/paired_status.json` (from T024). **Action**: If `is_paired` is false, verify the exclusion list matches the `excluded_trajectory_ids` from T025a. If `is_paired` is true, verify the exclusion list is empty. **Output**: `data/processed/exclusion_verification.json`. **Constraint**: This task verifies the exclusion logic, it does not generate it. **Depends on**: T025a, T024.

---

## Phase 7: Final Review & Documentation (Revision Round 1)

**Goal**: Address remaining analysis findings regarding documentation clarity, edge case logging, and final report completeness.

- [X] T055 [US3] **Enhance Edge Case Documentation**. **Logic**: Review `data/processed/edge_case_warnings.log` generated by T006b and T014a. **Action**: Ensure all warnings (NaN entropy, sample size < 300, homogeneity) are clearly documented in `docs/edge_cases.md` with specific examples and mitigation strategies. **Constraint**: Documentation must be explicit about how these edge cases affect statistical power and result interpretation. **Output**: `docs/edge_cases.md`. **Depends on**: T006b, T014a, T053.
- [X] T056 [US1] **Aggregate Token Budget Logs**. **Logic**: Read `data/processed/pruning_logs.jsonl` (from T015c). Aggregate into `data/processed/token_budget_detailed.csv` with columns: `trajectory_id`, `initial_tokens`, `selected_layers`, `final_tokens`, `layers_pruned`, `pruning_reason`. **Constraint**: This data is essential for verifying the token reduction hypothesis (SC-002) and understanding pruning behavior. **Serialization**: Serialize the `layers_pruned` list as a **JSON string** in the CSV column to handle list data. **Output**: `data/processed/token_budget_detailed.csv`. **Depends on**: T015c, T017.
- [X] T057a [US3] **Generate Statistical Report Template**. **Logic**: Create a markdown template for `data/processed/statistical_analysis_report.md` with sections and **exact placeholders**:
 1. **Methodology**: [Test Type: `{{test_type}}`], [Sample Size: `{{sample_size}}`], [Divergence Rate: `{{divergence_rate}}`].
 2. **Results**:
    - **Win Rate**: [p-value: `{{win_rate_p}}`], [effect size: `{{win_rate_effect}}`], [confidence interval: `{{win_rate_ci}}`].
    - **Token Usage**: [p-value: `{{token_p}}`], [effect size: `{{token_effect}}`], [confidence interval: `{{token_ci}}`].
 3. **Limitations**: [Sample Size Limitation: `{{sample_limitation}}`], [Divergence Impact: `{{divergence_impact}}`], [Power Analysis Result: `{{power_achieved}}`].
 **Output**: `data/processed/statistical_analysis_report_template.md`. **Depends on**: None.
- [X] T057b [US3] **Aggregate Statistical Data**. **Logic**: Read `data/processed/mcnemar_results.json` OR `data/processed/permutation_results.json` (whichever exists from T025b), `data/processed/statistical_test_summary.json`, `data/processed/power_analysis.json`, `data/processed/divergence_analysis.json`. **Action**: If `mcnemar_results.json` is missing, use `permutation_results.json`. If both are missing, log an error and proceed with empty data. **Output**: `data/processed/agg_stats.json`. **Depends on**: T025b, T025c, T044.
- [X] T057c [US3] **Assemble Final Statistical Report**. **Logic**: Fill `data/processed/statistical_analysis_report_template.md` (T057a) with data from `data/processed/agg_stats.json` (T057b) and `data/processed/success_criteria_report.json`. **Output**: `data/processed/statistical_analysis_report.md`. **Depends on**: T057a, T057b, T026.
- [X] T058 [US1] **Validate Data Pipeline Integrity**. **Logic**: Run a comprehensive end-to-end validation of the entire data pipeline from raw data ingestion to final statistical reporting. **Action**: Verify that all intermediate files are correctly generated, checksums match, and no data corruption occurred. **Constraint**: This task ensures the reproducibility of the entire experiment and validates the "Single Source of Truth" principle. **Output**: `data/processed/pipeline_validation_report.json`. **Depends on**: T005b, T006a, T008, T009, T017, T019, T025b.