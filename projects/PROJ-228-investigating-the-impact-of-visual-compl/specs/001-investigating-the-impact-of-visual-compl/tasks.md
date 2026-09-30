# Tasks: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

**Input**: Design documents from `/specs/001-visual-complexity-pfc/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[D]**: Dependent on previous tasks (cannot run in parallel)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create code and tests directory structure: `mkdir -p code tests/unit tests/integration data/raw data/interim data/processed`. **Verify**: `code/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/interim/`, `data/processed/` directories exist.

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (nibabel, numpy, scikit-image, scipy, pandas, statsmodels, nilearn, matplotlib, requests, tqdm, pyfd, wget, Pillow). **Verify**: Run `pip install -r requirements.txt` and verify `python -c "import nibabel; import numpy"` succeeds.

- [X] T003 [P] Configure linting and formatting tools: Create `.flake8` (max-line-length=88, exclude=venv,*.egg) and `pyproject.toml` (black config: line-length=88). **Verify**: Run `flake8 code/` and `black --check code/` with zero violations.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note**: All Foundational tasks marked [P] can run in parallel, EXCEPT T005a which depends on T001.

- [X] T004 Implement `code/config.py`: Initialize global seeds (numpy, random), define paths (`data/raw`, `data/interim`, `data/processed`), and set constants (OpenNeuro ID `ds000246`, HRF model `double-gamma` based on Friston et al. (1998): "Friston, K. J., et al. (1998). Event-related fMRI: characterizing differential responses. NeuroImage, 7(1), 30-40. ", HRF model peak=5s, undershoot=15s). **Verify**: Import `code.config` in Python shell without errors; constants match spec; citation is valid academic source; HRF parameters match `nilearn.glm.hemodynamic_models` canonical double-gamma.

- [X] T005 [P] Create `code/ingestion.py` skeleton with `wget` download logic and checksum verification for OpenNeuro dataset `ds000246`. **Verify**: `import code.ingestion` succeeds; function `def download_dataset(dataset_id: str) -> Path` exists.

- [X] T005a [P] Create `data/metadata.yaml` skeleton with keys: `dataset_id`, `version`, `checksum`, `download_date`. **AND** create/update `state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml` with `artifact_hashes` map. **Verify**: Files exist and are valid YAML/JSON. **Depends on**: T001. **Note**: This task creates the skeleton file. **Superseded by**: T014 for actual checksum computation and storage upon download.

- [X] T006 [P] Create `code/complexity.py` skeleton for image processing functions. **Verify**: `import code.complexity` succeeds; function `def calculate_entropy(image_path: Path) -> float` exists.

- [X] T007 Create `code/roi_extraction.py` skeleton for AAL atlas loading and smoothing. **Verify**: `import code.roi_extraction` succeeds; function `def extract_roi(bold_path: Path, mask_path: Path) -> np.ndarray` exists.

- [X] T008 Create `code/modeling.py` skeleton for GLM and permutation test structure. **Verify**: `import code.modeling` succeeds; function `def run_regression(X, y) -> dict` exists.

- [X] T009 Create `code/main.py` orchestrator with subject-wise chunking logic to enforce RAM limits. **Verify**: `import code.main` succeeds; function `def run_pipeline() -> None` exists.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, HRF Convolution, and Stimulus Complexity Calculation (Priority: P1) 🎯 MVP

**Goal**: Download preprocessed fMRI data/stimuli from `ds000246`, compute entropy/fractal dimension per frame, convolve with HRF, and output time-synced CSV.

**Independent Test**: Run ingestion script on a single subject; verify CSV output contains time-locked complexity scores and memory usage logs show ≤ 6GB peak.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Note on T010-T012**: These are "Write-First" tasks. They are marked [P] to allow parallel writing, but they will fail at runtime until T015/T016 are implemented.

- [X] T010 [P] [US1] Unit test for Shannon entropy calculation in `tests/unit/test_complexity.py`. **Test**: Implement `test_entropy_returns_positive`: Define a mock image path, call `calculate_entropy(mock_path)`, and assert `assert result > 0` to ensure the test fails before implementation.

- [X] T011 [P] [US1] Unit test for Fractal Dimension calculation in `tests/unit/test_complexity.py`. **Test**: Implement `test_fractal_dim_returns_positive`: Define a mock image path, call `calculate_fractal_dimension(mock_path)`, and assert `assert result > 0` to ensure the test fails before implementation.

- [X] T012 [P] [US1] Unit test for HRF convolution logic in `tests/unit/test_complexity.py`. **Test**: Implement `test_hrf_convolve_matches_shape`: Create a dummy time-series, call `convolve_with_hrf(dummy_series)`, and assert `assert len(output) >= len(input)` to ensure the test fails before implementation.

- [ ] T013 [D] [US1] Integration test for full ingestion pipeline on a single subject in `tests/integration/test_ingestion.py`. **Test**: Implement `test_pipeline_outputs_csv`: Run the pipeline on a single subject, check if `data/interim/complexity_metrics.csv` exists, and assert `assert os.path.exists(csv_path) and os.path.getsize(csv_path) > 0` to ensure the test fails before implementation. **Depends on**: T017. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/ingestion.py`: Download `ds000246` stimulus logs and BOLD data via `wget`, verify checksums, and implement logic to check for missing raw stimulus images. **CRITICAL**: <!-- FAILED: unspecified -->
 1. If raw images are missing, DO NOT raise a fatal error. Instead, trigger T014b to generate synthetic naturalistic images (Perlin noise/fractals) with a fixed seed.
 2. If the download fails entirely (network error or repo unavailability), raise a clear, descriptive error and halt.
 3. **ATOMIC CHECKSUM**: Immediately upon successful download (or synthetic generation), compute the checksum of the dataset (or generation parameters) and update `data/metadata.yaml` and `state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml` with `artifact_hashes`. This step MUST occur before any processing (T015) begins.
 **Verify**: `data/raw` contains downloaded files OR `data/raw/synthetic_stimuli/` exists; logs show checksum match (if raw) or generation success (if synthetic); dataset ID matches `ds000246`; metadata files updated atomically.

