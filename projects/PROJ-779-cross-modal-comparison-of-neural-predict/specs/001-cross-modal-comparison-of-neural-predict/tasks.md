# Tasks: Cross-Modal Comparison of Neural Prediction Error Signals

**Input**: Design documents from `/specs/001-cross-modal-prediction-error/`
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

- [X] T001a [P] Create `code/` directory and `code/__init__.py`
- [X] T001b [P] Create `code/data/` directory and `code/data/__init__.py`
- [X] T001c [P] Create `code/analysis/` and `code/validation/` directories with `__init__.py` files
- [X] T002 [P] Create `requirements.txt` with pinned versions (mne, numpy, scipy, scikit-learn, pandas, statsmodels, h5py, requests, pytest, huggingface_hub)
- [ ] T003 [P] Create virtualenv and install dependencies from `requirements.txt` <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T004 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create `code/config.py` defining paths, random seeds, sampling rate threshold (≥500 Hz), trial thresholds (≥100 oddball, ≥300 standard), and time windows
- [X] T006 [P] Implement `code/__init__.py` and module initialization
- [X] T007 [P] Setup `code/data/__init__.py` and base logging infrastructure
- [X] T008 Create base `code/data/data_loader.py` skeleton for dataset validation logic
- [X] T009 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T010 Setup environment configuration management (load from `.env` or defaults)
- [ ] T011 [P] **Setup**: Document "Real Data" assumption in `docs/README.md` and `code/config.py`, explicitly stating that all data must originate from OpenNeuro datasets and that no synthetic data generation is permitted.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel (dependent on data availability)

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OpenNeuro datasets (ds000246, ds000117) [UNRESOLVED-CLAIM: c_7bc70f80 — status=not_enough_info], validate trial counts and sampling rates, and apply standardized preprocessing (filtering, ICA, re-referencing).

**Independent Test**: Run `code/data/download.py` and `code/data/preprocess.py` on a subset; verify output files exist, artifact logs are generated, and sampling rate validation halts execution if <500 Hz.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T012 [P] [US1] Unit test for sampling rate validation in `tests/unit/data/test_validation.py`
- [~] T013 [P] [US1] Unit test for trial count validation in `tests/unit/data/test_validation.py`
- [~] T014 [P] [US1] Integration test for full download and preprocess pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [~] T015 [US1] Implement `code/data/download.py` to fetch ds (auditory) using `mne.datasets`. **This task must ensure metadata is extracted immediately after fetch to validate the dataset structure.**
- [~] T016 [US1] Implement `code/data/download.py` to fetch ds (visual) using `huggingface_hub.snapshot_download` with **Dataset ID: openneuro/ds ** and **Version Tag: r.0 **. **This task must ensure metadata is extracted immediately after fetch to validate the dataset structure.** **Depends on T015 completion** (sequential dataset fetch for consistency). <!-- FAILED: unspecified -->
- [~] T017 [US1] Implement `code/data/download.py` validation logic for Auditory: check sampling rate (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard); halt with specific error codes if failed (FR-008, FR-009, FR-011). **Depends on T015.**
- [~] T018 [US1] Implement `code/data/download.py` validation logic for Visual: check sampling rate (≥500 Hz) and trial counts (≥100 oddball, ≥300 standard); halt with specific error codes if failed (FR-008, FR-009, FR-011). **Depends on T016.** <!-- FAILED: unspecified -->
- [~] T019 [US1] Implement `code/data/preprocess.py` bandpass filter (low-frequency cutoff).
- [~] T020 [US1] Implement `code/data/preprocess.py` ICA artifact removal (using MNE default settings, CPU-tractable). **Depends on T019.**
- [~] T021 [US1] Implement `code/data/preprocess.py` common average re-referencing. **Depends on T020.**
- [~] T022 [US1] Implement `code/data/preprocess.py` to **SAVE CLEANED DATA ARTIFACT** (`data/processed/cleaned_data.fif`) and trial rejection logging. **Depends on T021.**
- [~] T023 [US1] Create `code/main.py` orchestration script to chain download → validate → preprocess

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. US2 and US3 can only start after T022 completes.

---

## Phase 4: User Story 2 - Prediction Error Signal Extraction and Quantification (Priority: P2)

