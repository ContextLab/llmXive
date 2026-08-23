# Tasks: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

**Input**: Design documents from `/specs/001-predicting-cold-rolling-texture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can be developed in parallel (different files, no logical dependency)
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

- [ ] T001a [P] Create `code/` directory. **Verify**: Ensure directory exists via `os.path.isdir('code')`.
- [ ] T001b [P] Create `data/` directory. **Verify**: Ensure directory exists via `os.path.isdir('data')`.
- [ ] T001c [P] Create `tests/` directory. **Verify**: Ensure directory exists via `os.path.isdir('tests')`.
- [ ] T001d [P] Create `docs/` directory. **Verify**: Ensure directory exists via `os.path.isdir('docs')`.
- [ ] T002 [P] Create `.gitignore` for Python, data, and IDE files.
- [ ] T003 [P] Initialize Python project with `requirements.txt` (pinning `orix`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `requests`, `pytest` with explicit version specifiers, e.g., `>=1.0.0`, to ensure reproducibility per Constitution Principle I). **Verify**: Ensure file exists and contains pinned versions.
- [ ] T004 [P] Configure linting (flake8/black) and formatting tools. **Verify**: Ensure config files (e.g., `.flake8`, `pyproject.toml` for black) exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create subdirectories `raw`, `processed`, `interim` within the existing `data/` folder with `.gitkeep` (Required by Plan.md Project Structure and FR-001 Data Hygiene). **Verify**: Ensure all subdirectories and `.gitkeep` files exist.
- [ ] T006 [P] Implement base configuration loader for environment variables and seed management (`code/__init__.py`).
- [ ] T007 [P] Setup logging infrastructure to track data lineage and processing steps (`code/utils/logging.py`).
- [ ] T008a [P] Implement Pydantic model for 'EBSD Sample' (`code/data/models.py`).
- [ ] T008b [P] Implement Pydantic model for 'Texture Descriptor' (`code/data/models.py`).
- [ ] T009 [P] Implement unit tests for base schema validation in `tests/unit/test_models.py`. **Logic**: 
 1. `test_EBSDSample_rejects_confidence_0.0`: Verify that an EBSD Sample with confidence index < 0.1 raises ValueError.
 2. `test_TextureDescriptor_mass_balance_check`: Verify that the sum of Brass, Copper, S, Goss, and random components equals 1.0 ± 0.01; raise ValueError if the sum is outside this tolerance.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel
**Dependency Note**: T012 and T014 are strictly blocked until T008a and T008b are complete.

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and standardize EBSD datasets for Al, Cu, and Ni across specific cold-rolling reductions to ensure the analysis is based on high-quality, crystallographically consistent data.

**Independent Test**: The pipeline can be tested by running the data acquisition script against the specified public repositories and verifying that the output is a tidy CSV/Parquet file containing only valid orientations with confidence indices ≥ 0.1, properly re-indexed to FCC symmetry.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests marked [P] can be written in parallel with implementation, but execution depends on the implementation being complete.

- [ ] T010 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py`
- [ ] T011 [P] [US1] Write test stubs and assertions for the download and filter flow (can be written in parallel with T012 implementation) in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch EBSD data. **Logic**:
 1. **Primary Sources**: Attempt to fetch from Materials Project (API endpoint: `https://materialsproject.org/rest/v2/...`) and MTData repositories (`https://mtdata.org/...`) as mandated by FR-001.
 2. **Fallback**: If primary sources fail (network error, 404), attempt to fetch from a verified HuggingFace dataset (e.g., `huggingface.co/datasets/materials/ebsd_fcc_reductions`) ONLY if the dataset is documented to contain the specific 'reduction' metadata variable.
 3. **Error Handling**: If ALL sources fail, or if the HuggingFace dataset lacks the required metadata, raise `DataUnavailableError` and exit. **DO NOT** generate synthetic data. (FR-001, Constitution Principle I)
 4. **Reduction Levels Resolution**:
    - **Attempt 1**: Check if `research.md` exists in the project root. If it does, parse it for a `reduction_levels` key (list of integers).
    - **Attempt 2 (Fallback)**: If `research.md` is missing, unreadable, or lacks the key, use the hardcoded default list: `[0, 10, 20, 30, 40, 50, 60, 70, 80]`.
    - **Execution**: Use the resolved list to filter or request data. If a specific level is missing in the source data, log a warning and proceed with available levels. If ALL levels for a specific metal are missing, raise `DataUnavailableError`.
 5. **Data Hygiene**: Ensure all downloaded files are checksummed upon receipt. (FR-001)
