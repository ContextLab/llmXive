# Tasks: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Input**: Design documents from `/specs/001-predicting-cognitive-load-eeg/`
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
 Implemented independently
 - Tested independently
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Project Initialization

**Purpose**: Project initialization and basic structure

- [X] T003 [P] Create project structure per implementation plan: `mkdir -p code/data code/features code/models tests/unit tests/integration data/raw data/processed results`.

- [X] T005 [P] Initialize Python project with pinned dependencies (`mne`, `scikit-learn`, `pandas`, `numpy`, `pyarrow`, `requests`) in `requirements.txt`

- [X] T006 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Verification & Power Analysis (formerly Phase 0) to ensure data availability.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `code/config.py` to load `pipeline_config.yaml` and environment variables.

- [X] T010 [P] Implement `code/data/download.py` with a strict verification gate: fetch the primary dataset (ds00XXXX), check for `gaze.tsv`; if missing, automatically attempt to fetch the fallback dataset (ds00XXXX) before raising a `FileNotFoundError` with a clear message and flag spec for the fallback dataset. **Do NOT implement silent synthetic fallback**.

- [X] T009 [US1] Implement `code/data/generate_manifest.py` to produce `data/manifest.yaml` containing fields: `url`, `version`, `checksum_sha256` (computed via SHA-256 of the downloaded tarball). **Must run after T010**.

