# Tasks: The Impact of Visual Attention on Recall of Emotional Stimuli in Rapid Visual Sequences

**Input**: Design documents from `/specs/001-visual-attention-recall/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/`). Execute: `mkdir -p data/raw data/processed artifacts/figures artifacts/logs code tests`
- [ ] T002 Initialize Python 3.11 project with dependencies (`projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/requirements.txt`). Include: pandas, numpy, statsmodels, scikit-learn, matplotlib, seaborn, datasets, requests, pytest, pyyaml, black, flake8, isort.
- [ ] T003 [P] Configure linting and formatting tools (`.pre-commit-config.yaml`). Configure black, flake8, isort.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create data directory structure (`data/raw/`, `data/processed/`, `artifacts/figures/`, `artifacts/logs/`)
- [ ] T005 [P] Implement logging infrastructure (`code/__init__.py`, `code/logging_config.py`). Create a logging configuration that sets up a rotating file handler to `artifacts/logs/app.log` with DEBUG level and JSON formatting.
- [ ] T006 [P] Create schema validation contracts (`specs/001-visual-attention-recall/contracts/dataset.schema.yaml`, `specs/001-visual-attention-recall/contracts/model_output.schema.yaml`). Define YAML schemas based on the Key Entities in spec.md. (Depends on data-model artifact being locked)
- [ ] T007 [P] Setup environment configuration management (`.env.example`, `code/config.py`). Define variables: DATA_PATH, RANDOM_SEED, and structure `code/config.py` to load them.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download raw RSVP dataset, extract gaze fixation metrics, and map stimuli to generate a clean analysis-ready CSV.

**Independent Test**: Run preprocessing on a small sample subset of participants. and verify output CSV contains non-null fixation durations, valid valence labels, and matches expected schema without crashing.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement dataset download script with checksum verification in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/download_data.py` (FR-001)
- [ ] T012a [US1] Implement Variable Validation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Parse dataset manifest to verify presence of Eye-tracking (x,y,timestamp), Valence, Recall, STAI. Log missing fields and exit with `ERROR: Variable X missing` if any are absent.
- [ ] T012b [US1] Implement Geometry Calibration in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Extract screen width (px), viewing distance (mm), sampling rate (Hz). Calculate `threshold_pixels_per_frame = (deg/s) * (pixels_per_degree) / (sampling_rate_hz)`. Halt if metadata missing with "ERROR: Cannot calibrate I-VT threshold without screen geometry."
- [ ] T012c [US1] Implement Temporal-Load Check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Verify `stimulus_duration_ms` in metadata. If missing, infer from `frame_count * (1000/fps)`. **If only `ISI` is available and `ISI != duration`, fail with "ERROR: Cannot verify Temporal-Load constraint; ISI does not equal stimulus duration."**
- [ ] T013 [US1] Implement I-VT velocity-threshold algorithm for fixation extraction in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py` (FR-002). Use the calculated pixel-threshold from T012b. Enforce a minimum fixation window of sufficient duration to ensure data validity.
- [ ] T014 [US1] Implement stimulus ID to valence mapping (IAPS/NimStim) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py` (FR-003). Reject unmapped IDs.
- [ ] T015 [US1] Implement STAI score merging and participant filtering in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Exclude participants missing STAI scores and log/report reduced sample size in `artifacts/logs/preprocessing.log`.
- [ ] T016 [US1] Implement trial filtering logic (missing data, blinks) with strict exclusion rules in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`. Exclude trials with >50% missing frames or blink duration >200ms. No imputation permitted.
- [ ] T017 [US1] Generate final analysis-ready CSV (`data/processed/analysis.csv`) with schema validation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/preprocess.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

### Tests for User Story 1

