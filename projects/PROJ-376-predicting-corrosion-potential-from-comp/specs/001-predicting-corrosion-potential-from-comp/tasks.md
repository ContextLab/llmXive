# Tasks: Predicting Corrosion Potential from Composition and Environment

**Input**: Design documents from `/specs/001-predict-corrosion-potential/`
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

- [ ] T001 Initialize project directory structure and verification script: Create `code/utils/setup_dirs.py` to generate `code/`, `data/`, `data/raw/`, `data/processed/`, `data/logs/`, `state/`, `contracts/`, `config/`, `code/data/`, `code/models/`, `code/utils/`, `code/tests/`. **Content**: The script MUST create these directories and write `state/setup_dirs_verified.json` containing a list of objects: `{"path": "<absolute_dir_path>", "created_at": "<ISO8601_timestamp>"}`. **Verification**: Run `python code/utils/setup_dirs.py` and verify `state/setup_dirs_verified.json` is valid JSON and all paths exist. **Producer**: `code/utils/setup_dirs.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create schema contracts: `contracts/ingest.schema.yaml` and `contracts/dataset.schema.yaml`. **Content**: Define fields for `ingest.schema.yaml` based on `AlloyRecord` in `data-model.md` and verify with `yamllint`. **Producer**: `code/utils/validate_schemas.py`. **Verification**: Generate `data/logs/schema_validation.log` containing `schema_file`, `validation_timestamp`, `tool_version`, `status`, and `details` (e.g., "Validated ingest.schema.yaml against yamllint v3.1.0: PASS").
- [X] T005 [P] Implement custom exceptions in `code/utils/exceptions.py` (DataInsufficientError, SchemaMismatchError)
- [X] T006 [P] Setup reproducible logging infrastructure in `code/utils/logging.py` (FR-010)
- [X] T007 Create base data model classes for AlloyRecord, EnvironmentRecord, CorrosionMeasurement. **Implementation**: Use Pydantic v2 for strict schema enforcement. Define `AlloyRecord` with fields: `alloy_id: str`, `composition: dict[str, float]`, `specific_alloy_designation: str`. Define `EnvironmentRecord` with fields: `ph: float`, `temperature: float`, `electrolyte_type: str`. Define `CorrosionMeasurement` with fields: `record_id: str`, `potential_mV: float`. **Verification**: Run `tests/unit/test_data_models.py` which must instantiate classes with valid/invalid data and exit 0 only if validation behaves as expected.
- [ ] T008 Setup environment configuration management for random seeds and file paths. **Artifact**: Create `config/seeds.yaml` and `config/paths.yaml`. **Content**: `seeds.yaml` MUST contain `random_state: a fixed seed for reproducibility`. `paths.yaml` MUST contain `data_raw: "data/raw"`, `data_processed: "data/processed"`, `logs: "data/logs"`. **Verification**: Run `code/utils/config_loader.py` and verify all keys (seeds, paths) exist and are non-empty.
- [ ] T009 [P] Update plan.md to mandate LOSO: Edit `specs/001-predict-corrosion-potential/plan.md` to replace all references to "GroupKFold (k=5)" with "Leave-One-Specific-Alloy-Out (LOSO)" in the Summary, Constitution Check, and Complexity Tracking sections. **Rationale**: The Spec (FR-004/FR-012) mandates LOSO; the plan must align with the Spec. **Verification**: Run `grep -i "groupkfold" specs/001-predict-corrosion-potential/plan.md` and ensure it returns no results. **Producer**: Manual edit or script updating plan.md.
- [ ] T014 [US1] Implement schema validation step in `code/data/preprocess.py` to enforce non-nulls and count records. **Halt Condition**: If <500 records or missing joint distribution, raise `SchemaMismatchError` as mandated by FR-014. **Producer**: `code/data/preprocess.py` must generate `data/logs/diagnostics/count_report.txt`. **Content**: Valid JSON with `record_count`, `valid_count`, `status`. **Verification**: Verify `data/logs/diagnostics/count_report.txt` exists and contains valid JSON with count < 500, AND verify `SchemaMismatchError` is raised and caught in integration tests.
- [ ] T015 [US1] Implement `code/data/split.py` with **Leave-One-Specific-Alloy-Out (LOSO)** logic to prevent data leakage as per FR-004/FR-012. **Pre-check**: Verify dataset contains ≥10 specific alloy designations; if not, raise `DataInsufficientError`. **Verification**: Verify that the `specific_alloy_designation` column is passed as the `groups` argument to the split logic. Verify that no specific alloy designation appears in both train and test sets. **Output**: Generate train/test indices for folds ensuring no alloy overlap. **Action**: Implement LOSO strictly as per Spec FR-004/FR-012. (FR-004, FR-012)
- [ ] T016 [US1] Add diagnostic logging for excluded records (missing pH, extreme pH) to `data/logs/pipeline.log`. **Format**: JSON lines with `record_id`, `reason`, `timestamp`. **Verification**: Verify `data/logs/pipeline.log` contains entries for excluded records.
- [ ] T017 [US1] Verify split integrity: ensure strict LOSO constraint is met (zero overlap of specific_alloy_designation_id between folds). **Deliverable**: Write `data/logs/split_validation.json` containing fold statistics and overlap verification. **Verification**: Verify `data/logs/split_validation.json` exists, is valid JSON, and contains `overlap_count: 0`. (SC-004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download and preprocess NIST Corrosion Database records into a unified, clean dataset with strict schema validation and leakage prevention.

**Independent Test**: Execute `code/data/download_nist.py` and `code/data/preprocess.py`; verify output `data/processed/corrosion_dataset.parquet` exists, contains ≥500 records, has no nulls in critical fields, and passes Leave-One-Specific-Alloy-Out (LOSO) validation (≥10 alloy designations).

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/download_nist.py` to fetch from NIST-IR-8200. **Pre-fetch**: Check verified-datasets registry/config for URL. **Halt**: If URL is missing, raise `DataInsufficientError` immediately and halt (Plan Data Acquisition Strategy). **Fetch**: Implement retry logic (exponential backoff, limited retries) and halt on /404 (FR-001, FR-002)
- [X] T013 [P] [US1] Implement `code/data/preprocess.py` to encode weight fractions, filter missing pH/temp, and exclude outliers (FR-003, FR-013)

