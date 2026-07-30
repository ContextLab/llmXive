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

**Data Flow**: T005b (Real Data Ingest) -> T006a (Parser) -> T006b (Entropy) -> T014a (Split) -> T008 (Ablation) -> T008d (Fallback) -> T014 (Validator) -> T009 (Train)

- [X] T004 Implement `code/config.py` for paths, seeds, and hyperparameters. Define `TOKEN_BUDGET=4096`, `MIN_CONTEXT=256`, AND `K_RANDOM_BASELINE=2` as explicit constants loaded from config or env vars.
- [X] T005b [US1] **Ingest Real AgenticSTS Trajectories**. **Logic**: Attempt to fetch the existing AgenticSTS trajectories from the canonical source. (e.g., ` or the specific AgenticSTS repo). **Action**: Download raw JSON/JSONL files to `data/raw/`. **Validation**: Verify checksums against the provided manifest. **Output**: `data/raw/agenticsts_trajectories.jsonl`. **Constraint**: This task MUST run BEFORE T006a. **Skip Condition**: If `data/raw/agenticsts_trajectories.jsonl` already exists and checksums match, skip. **CRITICAL**: If this task fails (network error, checksum mismatch), the pipeline MUST proceed to T005a ONLY if `data/raw/` is empty. **Depends on**: None.
- [X] T005a [US1] **Generate No-Data Warning**. **Logic**: If T005b fails AND T006a is skipped (due to missing input), generate `data/processed/edge_case_warnings.log` with the exact text: "Warning: No trajectory data available for entropy calculation; pipeline cannot proceed." **Action**: Write a newline-delimited JSON line to `data/processed/edge_case_warnings.log` with `{"level": "WARN", "message": "No data available", "timestamp": "<ISO8601>"}`. **Constraint**: This task MUST run AFTER T005b and T006a (to detect if T006a was skipped due to missing input). **Run Condition:** `CI=true` or local development where CI is not running. **Depends on**: T005b, T006a.
- [X] T006a [P] [US1] Implement `code/parser.py` to extract per-turn metrics from raw trajectory logs in `data/raw/`. **Input**: JSONL/JSON files from T005b. **Schema Definition**: `{"type": "object", "properties": {"trajectory_id": {"type": "string"}, "turn": {"type": "integer"}, "legal_moves": {"type": "array", "items": {"type": "string"}}}}`. **Validation**: MUST validate each file against `contracts/trajectory.schema.yaml` before processing. Raise `ValueError` if schema mismatch. **Logic**: If `CI=false` and `DEV_MODE=true` and input file is missing, generate a minimal synthetic dataset for local testing. **Else**: Raise `FileNotFoundError` ("Real data missing; pipeline cannot proceed"). **Output**: `data/processed/metrics_with_moves.csv`. **Depends on**: T005b.
- [X] T006b [P] [US1] Implement entropy calculation in `code/entropy.py`. **Logic**: Calculate Shannon entropy of the legal move distributions extracted by T006a. **Input**: `data/processed/metrics_with_moves.csv`. **Skip Condition**: If `data/processed/metrics_with_moves.csv` does not exist (e.g., T006a was skipped), skip this task. **Output**: `data/processed/entropy_metrics.csv`. **Depends on**: T006a.
- [X] T008 [US1] Generate ground truth labels (ablation study). **Logic**: Run the ablation study on the training set to generate utility labels by re-running the game engine with specific layers removed. **Input**: `data/raw/agenticsts_trajectories.jsonl`. **Output**: `data/processed/ablation_labels_train.json`. **Constraint**: If this fails, the pipeline MUST NOT proceed with mock data.
- [X] T008d [US1] **Ablation Failure Handling**. **Logic**: If T008 fails to generate ablation labels, log a CRITICAL error to `data/processed/edge_case_warnings.log` and generate `data/processed/fallback_flag.json` with `{"fallback": true, "use_heuristic": true, "reason": "Ablation study failed"}`. **Action**: Do NOT generate mock data. The pipeline must either fail or switch to a fixed-k heuristic (k=2) for training. **Constraint**: This task ensures the 'Verified Accuracy' principle is maintained by preventing fabrication. **Depends on**: T008.
- [X] T014a [P] [US1] Implement data splitting logic in `code/splitter.py`. **Input**: `data/processed/metrics_with_moves.csv`. **Output**: `data/processed/train_set.csv`, `data/processed/ablation_train_set.csv`, `data/processed/validation_set.csv`, `data/processed/test_set.csv`.
- [X] T014 [US1] Implement proxy validation logic in `code/classifier.py`. **Logic**: Load data, calculate Pearson correlation between static log proxy and ablation utility on the Validation set. **Output**: `data/processed/proxy_validation_report.json` containing a boolean `proxy_valid`.
- [X] T009 [US1] Train lightweight CPU-tractable models (Decision Tree/Logistic Regression). **Input**: Ablation labels from T008 or fallback heuristic, if enabled. **Output**: `models/layer_utility_classifier.pkl`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Dynamic Policy & Baselines (Priority: P1, P2) 🎯 MVP

**Goal**: Implement dynamic retrieval agent and baseline simulations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
- [X] T012 [P] [US1] Unit test for entropy calculation edge cases in `tests/unit/test_entropy.py`.

### Implementation for User Story 1 (Dynamic Policy)
- [X] T015a [US1] Implement Minimum Context Floor Logic in `code/simulator.py`. **Logic**: Before any selection, check if the calculated context is below `MIN_CONTEXT` (256 tokens). If so, append the "Current Objective" layer immediately. **Output**: Intermediate state with floor applied.
- [X] T015b [US1] Implement Dynamic Layer Selection in `code/simulator.py`. **Logic**: Use the trained model (T009) to predict utility, then select top-k layers based on entropy prediction or fallback heuristic. **Input**: State from T015a.
- [X] T015c [US1] Enforce Maximum Token Budget in `code/simulator.py`. **Logic**: Ensure the final prompt size is ≤ 4096 tokens. If exceeded, prune least useful layers. **Input**: State from T015b.
- [X] T017 [US1] Execute Dynamic Simulation on the test set. **Output**: `data/processed/simulation_logs_dynamic.json`.
- [X] T018 [P] Implement `code/engine_runner.py` to invoke the engine for re-simulation.
- [X] T019 [US2] [P] Implement "Static All-Layers" baseline execution. **Output**: `data/processed/simulation_logs_static.json`.
- [X] T020 [US2] [P] Implement "No-Store Random" baseline execution. **Output**: `data/processed/simulation_logs_random.json`.
- [X] T021 [US2] Create aggregation script `code/stats.py` to compute average win rate and token usage per condition.
- [X] T022 [US2] Generate summary CSV output in `data/processed/baseline_comparison.csv`. **Logic**: Calculate and report token reduction metrics regardless of the 30% threshold. **Schema**: `condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct`.
- [X] T023 [US2] Implement verification logic to calculate token reduction consistency. **Output**: `data/processed/token_consistency_report.json` with boolean `passed` and schema defined above. This task verifies SC-004. **Schema**: `{"actual_reduction": float, "threshold": float, "message": string}`.

---

## Phase 4: User Story 3 - Statistical Significance Reporting (Priority: P3)

**Goal**: Perform paired statistical tests to validate the dynamic policy's efficacy.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
- [X] T023a [P] [US3] Unit test for McNemar's test selection logic in `tests/unit/test_stats.py`.

- [X] T024 [P] [US3] Verify Paired Status in `code/stats.py`. **Logic**: Confirm that Dynamic and Static runs share the same `trajectory_id` and `initial_state_hash`. **Action**: Compute SHA256 hash of `json.dumps({'initial_state_hash': str, 'trajectory_id': str}, sort_keys=True)` for each trajectory. **Output**: `data/processed/paired_status.json` (boolean `is_paired`).
- [X] T025a [P] [US3] Execute McNemar's Test in `code/stats.py`. **Logic**: If `is_paired` is true, run McNemar's test on win/loss outcomes. **Output**: `data/processed/mcnemar_results.json`.
- [X] T025b [P] [US3] Execute Paired T-Test & Bonferroni in `code/stats.py`. **Logic**: Run paired t-test on token usage, apply Bonferroni correction. **Output**: `data/processed/ttest_results.json`.

---

## Phase 5: Performance & Validation (Optional/Advanced)

**Goal**: Ensure the pipeline meets performance constraints and statistical power requirements.

- [X] T031c [P] [US1] **Runtime Monitoring**. **Logic**: Monitor total runtime of the simulation phase. **Action**: If `total_runtime` (in hours) > 6, refactor code to enable streaming or reduce batch size. **Output**: `data/processed/runtime_report.json`.
- [X] T039 [P] [US1] **Memory Usage Verification**. **Logic**: Verify memory usage < 7GB with `--stream` on a 1GB file. **Action**: Use `psutil` to monitor peak RSS memory. **Output**: `data/processed/memory_report.json`.
- [X] T044 [P] [US1] **Power Analysis**. **Logic**: Implement a power analysis calculation to verify that n=298 is sufficient for the expected effect size (e.g., 0.2) at power=0.8. **Output**: `data/processed/power_analysis.json`.
- [X] T050 [P] [US3] **Divergence Check**. **Logic**: If divergence (percentage of trajectories where final state hash differs) is minimal (< 10%), continue with McNemar's test. **Output**: `data/processed/divergence_report.json`.
