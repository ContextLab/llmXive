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

- [ ] T000 [P] **Ratify Spec Amendment: ANOVA to Permutation Test**. **Action**: Create `specs/001-the-influence-of-visual-complexity-on-im/amendment-001.md` explicitly stating that FR-003 (Repeated-Measures ANOVA) is replaced by a Permutation Test to control for stimulus-set confounds, as justified in plan.md. **Verify**: Update `spec.md` to reference this amendment or mark FR-003 as "Amended". **Rationale**: Resolves legal disconnect between spec FR-003 and plan T033.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan. **Execute**: Run `mkdir -p code/{data,stimuli,analysis,viz,tests} data/{raw/stimuli,raw/responses,processed,results} docs`. **Verify**: Directory tree exists exactly as defined in plan.md.
- [ ] T002 Initialize Python project with `projects/PROJ-026-the-influence-of-visual-complexity-on-im/code/requirements.txt`. **Execute**: Create file with exact content:
```
python>=3.11
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
```
- [ ] T003 [P] Configure pytest, linting (ruff/flake8), and formatting (black) tools. **Execute**: Create `pyproject.toml` with exact content:
```toml
[tool.black]
line-length = 88
target-version = ['py']

[tool.ruff]
line-length = 88

[tool.pytest.ini_options]
testpaths = ["tests"]
```
- [ ] T004 [P] Create `code/config.py` to manage paths, random seeds, and constants. **Execute**: Define variables: `SEED = 42`, `DATA_ROOT = "data"`, `CODE_ROOT = "code"`, `RESULTS_ROOT = "data/results"`.
- [ ] T005 [P] Implement `code/__init__.py` and package structure for `data`, `stimuli`, `analysis`, `viz`.
- [ ] T007 Create base data models/entities in `code/data/models.py`. Fields: `ImageStimulus` (path, edge_density, entropy, fractal_dim), `ParticipantResponse` (participant_id, session_id, reaction_time, is_correct, timestamp), `AggregatedScore` (participant_id, session_id, d_score, n_trials_valid, status). Implement as Pydantic BaseModel classes.
- [ ] T008 [P] Configure logging infrastructure in `code/utils/logging.py`. **Execute**: Set log level to `INFO`, format to `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`, output to `logs/app.log`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T016 [US1] Implement image validation and error handling in `code/stimuli/validate.py`. Validates *input images* for corruption before batch processing. Skips corrupted files, logs filenames to `logs/validation.log`. **Pre-requisite**: Must run before T017a-1. **Note**: Placed in Phase 2 as a foundational prerequisite for all US1 tasks, despite [US1] tag indicating its functional domain. **Execute**: Create script that iterates `data/raw/stimuli/`, attempts to open each image, and writes valid/invalid status to `logs/validation.log`. **Verify**: Run script on a mix of valid/corrupt images; verify `logs/validation.log` contains correct entries.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Complexity Quantification (Priority: P1) 🎯 MVP

**Goal**: Compute objective visual complexity metrics (edge density, entropy, fractal dimension) for background images and categorize them into Low and High complexity (Median Split).

