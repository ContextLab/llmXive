# Tasks: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-agenticsts-a/`
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
- [ ] T003a [P] Generate `contracts/trajectory.schema.yaml` defining the trajectory schema (trajectory_id, turn, legal_moves, etc.) as per `data-model.md`.
- [ ] T003a-verify [P] **Verify Schema Existence**. **Logic**: Check that `contracts/trajectory.schema.yaml` exists and is valid YAML. **Action**: Write a status artifact `data/processed/schema_verification.json` with fields `status: "passed"` or `status: "failed"`, `schema_hash` (SHA256 of schema file), `file_path`, and an `error` message if invalid. **Output**: `data/processed/schema_verification.json`. **Constraint**: Must run before any task that parses raw trajectories. **Depends on**: T003a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data processing, model training, and validation gates.
**⚠️ CRITICAL**: No user story work (Phase 3+) can begin until this phase is complete.

**Data Flow**: T005c → T005b → T005b-d → T005b-verify → T005a → T006a → T006b → T008-baseline → T008b-baseline → T008-impl → T008 → T008-verify → T008c → T008c-verify → T008d → T008d-verify → T008e → T008e-verify → T014-impl → T014 → T014-verify → T009 → T017-impl → T018 → T015-impl → T017 → T019 → T020 → T021 → T021-verify → T022 → T022a → T023 → T023a → T024 → T025a → T025a-verify → T025-impl → T025b → T025c → T026 → T044 → T050 → T057b → T057c → T058 → T059 → T060 → T061 → T062 → T063 → T064 → T065

### Sub-Phase 2A: Data Ingestion & Validation

- [X] T005c [P] **Fetch Checksum Manifest**. **Logic**: Fetch `manifest.json` from `https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json` to `data/raw/manifest.json`. **Command**: `curl -L https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json -o data/raw/manifest.json`. **Output**: `data/raw/manifest.json`. **Depends on**: None.
- [ ] T005b [US1] **Ingest Real AgenticSTS Trajectories**. **Logic**: Fetch the existing AgenticSTS trajectories from the canonical source using `huggingface-cli`. **Command**: `huggingface-cli download agenticsts/trajectories --repo-type dataset --local-dir data/raw --filename trajectories.jsonl`. **Action**: Download raw JSONL files to `data/raw/`. **Validation**: Verify checksums against `data/raw/manifest.json` using `sha256sum`. If checksum mismatch, raise `FileNotFoundError`. **Output**: `data/raw/agenticsts_trajectories.jsonl`. **Constraint**: Must run BEFORE T006a. **Depends on**: T005c.
- [ ] T005b-verify [US1] **Validate Trajectory Schema**. **Logic**: Validate `data/raw/agenticsts_trajectories.jsonl` against `contracts/trajectory.schema.yaml` using `jsonschema` or `pydantic`. **Action**: If validation fails, raise `ValueError` with details. **Output**: `data/processed/ingestion_validation.json`. **Depends on**: T005b, T003a-verify.
- [ ] T005b-d [US1] **Ingest Original Static Retrieval Logs**. **Logic**: Fetch the original static retrieval logs from the canonical source using `huggingface-cli`. **Command**: `huggingface-cli download agenticsts/trajectories --repo-type dataset --local-dir data/raw --filename original_static_logs.jsonl`. **Validation**: Verify checksums against `data/raw/manifest.json`. **Constraint**: This data is used ONLY for Proxy Validation (FR-006), NOT for ground truth generation. **Output**: `data/raw/original_static_logs.jsonl`. **Depends on**: T005c.
- [ ] T005a [US1] **Log Data Availability Status**. **Logic**: Check if `data/raw/agenticsts_trajectories.jsonl` and `data/raw/original_static_logs.jsonl` exist. **Action**: If missing, write `{"level":"ERROR","message":"Real data missing; pipeline blocked.","timestamp":"<ISO8601>"}` to `data/processed/edge_case_warnings.log` and set `PIPELINE_BLOCKED=true` in `data/processed/config_state.json`. **Constraint**: Runs AFTER T005b and T005b-d. **Depends on**: T005b, T005b-d. <!-- FAILED: unspecified -->

