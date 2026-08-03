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

- [ ] T001a [P] Initialize project directory structure: Create `code/`, `data/raw/`, `data/processed/`, `data/features/`, `tests/`, `state/projects/` AND the placeholder file `state/projects/PROJ-122-identifying-structure-property-relations.yaml` in a single step.
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

- [ ] T005 [P] Create data schema definitions in `specs/001-structure-property-relationships/contracts/dataset.schema.yaml`: Define YAML schema with fields for SMILES, composition, Tg (K), Modulus (GPa), source, and validation rules per FR-001. **Content**: `type: object`, `required: [smiles, composition, tg_k, modulus_gpa]`, `properties: smiles (string, pattern: ^[A-Za-z0-9...]$), composition (array), tg_k (number, min: 0), modulus_gpa (number, min: 0)`.
- [ ] T006 [P] Create output schema definitions in `specs/001-structure-property-relationships/contracts/output.schema.yaml`: Define YAML schema for processed datasets, feature matrices, and model outputs per FR-001. **Content**: `type: object`, `required: [features, target, metadata]`, `properties: features (array of numbers), target (number), metadata (object)`.
- [X] T007 Implement base logging infrastructure in `code/utils/logger.py`
- [X] T008 Implement deterministic random seed pinning in `code/utils/seeds.py`
- [X] T009 Implement checksum utility for raw data in `code/utils/checksum.py`: Implement `compute_sha256(file_path)` and `write_state_hash(state_file, key, hash_value)` functions to update the `artifact_hashes` map in the state YAML.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Harmonization (Priority: P1) 🎯 MVP

**Goal**: Aggregate polymer blend data from NIST, Polymer Database, and Materials Project into a clean, unit-harmonized dataset.

**Independent Test**: Run ingestion script on known data; verify SMILES parsing, unit conversion (K, GPa), and weight-fraction validation logic.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation
> **Dependency**: T010 requires T005 and T006 completion.

- [ ] T010 [P] [US1] Contract test for data schema validation in `tests/test_contract.py`: **Precondition Check**: Verify T005 and T006 are populated with valid YAML schemas. If `dataset.schema.yaml` or `output.schema.yaml` are missing or invalid, the test MUST fail immediately with a clear error message "Schema artifacts missing or invalid". Implement tests validating data against `dataset.schema.yaml` (T005). **Dependency**: T005, T006 must be complete.
- [X] T011 [P] [US1] Unit test for unit conversion logic (C->K, Pa->GPa) in `tests/test_ingest.py`
- [X] T012 [P] [US1] Unit test for weight-fraction sum check (tolerance ±0.02) in `tests/test_ingest.py`
- [X] T013 [P] [US1] Unit test for RDKit SMILES parsing and invalid row exclusion in `tests/test_ingest.py`

### Implementation for User Story 1

