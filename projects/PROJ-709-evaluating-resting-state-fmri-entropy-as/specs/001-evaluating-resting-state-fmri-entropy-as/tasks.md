---
description: "Task list template for feature implementation"
---

# Tasks: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

**Input**: Design documents from `/specs/001-evaluating-resting-state-fmri-as-biomarker/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [X] T001 [P] Initialize project directory structure: Create `code/`, `data/raw/`, `data/processed/`, `data/derived/`, `code/logs/`, `tests/`, and `docs/` directories; create `code/__init__.py` and `.gitkeep` files in data directories.
- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `antropy`, `scikit-learn`, `nibabel`, `nilearn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `openneuro-py`, `pyyaml`.
- [X] T002b [P] [Depends: T002a] Verify environment pinning: Create `code/.venv` and verify the interpreter version is >=3.11 by running `code/.venv/bin/python --version`.
- [X] T003a [P] Configure environment pinning: Create `code/.env.example` with `CUDA_VISIBLE_DEVICES=` and `code/requirements.txt` with pinned versions to satisfy Constitution Principle I (Reproducibility).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `code/config.py` defining hyperparameters: `m=2`, `r_factor=0.2`, `fd_threshold=0.2`, `target_length=120`, `atlas_n=200`, `dataset_id="ds000305"`, and `SAMPLE_SIZE_N=50`. **Explicit Logic**: Assert that the loaded dataset contains at least 50 valid subjects; if fewer, raise a `RuntimeError`. **Verification**: Assert `config.dataset_id` is exactly "ds000305". **Note**: `SAMPLE_SIZE_N=50` is a resource-constrained subset of the Spec's Assumption (n≥100); this configuration is explicitly validated to prevent silent failure.
- [X] T005a [P] [Depends: T004] Implement `code/data_loader.py` to fetch the ADHD dataset from OpenNeuro (ds000305). **Use `datasets.load_dataset("openneuro/ds000305", split="train", streaming=True)` to stream metadata** and identify subjects. **Crucially**, for each subject identified, download the corresponding NIfTI file to `data/raw/` and write a SHA256 checksum to `data/raw/checksums.sha256` before processing. This ensures memory efficiency while satisfying Constitution Principle III (Data Hygiene) by preserving checksummed local files.
- [X] T005b [P] [Depends: T005a] Verify checksums using SHA256 and write `data/raw/checksums.sha256`.
- [X] T005c [P] [Depends: T005b] Implement `code/data_loader.py` to write the filtered list of valid subjects to `data/derived/valid_subjects.csv` with schema: `subject_id` (str), `site` (str), `diagnosis` (str).
- [X] T013a [P] [Depends: T005c] Implement `code/preprocessing.py`: Calculate Framewise Displacement (FD) for each volume using `nilearn` and `config.py` parameters.
- [X] T013b [P] [Depends: T013a] Implement `code/preprocessing.py`: Scrub volumes with FD > 0.2mm.
- [X] T013c [P] [Depends: T013b] Implement `code/preprocessing.py`: **Compute and save FD statistics for ALL subjects (included and excluded) to `data/derived/subject_fd_stats.csv`**. Schema: `subject_id`, `mean_fd`, `max_fd`, `scrub_fraction`. This artifact is required for SC-006 (Motion Confound Check) to ensure correlation is calculated on the full cohort.
- [X] T013d [Depends: T013b] Implement `code/preprocessing.py`: **Calculate the standard deviation (SD) for the entropy tolerance `r` using ONLY the time points remaining after motion scrubbing** (pre-truncation). **Output**: `data/derived/subject_sd_values.csv`. **Constraint**: This MUST happen BEFORE T014 (truncation) to comply with FR-010.
- [X] T005d [Depends: T013d, T013b] Implement exclusion logging in `code/data_loader.py`: Filter subjects with < 100 time points (post-scrubbing, pre-truncation) and log exclusions to `code/logs/exclusions.log` with headers: `subject_id`, `reason` (fixed string: "insufficient_time_points"), `time_point_count`. **Note**: This task MUST run AFTER scrubbing (T013b) and SD calculation (T013d) but BEFORE truncation (T014) to accurately capture the post-scrubbing count.
- [X] T014 [P] [Depends: T013d, T005d] Implement `code/preprocessing.py`: **Subsample/Truncate valid subjects to exactly N=120 volumes (FR-011)**. **Input**: Scrubbed time series and pre-calculated SD. **Output**: `data/processed/scrubbed_truncated_{subject_id}.nii.gz`. **Constraint**: This MUST happen AFTER SD calculation (T013d) to ensure consistent length bias without affecting the `r` parameter.
- [X] T005e [P] [Depends: T005d] Verify `data/derived/valid_subjects.csv` exists and contains only subjects not in `code/logs/exclusions.log`.
- [X] T007 [P] Create base data structures: Implement `code/models.py` with `dataclasses`: `Subject` (attributes: `id`, `nifti_path`, `phenotype`), `Parcel` (attributes: `index`, `mask_path`), `EntropyFeature` (attributes: `subject_id`, `parcel_index`, `value`). Use these for type hinting in downstream modules.
- [X] T008 [P] Configure environment for CPU-only execution: Create `code/.env` setting `CUDA_VISIBLE_DEVICES=` and update `code/config.py` to set `device="cpu"` explicitly; verify `CUDA_VISIBLE_DEVICES` is unset in the environment.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Parcel-wise Sample Entropy (Priority: P1) 🎯 MVP

