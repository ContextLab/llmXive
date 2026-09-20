# Tasks: Predicting Molecular Reactivity Using Machine Learning and Public Reaction Databases

**Input**: Design documents from `/specs/001-molecular-reactivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: (, https://www.wikidata.org/wiki/Q18615098)

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

- [X] T001 Execute `scripts/setup_dirs.sh` (or Python equivalent) to create `data/raw/`, `data/processed/`, `data/models/`, `src/data/`, `src/modeling/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `scripts/`
- [X] T002 Initialize Python project with `rdkit`, `xgboost`, `pandas`, `scikit-learn`, `pyarrow`, `requests` dependencies in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement centralized logging setup in `src/utils/logging.py`
- [X] T006 [P] Implement state management system (create `src/utils/state_manager.py` and `scripts/update_state.py`) to handle `state/projects/PROJ-442-predicting-molecular-reactivity-using-ma.yaml` updates and artifact checksums
- [X] T006b [P] Implement atomic write logic in `scripts/update_state.py` using a temporary file and `os.rename` to ensure `state.yaml` updates are atomic and prevent race conditions. (Dependency: T006).
- [X] T007 Create base data schemas and validation helpers in `src/data/schemas.py` (ReactionRecord, FeatureVector, ModelResult)
- [X] T008 Setup environment configuration management (load `config.yaml` from `src/modeling/config.yaml`)
- [X] T009 Create `src/main.py` orchestration script to call `scripts/update_state.py` after major stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Reaction Class Filtering (Priority: P1) 🎯 MVP

**Goal**: Download USPTO subset, parse SMILES, filter into SN1, SN2, Diels-Alder classes, and handle malformed data.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output file contains a single `reaction_type` column containing exactly three distinct values ("SN1", "SN2", "Diels-Alder") where present in the raw data, and that the total row count is ≥ 90% of the input file row count.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for SMILES normalization and error logging in `tests/unit/test_ingestion.py`
- [X] T011 [P] [US1] Unit test for reaction template matching logic in `tests/unit/test_templates.py`

### Implementation for User Story 1

