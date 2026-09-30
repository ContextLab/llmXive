# Tasks: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Input**: Design documents from `/specs/001-investigating-neural-synchrony-attention-switching/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

- [X] T001a [P] Create directory structure: `projects/PROJ-498-investigating-the-relationship-between-n/`, `projects/PROJ-498-investigating-the-relationship-between-n/code/`, `projects/PROJ-498-investigating-the-relationship-between-n/data/`, `projects/PROJ-498-investigating-the-relationship-between-n/tests/`
- [X] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `data/metrics/`, `data/trial_level/`, `code/`, `tests/unit/`, `tests/integration/`, `contracts/`, `logs/`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes dataset discovery and configuration.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Initialize Python 3 project with dependencies in `requirements.txt` (strict version pinning required, e.g., 'mne==1.7.0', 'numpy==1.24.3', 'scipy==1.11.0', 'pandas==2.0.0', 'statsmodels==0.14.0', 'scikit-learn==1.3.0', 'pyyaml==6.0.1', 'openneuro-py==2.2.0', 'bids-validator==1.12.0')
- [X] T003 [P] Configure linting and formatting tools (black, flake8, isort) in `projects/PROJ-498-investigating-the-relationship-between-n/`
- [X] T004 Implement `code/update_state_hashes.py` to generate/verify content hashes for artifacts
- [X] T005 [P] Implement `code/config.py` with paths, seeds, and hyperparameters. Config MUST define keys `primary_window` and `sensitivity_windows` as a list of tuples in milliseconds (e.g., `primary_window: (-500, 0)`, `sensitivity_windows: [(-600, 0), (-400, 0)]`). The task description must mandate that the code reads these keys from the configuration source to support FR-007 sensitivity analysis, but the initial values in `config.py` must be set to the standard values defined in the spec.
- [X] T007 Implement logging infrastructure to `logs/processing.log` and exclusion tracking to `data/exclusions.csv`
- [X] T008 Create `contracts/data_gap_report.schema.yaml` for the "Data Gap Report" artifact (defines keys: `dataset_id`, `reason`, `timestamp`, `fallback_id` where `fallback_id` is OPTIONAL/NULLABLE and MUST be set to `null` if no dataset is found)
- [X] T009 Create `contracts/sensitivity_report.schema.yaml` and `contracts/trial_level_analysis.schema.yaml`
- [ ] T012 Implement `code/download.py` to: 1) **Query the OpenNeuro API** for datasets containing 'task-switching' events (matching the spec's dynamic search requirement) with specific criteria: `event_type` contains 'task-switching', minimum 10 subjects, and must have both 'switch' and 'stay' event labels; 2) If a valid dataset is found, select the first one and save its ID to `data/selected_dataset_id.txt`; 3) If **NO** dataset is found via the API search, **ATTEMPT TO DOWNLOAD** the specified fallback dataset ID `ds004173` as mandated by FR-001 and the Spec's Assumptions; 4) If the fallback also fails or is invalid, **TRIGGER T012b** to generate the `data/data_gap_report.json` artifact and **HALT** execution. **Constraint**: Do NOT implement a hardcoded primary ID (e.g., ds004173) as a fallback unless the dynamic search fails. The API search is the single source of truth; the fallback is only for the case where the search yields no results.
- [ ] T012b [P] Implement logic to generate `data/data_gap_report.json` adhering to `contracts/data_gap_report.schema.yaml` (with `fallback_id: null` if no fallback was attempted or failed) and log the error to `logs/processing.log` with the specific reason "No verified task-switching dataset found via API search or fallback". **Dependency**: Triggered only by T012 if both API search and fallback fail.
- [X] T040b [P] Implement global runtime wrapper in `code/main.py` that tracks total pipeline execution time; immediately log a timeout violation to `logs/processing.log` and `data/metrics/runtime_log.json` and HALT execution if total runtime > 6 hours; generate `data/metrics/runtime_log.json` containing `start_time`, `end_time`, `total_duration_minutes`, `status` (success/timeout), and `passed_6h_limit` (boolean) to verify SC-002.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Preprocess and Epoch Public Task-Switching EEG Data (Priority: P1) 🎯 MVP

**Goal**: Download a verified task-switching dataset from OpenNeuro, preprocess it with strict memory constraints, and epoch it for analysis.

