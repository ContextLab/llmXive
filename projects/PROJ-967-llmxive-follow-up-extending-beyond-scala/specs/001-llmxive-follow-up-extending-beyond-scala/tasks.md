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
- [ ] T001d [!] Create dataset schema contract: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml` defining the *expected* structure based on the spec's explicit column list: `prompt` (str), `image_url` (str), `teacher_scores` (dict{dim: float}), `student_scalar` (float), `human_annotations` (dict{dim: float}), `primary_dimension` (str). **HARD PREREQUISITE**: This task must complete before T038 (Schema Discovery) in Phase 2. **NOTE**: This task is NOT parallel [P]; it must complete before Phase 2 begins. **ACTION**: Write a minimal valid YAML structure (e.g., `schema: { prompt: string, ... }`) rather than an empty file.
- [ ] T001f [P] Create output schema contract: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/output.schema.yaml` defining the structure of `data/processed/features.json` (e.g., `sample_id`, `variance`, `entropy`, `skewness`, `kurtosis`, `dominant_eigenvalue`, `fidelity_loss`). **DEPENDS: T001a**.
- [X] T001e [P] Initialize output artifacts: Create empty `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json` (with `[]` or `{}`) and `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json` (with `{}`) to prevent file-not-found errors in downstream tasks
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with pinned tool versions and configuration to satisfy Constitution Principle I (Reproducibility). **REPLACES T003**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T037 [!] [US1] Download Z-Reward evaluation dataset: Fetch the dataset using `datasets.load_dataset` with a prioritized list of **verified, existing sources**. <!-- FIXED: Real dataset source -->
 1. **Primary**: Try `ucimlrepo` (Image Segmentation dataset) or a verified HuggingFace dataset (e.g., `HuggingFaceM4/coco_captions` with synthetic rubric generation if needed, or a specific verified subset) that contains image prompts and scores.
 2. **Verification**: After loading, explicitly check for the presence of required columns: `prompt`, `image_url`, `teacher_scores` (dict with keys: Alignment, Realism, Aesthetics, Plausibility), `student_scalar`, `human_annotations` (dict with same keys), and `primary_dimension`.
 3. **CRITICAL**: If the specific columns are missing or the dataset ID is invalid, **FAIL LOUDLY** with a `RuntimeError` indicating the missing data structure. **DO NOT** use synthetic fallbacks or local file fallbacks. **DO NOT** fallback to a local file.
 4. **BLOCKING**: This task is NOT parallel [P]. It must complete successfully before T038 can run. **DEPENDS: T001a**.
- [ ] T038 [!] [US1] Schema Discovery and Validation: Read `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml` (created in T001d as a minimal valid template). Inspect the downloaded data in `data/raw/z_reward_data.parquet`. Perform **Schema Discovery**: map actual column names to logical fields (prompt, scores, annotations).
 1. **Validate**: Check if the actual data schema matches the template in `contracts/dataset.schema.yaml`.
 2. **Update**: If discrepancies are found (e.g., column names differ), update `contracts/dataset.schema.yaml` to reflect the *actual* schema.
 3. **Write**: Write the final validated schema content to `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` (populating T001d/T001f).
 4. **Raise**: Error if critical mismatch (e.g., missing rubric dimensions). **DEPENDS: T037**. **EXECUTION ORDER**: T037 must succeed before T038 runs.
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

