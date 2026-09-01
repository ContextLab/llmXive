# Tasks: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Input**: Design documents from `/specs/001-predicting-cognitive-load-eeg/`
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
 Implemented independently
 - Tested independently
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Project Initialization

**Purpose**: Project initialization and basic structure

- [X] T003 [P] Create project structure per implementation plan: `mkdir -p code/data code/features code/models tests/unit tests/integration data/raw data/processed results`.

- [X] T004 [P] Update `state/` YAML with checksums and `updated_at` timestamp for the new project structure. **Delegated to T043.**

- [X] T005 [P] Initialize Python 3.11 project with pinned dependencies (`mne`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `requests`) in `requirements.txt`

- [X] T006 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Verification & Power Analysis (formerly Phase 0) to ensure data availability.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/config.py` to load `pipeline_config.yaml` and environment variables.

- [X] T008 [P] Implement `code/data/loader.py` with chunked loading logic (by `epoch_id`) to ensure memory safety (≤ 6.5 GB). **Logic must be triggered when estimated memory usage > 6.5 GB. Do NOT use streaming API.**

- [X] T009 [US1] Implement `code/data/generate_manifest.py` to produce `data/manifest.yaml` containing fields: `url`, `version`, `checksum_sha256` (computed via SHA-256 of the downloaded tarball). **Must run after T010**.

- [X] T010 [P] Implement `code/data/download.py` with a strict verification gate: fetch the primary dataset, check for `gaze.tsv`; if missing, raise a `FileNotFoundError` with a clear message and flag spec for the fallback dataset. **Do NOT implement automatic fallback**.

- [X] T011 [P] Create `pipeline_config.yaml` with default signal processing parameters (–45 Hz bandpass, Hz downsampling, ICA settings, `line_noise_freq` as 50 or 60).

- [X] T036 [P] [Polish] Implement `code/utils/verify_data_integrity.py` to run pre-flight checks on `data/raw` ensuring all required files (EEG, gaze.tsv) exist and match checksums in `manifest.yaml` (T009) before any heavy processing begins. **Must run after T009**.

- [X] T000 [P] [US1] Implement `code/data/verify_dataset.py` to fetch `ds` (or `ds003465`) and verify the presence of `gaze.tsv`. **HALT** with `FileNotFoundError` and a clear message if gaze data is missing, flagging the spec for update. **Output**: `results/verification_report.json` containing `status`, `message`, and `n_channels` (derived from dataset metadata). **Must run first in data flow**.

- [X] T001 [US1] Implement `code/data/power_analysis.py` to calculate minimum N required for R²=0.2 with `n_channels * 2` predictors **derived from `results/verification_report.json` (T000 output)**. **Use alpha=0.05, power=0.8**. **HALT with `sys.exit(1)` and print error to stderr** if actual_n < calculated_min_n, flagging study as underpowered and preventing any further pipeline execution. **Output**: `results/power_analysis_report.json` (only if N is sufficient). **Must run after T036**.

- [X] T002 [US1] Implement `code/data/memory_check.py` to verify chunked loading logic with a **representative sample of the actual dataset (a subset of subjects from ds000246)**, ensuring peak memory usage stays within acceptable operational limits (≤ 6.5 GB). **Output**: `results/memory_check_report.json`. **Must run after T008 and T036**.

- [X] T042 [P] [US1] Implement `code/utils/runtime_profiler.py` to profile pipeline execution time and enforce the 6-hour runtime limit (SC-002). **Must log estimated runtime and HALT execution if actual execution time exceeds 6 hours**. **Output**: `results/runtime_profile.json` (mandatory for final report).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and prepare the OpenNeuro EEG dataset, ensuring artifact-free data aligned with behavioral logs within memory constraints.

**Independent Test**: Can be fully tested by executing the data loading and ICA artifact removal script on the target runner and verifying that the output contains clean epochs with matching behavioral timestamps, while monitoring memory usage to ensure it stays within acceptable system limits.

### Test-First Sub-Phase for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for chunked loading logic in `tests/unit/test_loader.py` (verify memory peak < 7GB)
- [X] T013 [P] [US1] Unit test for dataset verification gate in `tests/unit/test_download.py` (verify halt on missing gaze data)
- [X] T014 [P] [US1] Integration test for full preprocessing pipeline in `tests/integration/test_preprocess.py` (verify ICA removal and epoch retention > 70%)

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/preprocess_filter.py` to apply a Butterworth bandpass filter (high-pass at a low frequency, A low-pass filter with a frequency in the high-range audible spectrum.) and a notch filter at `line_noise_freq`. **Read filter parameters from `pipeline_config.yaml`**. **Validate that `line_noise_freq` is defined in `pipeline_config.yaml`; raise ValueError if missing**. **Check for `metadata_grid_frequency` in dataset metadata; if present, override `line_noise_freq` with this value to match local grid frequency**. **Must run after T010**. (Plan Phase 1, Step 2).
- [X] T016 [US1] Implement `code/data/preprocess_ica.py` to apply ICA for eye-blink artifact removal and retain only clean components. **Must run after T015**. (Plan Phase 1, Step 3).
- [X] T017 [US1] Implement `code/data/preprocess_epoch.py` to segment data into epochs aligned with behavioral events, exclude subjects with > 50% rejected epochs, calculate epoch retention rate, and **HALT execution if < 70%**. **Must run after T016**. (Plan Phase 1, Step 5).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Feature Extraction and Label Generation (Priority: P2)