### Tests for User Story 1 (SEQUENTIAL - Write After Implementation) ⚠️

> **NOTE**: Write these tests AFTER T012-T017 implementation. Run them to ensure they FAIL before fixing. These are NOT parallel with implementation. They must be written and run to fail after T012-T017 implementation.

- [X] T010 [US1] Write unit test for schema validation logic in `tests/unit/test_data_validation.py`. **Constraint**: Must fail before T012-T017 implementation. **Assertions**: Assert `SchemaMismatchError` is raised when record_count < 500; Assert `SchemaMismatchError` is raised when critical fields are null.
- [X] T011 [US1] Write integration test for data ingestion pipeline in `tests/integration/test_data_ingestion.py`. **Constraint**: Must fail before T012-T017 implementation. **Assertions**: Assert pipeline halts if NIST URL is missing; Assert output parquet has no nulls in critical fields.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting regressors on the preprocessed dataset to predict corrosion potential and evaluate performance against null baselines.

**Independent Test**: Run `code/models/train.py` and `code/models/evaluate.py`; verify `data/processed/model_results.json` contains R² and RMSE for both models, and that the best model is classified as "learnable" if R² > 0.0 (p < 0.05).

### Implementation for User Story 2

- [ ] T023a [US2] Create `config/astm_g59_tolerance.yaml` and define tolerance. **Source**: ASTM G59-19 Standard Practice for Conducting Potentiodynamic Polarization Resistance Measurements (public abstract/summary) or the community-default value if text is inaccessible. **Content**: If standard does not define a specific value, USE the community-standard default voltage.. **Do NOT halt**. **Verification**: Verify `config/astm_g59_tolerance.yaml` exists and contains `tolerance_mV: 150`.
- [X] T020 [P] [US2] Implement `code/models/train.py` to train Random Forest and Gradient Boosting (CPU-only, scikit-learn) with `random_state=42` using LOSO split indices (FR-005).
- [X] T021 [US2] Implement `code/models/evaluate.py` to calculate R² and RMSE on held-out test sets from LOSO split and aggregate metrics (FR-006). **Verification**: Ensure T023a has completed if tolerance is needed for evaluation.
- [ ] T023b [US2] Implement RMSE calculation in millivolts (mV) and compare against the tolerance from `config/astm_g59_tolerance.yaml`. **Key**: Read `tolerance_mV`. If missing, use default 150. **Verification**: Report comparison result; do not allow 'N/A' path. **Dependency**: Requires T021 (Evaluate) to be complete. (SC-002)
- [ ] T022 [US2] Implement null baseline comparison (mean prediction) and "learnable" classification logic (R² > 0.0, p < 0.05 via **one-sample permutation test** on aggregated predictions) (SC-001, SC-007). **Sub-steps**: 1. Generate null distribution via a sufficient number of permutations. 2. Calculate p-value. 3. Apply FDR correction. 4. Write classification result ("learnable" or "null") to `data/processed/model_results.json`. (FR-008)
- [X] T024 [US2] Save model artifacts and metrics to `data/processed/model_results.json` conforming to `contracts/model_results.schema.yaml`. **Verification**: Run `code/utils/validate_schema.py` against `data/processed/model_results.json` and exit 0.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for model training timing (must complete <30 mins) in `tests/unit/test_model_timing.py`
- [ ] T019 [P] [US2] Integration test for end-to-end training and evaluation in `tests/integration/test_model_training.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Feature Importance Analysis (Priority: P3)

**Goal**: Generate permutation importance scores and partial dependence plots to identify key alloying elements and environmental interactions.

**Independent Test**: Run `code/models/interpret.py`; verify output includes top 5 features with p-values < 0.05 (Bonferroni/FDR corrected) and at least one partial dependence plot visualizing non-linear interaction.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/models/interpret.py` to calculate permutation importance (FR-007)
- [X] T028 [US3] Implement statistical significance testing for feature importance using **one-sample permutation test** (null hypothesis: importance = 0) with 1,000 permutations, seed=42, applying Bonferroni or FDR correction for multiple comparisons (FR-008, SC-003).
- [X] T029 [US3] Generate partial dependence plots for top element-environment pairs (e.g., Chromium vs pH) (FR-009)
- [X] T030 [US3] Compile summary report stating whether specific elements consistently reduce corrosion potential. **Output**: Generate `data/processed/interpretability/summary.md` containing: 1. Top 5 features, 2. PDP plot paths (relative paths, e.g., `plots/pdp_cr_ph.png`), 3. Conclusion on element consistency. **Producer**: `code/models/interpret.py`. **Verification**: Verify `data/processed/interpretability/summary.md` exists and contains the string "Top 5 features" and at least one PDP plot path.
- [X] T031 [US3] Save all plots and reports to `data/processed/interpretability/`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for permutation significance logic (sufficient permutations for stable estimation, FDR correction) in `tests/unit/test_importance_stats.py`
- [ ] T026 [P] [US3] Integration test for plot generation in `tests/integration/test_interpretability.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a Update README.md: Add installation section with specific steps. **Verification**: Verify "Installation" section exists in README.md.
- [X] T032b Update README.md: Add API reference section for key scripts. **Verification**: Verify "API Reference" section exists in README.md.
- [X] T032c Update README.md: Add contribution guidelines section. **Verification**: Verify "Contributing" section exists in README.md.
- [X] T032d Update README.md: Add development setup instructions. **Verification**: Verify "Development Setup" section exists in README.md.
- [ ] T033 Profile `code/data/download_nist.py` and reduce memory usage. **Target**: < 2GB. **Tool**: `memory_profiler`. **Command**: `python -m memory_profiler --line-by-line code/data/download_nist.py` using `data/processed/corrosion_dataset.parquet` (first 5k rows). **Verification**: Run memory profiler and confirm reduction.
- [ ] T034a Create benchmark script: Implement `code/utils/benchmark.py` to load a subset of `data/processed/corrosion_dataset.parquet` and measure load time. **Verification**: Script must accept `--rows` argument and exit 0 on success.
- [ ] T034 Optimize data loading in `code/data/preprocess.py` to complete in < 30 seconds on 10k rows. **Benchmark**: Use `code/utils/benchmark.py` to load `data/processed/corrosion_dataset.parquet` (first 10k rows). **Verification**: Run benchmark script and confirm time < 30s.
- [X] T035 [P] Additional unit tests for edge cases (pH > 14, pH < 0) in `tests/unit/`
- [X] T036 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Depends on US1 completion (requires processed data)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained model)

### Within Each User Story

- Implementation (Producer) MUST exist before Tests (Consumer) can be written to fail.
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
# Launch all models for User Story 1 together:
Task: "Implement download_nist.py with retry logic"
Task: "Implement preprocess.py for encoding and filtering"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥500 records, no leakage, ≥10 alloys)
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling) - *Can start only after US1 data is ready*
 - Developer C: User Story 3 (Interpretability) - *Can start only after US2 model is ready*
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
- **Critical Constraint**: Do not use synthetic data. If NIST-IR-8200 yields <500 records, the pipeline MUST halt.
- **Critical Constraint**: All models must run on CPU-only GitHub Actions runners (no CUDA, no low-bit quantization).
- **Critical Constraint**: Split strategy MUST be Leave-One-Specific-Alloy-Out (LOSO) as per Spec FR-004/FR-012. The Plan's GroupKFold strategy is overridden by the Spec; update the Plan to reflect this.
- **Critical Constraint**: ASTM G tolerance comparison is mandatory; if standard is ambiguous, use the default 150 mV (Spec Assumptions).
- **Critical Constraint**: Statistical significance testing must use "one-sample permutation test" as per Spec FR-008.