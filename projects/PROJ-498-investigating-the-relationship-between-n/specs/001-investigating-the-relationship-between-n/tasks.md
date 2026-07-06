# Tasks: Investigating the Relationship Between Neural Synchrony and Attention Switching Costs

**Input**: Design documents from `/specs/001-investigating-neural-synchrony-attention-switching/`
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

- [ ] T001a [P] Create directory structure: `projects/PROJ-498-investigating-the-relationship-between-n/`, `projects/PROJ-498-investigating-the-relationship-between-n/code/`, `projects/PROJ-498-investigating-the-relationship-between-n/data/`, `projects/PROJ-498-investigating-the-relationship-between-n/tests/`
- [ ] T001b [P] Create subdirectories: `data/raw/`, `data/processed/`, `data/metrics/`, `data/trial_level/`, `code/`, `tests/unit/`, `tests/integration/`, `contracts/`, `logs/`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Initialize Python 3 project with dependencies in `requirements.txt` (strict version pinning required, e.g., 'mne==1.7.0', 'numpy==1.24.3', 'scipy==1.11.0', 'pandas==2.0.0', 'statsmodels==0.14.0', 'scikit-learn==1.3.0', 'pyyaml==6.0.1', 'openneuro-py==2.2.0', 'bids-validator==1.12.0')
- [ ] T003 [P] Configure linting and formatting tools (black, flake8, isort) in `projects/PROJ-498-investigating-the-relationship-between-n/`
- [ ] T004 Implement `code/update_state_hashes.py` to generate/verify content hashes for artifacts
- [ ] T005 Implement `code/config.py` with paths, seeds, and hyperparameters (bandpass low-frequency range to 45Hz, epoch to +2000ms, pre-stim to 0ms)
- [ ] T006 [P] Setup directory structure: `data/raw/`, `data/processed/`, `data/metrics/`, `data/trial_level/`, `code/`, `tests/`
- [ ] T007 Implement logging infrastructure to `logs/processing.log` and exclusion tracking to `data/exclusions.csv`
- [ ] T008 Create `contracts/data_gap_report.schema.yaml` for the "Data Gap Report" artifact (defines keys: `dataset_id`, `reason`, `timestamp`, `fallback_id` where `fallback_id` is OPTIONAL/NULLABLE and MUST be set to `null` if no dataset is found)
- [ ] T009 Create `contracts/sensitivity_report.schema.yaml` and `contracts/trial_level_analysis.schema.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Preprocess and Epoch Public Task-Switching EEG Data (Priority: P1) 🎯 MVP

**Goal**: Download a verified task-switching dataset from OpenNeuro via dynamic search, preprocess it with strict memory constraints, and epoch it for analysis.

**Independent Test**: Run on a single subject; verify output contains valid epoch objects with correct time window and no NaN artifacts; verify peak RSS ≤ 6.5 GB.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/download.py` to: 1) Query OpenNeuro API for datasets containing 'task-switching' events FIRST; 2) If found, select the first valid dataset (preferring the designated dataset if present in results); 3) If no dataset found, generate `data/data_gap_report.json` adhering to `contracts/data_gap_report.schema.yaml` (with `fallback_id: null`) and halt.
- [ ] T013 [US1] Implement `code/download.py` to fetch raw data to `data/raw/` with checksumming (SHA-256)
- [ ] T014 [US1] Implement `code/preprocess.py` bandpass filter (1–45 Hz)
- [ ] T015 [US1] Implement `code/preprocess.py` ICA-based artifact removal (reject components with kurtosis > 5 or spectral peak > 30 Hz)
- [ ] T015b [US1] Implement `code/preprocess.py` notch filter (50/60Hz) if line noise detected; log intervention to `logs/processing.log` with specific format: "Notch filter applied at {freq}Hz for subject {id}"
- [ ] T016 [US1] Implement `code/preprocess.py` epoching (-1000ms to +2000ms) around stimulus onset
- [ ] T017 [US1] Implement logic to exclude subjects with <10 valid trials/condition (reason: "insufficient trials") or >50% artifact removal (reason: "excessive artifact removal"); log to `data/exclusions.csv` with columns: `subject_id`, `reason`
- [ ] T018 [US1] Implement memory monitoring to ensure peak RSS ≤ 6.5 GB during sequential subject processing
- [ ] T018b [US1] Implement global runtime wrapper in `code/main.py` that tracks total pipeline execution time; immediately log a timeout violation to `logs/processing.log` and `data/metrics/runtime_log.json` if total runtime exceeds several hours, then halt.
- [ ] T018c [US1] Implement logic to generate `data/metrics/runtime_log.json` containing `start_time`, `end_time`, `total_duration_minutes`, and `status` (success/timeout) to verify SC-002.
- [ ] T019 [US1] Save clean epochs to `data/processed/` per subject (requires T004 for hashing)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Pre-Stimulus Frontoparietal Synchrony Metrics (Priority: P2)

