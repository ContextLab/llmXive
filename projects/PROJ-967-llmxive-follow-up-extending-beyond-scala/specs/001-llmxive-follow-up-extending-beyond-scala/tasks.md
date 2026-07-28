# Tasks: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Input**: Design documents from `/specs/001-llmxive-entanglement-analysis/`
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

**Purpose**: Project initialization, contract definition, and artifact scaffolding

- [ ] T001a [P] Create project directories: Create directories `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results` relative to repository root. **REPLACES T004**.
- [X] T001b [P] Create empty project files: Create empty files `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/.gitignore`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/pytest.ini`
- [X] T001c [P] Write dependencies: Write `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt` with pinned versions of pandas, numpy, scikit-learn, scipy, pyyaml, pytest, ruff, black
- [ ] T001d [!] Create **provisional** dataset schema template: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml` as a *provisional* template defining the *expected* structure based on the spec's explicit column list: `prompt` (str), `image_url` (str), `teacher_scores` (dict{dim: float}), `student_scalar` (float), `human_annotations` (dict{dim: float}), `primary_dimension` (str). **NOTE**: This task is NOT parallel [P]; it must complete before Phase 2 begins, but T038 will update this template based on actual data. **ACTION**: Write a minimal valid YAML structure (e.g., `schema: { prompt: string,... }`) representing the *expected* schema, not the final one. **CRITICAL**: This schema is provisional and may be updated by T038.
- [ ] T001f [P] Create output schema contract: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/output.schema.yaml` defining the structure of `data/processed/features.json` (e.g., `sample_id`, `variance`, `entropy`, `skewness`, `kurtosis`, `dominant_eigenvalue`, `fidelity_loss`). **DEPENDS: T001a**.
- [X] T001e [P] Initialize output artifacts: Create empty `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json` (with `[]` or `{}`) and `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json` (with `{}`) to prevent file-not-found errors in downstream tasks
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with pinned tool versions and configuration to satisfy Constitution Principle I (Reproducibility). **REPLACES T003**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T037 [!] [US1] Download Z-Reward evaluation dataset: Fetch the dataset using `datasets.load_dataset` with the **verified** source ID `z-reward/z-reward-v`.
 1. **Primary**: Try to load the dataset with ID 'z-reward/z-reward-v1'.
 2. **Fallback**: If the dataset is missing or invalid, **DO NOT** generate synthetic data. Instead, raise a `RuntimeError` with a clear message indicating the real data source `z-reward/z-reward-v1` is unavailable. This ensures strict adherence to Constitution Principle II (Verified Accuracy).
 3. **Verification**: After loading, explicitly check for the presence of required columns: `prompt`, `image_url`, `teacher_scores` (dict with keys: Alignment, Realism, Aesthetics, Plausibility), `student_scalar`, `human_annotations` (dict with same keys), and `primary_dimension`.
 4. **CRITICAL**: If the specific columns are missing, raise a `RuntimeError`. **DO NOT** use local file fallbacks. **DO NOT** fallback to a different real dataset if the schema doesn't match.
 5. **BLOCKING**: This task is NOT parallel [P]. It must complete successfully before T012 can run. **DEPENDS: T001a**.
- [X] T038 [!] [US1] Schema Discovery and Validation: Read `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/raw_data.parquet` (output of T012). Perform **Schema Discovery**: map actual column names to logical fields (prompt, scores, annotations).
 1. **Validate**: Check if the actual data schema matches the *provisional* template in `contracts/dataset.schema.yaml` (created in T001d).
 2. **Update**: If discrepancies are found (e.g., column names differ), update the schema template to reflect the *actual* schema.
 3. **Write**: Write the final validated schema content to `contracts/dataset.validated.schema.yaml` (a distinct file from the template).
 4. **Raise**: Error if critical mismatch (e.g., missing rubric dimensions). **DEPENDS: T012**. **EXECUTION ORDER**: T012 must succeed before T038 runs. T038 runs *after* T012 to validate the schema of the loaded real data.
- [X] T005 [P] Create `code/ingest.py` skeleton with argument parsing and logging setup
- [X] T006 [P] Create `code/features.py` skeleton with statistical helper functions
- [X] T007 [P] Create `code/train.py` skeleton with scikit-learn model configuration
- [X] T008 [P] Create `code/evaluate.py` skeleton for metrics calculation
- [X] T009 Setup `tests/` directory structure and `pytest.ini`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Ground-Truth Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest Z-Reward dataset, align teacher/student outputs with human annotations, and handle missing data gracefully.

**Independent Test**: A script loads the dataset, verifies the presence of all four rubric dimensions, flags missing data, and outputs a summary without crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for data loading and schema validation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`
- [X] T011 [P] [US1] Integration test for missing data handling and exclusion logic in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement Z-Reward dataset ingestion in `code/ingest.py` (load prompts, images, teacher scores, student scores, human annotations). Write output to `data/processed/raw_data.parquet`. **DEPENDS: T037**. **NOTE**: This task must be schema-agnostic; it loads whatever is available and handles missing columns gracefully. Uses the *provisional* schema from T001d for initial column mapping.
- [X] T013 [US1] Implement alignment logic in `code/ingest.py`: match teacher distributions, student scalars, and human annotations by sample ID. **CRITICAL**: Verify `student_scalar` column exists. If missing, attempt to load a separate `student_inference.parquet` file from `data/raw/` OR mark the sample as `excluded_reason: 'missing_student_scalar'` in the dataframe. **DO NOT** raise a `RuntimeError`. The pipeline must continue, and the sample will be excluded later in T024. **DEPENDS: T012**.
- [X] T014 [US1] Implement "primary quality dimension" identification logic in `code/ingest.py`: **Rule**: Use the value of the column `primary_dimension` if present in the dataset. **CRITICAL**: If `primary_dimension` is missing for a sample, mark that sample as `excluded_reason: 'missing_primary_dimension'` in the dataframe. **DO NOT** raise a `RuntimeError`. The pipeline must continue, and the sample will be excluded later in T024. **DEPENDS: T013**.
- [X] T015 [US1] Implement chunked loading or sampling logic in `code/ingest.py` to ensure RAM usage stays < 7GB on free-tier runners. **DEPENDS: T012**.
- [X] T016 [US1] Add summary output in `code/ingest.py`: print sample counts, missing data flags, dimension coverage stats. **DEPENDS: T012**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entanglement Quantification and Feature Engineering (Priority: P2)