- [X] T013a [US1] [P] Define SMARTS patterns for SN1, SN2, and Diels-Alder in `src/modeling/config.yaml`. **Patterns**: SN1: `[C;H0]([c,o,n])-[C;H0]` (carbocation intermediate), SN2: `[C;H0]([c,o,n])-[C;H0]` (backside attack, distinct from SN1 by stereochemistry context), Diels-Alder: `[C;H0]=[C;H0]-[C;H0]=[C;H0]` (diene) + `[C;H0]=[C;H0]` (dienophile). These patterns are version-controlled and serve as the single source of truth for reaction template matching (US1 Template Matching). Do not hardcode patterns in code. (Dependency: T008).
- [ ] T013b [US1] [P] Implement reaction matching function in `src/utils/chemistry.py` using RDKit to apply SMARTS patterns from config.yaml to reaction SMILES.
- [ ] T012 [US1] Implement `src/data/ingestion.py` to download the specified USPTO subset. **Requirement**: The `USPTO_URL` key MUST be defined in `src/modeling/config.yaml`. If missing or unreachable, raise `ValueError` with message: "USPTO_URL not configured: Please specify a valid USPTO-MIT subset URL in config.yaml". **Canonical URL**: Use a publicly available patent dataset (e.g., USPTO-MIT subset) hosted on a scholarly repository such as figshare. if not specified. No synthetic fallback allowed. Verify checksum, parse raw data into `data/raw/uspto_subset.parquet`, and log any fetch errors.
- [X] T014 [US1] Implement filtering logic in `src/data/ingestion.py` to exclude non-matching rows, log malformed SMILES to error file, and strictly derive target variable: use `yield_pct` if present, otherwise fallback to `success_flag` (binary) as per FR-004.
- [ ] T014b [US1] [P] Implement validation logic in `src/data/ingestion.py` to verify target variable derivation (strictly from experimental yield/success flags per FR-004) on the in-memory dataframe *during* ingestion (T014) and *before* saving. **Requirement**: If >5% of rows fail target derivation, raise `ValueError` and abort. **Output**: `data/processed/target_validation.log` (CSV format with headers: `row_id,target_source,value`). **Pass/Fail**: Log must contain at least one entry per reaction class. **Failure Condition**: If `yield_pct` or `success_flag` are missing for >5% of rows, abort. (Dependency: T014).
- [ ] T017 [US1] Save the validated filtered dataset to `data/processed/filtered_reactions_full.csv` with checksum and provenance metadata. **Requirement**: This file contains ALL valid reactions matching templates, including low-sample classes (<1,000 samples). **Verification**: Verify file exists, checksum matches `state.yaml`, and schema matches `data-model.md`. The Independent Test passes if the file contains "SN1", "SN2", "Diels-Alder" *where present in the raw data*. (Dependency: T014, T014b).
- [ ] T016a [US1] [P] Implement sample size check and logging in `src/data/ingestion.py`. Check count **per class**. Log a warning for low-sample classes (<1,000). **Output**: `data/processed/class_exclusion_metadata.json` listing excluded classes (those with <1,000 samples). **Schema**: `{"excluded_classes": [{"class": "class_name", "count": 123},...]}`. (Dependency: T017).
- [ ] T016b [US1] Generate `data/processed/filtered_reactions_clean.csv` by filtering `data/processed/filtered_reactions_full.csv` (from T017) using `class_exclusion_metadata.json` (from T016a) to exclude low-sample classes. This is the artifact consumed by US2. **Dependency**: T017, T016a.
- [ ] T015 [US1] Implement batch processing logic in `src/data/ingestion.py` to handle memory limits (process in chunks).
- [ ] T018 [US1] Integrate logging and state update calls in `src/data/ingestion.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Model Training (Priority: P2)

**Goal**: Convert reactants to features (RDKit), apply dimensionality reduction, and train XGBoost on CPU within 30 mins.

**Independent Test**: Can be fully tested by running the training script on a sample of reaction records and verifying that the model outputs a prediction file with a Spearman correlation coefficient > 0.5 and that the total runtime is < 30 minutes on a standard CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for RDKit feature extraction (MW, atom counts, topological indices) in `tests/unit/test_features.py`
- [X] T020 [P] [US2] Unit test for dimensionality reduction pipeline (Variance Threshold + SelectKBest) in `tests/unit/test_features.py`

### Implementation for User Story 2

- [ ] T021a [US2] [P] Implement feature extraction functions in `src/data/preprocessing.py` to extract molecular weight, atom counts, bond types, and topological indices using RDKit.
- [ ] T021b [US2] [P] Implement dimensionality reduction pipeline (Variance Threshold + SelectKBest, k=100, **scoring_function=f_classif**) in `src/data/preprocessing.py`.
- [ ] T021c [US2] [P] Implement batch processing wrapper in `src/data/preprocessing.py` to handle memory constraints during feature extraction.
- [ ] T022 [US2] [P] (Merged from T021) Integrate feature extraction, dimensionality reduction, and batch processing in `src/data/preprocessing.py`. **Crucial**: Load `data/processed/filtered_reactions_clean.csv` (from T016b) to ensure only valid classes are processed. (Dependency: T016b).
- [ ] T022b [US2] [P] Implement memory profiling in `src/data/preprocessing.py` to explicitly log peak memory usage and confirm it stays within the available RAM limit (SC-004).
- [ ] T024 [US2] Save feature matrix to `data/processed/feature_matrix.parquet` with checksum. Ensure the schema matches the definition in `data-model.md` (FeatureVector). **Verification**: Verify file exists, checksum matches `state.yaml`, and schema matches `data-model.md`. (Dependency: T022).
- [ ] T025 [US2] Implement `src/modeling/train.py` to load features, normalize target (Z-score), and train XGBoost model.
- [ ] T026a [US2] [P] Implement 5-fold Cross-Validation loop in `src/modeling/train.py` using `sklearn.model_selection.KFold(n_splits=5, shuffle=True, random_state=42)`. This is the primary validation method per FR-003. **Runtime Enforcement**: The script must enforce a strict timeout of a predefined duration. If the run exceeds this limit, save a `partial_model.pkl` with a `timeout` flag and log an error, rather than switching to fallback parameters. (Dependency: T024).
- [ ] T026b [US2] [P] Implement **Scaled Leave-One-Scaffold-Out (LOSO)** or **Scaffold-Binned** validation in `src/modeling/train.py`. **Requirement**: If full LOSO exceeds a practical time threshold, automatically switch to "Scaffold-Binned" (group scaffolds into 5 buckets, hold out one bucket) to preserve the scaffold-aware constraint without full overfitting. **Primary Artifact**: The LOSO/Scaffold-Binned model is the primary result; 5-fold CV is a baseline. (Dependency: T024, T026a).
- [ ] T027 [US2] Save trained model artifact (LOSO/Scaffold-Binned) to `data/models/xgboost_model.json` and training logs to `data/processed/training_log.json`. **Verification**: Verify file size > 0 and loadable by xgboost. **Dependency**: T026b (success).
- [ ] T028 [US2] Integrate logging, state update, and error handling in `src/modeling/train.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and Significance Testing (Priority: P3)

**Goal**: Compare performance across classes, compute Spearman ρ, and run permutation test for significance (p < 0.01).