### Sub-Phase 2B: Parser & Metrics

- [ ] T006a [US1] Implement `code/parser.py` to extract per‑turn metrics from raw trajectory logs in `data/raw/`. **Input**: JSONL files from T005b. **Logic**: Extract `health_ratio`, `enemy_threat`, `deck_size`, and `move_entropy` (Shannon entropy of legal moves). **Note**: `move_entropy` is a FEATURE, not the utility label. **Validation**: Must validate each file against `contracts/trajectory.schema.yaml` (generated in T003a). Raise `ValueError` on schema mismatch. **Constraint**: If `data/raw/` is empty or missing, raise `FileNotFoundError`. **NO** fallback to synthetic data. **Output**: `data/processed/metrics_with_moves.csv` (columns: `trajectory_id,turn,health_ratio,enemy_threat,deck_size,move_entropy,layer_name`). **Depends on**: T005b-verify, T003a-verify. <!-- FAILED: unspecified -->
- [ ] T006b [US1] Implement entropy calculation in `code/entropy.py`. **Logic**: Calculate Shannon entropy of the legal move distributions extracted by T006a. **Edge Case Handling**: If entropy is `NaN` or `Infinity`, log a warning to `data/processed/edge_case_warnings.log` and return the sentinel value `float('nan')`. The sentinel will trigger full‑layer fallback in T015b. **Input**: `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/entropy_metrics.csv`. **Depends on**: T006a. <!-- ATOMIZE: requested -->

### Sub-Phase 2C: Data Splitting & Ablation

- [X] T014a [US1] **Implement Data Splitting Logic** in `code/splitter.py`. **Logic**: Split data into train/validation/test sets. **Edge Cases**:
 1. If training set size `n < 300`, log a WARNING to `data/processed/edge_case_warnings.log` ("Statistical power marginal (n < 300)") and set `USE_HEURISTIC=true` in `data/processed/config_state.json` to trigger heuristic fallback in T009.
 2. After ablation (T008/T008c), if variance of `utility_delta` in training set < 1e‑6, log a CRITICAL warning.
 3. Ensure validation set has at least 20 trajectories; otherwise raise `ValueError`.
 **Input**: `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`, `data/processed/config_state.json`. **Depends on**: T006a.