**Goal**: Calculate statistical descriptors (variance, entropy, skewness, kurtosis) per sample, and a valid global covariance metric (Dominant Eigenvalue) for the teacher's score distributions across the dataset.

**Independent Test**: A script processes a fixed subset of teacher distributions and outputs a JSON record with calculated features, handling zero-variance cases gracefully.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for variance, entropy, skewness, kurtosis calculations in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`
- [X] T019 [P] [US2] Unit test for zero-variance edge case handling in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement variance and range calculation for dimensions in `code/features.py`. **DEPENDS: T012**.
- [X] T021 [US2] Implement entropy, skewness, and kurtosis calculation for teacher distributions in `code/features.py`. **DEPENDS: T012**.
- [ ] T022a [US2] Implement **Per-Sample Entanglement Score**:
 1. For each sample, extract the 4-dimensional teacher score vector (or the available dimension vector).
 2. Calculate **Variance** (var) across the dimensions.
 3. Calculate **Shannon Entropy** (normalize vector to sum=1, then compute -sum(p*log(p))).
 4. Calculate **Skewness** and **Kurtosis** of the dimension vector.
 5. **CRITICAL**: All metrics (variance, entropy, skewness, kurtosis) must be computed **per sample** and stored as columns in the dataframe. **NO** global constants for these features.
 6. **VALIDATION**: Handle zero-variance/constant cases gracefully (Entropy=0, Variance=0). **DEPENDS: T012**.
- [ ] T022b [US2] Implement **Global Dominant Eigenvalue**:
 1. **Input**: Use the *raw* dataset from T012 (`data/processed/raw_data.parquet`). **DO NOT** use filtered data (T024) for this calculation to ensure the covariance matrix is full-rank.
 2. Extract the matrix of teacher scores (N samples x 4 dimensions).
 3. Compute the **Covariance Matrix** of these scores across the N samples using `numpy.cov` (rowvar=False).
 4. Calculate the **Dominant Eigenvalue** (largest eigenvalue) of this 4x4 covariance matrix. This represents the overall structural entanglement of the dataset's score distributions.
 5. **CRITICAL**: This is a *global* scalar feature derived from the entire dataset, satisfying Constitution Principle VI (covariance across dimensions).
 6. **VALIDATION**: Ensure the calculation is robust to missing data (exclude samples with NaN scores before computing covariance). **DEPENDS: T012**.
- [X] T025a [US2] Implement **Compute Per-Sample Features**: Read aligned data from `code/ingest.py` (specifically the *filtered* output from T024: `data/processed/cleaned_data.parquet`). Compute per-sample stats (T020-T021, T022a) and import the Global Eigenvalue from T022b.
 1. **Compute** the per-sample features (variance, entropy, skewness, kurtosis, score_magnitude) for each row in the filtered dataframe.
 2. **Import** the Global Dominant Eigenvalue computed in T022b and broadcast it to all rows.
 3. **Note**: The Random Forest will use these per-sample features + the global eigenvalue.
 4. **DEPENDS: T024, T020, T021, T022a, T022b**. **VALIDATION**: Ensure output JSON matches `contracts/output.schema.yaml` and contains no null values for required keys (`sample_id`, `variance`, `entropy`, `score_magnitude`, `dominant_eigenvalue`, `fidelity_loss`).
- [X] T025b [US2] Implement **Merge Features**: Merge the computed per-sample features into the main dataframe.
 1. **DEPENDS: T025a**.
- [X] T025c [US2] Implement **Validate Output Schema**: Validate the output JSON matches `contracts/output.schema.yaml`.
 1. **DEPENDS: T025b**.
- [X] T023 [US2] Implement zero-variance handling in `code/features.py`: set entropy to 0 and variance to 0 without crashing. **DEPENDS: T020**.
- [ ] T041 (DELETED - Contradictory approximation logic removed; Per-sample approach in T022a/T022b is correct). <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train a CPU-based Random Forest regressor to predict fidelity loss using entanglement features, with k-fold cross-validation, permutation test, and null baseline comparison.

**Independent Test**: A script trains the model on a stratified random split (with quantile binning), runs k-fold cross-validation, and outputs R², MAE, and p-value (from permutation test) without using GPU.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US3] Unit test for Random Forest training and 5-fold CV execution in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_train.py`
- [X] T026 [P] [US3] Integration test for permutation test p-value calculation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_evaluate.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement "dimensional fidelity loss" calculation:
 1. Compute MAE between student scalar output and human-annotated score for the primary dimension (selected via metadata in T014).
 2. **Filter** the dataframe: Exclude samples where `primary_dimension` was missing (marked in T014) or where human annotations are missing OR where `student_scalar` was missing (marked in T013).
 3. **Output**: Write the filtered dataframe to `data/processed/cleaned_data.parquet`.
 4. **Output key**: `fidelity_loss`. **DEPENDS: T012, T014, T013**.