- [ ] T014a [D] [US1] Update `data/metadata.yaml` and `state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml` `artifact_hashes` after download. **CRITICAL**: This task is now superseded by the atomic step in T014. If T014 fails, this task is skipped. **Verify**: Both files updated with correct checksum/hash. **Depends on**: T005a, T014 (Success path only). **Note**: This task is a placeholder for the atomic step now in T014.

- [ ] T014b [D] [US1] Implement `code/synthetic_stimuli.py`: Generate a reproducible set of naturalistic images (Perlin noise/fractals) with fixed seed if raw images are missing. Store in `data/raw/synthetic_stimuli/`. **Verify**: Directory `data/raw/synthetic_stimuli/` exists; images match event log timing; seed is fixed. **Depends on**: T014 (failure path for raw images).

- [ ] T014d [D] [US1] Implement error handling for total dataset unavailability: If the `wget` download in T014 fails due to network error or repo unavailability (and synthetic generation is not an option, e.g., no event logs), raise a clear, descriptive error and halt execution. **Verify**: Script exits with code 1 and descriptive error message when simulated network failure occurs. **Depends on**: T014.

- [ ] T015 [US1] Implement `code/complexity.py`: Batch process stimulus images (raw OR synthetic from T014b) to compute Shannon Entropy and Fractal Dimension using `scikit-image`, ensuring memory-batched processing. **CRITICAL**: If `data/raw/synthetic_stimuli/` exists (from T014b), process those images. **Verify**: `data/interim` contains partial results; no OOM errors; synthetic images processed if raw missing. **Depends on**: T014 (Completion of download or synthetic generation).

- [ ] T016 [US1] Implement HRF convolution in `code/complexity.py`: Convolve complexity metrics with canonical HRF using `nilearn.glm.first_level.make_regressor` (Friston et al. (1998) double-gamma model, HRF model peak=5s, undershoot=15s) to align with BOLD signal. **Verify**: Output array length matches input + lag; convolution shape correct.