- [X] T012 [US1] Implement Z-Reward dataset ingestion in `code/ingest.py` (load prompts, images, teacher scores, student scores, human annotations). **DEPENDS: T038**.
- [X] T013 [US1] Implement alignment logic in `code/ingest.py`: match teacher distributions, student scalars, and human annotations by sample ID. **CRITICAL**: Verify `student_scalar` column exists. If missing, attempt to load a separate `student_inference.parquet` file from `data/raw/` OR mark the sample as `excluded_reason: 'missing_student_scalar'` in the dataframe. **DO NOT** raise a `RuntimeError`. The pipeline must continue, and the sample will be excluded later in T024. **DEPENDS: T012**.
- [X] T014 [US1] Implement "primary quality dimension" identification logic in `code/ingest.py`: **Rule**: Use the value of the column `primary_dimension` if present in the dataset. **CRITICAL**: If `primary_dimension` is missing for a sample, mark that sample as `excluded_reason: 'missing_primary_dimension'` in the dataframe. **DO NOT** raise a `RuntimeError`. The pipeline must continue, and the sample will be excluded later in T024. **DEPENDS: T013**.
- [X] T015 [US1] Implement chunked loading or sampling logic in `code/ingest.py` to ensure RAM usage stays < 7GB on free-tier runners. **DEPENDS: T012**.
- [X] T016 [US1] Add summary output in `code/ingest.py`: print sample counts, missing data flags, dimension coverage stats. **DEPENDS: T012**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entanglement Quantification and Feature Engineering (Priority: P2)

**Goal**: Calculate statistical descriptors (variance, entropy, skewness, kurtosis) per sample, and a valid per-sample 'Score Magnitude' (L2 norm) for the teacher's score distribution. Also compute a global covariance metric.

