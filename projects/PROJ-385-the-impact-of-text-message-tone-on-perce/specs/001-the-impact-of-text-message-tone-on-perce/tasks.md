# Tasks: The Impact of Text Message Tone on Perceived Emotional Support

**Input**: Design documents from `/specs/001-text-tone-emotional-support/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), data-model.md, contracts/

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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `specs/`). **Requirement**: Execute `mkdir -p code data/data/raw data/data/processed data/data/consent tests tests/contract tests/unit`. Create `code/__init__.py` with content `"""Code package."""`. Create `tests/__init__.py` with content `"""Tests package."""`. Create `README.md` in the repository root with header `# The Impact of Text Message Tone on Perceived Emotional Support`. **Verification**: Run `ls -R` to verify directory tree matches plan.md Project Structure and files exist with correct content.
- [X] T002 Initialize Python project with pinned dependencies in `code/requirements.txt` (pandas>=2.0.0, numpy>=1.24.0, scipy>=1.10.0, statsmodels>=0.14.0, linearmodels>=4.28.0, pyyaml>=6.0, pytest>=7.0.0). **Verification**: Run `pip check` to ensure no conflicts.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in **repository root**. **Requirement**: Create `ruff.toml` in repository root with rules: `line-length = 88`, `exclude = ["data"]`, `select = ["E", "W", "F", "I"]`. Create `pyproject.toml` in repository root with black config: `[tool.black] line-length = 88`. **Verification**: Run `ruff check.` from root and verify exit code 0. **Reference**: https://docs.astral.sh/ruff/rules/ for rule definitions.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define data model in `specs/001-text-tone-emotional-support/data-model.md` (Stimulus, Participant, Rating, AnalysisResult) and validate against spec/plan requirements. **Requirement**: Produces `specs/.../data-model.md` with explicit entity definitions. **Verification**: Grep for Stimulus, Participant, Rating, AnalysisResult in the file.
- [X] T005 Create data directory structure: `data/raw/`, `data/processed/`, `data/consent/`. **Requirement**: Execute `mkdir -p data/raw data/processed data/consent`. Create a `.gitkeep` file in each directory to ensure they are tracked by git even when empty. **Verification**: Run `ls data/` to verify three directories exist and `ls data/*/` to verify `.gitkeep` files exist.
- [X] T006 [P] Define and validate JSON/YAML schemas in `specs/001-text-tone-emotional-support/contracts/`. **Requirement**: Create `stimulus.schema.yaml` (properties: `id` (string), `text` (string), `emoji_count` (integer), `punctuation_type` (string), `length_category` (string)), `rating.schema.yaml` (properties: `participant_id` (string), `stimulus_id` (string), `relationship` (enum: ["friend", "acquaintance"]), `rating` (integer 1-7)), and `analysis_result.schema.yaml`. **Verification**: Run `yamllint` on schema files and verify they are valid YAML and match the spec.
- [X] T007 Create base configuration management for random seed pinning and path resolution in `code/config.py`. **Requirement**: File must define `RANDOM_SEED`, `DATA_ROOT`, `STIMULI_PATH`. **VARIANCE_PARAMS**: Define as a dictionary with keys `random_effect_variance` and `residual_variance` but **MUST be marked as deprecated fallback defaults**. The code must check for `pilot_data.json` first; if missing, use these defaults but log a warning that empirical estimates are preferred. **Verification**: Run `python -c "from code.config import *; assert RANDOM_SEED is not None"`.
- [X] T008 [P] Setup logging infrastructure by creating `code/logging_config.py` which configures a logger instance writing to `data/pipeline.log` to record pipeline steps and exclusion reasons (straight-lining, missing data). **Requirement**: File must ensure `data/pipeline.log` is created and writable immediately upon import. **Verification**: Run a dummy pipeline start/stop to ensure `data/pipeline.log` is created with entries. **Dependency**: None. **Blocking**: This task MUST complete before T023a.

---

## Phase 3: User Story 1 - Stimulus Generation and Data Collection (Priority: P1) 🎯 MVP

**Goal**: Generate a controlled set of text message stimuli and collect human ratings for perceived emotional support (via simulation or real collection).

**Independent Test**: Verify that `01_generate_stimuli.py` produces a valid `data/raw/stimuli.csv` and `04_collect_real_data.py` produces a valid `data/raw/ratings.csv` with correct schema and no missing fields.

