# Tasks: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Input**: Design documents from `/specs/001-llmxive-entanglement-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T000a [P] Create `research.md` schema template: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/research.md` with a "Verified datasets" section structure. **Content**: Define the YAML/JSON schema for the verification block (dataset_id, title_token_overlap, checksum, verification_date). **DEPENDS**: None.
- [ ] T000c [P] Create `verify_dataset.py`: Create `projects/PROJ-llmxive-follow-up-extending-beyond-scala/code/verify_dataset.py` with logic to validate dataset ID, check token overlap, and return verification status. **DEPENDS**: T000a.
- [ ] T000b [P] Populate `research.md` with verification results: Execute `code/verify_dataset.py` (created in Tc) to verify dataset ID `z-reward/z-reward-v1` (fallback `z-reward/z-reward-v2`). **CRITICAL**: Write the actual verification result to `research.md`, including `title_token_overlap` and `checksum`. If real data verification fails and synthetic is used, write `source: synthetic` and `note: synthetic_fallback` to `research.md`. **DEPENDS**: T000a, T000c.
- [ ] T000b-e [P] Update `research.md` for synthetic fallback: If T037b is invoked, append a note to `research.md` indicating `IS_SYNTHETIC_RUN: true` and the synthetic source. **DEPENDS**: T037b.
- [ ] T001a [P] Create data directories: Create directories `projects/PROJ-*/llmxive-follow-up-extending-beyond-scala/data/raw`, `projects/PROJ-*/llmxive-follow-up-extending-beyond-scala/data/processed`, `projects/PROJ-*/llmxive-follow-up-extending-beyond-scala/results` relative to repository root. **REPLACES**: None.
- [ ] T001a-2 [P] Create code/tests directories: Create directories `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests` relative to repository root. **REPLACES**: None.
- [X] T001b [P] Create empty project files: Create empty files `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/.gitignore`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/pytest.ini`
- [X] T001c [P] Write dependencies: Write `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt` with **pinned versions** (e.g., `pandas==2.0.3`, `numpy==1.24.3`) of pandas, numpy, scikit-learn, scipy, pyyaml, pytest, ruff, black. **CRITICAL**: Do not use version ranges; use exact `==` pins.
- [ ] T001d Create **provisional** dataset schema template: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/dataset.schema.yaml` with the following exact YAML content:
```yaml
schema_version: "1.0"
fields:
 - name: prompt
 type: string
 - name: image_url
 type: string
 - name: teacher_scores
 type: object
 properties:
 Alignment: float
 Realism: float
 Aesthetics: float
 Plausibility: float
 - name: student_scalar
 type: float
 - name: human_annotations
 type: object
 properties:
 Alignment: float
 Realism: float
 Aesthetics: float
 Plausibility: float
 - name: primary_dimension
 type: string
```
**NOTE**: This task is NOT parallel; it must complete before Phase 2 begins, but T038 will update this template based on actual data. **ACTION**: Write the YAML content above. **CRITICAL**: This schema is provisional and may be updated by T038. **VERIFICATION**: Verify the schema against the raw data columns in T038.
- [ ] T001f [P] Create output schema contract: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-entanglement-analysis/contracts/output.schema.yaml` defining the structure of `data/processed/features.json` (e.g., `sample_id`, `variance`, `entropy`, `skewness`, `kurtosis`, `mahalanobis_distance`, `fidelity_loss`). **DEPENDS**: T001a.
- [X] T001e [P] Initialize output artifacts: Create empty `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json` (with `[]` or `{}`) and `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json` (with `{}`) to prevent file-not-found errors in downstream tasks
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` and `pyproject.toml` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with pinned tool versions (`==` exact versions, no ranges) and configuration to satisfy Constitution Principle I (Reproducibility). **REPLACES**: T003. **CRITICAL**: `pyproject.toml` must use exact version pinning (e.g., `ruff==0.1.0`) and `.ruff.toml` must exist. **MANDATORY STEP**: Execute `pip freeze > requirements.txt` to ensure exact version pinning is captured in the artifact.
- [ ] T000d [P] Create synthetic data generator: Create `projects/PROJ-llmxive-follow-up-extending-beyond-scala/code/synthetic_data.py` with a schema-compliant generator function that accepts `--n-samples` and `--seed` arguments to generate a configurable number of synthetic samples. **DEPENDS**: T001d.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Acquisition, Filtering, Model Selection, and Global Feature Engineering.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase MUST complete before Phase 4 begins. **DEPENDENCY NOTE**: Phase 2 tasks (T024, T027d) are blocking prerequisites for all User Stories (Phase 3, 4, 5). Independent Implementation of US2 is subject to the completion of Phase 2.

