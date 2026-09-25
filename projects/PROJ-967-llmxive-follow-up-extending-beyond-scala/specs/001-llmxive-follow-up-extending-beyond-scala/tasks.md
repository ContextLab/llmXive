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
- [X] T000d [P] Create synthetic data generator: Add `projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/code/simulate.py` with CLI `--n-samples` and `--seed` to generate synthetic teacher/student data.

## Phase 2: Data Acquisition & Simulation (Foundational)

**Purpose**: Obtain data (real or synthetic) and prepare it for downstream processing.

- [ ] T037-deterministic-sim [FR-001][SC-005][P] **Data Producer: Simulated OxfordPets (Reframed Strategy)**
 1. **Enforce Plan Constraint**: Check `verified_sources` list. If 'z-reward' is present, raise `RuntimeError("Plan Conflict: Z-Reward is listed in verified_sources but Plan.md requires OxfordPets+Simulation. Aborting.")`.
 2. **Fetch Verified Data**: Fetch the verified `oxford_pets` dataset via `datasets.load_dataset("oxford_pets", split="test", streaming=False)`.
 3. **Simulate Distributions**: Invoke `code/simulate.py` to generate teacher score distributions (4 rubric dimensions) and student scalar outputs for each image.
 4. **Generate Annotations**: Produce synthetic human annotations (independent of teacher scores) for each sample.
 5. **Write Unified Dataset**: Save to `data/raw/oxford_pets_simulated.parquet`.
 6. **Validation Log**: Append to `data/raw/validation_log.json` with `source: "oxford_pets_simulated"`, `status: "generated"`.
 7. **Sample Count Log**: Write `data/processed/valid_sample_count.json` with `total_samples`, `valid_samples`, `excluded_count`.
 **Depends**: T001d, T000d.

- [ ] T037b [P] **Synthetic Unit‑Test Dataset**
 Generate a small synthetic dataset (`N=50`) for unit testing via `simulate.py --n-samples 50 --seed 42 --output data/raw/mock_oxford_pets.parquet`. Include mock human annotations (not for final analysis).
 **Depends**: T001d, T000d.

- [ ] T038 [P] **Schema Discovery & Validation**
 1. Read the raw dataset file from `data/raw/`.
 2. Infer actual column names and map to logical fields.
 3. Validate against provisional `contracts/dataset.schema.yaml`.
 4. On discrepancy, overwrite `contracts/dataset.schema.yaml` with the discovered schema.
 5. Raise error on missing rubric dimensions.
 **Depends**: T037-deterministic-sim, T037b.

- [ ] T039 [P] **Review: Data Provenance Verification**
 Explicitly verify that the `human_annotations` column in `data/raw/oxford_pets_simulated.parquet` is generated by a deterministic function of `species_id` and `prompt_text` ONLY, with NO dependency on `teacher_scores` or `student_scalar`. Add a test in `tests/unit/test_provenance.py` to assert this independence.
 **Depends**: T037-deterministic-sim.

- [ ] T012 [FR-001][P] **Ingestion**
 Load `data/raw/oxford_pets_simulated.parquet` (or the mock file) into a Pandas DataFrame, validate required columns (`image_path`, `species_id`, `prompt_text`, `teacher_scores`, `student_scalar`, `human_annotations`, `primary_dimension`), and write to `data/processed/raw_data.parquet`.
 **Depends**: T038, T039.

- [ ] T013 [P] **Alignment**
 Verify that teacher distributions, student scalars, and human annotations align by sample ID; mark samples missing `student_scalar` with `excluded_reason: 'missing_student_scalar'`.
 **Depends**: T012.

- [ ] T015 [P] **Chunked Loading**
 Implement streaming or chunked reading in `code/ingest.py` to keep RAM usage < 7 GB for the full dataset.
 **Depends**: T012.

- [ ] T016 [P] **Summary Output**
 After ingestion, print sample counts, missing‑data flags, and per‑dimension coverage statistics.
 **Depends**: T012.