- [ ] T013 [US1] Add error handling for missing reduction levels or corrupted files, logging warnings and proceeding (US-1 Scenario 3). **Logic**: If a specific metal/reduction combination is missing, skip that entry, log the error, and proceed with available data. If >50% of points are filtered in a sample, flag as "low reliability" and exclude (Edge Case). (FR-001)
- [ ] T014 [US1] Implement `code/data/preprocess.py` to filter confidence index < 0.1 and re-index orientations to FCC symmetry using `orix`. **Logic**:
 1. Read reduction levels from the resolved list (as determined in T012).
 2. If specific levels are `[deferred]` (from research.md), proceed with available levels and log a warning.
 3. If ALL levels are `[deferred]`, the script will have already failed in T012; this task assumes valid input exists. (FR-002)
 4. Integrate exclusion logic: flag samples where >50% of points are filtered as "low reliability" and EXCLUDE them from the final training set (Edge Case). (FR-001)
 5. **Symmetry Enforcement**: This is the sole mechanism for symmetry enforcement; no custom loss functions are used.
- [ ] T015 [US1] Generate consolidated Parquet output to `data/processed/cleaned_ebsd.parquet` with metadata (material, reduction, confidence). **Note**: This task depends on the completion of the preprocessing pipeline (T014) which incorporates the error handling (T013) and exclusion logic. **Dependency**: T012 -> T013 -> T014 -> T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Texture Quantification and Descriptor Extraction (Priority: P2)

**Goal**: Convert raw orientation data into specific, quantifiable texture descriptors (Texture Index, Volume Fractions of Brass, Copper, S, and Goss components) to enable statistical modeling.

**Independent Test**: The quantification module can be tested by processing a known benchmark dataset and verifying that the calculated volume fractions match published values within ±0.05.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Unit test for Brass/Copper/S/Goss calculation logic in `tests/unit/test_descriptors.py`
- [ ] T017 [P] [US2] Benchmark test against Rosenstock et al. (2018) values in `tests/unit/test_benchmark_validation.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/features/descriptors.py` to calculate Texture Index and volume fractions using MTEX-style search algorithms. **Logic**:
 1. **Euler Ranges (phi1, Phi, phi2 in degrees)**:
    - **Brass**: [35, 45, 55, 65] (Approximate: phi1=35-45, Phi=55-65, phi2=0-90)
    - **Copper**: [39, 39, 0, 0] (Approximate: phi1=39, Phi=39, phi2=0)
    - **S**: [59, 37, 63, 63] (Approximate: phi1=59, Phi=37, phi2=63)
    - **Goss**: [0, 45, 90, 0] (Approximate: phi1=0, Phi=45, phi2=90)
    - *Note*: Implement a search window of ±5 degrees around these central values to account for lattice rotation spread.
 2. **Symmetry**: Re-index orientations to FCC symmetry using `orix` before calculation (FR-002).
 3. **Output**: Calculate and return scalar values for each component. (FR-003)
- [ ] T019 [US2] Implement mass balance check: explicitly verify that the sum of major components (Brass, Copper, S, Goss) plus the "random" fraction equals 1.0 ± 0.01 for every sample. **Requirement**: This task is mandatory to verify spec.md US-2 Scenario 2 acceptance criteria. If the check fails, log an error and exclude the sample.
- [ ] T020 [US2] Output descriptors to `data/processed/descriptors.csv` linked to original sample IDs
- [ ] T021 [US2] Add validation to flag samples where texture evolution deviates from standard FCC trends (Edge Case). **Logic**: If a metal's texture evolution does not follow standard FCC trends (e.g., anomalous behavior), flag these outliers during validation rather than forcing a fit. **Requirement**: This task is mandatory to verify spec.md Edge Cases acceptance criteria.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train predictive models (Polynomial Regression, Gaussian Process) to estimate texture descriptors based on cold-rolling reduction with high accuracy (R² ≥ 0.85).

**Independent Test**: The model training and validation pipeline can be tested by splitting the dataset and verifying that the R² on the held-out test set meets a satisfactory performance threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T023 [P] [US3] Integration test for k-fold CV pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement `code/models/train.py` to fit separate polynomial (degree=2) and joint Gaussian Process (RBF kernel) models. **Mandatory**:
 1. **Hyperparameters**: Use GP length_scale search space [lower bound, upper bound]; Polynomial regularization (alpha) in [1e-4, 1e-2].
 2. **Feature Engineering**: Include 'Material Type' as a categorical feature (one-hot encoded) in the joint model to satisfy FR-008.
 3. **Output**: Return fitted models and training metrics. (FR-004, FR-008)
