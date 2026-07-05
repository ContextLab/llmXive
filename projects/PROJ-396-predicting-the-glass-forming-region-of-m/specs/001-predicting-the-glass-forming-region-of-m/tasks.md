# Tasks: Predicting the Glass Forming Region of Metallic Glass Alloys via Machine Learning

**Input**: Design documents from `/specs/001-glass-forming-region/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `data/` directory at repository root
- [ ] T002 Create `data/raw/` directory
- [ ] T003 Create `data/processed/` directory
- [ ] T004 Create `data/metadata/` directory
- [ ] T005 Create `code/` directory
- [ ] T006 Create `code/tests/` directory
- [~] T007 Create `results/` directory
- [~] T008 Create `results/models/` directory
- [~] T009 Create `results/reports/` directory
- [~] T010 Create `results/validation/` directory
- [~] T011 Create `tests/` directory
- [~] T012 Create `tests/unit/` directory
- [~] T013 Create `tests/integration/` directory
- [~] T014 Create `tests/contract/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T015 Initialize Python 3.11 project: Create `requirements.txt` (pandas, numpy, scikit-learn, pyyaml, requests, pytest, pytest-cov) and create virtualenv at `.venv`
- [~] T016 [P] Configure linting: Create `.flake8` and `pyproject.toml` with formatting rules for black/flake8
- [~] T017 Create `code/utils.py` with logging configuration (JSON format) and chunking helpers (function signatures: `estimate_ram`, `process_chunked`)
- [~] T018 Implement memory-safe chunking logic in `code/utils.py`: Implement `process_chunked` function with dynamic chunksize adjustment; **Fallback**: if memory estimation fails or total size unknown, force batch size to ≤1000 samples
- [~] T019 Create `data/metadata/descriptor_sources.yaml` with pinned versions of elemental property tables; **Requirement**: Must record the exact source (e.g., "Materials Project v2024", "GFA-DB v1.0") for *each* descriptor instance computed

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion & Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest metallic alloy composition data from public repositories and compute thermodynamic descriptors (ΔHmix, δ, VEC, Δχ).