- [ ] T014 [FR-003][P] **Primary Dimension & Cross-Dimensional Target Derivation**
 1. Read `data/processed/raw_data.parquet`.
 2. Derive `primary_dimension_index` via fixed schema rule: `int(hashlib.sha(prompt_text.encode()).hexdigest(), 16) % 4`.
 3. Derive `cross_dimension_target_index` as `(primary_dimension_index + offset) % 4` (Tautology-Breaking Rule), where `offset` represents a non-zero integer increment designed to break tautological dependencies.
 4. Identify `target_dimension` for fidelity loss as `cross_dimension_target_index`.
 5. Generate `data/processed/lineage_report_initial.json` with entries `{sample_id, source_type:"metadata", primary_dimension, target_dimension, derivation_rule:"sha256_prompt_text_mod_4_v1", cross_dim_rule:"(primary+1)%4"}`.
 6. Log exclusions (null primary dimension or missing target annotation) to `data/processed/exclusions_log.json` immediately.
 7. Write filtered data to `data/processed/cleaned_data.parquet` with `primary_dimension_index` and `target_dimension_index` columns.
 **Depends**: T038, T012, T013.

- [ ] T024 [FR-003][P] **Dimensional Fidelity Loss (Cross-Dimensional)**
 1. Read aligned data from `data/processed/cleaned_data.parquet`.
 2. Use `target_dimension_index` derived in T014 (Cross-Dimensional: `primary + 1`).
 3. Compute MAE between `student_scalar` and the human annotation for the `target_dimension_index` (Cross-Dimensional).
 4. Exclude samples with missing `student_scalar` or missing human annotation for the target (log to `exclusions_log.json`).
 5. Write filtered data to `data/processed/cleaned_data.parquet` (overwrite) with a new column `fidelity_loss`.
 6. Write summary stats (`mean`, `median`, `count`, `excluded_count`) to `data/processed/fidelity_loss_summary.json`.
 **Depends**: T014.

- [ ] T024b-variant [P] **Dimensional Fidelity Loss (Same-Dimension Variant)**
 1. Read aligned data from `data/processed/cleaned_data.parquet`.
 2. Compute MAE between `student_scalar` and the human annotation for `target_dimension = primary_dimension_index`.
 3. This task implements the "Same-Dimensional" hypothesis variant for comparative analysis, distinct from the FR-003 definition.
 4. Write results to `data/processed/same_dim_fidelity_loss.parquet` with a column named `same_dim_fidelity_loss`.
 **Depends**: T014.

- [ ] T014b [P] **Final Lineage Verification**
 1. Read `data/processed/cleaned_data.parquet` (post-T024 exclusion).
 2. Regenerate `lineage_report_final.json` from the final training set samples to ensure the lineage matches the exact data used for modeling.
 3. Compare against `lineage_report_initial.json` to log any discrepancies.
 **Depends**: T024.

## Phase 3: Global Entanglement Metrics (User Story 2)

- [ ] T022b-raw [FR-002][P] **Global Covariance Matrix (Structural/Entire Batch)**
 Compute covariance matrix and dominant eigenvalue on the teacher scores from `data/processed/raw_data.parquet` (includes all samples, pre-exclusion). Write results to `results/covariance_matrix_structural.json` and `results/dominant_eigenvalue_structural.json`.
 **Depends**: T012.

- [ ] T022b-training [FR-002][P] **Global Covariance Matrix (Training/Cleaned Batch)**
 Compute covariance matrix and dominant eigenvalue on the teacher scores from `data/processed/cleaned_data.parquet` (post-exclusion). Write to `results/covariance_matrix_training.json` and `results/dominant_eigenvalue_training.json`.
 **Depends**: T024.

- [ ] T022d [FR-007][P] **Global Entanglement Report**
 Assemble `data/processed/global_entanglement_report.json` containing:
 1. `structural_metrics`: Covariance matrix and eigenvalue from `results/covariance_matrix_structural.json` (for FR-002 "entire dataset").
 2. `training_metrics`: Covariance matrix and eigenvalue from `results/covariance_matrix_training.json` (for FR-006 compliance).
 3. `timestamp`, `dimension_list`.
 **Depends**: T022b-raw, T022b-training.

- [ ] T022a [FR-002][P] **Per‑Sample Entanglement Features**
 For each sample in `data/processed/cleaned_data.parquet`, compute **variance, entropy, skewness, and kurtosis** of the teacher score vector. Append these as columns and write to `data/processed/features.json`.
 **Note**: Per-sample covariance matrices are NOT computed (see Plan.md Constitution Check Principle VI).
 **Depends**: T024.

- [ ] T022c [P] **Mahalanobis Distance (Unconditional)**
 Using the global covariance matrix from `results/covariance_matrix_training.json`, compute Mahalanobis distance for each sample and merge as `mahalanobis_distance` into `data/processed/features.json`. Handle singular matrices with `numpy.linalg.pinv(rcond=1e-15)`.
 **Depends**: T024, T022b-training.

## Phase 4: Model Selection & Training (User Story 3)

