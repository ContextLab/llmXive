# Tasks: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Input**: Design documents from `/specs/001-neural-correlates-social-exclusion/`
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

- [X] T001 Create directory structure: `data/raw`, `data/processed`, `data/results`, `src`, `tests`, `state`
- [X] T002 Create `src/__init__.py` and `tests/__init__.py` to initialize Python packages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (numpy, pandas, scipy, scikit-learn, nibabel, nilearn, pyyaml, requests, matplotlib, pytest)
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`
- [X] T005 [P] Implement `config.yaml` with paths, seeds, and constants. **Specific Requirement**: Set `motion_threshold: 3.0` (float) explicitly to satisfy Constitution Principle VI and FR-002. Do NOT use "moderate" or vague defaults. Define `dmn_rois: ['Posterior_Cingulate_Cortex', 'Medial_Prefrontal_Cortex', 'Angular_Gyrus']`. **Dependencies**: None.
- [ ] T006 Implement base utility modules and custom exceptions.
 **Creates** `src/utils.py` (logging, helper functions) and `src/exceptions.py` defining two exception classes:
 ```python
 class DataUnavailableError(ValueError):
 """Raised when required data files or trial markers cannot be found."""
 def __init__(self, reason: str):
 super().__init__(f"Data unavailable: {reason}")

 class InsufficientSubjectsError(ValueError):
 """Raised when the number of retained subjects is below the minimum required (N<10)."""
 def __init__(self, count: int):
 super().__init__(f"Insufficient subjects (N={count}) for valid permutation test.")
 ```
 These classes are used throughout the pipeline (T012, T015, T017, T023). **NOTE**: This task is **not** parallel‑safe; it must complete before any downstream import.
- [X] T007 [P] Implement data integrity checker (SHA‑256) utility function in `src/integrity.py` to compute checksums and update `state/projects/PROJ-474-neural-correlates-of-simulated-social-ex.yaml` under `artifact_hashes`; **DO NOT** perform the actual download or checksumming of raw data in this task; this task provides the **utility function** that T012, T014 and T028 MUST call. **Schema**: `artifact_hashes`: `{ "raw/{filename}": "<sha256>", "processed/{filename}": "<sha256>" }`. **Dependencies**: T006 (for exception handling).
- [X] T008 Setup `pytest` configuration in `tests/conftest.py` with seed pinning for reproducibility

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Quality Control (Priority: P1) 🎯 MVP

**Goal**: Download real fMRI data from OpenNeuro, calculate motion metrics, and enforce strict QC thresholds (FR‑002, FR‑009, FR‑010).

**Independent Test**: Can be fully tested by executing the data pipeline on a single subject file, verifying the motion parameter output, and confirming the subject is either retained or excluded based on the >3 mm threshold.

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/data_loader.py` to fetch OpenNeuro dataset `ds000030`. **Steps (in order)**:
. Download the dataset zip from `https://openneuro.org/datasets/[dataset_identifier]/versions/1.0.0/download` with retry logic (exponential backoff, a limited number of attempts).
 2. Verify SHA‑256 checksum (provided in dataset metadata) using the utility from T007; raise `DataUnavailableError` on mismatch.
 3. Extract the zip to `data/raw/ds000030`.
 4. Scan each subject’s `events.tsv` files to ensure both “Inclusion” and “Exclusion” trial types exist; raise `DataUnavailableError` if any subject lacks required markers.
 5. **Critical**: Verify `*_confounds.tsv` exists. If pre-calculated FD is missing, calculate Framewise Displacement (FD) from the six motion parameters and their derivatives found in `confounds.tsv` using the standard formula (sum of absolute differences of translation and rotation).
 **Output**: `data/raw/ds000030` (BIDS directory) and per-subject motion metrics.
 **Prerequisites**: T006 (exceptions) and T007 (checksum utility).
- [X] T013 [US1] Implement `src/qc.py` to calculate Framewise Displacement (FD) for every subject from the standard BIDS `*_confounds.tsv` motion parameters. Output per‑subject FD CSV in `data/processed/fd_{subject_id}.csv`. **Depends on** T012 and T006.
- [X] T016 [US1] Implement `src/qc.py` to verify that each subject’s `events.tsv` contains both Inclusion and Exclusion markers (metadata check only). Produce a list of dictionaries `{subject_id, motion_metric, condition_status, retained}` where `condition_status` is `"valid"` if both markers exist, otherwise `"invalid"`. **Depends on** T013 (motion) and T012 (download). No time‑series extraction required here.
- [ ] T014 [US1] Implement `src/qc.py` to **filter** the list from T016 and write two JSON files:
 1. `data/processed/subject_qc_list.json` – full list (including excluded subjects).
 2. `data/processed/subjects_metadata.json` – **definitive list of retained subjects** with schema `[ {"subject_id": str, "motion_metric": float, "condition_status": "valid", "retained": true},... ]`.
 After writing each file, invoke the checksum utility (T007) to update the state file. **Depends on** T016 and T007. **Note**: This is the **sole producer** of `subjects_metadata.json`.
