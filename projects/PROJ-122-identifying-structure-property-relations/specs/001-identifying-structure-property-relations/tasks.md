# Tasks: Identifying Structure-Property Relationships in Polymer Blends

**Input**: Design documents from `/specs/001-structure-property-relationships/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED based on the spec's "Independent Test" sections.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root (adjusted to `code/` and `tests/` per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `state/`)
- [ ] T001a [P] Create directory structure: `code/`, `data/raw/`, `data/processed/`, `data/features/`, `tests/`, `state/projects/`
- [X] T001b [P] Create `code/requirements.txt` with pinned dependencies (pandas, rdkit, scikit-learn, xgboost, shap, pyyaml, requests, joblib, psutil)
- [ ] T001c [P] Create `tests/` directory structure: `contract/`, `integration/`, `unit/`
- [ ] T001d [P] Create `state/projects/` directory structure and placeholder `PROJ-122-identifying-structure-property-relations.yaml`
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools
- [ ] T004 [P] Initialize `.gitignore` and `pytest` configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create data schema definitions in `specs/001-structure-property-relationships/contracts/dataset.schema.yaml`
- [ ] T006 Create output schema definitions in `specs/001-structure-property-relationships/contracts/output.schema.yaml`
- [X] T007 Implement base logging infrastructure in `code/utils/logger.py`
- [X] T008 Implement deterministic random seed pinning in `code/utils/seeds.py`
- [X] T009 Implement checksum utility for raw data in `code/utils/checksum.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Aggregate polymer blend data from NIST, Polymer Database, and Materials Project into a clean, unit-harmonized dataset.

**Independent Test**: Run ingestion script on known data; verify SMILES parsing, unit conversion (K, GPa), and weight-fraction validation logic.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/test_contract.py`
- [X] T011 [P] [US1] Unit test for unit conversion logic (C->K, Pa->GPa) in `tests/test_ingest.py`
- [X] T012 [P] [US1] Unit test for weight-fraction sum check (tolerance ±0.02) in `tests/test_ingest.py`
- [X] T013 [P] [US1] Unit test for RDKit SMILES parsing and invalid row exclusion in `tests/test_ingest.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement API fetcher with exponential backoff (limited number of retries) in `code/01_ingest.py` <!-- FAILED: unspecified -->
- [X] T015 [US1] Implement unit harmonization logic (Tg to Kelvin, Modulus to GPa) in `code/01_ingest.py`
- [X] T016 [US1] Implement weight-fraction validation and exclusion logic in `code/01_ingest.py`
- [X] T017 [US1] Implement SMILES validation and RDKit parsing in `code/01_ingest.py`
- [X] T018 [US1] Implement data quality report generation (`data_quality_report.json`) in `code/01_ingest.py`
- [X] T019 [US1] Implement "Data Verification Gate" in `code/01_ingest.py`: **Invoke Reference-Validator Agent** to verify existence and accessibility of specific dataset URLs containing SMILES, Composition, Tg, and Modulus before ingestion; halt with clear error if no verified source is found (FR-015, FR-019). <!-- ATOMIZE: requested -->
- [X] T019b [US1] Implement weight-fraction tolerance sensitivity sweep in `code/01_ingest.py`: Run validation with thresholds defined in `config.py` (configurable list, not hardcoded) and log the impact on valid record counts and pass rate percentage per threshold to `tolerance_sensitivity_report.json` (FR-014).
- [ ] T019c [US1] Implement "Join Success Rate Check & Fallback Trigger" in `code/01_ingest.py`: Calculate the percentage of records with a "perfect join" (SMILES + Composition + Tg + Modulus). If failure rate > 50%, trigger "Monomer-Level Fallback" mode immediately and halt the main blend pipeline, switching to `code/02b_fallback.py` (FR-013, Plan Gate 1).
- [ ] T020 [US1] Save raw data to `data/raw/` with SHA-256 checksums in `state/`
- [ ] T020b [US1] Update Single Source of Truth: Write final artifact hashes to `state/projects/PROJ-122-identifying-structure-property-relations.yaml` (FR-018, Constitution).
- [ ] T020c [US1] Implement "Source Tagging" in `code/01_ingest.py`: Tag all ingested records with their source origin to enable stratified splitting in downstream tasks (FR-016). (Note: The actual split logic is implemented in T033c).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Descriptor Generation (Priority: P2)

**Goal**: Generate molecular descriptors from SMILES and compute blend-specific interaction features.

**Independent Test**: Run feature module on sample data; verify descriptor count (≥15), mathematical consistency of mixing rules, and VIF diagnostics.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T021 [P] [US2] Unit test for RDKit descriptor generation (MW, TPSA, Free Volume) in `tests/test_features.py`
- [ ] T022 [P] [US2] Unit test for Fox and Gordon-Taylor equation calculations in `tests/test_features.py`
- [ ] T023 [P] [US2] Unit test for VIF calculation logic (diagnostic only) in `tests/test_features.py`: Verify VIF computation for a small matrix and flagging of values > 5.0.

### Implementation for User Story 2