**Goal**: Compute the primary feature matrix (Subject x Variable Parcels) of Sample Entropy values from preprocessed fMRI data.

**Independent Test**: Run on multiple subjects; verify output `subject_entropy_features.csv` is a numeric matrix with dimensions corresponding to the number of subjects and A set of features. (no NaN), values in range [lower bound, upper threshold].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for motion scrubbing logic in `tests/unit/test_preprocessing.py`: Verify FD > 0.2mm removal using a synthetic time series with known FD values (e.g., [0.1, 0.3, 0.1]) and assert the output list of removed indices matches [1].
- [X] T011 [P] [US1] Unit test for entropy calculation in `tests/unit/test_entropy.py`: Verify m=2, r=0.2*SD on synthetic data (e.g., white noise) and assert the computed entropy falls within the theoretical bounds.
- [X] T012 [P] [US1] Integration test for full US1 pipeline on 2 subjects (sub-001, sub-002) in `tests/integration/test_us1_pipeline.py`. Verify output file path `data/processed/subject_entropy_features.csv` exists and has correct schema.

### Implementation for User Story 1

- [X] T015a [Depends: T014, T013d] Implement `code/entropy_engine.py`: **Compute Sample Entropy (m=2, r=0.2*SD) for each parcel using the TRUNCATED N=120 time series** (from T014) and the **pre-calculated SD from T013d**. **Constraint**: Load the pre-calculated SD values from `data/derived/subject_sd_values.csv` (generated in T013d) and use them for the `r` parameter. **Output**: `data/processed/subject_entropy_features.csv`. Verification: Assert SD is taken from T013d, and values are within biological range.
- [X] T015c [US1] [Depends: T015a] Implement `code/entropy_engine.py`: **Calculate the cohort-wide median entropy value for EACH of the parcels** across all valid subjects. **Output**: `data/derived/cohort_entropy_medians.csv` (parcel_index, median_value). This is required for FR-009 imputation.
- [X] T015d [US1] [Depends: T015c] Implement `code/entropy_engine.py`: **Handle zero-variance parcels by imputing with the cohort median** (from T015c). **Output**: `data/processed/subject_entropy_features.csv`. Verification: Assert no NaN values remain and imputed values match the cohort median.
- [X] T018 [US1] [Depends: T015d] Implement `code/main.py`: Orchestrate subject-loop, skipping subjects in `code/logs/exclusions.log`, to generate `data/processed/subject_entropy_features.csv`. **Function signature: `def run_pipeline() -> str` returning path to CSV.** **Verification**: `assert os.path.exists(output_path)`, `assert not df.isnull().any().any()`, `assert df.shape[1] == 201`, `assert list(df.columns) == ['subject_id'] + [f'parcel_{i:03d}' for i in range(1, 201)]`. **Add Data Provenance Check**: Verify that `data/raw/checksums.sha256` exists and matches current state of `data/raw/`; if mismatched, raise `RuntimeError`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train Ridge Regression and Logistic Ridge models using entropy features, compare against connectivity baseline, and evaluate performance.

**Independent Test**: Run modeling script; verify output of k-fold CV metrics (Pearson r, AUC) for Entropy-only, Connectivity-only, and Combined models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for 5-fold stratified CV split in `tests/unit/test_modeling.py`: Verify split logic using mock labels [0,0,1,1] and assert each fold maintains the exact class ratio.
- [X] T021 [P] [US2] Integration test for model training on small feature matrix in `tests/integration/test_us2_modeling.py`: Use input matrix x200 and assert output metrics (Pearson r, AUC) are generated.