- [X] T015 [US1] Implement `src/qc.py` to count retained subjects from `subjects_metadata.json`; if count < 10, raise `InsufficientSubjectsError`. **Depends on** T014.
- [X] T017 [US1] Implement `src/main.py` orchestrator to:
 1. Call T012 (download).
 2. Run QC steps T013‑T016.
 3. Invoke T014 to generate `subjects_metadata.json`.
 4. Execute T015; if `InsufficientSubjectsError` is raised, exit with error code `ERR_N_INSUFFICIENT`.
 5. Load the retained subject IDs from `subjects_metadata.json` and pass them to downstream pipelines (US2, US3).
 **Depends on** T012, T013, T014, T015, T016, T006, T007.
 **Produces** no new artifact beyond those listed above.

### Tests for User Story 1
> Note: Tasks T009‑T011 are implemented as failing stubs first. They will intentionally fail until the corresponding implementation tasks (T012‑T018) are completed, adhering to the "tests first" methodology. These tests are now independent of the implementation tasks to avoid circular dependencies. They define the expected interfaces and will be updated to assert behavior once the code exists.

- [X] T009 [US1] Unit test stub for `test_motion_calculation` in `tests/unit/test_qc.py`; define function signature `calculate_motion(subject_id)` in a stub file (independent of `src/qc.py` existence); assert `NotImplementedError`; verify eventual behavior: assert that motion > 3 mm triggers exclusion flag;
- [X] T010 [US1] Unit test stub for `test_motion_hard_stop` in `tests/unit/test_qc.py`; define function signature `check_subject_count(subject_list)` in a stub file; assert `NotImplementedError`; verify eventual behavior: assert that N < 10 raises `InsufficientSubjectsError`;
- [X] T011 [US1] Unit test stub for `test_condition_completeness` in `tests/unit/test_qc.py`; define function signature `verify_conditions(subject_id)` in a stub file; assert `NotImplementedError`; verify eventual behavior: assert that missing Inclusion or Exclusion condition triggers exclusion;

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Sensitivity Analysis (Pre-Halt)

**Goal**: Execute sensitivity analysis on the full subject list *before* the hard halt check to ensure SC-005 is met even if strict QC reduces N < 10.

- [ ] T036 [US3] Implement sensitivity analysis in `src/stats.py`:
 - Load the **full** subject list with motion metrics from `data/processed/subject_qc_list.json` (produced by T016).
 - **Run BEFORE T015/T017 hard halt** to ensure execution even if N < 10 after strict 3.0mm filtering.
 - Loop over motion thresholds **3.0 mm, 3.2 mm, 3.4 mm, 3.6 mm, 3.8 mm, 4.0 mm**.
 - For each threshold:
 1. Filter subjects from the full list (re-apply threshold).
 2. If N < 10 for a specific threshold, skip that threshold or record N/A.
 3. Re-use preprocessed time-series from T024 (if available) or re-extract from raw data if necessary.
 4. Compute connectivity metrics (MAC) and **re-run edge-wise statistical testing (FR-011)** with FDR correction for each threshold.
 5. Record global p-value, effect size, AND edge-wise corrected p-values.
 - Output `data/results/sensitivity_curve.csv` (columns: threshold, p_value, effect_size, edge_p_values) and a plot `data/results/sensitivity_curve.png`.
 **Depends on** T016 (full list), T024 (preprocessed data), and T006. **Does NOT depend on T014 or T015**.

**Checkpoint**: Sensitivity analysis complete before any hard halts.

---

## Phase 4: User Story 2 - Connectivity Metric Computation (Priority: P2)

**Goal**: Extract ROI time‑series, compute correlation matrices, and derive connectivity strength metrics (FR‑003, FR‑004, FR‑005).

**Independent Test**: Can be tested by running the calculation on a synthetic time‑series dataset with known correlations and verifying the output matches the expected mean absolute correlation value.

### Implementation for User Story 2

