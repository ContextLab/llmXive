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
- [X] T002a [P] Create `code/__init__.py` and `tests/__init__.py`
- [X] T002b [P] Create `projects/PROJ-517-neural-correlates-of-anticipatory-reward/requirements.txt` with pinned versions: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest
- [X] T002c [P] Initialize virtualenv in project root: Run `python -m venv.venv`, `source.venv/bin/activate`, and `pip install -r requirements.txt` (Ensure Python 3.x+). **Logic**: If `requirements.txt` is missing, exit with code 1. If Python version < 3.10, exit with code 1.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create `contracts/dataset.schema.yaml` defining trial_id, neuron_id, spike_timestamps, reward_magnitude, cue_timestamps, spike_sorting_metadata. **Schema**: `trial_id: string`, `neuron_id: string`, `spike_timestamps: array[integer]`, `reward_magnitude: float`, `cue_timestamps: array[integer]`, `spike_sorting_metadata: object {snr: float, isolation_distance: float}`
- [X] T005 Implement synthetic data generator in `code/synthetic_generator.py` adhering to `contracts/dataset.schema.yaml` for CI validation (Depends on T006; Output: `data/raw/synthetic_test.csv` with seed=42). **Columns**: `trial_id`, `neuron_id`, `spike_timestamps` (JSON stringified array in format '[1,2,3]'), `reward_magnitude`, `cue_timestamps` (JSON stringified array in format '[1,2,3]'), `spike_sorting_metadata` (JSON stringified object with `snr`, `isolation_distance`). **Requirement**: The generator MUST produce `spike_sorting_metadata` as a nested JSON object with keys `snr` and `isolation_distance`, matching the schema exactly. Do not produce flat columns.
- [X] T007 Create `contracts/output.schema.yaml` defining expected report structure and plot metadata. **Structure**: `validation_report.json`, `spike_sorting_validation_report.md`, `summary_report.txt`, `figures/*.png`.
- [X] T008 Setup `code/__init__.py` and basic logging configuration in `code/logging_config.py`
- [X] T004 [P] Implement checksum generation script `code/checksums.py` to compute and store SHA-256 hashes for all files in `data/`, `contracts/`, `specs/`, and `state/` into `state/artifact_hashes.json` (Constitution Principle III). **Logic**: Run after T002b, T005, T006, and T013f. **Dependency**: T004 depends on T005 completion and T013f completion; remove [P] flag. **Schema**: JSON object where keys are relative file paths and values are SHA-256 hex strings.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Load pre-processed spike train data and trial metadata from public repositories (or synthetic source) and align them by trial ID into a unified DataFrame.