### Implementation for User Story 2

- [X] T022a [P] [US2] [Depends: T014] Implement `code/connectivity_engine.py`: Compute full 200x200 functional connectivity matrix for each subject using the **truncated N=120 time series** (from T014) to ensure fair comparison with entropy features. Use chunked processing.
- [X] T022b [P] [Depends: T022a] Implement `code/connectivity_engine.py`: Write the single 200x200 matrix per subject to `data/processed/connectivity_matrix_{subject_id}.npy` (FR-008).
- [X] T022c [P] [US2] Implement aggregation logic in `code/connectivity_engine.py`: If multiple runs are merged, combine matrices from `data/processed/` into a unified list; ensure the Single Source of Truth is the individual subject matrix file.
- [X] T023a [Depends: T022a] Implement `code/connectivity_engine.py`: Apply PCA to reduce the 200x200 connectivity matrix to **exactly 200 components** as the intermediate baseline representation (FR-008).
- [X] T023b [P] [Depends: T023a] Implement `code/connectivity_engine.py`: Write the PCA output to `data/derived/connectivity_features_baseline.csv`. **This is the PRIMARY baseline for SC-001/SC-002. NO OTHER ARTIFACT MAY BE USED FOR PRIMARY CLAIMS.**
- [X] T024a [US2] [Depends: T018, T023b] Implement `code/modeling.py`: Train Ridge Regression for ADHD-RS prediction using the **Entropy-only** model. **This is the PRIMARY analysis for SC-001/SC-002.** Ensure the Entropy-only feature set strictly excludes motion covariates.
- [X] T024b [US2] [Depends: T018, T023b] Implement `code/modeling.py`: Train Ridge Regression for ADHD-RS prediction using the **Connectivity-only** model (using 200 components from T023b).
- [X] T024c [US2] [Depends: T018, T023b] Implement `code/modeling.py`: Train Ridge Regression for ADHD-RS prediction using the **Combined Entropy+Connectivity-Baseline** model.
- [X] T024d [P] [Depends: T024a, T024b, T024c] Implement `code/modeling.py`: **Assert the feature set** for each model. Raise `ValueError` if any motion covariates (e.g., `scrub_fraction`) are detected in the Entropy-only model.
- [X] T025 [US2] Implement `code/modeling.py`: Train Logistic Ridge for binary diagnosis (Entropy-only, Connectivity-Baseline, Combined) (FR-003).
- [X] T026 [US2] Implement `code/modeling.py`: Execute k-fold stratified cross-validation preserving label balance (FR-002).
- [X] T027 [US2] Implement `code/modeling.py`: Calculate mean Pearson r and AUC with standard deviations for all models.
- [X] T028 [US2] Implement `code/modeling.py`: Perform Nested Model Comparison (Likelihood Ratio Test) to verify unique value of entropy (FR-003).
- [X] T047 [US2] [Depends: T024a] Implement `code/modeling.py`: **Add explicit assertion in the Entropy-only model training pipeline that the feature matrix columns contain ONLY entropy values and NO motion covariates.** Raise a `ValueError` if any of the following columns are detected: `scrub_fraction`, `FD_mean`, `FD_std`, `motion_params`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate results via permutation testing, sensitivity analysis on `r`, and FDR correction.

**Independent Test**: Run permutation (1000 iters) and sensitivity sweep; verify p-value < 0.05 and stability plot.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for permutation logic in `tests/unit/test_validation.py`: Verify logic using a mock dataset with a known null distribution and assert the empirical p-value calculation matches the expected fraction of permuted models outperforming the observed.
- [X] T031 [P] [US3] Unit test for FDR logic in `tests/unit/test_validation.py`: Verify logic using a mock set of p-values with known significant indices and assert the count of significant features matches the expected result. **Add unit test for motion confound**: Create a mock dataset where entropy and FD are perfectly correlated (r=1.0) and verify that the motion confound check correctly flags the result as potentially confounded.

### Implementation for User Story 3