- [ ] T037 [US1] Download Z‑Reward evaluation dataset (real data) with adaptive fallback:
 1. **Primary**: Verify dataset ID `z-reward/z-reward-v1` via `code/verify_dataset.py` (T000b); if verified, load with `datasets.load_dataset`.
 2. **Secondary**: If primary verification fails, verify `z-reward/z-reward-v2` and load.
 3. **Tertiary**: If both verifications fail, check environment variable `Z_REWARD_ARCHIVE_PATH` for a local `.zip` archive, extract to `data/raw/`, and load.
 4. **Adaptive Fallback (Case A - MISSING DATA)**: Check `--mode` flag.
    - If `--mode=research` and file NOT found after all real source attempts: **Raise RuntimeError** with message "Real data missing in research mode."
    - If `--mode=test` (or no flag) and file NOT found: **Invoke** `code/synthetic_data.py` (T000d) to create `data/raw/z_reward_synthetic.parquet` (N=10,000) with `IS_MOCK_DATA = true`. Log this event.
 5. **Verification**: After loading, assert presence of required columns (`prompt`, `image_url`, `teacher_scores` with the four rubric keys, `student_scalar`, `human_annotations` with the four rubric keys, `primary_dimension`). If any are missing, raise a clear `RuntimeError`.
 6. **OUTPUT**: Write the loaded dataset to `data/raw/z_reward.parquet` (or `z_reward_synthetic.parquet` if fallback).
 7. **OUTPUT**: Write `data/raw/validation_log.json` containing schema validation results and fallback status.
 8. **OUTPUT**: Write `data/processed/valid_sample_count.json` with keys `total_samples`, `valid_samples` (non-null, finite for all fields), `excluded_count`. **CRITICAL**: This satisfies SC-005.
 9. **BLOCKING**: Must complete before any ingestion or schema validation tasks.
 **DEPENDS**: T000b, T001a, T000d.
- [ ] T037b [P] Generate synthetic dataset for unit testing (MANUAL INVOCATION ONLY):
 1. **Input**: None (uses fixed random seed for reproducibility).
 2. **Generate**: Create a Pandas DataFrame matching the schema with columns `prompt`, `image_url`, `teacher_scores` (Alignment, Realism, Aesthetics, Plausibility), `student_scalar`, `human_annotations` (same four keys), `primary_dimension`. **DEFAULT**: N=50 samples (configurable via `--n-samples`) to test Ridge Regression path.
 3. **Noise Independence**: Teacher scores are sampled from `np.random.normal(loc=5, scale=2, size=...)`; human annotations are sampled independently from a separate `np.random.normal(loc=5, scale=2,...)` *with a different seed*, guaranteeing independent noise structures.
 4. **Output**: Write to `data/raw/mock_z_reward.parquet`.
 5. **Flag**: Set `IS_MOCK_DATA = true` in `data/processed/config.json`.
 6. **CRITICAL**: Write `IS_SYNTHETIC_RUN: true` to `results.json` and append a note to `research.md` indicating synthetic data source.
 7. **NOTE**: This synthetic data is for unit‑testing only; final results must use real data when available. **DO NOT** invoke automatically from T037. This task is strictly manual.
 **DEPENDS**: T001d, T000d.
