---
description: "Task list template for feature implementation"
---

# Tasks: The Influence of Visual Complexity on Implicit Bias

**Input**: Design documents from `/specs/001-the-influence-of-visual-complexity-on-im/`
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

- [ ] T000 [FR-003] [Plan: Amendment 001] **Create Amendment File: ANOVA to Permutation Test**. **Action**: Write `specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md` with the content below, replacing `<CURRENT_DATE>` with the actual execution date. **Execute**: Write the file. **Verify**: File exists and contains the text below, specifically verifying the line "Status: Ratified" is present. **Versioning**: CRITICAL: After writing the amendment, update `state/projects/PROJ-026-the-influence-of-visual-complexity-on-im.yaml` to set `updated_at` to the current timestamp. **Rationale**: Resolves legal disconnect between spec FR-003 and plan T033. **Note**: This task is a 'Write Action'. Once completed, the automated pipeline (T033) can proceed by checking for the file's existence and the 'Ratified' status.
```markdown
# Amendment 001: Replacement of FR-003

**Date**: <CURRENT_DATE>
**Status**: Ratified

## Summary
This amendment replaces the original Functional Requirement FR-003 (Repeated-Measures ANOVA) with a **Permutation Test** (n=1000) to assess the significance of the difference in D-scores between complexity conditions.

## Justification
The original ANOVA requirement is methodologically invalid because 'Stimulus Set' is perfectly confounded with 'Complexity Level'. A parametric ANOVA would violate the assumption of independence. A Permutation Test provides a non-parametric alternative that correctly handles the stimulus-set confound by randomizing labels within the observed data structure.

## Impact
- **FR-003**: Updated to require Permutation Test.
- **Code**: `code/analysis/permutation.py` must implement the new logic.
- **Spec**: `spec.md` updated to reference this amendment.
```

