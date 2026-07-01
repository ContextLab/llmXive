# Tasks: Investigating the Neural Response to Deviance in Auditory Perception

**Input**: Design documents from `/specs/001-investigating-predictive-coding-errors/`
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

- [ ] T001 Create project structure per `plan.md` by executing: `mkdir -p projects/PROJ-118-investigating-the-neural-correlates-of-p/data/raw projects/PROJ-118-investigating-the-neural-correlates-of-p/data/processed projects/PROJ-118-investigating-the-neural-correlates-of-p/results projects/PROJ-118-investigating-the-neural-correlates-of-p/results/plots projects/PROJ-118-investigating-the-neural-correlates-of-p/code projects/PROJ-118-investigating-the-neural-correlates-of-p/tests/unit projects/PROJ-118-investigating-the-neural-correlates-of-p/tests/integration projects/PROJ-118-investigating-the-neural-correlates-of-p/specs/contracts`. This task explicitly creates the directories listed in `plan.md` under `Project Structure`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T002 Initialize Python 3.11 project: Run `python3 -m venv venv` in the project root. Create `requirements.txt` with a header comment `# Python 3.11` and pinned dependencies: `mne==1.6.0`, `numpy==1.26.0`, `scipy==1.11.4`, `pandas==2.1.4`, `matplotlib==3.8.2`, `scikit-learn==1.3.2`, `pingouin==0.5.3`, `statsmodels==0.14.0`.
- [ ] T003 [P] Configure linting and formatting: Install tools via `pip install black flake8 isort`. Create `.flake8` with `[flake8] max-line-length = 88` and `pyproject.toml` with `[tool.black] line-length = 88`.
- [X] T004 Create `code/config.yaml` with pipeline parameters using this schema:
 ```yaml
 filter: {low: 1, high: 30}
 ica: {threshold: 0.8, n_components: 0.99}
 epoch: {tmin: -0.2, tmax: 0.6}
 montage: {channels: ['Fp', 'Fp', 'F7', 'F8', 'F3', 'F4', 'Fz', 'FC3', 'FC4', 'FCz', 'C3', 'C4', 'Cz', 'CP3', 'CP4', 'CPz', 'P3', 'P4', 'Pz', 'PO7', 'PO8', 'O1', 'O2', 'Oz', 'AF7', 'AF8', 'FT7', 'FT8', 'TP7', 'TP8', 'PO3', 'PO4']} # 32 total
 ```
- [X] T005 [P] Implement `code/download.py`: Create `fetch_ds003645(output_dir: str) -> str` function that fetches the dataset using `mne-bids` with a `@retry(max_attempts=3, backoff=10)` decorator to handle network failures.
- [ ] T006 [P] Setup directory structure: Ensure `data/raw`, `data/processed`, `results`, `results/plots` exist.
- [~] T007 Create data schema definitions in `specs/contracts/`:
 - `specs/contracts/dataset.schema.yaml`: `subject_id: string (required)`, `session: string`, `run: string`, `checksum: string`.
 - `specs/contracts/mmn_metrics.schema.yaml`: `subject_id: string (required)`, `amplitude: float`, `latency: float`, `peak_detected: boolean`, `snr: float`, `condition: string`.
 - `specs/contracts/results.schema.yaml`: `metric_name: string (required)`, `value: float`, `unit: string`.
 - `specs/contracts/stats_report.schema.yaml`: `comparison: string (required)`, `p_value: float`, `effect_size: float`, `ci_lower: float`, `ci_upper: float`.
- [~] T008 Configure environment variable handling and logging infrastructure in `code/__init__.py`.
- [~] T009 Setup `pytest` configuration for unit and integration tests (`pytest.ini`).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Preprocess Auditory Oddball EEG Data (Priority: P1) 🎯 MVP

**Goal**: Automatically download OpenNeuro ds003645, subsample to 32 channels, filter, re-reference, epoch, and remove artifacts via ICA.

**Independent Test**: The pipeline can be run in isolation; upon completion, the output directory must contain `.fif` or `.edf` files with epochs labeled "standard" and "deviant", and the number of rejected epochs due to artifacts must be logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these test skeletons FIRST, ensure they FAIL before implementation. Execution depends on implementation.**

- [~] T010 [US1] Write test skeleton for download retry logic in `tests/unit/test_download.py` (expect failure until T005 is done). <!-- FAILED: unspecified -->
- [~] T011 [US1] Write test skeleton for preprocessing pipeline producing valid epochs in `tests/integration/test_preprocess.py` (expect failure until T013 is done).

### Implementation for User Story 1