- [ ] T008 [P] [US1] Unit test for I-VT algorithm logic in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_preprocess.py`. Implement `test_ivt_fixation_extraction`: asserts list of fixations with duration > 100ms is returned.
- [ ] T009 [P] [US1] Unit test for stimulus mapping in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_preprocess.py`. Implement `test_stimulus_valence_mapping`: asserts unmapped IDs raise KeyError.
- [ ] T010 [P] [US1] Integration test for full pipeline on sample data in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_integration.py`. Implement `test_full_preprocessing_pipeline`: asserts output CSV has non-null fixation durations and valid valence labels.

---

## Phase 4: User Story 2 - Mixed-Effects Model Execution and Interaction Testing (Priority: P2)

**Goal**: Fit mixed-effects logistic regression and perform likelihood-ratio testing to determine interaction significance.

**Independent Test**: Run model fitting on a simulated dataset with known parameters and verify the likelihood-ratio test correctly identifies the interaction term as significant.

### Implementation for User Story 2

- [ ] T020 [US2] Implement mixed-effects logistic regression model fitting (`recall ~ fixation_duration * valence * trait_anxiety + (1|participant) + (1|stimulus_id)`) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-004). Use 'logit' link, 'bobyqa' optimizer, max_iter high, tolerance to a sufficiently small threshold.
- [ ] T021 [US2] Implement fallback logic for random effects structure if convergence fails in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. If design not fully crossed or convergence fails, retry with formula: `... + (1|participant)` only. Log warning.
- [ ] T022 [US2] Implement Likelihood-Ratio Test (LRT) comparing full vs. reduced model in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-005).
- [ ] T023 [US2] Implement residual diagnostics and overdispersion check in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (FR-007). Report "Convergence: OK" or flag overdispersion if dispersion > 1.2.
- [ ] T023b [US2] Implement Bootstrap Convergence Verification in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`. Run bootstrap samples to measure convergence rate; verify ≥95% convergence (SC-002). Log results.
- [ ] T024 [US2] Implement Monte Carlo power analysis simulation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py` (SC-003). Execute simulation with iterations=1000, alpha=0.05, target effect size f² ≥ 0.15. Report achieved power.
- [ ] T025 [US2] Export model results and diagnostics to JSON (`artifacts/logs/model_results.json`, `artifacts/logs/power_analysis.json`) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/model_fit.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for model convergence diagnostics in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_model_convergence_check`: asserts convergence status is correctly identified.
- [ ] T019 [P] [US2] Unit test for likelihood-ratio test logic in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_model.py`. Implement `test_likelihood_ratio_test`: asserts p-value calculation is correct for known parameters.

---

## Phase 5: User Story 3 - Visualization of Marginal Effects (Priority: P3)

**Goal**: Generate marginal effect plots showing the slope of fixation duration on recall probability for high vs. low anxiety groups.

**Independent Test**: Generate the plot file (PNG) and verify it contains two distinct regression lines with shaded CIs and a legend, running headlessly.

### Implementation for User Story 3

- [ ] T028 [US3] Implement marginal effects calculation for high/low anxiety groups in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`. Calculate slopes and CIs from model coefficients.
- [ ] T029 [US3] Implement plot generation with 95% CI shaded regions and legend in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py` (FR-006).
- [ ] T030 [US3] Ensure headless rendering and disk usage constraints (<500MB) in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`. Set matplotlib backend to 'Agg'. Delete intermediate figures after saving.
- [ ] T031 [US3] Save final plot to `artifacts/figures/marginal_effects.png` in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/code/visualize.py`

**Checkpoint**: All user stories should now be independently functional

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for confidence interval calculation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py`. Implement `test_confidence_interval_calculation`: asserts CI bounds match standard errors.
- [ ] T027 [P] [US3] Integration test for plot generation in `projects/PROJ-484-the-impact-of-visual-attention-on-recall/tests/test_visualize.py`. Implement `test_plot_generation`: asserts PNG file exists, has two lines, shaded regions, and legend.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Create pipeline entry point script (`code/run_pipeline.py`) to orchestrate download -> preprocess -> model -> visualize in sequence, handling errors.
- [ ] T033 [P] Add comprehensive logging to all pipeline stages and verify log rotation
- [ ] T034 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T035 [P] Run full integration test suite and verify all acceptance criteria
- [ ] T036 [P] Validate `quickstart.md` execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (`data/processed/analysis.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2 (`artifacts/logs/model_results.json`)

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
Task: "Unit test for I-VT algorithm logic in tests/test_preprocess.py"
Task: "Unit test for stimulus mapping in tests/test_preprocess.py"

# Launch all implementation tasks for User Story 1 together (after foundation):
Task: "Implement dataset download script in code/download_data.py"
Task: "Implement geometry calibration in code/preprocess.py"
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
   - Developer B: User Story 2 (requires US1 data)
   - Developer C: User Story 3 (requires US2 results)
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
- **Critical Data Constraint**: All data loading tasks MUST fail loudly if real data is not found; no synthetic fallbacks are permitted.
- **Compute Constraint**: Model fitting MUST be CPU-tractable; if GPU is required, the task must specify a scaled-down version for a single Kaggle GPU, not a fabricated CPU approximation.