- [X] T000 [US1] Implement `code/data/verify_dataset.py` to verify the presence of `gaze.tsv` and EEG data in the downloaded dataset (output of T010). **Do NOT fetch data; verify local files**. **HALT** with `FileNotFoundError` and a clear message if gaze data is missing (after T010's fallback attempt fails), flagging the spec for update. **Output**: `results/verification_report.json` containing `status`, `message`, and `n_channels` (derived from dataset metadata). **Must run after T010**.

- [X] T036 [P] [Polish] Implement `code/utils/verify_data_integrity.py` to run pre-flight checks on `data/raw` ensuring all required files (EEG, gaze.tsv) exist and match checksums in `manifest.yaml` (T009) AND that `results/verification_report.json` (T000) exists and indicates success, before any heavy processing begins. **Must run after T000 and T009**.

- [X] T001 [P] [US1] Implement `code/data/power_analysis.py` to calculate minimum N required for R²=0.2 with `n_channels * 2` predictors **derived from `results/verification_report.json` (T000 output)**. **Use alpha=0.05, power=0.8**. **Must explicitly check for the existence of `results/verification_report.json` before reading n_channels. If the file is missing, exit with a specific error code (e.g., sys.exit(2)) and print "Power analysis failed: verification report missing"**. **HALT with `sys.exit(1)` and print error to stderr** if actual_n < calculated_min_n, flagging study as underpowered and preventing any further pipeline execution. **Output**: `results/power_analysis_report.json` (only if N is sufficient). **Must run after T000**.

- [X] T008 [P] [US1] Implement `code/data/loader.py` with chunked loading logic (by `epoch_id`) to ensure memory safety (≤ 6.5 GB). **Logic must be triggered when estimated memory usage > 5.5 GB**. **Do NOT use streaming API**.

- [X] T002 [P] [US1] Implement `code/data/memory_check.py` to verify chunked loading logic with a **representative sample of the actual dataset (a subset of subjects from ds000246)**, ensuring peak memory usage stays within acceptable operational limits (≤ 6.5 GB). **Note**: The dependency on T036 is for **runtime execution only** (the memory check script must run after T036's verification script has confirmed data integrity), NOT for task implementation order. The task T002 can be implemented independently. **Output**: `results/memory_check_report.json`. **Must run after T008**.

- [X] T042 [P] [US1] Implement `code/utils/runtime_profiler.py` to profile pipeline execution time and enforce the -hour runtime limit (SC-002). **Must provide a `check_and_halt()` function that checks elapsed time and calls `sys.exit(1)` if limit exceeded**. **Must log estimated runtime and HALT execution if actual execution time exceeds a reasonable threshold.**. **Output**: `results/runtime_profile.json` (mandatory for final report).

- [X] T011 [P] Create `pipeline_config.yaml` with default signal processing parameters: **Low-frequency to Hz bandpass**, **Hz downsampling**, **/60 Hz line noise**, and **explicit ICA settings (method='picard', n_components=0.95)**.

- [X] T011b [P] [Polish] Implement `code/data/generate_config_defaults.py` to **generate and validate the `window_sizes` list in `pipeline_config.yaml`**. **Must ensure `window_sizes` key exists with a list of at least 3 integers (e.g., [5, 10, 20])**. **Must run after T011 and before T029**. **Output**: Updated `pipeline_config.yaml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and prepare the OpenNeuro EEG dataset, ensuring artifact-free data aligned with behavioral logs within memory constraints.

**Independent Test**: Can be fully tested by executing the data loading and ICA artifact removal script on the target runner and verifying that the output contains clean epochs with matching behavioral timestamps, while monitoring memory usage to ensure it stays within acceptable system limits.

### Test-First Sub-Phase for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T012 [P] [US1] Unit test for chunked loading logic in `tests/unit/test_loader.py` (verify memory peak < 6.5GB).
- [X] T013 [P] [US1] Unit test for dataset verification gate in `tests/unit/test_download.py` (verify halt on missing gaze data).
- [X] T014 [P] [US1] Integration test for full preprocessing pipeline in `tests/integration/test_preprocess.py` (verify ICA removal and epoch retention > 70%).

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/preprocess_filter.py` to apply a Butterworth bandpass filter (low-frequency cutoff to 45 Hz) and a notch filter (50/60 Hz) as defined in `pipeline_config.yaml`. **Read filter parameters (1–45 Hz, 250 Hz) from `pipeline_config.yaml`**. **Validate that `line_noise_freq` is defined in `pipeline_config.yaml`; raise ValueError if missing**. **Check for `metadata_grid_frequency` in dataset metadata; if present, override `line_noise_freq` with this value to match local grid frequency**. **Must run after T010**. (Plan Phase 1, Step 2).
- [X] T016 [US1] Implement `code/data/preprocess_ica.py` to apply ICA for eye-blink artifact removal and retain only clean components. **Must run after T015**. (Plan Phase 1, Step 3).
- [X] T017 [US1] Implement `code/data/preprocess_epoch.py` to segment data into epochs aligned with behavioral events, exclude subjects with > 50% rejected epochs, calculate epoch retention rate, and **HALT execution if < 70%**. **Must run after T016**. (Plan Phase 1, Step 5).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Feature Extraction and Label Generation (Priority: P2)

**Goal**: Compute spectral power features (theta/alpha) and generate continuous cognitive load labels from gaze variance.

**Independent Test**: Can be fully tested by running the feature extraction module on a subset of clean epochs and verifying that the resulting feature matrix contains valid theta/alpha power ratios and that the label distribution is non-trivial.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T018 [P] [US2] Unit test for Welch's PSD calculation in `tests/unit/test_extract.py` (verify band limits).
- [X] T019 [P] [US2] Unit test for gaze variance calculation in `tests/unit/test_labels.py` (verify min-max scaling).
- [X] T020 [P] [US2] Unit test for missing value flagging in `tests/unit/test_validity.py` (verify > 5% threshold).

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/features/extract.py` to compute PSD using Welch's method (FR-003) with built-in **chunked loading logic** to ensure memory safety during PSD computation on the full dataset (SC-002). The module must extract mean power for theta and alpha bands per channel, handle division-by-zero using **`EPSILON = 1e-9` defined as a global constant in `code/features/extract.py`** (Edge Case) when calculating ratios, and flag epochs with > 5% missing sensor data for exclusion. **Must run after T017**. **Must pass raw power values to T040 for stability validation**.

- [X] T022 [US2] Implement `code/features/labels.py` to derive continuous cognitive load score from gaze variance per epoch (FR-004), normalize labels via min-max scaling per subject (FR-004), and identify and exclude epochs with > 5% missing sensor data (FR-003). **Must run after T017 and T021**.

- [X] T040 [P] [US2] Implement `code/features/validity.py` to explicitly check SC-005 (Measurement validity) by verifying that extracted theta/alpha power values are non-zero and stable across subjects, **calculating the coefficient of variation**, and to **log specific failed epoch IDs and subject IDs to `results/stability_report.json`** for exclusion. **Must run after T021**. **Must read raw power data from T021 output**. **Must write the quantitative stability metrics (CV), failed_epoch_ids, and failed_subject_ids to `results/stability_report.json`**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Model Training and Statistical Validation (Priority: P3)

**Goal**: Train a Ridge Regression model, validate performance against baseline, and apply statistical corrections.

**Independent Test**: Can be fully tested by running the training and evaluation script on the held-out test set and verifying that the reported R² and RMSE values are calculated correctly and that the model outperforms the baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (Pre-implementation TDD) to ensure they FAIL before implementation**

- [X] T023 [P] [US3] Unit test for Ridge Regression CV in `tests/unit/test_train.py` (verify subject-wise split).
- [X] T024 [P] [US3] Unit test for permutation testing in `tests/unit/test_evaluate.py` (verify null distribution).
- [X] T025 [P] [US3] Unit test for multiple-comparison correction in `tests/unit/test_evaluate.py` (verify Bonferroni).

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/models/split.py` to perform a subject-wise split of subjects into train/test sets ensuring no subject overlap, dynamically calculate the split size, and save a **split manifest file**. **Must run after T022**.

- [X] T027 [US3] Implement `code/models/evaluate.py` to perform **Channel Importance Analysis**: (1) Compute Pearson correlation per channel/band using the feature matrix and labels from T021/T022, (2) Apply Bonferroni correction to the **combined set of all channel-band tests (channels × bands)**, the **global model significance test (from T038)**, and the **baseline comparison (from T041)** to control family-wise error rate (FR-007), (3) Generate a unified `results/channel_importance.json` report with schema: `[{ "channel": str, "band": str, "correlation": float, "p_value": float, "p_value_corrected": float }]`. **Must load the subject-wise split manifest generated by T026**. **Must run after T026, T021, T022**. **Do NOT depend on T028 (model training) for correlation calculation**.

- [X] T028 [US3] Implement `code/models/train.py` to train Ridge Regression model with subject-wise k-fold CV, tune alpha, and evaluate on held-out test set (FR-005, FR-006). **Must load the subject-wise split manifest generated by T026 and use it for the training split**. **Must expose a callable function `train_model(X_train, y_train, subject_ids)` that returns the trained model and metrics, to allow external invocation by T029**. **Must run after T026**.

- [X] T029 [US3] Implement `code/models/sensitivity.py` to perform sensitivity analysis (FR-008): **Validate that `window_sizes` key exists in `pipeline_config.yaml` (generated by T011b)**; **Iterate through the list of gaze variance window sizes**; **re-calculate labels by importing and reusing the label generation function from `code/features/labels.py` (T022) for each iteration**; **re-train and re-evaluate the model for each window size by calling the `train_model` function exposed by `code/models/train.py` (T028)**; and store comparative stability metrics in `results/sensitivity_report.csv` and `results/sensitivity_p_values.json`. **Must run after T022, T021, T011b, T028**. **Note**: This task imports the `train_model` function from the module created by T028 for re-training steps, ensuring code dependency is satisfied and aligning with Plan.md Phase 3 requirements.

- [X] T038 [US3] Implement `code/models/permutation_test.py` to perform a rigorous permutation test (shuffling labels) to derive a p-value for the global R², ensuring the model outperforms a random baseline. **Must run after T028**. **Must output `results/permutation_test.json` with null distribution stats and **raw p-value****.

- [X] T041 [US3] Implement `code/models/baseline.py` to implement the mean-baseline predictor comparison logic (FR-006). **Must run after T028**. **Must load the training set labels from the split manifest generated by T026** to calculate the mean on the correct data split. **Output**: `results/baseline_comparison.json` with R² and RMSE for mean-baseline vs Ridge model.

- [ ] T030 [US3] Implement `code/main.py` to orchestrate the full pipeline: Data -> Features -> Model -> Report. **Must specify CLI arguments (`--data-dir`, `--output-dir`), expected output paths, and verify `main.py` runs end-to-end producing `results/model_metrics.json` (exit code 0 and existence of required output files)**. **Must call the `check_and_halt()` function from T042 at start and after major phases**. **Must explicitly read and merge outputs from T028 (R², RMSE), T038 (p-value), T041 (baseline metrics), and T042 (runtime)** into a single `results/model_metrics.json` file. **Must compare the final R² against the `r2_threshold` defined in `pipeline_config.yaml`**. **If R² < threshold, MUST call `sys.exit(1)` with a clear error message "Threshold Gate Failed: R² < threshold"**. **Must run after T028, T029, T038, T041, T042**.

**Checkpoint**: At this point, User Story 3 should be fully functional and testable independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] [Polish] Update `README.md` with installation steps and `quickstart.md` with the exact command `python code/main.py --data-dir data/processed --output-dir results`.
- [X] T032 [P] [Polish] Refactor `code/data/loader.py` to reduce cyclomatic complexity < 10 **measured using ruff** and improve readability.
- [X] T033 [P] [Polish] Optimize `code/data/preprocess_ica.py` to reduce peak memory usage by at least 10% **measured using memory_profiler** while maintaining accuracy.
- [X] T034 [P] [Polish] Run quickstart.md validation to ensure end-to-end reproducibility.
- [X] T035 [P] [Polish] Implement `code/features/stimulus_control.py` to regress out stimulus complexity metrics (if available in metadata) or explicitly flag this as a limitation in the final report (Plan Phase 3).

- [X] T043 [P] [Polish] Implement `code/utils/update_state.py` to act as the single source of truth for state updates. **Must be invoked by the orchestrator (T030) or post-task hooks** to update `state/` YAML with checksums and `updated_at` timestamp upon any artifact change, as required by Constitution Principle V. **Delegates all state updates from other tasks**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Init)**: No dependencies - can start immediately
- **Phase 1 (Foundational)**: No dependencies - can start immediately. Includes all data verification tasks (T010, T009, T000, T036, T001, T002, T042, T011b) to ensure data availability before processing.
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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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
- **Critical**: Ensure all data loading uses chunking to stay within available memory constraints (triggered at > 5.5 GB).
- **Critical**: Ensure no GPU usage or deep learning models are introduced
- **Constitution Principle V**: State updates are now handled exclusively by T043. All other tasks delegate state updates to T043.
- **Revision Note**: T015, T016, T017 split from original T015 for granularity. T026, T027 merged for Channel Importance. T029 updated for explicit sensitivity loop. T000/T001 fixed for data flow. T036 moved to Phase 1 to break circular dependency. T002 moved to Phase 1 to ensure data availability. T000/T001 moved to Phase 1. T027/T028 order corrected. T032/T033 made specific. T042 added for runtime profiling. T041 added for mean-baseline. T043 added for state updates. T011b added for config validation.
- **Revision Concern T037**: Removed to avoid streaming API drift; T008 updated to enforce chunked loading.
- **Revision Concern T038**: Added to address the requirement for a permutation baseline test (FR-006) which was previously only implied.
- **Revision Concern T039**: Removed as scope creep; replaced with T040 for validity checks and T043 for state updates.
- **Revision Concern T040**: Added to explicitly implement SC-005 validity checks as a separate, testable module.
- **Dependency Fix**: T010 -> T009 -> T000 -> T036 -> T001. T009 no longer depends on T036. T027 no longer depends on T028. T029 explicitly calls T022 and T021. T030 merges all final metrics. T030 now depends on T042, T028, T038, T041, T029. T001 checks for T000 output file existence.
- **Correction**: T000 no longer fetches data; it verifies T010's output. T036 now depends on T000 to ensure verification report exists before integrity checks. T012 threshold corrected to 6.5GB. T029 logic changed to statistical check to avoid runtime explosion. T030 now enforces hard halt on threshold failure.
- **Ordering Clarification**: T028 now explicitly exposes `train_model()` for T029. T030 explicitly depends on T028. T002 runtime dependency on T036 clarified.
- **Correction T029**: Updated to mandate re-training for each window size to align with Plan.md Phase 3.
- **Correction T002**: Removed implementation dependency on T036; clarified runtime constraint.
- **Correction T030**: Added explicit T028 dependency to prevent scheduler issues.

# Analyze report (current R1 output — drives the panel concerns)

- (severity: CRITICAL) (tasks.md:Phase 4) — FR-006 requires validation against a "permutation baseline" and SC-001 requires measuring against a "pre-defined threshold," but T028 (train.py) and T030 (main.py) lack explicit logic to run the permutation test (T038) *before* final evaluation or to enforce the R² threshold check that would trigger a "failed" status in `results/model_metrics.json`; the current flow calculates metrics but does not implement the "compare against baseline" or "threshold gate" logic required to satisfy the spec's acceptance criteria.
- (severity: HIGH) (tasks.md:Phase 3 vs spec.md:FR-008) — FR-008 mandates a sensitivity analysis on the "gaze variance calculation window," but T029 (sensitivity.py) is described as iterating through `window_sizes` in `pipeline_config.yaml` without a corresponding task to *generate* or *validate* that this configuration key exists with the necessary range of values, creating a risk that the sensitivity analysis will fail or run with default/empty parameters if the config isn't manually pre-populated.
- (severity: MEDIUM) (tasks.md:Phase 2 vs spec.md:SC-005) — SC-005 requires verifying that theta/alpha power ratios are "non-zero, stable," and while T040 (validity.py) is added to check this, T021 (extract.py) is described as handling division-by-zero with an epsilon but does not explicitly include a task to *log* or *flag* the specific epochs/subjects that fail the stability check defined in SC-005, potentially leaving the "measurement validity" evidence unrecorded in a structured report.
- (severity: MEDIUM) (tasks.md:Phase 1 vs plan.md:Phase 0) — The plan's "Phase 0" explicitly includes a "Power Analysis" step to calculate minimum N, and T001 implements this, but the task description relies on `n_channels` being "derived from `results/verification_report.json` (T000 output)"; however, T000 is described as outputting `n_channels` only if the dataset verification *succeeds*, creating a logical gap where the power analysis (T001) might run before the dataset is fully verified or fail to receive the necessary input if T000 halts execution due to missing data.
- (severity: LOW) (tasks.md:Phase 4 vs spec.md:FR-006) — FR-006 requires comparing the model against a "mean-baseline predictor," and T041 implements this, but the task description for T030 (orchestrator) states it must "merge outputs from T028, T038, T041, and T042," yet T041 is not listed in the dependency chain for T030 in the "Dependencies & Execution Order" section (T030 depends on T029, T038, T041, T042), which is a minor documentation inconsistency in the dependency graph that could lead to the baseline comparison being omitted from the final report if the execution order is strictly followed by a scheduler that ignores the text description.

# Prior reviews (per-round history; outstanding concerns)

(no prior reviews)

# Panel concerns to address (R1 output)

- [concern ordering-89a9acf6] severity=requirement reviewer=ordering location=tasks.md:Phase 4
 T029 (Sensitivity Analysis) explicitly states it must 're-train and re-evaluate the model for each window size by calling the training logic from code/models/train.py (T028)'. T028 is a task to 'Implement' the training script. T029 is a task to 'Implement' the sensitivity script. The dependency 'Must run after T028' is correct for the *implementation* order (you can't call a function that doesn't exist). However, the *execution* flow described in T029 implies that T029 will *invoke* the logic of T028. This is a semantic dependency on the *code* produced by T028, not just the task completion. The current ordering is acceptable for implementation, but the description in T029 blurs the line between 'task dependency' and 'code dependency'. A more precise issue: T029 depends on T022 (labels) and T028 (train). T028 depends on T026 (split). T026 depends on T022. The chain T022 -> T026 -> T028 -> T029 is correct. However, T029 also depends on T022 for label generation. The description says 'Must run after T022, T028'. This is correct. The concern is the 're-train' logic: T029 calls T028's logic. If T028 is a script that runs once, T029 must import the function. The task description is slightly ambiguous about whether T028 is a script to be run or a module to be imported. Given the context of 'Implement code/models/train.py', it's a module. The dependency is fine. Wait, looking closer at T029: 're-train and re-evaluate the model for each window size by calling the training logic from code/models/train.py (T028)'. This implies T028 is a module. The dependency 'Must run after T028' is correct. No violation here. Re-evaluating T001: The 'HALT' in T000 is a runtime behavior. The task dependency 'Must run after T000' is a build-time dependency. If T000 fails, the build fails, and T001 is never scheduled. This is correct. The concern is weak. Let's look for a stronger one.
- [concern ordering-7e3fa1b0] severity=requirement reviewer=ordering location=tasks.md:Phase 4
 T030 (main.py) is the orchestrator. It 'Must merge outputs from T028, T038, T041, and T042'. T030 depends on T029, T038, T041, T042. T029 (Sensitivity) depends on T028 (Train). T038 (Permutation) depends on T028. T041 (Baseline) depends on T028. T042 (Runtime) is independent but T030 depends on it. The dependency graph for T030 is: T029, T038, T041, T042. T029 depends on T028. T038 depends on T028. T041 depends on T028. So T030 indirectly depends on T028 via T029, T038, T041. This is correct. However, T030's description says 'Must merge outputs from T028...'. T028 is a task. The output of T028 is the trained model and metrics. T030 needs to read these. The dependency 'Must run after T028' is implied by the dependencies on T029, T038, T041. But T030 is listed as depending on T029, T038, T041, T042. It does NOT explicitly list T028. If T029, T038, T041 are implemented but T028 is not (e.g., T028 is skipped or fails silently in a scheduler that doesn't check transitive deps), T030 might run without the T028 output. The explicit dependency 'Must run after T028' should be added to T030 to ensure the base model output is available, even if T029/T038/T041 are not run (though they are required for the full report). The current list is 'T029, T038, T041, T042'. T028 is missing from the explicit 'Must run after' list for T030, even though it is a transitive dependency. This is a potential ordering gap if the scheduler only checks direct dependencies.
- [concern ordering-47af9d5e] severity=requirement reviewer=ordering location=tasks.md:Phase 1
 T002 (Memory Check) 'Must run after T008 and T036'. T008 is 'Implement code/data/loader.py'. T036 is 'Implement code/utils/verify_data_integrity.py'. T002 is 'Implement code/data/memory_check.py'. The dependency 'Must run after T008' is correct (needs the loader). The dependency 'Must run after T036' is questionable. T036 is a 'pre-flight check' that runs *before* heavy processing. T002 is a 'memory check' that runs *after* the loader is implemented. T036 depends on T000 and T009. T002 depends on T008 and T036. Why does T002 depend on T036? T036 verifies data integrity. T002 verifies memory usage of the loader. T002 uses a 'representative sample of the actual dataset'. T036 ensures the dataset is present and valid. If T036 fails (data missing), T002 cannot run. So the dependency is valid for the *execution* of T002. But T002 is an *implementation* task. The 'Must run after' likely refers to the *runtime* dependency of the script being implemented. T002's script needs to run after T036's script has verified the data. This is a runtime dependency, not a task implementation dependency. The task list is a mix of implementation and execution order. This is a semantic ambiguity. However, the 'Must run after' in T002 is likely intended to mean 'The script T002 must be executed after T036'. This is correct. The concern is that the task list conflates implementation order with execution order. But the lens is 'ordering' of tasks. If the tasks are 'Implement', then the order of implementation doesn't matter as much as the order of execution. The 'Must run after' in the task description is a constraint on the *execution* of the implemented script. The task list itself is a plan for implementation. The 'Must run after' in T002 is a constraint on the *script* T002, not the *task* T002. This is a semantic issue. The task T002 can be implemented at any time. The script T002 must be run after T036. The task description is confusing. But is it a 'ordering violation'? The task T002 is listed after T036. This is fine. The 'Must run after' is a runtime constraint. The task order is fine. Let's look for a clearer violation.

# Recent reviewer / personality comments

(no recent comments)