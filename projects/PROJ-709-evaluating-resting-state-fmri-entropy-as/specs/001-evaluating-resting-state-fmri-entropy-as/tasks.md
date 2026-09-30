# Tasks: Evaluating Resting‑State fMRI Entropy as a Biomarker for Attention‑Deficit Traits

**Input**: Design documents from `/specs/001-evaluating-resting-state-fmri-entropy-as-biomarker/`
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

- [X] T001 [P] Initialize project directory structure: Create `code/`, `data/raw/`, `data/processed/`, `data/derived/`, `tests/`, and `docs/` directories; create `code/__init__.py` and `.gitkeep` files in data directories.
- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `antropy`, `scikit-learn`, `nibabel`, `nilearn`, `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `statsmodels`, `openneuro-py`, `pyyaml`. **Verification**: Create virtual environment using `python3 -m venv code/.venv`, then verify the venv interpreter version by running `code/.venv/bin/python --version` to ensure it is 3.11 or higher.
- [X] T003a [P] Configure environment pinning: Create `code/.env.example` with `CUDA_VISIBLE_DEVICES=` and `code/requirements.txt` with pinned versions to satisfy Constitution Principle I (Reproducibility).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` defining hyperparameters: `m=2`, `r_factor=0.2`, `fd_threshold=0.2`, `target_length=120`, `atlas_n=200`, `dataset_id="[dataset_identifier]"`.
- [X] T005a [P] [Depends: T004] Implement `code/data_loader.py` to fetch the ADHD dataset from OpenNeuro; verify checksums using SHA256 and write `data/raw/checksums.sha256`; **MUST write the filtered list of valid subjects to `data/derived/valid_subjects.csv`** with schema: `subject_id` (str), `site` (str), `diagnosis` (str).
- [X] T013a [P] [Depends: T005a] Implement `code/preprocessing.py`: Calculate Framewise Displacement (FD) for each volume using `nilearn` and `config.py` parameters.
- [X] T013b [P] [Depends: T013a] Implement `code/preprocessing.py`: Scrub volumes with FD > 0.2mm.
- [X] T005b [P] [Depends: T013b] Implement exclusion logging in `code/data_loader.py`: Filter subjects with < 100 time points (post-scrubbing, pre-truncation) and log exclusions to `data/raw/exclusions.log` with headers: `subject_id`, `reason` (fixed string: "insufficient_time_points"), `time_point_count`. **Note**: This task MUST run AFTER scrubbing (T013b) but BEFORE truncation (T014) to accurately capture the post-scrubbing count.
- [X] T013c [P] [Depends: T013b] Implement `code/preprocessing.py`: **Compute and save FD statistics for ALL subjects (included and excluded) to `data/derived/subject_fd_stats.csv`**. Schema: `subject_id`, `mean_fd`, `max_fd`, `scrub_fraction`. This artifact is required for SC-006 (Motion Confound Check) to ensure correlation is calculated on the full cohort.
- [X] T014 [P] [Depends: T005b] Implement `code/preprocessing.py`: Subsample/Truncate valid subjects to exactly N=120 volumes (FR-011). **Output**: `data/processed/scrubbed_truncated_{subject_id}.nii.gz`.
- [X] T005c [P] [Depends: T005b] Verify `data/derived/valid_subjects.csv` exists and contains only subjects not in `exclusions.log`.
- [X] T007 [P] Create base data structures: Implement `code/models.py` with `dataclasses`: `Subject` (attributes: `id`, `nifti_path`, `phenotype`), `Parcel` (attributes: `index`, `mask_path`), `EntropyFeature` (attributes: `subject_id`, `parcel_index`, `value`). Use these for type hinting in downstream modules.
- [X] T008 [P] Configure environment for CPU-only execution: Create `code/.env` setting `CUDA_VISIBLE_DEVICES=` and update `code/config.py` to set `device="cpu"` explicitly; verify `CUDA_VISIBLE_DEVICES` is unset in the environment.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute Parcel-wise Sample Entropy (Priority: P1) 🎯 MVP

**Goal**: Compute the primary feature matrix (Subject x Variable Parcels) of Sample Entropy values from preprocessed fMRI data.