- [ ] T017 [US1] Implement output generation in `code/complexity.py`: Write time-synced CSV (`data/interim/complexity_metrics.csv`) with columns: `frame_id`, `timestamp`, `entropy`, `fractal_dim`, `hrf_convolved`. **Verify**: File exists; columns match exactly; first 5 rows printed.

- [ ] T018 [US1] Add error handling for NaN/Inf values in complexity metrics (replace with 0 or exclude frame) and log incidents. **Verify**: Log file contains "NaN replaced" entries for test data with artifacts.

- [ ] T018b [D] [US1] Implement missing frame handling: Parse stimulus logs (from T014) for missing timestamps, flag them, and exclude those specific frames from the complexity calculation. **Verify**: Log contains "Missing frame excluded" entries for test data with gaps. **Depends on**: T014 (Access to raw stimulus logs).

- [ ] T019 [US1] Add memory monitoring in `code/ingestion.py` and `code/complexity.py` to abort if RAM > 6GB. **CRITICAL**: Log peak RAM usage to `data/interim/memory_profile.log` with the EXACT format: "Peak RAM: {value:.2f} GB". **Verify**: Script exits with code 1 and error message if simulated memory spike occurs; log file contains peak RAM entry in the specified format.

- [ ] T019a [D] [US1] Implement watchdog timer for 6-hour execution limit in `code/main.py`. **CRITICAL**: Abort execution with a clear error if total runtime exceeds 6 hours. **Verify**: Script exits with code 1 and error message if simulated timeout occurs; log contains "Timeout exceeded" entry. **Depends on**: T009.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - ROI Extraction and Fixed Preprocessing (Priority: P2)

**Goal**: Extract mean DLPFC BOLD time-series using AAL atlas, apply smoothing and z-score normalization.

**Independent Test**: Run extraction on a single subject; verify output is a 1D CSV aligned with TR, with smoothing/normalization applied.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for AAL mask loading and voxel filtering in `tests/unit/test_roi_extraction.py`. **Test**: Implement `test_mask_loads_correctly`: Load the AAL mask, call `extract_roi(mock_bold, mock_mask)`, and assert `assert result.shape[0] > 0` to ensure the test fails before implementation.

- [ ] T021 [P] [US2] Unit test for Appropriate FWHM smoothing logic in `tests/unit/test_roi_extraction.py`. **Test**: Implement `test_smoothing_increases_variance`: Apply smoothing to a test image, calculate variance, and assert `assert variance_smoothed > variance_raw` to ensure the test fails before implementation.

- [ ] T022 [P] [US2] Integration test for ROI extraction pipeline in `tests/integration/test_roi_extraction.py`. **Test**: Implement `test_extraction_outputs_csv`: Run the extraction pipeline, check if `data/interim/pfc_timeseries.csv` exists, and assert `assert os.path.exists(csv_path) and os.path.getsize(csv_path) > 0` to ensure the test fails before implementation.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/roi_extraction.py`: Load AAL atlas mask, identify DLPFC voxels, and filter out-of-brain voxels. **Verify**: Mask loaded; valid voxel count > 0.

- [ ] T024 [US2] Implement spatial smoothing on BOLD data using `nilearn.image.smooth_img` with a Gaussian kernel with a moderate FWHM. **Verify**: Smoothed image file created; kernel size confirmed to be within a range suitable for the target application.

- [ ] T025 [US2] Implement z-score normalization of the **voxel-wise** BOLD data within the ROI mask **before** averaging to ensure SNR. **Verify**: Output mean ~0, std ~1; normalization applied voxel-wise before averaging; **Verify Voxel-Wise**: Check that mean and std of the voxel-wise data (before averaging) are approximately 0 and 1 respectively.

- [ ] T026 [US2] Output mean PFC BOLD signal per timepoint to `data/interim/pfc_timeseries.csv` (columns: `timepoint`, `bold_signal_mean`, `subject_id`). **Verify**: File exists; columns match; length matches stimulus timeline.

- [ ] T027 [US2] Add logging for excluded voxels and alignment verification with stimulus timeline. **Verify**: Log contains voxel exclusion count.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Perform linear regression (complexity vs. PFC), apply FDR correction, and run circular block permutation tests.

**Independent Test**: Run analysis script; verify results JSON contains correlation coefficients, FDR-corrected p-values, and permutation test results within 60 mins.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_modeling.py`. **Test**: Implement `test_fdr_corrects_p_values`: Pass a list of p-values to `apply_fdr`, and assert `assert all(p_corrected >= p_raw for p_corrected, p_raw in zip(result, p_values))` to ensure the test fails before implementation.

