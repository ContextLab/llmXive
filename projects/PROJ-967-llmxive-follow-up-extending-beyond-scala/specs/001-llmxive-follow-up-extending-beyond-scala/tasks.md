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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, contract definition, and artifact scaffolding

- [ ] T001a [P] Create project directory structure: Create directories `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/tests` relative to repository root.
- [ ] T001b [P] Create empty project files: Create empty files `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/.gitignore`, `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/pytest.ini`.
- [ ] T001c [P] Write dependencies: Write `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/requirements.txt` with **pinned versions** (`pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `pyyaml==6.0.1`, `pytest==7.4.0`, `ruff==0.9.0`, `black==24.8.0`).
- [ ] T001d [P] Create provisional dataset schema template: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/contracts/dataset.schema.yaml` with the exact YAML content matching the OxfordPets structure + simulated outputs.
- [ ] T001f [P] Create output schema contract: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/specs/001-llmxive-follow-up-extending-beyond-scala/contracts/output.schema.yaml` defining the structure of `data/processed/features.json`.
- [ ] T001e [P] Initialize output artifacts: Create `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/processed/features.json` with content `[]` and `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/results/results.json` with content `{}`.
- [ ] T003a [P] Create linting and formatting config: Create `.ruff.toml` and `pyproject.toml` in `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/` with pinned tool versions and configuration.
- [ ] T003b-venv [P] Create virtualenv: `python -m venv venv`.
- [ ] T003b-install [P] Install dependencies: Activate virtualenv and run `pip install -r code/requirements.txt`; then `pip freeze > code/requirements.lock.txt`.
- [ ] T003b-verify [P] Verify lock file exists and contains pinned versions.
- [ ] T000d [P] Create synthetic data generator: Add `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/simulate.py` with CLI `--n-samples` and `--seed` to generate synthetic teacher/student data.

## Phase 2: Data Acquisition & Simulation (Foundational)

**Purpose**: Obtain data (real or synthetic) and prepare it for downstream processing.

- [ ] T037 [FR-001][SC-005][P] **Data Producer**  
  1. **Attempt Real Load**: Try to load the Z‑Reward evaluation dataset via its documented source. If unavailable, log failure.  
  2. **Fallback Load**: Fetch the verified `oxford_pets` dataset via `datasets.load_dataset("oxford_pets", split="test", streaming=False)`.  
  3. **Simulate Distributions**: Invoke `code/simulate.py` to generate teacher score distributions (4 rubric dimensions) and student scalar outputs for each image.  
  4. **Generate Annotations**: Produce synthetic human annotations (independent of teacher scores) for each sample.  
  5. **Write Unified Dataset**: Save to `data/raw/oxford_pets_simulated.parquet`.  
  6. **Validation Log**: Write `data/raw/validation_log.json` with keys `source`, `status`, `message`, `schema_valid`, `sample_count`.  
  7. **Sample Count Log**: Write `data/processed/valid_sample_count.json` with `total_samples`, `valid_samples`, `excluded_count`.  
  **Depends**: T001a, T000d.

- [ ] T037z [SC-005][P] **Dataset Availability Logging**  
  Record the inability to locate the Z‑Reward dataset and the decision to use the synthetic OxfordPets pipeline in `data/raw/validation_log.json`.  
  **Depends**: T037.

- [ ] T037b [P] **Synthetic Unit‑Test Dataset**  
  Generate a small synthetic dataset (`N=50`) for unit testing via `simulate.py --n-samples 50 --seed 42 --output data/raw/mock_oxford_pets.parquet`. Include mock human annotations (not for final analysis).  
  **Depends**: T001d, T000d.

- [ ] T037c [P] **Fail‑Loud Handling**  
  If both real data load and synthetic generation fail (e.g., schema mismatch), raise a clear `RuntimeError` and abort the pipeline. If synthetic generation succeeds, log "Synthetic generation successful; skipping fail‑loud".  
  **Depends**: T037.

- [ ] T038 [P] **Schema Discovery & Validation**  
  1. Read the raw dataset file from `data/raw/`.  
  2. Infer actual column names and map to logical fields.  
  3. Validate against provisional `contracts/dataset.schema.yaml`.  
  4. On discrepancy, overwrite `contracts/dataset.schema.yaml` with the discovered schema.  
  5. Raise error on missing rubric dimensions.  
  **Depends**: T037 or T037b.

- [ ] T012 [FR-001][P] **Ingestion**  
  Load `data/raw/oxford_pets_simulated.parquet` (or the mock file) into a Pandas DataFrame, validate required columns (`image_path`, `species_id`, `teacher_scores`, `student_scalar`, `human_annotations`, `primary_dimension`), and write to `data/processed/raw_data.parquet`.  
  **Depends**: T037, T038.

- [ ] T013 [P] **Alignment**  
  Verify that teacher distributions, student scalars, and human annotations align by sample ID; mark samples missing `student_scalar` with `excluded_reason: 'missing_student_scalar'`.  
  **Depends**: T012.

- [ ] T015 [P] **Chunked Loading**  
  Implement streaming or chunked reading in `code/ingest.py` to keep RAM usage < 7 GB for the full dataset.  
  **Depends**: T012.

- [ ] T016 [P] **Summary Output**  
  After ingestion, print sample counts, missing‑data flags, and per‑dimension coverage statistics.  
  **Depends**: T012.

- [ ] T014 [FR-003][P] **Primary Dimension Identification**  
  Derive `primary_dimension` via `hash(species_id) % 4` using the fixed rule string `"species_id_hash_mod_4_v1"` (hashing with Python's built‑in `hash` and modulo 4).  
  - Generate `data/processed/lineage_report.json` with entries `{sample_id, source_type:"metadata", dimension, derivation_rule:"species_id_hash_mod_4_v1", derivation_rule_hash:"<SHA‑256 of rule string>"}`.  
  - Log exclusions (null primary dimension) to `data/processed/exclusions_log.json`.  
  **Depends**: T038.

- [ ] T024 [FR-003][P] **Dimensional Fidelity Loss (Cross‑Dimensional)**  
  1. Read aligned data from `data/processed/raw_data.parquet`.  
  2. Use `primary_dimension` from T014; compute `target_dimension = (primary_dimension_index + 1) % 4`.  
  3. Compute MAE between `student_scalar` and the human annotation for `target_dimension`.  
  4. Exclude samples with missing `primary_dimension`, missing human annotation for the target, or missing `student_scalar`.  
  5. Log each exclusion to `exclusions_log.json`.  
  6. Write filtered data to `data/processed/cleaned_data.parquet`.  
  7. Write summary stats (`mean`, `median`, `count`, `excluded_count`) to `data/processed/fidelity_loss_summary.json`.  
  **Depends**: T012, T014.

## Phase 3: Global Entanglement Metrics (User Story 2)

- [ ] T022b-raw [FR-002][P] **Global Covariance Matrix (Raw Data)**  
  Compute covariance matrix and dominant eigenvalue on the teacher scores from the *raw* dataset (`data/processed/raw_data.parquet`). Write results to `results/covariance_matrix_raw.json` and `results/dominant_eigenvalue_raw.json`.  
  **Depends**: T012, T037.

- [ ] T022b-filtered [FR-002][P] **Global Covariance Matrix (Filtered Data)**  
  Compute covariance matrix and dominant eigenvalue on the *filtered* dataset (`data/processed/cleaned_data.parquet`). Write to `results/covariance_matrix.json` and `results/dominant_eigenvalue.json`.  
  **Depends**: T024.

- [ ] T022d [FR-007][P] **Global Entanglement Report**  
  Assemble `data/processed/global_entanglement_report.json` containing the covariance matrix, dominant eigenvalue, computation source (`filtered_data`), timestamp, and dimension list.  
  **Depends**: T022b-filtered.

- [ ] T022a [FR-002][P] **Per‑Sample Entanglement Features**  
  For each sample in `data/processed/cleaned_data.parquet`, compute variance, entropy, skewness, and kurtosis of the teacher score vector. Append these as columns and write to `data/processed/features.json`.  
  **Depends**: T024, T022b-filtered.

- [ ] T022c [FR-002][P] **Mahalanobis Distance (Unconditional)**  
  Using the global covariance matrix from `results/covariance_matrix.json`, compute Mahalanobis distance for each sample and merge as `mahalanobis_distance` into `data/processed/features.json`. Handle singular matrices with `numpy.linalg.pinv(rcond=1e-15)`.  
  **Depends**: T024, T022b-filtered.

## Phase 4: Model Selection & Training (User Story 3)

- [ ] T027d [FR-004][P] **Model Selection**  
  Based on sample count `N` from `data/processed/cleaned_data.parquet`:  
  * `N < 30` → `model_type = "fail"` (write failure metadata).  
  * `30 ≤ N < 300` → `model_type = "ridge"` (low‑power).  
  * `N ≥ 300` → `model_type = "rf"` (Random Forest).  
  Write `data/processed/model_selection.json`.  
  **Depends**: T024.

- [ ] T027h [P] **Global Feature Injection**  
  Read `results/dominant_eigenvalue.json` and append the value as column `global_eigenvalue` to every row of `data/processed/features.json`. Overwrite the file with enriched data.  
  **Depends**: T022a, T022b-filtered.

- [ ] T027a [P] **Training Split**  
  Load enriched features, perform quantile‑based stratified `train_test_split(test_size=0.2, random_state=42)`, and write split indices to `data/processed/split_config.json`.  
  **Depends**: T027h, T027d.

- [ ] T027b [P] **Prepare for Training**  
  Route to the appropriate training task based on `model_type` (`rf` → T027f, `ridge` → T027g, `fail` → T027c).  
  **Depends**: T027a.

- [ ] T027f [FR-004][P] **Train Random Forest**  
  Train `RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=2)` on the training split; save model to `results/model.pkl`.  
  **Depends**: T027b.

- [ ] T027g [FR-004][P] **Train Ridge Regression**  
  Train `Ridge(alpha=1.0, random_state=42)` on the training split; save model to `results/model.pkl`.  
  **Depends**: T027b.

- [ ] T027c [P] **Placeholder Model for Failure**  
  Write metadata `{"status":"fail","message":"Critical Power Limitation: N < 30"}` to `data/processed/model_fail.json` and `results/results.json`.  
  **Depends**: T027b.

- [ ] T027e [P] **Failure Report**  
  When `model_type == "fail"`, write a detailed report to `results/results.json` with keys `hypothesis_status:"unsupported"`, `reason:"Critical Power Limitation: N < 30"`, `r2:null`, `mae:null`, `p_value:null`; update `quickstart.md` to note unsupported status.  
  **Depends**: T027b.

- [ ] T028 [P] **k‑Fold Cross‑Validation**  
  Perform k‑fold CV using the estimator selected in T027a (RF or Ridge). Write mean R², std dev, and MAE to `results/cv_metrics.json`.  
  **Depends**: T027a, T027d.

- [ ] T029 [P] **Evaluation**  
  Evaluate the trained model on the held‑out test set; write predictions, compute residuals (`y_true - y_pred`) to `data/processed/residuals.csv`.  
  **Depends**: T028.

- [ ] T030c [P] **Null Baseline & Paired t‑Test**  
  1. Train `DummyRegressor(strategy='mean')` on the training split.  
  2. Evaluate on the test set to obtain baseline R² and MAE.  
  3. Perform a paired t‑test (`scipy.stats.ttest_rel`) on the residuals of the model vs. baseline.  
  4. Write `baseline_r2`, `baseline_mae`, `p_value_ttest`, `t_statistic`, `df`, and `t_test_status` (significant / not significant / unsupported) to `results/results.json`.  
  5. If `p_value_ttest >= 0.05`, set `hypothesis_status:"unsupported"` in `results.json`.  
  **Depends**: T029, T027a.

- [ ] T030d [P] **Partial Correlation Control**  
  Compute partial correlation between the primary entanglement feature (`variance`) and `fidelity_loss`, controlling for `student_scalar` and `teacher_mean`. Write `partial_correlation_coefficient` and `partial_correlation_p_value` to `results/partial_correlation.json` and also embed them in `results/results.json`.  
  **Depends**: T029.

- [ ] T031 [P] **Integrate Pipeline Outputs**  
  Verify that `results/results.json` contains all required keys (`p_value_permutation`, `p_value_ttest`, `t_statistic`, `df`, `baseline_r2`, `baseline_mae`, `mean_r2`, `mean_mae`, `hypothesis_status`, `partial_correlation_coefficient`, `partial_correlation_p_value`).  
  **Depends**: T027a, T027f, T027g, T028, T029, T030c, T030d.

## Phase 5: Polish & Cross‑Cutting Concerns

- [ ] T032 [P] **Documentation**  
  Create `quickstart.md` with reproducible steps (install, download, ingest, train, evaluate).  
  **Depends**: T031.

- [ ] T033 [P] **Code Cleanup**  
  Run `ruff check` and `black --check` on `code/` and `tests/`; fix all reported issues.  
  **Depends**: T031.

- [ ] T034a [P] **Feature Engineering Profiling**  
  Profile `code/features.py` on a representative data sample; write `results/profile_report.txt`.  
  **Depends**: T022a.

- [ ] T034b [P] **Feature Engineering Optimization**  
  Refactor `code/features.py` based on profiling results to ensure total runtime < 6 h on CI.  
  **Depends**: T034a.

- [ ] T035a [P] **Unit Test: Empty Dataset Handling**  
  Add test `test_ingest_empty.py` verifying graceful handling of an empty input dataset. This test uses mocked data and does not depend on the full pipeline (T012/T037). It only depends on T001a for infrastructure.  
  **Depends**: T001a.

- [ ] T035b [P] **Unit Test: NaN Values in Teacher Scores**  
  Add test `test_features_nan.py` ensuring NaNs are handled without crash. This test uses mocked data and does not depend on the full pipeline (T022a/T024/T012/T037). It only depends on T001a for infrastructure.  
  **Depends**: T001a.

- [ ] T035c [P] **Unit Test: Missing Human Annotations**  
  Add test `test_ingest_missing_annotations.py` confirming proper exclusion logging. This test uses mocked data and does not depend on the full pipeline (T012/T037). It only depends on T001a for infrastructure.  
  **Depends**: T001a.

- [ ] T035d [P] **Unit Test: Zero‑Variance Distributions**  
  Add test `test_features_zero_variance.py` checking variance/entropy handling. This test uses mocked data and does not depend on the full pipeline (T022a/T024/T012/T037). It only depends on T001a for infrastructure.  
  **Depends**: T001a.

- [ ] T036 [P] **Quickstart Validation**  
  Run the full pipeline via `quickstart.md` steps on a fresh runner to confirm reproducibility.  
  **Depends**: T031.

- [ ] T014a [P] **Spec Amendment Documentation**  
  Record the formal amendment that redefines the primary quality dimension rule and the cross‑dimensional fidelity loss computation, linking to FR‑003 and Principle VII.  
  **Depends**: T014.