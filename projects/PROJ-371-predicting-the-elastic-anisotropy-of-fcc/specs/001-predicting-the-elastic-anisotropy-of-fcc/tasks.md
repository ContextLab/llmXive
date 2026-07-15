# Tasks: Predicting the Elastic Anisotropy of FCC Metals from Composition

**Input**: Design documents from `/specs/001-elastic-anisotropy/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001 Create project structure per implementation plan: `mkdir -p src/{data,models,utils,cli} tests/{unit,integration} data/{raw,processed} output` <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T002 Create `pyproject.toml` with dependencies: `pandas, scikit-learn, mendeleev, requests, pyyaml, matplotlib, python-dotenv, ruff, black, pytest`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Create `src/utils/config.py` to manage paths (data/raw, data/processed, output), random seeds (42), and constants
- [ ] T005 [P] Implement `src/utils/logging.py` for structured logging and error tracking
- [ ] T006 Create `tests/unit/test_config.py` to verify configuration loading and seed reproducibility
- [~] T007 Setup `data/raw/` and `data/processed/` directory structures with `.gitkeep`
- [X] T008 Create `tests/unit/test_logging.py` to verify log output formats

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Fetch elastic constants from public databases and compute compositional descriptors automatically.

**Independent Test**: Can be fully tested by running the data pipeline script against a static subset of known FCC entries and verifying the output CSV contains the required columns (C11, C12, C44, A1, descriptors).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Add `tests/unit/test_features.py::test_descriptor_variance_handles_empty_input` to verify descriptor calculation handles empty input without crashing
- [X] T010 [P] [US1] Add `tests/unit/test_ingest.py::test_ingest_handles_missing_C11` to verify the ingest script skips entries with missing C11 and logs the ID
- [~] T011 [P] [US1] Add `tests/integration/test_pipeline.py::test_pipeline_end_to_end_static` using a static manifest `data/raw/manifest_subset.json` containing a list of known FCC material IDs (e.g., MP-123, AFLOW-456) to verify the full pipeline runs on a known subset

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/data/ingest.py` to fetch C11, C12, C44 from Materials Project and AFLOWlib APIs for a curated list of FCC IDs; validate `MP_API_KEY` environment variable; handle missing values by skipping and logging ID; verify ≥50 unique entries (SC-001) (FR-001, Edge Case 1)
- [ ] T013 [US1] Implement `src/data/clean.py` to filter for single-phase FCC entries, exclude entries where C11=C12 (preventing division by zero in A1), and calculate A1 = 2*C44 / (C11-C12) (Edge Case 2, Edge Case 3)
- [ ] T014 [US1] Implement `src/data/features.py` to compute atomic radius variance, electronegativity standard deviation, and valence electron concentration using `mendeleev` or `pymatgen` (FR-002)
- [ ] T015 [US1] Create `src/cli/run_pipeline.py` orchestration script to fetch, clean, and feature-engineer data, saving results to `data/processed/elastic_anisotropy.csv`
- [ ] T016 [US1] Add validation in `src/cli/run_pipeline.py` to ensure output CSV has no null values in descriptor columns (US-1 Acceptance 2)
- [~] T017 [US1] Verify pipeline execution on free-tier CI constraints (CPU only, <7GB RAM) by running with a sample subset of entries

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train regression models on the ingested data and evaluate performance using CPU-only resources.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed dataset and verifying the output JSON contains R², MAE, and RMSE metrics for each model type.

**⚠️ Dependency**: This phase depends on the completion of T015 (Data Pipeline) which produces the cleaned dataset required for LOEO splitting.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Add `tests/unit/test_train.py::test_loeo_split_no_element_overlap` to verify the LOEO split logic ensures no element overlap between train and test sets
- [ ] T019 [P] [US2] Add `tests/unit/test_evaluate.py::test_metrics_calculation_matches_scikit_learn` to verify R², MAE, and RMSE calculations match scikit-learn standards

### Implementation for User Story 2

