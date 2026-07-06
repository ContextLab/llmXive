# Tasks: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Input**: Design documents from `/specs/001-neural-synchrony-switching-costs/`
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

- [ ] T001a [P] Create `code/` directory at repository root
- [ ] T001b [P] Create `data/raw/`, `data/interim/`, `data/processed/` directories
- [ ] T001c [P] Create `tests/` directory structure
- [ ] T001d [P] Create `state/` directory for artifact hashes
- [ ] T001e [P] Create `requirements.txt` with pinned dependencies (mne, numpy, pandas, statsmodels, scipy, pyyaml, requests)
- [ ] T002 [P] Configure linting and formatting tools (ruff/black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup directory structure (if not done in Phase 1)
- [ ] T005 [P] Implement `code/download_data.py` to fetch OpenNeuro dataset **ds004173** specifically using `mne.datasets.fetch_openneuro_dataset`, verify event labels ('switch'/'stay'), and halt execution with clear error if missing.
- [ ] T006 Implement checksum verification (SHA256) in `code/download_data.py` and write to `state/artifact_hashes.yaml` (Depends on T005 completion: data download required for checksum)
- [ ] T007 Create `code/utils.py` with helper functions for batched processing (A moderate number of trials per batch) to manage GB RAM limit
- [ ] T009 Configure logging infrastructure to `logs/` for pipeline execution

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Preprocess EEG Data and Extract Behavioral Metrics (Priority: P1) 🎯 MVP

**Goal**: Ingest raw EEG data, apply standard preprocessing (1-45Hz filter, ICA), extract trial-by-trial RT/accuracy, and save cleaned epochs.

**Independent Test**: The system can be tested by running the preprocessing script on a single subject's data and verifying that the output contains a CSV with columns for `subject_id`, `trial_id`, `condition`, `reaction_time`, `accuracy`, alongside cleaned EEG epochs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010a [P] [US1] Unit test for filtering logic in `tests/unit/test_filtering.py`: Implement `test_bandpass_filter_cuts_off_at_1hz` asserting 1Hz cutoff
- [ ] T011a [P] [US1] Contract test for output CSV schema in `tests/contract/test_behavioral_csv.py`: Implement test using `contracts/behavioral_csv.schema.yaml`

### Implementation for User Story 1

- [ ] T012a [US1] Implement `code/preprocess_eeg.py`: Apply a bandpass filter to remove DC offset and very low-frequency drift., consistent with standard preprocessing pipelines [DOI:10.1016/j.neuroimage.2008.04.123]. (Depends on T004, T005)
- [ ] T013a [US1] Implement `code/preprocess_eeg.py`: Perform ICA-based artifact removal (Depends on T012a)
- [ ] T014a [US1] Implement `code/preprocess_eeg.py`: Epoch data from a pre-stimulus baseline period to a post-stimulus interval relative to stimulus onset. (Depends on T013a)
- [ ] T015a [US1] Implement `code/preprocess_eeg.py`: Extract behavioral metrics (RT, accuracy) and condition labels (Depends on T014a)
- [ ] T016a [US1] Implement `code/preprocess_eeg.py`: Implement exclusion logic: Flag subjects with >20% artifact trials or <20 switch trials (Depends on T015a)
- [ ] T017a [US1] Implement `code/preprocess_eeg.py`: Save preprocessed epochs and behavioral CSV to `data/interim/` (e.g., `sub-01_behavioral.csv`, `sub-01_epochs.fif`) and verify output columns (Depends on T016a)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Pre-Stimulus Instantaneous Phase Difference (Priority: P2)

**Goal**: Calculate Instantaneous Phase Difference (IPD) or wPLI for frontoparietal pairs in theta/gamma bands during a pre-stimulus time window.

**Independent Test**: The system can be tested by computing the metric on a subset of trials and verifying that the output matrix contains valid phase difference values (bounded between -π and π) for the specified frequency bands and electrode pairs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019a [P] [US2] Unit test for Morlet wavelet parameters (≥7 cycles) in `tests/unit/test_wavelets.py`: Implement `test_morlet_cycles_ge_7` asserting cycle count
- [ ] T020a [P] [US2] Contract test for synchrony feature matrix schema in `tests/contract/test_synchrony_features.py`: Implement test using `contracts/synchrony_features.schema.yaml`

### Implementation for User Story 2

**⚠️ DEPENDENCY GATE**: This phase depends on T017a (US1) completion. Do not start until US1 data is available.

- [ ] T021a [US2] Implement `code/compute_synchrony.py`: Load preprocessed epochs from `data/interim/` (Depends on T017a)
- [ ] T022a [US2] Implement `code/compute_synchrony.py`: Define frontoparietal pairs (F3/F4/FC3/FC4 vs P3/P4/CP3/CP4) (Depends on T021a)
- [ ] T023a [US2] Implement `code/compute_synchrony.py`: Apply Morlet wavelets (≥7 cycles) for –7 Hz (theta) and –45 Hz (gamma) bands on ms to 0ms window (Depends on T022a)
- [ ] T023b [US2] Implement `code/compute_synchrony.py`: Verify Morlet wavelet parameters (≥7 cycles) achieve side-lobe attenuation > 20 dB (Depends on T023a)
- [ ] T024a [US2] Implement `code/compute_synchrony.py`: Calculate Instantaneous Phase Difference (IPD) per trial (Depends on T023b)
- [ ] T025a [US2] Implement `code/compute_synchrony.py`: Calculate sin(IPD) and cos(IPD) transformations for LMM compatibility (Depends on T024a)
- [ ] T026a [US2] Implement `code/compute_synchrony.py`: Calculate weighted Phase-Lag Index (wPLI) over a sliding window of multiple trials. as required alternative (Depends on T023a)
- [ ] T027a [US2] Implement `code/compute_synchrony.py`: Save synchrony features to `data/interim/` (e.g., `sub-01_synchrony_features.csv`) (Depends on T025a, T026a)
- [ ] T028a [US2] Verify output: Check phase values are within [-π, π] and time window strictly excludes post-stimulus activity (Depends on T027a)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Correlation Testing (Priority: P3)

**Goal**: Fit LMM to test if pre-stimulus synchrony predicts switching costs, apply multiple-comparison corrections, and run permutation tests.

**Independent Test**: The system can be tested by running the analysis on the generated feature/behavioral datasets and verifying that the output includes a fixed effect estimate, p-value, and confidence interval derived from the LMM.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029a [P] [US3] Unit test for LMM formula construction in `tests/unit/test_lmm_model.py`: Implement `test_lmm_formula_includes_interaction` asserting formula string
- [ ] T030a [P] [US3] Contract test for statistical results schema in `tests/contract/test_lmm_results.py`: Implement test using `contracts/lmm_results.schema.yaml`

### Implementation for User Story 3

**⚠️ DEPENDENCY GATE**: This phase depends on T017a (US1) and T027a (US2) completion. Do not start until both data sources are available.

- [ ] T031a [US3] Implement `code/analyze_lmm.py`: Merge behavioral data and synchrony features (Depends on T017a, T027a)
- [ ] T032a [US3] Implement `code/analyze_lmm.py`: Log-transform reaction times as primary default; use robust estimator only if log-transform fails (Depends on T031a)
- [ ] T033a [US3] Implement `code/analyze_lmm.py`: Fit LMM with fixed effects (synchrony, condition, interaction) AND random intercept for subject (1 | subject_id) (Depends on T032a)
- [ ] T034a [US3] Implement `code/analyze_lmm.py`: Perform Likelihood Ratio Test (Full vs. Reduced model) for interaction significance (Depends on T033a)
- [ ] T035a [US3] Implement `code/analyze_lmm.py`: Apply Bonferroni or FDR correction to p-values across bands and electrode pairs, including the permutation p-values (Depends on T034a)
- [ ] T036a [US3] Implement `code/analyze_lmm.py`: Run permutation test (sufficient iterations) permuting the interaction term fixed effect coefficient to generate empirical p-value (Depends on T035a)
- [ ] T037a [US3] Implement `code/analyze_lmm.py`: Implement directionality check for IPD interaction vector (dot product with expected direction) (Depends on T036a)
- [ ] T038a [US3] Implement `code/analyze_lmm.py`: Save final results to `data/processed/lmm_results.csv` (Depends on T037a)
- [ ] T039a [US3] Generate report: Print fixed effect estimates, corrected p-values, and permutation p-values (Depends on T038a)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T040a [P] Update README.md Installation section
- [ ] T040b [P] Update README.md Usage section
- [ ] T040c [P] Update README.md Data Sources section
- [ ] T041a [P] Remove unused imports from all scripts
- [ ] T041b [P] Enforce ruff rules across all code
- [ ] T041c [P] Refactor code for readability
- [ ] T042 Performance optimization: Verify sequential processing fits within 6 hours and 7GB RAM
- [ ] T043a [P] Unit test for batched processing logic in `tests/unit/test_batching.py`
- [ ] T043b [P] Unit test for error handling in `tests/unit/test_error_handling.py`
- [ ] T043c [P] Unit test for LMM permutation logic in `tests/unit/test_permutation.py`
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [ ] T045 Generate `sensitivity_analysis.md` for ANY parameter modification from spec (Mandatory per Constitution Principle VI)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T017a)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data output (T017a, T027a)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005) can run in parallel with other Phase 2 tasks (T004, T007, T009), but T006 depends on T005 and cannot run in parallel with it.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for filtering logic in tests/unit/test_filtering.py"
Task: "Contract test for output CSV schema in tests/contract/test_behavioral_csv.py"

# Launch all models for User Story 1 together:
Task: "Implement code/preprocess_eeg.py: Apply 1-45 Hz bandpass filter"
Task: "Implement code/preprocess_eeg.py: Perform ICA-based artifact removal"
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
   - Developer B: User Story 2
   - Developer C: User Story 3
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