# Tasks: Predicting Reaction Mechanisms from Spectroscopic Data with Machine Learning

**Input**: Design documents from `/specs/001-predicting-reaction-mechanisms/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

- [ ] T001a [P] Create project directory structure: `src/`, `tests/`, `specs/001-predicting-reaction-mechanisms/`, `data/`, `state/projects/`
- [ ] T001b [P] Create `__init__.py` files for all `src/` and `tests/` subdirectories to establish Python packages
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (scikit-learn, xgboost, pandas, numpy, datasets, pyyaml, pytest, pubchempy, pyscf)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `src/utils/logging.py` for warning/flagging logic (edge case handling)
- [ ] T005 [P] Implement `src/utils/io.py` for checksum generation and file I/O helpers (Principle III)
- [ ] T006 Create base schema definitions in `specs/contracts/` (dataset.schema.yaml, output.schema.yaml)
- [X] T007 [P] Setup `src/ingestion/__init__.py` and `src/modeling/__init__.py` package structures
- [ ] T008 Configure random seed pinning utility in `src/utils/seed.py` (Reproducibility Principle I)
- [ ] T033a [P] [Foundational] Create `src/analysis/dft_setup.py` and `data/reference/literature_db.json` to support dynamic literature cross-reference and local DFT calculations (FR-010 prerequisite)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw IR/NMR data, filter by provenance, convert to fixed-length fingerprints, and verify labels.

**Independent Test**: Run `src/ingestion/preprocess.py` against a small NIST subset; verify output CSV has an appropriate number of bins, valid {SN1, SN2, E1} labels, and zero NaNs in labels.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Contract test for fingerprint schema in `tests/contract/test_fingerprint_schema.py`
- [X] T010 [P] [US1] Integration test for end-to-end ingestion of a small NIST sample in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `src/ingestion/load_nist.py` to fetch NIST WebBook JSONL (cm-1); MUST parse the 'provenance' field to distinguish 'kinetic studies' from 'product structure' labels; EXCLUDE rows where provenance is not 'kinetic studies' or 'validated intermediates' with NO fallback to synthetic or product-structure data; strict URL validation (no synthetic fallback)
- [ ] T012 [P] [US1] Implement `src/ingestion/load_pubchem.py` to fetch PubChem Parquet subsets (NMR chemical shift ranges); MUST parse the 'provenance' field to distinguish 'kinetic studies' from 'product structure' labels; EXCLUDE rows where provenance is not 'kinetic studies' or 'validated intermediates' with NO fallback to synthetic or product-structure data; strict URL validation <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T013 [US1] Implement provenance filtering logic in `src/ingestion/load_*.py` to EXCLUDE rows where the 'provenance' field indicates labels inferred solely from product structure (FR-008); ensure NO fallback mechanism exists
- [ ] T014 [US1] Implement `src/ingestion/preprocess.py` to normalize spectra and bin into 512-element vectors (FR-001)
- [ ] T015 [US1] Add outlier detection in `src/ingestion/preprocess.py` to exclude spectra with extreme variance or missing frequency ranges
- [ ] T016 [US1] Implement class balance validation in `src/ingestion/preprocess.py` to flag classes with <50 samples (FR-001, Edge Case)
- [ ] T017 [US1] Calculate checksums for all downloaded datasets and record them ONLY in `state/projects/PROJ-088-predicting-reaction-mechanisms-from-spec.yaml` `artifact_hashes` map (Principle III); do NOT write to separate text files

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and XGBoost models with stratified 5-fold CV, ensuring no data leakage and strict associational reporting.

**Independent Test**: Run `src/modeling/train.py`; verify JSON report contains mean accuracy, std dev, and per-class F1-scores derived strictly from disjoint folds.

### Tests for User Story 2

- [ ] T018 [P] [US2] Contract test for training output schema in `tests/contract/test_training_report_schema.py`
- [ ] T019 [P] [US2] Integration test for stratified split disjointness in `tests/integration/test_cv_splitting.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `src/modeling/train.py` with Random Forest classifier and stratified 5-fold cross-validation (FR-002)
- [ ] T021 [P] [US2] Implement `src/modeling/train.py` with XGBoost classifier and stratified 5-fold cross-validation (FR-002)
- [ ] T022 [US2] Implement `src/modeling/metrics.py` to calculate accuracy, F1, and confusion matrices (SC-001)
- [ ] T023 [US2] Add logic to `src/modeling/train.py` to enforce strict disjoint training/test folds (no leakage)
- [ ] T024 [US2] Implement `src/utils/report.py` to generate JSON reports with explicit "associational" framing (FR-006)
- [ ] T025 [US2] Add forbidden word filter in `src/utils/report.py` to exclude causal terms ("cause", "drive", "determine", etc.) (FR-006)
- [ ] T026 [US2] Add runtime and memory logging to `src/modeling/train.py` to verify <6h runtime and <7GB RAM (FR-005, SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Statistical Significance (Priority: P3)

**Goal**: Extract feature importance, run permutation tests with BH correction, and validate top features against literature/DFT.

**Independent Test**: Run `src/analysis/permutation.py`; verify p-value < 0.05 is reported, top 10 bins are ranked, and BH correction is applied.

### Tests for User Story 3

- [ ] T027 [P] [US3] Contract test for importance report schema in `tests/contract/test_importance_report_schema.py`
- [ ] T028 [P] [US3] Unit test for Benjamini-Hochberg correction logic in `tests/unit/test_bh_correction.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/importance.py` to extract and rank feature importance scores from RF/XGBoost (FR-003)
- [ ] T030 [P] [US3] Implement `src/analysis/importance.py` to calculate importance variance across CV folds (SC-002)
- [ ] T030a [US3] Calculate the variance of feature importance scores across folds and generate a `data/results/stability_variance.csv` report to measure stability (SC-002)
- [ ] T031 [US3] Implement `src/analysis/permutation.py` to run a single model-level permutation test (N=200) to assess overall predictive power (FR-004); output the final p-value and the feature importance scores of the trained model
- [ ] T031a [US3] Extract and aggregate the feature importance scores from the trained model (output of T031) into `data/results/feature_importance_scores.json` for downstream BH correction
- [ ] T032 [US3] Implement Benjamini-Hochberg correction in `src/analysis/importance.py` using the feature importance scores from T031a to identify significant bins (FR-007)
- [ ] T033 [US3] Implement `src/analysis/validation.py` to map top bins to known vibrational modes using `pubchempy` for dynamic literature cross-reference and the `pyscf` script from T033a for local DFT calculations (FR-010)
- [ ] T034 [US3] Implement `src/analysis/validation.py` to verify top features are not proxies for product structure (FR-009)
- [ ] T035 [US3] Add logic to handle "marginally significant" p-values (e.g., 0.051) explicitly in reports (Edge Case)
- [ ] T036 [US3] Generate visualization helper in `src/analysis/validation.py` to map top bins back to frequency ranges (e.g., carbonyl stretch)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Run full end-to-end integration test on a small real dataset subset
- [ ] T038 Update `README.md` and `docs/quickstart.md` with execution instructions
- [ ] T039 [P] Code cleanup and refactoring (remove unused imports, optimize memory usage)
- [ ] T040 [P] Additional unit tests for edge cases (missing labels, noisy spectra) in `tests/unit/`
- [ ] T041 Validate `quickstart.md` executes successfully on a fresh runner
- [ ] T042 Verify all causal language is removed from generated reports (manual audit)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loaders/models before services
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
# Launch all tests for User Story 1 together:
Task: "Contract test for fingerprint schema in tests/contract/test_fingerprint_schema.py"
Task: "Integration test for end-to-end ingestion of a small NIST sample in tests/integration/test_ingestion_flow.py"

# Launch all ingestion tasks for User Story 1 together:
Task: "Implement src/ingestion/load_nist.py..."
Task: "Implement src/ingestion/load_pubchem.py..."
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
- **Data Integrity**: Never use synthetic fallbacks; if real data fetch fails, the task must fail loudly.
- **Causal Language**: Strictly enforce FR-006 in all report generation logic.
- **Streaming**: For large datasets, use `streaming=True` in `datasets` library to stay within RAM limits.
- **Provenance Parsing**: T011/T012 must explicitly parse 'provenance' metadata to satisfy FR-008.
- **No Fallback**: T011-T013 must strictly exclude non-kinetic labels with NO fallback mechanism.
- **Permutation Test**: T031 performs a single model-level permutation test; T031a extracts importance scores for BH correction.
- **Stability Reporting**: T030a must calculate variance and output a CSV file.
- **DFT Source**: T033 uses `pubchempy` and `pyscf` (from T033a) for dynamic validation.
- **State Update**: T017 must update the project state YAML file ONLY.