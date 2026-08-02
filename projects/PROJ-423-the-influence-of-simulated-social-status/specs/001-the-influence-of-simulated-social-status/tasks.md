# Tasks: The Influence of Simulated Social Status on Risk-Taking Behavior

**Input**: Design documents from `/specs/001-simulated-status-risk/`
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

## Phase 0: Research & Data Strategy (Prerequisite)

**Purpose**: Generate `research.md` with fixed simulation parameters to satisfy Phase 1 dependencies.

- [X] T000a-Verify [P] **Must run first**: Verify effect size citations listed in `sources_list.md` (input artifact) using the Reference-Validator Agent. **Execution**: Run `python code/verify_citations.py --sources-file sources_list.md`. **Constraint**: If validation fails (unreachable/mismatch), the process MUST halt with an error. No fallback to defaults is permitted. Output: `state/verification_report.json`.
- [X] T000a-Generate [P] **Must run after T000a-Verify**: Generate `research.md` in `specs/001-simulated-status-risk/` containing verified effect sizes (Cohen's d) and calculated sample size N. **Specifics**: Calculate N using `code/power_analysis.py` based on verified effect sizes (alpha=0.05, power=0.80). Write N and citations to `research.md`. **Output Schema**: Markdown file with YAML frontmatter containing keys: `effect_sizes` (dict with keys: `status_high`, `status_low`, `observed_risky`, `observed_conservative`, `interaction`), `sample_size` (int), `citations` (list), and `methodology` (string).
- [X] T000b-SimulateParams [P] **Must run after T000a-Verify**: Generate `code/simulation_parameters.json` containing the verified effect sizes (for the Simulation Path), calculated N, and random seed. **Constraint**: This file serves as the Single Source of Truth for SC-004 (validity of risk-taking measure). If the meta-analysis path is selected, this file contains meta-analytic parameters; if the simulation path is selected (default), it contains the synthetic effect sizes derived from the verified literature.

---

## Phase 1: Setup & Foundational (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and data configuration prerequisites.

- [X] T001a [P] Create `data/` directory structure (`data/raw/`, `data/processed/`) with `.gitkeep` files to ensure tracking.
- [X] T001b [P] Create `code/` directory structure (`code/__init__.py`, `code/config.py`) with `.gitkeep` files.
- [X] T001c [P] Create `tests/` and `docs/` directory structures with `.gitkeep` files.
- [X] T002a [P] Create `code/requirements.txt` listing specific dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`, `jinja2`, `weasyprint`, `datasets`, `radon`.
- [X] T002b [P] Pin versions in `code/requirements.txt` for all dependencies listed in T002a using `pip freeze`. **Constraint**: Run this command in a clean virtual environment after installing dependencies to ensure deterministic version pinning.
- [X] T003a [P] Create `.pre-commit-config.yaml` configuring ruff and black hooks.
- [ ] T003b [P] Create `.gitignore` excluding `__pycache__`, `*.pyc`, `.env`, and `data/raw/*.csv` (checksummed only).

**⚠️ CRITICAL**: No user story work can begin until this phase (and T000a) is complete.

- [X] T010a [US1] **Must run after T000b-SimulateParams**: Read verified effect sizes and N from `code/simulation_parameters.json` and define them as constants in `code/config.py` for simulation parameters.
- [X] T010b-Simulate [US1] **Must run after T010a**: Implement `code/simulate.py`: Synthetic data generator that supports **both** between-subjects and within-subjects designs based on a `DESIGN_TYPE` flag in `code/simulation_parameters.json`. Ensures N participants (between) or N subjects with repeated measures (within). Output: `data/raw/simulation_output.csv`.
- [X] T004 [P] Create `data/checksums.json` with initial structure `{"files": {}}` to satisfy Constitution Principle III.
- [X] T005 [P] Implement `code/logger.py` with a standard logging configuration (JSON format, file output) and **update** `code/config.py` to include a `LOGGING_CONFIG` dictionary.
- [X] T006 [P] Create `code/models.py` explicitly defining `Participant`, `Condition`, and `ModelResult` entities as Pydantic or dataclass models.
- [X] T007 [P] Setup pytest framework in `tests/` with `conftest.py` and `tests/contract/` directory.
- [X] T008 [P] Implement `code/utils.py` for common helpers (seeding, file I/O, checksum calculation).
- [X] T024b-SchemaDef [P] **Must run before T025a**: Create `contracts/model_config.schema.yaml` with the following explicit content:
  ```yaml
  type: object
  required:
    - design_type
    - family_type
    - n_subjects
  properties:
    design_type:
      type: string
      enum: ["between-subjects", "within-subjects"]
    family_type:
      type: string
      enum: ["gaussian", "binomial"]
    n_subjects:
      type: integer
      description: Number of unique participants
  ```

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Synthesis and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset based on meta-analytic effect sizes OR aggregate real data via meta-analysis, and preprocess it for analysis, ensuring correct categorical factor integrity.

**Independent Test**: Verify that the output CSV contains required columns (`status_level`, `observed_behavior`, `risk_taking_score`, `participant_id`), that the data structure is correctly tagged, and that the random seed produces deterministic results.

**Note on Meta-Analysis Path**: The Spec (FR-001) allows an 'OR' path for meta-analysis. However, the Plan explicitly states no suitable public dataset exists. Therefore, this implementation phase focuses exclusively on the **Simulation Path**. The meta-analysis path is deferred to a future research phase pending the identification of a valid dataset registry.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/simulate.py`: Add a validation function that raises a `ValueError` with the message "Error: status_level has no variance. Experimental condition integrity violated." if the generated data lacks variance, and exit with code 1.
- [X] T012a [US1] Implement `code/preprocess.py`: Load raw synthetic data, map `status_level` and `observed_behavior` to categorical factors (High/Low, Risky/Conservative).
- [X] T012b [US1] **Must run after T012a**: Implement `code/preprocess.py`: Implement the specific binning strategy (e.g., High vs Low/Medium) for input data with >2 levels. **Output**: Write a `binning_state.json` file to `data/processed/` with `binning_applied: true` if binning is used. **Constraint**: Do NOT modify `code/config.py`.
- [X] T013 [US1] **Must run after T012b**: Implement `code/preprocess.py`: Handle missing values (imputation or exclusion) and report the final N used for analysis. **Constraint**: Output MUST be written to `data/processed/cleaned_data.csv`. The logic MUST preserve the `participant_id` granularity (do not aggregate rows) to ensure downstream design detection is possible.
- [X] T014a [US1] Implement `code/preprocess.py`: Detect outcome variable type (binary vs. continuous) based on data distribution in `data/processed/cleaned_data.csv`. **Output**: Write the detected type (e.g., "binary" or "continuous") to `data/processed/outcome_type.json`.
- [X] T014b [US1] **Must run after T014a**: Implement `code/preprocess.py`: **Remove** any logic to switch regression families. This task is now strictly a detector that reads `data/processed/outcome_type.json` and logs the detected type. The decision to switch families is moved to T021b. **Constraint**: Ensure `data/processed/outcome_type.json` is valid JSON with a single key `type`.

- [X] T015 [P] [US1] Write `tests/contract/test_data_schema.py` to validate output CSV columns and data types against `data-model.md`.
- [X] T016 [P] [US1] Write `tests/unit/test_data_generation.py` to verify deterministic output given a fixed seed.
- [X] T020b [US1] Define the JSON schema for `structure_config.json` in `contracts/structure_schema.yaml` (keys: `type`, `n_subjects`, `model_type`; types: string, int, string) and validate that T021b's output matches this schema. **Note**: This schema is now explicitly listed in the plan's Contract Mapping section as required for intermediate artifacts.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Adaptive Regression Analysis (Priority: P1)

**Goal**: Fit an adaptive regression model (Mixed-Effects if within-subjects, Fixed-Effects if between-subjects) to test the interaction, explicitly calculating VIF, Parameter Recovery, and 95% CI Width.

**Independent Test**: Run the model on the synthetic dataset with a known interaction effect and verify that the estimated coefficient matches the injected parameter within the confidence interval, and that the p-value is correctly calculated against the null.

### Implementation for User Story 2

- [X] T021b [US2] **Must run after T013 and T014a**: Implement `code/analysis.py`: Function `generate_model_config` that reads `data/processed/cleaned_data.csv` AND `data/processed/outcome_type.json`. 
  **Logic**: 
  1. Count unique `participant_id` values vs total rows in `cleaned_data.csv`. If unique < total, set `design_type: "within-subjects"`, else `design_type: "between-subjects"`. 
  2. Read `type` from `outcome_type.json`. If "binary", set `family_type: "binomial"`, else `family_type: "gaussian"`.
  3. Set `n_subjects` to the count of unique `participant_id` values.
  4. Write `data/processed/model_config.json` containing `design_type`, `family_type`, and `n_subjects`.
  **Constraint**: Do NOT hardcode values. The logic must inspect the actual `cleaned_data.csv` and `outcome_type.json` to determine the structure and family truthfully. This task consolidates the previously fragmented logic into a single source of truth for the model configuration.
- [X] T021a [US2] **Must run after T021b**: Implement `code/analysis.py`: Function `fit_adaptive_model` that reads `data/processed/model_config.json`. 
  **Logic**: 
  1. Read `design_type`. If "within-subjects", fit a Mixed-Effects model (`risk_taking ~ status_level * observed_behavior + (1|participant_id)`). If "between-subjects", fit a Fixed-Effects model (`risk_taking ~ status_level * observed_behavior`).
  2. Read `family_type`. Use `gaussian` family for continuous outcomes, `binomial` for binary outcomes.
  **Constraint**: Do NOT hardcode model type or family. The selection MUST be driven dynamically by the unified `model_config.json` generated in T021b.
- [X] T022 [US2] Implement `code/analysis.py`: Calculate Variance Inflation Factors (VIF) for all predictors and flag if > 5.0.
- [X] T023 [US2] Implement `code/analysis.py`: Extract fixed effects coefficients, standard errors, and p-values for the interaction term.
- [X] T023b-SimulationValidation [US2] **Must run after T023 and T000b-SimulateParams**: Implement `code/analysis.py`: Logic to calculate "Parameter Recovery" by comparing the estimated interaction coefficient to the `injected_interaction_effect` loaded from `code/simulation_parameters.json` (set in T000b-SimulateParams) and checking if it falls within the confidence interval. **Dependency**: This task requires the injected parameter from `simulation_parameters.json` (T000b-SimulateParams) and the model output from T023. It is NOT parallelizable with T023. **Note**: This is a simulation validation metric, distinct from the primary scientific success criteria.
- [X] T023c-CI-Validate [US2] **Must run after T023**: Implement `code/analysis.py`: Calculate and report the **width of the 95% Confidence Interval** for the interaction coefficient (Upper Bound - Lower Bound) as a standalone success metric for SC-003. Ensure this value is explicitly logged and included in the model output schema. **Constraint**: Read `ci_width_warning_threshold` from `code/simulation_parameters.json` and flag if CI width exceeds this value.
- [X] T024 [US2] Implement `code/analysis.py`: Add fallback logic to use asymptotic standard errors if bootstrap resampling fails (memory constraints).
- [X] T025a [P] [US2] **Must run after T024b-SchemaDef**: Write `tests/contract/test_model_config.py` to validate `data/processed/model_config.json` against `contracts/model_config.schema.yaml`. **Constraint**: The test must explicitly check for the presence and type of all keys defined in T024b-SchemaDef.
- [X] T025b [P] [US2] **Must run after T024b-SchemaDef**: Write `tests/contract/test_model_output.py` to validate model output schema (coefficients, p-values, VIF, ci_width, model_type) against `contracts/model_output.schema.yaml`. **Constraint**: The test must explicitly check for the presence and type of all keys defined in T024b-SchemaDef.
- [X] T026 [P] [US2] Write `tests/unit/test_analysis.py` to verify parameter recovery (estimated vs. injected effect size), correct family selection, and CI width calculation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Sensitivity Analysis and Reporting (Priority: P2)

**Goal**: Conduct sensitivity analyses on outlier thresholds, perform post-hoc comparisons with Bonferroni correction, and generate reproducible reports with forest plots.

**Independent Test**: Manually alter the outlier threshold in config and verify the report explicitly lists the change in the headline effect size and p-value.

### Implementation for User Story 3

- [X] T030 [US3] **Must run after T023**: Implement `code/analysis.py`: Sensitivity analysis module to sweep outlier exclusion threshold over a range of standard deviations. **Strict Constraint**: Calculate absolute deviation from the *cell mean* within each of the 4 experimental conditions (High/Risky, High/Conservative, Low/Risky, Low/Conservative) before exclusion. Do NOT use a global mean. **Output**: Generate a table of means and 95% CIs for each condition at each threshold.
- [X] T031 [US3] Implement `code/analysis.py`: Perform post-hoc pairwise comparisons with Bonferroni correction for all condition combinations, executing this logic UNCONDITIONALLY regardless of the primary interaction significance (per FR-006).
- [X] T035-ReportSchema [P] [US3] **Must run before T033**: Create `contracts/report_schema.yaml` explicitly defining the structure of the final report data, including keys: `model_table`, `vif_table`, `sensitivity_table`, `forest_plot_img`. **Constraint**: This schema ensures the report generation has a verifiable contract.
- [X] T032 [P] [US3] Implement `code/report.py`: Generate forest plot of condition means with Confidence Intervals using `matplotlib/seaborn`. **Specifics**: Read the condition means and their 95% CIs from the descriptive statistics calculated in T030. Calculate the 95% Confidence Interval for the mean risk-taking score of each of the four condition combinations and use these specific values for the plot error bars.
- [X] T032b [P] [US3] Create the directory `reports/templates/` and implement the file `reports/templates/analysis_report.html`. **Specifics**: This template must define the HTML structure for the final report, including placeholders `{{ model_table }}` (dict of coefficients), `{{ vif_table }}` (dict of VIFs), `{{ sensitivity_table }}` (dict of sensitivity results), and `{{ forest_plot_img }}` (base64 string or path). **Constraint**: The variable names passed to the Jinja2 template in `code/report.py` must match these placeholders exactly.
- [X] T033 [US3] Implement `code/report.py`: Generate PDF/HTML summary containing model coefficients, VIF table, sensitivity sweep results, and forest plot, saving to `reports/analysis_report.html`. Use `jinja2` to render `reports/templates/analysis_report.html` with the analysis data, and use `weasyprint` to convert the rendered HTML to a PDF. **Dependency**: Must depend on T035-ReportSchema.
- [X] T036-ReportValidation [P] [US3] Write `tests/contract/test_report_schema.py` to validate the generated report structure (HTML content or parsed data) against `contracts/report_schema.yaml`.
- [X] T043a [P] [US3] Write `tests/unit/test_outlier_logic.py` to verify that changing the threshold in config updates the sensitivity table. **Specifics**: Create a test that modifies the outlier threshold in a mock config, runs the sensitivity sweep, and asserts that the resulting table shows different exclusion counts and coefficient values.
- [X] T043b [P] [US2] Write `tests/unit/test_vif_logic.py` to verify VIF calculation and threshold flagging. **Specifics**: Create a test that feeds a dataset with known multicollinearity into the VIF calculator and asserts that the VIF values are correctly computed and flagged if > 5.0.
- [X] T043c [P] [US2] Write `tests/unit/test_parameter_recovery.py` to verify the logic in T023b-SimulationValidation (estimated vs. injected effect size). **Specifics**: Create a test that simulates data with a known interaction effect, runs the analysis, and asserts that the estimated effect falls within the calculated confidence interval of the injected effect.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] Update `quickstart.md` with specific execution steps and dependencies
- [X] T040b [P] Add comprehensive docstrings to `code/generate_data.py`, `code/analysis.py`, and `code/report.py`
- [X] T041a-Analysis [P] Refactor `code/analysis.py` using `radon` tool to reduce cyclomatic complexity to a lower, more manageable level for all functions. **Target Functions**: `fit_adaptive_model`, `sensitivity_sweep`. **Strategy**: Extract helper functions for VIF calculation and outlier filtering. **Command**: `radon cc -m 10 code/analysis.py`. **Acceptance Criteria**: Max complexity < 10.
- [X] T041b-Simulate [P] Refactor `code/simulate.py` using `radon` tool to reduce cyclomatic complexity to an acceptable threshold for all functions. **Command**: `radon cc -m 10 code/simulate.py`. Target: All functions with complexity >= 10.
- [X] T042a-Baseline [P] Profile `code/analysis.py` using `cProfile` and save output to `reports/baseline_profile.txt`.
- [X] T042b-PerformanceCheck [P] Verify that the full pipeline (simulation -> analysis -> report) completes within the time limit specified in Assumption. **Constraint**: If runtime exceeds a predefined threshold, log a warning but do not fail the build.
- [X] T044 Run `quickstart.md` validation to ensure full pipeline reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 0 completion (T000a-Verify, T000a-Generate, T000b-SimulateParams must run before T010a/T010b) - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T014 flag, T021b structure)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Unit test for data generation in tests/unit/test_data_generation.py"

# Launch all models for User Story 1 together:
Task: "Create data generator in code/simulate.py"
Task: "Create preprocessor in code/preprocess.py"
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
 - Developer A: User Story 1 (Data Generation/Preprocessing)
 - Developer B: User Story 2 (Analysis/Modeling)
 - Developer C: User Story 3 (Sensitivity/Reporting)
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
- **Critical Constraint**: This project uses an Adaptive Model Selection (Mixed-Effects if within-subjects, Fixed-Effects if between-subjects) as per FR-003.
- **Critical Constraint**: The loader must FAIL LOUDLY if real data fetch fails; no synthetic fallbacks are permitted.
- **Critical Constraint**: All simulation parameters must be derived from verified meta-analytic sources in `research.md` or `sources_list.md`.
- **Critical Constraint**: The 'OR' path of FR-001 (simulation OR meta-analysis) is currently satisfied by the simulation path only, as the meta-analysis path is deferred due to lack of a public dataset.
- **Critical Constraint**: The `model_config.json` (T021b) is the single source of truth for both design structure and family type, ensuring T021a has all required parameters.