- [ ] T029 [P] [US3] Unit test for Circular Block Permutation implementation in `tests/unit/test_modeling.py`. **Test**: Implement `test_permutation_generates_null`: Run the permutation test on dummy data, check if a null distribution is generated, and assert `assert len(null_distribution) > 0` to ensure the test fails before implementation.

- [ ] T030 [P] [US3] Integration test for full statistical pipeline in `tests/integration/test_modeling.py`. **Test**: Implement `test_pipeline_outputs_json`: Run the full pipeline, check if `data/processed/regression_results.json` exists, and assert `assert os.path.exists(json_path) and os.path.getsize(json_path) > 0` to ensure the test fails before implementation.

### Implementation for User Story 3

- [ ] T030a [D] [US3] Implement Data Integrity Check: Verify `complexity_metrics.csv` (T017) and `pfc_timeseries.csv` (T026) exist and match checksums in `data/metadata.yaml` (updated by T014) before modeling. **CRITICAL**: This task MUST NOT run until User Story 1 (T017) and User Story 2 (T026) and T014 are marked COMPLETE. This task verifies data integrity only after full generation. **Verify**: Script exits if checksums mismatch or files missing. **Depends on**: T017 (COMPLETE), T026 (COMPLETE), T014 (COMPLETE).

- [ ] T031 [US3] Implement `code/modeling.py`: Load `complexity_metrics.csv` and `pfc_timeseries.csv`, merge on timepoint. **Verify**: Merged DataFrame created; no NaNs in key columns.

- [ ] T032 [US3] Implement Single-subject Linear Regression (OLS) with AR(1) pre-whitening using `nilearn.glm.first_level.FirstLevelModel` with `noise_model='ar1'` to handle temporal autocorrelation. **Verify**: Coefficients and p-values calculated; residuals checked for autocorrelation.

- [ ] T033 [US3] Implement FDR correction for the two metrics (entropy, fractal dimension) using Benjamini-Hochberg procedure. **Verify**: Corrected p-values saved; Log contains FDR vs FWER comparison metric (from T033a).

- [ ] T033a [D] [US3] Calculate FDR vs. FWER: Calculate the False Discovery Rate (FDR) and Family-Wise Error Rate (FWER) for the two metrics and output a comparison metric to verify SC-002. **Metric**: Compare the count of false positives at alpha=0.05 between FDR and FWER methods. **Output**: `data/processed/fdr_fwer_comparison.csv` with columns `metric_name, fdr_count, fwer_count, alpha_threshold`. **Verify**: Comparison metric logged; FDR and FWER values saved; **Verify**: Log the count of significant findings under FDR vs FWER at alpha=0.05. **Depends on**: T033.

- [ ] T034a [US3] Implement Circular Block Permutation Logic: Calculate block size as an integer multiple of TR (Repetition Time) and implement circular wrap-around (index modulo N) to preserve temporal autocorrelation. **CRITICAL**: This logic must operate on the **residuals** from the regression model (T032). **Verify**: Block size calculation is proportional to TR as established in Winkler et al.: "Winkler, A. M., et al. (2014). Permutation inference for the general linear model. NeuroImage, [volume], -397. "; wrap-around logic applied correctly in test data. **Depends on**: T031, T032.

- [ ] T034b [D] [US3] Execute Circular Block Permutation Test: Run multiple iterations using the logic from T034a (on **residuals** from T032) to generate null distribution and histogram. **CRITICAL**: This task consumes the **residuals** from T032 and must run **after** FDR correction (T033) to ensure the null distribution is generated in the correct validation sequence. **Verify**: Null distribution histogram generated; temporal autocorrelation preserved (verified by checking block integrity). **Depends on**: T034a, T032, T033.