**⚠️ CRITICAL NOTE ON DATA PATHS & FR-002**:
- **FR-002 Requirement**: "System MUST collect independent human ratings... verified via Prolific ID."
- **T014 (Mock)**: Generates synthetic data. **MANDATORY for CI/Development**. Satisfies structural requirements of FR-002 for automated testing.
- **T015b-Proc (Real Data)**: Generates real data AND anonymized consent records. **MANUAL/EXTERNAL STEP**. To be executed outside of CI. Does NOT block automated pipeline.
- **T015c-Mock**: Generates mock consent records for CI. **MANDATORY for CI**.
- **T015c (Real)**: Generates real consent records. **MANUAL/EXTERNAL STEP**.
- **MVP Status**: The default execution path MUST include T014 and T015c-Mock. T015b-Proc/T015c are manual steps for production.

### 3.1 Generation (Blocking Prerequisites for Validation)

- [ ] T013 [US1] Implement factorial stimulus generator in `code/01_generate_stimuli.py`. **Requirement**: Generate a set of unique text message variants by using **3 emoji levels**, **2 punctuation levels**, and **2 length levels** (3 × 2 × 2 = **48 unique variants**). **Output** `data/raw/stimuli.csv` with columns: `id, text, emoji_count, punctuation_type, length_category, scenario_id`. **Verification**: Run `python code/01_generate_stimuli.py --verify` to ensure exactly **48 unique factorial combinations** are present (no filtering) and the file `data/raw/stimuli.csv` is valid CSV. **Dependency**: None. **Blocking**: This task MUST produce `data/raw/stimuli.csv` before T009, T010a, T016, and T017 can proceed.

### 3.2 Mock Data Path (MANDATORY for CI/Development)

- [ ] T014 [US1] [MANDATORY CI] Implement mock Prolific data collection in `code/02_simulate_ratings.py`. **Requirement**: Generates `data/raw/ratings.csv` with P-IDs, stimulus IDs, relationship context, Likert scores; **reads target_N (participants) from `data/processed/power_analysis_results.json` produced by T009**; **generates total rows = target_N (participants) × [multiple] (contexts) × 48 (stimuli)** to simulate a full within-subjects design. Simulates Prolific ID format validation. **Satisfies structural FR-002 for CI**. **Dependency**: T009, T013.
- [ ] T015c-Mock [US1] [MANDATORY CI] Implement mock consent record generation for unit testing in `code/04_collect_real_data.py`. **Requirement**: Satisfies Plan.md Constitution Check VI for simulation mode. **Trigger**: Must require CLI flag `--mode mock`. **Verification**: Verify mock consent records are generated ONLY when `--mode mock` is active. **Dependency**: T014. **NOTE**: These mock consent records are for unit testing schema compliance ONLY and do NOT satisfy Constitution Principle VI for the final research product. Real consent records (T015c) are required for production.

### 3.3 Real Data Path (MANUAL/EXTERNAL STEP)

- [ ] T015a-Real [US1] [Manual Only] Implement Prolific API client in `code/stubs/prolific_api_client.py`. **Requirement**: Satisfies FR-002 for real human ratings. Implements recruitment, survey deployment, and Prolific ID verification using the official Prolific API. **Methods**: `deploy_survey()`, `get_responses()`, `verify_prolific_id()`. **Input**: Requires `API_KEY` and `SURVEY_ID` from environment variables. **Verification**: Verify real API calls are made (or stubbed in CI) and Prolific IDs are correctly mapped. **Dependency**: None (Foundational).
- [ ] T015b-Code [US1] [MANDATORY] Implement Prolific data ingestion logic in `code/04_collect_real_data.py`. **Requirement**: Satisfies FR-002 for real human ratings. **Input Format**: Parse Prolific response export (comma-delimited, header row present, ISO-8601 dates, columns: `ProlificID`, `ResponseID`, `StartDate`, `Q1`... `Q40`). **Enforcement**: The script MUST read `target_N` from `data/processed/power_analysis_results.json` (produced by T009). **Pre-Check**: Before recruitment, verify Prolific API quota or survey limit matches `target_N`; raise an error if insufficient. **ID Mapping**: Explicitly map `ProlificID` to `participant_id`. **Dependency**: T015a-Real, T009, T013. **Verification**: Verify artifact `data/raw/real_ratings.csv` exists with real P-ID format and valid Likert scores. **NOTE**: This task is the **CODE IMPLEMENTATION** of the real data path. It is mandatory for the project structure.
- [ ] T015b-Proc [US1] [MANUAL/EXTERNAL] Execute the Prolific data collection process. **Requirement**: Run `python code/04_collect_real_data.py --mode real` to fetch and save `data/raw/real_ratings.csv`. **Dependency**: T015b-Code. **NOTE**: This is a manual step. If skipped, the pipeline will use T014 (Mock) data, and FR-002 will be considered unsatisfied for the final deliverable.
- [ ] T015c [US1] [MANUAL/EXTERNAL] Implement consent record generation in `code/04_collect_real_data.py`. **Requirement**: Satisfies Constitution Principle VI. **Trigger**: Must require CLI flag `--mode real` or env var `REAL_DATA_MODE=1`. **Pre-Condition**: MUST verify that `data/raw/real_ratings.csv` (from T015b-Proc) exists. If the file is missing, the script MUST raise a `FileNotFoundError` with a clear message indicating that consent records cannot be generated without real data. **Verification**: Add a check to ensure consent records are generated ONLY when real data mode is active AND the input file exists. **Dependency**: T015b-Proc. **CRITICAL**: If T015b-Proc is executed, T015c MUST be executed. Skipping T015c when T015b-Proc is active violates Constitution Principle VI.

