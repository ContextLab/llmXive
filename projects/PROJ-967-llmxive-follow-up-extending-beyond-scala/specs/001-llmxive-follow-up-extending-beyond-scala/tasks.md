# Tasks: llmXive Follow-up: Teacher Entanglement vs. Scalar Distillation Loss

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-beyond-scala/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, contract definition, and artifact scaffolding

- [ ] T001a [P] Create project directory structure: Create directories `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests` relative to repository root. **REPLACES**: None.
- [ ] T000a-struct [P] Create `research.md` schema template: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/research.md` with a "Verified datasets" section structure. **Content**: If the file does not exist, create it. If it exists, append/ensure the `verified_datasets` key is present. Write the following exact YAML content to the file (using empty values):
```yaml
verified_datasets:
 - dataset_id: "z-reward"
   title_token_overlap:
   checksum:
   verification_date:
   source_type:
```
**VERIFICATION**: After writing, read the file and assert it contains the `verified_datasets` key. **DEPENDS**: T001a.
- [ ] T000c [P] Create `verify_dataset.py`: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/verify_dataset.py` with logic to validate dataset ID 'Z-Reward', check token overlap using **whitespace split** tokenization and a configurable threshold (default set to a standard confidence level, read from `research.md` if available), and return verification status. **Output Contract**: The script must print a JSON object to `stdout` containing `{"verified": bool, "checksum": str, "source_type": str}`. **DEPENDS**: T001a.
- [ ] T000b [US1] Populate `research.md` and `config.json` with verification results: Execute `code/verify_dataset.py` (created in T000c) to verify dataset ID 'Z-Reward'. **Command**: `python code/verify_dataset.py --dataset-id Z-Reward`. **CRITICAL**: Read the JSON output from `stdout` of T000c. Extract the keys `title_token_overlap`, `checksum`, and `source_type` and write them to `research.md`. If real data verification fails and synthetic is used, write `source: synthetic` and `note: synthetic_fallback` to `research.md`. **CRITICAL**: If `source_type` is 'synthetic', also write `IS_SYNTHETIC_RUN: true` to `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/config.json` (NOT research.md) in the same atomic write operation. **DEPENDS**: T000a-struct, T000c.
- [ ] T001b [P] Create empty project files: Create empty files `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/.gitignore`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/pytest.ini`. **DEPENDS**: T001a.
- [ ] T001c [P] Write dependencies: Write `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt` with **pinned versions** (e.g., `pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `ruff==0.9.0`, `black==24.8.0`). **CRITICAL**: Do not use version ranges; use exact `==` pins.
- [ ] T001d [P] Create **provisional** dataset schema template: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/contracts/dataset.schema.yaml` with the following exact YAML content:
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
**NOTE**: This task is sequential; it must complete before Phase 4 begins. **DEPENDS**: T001a.
- [ ] T001f [P] Create output schema contract: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/contracts/output.schema.yaml` defining the structure of `data/processed/features.json` (e.g., `sample_id`, `variance`, `entropy`, `skewness`, `kurtosis`, `mahalanobis_distance`, `fidelity_loss`). **DEPENDS**: T001a.
- [ ] T001e [P] Initialize output artifacts: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json` with content `[]` and `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json` with content `{}` to prevent file-not-found errors in downstream tasks. **DEPENDS**: T001a.
- [ ] T003a [P] Create linting and formatting config: Create `.ruff.toml` and `pyproject.toml` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with pinned tool versions (`ruff==0.9.0`, `black==24.8.0`) and configuration to satisfy Constitution Principle I. **Content for `.ruff.toml`**:
```toml
[lint]
select = ["E", "F", "W", "I", "D"]
ignore = ["D100", "D104"]
line-length = 100

[lint.pydocstyle]
convention = "google"