- [X] T018 [US2] Implement `src/confounds_extractor.py` to locate and read each subject’s `*_confounds.tsv` (standard BIDS) for the six motion parameters and their first‑order derivatives, and to generate WM/CSF masks using the Harvard‑Oxford atlas via nilearn. **Steps**:
 1. Use `nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thrmm')` to fetch the atlas.
 2. Extract WM and CSF masks based on atlas labels.
 Outputs:
 - `data/processed/confounds_{subject_id}.tsv`
 - `data/processed/wm_mask_{subject_id}.nii.gz`
 - `data/processed/csf_mask_{subject_id}.nii.gz`
 **Depends on** T012 (raw data) and T006 (exceptions).
- [X] T023 [US2] Implement `src/preprocessing.py` to perform nuisance regression on each subject’s raw 4D NIfTI using: (i) six motion parameters + their derivatives from `confounds_{subject_id}.tsv`, (ii) WM signal extracted with `wm_mask_{subject_id}.nii.gz`, (iii) CSF signal extracted with `csf_mask_{subject_id}.nii.gz`. Use memory‑mapped loading (`nilearn.image.load_img(..., mmap=True)`) to stay <7 GB RAM. Output preprocessed NIfTI to `data/processed/preprocessed_{subject_id}.nii.gz`. After writing, call the checksum utility (T007). **Depends on** T018 and T006. **Note**: Correlation matrices (FR-004) MUST be computed on this **preprocessed** time-series.
- [X] T024 [US2] Implement `src/extraction.py` to extract BOLD time‑series from PCC, mPFC, and Angular Gyrus using the AAL/Harvard‑Oxford atlas. **Specific Labels**: Use labels `'Posterior_Cingulate_Cortex'`, `'Medial_Prefrontal_Cortex'`, `'Angular_Gyrus'`. **Fallback**: If exact string labels are not found in the atlas, map semantic names to indices or use nearest neighbor matching based on atlas coordinates. Load preprocessed files with `mmap=True`. Output per‑subject CSVs `data/processed/timeseries_{subject_id}.csv`. **Depends on** T023.
- [X] T025 [US2] Implement `src/connectivity.py` to segment each subject’s time‑series into Inclusion and Exclusion blocks based on `events.tsv` markers. **Depends on** T024.
- [X] T026 [US2] Implement `src/connectivity.py` to compute Pearson correlation matrices for each condition (Inclusion, Exclusion). **Depends on** T025.
- [X] T027 [US2] Implement `src/connectivity.py` to calculate Mean Absolute Correlation (MAC) per condition per subject and write a consolidated JSON `data/processed/connectivity_metrics.json` with schema `{ "subject_id": {"inclusion": float, "exclusion": float} }`. Also invoke the checksum utility (T007). **Depends on** T026.

### Tests for User Story 2

- [X] T020 [P] [US2] Unit test for preprocessing logic in `tests/unit/test_preprocessing.py` (verify nuisance regression)
- [X] T021 [P] [US2] Unit test for ROI extraction logic in `tests/unit/test_extraction.py` (verify signal extraction from PCC, mPFC, Angular)
- [X] T022 [P] [US2] Unit test for correlation calculation in `tests/unit/test_connectivity.py` (verify Pearson correlation and MAC math)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Hypothesis Testing (Priority: P3)

**Goal**: Execute permutation tests, apply FDR correction, generate sensitivity curves, and frame results correctly (FR‑006, FR‑007, FR‑008, FR‑011, SC‑005).

**Independent Test**: Can be tested by running the permutation test on a dataset where the null hypothesis is known to be true (random noise) and verifying the p‑value distribution is uniform.

### Implementation for User Story 3

- [X] T033 [US3] Implement `src/stats.py` with a non‑parametric paired permutation test for MAC values (subject‑level). Iterations are adaptive: `max(1000, 10 * N)` capped at 10 000 to stay computationally feasible. Returns p‑value, effect size (Cohen’s d), and the full null distribution.
- [X] T034 [US3] Implement `src/stats.py` for **edge‑wise** paired permutation tests. Dynamically derive the list of edges from the ROI extraction step (T024) – i.e., all pairwise combinations among the extracted DMN nodes. Apply Benjamini‑Hochberg FDR correction (q ≤ 0.05) to the resulting p‑values. Returns a dictionary `{edge: {"p": float, "effect_size": float}}`.
- [X] T035 [US3] Extend `src/stats.py` to compute the standard deviation of the MAC null distribution and store both `std_dev_null` and a stability ratio `z_score = |mean_MAC - mean_null| / std_dev_null` in `data/results/stability_metric.json`. **Depends on** T033.
- [X] T037 [US3] Implement check in `src/stats.py` to read dataset metadata (`dataset_description.json`) for field `randomization_verified`. If false or missing, set a flag `is_associational = True`. Downstream reporting will embed the literal word “associational”.
- [X] T038 [US3] Implement `src/visualization.py` to generate:
 - Null‑distribution histogram for the global MAC test.
 - Bar plot with mean MAC difference and 95 % confidence intervals.
 - Edge‑wise significance heatmap (optional).
 Outputs saved under `data/results/`.