### 3.4 Validation (Sequential Dependencies)

- [ ] T010a [US1] [ATOMIZE] Create and verify contract test file for stimulus data in `tests/contract/test_stimulus_schema.py`. **Function**: `test_stimulus_schema_valid`. **Requirement**: Validate `data/raw/stimuli.csv` against schema from T006. **Dependency**: T013. **Verification**: Run `pytest tests/contract/test_stimulus_schema.py` and ensure it passes. **Note**: If `data/raw/stimuli.csv` is missing, the test must FAIL (not crash) to indicate missing input. This is a post-condition check.
- [ ] T011a [US1] [ATOMIZE] Create and verify contract test file for rating data in `tests/contract/test_rating_schema.py`. **Function**: `test_rating_schema_valid`. **Requirement**: Validate `data/raw/ratings.csv` (from T014) or `data/raw/real_ratings.csv` (from T015b-Proc) against schema from T006. **Dependency**: T014 (CI) or T015b-Proc (Manual). **Verification**: Run `pytest tests/contract/test_rating_schema.py` and ensure it passes.

### 3.5 Cleaning & Preprocessing

- [ ] T017 [US1] [Integrated] Implement validation logic to ensure relationship context (friend/acquaintance) is randomized and logged. **Requirement**: **Integrated into T014 (Mock) and T015b-Code (Real)**. **Verification**: Assert that randomization is recorded in the output file and logged. **Dependency**: T014 (CI) or T015b-Code (Manual). **Note**: T017 is no longer a standalone blocking task; its logic is embedded in the data generation tasks.
- [ ] T016 [US1] Implement straight-lining detector AND missing data handler in `code/03_clean_data.py`. **Requirement**:
 1. Flags participants with zero variance across the **full set of stimuli** and logs reason 'STRAIGHT_LINING'.
 2. **DYNAMIC COUNT CHECK**: MUST read the total count of unique `id` values from `data/raw/stimuli.csv` at runtime. Do NOT use hardcoded values like '40' or '12'.
 3. **Missing Data**: If a participant's rated count < total stimulus count, **FLAG** the participant with reason 'MISSING_DATA' and log to `data/processed/cleaning_log.csv`, THEN implement listwise deletion (dropping the participant from analysis).
 4. **Data Corruption**: If a participant's rated count > total stimulus count (indicating duplicate entries or data corruption), the participant MUST be flagged with reason 'DATA_CORRUPTION' and excluded. Log the specific discrepancy (e.g., "Participant P-123 rated 45 stimuli but only 48 exist").
 5. **Validation Step**: Assert that the total stimulus count from `data/raw/stimuli.csv` is at least 1. If not, raise an error to preserve FR-006 constraint.
 6. Output exclusion flags and reasons to `data/processed/cleaning_log.csv`.
 **Verification**: Assert that participants with 0 variance are correctly flagged, partial raters are flagged and excluded, and data corruption (count > total) is handled and logged. **Dependency**: T013, T006, T014 (CI) or T015b-Proc (Manual). **Note**: T016 runs after T014 (CI) or T015b-Proc (Manual).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Stimuli and Ratings generated, Consent handling ready for real path)

---

## Phase 3b: Validation & Benchmarking (Post-Data Generation)

**Purpose**: Validate data generation and benchmark performance before analysis

