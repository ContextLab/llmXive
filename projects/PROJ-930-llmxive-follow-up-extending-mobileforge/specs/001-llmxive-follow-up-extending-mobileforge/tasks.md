# Tasks: llmXive Follow-up: Extending MobileForge with CPU-Tractable Logic Distillation

**Input**: Design documents from `/specs/002-mobileforge-logic-distillation/`
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

- [ ] T001 Create project directory structure: Execute `mkdir -p projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{data/raw,data/processed,data/evaluation,models,utils,tests/unit,tests/integration}`
- [ ] T001b Initialize project config files: Execute `touch projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{requirements.txt,README.md}`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin, including Power Analysis to determine N *before* data extraction.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinned `torch`, `transformers`, `datasets`, `pandas`, `scikit-learn`, `pytest`, `statsmodels`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup `state/` directory for artifact checksums and versioning (Constitution Principle III)
- [ ] T005 [P] [Foundational] Implement `utils/emulator.py`: Thin wrapper for interacting with the `androidworld` dataset evaluation interface. Must expose functions: `launch_emulator()`, `send_action(action_seq)`, `check_crash()`, `get_screenshot()`. Must define error codes: `EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`. **Produces the interface required by US3 (T026/T027)**.
- [ ] T005a [P] [Foundational] Implement `tests/unit/test_emulator.py` with mock emulator fixtures to verify T005 functions in isolation.
- [ ] T006 [P] Setup `utils/metrics.py` base classes for "Success Rate" and "Step Efficiency" calculation
- [ ] T007 [P] Create base data entities and schema definitions in `code/data/schema.py` for `ExtractionDataset`, `DistilledModel`, and `EvaluationResult`
- [ ] T008 Configure environment variable management for dataset paths and random seeds (Constitution Principle I)
- [ ] T009 [P] [Foundational] Implement `utils/power_analysis.py` script: Define function `calculate_required_n(effect_size=0.2, alpha=0.05, power=0.8) -> dict` which returns `{'validated_n': int, 'effect_size': float, 'power': float, 'baseline_p0': 0.5}`. **Explicitly forbid accepting any 'estimated p0' from pilot data; use ONLY the assumed p0=0.5.** **Runtime Check:** Before calculation, verify that no data extraction artifacts (e.g., `data/processed/`, `state/extraction_stats.json`) exist with timestamps newer than the script start; if found, script MUST fail with "A priori constraint violated: Data extraction detected before power analysis." Output must be written to `state/validated_n.json` with the exact schema: `{"validated_n": <int>, "effect_size": 0.2, "power": 0.8, "baseline_p0": 0.5}`. **This N is the authoritative sample size for evaluation and must be calculated BEFORE data extraction.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Dataset Construction (Priority: P1) 🎯 MVP

**Goal**: Extract and filter `(UI_state, Corrective_Hint, Action)` triples from MobileForge logs, ensuring "failed-then-success" trajectories and purely linguistic hints.

**Independent Test**: Running `code/utils/extraction.py` against raw logs produces a CSV/JSON with sufficient valid triples (target determined by T009), no nulls in key fields, and zero coordinate-based hints.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for "failed-then-success" filter logic in `code/tests/unit/test_extraction.py`
- [ ] T011 [P] [US1] Unit test for "coordinate-free" hint validation regex in `code/tests/unit/test_extraction.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/raw/download_mobileforge.py`: Fetch real data from verified Hugging Face source (`datasets.load_dataset("mobileforge")`). Must fail loudly on network error (no synthetic fallback).
- [ ] T013 [US1] Implement `code/utils/extraction.py`: Log parser to extract `(UI_state, Corrective_Hint, Action)` triples from raw logs.
- [ ] T014 [US1] Implement `code/utils/extraction.py`: Filter logic for "initial failure, post-hint success" trajectories.
- [ ] T015 [US1] Implement `code/utils/extraction.py`: Hint purity checker to exclude coordinate-based visual grounding (e.g., `[x,y]`).
- [ ] T016 [US1] Implement `code/utils/extraction.py`: **First step: Read `state/validated_n.json` to retrieve N.** **Dependency: T009 must complete before this task.** **Runtime Check:** Verify `state/validated_n.json` exists and was generated before any data extraction artifacts (check timestamps). If `validated_n.json` is missing or data artifacts are newer, script MUST exit with code 1 and a fatal error "A priori constraint violated". Count valid triples. **If count < N, script MUST exit with code 1 and a fatal error message "Dataset Volume Insufficient: X < N".** Do NOT log a warning and continue. Generate `ExtractionDataset` (CSV/Parquet) at `code/data/processed/triples_v1.parquet`. **Write valid triple count and validation status to `state/extraction_stats.json` with schema `{"valid_count": <int>, "status": "PASS|FAIL"}`.**
- [ ] T017 [US1] Implement checksum generation for `ExtractionDataset` in `state/` (Constitution Principle III)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Tractable Model Training (Priority: P2)