- [X] T014a-verify [US1] **Verify Data Splits**. **Logic**: Check that `data/processed/train_set.csv`, `data/processed/validation_set.csv`, and `data/processed/test_set.csv` exist and are non-empty. **Action**: If any file is missing or empty, raise `FileNotFoundError`. **Output**: `data/processed/splits_verified.json`. **Depends on**: T014a.
- [ ] T008-baseline [US1] **Generate Baseline Win Rates (Training Set)**. **Logic**: For each trajectory in `data/processed/train_set.csv`, run the "all‑layers" baseline via `python code/engine_runner.py --mode static --trajectory <id> --initial_state_hash <hash>` and record the win/loss outcome. **Action**: Extract `initial_state_hash` from the trajectory file to ensure deterministic re-simulation. **Output**: `data/processed/baseline_win_rates_train.json` (keys: `trajectory_id`, `win_rate`, `initial_state_hash`). **Constraint**: Must succeed before any ablation study. **Depends on**: T005b, T018, T004, T014a-verify. <!-- FAILED: unspecified -->
- [ ] T008b-baseline [US1] **Generate Baseline Win Rates (Hold-out Set)**. **Logic**: Same as T008-baseline but using `data/processed/validation_set.csv`. **Output**: `data/processed/baseline_win_rates_holdout.json`. **Constraint**: Required for T008c. **Depends on**: T005b, T018, T004, T014a-verify.
- [X] T008-impl [US1] **Implement Ablation Study Logic**. **Logic**: Implement `code/ablation.py` to iterate through each trajectory and each memory layer, remove the layer, re-run the engine via `code/engine_runner.py --ablate-layer <layer_name> --trajectory <id> --initial_state_hash <hash>`, and compute `utility_delta = baseline_win_rate - ablated_win_rate`. **Output**: Logic ready for execution. **Depends on**: T018. <!-- ATOMIZE: requested -->
- [ ] T008 [US1] **Generate Ground Truth Labels (Ablation – Training Set)**. **Logic**: Execute `code/ablation.py` on `data/processed/train_set.csv` using baseline values from `data/processed/baseline_win_rates_train.json`. **Output**: `data/processed/ablation_labels_train.json` (schema: `{"trajectory_id": "<id>", "layer_name": "<name>", "utility_delta": <float>}`). **Constraint**: Requires T008-baseline. **Depends on**: T008-baseline, T008-impl, T018, T004, T014a-verify. <!-- ATOMIZE: requested -->
- [ ] T008-verify [US1] **Validate Ablation Output (Training)**. **Logic**: Ensure `data/processed/ablation_labels_train.json` exists and contains at least one entry. **Action**: If missing/empty, raise `FileNotFoundError`. **Depends on**: T008.
- [ ] T008c [US1] **Generate Ground Truth Labels (Ablation – Hold‑out Set)**. **Logic**: Execute `code/ablation.py` on `data/processed/validation_set.csv` using baseline values from `data/processed/baseline_win_rates_holdout.json`. **Output**: `data/processed/ablation_labels_holdout.json` (schema: `{"trajectory_id": "<id>", "layer_name": "<name>", "utility_delta": <float>}`). **Constraint**: Requires T008b-baseline. **Depends on**: T008b-baseline, T008-impl, T018, T004, T014a-verify.
- [ ] T008c-verify [US1] **Validate Ablation Output (Hold‑out)**. **Logic**: Ensure `data/processed/ablation_labels_holdout.json` exists and contains at least 20 entries. **Action**: If not, raise `ValueError`. **Depends on**: T008c.
- [ ] T008d [US1] **Merge Ground Truth Utility (Training)**. **Logic**: Join `ablation_labels_train.json` with `metrics_with_moves.csv` to produce `data/processed/ground_truth_utility_train.csv` (columns include `utility_delta`). **Depends on**: T006a, T008, T008-verify.
- [ ] T008d-verify [US1] **Validate Merged Utility (Training)**. **Logic**: Verify `utility_delta` column exists and is numeric. **Depends on**: T008d.
- [ ] T008e [US1] **Merge Ground Truth Utility (Hold‑out)**. **Logic**: Same as T008d but for hold‑out set, producing `data/processed/ground_truth_utility_holdout.csv`. **Depends on**: T006a, T008c, T008c-verify.
- [ ] T008e-verify [US1] **Validate Merged Utility (Hold‑out)**. **Logic**: Verify `utility_delta` column exists and is numeric. **Depends on**: T008e.

### Sub-Phase 2D: Proxy Validation & Model Training

- [ ] T014-impl [US3] **Implement Proxy Validation Logic**. **Logic**:
 1. **Generate Proxy**: Load `data/raw/original_static_logs.jsonl` and compute `proxy_utility` per layer by calculating the **mean retrieval frequency** per layer across the hold-out set. Output `proxy_utility_labels.csv` (columns: `trajectory_id,layer_name,proxy_utility`).
 2. **Validate**: Join `proxy_utility_labels.csv` with `ground_truth_utility_holdout.csv` and calculate Pearson correlation (`scipy.stats.pearsonr`).
 3. **Gate**: Write `proxy_valid` boolean to `data/processed/proxy_validation_report.json`. If correlation < 0.7, set `proxy_valid:false` and set `USE_HEURISTIC=true` in `data/processed/config_state.json`.
 **Output**: `data/processed/proxy_validation_report.json`, `data/processed/proxy_utility_labels.csv`. **Depends on**: T008e, T008d, T006a, T005b-d.