- [ ] T037a [P] Implement CLI entry point in `code/run_pipeline.py` (handles argument parsing for `--mode`, `--seed`, `--benchmark`). **Requirement**: Must support `--mode mock` (CI) and `--mode real` (Manual). **Verification**: Run `python code/run_pipeline.py --help` and verify output. **Dependency**: None.
- [ ] T037-Mock [P] [MANDATORY] Benchmark full pipeline duration by running the full pipeline with `--benchmark --mode mock` using the target N from `data/processed/power_analysis_results.json` and the full stimulus set from `data/raw/stimuli.csv` to ensure the benchmark reflects the actual SC-005 constraint. **Requirement**: Measure **wall-clock time in seconds** for the entire pipeline (Data Generation + Cleaning + LMM Analysis + Sensitivity). Output MUST include keys `total_duration_seconds`, `per_stage_duration`. **Verification**: If `total_duration_seconds > 21600`, log a warning "Pipeline exceeds 6h limit; flag for optimization" and **DO NOT FAIL** the task. If `< 21600`, pass. **Dependency**: T009, T037a, T013, T014, T016, T020, T021, T022, T024, T025, T027, T028, T029, T030, T031. **Note**: T037a must complete before T037-Mock runs.

**Checkpoint**: Data validated, performance benchmarked, pipeline ready for analysis

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline (Priority: P2)

**Goal**: Execute Linear Mixed-Effects Models (LMM) to test for interaction effects between relationship type and cue intensity.

**Independent Test**: Verify that `04_run_lmm.py` produces `data/processed/analysis_results.json` with fixed effect estimates, p-values, and Tukey-corrected post-hoc results without GPU usage.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for LMM model construction with mock data in `tests/unit/test_analysis_logic.py`
- [X] T019a [US2] [ATOMIZE] Create unit test file for LMM preprocessing logic in `tests/unit/test_lmm_preprocessing.py`. **Requirement**: Implement tests for data loading, listwise deletion, and schema validation. **Function**: `test_preprocessing_logic`. **Dependency**: T020.
- [X] T019b [US2] [ATOMIZE] Create unit test file for LMM model execution in `tests/unit/test_lmm_execution.py`. **Requirement**: Implement tests for Satterthwaite approximation and p-value calculation. **Function**: `test_lmm_execution`. **Dependency**: T021, T022.
- [X] T019c [US2] [ATOMIZE] Create unit test file for Tukey correction logic in `tests/unit/test_lmm_posthoc.py`. **Requirement**: Implement tests for Tukey-corrected pairwise comparisons. **Function**: `test_lmm_posthoc`. **Dependency**: T024.
- [X] T019d [US2] [ATOMIZE] Create integration test file for full LMM pipeline in `tests/integration/test_lmm_pipeline.py`. **Requirement**: Implement end-to-end test: load data, run LMM, verify p-values and Tukey corrections. **Function**: `test_full_lmm_pipeline`. **Dependency**: T019a, T019b, T019c, T020, T021, T022, T024.

### Implementation for User Story 2

- [ ] T020 [US2] Implement data preprocessing step in `code/04_run_lmm.py` to handle listwise deletion of excluded participants (**reads exclusion flags from `data/processed/cleaning_log.csv` produced by T016**). **Requirement**: If `data/raw/real_ratings.csv` does not exist, fallback to `data/raw/ratings.csv` (from T014) and log a warning that FR-002 is not satisfied. **Dependency**: T016, T006, T013, T014 (or T015b-Proc).
- [ ] T021 [US2] Implement primary LMM script in `code/04_run_lmm.py` using `statsmodels` or `linearmodels` (Random intercepts for Participant and Stimulus)
- [ ] T022 [US2] Implement Satterthwaite approximation for degrees of freedom and p-value calculation in `code/04_run_lmm.py`
- [ ] T023a [US2] Implement validation check in `code/04_run_lmm.py` that asserts the LMM model summary includes a variance component for **Stimulus**; **if Stimulus variance is negligible (< 0.001), the script MUST log a warning to `data/pipeline.log` and generate a transient exclusion summary object**. **Requirement**: **Do NOT produce a final SSoT file**. The exclusion data must be merged into `analysis_results.json` by T025. **Dependency**: T020, T021, T008.
- [ ] T023b [P] Create unit test file `tests/unit/test_analysis_validation.py` to validate T023a logic. **Requirement**: Implement tests for: (1) `assert_zero_variance_triggers_flag`, (2) `assert_non_zero_variance_no_flag`, (3) `assert_log_entry_created`, (4) `assert_exclusion_summary_generated`. **Dependency**: T023a.
- [ ] T024 [US2] Implement Tukey-corrected post-hoc pairwise comparisons in `code/04_run_lmm.py` (triggered if interaction p < 0.05)
- [ ] T025 [US2] Implement result serialization to `data/processed/analysis_results.json` (JSON format for single source of truth). **Requirement**: The JSON output MUST include a top-level key `exclusion_summary` containing the count of excluded participants and reasons, **merged from the transient object produced by T023a**. This ensures `analysis_results.json` is the **Single Source of Truth** for all analysis metrics, including exclusions, satisfying Constitution Principle IV and resolving the conflict in Plan.md's Constitution Check. **Dependency**: T020, T021, T023a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis results generated)

