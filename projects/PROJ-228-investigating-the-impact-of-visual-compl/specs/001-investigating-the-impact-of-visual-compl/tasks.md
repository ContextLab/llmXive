# Tasks: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

**Input**: Design documents from `/specs/001-visual-complexity-pfc/`
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

**Purpose**: Project initialization and basic structure

- [X] T001a Create source directory structure: `mkdir -p code tests/unit tests/integration`. **Verify**: Directories exist. <!-- FAILED: unspecified -->
- [X] T001b Create data directory structure: `mkdir -p data/raw data/interim data/results`. **Verify**: Directories exist.
- [X] T001c Create documentation directory structure: `mkdir -p docs`. **Verify**: Directory exists.
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (nibabel, numpy, scikit-image, scipy, pandas, statsmodels, nilearn, matplotlib, requests, tqdm). **Verify**: Run `pip install -r requirements.txt` and verify `python -c "import nibabel; import numpy"` succeeds.
- [X] T003 [P] Configure linting and formatting tools (black, flake8)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py`:Initialize global seeds (numpy, random), define paths (`data/raw`, `data/interim`, `data/results`), and set constants (OpenNeuro ID `ds000246`, HRF model `double-gamma` with peak=5s, undershoot=15s, {{claim:c_0e75b9e6}} (Wikipedia: Samsung Galaxy A50, https://en.wikipedia.org/wiki/Samsung_Galaxy_A50)). **Verify**: Import `code.config` in Python shell without errors; constants match spec.
- [ ] T005 [P] Create `code/ingestion.py` skeleton with `wget` download logic and checksum verification for OpenNeuro dataset `ds000246`. **Verify**: `import code.ingestion` succeeds; function `def download_dataset(dataset_id: str) -> Path` exists.
- [X] T005a [P] Create `data/metadata.yaml` skeleton with keys: `dataset_id`, `version`, `checksum`, `download_date`. **AND** create/update `state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml` with `artifact_hashes` map. **Verify**: Files exist and are valid YAML/JSON. **Depends on**: T001b.
- [X] T006 [P] Create `code/complexity.py` skeleton for image processing functions. **Verify**: `import code.complexity` succeeds; function `def calculate_entropy(image_path: Path) -> float` exists.
- [X] T007 Create `code/roi_extraction.py` skeleton for AAL atlas loading and smoothing. **Verify**: `import code.roi_extraction` succeeds; function `def extract_roi(bold_path: Path, mask_path: Path) -> np.ndarray` exists.
- [X] T008 Create `code/modeling.py` skeleton for GLM and permutation test structure. **Verify**: `import code.modeling` succeeds; function `def run_regression(X, y) -> dict` exists.
- [ ] T009 Create `code/main.py` orchestrator with subject-wise chunking logic to enforce RAM limits. **Verify**: `import code.main` succeeds; function `def run_pipeline() -> None` exists.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, HRF Convolution, and Stimulus Complexity Calculation (Priority: P1) 🎯 MVP

**Goal**: Download preprocessed fMRI data/stimuli from `ds000246`, compute entropy/fractal dimension per frame, convolve with HRF, and output time-synced CSV.

**Independent Test**: Run ingestion script on a single subject; verify CSV output contains time-locked complexity scores and memory usage logs show ≤ 6GB peak.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for Shannon entropy calculation in `tests/unit/test_complexity.py`. **Test**: `test_entropy_returns_positive` asserts `calculate_entropy` raises `NotImplementedError` before implementation. <!-- ATOMIZE: requested -->
- [X] T011 [P] [US1] Unit test for Fractal Dimension calculation in `tests/unit/test_complexity.py`. **Test**: `test_fractal_dim_returns_positive` asserts `calculate_fractal_dimension` raises `NotImplementedError` before implementation.
- [ ] T012 [P] [US1] Unit test for HRF convolution logic in `tests/unit/test_complexity.py`. **Test**: `test_hrf_convolve_matches_shape` asserts `convolve_with_hrf` raises `NotImplementedError` before implementation.
- [ ] T013 [P] [US1] Integration test for full ingestion pipeline on a single subject in `tests/integration/test_ingestion.py`. **Test**: `test_pipeline_outputs_csv` asserts file creation fails before implementation.

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/ingestion.py`: Download `ds000246` stimulus logs and BOLD data via `wget`, verify checksums, handle missing frames gracefully. **Verify**: `data/raw` contains downloaded files; logs show checksum match; dataset ID matches `ds000246`.
- [ ] T014a [US1] Write dataset `ds000246` checksum and version to `data/metadata.yaml` AND update `state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml` `artifact_hashes` immediately after download. **Verify**: Both files updated with correct checksum. **Depends on**: T005a.
- [ ] T015 [US1] Implement `code/complexity.py`: Batch process stimulus images to compute Shannon Entropy and Fractal Dimension using `scikit-image`, ensuring memory-batched processing. **Verify**: `data/interim` contains partial results; no OOM errors.
- [ ] T016 [US1] Implement HRF convolution in `code/complexity.py`: Convolve complexity metrics with canonical HRF using `nilearn.glm.first_level.make_regressor` (double-gamma model, peak=5s, undershoot=15s) to align with BOLD signal. **Verify**: Output array length matches input + lag; convolution shape correct.
- [ ] T017 [US1] Implement output generation in `code/complexity.py`: Write time-synced CSV (`data/interim/complexity_metrics.csv`) with columns: `frame_id`, `timestamp`, `entropy`, `fractal_dim`, `hrf_convolved`. **Verify**: File exists; columns match exactly; first 5 rows printed.
- [ ] T018 [US1] Add error handling for NaN/Inf values in complexity metrics (replace with 0 or exclude frame) and log incidents. **Verify**: Log file contains "NaN replaced" entries for test data with artifacts.
- [ ] T019 [US1] Add memory monitoring in `code/ingestion.py` and `code/complexity.py` to abort if RAM > 6GB. **Verify**: Script exits with code 1 and error message if simulated memory spike occurs.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - ROI Extraction and Fixed Preprocessing (Priority: P2)