**Independent Test**: The pipeline can be tested by running the ingestion script against a small, synthetic dataset containing known spike counts and reward values, verifying that the output DataFrame correctly links each trial's firing rate to its specific reward magnitude.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Implement contract test `tests/contract/test_ingestion_schema.py::test_schema_validates_trial_id`: Assert that input CSV with valid `trial_id` passes schema validation; assert invalid `trial_id` format raises `ValidationError`
- [X] T010 [P] [US1] Implement integration test `tests/integration/test_ingestion_pipeline.py::test_data_alignment`: Load `data/raw/synthetic_test.csv`, run `code/ingestion.py`, assert output DataFrame contains columns `['trial_id', 'neuron_id', 'spike_count', 'reward_magnitude']` and `spike_count.sum() == expected_total`. **Fix**: Ensure test explicitly calls `code/synthetic_generator.py` to create the input file if it does not exist, preventing "file missing" errors.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/ingestion.py` to load CSV/Neurodata files from `data/raw/` or synthetic generator
- [X] T012 [US1] Implement spike count calculation in `code/ingestion.py`: Count spikes in the specific window `[-500ms, 0ms]` relative to reward timestamp (FR-002). **Logic**: Calculate `timestamp_relative_to_reward` for each spike; filter spikes where `-500 <= timestamp_relative_to_reward <= 0`.
- [X] T013a [US1] Implement validation logic in `code/ingestion.py`: Count trials per reward magnitude level
- [X] T013b [US1] Implement validation logic in `code/ingestion.py`: Check for >= 30 trials per reward magnitude level (FR-007); halt if any level < 30
- [X] T013c [US1] Implement validation logic in `code/ingestion.py`: Handle zero-reward trials (keep as valid) and silent neurons (filter out with log warning)
- [X] T013e [US1] Implement validation logic in `code/ingestion.py`: Validate upstream spike sorting metadata (SNR/Isolation Distance) and GENERATE `data/processed/spike_sorting_validation_report.md` documenting rejection criteria. **Logic**: Filter trials where `snr <= 3` OR `isolation_distance <= 20`. **Output**: Markdown report with headers: "Rejection Criteria", "Rejected Trials", "Acceptance Rate". (Constitution Principle VI). **Fix**: Ensure this task is marked as implemented and the report generation logic is present in `code/ingestion.py`.
- [X] T013f [US1] Implement validation logic in `code/ingestion.py`: Generate `data/processed/validation_report.json` containing data loss metrics (`ingestion_rows_total`, `ingestion_rows_valid`, `ingestion_rows_dropped`), `validated_sample_size`, and `confounded_trial_count`. **Logic**: Calculate `confounded_trial_count` as the number of trials with cue-reward delay <500ms. **Persistence**: Ensure file is written to disk.
- [X] T014 [US1] Implement `code/ingestion.py` output: unified Pandas DataFrame with `trial_id`, `neuron_id`, `spike_count`, `reward_magnitude`, `timestamp_relative_to_reward`
- [X] T015 [US1] Implement error handling for missing/malformed metadata files (US-1 Acceptance Scenario 2)
- [X] T017 [US1] Implement `code/data_loader.py` with `load_real_data()` function that fetches from OpenNeuro/Zenodo using `datasets.load_dataset()` or `hf_hub_download()` with `streaming=True` for large files. **Logic**: Check `os.getenv('CI') == 'true'`. If True, allow fallback to `code/synthetic_generator.py` and log a warning. If False (Production), raise `FileNotFoundError` immediately on fetch failure with message "Real data fetch failed. No synthetic fallback allowed in production. Please manually upload data to data/raw/". **Constraint**: NO synthetic fallback in production. The function MUST fail loudly. **Artifact**: Write `state/data_source_status.json` with `status` (success/failure) and `error_message` (if any).
- [X] T018 [US1] Implement `code/main.py` CLI argument parser to accept `--data-source` (openneuro, zenodo, synthetic, local) and enforce `--data-source=synthetic` only for CI environments (detected by `CI=true` env var). **Dependency**: Depends on T017 implementation.
- [X] T013h [US1] Implement validation logic in `code/ingestion.py`: HALT execution and raise `Exception` if `validated_sample_size < 30` OR `confounded_trial_count > 0`. **Logic**: Read `validated_sample_size` and `confounded_trial_count` from `data/processed/validation_report.json` (generated by T013f). If `confounded_trial_count > 0`, raise `Exception("Analysis halted: Found {confounded_trial_count} trials with cue-reward delay <500ms. Neural Correlates claim integrity compromised.")`. **Artifact**: Write `state/claim_status.json` with `status: "REJECTED"` and `reason` if halted.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Post-Ingestion Validation (Blocking for US2)

**Purpose**: Calculate metrics required for US2 that depend on the *validated* dataset from US1 and perform mandatory safety checks.

**⚠️ BLOCKING**: Phase 4 cannot start until T042a, T043a, and T022a are marked [X]

- [X] T042a [US2] Implement `code/ingestion.py` time-resolved analysis check: If the dataset lacks `cue_timestamps` for time-binned PSTH, **HALT** the pipeline and raise `Exception("Construct Validity Limitation: No time-resolved analysis possible. Neural Correlates claim rejected.")`. **Requirement**: Do not continue with session-level aggregation. The claim must be rejected. **Artifact**: Write `state/claim_status.json` with `status: "REJECTED"` and `reason` if halted. **Dependency**: Depends on T013f completion.
- [X] T043a [US2] Implement `code/ingestion.py` spike sorting metadata check: If spike sorting metadata (SNR/Isolation Distance) is missing or insufficient (per T013e), **HALT** the pipeline and raise `Exception("Neural Correlates Claim Restricted: Spike sorting metadata missing. Analysis halted.")`. **Requirement**: Do not append a limitation note and continue. The analysis must be rejected. **Artifact**: Write `state/claim_status.json` with `status: "REJECTED"` and `reason` if halted. **Dependency**: Depends on T013e completion.
- [X] T022a [US2] Implement `code/modeling.py` function to calculate observed variance of `spike_count` from the *validated* dataset (post-T013f) and store in `data/processed/observed_variance.json`. **Input**: Read `validated_sample_size` from `data/processed/validation_report.json`. **Logic**: Explicitly verify `validation_report.json` exists and contains valid data before proceeding. **Dependency**: T022a depends on T042a and T043a completion.

**Checkpoint**: Safety gates passed; variance calculated. US2 can now proceed.

---

## Phase 4: User Story 2 - Statistical Modeling and Significance Testing (Priority: P2)

**Goal**: Fit a Generalized Linear Model (GLM) regressing firing rates on reward magnitude and run a permutation test to validate the coefficient.

**Independent Test**: The analysis module can be tested by running it on a dataset where the reward magnitude is known to have no correlation with firing rates (null data), verifying that the resulting p-value exceeds the significance threshold (e.g., p > 0.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Implement unit test `tests/unit/test_modeling_selection.py::test_glm_selection`: Input data with dispersion=1.5; assert `statsmodels` NegativeBinomial model is returned; Input dispersion=0.9; assert `Poisson` model is returned
- [X] T020 [P] [US2] Implement unit test `tests/unit/test_modeling_permutation.py::test_permutation_null`: Input data with seed=42 and no correlation; assert `p_value > 0.05` after 1000 iterations; The null distribution mean is centered near zero.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/modeling.py` dispersion check (FR-010) to calculate dispersion parameter
- [X] T022 [US2] Implement `code/modeling.py` model selection: Negative Binomial (dispersion > 1.1) or Poisson (dispersion <= 1.1) (FR-003). **Dependency**: Must run AFTER T022a.
- [X] T023 [US2] Implement `code/modeling.py` GLM fitting: `firing_rate ~ reward_magnitude + cue_delay`. **Requirement**: The formula MUST include `cue_delay` as a covariate to control for timing effects (Plan Phase 2).
- [X] T024 [US2] Implement `code/modeling.py` Power Analysis: Calculate MDES (SC-002) using **final validated sample size** and **observed variance from the filtered dataset** (from T022a); Parameters: power=0.80, alpha=0.05, effect size metric=Cohen's f2; report `mdes_80_power`. **Dependencies**: T013f, T022a. **Dependency**: T024 depends on T022a completion.
- [X] T025 [US2] Implement `code/modeling.py` Permutation Test: Run **Freedman-Lane** permutation test for significance validation (FR-004, SC-001). **Requirement**: Use Freedman-Lane algorithm to handle covariates correctly. Iterations >= 1000.
- [X] T026a [US2] Implement `code/modeling.py` Robustness Check: Fit categorical GLM treating `reward_magnitude` as a factor (Plan Complexity Tracking)
- [X] T026b [US2] Implement `code/modeling.py` Robustness Check: Perform Likelihood Ratio Test (LRT) comparing categorical vs linear model; if p < 0.05, flag non-linearity (Plan Complexity Tracking)
- [X] T027 [US2] Implement `code/modeling.py` Cross-Validation: k-fold CV to evaluate predictive performance (FR-008); Calculate and report R2 and MSE on held-out data; also report coefficient stability (cv_score_mean, cv_score_std)
- [X] T028a [US2] Implement `code/modeling.py` Neuron Grouping: Detect, count, and group analyzed neurons from the input DataFrame; report `neuron_count`
- [X] T028b [US2] Implement `code/modeling.py` Multiple Comparisons: Apply Bonferroni correction if `neuron_count` > 1 (SC-005); Depends on T028a
- [X] T029 [US2] Implement `code/modeling.py` Reward Independence Check: Flag if reward is endogenous vs exogenous
- [X] T041 [US2] Implement `code/modeling.py` collinearity check: Calculate Variance Inflation Factor (VIF) for `reward_magnitude` and `cue_delay` (if included as covariate); if VIF > 5, flag in `validation_report.json` and log a warning (Addresses Plan Complexity Tracking: Collinearity Check).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots of firing rate vs. reward magnitude with confidence intervals and a summary statistics report.