- [ ] T019a [P] [US1] Implement Data Verification Gate in `code/01_ingest.py` (Pre-ingestion): **Invoke Reference-Validator Agent** to verify existence and accessibility of specific dataset URLs containing SMILES, Composition, Tg, and Modulus. **Input**: List of URLs from `config.py`. **Output**: `state/verification_log.json` with keys `url`, `status`, `overlap_score`. **Logic**: Check `CITATION_TITLE_OVERLAP_THRESHOLD >= 0.7`. **Action**: If no URL passes, HALT pipeline with error code 1 and message "Data Verification Gate Failed: No verified source found" (FR-015, FR-019). **Dependency**: This task runs BEFORE any data fetching (T014-T018).
- [ ] T014 [US1] Implement API fetcher with exponential backoff in `code/01_ingest.py`: Implement with exact parameters: initial=1s, multiplier=2, max=5 retries per FR-010. Output: `code/01_ingest.py` with function `fetch_with_backoff(url)`. **Dependency**: Requires T019a to pass.
- [ ] T015 [US1] Implement unit harmonization logic (Tg to Kelvin, Modulus to GPa) in `code/01_ingest.py`
- [ ] T016 [US1] Implement weight-fraction validation and exclusion logic in `code/01_ingest.py`
- [ ] T017 [US1] Implement SMILES validation and RDKit parsing in `code/01_ingest.py`
- [ ] T018 [US1] Implement data quality report generation (`data_quality_report.json`) in `code/01_ingest.py`
- [ ] T020 [US1] Save raw data to `data/raw/` with SHA-256 checksums in `state/`: Compute SHA-256 hash for each raw file. **Mechanism**: Invoke `utils.checksum.write_state_hash(state_file="state/projects/PROJ-122-identifying-structure-property-relations.yaml", key="raw_data_<filename>", hash_value=...)` to explicitly update the `artifact_hashes` map in the state YAML (FR-018). **Dependency**: Requires T019a to pass. **Note**: This task MUST run BEFORE T019c to ensure data is available for fallback.
- [ ] T020c [US1] Implement "Source Tagging" in `code/01_ingest.py`: Tag all ingested records with their source origin (column 'source') to enable stratified splitting in downstream tasks (FR-016). **Dependency**: Required for T019c. **Order**: Must run BEFORE T019c.
- [ ] T019c [US1] Implement "Join Success Rate Check & Fallback Trigger" in `code/01_ingest.py`: Calculate the percentage of records with a "perfect join" (SMILES, Composition, Tg, Modulus all non-null). **Precondition**: Verify that T019a (Data Verification Gate) passed AND T020 (Raw Data Save) AND T020c (Source Tagging) are complete. **Action**: If join failure rate > 50% AND verified source exists, trigger "Monomer-Level Fallback" mode immediately and halt the main blend pipeline, switching to `code/02b_fallback.py` (FR-013). **Action**: If join failure rate > 50% AND no verified source, HALT with "Data Insufficient for Fallback". **Exit Mechanism**: Raise `SystemExit` with code 1 and message. **Dependency**: Requires T020c and T020 to be executed first.
- [ ] T019b [US1] Implement "Sensitivity Sweep Script" in `code/01b_sensitivity.py`: Run a comprehensive sensitivity sweep over a range of weight-fraction tolerance values (e.g., low, medium, and high magnitudes) defined in `config.py`. **Range**: Values from `config.py`. **Output**: `tolerance_sensitivity_report.json` with keys `threshold`, `pass_rate`, `baseline_pass_rate` (at 0.02), `delta_pass_rate` (calculated as `pass_rate - baseline_pass_rate`), and `impact_assessment` (string describing the impact on data quality). **Metric**: Percentage of valid records per threshold. **Logic**: Calculate `delta_pass_rate` to quantify impact. **Dependency**: Requires T014-T018 completion (raw data available).

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
- [ ] T027b [US2] Implement Interaction Features: Compute Fox equation and Gordon-Taylor equation predictions. **Output**: `data/features/interaction_features.csv` containing these predictions. **Clarification**: These are *predictions* used to calculate the target variable, NOT the target itself, and NOT baseline metrics (which belong in Phase 5). They serve as inputs for the target derivation in T027a. **Dependency**: Requires T024 (descriptors).
- [ ] T027a [US2] Implement Target Variable Derivation: Compute `Tg_residual` (Tg_measured - Tg_Fox) as the **target variable** for model training in `code/02_features.py`. **Output Filename**: `data/processed/processed_data.csv`. **Columns**: All feature columns plus `Tg_residual`. **Formula**: `Tg_residual = Tg_measured - Tg_Fox` (handling missing Tg_Fox by exclusion). **Dependency**: Requires T027b output (Fox prediction).
- [ ] T028a [US2] Implement Variance Inflation Factor (VIF) **Diagnostics** in `code/02_features.py`: Compute VIF for all predictors. If VIF > 5.0, flag the predictor. Output VIF diagnostics to `data/features/vif_report.json`. (Note: Sensitivity analysis re-training logic is moved to T038d in Phase 5) (FR-008).
- [ ] T029 [US2] Save feature matrix to `data/features/` with traceability metadata in `code/02_features.py`
- [ ] T029b [US2] Implement "Stratified Random Sampling" in `code/02_features.py`: If raw dataset exceeds a configurable threshold of `max RAM capacity` (queried via `psutil` and defined in `config.py`), perform stratified sampling to target a reduced volume, ensuring CPU-tractable execution while preserving source distribution (FR-017). Sampling method: Stratified by source column.

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