[format]
quote-style = "double"
indent-style = "space"
```
**DEPENDS**: T001c.
- [ ] T003b-venv [US0] Create virtualenv: Create a virtualenv in `venv` directory. **Command**: `python -m venv venv`. **CRITICAL**: This task is a hard prerequisite for T003b-install. **DEPENDS**: T003a, T001c.
- [ ] T003b-install [US0] Install dependencies: Activate virtualenv and install dependencies. **Command**: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows), then `pip install -r code/requirements.txt`, then `pip freeze > code/requirements.lock.txt`. **CRITICAL**: This task must run after T003b-venv. **DEPENDS**: T003b-venv.
- [ ] T003b-verify [US0] Verify lock file: Verify `code/requirements.lock.txt` exists and contains pinned versions. **DEPENDS**: T003b-install.
- [ ] T000d [P] Create synthetic data generator: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/synthetic_data.py` with a schema-compliant generator function that accepts `--n-samples` and `--seed` arguments to generate a configurable number of synthetic samples. **DEPENDS**: T001d.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Acquisition, Filtering, Model Selection, and Global Feature Engineering.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase MUST complete before Phase 4 begins. **DEPENDENCY NOTE**: Phase 2 tasks (T024, T027d) are blocking prerequisites for all User Stories (Phase 3, 4, 5). Independent Implementation of US2 is subject to the completion of Phase 2.

- [ ] T005 [P] Create `code/ingest.py` skeleton with argument parsing and logging setup. **DEPENDS**: T001a.
- [ ] T006 [P] Create `code/features.py` skeleton with statistical helper functions. **DEPENDS**: T001a.
- [ ] T007 [P] Create `code/train.py` skeleton with scikit‑learn model configuration. **DEPENDS**: T001a.
- [ ] T008 [P] Create `code/evaluate.py` skeleton for metrics calculation. **DEPENDS**: T001a.
- [ ] T009 [P] Setup `tests/` directory structure and `pytest.ini`. **DEPENDS**: T001a.
- [ ] T037 [US1] Download Z‑Reward evaluation dataset (real data) with strict fallback:
 1. **Primary**: Verify dataset ID via `code/verify_dataset.py` (T000c); if verified, load with `datasets.load_dataset("z-reward")`.
 2. **Secondary**: If primary verification fails, check environment variable `Z_REWARD_ARCHIVE_PATH` for a local `.zip` or `.tar.gz` archive, extract to `data/raw/` (using `tar -xzf $Z_REWARD_ARCHIVE_PATH -C data/raw/` or `unzip $Z_REWARD_ARCHIVE_PATH -d data/raw/`), and load.
 3. **Adaptive Fallback**:
 - If the environment variable `MODE` is set to `research` and no real data is found, **invoke T037c** (Automatic Synthetic Fallback) to generate synthetic data. **CRITICAL**: This satisfies FR-007 (Real data only for research) by generating a schema-compliant synthetic dataset when real data is missing, rather than failing the pipeline. **Command**: `python code/synthetic_data.py --n-samples 10000 --output data/raw/z_reward_synthetic.parquet`.
 - If the environment variable `MODE` is set to `test` and no real data is found, **invoke T037c** to generate synthetic data.
 4. **Verification**: After loading, assert presence of required columns (`prompt`, `image_url`, `teacher_scores`, `student_scalar`, `human_annotations`, `primary_dimension`). If any are missing, raise a clear `RuntimeError`.
 5. **OUTPUT**: Write the loaded dataset to `data/raw/z_reward.parquet` (or `z_reward_synthetic.parquet` if fallback).
 6. **OUTPUT**: Write `data/raw/validation_log.json` containing keys: `source`, `status`, `message`, `schema_valid`, `sample_count`.
 7. **OUTPUT**: Write `data/processed/valid_sample_count.json` with keys `total_samples`, `valid_samples`, `excluded_count`. **CRITICAL**: This satisfies SC-005.
 **DEPENDS**: T000b, T001a, T000d.
- [ ] T037c [US1] Generate synthetic dataset automatically (FALLBACK):
 1. **Trigger**: Invoked automatically by T037 if real data is missing.
 2. **Generate**: Create a Pandas DataFrame matching the schema with columns `prompt`, `image_url`, `teacher_scores`, `student_scalar`, `human_annotations`, `primary_dimension`. **DEFAULT**: N=10,000 samples.
 3. **Noise Independence**: Teacher scores are sampled from `np.random.normal(loc=5, scale=2, size=...)`; human annotations are sampled independently from a separate `np.random.normal(loc=5, scale=2,...)` *with a different seed*, guaranteeing independent noise structures.
 4. **Output**: Write to `data/raw/z_reward_synthetic.parquet`.
 5. **Flag**: Set `IS_SYNTHETIC_RUN: true` in `data/processed/config.json` and `research.md`.
 6. **CRITICAL**: This task is strictly for automatic fallback. Do NOT invoke manually for unit testing (use T037b for that).
 **DEPENDS**: T001d, T000d.