- [ ] T020 [US2] Implement `src/models/train.py` to train Random Forest, Gradient Boosting, and Linear Regression models using CPU-only resources (no GPU/CUDA) with Leave-One-Element-Out (LOEO) cross-validation. **Note**: This deviates from Spec's "random 80/20 split" assumption; justification: Plan.md "Complexity Tracking" and Constitution Principle VII mitigation to prevent chemical similarity leakage. Requires data pre-grouped by element (produced by T014) (FR-003, Constitution Principle VII Mitigation, US-2 Acceptance 1)
- [ ] T021 [US2] Implement LOEO cross-validation logic in `src/models/train.py` to mitigate chemical similarity leakage; document trade-off between LOEO and Spec's random split assumption (Plan: Constitution Principle VII Mitigation)
- [ ] T022 [US2] Implement `src/models/evaluate.py` to compute R², MAE, and RMSE on the held-out test set and save results to `output/metrics.json` (US-2 Acceptance 2)
- [ ] T023 [US2] Ensure training completes within 1 hour on standard CPU environment (US-2 Acceptance 1)
- [ ] T024 [US2] Log model hyperparameters and performance metrics to `output/metrics.json` for traceability (Constitution Principle IV)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Physical Consistency and Reporting (Priority: P3)

**Goal**: Verify predictions adhere to physical bounds, perform sensitivity analysis, and generate reports.

**Independent Test**: Can be tested by running the validation script on model predictions and verifying the report flags any values outside the theoretical range (0 < A₁ < 3) and includes the sensitivity analysis.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Add `tests/unit/test_evaluate.py::test_physical_bounds_flags_out_of_range` to verify the consistency check flags predictions outside 0 < A₁ < 3
- [ ] T026 [P] [US3] Add `tests/unit/test_sensitivity.py::test_sensitivity_sweep_variance_calculation` to verify the variance calculation across the sweep {2.5, 3.0, 3.5} and the threshold check (<= 0.1)

### Implementation for User Story 3

- [ ] T027 [US3] Implement `src/models/sensitivity.py` to sweep outlier removal thresholds over a range of standard deviations (FR-005), calculate the variance of R² across these three sweeps, and log a warning if variance > 0.1 (US-3 Acceptance 2, Merged T031 logic)
- [ ] T028 [US3] Implement `src/models/evaluate.py` physical consistency check to flag predictions where A1 <= 0 or A1 >= 3 (SC-003, US-3 Acceptance 1)
- [ ] T029 [US3] Generate `output/validation_report.md` including feature importance, sensitivity analysis results (variance <= 0.1 check), and explicit associational framing (FR-004, US-3 Acceptance 2)
- [ ] T030 [US3] Implement Verification Gate logic in `src/cli/run_pipeline.py` to ensure all citations in the report are resolvable and metrics match `output/metrics.json` (Constitution Principle II)
- [ ] T031 [US3] **REMOVED**: Logic merged into T027.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Update `README.md` (installation, CLI usage) and create `docs/quickstart.md`
- [ ] T033 Run `ruff check` and `black --check`; fix any violations found in `src/` and `tests/`
- [ ] T034 Implement API key loading via `python-dotenv` in `src/utils/config.py`; add validation for `MP_API_KEY` presence (Replaces removed timing task)
- [ ] T035 [P] If tests requested: Add missing coverage for edge cases in `tests/unit/`; otherwise, skip
- [ ] T036 Execute `python -m src.cli.run_pipeline --validate` and verify exit code 0
- [ ] T037 Verify full pipeline runtime < 1 hour on CPU-only CI; log timing breakdown in `output/timing.json` (Optional manual check, not automated artifact)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Add tests/unit/test_features.py::test_descriptor_variance_handles_empty_input"
Task: "Add tests/unit/test_ingest.py::test_ingest_handles_missing_C11"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingest.py to fetch C11, C12, C44..."
Task: "Implement src/data/features.py to compute atomic radius variance..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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