- [ ] T038 [P] [US1] Schema Discovery and Validation:
 1. Read the raw dataset file produced by T037 (or T037b) from `data/raw/`.
 2. Perform schema discovery, mapping actual column names to logical fields.
 3. Validate against the provisional template `contracts/dataset.schema.yaml`.
 4. If discrepancies exist, **overwrite** `contracts/dataset.schema.yaml` with the final validated schema.
 5. Raise an error on critical mismatches (e.g., missing rubric dimensions).
 **DEPENDS**: T037 OR T037b.
- [ ] T014 [US1] Implement primary quality dimension identification logic (Shared Utility):
 1. **Primary Rule**: Derive the `primary_dimension` from prompt metadata using a fixed schema rule (e.g., parse `prompt_metadata.primary_dimension` or a deterministic hash of the prompt text mapping to one of the four dimensions).
 2. **Secondary Rule**: If the metadata rule yields no result, use the value of the column `primary_dimension` **if present**.
 3. **Fallback Rule**: If both fail, default to 'Alignment' (deterministic fallback).
 4. **Output**: Ensure `primary_dimension` is NEVER null. Add a log entry for samples using the fallback.
 5. **CRITICAL**: This logic is now a shared utility function used by T024 to ensure the rule exists before the lineage report is generated.
 **DEPENDS**: T038.
- [ ] T024 [US3] Implement "dimensional fidelity loss" calculation and filtering:
 1. **Input**: Read the raw dataset from `data/raw/z_reward.parquet` (output of T037).
 2. **Derivation Rule**: Read the derivation rule logic from T014 (now a shared utility) to determine `primary_dimension`.
 3. **Calculate Target**: Compute MAE between `student_scalar` and the human‑annotated score for the sample's `primary_dimension`.
 4. **Filter**: Exclude samples where `primary_dimension` is null, human annotation for that dimension is missing, or `student_scalar` is missing.
 5. **Output**: Write the filtered dataframe to `data/processed/cleaned_data.parquet`.
 6. **Output**: Write summary statistics (`mean`, `median`, `count`, `excluded_count`) to `data/processed/fidelity_loss_summary.json`.
 7. **CRITICAL**: Generate `data/processed/lineage_report.json` with schema `[{sample_id, source_type: "metadata", dimension, derivation_rule_hash}]`. This report MUST explicitly state "Source: Metadata Only" for every sample to prove target independence (SC-004). It must verify that `primary_dimension` was derived solely from metadata (using the rule from T014) and not model scores. **CRITICAL**: This satisfies SC-004.
 8. **BLOCKING**: This task must complete before T022b (Global Covariance), T027d (Model Selection), and Phase 4 tasks.
 **DEPENDS**: T037 OR T037b, T038, T014.
- [ ] T027d [US3] Model‑selection task:
 1. **MUST run after T024 completes**.
 2. Read `data/processed/cleaned_data.parquet` (output of T024) and count N.
 3. If N < 30 → set `model_type = "fail"`. **Action**: Write `{"status": "fail", "model_type": "fail", "reason": "Critical Power Limitation: N < 30"}` to `data/processed/model_selection.json`. The pipeline continues to generate a failure report in `results.json`.
 4. If 30 ≤ N < 300 → set `model_type = "ridge"` (use Ridge Regression).
 5. If N ≥ 300 → set `model_type = "rf"` (use Random Forest) and ensure Mahalanobis distance will be computed (T022c).
 6. Write `data/processed/model_selection.json` with the selected `model_type`.
 **DEPENDS**: T024, T038.
- [ ] T022a [US2] Implement **Per‑Sample Entanglement Score**:
 1. For each sample, extract the 4‑dimensional teacher score vector.
 2. Compute Variance, Shannon Entropy (normalize to sum = 1), Skewness, and Kurtosis.
 3. Handle zero‑variance cases (set variance = 0, entropy = 0) without crashing.
 4. Append these columns to the dataframe and write to `data/processed/entanglement_scores.csv`.
 **DEPENDS**: T024, T038.