- [X] T032a [P] [US3] Implement `code/validation.py`: **Perform a sufficient number of permutations of outcome labels** to ensure robust statistical inference (FR-004, SC-003). **Set `np.random.seed(42)` (or configurable seed) BEFORE the permutation loop starts**. Add a verification step that re-runs the permutation with the same seed and asserts the `p_value_permutation` is identical.
- [X] T032b [P] [Depends: T032a] Implement `code/validation.py`: **Write the empirical p-value** to `data/derived/permutation_p_value.txt`. Verification: Assert the log shows that the full set of iterations has been completed.
- [X] T033 [US3] Implement `code/validation.py`: **Sweep `r` across a range of representative values** (0.15, 0.20, 0.25) and calculate performance variance (FR-005). **Output**: `data/derived/sensitivity_analysis.csv`.
- [X] T034 [US3] Implement `code/validation.py`: Apply FDR correction to parcel-level coefficients; output `significant_parcels.csv`; **record the count of significant parcels (even if zero) and flag the result in the report; do NOT raise an exception** (FR-006, SC-005).
- [X] T035 [US3] [Depends: T013c, T015d] Implement `code/validation.py`: Calculate correlation between mean entropy and mean FD using `data/derived/subject_fd_stats.csv` and `data/processed/subject_entropy_features.csv`. **Logic**: `if abs(corr) >= 0.3: flag = True; write to motion_confound_report.json`. Flag if |r| ≥ 0.3 (SC-006).
- [X] T036a [US3] [Depends: T027, T024a, T023b] Implement `code/validation.py`: **Calculate the raw difference in mean Pearson correlation (Δr) between Entropy-only and Connectivity-Baseline (200 components from T023b) models; output `delta_r` to `model_metrics.json`** (SC-001).
- [X] T036b [US3] [Depends: T027, T024a, T023b] Implement `code/validation.py`: Perform paired t-test on fold differences (Entropy vs Connectivity) to assess statistical significance of Δr.
- [X] T037 [US3] [Depends: T027, T024a, T023b] Implement `code/validation.py`: **Calculate the 95% confidence interval lower bound for ΔAUC using the percentile method with 1000 bootstrap iterations**. Extract the lower bound and verify if it is ≥ 0.05 (SC-002).
- [X] T038a [US3] [Depends: T036a, T036b, T037, T032b, T033, T034, T035] Implement `code/validation.py`: **Calculate and aggregate all validation metrics** (delta_r, delta_auc_ci_lower, p_value_permutation, sensitivity_variance_r, sensitivity_variance_auc, significant_parcels_count, motion_confound_flag) into `data/derived/model_metrics.json`.
- [X] T039a [P] [US3] Implement `code/validation.py`: **Aggregate the `code/logs/exclusions.log`** into a structured format.
- [X] T039b [P] [Depends: T035, T039a] Implement `code/validation.py`: **Generate `data/derived/motion_confound_report.json`** containing the motion correlation result and exclusion summary.
- [X] T048 [US3] [Depends: T015d, T032a] Implement `code/validation.py`: **Ensure permutation testing uses the EXACT same feature matrix and preprocessing pipeline as the primary model (T024a) to guarantee statistical validity.** Verification: **Compute SHA256 hash of feature matrix used in T024a and T048; assert hashes match.**
- [X] T051 [P] [US3] **Implement a verification step in `code/validation.py` that asserts the permutation count is exactly 1,000 in the final log.** If the count is less, raise a `RuntimeError`.

**Success Criteria Verification Tasks**

