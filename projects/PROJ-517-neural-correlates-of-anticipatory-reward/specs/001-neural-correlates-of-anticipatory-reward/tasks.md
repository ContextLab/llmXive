# Tasks: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

**Input**: Design documents from `/specs/001-neural-correlates-of-anticipatory-reward/`
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

- [ ] T001a [P] Create source code directories: `code/`, `tests/` (relative to project root)
- [ ] T001b [P] Create data directories: `data/raw/`, `data/processed/`, `data/figures/` (relative to project root)
- [ ] T001c [P] Create spec directories: `specs/001-neural-correlates-of-anticipatory-reward/` (relative to project root)
- [ ] T002a [P] Create `code/__init__.py` and `tests/__init__.py`
- [ ] T002b [P] Create `projects/PROJ-517-neural-correlates-of-anticipatory-reward/requirements.txt` with pinned versions: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest
- [ ] T002c [P] Initialize virtualenv in project root: Run `python -m venv.venv`, `source.venv/bin/activate`, and `pip install -r requirements.txt` (Ensure Python 3.10+) <!-- FAILED: unspecified -->
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T006 [P] Create `contracts/dataset.schema.yaml` defining trial_id, neuron_id, spike_timestamps, reward_magnitude, cue_timestamps, spike_sorting_metadata
- [~] T005 Implement synthetic data generator in `code/synthetic_generator.py` adhering to `contracts/dataset.schema.yaml` for CI validation (Depends on T006; Output: `data/raw/synthetic_test.csv` with seed=42)
- [~] T007 Create `contracts/output.schema.yaml` defining expected report structure and plot metadata
- [~] T008 Setup `code/__init__.py` and basic logging configuration in `code/logging_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Load pre-processed spike train data and trial metadata from public repositories (or synthetic source) and align them by trial ID into a unified DataFrame.

**Independent Test**: The pipeline can be tested by running the ingestion script against a small, synthetic dataset containing known spike counts and reward values, verifying that the output DataFrame correctly links each trial's firing rate to its specific reward magnitude.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Implement contract test `tests/contract/test_ingestion_schema.py::test_schema_validates_trial_id`: Assert that input CSV with valid `trial_id` passes schema validation; assert invalid `trial_id` format raises `ValidationError`
- [~] T010 [P] [US1] Implement integration test `tests/integration/test_ingestion_pipeline.py::test_data_alignment`: Load `data/raw/synthetic_test.csv`, run `code/ingestion.py`, assert output DataFrame contains columns `['trial_id', 'neuron_id', 'spike_count', 'reward_magnitude']` and `spike_count.sum() == expected_total`

### Implementation for User Story 1

- [~] T011 [US1] Implement `code/ingestion.py` to load CSV/Neurodata files from `data/raw/` or synthetic generator
- [~] T012 [US1] Implement spike count calculation in `code/ingestion.py`: count spikes in [-500ms, 0ms] window relative to reward (FR-002)
- [~] T013a [US1] Implement validation logic in `code/ingestion.py`: Count trials per reward magnitude level
- [~] T013b [US1] Implement validation logic in `code/ingestion.py`: Check for >= 30 trials per reward magnitude level (FR-007); halt if any level < 30
- [~] T013c [US1] Implement validation logic in `code/ingestion.py`: Handle zero-reward trials (keep as valid) and silent neurons (filter out with log warning)
- [~] T013d [US1] Implement validation logic in `code/ingestion.py`: Check cue-reward delay; if ANY trial has delay < 500ms, FLAG the specific trials and HALT execution ONLY if the number of valid trials drops below 30 per level or if >50% of trials are confounded (FR-009)
- [~] T013e [US1] Implement validation logic in `code/ingestion.py`: Validate upstream spike sorting metadata (SNR/Isolation Distance) and GENERATE `data/processed/spike_sorting_validation_report.md` documenting rejection criteria (SNR > 3, Isolation Distance > 20) (Constitution Principle VI)
- [~] T013f [US1] Implement validation logic in `code/ingestion.py`: Generate `data/processed/validation_report.json` containing data loss metrics (`ingestion_rows_total`, `ingestion_rows_valid`, `ingestion_rows_dropped`) and validation status flags (SC-004)
- [~] T014 [US1] Implement `code/ingestion.py` output: unified Pandas DataFrame with `trial_id`, `neuron_id`, `spike_count`, `reward_magnitude`, `timestamp_relative_to_reward`
- [~] T015 [US1] Implement error handling for missing/malformed metadata files (US-1 Acceptance Scenario 2)
- [~] T016 [US1] Add logging for data loss metrics: `ingestion_rows_total`, `ingestion_rows_valid`, `ingestion_rows_dropped` (SC-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Post-Ingestion Validation (Blocking for US2)

**Purpose**: Calculate metrics required for US2 that depend on the *validated* dataset from US1

- [~] T022a [US2] Implement `code/modeling.py` function to calculate observed variance of `spike_count` from the *validated* dataset (post-T013f) and store in `data/processed/observed_variance.json`

---

## Phase 4: User Story 2 - Statistical Modeling and Significance Testing (Priority: P2)

**Goal**: Fit a Generalized Linear Model (GLM) regressing firing rates on reward magnitude and run a permutation test to validate the coefficient.

**Independent Test**: The analysis module can be tested by running it on a dataset where the reward magnitude is known to have no correlation with firing rates (null data), verifying that the resulting p-value exceeds the significance threshold (e.g., p > 0.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Implement unit test `tests/unit/test_modeling_selection.py::test_glm_selection`: Input data with dispersion=1.5; assert `statsmodels` NegativeBinomial model is returned; Input dispersion=0.9; assert `Poisson` model is returned
- [~] T018 [P] [US2] Implement unit test `tests/unit/test_modeling_permutation.py::test_permutation_null`: Input data with seed=42 and no correlation; assert `p_value > 0.05` after 1000 iterations; The null distribution mean is centered near zero.

### Implementation for User Story 2

- [~] T019 [US2] Implement `code/modeling.py` dispersion check (FR-010) to calculate dispersion parameter
- [~] T020 [US2] Implement `code/modeling.py` model selection: Negative Binomial (dispersion > 1.1) or Poisson (dispersion <= 1.1) (FR-003)
- [~] T021 [US2] Implement `code/modeling.py` GLM fitting: `firing_rate` ~ `reward_magnitude`
- [~] T022 [US2] Implement `code/modeling.py` Power Analysis: Calculate MDES (SC-002) using **final validated sample size** and **observed variance from the filtered dataset** (from T022a); Parameters: power=0.80, alpha=0.05, effect size metric=Cohen's f2; report `mdes_80_power` (Depends on T013f, T022a)
- [~] T023 [US2] Implement `code/modeling.py` Permutation Test: + iterations to generate null distribution and p-value (FR-004, SC-001)
- [~] T024a [US2] Implement `code/modeling.py` Robustness Check: Fit categorical GLM treating `reward_magnitude` as a factor (Plan Complexity Tracking)
- [~] T024b [US2] Implement `code/modeling.py` Robustness Check: Perform Likelihood Ratio Test (LRT) comparing categorical vs linear model; if p < 0.05, flag non-linearity (Plan Complexity Tracking)
- [~] T025 [US2] Implement `code/modeling.py` Cross-Validation: k-fold CV to evaluate predictive performance (FR-008); Calculate and report R2 and MSE on held-out data; also report coefficient stability (cv_score_mean, cv_score_std)
- [~] T026a [US2] Implement `code/modeling.py` Neuron Grouping: Detect, count, and group analyzed neurons from the input DataFrame; report `neuron_count`
- [~] T026b [US2] Implement `code/modeling.py` Multiple Comparisons: Apply Bonferroni correction if `neuron_count` > 1 (SC-005); Depends on T026a
- [~] T027 [US2] Implement `code/modeling.py` Reward Independence Check: Flag if reward is endogenous vs exogenous

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots of firing rate vs. reward magnitude with confidence intervals and a summary statistics report.

**Independent Test**: The reporting module can be tested by generating a plot from a small dataset and verifying that the output image file exists and contains the expected axes labels, data points, and confidence interval bands.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Implement visual regression test `tests/visual/test_plots.py::test_plot_generation`: Generate plot from `data/processed/test_data.csv`; assert output `data/figures/result.png` exists; assert SSIM > 0.95 against reference image `tests/visual/ref/result.png`

### Implementation for User Story 3

- [~] T029 [US3] Implement `code/visualization.py`: Generate scatter plot with `reward_magnitude` (x), `firing_rate` (y), regression line, and 95% CI (FR-005, SC-003)
- [~] T030 [US3] Implement `code/reporting.py`: Generate `summary_report.txt` with coefficient, p-value, MDES, CV scores, and data loss metrics (FR-006)
- [ ] T031 [US3] Implement `code/reporting.py`: Selection Bias Impact Analysis (compare included vs excluded trials)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Integration & Orchestration

**Purpose**: Chain all components into a single executable pipeline

- [ ] T032 [P] Implement `code/main.py` orchestration: Chain Ingestion (T011-T016) -> Validation (T013a-T013f) -> Modeling (T019-T027) -> Visualization (T029) -> Reporting (T030-T031). Ensure strict ordering dependencies are enforced.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `README.md` and `docs/`
- [ ] T034 Code cleanup and refactoring
- [ ] T035 Performance optimization for permutation test on CPU
- [ ] T036a [P] Unit tests for edge cases: zero-reward trials, silent neurons in `tests/unit/test_edge_cases.py`
- [ ] T036b [P] Unit tests for validation logic (FR-007, FR-009) in `tests/unit/test_validation.py`
- [ ] T037 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T006 MUST complete before T005
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Post-Ingestion Validation (Phase 3.5)**: Depends on Phase 3 (US1) completion
 - T022a MUST complete before T022 (MDES)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (aligned DataFrame)
 - T022 specifically depends on T014 (Unified DataFrame) AND T013f (Validation Report) for observed variance
 - T022a explicitly depends on T013f
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T005) can run in parallel (within Phase 2)
- T005 is sequential (depends on T006) and cannot run in parallel with T006
- Once Foundational phase completes, US1 can start immediately
- US2 Modeling tasks (T019-T027) can run in parallel *except* T022 and T022a which must wait for US1 validation
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with dependency awareness)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Implement contract test tests/contract/test_ingestion_schema.py::test_schema_validates_trial_id"
Task: "Implement integration test tests/integration/test_ingestion_pipeline.py::test_data_alignment"

# Launch all models for User Story 1 together:
Task: "Implement spike count calculation in code/ingestion.py"
Task: "Implement validation logic in code/ingestion.py"
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
 - Developer B: User Story 2 (Modeling logic, excluding MDES)
 - Developer C: User Story 3 (Visualization logic)
3. Once US1 completes validation (T013f):
 - Developer B: MDES calculation (T022a, T022)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on free CPU-only CI (no GPU, no 8-bit quantization, no large LLMs). Use `scipy`, `statsmodels`, `scikit-learn` only.
- **Data Integrity**: No fake data generation for final results. Synthetic data is ONLY for pipeline validation (CI). Real data must be fetched from verified URLs (OpenNeuro/Zenodo) or explicitly flagged as missing.