- [ ] T033 [US3] Implement data splitting (train/validation/test) with fixed seed in `code/03_train.py`: **Gate**: Check if N < 100; if so, raise `DataInsufficiencyError` with message "Dataset size N={N} < 100" and halt pipeline (FR-012). **Logic**: 
  - **If N >= 500**: Use random split with fixed seed (70/15/15).
  - **If N < 500**: Implement Stratified Repeated K-Fold with **5 folds and 3 repeats** (as per FR-005 "multiple folds, multiple repeats").
  - **Stratification**: Stratify by 'source' column (FR-016).
  **Dependency**: Requires T027a (Target Variable).
- [ ] T033d [US3] Implement "Target Variable Assignment" in `code/03_train.py`: Explicitly assign `y = Tg_residual` (computed in T027a) as the target vector for all training models (FR-004).
- [ ] T033e [US3] Implement "Report Source Stratification Success" in `code/03_train.py`: Generate a report verifying the split distribution by source to confirm stratification worked as intended (FR-016).
- [ ] T034 [US3] Implement Random Forest and XGBoost training with cross-validation in `code/03_train.py`
- [ ] T035 [US3] Implement linear regression baseline training in `code/03_train.py`
- [ ] T036 [US3] Implement paired t-test comparison (ML vs Linear) and **configurable correction method** (default Bonferroni or FDR, configurable in `config.py`) in `code/03_train.py` (Assumptions). Output: p-value and conclusion (reject/fail to reject null hypothesis).
- [ ] T037 [US3] Implement SHAP value computation for a representative set of top predictions in `code/03_train.py`
- [ ] T037b [US3] Implement VIF diagnostic reporting in `code/03_train.py`: Report VIF values for the final model features (note: sensitivity analysis logic is moved to T038d).
- [ ] T038 [US3] Implement multiple independent training runs with different seeds for stability analysis in `code/03_train.py`: Execute multiple independent runs with varying random seeds.. (FR-009).
- [ ] T038d [US3] Implement VIF Sensitivity Analysis: If VIF > 5.0 (from T028a), **re-train** the model excluding the predictor with the highest VIF, compare MAE/R² against the full model, and report the impact in `data/features/vif_sensitivity_report.json`. **Mandatory Action**: If VIF > 10, **EXCLUDE** the predictor from the final feature matrix, re-train the model with the reduced set, and save the new model artifact to `data/models/model_final_vif_corrected.pkl` (FR-008). **Action**: Update `data/features/processed_data.csv` to remove the predictor and save the new model artifact. **Dependency**: Requires T028a COMPLETION and the generation of `vif_report.json` before this task can start.

**Checkpoint**: All user stories should now be independently functional
**Note**: T038d must strictly wait for T028a to complete and produce `vif_report.json`.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] [US3] Generate MAE and p-value summary table in `code/04_report.py`
- [ ] T040b [P] [US3] Generate SHAP summary plot and feature importance bar chart in `code/04_report.py`
- [ ] T040c1 [P] [US3] Implement aggregation logic for stability metrics in `code/05_aggregate_stability.py`: Execute after multiple independent runs (T038) to aggregate results. **Logic**: Calculate the frequency of each feature appearing in the top-ranked list across multiple runs; identify descriptors that appear in ≥ 80% of runs; **Count and Report**: Explicitly count and report if at least 3 such descriptors exist (SC-003); output to `data/features/stability_metrics.json`. **Dependency**: Requires T038 completion.
- [ ] T040c2 [P] [US3] Generate stability frequency chart in `code/05_aggregate_stability.py`: Create visualization of feature stability frequencies.
- [ ] T041 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043a [P] Profile pipeline runtime on local runner to identify bottlenecks in `code/`
- [ ] T043b [P] Implement batched SHAP calculation in `code/03_train.py`: Refactor to handle large datasets if profiling shows runtime > 4 hours.
- [ ] T044 [P] Additional unit tests for edge cases (rate limits, missing SMILES) in `tests/`
- [ ] T045 Run quickstart.md validation to ensure reproducibility

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