- [ ] T014 [US3] **Execute Proxy Validation**. **Logic**: Run `code/proxy_validator.py` (implemented in T014-impl). **Output**: `data/processed/proxy_validation_report.json`. **Depends on**: T014-impl.
- [ ] T014-verify [US3] **Validate Proxy Report**. **Logic**: Ensure `proxy_validation_report.json` exists and contains a boolean `proxy_valid`. **Depends on**: T014.
- [ ] T009 [US1] **Train Lightweight Classifier**. **Input**: `data/processed/ground_truth_utility_train.csv`. **Logic**:
 - If `USE_HEURISTIC=true` (from T014a or T014), train a fixed‑k=2 heuristic.
 - Else if `proxy_valid=true` (from T014), train on `proxy_utility_labels.csv` (if correlation high enough) OR `ground_truth_utility_train.csv` (if ablation preferred).
 - Else train on `ground_truth_utility_train.csv`.
 **Output**: `models/layer_utility_classifier.pkl`. **Depends on**: T008d-verify, T014-verify, T014a-verify.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

### Tests for User Story 1 (OPTIONAL)

- [X] T012 [P] [US1] Unit test for entropy calculation edge cases in `tests/unit/test_entropy.py`.

### Implementation for User Story 1 (Dynamic Policy)

- [X] T015a [US1] **Minimum Context Floor Logic** in `code/simulator.py`. If calculated context < `MIN_CONTEXT` (256 tokens), prepend the "Current Objective" layer. **Output**: Updated simulation state.
- [ ] T015-impl [US1] **Implement Dynamic Retrieval Agent**. **Logic**: Implement `code/dynamic_agent.py` to orchestrate the turn-by-turn loop: (1) Calculate entropy for current turn, (2) Query trained classifier (T009) for top-k layers, (3) Apply token budget constraints (T015c), (4) Apply minimum context floor (T015a). **Output**: Logic ready for execution. **Depends on**: T009, T015a.
- [X] T015b [US1] **Dynamic Layer Selection** in `code/simulator.py`. Use the trained classifier (T009) to predict utility and select top‑k layers constrained by token budget. If entropy module returns `NaN`/`Infinity` sentinel, force selection of the full "all‑layers" set. **Output**: Selected layer list.
- [X] T015c [US1] **Enforce Maximum Token Budget** in `code/simulator.py`. If prompt exceeds the model's context window, prune least‑useful layers until within budget. Log each pruning event to `data/processed/pruning_logs.jsonl` with schema:
 ```json
 {"trajectory_id":"<id>","initial_tokens":<int>,"selected_layers":[...],"final_tokens":<int>,"layers_pruned":[...],"pruning_reason":"<string>"}
 ```
- [ ] T017-impl [US1] **Update Main Script**. **Logic**: Update `code/main.py` to handle `--mode dynamic`, `--mode static`, and `--mode random` flags, and to orchestrate the simulation loops using `engine_runner.py` and `dynamic_agent.py`. **Output**: `code/main.py` updated. **Depends on**: T015-impl, T018.
- [ ] T017 [US1] **Execute Dynamic Simulation on Test Set**. **Pre-check**: Verify `code/main.py` exists and handles `--mode dynamic`. **Logic**: Run `python code/main.py --mode dynamic --split test`. **Output**: `data/processed/simulation_logs_dynamic.json`. **Depends on**: T015a, T015b, T015c, T018, T009, T017-impl.
- [ ] T019 [US2] **Execute Static All‑Layers Baseline**. **Pre-check**: Verify `code/main.py` handles `--mode static`. **Logic**: Run `python code/main.py --mode static --split test`. **Output**: `data/processed/simulation_logs_static.json`. **Depends on**: T018, T017-impl. **Note**: Can run in parallel with T009 and T017.
- [ ] T020 [US2] **Execute No‑Store Random Baseline**. **Pre-check**: Verify `code/main.py` handles `--mode random`. **Logic**: Run `python code/main.py --mode random --split test`. **Output**: `data/processed/simulation_logs_random.json`. **Depends on**: T018, T017-impl. **Note**: Can run in parallel with T009 and T017.
- [X] T021 [US2] **Aggregate Metrics per Condition**. Read the three simulation logs and compute for each condition:
 - average win rate
 - average token count
 - standard deviation of token count
 - token reduction percentage vs static (`(static‑dynamic)/static * 100`)
 - **standard deviation of token savings** (`std_dev_token_savings`) across trajectories
 - `threshold_met` flag (true if token reduction ≥ 30%)
 Write to `data/processed/baseline_aggregation.csv` with columns:
 `condition,win_rate,avg_tokens,std_dev_tokens,token_reduction_pct,std_dev_token_savings,threshold_met`. **Depends on**: T017, T019, T020.