**Goal**: Train a lightweight T5-small (Encoder-Decoder, ≤100M params) model on CPU to predict action sequences from UI states and hints.

**Independent Test**: Training job on `ubuntu-22.04` runner completes in ≤6 hours, Final loss converges, with no GPU/CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model initialization ensuring CPU-only device mapping in `code/tests/unit/test_train.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/models/train_distilled.py`: Initialize T5-small (Encoder-Decoder, ≤100M params) with `device="cpu"` and sequence generation head (per amended FR-002).
- [ ] T021 [US2] Implement `code/models/train_distilled.py`: Data loading with streaming/chunking to fit ≤7GB RAM constraint.
- [ ] T020 [US2] Implement `code/models/train_distilled.py`: Training loop with loss monitoring and convergence check. **Script must log final loss.** **CRITICAL CONSTRAINT: The script MUST enforce a hard timeout of a predetermined duration. (e.g., via `signal.alarm` or `subprocess` timeout). If the 6-hour limit is exceeded, the script MUST exit with code 1 and the message "Training Timeout: Exceeded 6 hours", failing the build immediately to satisfy SC-003.**
- [ ] T022 [US2] Add explicit assertion/error check to fail loudly if CUDA device is detected (Constitution Principle VI).
- [ ] T023 [US2] Save `DistilledModel` weights and config to `code/models/` upon completion.
- [ ] T024 [US2] Log training duration and resource usage to verify ≤6h CPU constraint.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate the distilled model against a TinyLlama baseline on a representative set of unseen AndroidWorld tasks, performing statistical significance testing with a paired design.

**Independent Test**: Evaluation script produces success rate, step efficiency, and a p-value < 0.05 from McNemar's test with power ≥ 0.8.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Integration test for emulator interaction with task execution in `code/tests/integration/test_eval.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `code/data/evaluation/`: **First step: Read `state/validated_n.json` to retrieve N.** **Dependency: T009 must complete before this task.** Load **N** tasks from `androidworld` dataset (DOI:10.48550/arXiv.2405.14793) using `datasets.load_dataset("androidworld")`. **If the dataset contains fewer than N unique tasks, script MUST exit with code 1 and a fatal error message "Dataset Size Insufficient: X < N".** Do NOT proceed with available tasks. Ensure task IDs are tracked for pairing. Output the list of task IDs to `data/evaluation/tasks.json`.
- [ ] T027 [US3] Implement `code/models/eval.py`: **Load task IDs from `data/evaluation/tasks.json`.** Execution loop for `DistilledModel` on the tracked tasks via headless emulator.
- [ ] T028 [US3] Implement `code/models/eval.py`: **Load task IDs from `data/evaluation/tasks.json`.** Execution loop for TinyLlama baseline on the **exact same** tracked tasks (same task IDs) to enable pairing.
- [ ] T029 [US3] Implement `code/models/eval.py`: **Load task IDs from `data/evaluation/tasks.json`.** "Generic retry" prompt baseline run on the **same** set of tasks for ablation study (Constitution Principle VII), distinct from primary TinyLlama comparison. **Output results to `data/results/ablation_results.json` with schema `{"task_id": <str>, "success": <bool>}`.** *Dependency: T026 must complete before this task.*
- [ ] T030 [US3] Implement `code/utils/metrics.py`: **Load task IDs from `data/evaluation/tasks.json`.** Calculate "Success Rate" and "Step Efficiency" for both models. **Output paired results to `data/results/results.csv` with columns: `task_id`, `distilled_success` (binary True/False), `baseline_success` (binary True/False), `distilled_efficiency`, `baseline_efficiency`.** **Verify that all task IDs from `tasks.json` are present in both model outputs.** Ensure `data/results/` directory exists before writing.
- [ ] T031 [US3] Implement `code/utils/metrics.py`: **Load paired results from `data/results/results.csv`.** **Explicitly verify that the input data contains paired binary outcomes (Success/Fail) from the exact same task instances (same task_id) for both models.** **Extract the binary `distilled_success` and `baseline_success` columns to construct the 2x2 contingency table (cells: a=both success, b=distilled success/baseline fail, c=distilled fail/baseline success, d=both fail).** Perform **McNemar's test** (for binary outcomes) comparing Distilled vs. TinyLlama baseline. **Dependency: T037 (Ablation Report) must complete before this task to ensure the ablation study accompanies the performance claim.** *Dependency: T030 must complete before this task.*
- [ ] T033 [US3] Generate `EvaluationResult` report with metrics, p-values, and power analysis in `data/results/`. **Dependency: T037 must complete.**
- [ ] T037 [US3] Generate `AblationReport` comparing "hint" input vs. "generic retry" baseline performance **using results from `data/results/ablation_results.json`**. **Output to `state/ablation_report.md` (Markdown format) including quantitative metrics: success rate difference, p-value.** *Dependency: T029 must complete before this task.*

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis & Robustness (Priority: P3)

