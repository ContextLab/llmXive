# Tasks: Investigating the Neural Response to Deviance in Auditory Perception

**Input**: Design documents from `/specs/001-investigating-the-neural-correlates-of-predictive-coding-errors/`
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

## Phase 0: Data Acquisition & Validation (Blocking Prerequisite)

**Purpose**: Download and verify the raw dataset before any processing begins.

- [X] T010 [P] [FR-001] Implement `code/download.py`: Fetch the target dataset from OpenNeuro using `wget` or `curl` (via subprocess) with retry logic (3 attempts, 10s backoff). Write raw files to `data/raw`. **Verify**: Files written to `data/raw`.
- [X] T011 [P] [FR-001] Implement `code/download.py` verification logic: Verify checksums against OpenNeuro manifest hashes before finalizing `data/raw`. **Verify**: Checksums match or error raised.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure per implementation plan: `data/raw`, `data/processed`, `code`, `tests`, `results` directories in `projects/PROJ-118-investigating-the-neural-correlates-of-p/`. **Verify**: List directories to confirm creation.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`: `mne>=1.6.0`, `numpy`, `scipy`, `pandas`, `matplotlib`, `scikit-learn`, `pingouin>=0.5.0`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `data/raw` and `data/processed` directory structure with `.gitkeep` files. **Verify**: Directories exist.
- [X] T005 [P] Create `code/config.yaml` defining pipeline parameters (filter: 1-30Hz, epoch: pre-stimulus baseline to post-stimulus window, ICA threshold: optimized for component selection).
- [X] T006 [P] Implement `code/__init__.py` and helper utility functions for logging and path resolution
- [X] T007 Create base data loading schema and validation logic in `code/data_utils.py`
- [ ] T008 Configure `pytest` environment in `tests/` with `conftest.py` for fixtures
- [ ] T009 Setup environment variable management for `OPENNEURO_API_KEY` (if needed) and local paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Preprocess Auditory Oddball EEG Data (Priority: P1) 🎯 MVP

**Goal**: Download an OpenNeuro dataset, subsample to 32 channels, filter, re-reference, epoch, and remove artifacts via ICA.

**Independent Test**: Upon completion, `data/processed` contains `.fif` files with epochs labeled "standard" and "deviant", and a log file confirms the number of rejected epochs/components.

### Implementation for User Story 1

- [X] T015 [US1] [FR-001b] Implement channel montage selection in `code/preprocess.py` to define the standard channel montage list (Fz, FCz, Cz, Pz, etc.) required by FR-001b for T016.
- [X] T016 [US1] [FR-001b] Implement subsampling in `code/preprocess.py` to reduce raw data to the selected montage to fit memory constraints, preserving original raw data in `data/raw`.
- [X] T017 [US1] [FR-002] Implement filtering in `code/preprocess.py` to apply a bandpass filter and re-reference to common average.
- [X] T018 [US1] [FR-002] Implement epoching in `code/preprocess.py` to create epochs covering a pre-stimulus baseline to a post-stimulus window for "standard" and "deviant" conditions. **Input**: `data/raw`. **Output**: `data/processed/epo_raw.fif` (Intermediate artifact). **Success**: File exists, epoch count > 0, log confirms epoching. **Note**: Epoching runs BEFORE ICA.
- [X] T019 [US1] [FR-003] Implement ICA component detection in `code/preprocess.py` to identify components correlating >0.8 with frontal channels or showing frontal topography. **Input**: `data/processed/epo_raw.fif`.
- [X] T020 [US1] [FR-003] Implement ICA component removal in `code/preprocess.py` to remove detected blink components and log the count of removed components. **Input**: `data/processed/epo_raw.fif`. **Output**: `data/processed/epo_clean.fif` (Final cleaned epochs).
- [X] T021 [US1] [SC-001] Implement logic to calculate rejection rates from ICA logs, exclude participants with >50% rejected trials (if rejected_trials > 0.5 * total_trials), and log their IDs to `data/processed/rejected_participants.log` (JSON format).
- [X] T051 [US1] [FR-001] Integration test `test_preprocess_pipeline_sub_01` in `tests/integration/test_preprocess.py`: run pipeline on `sub-01`, assert `data/processed/epo_clean.fif` exists and contains >0 epochs. **Verify**: File exists, epoch count > 0.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract MMN Amplitude and Latency Metrics (Priority: P2)

**Goal**: Calculate peak MMN amplitude and latency for each participant from **Difference Waves** (Deviant - Standard).

**Independent Test**: Running the extraction script produces `results/metrics.csv` with columns for `standard_amplitude`, `standard_latency`, `deviant_amplitude`, `deviant_latency`, `peak_detected`, and `snr`.

### Implementation for User Story 2

- [X] T022a [US2] [FR-004] Implement `code/extract.py` part 1: Load `data/processed/epo_clean.fif` (from T020) and compute average ERPs for "standard" and "deviant" conditions separately for each participant. **Verify**: Two ERPs per participant created.
- [X] T022b [US2] [FR-004] Implement `code/extract.py` to compute the difference wave (Deviant ERP - Standard ERP) for each participant. **Input**: ERPs from T022a. **Output**: `data/processed/diff_wave.fif`. **Must follow T022a**.
- [X] T023 [US2] [FR-004] Implement peak search logic in `code/extract.py` to find the most negative voltage in the **early post-stimulus** window at Fz and FCz electrodes on the **Difference Wave** (from T022b). **Input**: `data/processed/diff_wave.fif`.
- [X] T024 [US2] [SC-005] Implement secondary window fallback in `code/extract.py` to search **100–300 ms** if no peak ≥ 2.0 µV is found in the primary window for the difference wave, flagging `peak_detected=false` if still not found.
- [X] T025 [US2] [FR-004] Implement SNR calculation in `code/extract.py` for each detected peak and difference wave.
- [X] T026 [US2] [FR-004] Implement `results/metrics.csv` generation in `code/extract.py` with columns: `participant_id`, `standard_amplitude`, `standard_latency`, `deviant_amplitude`, `deviant_latency`, `peak_detected` (boolean), `snr`. **Schema**: `peak_detected` as boolean, null values as JSON null. **Includes logic to retain participants with `peak_detected=false` for prevalence analysis but flag them for exclusion from mean t-test calculations.**
- [X] T050 [US2] [FR-004] Integration test `test_metric_extraction_sub_01` in `tests/integration/test_extract.py`: run extraction on `sub-01`, assert `results/metrics.csv` exists with columns `standard_amplitude`, `deviant_amplitude`, `peak_detected`. **Verify**: File exists, columns present.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison and Visualization (Priority: P3)

**Goal**: Execute paired t-tests with FDR correction, permutation tests, and generate visualizations (ERP plots, topomaps).

**Independent Test**: Script generates `results/statistics.json` with p-values, Cohen's d, and `results/plots/` containing PNGs of ERP waveforms and topographic maps.

### Implementation for User Story 3

- [X] T029 [US3] [FR-005] Implement logic in `code/stats.py` to filter `results/metrics.csv` (from T026) based on `peak_detected` flag and exclusion lists from US1 (T021) before statistical testing. **Input**: `results/metrics.csv`.
- [X] T030 [US3] [FR-005] Implement paired-sample t-test in `code/stats.py` on difference scores for Amplitude and Latency at Fz/FCz (Wilcoxon if normality violated).
- [X] T031 [US3] [FR-005] Implement FDR correction in `code/stats.py` for the 4 comparisons (Amplitude Fz, Amplitude FCz, Latency Fz, Latency FCz) as per FR-005.
- [X] T032 [US3] [FR-005] [SC-003] [Const-VII] Implement mixed-effects model in `code/stats.py` with `condition` as fixed effect and `subject` as random effect, explicitly referencing **Plan Phase 3** and Constitution Principle VII.
- [X] T033 [US3] [FR-006] Implement non-parametric cluster-based permutation test (1000 permutations) in `code/stats.py` to validate spatiotemporal extent of MMN as a **substitute for linear scaling analysis** (per FR-006), using clustering threshold p < 0.05 (uncorrected) and channel adjacency based on standard 32-channel montage.
- [X] T034 [US3] [SC-003] Calculate Cohen's d effect sizes and confidence intervals for all significant findings in `code/stats.py`.
- [X] T035 [US3] [FR-005] Generate `results/statistics.json` in `code/stats.py` containing p-values, effect sizes, cluster results, mixed-effects summary, and prevalence. **Schema**: JSON object with keys `p_values`, `effect_sizes`, `cluster_results`, `mixed_effects`, `prevalence`.
- [X] T039 [US3] [SC-001] Calculate and log the prevalence (proportion of participants with `peak_detected=true`) in `results/statistics.json`. **Input**: `results/metrics.csv`.
- [X] T039b [US3] [SC-005] Verify that peak latency falls within the 150–250 ms window for ≥80% of valid participants. **Task**: Assert threshold met, fail task if not. **Output**: `results/latency_validation.json` containing `threshold_met: boolean` and `percentage: float`.
- [X] T036 [US3] [FR-007] Implement ERP plot generation in `code/viz.py` to create grand-average ERP plots (Standard, Deviant, Difference) with confidence interval shaded regions.
- [X] T037 [US3] [FR-007] Implement topographic map generation in `code/viz.py` of the MMN difference (Deviant - Standard) at peak latency.
- [X] T038 [US3] [FR-007] Save all visualizations to `results/plots/` as PNG files (`erp_plot.png`, `topomap.png`). **Verify**: Files exist.
- [X] T051 [US3] [FR-005] Unit test `test_fdr_correction_4_comparisons` in `tests/unit/test_stats.py`: assert FDR correction logic on 4 input p-values. **Verify**: Correct p-values returned.
- [X] T052 [US3] [FR-007] Integration test `test_viz_generation` in `tests/integration/test_viz.py`: run viz module, assert `results/plots/erp_plot.png` and `results/plots/topomap.png` exist. **Verify**: Files exist.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041 Code cleanup and refactoring in `code/`
- [ ] T042 Performance optimization: verify ICA and permutation tests run within 6 hours on 2 CPU / 7 GB RAM
- [ ] T043 [P] Additional unit tests for edge cases (e.g., empty datasets, missing peaks) in `tests/unit/`
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T045 Verify all artifacts are hashed and `state.yaml` is updated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Acquisition)**: No dependencies - can start immediately
- **Phase 1: Setup**: No dependencies - can start immediately
- **Phase 2: Foundational**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/processed/epo_clean.fif` to extract metrics)
- **User Story 3 (P3)**: Depends on User Story 2 (requires `results/metrics.csv` for statistical analysis)

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks (Tests depend on artifacts).
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Acquisition
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify epochs and ICA logs)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Metrics ready)
4. Add User Story 3 → Test independently → Deploy/Demo (Full analysis)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Extraction Logic) - *Can start once T021 is done*
 - Developer C: User Story 3 (Stats/Viz) - *Can start once T027 is done*
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
- **Critical Constraint**: All tasks must be CPU-tractable on a standard dual-core configuration with sufficient memory. No GPU, no 8-bit quantization, no large LLMs.
- **Data Integrity**: Never fabricate data. All metrics must come from real `ds003645` data fetched via `code/download.py`.