**Independent Test**: Run on a single subject; verify output contains valid epoch objects with correct time window and no NaN artifacts; verify peak RSS ≤ 6.5 GB.

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/download.py` to fetch raw data to `data/raw/` using the ID from `data/selected_dataset_id.txt` with checksumming (SHA-256). **Dependency**: Requires T012 to complete first. **Error Handling**: If `data/selected_dataset_id.txt` does not exist (indicating T012 failed with a Data Gap Report), this task MUST exit gracefully with a specific error code and log "Download skipped: No dataset ID found (Data Gap Report generated)". **File Format**: The file `data/selected_dataset_id.txt` must contain a single plain-text string with no trailing whitespace. **Artifact**: Generate `data/raw/checksums.json` mapping filenames to SHA-256 hashes.
- [X] T014 [US1] Implement `code/preprocess.py` to apply a **1–45 Hz bandpass filter** (low cutoff 1 Hz, high cutoff frequency) as mandated by FR-002 and US-1. **Memory Constraint**: Wrap processing in a memory monitor using `psutil` to poll RSS at frequent intervals. Use a `try/finally` block to log memory usage to `data/metrics/memory_profile.json` (with key `peak_rss_gb` per subject) if the limit is approached. **Verification**: Verify `data/metrics/memory_profile.json` exists and `peak_rss_gb` <= 6.5. If a single subject exceeds a predefined memory threshold, log the subject to `data/exclusions.csv` with reason "memory_limit_exceeded" and exclude them from further processing, but DO NOT halt the entire pipeline for other subjects. The exclusion MUST be logged to ensure reproducibility.
- [X] T015c [US1] Implement `code/preprocess.py` notch filter (line frequency) if line noise detected; log intervention to `logs/processing.log` with specific format: "Notch filter applied at {freq}Hz for subject {id}". **Ordering**: This task MUST be executed BEFORE T015a (ICA fitting) to prevent line noise from contaminating ICA decomposition. **Dependency**: Requires T014 (bandpass) to be complete.
- [X] T015a [US1] Implement `code/preprocess.py` ICA fitting on the bandpass-filtered and notch-filtered data. **Algorithm**: Use `mne.preprocessing.ICA` with `method='infomax'` and `n_components='auto'`. **Dependency**: Requires T015c (notch filter) to be complete to ensure clean data for decomposition.
- [ ] T015b [US1] Implement `code/preprocess.py` component rejection logic: identify and remove ICA components exhibiting a kurtosis > 5 or a spectral peak > 30 Hz. **Artifact**: Generate `data/processed/ica_components.csv` listing rejected component IDs, their kurtosis values, and spectral peak frequencies. **Schema**: Columns must be `component_id` (int), `kurtosis` (float), `spectral_peak_freq` (float), `rejected` (bool). **Verification**: Verify file exists and contains >0 rejected components if artifacts were present. **Dependency**: Requires T015a (ICA fitting) to be complete.
- [X] T016 [US1] Implement `code/preprocess.py` epoching from a pre-stimulus baseline period to a post-stimulus period around stimulus onset. **Memory Constraint**: Continue monitoring RSS using `psutil`. Use a `try/finally` block to log memory usage to `data/metrics/memory_profile.json`. **Verification**: Verify `data/metrics/memory_profile.json` exists and `peak_rss_gb` <= 6.5. If a single subject exceeds 6.5 GB, log the subject to `data/exclusions.csv` with reason "memory_limit_exceeded" and exclude them from further processing, but DO NOT halt the entire pipeline for other subjects. **Dependency**: Requires T015b (rejection) to be complete.
- [ ] T017 [US1] Implement logic to exclude subjects with <10 valid trials/condition (reason: "insufficient trials") or >50% artifact removal (reason: "excessive artifact removal"); log to `data/exclusions.csv` with columns: `subject_id`, `reason`. **Critical**: This task MUST maintain an in-memory count of `valid_subject_count` (subjects not excluded) and pass this count to T017b. **Dependency**: Requires T016 to be complete.
- [ ] T017b [P] Implement logic to check if `valid_subject_count` (from T017) is zero. If zero, generate `data/processing_gap_report.json` (schema: `total_subjects`, `excluded_count`, `reason: "all_subjects_excluded_due_to_memory_limits"`) and HALT execution. **Dependency**: Requires T017 to complete and provide the `valid_subject_count`.
- [X] T019 [US1] Save clean epochs to `data/processed/` per subject (e.g., `sub-XX_epoched.fif`); verify file exists and contains valid epoch objects (requires T004 for hashing).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Pre-Stimulus Frontoparietal Synchrony Metrics (Priority: P2)

**Goal**: Calculate Phase-Locking Value (PLV) or weighted Phase-Lag Index (wPLI) between frontoparietal electrode pairs in the pre-stimulus window.
**⚠️ DEPENDENCY**: Requires T019 (clean epochs) to be complete.

**Independent Test**: Compute PLV on a synthetic signal with known phase relationships; verify output matches theoretical expectation within 0.05 tolerance.

### Implementation for User Story 2

- [X] T022 [US2] Implement electrode mapping in `code/synchrony.py`: F3/F4, FC3/FC4 → DLPFC; P3/P4, CP3/CP4 → Parietal
- [ ] T023 [US2] Implement frequency band filtering for **theta (4–7 Hz)** and **gamma (30–45 Hz)** and compute wPLI **in-memory** without writing intermediate files. **Implementation Directive**: You MUST implement a streaming or in-memory processing loop that iterates over epochs, applies the bandpass filter, computes wPLI, and discards the filtered data immediately. **DO NOT** write filtered epochs to `data/processed/band_filtered/`. **Verification**: Verify power spectral density peaks exist within the defined theta (4–7 Hz) and gamma (30–45 Hz) bands for the current subject's data using `scipy.signal.find_peaks` with `prominence=3`, frequency resolution of **1 Hz bins**, and a threshold of **>3dB relative to mean power**. **Dependency**: Requires T019 (clean epochs) to be complete. **Data Hygiene**: Do NOT persist intermediate band-filtered files to avoid storage bloat and OOM errors.
- [ ] T024 [US2] Implement `code/synchrony.py` to compute **weighted Phase-Lag Index (wPLI)** for the **pre-stimulus window (-500ms to 0ms)** between the defined frontoparietal electrode pairs for **both theta and gamma bands**. The algorithm must use the standard wPLI formula to mitigate volume conduction. **Dependency**: Requires T023 to be complete.
- [ ] T025 [US2] Save synchrony matrices to `data/metrics/synchrony_metrics.csv` with columns: `subject_id`, `pair_id`, `band`, `value`. **Schema**: `pair_id` format must be 'F3_P3' (underscore separated). `value` must be rounded to 6 decimal places. **Required Pairs**: F3-P3, F3-P4, F4-P3, F4-P4. **Verification**: Verify file exists, contains 4 columns, and the `band` column contains strictly "theta" or "gamma" values (not a single aggregated mean). **Output MUST contain separate rows for each band (theta and gamma) per subject** to allow multiple-comparison correction (FR-005). This satisfies FR-003 and SC-003. **Traceability**: The long-format structure is explicitly required to support FR-005 (multiple-comparison correction). **Dependency**: Requires T024 to be complete.
- [ ] T026 [US2] Implement timing wrapper in `code/synchrony.py` that logs duration to `data/metrics/synchrony_timing.json` and RAISES EXCEPTION if duration > 30 minutes per subject to verify US-2 Acceptance 3. **Timing**: Use `time.perf_counter()` to measure the **entire** synchrony calculation (filtering + wPLI) per subject. **Dependency**: Requires T023 and T024 to be complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Synchrony with Behavioral Switching Costs (Priority: P3)

**Goal**: Compute attention switching costs and correlate with synchrony using permutation testing and mixed-effects models.
**⚠️ DEPENDENCY**: Requires T019 (epochs) and T025 (synchrony metrics) to be complete.

**Independent Test**: Run on a mock null dataset (randomly shuffled data); verify Type I error rate ≤ 5% across 1000 iterations.

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/analysis.py` to compute switching costs (RT_switch - RT_stay) per subject
- [X] T031 [US3] Implement `code/analysis.py` primary correlation: Pearson/Spearman between mean synchrony and switching costs
- [X] T032 [US3] Implement `code/analysis.py` permutation testing with a sufficient number of iterations (shuffling subject vectors) as mandated by FR-005; log iteration count.
- [X] T033 [US3] Implement multiple-comparison correction (Bonferroni) for theta and gamma bands in the **primary subject-level analysis**; update `data/metrics/correlation_results.json` with corrected p-values; **Verification**: Verify correction logic is applied to the subject-level analysis.
- [X] T036 [US3] Generate `data/trial_level/per_trial_synchrony.csv` with columns: `subject_id`, `trial_id`, `condition`, `synchrony`, `rt`; exclude rows with missing synchrony; requires T004.
- [X] T035 [US3] Implement `code/analysis.py` secondary trial-level analysis: Linear Mixed-effects model (`RT ~ Synchrony + (1|Subject)`) using `statsmodels`. **Correction Requirement**: Apply standard significance testing (p < 0.05) to the trial-level model; **DO NOT** apply Bonferroni correction here as FR-005 only mandates it for the frequency-band comparison in the subject-level analysis. Handle missing trial-level synchrony by excluding rows.
- [ ] T034a [US3] Implement `code/analysis.py` sensitivity analysis logic: repeat correlation for windows **[-600, 0]** and **[-400, 0]**; validate stability (r change < 0.1, p < 0.05) against primary result. **Dependency**: Requires output of T019 and T025 (data artifacts) and T005 (config). **Critical**: This task MUST write `primary_window_r` and `primary_window_p` keys to `data/metrics/correlation_results.json` before T034b executes.
- [ ] T034b [US3] Generate `data/metrics/sensitivity_report.json` (requires T004) and VERIFY that `r change < 0.1` and `p < 0.05` thresholds are met against SC-004 by comparing against `data/metrics/correlation_results.json` (specifically keys `primary_window_r` and `primary_window_p`). **Rounding**: Compare values rounded to a consistent level of precision.. **Schema**: Report must contain keys `primary_window_r`, `primary_window_p`, `sensitivity_windows` (list of objects with `window`, `r`, `p`, `limitation_flag`). **Logic**: If criteria are violated (r change >= 0.1 or p >= 0.05), **TRIGGER T034c** to generate a failure artifact and **EXIT THE PIPELINE WITH A NON-ZERO CODE**. **DO NOT** proceed to generate the final report if stability criteria are violated. **Dependency**: Requires T034a to be complete.
- [ ] T034c [P] Implement logic to generate `data/failure_state.json` with keys `status: "failed"`, `reason: "sensitivity_analysis_stability_violation"`, `details: { ... }` when T034b detects a stability violation. **Dependency**: Triggered only by T034b on stability failure.
- [X] T037 [US3] Save final results to `data/metrics/correlation_results.json` and `data/metrics/trial_level_analysis.json` with keys: `correlation`, `p_value`, `framing_note` (must contain "associational"); generate `results_summary.md` containing the associational framing text; requires T004
- [X] T038 [US3] Implement programmatic assertion in `code/analysis.py` to verify output JSON and `results_summary.md` contain "associational" framing as mandated by FR-008. **Artifact**: Generate `data/validation_log.txt` and exit with code 0 if passed, 1 if failed.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Implement `code/main.py` pipeline orchestrator to run phases sequentially (Note: Runtime wrapper T040b is in Phase 1)
- [ ] T041 [P] Add documentation updates in `projects/PROJ-498-investigating-the-relationship-between-n/README.md`: Update README.md with a "Usage" section containing the command: `python code/main.py`. The description must explain that the command uses the dataset ID found in `data/selected_dataset_id.txt` (which is the result of the OpenNeuro API search for 'task-switching' datasets). If `data/selected_dataset_id.txt` does not exist (due to T012 failure and Data Gap Report generation), the README should note that the pipeline requires a successful dataset search to proceed.
- [X] T042 [P] Run `code/update_state_hashes.py` to update state file with new artifact hashes
- [X] T043 [P] Verify `quickstart.md` validation: Run the commands in quickstart.md in a fresh virtualenv; verify all commands exit with code 0 and produce expected artifacts.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. Includes T012 (Dataset Search) and T005 (Config).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: MUST start after User Story 1 completion (requires clean epochs from T019)
- **User Story 3 (P3)**: MUST start after User Story 1 and User Story 2 completion (requires epochs and synchrony metrics)

### Within Each User Story

- Implementation MUST be complete before integration tests run
- Models/Config before Services
- Services before Endpoints/Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start
- Once User Story 1 completes, User Story 2 can start
- Once User Story 2 completes, User Story 3 can start
- Different user stories cannot be worked on in parallel due to strict data-flow dependencies

---

## Parallel Example: User Story 1

```bash
# Launch all setup tasks for User Story 1 together:
Task: "Implement code/config.py with paths and seeds"
Task: "Setup directory structure"

# Launch implementation tasks sequentially:
Task: "Implement download.py" -> "Implement preprocess.py" -> "Implement epoching"
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

### Sequential Team Strategy

Due to data-flow dependencies:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
3. Once US1 completes:
 - Developer B: User Story 2
4. Once US2 completes:
 - Developer C: User Story 3

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All tasks must run on CPU-only (limited cores, constrained RAM); no GPU/CUDA/8-bit quantization allowed.
- **Critical**: No fabricated data; all inputs must come from real OpenNeuro datasets (API search first).
- **Critical**: All output files must adhere to the specified schemas and include required framing (associational).