---

## Phase 5: User Story 3 - Methodological Robustness and Sensitivity Reporting (Priority: P3)

**Goal**: Perform sensitivity analysis on "Cue Intensity" definitions using structural rules and report robustness of findings.

**Independent Test**: Verify that `05_sensitivity_analysis.py` re-runs LMM with Alternative cue definitions and outputs a stability report in `data/processed/sensitivity_report.csv`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for alternative cue definition logic in `tests/unit/test_sensitivity_logic.py`

### Implementation for User Story 3

- [ ] T027 [US3] [P] Define **three specific theoretical hypotheses** for "Cue Intensity" based on psycholinguistic literature and output them as machine-readable JSON in `data/processed/sensitivity_definitions.json`. **Schema Requirement**: JSON must contain a list of definitions, each with keys `name` (string), `type` (enum: "weighted_sum"), `formula_type` (string: "weighted_sum"), `rule` (object: e.g., `{"weights": {"emoji": 0.7, "punct": 0.2, "len": 0.1}}`). **Definitions**:
 1. **Emoji-Dominance**: Weights {emoji: high, punct: moderate, len: low}. Rationale: Based on Hancock & Dunham (2004) on emoji as primary emotional carrier.
 2. **Punctuation-Dominance**: Weights {emoji: 0.2, punct: 0.7, len: <relative magnitude>}. Rationale: Based on Derks et al. (2008) on punctuation as tone indicator.
 3. **Length-Dominance**: Weights {emoji: 0.1, punct: 0.2, len: }. Rationale: Based on message length as a proxy for effort/empathy.
 **Formula**: `Cue_Intensity = (w_emoji * emoji_count) + (w_punct * punct_score) + (w_len * len_score)`. **Verification**: Validate JSON schema against expected keys and count a representative set of items (must be 3). **Requirement**: Verify that `research.md` contains citations for "Hancock & Dunham" and "Derks et al." before generating the file. **Dependency**: None.
