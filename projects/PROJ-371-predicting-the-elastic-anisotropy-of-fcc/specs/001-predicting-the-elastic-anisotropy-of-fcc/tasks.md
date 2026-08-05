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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001-new [P] Create project directory structure: `mkdir -p src/{data,models,utils,cli} tests/{unit,integration} data/{raw,processed} output`
- [ ] T003-new [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml` and `.ruff.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002-new [P] **Implement LOEO Splitter Function**: Implement the core Leave-One-Element-Out (LOEO) *algorithm* (function logic) in `src/models/loeo_split.py`. This task creates the reusable function that accepts a list of element groups and returns train/test indices. **Note**: This task implements the *logic* only; it does NOT generate split artifacts. The execution of this logic to create artifacts is handled in T021. (Plan: Complexity Tracking, Constitution Principle VII Mitigation)
- [ ] T004-new [P] Create `src/utils/config.py` to manage paths (data/raw, data/processed, output), random seeds (fixed for reproducibility), constants, and **configurable sensitivity analysis thresholds** (default: [2.5, 3.0, 3.5] std devs).
- [ ] T005-new [P] Implement `src/utils/logging.py` for structured logging and error tracking
- [ ] T006-new [P] [US1] Add `tests/unit/test_config.py` to verify configuration loading and seed reproducibility (Depends on T004-new)
- [ ] T007-new [P] Setup `data/raw/` and `data/processed/` directory structures with `.gitkeep`
- [ ] T008-new [P] [US1] Add `tests/unit/test_logging.py` to verify log output formats (Depends on T005-new)
- [ ] T019-new [US1] Implement API key loading via `python-dotenv` in `src/utils/config.py`; add validation for `MP_API_KEY` presence; raise explicit error if missing. **Dependency**: Must run after T004-new (config.py creation). (FR-001, Constitution Principle I)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Fetch elastic constants from public databases and compute compositional descriptors automatically.

**Independent Test**: Can be fully tested by running the data pipeline script (`T015`) against a static subset of known FCC entries (via `--test-mode`) and verifying the output CSV contains the required columns (C11, C12, C44, A1, descriptors).

### Implementation for User Story 1

- [ ] T011-new [P] [US1] Create and populate `data/raw/manifest.json` with a curated list of known FCC material IDs (e.g., MP-123, AFLOW-456) to serve as the input source for the ingestion script. This task ensures T012a/b have a defined input artifact. (FR-001, SC-001, F001)
- [X] T012a [US1] Implement `src/data/ingest_mp.py` to fetch C11, C12, C44 from Materials Project API (endpoint: `/materials/v1/elasticity`) for IDs in `manifest.json`. **CRITICAL**: Do NOT implement fallback to synthetic/mock data. If API key missing or fetch fails, raise explicit error. [UNRESOLVED-CLAIM: c_b856c987 — status=not_enough_info] For `--test-mode`, load static fixtures from `data/raw/manifest.json` (real data subset), NOT synthetic mocks. (FR-001, Edge Case 1)
- [ ] T012b [US1] Implement `src/data/ingest_aflow.py` to fetch C11, C12, C44 from AFLOWlib API for IDs in `manifest.json`. **CRITICAL**: If API key missing or fetch fails,raise explicit error. For `--test-mode`, load static fixtures. (FR-001, Edge Case 1) <!-- FAILED: unspecified -->
- [ ] T012c [US1] Implement `src/data/validate_ingest.py` to merge MP/AFLOW results, {{claim:c_c00f8a07}} (2409.02789, https://arxiv.org/abs/2409.02789) (SC-001), and log skipped IDs. (FR-001, SC-001)
- [ ] T013 [US1] Implement `src/data/clean.py` to filter for single-phase FCC entries (check `structure['symmetry']['crystal_system'] == 'cubic'` for MP; check `tags['fss']` or equivalent cubic flag for AFLOW), exclude entries where C11=C12 (preventing division by zero in A1), and calculate A1 = 2*C44 / (C11-C12) (Edge Case 2, Edge Case 3)
- [ ] T014 [US1] Implement `src/data/features.py` to compute atomic radius variance, electronegativity standard deviation, and valence electron concentration using `mendeleev` or `pymatgen` (FR-002)
- [ ] T014b [US1] Implement `src/data/group_elements.py` to parse chemical formulas from the cleaned dataset and generate `data/processed/element_groups.json` (mapping element -> list of material IDs) required for LOEO cross-validation. **Dependency**: Must not start until T002-new is complete. (Dependency for T021)
- [ ] T015 [US1] Create `src/cli/run_pipeline.py` orchestration script to fetch, clean, and feature-engineer data, saving results to `data/processed/elastic_anisotropy.csv`. **Must support `--test-mode` flag**: if set, bypass live API calls (T012a/b) and load static fixtures from `data/raw/manifest.json` to enable offline testing. **Verification**: Verify output CSV exists at `data/processed/elastic_anisotropy.csv` with >0 rows. (FR-001, US-1 Acceptance 2, executability-41ed0ce7)
- [ ] T016 [US1] Add validation in `src/cli/run_pipeline.py` to ensure output CSV has no null values in descriptor columns (US-1 Acceptance 2)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train regression models on the ingested data and evaluate performance using CPU-only resources.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed dataset and verifying the output JSON contains R², MAE, and RMSE metrics for each model type.

**⚠️ Dependency**: This phase depends on the completion of T011-new (Manifest), T014b (Element Grouping), and T015 (Data Pipeline). **Crucially**, it depends on T002-new (LOEO Logic) for the splitter function and T021 (LOEO Execution) for the split artifacts.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Add `tests/unit/test_train.py::test_loeo_split_no_element_overlap` to verify the LOEO split logic ensures no element overlap between train and test sets
- [ ] T040 [P] [US2] Add `tests/unit/test_evaluate.py::test_metrics_calculation_matches_scikit_learn` to verify R², MAE, and RMSE calculations match scikit-learn standards. **Also verify**: This task must check if R² >= 0.5 and log the result as 'benchmark_status' in `output/metrics.json` to satisfy SC-004. (SC-004, US-2 Acceptance 2)

### Implementation for User Story 2

- [ ] T021 [US2] **Execute LOEO Splitting**: Import the LOEO splitter function implemented in T002-new (`src/models/loeo_split.py`). Execute this function using `data/processed/element_groups.json` (from T014b) as input to generate train/test indices. Save the resulting split indices to `data/processed/loeo_splits.json`. **Dependency**: Must run after T002-new (logic) and T014b (groups). **Verification**: Verify `data/processed/loeo_splits.json` exists and contains valid indices. (Plan: Constitution Principle VII Mitigation, executability-6a227e3d)
- [ ] T020 [US2] Implement `src/models/train.py` to train Random Forest, Gradient Boosting, and Linear Regression models using CPU-only resources (no GPU/CUDA). **Dependency**: Must consume `data/processed/loeo_splits.json` from T021. **Logic**: Load pre-computed splits; do NOT re-calculate splits. **Verification**: Ensure no CUDA imports; log hyperparameters. (FR-003, Constitution Principle VII Mitigation, coverage-e7c20276)
- [ ] T022 [US2] Implement `src/models/evaluate.py` to compute R², MAE, and RMSE on the held-out test set, **save residuals and outlier-flagged dataset** to `data/processed/residuals_and_flags.json`, and save metrics to `output/metrics.json`. **Verification**: Verify `data/processed/residuals_and_flags.json` exists and contains data. (US-2 Acceptance 2, Dependency for T027, executability-6a227e3d)
- [ ] T037 [US2] Implement timing instrumentation in `src/cli/run_pipeline.py` to measure total runtime and **log the result to `output/timing.json`**. If runtime > 1 hour, log a **warning** (do not crash/assert) and flag the run as 'timeout_warning'. This task verifies US-2 Acceptance 1. (coverage-b92b8fbe, coverage-d3940482, constraint_preservation-f8033372)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Physical Consistency and Reporting (Priority: P3)

**Goal**: Verify predictions adhere to physical bounds, perform sensitivity analysis, and generate reports.

**Independent Test**: Can be tested by running the validation script on the model predictions and verifying the report flags any values outside the theoretical range (0 < A₁ < 3) and includes the sensitivity analysis.

**⚠️ Dependency**: This phase depends on the completion of T022 (Metrics & Residuals). **Ordering Note**: T028 (Physical Check) must precede T027 (Sensitivity) to ensure physical consistency is checked before sensitivity sweeps on the data.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Add `tests/unit/test_evaluate.py::test_physical_bounds_flags_out_of_range` to verify the consistency check flags predictions outside 0 < A₁ < 3
- [ ] T026 [P] [US3] Add `tests/unit/test_sensitivity.py::test_sensitivity_sweep_variance_calculation` to verify the variance calculation across the sweep and the threshold check (<= 0.1)

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/models/evaluate.py` physical consistency check to flag predictions where A1 <= 0 or A1 >= 3 (SC-003, US-3 Acceptance 1). **Output**: Update `data/processed/residuals_and_flags.json` with physical violation flags.
- [ ] T028b [US3] Implement logic in `src/models/evaluate.py` to **calculate the aggregate violation rate percentage** and compare it against a predefined significance threshold defined in SC-003; log a warning if rate > 5% (SC-003, coverage-a9a2778d)
- [ ] T027 [US3] Implement `src/models/sensitivity.py` to sweep outlier removal thresholds over a **configurable range of standard deviation values** (loaded from `src/utils/config.py`, default: [2.5, 3.0, 3.5]). Calculate the variance of R² across these sweeps using the residuals from T022, **save the variance value to `output/sensitivity.json` and `output/metrics.json`**, and log a warning if variance > 0.1 (US-3 Acceptance 2, FR-005, coverage-f3d78a40, coverage-6955ef8c, coverage-4e26fac5)
- [ ] T029 [US3] Generate `output/validation_report.md` including feature importance, sensitivity analysis results (variance <= 0.1 check), explicit **associational framing** (FR-004: "findings reflect correlations, not causal mechanisms"), and the violation rate percentage from T028b. **Verification**: Ensure report contains the exact phrase "associational, not causal". (FR-004, US-3 Acceptance 2, coverage-e01bcda2)
- [ ] T030 [US3] Implement Verification Gate logic in `src/cli/run_pipeline.py` to ensure all citations in the report are resolvable and metrics match `output/metrics.json` (Constitution Principle II)
- [ ] T041 [US2] Implement logic in `output/metrics.json` generation (or `src/models/evaluate.py`) to explicitly check if R² >= 0.5 and log a boolean `benchmark_met` and a string `benchmark_status` (e.g., "Met", "Not Met") to satisfy SC-004. (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Update `README.md` (installation, CLI usage) and create `docs/quickstart.md`
- [ ] T033 [P] Run `ruff check` and `black --check`; fix any violations found in `src/` and `tests/`
- [ ] T035a [P] Add `tests/unit/test_ingest.py::test_ingest_handles_missing_C11` to verify skipping and logging (Edge Case 1)
- [ ] T035b [P] Add `tests/unit/test_clean.py::test_clean_excludes_C11_equals_C12` to verify division-by-zero handling (Edge Case 2)
- [ ] T036 [P] Execute `python -m src.cli.run_pipeline --validate` and verify exit code 0

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015), Element Grouping (T014b), **Manifest (T011-new)**, **LOEO Logic (T002-new)**, and **LOEO Execution (T021)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (T022, T028)

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