- [ ] T025 [US3] Implement k-fold cross-validation in `code/models/validate.py` to output RMSE and R² metrics (FR-005)
- [ ] T026 [US3] Implement extrapolation flagging: explicitly check if predictions are made outside the "lower-bound threshold" (default 0.0, configurable). If so, flag the prediction as "extrapolated" and apply a confidence penalty factor to the standard error. **Requirement**: This task is mandatory to verify spec.md FR-009 acceptance criteria.
- [ ] T027 [US3] Implement "Hold-out Physics Check" in `code/analysis/physics_check.py` to validate that trends (e.g., Brass increase) match known physics AND ensure all output reports explicitly frame findings as associational relationships (FR-006). **Report Template**: Generate a Markdown report with sections: 'Observed Trend', 'Expected Physics', 'Deviation Metric', 'Associational Framing Statement' (must state 'No causal claims; correlation only'). **Note**: This task focuses on trend validation, not symmetry constraints (which are handled in T014).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Model Robustness and Extrapolation Bounds (Priority: P4)

**Goal**: Ensure model stability under data sparsity and quantify the impact of missing microstructural variables.

**Independent Test**: The robustness module can be tested by running sensitivity analysis on interpolation tolerance and verifying R² variation ≤ 0.02.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [US4] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`. **Note**: This task is REQUIRED to verify SC-004 and must be implemented.
- [ ] T029 [P] [US4] Integration test for variance decomposition in `tests/integration/test_variance_decomposition.py`

### Implementation for User Story 4

- [ ] T030 [US4] Implement `code/analysis/robustness.py` to sweep interpolation tolerance over the specific set **{0.01, 0.05, 0.1}** as mandated by FR-007. **Logic**: Filter data points where `|reduction_query - reduction_train| > tolerance`. **Output**: Generate `data/processed/sensitivity_analysis.csv` containing the R² values for each tolerance. (FR-007)
- [ ] T031 [US4] Verify R² variation remains ≤ 0.02 across the swept tolerances {0.01, 0.05, 0.1} using T030 output (US-4 Scenario 2). **Requirement**: This task is mandatory to verify spec.md SC-004 acceptance criteria.
- [ ] T032 [US4] Implement variance decomposition (Shapley values or Hierarchical Modeling) to quantify residual variance from missing microstructural variables (FR-008)
- [ ] T033 [US4] Report the percentage of variance attributable to missing variables (e.g., grain size, SFE) in final metrics (US-4 Scenario 3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Removed (Scope Violation)

**Note**: Phase 7 (Physics Validation & Structural Integrity) and tasks T039-T044 have been removed as they implemented ODF reconstruction and pole figure validation which are not defined in spec.md FR-003 or FR-004. These were scope violations.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `docs/` including model limitations, associational framing, and the sensitivity analysis methodology.
- [ ] T046 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls)
- [ ] T047 [P] Additional unit tests for edge cases (missing data, extrapolation, symmetry errors) in `tests/unit/`
- [ ] T048 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T049 Verify all artifacts (data, models, metrics) are derived via script (Constitution Principle IV)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Physics Validation (Phase 7)**: REMOVED (Scope Violation)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 descriptor output (T020)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US3 model output (T024/T025)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel (development phase only)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Write test stubs and assertions for the download and filter flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/preprocess.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: User Story 4
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no logical dependencies (can be developed in parallel)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Review Update**: Phase 7 (T039-T044) removed to resolve coverage and executability concerns regarding ODF reconstruction and custom loss functions.
- **Critical Review Update**: T012 logic corrected to strictly prioritize Materials Project/MTData and fail loudly on missing data, removing synthetic fallback.
- **Critical Review Update**: T030 updated to explicitly list the sweep set {0.01, 0.05, 0.1} to meet FR-007.
- **Critical Review Update**: T018 updated with specific Euler ranges (Brass, Copper, S, Goss) to meet executability.
- **Critical Review Update**: T024 updated with hyperparameter ranges; T030 updated with explicit filtering logic.
- **Critical Review Update**: Task statuses corrected (T001-T005, T048-T049) to reflect actual artifact existence.