- [~] T012 [US1] Implement `code/download.py`: Fetch ds003645 from OpenNeuro using `mne-bids`. Function signature: `def fetch_ds003645(output_dir: str) -> str`. Handles `ValueError` and `TimeoutError` with retry logic.
- [~] T013 [US1] Implement `code/preprocess.py`: A single cohesive script that performs the following steps in order:
 1. Load raw data from `data/raw` using `mne.io.read_raw_fif` into a copy.
 2. Subsample the COPY to the 32-channel montage defined in `code/config.yaml` (channels: Fp1, Fp2, F7, F8, F3, F4, Fz, FC3, FC4, FCz, C3, C4, Cz, CP3, CP4, CPz, P3, P4, Pz, PO7, PO8, O1, O2, Oz, AF7, AF8, FT7, FT8, TP7, TP8, PO3, PO4) using `raw.pick_channels()`.
 3. Apply bandpass filter (low-frequency cutoff) using `raw.filter()` and re-reference to common average using `raw.set_eeg_reference('average')`.
 4. Epoch data (-200 ms to 600 ms) into "standard" and "deviant" conditions using `mne.Epochs()` based on event codes.
 5. Run ICA using `mne.preprocessing.ICA()`, identify eye-blink components using `ica.find_bads_eog()` with correlation threshold > 0.8 on frontal channels (Fp1, Fp2, F7, F8, Fz, FCz), and remove them via `ica.apply()`.
 6. Save cleaned epochs to `data/processed/epo.fif`.
- [~] T017 [US1] Add logging for rejected epochs and removed ICA components to `results/preprocess_log.txt` (FR-003). Format per subject: "Subject {subject_id}: Rejected {count} epochs, Removed {ica_count} ICA components".
- [~] T014 [US1] [P] Unit test for preprocessing logic (mock data) in `tests/unit/test_preprocess.py`.
- [ ] T015 [US1] [P] Integration test for preprocessing pipeline in `tests/integration/test_preprocess.py` (now runnable after T013).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract MMN Amplitude and Latency Metrics (Priority: P2)

**Goal**: Calculate peak MMN amplitude and latency for each participant from raw conditions (Deviant vs Standard) at Fz and FCz, AND extract difference wave metrics for visualization.

