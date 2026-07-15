# Tasks: Predicting Insect Pollinator Networks from Floral Trait Data

**Input**: Design documents from `/specs/001-predicting-pollinator-networks/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure: `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `results/` at repository root.
- [ ] T001b [P] Create empty `__init__.py` files in `code/`, `tests/`, and `code/utils/` to initialize Python packages.
- [X] T002 Initialize Python 3.11 project with `scikit-learn`, `pandas`, `numpy`, `networkx`, `requests`, `tqdm`, `pyyaml`, `datasets` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (`ruff`), formatting (`black`), and type checking (`mypy`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement data hygiene utilities: checksum verification, raw vs processed directory structure (`data/raw/`, `data/processed/`) in `code/utils/io_utils.py` (Depends on T008 schema)
- [X] T005 [P] Implement reference validation wrapper for the Reference-Validator Agent pre-commit hook in `code/utils/citation_validator.py`
- [~] T006 [P] Create base configuration management (env vars, random seeds) in `code/config.py`
- [~] T007 [P] Setup logging infrastructure with structured JSON output in `code/utils/logger.py`
- [~] T008 [P] Define data schemas and validation logic in `code/contracts/dataset.schema.yaml` and `code/contracts/output.schema.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest bipartite interaction matrices from Web of Life and trait metadata, preprocess into a unified feature matrix.

**Independent Test**: Can be fully tested by running the data ingestion script against a small, fixed set of 3 Web of Life ecosystems and verifying the output feature matrix dimensions and data types match the expected schema (rows: plant-pollinator pairs, columns: encoded traits + binary link label).

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [~] T009 [P] [US1] Unit test for Web of Life downloader in `tests/test_ingestion.py` (mock network calls, verify file structure)
- [~] T010 [P] [US1] Unit test for heuristic mapping logic in `tests/test_ingestion.py` (verify fallback paths: mapping file -> DOI scrape -> Dryad API)
- [~] T011 [P] [US1] Integration test for full ingestion pipeline on 3 sample ecosystems in `tests/integration/test_ingestion_flow.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/ingestion.py`: Web of Life downloader with error handling (skip ecosystem if no trait data, log warning). **Must return the count of valid ecosystems retrieved.**
- [ ] T013 [P] [US1] Implement `code/ingestion.py`: Heuristic mapping strategy (Mapping file -> DOI scrape -> Dryad API search). **Runs in parallel with T012.**
- [ ] T014 [US1] Implement `code/preprocessing.py`: **Co-occurrence Logic & Temporal Validation**. Validate presence of temporal metadata. If missing, **default to spatial-only co-occurrence** (species in same ecosystem) and log a warning; do NOT block execution. Ensure strict adherence to FR-007 (spatial co-occurrence is sufficient).
- [ ] T015 [US1] Implement `code/preprocessing.py`: **Negative Sample Generation**. Generate negative samples strictly from co-occurring pairs (using logic from T014).
- [ ] T016 [US1] Implement `code/preprocessing.py`: Missing value handling (median imputation, flag >15% missingness)
- [ ] T017 [US1] Implement `code/preprocessing.py`: Outlier handling (winsorize at the extreme percentiles) and Z-score normalization
- [ ] T018 [US1] Implement `code/preprocessing.py`: Categorical encoding (one-hot, no leakage) and sampling effort extraction
- [ ] T019 [US1] Implement `code/preprocessing.py`: Unified feature matrix construction (rows: pairs, cols: traits + label, exclude species IDs)
- [ ] T020 [US1] [Depends on T012] **Validation & Threshold Enforcement**: Implement logic to verify the count of valid ecosystems (from T012). **If valid_count < 8, log a warning stating the reduced sample size and proceed with the available data.** Do NOT raise SystemExit. This task MUST be completed before T021 (Orchestrator).
- [ ] T021 [US1] Create `code/main.py` orchestrator to run ingestion and preprocessing sequentially (depends on T020 validation logic).
- [ ] T022 [US1] Add validation logic to ensure output matches `code/contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest classifier with stratified k-fold CV and calculate permutation importance.

**Independent Test**: Can be fully tested by training the model on a subset of the data (e.g., 1 ecosystem) and verifying that the cross-validation loop completes, produces consistent AUC-ROC scores across folds, and that the model object is serializable.

### Tests for User Story 2

- [ ] T023 [P] [US2] Unit test for stratified split generation in `tests/test_model.py`
- [ ] T024 [P] [US2] Unit test for permutation importance calculation in `tests/test_model.py`
- [ ] T025 [P] [US2] Integration test for training loop on sample data in `tests/integration/test_training_flow.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `code/model_training.py`: **OOM Protection**. Implement chunked processing or memory profiling for large ecosystems.
- [ ] T027 [US2] Implement `code/model_training.py`: **Logging Setup**. Add logging for CV metrics and importance scores to `results/metrics.json`.
- [ ] T028 [US2] Implement `code/model_training.py`: Random Forest configuration (class_weight='balanced', stratified k-fold CV)
- [ ] T029 [US2] Implement `code/model_training.py`: Cross-validation loop (mean AUC-ROC, std dev)
- [ ] T030 [US2] Implement `code/model_training.py`: Permutation importance calculation (top traits ranking)
- [ ] T031 [US2] Implement `code/model_training.py`: Model serialization (save to `data/processed/model.pkl`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generalization Validation and Reporting (Priority: P3)

**Goal**: Evaluate model using LOEO cross-validation, compare against null models, and generate visualizations.

**Independent Test**: Can be fully tested by running the evaluation script on a single held-out ecosystem and verifying that an AUC-ROC score is generated, a network comparison plot is saved, and the results are logged to a summary report.

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for LOEO loop logic in `tests/test_validation.py`
- [ ] T033 [P] [US3] Unit test for Trait-Shuffled Null Model in `tests/test_validation.py`
- [ ] T034 [P] [US3] Unit test for Degree-Preserving Null Model in `tests/test_validation.py`
- [ ] T035 [P] [US3] Unit test for NetworkX visualization generation in `tests/test_visualization.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/validation.py`: **LOEO Loop & Primary Validation**. Implement Leave-One-Ecosystem-Out (LOEO) cross-validation loop. **Implement the Trait-Shuffled Null Model as the primary validation metric** for trait efficacy within this loop, comparing against the CV mean.
- [ ] T037 [US3] Implement `code/validation.py`: **CV Mean Baseline Calculation**. Explicitly calculate and report the 'cross-validation mean' (mean of internal 5-fold CV on full dataset or N-1 folds) required by SC-003 for comparison against LOEO results.
- [ ] T038 [US3] Implement `code/validation.py`: Trait-Shuffled Null Model (primary validation for trait efficacy) - **Logic integrated into T036**.
- [ ] T039 [US3] Implement `code/validation.py`: Degree-Preserving Null Model (secondary, topology-focused)
- [ ] T040 [US3] Implement `code/validation.py`: Permutation test for statistical significance (p < 0.05) with dynamic iteration scaling (fallback to 100 iters if >3h runtime). **If fallback is triggered, explicitly flag the result as 'approximate' in the report to acknowledge reduced statistical power.**
- [ ] T041 [US3] Implement `code/visualization.py`: NetworkX plots (observed vs. predicted links, highlighting discrepancies)
- [ ] T042 [US3] Implement `code/visualization.py`: Precision-Recall curves and AUC-ROC plots
- [ ] T043 [US3] **Saturated Model Implementation**: Implement a 'Saturated Model' baseline **as a separate diagnostic step** using species IDs and interaction features **only for this baseline calculation** (distinct from the primary Trait-Only model) to calculate the 'trait gap' (Saturated AUC - Observed AUC) required by SC-004.
- [ ] T044 [US3] **Sensitivity Analysis**: Re-run evaluation on "high-confidence" negatives (high sampling effort) to assess label noise impact.
- [ ] T045 [US3] **Report Generation**: Implement `code/reporting.py`: Generate Markdown summary report (`results/report.md`) with metrics, importance, **trait gap (from T043)**, and sensitivity analysis (from T044) results.
- [ ] T046 [US3] **Citation Validation**: Run Reference-Validator Agent on `results/report.md` and ensure exit code 0.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Documentation updates in `docs/` (include quickstart.md with execution instructions)
- [ ] T048 Code cleanup and refactoring (remove dead code, ensure type hints)
- [ ] T049 Performance optimization: Verify streaming/chunking logic handles large datasets within 7 GB RAM by running a test with a 2GB synthetic dataset and confirming peak memory usage < 6.5 GB.
- [ ] T050 [P] Additional unit tests for edge cases (empty ecosystems, missing metadata) in `tests/unit/`
- [ ] T051 Run `quickstart.md` validation to ensure end-to-end reproducibility, **verifying that the dynamic iteration scaling fallback triggers correctly and produces reproducible results given the same runtime constraints.**
- [ ] T052 Verify all artifacts (models, metrics, reports) are generated with deterministic seeds

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Ingestion/Preprocessing (T012-T022) before Model Training (T026-T031)
- Model Training before Validation/Reporting (T036-T046)
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
Task: "Unit test for Web of Life downloader in tests/test_ingestion.py"
Task: "Unit test for heuristic mapping logic in tests/test_ingestion.py"
Task: "Integration test for full ingestion pipeline in tests/integration/test_ingestion_flow.py"

# Launch all preprocessing tasks for User Story 1 together (T012 & T013 parallel, T014-T022 sequential):
Task: "Implement Web of Life downloader in code/ingestion.py"
Task: "Implement Heuristic mapping strategy in code/ingestion.py"
Task: "Implement Co-occurrence Logic & Temporal Validation in code/preprocessing.py"
Task: "Implement Negative Sample Generation in code/preprocessing.py"
Task: "Implement Validation & Threshold Enforcement in code/preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify feature matrix output and threshold enforcement)
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
 - Developer A: User Story 1 (Ingestion/Preprocessing)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Validation/Reporting)
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
- **Data Integrity**: Never fall back to synthetic data if real fetch fails; let the run fail loudly.
- **Co-occurrence**: Ensure negative samples are derived strictly from the interaction matrix (spatial co-occurrence) with explicit temporal validation. If temporal data is missing, spatial-only is sufficient.
- **LOEO**: Ensure the validation strategy is Leave-One-Ecosystem-Out, not a single held-out test.
- **Null Models**: Prioritize Trait-Shuffled Null Model for trait efficacy; use Degree-Preserving only for topology comparison.
- **Threshold**: If <8 ecosystems are retrieved, log a warning and proceed; do NOT fail the pipeline.
- **Trait Gap**: Must be calculated using a Saturated Model baseline (T043) as a distinct diagnostic step.
- **Approximate Results**: If permutation test fallback triggers, explicitly flag the result as approximate in the report.