- [ ] T022b [US2] **Global Covariance Matrix** (computed on the *filtered* dataset or raw fallback):
 1. **Input**: Read the *filtered* aligned data from `data/processed/cleaned_data.parquet` (output of T024). **CRITICAL**: Verify this file exists before proceeding. **MUST run after T024 completes**.
 2. Extract the N × 4 matrix of teacher scores.
 3. If N < 4, **Fallback**: Read raw data from `data/raw/z_reward.parquet` (T037 output) and compute covariance. If raw N < 4, write `{"status": "fail", "message": "Insufficient samples for covariance"}` to `results/covariance_matrix.json` AND `results/results.json` (propagate fail state to satisfy SC-001).
 4. Compute the covariance matrix (`numpy.cov`, `rowvar=False`).
 5. Write the covariance matrix to `results/covariance_matrix.json`.
 **DEPENDS**: T024 (or T037 if fallback).
- [ ] T022b-eigen [US2] **Dominant Eigenvalue Extraction** (Unconditional):
 1. Input: Read the covariance matrix from `results/covariance_matrix.json` (output of T022b).
 2. **Validation**: Validate that the input file contains a square numeric matrix before proceeding.
 3. Compute the dominant eigenvalue (largest eigenvalue) of this matrix.
 4. Write the dominant eigenvalue to `results/dominant_eigenvalue.json`.
 **DEPENDS**: T022b.
- [ ] T025a-core [US2] Compute Per‑Sample Stats (Unconditional):
 1. Read aligned data from `data/processed/cleaned_data.parquet` (filtered dataset from T024).
 2. **Merge**: Merge features from T022a (entanglement_scores.csv) into the cleaned dataset. Do NOT re-compute T020-T021.
 3. **Output**: Write base features (Variance, Entropy, Skewness, Kurtosis, Difficulty Proxy) to `data/processed/features_base.json`.
 4. **Trace Log**: The `lineage_report.json` is already generated in T024. Copy it here or reference it.
 5. Ensure no null values for required keys.
 6. **NOTE**: T022a is independent of T027d, so T025a-core is not blocked by T027d.
 **DEPENDS**: T024, T022a.
- [X] T005 [P] Create `code/ingest.py` skeleton with argument parsing and logging setup
- [X] T006 [P] Create `code/features.py` skeleton with statistical helper functions
- [X] T007 [P] Create `code/train.py` skeleton with scikit‑learn model configuration
- [X] T008 [P] Create `code/evaluate.py` skeleton for metrics calculation
- [X] T009 [P] Setup `tests/` directory structure and `pytest.ini`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Ingestion and Ground‑Truth Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest Z‑Reward dataset, align teacher/student outputs with human annotations, and handle missing data gracefully.

