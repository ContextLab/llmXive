# Tasks: Uncovering Correlations Between Processing Conditions and Texture in Rolled Metals

**Input**: Design documents from `/specs/001-uncovering-correlations/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `docs/`)
- [ ] T002 Initialize Python 3.11 project with dependencies (`scikit-learn`, `pandas`, `numpy`, `pymtex`, `pyyaml`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` for hyperparameters, paths, and random seeds
- [X] T005 [P] Implement `code/utils/logging.py` for `pipeline.log` and structured warnings (FR-007, FR-012)
- [ ] T006 [P] Create `code/data/` directory structure (`raw/`, `processed/`)
- [~] T007 [P] Define data schemas in `docs/contracts/` (`dataset.schema.yaml`, `input.schema.yaml`, etc.)
- [X] T008 Implement `code/utils/texture.py` wrapper for `pymtex` to compute ODF intensities ({100}, {110}, {111}) in MRD (FR-003)
- [X] T009 Implement `code/data/synthetic.py` physics-based generator ensuring ≥50 samples/alloy family with known ground truth (FR-001, FR-011)
- [X] T009a Implement `code/data/synthetic.py` configuration to generate at least 3 distinct alloy families with ≥50 samples each and output `ground_truth.json` validating family counts (FR-009) <!-- SKIPPED: YAML+regex parse failed (while scanning for the next token
found character '`' that cannot start any token
 in "<unicode string>", line 3, column 17:
 - Public names: `generate_synthetic_dataset`, `v...
 ^) -->
- [ ] T010 Implement `code/data/loader.py` to attempt real data ingestion (Materials Project/OMDB/NIST) and fallback to synthetic (FR-001, FR-008); **MUST validate that the combined dataset (Real + Synthetic) contains at least 3 distinct alloy families** before training proceeds.
- [X] T011a Implement `code/data/processor.py` for unit standardization, median imputation (≤20% NaN), 3σ outlier removal, and derivation of physics-based features (strain rate, Zener-Hollomon) per spec formulas (FR-002); **depends on T008** (Texture Utils) for ODF-based feature derivation if applicable.
- [X] T011b Create unit tests `tests/test_preprocessing.py` to validate mathematical correctness of derived features (strain rate, Zener-Hollomon) against spec definitions **explicitly listing the mathematical formulas as docstrings in test_preprocessing.py** before model ingestion (FR-002)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑End Data‑Driven Texture Prediction (Priority: P1) 🎯 MVP

**Goal**: Ingest data, train a multi-output RandomForest model, and generate predictions for test and new samples.

**Independent Test**: Execute the full pipeline on a curated subset (≥200 samples) and verify `predictions.csv` and model file are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: The spec requires an independent test execution. We will create integration tests to verify the pipeline runs end-to-end.

- [X] T012 [P] [US1] Create integration test `tests/test_pipeline.py` to run full pipeline on synthetic data and verify artifact existence

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/models/trainer.py` for multi-output RandomForestRegressor training with 5-fold CV grid search (≤30 mins) (FR-004)
- [ ] T014 [US1] Implement `code/models/predictor.py` for inference logic handling out-of-range warnings (Edge Case)
- [ ] T015 [US1] Implement `code/main.py` entry point to orchestrate: Load -> Preprocess -> Train -> Predict -> Save (FR-001, FR-004, FR-005)
- [ ] T016 [US1] Add validation logic in `main.py` to abort if <50 samples/alloy family (FR-008)
- [ ] T017 [US1] Implement logic to save `predictions.csv` and `new_predictions.csv` (FR-005)
- [ ] T018 [US1] Implement logic to save `pipeline.log` with all warnings and hyper-params (FR-007)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Evaluation & Feature‑Importance Reporting (Priority: P2)

**Goal**: Assess model performance (R², MAE, RMSE) per alloy family and generate feature importance visualizations.

**Independent Test**: Run evaluation on held-out test split and verify `evaluation_report.json` and `importance_plot.png`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Create unit test `tests/test_evaluation.py` to verify metric calculations and threshold checks (FR-010)

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/models/evaluator.py` to compute R², MAE, RMSE per texture coefficient and per alloy family (FR-009, FR-010)
- [ ] T021 Implement permutation importance calculation and ranking logic (FR-005)
- [ ] T021a [US2] Implement validation logic in `code/models/evaluator.py` to check SC-002 (at least one variable importance ≥0.10 for EVERY AlloyFamily); **log failure and record metrics in the evaluation report if failed, do NOT halt the pipeline**; proceed to sensitivity analysis (FR-010, SC-002)
- [ ] T022 [US2] Implement `importance_plot.png` generation (≤5 MB) with ranked feature list (FR-005)
- [ ] T023 [US2] Implement `sensitivity_analysis.py` to sweep R² and importance thresholds from **0.01 to 0.50 in steps of 0.01** to report stability across low to moderate magnitudes (FR-010)
- [ ] T024 [US2] Generate `evaluation_report.json` including `data_source_type` (Real/Synthetic); **logic: Set data_source_type to "Synthetic" if the synthetic generator was invoked or if real data count < threshold, else "Real"**; include per-family metrics and missing confounds warning (SC-004, FR-012)
- [ ] T025 [US2] Generate `sensitivity_report.json` with threshold sweep results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproducible Containerized Execution (Priority: P3)

**Goal**: Containerize workflow and provide GitHub Actions CI workflow.

**Independent Test**: Trigger CI job; verify it completes in ≤6h with ≤2 CPU/6GB RAM and produces identical artifacts.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Create `tests/test_ci.py` (mock) to validate resource constraints in local environment; **MUST be conditional on `ENABLE_DOCKER` flag and skipped if false** (optional)

### Implementation for User Story 3

- [ ] T027 [P] [US3] Create `Dockerfile` based on `python:3.11-slim` with all dependencies; implement conditional check for `ENABLE_DOCKER` config flag to skip build if false (FR-006)
- [ ] T028 [US3] Create `.github/workflows/ci.yml` to build image (if `ENABLE_DOCKER=true`), run pipeline, and verify exit code 0; skip containerization step if flag is false (FR-006)
- [ ] T029 [US3] Add error handling in CI workflow to log missing resources clearly; ensure workflow respects `ENABLE_DOCKER` flag (Edge Case)
- [ ] T030 [US3] Document local run instructions in `docs/quickstart.md` including `ENABLE_DOCKER` configuration

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` (research.md, data-model.md)
- [ ] T032 Code cleanup and refactoring for readability
- [ ] T033 [P] Implement timeout mechanism and early-stopping logic in `code/models/trainer.py` to programmatically enforce a wall-clock limit for grid search (FR-004)
- [ ] T034 [P] Additional unit tests in `tests/unit/` for data loaders and synthetic generator
- [ ] T035 Run `quickstart.md` validation to ensure all steps work in sequence

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - *Specific Dependency*: T009a (Synthetic Config for ≥3 families) and T010 (Loader) must be complete before T013 (Trainer) can run.
 - *Specific Dependency*: T008 (Texture Utils) must be complete before T011a (Processor) can derive features if needed.
 - *Specific Dependency*: T011b (Validation Tests) must pass before T013 (Trainer) consumes derived features.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires trained model from US1 to evaluate
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires complete pipeline from US1/US2 to containerize

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before Services/Trainers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006, T007, T008) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Synthetic data run)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Core Pipeline)
 - Developer B: User Story 2 (Evaluation & Reporting)
 - Developer C: User Story 3 (CI/CD & Docker)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must be executable on CPU-only CI with constrained memory resources. No GPU/8-bit quantization tasks.
- **Data Integrity**: Synthetic data generator (T009/T009a) must produce `ground_truth.json` for validation; real data loader (T010) must strictly abort if <50 samples found and **must validate ≥3 distinct families in the combined dataset**.
- **Physics Validation**: T011b must pass before T013 consumes derived features.
- **Threshold Enforcement**: T021a must log failure and record metrics if SC-002 is not met; **do not halt**.
- **Optional Features**: T026-T029 respect `ENABLE_DOCKER` flag.
- **Time Constraints**: T033 enforces 30-min limit programmatically.