- [X] T039 [US3] Implement `src/main.py` orchestration for statistical analysis:
 1. Load `connectivity_metrics.json`.
 2. Run T033 (global MAC permutation).
 3. Run T034 (edge‑wise tests).
 4. Run T035 (stability metric).
 5. Run T037 to set associational framing.
 6. Run T038 to produce visualizations.
 7. Compile all results into `data/results/statistical_report.json` (including global p‑value, effect size, edge‑wise corrected p‑values, stability metric, sensitivity curve summary, and associational flag).
 8. Validate that the report contains the literal string “associational” when required; raise `ValueError` otherwise.
 **Depends on** T027, T033‑T035, T037‑T038, and T043 (refactored main).
- [X] T040 [US3] Implement `src/verification.py` to programmatically verify that `statistical_report.json` (or final PDF/HTML) contains the word “associational” when the flag is set; raise an error if missing. **Depends on** T039.

### Tests for User Story 3

- [X] T029 [P] [US3] Unit test for `test_permutation_logic` in `tests/unit/test_stats.py` (verify shift detection in synthetic data)
- [X] T030 [P] [US3] Unit test for `test_edge_wise_fdr` in `tests/unit/test_stats.py` (verify FDR correction application)
- [X] T031 [P] [US3] Unit test for `test_sensitivity_curve` in `tests/unit/test_stats.py` (verify generation of curve across thresholds)
- [X] T032 [P] [US3] Unit test for stability metric calculation in `tests/unit/test_stats.py` (verify null distribution std dev calculation)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Create `quickstart.md` in `specs/001-neural-correlates-social-exclusion/`
- [X] T042 [P] Create `data-model.md` in `specs/001-neural-correlates-social-exclusion/`
- [ ] T043 Refactor `src/main.py` into a clean orchestrator that sequentially invokes:
 - T017 (download & QC)
 - T023‑T027 (preprocessing, extraction, connectivity)
 - T033‑T039 (statistics, visualizations, reporting)
 - Handles exceptions from `src/exceptions.py` and ensures graceful exit codes.
 **Depends on** all prior tasks; ensures a single entry‑point for the pipeline.
- [X] T044 Performance optimization: Ensure memory usage stays within 7 GB limit during permutation tests (chunking if necessary)
- [X] T045 [P] Additional unit tests for edge cases (missing files, malformed JSON) in `tests/unit/`
- [X] T046 Run `quickstart.md` validation to ensure end‑to‑end pipeline execution on CPU‑only runner

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires QC output from US1 (`subjects_metadata.json`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires Connectivity Metrics from US2 (`connectivity_metrics.json`)

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
- All tests for a user story marked [P] can run in parallel (once implementation exists)
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
- **Real Data Only**: T012 must fetch real data from OpenNeuro ds000030. Simulation is only for unit tests, not the main pipeline.
- **CPU Constraints**: All tasks must be feasible on Multiple CPU cores, sufficient RAM, no GPU.
- **Sensitivity Curve Logic**: T036 re‑calculates metrics for different motion thresholds **≥ 3.0 mm** using the full subject list, satisfying SC‑005 without violating the hard exclusion rule.
- **Memory Management**: T023 and T024 must strictly adhere to memory‑mapped loading (`mmap=True`) to prevent OOM errors on the 7 GB runner.
- **Error Handling**: All data loading tasks must fail loudly (raise exceptions) rather than falling back to synthetic data, per the "Real Data Only" constitution rule.
- **Exception Definitions**: `DataUnavailableError` and `InsufficientSubjectsError` are defined in `src/exceptions.py` and are imported wherever needed.
- **Checksum Flow**: Any artifact creation task (T012, T014, T023, T027, etc.) calls the checksum utility (T007) immediately after writing to keep the state file up‑to‑date.
- **ATLAS LABELS**: T024 uses specific atlas labels; fallback logic is implemented for missing labels.
- **SENSITIVITY ORDERING**: T036 runs BEFORE T015/T017 to avoid hard halts.