**Independent Test**: Running the extraction script on a sample of participants must produce a CSV or JSON file where each row represents a participant, containing columns for "deviant_amplitude", "deviant_latency", "standard_amplitude", and "standard_latency", plus flags for outliers.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [US2] Unit test for peak detection logic within 150-250ms window in `tests/unit/test_extract.py`.
- [ ] T019 [US2] Integration test for metric extraction producing valid CSV in `tests/integration/test_extract.py`.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/extract.py`: Extract **Raw Condition Peaks** for Deviant and Standard conditions separately at Fz and FCz. Identify the most negative peak in the early post-stimulus window for each condition. **Dependency**: Requires output of T013 (cleaned epochs).
- [ ] T020b [US2] Implement `code/extract.py`: Compute **Difference Wave** (Deviant ERP - Standard ERP) for each participant using `epochs['deviant'].get_data() - epochs['standard'].get_data()` solely for visualization purposes (not primary statistics).
- [ ] T021 [US2] Implement `code/extract.py`: Identify peak negative amplitude and corresponding latency in an early-to-mid post-stimulus window at Fz and FCz electrodes from the **Raw Conditions** (FR-004).
- [ ] T022 [US2] Implement `code/extract.py`: If no clear peak is found (amplitude < 2.0 µV or no peak in window), record `NaN` for amplitude/latency and set `peak_detected=false`. **Do NOT exclude the row**; retain the participant record for N_total counting.
- [ ] T023 [US2] Implement `code/extract.py`: Read `results/preprocess_log.txt` (generated by T017). Parse lines matching regex `r'Subject (\w+): Rejected (\d+) epochs'`. Exclude participants with >50% rejected trials from statistical analysis (T027), but log their IDs to `results/excluded_subjects.txt`.
- [ ] T024a [US2] Implement `code/extract.py`: Save raw condition peaks to `results/raw_peaks.csv` with columns: `subject_id`, `condition` (Deviant/Standard), `electrode` (Fz/FCz), `amplitude`, `latency`. This file is required for T027.
- [ ] T024b [US2] Implement `code/extract.py`: Reshape metrics into a **long-format** dataset `results/metrics_long.csv` with columns: `subject_id`, `condition` (Deviant/Standard), `electrode`, `amplitude`, `latency`. This file is required for T030.
- [ ] T024c [US2] Implement `code/extract.py`: Output `results/metrics.csv` (wide format) with columns: `subject_id` (string), `deviant_amplitude` (float), `deviant_latency` (float), `standard_amplitude` (float), `standard_latency` (float), `peak_detected` (boolean), `snr` (float). **SNR Formula**: `abs(peak_amplitude) / std_dev(baseline_window)` where baseline is -200ms to 0ms. **Requirement**: This output satisfies US-2 Independent Test.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison and Visualization (Priority: P3)

**Goal**: Execute paired t-tests with FDR correction on raw conditions (4 comparisons), permutation tests, and generate visualization reports.

**Independent Test**: The script must generate a final report containing a p-value, a Cohen's d value, and PNG images of the ERP waveforms and topographic maps.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [US3] Unit test for FDR correction logic in `tests/unit/test_stats.py`.
- [ ] T026 [US3] Unit test for permutation test logic in `tests/unit/test_stats.py`.
- [ ] T026b [US3] Integration test for visualization generation in `tests/integration/test_viz.py`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement `code/stats.py`: Perform paired-sample t-tests on **Raw Condition Vectors** (Deviant vs Standard) for Amplitude and Latency at Fz and FCz using `scipy.stats.ttest_rel`. This results in multiple comparisons: Amplitude Fz, Amplitude FCz, Latency Fz, Latency FCz. **Input**: Use `results/raw_peaks.csv` (T024a).
- [ ] T028 [US3] Implement `code/stats.py`: Apply False Discovery Rate (FDR) correction for the 4 comparisons using `statsmodels.stats.multitest.multipletests(method='fdr_bh')`.
- [ ] T029 [US3] Implement `code/stats.py`: Perform non-parametric cluster-based permutation test with a sufficient number of permutations to ensure robust statistical inference. using `mne.stats.permutation_cluster_test` on the time x electrode data matrix. **Adjacency**: Generate adjacency matrix using `mne.channels.make_standard_montage` and `get_adjacency_matrix` for the full 32-channel montage.
- [ ] T030 [US3] Implement `code/stats.py`: Fit mixed-effects model with `condition` as fixed effect and `subject` as random effect using `statsmodels` with formula `amplitude ~ condition + (1|subject)`. **Input**: Use `results/metrics_long.csv` (T024b). Output model summary to `results/statistics.json`.
- [ ] T031 [US3] Implement `code/stats.py`: Calculate Cohen's d and confidence intervals for all significant findings using `pingouin.compute_effsize`.
- [ ] T032 [US3] Implement `code/viz.py`: Generate grand-average ERP plots with confidence intervals using `matplotlib`.
- [ ] T033 [US3] Implement `code/viz.py`: Generate topographic maps of the MMN difference (Deviant - Standard) at peak latency using `mne.viz.plot_topomap`.
- [ ] T034 [US3] Output `results/statistics.json` with p-values, effect sizes, permutation results, model summaries, and **prevalence** (count of participants where `peak_detected=true` / total N).
- [ ] T035 [US3] Output `results/plots/*.png` for ERPs and topomaps.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `README.md` and `quickstart.md`.
- [ ] T037 Code cleanup and refactoring for memory efficiency in `code/preprocess.py`.
- [ ] T038 Performance optimization: Ensure total runtime ≤6 hours on GitHub Actions free-tier (SC-004).
- [ ] T039 [P] Additional unit tests for edge cases (missing peaks, download failures) in `tests/unit/`.
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility.

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
- **User Story 2 (P2)**: Depends on US1 completion (requires preprocessed epochs)
- **User Story 3 (P3)**: Depends on US2 completion (requires metrics.csv and raw_peaks.csv)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config before services/scripts
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
Task: "Write test skeleton for download retry logic in tests/unit/test_download.py"
Task: "Write test skeleton for preprocessing pipeline producing valid epochs in tests/integration/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py"
Task: "Implement code/preprocess.py (full pipeline)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify epochs and logs)
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
 - Developer A: User Story 1 (Preprocessing)
 - Developer B: User Story 2 (Extraction) - *Note: Requires US1 data, so sequential in practice unless mock data used for dev*
 - Developer C: User Story 3 (Stats/Viz) - *Note: Requires US2 data*
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
- **Critical Constraint**: All processing must run on CPU-only hardware (GitHub Actions free-tier). No GPU, no quantized models, no large LLMs.
- **Data Integrity**: All results must be derived from real OpenNeuro ds003645 data. No fabrication.
- **Constitution VI Compliance**: Raw data in `data/raw` is NEVER modified. Subsampling (T013) is performed on a COPY.