- [X] T021-verify [US2] **Verify Aggregation Output**. Ensure `baseline_aggregation.csv` exists and contains all required columns with numeric types. **Depends on**: T021.
- [ ] T022 [US2] **Generate Summary CSV**. Create `data/processed/baseline_comparison.csv` summarizing condition, win_rate, avg_tokens, token_reduction_pct, threshold_met. **Depends on**: T021.
- [ ] T022a [US2] **Per‑Trajectory Token Savings**. **Logic**: Join `simulation_logs_dynamic.json` and `simulation_logs_static.json` on `trajectory_id` AND `initial_state_hash`. Calculate `savings = static_tokens - dynamic_tokens` for each matched pair. **Error Handling**: If `initial_state_hash` is missing from a log, skip the row and log to `edge_case_warnings.log`. Write `data/processed/token_savings_per_trajectory.csv` (`trajectory_id,static_tokens,dynamic_tokens,savings`). **Constraint**: If trajectories diverged (no match on `initial_state_hash`), exclude from this calculation and log to `edge_case_warnings.log`. **Depends on**: T017, T019.
- [ ] T023 [US2] **Token Reduction Consistency Check**. **Logic**: Calculate standard deviation of `savings` from `token_savings_per_trajectory.csv`. **Validation**: If `n < 30` (valid pairs), log warning and set `passed:false` due to insufficient sample size. Else, if `std_dev < 0.10 * mean_savings` set `passed:true` else `false`. Write `data/processed/token_consistency_report.json` (`{ "passed": <bool>, "n": <int>, "std_dev": <float> }`). **Depends on**: T022a.

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

### Tests for User Story 3 (OPTIONAL)

- [X] T023a [P] [US3] Unit test for McNemar's test selection logic in `tests/unit/test_stats.py`.

- [ ] T024 [P] [US3] **Verify Paired Status**. **Logic**: Compare `simulation_logs_dynamic.json` and `simulation_logs_static.json` on `trajectory_id` and `initial_state_hash`. If all pairs match, `is_paired=true`. If mismatches exist, list `excluded_trajectory_ids`. **Output**: `data/processed/paired_status.json` (`{ "is_paired": <bool>, "valid_trajectory_ids": [...], "excluded_trajectory_ids": [...] }`). **Depends on**: T017, T019.

- [X] T025a [US3] **Generate Exclusion List**. If `is_paired` is false, log a warning and produce `data/processed/exclusion_report.json` containing `is_paired`, `valid_trajectory_ids`, `excluded_trajectory_ids`, and `divergence_rate`. **Depends on**: T024.

- [ ] T025a-verify [US3] **Verify Exclusion Filter**. Confirm that `excluded_trajectory_ids` are a subset of `test_set.csv` and that `valid_trajectory_ids` intersect correctly. Write `data/processed/exclusion_verification.json` (`{ "filter_verified": <bool> }`). **Depends on**: T025a.

- [ ] T025-impl [US3] **Implement Statistical Tests Logic**. **Logic**: Implement `code/stats.py` with:
 1. **Paired case**: McNemar's test for win/loss; Paired t-test for token usage.
 2. **Unpaired case**: Fisher's Exact Test for win/loss (for binary outcomes); Permutation test (10,000 permutations) for token usage if n > 30, else Z-test for proportions.
 3. **Correction**: Apply Bonferroni correction to all p-values (multiply by number of tests). [UNRESOLVED-CLAIM: c_9561a618 — status=not_enough_info]
 **Output**: Logic ready for execution. **Depends on**: T025a.

