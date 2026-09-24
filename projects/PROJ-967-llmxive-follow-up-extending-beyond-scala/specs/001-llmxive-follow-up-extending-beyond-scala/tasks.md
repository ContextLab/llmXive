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

- [ ] T037-real [FR-001][SC-005][P] **Data Producer: Z-Reward Attempt**
 1. **Attempt Real Load**: Try to load the Z-Reward evaluation dataset via `datasets.load_dataset("z-reward/evaluation", split="test", streaming=False)`.
 2. **Error Handling**: If the dataset is not found (404) or missing required files, log the failure to `data/raw/validation_log.json` with `status: "fallback_required"`, `message: "Z-Reward dataset unavailable"`, and `source: "z-reward/evaluation"`. Do NOT raise a RuntimeError; complete the task successfully to allow the fallback task to proceed.
 3. **Success Path**: If the dataset loads successfully, log `status: "success"` and proceed to T012.
 **Depends**: T001a, T000d.

- [ ] T037-sim [FR-001][SC-005][P] **Data Producer: Simulation Fallback**
 1. **Trigger**: Run after T037-real completes (regardless of success/failure status, but primarily for fallback).
 2. **Fetch Verified Data**: Fetch the verified `oxford_pets` dataset via `datasets.load_dataset("oxford_pets", split="test", streaming=False)`.
 3. **Simulate Distributions**: Invoke `code/simulate.py` to generate teacher score distributions (4 rubric dimensions) and student scalar outputs for each image.
 4. **Generate Annotations**: Produce synthetic human annotations (independent of teacher scores) for each sample.
 5. **Write Unified Dataset**: Save to `data/raw/oxford_pets_simulated.parquet`.
 6. **Validation Log**: Append to `data/raw/validation_log.json` with `source: "oxford_pets_simulated"`, `status: "generated"`.
 7. **Sample Count Log**: Write `data/processed/valid_sample_count.json` with `total_samples`, `valid_samples`, `excluded_count`.
 **Depends**: T037-real, T001d, T000d.

- [ ] T037b [P] **Synthetic Unit‑Test Dataset**
 Generate a small synthetic dataset (`N=50`) for unit testing via `simulate.py --n-samples 50 --seed 42 --output data/raw/mock_oxford_pets.parquet`. Include mock human annotations (not for final analysis).
 **Depends**: T001d, T000d.

- [ ] T038 [P] **Schema Discovery & Validation**
 1. Read the raw dataset file from `data/raw/`.
 2. Infer actual column names and map to logical fields.
 3. Validate against provisional `contracts/dataset.schema.yaml`.
 4. On discrepancy, overwrite `contracts/dataset.schema.yaml` with the discovered schema.
 5. Raise error on missing rubric dimensions.
 **Depends**: T037-real, T037-sim, T037b.

- [ ] T039 [P] **Review: Data Provenance Verification**
 Explicitly verify that the `human_annotations` column in `data/raw/oxford_pets_simulated.parquet` is generated by a deterministic function of `species_id` and `prompt_text` ONLY, with NO dependency on `teacher_scores` or `student_scalar`. Add a test in `tests/unit/test_provenance.py` to assert this independence.
 **Depends**: T037-sim.

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

- [ ] T014 [FR-003][P] **Primary Dimension Identification**
 Derive `primary_dimension` via a fixed schema rule using `prompt_text` (prompt metadata).
 - **Rule**: `primary_dimension_index = int(hashlib.sha(prompt_text.encode()).hexdigest(), 16) % 4`.
 - **Reproducibility**: Set `PYTHONHASHSEED=0` in the execution environment or use the deterministic hash method above.
 - Generate `data/processed/lineage_report.json` with entries `{sample_id, source_type:"metadata", dimension, derivation_rule:"sha256_prompt_text_mod_4_v1", derivation_rule_hash:"<SHA‑256 of rule string>"}`.
 - Log exclusions (null primary dimension) to `data/processed/exclusions_log.json`.
 **Depends**: T038.

- [ ] T024 [FR-003][P] **Dimensional Fidelity Loss (Same-Dimension)**
 1. Read aligned data from `data/processed/raw_data.parquet`.
 2. Use `primary_dimension` from T014.
 3. Compute MAE between `student_scalar` and the human annotation for the **same** `primary_dimension` (i.e., `target_dimension = primary_dimension_index`).
 4. Exclude samples with missing `primary_dimension`, missing human annotation for the target, or missing `student_scalar`.
 5. Log each exclusion to `exclusions_log.json`.
 6. Write filtered data to `data/processed/cleaned_data.parquet` with a new column `fidelity_loss`.
 7. Write summary stats (`mean`, `median`, `count`, `excluded_count`) to `data/processed/fidelity_loss_summary.json`.
 **Depends**: T012, T014.

- [ ] T014b [P] **Fidelity Loss Lineage Verification**
 1. Read `data/processed/cleaned_data.parquet` (output of T024).
 2. Generate a specific lineage trace for the `fidelity_loss` column, proving it was derived solely from `student_scalar` and `human_annotations` (target dimension) using the rule defined in T014.
 3. Verify that no `teacher_scores` values were used in the calculation.
 4. Write `data/processed/fidelity_loss_lineage.json` containing the derivation rule, input columns, and exclusion log reference.
 **Depends**: T024, T014.

- [ ] T024b-variant [P] **Dimensional Fidelity Loss (Cross-Dimensional Variant)**
 1. Read aligned data from `data/processed/raw_data.parquet`.
 2. Compute MAE between `student_scalar` and the human annotation for `target_dimension = (primary_dimension_index + 1) % 4`.
 3. This task implements the "Cross-Dimensional" hypothesis variant from the Plan.md for comparative analysis, distinct from the FR-003 definition.
 4. Write results to `data/processed/cross_dimensional_fidelity_loss.parquet` with a column named `cross_dim_fidelity_loss`.
 **Depends**: T012, T014.