**Goal**: Extract mean DLPFC BOLD time-series using AAL atlas, apply smoothing and z-score normalization.

**Independent Test**: Run extraction on a single subject; verify output is a 1D CSV aligned with TR, with smoothing/normalization applied.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test for AAL mask loading and voxel filtering in `tests/unit/test_roi_extraction.py`. **Test**: `test_mask_loads_correctly` asserts `NotImplementedError` before implementation.
- [ ] T021 [P] [US2] Unit test for 4mm FWHM smoothing logic [UNRESOLVED-CLAIM: c_ab1011b0 — status=not_enough_info] in `tests/unit/test_roi_extraction.py`. **Test**: `test_smoothing_increases_variance` asserts `NotImplementedError` before implementation.
- [ ] T022 [P] [US2] Integration test for ROI extraction pipeline in `tests/integration/test_roi_extraction.py`. **Test**: `test_extraction_outputs_csv` asserts file creation fails before implementation.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `code/roi_extraction.py`: Load AAL atlas mask, identify DLPFC voxels, and filter out-of-brain voxels. **Verify**: Mask loaded; valid voxel count > 0.
- [ ] T024 [US2] Implement spatial smoothing on BOLD data using `nilearn.image.smooth_img` with an appropriate FWHM kernel. **Verify**: Smoothed image file created; kernel size confirmed.
- [ ] T025 [US2] Implement z-score normalization of the mean time-series within the DLPFC ROI. **Verify**: Output mean ~0, std ~1.
- [ ] T026 [US2] Output mean PFC BOLD signal per timepoint to `data/interim/pfc_timeseries.csv` (columns: `timepoint`, `bold_signal_mean`, `subject_id`). **Verify**: File exists; columns match; length matches stimulus timeline.
- [ ] T027 [US2] Add logging for excluded voxels and alignment verification with stimulus timeline. **Verify**: Log contains voxel exclusion count.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Modeling and Validation (Priority: P3)

**Goal**: Perform linear regression (complexity vs. PFC), apply FDR correction, and run circular block permutation tests.