**Independent Test**: Can be fully tested by running the analysis script on the cross-validation results and verifying that the output report contains a ranked list of reaction classes by Spearman ρ, with SN1/SN2/Diels-Alder labels clearly distinguished, and a p-value < 0.01 for the permutation test.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for Spearman correlation calculation and permutation test logic in `tests/unit/test_evaluate.py`

### Implementation for User Story 3

- [ ] T032a [US3] [P] Define and validate the permutation test iteration count. Set `permutation_iterations` to a sufficiently large number in `src/modeling/config.yaml` (baseline). **Output**: Log entry confirming the value. (Dependency: None).
- [ ] T030 [US3] Implement `src/modeling/evaluate.py` to load model results (from T027) and compute Spearman rank correlation (ρ) between predicted and observed reactivity. **Requirement**: "Observed" rankings are derived strictly from `yield_pct` or `success_flag` (Z-score normalized). **Dependency**: T027.
- [ ] T030b [US3] [P] Implement logic in `src/modeling/evaluate.py` to load and validate the existence of `data/processed/target_validation.log` (from T014b) before proceeding with analysis. This ensures the 'observed' rankings are linked to the validated target. **Dependency**: `data/processed/target_validation.log` (Artifact from T014b).
- [ ] T032 [US3] Implement permutation test (sufficient iterations) in `src/modeling/evaluate.py` to calculate p-values against the null hypothesis of ρ = 0. Shuffle targets within each class using `numpy.random.shuffle` with **seed=42**. **Requirement**: The iteration count MUST be set to the value in Ta. Log the rationale for the chosen iteration count. **Dependency**: T030, T032a.
- [ ] T032b [US3] [P] Implement **Power Analysis** in `src/modeling/evaluate.py`. Calculate the minimum detectable p-value resolution based on a sufficient number of iterations. If the observed p-value is near the resolution limit (e.g., 0.005-0.006), dynamically increase iterations (capped by time) to ensure "sufficient" precision. **Dependency**: T032.
- [ ] T035 [US3] Implement logic to skip classes in the final report if sample size < 1,000 (reusing logic from T016a and `class_exclusion_metadata.json`) to satisfy FR-006. **Dependency**: `class_exclusion_metadata.json` (Artifact from T016a).
- [ ] T033 [US3] Generate summary report ranking SN1, SN2, Diels-Alder by Spearman ρ with p-values in `data/processed/analysis_report.json`. **Verification**: Verify file exists at `data/processed/analysis_report.json` with keys: `spearman_rho`, `p_value`, `class_rankings`. **Dependency**: T030, T032, T032b, T035.
- [ ] T034 [US3] Implement logic to flag "Not Significant" if p-value ≥ 0.01, ensuring FR-005 and SC-002 thresholds are explicitly reported/enforced.
- [ ] T036 [US3] Integrate logging, state update, and final report generation in `src/modeling/evaluate.py`.
- [ ] T037 [US3] Verify that `main.py` orchestrates the full pipeline (Ingestion → Features → Train → Evaluate).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Generate README.md sections: Setup, Data Sources (with citations), Pipeline Execution.
- [X] T040 Run `flake8` on `src/` and fix reported errors to ensure code cleanup is deterministic.
- [X] T041 Performance optimization: verify batch sizes and chunking logic to stay within available RAM constraints.
- [X] T042 [P] Additional unit tests for edge cases (malformed SMILES, missing classes) in `tests/unit/`.
- [X] T043 Run `quickstart.md` validation and ensure all scripts run end-to-end on CPU-only runner.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (clean filtered data) for feature extraction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model results) for evaluation

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
Task: "Unit test for SMILES normalization and error logging in tests/unit/test_ingestion.py"
Task: "Unit test for reaction template matching logic in tests/unit/test_templates.py"