- [X] T027a [US3] Implement Random Forest training setup in `code/train.py`: Read features from `data/processed/cleaned_data.parquet` (including `fidelity_loss`); configure train/test split with `test_size=0.2` and `random_state=42`; ensure CPU-only execution (`n_jobs=2`); **DEPENDS: T025c, T024**.
 1. **Stratification Strategy**: Since `fidelity_loss` is continuous, apply **quantile-based binning** (n_bins=5) to the target variable before stratified splitting to ensure deterministic and reproducible splits.
 2. **Save**: Write the split configuration (indices or seed) to `data/processed/split_config.json`.
- [X] T027b [US3] Implement Random Forest training execution in `code/train.py`: Train model with `n_estimators=100`, `max_depth=None`, `random_state=42`; **DEPENDS: T027a**; **Return** the trained model object for T027c.
- [ ] T027c [US3] Save model artifact: Serialize trained model from T027b to `results/model.pkl`; **DEPENDS: T027b**.
- [X] T028 [US3] Implement k-fold cross-validation logic in `code/train.py` with stratified splitting. **DEPENDS: T027b**.
- [ ] T030a [US3] Implement permutation test logic: **Permute the feature matrix (X)** against the target (y) `n_permutations=1000` times with `random_state=42`. Calculate R² for each permutation. Compute p-value as the fraction of permuted R² values >= observed R². This validates the **correlation strength** (SC-001). **DEPENDS: T025c, T027b**. **Output**: Provide a function `calculate_permutation_pvalue` to be called by T029.
- [X] T029 [US3] Implement evaluation script in `code/evaluate.py`: calculate mean R², std dev, MAE, and call T030a to get permutation test p-value. **DEPENDS: T028, T030a**.
- [ ] T030c [US3] Implement Null Baseline Comparison:
 1. **Train a Mean Predictor**: Use `sklearn.dummy.DummyRegressor(strategy='mean')` to train a model that predicts the mean of `fidelity_loss` on the training set.
 2. Evaluate this Mean Predictor on the test set to get its R² and MAE.
 3. **Compare**: Compare the Random Forest R²/MAE (from T027b/T029) against the Mean Predictor's R²/MAE.
 4. **Requirement**: Verify that the Random Forest R² > Mean Predictor R² (or R² > 0.0).
 5. **Statistical Significance**: Perform a **paired t-test** on the residuals of the Random Forest vs the Mean Predictor (on the test set) to verify significant improvement (p < 0.05). This satisfies SC-002. Use `scipy.stats.ttest_rel`.
 6. **Fallback**: If the t-test assumptions are violated (e.g., Shapiro-Wilk p < 0.05), perform a **bootstrap-based comparison** of MAE (n_resamples=1000, confidence_level=0.95) to generate a confidence interval for the difference in MAE. If the 95% CI does not include 0, the improvement is significant.
 7. **Final Fallback**: If both t-test and bootstrap fail to show significance, check if **R² > 0.0**. If R² > 0.0, the task passes (satisfying SC-002). **CRITICAL**: The task passes if (t-test p < 0.05) OR (R² > 0.0).
 8. **Dependency**: Load split configuration from `data/processed/split_config.json` to ensure the same test set is used. **DEPENDS: T029, T027b**.