**Independent Test**: A script loads the dataset, verifies the presence of all four rubric dimensions, flags missing data, and outputs a summary without crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for data loading and schema validation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`
- [X] T011 [P] [US1] Integration test for missing data handling and exclusion logic in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement Z‑Reward dataset ingestion in `code/ingest.py` (load prompts, images, teacher scores, student scores, human annotations). Write output to `data/processed/raw_data.parquet`. **DEPENDS**: T037 OR T037b. Must be schema‑agnostic; uses provisional schema from T001d for initial column mapping. Supports `--use-mock-data` flag if synthetic data was generated.
- [X] T013 [US1] Implement alignment logic in `code/ingest.py`: match teacher distributions, student scalars, and human annotations by sample ID. If `student_scalar` is missing, mark the sample with `excluded_reason: 'missing_student_scalar'` (do not raise). **DEPENDS**: T012.
- [X] T015 [US1] Implement chunked loading or sampling logic in `code/ingest.py` to keep RAM usage < 7 GB. **DEPENDS**: T012.
- [X] T016 [US1] Add summary output in `code/ingest.py`: print sample counts, missing‑data flags, and dimension coverage stats. **DEPENDS**: T012.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entanglement Quantification and Feature Engineering (Priority: P2)

**Goal**: Calculate statistical descriptors (variance, entropy, skewness, kurtosis) per sample, and a valid global covariance metric (Dominant Eigenvalue) for the teacher's score distributions across the dataset, and a per‑sample Mahalanobis distance.

**Independent Test**: A script processes a fixed subset of teacher distributions and outputs a JSON record with calculated features, handling zero‑variance cases gracefully.

**⚠️ NOTE**: Phase 4 depends on Phase 2 completion (T024, T027d).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for variance, entropy, skewness, kurtosis calculations in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`
- [X] T019 [P] [US2] Unit test for zero‑variance edge case handling in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement variance and range calculation for dimensions in `code/features.py`. **DEPENDS**: T012.
- [X] T021 [US2] Implement entropy, skewness, and kurtosis calculation for teacher distributions in `code/features.py`. **DEPENDS**: T012.
- [ ] T022c [US2] **Per‑Sample Mahalanobis Distance** (conditional):
 1. **Conditional Execution**: Run only if the pipeline will use Random Forest (i.e., after model‑selection task determines `model_type == "rf"` and N ≥ 300).
 2. **MUST run after T024 and T027d**.
 3. Input: Use the *filtered* dataset from `data/processed/cleaned_data.parquet` (output of T024) and the global covariance matrix/mean from T022b.
 4. **Statistical Consistency**: If the filtered dataset differs significantly from the global set (e.g., >10% samples removed), recompute the mean and covariance on the *filtered* set for the Mahalanobis calculation to ensure statistical consistency.
 5. Compute Mahalanobis distance for each sample:
 $D_M(x) = \sqrt{(x-\mu)^T \Sigma^{-1} (x-\mu)}$.
 6. Handle singular covariance matrices with pseudo‑inverse, issuing a warning.
 7. Append `mahalanobis_distance` column and write to `data/processed/entanglement_scores.csv`.
 8. **Else**: If `model_type != "rf"`, write a 'skipped' log entry to `data/processed/feature_status.json`.
 **DEPENDS**: T022b, T024, T027d.

- [X] T023 [US2] Implement zero‑variance handling in `code/features.py`: set entropy to 0 and variance to 0 without crashing. **DEPENDS**: T020.

- [ ] T025b-mahalanobis [US2] Append Mahalanobis Distance (Conditional):
 1. **Conditional**: If `model_type == "rf"`, read `data/processed/features_base.json` and append `mahalanobis_distance` from T022c.
 2. **Else**: If `model_type != "rf"`, copy `features_base.json` to `data/processed/features.json` without Mahalanobis.
 3. Write final `data/processed/features.json`.
 **DEPENDS**: T025a-core, T022c, T027d.

- [X] T025c [US2] Validate Output Schema:
 1. Verify that the merged JSON matches `contracts/output.schema.yaml`.
 **DEPENDS**: T025b-mahalanobis.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train a CPU‑based model to predict fidelity loss using entanglement features, with k‑fold CV, permutation test, and null‑baseline comparison.

**Independent Test**: A script trains the model on a stratified random split (with quantile binning), runs 5‑fold CV, and outputs R², MAE, and permutation‑test p‑value without using GPU.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US3] Unit test for Random Forest training and 5‑fold CV execution in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_train.py`
- [X] T026 [P] [US3] Integration test for permutation test p‑value calculation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_evaluate.py`

### Implementation for User Story 3

- [X] T027a [US3] Configure training split:
 1. Read features from `data/processed/features.json` (output of T025b-mahalanobis).
 2. Perform quantile‑based binning (5 bins) on the target `fidelity_loss` for stratified `train_test_split(test_size=0.2, random_state=42)`.
 3. Store split indices in `data/processed/split_config.json`.
 4. **Conditional Model**: Based on `model_type` from T027d, select the appropriate estimator (Random Forest or Ridge) for downstream training tasks.
 **DEPENDS**: T025b-mahalanobis, T027d.