- [ ] T037b [US1] Generate synthetic dataset for unit testing (MANUAL INVOCATION ONLY):
 1. **Input**: None (uses fixed random seed for reproducibility).
 2. **Generate**: Create a Pandas DataFrame matching the schema with columns `prompt`, `image_url`, `teacher_scores`, `student_scalar`, `human_annotations`, `primary_dimension`. **DEFAULT**: N=50 samples (configurable via `--n-samples`) to test Ridge Regression path. **COMMAND**: `python code/synthetic_data.py --n-samples 50 --seed 42 --output data/raw/mock_z_reward.parquet`.
 3. **Noise Independence**: Teacher scores are sampled from `np.random.normal(loc=5, scale=2, size=...)`; human annotations are sampled independently from a separate `np.random.normal(loc=5, scale=2,...)` *with a different seed*, guaranteeing independent noise structures.
 4. **Output**: Write to `data/raw/mock_z_reward.parquet`.
 5. **Flag**: Set `IS_MOCK_DATA = true` in `data/processed/config.json`. **CRITICAL**: Do NOT write `IS_SYNTHETIC_RUN: true` to `results.json` or `research.md` for this task.
 6. **CRITICAL**: This synthetic data is for unit‑testing only; final results must use real data when available. **CRITICAL**: The generated `human_annotations` are **mocks for code structure testing only** and MUST NOT be used to validate the hypothesis or calculate final fidelity loss metrics. **DO NOT** invoke automatically from T037. This task is strictly manual. **DEPENDS**: T001d, T000d.
- [ ] T038 [US1] Schema Discovery and Validation:
 1. Read the raw dataset file produced by T037 (or T037b) from `data/raw/`.
 2. Perform schema discovery, mapping actual column names to logical fields.
 3. Validate against the provisional template `contracts/dataset.schema.yaml`.
 4. If discrepancies exist, **overwrite** `contracts/dataset.schema.yaml` with the final validated schema.
 5. Raise an error on critical mismatches (e.g., missing rubric dimensions).
 **DEPENDS**: T037 OR T037b.
- [ ] T014 [US1] Implement primary quality dimension identification logic (Shared Utility):
 1. **Primary Rule**: Derive the `primary_dimension` from prompt metadata using a fixed schema rule (e.g., parse `prompt_metadata.primary_dimension` or a deterministic hash of the prompt text mapping to one of the four dimensions).
 2. **Exclusion Rule**: If the metadata rule yields no result, **EXCLUDE** the sample from the dataset. Log the exclusion. **CRITICAL**: Do NOT use a fallback column value.
 3. **Output**: Ensure `primary_dimension` is NEVER null. Add a log entry for samples using the exclusion.
 4. **CRITICAL**: This logic is now a shared utility function used by T024 to ensure the rule exists before the lineage report is generated. **CRITICAL**: This satisfies FR-003 and FR-006 by excluding samples rather than defaulting to a biased value.
 **DEPENDS**: T038.