**Independent Test**: Run on multiple subjects; verify output `subject_entropy_features.csv` is a numeric matrix with dimensions corresponding to the number of subjects and 201 features. (no NaN), values in range [lower bound, upper threshold].

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for motion scrubbing logic in `tests/unit/test_preprocessing.py` (verify FD > 0.2mm removal)
- [X] T011 [P] [US1] Unit test for entropy calculation in `tests/unit/test_entropy.py` (verify m=2, r=0.2*SD on synthetic data)
- [ ] T012 [P] [US1] Integration test for full US1 pipeline on 2 subjects in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [X] T015a [US1] [Depends: T014] Implement `code/entropy_engine.py`: **Truncate or interpolate time series to exactly N=120 volumes** if not already done (FR-011). **Output**: `data/processed/entropy_truncated_{subject_id}.nii.gz`. Verification: Assert output file length is exactly 120 volumes.
- [X] T015b [US1] [Depends: T015a] Implement `code/entropy_engine.py`: **Compute SD on the N=120 truncated series, THEN calculate SampEn (m=2, r=0.2*SD) for each parcel** (FR-001, FR-010). **Output**: `data/processed/subject_entropy_raw.csv` (subject_id, parcel_01...parcel_200). Verification: Assert SD is calculated on 120 points, not pre-truncated data.
- [X] T015c [US1] [Depends: T015b] Implement `code/entropy_engine.py`: **Handle zero-variance parcels by imputing with cohort median** (FR-009). **Output**: `data/processed/subject_entropy_features.csv`. Verification: Assert no NaN values remain.
- [X] T018 [US1] [Depends: T015c] Implement `code/main.py`: Orchestrate subject-loop, skipping subjects in `exclusions.log`, to generate `data/processed/subject_entropy_features.csv`. **Function signature: `def run_pipeline() -> str` returning path to CSV.** **Verification**: `assert os.path.exists(output_path)`, `assert not df.isnull().any().any()`, `assert df.shape[1] == 201`, `assert list(df.columns) == ["subject_id"] + [f"parcel_{i:02d}" for i in range(1, 201)]`.
- [X] T046 [US1] [Depends: T015b] Implement `code/entropy_engine.py`: **Add explicit validation to ensure the SD for `r` is computed strictly on the N=120 truncated time series.** Add a unit test in `tests/unit/test_entropy.py` to verify this specific order of operations. **Test Data**: Create a mock time series of length 120 with variance 0.5, then truncate to 100. Verify SD is calculated on the 100-point series (variance ~0.5), not the original 120-point series.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train Ridge Regression and Logistic Ridge models using entropy features, compare against connectivity baseline, and evaluate performance.

**Independent Test**: Run modeling script; verify output of k-fold CV metrics (Pearson r, AUC) for Entropy-only, Connectivity-only, and Combined models.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for 5-fold stratified CV split in `tests/unit/test_modeling.py`
- [X] T021 [P] [US2] Integration test for model training on small feature matrix in `tests/integration/test_us2_modeling.py`

### Implementation for User Story 2

- [X] T022a [P] [US2] [Depends: T014] Implement `code/connectivity_engine.py`: Compute full 200x200 functional connectivity matrix for each subject using chunked processing; **Write the single 200x200 matrix per subject to `data/processed/connectivity_matrix_{subject_id}.npy`** (FR-008). **Note: This task is independent of entropy features and runs in parallel with US1.**
- [X] T022b [US2] Implement aggregation logic in `code/connectivity_engine.py`: If multiple runs are merged, combine matrices from `data/processed/` into a unified list; ensure the Single Source of Truth is the individual subject matrix file.
- [X] T023a [US2] Implement `code/connectivity_engine.py`: Apply PCA to reduce the 200x200 connectivity matrix to **200 components** (no reduction) as the intermediate baseline representation (FR-008). **Output**: `data/derived/connectivity_features_baseline.csv`. **This is the PRIMARY baseline for SC-001/002.**
- [X] T023c [US2] [Depends: T023a] Implement `code/connectivity_engine.py`: **Perform Feature Selection (L1-Regularized Logistic Regression) on the PCA components to reduce the feature space to a smaller, optimized subset of features** to address the N=100, p=200 underpowered ratio. **Output**: `data/derived/connectivity_features_reduced.csv`. **Note**: This is for exploratory analysis; the primary baseline comparison uses the 200-component set from T023a.
- [X] T023d [US2] [Depends: T023c] Implement `code/connectivity_engine.py`: **Save the reduced feature matrix** and log the number of selected features.
- [X] T024a [P] [US2] [Depends: T018, T023a] Implement `code/modeling.py`: Train Ridge Regression for ADHD-RS prediction using three models: (1) Entropy-only, (2) **Connectivity-Baseline (using 200 components from T023a)**, and (3) **Combined Entropy+Connectivity-Baseline**. **This is the PRIMARY analysis for SC-001/002.** Ensure the Entropy-only feature set strictly excludes motion covariates.
- [X] T024b [P] [US2] [Depends: T018, T023d] Implement `code/modeling.py`: Train exploratory models using the **Reduced Features (T023d)** for comparison only.
- [X] T025 [US2] Implement `code/modeling.py`: Train Logistic Ridge for binary diagnosis (Entropy-only, Connectivity-Baseline, Combined) (FR-003).
- [X] T026 [US2] Implement `code/modeling.py`: Execute k-fold stratified cross-validation preserving label balance (FR-002).
- [X] T027 [US2] Implement `code/modeling.py`: Calculate mean Pearson r and AUC with standard deviations for all models (both primary and exploratory).
- [X] T028 [US2] Implement `code/modeling.py`: Perform Nested Model Comparison (Likelihood Ratio Test) to verify unique value of entropy (FR-003).
- [X] T047 [US2] [Depends: T024a] Implement `code/modeling.py`: **Add explicit assertion in the Entropy-only model training pipeline that the feature matrix columns contain ONLY entropy values and NO motion covariates.** Raise a `ValueError` if any of the following columns are detected: `scrub_fraction`, `FD_mean`, `FD_std`, `motion_params`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate results via permutation testing, sensitivity analysis on `r`, and FDR correction.

