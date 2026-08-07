# Tasks: Predicting the Elastic Anisotropy of FCC Metals from Composition

**Input**: Design documents from `/specs/001-elastic-anisotropy/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Dependency (Must run after previous task)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Spec Alignment (Critical)

**Purpose**: Resolve contradictions between Spec and Plan/Constitution before implementation begins.

- [ ] T000-new [D] **Update Spec Assumptions**: Update `specs/001-elastic-anisotropy/spec.md` Assumptions section to explicitly state that while random splits are generally preferred for interpolation, **Constitution Principle VII (Chemical Similarity Leakage)** mandates the use of **Leave-One-Element-Out (LOEO)** splitting for this project. This task amends the spec to justify the deviation in the Plan and Tasks. (Constraint Preservation: F001, constraint_preservation-d13dd4df)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a-new [P] Create source directory: `mkdir -p src/{data,models,utils,cli}`
- [ ] T001b-new [P] Create test directory: `mkdir -p tests/{unit,integration}`
- [ ] T001c-new [P] Create data directory: `mkdir -p data/{raw,processed}` and `output`
- [ ] T003-new [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml` and `.ruff.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002-new [P] **Implement LOEO Splitter Function**: Implement the core Leave-One-Element-Out (LOEO) *algorithm* (function logic) in `src/models/loeo_split.py`. This task creates the reusable function that accepts a list of element groups and returns train/test indices. **Note**: This task implements the *logic* only; it does NOT generate split artifacts. The execution of this logic to create artifacts is handled in T021. (Plan: Complexity Tracking, Constitution Principle VII Mitigation)
- [ ] T004-new [P] Create `src/utils/config.py` to manage paths (data/raw, data/processed, output), random seeds (fixed for reproducibility), constants, and **configurable sensitivity analysis thresholds** (default: [, 3.0, 3.5] std devs).
- [ ] T005-new [P] Implement `src/utils/logging.py` for structured logging and error tracking
- [ ] T019-new [D] [US1] **Implement API Key Loading**: Implement API key loading via `python-dotenv` in `src/utils/config.py`; add validation for `MP_API_KEY` presence; raise explicit error if missing. **Dependency**: Must run after T004-new (config.py creation). (FR-001, Constitution Principle I)
- [ ] T006-new [D] [US1] **Add Config Tests**: Add `tests/unit/test_config.py` to verify configuration loading and seed reproducibility. **Dependency**: Must run after T019-new to ensure API key logic is present. (FR-001, Constitution Principle I)
- [ ] T007-new [P] Setup `data/raw/` and `data/processed/` directory structures with `.gitkeep`
- [ ] T008-new [P] [US1] Add `tests/unit/test_logging.py` to verify log output formats (Depends on T005-new)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Fetch elastic constants from public databases and compute compositional descriptors automatically.

**Independent Test**: Can be fully tested by running the data pipeline script (`T015`) against a static subset of known FCC entries (via `--test-mode`). **Requirement**: All Phase 2 (Foundational) tasks MUST be complete before this test can be executed.

### Implementation for User Story 1

- [ ] T011-new [P] [US1] **Create Data Manifest**: Create and populate `data/raw/manifest.json` with a curated list of known FCC material IDs (e.g., MP-123, AFLOW-456). **Also Create**: `data/raw/fixtures/mp_test_data.json` and `data/raw/fixtures/aflow_test_data.json` containing static elastic constant data for these IDs to support offline testing. (FR-001, SC-001, F001)
- [ ] T012a-new [D] [US1] **Implement MP Ingestion**: Implement `src/data/ingest_mp.py` to fetch C11, C12, C44 from Materials Project API for IDs in `manifest.json`. **CRITICAL**: Do NOT implement fallback to synthetic/mock data. If API key missing or fetch fails, raise explicit error. For `--test-mode`, load static fixtures from `data/raw/fixtures/mp_test_data.json`. (FR-001, Edge Case 1)
- [ ] T012b-new [D] [US1] **Implement AFLOW Ingestion**: Implement `src/data/ingest_aflow.py` to fetch C11, C12, C44 from AFLOWlib API for IDs in `manifest.json`. **CRITICAL**: If API key missing or fetch fails, raise explicit error. For `--test-mode`, load static fixtures from `data/raw/fixtures/aflow_test_data.json`. (FR-001, Edge Case 1)
- [ ] T012c-new [D] [US1] **Implement Data Validation**: Implement `src/data/validate_ingest.py` to merge MP/AFLOW results, validate data integrity (missing C11, C12, C44), and log skipped IDs. **Note**: Citation verification is handled by T030 (Verification Gate); this task focuses on data structure integrity. (FR-001, SC-001)
- [ ] T013-new [D] [US1] **Implement Cleaning**: Implement `src/data/clean.py` to filter for single-phase FCC entries (check `structure['symmetry']['crystal_system'] == 'cubic'` for MP; check `tags['fss']` or equivalent cubic flag for AFLOW), exclude entries where C11=C12 (preventing division by zero in A1), and calculate A1 = 2*C44 / (C11-C12) (Edge Case 2, Edge Case 3)
- [ ] T014-new [D] [US1] **Implement Feature Engineering**: Implement `src/data/features.py` to compute atomic radius variance, electronegativity standard deviation, and valence electron concentration using `mendeleev` or `pymatgen` (FR-002)
- [ ] T015-new [D] [US1] **Create Orchestration Pipeline**: Create `src/cli/run_pipeline.py` orchestration script to fetch, clean, and feature-engineer data, saving results to `data/processed/elastic_anisotropy.csv`. **Must support `--test-mode` flag**: if set, bypass live API calls (T012a/b) and load static fixtures from `data/raw/fixtures/`. **Verification**: Verify output CSV exists at `data/processed/elastic_anisotropy.csv` with >0 rows AND contains required descriptor columns (atomic radius variance, electronegativity std dev, VEC) with no null values. (FR-001, US-1 Acceptance 2, executability-41ed0ce7)
- [ ] T016-new [D] [US1] **Add Descriptor Validation**: Add validation in `src/cli/run_pipeline.py` (or separate script) to ensure output CSV has no null values in descriptor columns (US-1 Acceptance 2). **Note**: T015 now includes the primary check; this task ensures robustness.
- [ ] T014b-new [D] [US1] **Generate Element Groups**: Implement `src/data/group_elements.py` to parse chemical formulas from the cleaned dataset (output artifact: `data/processed/elastic_anisotropy.csv` from T015) and generate `data/processed/element_groups.json` (mapping element -> list of material IDs) required for LOEO cross-validation. **Note**: This task parses the *output artifact* of T015. **Dependency**: Must run after T015 completes to ensure `elastic_anisotropy.csv` exists. (Dependency for T021)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. T014b produces the element groups needed for Phase 4.

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train regression models on the ingested data and evaluate performance using CPU-only resources.

**Independent Test**: Can be fully tested by executing the training script on the preprocessed dataset and verifying the output JSON contains R², MAE, and RMSE metrics for each model type.

**⚠️ Dependency**: This phase depends on the completion of T011-new (Manifest), **T015-new (Data Pipeline)**, **T014b-new (Element Groups)**, T002-new (LOEO Logic), and T021-new (LOEO Execution). **Crucially**, it depends on T002-new (LOEO Logic) for the splitter function.

### Implementation for User Story 2

- [ ] T021-new [D] [US2] **Execute LOEO Splitting**: Import the LOEO splitter function implemented in T002-new (`src/models/loeo_split.py`). Execute this function using `data/processed/element_groups.json` (from T014b-new) as input to generate train/test indices. **Execution Order**: T002 (Logic) must be complete before T021 starts; T015 (Data) and T014b (Groups) must be complete before T021 starts. Save the resulting split indices to `data/processed/loeo_splits.json`. **Verification**: Verify `data/processed/loeo_splits.json` exists and contains valid indices. **Authority**: This task implements Constitution Principle VII (Chemical Similarity Leakage Prevention) by enforcing LOEO, overriding the Spec's random split assumption (per T000). (Plan: Constitution Principle VII Mitigation, executability-6a227e3d)
- [ ] T020-new [D] [US2] **Implement Model Training**: Implement `src/models/train.py` to train Random Forest, Gradient Boosting, and Linear Regression models using CPU-only resources (no GPU/CUDA). **Dependency**: Must consume `data/processed/loeo_splits.json` from T021-new. **Logic**: Load pre-computed splits; do NOT re-calculate splits. **Verification**: Ensure no CUDA imports; log hyperparameters. **Authority**: This task implements Constitution Principle VII (Chemical Similarity Leakage Prevention) by using LOEO splits. (FR-003, Constitution Principle VII Mitigation, coverage-e7c20276)
- [ ] T022-new [D] [US2] **Implement Evaluation & Benchmarks**: Implement `src/models/evaluate.py` to compute R², MAE, and RMSE on the held-out test set, **save residuals and outlier-flagged dataset** to `data/processed/residuals_and_flags.json`, and save metrics to `output/metrics.json`. **CRITICAL**: Explicitly check if the best performing model (highest R²) has R² >= 0.5 and log a boolean `benchmark_met` and a string `benchmark_status` (e.g., "Met", "Not Met") to `output/metrics.json` to satisfy SC-004. (US-2 Acceptance 2, Dependency for T027, executability-6a227e3d, SC-004, coverage-8d8544e8, coverage-cafe35d6, coverage-55229aae)
- [ ] T037-new [D] [US2] **Implement Timing Instrumentation**: Implement timing instrumentation in `src/cli/run_pipeline.py` to measure total runtime and **log the result to `output/timing.json`**. If runtime > 1 hour, **raise a RuntimeError** to enforce the hard constraint of US-2 Acceptance 1. Flag the run as 'timeout_error'. This task verifies US-2 Acceptance 1. (coverage-b92b8fbe, coverage-d3940482, constraint_preservation-f8033372)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Physical Consistency and Reporting (Priority: P3)

**Goal**: Verify predictions adhere to physical bounds, perform sensitivity analysis, and generate reports.

**Independent Test**: Can be tested by running the validation script on the model predictions and verifying the report flags any values outside the theoretical range (0 < A₁ < 3) and includes the sensitivity analysis.

**⚠️ Dependency**: This phase depends on the completion of T022-new (Metrics & Residuals). **Ordering Note**: T028-new (Physical Check) must precede T027-new (Sensitivity) to ensure physical consistency is checked before sensitivity sweeps on the data.

### Implementation for User Story 3

- [ ] T028-new [D] [US3] **Implement Physical Consistency Check**: Implement `src/models/evaluate.py` physical consistency check to flag predictions where A1 <= 0 or A1 >= 3 (SC-003, US-3 Acceptance 1). **Output**: Update `data/processed/residuals_and_flags.json` with physical violation flags.
- [ ] T028b-new [D] [US3] **Calculate Violation Rate & Flag**: Implement logic in `src/models/evaluate.py` to **calculate the aggregate violation rate percentage** using the formula: `(count of A1 violations / total count of predictions) * 100`. Compare this rate against the 5% threshold defined in SC-003; log a warning if rate > 5%. **CRITICAL**: Append the `violation_rate` (float) and `warning_flag` (boolean) to `output/metrics.json` to ensure the evidence is preserved for SC-003. (SC-003, FR-005, coverage-1cb53f19, coverage-7dbb9688)
- [ ] T027-new [D] [US3] **Implement Sensitivity Analysis**: Implement `src/models/sensitivity.py` to sweep outlier removal thresholds over a **configurable range of standard deviation values** (loaded from `src/utils/config.py`, default: [2.5, 3.0, 3.5]). **Mandatory**: **Re-train** the model for *each* threshold to generate a distinct R² value (to ensure robustness against data subset changes), then calculate the variance of these R² values. Save the variance value to `output/sensitivity.json` and `output/metrics.json`, and log a warning if variance > 0.1 (US-3 Acceptance 2, FR-005, coverage-f3d78a40, coverage-6955ef8c, coverage-4e26fac5, constraint_preservation-ccc90e30)
- [ ] T029-new [D] [US3] **Generate Validation Report**: Generate `output/validation_report.md` including feature importance, sensitivity analysis results (variance <= 0.1 check), explicit **associational framing** (FR-004: "findings reflect correlations, not causal mechanisms"), and the violation rate percentage from T028b-new. **CRITICAL**: Read the `warning_flag` from `output/metrics.json` and explicitly include its status (e.g., "WARNING: Violation rate exceeds 5%") in the report text to satisfy SC-003 evidence requirements. (FR-004, US-3 Acceptance 2, coverage-e01bcda2, coverage-1cb53f19, coverage-7dbb9688)
- [ ] T030-new [D] [US3] **Implement Verification Gate**: Implement Verification Gate logic in `src/cli/run_pipeline.py` to ensure all citations in the report are resolvable and metrics match `output/metrics.json` (Constitution Principle II)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032-new [P] Update `README.md` (installation, CLI usage) and create `docs/quickstart.md`
- [ ] T033-new [P] Run `ruff check` and `black --check`; fix any violations found in `src/` and `tests/`
- [ ] T035a-new [P] Add `tests/unit/test_ingest.py::test_ingest_handles_missing_C11` to verify skipping and logging (Edge Case 1)
- [ ] T035b-new [P] Add `tests/unit/test_clean.py::test_clean_excludes_C11_equals_C12` to verify division-by-zero handling (Edge Case 2)
- [ ] T036-new [P] Execute `python -m src.cli.run_pipeline --validate` and verify exit code 0

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015), Element Grouping (T014b), **Manifest (T011)**, **LOEO Logic (T002)**, and **LOEO Execution (T021)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (T022, T028)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2, except T006 which depends on T019)
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

1. Complete Phase 0: Spec Alignment (T000)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
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
- [D] tasks = Dependency (Must run after previous task)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence