# Tasks: Predicting Cognitive Load from EEG Spectral Power Changes During Naturalistic Viewing

**Input**: Design documents from `/specs/001-predicting-cognitive-load-eeg/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-295-predicting-cognitive-load-eeg/` with explicit directories: `data/raw`, `data/processed`, `code`, `tests`, `specs/001-predicting-cognitive-load-from-eeg-spect/contracts`.
- [ ] T002 Initialize Python 3.11 project with dependencies defined in `projects/PROJ-295-predicting-cognitive-load-eeg/requirements.txt` (pinned versions: e.g., `mne==1.6.0`, `pandas==2.0.0`, `numpy==1.24.0`, `scikit-learn==1.3.0`, `pyyaml==6.0`, `requests==2.31.0`, `tqdm==4.65.0`, `opencv-python==4.8.0`, `jsonschema==4.19.0`, `pytest==7.4.0`).
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `projects/PROJ-295-predicting-cognitive-load-eeg/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] Create JSON schema files (`eeg-epoch.schema.yaml`, `cognitive-load-label.schema.yaml`, `spectral-feature-vector.schema.yaml`) in `projects/PROJ-295-predicting-cognitive-load-eeg/specs/001-predicting-cognitive-load-from-eeg-spect/contracts/` with full definitions including properties: `subject_id` (string), `epoch_start` (float), `theta_power` (float), `alpha_power` (float), `cognitive_load_score` (float). The schema files MUST include standard JSON Schema keys (`type`, `required`, `properties`) and reference the `data-model.md` section for full validation rules.
- [ ] T005 [P] Implement `validate_contracts.py` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` using `jsonschema` to validate artifacts against schemas created in T006.
- [ ] T004 Create `pipeline_config.yaml` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` with preprocessing parameters: `low_cutoff: 1.0`, `high_cutoff: 45.0`, `samplerate: 250`. Implement logic to handle line noise removal for both 50 Hz and 60 Hz (e.g., `notch_freqs: [50, 60]`) to satisfy FR-001.
- [ ] T007 Create `data/manifest.json` structure and checksumming logic in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` to track dataset versions and artifact hashes.
- [ ] T008 [P] Configure environment configuration management (random seeds, CPU-only flags) in `projects/PROJ-295-predicting-cognitive-load-eeg/code/`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, clean, and prepare the OpenNeuro ds000246 dataset for analysis, ensuring artifact-free EEG aligned with behavioral logs within RAM constraints.

**Independent Test**: Execute the data loading and ICA artifact removal script on the target runner, verify output contains clean epochs with matching behavioral timestamps, and monitor memory usage to ensure it remains within acceptable system limits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test `test_download_checksum_match` for data download integrity and checksum verification in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_preprocess.py`.
- [ ] T010 [P] [US1] Unit test `test_ica_rejection_logic` for ICA artifact rejection logic and memory profiling in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_preprocess.py`.
- [ ] T011 [P] [US1] Integration test `test_end_to_end_ingestion` for end-to-end data ingestion pipeline (download -> filter -> ICA -> align) in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_preprocess.py`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `download_data.py` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` to fetch OpenNeuro ds using `bids` or direct HTTP with chunked loading and checksum validation.
- [ ] T013 [US1] Implement `preprocess_eeg.py` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` to apply 1-45 Hz bandpass, downsample to a standard sampling rate, remove line noise (50/60 Hz), and run ICA for eye-blink removal. Include a strict memory guard: if available RAM < 7 GB, raise a `RuntimeError` immediately (do not subsample or skip epochs) to enforce FR-001 and SC-002 validity constraints. Include memory-efficient chunked loading logic within this script to handle large datasets without exceeding RAM.
- [ ] T015 [US1] Implement alignment logic in `projects/PROJ-295-predicting-cognitive-load-eeg/code/preprocess_eeg.py` to match EEG epochs with behavioral logs (gaze data) ensuring <100ms mismatch.
- [ ] T016 [US1] Add error handling in `projects/PROJ-295-predicting-cognitive-load-eeg/code/preprocess_eeg.py` to halt with clear error if behavioral logs are missing or subjects have >50% rejected epochs.
- [ ] T017 [US1] Integrate `validate_contracts.py` into `preprocess_eeg.py` to validate output epochs against `eeg-epoch.schema.yaml` before saving to `data/processed/`.
- [ ] T042 [US1] Implement logic to calculate the percentage of epochs retained after ICA (using the validated epochs from T017), log the rate to stdout, and record it in `data/manifest.json`. Do NOT fail the pipeline if the threshold is not met; only report for transparency as per SC-004.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Label Generation (Priority: P2)

**Goal**: Compute spectral power features (theta/alpha) and generate continuous cognitive load labels from gaze variance.

**Independent Test**: Run the feature extraction module on a subset of clean epochs and verify the resulting feature matrix contains valid theta/alpha power ratios and that the label distribution is non-trivial.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `test_welch_psd_theta_band` for Welch's PSD calculation and band extraction in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_features.py`.
- [ ] T019 [P] [US2] Unit test `test_cognitive_load_label_gen` for cognitive load label generation (gaze variance) and min-max normalization in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_features.py`.
- [ ] T020 [P] [US2] Integration test `test_feature_extraction_pipeline` for feature extraction pipeline (epochs -> features + labels) in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_features.py`.

### Implementation for User Story 2

- [ ] T021 [US2] Implement `extract_features.py` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` to compute PSD using Welch's method and extract log-transformed relative power for theta and alpha bands.
- [ ] T022 [US2] Implement epsilon addition (e-6) in `projects/PROJ-295-predicting-cognitive-load-eeg/code/extract_features.py` to prevent division by zero during theta/alpha ratio calculation.
- [ ] T023 [US2] Implement label generation logic in `projects/PROJ-295-predicting-cognitive-load-eeg/code/extract_features.py` to derive cognitive load scores from gaze variance and normalize via min-max scaling per subject.
- [ ] T024 [US2] Implement missing value detection in `projects/PROJ-295-predicting-cognitive-load-eeg/code/extract_features.py` to flag epochs with >5% missing sensor data for exclusion.
- [ ] T026 [US2] Integrate `validate_contracts.py` into `extract_features.py` to validate feature matrices against `spectral-feature-vector.schema.yaml` and labels against `cognitive-load-label.schema.yaml`.
- [ ] T043 [US2] Implement sensitivity analysis logic in `projects/PROJ-295-predicting-cognitive-load-eeg/code/extract_features.py` to vary gaze variance window sizes (short, medium, and long durations), re-run label generation for each, compare results, and output a CSV report of scores vs. window sizes to assess robustness of the results (FR-008).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Training and Statistical Validation (Priority: P3)

**Goal**: Train a Ridge Regression model, validate performance against a permutation baseline, and apply multiple-comparison correction.

**Independent Test**: Run the training and evaluation script on the held-out test set and verify that reported R² and RMSE values are calculated correctly and that the model outperforms the baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test `test_losos_split_no_overlap` for subject-wise split logic (majority train, held-out test) and cross-validation setup in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_model.py`.
- [ ] T029 [P] [US3] Unit test `test_permutation_baseline` for permutation baseline generation and statistical significance testing in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_model.py`.
- [ ] T030 [P] [US3] Integration test `test_model_training_pipeline` for end-to-end model training and evaluation pipeline in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/test_model.py`.

### Implementation for User Story 3

- [ ] T031 [US3] Implement `train_model.py` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` to perform a subject-wise majority split (e.g., % train, 20% test) and tune Ridge alpha via k-fold cross-validation within the training set, strictly adhering to FR-005.
- [ ] T032 [US3] Implement `evaluate_results.py` in `projects/PROJ-295-predicting-cognitive-load-eeg/code/` to compute Pearson correlation, RMSE, and compare against a permutation baseline (shuffled labels).
- [ ] T033 [US3] Implement multiple-comparison correction (Bonferroni or FDR) in `projects/PROJ-295-predicting-cognitive-load-eeg/code/evaluate_results.py` for per-channel/per-band hypothesis tests.
- [ ] T034 [US3] Implement logic in `projects/PROJ-295-predicting-cognitive-load-eeg/code/evaluate_results.py` to report effect size (R²) and write the metric to `results/metrics.json`. Do NOT write a boolean 'valid' field or enforce a pass/fail gate based on R² ≥ 0.2; this is a study measurement target, not a runtime constraint.
- [ ] T035 [US3] Add visualization and reporting logic in `projects/PROJ-295-predicting-cognitive-load-eeg/code/evaluate_results.py` to output final metrics and statistical validity confirmation.
- [ ] T036 [US3] Integrate `validate_contracts.py` into `evaluate_results.py` to ensure all output artifacts conform to defined schemas.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `projects/PROJ-295-predicting-cognitive-load-eeg/` (README, quickstart.md).
- [ ] T038 Code cleanup and refactoring across `projects/PROJ-295-predicting-cognitive-load-eeg/code/`.
- [ ] T039 Performance optimization for data loading if runtime exceeds limits.
- [ ] T040 [P] Additional unit tests in `projects/PROJ-295-predicting-cognitive-load-eeg/tests/`.
- [ ] T041 Run `quickstart.md` validation to ensure reproducibility on clean runner.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on clean epochs from US1** (T013/T017 must complete before T021/T026)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on features/labels from US2** (T021/T023 must complete before T031)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) **ONLY IF** their data dependencies are met (US2 depends on US1 output, US3 depends on US2 output)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only if** the data flow dependencies (US1 -> US2 -> US3) are respected

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test test_download_checksum_match in tests/test_preprocess.py"
Task: "Unit test test_ica_rejection_logic in tests/test_preprocess.py"

# Launch all implementation tasks for User Story 1 together (after foundation):
Task: "Implement download_data.py"
Task: "Implement preprocess_eeg.py (includes memory guard logic)"
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
   - Developer A: User Story 1
   - Developer B: User Story 2 (waits for US1 output)
   - Developer C: User Story 3 (waits for US2 output)
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
- **Split Strategy**: T031 implements subject-wise majority split (80/20) as per FR-005.
- **Memory Guard**: T013 enforces strict 250 Hz and fails on low RAM; no subsampling fallback.
- **Sensitivity Analysis**: T043 moved to Phase 4 (US-2) to align with FR-008.