**Goal**: Compute difference waves (oddball - standard), extract peak latency and mean amplitude in modality-specific windows, and generate summary statistics.

**Independent Test**: Process preprocessed data for one modality; verify output JSON contains peak latency (ms), mean amplitude (µV), and correct time window labels.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T024 [P] [US2] Unit test for difference wave computation in `tests/unit/analysis/test_metrics.py`
- [~] T025 [P] [US2] Unit test for peak/amplitude extraction in `tests/unit/analysis/test_metrics.py`
- [~] T026 [P] [US2] Integration test for full extraction pipeline in `tests/integration/test_extraction.py`

### Implementation for User Story 2

- [~] T027 [P] [US2] Implement `code/analysis/metrics.py` function to compute difference waves (Oddball - Standard) at fronto-central electrodes (Auditory). **Depends on T022 (Cleaned Data Artifact).**
- [~] T028 [P] [US2] Implement `code/analysis/metrics.py` function to compute difference waves at occipito-parietal electrodes (Visual). **Depends on T022 (Cleaned Data Artifact).**
- [~] T029 [US2] Implement `code/analysis/metrics.py` peak latency extraction (Auditory and Visual modalities)
- [~] T030 [US2] Implement `code/analysis/metrics.py` mean amplitude extraction for the same windows <!-- FAILED: unspecified -->
- [~] T031 [US2] Implement `code/analysis/metrics.py` to generate a summary table (DataFrame/JSON) with latency, amplitude, and modality labels
- [~] T032 [US2] Update `code/main.py` to call extraction after preprocessing and save results to `data/results/metrics_summary.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Source Localization, Statistical Comparison, and Infrastructure Validation (Priority: P3)

**Goal**: Apply MNE for source localization, perform statistical comparison (permutation tests, TOST, t-test), validate reliability (split-half), and ensure end-to-end CI feasibility.

**Independent Test**: Run full pipeline on GitHub Actions free-tier (limited CPU, GB RAM); verify exit code 0 within 6 hours, source maps generated, and statistical decisions reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T033 [P] [US3] Unit test for MNE lead field generation in `tests/unit/analysis/test_source.py` <!-- SKIPPED: non-mapping output -->
- [~] T034 [P] [US3] Unit test for permutation test logic in `tests/unit/analysis/test_stats.py`
- [~] T035 [P] [US3] Unit test for split-half reliability calculation in `tests/unit/validation/test_reliability.py`
- [~] T036 [P] [US3] CI Integration test: Run full pipeline on GitHub Actions and verify time/memory constraints

### Implementation for User Story 3

- [~] T037 [US3] Implement `code/analysis/source.py` to setup ICBM152 head model and compute lead fields. **Depends on T022 (cleaned data) and T005 (config paths).**
- [~] T038 [US3] Implement `code/analysis/source.py` MNE with depth weighting and orientation normalization. **Depends on T037 (Lead Fields).**
- [~] T039 [US3] Implement `code/analysis/source.py` sensitivity analysis: sweep spatial smoothing kernel (σ ∈ {low, medium, high} mm), compute Coefficient of Variation, and **Generate and save `data/results/sensitivity_analysis.csv` containing source strength vs. sigma values** (FR-014). **Depends on T038.**
- [ ] T040 [US3] Implement `code/analysis/stats.py` Mixed-Effects Permutation Test (sufficient permutations for robust inference) for **source strength** modality comparison. **Depends on T039.**
- [ ] T041 [US3] Implement `code/analysis/stats.py` independent samples t-test for **source strength** modality comparison (Required by FR-006 'OR' condition). **Depends on T040.**
- [ ] T042 [US3] Implement `code/analysis/stats.py` TOST (Two One-Sided Tests) for **source strength** equivalence. **Depends on T041.**
- [ ] T043 [US3] Implement `code/analysis/stats.py` Benjamini-Hochberg correction for multiple comparisons. **Depends on T042.**
- [ ] T044 [US3] Implement `code/validation/reliability.py` split-half reliability (Odd/Even trials) and Cronbach's α calculation (FR-013). **Depends on T039.**
- [ ] T045 [US3] Implement `code/main.py` to aggregate results from T037-T044 for final report generation (Report Assembly). **Depends on completion of T037-T044.**
- [ ] T046 [US3] Implement `code/main.py` logic for Latency Classification: Check |Δt| < 50ms [UNRESOLVED-CLAIM: c_737cb22f — status=not_enough_info] (SC-001) and set classification field.
- [ ] T047 [US3] Implement `code/main.py` logic for Source Overlap: Check **Dice > 0.6 AND TOST p < 0.05** (Plan Logic) and set classification field. **Note: Implements Plan Phase 4 logic, overriding obsolete SC-002 text.**
- [ ] T048 [US3] **Data Integrity Verification**: Implement `code/main.py` to validate that processed data artifacts match the checksums recorded in `data/manifest.json` (generated during T015/T016). **Replace any 'random source' detection logic with this concrete checksum verification to ensure data originates from the fetched OpenNeuro sources.** **Depends on T045.**
- [ ] T049 [US3] Generate final report in `data/results/final_report.md` stating: (A) Latency difference vs 50ms threshold, (B) Source overlap (Dice) & TOST result, (C) Reliability score, (D) Computational feasibility confirmation. **Depends on T046, T047, T048.**

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T050 [P] Documentation updates: Create `docs/README.md` with installation steps and `docs/quickstart.md` with usage examples.
- [ ] T051 Code cleanup and refactoring
- [ ] T052 Performance optimization to ensure <6h runtime on CI (e.g., subsampling if needed, optimizing MNE parameters)
- [ ] T053 [P] Additional unit tests for edge cases (missing modalities, low SNR) in `tests/unit/`
- [ ] T054 Run `quickstart.md` validation to ensure reproducibility

---

## Phase 7: Review Resolution & Constitution Compliance (Revision Pass)

**Purpose**: Address specific reviewer concerns regarding Constitution Principle VII (Validation Independence) and ensure strict adherence to the "Real Data + Real Results" rule.

### Implementation for Review Resolution

- [ ] T055 [US3] **Draft Constitution Amendment**: Create `docs/constitution-amendment-vii.md` explicitly documenting the substitution of behavioral measures with split-half reliability for passive oddball paradigms, and submit for ratification. **This task MUST be completed before T056/T057 are executed.**
- [ ] T056 [US3] Refactor `code/validation/reliability.py` to explicitly document that Split-Half Reliability is used as a **proxy** for Validation Independence (Principle VII) and reference the approved amendment from T055 (FR-013).
- [ ] T057 [US3] Update `data/results/final_report.md` generation logic to include a dedicated "Constitution Compliance" section that explicitly cites the approved amendment from T055 and confirms all other principles (I-VI) are met.

**Checkpoint**: All reviewer concerns regarding Constitution Principle VII and data integrity are explicitly addressed and documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
 - **Note**: US2 and US3 strictly depend on the *completion* of US1 data generation (T022), even if developed in parallel.
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Review Resolution (Phase 7)**: Depends on the completion of the core implementation (Phases 1-5) to address specific logic and documentation gaps.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T022)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on metrics from US2 and data from US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows) **provided data dependencies are managed**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members, but US2/US3 implementation requires US1 data to be ready.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for sampling rate validation in tests/unit/data/test_validation.py"
Task: "Unit test for trial count validation in tests/unit/data/test_validation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/preprocess.py" (T019-T021)
```
*Note: T015 (Download Auditory) and T016 (Download Visual) are sequential and cannot run in parallel with each other or with preprocessing. T017 depends on T015; T018 depends on T016.*

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
 - Developer B: User Story 2 (waits for T022 data)
 - Developer C: User Story 3 (waits for T022 data)
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
- **Critical Constraint**: All tasks must be executable on CPU-only GitHub Actions free-tier (limited CPU resources, 7GB RAM, 6h limit). No GPU, no 8-bit quantization, no large model training.
- **Data Integrity**: All datasets must be fetched from real sources (OpenNeuro ds000246, ds000117); no synthetic data generation.
- **Constitution Compliance**: Explicitly acknowledge the use of Split-Half Reliability as a proxy for Validation Independence (Principle VII) in all reporting and documentation, pending formal amendment (T055).