**Independent Test**: Run the script on a solid color image and a noise image; verify noise scores are strictly higher.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for edge density calculation in `tests/test_stimuli/test_metrics.py`
- [ ] T010 [P] [US1] Unit test for entropy calculation in `tests/test_stimuli/test_metrics.py`
- [ ] T011 [P] [US1] Unit test for fractal dimension (box-counting) in `tests/test_stimuli/test_metrics.py`
- [ ] T012 [P] [US1] Integration test for full pipeline on sample images in `tests/test_stimuli/test_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement edge density (Canny) in `code/stimuli/metrics.py`. **Parameters**: Canny thresholds (low=50, high=150), kernel size=3. **Note**: Must complete before T017a-2.
- [ ] T014 [US1] Implement entropy of grayscale histograms in `code/stimuli/metrics.py`. **Note**: Must complete before T017a-2.
- [ ] T015 [US1] Implement fractal dimension via box-counting in `code/stimuli/metrics.py` (handle edge cases: clamp value to a valid physical range or raise ValueError if out of bounds). **Parameters**: Box sizes: `box_sizes` will be varied across a range of scales. **Note**: Must complete before T017a-2.
- [ ] T017a-1 [US1] Read metadata and validate images. **Execute**: Read `logs/validation.log` from T016. Iterate `data/raw/stimuli/`. For each file, check validity. **Verify**: Output list of valid/invalid files to `data/processed/valid_images_list.txt`. **Depends on**: T016.
- [ ] T017a-2 [US1] Compute metrics for valid images. **Execute**: Read `data/processed/valid_images_list.txt`. **WAIT FOR COMPLETION** of T013, T014, T015 (parallel block). For each valid image, run T013, T014, T015. **Verify**: Output `data/processed/complexity_metrics_raw.csv` with columns: `filename`, `edge_density`, `entropy`, `fractal_dim`. **Depends on**: T013, T014, T015, T017a-1.
- [ ] T017a-3 [US1] Write final complexity scores CSV. **Execute**: Read `data/processed/complexity_metrics_raw.csv`. Apply **Median Split (q=2)** to `edge_density` to assign `complexity_category` ('Low', 'High'). **Output**: `data/processed/complexity_scores.csv` with columns: `filename`, `edge_density`, `entropy`, `fractal_dim`, `complexity_category`. **CRITICAL**: Do NOT include `participant_id` or `session_id` here. **Verify**: File exists, categories are balanced (approx 50/50), and median split logic is correct. **Depends on**: T017a-2.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Experimental Data Collection and D-Score Aggregation (Priority: P2)

**Goal**: Aggregate raw IAT response times into valid D-scores per session using Greenwald D2 algorithm.

**Independent Test**: Simulate two IAT sessions for a synthetic participant; verify D-scores match expected values within tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for D-score calculation (Greenwald D2) in `tests/test_data/test_process.py`
- [ ] T020 [P] [US2] Unit test for trial filtering (latency <300ms, >10000ms, errors) in `tests/test_data/test_process.py`
- [ ] T021 [P] [US2] Integration test for participant exclusion (<10 valid trials) in `tests/test_data/test_process.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement trial filtering logic (latency bounds, error handling) in `code/data/process.py`. **Thresholds**: Remove trials <300ms or >10000ms.
- [ ] T023 [P] [US2] Implement Greenwald D2 algorithm for D-score aggregation in `code/data/process.py`. **Logic**: Use standard D formula (Greenwald et al., year).
- [ ] T026a [US2] [P] Create `code/data/load.py` to load raw response logs (support synthetic `--null-effect` mode for CI). **Constraint**: If `--null-effect` flag is NOT set and real data files are missing, raise `RuntimeError` immediately. **Depends on**: (None - independent).
- [ ] T027a [US2] [P] Generate `data/processed/counterbalance_assignment.csv` mapping participant IDs to session orders (Low-High vs High-Low) using a seeded random shuffle (seed=42). **Action**: This task MUST execute for ALL runs (both real data and synthetic `--null-effect` mode) to ensure session-order metadata is always available. **CLI**: Accept `--split-ratio` argument (default a moderate baseline) to determine the ratio of participants starting with Low vs High. **Note**: Synthetic data strictly for CI; real data requires this metadata. **Depends on**: (None - independent metadata generation).
- [ ] T027b [US2] Log the specific counterbalancing assignment strategy used in `logs/counterbalance_strategy.log`. Verify file exists and contains the seed and split ratio. **Depends on**: T027a.
- [ ] T026b-1 [US2] [P] Filter raw trials. **Execute**: Read raw response logs via T026a. Apply T022 (latency bounds). **Verify**: Output `data/processed/filtered_trials.csv`. **Depends on**: T022, T026a.
- [ ] T026b-2 [US2] [P] Calculate D-scores. **Execute**: Read `data/processed/filtered_trials.csv`. Apply T023 (Greenwald D2). **Verify**: Output `data/processed/d_scores_raw.csv` with `participant_id`, `session_id`, `d_score`, `n_trials_valid`. **Depends on**: T023, T026b-1.
- [ ] T026b-3 [US2] [P] Aggregate and join complexity. **Execute**: Read `data/processed/d_scores_raw.csv`. **THEN** Join with `data/processed/counterbalance_assignment.csv` (T027a) to determine session order. **THEN** Join with `data/processed/complexity_scores.csv` (T017a-3) to assign `complexity_condition` (Low/High) based on the image set used in that session. **Logic**: Exclude participants with <10 valid trials. **Output**: `data/processed/aggregated_d_scores.csv` with columns: `participant_id`, `session_id`, `complexity_condition`, `d_score`, `n_trials_valid`, `status`. **Verify**: Output schema matches spec, `status` flags NaN for <10 trials. **Depends on**: T026b-2, T027a, T017a-3.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Visualization (Priority: P3)