## Phase 3: Global Entanglement Metrics (User Story 2)

- [ ] T022b-raw [FR-002][P] **Global Covariance Matrix (Raw Data)**
 Compute covariance matrix and dominant eigenvalue on the teacher scores from the *raw* dataset (`data/processed/raw_data.parquet`). Write results to `results/covariance_matrix_raw.json` and `results/dominant_eigenvalue_raw.json`.
 **Depends**: T012, T037-sim.

- [ ] T022b-filtered [FR-002][P] **Global Covariance Matrix (Filtered Data)**
 Compute covariance matrix and dominant eigenvalue on the *filtered* dataset (`data/processed/cleaned_data.parquet`). Write to `results/covariance_matrix.json` and `results/dominant_eigenvalue.json`.
 **Depends**: T024.

- [ ] T022d [FR-007][P] **Global Entanglement Report**
 Assemble `data/processed/global_entanglement_report.json` containing the covariance matrix, dominant eigenvalue, computation source (`filtered_data`), timestamp, and dimension list.
 **Depends**: T022b-filtered.

- [ ] T022a [FR-002][P] **Per‑Sample Entanglement Features**
 For each sample in `data/processed/cleaned_data.parquet`, compute **variance, entropy, skewness, and kurtosis** of the teacher score vector. Append these as columns and write to `data/processed/features.json`.
 **Note**: Per-sample covariance matrices are NOT computed (see Plan.md Constitution Check Principle VI).
 **Depends**: T024, T022b-filtered.

- [ ] T022c [P] **Mahalanobis Distance (Unconditional)**
 Using the global covariance matrix from `results/covariance_matrix.json`, compute Mahalanobis distance for each sample and merge as `mahalanobis_distance` into `data/processed/features.json`. Handle singular matrices with `numpy.linalg.pinv(rcond=1e-15)`.
 **Depends**: T024, T022b-filtered.

## Phase 4: Model Selection & Training (User Story 3)

- [ ] T027d-early [P] **Performance Gate & Early Exit**
 1. Estimate runtime for T027f based on sample count from T024 and feature count.
 2. If estimated time > 5.5 hours, log a warning and proceed with a reduced `n_estimators` (e.g., 10) for T027f, or fail gracefully if the constraint is strict.
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
 Read `results/dominant_eigenvalue.json` and append the value as column `global_eigenvalue` to every row of `data/processed/features.json` (written by T022a). Overwrite the file with enriched data.
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
 1. Train `DummyRegressor(strategy='mean')` on the **same** training split used for the main model (read from `split_config.json`).
 2. Evaluate on the test set to obtain baseline R² and MAE.
 3. Perform a paired t‑test (`scipy.stats.ttest_rel`) on the residuals of the model vs. baseline.
 4. Write `baseline_r2`, `baseline_mae`, `p_value_ttest`, `t_statistic`, `df`, and `t_test_status` (significant / not significant / unsupported) to `results/results.json`.
 5. If `p_value_ttest >= 0.05`, set `hypothesis_status:"unsupported"` in `results.json`.
 **Depends**: T029, T027a.

- [ ] T030e [FR-005][P] **Permutation Test Implementation**
 1. Load the trained model (from T027f/g) and the test set features/targets.
 2. Permute the `fidelity_loss` target variable multiple times (fixed seed 42).
 3. For each permutation, re-evaluate the model (or compute correlation) and record the statistic.
 4. Calculate the p-value as the fraction of permuted statistics >= observed statistic.
 5. Write `results/permutation_pvalue.json` with `p_value`, `permutation_count`, `permutation_seed`, `observed_statistic`.
 6. Update `results/results.json` to include `p_value_permutation`.
 **Depends**: T029, T027a, T027h.

- [ ] T030d [P] **Partial Correlation Control**
 Compute partial correlation between the primary entanglement feature (`variance`) and `fidelity_loss`, controlling for `student_scalar` and `teacher_mean`. Write `partial_correlation_coefficient` and `partial_correlation_p_value` to `results/partial_correlation.json` and also embed them in `results/results.json`.
 **Depends**: T029.

- [ ] T031 [P] **Integrate Pipeline Outputs**
 Verify that `results/results.json` contains all required keys (`p_value_permutation`, `p_value_ttest`, `t_statistic`, `df`, `baseline_r2`, `baseline_mae`, `mean_r2`, `mean_mae`, `hypothesis_status`, `partial_correlation_coefficient`, `partial_correlation_p_value`).
 **Depends**: T027a, T027f, T027g, T028, T029, T030c, T030d, T030e.

- [ ] T031b [P] **Cross-Dimensional Variant Reporting**
 If `data/processed/cross_dimensional_fidelity_loss.parquet` exists, compute the same metrics (R², MAE) for this variant and append to `results/results.json` under `cross_dim_metrics`.
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
 Record the formal amendment that redefines the primary quality dimension rule and the cross‑dimensional fidelity loss computation, linking to FR‑003 and Principle VII.
 **Depends**: T014.

- [ ] T042 [P] **Review: Permutation Test Robustness**
 Verify that the permutation test implementation in `code/model.py` (written by T030e) uses at least 1000 permutations and a fixed random seed to ensure reproducibility. Update `results/results.json` to include `permutation_count` and `permutation_seed`.
 **Depends**: T030e.

- [ ] T043 [P] **Review: Global Covariance Matrix Stability**
 Add a check in `code/features.py` to ensure the global covariance matrix is positive semi-definite. If not, apply a small regularization term (`epsilon * I`) before eigenvalue decomposition and log the `epsilon` value used to `results/covariance_stability.json`.
 **Depends**: T022b-filtered.

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