- [ ] T028 [US3] Implement sensitivity analysis engine in `code/05_sensitivity_analysis.py` (**reads operationalization definitions from `data/processed/sensitivity_definitions.json` produced by T027**; **reads primary results from `data/processed/analysis_results.json` produced by T025**; **reads cleaned data from `data/processed/clean_ratings.csv` produced by T020**; **dynamically applies each definition to re-calculate the 'Cue Intensity' variable using the `weighted_sum` formula: `Cue_Intensity = sum(w_i * x_i)`** and re-runs the LMM for each definition). **Dependency**: T027, T025, T020.
- [ ] T029 [US3] Implement re-execution of LMM for each alternative definition in `code/05_sensitivity_analysis.py` (reusing Tukey logic from T024).
- [ ] T030 [US3] Implement stability metric calculation (variation in F-statistics and p-values across definitions) in `code/05_sensitivity_analysis.py`
- [ ] T031 [US3] Generate sensitivity report CSV in `data/processed/sensitivity_report.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `specs/001-text-tone-emotional-support/quickstart.md`. **Requirement**: Add a section on how to run the power analysis, a section on how to run the pipeline with `--benchmark`, and verify the document contains a `python code/run_pipeline.py` command. **Verification**: Verify `quickstart.md` contains the required sections and commands.
- [ ] T035 [P] Run full pipeline end-to-end test with fixed seed to verify reproducibility. **Requirement**: Run `python code/run_pipeline.py --seed [RANDOM_SEED]`. Verify `data/processed/analysis_results.json` is generated. Compute the SHA256 hash of the output file and log it. **Verification**: The task must succeed if the pipeline runs without error and produces a deterministic hash for the given seed. **Dependency**: T009, T013, T014, T016, T025.
- [ ] T036 [P] Additional unit tests for edge cases (missing data in ratings.csv, invalid P-ID format) in `tests/unit/`. **Requirement**: Create `tests/unit/test_edge_cases.py` with tests for: (1) `assert_missing_data_handled` (verify listwise deletion), (2) `assert_invalid_pid_rejected` (verify regex validation). **Dependency**: T014, T016.
- [ ] T038 [P] Run quickstart.md validation by executing `pytest tests/integration/test_quickstart.py` and verifying exit code 0.
- [ ] T039 [P] Update `specs/001-text-tone-emotional-support/research.md` with final methodology notes, power analysis justification, and sensitivity analysis summary. **Requirement**: Add a paragraph on the power analysis results (from T009) and a section on the sensitivity analysis summary (from T031). **Verification**: Verify `research.md` contains the required sections. **Dependency**: T041.
- [ ] T040 [P] Generate final `README.md` in the feature folder summarizing how to run the pipeline, interpret results, and reproduce the study. **Requirement**: Include a `Usage` section with CLI examples (`python code/run_pipeline.py --mode mock`) and a `Results` section explaining how to interpret the output files (`analysis_results.json`, `sensitivity_report.csv`). **Verification**: Verify `README.md` exists and contains the required sections. **Dependency**: T041.
- [ ] T041 [P] [GATE] Verify Real Data for Final Report. **Requirement**: Check for existence of `data/raw/real_ratings.csv`. **Verification**: If `data/raw/real_ratings.csv` is missing, **FAIL** this task and prevent T039 and T040 from being marked complete. If present, pass. **Dependency**: T015b-Proc (Manual) or T014 (CI Fallback). **Note**: This task enforces FR-002 by blocking final report generation if real data is missing (unless explicitly overridden by a manual flag, which must be documented).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion (T009 must complete before Phase 3)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/raw/ratings.csv` and `data/raw/stimuli.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 (requires primary analysis results to test robustness)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Generators before Simulators
- Simulators before Analyzers
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **except T010/T011 which depend on T013/T014 and are now in Phase 3**
- Tests for different user stories can run in parallel
- Within US1, stimulus generation and rating simulation can run in parallel once data schemas are defined
- **T010a and T011a can run in parallel with each other ONLY AFTER T013 and T014 (or T015b-Proc for manual) have completed.**
- **T017 is integrated into T014/T015b-Code; T016 depends on T014/T015b-Proc completion.**

---

## Parallel Example: User Story 1

```bash
# Launch schema validation and generator in parallel (Phase 3):
# Note: T010a depends on T013, so T010a runs AFTER T013 completes.
Task: "Implement factorial stimulus generator in code/01_generate_stimuli.py" (T013)
Task: "Create and verify contract test file for stimulus data in tests/contract/test_stimulus_schema.py" (T010a, after T013)

# Launch rating simulation, cleaning logic, validation, and contract tests in parallel:
Task: "Implement mock data collection in code/02_simulate_ratings.py" (T014, CI Path)
Task: "Implement straight-lining detector in code/03_clean_data.py" (T016, after T014)
Task: "Create and verify contract test file for rating data in tests/contract/test_rating_schema.py" (T011a, after T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Generate stimuli and **Mock** ratings via T014 for CI)
4. **STOP and VALIDATE**: Test US1 independently (verify data schemas)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Analysis results)
4. Add User Story 3 → Test independently → Deploy/Demo (Sensitivity report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Generation & Mock Collection for CI)
 - Developer B: User Story 2 (LMM Analysis) - *Wait for US1 data*
 - Developer C: User Story 3 (Sensitivity) - *Wait for US2 results*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T010/T011 which depend on T013/T014)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Consent Records**: T015c-Mock generates `data/consent/mock_consent_records/` for CI. T015c generates real consent records for manual execution.
- **Simulation Mode**: T014 is MANDATORY for CI. The default execution path MUST use T014 (Mock Data). T015b-Proc is MANUAL/EXTERNAL.
- **Single Source of Truth**: All exclusions (straight-lining, variance, missing data) are logged to `data/processed/cleaning_log.csv` (audit log) and **summarized in `data/processed/analysis_results.json` (SSoT)**. The `analysis_results.json` file is the **sole** source for downstream reporting and paper generation, ensuring compliance with Constitution Principle IV.
- **New Tasks (T039, T040, T041)**: Added to address the need for comprehensive documentation and reproducibility notes as part of the final polish phase, ensuring the research output is complete and understandable. T041 enforces FR-002.