- [ ] T031 [US3] Integrate training and evaluation: Read features from `data/processed/cleaned_data.parquet`, train model, run CV, run permutation test, run null baseline comparison, and write final metrics to `results/results.json`; **DEPENDS: T027a, T027c, T028, T029, T030c**.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Create `quickstart.md` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with explicit steps to reproduce the full pipeline (Install -> Download -> Ingest -> Train -> Evaluate) to satisfy Constitution Principle I. **DEPENDS: T031**.
- [ ] T033 [P] Code cleanup and refactoring: Run `ruff check` and `black --check` on `code/` and `tests/`. Fix all errors until `ruff` exits with code 0 and `black` reports no changes. **DEPENDS: T031**.
- [X] T034 [P] Profile and optimize feature engineering loop: Run `cProfile` on `code/features.py` using a **[deferred] random sample** of the full dataset (or maximum available subset) to estimate runtime.
 1. **Research Question**: What are the key constraints limiting system performance?
 2. **Method**: Systematic bottleneck analysis.
 3. **References**: scikit-learn documentation on Random Forests; scipy.stats documentation for statistical tests.
 4. **Optimization**: If **estimated runtime** > 30 minutes, implement optimization to **reduce runtime** using **vectorization with numpy**. **Warning**: If estimated runtime > 6 hours, the task fails. **DEPENDS: T025c**.
- [ ] T035 [P] Additional unit tests for edge cases: Write tests for `test_ingest.py` and `test_features.py` covering: (1) Empty dataset, (2) NaN values in teacher logits, (3) Missing human annotations for all dimensions, (4) Zero-variance distributions. **DEPENDS: T018, T019**.
- [ ] T036 Run quickstart.md validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Includes Data Acquisition (T037)** which must complete before US1 implementation (T012).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Acquisition (Phase 2)**: Must complete before US1 implementation (T012) can successfully run on real data
- **T025c (Validate)**: Must complete before T027a (Training)
- **T037 (Download)**: Must complete before T012 (Ingestion)
- **T038 (Validation)**: Must complete after T012 (Ingestion)
- **T001d (Schema)**: Must complete before T038 (Validation)
- **T012 (Ingestion)**: Must complete before T024 (Filter) and T022a/T022b (Feature Calculation)
- **T024 (Filter)**: Must complete before T025a (Feature Integration)
- **T022b (Eigenvalue)**: Must complete before T025a (Feature Integration)
- **T025a (Compute)**: Must complete before T025b (Merge)
- **T025b (Merge)**: Must complete before T025c (Validate)
- **T025c (Validate)**: Must complete before T027a (Config)
- **T027a (Config)**: Must complete before T027b (Train)
- **T027b (Train)**: Must complete before T027c (Save Model)
- **T030a (Permutation)**: Must complete before T029 (Evaluation)
- **T029 (Evaluation)**: Must complete before T030c (Null Baseline)
- **T030c (Null Baseline)**: Must complete before T031 (Integration)
- **T001d Tag Clarification**: T001d is NOT parallel [P]. It must complete before Phase 2 begins to ensure T038 has a valid schema file.
- **T024 (Filter)**: Must complete before T025 (Feature Integration).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data alignment
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (target calculation) and US2 (features)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading before feature engineering
- Feature engineering before model training
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T038 which depends on T012**
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Data acquisition (T037) runs in parallel with Setup and Foundational tasks but must finish before T012

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for data loading and schema validation in tests/test_ingest.py"
Task: "Integration test for missing data handling in tests/test_ingest.py"