- [X] T043a [US3] [Depends: T038a] Implement `code/validation.py`: **Verify SC-001**: Assert `delta_r >= 0.05`. Output `sc001_passed` (bool) to `final_success_report.json`.
- [X] T043b [US3] [Depends: T038a] Implement `code/validation.py`: **Verify SC-002**: Assert `delta_auc_ci_lower >= 0.05`. Output `sc002_passed` (bool) to `final_success_report.json`.
- [X] T043c [US3] [Depends: T038a] Implement `code/validation.py`: **Verify SC-003**: Assert `p_value_permutation < 0.05`. Output `sc003_passed` (bool) to `final_success_report.json`.
- [X] T043d [US3] [Depends: T038a] Implement `code/validation.py`: **Verify SC-004**: Assert `|perf(0.20) - mean(perf)| / mean(perf) <= 0.10`. Output `sc004_passed` (bool) to `final_success_report.json`.
- [X] T043e [US3] [Depends: T038a] Implement `code/validation.py`: **Verify SC-005**: **Calculate** `significant_parcels_count`. **Record** the count in `final_success_report.json` (do NOT assert > 0). The spec requires measuring the count, not enforcing a positive result.
- [X] T043f [US3] [Depends: T035] Implement `code/validation.py`: **Verify SC-006**: Assert `abs(corr_entropy_fd) < 0.3`. Output `sc006_passed` (bool) to `final_success_report.json`.
- [X] T043g [P] [Depends: T043a, T043b, T043c, T043d, T043e, T043f] Implement `code/validation.py`: **Generate `data/derived/final_success_report.json`** containing all boolean flags: `sc001_passed`, `sc002_passed`, `sc003_passed`, `sc004_passed`, `sc005_passed`, `sc006_passed`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [X] T040 [P] Documentation updates: Update `README.md` with a **Quickstart section** containing a single command to run the full pipeline (`python code/main.py`), and verify execution with `--help` to assert it displays usage information without errors.
- [X] T041 [P] Code cleanup: Run `black` and `isort` on `code/` and `tests/`; verify with `black --check` and `isort --check-only`.
- [X] T042a [P] [US3] Implement `tests/integration/test_performance.py`: Run `code/main.py --subset=50` (where 50 means A cohort of subjects) and assert `runtime < 6h`.
- [X] T042b [P] [Depends: T042a] Record runtime in `data/derived/runtime_log.txt`.
- [X] T044a [P] [US3] Implement `tests/unit/` execution: Run `pytest tests/unit/` and assert exit code 0.
- [X] T044b [P] [US3] Implement `tests/integration/` execution: Run `pytest tests/integration/` and assert exit code 0.
- [X] T044c [P] [US3] Implement `tests/` full suite execution: Run `pytest tests/` and assert exit code 0.
- [X] T045a [P] [US3] Implement `code/validation.py`: Verify `python code/main.py --help` output contains "Usage".
- [X] T045b [P] [US3] Implement `code/validation.py`: Verify `python code/main.py --help` output contains "Options".
- [X] T049 [P] [US1] **Implement robust error handling in `code/data_loader.py` to ensure that if the OpenNeuro fetch fails, the script raises a clear `RuntimeError` and does NOT fall back to synthetic data generation.** Verify by simulating a network failure and asserting the process halts with an appropriate error message.
- [X] T050 [P] [US2] **Add explicit logging in `code/modeling.py` to record the exact number of samples (N) and features (P) used in each model training run, and verify that N < P triggers a warning log entry regarding potential overfitting.**
- [X] T053 [P] [US1] **Add a verification step in `code/entropy_engine.py` to ensure that the entropy calculation does not produce NaN or Inf values for any parcel, and log the specific subject/parcel combination if such values occur, triggering an exclusion.**
- [X] T054 [P] [US2] **Implement a robust check in `code/modeling.py` to ensure that the stratified cross-validation splits maintain a minimum of samples per class in each fold, raising a `ValueError` if the class distribution is too imbalanced for valid stratification.**
- [X] T055 [P] [US1] **Implement unit test in `tests/unit/test_entropy.py`**: Create a synthetic white noise signal and verify biological plausibility by asserting the computed entropy falls within the expected theoretical bounds.
- [X] T056 [P] [US2] **Implement unit test in `tests/unit/test_modeling.py`**: Create a mock dataset with a known class imbalance (e.g., a skewed ratio). and verify that stratified CV logic maintains the exact ratio of classes in each fold.
- [X] T057 [P] [US3] **Implement unit test in `tests/unit/test_validation.py`**: Create a mock set of p-values with known significant and non-significant values and verify that the FDR correction correctly identifies the significant ones.
- [X] T058 [P] [US3] **Implement unit test in `tests/unit/test_validation.py`**: Create a mock dataset where entropy and FD are perfectly correlated (r=1.0) and verify that the motion confound check correctly flags the result as potentially confounded.
- [X] T059 [P] [US3] **Implement unit test in `tests/unit/test_validation.py`**: Create a mock dataset and verify that the sensitivity analysis logic correctly calculates the performance variance across different `r` values.
- [X] T060 [P] [US3] **Implement unit test in `tests/unit/test_validation.py`**: Create a mock dataset with a known null distribution and verify that the permutation testing logic correctly calculates the empirical p-value.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Revision & Data Integrity (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data streaming, sample size justification, and reproducibility of the permutation test.

(No tasks remain in this phase; all logic has been moved to earlier phases as per ordering corrections.)

**Checkpoint**: All user stories should now be independently functional