- [ ] T035 [D] [US3] Generate `data/processed/regression_results.json` containing: `correlation_coefficient`, `p_value`, `fdr_corrected_p`, `permutation_p`, `is_significant`. **Logic**: Calculate `p_value` as (count of null stats >= observed stat) / (total permutations). **CRITICAL**: The 'observed stat' is the coefficient from the **FDR-corrected model (T033)**. The 'null stats' are from **T034b (circular block permutation of residuals from T032)**. Derive `is_significant` as `True` if `p_value < 0.05`. **Verify**: JSON file valid; all keys present; boolean logic correct; verification confirms null distribution used was circular block. **Depends on**: T032, T033, T034b.

- [ ] T036 [US3] Generate `data/processed/null_distribution.png` histogram for permutation test visualization. **Verify**: Image file created.

- [ ] T037 [US3] Add logic to exclude subjects with excessive motion artifacts (flagged in logs) from group-level aggregation. **Verify**: Log shows excluded subjects; group stats recalculated.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [General] Update `README.md` with installation instructions, environment setup, and run instructions (`python -m code.main`). **Verify**: README contains clear steps; `python -m code.main` runs successfully.

- [ ] T038b [General] Create `docs/quickstart.md` with pipeline execution steps and expected outputs. **Verify**: File exists and contains accurate execution steps.

- [ ] T039a [FR-002] [FR-007] Extract memory monitoring logic to a utility module `code/utils/memory.py` for reuse in the main pipeline orchestrator. **Verify**: Module importable; no circular dependencies; memory check used in `code/main.py`.

- [ ] T039b [FR-002] Remove dead code and unused imports from `code/` modules. **Verify**: `flake8 --select=F401` reports zero unused imports.

- [ ] T040 Optimize batch sizes in `code/complexity.py` to ensure peak RAM usage stays ≤ 6GB. **Verify**: Run with test data; log confirms peak ≤ 6GB.

- [ ] T041a [P] [US1] Unit test for missing frames in `tests/unit/test_complexity.py`. **Test**: Implement `test_missing_frames`: Pass data with missing frames, call the processing function, and assert `assert len(output) < len(input)` to ensure the test fails before implementation.

- [ ] T041b [P] [US1] Unit test for NaN handling in `tests/unit/test_complexity.py`. **Test**: Implement `test_nan_handling`: Pass data with NaN values, call the processing function, and assert `assert 0 not in output` (or similar logic) to ensure the test fails before implementation.

- [ ] T042 Run quickstart.md validation: Execute `python -m code.main` (as defined in quickstart.md) and verify exit code 0 and `data/processed/regression_results.json` exists.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **MUST** run after US1 and US2 are complete to ensure data availability (complexity metrics and PFC time-series must exist before regression).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T005a
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- US3 MUST wait for US1 and US2 completion

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
 - Developer A: User Story 1 (Data Ingestion & Complexity)
 - Developer B: User Story 2 (ROI Extraction)
 - Developer C: User Story 3 (Modeling) - *Must wait for A and B data files*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [D] tasks = dependent on previous tasks (cannot run in parallel)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: US3 tasks (T031-T036) depend on the successful output of US1 (T019) and US2 (T027). Do not attempt to run modeling scripts before data files exist.
- **Dataset ID**: All tasks reference `ds000246` as per Spec FR-001. The plan consistently references `ds000246`.
- **HRF Lag**: Fixed at double-gamma model (HRF model peak=5s, undershoot=15s) based on Friston et al. (1998) for reproducibility.
- **Resource Constraint**: All image processing tasks must use batched loading to ensure ≤ 6GB RAM usage on CPU-only runners.
- **Single-Subject Focus**: Implementation focuses strictly on single-subject regression and permutation testing as per Spec US-3. No group-level aggregation is implemented.
- **Significance Logic**: T035 explicitly checks `p < 0.05` derived from the permutation count, aligning with SC-001.
- **Revision Status**: This tasks.md file has been revised to address specific panel concerns regarding synthetic stimuli, HRF citations, FDR correction, test executability, and scope alignment.