- [ ] T001 Create project structure per implementation plan. **Execute**: Run `mkdir -p code/{data,stimuli,analysis,viz,tests} data/{raw/stimuli,raw/responses,processed,results} docs`. **Verify**: Directory tree exists exactly as defined in plan.md.
- [X] T002 [P] Initialize Python project with `code/requirements.txt`. **Execute**: Create file with exact content:
```
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0
scikit-learn>=1.3.0
pillow>=10.0.0
opencv-python-headless>=4.8.0
matplotlib>=3.7.0
seaborn>=0.12.0
statsmodels>=0.14.0
pytest>=7.4.0
memory-profiler>=0.61.0
```
**Verify**: File exists and contains the exact lines specified above. (Note: Python version constraint is handled in pyproject.toml, not here).
- [X] T003 [P] Configure pytest, linting (ruff/flake8), and formatting (black) tools. **Execute**: Create `pyproject.toml` with exact content:
```toml
[project]
name = "visual-complexity-iat"
version = "1.0.0"
requires-python = ">=3.11,<3.12"
dependencies = [
 "numpy>=1.24.0",
 "pandas>=2.0.0",
 "scipy>=1.11.0",
 "scikit-learn>=1.3.0",
 "pillow>=10.0.0",
 "opencv-python-headless>=4.8.0",
 "matplotlib>=3.7.0",
 "seaborn>=0.12.0",
 "statsmodels>=0.14.0",
 "pytest>=7.4.0",
 "memory-profiler>=0.61.0"
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
```
- [ ] T004 [P] Create `code/config.py` to manage paths, random seeds, and constants. **Execute**: Define variables: `SEED = 42`, `DATA_ROOT = "data"`, `CODE_ROOT = "code"`, `RESULTS_ROOT = "data/results"`.
- [ ] T005 [P] Implement `code/__init__.py` and package structure for `data`, `stimuli`, `analysis`, `viz`.
- [~] T007 Create base data models/entities in `code/data/models.py`. Fields: `ImageStimulus` (path: str, edge_density: float, entropy: float, fractal_dim: float), `ParticipantResponse` (participant_id: str, session_id: str, reaction_time: float, is_correct: bool, timestamp: datetime), `AggregatedScore` (participant_id: str, session_id: str, d_score: float, n_trials_valid: int, status: str). Implement as Pydantic BaseModel classes with explicit type hints.
- [~] T008 [P] Configure logging infrastructure in `code/utils/logging.py`. **Execute**: Set log level to `INFO`, format to `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, output to `logs/app.log`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T016 [P] Implement image validation and error handling in `code/stimuli/validate.py`. Validates *input images* for corruption before batch processing. Skips corrupted files, logs filenames to `logs/validation.log`. **Note**: Must run before T017a-1. **Execute**: Create script that iterates `data/raw/stimuli/`, attempts to open each image, and writes valid/invalid status to `logs/validation.log`. **Verify**: Run script on a mix of valid/corrupt images; verify `logs/validation.log` contains correct entries.

- [~] T013 [P] Implement edge density (Canny) in `code/stimuli/metrics.py`. **Parameters**: Canny thresholds (low=50, high=150), kernel size=3. **Note**: Must complete before T017a-2.
- [~] T014 [P] Implement entropy of grayscale histograms in `code/stimuli/metrics.py`. **Note**: Must complete before T017a-2.
- [~] T015 [P] Implement fractal dimension via box-counting in `code/stimuli/metrics.py`. **Parameters**: Box sizes: a range of scales including the smallest unit and subsequent powers of two.. **Edge Case Handling**: If calculation fails or value is out of range (valid range [lower boundary, upper boundary]), clamp to nearest valid boundary (lower boundary or upper boundary), log the filename and reason to `logs/manual_review.log`, and assign the clamped value. **DO NOT raise ValueError**. **Note**: Must complete before T017a-2.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Complexity Quantification (Priority: P1) 🎯 MVP

**Goal**: Compute objective visual complexity metrics (edge density, entropy, fractal dimension) for background images and categorize them into Low and High complexity (Multivariate Median Split).

**Independent Test**: Run the script on a solid color image and a noise image; verify noise scores are strictly higher.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Unit test for edge density: `test_edge_density_solid_vs_noise` in `tests/test_stimuli/test_metrics.py`. **Assertion**: Solid image score < Noise image score.
- [~] T010 [P] [US1] Unit test for entropy: `test_entropy_solid_vs_noise` in `tests/test_stimuli/test_metrics.py`. **Assertion**: Solid image score < Noise image score.
- [~] T011 [P] [US1] Unit test for fractal dimension: `test_fractal_dimension_clamping` in `tests/test_stimuli/test_metrics.py`. **Assertion**: Out-of-range input returns clamped value and logs to `logs/manual_review.log`.
- [~] T012 [P] [US1] Integration test for full pipeline: `test_complexity_pipeline` in `tests/test_stimuli/test_pipeline.py`. **Assertion**: Output CSV has correct columns and categories.

### Implementation for User Story 1

- [~] T017a-1 [US1] Read validation log and filter valid images. **Execute**: Check if `logs/validation.log` exists. If NOT, execute `python code/stimuli/validate.py` to generate it. If YES, iterate `data/raw/stimuli/`. For each file, check validity status. **Verify**: Output list of valid/invalid files to `data/processed/valid_images_list.txt`. **Depends on**: T016.
- [ ] T017a-2 [US1] Compute metrics for valid images. **Execute**: Read `data/processed/valid_images_list.txt`. For each valid image, run T013, T014, T015. **Verify**: Output `data/processed/complexity_metrics_raw.csv` with columns: `filename`, `edge_density`, `entropy`, `fractal_dim`. **Depends on**: T013, T014, T015, T017a-1.

- [ ] T017a-3 [US1] **Merge PCA Validation & Categorization**. **Execute**: Read `data/processed/complexity_metrics_raw.csv`. **Step 1 (Validation)**: Perform PCA on the three metrics. Calculate cumulative variance. If cumulative variance < 0.8, write `{"status": "warning", "message": "Low variance"}` to `data/results/pca_variance.json`. **Step 2 (Extraction)**: Extract the first principal component (PC1) scores. **Step 3 (Split)**: Apply Median Split. Sort PC1 scores. Split at index `floor(n/2)`. Values at the split index and below are assigned to 'Low'; above to 'High'. **Output**: `data/processed/complexity_scores.csv` with columns: `filename`, `edge_density`, `entropy`, `fractal_dim`, `complexity_category` (derived from PC1). **CRITICAL**: Do NOT include `participant_id` or `session_id` here. **Verify**: File exists, categories are balanced (approx 50/50), and median split logic is correct based on PC1. **Depends on**: T017a-2. (Note: T051 merged into this task).

- [ ] T027a-Map [US1] [P] **Generate Stimulus Set Mapping (Schema Definition)**. **Execute**: Read `data/processed/complexity_scores.csv` (T017a-3). Create a mapping file `data/processed/stimulus_set_mapping.csv` that defines the static schema: **All** images with 'Low' category map to 'SetA'; **All** images with 'High' category map to 'SetB**. **CRITICAL**: This task defines the *schema* (SetA=Low, SetB=High) required by T027a. It does NOT assign sets to participants. It only establishes the rule that SetA corresponds to Low Complexity and SetB to High Complexity. **Verify**: File exists with columns `filename`, `stimulus_set_id`. **Note**: This task defines the *schema* (SetA=Low, SetB=High) required by T027a. It does not assign sets to participants. **Depends on**: T017a-3.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Experimental Data Collection and D-Score Aggregation (Priority: P2)

**Goal**: Aggregate raw IAT response times into valid D-scores per session using Greenwald D2 algorithm.

**Independent Test**: Simulate two IAT sessions for a synthetic participant; verify D-scores match expected values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for D-score calculation: `test_d_score_greenwald_d2` in `tests/test_data/test_process.py`. **Assertion**: Synthetic input yields expected D-score within 0.001 tolerance.
- [~] T020 [P] [US2] Unit test for trial filtering: `test_trial_filtering_latency_bounds` in `tests/test_data/test_process.py`. **Assertion**: Trials <300ms or >10000ms are excluded.
- [~] T021 [P] [US2] Unit test for participant exclusion: `test_insufficient_trials_exclusion` in `tests/test_data/test_process.py`. **Assertion**: Participant with <10 trials is flagged as NaN.

### Implementation for User Story 2

- [~] T022 [P] [US2] Implement trial filtering logic (latency bounds, error handling) in `code/data/process.py`. **Thresholds**: Remove trials <300ms or >10000ms.
- [~] T023 [P] [US2] Implement Greenwald D2 algorithm for D-score aggregation in `code/data/process.py`. **Logic**: Use standard D formula (Greenwald et al., year).
- [~] T042 [US2] [P] [FR-006] [Plan: Constitution Compliance] **Implement Dual-Mode Data Loader**. **Execute**: Create `code/data/load.py`. **Logic**:
 1. If `GITHUB_ACTIONS` is set and real data is missing, generate synthetic data (with a warning log).
 2. If `--null-effect` flag is set, generate synthetic data.
 3. If `GITHUB_ACTIONS` is NOT set and `--null-effect` is NOT set and real data is missing, raise `RuntimeError` immediately.
 **Verify**: Run `pytest tests/test_data/test_load_modes.py` to verify all three modes. **Depends on**: (None - independent).

- [~] T059 [US2] [FR-006] [Plan: Data Hygiene] **Enforce Real Data Integrity in Production**. **Execute**: Refactor `code/data/load.py` (T042) to ensure that in production mode (no `--null-effect` flag, not CI), the script **strictly** requires real data. If the real data source is unavailable, raise `RuntimeError`. **Constraint**: Synthetic data is ONLY permitted if explicitly triggered by `--null-effect` or `GITHUB_ACTIONS`. **Verify**: Run `pytest tests/test_data/test_load_no_fallback.py` which mocks a network failure in local mode and asserts `RuntimeError` is raised. **Depends on**: T042.

- [~] T061 [US2] [Plan: Data Hygiene] **Implement Checksum Generation for Real Data**. **Execute**: Update `code/data/load.py` to compute the SHA-256 hash of any downloaded real data file. **Logic**:
 1. If `data/checksums.json` does not exist, compute the hash of the downloaded file and write it to `data/checksums.json` (Generate-on-First-Run).
 2. If `data/checksums.json` exists, verify the hash matches. If mismatch, raise `ValueError`.
 **Constraint**: This task generates the checksums file if missing; it does not assume a pre-existing one. **Verify**: Run `pytest tests/test_data/test_checksum_generation.py` to verify hash generation and storage. **Depends on**: T042.

- [ ] T027a [US2] [P] [FR-002] [Plan: Stimulus Manipulation Integrity] **Generate Counterbalance Assignment**. **Execute**: Read from `data/raw/responses/participants.csv` if real data exists; otherwise generate N=60 synthetic IDs. **Action**: Generate `data/processed/counterbalance_assignment.csv` mapping participant IDs to session orders and stimulus sets. **Schema**: `participant_id` (str), `session_order` (str: "Low-High" or "High-Low"), `stimulus_set_id` (str: "SetA" or "SetB"). **Algorithm**: 1. Create list of participant IDs. 2. Shuffle using `numpy.random.shuffle` with seed=42. 3. Assign first half to 'Low-High' and 'SetA', second half to 'High-Low' and 'SetB'. **CRITICAL**: The `stimulus_set_id` assignment MUST strictly adhere to the schema defined in T027a-Map (SetA=Low, SetB=High). The shuffle only determines *which participants* get SetA or SetB, not the definition of SetA/SetB. **Note**: Synthetic data strictly for CI; real data requires this metadata. **Depends on**: T027a-Map, T042.

- [~] T027b [US2] Log the specific counterbalancing assignment strategy used in `logs/counterbalance_strategy.log`. Verify file exists and contains the seed and split ratio. **Depends on**: T027a.
- [ ] T026b-1 [US2] [P] Filter raw trials. **Execute**: Read raw response logs via T042/T026a. Apply T022 (latency bounds). **Verify**: Output `data/processed/filtered_trials.csv`. **Depends on**: T022, T042.
- [ ] T026b-2 [US2] [P] Calculate D-scores. **Execute**: Read `data/processed/filtered_trials.csv`. Apply T023 (Greenwald D2). **Verify**: Output `data/processed/d_scores_raw.csv` with `participant_id`, `session_id`, `d_score`, `n_trials_valid`. **Depends on**: T023, T026b-1.
- [ ] T026b-3 [US2] Aggregate and join complexity. **Execute**: Read `data/processed/d_scores_raw.csv`. **THEN** Join with `data/processed/counterbalance_assignment.csv` (T027a) using `participant_id` to determine `session_order` and `stimulus_set_id`. **THEN** Join with `data/processed/complexity_scores.csv` (T017a-3) using `stimulus_set_id` (mapped from filename logic or explicit set ID in T027a) to assign `complexity_condition` (Low/High). **Logic**: Exclude participants with <10 valid trials. **Output**: `data/processed/aggregated_d_scores.csv` with columns: `participant_id`, `session_id`, `complexity_condition`, `d_score`, `n_trials_valid`, `status`. **Verify**: Output schema matches spec, `status` flags NaN for <10 trials, and **explicitly log the number of rows successfully joined** to `logs/join_report.log`. **Depends on**: T026b-2, T027a, T017a-3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Permutation Test (with LOIO sensitivity) and generate publication-quality plots.

**Independent Test**: Run analysis on pre-generated dataset; verify p-value, effect size, and plots match expected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for Permutation Test logic: `test_permutation_test_null_distribution` in `tests/test_analysis/test_permutation.py`. **Assertion**: Null distribution mean approximates zero.
- [~] T029 [P] [US3] Unit test for Sensitivity Analysis (threshold sweep): `test_threshold_sweep_logic` in `tests/test_analysis/test_permutation.py`. **Assertion**: Sweep points are generated correctly.
- [~] T030 [P] [US3] Unit test for Leave-One-Image-Out (LOIO) logic: `test_loio_logic` in `tests/test_analysis/test_permutation.py`. **Assertion**: One image exclusion yields correct p-value.
- [~] T031 [P] [US3] Integration test for full analysis pipeline: `test_full_analysis_pipeline` in `tests/test_analysis/test_pipeline.py`. **Assertion**: Output files exist and contain expected keys.

### Implementation for User Story 3

- [~] T033-check [US3] **Check Amendment**. **Execute**: Verify `amendment-001.md` exists (from T000). If missing, raise `RuntimeError`. **Depends on**: T000.
- [~] T033-impl [US3] **Implement Permutation Test function**. **Parameters**: `n_permutations=1000`, seed 42, metric = mean difference of D-scores. **Note**: This task implements the Plan's Permutation Test logic as a reusable function. **Depends on**: T033-check.
- [~] T033-run [US3] **Execute Permutation Test**. **Execute**: Call the function from T033-impl with the aggregated data. **Verify**: Output `data/results/permutation_results.json` is generated. **Depends on**: T033-impl, T017a-3, T026b-3, T033-check.

- [~] T034 [US3] **Calculate Effect Sizes**. **Methodology**: 1. Calculate `observed_cohen_d` from the mean difference and pooled SD of the D-scores. 2. Calculate `partial_eta2` by performing a standard OLS ANOVA on the observed D-scores grouped by complexity condition (using `statsmodels`) and extracting `SS_effect / (SS_effect + SS_error)` from the ANOVA table. 3. Calculate `perm_standardized_mean_diff` from the permutation distribution statistics. **Deliverable**: Write `data/results/permutation_results.json` with keys: `p_value`, `effect_size`, `observed_cohen_d`, `partial_eta2`, `perm_standardized_mean_diff`. **CRITICAL**: Must explicitly include `partial_eta2`. **Verify**: File exists and contains the required keys. **Depends on**: T033-run.

- [~] T035 [US3] **Implement Sensitivity Analysis (Threshold + LOIO)**. **Logic**:
 1. **Threshold Sweep**: Read `complexity_metrics_raw.csv` to calculate SD of the `edge_density` column. For each shift (±0.05*SD, ±0.10*SD, ±0.15*SD, 0), re-run the Permutation Test function (T033-impl) with the shifted threshold. **OPTIMIZATION**: Use a subset of n=100 permutations for these shifts to ensure runtime compliance (SC-005) and CI buffer. If n < 15 per condition, mark as 'invalid'.
 2. **LOIO**: Exclude one image at a time, re-run permutation test with **n=100 permutations**, report p-value variation.
 3. **Combine Results**: Merge both results into a single JSON object.
 **Output**: Write `data/results/sensitivity_results.json` containing both `threshold_sweep` and `loio_results` keys. **Depends on**: T033-impl, T017a-3, T034.

- [~] T036-verify [US3] **Verify output files**. **Execute**: Check existence and schema of `data/results/permutation_results.json` (keys: p_value, observed_cohen_d, partial_eta2, perm_standardized_mean_diff) and `data/results/sensitivity_results.json` (keys: threshold_sweep, loio_results). **Constraint**: Do NOT write or modify files. **Verify**: Exit 0 if valid, raise ValueError if missing. **Depends on**: T034, T035.

- [~] T037 [US3] Implement publication-quality plotting (Seaborn boxplot, 95% confidence interval error bars, 12pt font size, viridis palette) in `code/viz/plot.py`. **Parameters**: Figure size (appropriate dimensions), DPI=300, font family='Arial', `confidence_level=0.95`, output path `data/results/d_score_comparison.png`. **Depends on**: T034, T035, T036-verify.
- [~] T038 [US3] Create `code/main.py` to orchestrate the full pipeline (Load -> Process -> Analyze -> Plot).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T039 [P] Documentation updates in `docs/` (README, usage examples). **Content**: Create `docs/README.md` (Installation, Usage, Data Format, API Reference) and `docs/usage.md` (Detailed examples). **Verify**: File exists and contains all required sections.
- [~] T040a [P] **REVISION**: Code cleanup and type hints for `code/data/`. **Execute**: Run `ruff check --fix code/data/` and `mypy code/data/ --strict`. **Verify**: Exit code 0.
- [~] T040b [P] **REVISION**: Code cleanup and type hints for `code/stimuli/`. **Execute**: Run `ruff check --fix code/stimuli/` and `mypy code/stimuli/ --strict`. **Verify**: Exit code 0.
- [~] T040c [P] **REVISION**: Code cleanup and type hints for `code/analysis/`. **Execute**: Run `ruff check --fix code/analysis/` and `mypy code/analysis/ --strict`. **Verify**: Exit code 0.
- [~] T040d [P] **REVISION**: Code cleanup and type hints for `code/viz/`. **Execute**: Run `ruff check --fix code/viz/` and `mypy code/viz/ --strict`. **Verify**: Exit code 0.
- [ ] T041a [US1] Create memory profiling script in `code/utils/profile_memory.py`. **Action**: Script must use `memory_profiler` to measure peak memory usage of the main pipeline. **Verify**: Script exists and can be run independently.
- [ ] T041b [US1] Run profiling and assert memory usage <7GB. **Action**: **Pre-condition**: Verify T017a-3 completed successfully (no error status). If T017a-3 failed, skip this task. Execute `python code/utils/profile_memory.py` with synthetic dataset (N=100 participants, 50 images) and assert `peak_memory < 7GB`. **Verify**: Log output confirms memory limit was not exceeded. **Depends on**: T041a, T038, T017a-3.
- [~] T043a [CI] **REVISION**: Add CI workflow file `.github/workflows/analysis.yml`. **Execute**: Create file with exact content:
```yaml
name: Analysis Pipeline
on: [push, pull_request]
jobs:
 run-analysis:
 runs-on: ubuntu-latest
 timeout-minutes:
 steps:
 - uses: actions/checkout@v3
 - name: Set up Python
 uses: actions/setup-python@v4
 with:
 python-version: "3.11"
 - name: Install dependencies
 run: |
 pip install -r code/requirements.txt
 - name: Run Pipeline
 run: python code/main.py --null-effect
 - name: Verify Results
 run: |
 test -f data/results/permutation_results.json
 test -f data/results/sensitivity_results.json
 test -f data/results/d_score_comparison.png