- [X] T027b [US3] Train the selected model:
 1. If `model_type == "rf"` → train `RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=2)`.
 2. If `model_type == "ridge"` → train `Ridge(alpha=1.0, random_state=42)`.
 3. If `model_type == "fail"`, skip training and proceed to T027c.
 4. Save the trained model object to `results/model.pkl`.
 **DEPENDS**: T027a.

- [ ] T027c [US3] Save placeholder model when training is skipped (e.g., N < 30):
 1. If `model_type == "fail"`, write metadata `{"status":"fail", "message":"Critical Power Limitation: N < 30"}` to `results/model.pkl` using `pickle.dump(metadata, f)`.
 2. Also write `{"status":"fail", "message":"Critical Power Limitation: N < 30"}` to `results/results.json` to satisfy SC-001.
 **DEPENDS**: T027b.

- [X] T028 [US3] Implement k‑fold cross‑validation using the same stratified bins from T027a. Compute mean R² and MAE across folds.

- [ ] T030a [US3] Implement permutation test:
 1. Using the training split (X_train, y_train) from T027a, permute `y_train` `n_permutations=1000` times (fixed `random_state=42`).
 2. Compute R² for each permutation.
 3. Return p‑value = fraction of permuted R² ≥ observed R².
 **DEPENDS**: T027a, T027b.

- [X] T029 [US3] Evaluation script:
 1. Compute mean R², std dev, MAE on the test set.
 2. **OUTPUT**: Calculate residuals (y_true - y_pred) and write them to `data/processed/residuals.csv`.
 3. Call `calculate_permutation_pvalue` (T030a) and store `p_value_permutation`.
 **DEPENDS**: T028, T030a.

- [ ] T030c [US3] Null Baseline Comparison (strict):
 1. **MUST run after T029 completes**.
 2. Train a `DummyRegressor(strategy='mean')` on the training split.
 3. Evaluate on the test set to obtain baseline R² and MAE.
 4. **CRITICAL**: Compute absolute errors for both the selected model and the baseline. Calculate the vector of absolute errors for each.
 5. Perform a paired t‑test (`scipy.stats.ttest_rel`) on the **absolute errors** (not residuals) of the selected model vs. the baseline. **NOTE**: This satisfies SC-002 by comparing the distribution of errors, which is statistically equivalent to comparing the aggregate MAE metrics.
 6. **Reporting**: Compute p-value. If p < 0.05, report "significant"; otherwise report "not significant". **DO NOT** fail the task based on p-value.
 7. Write `baseline_r2`, `p_value_ttest`, `t_test_status` (significant/not significant), and `p_value_permutation` to `results/results.json`.
 **DEPENDS**: T029, T027a.

- [ ] T031 [US3] Integrate training and evaluation:
 1. Run the full pipeline: feature generation → model selection → training → CV → evaluation → null baseline comparison.
 2. Ensure `results/results.json` contains the required keys (`p_value_permutation`, `p_value_ttest`, `baseline_r2`, `mean_r2`, `mean_mae`).
 **DEPENDS**: T027a, T027b, T028, T029, T030c.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Create `quickstart.md` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with explicit steps to reproduce the full pipeline (Install → Download → Ingest → Train → Evaluate) to satisfy Constitution Principle I. **DEPENDS**: T031.
- [ ] T033 [P] Code cleanup and refactoring: Run `ruff check` and `black --check` on `code/` and `tests/`. Fix all errors until `ruff` exits with code 0 and `black` reports no changes. **DEPENDS**: T031.
- [ ] T034a [P] Profile and optimize feature engineering loop (Part 1): Run `cProfile` on `code/features.py` using a random sample of the full dataset (or the maximum available subset) to estimate runtime.
 1. **Research Question**: Identify bottlenecks limiting performance.
 2. **Method**: Systematic profiling; reference scikit‑learn and scipy docs.
 3. **Output**: Generate `results/profile_report.txt` with bottleneck analysis (top 5 functions by cumulative time).
 **DEPENDS**: T025c.