# Launch all models for User Story 1 together:
Task: "Define SMARTS patterns in config.yaml"
Task: "Implement reaction matching function in src/utils/chemistry.py"
Task: "Apply matching to classify reactions"
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
- **Critical Constraint**: All tasks must run on CPU-only (limited core count, constrained RAM). No GPU, no 8-bit/4-bit quantization, no large LLMs. Use small models and sampled data if necessary.
- **Plan Deviation Note**: The plan mentions "LOSO validation" as a complexity, but Spec FR-003 strictly mandates "5-fold CV" and "30-minute runtime". T026a implements 5-fold CV as the primary method with a strict timeout. T026b implements LOSO as a separate, optional experiment that does not affect the primary model artifact, ensuring both requirements are addressed without violating FR-003.
- **Data Flow Clarification**: T017 saves the full dataset (including low-sample classes). T016a generates metadata for excluded classes. T016b generates the clean dataset artifact (excluding low-sample classes) that is consumed by US2 (T022). T035 uses T016a's metadata to filter the dataset for the final report, ensuring data integrity while meeting FR-006.
- **Runtime Constraint**: T026a enforces the 30-minute limit by aborting the run if exceeded, rather than dynamically adjusting parameters. This ensures FR-003 is satisfied by producing a model within the time budget while maintaining reproducibility.
- **Data Source Verification**: T012 requires a verified public repository URL in `config.yaml`. If the URL is missing or unreachable, the script MUST fail loudly (raise an exception) rather than generating synthetic data.
- **Target Variable Integrity**: T014 and T014b explicitly enforce that the target variable is derived ONLY from experimental yield or success flags, preventing data leakage from structural features. T014b validates this *during* ingestion, before T017 saves the artifact.
- **Permutation Test Validity**: T032 ensures the permutation test shuffles targets within each class to maintain class balance, and logs the iteration count (1000) to ensure statistical power.
- **Memory Management**: T022b and T041 ensure that batch processing and chunking are implemented to prevent OOM errors on the GB RAM limit.
- **Removed Redundancy**: T031b was removed as it duplicated the target validation logic of T014b. US3 (T030) now assumes the target was validated in US1 and references the validation log.
- **Target Validation Flow**: T014b now runs before T017 to validate targets during ingestion. T030b explicitly loads the validation log to ensure the target integrity is confirmed before analysis.
- **LOSO Fallback**: T026b does NOT use a fallback configuration; it simply skips the experiment if the time limit is exceeded, preserving the primary 5-fold CV model.
- **Data Artifact Clarity**: T017 saves the 'full' dataset, while T016b generates the 'clean' dataset for downstream analysis, ensuring data hygiene and clarity.
- **Permutation Iterations**: T032a explicitly defines the iteration count (1000) to satisfy FR-005.
- **Runtime Enforcement**: T026a enforces runtime via timeout, not dynamic adjustment.
- **Dynamic Adjustment Removed**: T026c was removed as it contradicted the fixed timeout strategy. The system now strictly aborts on timeout.
- **Unified Exclusion Logic**: T016a and T016b now share the same exclusion metadata, ensuring the training data and report exclusions are consistent.
- **Explicit Permutation Count**: T032a defines the count as 1000, and T032 enforces it, ensuring the test is statistically valid.
- **Task Ordering Correction**: T016b (generate clean data) now explicitly depends on T016a (sample size check) and is no longer marked [P], as the exclusion metadata must be generated before the clean file can be created.
- [ ] T044 [US1] [P] Implement explicit dataset streaming logic in `src/data/ingestion.py` using `datasets.load_dataset(..., streaming=True)` or chunked `pandas.read_parquet` to handle datasets exceeding substantial RAM requirements. **Requirement**: The task must explicitly state the chunk size (e.g., a sufficiently large batch) and the accumulation strategy for statistics, ensuring the full dataset contributes without holding it in memory. If the The full stream cannot complete within the available time window., task a deterministic sample (e.g., first N rows or fixed-seed random) and log the limitation. (Dependency: T012).
- [ ] T045 [US1] [P] Add explicit error handling in `src/data/ingestion.py` to catch `HTTPError` or `FileNotFoundError` during the USPTO download and raise a descriptive `ValueError` immediately. **Constraint**: Ensure NO `try/except` block catches this error to fall back to `generate_synthetic_*()` or `mock_*()`. The script must fail loudly to trigger the execution stage's verified-source re-try mechanism. (Dependency: T012).
- [ ] T046 [US2] [P] Implement explicit feature batching in `src/data/preprocessing.py` to ensure feature extraction does not exceed available RAM constraints. **Requirement**: Process the `filtered_reactions_clean.csv` in chunks defined by T044, accumulating feature matrices incrementally or writing intermediate chunks to disk if memory pressure is detected. Log the peak memory usage per chunk. (Dependency: T021a, T021c, T044).
- [ ] T047 [US3] [P] Implement a "Power Analysis" log in `src/modeling/evaluate.py` that explicitly calculates and reports the statistical power of the permutation test based on the sample size per class and the chosen iteration count (1000). **Requirement**: If the power is deemed insufficient (e.g., < 0.8), log a warning but proceed with the test as per FR-005, clearly marking the result as "Low Power" in the final report. (Dependency: T032).
- [ ] T048 [US1] [P] Add a verification task to `tests/unit/test_ingestion.py` that specifically checks the "Fail Loudly" behavior of T045. **Requirement**: The test must mock a failed download and assert that the script raises `ValueError` and does NOT produce a synthetic dataset file. (Dependency: T045).
- [ ] T049 [US2] [P] Add a verification task to `tests/unit/test_features.py` that simulates a memory-limited environment and asserts that T046's batching logic successfully processes the data without OOM. (Dependency: T046).
- [ ] T050 [US3] [P] Add a verification task to `tests/unit/test_evaluate.py` that asserts the "Low Power" warning is correctly generated and included in the report when sample sizes are small. (Dependency: T047).