- [ ] T025b [US3] **Execute Statistical Tests**.
 1. **Paired case** (`is_paired:true`): Run McNemar's test on win/loss outcomes and paired t‑test on token usage.
 2. **Unpaired case** (`is_paired:false`): Filter to `valid_trajectory_ids` and run Fisher's Exact Test (or Z-test if n > 30) for both outcomes.
 Always apply Bonferroni correction. Write results to **single** file `data/processed/statistical_test_results.json` with schema:
 ```json
 {
 "test_type": "mcnemar" | "fisher" | "permutation",
 "win_rate": { "p_value": <float>, "effect_size": <float>, "ci": [<float>,<float>] },
 "token_usage": { "p_value": <float>, "effect_size": <float>, "ci": [<float>,<float>] }
 }
 ```
 **Depends on**: T025a, T025a-verify, T017, T019, T022a, T025-impl.

- [X] T025c [US3] **Analyze Divergence Metrics**. Read `exclusion_report.json` and output `data/processed/divergence_analysis.json` with fields `divergence_rate`, `impact_assessment`, `recommendation`. **Depends on**: T025a.
- [ ] T026 [US3] **Generate Success Criteria Report**. **Logic**: Aggregate results from T022, T023, T025b, T025c into `data/processed/success_criteria_report.json` mapping SC‑001‑SC‑004 to `pass`/`fail`. **Failure Logic**:
 - If SC-001 (Win Rate Significance) fails → `pass: false`.
 - If SC-003 (Token Usage Significance) fails → `pass: false`.
 - If SC-004 (Consistency) fails → `pass: false`.
 - If SC-002 (Token Reduction ≥ 30%) fails → `threshold_met: false` but **do not abort**; pipeline continues.
 - Write `pass: true` only if SC-001, SC-003, SC-004 pass. **Output**: `data/processed/success_criteria_report.json`. **Depends on**: T022, T023, T025b, T025c.

---

## Phase 5: Performance & Validation (Required for Final Report)

- [X] T031c [P] **Runtime Monitoring**. If total runtime > 6 h, log suggestion to enable streaming or batch reduction. [UNRESOLVED-CLAIM: c_20dcc60d — status=not_enough_info] Output: `data/processed/runtime_report.json`.
- [X] T039 [P] **Memory Usage Verification**. Stream a 1 GB file and ensure peak RSS < 7 GB; write `data/processed/memory_report.json`.
- [ ] T044 [P] **Power Analysis**. **Logic**: Perform power analysis (α=0.05, power=0.8, effect size=0.2) on the sample size used. Write `data/processed/power_analysis.json` including `sample_size`, `achieved_power`, and warning if `n < 300`. **Depends on**: T014a.
- [ ] T050 [P] **Divergence Check**. **Logic**: Compute percentage of trajectories where final state hash differs; flag if > 10%. Output: `data/processed/divergence_report.json`. **Depends on**: T017, T019.

---

## Phase 6: Revision & Edge Case Resolution (Addressing Review Concerns)

- [X] T051 [US1] **Enforce Strict Data Fallback Policy**. Refactor `parser.py`, `entropy.py`, `ablation.py` to remove silent synthetic fallbacks; raise `FileNotFoundError` for missing files. Exceptions allowed only for NaN handling in T006b. **Depends on**: T001.
- [X] T052 [US1] **Implement Streaming Data Ingestion**. Update `parser.py` to use `ijson` or `datasets.load_dataset(..., streaming=True)` for line‑by‑line processing. **Depends on**: T006a, T002.
- [ ] T053 [US3] **Formalize Statistical Power Reporting**. Enhance `power_analysis.json` to include sample size `n`, achieved power, and warning if `n < 300` (exact text: "Statistical power marginal; results should be interpreted with caution."). **Depends on**: T014a, T044.
- [ ] T054 [US3] **Verify Exclusion List Integrity**. Ensure `excluded_trajectory_ids` match mismatched hashes from `paired_status.json`. **Depends on**: T025a, T024.