**Independent Test**: Run the data pipeline script on a sample subset and verify the output CSV contains required columns (composition, GFA label, ΔHmix, δ, VEC, Δχ) with no null values in predictor fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T020 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [~] T021 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_data_ingestion.py`

### Implementation for User Story 1

- [~] T022 [US1] Implement `code/data_ingestion.py` fetch logic: Define Zenodo GFA-DB as primary source (API endpoint: `) and Materials Project as fallback; implement fetching with retry logic, exponential backoff, and graceful failure for 503; **Output**: Raw data in `data/raw/`
- [ ] T023 [US1] Implement `code/data_ingestion.py` fallback: Generate synthetic dataset (Inoue's rules) **only for code testing** in `data/raw/synthetic_fallback.csv`; implement `generate_synthetic_dataset` function; **Requirement**: If synthetic mode is active, pipeline MUST halt with `SYNTHETIC_ONLY` error before any metric calculation or report generation to prevent accidental inclusion in final results
- [ ] T024 [US1] Implement `code/data_ingestion.py` chunked processing: Read CSV in batches of ≤1000, estimate RAM, adjust chunksize dynamically; enforce fallback to ≤1000 if memory exceeds limit
- [ ] T025 [US1] Implement `code/data_ingestion.py` schema validation: Verify `composition` and `gfa_label` (or `critical_cooling_rate`); apply threshold `Rc < 100 K/s` if needed; **Output**: Filtered CSV `data/processed/validated_compositions.csv` and log of excluded samples
- [ ] T026 [US1] Create `code/descriptor_computation.py` with standardized elemental property lookup using `data/metadata/descriptor_sources.yaml`; define formulas: ΔHmix, δ, VEC, Δχ
- [ ] T027 [US1] Implement `code/descriptor_computation.py` to compute ΔHmix, δ, VEC, Δχ for each sample using the defined formulas
- [ ] T028 [US1] Implement `code/descriptor_computation.py` logic to flag and exclude samples with missing elemental data (log entry required)
- [ ] T029 [US1] Run `code/descriptor_computation.py` to generate `data/processed/computed_descriptors.csv` with all computed features and original composition; **Depends on**: T023 (if testing) or T022 (if production)
- [ ] T030 [P] [US1] Unit test for descriptor computation formulas in `tests/unit/test_descriptors.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training & Cross-System Evaluation (Priority: P1)

**Goal**: Train Random Forest and Gradient Boosting classifiers, evaluate using stratified cross-validation and cross-system validation (distinct chemical families).

**Independent Test**: Run the training script and verify model artifacts (pkl files) and performance report (JSON/CSV) are generated containing accuracy and AUC-ROC metrics.

**⚠️ DEPENDENCY**: This phase CANNOT start until Phase 3 (US1) is complete and `data/processed/computed_descriptors.csv` exists.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T032 [P] [US2] Integration test for cross-system validation split in `tests/integration/test_cross_system_validation.py`

### Implementation for User Story 2

- [ ] T033 [US2] Implement `code/model_training.py` to load `data/processed/computed_descriptors.csv`
- [ ] T034 [US2] Implement `code/model_training.py` family assignment logic: Group by element with highest atomic fraction (Fe, Zr, Mg, Cu, Ti); **Tie-break**: Alphabetical order; **Input Column**: `composition`
- [ ] T035 [US2] Implement `code/model_training.py` split strategy: Primary = cross-system (train Fe-based, test Zr-based); fallback = stratified random split (80/20) if N < 20 per family
- [ ] T036 [US2] Implement `code/model_training.py` to train Random Forest classifier with stratified 5-fold cross-validation and grid search
- [ ] T037 [US2] Implement `code/model_training.py` to train Gradient Boosting classifier with stratified 5-fold cross-validation and grid search
- [ ] T038 [US2] Implement `code/model_training.py` to compute accuracy and AUC-ROC metrics for both models
- [ ] T039 [US2] Implement `code/model_training.py` cross-system validation: Calculate and report AUC-ROC on external family (e.g., Zr-based) if trained on Fe-based; **Output**: `results/reports/cross_system_metrics.json`; **Note**: Constitution Principle VII requires AUC ≥ 0.70 for generalizability claims, but Spec SC-002 defers the target; report measured value and flag if < 0.70
- [ ] T040 [US2] Save model artifacts to `results/models/` (pkl files)
- [ ] T041 [US2] Generate performance report to `results/reports/model_metrics.json`
- [ ] T042 [P] [US2] Unit test for family assignment logic in `tests/unit/test_family_assignment.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Methodological Validation & Sensitivity Analysis (Priority: P2)

**Goal**: Perform collinearity diagnostics, execute threshold sensitivity analysis, and ensure findings are framed as associational.

**Independent Test**: Verify the output report includes a collinearity matrix (VIF), a threshold sensitivity sweep table, and explicit "associational" language in the Conclusion section.

**⚠️ DEPENDENCY**: This phase CANNOT start until Phase 4 (US2) is complete and model artifacts exist in `results/models/`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T043 [P] [US3] Contract test for validation report schema in `tests/contract/test_validation_report.py`
- [ ] T044 [P] [US3] Integration test for sensitivity analysis in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T045 [US3] Implement `code/validation.py` to compute Variance Inflation Factor (VIF) for all predictors
- [ ] T046 [US3] Implement `code/validation.py` to flag any VIF > 5 in the report; **Do NOT** apply PCA automatically; **Note**: Spec FR-006 requires flagging only, not transformation
- [ ] T047 [US3] Implement `code/validation.py` threshold sensitivity analysis: Sweep classification cutoffs over {0.4, 0.5, 0.6}
- [ ] T048 [US3] Implement `code/validation.py` to compute false-positive rates for each threshold and calculate the **variation (delta)** between thresholds; generate sensitivity table
- [ ] T049 [US3] Implement `code/validation.py` to generate `results/validation/collinearity_report.json` with VIF scores
- [ ] T050 [US3] Implement `code/validation.py` to generate `results/validation/sensitivity_analysis.json` with threshold metrics and FPR deltas
- [ ] T051 [US3] Implement `code/validation.py` to generate final `results/validation/validation_report.json` including:
 - Accuracy, AUC, VIF scores, threshold sensitivity tables
 - Explicit "associational" language in Conclusion section
 - Data provenance note if source is synthetic/unverified (merged from T043 logic)
- [ ] T052 [P] [US3] Unit test for VIF computation in `tests/unit/test_vif.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T053 [P] Documentation updates in `README.md` and `docs/`
- [ ] T054 Code cleanup and refactoring
- [ ] T055 Additional unit tests in `tests/unit/`
- [ ] T056 Security hardening: Validate `composition` strings (regex for valid element symbols) and implement try/except blocks for all API calls
- [ ] T057 Run `quickstart.md` validation
- [ ] T058 Verify all results are reproducible with pinned random seeds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Strictly Serial Dependencies
 - **User Story 1 (Phase 3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **User Story 2 (Phase 4)**: CANNOT start until User Story 1 completes (T029 produces `data/processed/computed_descriptors.csv`)
 - **User Story 3 (Phase 5)**: CANNOT start until User Story 2 completes (T040 produces model artifacts)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **User Stories CANNOT run in parallel with each other** due to data dependencies:
 - US2 requires US1 output
 - US3 requires US2 output
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schema.py"
Task: "Integration test for data ingestion pipeline in tests/integration/test_data_ingestion.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Define source priority logic in code/data_ingestion.py"
Task: "Create code/descriptor_computation.py with standardized elemental property lookup"
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

### Sequential Team Strategy

Due to strict data dependencies:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Must complete before US2 starts)
 - Developer B: User Story 2 (Cannot start until US1 data is ready)
 - Developer C: User Story 3 (Cannot start until US2 models are ready)
3. Stories complete and integrate sequentially

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (2 cores, ~7 GB RAM, no GPU). No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: All analysis tasks must consume real datasets from verified sources. No synthetic/fake data for final results (synthetic only for fallback testing).
- **Ordering**: Tasks that produce data (T029) MUST precede tasks that consume it (T033).
- **Constitutional Note**: Constitution Principle VII mandates AUC ≥ 0.70 for generalizability claims. The Spec defers this target. Implementation will report the measured value and flag if < 0.70, but will not enforce a hard gate unless Spec is updated.