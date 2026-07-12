# Tasks: Predicting Sleep Stage Transitions from Scalp EEG Using Deep Learning

**Input**: Design documents from `/specs/001-predicting-sleep-stage-transitions-from/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `src/`, `tests/`, `data/`, `specs/` directories
- [ ] T001b Create `data/raw`, `data/processed`, `data/interim` subdirectories
- [ ] T001c Create `src/data`, `src/features`, `src/models`, `src/utils` subdirectories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement configuration management in `src/utils/config.py` (paths, seeds, hyperparameters)
- [ ] T005 [P] Setup logging infrastructure in `src/utils/logging.py`
- [ ] T006 Create base data schemas and validation logic in `tests/contract/test_schemas.py`
- [~] T007 [P] Implement constraint checking for model parameters and memory in `tests/contract/test_constraints.py`
- [~] T008 Setup CI pipeline (`ci.yml`) to run contract tests and reference validator before merge

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Preprocessing and Transition Window Extraction (Priority: P1) 🎯 MVP

**Goal**: Download Sleep-EDF SC data, preprocess (interpolate, filter), and segment into 30s epochs and 60s transition windows.

**Independent Test**: The pipeline can be tested by running the preprocessing script on a subset and verifying the output contains the correct number of transition windows centered on hypnogram changes, and that spectral content matches expected physiological ranges.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test for data download and checksum verification in `tests/unit/test_download.py`
- [~] T010 [P] [US1] Unit test for notch filter attenuation (≥90% at 50/60Hz) in `tests/unit/test_preprocess.py` <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
 in "<unicode string>", line 1, column 7:
 def run_tests():
 ^
expected <block end>, but found '<scalar>'
 in "<unicode string>", line 2, column 13:
 """
 ^) -->
- [~] T011 [P] [US1] Integration test for segmenting a subject with no transitions (edge case) in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [~] T012 [P] [US1] Implement `src/data/download.py`: Download Sleep-EDF SC subset from PhysioNet, verify checksums, handle missing subjects gracefully
- [~] T013 [US1] Implement `src/data/preprocess.py`: Linear interpolation for missing data, bandpass (0.5–45 Hz), notch (50/60 Hz) filters
- [~] T014 [US1] Implement `src/data/preprocess.py`: Segmentation logic for 30s stable epochs and 60s **centered** transition windows (for statistical analysis), saving to `data/processed/centered_transition_windows.parquet`
- [~] T014b [US1] Implement `src/data/preprocess.py`: Segmentation logic for **60s pre-transition input windows** ending 30s *before* annotated stage changes (for model training input) to avoid tautology, saving to `data/processed/pre_transition_windows.parquet` (depends on T014 raw data extraction)
- [ ] T014c [US1] Implement `src/data/preprocess.py`: Extract available EOG channels (e.g., EOG-M1) if present; if EOG is missing or insufficient, create a metadata flag indicating "EOG unavailable" to trigger fallback logic in T021, saving to `data/processed/eog_signals.parquet`
- [ ] T015 [US1] Implement `src/data/loader.py`: Utilities to load and iterate over processed epochs/windows
- [ ] T016 [US1] Add metadata flagging for imputed segments in the output dataframes

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Transition Characterization (Priority: P2)

**Goal**: Compute time/freq/non-linear features, perform Cluster-Based Permutation Tests with FDR correction, and validate against independent physiological targets.

**Independent Test**: The feature extraction module can be tested by running it on a fixed dataset and verifying that statistical tests identify known physiological differences and that transition windows show distinct feature distributions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for feature extraction (RMS, Zero-Crossing, Delta/Theta power) in `tests/unit/test_features.py`
- [ ] T018 [P] [US2] Unit test for Cluster-Based Permutation Test logic with FDR correction in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `src/features/extraction.py`: Compute time-domain (RMS, ZC), frequency-domain (absolute/relative power), and non-linear (Sample Entropy, DFA) features
- [ ] T020 [US2] Implement `src/features/stats.py`: Cluster-Based Permutation Tests with Benjamini-Hochberg FDR correction (q ≤ 0.05) to compare transition vs. stable epochs
- [ ] T021 [US2] Implement validation logic against independent physiological targets: **Attempt to use EOG signals (from T014c) if available; if EOG is missing (flagged in metadata), automatically switch to validating against the expert re-scoring subset** as per FR-010 fallback strategy; ensure validation is never skipped
- [ ] T022 [US2] Generate summary report in `data/processed/features_summary.json` **validating against the schema in `tests/contract/test_schemas.py`** (from T006), listing top 5 features by effect size and validation scores

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Lightweight Temporal Model Training and Validation (Priority: P3)

**Goal**: Train a lightweight 1D-CNN (≤100k params) to predict transition probability 30s in advance, validate on held-out subjects (LOSO), and ensure CPU feasibility.

**Independent Test**: The model training and validation can be tested by running the training loop on CPU, verifying convergence within 4 hours, and that held-out transition prediction accuracy exceeds random baseline by ≥5%.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Contract test for model parameter count (≤100k) in `tests/contract/test_constraints.py`
- [ ] T024 [P] [US3] Unit test for LOSO cross-validation split logic in `tests/unit/test_model.py`
- [ ] T025 [P] [US3] Integration test for training loop timing and memory usage (peak RSS ≤ 7GB) in `tests/integration/test_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `src/models/architecture.py`: Define lightweight 1D-CNN (≤100k params) with strict regularization (Dropout, L2)
- [ ] T027 [US3] Implement `src/models/train.py`: Training loop with LOSO CV, **consuming the pre-transition windows from T014b** (`data/processed/pre_transition_windows.parquet`) to predict transition probability 30s in advance (avoiding tautology)
- [ ] T028 [US3] Implement `src/models/validate.py`: Validation on held-out subjects, calculating transition prediction accuracy vs. random baseline
- [ ] T029 [US3] Implement analysis of attention weights/feature importance to visualize which input epochs contributed most to predictions
- [ ] T030a [US3] Save model weights to `data/processed/model_checkpoint.pth`
- [ ] T030b [US3] Save training metrics to `data/processed/metrics.json`
- [ ] T030c [US3] Compute SHA-256 hashes for model and metrics, outputting them to a temporary file (e.g., `data/processed/hashes.tmp`); **do NOT write to `state/...yaml` directly**; the `scripts/update-state-hash.sh` hook (triggered by the Advancement-Evaluator Agent) will read this temp file and update `state/projects/PROJ-102-...yaml` as the sole writer per Constitution Principle V

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `README.md`
- [ ] T032 Code cleanup and refactoring across `src/`
- [ ] T033 Performance optimization to ensure total pipeline ≤ 6 hours on free-tier runner
- [ ] T034 [P] Additional unit tests for edge cases (missing annotations, empty transition sets) in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014, T014b, T014c)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data (T014b) and US2 feature logic (or raw signal fallback)

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
Task: "Contract test for data download in tests/unit/test_download.py"
Task: "Unit test for notch filter in tests/unit/test_preprocess.py"

# Launch implementation tasks:
Task: "Implement src/data/download.py"
Task: "Implement src/data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Data pipeline works, no crashes on missing data)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Statistical insights)
4. Add User Story 3 → Test independently → Deploy/Demo (Predictive model)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Features & Stats)
 - Developer C: User Story 3 (Model Training)
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
- **Constraint**: All tasks must run on CPU-only CI (limited CPU, limited RAM, 6h limit). No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: No fake data. All tasks must use real Sleep-EDF SC data from PhysioNet.