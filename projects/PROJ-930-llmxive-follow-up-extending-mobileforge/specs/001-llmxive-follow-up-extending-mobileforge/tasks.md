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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{data/raw,data/processed,data/evaluation,models,utils,tests/unit,tests/integration}` and `touch projects/PROJ-930-llmxive-follow-up-extending-mobileforge/code/{requirements.txt,README.md}`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin, including Kickback requests for spec amendments.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinned `torch`, `transformers`, `datasets`, `pandas`, `scikit-learn`, `pytest`, `statsmodels`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 Setup `state/` directory for artifact checksums and versioning (Constitution Principle III)
- [ ] T005 [P] Implement `utils/emulator.py`: Headless Android emulator wrapper with robust retry logic for environment crashes. Must expose functions: `launch_emulator()`, `send_action(action_seq)`, `check_crash()`, `get_screenshot()`. Must define error codes: `EMU_CRASH`, `EMU_TIMEOUT`, `EMU_NOT_FOUND`. **Produces the interface required by US3 (T026/T027)**.
- [ ] T005a [P] [US2] Implement `tests/unit/test_emulator.py` with mock emulator fixtures to verify T005 functions in isolation.
- [ ] T006 [P] Setup `utils/metrics.py` base classes for "Success Rate" and "Step Efficiency" calculation
- [ ] T007 [P] Create base data entities and schema definitions in `code/data/schema.py` for `ExtractionDataset`, `DistilledModel`, and `EvaluationResult`
- [ ] T008 Configure environment variable management for dataset paths and random seeds (Constitution Principle I)
- [ ] T009 [P] Implement `utils/power_analysis.py` script structure: Define function `calculate_required_n(effect_size: float, alpha: float, power: float) -> dict` which returns `{'validated_n': int, 'effect_size': float, 'power': float}`. Output must be written to `state/validated_n.json`. *Note: This is an initial estimate.*
- [ ] T019a [P] [Kickback] **Spec Amendment Required**: Update `spec.md`:FR-005 to replace "paired t-test" with "McNemar's test (for binary paired outcomes)". Justification: Binary success/fail outcomes require a test for paired proportions, not continuous means.
- [ ] T019b [P] [Kickback] **Spec Amendment Required**: Update `spec.md`:FR-007 to replace "post-hoc power analysis" with "A priori power analysis". Justification: Post-hoc power is tautological; a priori analysis validates sample size sufficiency before execution.
- [ ] T019c [P] [Kickback] **Spec Amendment Required**: Update `spec.md`:FR-002 to replace "encoder-only model (e.g., DistilBERT)" with "Encoder-Decoder model (e.g., T5-small)". Justification: Sequence generation requires an Encoder-Decoder architecture; encoder-only models cannot natively generate variable-length sequences.
- [ ] T019d [P] [Kickback] **Spec Amendment Required**: Update `spec.md`:US-3 and FR-003 to replace "500 unseen tasks" with "N tasks determined by A priori power analysis (see T032)". Update `spec.md`:SC-006 to reference McNemar's test for statistical power measurement.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Dataset Construction (Priority: P1) 🎯 MVP

**Goal**: Extract and filter `(UI_state, Corrective_Hint, Action)` triples from MobileForge logs, ensuring "failed-then-success" trajectories and purely linguistic hints.

**Independent Test**: Running `code/utils/extraction.py` against raw logs produces a CSV/JSON with sufficient valid triples (target determined by T032), no nulls in key fields, and zero coordinate-based hints.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Unit test for "failed-then-success" filter logic in `code/tests/unit/test_extraction.py`
- [ ] T011 [P] [US1] Unit test for "coordinate-free" hint validation regex in `code/tests/unit/test_extraction.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/raw/download_mobileforge.py`: Fetch real data from verified Hugging Face source (`datasets.load_dataset("mobileforge")`). Must fail loudly on network error (no synthetic fallback).
- [ ] T013 [US1] Implement `code/utils/extraction.py`: Log parser to extract `(UI_state, Corrective_Hint, Action)` triples from raw logs.
- [ ] T014 [US1] Implement `code/utils/extraction.py`: Filter logic for "initial failure, post-hint success" trajectories.
- [ ] T015 [US1] Implement `code/utils/extraction.py`: Hint purity checker to exclude coordinate-based visual grounding (e.g., `[x,y]`).
- [ ] T016 [US1] Generate `ExtractionDataset` (CSV/Parquet) at `code/data/processed/triples_v1.parquet`. **Script must count valid triples. If count < estimated_n (from T009), script must exit with code 1 and log "Dataset Shortage"**.
- [ ] T017 [US1] Implement checksum generation for `ExtractionDataset` in `state/` (Constitution Principle III)
- [ ] T032 [US1] **A Priori Power Analysis & N Finalization**: Implement `code/utils/power_analysis.py` logic to calculate the final required N based on the **actual** extracted triple count from T016 and assumed effect size. Output `validated_n` to `state/validated_n.json`. **This N is the authoritative sample size for evaluation.** *Note: This task runs AFTER T016 and BEFORE T026.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Tractable Model Training (Priority: P2)

**Goal**: Train a lightweight T5-small (Encoder-Decoder, ≤100M params) model on CPU to predict action sequences from UI states and hints.

**Independent Test**: Training job on `ubuntu-22.04` runner completes in ≤6 hours, Final loss ≤0.5, with no GPU/CUDA errors.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model initialization ensuring CPU-only device mapping in `code/tests/unit/test_train.py`

### Implementation for User Story 2

- [ ] T019 [US2] Implement `code/models/train_distilled.py`: Initialize T5-small (Encoder-Decoder, ≤100M params) with `device="cpu"` and sequence generation head (per amended FR-002).
- [ ] T021 [US2] Implement `code/models/train_distilled.py`: Data loading with streaming/chunking to fit ≤7GB RAM constraint.
- [ ] T020 [US2] Implement `code/models/train_distilled.py`: Training loop with loss monitoring and convergence check. **Script must assert final_loss <= 0.5**. If not met, exit with code 1.
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

- [ ] T026 [US3] Implement `code/data/evaluation/`: Load **N** tasks (where N comes from `state/validated_n.json` generated by T032) from `androidworld` dataset (DOI:10.48550/arXiv.2405.14793) using `datasets.load_dataset("androidworld")`. Ensure task IDs are tracked for pairing. *Dependency: T032 must complete before this task.*
- [ ] T027 [US3] Implement `code/models/eval.py`: Execution loop for `DistilledModel` on the tracked tasks via headless emulator.
- [ ] T028 [US3] Implement `code/models/eval.py`: Execution loop for TinyLlama baseline on the **exact same** tracked tasks (same task IDs) to enable pairing.
- [ ] T029 [US3] Implement `code/models/eval.py`: "Generic retry" prompt baseline run on the **same** set of tasks for ablation study (Constitution Principle VII), distinct from primary TinyLlama comparison. **Produces ablation results required by T037.**
- [ ] T030 [US3] Implement `code/utils/metrics.py`: Calculate "Success Rate" and "Step Efficiency" for both models, outputting paired results (task_id -> [distilled_score, baseline_score]) to `data/results/results.csv`.
- [ ] T031 [US3] Implement `code/utils/metrics.py`: Perform **McNemar's test** (for binary outcomes) comparing Distilled vs. TinyLlama baseline on the paired results (same task IDs) to satisfy amended FR-005. Input: 2x2 contingency table from `results.csv` (columns: `task_id`, `distilled_success`, `baseline_success`).
- [ ] T033 [US3] Generate `EvaluationResult` report with metrics, p-values, and power analysis in `data/results/`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Sensitivity Analysis & Robustness (Priority: P3)

**Goal**: Verify robustness of results against "inconsistency tolerance" threshold variations and perform stress tests.

**Independent Test**:

### Implementation for User Story 4

- [ ] T034 [US4] Implement `code/models/eval.py`: Sensitivity sweep logic for "inconsistency tolerance" thresholds across a range of significance levels as mandated by FR-006 and SC-005.
- [ ] T035 [US4] Implement `code/utils/metrics.py`: Variance calculation for success rates across swept thresholds.
- [ ] T036 [US4] Generate `SensitivityReport` in `data/results/` measuring variance across swept thresholds (no hard pass/fail threshold, per SC-005).
- [ ] T037 [US4] Generate `AblationReport` comparing "hint" input vs. "generic retry" baseline performance **using results from T029**. *Dependency: T029 must complete before this task.*
- [ ] T038 [US4] Implement `code/models/eval.py`: **Stress Test** logic to evaluate Distilled Model on a subset of tasks with ambiguous hints (if available) to measure distribution shift.
- [ ] T039 [US4] Implement `code/utils/metrics.py`: **Confounding Control** via difficulty matching to rule out confounders in the evaluation set.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Documentation: Update `README.md` with CLI usage examples and installation instructions.
- [ ] T040b [P] Documentation: Update `README.md` with pinned dependency list and version info.
- [ ] T040c [P] Documentation: Generate architecture diagram in `docs/` showing data flow from logs to model to eval.
- [ ] T041a [P] Code cleanup: Remove unused imports and variables across `code/`.
- [ ] T041b [P] Code cleanup: Enforce line length < 88 and formatting consistency (black).
- [ ] T041c [P] Code cleanup: Fix missing type hints in `code/utils/` and `code/models/`.
- [ ] T042 Performance optimization for data streaming and model inference
- [ ] T043 [P] Additional unit tests for edge cases (empty logs, emulator crashes) in `code/tests/unit/`
- [ ] T044 Run `quickstart.md` validation and update if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)**: Must complete before US2 (Training needs dataset) and US3 (Evaluation needs model)
 - **US2 (P2)**: Must complete before US3 and US4 (Evaluation needs model)
 - **US3 (P3)**: Can run in parallel with US4 once US2 is complete
 - **US4 (P3)**: Can run in parallel with US3 once US2 is complete
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 (Dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (Tasks) and US2 (Model)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 (Model) and specifically **T029** (Ablation Results from US3)

### Specific Artifact Dependencies

- **T032 (N Calculation)**: Must complete before T026 (Evaluation Load). T032 is in Phase 3; T026 is in Phase 5.
- **T029 (Ablation Run)**: Must complete before T037 (Ablation Report). T029 is in Phase 5; T037 is in Phase 6.
- **T005 (Emulator)**: Provides interface for T026/T027.
- **T016 (Data Extraction)**: Must complete before T032 (N Calculation).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
 - **US1** must run first (blocks US2)
 - Once **US1** completes, **US2** can start
 - Once **US2** completes, **US3** and **US4** can run in parallel
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
- **Architecture Note**: Tasks now mandate T5-small (Encoder-Decoder) per amended FR-002 (see Kickback T019c).
- **Statistical Note**: Tasks now mandate McNemar's test and A priori analysis per amended FR-005/FR-007 (see Kickback T019a, T019b).
- **Kickback Note**: Tasks T019a-d are Kickback requests. The spec.md MUST be updated externally to reflect these changes before the project is considered fully compliant.