**Independent Test**: Run analysis script; verify results JSON contains correlation coefficients, FDR-corrected p-values, and permutation test results within 60 mins.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_modeling.py`. **Test**: `test_fdr_corrects_p_values` asserts `NotImplementedError` before implementation.
- [ ] T029 [P] [US3] Unit test for Circular Block Permutation implementation in `tests/unit/test_modeling.py`. **Test**: `test_permutation_generates_null` asserts `NotImplementedError` before implementation.
- [ ] T030 [P] [US3] Integration test for full statistical pipeline in `tests/integration/test_modeling.py`. **Test**: `test_pipeline_outputs_json` asserts file creation fails before implementation.

### Implementation for User Story 3

- [ ] T030a [US3] Implement Data Integrity Check: Verify `complexity_metrics.csv` and `pfc_timeseries.csv` exist and match checksums in `data/metadata.yaml` and `state/projects/...yaml` before modeling. **Verify**: Script exits if checksums mismatch or files missing.
- [ ] T031 [US3] Implement `code/modeling.py`: Load `complexity_metrics.csv` and `pfc_timeseries.csv`, merge on timepoint. **Verify**: Merged DataFrame created; no NaNs in key columns.
- [ ] T032 [US3] Implement Single-subject Linear Regression (OLS) with AR(1) pre-whitening using `nilearn.glm.first_level.FirstLevelModel` with `noise_model='ar1' [UNRESOLVED-CLAIM: c_43739738 — status=not_enough_info] ` to handle temporal autocorrelation. **Verify**: Coefficients and p-values calculated; residuals checked for autocorrelation.
- [ ] T033 [US3] Implement FDR correction ({{claim:c_2be034ca}} (Wikidata Q136366870, https://www.wikidata.org/wiki/Q136366870)) for the two metrics (entropy, fractal dimension). **Verify**: Corrected p-values saved.
- [ ] T034 [US3] Implement Circular Block Permutation Test with a sufficient number of iterations. **Block Size**: Calculate as 2 * TR (Repetition Time) to preserve temporal autocorrelation. **Verify**: Null distribution histogram generated.
- [ ] T035 [US3] Generate `data/results/regression_results.json` containing: `correlation_coefficient`, `p_value`, `fdr_corrected_p`, `permutation_p`, `is_significant`. **Logic**: Derive `is_significant` as `True` if the observed correlation coefficient falls outside the confidence interval of the null distribution generated by the permutation test. **Verify**: JSON file valid; all keys present; boolean logic correct.
- [ ] T036 [US3] Generate `data/results/null_distribution.png` histogram for permutation test visualization. **Verify**: Image file created.
- [ ] T037 [US3] Add logic to exclude subjects with excessive motion artifacts (flagged in logs) from group-level aggregation. **Verify**: Log shows excluded subjects; group stats recalculated.
- [ ] T037a [US3] Implement Group-level aggregation: Collect subject-level beta-weights and standard errors into a single DataFrame. **Verify**: Aggregated DataFrame created.
- [ ] T037b [US3] Implement Group-level t-test: Perform one-sample t-test on subject-level beta-weights against zero to determine group significance. **Verify**: Group-level p-value and confidence interval calculated.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [FR-001] Update `README.md` with installation instructions, environment setup, and run instructions (`python -m code.main`). **Verify**: README contains clear steps; `python -m code.main` runs successfully.
- [ ] T038b [FR-001] Create `docs/quickstart.md` with pipeline execution steps and expected outputs. **Verify**: File exists and contains accurate execution steps.
- [ ] T039a [FR-002] [FR-007] Extract memory monitoring logic to a utility module `code/utils/memory.py` for reuse in the main pipeline orchestrator. **Verify**: Module importable; no circular dependencies; memory check used in `code/main.py`.
- [ ] T039b [FR-002] Remove dead code and unused imports from `code/` modules. **Verify**: `flake8 --select=F401` reports zero unused imports.
- [ ] T040 Optimize batch sizes in `code/complexity.py` to ensure peak RAM usage stays < 5.5GB. **Verify**: Run with test data; log confirms peak < 5.5GB.
- [ ] T041 [P] Additional unit tests for edge cases (missing frames, NaN handling) in `tests/unit/`.
- [ ] T042 Run quickstart.md validation: Execute `python -m code.main` (as defined in quickstart.md) and verify exit code 0 and `data/results/regression_results.json` exists.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: US3 tasks (T031-T037b) depend on the successful output of US1 (T019) and US2 (T027). Do not attempt to run modeling scripts before data files exist.
- **Dataset ID**: All tasks reference `ds000246` as per Spec FR-001. (Note: Plan.md contains a discrepancy mentioning `ds000248`; tasks enforce `ds000246` to comply with the Spec).
- **HRF Lag**: Fixed at double-gamma model (peak=5s, undershoot=15s) for reproducibility.
- **Resource Constraint**: All image processing tasks must use batched loading to ensure <6GB RAM usage on CPU-only runners.
- **Two-Level GLM**: Implementation includes subject-level AR(1) pre-whitening (T032) and group-level t-test (T037b) as required by the Plan and Spec.
- **Significance Logic**: T035 explicitly checks if the observed statistic falls outside the 95% CI of the null distribution [UNRESOLVED-CLAIM: c_3a5e375a — status=not_enough_info], not just p < 0.05.