- [ ] T027d-early [P] **Performance Gate & Early Exit**
 1. Estimate runtime for T030-stats based on sample count from T024 and feature count.
 2. If estimated time > 5.5 hours, log a warning and proceed with a reduced `n_estimators` (e.g., 10) for T030-stats, or fail gracefully if the constraint is strict.
 3. Write `data/processed/performance_gate.json` with `estimated_time`, `action_taken`.
 **Depends**: T024.

- [ ] T027d [FR-004][P] **Data Sufficiency Check & Model Selection**
 1. Load `data/processed/cleaned_data.parquet` and count samples `N`.
 2. Write `data/processed/model_selection.json` with schema: `{"model_type": "rf" | "ridge" | "fail", "reason": "...", "sample_count": N}`.
 3. **Logic**:
 - `N < 30` → `model_type = "fail"`, `reason = "Critical Power Limitation: N < 30"`.
 - `30 ≤ N < 300` → `model_type = "ridge"`, `reason = "Low sample count; using Ridge Regression"`.
 - `N ≥ 300` → `model_type = "rf"`, `reason = "Sufficient sample count; using Random Forest"`.
 4. Do NOT raise an error; write the file and complete.
 **Depends**: T024.

- [ ] T027h [P] **Global Feature Injection**
 Read `results/dominant_eigenvalue_training.json` and append the value as column `global_eigenvalue` to every row of `data/processed/features.json` (written by T022a). Overwrite the file with enriched data.
 **Depends**: T022a, T022b-training.

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
 Perform k‑fold CV using the estimator selected in Ta (RF or Ridge). Write mean R², std dev, and MAE to `results/cv_metrics.json`.
 **Depends**: T027a, T027d.

- [ ] T029 [P] **Evaluation**
 Evaluate the trained model on the held‑out test set; write predictions, compute residuals (`y_true - y_pred`) to `data/processed/residuals.csv`.
 **Depends**: T028.

- [ ] T030-stats [FR-005][P] **Unified Statistical Validation (Permutation + T-Test)**
 1. Load the trained model from `results/model.pkl` and the test set features/targets from `data/processed/residuals.csv` (using `split_config.json` to ensure same split).
 2. **Permutation Test**: Permute the `fidelity_loss` target variable a sufficient number of times (fixed seed, min 1000). Calculate p-value as fraction of permuted statistics >= observed statistic.
 3. **T-Test**: Train `DummyRegressor(strategy='mean')` on the SAME training split. Evaluate on test set. Perform paired t-test on residuals of model vs. baseline.
 4. Write a unified `results/results.json` entry containing: `r2`, `mae`, `p_value_permutation`, `p_value_ttest`, `t_statistic`, `df`, `baseline_r2`, `baseline_mae`, `hypothesis_status`.
 5. If `p_value_ttest >= 0.05`, set `hypothesis_status:"unsupported"`.
 **Depends**: T029, T027a, T027h.

- [ ] T030d [P] **Partial Correlation Control**
 Compute partial correlation between the primary entanglement feature (`variance`) and `fidelity_loss`, controlling for `student_scalar` and `teacher_mean`. Write `partial_correlation_coefficient` and `partial_correlation_p_value` to `results/partial_correlation.json` and also embed them in `results/results.json`.
 **Depends**: T029.

- [ ] T031 [P] **Integrate Pipeline Outputs**
 Verify that `results/results.json` contains all required keys (`p_value_permutation`, `p_value_ttest`, `t_statistic`, `df`, `baseline_r2`, `baseline_mae`, `mean_r2`, `mean_mae`, `hypothesis_status`, `partial_correlation_coefficient`, `partial_correlation_p_value`).
 **Depends**: T027a, T027f, T027g, T028, T029, T030-stats, T030d.

- [ ] T031b [P] **Cross-Dimensional Variant Reporting**
 If `data/processed/same_dim_fidelity_loss.parquet` exists, compute the same metrics (R², MAE) for this variant and append to `results/results.json` under `same_dim_metrics`.
 **Depends**: T024b-variant, T031.

## Phase 5: Polish & Cross‑Cutting Concerns

- [ ] T032 [P] **Documentation**
 Create `quickstart.md` with reproducible steps (install, download, ingest, train, evaluate).
 **Depends**: T031.

- [ ] T033 [P] **Code Cleanup**
 Run `ruff check` and `black --check` on `code/` and `tests/`; fix all reported issues.
 **Depends**: T031.

- [ ] T034a [P] **Feature Engineering Profiling**
 Profile `code/features.py` on a representative data sample; write `results/profile_report.txt`.
 **Depends**: T016.