- [ ] T012 [US1] Implement Z‑Reward dataset ingestion in `code/ingest.py` (load prompts, images, teacher scores, student scores, human annotations, **logits**, and **pre-computed inference outputs**). Write output to `data/processed/raw_data.parquet`. **DEPENDS**: T037 OR T037b. Must be schema‑agnostic; uses provisional schema from T001d for initial column mapping. Supports `--use-mock-data` flag if synthetic data was generated (manual only).
- [ ] T013 [US1] Implement alignment logic in `code/ingest.py`: match teacher distributions, student scalars, and human annotations by sample ID. If `student_scalar` is missing, mark the sample with `excluded_reason: 'missing_student_scalar'` (do not raise). **DEPENDS**: T012.
- [ ] T015 [US1] Implement chunked loading or sampling logic in `code/ingest.py` to keep RAM usage < 7 GB. **DEPENDS**: T012.
- [ ] T016 [US1] Add summary output in `code/ingest.py`: print sample counts, missing‑data flags, and dimension coverage stats. **DEPENDS**: T012.
- [ ] T024 [Foundational] Implement "dimensional fidelity loss" calculation and filtering:
 1. **Input**: Read the aligned dataset from `data/processed/raw_data.parquet` (output of T012). **CRITICAL**: This task depends on T012 (Ingestion) to ensure data is aligned.
 2. **Derivation Rule**: Read the derivation rule logic from T014 (now a shared utility) to determine `primary_dimension`.
 3. **Verification**: Assert that the derivation logic **does not** reference teacher or student scores. If it does, raise an error. **CRITICAL**: This ensures target independence (SC-004).
 4. **Calculate Target**: Compute MAE between `student_scalar` and the human‑annotated score for the sample's `primary_dimension`.
 5. **Filter**: Exclude samples where `primary_dimension` is null, human annotation for that dimension is missing, or `student_scalar` is missing.
 6. **Output**: Write the filtered dataframe to `data/processed/cleaned_data.parquet`.
 7. **Output**: Write summary statistics (`mean`, `median`, `count`, `excluded_count`) to `data/processed/fidelity_loss_summary.json`.
 8. **Output**: Generate `data/processed/lineage_report.json` with schema `[{sample_id, source_type: "metadata", dimension, derivation_rule_hash}]`. **derivation_rule_hash** MUST be the **SHA-256** hash of the *actual source code* of the function `derive_primary_dimension_from_metadata` (e.g., by hashing the function's `inspect.getsource()`) using `hashlib.sha256(..., usedforsecurity=False).hexdigest()`. This report MUST explicitly state "Source: Metadata Only" for every sample to prove target independence (SC-004). It must verify that `primary_dimension` was derived solely from metadata (using the rule from T014) and not model scores. **CRITICAL**: This satisfies SC-004.
 9. **BLOCKING**: This task must complete before T022b (Global Covariance), T027d (Model Selection), and Phase 4 tasks.
 **DEPENDS**: T012, T014.
- [ ] T027d [US3] Model‑selection task:
 1. **MUST run after T024 completes**.
 2. Read `data/processed/cleaned_data.parquet` (output of T024) and count N.
 3. If N < 30 → set `model_type = "fail"`. **Action**: Write `{"model_type": "fail", "n_samples": N, "threshold": 30, "reason": "Critical Power Limitation: N < 30", "status": "unsupported"}` to `data/processed/model_selection.json`. **CRITICAL**: If `model_type == "fail"`, SKIP T022a, T022c, and T027b. Proceed directly to T027e.
 4. If 30 ≤ N < 300 → set `model_type = "ridge"` (use Ridge Regression). **Label**: `low_power`.
 5. If N ≥ 300 → set `model_type = "rf"` (use Random Forest) and ensure Mahalanobis distance will be computed (T022c).
 6. Write `data/processed/model_selection.json` with the selected `model_type`, `n_samples`, `threshold`, and `reason`.
 7. **CRITICAL**: If `model_type` is "ridge" or "rf", proceed to T028 (k-fold CV).
 **DEPENDS**: T024.
- [ ] T022b-raw [US2] **Global Covariance Matrix (Raw Data)**:
 1. **Input**: Read the *raw* dataset from `data/processed/raw_data.parquet` (output of T012) to satisfy FR-002 "Entire Dataset" requirement. **CRITICAL**: This task depends on T037 (Download) to ensure raw data exists.
 2. **Execution**: This task MUST run regardless of model selection logic (Ridge vs RF) to test the global hypothesis on the full population.
 3. Extract the N × 4 matrix of teacher scores for the **four rubric dimensions** (Alignment, Realism, Aesthetics, Plausibility).
 4. Compute the covariance matrix (`numpy.cov`, `rowvar=False`).
 5. Compute the dominant eigenvalue (largest eigenvalue) of this matrix.
 6. **Validation**: Validate that the input file contains a square numeric matrix and that eigenvalues are real and finite.
 7. Write the covariance matrix to `results/covariance_matrix_raw.json`.
 8. Write the dominant eigenvalue to `results/dominant_eigenvalue_raw.json`.
 **DEPENDS**: T037.
- [ ] T022b [US2] **Global Covariance Matrix (Filtered Data)**:
 1. **Input**: Read the *filtered* dataset from `data/processed/cleaned_data.parquet` (output of T024). **CRITICAL**: Use the cleaned dataset to ensure consistency with the target variable and data hygiene principles.
 2. **Execution**: This task MUST run regardless of model selection logic (Ridge vs RF) to test the global hypothesis.
 3. Extract the N × 4 matrix of teacher scores for the **four rubric dimensions** (Alignment, Realism, Aesthetics, Plausibility).
 4. Compute the covariance matrix (`numpy.cov`, `rowvar=False`).
 5. Compute the dominant eigenvalue (largest eigenvalue) of this matrix.
 6. **Validation**: Validate that the input file contains a square numeric matrix and that eigenvalues are real and finite.
 7. Write the covariance matrix to `results/covariance_matrix.json`.
 8. Write the dominant eigenvalue to `results/dominant_eigenvalue.json`.
 **DEPENDS**: T024.
- [ ] T022a [US2] Implement **Per‑Sample Entanglement Score**:
 1. **Input**: Read the *filtered* dataset from `data/processed/cleaned_data.parquet` (output of T024).
 2. **Check**: Verify `results/dominant_eigenvalue.json` exists (output of T022b). If missing, raise error.
 3. For each sample, extract the 4‑dimensional teacher score vector.
 4. Compute Variance, Entropy, Skewness, and Kurtosis.
 5. **Read Global Metric**: Read the dominant eigenvalue from `results/dominant_eigenvalue.json` and append it as a column `global_eigenvalue` to every row in the dataframe.
 6. **Output**: Append these features to the dataframe AND append the **global dominant eigenvalue** (from T022b) as a column `global_eigenvalue` to each row. Write to `data/processed/entanglement_scores.csv`. **CRITICAL**: Do NOT compute the eigenvalue per-sample; it is a global metric passed to each sample.
 **DEPENDS**: T024, T022b.
- [ ] T022c [US2] **Per-Sample Mahalanobis Distance** (Unconditional):
 1. **Unconditional Execution**: Run this task regardless of model type. It is a foundational feature engineering task.
 2. **MUST run after T024 and T022b**. **CRITICAL**: Ensure T022b has completed and written `results/dominant_eigenvalue.json` before starting this task.
 3. Input: Use the *filtered* dataset from `data/processed/cleaned_data.parquet` (output of T024) and the **global** covariance matrix (from T022b).
 4. Compute Mahalanobis distance for each sample:
 $D_M(x) = \sqrt{(x-\mu)^T \Sigma^{-1} (x-\mu)}$.
 5. Handle singular covariance matrices with **`numpy.linalg.pinv` with `rcond=1e-15`**, issuing a warning.
 6. Append `mahalanobis_distance` column and write to `data/processed/entanglement_scores.csv`.
 **DEPENDS**: T024, T022b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 1 - Dataset Ingestion and Ground‑Truth Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest Z‑Reward dataset, align teacher/student outputs with human annotations, and handle missing data gracefully.

**Independent Test**: A script loads the dataset, verifies the presence of all four rubric dimensions, flags missing data, and outputs a summary without crashing.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for data loading and schema validation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`
- [ ] T011 [P] [US1] Integration test for missing data handling and exclusion logic in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Entanglement Quantification and Feature Engineering (Priority: P2)

**Goal**: Calculate statistical descriptors (variance, entropy, skewness, kurtosis) per sample, and a valid global covariance metric (Dominant Eigenvalue) for the teacher's score distributions across the dataset, and a per‑sample Mahalanobis distance.

**Independent Test**: A script processes a fixed subset of teacher distributions and outputs a JSON record with calculated features, handling zero‑variance cases gracefully.

**⚠️ NOTE**: Phase 4 depends on Phase 2 completion (T024, T027d).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for variance, entropy, skewness, kurtosis calculations in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`
- [ ] T019 [P] [US2] Unit test for zero‑variance edge case handling in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement variance and range calculation for dimensions in `code/features.py`. **DEPENDS**: T012.
- [ ] T021 [US2] Implement entropy, skewness, and kurtosis calculation for teacher distributions in `code/features.py`. **DEPENDS**: T012.
- [ ] T023 [US2] Implement zero‑variance handling in `code/features.py`: set entropy to 0 and variance to 0 without crashing. **DEPENDS**: T020.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train a CPU‑based model to predict fidelity loss using entanglement features, with k‑fold CV, permutation test, and null‑baseline comparison.

**Independent Test**: A script trains the model on a stratified random split (with quantile binning), runs 5‑fold CV, and outputs R², MAE, and permutation‑test p‑value without using GPU.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T043 [P] [US3] Unit test for Random Forest training and 5‑fold CV execution in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_train.py`
- [ ] T026 [P] [US3] Integration test for permutation test p‑value calculation in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_evaluate.py`

### Implementation for User Story 3

- [ ] T027a [US3] Configure training split:
 1. Read features from `data/processed/entanglement_scores.csv` (output of T022a/T022c).
 2. Perform quantile‑based binning on the target `fidelity_loss` for stratified `train_test_split(test_size=0.2, random_state=42)`.
 3. Store split indices in `data/processed/split_config.json`.
 4. **Conditional Model**: Based on `model_type` from T027d, select the appropriate estimator (Random Forest or Ridge).
 **DEPENDS**: T022a, T022c, T027d.
- [ ] T027b [US3] Prepare for training:
 1. If `model_type == "rf"` → proceed to T027f.
 2. If `model_type == "ridge"` → proceed to T027g.
 3. If `model_type == "fail"`, skip training and proceed to T027c.
 **DEPENDS**: T027a.
- [ ] T027f [US3] Train Random Forest (N>=300):
 1. Train `RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=2)`.
 2. Save the trained model object to `results/model.pkl`.
 **DEPENDS**: T027b.
- [ ] T027g [US3] Train Ridge Regression (30<=N<300):
 1. Train `Ridge(alpha=1.0, random_state=42)`.
 2. Save the trained model object to `results/model.pkl`.
 **DEPENDS**: T027b.
- [ ] T027c [US3] Save placeholder model when training is skipped (e.g., N < 30):
 1. If `model_type == "fail"`, write metadata `{"status":"fail", "message":"Critical Power Limitation: N < 30"}` to `data/processed/model_fail.json` (NOT model.pkl).
 2. Also write `{"status":"fail", "message":"Critical Power Limitation: N < 30"}` to `results/results.json`.
 **DEPENDS**: T027b.
- [ ] T027e [US3] Generate failure report for N < 30:
 1. **Trigger**: If `model_type == "fail"` (from T027d).
 2. **Action**: Write a detailed failure report to `results/results.json` with keys: `hypothesis_status: "unsupported"`, `reason: "Critical Power Limitation: N < 30"`, `r2: null`, `mae: null`, `p_value: null`.
 3. **Action**: Update `quickstart.md` to reflect the "unsupported" status.
 **DEPENDS**: T027d.
- [ ] T028 [US3] Implement k‑fold cross-validation:
 1. **Trigger**: Run this task if `model_type` is "rf" or "ridge" (from T027d). **CRITICAL**: This task MUST execute for BOTH Random Forest and Ridge Regression paths.
 2. **Execution**: Use the stratified bins from T027a.
 3. **Model**: Use the estimator selected in T027a (RF or Ridge).
 4. **Metric**: Compute mean R² and MAE across folds.
 5. **Output**: Write mean R², std dev, and MAE to `results/cv_metrics.json`.
 **DEPENDS**: T027a, T027d.
- [ ] T029 [US3] Evaluation script:
 1. Compute mean R², std dev, MAE on the test set.
 2. **OUTPUT**: Calculate residuals (y_true - y_pred) and write them to `data/processed/residuals.csv`.
 3. Call `calculate_permutation_pvalue` (sub-task of T030c) and store `p_value_permutation`.
 **DEPENDS**: T028.
- [ ] T030c [US3] Null Baseline Comparison (strict):
 1. **MUST run after T029 completes**.
 2. **Check**: If `model_type == "fail"`, skip t-test and write `{"hypothesis_status": "unsupported", "reason": "N < 30"}` to `results.json`.
 3. **Normal Path**: Train a `DummyRegressor(strategy='mean')` on the training split.
 4. Evaluate on the test set to obtain baseline R² and MAE.
 5. **Metric Comparison**: Compute the aggregate MAE for both models. Perform a **paired t-test** on the MAE of the model vs the null baseline using `scipy.stats.ttest_rel` to compare the MAE metrics as required by SC-002.
 6. **Reporting**: Compute p-value. If p < 0.05, report "significant"; otherwise report "not significant". **CRITICAL**: If p >= 0.05, the hypothesis MUST be flagged as "unsupported" in `results.json` and `quickstart.md` using the key `hypothesis_status`. **DO NOT** treat this as a neutral success state.
 7. **OUTPUT**: Write `baseline_r2`, `p_value_ttest`, `t_test_status` (significant/not significant/unsupported), and `p_value_permutation` to `results/results.json`. **CRITICAL**: The `p_value_ttest` key must be explicitly written to `results/results.json`.
 **DEPENDS**: T029, T027a.
- [ ] T030d [US3] Implement Partial Correlation Control:
 1. **MUST run after T029 completes**.
 2. **Input**: Use the features from `data/processed/entanglement_scores.csv` and the target `fidelity_loss`.
 3. **Control Variables**: Use `student_scalar` and `teacher_mean` as control variables to isolate the "entanglement" effect.
 4. **Calculation**: Compute the partial correlation between the primary entanglement feature (e.g., variance) and `fidelity_loss`, controlling for the base error magnitude.
 5. **Reporting**: Output the partial correlation coefficient and p-value to `results/partial_correlation.json`.
 6. **OUTPUT**: ALSO write the partial correlation coefficient and p-value to `results/results.json` under keys `partial_correlation_coefficient` and `partial_correlation_p_value`.
 7. **Validation**: This step is required by the Plan's "Complexity Tracking" to avoid circularity.
 **DEPENDS**: T029.
- [ ] T031 [US3] Integrate training and evaluation:
 1. Run the full pipeline: feature generation → model selection → training → CV → evaluation → null baseline comparison → partial correlation.
 2. Ensure `results/results.json` contains the required keys (`p_value_permutation`, `p_value_ttest`, `baseline_r2`, `mean_r2`, `mean_mae`, `hypothesis_status`, `partial_correlation_coefficient`, `partial_correlation_p_value`).
 **DEPENDS**: T027a, T027f, T027g, T028, T029, T030c, T030d.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Create `quickstart.md` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with explicit steps to reproduce the full pipeline (Install → Download → Ingest → Train → Evaluate) to satisfy Constitution Principle I. **DEPENDS**: T031.
- [ ] T033 [P] Code cleanup and refactoring: Run `ruff check` and `black --check` on `code/` and `tests/`. Fix all errors until `ruff` exits with code 0 and `black` reports no changes. **DEPENDS**: T031.
- [ ] T034a [P] Profile and optimize feature engineering loop (Part 1): Run `python -m cProfile -o results/profile.prof code/features.py` using a random sample of the full dataset (or the maximum available subset) to estimate runtime.
 1. **Research Question**: Identify bottlenecks limiting performance.
 2. **Method**: Systematic profiling; reference scikit‑learn and scipy docs.
 3. **Output**: Generate `results/profile_report.txt` (text summary) with bottleneck analysis (top functions by cumulative time).
 **DEPENDS**: T022a.
- [ ] T034b [P] Profile and optimize feature engineering loop (Part 2): Refactor `code/features.py` based on `results/profile_report.txt` from T034a.
 1. **Optimization**: If estimated runtime > 30 min, refactor to vectorized NumPy operations; ensure total runtime stays < 6 h on the CI runner.
 **DEPENDS**: T034a.
- [ ] T035a [P] Additional unit tests for edge cases: Write test for empty dataset in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`. **DEPENDS**: T001a.
- [ ] T035b [P] Additional unit tests for edge cases: Write test for NaN values in teacher logits in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`. **DEPENDS**: T001a.
- [ ] T035c [P] Additional unit tests for edge cases: Write test for missing human annotations for all dimensions in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_ingest.py`. **DEPENDS**: T001a.
- [ ] T035d [P] Additional unit tests for edge cases: Write test for zero‑variance distributions in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests/test_features.py`. **DEPENDS**: T001a.
- [ ] T036 [P] Run `quickstart.md` validation to ensure reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**. Includes Data Acquisition, Filtering, Model Selection, and Global Feature Engineering.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Acquisition (Phase 2)**: Must complete before ANY downstream tasks.
- **T022b and T024 are parallelizable after Phase 2**
- **T022c depends on T022b and T024**
### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for aligned data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (target calculation) and US2 (features)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **CRITICAL**: All data loading tasks must use real, reachable URLs or package-based fetchers.
- **CRITICAL**: All model training tasks must be CPU‑only (no CUDA, no 8-bit quantization, no large LLMs). Use small models and sampled datasets if necessary.
- **CRITICAL**: Entanglement features (T022a, T022c) MUST be computed using **per-sample** statistical descriptors (variance, entropy, skewness, kurtosis, Mahalanobis Distance). **NO** global constants are allowed as per-sample features EXCEPT the global eigenvalue which is passed to each sample.
- **CRITICAL**: T022b computes Global Covariance/Eigenvalue via covariance matrix of the *FILTERED* dataset (output of T024), satisfying Constitution Principle VI and FR-002. **T022b-raw** computes on RAW data for FR-002 compliance.
- **CRITICAL**: T022c computes Per‑Sample Mahalanobis Distance on the *filtered* dataset using the *global* stats (from T022b) to ensure statistical consistency.
- **CRITICAL**: Target variable (T024) MUST be calculated in `code/ingest.py` using metadata‑based dimension selection (T014), independent of model scores.
- **CRITICAL**: T037 MUST invoke T037c (Automatic Synthetic Fallback) if real data is missing, ensuring pipeline executability.
- **CRITICAL**: T037b MUST explicitly state that generated human annotations are mocks for code structure testing only.
- **CRITICAL**: T024 MUST verify that target derivation does not reference model scores.
- **CRITICAL**: T030c MUST flag the hypothesis as "unsupported" if p >= 0.05.
- **CRITICAL**: T027d sets `model_type = "fail"` for N < 30 and continues the pipeline to generate a failure report, skipping feature engineering if applicable.
- **CRITICAL**: T003 mandates `pip freeze` to a lock file.
- **CRITICAL**: T022b is unconditional and has a fallback to raw data if filtered data is insufficient.
- **CRITICAL**: T037 distinguishes between `MODE=research` (auto-fallback) and `MODE=test` (auto-fallback) and `MODE=manual` (fail if missing).
- **CRITICAL**: T037b defaults to N=50 to test Ridge path.
- **CRITICAL**: T014 must enforce strict exclusion (no fallback to default values) to prevent bias in the target variable calculation.
- **CRITICAL**: T037 must not invoke T037b automatically; T037b is strictly manual.
- **CRITICAL**: T022a must not include the dominant eigenvalue as a per-sample feature computed per sample; it is a global metric passed to each sample.
- **CRITICAL**: T027d must not skip the pipeline if N < 30; it must continue to generate a failure report.
- **CRITICAL**: T030c must not treat a non-significant p-value as a success; it must flag the hypothesis as unsupported.
- **CRITICAL**: T022b uses the *filtered* dataset (T024 output) for global covariance, ensuring consistency with Constitution Principle VII.
- **CRITICAL**: T030d implements Partial Correlation to control for circularity as required by the Plan.
- **CRITICAL**: T028 must run for both RF and Ridge paths as triggered by T027d.
- **CRITICAL**: T030c must output `p_value_ttest` to `results.json`.
- **CRITICAL**: T030d must output partial correlation metrics to `results.json`.