**Goal**: Calculate Phase-Locking Value (PLV) or weighted Phase-Lag Index (wPLI) between frontoparietal electrode pairs in the pre-stimulus window.
**⚠️ DEPENDENCY**: Requires T019 (clean epochs) to be complete.

**Independent Test**: Compute PLV on a synthetic signal with known phase relationships; verify output matches theoretical expectation within 0.05 tolerance.

### Implementation for User Story 2

- [ ] T022 [US2] Implement electrode mapping in `code/synchrony.py`: F3/F4, FC3/FC4 → DLPFC; P3/P4, CP3/CP4 → Parietal
- [ ] T023 [US2] Implement frequency band filtering for theta (–7 Hz) and gamma (–45 Hz)
- [ ] T024 [US2] Implement `code/synchrony.py` to compute wPLI/PLV for pre-stimulus window (a sufficiently long baseline period prior to stimulus onset)
- [ ] T025 [US2] Save synchrony matrices to `data/metrics/synchrony_metrics.csv` with columns: `subject_id`, `pair_id`, `band`, `value` (aggregated as mean); requires T004 for hashing
- [ ] T026 [US2] Ensure computation completes in ≤ 30 minutes per subject on CPU

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate Synchrony with Behavioral Switching Costs (Priority: P3)

**Goal**: Compute attention switching costs and correlate with synchrony using permutation testing and mixed-effects models.
**⚠️ DEPENDENCY**: Requires T019 (epochs) and T025 (synchrony metrics) to be complete.

**Independent Test**: Run on a mock null dataset (randomly shuffled data); verify Type I error rate ≤ 5% across 1000 iterations.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analysis.py` to compute switching costs (RT_switch - RT_stay) per subject
- [ ] T031 [US3] Implement `code/analysis.py` primary correlation: Pearson/Spearman between mean synchrony and switching costs
- [ ] T032 [US3] Implement `code/analysis.py` permutation testing with a sufficient number of iterations to ensure robust statistical inference (shuffling subject vectors) as mandated by FR-005; log iteration count.
- [ ] T033 [US3] Implement multiple-comparison correction (Bonferroni) for theta and gamma bands
- [ ] T034 [US3] Implement `code/analysis.py` sensitivity analysis: repeat correlation for windows [-600, 0] and [-400, 0]; validate stability (r change < 0.1, p < 0.05) against primary result; save `data/metrics/sensitivity_report.json` (requires T004)
- [ ] T035 [US3] Implement `code/analysis.py` secondary trial-level analysis: Linear Mixed-Effects model (`RT ~ Synchrony + (1|Subject)`) using `statsmodels`; handle missing trial-level synchrony by excluding rows
- [ ] T036 [US3] Generate `data/trial_level/per_trial_synchrony.csv` with columns: `subject_id`, `trial_id`, `condition`, `synchrony`, `rt`; exclude rows with missing synchrony; requires T004
- [ ] T037 [US3] Save final results to `data/metrics/correlation_results.json` and `data/metrics/trial_level_analysis.json` with keys: `correlation`, `p_value`, `framing_note` (must contain "associational"); generate `results_summary.md` containing the associational framing text; requires T004
- [ ] T038 [US3] Implement programmatic assertion in `code/analysis.py` to verify output JSON and `results_summary.md` contain "associational" framing as mandated by FR-008

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Implement `code/main.py` pipeline orchestrator to run phases sequentially
- [ ] T041 [P] Add documentation updates in `projects/PROJ-498-investigating-the-relationship-between-n/README.md`
- [ ] T042 [P] Run `code/update_state_hashes.py` to update state file with new artifact hashes
- [ ] T043 [P] Verify `quickstart.md` validation
- [ ] T044 [P] Code cleanup and refactoring for CPU efficiency

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
- **Critical**: No fabricated data; all inputs must come from real OpenNeuro datasets (searched dynamically).
- **Critical**: All output files must adhere to the specified schemas and include required framing (associational).