**Independent Test**: The reporting module can be tested by generating a plot from a small dataset and verifying that the output image file exists and contains the expected axes labels, data points, and confidence interval bands.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Implement visual regression test `tests/visual/test_plots.py::test_plot_generation`: Generate plot from `data/processed/test_data.csv`; assert output `data/figures/result.png` exists; assert SSIM > 0.95 against reference image `tests/visual/ref/result.png`

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/visualization.py`: Generate scatter plot with `reward_magnitude` (x), `firing_rate` (y), regression line, and 95% CI (FR-005, SC-003)
- [X] T032 [US3] Implement `code/reporting.py`: Generate `summary_report.txt` with coefficient, p-value, MDES, CV scores, and data loss metrics (FR-006)
- [X] T033 [US3] Implement `code/reporting.py`: Selection Bias Impact Analysis (compare included vs excluded trials)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Integration & Orchestration

**Purpose**: Chain all components into a single executable pipeline

- [X] T034a [P] Implement `code/main.py` CLI setup: Argument parsing, environment validation, and data source selection logic (Dependencies: T017, T018)
- [X] T034b [P] Implement `code/main.py` pipeline execution: Chain Ingestion (T011-T018) -> Validation (T013a-T013h) -> **T042a, T043a** -> **T022a** -> Modeling (T021-T029, T041) -> Visualization (T031) -> Reporting (T032-T033). **Logic**: Explicitly call `ingestion.run()`, `validation.run()`, `modeling.calculate_variance()`, `modeling.run()`, `visualization.run()`, `reporting.run()` in sequence. Handle errors between steps and log final status. Ensure strict ordering dependencies are enforced. **Fix**: Mark as [X] and ensure the implementation logic explicitly calls the functions from the previous phases in the correct order, handling errors and logging the final status.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `README.md` and `docs/`
- [X] T036 Code cleanup and refactoring
- [X] T037 Performance optimization for permutation test on CPU
- [X] T038a [P] Unit tests for edge cases: zero-reward trials, silent neurons in `tests/unit/test_edge_cases.py`
- [X] T038b [P] Unit tests for validation logic (FR-007, FR-009) in `tests/unit/test_validation.py`
- [X] T039 Run `quickstart.md` validation
- [ ] T040 [P] [US1] Implement unit test `tests/unit/test_data_loader.py::test_load_real_data_fails_loudly`: Assert that `load_real_data()` raises `FileNotFoundError` when `os.getenv('CI')` is False and the fetch fails, ensuring no silent synthetic fallback occurs in production (Addresses Constitution Principle II: Verified Accuracy).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T006 MUST complete before T005 (Serial dependency)
 - T005 MUST complete before T004 (Serial dependency)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Post-Ingestion Validation (Phase 3.5)**: Depends on Phase 3 (US1) completion
 - T042a, T043a, T022a MUST complete before T022 (Modeling)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (aligned DataFrame)
 - T022 specifically depends on T014 (Unified DataFrame) AND T013f (Validation Report) for observed variance
 - T022a explicitly depends on T013f
 - T024 depends on T022a
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T005, T004) can run in parallel (within Phase 2)
 - T005 is sequential (depends on T006)
 - T004 is sequential (depends on T005, T013f)
- Once Foundational phase completes, US1 can start immediately
- US2 Modeling tasks (T021-T029) can run in parallel *except* T022 and T024 which must wait for US1 validation
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
- **Streaming Requirement**: For large datasets, `code/data_loader.py` MUST use `streaming=True` to process data in chunks, never loading the full dataset into RAM.
- **Fail Loudly**: `code/data_loader.py` MUST raise an exception if real data fetch fails in production; NO synthetic fallback allowed in production runs. CI environments are the only exception.
- **Reproducibility**: All dependencies in `requirements.txt` must be pinned. All data files must be checksummed.
- **Constitution Compliance**: T013e must generate the spike sorting report. T017 must align with Plan.md risk mitigation (synthetic fallback allowed in CI). T042a/T043a must halt on missing data. T013h must halt on any confounded trials.
- **New Revision Concerns**: T040 ensures strict adherence to the "Fail Loudly" principle for data loading. T041 addresses collinearity checks omitted in the initial pass. T042a and T043a address the mandatory HALT/REJECT logic for missing metadata or time-resolved data required by Phase 0 research. T013h addresses the strict confounding check.