- [ ] T034b [P] Profile and optimize feature engineering loop (Part 2): Refactor `code/features.py` based on `results/profile_report.txt` from T034a.
 1. **Optimization**: If estimated runtime > 30 min, refactor to vectorized NumPy operations; ensure total runtime stays < 6 h on the CI runner.
 **DEPENDS**: T034a.
- [ ] T035a [P] Additional unit tests for edge cases: Write test for empty dataset in `test_ingest.py`. **DEPENDS**: T018.
- [ ] T035b [P] Additional unit tests for edge cases: Write test for NaN values in teacher logits in `test_features.py`. **DEPENDS**: T018.
- [ ] T035c [P] Additional unit tests for edge cases: Write test for missing human annotations for all dimensions in `test_ingest.py`. **DEPENDS**: T018.
- [ ] T035d [P] Additional unit tests for edge cases: Write test for zero‑variance distributions in `test_features.py`. **DEPENDS**: T018.
- [ ] T036 [P] Run `quickstart.md` validation to ensure reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**. Includes Data Acquisition (T037), Filtering (T024), Model Selection (T027d), and Global Feature Engineering (T022a, T022b). **MUST complete before Phase 4.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Acquisition (Phase 2)**: Must complete before T012 (Ingestion) can successfully run on real data (or mock data via T037b)
- **T038** runs after T037/T037b
- **T027d** runs after T024 (to get N)
- **T027a** reads the model‑selection flag
- **T022c** runs only when `model_type == "rf"` (checked in T027d)
- **T025b-mahalanobis** conditionally includes Mahalanobis distance based on the same flag
- **CRITICAL ORDERING**: T022b (Global Covariance) MUST run AFTER T024 (Filtering). T022b depends on T024. T022b and T024 can run in parallel after T012, but T022b must complete before T025a (which reads the global metric) and T022c (which uses the global metric).
- **CRITICAL ORDERING**: T022c (Mahalanobis) depends on T027d (Model Selection) to prevent execution when Ridge is selected. T022c reads filtered data from T024.
- **CRITICAL ORDERING**: T025a-core (Base Features) runs AFTER T024. T025b-mahalanobis runs AFTER T027d.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for aligned data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (target calculation) and US2 (features)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T038** which depends on T037/T037b, **T024** which depends on T037, and **T027d** which depends on T024.
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **CRITICAL**: All data loading tasks (T012, T037) must use real, reachable URLs (verified UCI or HF datasets) or package‑based fetchers. **NO synthetic fallbacks** allowed for final results, but T037b is allowed for unit testing (manual invocation). **T037 now raises RuntimeError if real data is missing AND no synthetic fallback is triggered.**
- **CRITICAL**: All model training tasks must be CPU‑only (no CUDA, no 8‑bit quantization, no large LLMs). Use small models and sampled datasets if necessary.
- **CRITICAL**: Entanglement features (T022a, T022c) MUST be computed using **per‑sample** statistics (Entropy, Variance, Skewness, Kurtosis, Mahalanobis Distance). **NO** global constants are allowed as per‑sample features.
- **CRITICAL**: T022b computes Global Covariance/Eigenvalue via covariance matrix of the *filtered* dataset (output of T024), satisfying Constitution Principle VI and FR-006. T022b depends on T024.
- **CRITICAL**: T022c computes Per‑Sample Mahalanobis Distance on the *filtered* dataset **only** when Random Forest is used. T022c depends on T027d.
- **CRITICAL**: Target variable (T024) MUST be calculated in `code/ingest.py` using metadata‑based dimension selection (T014), independent of model scores.
- **CRITICAL**: Data Acquisition (T037, T037b) must complete before US1 implementation (T012) to ensure the ingestion script has real data to process. If T037 fails, T037b is auto-invoked.
- **CRITICAL**: T025c must complete before T027a (Training) to guarantee feature‑schema compliance.
- **CRITICAL**: T037 uses a multi‑source fallback chain (v1 → v2 → local archive) instead of hard‑coded single ID.
- **CRITICAL**: T038 performs schema discovery on the raw source file (T037 or T037b) before ingestion.
- **CRITICAL**: T033 has a concrete "done" state (ruff exit code 0).
- **CRITICAL**: T034a and T034b split profiling and refactoring.
- **CRITICAL**: T035 specifies exact edge cases (split into T035a-d).
- **CRITICAL**: T001a, T001a-2, T001b, T001c use the correct project prefix path.
- **CRITICAL**: T013 handles missing student scalar columns explicitly by marking as excluded, NOT crashing.
- **CRITICAL**: T014 and T013 must both handle missing data gracefully (exclusion) to prevent pipeline crashes.
- **CRITICAL**: T022a computes valid per‑sample stats (Variance, Entropy, Skewness, Kurtosis).
- **CRITICAL**: T022b computes Global Covariance/Eigenvalue via covariance matrix on *filtered* dataset.
- **CRITICAL**: T022c computes Per‑Sample Mahalanobis Distance on *filtered* data when Random Forest is used.
- **CRITICAL**: T030c trains the Mean Predictor inline, compares R²/MAE, and mandates a **paired t-test on absolute errors** as the primary validation method, with a fallback to reporting `p_value_ttest: null` if assumptions are violated. **NO bootstrap**. Task does NOT fail if p >= 0.05; it reports status.
- **CRITICAL**: T027a uses **quantile‑based binning** for stratified splitting of continuous targets.
- **CRITICAL**: T024 must filter the dataframe, write to `data/processed/cleaned_data.parquet`, write `data/processed/fidelity_loss_summary.json`, AND write `data/processed/lineage_report.json` before T025a reads it.
- **CRITICAL**: T025a-core must read the *filtered* output from T024.
- **CRITICAL**: T001d creates a *provisional* template that T038 updates.
- **CRITICAL**: T037 is NOT parallel [P] and does NOT auto-invoke T037b (it invokes its own logic).
- **CRITICAL**: T022b depends on T024 (filtered data), NOT T012.
- **CRITICAL**: T022c depends on T027d (Model Selection) to prevent execution when Ridge is selected.
- **CRITICAL**: T030c allows the Random Forest R² > 0 as a pass condition only if the paired t‑test is significant; otherwise the task reports "not significant" but does NOT fail.
- **CRITICAL**: T025a-core does NOT depend on T022c. T025a-core handles the absence of Mahalanobis distance gracefully.
- **CRITICAL**: T022b runs AFTER T024 in the execution graph to satisfy FR-002.
- **CRITICAL**: T014 prioritizes metadata parsing over column presence.
- **CRITICAL**: T029 explicitly outputs `residuals.csv`.
- **CRITICAL**: T003 mandates `pip freeze`.
- **CRITICAL**: T027d sets `model_type = "fail"` for N < 30 and continues the pipeline to generate a failure report.
- **CRITICAL**: T000 mandates the execution of the Reference-Validator Agent and recording of verification results.
- **CRITICAL**: T025a-core must generate `data/processed/lineage_report.json` to satisfy SC-004. (Moved to T024).
- **CRITICAL**: T024 is now in Phase 2 to ensure US2 independence.
- **CRITICAL**: T027d is now in Phase 2 to ensure US2 independence.
- **CRITICAL**: T024 generates `lineage_report.json` to satisfy SC-004.
- **CRITICAL**: T022b is unconditional and has a fallback to raw data if filtered data is insufficient.
- **CRITICAL**: T037 distinguishes between `--mode=research` (fail if missing) and `--mode=test` (synthetic fallback).
- **CRITICAL**: T037b defaults to N=50 to test Ridge path.
- **CRITICAL**: T000b handles synthetic fallback in `research.md`.
- **CRITICAL**: T030c performs t-test on absolute errors.
- **CRITICAL**: T000c and T000d are created to ensure executability.
- **CRITICAL**: T022c is not [P] and depends on T027d.
- **CRITICAL**: T025a-core handles missing Mahalanobis gracefully.
- **CRITICAL**: T024 and T027d are blocking prerequisites for Phase 4.