- [ ] T024 [US2] Implement molecular descriptor generation (≥15 features) using RDKit in `code/02_features.py`
- [ ] T025 [US2] Implement weighted average descriptor calculation for blends in `code/02_features.py`
- [ ] T026 [US2] Implement absolute difference calculation for component descriptors in `code/02_features.py`
- [ ] T027a [US2] Implement Target Variable Derivation: Compute `Tg_residual` (Tg_measured - Tg_Fox) as the **target variable** for model training in `code/02_features.py`. Save the dataset with this target column to `data/processed/` (FR-004).
- [ ] T027b [US2] Implement Interaction Features: Compute Fox equation and Gordon-Taylor equation predicted values as **input features** (interaction features) to be added to the feature matrix in `code/02_features.py`. Save baseline metrics to `data/features/baseline_metrics.json` for later comparison (FR-004).
- [ ] T028a [US2] Implement Variance Inflation Factor (VIF) **Diagnostics** in `code/02_features.py`: Compute VIF for all predictors. If VIF > 5.0, flag the predictor. Output VIF diagnostics to `data/features/vif_report.json`. (Note: Sensitivity analysis re-training logic is moved to T038d in Phase 5) (FR-008).
- [ ] T029 [US2] Save feature matrix to `data/features/` with traceability metadata in `code/02_features.py`
- [ ] T029b [US2] Implement "Stratified Random Sampling" in `code/02_features.py`: If raw dataset exceeds a configurable threshold of `max RAM capacity` (queried via `psutil` and defined in `config.py`), perform stratified sampling to target a reduced volume, ensuring CPU-tractable execution while preserving source distribution (FR-017).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Training and Statistical Validation (Priority: P3)

**Goal**: Train Random Forest/XGBoost models, compare against baselines, and generate interpretability reports.

**Independent Test**: Execute training pipeline; verify MAE reporting, paired t-test execution, and SHAP value generation.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T030 [P] [US3] Unit test for model training and 5-fold CV logic in `tests/test_train.py`
- [ ] T031 [P] [US3] Unit test for paired t-test implementation and p-value reporting in `tests/test_train.py`
- [ ] T031b [P] [US3] Unit test for VIF sensitivity analysis logic in `tests/test_train.py`: Verify re-training logic and comparison of MAE/p-value when excluding the highest VIF predictor.
- [ ] T032 [P] [US3] Unit test for SHAP value generation and feature importance ranking in `tests/test_train.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement data splitting (train/validation/test) with fixed seed in `code/03_train.py`: **Gate**: Check if N < 100; if so, raise `DataInsufficiencyError` with message "Dataset size N={N} < 100" and halt pipeline (FR-012).
- [ ] T033c [US3] Implement "Source Stratified Split" in `code/03_train.py`: Ensure validation splits are stratified by data source (using the tags from T020c) to address domain shift (FR-016).
- [ ] T033d [US3] Implement "Target Variable Assignment" in `code/03_train.py`: Explicitly assign `y = Tg_residual` (computed in T027a) as the target vector for all training models (FR-004).
- [ ] T033e [US3] Implement "Report Source Stratification Success" in `code/03_train.py`: Generate a report verifying the split distribution by source to confirm stratification worked as intended (FR-016).
- [ ] T034 [US3] Implement Random Forest and XGBoost training with cross-validation in `code/03_train.py`
- [ ] T035 [US3] Implement linear regression baseline training in `code/03_train.py`
- [ ] T036 [US3] Implement paired t-test comparison (ML vs Linear) and **configurable correction method** (default Bonferroni or FDR, configurable in `config.py`) in `code/03_train.py` (Assumptions).
- [ ] T037 [US3] Implement SHAP value computation for a representative set of top predictions in `code/03_train.py`
- [ ] T037b [US3] Implement VIF diagnostic reporting in `code/03_train.py`: Report VIF values for the final model features (note: sensitivity analysis logic is moved to T038d).
- [ ] T038 [US3] Implement multiple independent training runs with different seeds for stability analysis in `code/03_train.py`: Execute multiple independent runs with varying random seeds.. (FR-009).
- [ ] T038d [US3] Implement VIF Sensitivity Analysis: If VIF > 5.0 (from T028a), **re-train** the model excluding the predictor with the highest VIF, compare MAE/R² against the full model, and report the impact in `data/features/vif_sensitivity_report.json`. If VIF > 10, flag for exclusion (FR-008).
- [ ] T040 [US3] Generate summary statistics and plots in `code/04_report.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] [US3] Generate MAE and p-value summary table in `code/04_report.py`
- [ ] T040b [P] [US3] Generate SHAP summary plot and feature importance bar chart in `code/04_report.py`
- [ ] T040c [P] [US3] Aggregate stability metrics across multiple runs and generate feature stability frequency chart in `code/05_aggregate_stability.py`: Execute after multiple independent runs (T038) to aggregate results. **Logic**: Calculate the frequency of each feature appearing in the top-ranked list across multiple runs.; identify descriptors that appear in ≥ 80% of runs; output to `data/features/stability_metrics.json` (Explicitly covers SC-003).
- [ ] T041 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043a [P] Profile pipeline runtime on local runner to identify bottlenecks in `code/`
- [ ] T043b [P] Refactor `code/03_train.py` to implement batched SHAP calculation if profiling shows runtime > 4 hours
- [ ] T044 [P] Additional unit tests for edge cases (rate limits, missing SMILES) in `tests/`
- [ ] T045 Run quickstart.md validation to ensure reproducibility
- [ ] T050 [P] Update State Files with Final Hashes: Write final artifact hashes for all processed data to `state/projects/PROJ-122-identifying-structure-property-relations.yaml` AND `data/state.json` to satisfy FR-018 and Constitution requirements (FR-018).

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 feature output

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
Task: "Contract test for data schema validation in tests/test_contract.py"
Task: "Unit test for unit conversion logic in tests/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement API fetcher with exponential backoff in code/01_ingest.py"
Task: "Implement unit harmonization logic in code/01_ingest.py"
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
- **Feasibility Check**: All tasks are designed for CPU-only execution (no CUDA, no 8-bit quantization).
- **Data Integrity**: No synthetic data generation; all tasks rely on real public APIs or local processed data.