**Goal**: Perform Permutation Test (with LOIO sensitivity) and generate publication-quality plots.

**Independent Test**: Run analysis on pre-generated dataset; verify p-value, effect size, and plots match expected values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for Permutation Test logic in `tests/test_analysis/test_permutation.py`
- [ ] T029 [P] [US3] Unit test for Sensitivity Analysis (threshold sweep) in `tests/test_analysis/test_permutation.py`
- [ ] T030 [P] [US3] Unit test for Leave-One-Image-Out (LOIO) logic in `tests/test_analysis/test_permutation.py`
- [ ] T031 [P] [US3] Integration test for full analysis pipeline in `tests/test_analysis/test_pipeline.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement PCA dimensionality check in `code/analysis/pca.py` (verify metric construct validity). **Justification**: Required by Plan.md "Complexity Tracking" section to avoid cherry-picking a single metric (Methodology Concern 07f04f81). **Output**: Write `data/results/pca_variance.json` with cumulative variance. **FAIL CONDITION**: If cumulative variance < 0.8, raise `ValueError` and halt pipeline. **Verify**: Cumulative variance > 0.8. **Depends on**: T017a-3 (to read complexity metrics).
- [ ] T033 [US3] Implement Permutation Test in `code/analysis/permutation.py`. **Parameters**: `n_permutations=1000`, seed 42, metric = mean difference of D-scores. **Note**: This task implements FR-003 as ratified by plan override (replacing ANOVA) per T000. **Depends on**: T032, T026b-3.
- [ ] T034 [US3] Calculate effect sizes: Report 'Permutation Effect Size' (Cohen's d) and 'Permutation p-value'. **Supplementary**: Also calculate partial η² for compatibility with FR-004. **Deliverable**: Write `data/results/permutation_results.json` with keys: `p_value`, `effect_size`, `partial_eta2`, `observed_cohen_d`. **CRITICAL**: Must explicitly include `observed_cohen_d` and `partial_eta2` to support T034b. **Depends on**: T033.
- [ ] T034b [US3] Implement **Prospective** Power Analysis. **Logic**: Read target effect size (η² > 0.02) and N=60 from config. Use `statsmodels.stats.power.TTestIndPower` (or equivalent) to calculate power for N=60 and target eta2. **Output**: Write `data/results/power_analysis.json` with `power_value`, `target` (0.80), `status` (pass/fail), `eta2_threshold_met` (boolean). **FAIL CONDITION**: If `power_value < 0.80`, the study design is invalid; raise `RuntimeError` with message "Insufficient power for N=60". **Note**: This task is independent of observed results (T033) and validates study design. **Depends on**: (None - independent design check).
- [ ] T035a [US3] Implement Sensitivity Analysis: Threshold sweep (±0.05, ±0.10, ±0.15 *standard deviations* of the complexity metric distribution). **Logic**: Read `complexity_scores.csv` (from T017a-3) to calculate the standard deviation (SD) of the complexity metric. For each shift (±0.05*SD, ±0.10*SD, ±0.15*SD), re-run analysis. **Exclusion Logic**: For each sweep point, count valid participants. If n < 15 per condition, mark the point as 'invalid' in the JSON output. **Output**: Write `data/results/sensitivity_results.json`. **Depends on**: T033, T017a-3 (explicit dependency on T017a-3 for SD calculation).
- [ ] T035b [US3] Implement Leave-One-Image-Out (LOIO) sensitivity analysis in `code/analysis/permutation.py`. **Logic**: Exclude one image at a time, re-run permutation test, report p-value variation. **Output**: Append results to `data/results/sensitivity_results.json`. **Depends on**: T033.
- [ ] T036 [US3] Save results to `data/results/permutation_results.json` and `data/results/sensitivity_results.json`. Dependency: Requires T033, T034, T035a, and T035b. Save results and verify both files exist and contain the expected keys (p_value, effect_size, sensitivity_sweep, loio_results).
- [ ] T037 [US3] Implement publication-quality plotting (Seaborn boxplot, 95% confidence interval error bars, pt font size, viridis palette) in `code/viz/plot.py`. **Parameters**: Figure size (appropriate dimensions), DPI=300, font family='Arial', `confidence_level=0.95`, output path `data/results/d_score_comparison.png`. **Depends on**: T033, T034, T035a, T035b, T036.
- [ ] T038 [US3] Create `code/main.py` to orchestrate the full pipeline (Load -> Process -> Analyze -> Plot).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, usage examples). **Content**: Create `docs/README.md` (Installation, Usage, Data Format, API Reference) and `docs/usage.md` (Detailed examples). **Verify**: File exists and contains all required sections.
- [ ] T040 Code cleanup and refactoring. **Execute**: Run `ruff check --fix code/` and `mypy code/ --strict`. **Verify**: Exit code 0 for both commands; no `print` statements remain in `code/`. **Criteria**: All functions have type hints. **FAIL CONDITION**: If mypy finds any missing type hints, the task fails.
- [ ] T041a [US1] Create memory profiling script in `code/utils/profile_memory.py`. **Action**: Script must use `memory_profiler` to measure peak memory usage of the main pipeline. **Verify**: Script exists and can be run independently.
- [ ] T041b [US1] Run profiling and assert memory usage <7GB. **Action**: Execute `python code/utils/profile_memory.py` and assert `peak_memory < 7GB`. **Verify**: Log output confirms memory limit was not exceeded. **Depends on**: T041a, T038.
- [ ] T042 [US2] Implement strict "fail loud" data loading in `code/data/load.py` that raises an exception if real data is missing, preventing any fallback to synthetic data during production runs. **FAIL CONDITION**: If `--null-effect` flag is not set and data is synthetic, raise `RuntimeError`.
- [ ] T043a [CI] Add CI workflow file `.github/workflows/analysis.yml`. **Execute**: Create file with exact content:
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
          python-version: latest stable release
      - name: Install dependencies
        run: |
          pip install -r code/requirements.txt
      - name: Run Pipeline
        run: python code/main.py
      - name: Verify Results
        run: |
          test -f data/results/permutation_results.json
          test -f data/results/sensitivity_results.json
          test -f data/results/d_score_comparison.png
```
**Verify**: File exists and passes `actionlint` (if available) or manual syntax check.
- [ ] T044 [US3] **REVISION**: Implement robust error handling for the PCA dimensionality check in `code/analysis/pca.py`. **Execute**: Wrap the PCA logic in a try-except block that catches `ValueError` and `RuntimeError`. On error, write `{"status": "error", "message": "<error details>"}` to `data/results/pca_variance.json`. **Verify**: Run `pytest tests/test_analysis/test_pca_error_handling.py` which injects invalid data and asserts the error JSON is written. **Depends on**: T032.
- [ ] T045 [US3] **REVISION**: Add a explicit validation step in `code/main.py` to verify that `data/processed/complexity_scores.csv` contains at least one valid image before proceeding to T032 (PCA). **Execute**: Insert a check in `code/main.py` after T017a-3 completion that raises `ValueError` if the CSV is empty or all rows are 'skipped'. **Verify**: Run `pytest tests/test_main/test_main_empty_data.py` which creates an empty CSV and asserts `ValueError` is raised. **Depends on**: T038.
- [ ] T046 [US2] **REVISION**: Update `code/data/process.py` to explicitly log the number of participants excluded due to insufficient trials (<10) to `logs/exclusion_report.log` with a breakdown by session. **Execute**: Add logging statements in T026b-3 to record `participant_id`, `session_id`, and `reason='insufficient_trials'` for each excluded row. **Verify**: Run pipeline with synthetic data including invalid participants; verify `logs/exclusion_report.log` contains the expected format and counts. **Depends on**: T026b-3.
- [ ] T047 [US1] **REVISION**: Add a CLI argument `--output-format` to `code/stimuli/process.py` (T017a-3) to support both CSV and Parquet output for the complexity scores, with Parquet as the default for performance. **Execute**: Use `pyarrow` to write `complexity_scores.parquet` if the flag is set. **Verify**: Run `pytest tests/test_stimuli/test_process_parquet_output.py` which asserts Parquet file is created and readable. **Depends on**: T017a-3.