**Goal**: Verify robustness of results against "inconsistency tolerance" threshold variations and perform stress tests.

**Independent Test**:

### Implementation for User Story 4

- [ ] T034 [US4] Implement `code/models/eval.py`: Sensitivity sweep logic for "inconsistency tolerance" thresholds across a range of Levenshtein distances as mandated by FR-006.
- [ ] T035 [US4] Implement `code/utils/metrics.py`: Variance calculation for success rates across swept thresholds.
- [ ] T036 [US4] Generate `SensitivityReport` in `data/results/` measuring variance across swept thresholds (no hard pass/fail threshold, per SC-005). **Dependency: T037 must complete to ensure ablation context is available.**

**Note**: T037 (Ablation Report) is located in Phase 5 (US3) to maintain logical grouping with its data source (T029), though US4 can start in parallel with US3 execution.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Documentation: Update `README.md` with CLI usage examples and installation instructions.
- [ ] T040b [P] Documentation: Update `README.md` with pinned dependency list and version info.
- [ ] T040c [P] Documentation: Generate architecture diagram in `docs/` showing data flow from logs to model to eval.
- [ ] T041a [P] Code cleanup: Remove unused imports and variables across `code/`.
- [ ] T041b [P] Code cleanup: Enforce line length < 88 and formatting consistency (black).
- [ ] T041c [P] Code cleanup: Fix missing type hints in `code/utils/` and `code/models/`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must complete before US2 (Training needs dataset) and US3 (Evaluation needs model)
 - **US2 (P2)**: Must complete before US3 and US4 (Evaluation needs model)
 - **US3 (P3)**: Can run in parallel with US4 once US2 is complete
 - **US4 (P3)**: Can run in parallel with US3 once US2 is complete (Note: Final US4 reporting depends on US3 completion)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (Dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (Tasks) and US2 (Model)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (Model). **Final reporting (T036) depends on US3 completion (T037 results)** to ensure ablation context is available.

### Specific Artifact Dependencies

- **T009 (N Calculation)**: Must complete before T016 (Data Extraction) and T026 (Evaluation Load). T009 is in Phase 2; T016/T026 are in Phase 3/5. **Explicitly enforced by file existence and timestamp checks.**
- **T029 (Ablation Run)**: Must complete before T037 (Ablation Report). T029 is in Phase 5; T037 is in Phase 5.
- **T005 (Emulator)**: Provides interface for T026/T027.
- **T016 (Data Extraction)**: Must complete before T017 (Checksums).
- **T037 (Ablation Report)**: Must complete before T031 (McNemar's Test) and T033 (Evaluation Report) and T036 (Sensitivity Report).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
 - **US1** must run first (blocks US2)
 - Once **US1** completes, **US2** can start
 - Once **US2** completes, **US3** and **US4** can start in parallel
- All tests for a user story marked [P] can run in parallel

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Data Constraint**: All data loaders MUST fail loudly on missing real data; no synthetic fallbacks allowed.
- **Critical Compute Constraint**: All training must be explicitly CPU-only; any CUDA usage must trigger an immediate failure.
- **Architecture Note**: Tasks now mandate T5-small (Encoder-Decoder) per amended FR-002.
- **Statistical Note**: Tasks now mandate McNemar's test and A priori analysis per amended FR-005/FR-007.
- **Power Analysis Note**: T009 calculates N using assumed parameters (p0=0.5) BEFORE data extraction (T016) to satisfy "A priori" requirement. Includes runtime timestamp checks.
- **Data Volume Note**: T016 and T026 now enforce N as a hard constraint; scripts MUST exit with code 1 if data is insufficient or if `validated_n.json` is missing.
- **Ablation Note**: T029 outputs to `data/results/ablation_results.json`; T037 reads from this file to generate `state/ablation_report.md`. T037 is a strict dependency for T031, T033, and T036.
- **Sensitivity Note**: T034 explicitly sweeps thresholds [0, 1, 2, 3].
- **Performance Note**: T020 now explicitly enforces the 6-hour timeout as a hard failure condition, resolving the previous contradiction.