- [ ] T034b [P] **Feature Engineering Optimization**
 Refactor `code/features.py` based on profiling results to ensure total runtime < 6 h on CI.
 **Depends**: T034a.

- [ ] T035a [P] **Unit Test: Empty Dataset Handling**
 Add test `tests/unit/test_ingest.py::test_empty_dataset_returns_zero_rows`. Assert that `code/ingest.py` returns an empty DataFrame and logs "No data found" when input file is empty.
 **Depends**: T001a.

- [ ] T035b [P] **Unit Test: NaN Values in Teacher Scores**
 Add test `tests/unit/test_features.py::test_nan_handling_in_features`. Assert that `code/features.py` replaces NaNs with 0.0 and logs a warning, without crashing.
 **Depends**: T001a.

- [ ] T035c [P] **Unit Test: Missing Human Annotations**
 Add test `tests/unit/test_ingest.py::test_missing_annotations_excludes_samples`. Assert that `code/ingest.py` excludes samples with missing annotations and logs "Excluded due to missing annotation" in `exclusions_log.json`.
 **Depends**: T001a.

- [ ] T035d [P] **Unit Test: Zero‑Variance Distributions**
 Add test `tests/unit/test_features.py::test_zero_variance_entropy`. Assert that `code/features.py` sets entropy to 0.0 and variance to 0.0 for zero-variance distributions, without raising errors.
 **Depends**: T001a.

- [ ] T036 [P] **Quickstart Validation**
 Run the full pipeline via `quickstart.md` steps on a fresh runner to confirm reproducibility.
 **Depends**: T031.

- [ ] T042 [P] **Review: Permutation Test Robustness**
 1. Add `assert permutation_count >= 1000` at the start of the `run_permutation_test` function in `code/model.py` to enforce the minimum permutation count.
 2. Update `results/results.json` to include `permutation_count` and `permutation_seed`.
 **Depends**: T030-stats.

- [ ] T043 [P] **Review: Global Covariance Matrix Stability**
 Add a check in `code/features.py` to ensure the global covariance matrix is positive semi-definite. If not, apply a small regularization term (`epsilon * I`) before eigenvalue decomposition and log the `epsilon` value used to `results/covariance_stability.json`.
 **Depends**: T022b-training.

## Phase 6: Review Resolution & Verification (Revision Pass)

**Purpose**: Address specific concerns from prior research-stage reviews regarding data provenance and statistical validity.

- [ ] T040 [P] **Review: VIF Check Implementation**
 Implement a Variance Inflation Factor (VIF) check in `code/features.py`. If VIF > 5 for any feature (other than `mean_teacher_score`), drop that feature from the training set and log the decision to `data/processed/vif_report.json`. Update `code/model.py` to read this report before training.
 **Depends**: T022a.

## Phase 7: Final Validation & Reporting

**Purpose**: Ensure all metrics are correctly aggregated and the final report is ready for publication.

- [ ] T044 [P] **Final Report Generation**
 Aggregate all metrics from `results/*.json` and `data/processed/*.json` into a single `results/final_report.md`. Include sections for: Data Summary, Entanglement Metrics, Model Performance, Hypothesis Validation, and Limitations.
 **Depends**: T031, T042, T043.

- [ ] T045 [P] **Reproducibility Audit**
 Run a full pipeline execution from scratch (clean state) using `quickstart.md` and verify that the `results/final_report.md` matches the previous run within acceptable floating-point tolerance.
 **Depends**: T036, T044.

- [ ] T046 [P] **Constitution Compliance Check**
 Run a script to verify that all Constitution Principles (I-VII) are satisfied by the final artifacts. Generate `results/compliance_check.json`.
 **Depends**: T044.

- [ ] T047 [P] **State Update**
 Update `state/projects/PROJ-967-llmxive-follow-up-extending-beyond-scala.yaml` to reflect the completion of all tasks and the final status of the feature.
 **Depends**: T045, T046.

- [ ] T048 [P] **Pipeline Runtime Audit**
 1. Measure the total runtime of the full pipeline (ingestion + feature engineering + training) from start to finish.
 2. Compare `total_time_seconds` against a predefined time threshold (6 hours = 21600s).
 3. If `total_time_seconds > 21600`, raise `RuntimeError("Pipeline exceeded 6-hour limit: {total_time_seconds}s")` and exit.
 4. If within limit, write `results/runtime_audit.json` with `total_time_seconds`, `status:"pass"`.
 **Depends**: T044, T045.