**Independent Test**: Run permutation (iter) and sensitivity sweep; verify p-value < 0.05 and stability plot.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for permutation logic in `tests/unit/test_validation.py`
- [X] T031 [P] [US3] Unit test for FDR logic and verify count > 0 logic (SC-005) in `tests/unit/test_validation.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/validation.py`: Perform a sufficient number of permutations of outcome labels to derive empirical p-values (FR-004).
- [X] T033 [US3] Implement `code/validation.py`: Sweep `r` across a range of low values and calculate performance variance (FR-005).
- [X] T034 [US3] Implement `code/validation.py`: Apply FDR correction to parcel-level coefficients; output `significant_parcels.csv`; **record the count of significant parcels (even if zero) and flag the result in the report; do NOT raise an exception** (FR-006, SC-005).
- [X] T035 [US3] [Depends: T013c, T015c] Implement `code/validation.py`: Calculate correlation between mean entropy and mean FD using `data/derived/subject_fd_stats.csv` and `data/processed/subject_entropy_features.csv`. **Logic**: `if abs(corr) >= 0.3: flag = True; write to motion_confound_report.json`. Flag if |r| ≥ 0.3 (SC-006).
- [X] T036a [US3] [Depends: T027, T024a, T023a] Implement `code/validation.py`: **Calculate the raw difference in mean Pearson correlation (Δr) between Entropy-only and Connectivity-Baseline (200 components from T023a) models; output `delta_r` to `model_metrics.json`** (SC-001).
- [X] T036b [US3] [Depends: T027, T024a, T023a] Implement `code/validation.py`: Perform paired t-test on fold differences (Entropy vs Connectivity) to assess statistical significance of Δr (separate from the effect size check).
- [X] T037 [US3] [Depends: T027, T024a, T023a] Implement `code/validation.py`: **Calculate confidence interval for ΔAUC using bootstrapping (sufficient iterations).** Extract the lower bound of the 95% CI and verify if it is ≥ 0.05 (SC-002). **Note**: If a high number of iterations exceed a significant duration threshold, reduce to a lower number of iterations. and log the reduction. Do not use approximations.
- [X] T038 [US3] [Depends: T032, T033] Generate `data/derived/model_metrics.json` aggregating all success criteria metrics from T024a, T025, T027, T032, T033, T036a, T037 with schema: `delta_r` (float), `delta_auc_ci_lower` (float), `p_value_permutation` (float), `sensitivity_variance_r` (float, **calculated as np.var([r_values]) from T033 results**), `sensitivity_variance_auc` (float), `significant_parcels_count` (int).
- [X] T039 [US3] Generate `data/derived/motion_confound_report.json` and sensitivity plots.
- [X] T048 [US3] [Depends: T032] Implement `code/validation.py`: **Ensure permutation testing uses the EXACT same feature matrix and preprocessing pipeline as the primary model (T024a) to guarantee statistical validity.** Verification: **Compute SHA256 hash of feature matrix used in T024a and T048; assert hashes match.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T040 [P] Documentation updates in `docs/` and `README.md`; **Add a Quickstart section with a single command to run the full pipeline**
- [ ] T041 Code cleanup and refactoring of `code/` modules
- [ ] T042a [P] [US3] Implement `tests/integration/test_performance.py`: Run `code/main.py --subset=50` and assert `runtime < 6h`; record in `data/derived/runtime_log.txt`.
- [ ] T043 [P] Run full integration test suite on the complete dataset subset
- [ ] T044 Finalize `paper/` draft with all verified metrics from `model_metrics.json`
- [ ] T045 Run quickstart.md validation
- [ ] T049 [P] [US1] **Implement robust error handling in `code/data_loader.py` to ensure that if the OpenNeuro fetch fails, the script raises a clear `RuntimeError` and does NOT fall back to synthetic data generation.** Verify by simulating a network failure and asserting the process halts with an appropriate error message.
- [ ] T050 [P] [US2] **Add explicit logging in `code/modeling.py` to record the exact number of samples (N) and features (P) used in each model training run, and verify that N < P triggers a warning log entry regarding potential overfitting.**
- [ ] T051 [P] [US3] **Implement a "dry-run" mode in `code/validation.py` that executes the permutation logic with a small number of iterations (e.g., 10) to verify the pipeline integrity before committing to the full 1,000 iterations required by SC-003.**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Unit test for motion scrubbing logic in tests/unit/test_preprocessing.py"
Task: "Unit test for entropy calculation in tests/unit/test_entropy.py"

# Launch all models for User Story 1 together:
Task: "Implement code/preprocessing.py: Calculate Framewise Displacement"
Task: "Implement code/entropy_engine.py: Compute SD and SampEn"
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
 - Developer A: User Story 1 (Entropy Pipeline)
 - Developer B: User Story 2 (Modeling & Connectivity)
 - Developer C: User Story 3 (Validation & Stats)
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
