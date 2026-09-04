---
description: "Task list template for feature implementation"
---

# Tasks: Neural Correlates of Anticipatory Reward Processing in Vocal Learning

**Input**: Design documents from `/specs/001-neural-correlates-of-anticipatory-reward/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Research & Data Verification (Mandatory Pre-Implementation)

**Purpose**: Perform critical verification steps defined in plan.md Phase 0 before any code is written.

**⚠️ BLOCKING**: No Phase 1 tasks can begin until Phase 0 is complete and `state/claim_status.json` is initialized.

- [ ] T000a [P] **Dataset Identification (Manual)**: Researcher to search OpenNeuro/Zenodo for a dataset using the query `subject-type:human AND modality:neurophysiology AND task:reward`. **Output**: Write `state/dataset_candidates.json` with fields `dataset_id` (string), `url` (string), `search_query` (string), `verified` (boolean). **Note**: This is a manual research step; code verification follows in T000b.
- [ ] T000b [P] **Dataset Verification**: Verify the candidate URL/dataset_id from T000a. **Input**: `state/dataset_candidates.json` (fields: `dataset_id`, `url`). **Logic**: Fetch dataset metadata and explicitly check for the presence of `spike_sorting_metadata` (SNR, isolation_distance) columns. **Output**: Update `state/dataset_candidates.json` with `verified: true/false` and `missing_columns` (list) if any. **Constraint**: If SNR/isolation_distance are missing, set `verified: false` and halt Phase 0.
- [ ] T000c [P] **Time-Resolved Analysis Check**: Verify if the dataset supports time-binned analysis (PSTH). **Input**: `state/dataset_candidates.json`. **Logic**: Check for `spike_timestamps` granularity and `cue_timestamps` availability. **Output**: If not supported, set `state/claim_status.json` to `{"status": "LIMITED", "reason": "No time-resolved analysis possible"}` and proceed to 'Session-Level Aggregation' mode. If supported, set `status: "SUCCESS"`. **Traceability**: Plan.md Phase 0 Step 3.
- [ ] T000c-B [P] **Generate Time-Resolved Limitation Artifact**: If T000c determines PSTH is unsupported, generate the 'Construct Validity Limitation' note. **Output**: Write `data/processed/construct_validity_limitation.md` with a formal note explaining the switch to 'Session-Level Aggregation' mode and the resulting limitations on temporal analysis. **Dependency**: T000c. **Traceability**: Plan.md Phase 0 Step 3 Fallback Strategy.
- [ ] T000d [P] **Statistical Strategy Definition & Implementation**: Define dispersion check logic (LRT/AIC) and permutation test parameters (SC-001). **Output**: Generate `state/statistical_strategy.md` containing the exact parameters: `alpha=0.05`, `permutation_iterations=1000`, `dispersion_formula=LRT/AIC`. **Constraint**: This task consolidates definition and artifact generation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Initialize Directories and Files**: Create `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/figures/`, `code/__init__.py`, `tests/__init__.py`. **Logic**: `os.makedirs(..., exist_ok=True)`. Verify all exist.
- [ ] T002b [P] Create `projects/PROJ-517-neural-correlates-of-anticipatory-reward/requirements.txt` with pinned versions: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn, pyyaml, pytest
- [ ] T002c [P] **Generate Venv Script**: Create a shell script `scripts/setup_venv.sh` that runs `python -m venv .venv`, `source .venv/bin/activate`, and `pip install -r requirements.txt`. **Logic**: Ensure the script handles errors if Python version < 3.10.
- [ ] T002d [P] **Execute Venv Script**: Run `scripts/setup_venv.sh` to initialize the virtual environment. **Logic**: If `requirements.txt` is missing, exit with code 1.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Checkpoint**: All contracts (T003a, T006), Data Model (T018), and Synthetic Generator (T005a, T005a-Run) must be complete. T005b (Run Synthetic Generator) is a hard prerequisite for Phase 3 tasks like T010.

- [ ] T003a [P] **Create Dataset Schema**: Create `contracts/dataset.schema.yaml` defining `trial_id` (string), `neuron_id` (string), `spike_time_ms` (float), `cue_time_ms` (float), `reward_magnitude` (float), `snr` (float), `isolation_distance` (float). **Schema**: Use flat float columns for timestamps to support streaming. **Note**: Updated from `array[float]` to `float` for streaming compatibility. **Traceability**: Plan.md Phase 1 Step 1.
- [ ] T005a [P] **Implement Synthetic Generator Logic**: Implement `code/synthetic_generator.py` adhering to `contracts/dataset.schema.yaml` for CI validation. **Columns**: `trial_id`, `neuron_id`, `spike_time_ms` (float, generated via Poisson process lambda=50Hz, seed=42), `cue_time_ms` (float), `reward_magnitude`, `snr`, `isolation_distance`. **Requirement**: Do NOT use JSON stringified arrays; use flat float columns. **Algorithm**: Generate spikes using `numpy.random.poisson` scaled to milliseconds. **Traceability**: Staged Simplification - Spec requires `Array` but we use `float` for CPU streaming; future adapter required if strict array compliance needed. **Dependency**: T003a.
- [ ] T005a-Adapter [P] **Implement Schema Adapter**: Implement `code/schema_adapter.py` to handle the conversion from `spike_timestamps` (Array, Spec) to `spike_time_ms` (float, Task). **Logic**: If input data contains `spike_timestamps` as an array, flatten it to `spike_time_ms` before processing. **Traceability**: Resolves spec contradiction for T005a.
- [ ] T005a-Run [P] **Run Synthetic Generator**: Execute `code/synthetic_generator.py` to produce `data/raw/synthetic_test.csv` with seed=42. **Dependency**: T005a.
- [ ] T006 [P] Create `contracts/output.schema.yaml` defining expected report structure and plot metadata. **Structure**: `validation_report.json`, `spike_sorting_validation_report.md`, `summary_report.txt`, `figures/*.png`. **Traceability**: Plan.md Phase 1 Step 1.
- [X] T008 [P] Setup `code/__init__.py` and basic logging configuration in `code/logging_config.py`
- [ ] T018 [P] **Generate Data Model**: Create `specs/001-neural-correlates-of-anticipatory-reward/data-model.md` based on `contracts/dataset.schema.yaml` (T003a) and spec. **Output**: `data-model.md` with field types, units (ms, spikes/sec), and constraints. **Traceability**: Aligns with Plan.md Phase 1 remediation step. **Dependency**: T003a, T006.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Load pre-processed spike train data and trial metadata from public repositories (or synthetic source) and align them by trial ID into a unified DataFrame.

**Independent Test**: The pipeline can be tested by running the ingestion script against a small, synthetic dataset containing known spike counts and reward values, verifying that the output DataFrame correctly links each trial's firing rate to its specific reward magnitude.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Implement contract test `tests/contract/test_ingestion_schema.py::test_schema_validates_trial_id`: Assert that input CSV with valid `trial_id` passes schema validation; assert invalid `trial_id` format raises `ValidationError`
- [ ] T009b [P] [US1] Implement general contract test `tests/contract/test_schemas.py::test_schemas_validates`: Validate `contracts/dataset.schema.yaml` (T003a) and `contracts/output.schema.yaml` (T006) against generated data (T005a-Run) and output (T014). **Dependency**: T003a, T006, T005a-Run.
- [ ] T010 [P] [US1] Implement integration test `tests/integration/test_ingestion_pipeline.py::test_data_alignment`: Load `data/raw/synthetic_test.csv`, run `code/ingestion.py`, assert output DataFrame contains columns `['trial_id', 'neuron_id', 'spike_count', 'reward_magnitude']` and `spike_count.sum() == expected_total`. **Fix**: Ensure test explicitly calls `code/synthetic_generator.py` to create the input file if it does not exist, preventing "file missing" errors. **Dependency**: T005a-Run.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/ingestion.py` to load CSV/Neurodata files from `data/raw/` or synthetic generator
- [X] T012 [US1] Implement spike count calculation in `code/ingestion.py`: Count spikes in the specific window `[-500ms, 0ms]` relative to reward timestamp (FR-002). **Logic**: Filter rows where `spike_time_ms` is within `reward_time_ms - 500` and `reward_time_ms`. **Format**: Expect `spike_time_ms` as a float column, not JSON string.
- [X] T012b [US1] Implement `code/ingestion.py` to calculate `cue_delay`: Derive `cue_delay` as `reward_time_ms - cue_time_ms` for each trial. **Requirement**: Add `cue_delay` to the unified DataFrame. **Validation**: If `cue_time_ms` is missing or array-based, flag a 'Construct Validity Limitation' and halt if not in 'Session-Level Aggregation' mode. **Traceability**: Addresses the data dependency gap for T023 (GLM covariate).
- [X] T013a [US1] Implement validation logic in `code/ingestion.py`: Count trials per reward magnitude level
- [X] T013b [US1] Implement validation logic in `code/ingestion.py`: Check for >= 30 trials per reward magnitude level (FR-007); halt if any level < 30
- [X] T013c [US1] Implement validation logic in `code/ingestion.py`: Handle zero-reward trials (keep as valid) and silent neurons (filter out with log warning)
- [ ] T013e [US1] **Implement Validation & Reporting (Consolidated)**: Implement `code/ingestion.py` logic to:
    1. Validate upstream spike sorting metadata (SNR/Isolation Distance). Filter trials where `snr <= 3` OR `isolation_distance <= 20`.
    2. Generate `data/processed/spike_sorting_validation_report.md` with headers: "Rejection Criteria", "Rejected Trials", "Acceptance Rate".
    3. Generate `data/processed/validation_report.json` containing data loss metrics (`ingestion_rows_total`, `ingestion_rows_valid`, `ingestion_rows_dropped`), `validated_sample_size`, and `confounded_trial_count`. Calculate `confounded_trial_count` as trials with cue-reward delay <500ms. Add `confounded` boolean column to output DataFrame and write `flagged_trial_ids` to report.
    4. **State Updates**:
        - If `snr`/`isolation_distance` missing: Set `state/claim_status.json` to `{"status": "REJECTED", "reason": "Missing spike sorting metadata"}`.
        - If `cue_time_ms` missing: Set `status` to `{"status": "LIMITED", "reason": "No time-resolved analysis possible"}`.
        - If `confounded_trial_count > 0`: Set `status` to `{"status": "LIMITED", "reason": "Confounded trials detected"}`. **Note**: Does not halt pipeline, but blocks 'Neural Correlates' claim generation.
        - If Valid: Set `status` to `SUCCESS`.
    5. **Fallback Artifacts**:
        - If `status` is "REJECTED": Generate `data/processed/descriptive_stats_only.md` with a formal rejection note stating the claim is invalid due to missing metadata.
        - If `status` is "LIMITED": Generate `data/processed/descriptive_stats_only.md` with a formal limitation note.
    **Traceability**: Plan.md Phase 0 Step 2 (Metadata Check), SC-004 (Data Loss), FR-007 (Trial Count), FR-009 (Cue Delay).
- [X] T014 [US1] Implement `code/ingestion.py` output: unified Pandas DataFrame with `trial_id`, `neuron_id`, `spike_count`, `reward_magnitude`, `timestamp_relative_to_reward`, `cue_delay`, `confounded`
- [ ] T015 [US1] Implement error handling for missing/malformed metadata files (US-1 Acceptance Scenario 2)
- [ ] T017 [US1] Implement `code/data_loader.py` with `load_real_data()` function that fetches from OpenNeuro/Zenodo using `datasets.load_dataset()` or `hf_hub_download()` with `streaming=True` for large files. **Input**: `state/dataset_candidates.json` (fields: `dataset_id`, `url`). **Logic**: Check `os.getenv('CI') == 'true'`. If True, allow fallback to `code/synthetic_generator.py` and log a warning. **Crucial**: If `CI=true`, set `state/data_source_status.json` to `{"status": "success", "source": "synthetic", "is_final": false, "claim_eligible": false}`. If False (Production), raise `FileNotFoundError` immediately on fetch failure with message "Real data fetch failed. No synthetic fallback allowed in production. Please manually upload data to data/raw/". **Constraint**: NO synthetic fallback in production. The function MUST fail loudly. **Artifact**: Write `state/data_source_status.json` with `status` (success/failure), `source`, `is_final`, and `claim_eligible`. **Traceability**: Plan.md Phase 0 fallback strategy for missing file (REJECT status). **Note**: Metadata validation logic is handled in T013e, not T017.
- [ ] T017c [US1] **Fallback Artifact Generation (REJECTED)**: If T013e sets status to "REJECTED", generate `data/processed/descriptive_stats_only.md` with a formal rejection note stating the claim is invalid due to missing metadata. **Traceability**: Plan.md Phase 0 Fallback Strategy (REJECT condition). **Dependency**: T013e.
- [ ] T017b [US1] **Fallback Artifact Generation (LIMITED)**: If T013e sets status to "LIMITED", generate `data/processed/descriptive_stats_only.md` with a formal limitation note. **Traceability**: Plan.md Phase 0 Fallback Strategy. **Dependency**: T013e.
- [ ] T044b [P] **Verified Data Source Initialization**: Ensure `state/verified_data_source.json` exists. **Logic**: If not present, write `{"status": "NO_VERIFIED_SOURCE"}`. **Content**: Explicit JSON content to be written. **Dependency**: None.
- [ ] T044 [P] [US1] Implement `code/ingestion.py` logic to detect and utilize a "VERIFIED REAL DATA SOURCE" block from execution feedback if present, overriding any guessed URLs or package IDs. **Input**: `state/verified_data_source.json`. **Requirement**: If `state/verified_data_source.json` exists AND its status is NOT "NO_VERIFIED_SOURCE", load the `package_id` and `access_recipe` from it and use that exclusively; do not attempt to fetch from OpenNeuro/Zenodo directly. **Artifact**: Update `state/data_source_status.json` to reflect the verified source usage. **Schema**: `state/verified_data_source.json` must contain `{"package_id": "string", "access_recipe": "string"}`. **Traceability**: Plan.md Phase 0 Step 1 (Dataset Identification).
- [ ] T044c [P] **Manual Upload Instruction Generation**: If `state/verified_data_source.json` is "NO_VERIFIED_SOURCE" and `state/dataset_candidates.json` is missing/failed, generate `docs/MANUAL_DATA_UPLOAD.md` with explicit instructions for the user to manually upload data. **Traceability**: Plan.md Phase 0 requirement for explicit statement. **Dependency**: T044b.
- [ ] T045 [P] [US1] Implement `code/ingestion.py` streaming logic for large datasets: Use `datasets.load_dataset(..., streaming=True)` and iterate in chunks to calculate spike counts and statistics without loading the full dataset into RAM. **Requirement**: Explicitly state the chunking strategy (e.g., `chunk_size=10000`) and the accumulation method (online statistics) in the code comments. **Constraint**: If the full dataset cannot be processed within the compute budget, fall back to a well-defined REAL sample (e.g., `itertools.islice` first N rows) and state the sample size and limitation in `validation_report.json`.
- [ ] T046 [P] [US1] Implement `code/ingestion.py` logic to strictly enforce the "No Synthetic Data for Final Results" rule: If `--data-source` is not `synthetic` and the data fetch fails, raise `FileNotFoundError` immediately. **Requirement**: Ensure no `try/except` block swallows the error or falls back to `generate_synthetic_*()` in production mode (non-CI). **Constraint**: This task addresses the "Fail Loudly" principle to prevent fabrication. **Error Message**: "Real data fetch failed. No synthetic fallback allowed in production. Please manually upload data to data/raw/".
- [ ] T047 [P] [US2] Implement `code/modeling.py` logic to verify that the input data is REAL (not synthetic) before running the final GLM and permutation test. **Requirement**: Check `state/data_source_status.json` for `claim_eligible: true`. If `claim_eligible` is false or source is synthetic, raise `Exception("Final results cannot be generated from synthetic data in production.")`. **Constraint**: This task ensures the "Real data + real results only" rule is enforced at the modeling stage.
- [ ] T048 [P] [US1] Implement explicit sample size declaration in `code/data_loader.py` and `validation_report.json`: When a real dataset is streamed or sampled, the code MUST record the exact number of rows processed (N) and the sampling method (e.g., "streaming", "islice_first_N", "random_seed_42") in `validation_report.json` under `sample_details`. **Requirement**: `sample_details` must be a JSON object: `{"method": "string", "N": int}`. **Logic**: If `streaming=True`, set method to "streaming"; if `itertools.islice`, set to "islice_N". This ensures transparency regarding statistical power and representativeness as per Constitution Principle I and the "Real data + real results only" rule.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: Post-Ingestion Validation (Integrated into Phase 3)

**Purpose**: Calculate metrics required for US2 that depend on the *validated* dataset from US1 and perform mandatory safety checks.

**⚠️ BLOCKING**: Phase 4 cannot start until T022a is marked [X]

- [ ] T022a [US1/Validation] **Calculate Observed Variance**: Implement `code/modeling.py` function to calculate observed variance of `spike_count` from the *validated* dataset (post-T013e) and store in `data/processed/observed_variance.json`. **Input**: Read `validated_sample_size` (int) from `data/processed/validation_report.json`. **Logic**: **Halt Check**: Before calculating variance, read `state/claim_status.json`. If `status == "REJECTED"`, raise `RuntimeError("Pipeline halted due to claim rejection. No modeling permitted.")`. Explicitly verify `validation_report.json` exists and contains valid data before proceeding. **Dependency**: T013e. **Traceability**: Moved from Phase 3.5 to Phase 3 to align with US1 completion.

**Checkpoint**: Safety gates passed; variance calculated. US2 can now proceed.

---

## Phase 4: User Story 2 - Statistical Modeling and Significance Testing (Priority: P2)

**Goal**: Fit a Generalized Linear Model (GLM) regressing firing rates on reward magnitude and run a permutation test to validate the coefficient.

**Independent Test**: The analysis module can be tested by running it on a dataset where the reward magnitude is known to have no correlation with firing rates (null data), verifying that the resulting p-value exceeds the significance threshold (e.g., p > 0.05).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Implement unit test `tests/unit/test_modeling_selection.py::test_glm_selection`: Input data with dispersion=1.5; assert `statsmodels` NegativeBinomial model is returned; Input dispersion=0.9; assert `Poisson` model is returned
- [ ] T020 [P] [US2] Implement unit test `tests/unit/test_modeling_permutation.py::test_permutation_null`: Input data with seed=42 and no correlation; assert `p_value > 0.05` after 1000 iterations; The null distribution mean is centered near zero.

### Implementation for User Story 2

- [ ] T021 [US2] **Dispersion Calculation**: Implement the actual statistical dispersion check (deviance/df or Pearson chi-square) and write result to `data/processed/dispersion_metric.json`. **Dependency**: T022a.
- [ ] T022 [US2] Implement `code/modeling.py` model selection: Negative Binomial (dispersion > 1.1) or Poisson (dispersion <= 1.1) (FR-003). **Dependency**: Must run AFTER T021.
- [ ] T041 [US2] **Collinearity Check**: Implement `code/modeling.py` logic to calculate Variance Inflation Factor (VIF) for `reward_magnitude` and `cue_delay` (if included as covariate). **Logic**: If VIF > 5, **drop predictor** (remove from model formula) and flag in `data/processed/collinearity_report.json` and log a warning. **Output**: Write `adjusted_formula` to `data/processed/collinearity_report.json`. **Requirement**: If a predictor is dropped, re-fit the model using the adjusted formula. **Traceability**: Addresses Plan Complexity Tracking: Collinearity Check. **Dependency**: Must run BEFORE T023 to ensure correct formula is used.
- [ ] T023 [US2] Implement `code/modeling.py` GLM fitting: `firing_rate ~ reward_magnitude + cue_delay` (or adjusted formula from T041). **Input**: Read `adjusted_formula` from `data/processed/collinearity_report.json`. **Requirement**: The formula MUST include `cue_delay` as a covariate to control for timing effects, unless dropped by T041. **Wait for**: T022a (Phase 3) and T041 (Phase 4). **Traceability**: Constitution Principle VII (Statistical Rigor) and Plan.md Phase 2 (Covariate Control).
- [ ] T024 [US2] Implement `code/modeling.py` Power Analysis: Calculate MDES (SC-002) using **final validated sample size** and **observed variance from the filtered dataset** (from T022a); Parameters: power=0.80, alpha=0.05, effect size metric=Cohen's f2; report `mdes_80_power`. **Dependencies**: T013e, T022a. **Traceability**: Plan T037.
- [ ] T025 [US2] Implement `code/modeling.py` Permutation Test: Run **Freedman-Lane** permutation test for significance validation (FR-004, SC-001). **Requirement**: Use Freedman-Lane algorithm to handle covariates correctly. Iterations >= 1000. **Traceability**: Constitution Principle VII (Statistical Rigor) and Plan.md Phase 2 (Freedman-Lane for covariates).
- [ ] T026a [US2] Implement `code/modeling.py` Robustness Check: Fit categorical GLM treating `reward_magnitude` as a factor (Plan Complexity Tracking)
- [ ] T026b [US2] Implement `code/modeling.py` Robustness Check: Perform Likelihood Ratio Test (LRT) comparing categorical vs linear model; if p < 0.05, flag non-linearity (Plan Complexity Tracking)
- [ ] T027 [US2] Implement `code/modeling.py` Cross-Validation: k-fold CV to evaluate predictive performance (FR-008); Calculate and report R2 and MSE on held-out data; also report coefficient stability (cv_score_mean, cv_score_std)
- [ ] T028a [US2] Implement `code/modeling.py` Neuron Grouping: Detect, count, and group analyzed neurons from the input DataFrame; report `neuron_count`
- [ ] T028b [US2] Implement `code/modeling.py` Multiple Comparisons: Apply Bonferroni correction if `neuron_count` > 1 (SC-005); Depends on T028a
- [ ] T029 [US2] Implement `code/modeling.py` Reward Independence Check: Flag if reward is endogenous vs exogenous
- [ ] T049 [P] [US2] Implement MDES sensitivity analysis in `code/modeling.py`: Calculate and report the detectable effect size (MDES) for the *actual* observed variance and sample size, explicitly comparing it to the theoretical MDES calculated at the design phase (T024). **Requirement**: If the actual MDES is significantly larger than the design target (e.g., >1.5x), flag this in `summary_report.txt` as a "Power Limitation".

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatter plots of firing rate vs. reward magnitude with confidence intervals and a summary statistics report.

**Independent Test**: The reporting module can be tested by generating a plot from a small dataset and verifying that the output image file exists and contains the expected axes labels, data points, and confidence interval bands.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Implement visual regression test `tests/visual/test_plots.py::test_plot_generation`: Generate plot from `data/processed/test_data.csv`; assert output `data/figures/result.png` exists; assert SSIM > 0.95 against reference image `tests/visual/ref/result.png`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/visualization.py`: Generate scatter plot with `reward_magnitude` (x), `firing_rate` (y), regression line, and 95% CI (FR-005, SC-003)
- [ ] T032 [US3] Implement `code/reporting.py`: Generate `summary_report.txt` with coefficient, p-value, MDES, CV scores, and data loss metrics (FR-006)
- [ ] T033 [US3] Implement `code/reporting.py`: Selection Bias Impact Analysis (compare included vs excluded trials)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Integration & Orchestration

**Purpose**: Chain all components into a single executable pipeline

- [ ] T034a [P] **Implement Orchestration Logic**: Implement `code/run_pipeline.py` (Orchestration Module). **Logic**: Chain Ingestion (T011-T014, T013e) -> Validation (T013e) -> **T017a, T017b** -> **T022a** -> Modeling (T021-T029, T041) -> Visualization (T031) -> Reporting (T032-T033). **Output**: Write the orchestration logic to `code/run_pipeline.py`. **Dependency**: Depends on T017 implementation.
- [ ] T034b [P] **Execute Pipeline**: Run `code/run_pipeline.py` with error handling. **Logic**: Explicitly call `ingestion.run()`, `validation.run()`, `modeling.calculate_variance()`, `modeling.run()`, `visualization.run()`, `reporting.run()` in sequence. Handle errors between steps and log final status. Ensure strict ordering dependencies are enforced. **Note**: This module is the distinct orchestration entry point as per plan.md project structure. **Dependency**: T034a.
- [ ] T034c [P] Implement `code/main.py` CLI setup: Argument parsing, environment validation, and data source selection logic (Dependencies: T017). **Logic**: Include logic to parse `--data-source` (openneuro, zenodo, synthetic, local) and enforce `--data-source=synthetic` only for CI environments (detected by `CI=true` env var). **Dependency**: Depends on T017 implementation.
- [ ] T004 [P] Implement checksum generation script `code/checksums.py` to compute and store SHA-256 hashes for all files in `data/`, `contracts/`, `specs/`, `state/`, and `code/` into `state/artifact_hashes.json` (Constitution Principle III). **Logic**: Run AFTER T032-T033 (Reporting), T031 (Visualization), and all Phase 0-2 artifacts are generated. **Dependency**: T004 depends on T032, T033, T031, T018, T003a, T006, T000d completion. **Schema**: JSON object where keys are relative file paths and values are SHA-256 hex strings. **Requirement**: Verify that all files to be checksummed exist and are non-empty before computing hashes; skip or log a warning if a file is missing or empty.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `README.md` and `docs/`
- [ ] T036 Code cleanup and refactoring
- [ ] T037 Performance optimization for permutation test on CPU
- [ ] T038a [P] Unit tests for edge cases: zero-reward trials, silent neurons in `tests/unit/test_edge_cases.py`
- [ ] T038b [P] Unit tests for validation logic (FR-007, FR-009) in `tests/unit/test_validation.py`
- [ ] T039 Run `quickstart.md` validation
- [ ] T040 [P] [US1] Implement unit test `tests/unit/test_data_loader.py::test_load_real_data_fails_loudly`: Assert that `load_real_data()` raises `FileNotFoundError` when `os.getenv('CI')` is False and the fetch fails, ensuring no silent synthetic fallback occurs in production (Addresses Constitution Principle II: Verified Accuracy).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - T003a MUST complete before T005a (Serial dependency)
 - T003a, T006 MUST complete before T018 (Data Model)
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Integration (Phase 6)**: Depends on all User Stories completion
 - T004 (Checksums) depends on T032, T033, T031, T018, T003a, T006, T000d
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (aligned DataFrame)
 - T022 specifically depends on T014 (Unified DataFrame) AND T013e (Validation Report) for observed variance
 - T022a explicitly depends on T013e
 - T024 depends on T022a
 - **T023 depends on T012b** (cue_delay calculation) AND **T041** (collinearity check)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T005a) can run in parallel (within Phase 2)
 - T005a is sequential (depends on T003a)
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

1. Complete Phase 0: Research & Data Verification
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (Modeling logic, excluding MDES)
 - Developer C: User Story 3 (Visualization logic)
3. Once US1 completes validation (T013e):
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
- **Constitution Compliance**: T013e must generate the spike sorting report. T017 must align with Plan.md risk mitigation (synthetic fallback allowed in CI). T017b/T017c must implement fallback logic (Session-Level Aggregation) as per Plan.md. T013h addresses the strict confounding check. T044, T045, T046, T047 address the "Real data + real results only" and "Streaming" requirements to prevent fabrication and handle large datasets correctly. T001d addresses the directory creation verification failure. T004 moved to Phase 6 to resolve circular dependency. T023 and T025 updated with traceability notes. T012b added to calculate `cue_delay`.
- **New Revision Concerns**: T040 ensures strict adherence to the "Fail Loudly" principle for data loading. T041 addresses collinearity checks omitted in the initial pass. T013e and T017c now handle the mandatory HALT/REJECT logic for missing metadata or time-resolved data required by Phase 0 research, but now with fallback logic. T013h addresses the strict confounding check. T044, T045, T046, T047 address the "Real data + real results only" and "Streaming" requirements to prevent fabrication and handle large datasets correctly. T001d addresses the directory creation verification failure. T004 moved to Phase 6 to resolve circular dependency. T023 and T025 updated with traceability notes. T048 and T049 address the requirement to explicitly declare sample sizes and power limitations for real data, ensuring no fabrication or ambiguity about statistical power.
- **Phase 0 Requirement**: Phase 0 tasks (T000a-T000d) are mandatory and must be completed before Phase 1.
- **Circular Dependency Resolved**: T004 (Checksums) is in Phase 6 and depends on final artifacts. T005a (Synthetic Generator) is in Phase 2. The note "T005a MUST complete before T004" was a textual error in the dependency notes and has been removed. T004 checksums the final state, which includes T005a's output, which is valid.
- **HALT Logic**: T022a now explicitly checks `state/claim_status.json` and halts if status is "REJECTED", ensuring the pipeline does not proceed with invalid data.
- **Data Format**: T003a and T005a now explicitly use flat float columns (`spike_time_ms`) to support streaming and align with CPU constraints, resolving the JSON stringified array issue.
- **CI vs Production**: T017 explicitly marks CI runs as "validation-only" to prevent misinterpretation of synthetic results as final.
- **Redundancy Removed**: T000b and T000c removed from Phase 0; logic consolidated into T013e. T002a removed. T017a removed (merged into T013e).
- **Schema Alignment**: T003a updated to match flat row format required by T005a and T012.
- **Collinearity Handling**: T041 updated to run before T023 and include dynamic formula adjustment.
- **Verification Logic**: T044 and T044b updated to handle "NO_VERIFIED_SOURCE" state correctly.
- **Statistical Strategy**: T000d added to write strategy file; T021 renamed from T021b to T021.
- **Task ID Conflict**: T003 renamed to T003a to avoid conflict with linting T003.
- **Phase 3.5 Integration**: Phase 3.5 has been removed. T022a is now part of Phase 3 (US1) to align with the logical dependency chain.
- **Traceability**: T024 now references Plan T037. T017c handles the REJECT condition. T044c handles manual upload instructions. T013g fulfills Plan T038.
- **Schema Mismatch Resolution**: T005a-Adapter added to handle conversion from Spec Array to Task Float.
- **Task Consolidation**: T013e-T013h consolidated into T013e to prevent race conditions.
- **Phase 3.5 Removal**: Phase 3.5 section removed; content merged into Phase 3.
- **Dependency Clarification**: Phase 2 Checkpoint updated to explicitly state T005b is a prerequisite for T010.
- **Input/Output Definitions**: All tasks (T000a-T000d, T017, T022a, T041, T023) updated with explicit input/output schemas.
- **Ordering Fixes**: T041 moved before T023; T013e/T013g before T013f/T013h; T044b before T044.
- **Phase 1 Alignment**: T018 moved to Phase 1 to align with Plan.md Phase 1 requirements.
- **Fallback Artifacts**: T017b/T017c explicitly named 'Descriptive Statistics Only' report.
- **Traceability Gap Closed**: T044-T044c linked to Plan.md Phase 0 Step 1.
- **Plan ID Mismatch**: T013g linked to Plan T038.
- **Critical Blockers Resolved**: All critical missing artifacts (T000a-T000d, T003a, T006, T018, T005a) are now explicitly defined and ordered.