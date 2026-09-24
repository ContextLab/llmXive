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

## Phase 0: Research & Methodology

**Purpose**: Document methodological shifts and ratify amendments before implementation

- [ ] T000 [GATE: Human Action Required] **Ratify Spec Amendment: ANOVA to Permutation Test**. **Action**: A human researcher MUST ratify the amendment that replaces FR-003 (Repeated-Measures ANOVA) with a Permutation Test. **Execute**: Create `specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md` with the EXACT content below:
```markdown
# Amendment 001: Replacement of FR-003

**Date**: 2026-06-29
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
**Verify**: File exists and contains the text above. **Rationale**: Resolves legal disconnect between spec FR-003 and plan T033. **Note**: This task is a blocking GATE. Implementation tasks (T033) in Phase 5 depend on the COMPLETION of this ratification. **Depends on**: None (Initial Gate).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan. **Execute**: Run `mkdir -p code/{data,stimuli,analysis,viz,tests} data/{raw/stimuli,raw/responses,processed,results} docs`. **Verify**: Directory tree exists exactly as defined in plan.md.
- [ ] T002 Initialize Python project with `projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/requirements.txt`. **Execute**: Create file with exact content:
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
# Python version: >=3.11 (set via environment)
```
- [X] T003 [P] Configure pytest, linting (ruff/flake8), and formatting (black) tools. **Execute**: Create `pyproject.toml` with exact content:
```toml
[tool.black]
line-length = 88
target-version = ['py3']

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
```
- [X] T004 [P] Create `code/config.py` to manage paths, random seeds, and constants. **Execute**: Define variables: `SEED = 42`, `DATA_ROOT = "data"`, `CODE_ROOT = "code"`, `RESULTS_ROOT = "data/results"`.
- [X] T005 [P] Implement `code/__init__.py` and package structure for `data`, `stimuli`, `analysis`, `viz`.
- [X] T007 Create base data models/entities in `code/data/models.py`. Fields: `ImageStimulus` (path, edge_density, entropy, fractal_dim), `ParticipantResponse` (participant_id, session_id, reaction_time, is_correct, timestamp), `AggregatedScore` (participant_id, session_id, d_score, n_trials_valid, status). Implement as Pydantic BaseModel classes.
- [X] T008 [P] Configure logging infrastructure in `code/utils/logging.py`. **Execute**: Set log level to `INFO`, format to `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, output to `logs/app.log`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T016 [P] Implement image validation and error handling in `code/stimuli/validate.py`. Validates *input images* for corruption before batch processing. Skips corrupted files, logs filenames to `logs/validation.log`. **Note**: Must run before T017a-1. **Execute**: Create script that iterates `data/raw/stimuli/`, attempts to open each image, and writes valid/invalid status to `logs/validation.log`. **Verify**: Run script on a mix of valid/corrupt images; verify `logs/validation.log` contains correct entries.

- [X] T013 [P] Implement edge density (Canny) in `code/stimuli/metrics.py`. **Parameters**: Canny thresholds (low=50, high=150), kernel size=3. **Note**: Must complete before T017a-2.
- [X] T014 [P] Implement entropy of grayscale histograms in `code/stimuli/metrics.py`. **Note**: Must complete before T017a-2.
- [X] T015 [P] Implement fractal dimension via box-counting in `code/stimuli/metrics.py`. **Parameters**: Box sizes: `box_sizes` will be varied across a range of scales. **Edge Case Handling**: If calculation fails or value is out of range [1.0, 3.0], clamp to nearest valid boundary (1.0 or 3.0), log the filename and reason to `logs/manual_review.log`, and assign the clamped value. **DO NOT raise ValueError**. **Note**: Must complete before T017a-2.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Complexity Quantification (Priority: P1) 🎯 MVP

**Goal**: Compute objective visual complexity metrics (edge density, entropy, fractal dimension) for background images and categorize them into Low and High complexity (Median Split).

**Independent Test**: Run the script on a solid color image and a noise image; verify noise scores are strictly higher.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for edge density: `test_edge_density_solid_vs_noise` in `tests/test_stimuli/test_metrics.py`. **Assertion**: Solid image score < Noise image score.
- [X] T010 [P] [US1] Unit test for entropy: `test_entropy_solid_vs_noise` in `tests/test_stimuli/test_metrics.py`. **Assertion**: Solid image score < Noise image score.
- [X] T011 [P] [US1] Unit test for fractal dimension: `test_fractal_dimension_clamping` in `tests/test_stimuli/test_metrics.py`. **Assertion**: Out-of-range input returns clamped value and logs to `logs/manual_review.log`.
- [X] T012 [P] [US1] Integration test for full pipeline: `test_complexity_pipeline` in `tests/test_stimuli/test_pipeline.py`. **Assertion**: Output CSV has correct columns and categories.

### Implementation for User Story 1

- [ ] T017a-1 [US1] Read validation log and filter valid images. **Execute**: Check if `logs/validation.log` exists. If NOT, run T016 to create it. If YES, read it. Iterate `data/raw/stimuli/`. For each file, check validity status. **Verify**: Output list of valid/invalid files to `data/processed/valid_images_list.txt`. **Depends on**: T016.
- [ ] T017a-2 [US1] Compute metrics for valid images. **Execute**: Read `data/processed/valid_images_list.txt`. **WAIT FOR COMPLETION** of T013, T014, T015 (parallel block). For each valid image, run T013, T014, T015. **Verify**: Output `data/processed/complexity_metrics_raw.csv` with columns: `filename`, `edge_density`, `entropy`, `fractal_dim`. **Depends on**: T013, T014, T015, T017a-1.

- [ ] T032 [US1] **REVISION**: Implement PCA dimensionality check in `code/analysis/pca.py` (verify metric construct validity). **Justification**: Required by Plan.md "Complexity Tracking" section to avoid cherry-picking a single metric (Methodology Concern 07f04f81). **Input**: Read 3 metrics from `data/processed/complexity_metrics_raw.csv`. **Output**: Write `data/results/pca_variance.json` with cumulative variance. **Warning Logic**: If cumulative variance < 0.8, write `{"status": "warning", "message": "Low variance"}` to `data/results/pca_variance.json`. **DO NOT raise ValueError or halt pipeline**. **Verify**: File exists with status field. **CRITICAL**: This task MUST run BEFORE T017a-3 to ensure multivariate validation precedes categorization. **Depends on**: T017a-2.

- [ ] T017a-3 [US1] **REVISION**: Write final complexity scores CSV. **Execute**: Read `data/processed/complexity_metrics_raw.csv`. **Verify** that T032 (PCA) has completed. Apply **Median Split (q=2)** to `edge_density` to assign `complexity_category` ('Low', 'High'). **Output**: `data/processed/complexity_scores.csv` with columns: `filename`, `edge_density`, `entropy`, `fractal_dim`, `complexity_category`. **CRITICAL**: Do NOT include `participant_id` or `session_id` here. **Verify**: File exists, categories are balanced (approx 50/50), and median split logic is correct. **Depends on**: T017a-2, T032.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Experimental Data Collection and D-Score Aggregation (Priority: P2)

**Goal**: Aggregate raw IAT response times into valid D-scores per session using Greenwald D2 algorithm.

**Independent Test**: Simulate two IAT sessions for a synthetic participant; verify D-scores match expected values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for D-score calculation: `test_d_score_greenwald_d2` in `tests/test_data/test_process.py`. **Assertion**: Synthetic input yields expected D-score within 0.001 tolerance.
- [X] T020 [P] [US2] Unit test for trial filtering: `test_trial_filtering_latency_bounds` in `tests/test_data/test_process.py`. **Assertion**: Trials <300ms or >10000ms are excluded.
- [X] T021 [P] [US2] Unit test for participant exclusion: `test_insufficient_trials_exclusion` in `tests/test_data/test_process.py`. **Assertion**: Participant with <10 trials is flagged as NaN.

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement trial filtering logic (latency bounds, error handling) in `code/data/process.py`. **Thresholds**: Remove trials <300ms or >10000ms.
- [X] T023 [P] [US2] Implement Greenwald D2 algorithm for D-score aggregation in `code/data/process.py`. **Logic**: Use standard D formula (Greenwald et al., year).
- [X] T026a [US2] [P] Create `code/data/load.py` to load raw response logs (support synthetic `--null-effect` mode for CI). **Constraint**: If `--null-effect` flag is NOT set and real data files are missing, raise `RuntimeError` immediately. **Depends on**: (None - independent).
- [ ] T027a [US2] [P] **REVISION**: Generate `data/processed/counterbalance_assignment.csv` mapping participant IDs to session orders. **Schema**: `participant_id` (str), `session_order` (str: "Low-High" or "High-Low"), `stimulus_set_id` (str: "SetA" or "SetB"). **Action**: This task MUST execute for ALL runs (both real data and synthetic `--null-effect` mode) to ensure session-order metadata is always available. **CLI**: Accept `--split-ratio` argument (default balanced allocation) to determine the ratio of participants starting with Low vs High. **Algorithm**: Seeded random shuffle (seed=42) assigning `session_order` and `stimulus_set_id` such that SetA maps to Low-High and SetB maps to High-Low (or vice versa, consistent with counterbalancing). **Note**: Synthetic data strictly for CI; real data requires this metadata. **Depends on**: (None - independent metadata generation).
- [ ] T027b [US2] Log the specific counterbalancing assignment strategy used in `logs/counterbalance_strategy.log`. Verify file exists and contains the seed and split ratio. **Depends on**: T027a.
- [ ] T026b-1 [US2] [P] Filter raw trials. **Execute**: Read raw response logs via T026a. Apply T022 (latency bounds). **Verify**: Output `data/processed/filtered_trials.csv`. **Depends on**: T022, T026a.
- [ ] T026b-2 [US2] [P] Calculate D-scores. **Execute**: Read `data/processed/filtered_trials.csv`. Apply T023 (Greenwald D2). **Verify**: Output `data/processed/d_scores_raw.csv` with `participant_id`, `session_id`, `d_score`, `n_trials_valid`. **Depends on**: T023, T026b-1.
- [ ] T026b-3 [US2] **REVISION**: Aggregate and join complexity. **Execute**: Read `data/processed/d_scores_raw.csv`. **THEN** Join with `data/processed/counterbalance_assignment.csv` (T027a) using `participant_id` to determine `session_order` and `stimulus_set_id`. **THEN** Join with `data/processed/complexity_scores.csv` (T017a-3) using `stimulus_set_id` (mapped from filename logic or explicit set ID in T027a) to assign `complexity_condition` (Low/High). **Logic**: Exclude participants with <10 valid trials. **Output**: `data/processed/aggregated_d_scores.csv` with columns: `participant_id`, `session_id`, `complexity_condition`, `d_score`, `n_trials_valid`, `status`. **Verify**: Output schema matches spec, `status` flags NaN for <10 trials, and **explicitly log the number of rows successfully joined** to `logs/join_report.log`. **Depends on**: T026b-2, T027a, T017a-3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Permutation Test (with LOIO sensitivity) and generate publication-quality plots.

**Independent Test**: Run analysis on pre-generated dataset; verify p-value, effect size, and plots match expected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for Permutation Test logic: `test_permutation_test_null_distribution` in `tests/test_analysis/test_permutation.py`. **Assertion**: Null distribution mean approximates zero.
- [X] T029 [P] [US3] Unit test for Sensitivity Analysis (threshold sweep): `test_threshold_sweep_logic` in `tests/test_analysis/test_permutation.py`. **Assertion**: Sweep points are generated correctly.
- [X] T030 [P] [US3] Unit test for Leave-One-Image-Out (LOIO) logic: `test_loio_logic` in `tests/test_analysis/test_permutation.py`. **Assertion**: One image exclusion yields correct p-value.
- [X] T031 [P] [US3] Integration test for full analysis pipeline: `test_full_analysis_pipeline` in `tests/test_analysis/test_pipeline.py`. **Assertion**: Output files exist and contain expected keys.

### Implementation for User Story 3

- [X] T033 [US3] **REVISION**: Implement Permutation Test in `code/analysis/permutation.py`. **Parameters**: `n_permutations=1000`, seed 42, metric = mean difference of D-scores. **Pre-Check**: Verify `amendment-001.md` exists (from T000). If missing, raise `RuntimeError`. **Note**: This task implements the Plan's Permutation Test requirement independently of T000 (Spec Amendment) but requires T000 to be COMPLETED before execution. **Depends on**: T000, T032, T026b-3.

- [ ] T034 [US3] **REVISION**: Calculate effect sizes: Report 'Permutation Effect Size' (Cohen's d) and 'Permutation p-value'. **Methodology**: Calculate `observed_cohen_d` from the mean difference and pooled SD of the D-scores. Calculate `partial_eta2` using a **one-way ANOVA on the D-scores** *solely for effect size estimation*, explicitly noting this does not contradict the Permutation Test (which handles hypothesis testing). **Deliverable**: Write `data/results/permutation_results.json` with keys: `p_value`, `effect_size`, `partial_eta2`, `observed_cohen_d`. **CRITICAL**: Must explicitly include `observed_cohen_d` and `partial_eta2` to support T034b. **Verify**: File exists and contains all four keys. **Depends on**: T033.

- [ ] T035 [US3] **REVISION**: Implement Sensitivity Analysis (Threshold + LOIO). **Logic**:
 1. **Threshold Sweep**: Read `complexity_metrics_raw.csv` to calculate SD of `edge_density`. For each shift (±0.05*SD, ±0.10*SD, ±0.15*SD), re-run analysis. If n < 15 per condition, mark as 'invalid'.
 2. **LOIO**: Exclude one image at a time, re-run permutation test, report p-value variation.
 3. **Combine Results**: Merge both results into a single JSON object.
 **Output**: Write `data/results/sensitivity_results.json` containing both `threshold_sweep` and `loio_results` keys. **Depends on**: T033, T017a-3.

- [ ] T036 [US3] Save results to `data/results/permutation_results.json` and `data/results/sensitivity_results.json`. Dependency: Requires T033, T034, T035. Save results and verify both files exist and contain the expected keys (p_value, effect_size, sensitivity_sweep, loio_results).
- [ ] T037 [US3] Implement publication-quality plotting (Seaborn boxplot, 95% confidence interval error bars, pt font size, viridis palette) in `code/viz/plot.py`. **Parameters**: Figure size (appropriate dimensions), DPI=300, font family='Arial', `confidence_level=0.95`, output path `data/results/d_score_comparison.png`. **Depends on**: T033, T034, T035, T036.
- [ ] T038 [US3] Create `code/main.py` to orchestrate the full pipeline (Load -> Process -> Analyze -> Plot).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, usage examples). **Content**: Create `docs/README.md` (Installation, Usage, Data Format, API Reference) and `docs/usage.md` (Detailed examples). **Verify**: File exists and contains all required sections.
- [ ] T040a [P] **REVISION**: Code cleanup and type hints for `code/data/`. **Execute**: Run `ruff check --fix code/data/` and `mypy code/data/ --strict`. **Verify**: Exit code 0.
- [ ] T040b [P] **REVISION**: Code cleanup and type hints for `code/stimuli/`. **Execute**: Run `ruff check --fix code/stimuli/` and `mypy code/stimuli/ --strict`. **Verify**: Exit code 0.
- [ ] T040c [P] **REVISION**: Code cleanup and type hints for `code/analysis/`. **Execute**: Run `ruff check --fix code/analysis/` and `mypy code/analysis/ --strict`. **Verify**: Exit code 0.
- [ ] T040d [P] **REVISION**: Code cleanup and type hints for `code/viz/`. **Execute**: Run `ruff check --fix code/viz/` and `mypy code/viz/ --strict`. **Verify**: Exit code 0.
- [ ] T041a [US1] Create memory profiling script in `code/utils/profile_memory.py`. **Action**: Script must use `memory_profiler` to measure peak memory usage of the main pipeline. **Verify**: Script exists and can be run independently.
- [ ] T041b [US1] Run profiling and assert memory usage <7GB. **Action**: Execute `python code/utils/profile_memory.py` with synthetic dataset (N=100 participants, 50 images) and assert `peak_memory < 7GB`. **Verify**: Log output confirms memory limit was not exceeded. **Depends on**: T041a, T038, T032.
- [ ] T042 [US2] **REVISION**: Implement strict "fail loud" data loading in `code/data/load.py` that raises an exception if real data is missing, preventing any fallback to synthetic data during production runs. **FAIL CONDITION**: If `--null-effect` flag is NOT set and real data is missing, raise `RuntimeError`. **ALLOWED**: If `--null-effect` flag IS set, synthetic data is permitted for CI.
- [ ] T043a [CI] **REVISION**: Add CI workflow file `.github/workflows/analysis.yml`. **Execute**: Create file with exact content:
```yaml
name: Analysis Pipeline
on: [push, pull_request]
jobs:
  run-analysis:
    runs-on: ubuntu-latest
    timeout-minutes: 360
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
- [ ] T034b [US3] **REVISION**: Implement **Post-Hoc** Power Analysis. **Logic**: Hardcode target effect size (η² = 0.02) and N=60. Use `statsmodels.stats.power.TTestIndPower` to calculate power for N=60 and target eta2. **Output**: Write `data/results/power_analysis.json` with `power_value`, `target` (0.80), `status` (measured). **DO NOT raise RuntimeError**. If power < 0.80, set `status` to "warning" and log the value. **Note**: This is a measurement, not a gate. **Rationale**: Addresses the "Power Analysis" requirement in the Plan's 'Analysis Pipeline' section and 'Complexity Tracking' table. **Depends on**: (None - independent design check).
- [ ] T044 [US3] **REVISION**: Implement robust error handling for the PCA dimensionality check in `code/analysis/pca.py`. **Execute**: Wrap the PCA logic in a try-except block that catches `ValueError` and `RuntimeError`. On error, write `{"status": "error", "message": "<error details>"}` to `data/results/pca_variance.json`. **Verify**: Run `pytest tests/test_analysis/test_pca_error_handling.py` which injects invalid data and asserts the error JSON is written. **Depends on**: T032.
- [ ] T045 [US3] **REVISION**: Add a explicit validation step in `code/main.py` to verify that `data/processed/complexity_scores.csv` contains at least one valid image before proceeding to T032 (PCA). **Execute**: Insert a check in `code/main.py` after T017a-3 completion that raises `ValueError` if the CSV is empty or all rows are 'skipped'. **Verify**: Run `pytest tests/test_main/test_main_empty_data.py` which creates an empty CSV and asserts `ValueError` is raised. **Depends on**: T038.
- [ ] T046 [US2] **REVISION**: Update `code/data/process.py` to explicitly log the number of participants excluded due to insufficient trials (<10) to `logs/exclusion_report.log` with a breakdown by session. **Execute**: Add logging statements in T026b-3 to record `participant_id`, `session_id`, and `reason='insufficient_trials'` for each excluded row. **Verify**: Run pipeline with synthetic data including invalid participants; verify `logs/exclusion_report.log` contains the expected format and counts. **Depends on**: T026b-3.
- [ ] T048 [US1] **REVISION**: Add robust error handling for fractal dimension calculation in `code/stimuli/metrics.py`. **Execute**: Wrap the box-counting algorithm in a try-except block. If the calculation fails (e.g., division by zero, invalid box sizes), log the error to `logs/metrics.log` and assign a `NaN` value to the `fractal_dim` column for that image, rather than crashing the entire batch. **Verify**: Run `pytest tests/test_stimuli/test_fractal_error_handling.py` with a corrupted image input and assert the script continues and outputs `NaN` for that specific metric. **Depends on**: T015.
- [ ] T049 [US3] **REVISION**: Implement explicit handling for the "insufficient participants" edge case in the sensitivity analysis (T035). **Execute**: Ensure the code in `code/analysis/permutation.py` explicitly checks `n < 15` per condition *before* attempting the permutation test. If the threshold is invalid, write a specific entry in `sensitivity_results.json` with `status: "invalid"` and `reason: "n < 15"`, rather than attempting a test with insufficient data and failing silently or with a generic error. **Verify**: Run `pytest tests/test_analysis/test_sensitivity_edge_cases.py` with a dataset that triggers the n<15 condition and assert the JSON output contains the correct status and reason. **Depends on**: T035.
- [ ] T050 [US2] **REVISION**: Add a specific test case for the "missing data for one session" edge case in `code/data/process.py`. **Execute**: Create a unit test in `tests/test_data/test_process.py` that simulates a participant with valid trials in Session A but missing data for Session B. Verify that the aggregation logic correctly flags the missing session's D-score as `NaN` and excludes the participant from the repeated-measures comparison, logging the exclusion count. **Verify**: Run the test and assert the exclusion count is incremented and the D-score is `NaN`. **Depends on**: T026b-3.