**Goal**: Compute spectral power features (theta/alpha) and generate continuous cognitive load labels from gaze variance.

**Independent Test**: Can be fully tested by running the feature extraction module on a subset of clean epochs and verifying that the resulting feature matrix contains valid theta/alpha power ratios and that the label distribution is non-trivial.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T018 [P] [US2] Unit test for Welch's PSD calculation in `tests/unit/test_extract.py` (verify band limits)
- [X] T019 [P] [US2] Unit test for gaze variance calculation in `tests/unit/test_labels.py` (verify min-max scaling)
- [X] T020 [P] [US2] Unit test for missing value flagging in `tests/unit/test_validity.py` (verify > 5% threshold)

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/features/extract.py` to compute PSD using Welch's method (FR-003) with built-in **chunked loading logic** to ensure memory safety during PSD computation on the full dataset (SC-002). The module must extract mean power for theta and alpha bands per channel, handle division-by-zero using **`EPSILON = 1e-9` defined as a global constant in `code/features/extract.py`** (Edge Case) when calculating ratios, and flag epochs with > 5% missing sensor data for exclusion. **Must run after T017**.

- [X] T022 [US2] Implement `code/features/labels.py` to derive continuous cognitive load score from gaze variance per epoch (FR-004), normalize labels via min-max scaling per subject (FR-004), and identify and exclude epochs with > 5% missing sensor data (FR-003). **Must run after T017 and T021**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Model Training and Statistical Validation (Priority: P3)

**Goal**: Train a Ridge Regression model, validate performance against baseline, and apply statistical corrections.

**Independent Test**: Can be fully tested by running the training and evaluation script on the held-out test set and verifying that the reported R² and RMSE values are calculated correctly and that the model outperforms the baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T023 [P] [US3] Unit test for Ridge Regression CV in `tests/unit/test_train.py` (verify subject-wise split)
- [X] T024 [P] [US3] Unit test for permutation testing in `tests/unit/test_evaluate.py` (verify null distribution)
- [X] T025 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_evaluate.py` (verify Bonferroni)

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/models/split.py` to perform a subject-wise split of subjects into train/test sets ensuring no subject overlap, dynamically calculate the split size, and save a **split manifest file**. **Must run after T022**.

- [X] T028 [US3] Implement `code/models/train.py` to train Ridge Regression model with subject-wise k-fold CV, tune alpha, and evaluate on held-out test set (FR-005, FR-006). **Must load the subject-wise split manifest generated by T026 and use it for the training split**. **Must run after T026**.

- [X] T027 [US3] Implement `code/models/evaluate.py` to perform **Channel Importance Analysis**: (1) Compute Pearson correlation per channel/band using the feature matrix and labels from T021/T022, (2) Apply Bonferroni correction to the **combined set of all channel-band tests (channels × bands)** AND **raw p-values from T029 (sensitivity) and T038 (permutation test)** to control family-wise error rate (FR-007), (3) Generate a unified `results/channel_importance.json` report with schema: `[{ "channel": str, "band": str, "correlation": float, "p_value": float, "p_value_corrected": float }]`. **Must load the subject-wise split manifest generated by T026**. **Must run after T026, T029, T038**.

- [X] T029 [US3] Implement `code/models/sensitivity.py` to perform sensitivity analysis (FR-008): **Validate that `window_sizes` key exists in `pipeline_config.yaml` as a list of integers**; **Iterate through the list of gaze variance window sizes**, **re-calculate labels by importing and reusing the label generation function from `code/features/labels.py` (T022)** for each iteration, **re-train and re-evaluate the model** for each window size by calling the training logic from `code/models/train.py` (T028), and store comparative R² results and **raw p-values for each window size** in `results/sensitivity_report.csv` and `results/sensitivity_p_values.json`. **Must run after T022, T028**.

- [X] T038 [US3] Implement `code/models/permutation_test.py` to perform a rigorous permutation test (shuffling labels) to derive a p-value for the global R², ensuring the model outperforms a random baseline. **Must run after T028**. **Must output `results/permutation_test.json` with null distribution stats and **raw p-value****.

- [X] T041 [US3] Implement `code/models/baseline.py` to implement the mean-baseline predictor comparison logic (FR-006). **Must run after T028**. **Must load the training set labels from the split manifest generated by T026** to calculate the mean on the correct data split. **Output**: `results/baseline_comparison.json` with R² and RMSE for mean-baseline vs Ridge model.

- [X] T030 [US3] Implement `code/main.py` to orchestrate the full pipeline: Data -> Features -> Model -> Report. **Must specify CLI arguments (`--data-dir`, `--output-dir`), expected output paths, and verify `main.py` runs end-to-end producing `results/model_metrics.json` (exit code 0 and existence of required output files)**. **Must merge outputs from T028, T038, T041, and T042 into a single `results/model_metrics.json` file**. **Must run after T029, T038, T041**.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] [Polish] Update `README.md` with installation steps and `quickstart.md` with the exact command `python code/main.py --data-dir data/processed --output-dir results`.
- [X] T032 [P] [Polish] Refactor `code/data/loader.py` to reduce cyclomatic complexity < 10 **if cyclomatic complexity > 10** and improve readability.
- [X] T033 [P] [Polish] Optimize `code/data/preprocess_ica.py` to reduce peak memory usage by at least 10% **if peak memory > 6.0 GB** while maintaining accuracy.
- [X] T034 [P] [Polish] Run quickstart.md validation to ensure end-to-end reproducibility.
- [X] T035 [P] [Polish] Implement `code/features/stimulus_control.py` to regress out stimulus complexity metrics (if available in metadata) or explicitly flag this as a limitation in the final report (Plan Phase 3).

- [X] T040 [P] [US2] Implement `code/features/validity.py` to explicitly check SC-005 (Measurement validity) by verifying that extracted theta/alpha power values are non-zero and stable across subjects, **calculating the coefficient of variation**, and to flag any subjects with anomalous power distributions for exclusion. **Must run after T021**. **Must write the quantitative stability metrics (CV) and status to `results/stability_report.json`**.

- [X] T043 [P] [Polish] Implement `code/utils/update_state.py` to act as the single source of truth for state updates. **Must be invoked by the orchestrator (T030) or post-task hooks** to update `state/` YAML with checksums and `updated_at` timestamp upon any artifact change, as required by Constitution Principle V. **Delegates all state updates from other tasks**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Init)**: No dependencies - can start immediately
- **Phase 1 (Foundational)**: No dependencies - can start immediately. Includes all data verification tasks (T000, T001, T002, T036, T042) to ensure data availability before processing.
- **User Stories (Phase 2+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on features from US2 and data from US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (if applicable)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for chunked loading logic in tests/unit/test_loader.py"
Task: "Unit test for dataset verification gate in tests/unit/test_download.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/preprocess_filter.py to apply 1–45 Hz bandpass filter"
Task: "Implement code/data/preprocess_ica.py to apply ICA"
Task: "Implement code/data/preprocess_epoch.py to segment data and check retention"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Project Initialization
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories, includes Data Verification)
3. Complete Phase 2: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ICA removal and memory limits)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Initialization + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Initialization + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Features/Labels)
 - Developer C: User Story 3 (Modeling/Stats)
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
- **Critical**: Ensure `code/data/download.py` halts if `gaze.tsv` is missing (Spec Contradiction Check) or falls back to `ds003465`
- **Critical**: Ensure all data loading uses chunking to stay within available memory constraints (triggered at > 6.5 GB).
- **Critical**: Ensure no GPU usage or deep learning models are introduced
- **Constitution Principle V**: State updates are now handled exclusively by T043. All other tasks delegate state updates to T043.
- **Revision Note**: T015, T016, T017 split from original T015 for granularity. T026, T027 merged for Channel Importance. T029 updated for explicit sensitivity loop. T000/T001 fixed for data flow. T036 moved to Phase 1 to break circular dependency. T002 moved to Phase 1 to ensure data availability. T000/T001 moved to Phase 1. T027/T028 order corrected. T032/T033 made specific. T042 added for runtime profiling. T041 added for mean-baseline. T043 added for state updates.
- **Revision Concern T037**: Removed to avoid streaming API drift; T008 updated to enforce chunked loading.
- **Revision Concern T038**: Added to address the requirement for a permutation baseline test (FR-006) which was previously only implied.
- **Revision Concern T039**: Removed as scope creep; replaced with T040 for validity checks and T043 for state updates.
- **Revision Concern T040**: Added to explicitly implement SC-005 validity checks as a separate, testable module.
- **Dependency Fix**: T000 -> T010 -> T009 -> T036 -> T001. T009 no longer depends on T036. T027 no longer depends on T028. T029 explicitly calls T028 and T022. T030 merges all final metrics.