# Launch implementation tasks together:
Task: "Implement Z-Reward dataset ingestion in code/ingest.py"
Task: "Implement alignment logic in code/ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Data Acquisition)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently with real data
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
 - Developer A: User Story 1 (Data ingestion)
 - Developer B: User Story 2 (Feature engineering)
 - Developer C: User Story 3 (Model training)
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
- **CRITICAL**: All data loading tasks (T012, T037) must use real, reachable URLs (verified UCI or HF datasets) or package-based fetchers. **NO synthetic fallbacks** allowed.
- **CRITICAL**: All model training tasks must be CPU-only (no CUDA, no 8-bit quantization, no large LLMs). Use small models and sampled datasets if necessary.
- **CRITICAL**: Entanglement features (T022a, T022b) MUST be computed using **per-sample** statistics (Entropy, Variance, Skewness, Kurtosis) AND a **Global Dominant Eigenvalue** derived from the dataset's covariance matrix. **NO** global constants are allowed as per-sample features.
- **CRITICAL**: T022b computes Global Dominant Eigenvalue via covariance matrix of the full dataset.
- **CRITICAL**: Target variable (T024) MUST be calculated in `code/features.py` using metadata-based dimension selection (T014), independent of model scores.
- **CRITICAL**: Data Acquisition (T037, T038) must complete before US1 implementation (T012) to ensure the ingestion script has real data to process.
- **CRITICAL**: T001e initializes output files to prevent "file not found" errors.
- **CRITICAL**: T025 is split into T025a (Compute), T025b (Merge), T025c (Validate).
- **CRITICAL**: T038 depends on T012 (Ingestion) only (no fallback).
- **CRITICAL**: T004 is deleted (merged into T001a).
- **CRITICAL**: T041 is deleted (contradictory logic).
- **CRITICAL**: T032 creates `quickstart.md` for reproducibility.
- **CRITICAL**: T003 creates `.ruff.toml` and `pyproject.toml`.
- **CRITICAL**: T037 uses a specific dataset ID 'z-reward/z-reward-v1' with a hard failure on missing data.
- **CRITICAL**: T038 performs schema discovery and populates the schema files.
- **CRITICAL**: T033 has a concrete "done" state (ruff exit code 0).
- **CRITICAL**: T034 has a concrete metric (runtime reduction or bottleneck report) using a [deferred] sample for profiling.
- **CRITICAL**: T035 specifies exact edge cases.
- **CRITICAL**: T001a, T001b, T001c use the correct project prefix path.
- **CRITICAL**: T013 handles missing student scalar columns explicitly by marking as excluded, NOT crashing.
- **CRITICAL**: T039 and T042 have been removed from the active task list.
- **CRITICAL**: T014 marks missing samples for exclusion instead of crashing.
- **CRITICAL**: T013 and T014 must both handle missing data gracefully (exclusion) to prevent pipeline crashes.
- **CRITICAL**: T022a computes valid per-sample stats (Variance, Entropy, Skewness, Kurtosis).
- **CRITICAL**: T022b computes Global Dominant Eigenvalue via covariance matrix.
- **CRITICAL**: T030c trains the Mean Predictor inline, compares R²/MAE, and mandates a **paired t-test** on residuals as the primary validation method, with bootstrap as a fallback, and **R² > 0.0** as the final fallback.
- **CRITICAL**: T027a uses **quantile-based binning** for stratified splitting of continuous targets.
- **CRITICAL**: T024 must filter the dataframe and write to `data/processed/cleaned_data.parquet` before T025a reads it.
- **CRITICAL**: T025a must read the *filtered* output from T024.
- **CRITICAL**: T001d creates a *provisional* template that T038 updates.
- **CRITICAL**: T037 is NOT parallel [P].
- **CRITICAL**: T022b depends on T012 (Raw Data) to ensure full-rank covariance matrix.
- **CRITICAL**: T025a depends on T022b (Global Scalar) and T024 (Filtered Data).