**Independent Test**: A script processes a fixed subset of teacher distributions and outputs a JSON record with calculated features, handling zero-variance cases gracefully.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for variance, entropy, skewness, kurtosis calculations in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`
- [X] T019 [P] [US2] Unit test for zero-variance edge case handling in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement variance and range calculation for dimensions in `code/features.py`. **DEPENDS: T012**.
- [X] T021 [US2] Implement entropy, skewness, and kurtosis calculation for teacher distributions in `code/features.py`. **DEPENDS: T012**.
- [ ] T022a [US2] Implement **Per-Sample Entanglement Score**:
 1. For each sample, extract the -dimensional teacher score vector (or the available dimension vector).
 2. Calculate **Variance** (var) across the dimensions.
 3. Calculate **Shannon Entropy** (normalize vector to sum=1, then compute -sum(p*log(p))).
 4. Calculate **Skewness** and **Kurtosis** of the dimension vector.
 5. **CRITICAL**: All metrics (variance, entropy, skewness, kurtosis) must be computed **per sample** and stored as columns in the dataframe. **NO** global constants for these features.
 6. **VALIDATION**: Handle zero-variance/constant cases gracefully (Entropy=0, Variance=0). **DEPENDS: T012**.
- [ ] T022b [US2] Implement **Per-Sample Score Magnitude** (formerly Dominant Eigenvalue):
 1. For each sample, extract the 4-dimensional teacher score vector $v$.
 2. Compute the **L2-norm squared** ($||v||^2$) as the "Score Magnitude".
 3. **CRITICAL**: This calculation is performed **per sample**, resulting in a single scalar value for each row in the dataframe. This value serves as a per-sample predictor for the Random Forest.
 4. **VALIDATION**: Handle zero-variance cases (if $v$ is zero vector, magnitude is 0). **DEPENDS: T012**.
- [ ] T022c [US2] Implement **Global Covariance Eigenvalue**:
 1. Compute the **global covariance matrix** of the teacher scores across the *entire dataset* (not per sample).
 2. Calculate the **Dominant Eigenvalue** of this global covariance matrix.
 3. **CRITICAL**: This is a *single* scalar value for the entire dataset, representing the "structural entanglement" of the teacher model as per Constitution Principle VI. Store this as a metadata field in the results, not as a per-sample feature.
 4. **VALIDATION**: Ensure the calculation is robust to missing data (exclude samples with NaN scores). **DEPENDS: T012**.
- [X] T025 [US2] Integrate Ingestion and Feature Engineering: Read aligned data from `code/ingest.py` (or intermediate state). Compute per-sample stats (T020-T021, T022a, T022b). <!-- FIXED: Per-sample approach -->
 1. **Merge** the per-sample features (variance, entropy, skewness, kurtosis, score_magnitude) into the main dataframe.
 2. **Note**: The Random Forest will use these per-sample features.
 3. **DEPENDS: T012, T020, T021, T022a, T022b**. **VALIDATION**: Ensure output JSON matches `contracts/output.schema.yaml` and contains no null values for required keys (`sample_id`, `variance`, `entropy`, `score_magnitude`, `fidelity_loss`).
- [X] T023 [US2] Implement zero-variance handling in `code/features.py`: set entropy to 0 and variance to 0 without crashing. **DEPENDS: T020**.
- [ ] T041 (DELETED - Contradictory approximation logic removed; Per-sample approach in T022a/T022b is correct). <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->

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
 3. **Output key**: `fidelity_loss`. **DEPENDS: T012, T014, T013**.
- [X] T027a [US3] Implement Random Forest training setup in `code/train.py`: Read features from `data/processed/features.json` (including `fidelity_loss`); configure train/test split with `test_size=0.2` and `random_state=42`; ensure CPU-only execution (`n_jobs=2`); **DEPENDS: T025, T024**.
  1. **Stratification Strategy**: Since `fidelity_loss` is continuous, apply **quantile-based binning** (n_bins=5) to the target variable before stratified splitting to ensure deterministic and reproducible splits.
- [X] T027b [US3] Implement Random Forest training execution in `code/train.py`: Train model with `n_estimators=100`, `max_depth=None`, `random_state=42`; **DEPENDS: T027a**; **Return** the trained model object for T027c.
- [ ] T027c [US3] Save model artifact: Serialize trained model from T027b to `results/model.pkl`; **DEPENDS: T027b**.
- [X] T028 [US3] Implement k-fold cross-validation logic in `code/train.py` with stratified splitting. **DEPENDS: T027b**.
- [ ] T030a [US3] Implement permutation test logic: **Permute the feature matrix (X)** against the target (y) `n_permutations=1000` times with `random_state=42`. Calculate R² for each permutation. Compute p-value as the fraction of permuted R² values >= observed R². This validates the **correlation strength** (SC-001). **DEPENDS: T025, T027b**. **Output**: Provide a function `calculate_permutation_pvalue` to be called by T029.
- [X] T029 [US3] Implement evaluation script in `code/evaluate.py`: calculate mean R², std dev, MAE, and call T030a to get permutation test p-value. **DEPENDS: T028, T030a**.
- [ ] T030b [US3] Write results: Serialize R², MAE, and p-value to `results/results.json`. **DEPENDS: T029**.
- [ ] T030c [US3] Implement Null Baseline Comparison:
 1. **Train a Mean Predictor**: Use `sklearn.dummy.DummyRegressor(strategy='mean')` to train a model that predicts the mean of `fidelity_loss` on the training set.
 2. Evaluate this Mean Predictor on the test set to get its R² and MAE.
 3. **Compare**: Compare the Random Forest R²/MAE (from T027b/T029) against the Mean Predictor's R²/MAE.
 4. **Requirement**: Verify that the Random Forest R² > Mean Predictor R² (or R² > 0.0).
 5. **Statistical Significance**: Perform a **bootstrap-based comparison** of MAE (multiple resamples) to generate a confidence interval for the difference in MAE. If the 95% CI does not include 0, the improvement is significant.
 6. **Fallback**: If bootstrap fails, perform a **permutation test** on the residuals. **DO NOT** use a paired t-test (invalid for constant baseline). **DEPENDS: T029, T027b**.
- [ ] T031 [US3] Integrate training and evaluation: Read features from `data/processed/features.json`, train model, run CV, run permutation test, run null baseline comparison, and write final metrics to `results/results.json`; **DEPENDS: T027a, T027c, T028, T029, T030c**.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Create `quickstart.md` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with explicit steps to reproduce the full pipeline (Install -> Download -> Ingest -> Train -> Evaluate) to satisfy Constitution Principle I. **DEPENDS: T031**.
- [ ] T033 [P] Code cleanup and refactoring: Run `ruff check` and `black --check` on `code/` and `tests/`. Fix all errors until `ruff` exits with code 0 and `black` reports no changes. **DEPENDS: T031**.
- [ ] T034 [P] Profile and optimize feature engineering loop: Run `cProfile` on `code/features.py`. Generate a report identifying the primary bottlenecks.
 1. **Research Question**: What are the key constraints limiting system performance?
 2. **Method**: Systematic bottleneck analysis.
 3. **References**: scikit-learn documentation on Random Forests; scipy.stats documentation for statistical tests.
 4. **Optimization**: If runtime > 30 minutes, implement optimization to **reduce runtime** using **vectorization with numpy**. **Warning**: If runtime > 6 hours, the task fails. **DEPENDS: T025**.
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
- **T025 (Feature Integration)**: Must complete before T027a (Training)
- **T037 (Download)**: Must complete before T038 (Validation)
- **T038 (Validation)**: Must complete before T012 (Ingestion)
- **T001d (Schema)**: Must complete before T038 (Validation)
- **T012 (Ingestion)**: Must complete before T025 (Compute Features)
- **T027a (Config)**: Must complete before T027b (Train)
- **T027b (Train)**: Must complete before T027c (Save Model)
- **T030a (Permutation)**: Must complete before T029 (Evaluation)
- **T029 (Evaluation)**: Must complete before T030c (Null Baseline)
- **T030c (Null Baseline)**: Must complete before T031 (Integration)
- **T001d Tag Clarification**: T001d is NOT parallel [P]. It must complete before Phase 2 begins to ensure T038 has a valid schema file.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T038 which depends on T037**
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
- **CRITICAL**: Entanglement features (T022a, T022b) MUST be computed using **per-sample** statistics (Entropy, Variance, Skewness, Kurtosis, Score Magnitude) derived from the sample's distribution. **NO** global constants are allowed as per-sample features.
- **CRITICAL**: Global Covariance Eigenvalue (T022c) is computed on the full dataset batch, not per sample.
- **CRITICAL**: Target variable (T024) MUST be calculated in `code/features.py` using metadata-based dimension selection (T014), independent of model scores.
- **CRITICAL**: Data Acquisition (T037, T038) must complete before US1 implementation (T012) to ensure the ingestion script has real data to process.
- **CRITICAL**: T001e initializes output files to prevent "file not found" errors.
- **CRITICAL**: T025 is the unified task for feature integration.
- **CRITICAL**: T027b trains the model and returns the object; T027c saves it to `results/model.pkl`.
- **CRITICAL**: T038 depends on T037 only (no fallback).
- **CRITICAL**: T004 is deleted (merged into T001a).
- **CRITICAL**: T041 is deleted (contradictory logic).
- **CRITICAL**: T032 creates `quickstart.md` for reproducibility.
- **CRITICAL**: T003 creates `.ruff.toml` and `pyproject.toml`.
- **CRITICAL**: T037 uses a dynamic list of verified sources (UCI/verified HF).
- **CRITICAL**: T038 performs schema discovery and populates the schema files.
- **CRITICAL**: T033 has a concrete "done" state (ruff exit code 0).
- **CRITICAL**: T034 has a concrete metric (runtime reduction or bottleneck report).
- **CRITICAL**: T035 specifies exact edge cases.
- **CRITICAL**: T001a, T001b, T001c use the correct project prefix path.
- **CRITICAL**: T013 handles missing student scalar columns explicitly by marking as excluded, NOT crashing.
- **CRITICAL**: T039 and T042 have been removed from the active task list.
- **CRITICAL**: T014 marks missing samples for exclusion instead of crashing.
- **CRITICAL**: T013 and T014 must both handle missing data gracefully (exclusion) to prevent pipeline crashes.
- **CRITICAL**: T022a computes valid per-sample stats (Variance, Entropy, Skewness, Kurtosis).
- **CRITICAL**: T022b computes Per-Sample Score Magnitude (L2 norm squared).
- **CRITICAL**: T022c computes Global Covariance Eigenvalue on the full dataset.
- **CRITICAL**: T030c trains the Mean Predictor inline, compares R²/MAE, and mandates a **bootstrap-based comparison** (or permutation test) for statistical significance. **NO paired t-test**.
- **CRITICAL**: T027a uses **quantile-based binning** for stratified splitting of continuous targets.