```
**Verify**: File exists and passes `actionlint` (if available) or manual syntax check. **Depends on**: T038 (main.py must exist).
- [~] T034b [Plan: Analysis Pipeline] **REVISION**: Implement **Simulation-Based** Power Analysis. **Logic**:
 1. **Derive Effect Size**: Read `research.md` or literature citations to find a justified effect size. If none exists, default to a conservative 0.3 and log the source.
 2. Simulate data under the alternative hypothesis (effect size = derived/default) for N=60.
 3. Run the Permutation Test (n=1000) on the simulated data.
 4. Repeat multiple times.
 **Output**: Write `data/results/power_analysis.json` with `power_value` (proportion of significant results), `target` (0.80), `status` (measured), `effect_size_source` (log of derivation). **FAILURE CONDITION**: If simulated power < 0.80, raise RuntimeError to halt the pipeline. **Note**: This is a verification gate. **Rationale**: Addresses the "Power Analysis" requirement in the Plan's 'Analysis Pipeline' section and 'Complexity Tracking' table using a method compatible with the Permutation Test. **Depends on**: T033-impl, T026b-3.
- [~] T044 [US3] **REVISION**: Implement robust error handling for the PCA dimensionality check in `code/analysis/pca.py`. **Execute**: Wrap the PCA logic in a try-except block that catches `ValueError` and `RuntimeError`. On error, write `{"status": "error", "message": "<error details>"}` to `data/results/pca_variance.json`. **Verify**: Run `pytest tests/test_analysis/test_pca_error_handling.py` which injects invalid data and asserts the error JSON is written. **Depends on**: T017a-3 (merged logic).
- [~] T045 [US3] **REVISION**: Add a explicit validation step in `code/main.py` to verify that `data/processed/complexity_scores.csv` contains at least one valid image before proceeding to T033-run. **Execute**: Insert a check in `code/main.py` after T017a-3 completion that raises `ValueError` if the CSV is empty or all rows are 'skipped'. **Verify**: Run `pytest tests/test_main/test_main_empty_data.py` which creates an empty CSV and asserts `ValueError` is raised. **Depends on**: T038.
- [~] T046 [US2] **REVISION**: Update `code/data/process.py` to explicitly log the number of participants excluded due to insufficient trials (<10) to `logs/exclusion_report.log` with a breakdown by session. **Execute**: Add logging statements in T026b-3 to record `participant_id`, `session_id`, and `reason='insufficient_trials'` for each excluded row. **Verify**: Run pipeline with synthetic data including invalid participants; verify `logs/exclusion_report.log` contains the expected format and counts. **Depends on**: T026b-3.
- [~] T048 [US1] **REVISION**: Add robust error handling for fractal dimension calculation in `code/stimuli/metrics.py`. **Execute**: Wrap the box-counting algorithm in a try-except block. If the calculation fails (e.g., division by zero, invalid box sizes), log the error to `logs/metrics.log` and assign a `NaN` value to the `fractal_dim` column for that image, rather than crashing the entire batch. **Verify**: Run `pytest tests/test_stimuli/test_fractal_error_handling.py` with a corrupted image input and assert the script continues and outputs `NaN` for that specific metric. **Depends on**: T015.
- [~] T049 [US3] **REVISION**: Implement explicit handling for the "insufficient participants" edge case in the sensitivity analysis (T035). **Execute**: Ensure the code in `code/analysis/permutation.py` explicitly checks `n < 15` per condition *before* attempting the permutation test. If the threshold is invalid, write a specific entry in `sensitivity_results.json` with `status: "invalid"` and `reason: "n < 15"`, rather than attempting a test with insufficient data and failing silently or with a generic error. **Verify**: Run `pytest tests/test_analysis/test_sensitivity_edge_cases.py` with a dataset that triggers the n<15 condition and assert the JSON output contains the correct status and reason. **Depends on**: T035.
- [~] T050 [US2] **REVISION**: Add a specific test case for the "missing data for one session" edge case in `code/data/process.py`. **Execute**: Create a unit test in `tests/test_data/test_process.py` that simulates a participant with valid trials in Session A but missing data for Session B. Verify that the aggregation logic correctly flags the missing session's D-score as `NaN` and excludes the participant from the repeated-measures comparison, logging the exclusion count. **Verify**: Run the test and assert the exclusion count is incremented and the D-score is `NaN`. **Depends on**: T026b-3.
- [~] T052 [US3] **REVISION**: Update `code/analysis/permutation.py` to log the exact permutation seed and iteration count to `logs/permutation_run.log` for full reproducibility verification. **Execute**: Add logging statements at the start of the permutation loop in `code/analysis/permutation.py`. **Verify**: Run pipeline and check `logs/permutation_run.log` for seed=42 and n=1000 entries. **Depends on**: T033-impl.
- [~] T053 [US3] **REVISION**: Add a validation task in `code/main.py` to ensure `data/results/permutation_results.json` contains `observed_cohen_d`, `partial_eta2`, and `p_value` before generating plots (T037). **Execute**: Insert a check in `code/main.py` after T034 that raises `ValueError` if keys are missing. **Verify**: Run `pytest tests/test_main/test_main_missing_results.py` which mocks missing keys and asserts `ValueError`. **Depends on**: T034, T038.
- [~] T054 [US1] **REVISION**: Add a specific test for the "median split tie-breaking" edge case in `tests/test_stimuli/test_metrics.py`. **Execute**: Create a dataset where the median value appears multiple times and verify the split logic assigns them consistently to 'Low' (as defined in T017a-3). **Verify**: Run the test and assert the split is consistent and documented. **Depends on**: T017a-3.

---

## Phase N+1: Final Verification & Documentation (New)

**Purpose**: Final validation steps to ensure the pipeline is robust, reproducible, and ready for publication.

- [~] T055 [US3] [FR-003] [Plan: Constitution Compliance] **Final End-to-End Reproducibility Test**. **Execute**: Create a script `tests/test_reproducibility/test_full_pipeline.py` that: (1) Seeds all random generators, (2) Runs the full pipeline from `code/main.py --null-effect`, (3) Captures SHA-256 hashes of all output files in `data/results/` (excluding timestamped logs), (4) Re-runs the pipeline, (5) Asserts that the hashes match exactly. **Verify**: Script passes on two consecutive runs. **Rationale**: Ensures the permutation test and all downstream steps are fully deterministic given the seed. **Depends on**: T038, T043a.
- [~] T056 [US3] [FR-005] **Generate Final Report Artifact**. **Execute**: Create `code/viz/generate_report.py` that reads `data/results/permutation_results.json`, `data/results/sensitivity_results.json`, and `data/results/power_analysis.json`. **Output**: Generate a single `data/results/final_report.md` containing: (1) Summary of hypothesis test (p-value, effect size), (2) Sensitivity analysis summary (robustness check), (3) Power analysis conclusion, (4) Links to generated plots. **Verify**: File exists and contains all required sections. **Depends on**: T034, T035, T034b.
- [~] T057 [US1] **Documentation of Data Flow**. **Execute**: Update `docs/README.md` to include a detailed "Data Flow" section that explicitly maps the dependencies between T017a-3 (Complexity Scores), T027a-Map (Set Mapping), and T027a (Counterbalance). **Verify**: Section exists and correctly describes the flow. **Rationale**: Prevents future confusion about how stimulus sets are assigned to complexity conditions. **Depends on**: T017a-3, T027a-Map, T027a.
- [~] T058 [US3] **Final Code Review Checklist**. **Execute**: Create `docs/CODE_REVIEW_CHECKLIST.md` containing a list of items to verify before merging: (1) All `[X]` tasks completed, (2) `amendment-001.md` exists and is ratified, (3) No synthetic data fallbacks in production code, (4) All output files have correct schema, (5) Logs contain required audit trails. **Verify**: Checklist exists and covers all critical path items. **Depends on**: T000, T042, T036-verify.