---

## Phase 7: Final Review & Documentation (Revision Round 1)

- [X] T055 [US3] **Enhance Edge Case Documentation**. Populate `docs/edge_cases.md` with all warnings from `edge_case_warnings.log`, including NaN entropy, sample‑size < 300, and homogeneity warnings, plus mitigation strategies. **Depends on**: T006b, T014a, T053.
- [ ] T056 [US1] **Aggregate Token Budget Logs**. Convert `pruning_logs.jsonl` into `data/processed/token_budget_detailed.csv` (JSON‑stringify list columns). **Depends on**: T015c, T017.
- [X] T057a [US3] **Generate Statistical Report Template**. Create `data/processed/statistical_analysis_report_template.md` with placeholders; the `{{sample_limitation}}` placeholder **must be filled** with the exact warning: "Statistical power marginal (n<300); results should be interpreted with caution." **Depends on**: None.
- [ ] T057b [US3] **Aggregate Statistical Data**. Combine results from `statistical_test_results.json`, `power_analysis.json`, and `divergence_analysis.json` into `data/processed/agg_stats.json`. **Depends on**: T025b, T025c, T044, T050.
- [ ] T057c [US3] **Assemble Final Statistical Report**. Populate the template from T057a with data from `agg_stats.json` and `success_criteria_report.json`, producing `data/processed/statistical_analysis_report.md`. **Depends on**: T057a, T057b, T026.
- [ ] T058 [US1] **Validate Data Pipeline Integrity**. Verify checksums, existence of all intermediate files, and generate `data/processed/pipeline_validation_report.json`. **Depends on**: T005b, T006a, T008, T009, T017, T019, T025b.

---

## Phase 8: Final Verification & Cleanup (Revision Round 2)

- [X] T059 [US3] **Verify NaN/Inf Handling End‑to‑End**. Unit tests for entropy NaN/Inf (as in T012) plus integration test confirming that `code/simulator.py` (T015b) receives the sentinel and selects the full "all‑layers" set, logging a warning. Output: updated `tests/unit/test_entropy_nan_handling.py` and verified `edge_case_warnings.log`. **Depends on**: T006b, T055, T015b.
- [X] T060 [US1] **Validate Token Budget Pruning Logic**. Integration test ensuring that when token budget is exceeded, least‑useful layers are pruned, the "Current Objective" layer remains per floor rule, and `pruning_reason` is correctly recorded. Output: updated `tests/integration/test_token_budget_pruning.py` and verified `pruning_logs.jsonl`. **Depends on**: T015c, T056.
- [ ] T061 [US3] **Finalize Statistical Power Report**. Ensure `power_analysis.json` contains the exact warning text for n < 300 and that `final_report.md` reflects this. **Depends on**: T053, T055.
- [X] T062 [US1] **Verify Streaming Data Ingestion**. Test with a large synthetic file to confirm `parser.py` stays within memory limits; write `data/processed/streaming_verification_report.json`. **Depends on**: T052, T039.
- [ ] T063 [US3] **Final Statistical Report Assembly**. Assemble the comprehensive report by concatenating `statistical_analysis_report.md`, `success_criteria_report.json`, and `final_report.md` into `data/processed/final_comprehensive_report.md`. **Depends on**: T057c, T061, T058.
- [ ] T064 [US1] **Final Data Pipeline Validation**. Run an end‑to‑end validation after all previous steps, ensuring every artifact matches checksums and no data corruption. Output: `data/processed/final_pipeline_validation_report.json`. **Depends on**: T058, T062.
- [X] T065 [US3] **Final Documentation Review**. Review and update all documentation (`docs/edge_cases.md`, `final_comprehensive_report.md`, `README.md`) for clarity and completeness. **Depends on**: T055, T063, T064.