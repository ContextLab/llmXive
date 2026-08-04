# Tasks: The Influence of Simulated Social Status on Risk-Taking Behavior

**Input**: Design documents from `/specs/001-the-influence-of-simulated-social-status/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

- [X] T000d-VerifyScript-Write **Must run before T000e-VerifyScript-Run**: Implement `code/verify_citations.py`: Script that accepts `--sources-file` argument, loads citations, validates them against primary sources (Title overlap >= 0.7), and writes `state/verification_report.json`. **Input**: `projects/PROJ-423-the-influence-of-simulated-social-status/specs/001-the-influence-of-simulated-social-status/sources_list.md` (YAML/JSON list of citations). **Constraint**: Must raise an error if any citation failed validation. **Output Schema**: `state/verification_report.json` must contain a list of objects with keys: `source_id`, `status` (validated/mismatch/unreachable), `extracted_effect_size` (float, optional), `source_url`.
- [X] T000e-VerifyScript-Run **Must run after T000d-VerifyScript-Write**: Verify effect size citations listed in `projects/PROJ-423-the-influence-of-simulated-social-status/specs/001-the-influence-of-simulated-social-status/sources_list.md` using the Reference-Validator Agent. **Execution**: Run `python code/verify_citations.py --sources-file projects/PROJ-423-the-influence-of-simulated-social-status/specs/001-the-influence-of-simulated-social-status/sources_list.md`. **Constraint**: If validation fails (unreachable/mismatch), the process MUST halt with an error. No fallback to defaults is permitted. Output: `state/verification_report.json`.
- [X] T000f-DefineHypothesizedEffects **Must run after T000e-VerifyScript-Run**: Extract numerical effect sizes (Cohen's d) from the verified citations in `state/verification_report.json` and write them to `state/effect_sizes.json`. **Input**: `state/verification_report.json` (must contain keys: `status`, `extracted_effect_size`, `source_id`). **Constraint**: If a citation does not yield a numerical effect size, the script MUST skip that entry, log a warning, and proceed with available data (do NOT halt the entire pipeline if other studies are valid). **Output**: `state/effect_sizes.json` containing keys: `status_high`, `status_low`, `observed_risky`, `observed_conservative`, `interaction`. **Schema**: `{"status_high": float, "status_low": float, ...}`.
- [X] T000c-PowerAnalysis **Must run after T000f-DefineHypothesizedEffects**: Implement `code/power_analysis.py`: Script that calculates minimum N for power=0.80 given effect sizes from `state/effect_sizes.json`. **Input**: `state/effect_sizes.json`. **Constraint**: Must read effect sizes directly from `state/effect_sizes.json` and validate that the values match the cited sources. If drift is detected, halt with an error. **Output**: N value written to `state/power_analysis_result.json`.
- [X] T000g-GenerateResearch **Must run after T000c-PowerAnalysis**: Generate `research.md` in `projects/PROJ-423-the-influence-of-simulated-social-status/specs/001-the-influence-of-simulated-social-status/` containing verified effect sizes (Cohen's d) and calculated sample size N. **Specifics**: Calculate N using `code/power_analysis.py` based on verified effect sizes (alpha=0.05, power=0.80). Write N and citations to `research.md`. **Output Schema**: Markdown file with YAML frontmatter containing keys: `effect_sizes` (dict with keys: `status_high`, `status_low`, `observed_risky`, `observed_conservative`, `interaction`), `sample_size` (int), `citations` (list), and `methodology` (string).
- [X] T000h-SimulateParams **Must run after T000g-GenerateResearch**: Generate `code/simulation_parameters.json` containing the verified effect sizes (for the Simulation Path), calculated N, and random seed. **Constraint**: This file serves as the Single Source of Truth for SC-004 (validity of risk-taking measure). Values MUST be populated ONLY from the verified sources in `research.md` and `state/effect_sizes.json`. **Explicitly include keys**: `injected_interaction_effect` (float, the hypothesized effect size), `ci_width_warning_threshold` (float, e.g., 0.5), `design_type` (string), `data_source` (string: "simulation" or "meta_analysis"), and `random_seed` (int).

---

## Phase 1: Setup & Foundational (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and data configuration prerequisites.

- [X] T001a [P] Create `data/` directory structure (`data/raw/`, `data/processed/`) with `.gitkeep` files to ensure tracking.
- [X] T001b [P] Create `code/` directory structure (`code/__init__.py`, `code/config.py`) with `.gitkeep` files.
- [X] T001c [P] Create `tests/` and `docs/` directory structures with `.gitkeep` files.
- [X] T002a [P] Create `code/requirements.txt` listing specific dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`, `jinja2`, `weasyprint`, `datasets`, `radon`.
- [X] T002b-CreateVenv [P] Create a clean virtual environment using `python3.11 -m venv.venv` to prepare for version pinning.
- [X] T002c-PinVersions [P] **Must run after T002b-CreateVenv**: Pin versions in `code/requirements.txt` for all dependencies listed in T002a using `pip freeze`. **Constraint**: Run this command in the clean virtual environment created in T002b-CreateVenv to ensure deterministic version pinning.
- [X] T003a [P] Create `.pre-commit-config.yaml` configuring ruff and black hooks.
- [X] T003b [P] Create `.gitignore` excluding `__pycache__`, `*.pyc`, `.env`, and **`data/processed/*.tmp`**, **`data/processed/__pycache__`**. **Constraint**: Do NOT exclude `data/processed/*.csv`. Processed CSVs MUST be tracked in Git to ensure the checksums recorded in `data/checksums.json` (T004) correspond to versioned artifacts. Note: `data/checksums.json` MUST be tracked to record integrity of processed data.
- [X] T004 [P] **Must run after T001a**: Create `data/checksums.json` with initial structure `{"files": {}}` to satisfy Constitution Principle III. **Constraint**: This file will be updated by the simulation, preprocessing, and checksum recording scripts to record checksums of raw and processed data.
- [X] T013b [P] **Must run after T013**: Implement `code/utils.py`: Function to calculate SHA256 checksum of a file and append the result to `data/checksums.json`. **Constraint**: This function must be called by T013 after `cleaned_data.csv` is written to ensure the processed artifact is checksummed even though it is gitignored.
- [X] T005 [P] Implement `code/logger.py` with a standard logging configuration (JSON format, file output) and **update** `code/config.py` to include a `LOGGING_CONFIG` dictionary.
- [X] T006 [P] Create `code/models.py` explicitly defining `Participant`, `Condition`, and `ModelResult` entities as Pydantic or dataclass models.
- [X] T007 [P] Setup pytest framework in `tests/` with `conftest.py` and `tests/contract/` directory.
- [X] T008 [P] Implement `code/utils.py` for common helpers (seeding, file I/O, checksum calculation).
- [X] T020b [P] **Must run before T025b**: Create `contracts/model_output.schema.yaml` with explicit content defining the schema for `data/processed/model_output.json` (keys: `coefficients`, `p_values`, `vif`, `ci_bounds`, `parameter_recovery`, `model_type`, `ci_width`; types: dict, dict, dict, dict, dict, string, float). **Constraint**: This file must be created as a YAML file in the `contracts/` directory.
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
- [X] T014a [US1] **Must run after T013**: Implement `code/preprocess.py`: Detect outcome variable type (binary vs. continuous) based on data distribution in `data/processed/cleaned_data.csv`. **Logic**: If unique values in `risk_taking_score` < 10, assume binary; else continuous. **Output**: Write the detected type (e.g., "binary" or "continuous") to `data/processed/outcome_type.json`. **Constraint**: Ensure `data/processed/outcome_type.json` is valid JSON with a single key `type`. **Schema**: `{"type": "binary" | "continuous"}`.

**⚠️ CRITICAL**: No user story work can begin until this phase (and T000f) is complete.

- [X] T010a [US1] **Must run after T000h-SimulateParams**: Read verified effect sizes and N from `code/simulation_parameters.json` and define them as constants in `code/config.py` for simulation parameters.
- [X] T010b-ExecuteDataSource [US1] **Must run after T000h-SimulateParams**: Implement `code/simulate.py` and `code/meta_analysis.py` logic in a single script `code/execute_data_source.py`. **Logic**: Read `data_source` from `code/simulation_parameters.json`. If "simulation", run `simulate.py` to generate `data/raw/simulation_output.csv`. If "meta_analysis", run `meta_analysis.py` to generate `data/raw/meta_analysis_output.csv`. **Constraint**: If `data_source` is "meta_analysis" but the registry (`projects/PROJ-423-the-influence-of-simulated-social-status/specs/001-the-influence-of-simulated-social-status/meta_registry.json`) is invalid or unreachable, the script MUST raise a hard error and halt. Do NOT fallback to simulation. **Valid Registry Definition**: A local JSON file at `projects/PROJ-423-the-influence-of-simulated-social-status/specs/001-the-influence-of-simulated-social-status/meta_registry.json` containing a list of study IDs and URLs with keys `study_id`, `url`, `effect_size`. Output: `data/raw/active_data_source.csv` (symlink or copy of the active source).
- [X] T010d-Merge [US1] **Must run after T010b-ExecuteDataSource**: Implement `code/preprocess.py`: Logic to select the active data source (simulation or meta-analysis) based on `code/simulation_parameters.json` and produce the unified `data/processed/cleaned_data.csv`. **Constraint**: If `data_source` is "meta_analysis" and the source file does not exist, raise a hard error. If `data_source` is "simulation" and the source file does not exist, raise a hard error. No silent fallbacks.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Synthesis and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset based on meta-analytic effect sizes OR aggregate real data via meta-analysis, and preprocess it for analysis, ensuring correct categorical factor integrity.

**Independent Test**: Verify that the output CSV contains required columns (`status_level`, `observed_behavior`, `risk_taking_score`, `participant_id`), that the data structure is correctly tagged, and that the random seed produces deterministic results.

**Note on Meta-Analysis Path**: The Spec (FR-001) allows an 'OR' path for meta-analysis. The implementation now includes `code/execute_data_source.py` (T010b) to handle this path if a valid dataset registry is provided. If no registry is provided, the Simulation Path is used by default.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/simulate.py`: Add a validation function that raises a `ValueError` with the message "Error: status_level has no variance. Experimental condition integrity violated." if the generated data lacks variance, and exit with code 1.
- [X] T012a [US1] Implement `code/preprocess.py`: Load raw synthetic data (or meta-analysis data), map `status_level` and `observed_behavior` to categorical factors (High/Low, Risky/Conservative).
- [X] T012b [US1] **Must run after T012a**: Implement `code/preprocess.py`: Implement the specific binning strategy (e.g., High vs Low/Medium) for input data with >2 levels. **Output**: Write a `binning_state.json` file to `data/processed/` with `binning_applied: true` if binning is used. **Constraint**: Do NOT modify `code/config.py`.
- [X] T012c-FlagAmbiguity [US1] **Must run after T012b**: Implement `code/preprocess.py`: Logic to flag ambiguity for manual review if the binning strategy is insufficient or ambiguous (e.g., if >2 levels remain after binning or mapping is ambiguous). **Output**: Write `ambiguity_flag.json` to `data/processed/` with `flag: true` if ambiguity detected. **Constraint**: If flag is true, downstream tasks MUST halt or prompt for manual review. **Logic**: "Insufficient" is defined as >2 levels remaining after binning.
- [X] T013 [US1] **Must run after T012c-FlagAmbiguity**: Implement `code/preprocess.py`: Handle missing values (imputation or exclusion) and report the final N used for analysis. **Constraint**: Output MUST be written to `data/processed/cleaned_data.csv`. The logic MUST preserve the `participant_id` granularity (do not aggregate rows) to ensure downstream design detection is possible. **Validation**: Verify `participant_id` column contains NO null values and NO duplicate entries for the same experimental condition before writing. If duplicates or nulls are found, raise `DataIntegrityError`.
- [X] T014b [P] [US1] **Parallel Task**: Review `code/preprocess.py` to ensure no legacy logic for regression family selection exists, as this logic is now explicitly implemented in T021a. **Constraint**: Verify that `code/preprocess.py` only handles data cleaning and does not modify regression family based on `outcome_type.json`.
- [X] T015 [P] [US1] Write `tests/contract/test_data_schema.py` to validate output CSV columns and data types against `data-model.md`.
- [X] T016 [P] [US1] Write `tests/unit/test_data_generation.py` to verify deterministic output given a fixed seed.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Adaptive Regression Analysis (Priority: P1)

**Goal**: Fit an adaptive regression model (Mixed-Effects if within-subjects, Fixed-Effects if between-subjects) to test the interaction, explicitly calculating VIF, Parameter Recovery, and 95% CI Width.

**Independent Test**: Run the model on the synthetic dataset with a known interaction effect and verify that the estimated coefficient matches the injected parameter within the confidence interval, and that the p-value is correctly calculated against the null.

### Implementation for User Story 2

- [X] T021b-ValidateDesign [US2] **Must run after T013 and T014a**: Implement `code/analysis.py`: Function `validate_design_structure` that reads `data/processed/cleaned_data.csv`.
 **Logic**:
 1. Count unique `participant_id` values vs total rows.
 2. If unique < total, set `design_type: "within-subjects"`, else `design_type: "between-subjects"`.
 3. Assert that the detected structure is consistent (e.g., no single participant has >100 rows which might indicate data corruption).
 4. Write the validated `design_type` to `data/processed/design_type.json` (intermediate file).
 **Constraint**: This task must raise an error if the detection is ambiguous or fails, preventing silent model mismatch. **Output Schema**: `data/processed/design_type.json` must contain `{"design_type": "between-subjects" | "within-subjects"}`.
- [X] T014c-FlagAmbiguousType [US2] **Must run after T014a**: Implement `code/analysis.py`: Logic to check `data/processed/outcome_type.json`. If the detected type is ambiguous (e.g., data is neither clearly binary nor continuous), write `ambiguity_type_flag.json` to `data/processed/` and halt. **Constraint**: This task ensures the spec's automatic detection logic is validated and does not fail silently.
- [X] T021d-GenerateConfig [US2] **Must run after T021b-ValidateDesign and T014c-FlagAmbiguousType**: Generate `data/processed/model_config.json` containing `design_type` (from T021b-ValidateDesign), `family_type` (from T014a), and `n_subjects`. **Constraint**: Do NOT hardcode values. The logic must inspect the actual `cleaned_data.csv` and `outcome_type.json` to determine the structure and family truthfully. **Output Schema**: `model_config.json` must contain keys: `design_type` (string), `family_type` (string), `n_subjects` (integer).
- [X] T021c-Alias [US2] **Must run after T021d-GenerateConfig**: Generate `data/processed/structure_config.json` as a copy or symlink of `data/processed/model_config.json` to satisfy the plan's artifact naming convention in "Contract Mapping". **Constraint**: Ensure both files have identical content.
- [X] T021a [US2] **Must run after T021d-GenerateConfig**: Implement `code/analysis.py`: Function `fit_adaptive_model` that reads `data/processed/model_config.json`.
 **Logic**:
 1. Read `design_type`. If "within-subjects", fit a Mixed-Effects model (`risk_taking ~ status_level * observed_behavior + (1|participant_id)`). If "between-subjects", fit a Fixed-Effects model (`risk_taking ~ status_level * observed_behavior`).
 2. Read `family_type`. Use `gaussian` family for continuous outcomes, `binomial` for binary outcomes.
 3. **Re-verification**: Before fitting, re-verify that the data in `cleaned_data.csv` matches the `design_type` and `family_type` in `model_config.json`. If mismatch, halt with a clear error.
 **Constraint**: Do NOT hardcode model type or family. The selection MUST be driven dynamically by the unified `model_config.json` generated in T021d-GenerateConfig. **Additional Constraint**: Assert that the formula string matches the `design_type` before fitting. **Fallback**: If bootstrap resampling fails due to memory, log a warning and use asymptotic standard errors (as per spec edge case), but do not fail silently for other errors.
- [X] T022 [US2] **Must run after T021a**: Implement `code/analysis.py`: Calculate Variance Inflation Factors (VIF) for all predictors and flag if > 5.0.
- [X] T023 [US2] **Must run after T021a**: Implement `code/analysis.py`: Extract fixed effects coefficients, standard errors, and p-values for the interaction term. **Explicitly calculate and write**: 1) The % Confidence Interval bounds (lower, upper) for the interaction coefficient to `data/processed/model_output.json`. 2) The "Parameter Recovery" metric (difference between estimated and injected effect size) to `data/processed/model_output.json`. 3) The **width of the 95% Confidence Interval** (Upper - Lower) as a top-level field `ci_width` in `data/processed/model_output.json`. **Constraint**: Read `injected_interaction_effect` from `code/simulation_parameters.json`.
- [X] T023b-SimulationValidation [US2] **Must run after T023 and T000h-SimulateParams**: Implement `code/analysis.py`: Logic to calculate "Parameter Recovery" by comparing the estimated interaction coefficient to the `injected_interaction_effect` loaded from `code/simulation_parameters.json` (set in T000h-SimulateParams) and checking if it falls within the confidence interval. **Dependency**: This task requires the injected parameter from `simulation_parameters.json` (T000h-SimulateParams) and the model output from T023. It is NOT parallelizable with T023. **Note**: This is a simulation validation metric, distinct from the primary scientific success criterion.
- [X] T023c-ValidateCIWidth [US2] **Must run after T023**: Implement `code/analysis.py`: Calculate and report the **width of the 95% Confidence Interval** for the interaction coefficient (Upper Bound - Lower Bound) as a standalone success metric for SC-003. Read `ci_width_warning_threshold` from `code/simulation_parameters.json` and flag if CI width exceeds this value. **Constraint**: Write `ci_width` to `data/processed/model_output.json` and log a warning if threshold exceeded.
- [X] T025a [P] [US2] **Must run after T024b-SchemaDef and T021c-Alias**: Write `tests/contract/test_model_config.py` to validate `data/processed/structure_config.json` (and `model_config.json`) against `contracts/model_config.schema.yaml`. **Constraint**: The test must explicitly check for the presence and type of all keys defined in T024b-SchemaDef.
- [X] T025b [P] [US2] **Must run after T020b**: Write `tests/contract/test_model_output.py` to validate model output schema (coefficients, p-values, VIF, ci_bounds, parameter_recovery, model_type, ci_width) against `contracts/model_output.schema.yaml`. **Constraint**: The test must explicitly check for the presence and type of all keys defined in T020b. **Execution**: Run `pytest tests/contract/test_model_output.py` to validate T023's output.
- [X] T026 [P] [US2] Write `tests/unit/test_analysis.py` to verify parameter recovery (estimated vs. injected effect size), correct family selection, CI width calculation, and **assert that `ci_width` is present in the output**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Sensitivity Analysis and Reporting (Priority: P2)

**Goal**: Conduct sensitivity analyses on outlier thresholds, perform post-hoc comparisons with Bonferroni correction, and generate reproducible reports with forest plots.

**Independent Test**: Manually alter the outlier threshold in config and verify the report explicitly lists the change in the headline effect size and p-value.

### Implementation for User Story 3

- [X] T030 [US3] **Must run after T023**: Implement `code/analysis.py`: Sensitivity analysis module to sweep outlier exclusion threshold over a range of standard deviations. **Strict Constraint**: Calculate absolute deviation from the *cell mean* within each of the 4 experimental conditions (High/Risky, High/Conservative, Low/Risky, Low/Conservative) before exclusion. Do NOT use a global mean. **Explicitly list sweep values**: {, 3.0, 3.5}. **Output**: Generate a table of means and confidence intervals for each condition at each threshold. **Output Schema**: CSV file `data/processed/sensitivity_sweep.csv` with columns: `threshold`, `interaction_coef`, `p_value`, `n_excluded`.
- [X] T031 [US3] **Must run after T023**: Implement `code/analysis.py`: Perform post-hoc pairwise comparisons with Bonferroni correction for all condition combinations, executing this logic UNCONDITIONALLY regardless of the primary interaction significance (per FR-006).
- [X] T031b-ValidateStability [US3] **Must run after T031**: Implement `code/analysis.py`: Logic to check if the interaction p-value remains < 0.05 across all outlier thresholds {2.5, 3.0, 3.5} as required by SC-002. **Output**: Write `stability_metric.json` to `data/processed/` with `stable: true/false` and a list of p-values. **Constraint**: This task explicitly performs the measurement required by SC-002. It reads p-values from `data/processed/sensitivity_sweep.csv`.
- [X] T035-ReportSchema [P] [US3] **Must run before T033**: Create `contracts/report_schema.yaml` explicitly defining the structure of the final report data, including keys: `model_table`, `vif_table`, `sensitivity_table`, `forest_plot_img`, `ci_width_metric`, `stability_metric`. **Constraint**: This schema ensures the report generation has a verifiable contract.
- [X] T032 [P] [US3] **Must run after T030**: Implement `code/report.py`: Generate forest plot of condition means with Confidence Intervals using `matplotlib/seaborn`. **Specifics**: Read the condition means and their 95% CIs from the descriptive statistics calculated in T030. Calculate the confidence interval for the mean risk-taking score of each of the four condition combinations and use these specific values for the plot error bars.
- [X] T032b [P] [US3] Create the directory `reports/templates/` and implement the file `reports/templates/analysis_report.html`. **Specifics**: This template must define the HTML structure for the final report, including placeholders `{{ model_table }}` (dict of coefficients), `{{ vif_table }}` (dict of VIFs), `{{ sensitivity_table }}` (dict of sensitivity results), `{{ forest_plot_img }}` (base64 string or path), `{{ ci_width_metric }}`, and `{{ stability_metric }}`. **Constraint**: The variable names passed to the Jinja2 template in `code/report.py` must match these placeholders exactly.
- [X] T033 [US3] **Must run after T035-ReportSchema, T032, T031b, T030**: Implement `code/report.py`: Generate PDF/HTML summary containing model coefficients, VIF table, sensitivity sweep results, and forest plot, saving to `reports/analysis_report.html`. Use `jinja2` to render `reports/templates/analysis_report.html` with the analysis data, and use `weasyprint` to convert the rendered HTML to a PDF. **Dependency**: Must depend on T035-ReportSchema. **Constraint**: Ensure `ci_width_metric` and `stability_metric` are explicitly included in the report.
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
- [X] T041a-Analysis [P] Refactor `code/analysis.py` using `radon` tool to reduce cyclomatic complexity to a lower, more manageable level for all functions. **Target Functions**: `fit_adaptive_model`, `sensitivity_sweep`. **Strategy**: Extract helper functions for VIF calculation and outlier filtering. **Command**: `radon cc -m 10 code/analysis.py`. **Acceptance Criteria**: max cyclomatic complexity <= 10.
- [X] T041b-Simulate [P] Refactor `code/simulate.py` using `radon` tool to reduce cyclomatic complexity to an acceptable threshold for all functions. **Command**: `radon cc -m 10 code/simulate.py`. Target: All functions with complexity >= 10.
- [X] T042a-Baseline [P] Profile `code/analysis.py` using `cProfile` and save output to `reports/baseline_profile.txt`.
- [X] T042b-PerformanceCheck [P] Verify that the full pipeline (simulation -> analysis -> report) completes within the time limit specified in Assumption. **Constraint**: If runtime exceeds the configured threshold or memory exceeds the configured threshold, log a warning but do not fail the build. The threshold values are explicitly set in `code/config.py`.
- [X] T044 Run `quickstart.md` validation to ensure full pipeline reproducibility

---

## Phase 6: Documentation & Plan Alignment (Post-Implementation)

**Purpose**: Address workflow inversion where the plan was finalized after task generation. These tasks are now MANDATORY to align the plan with the implementation before final acceptance.

- [X] T050 **Plan Alignment (Mandatory)**: Update `plan.md` to correct the sensitivity sweep threshold list from `{3.0, 3.5}` to `{2.5, 3.0, 3.5}` in the "Complexity Tracking" and "Phase 2" sections to match the implementation tasks. **Constraint**: This task acknowledges that the plan was not finalized prior to task generation and is being corrected retroactively. **Status**: Plan updated. **Must run after Phase 4 completion**.
- [X] T051 **Plan Alignment (Mandatory)**: Update `plan.md` to replace all references to `structure_config.json` with `model_config.json` OR acknowledge that `structure_config.json` is generated as an alias in T021c to maintain compatibility with the plan's existing contract mapping. **Constraint**: This task acknowledges that the plan was not finalized prior to task generation and is being corrected retroactively. **Status**: Plan updated. **Must run after Phase 4 completion**.
- [X] T052 **Plan Alignment (Mandatory)**: Update `plan.md` "Assumptions" section to explicitly state that the project relies on **simulated data based on meta-analytic parameters** as the primary input, and that the meta-analysis path is a secondary fallback only if a valid registry is provided, ensuring the "Assumption about data availability" is not misleading regarding the default execution path. **Constraint**: This task acknowledges that the plan was not finalized prior to task generation and is being corrected retroactively. **Status**: Plan updated. **Must run after Phase 4 completion**.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 0 completion (T000d-VerifyScript-Write, T000e-VerifyScript-Run, T000f-DefineHypothesizedEffects, T000c-PowerAnalysis, T000g-GenerateResearch, T000h-SimulateParams must run before T010a/T010b) - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Phase 6 (Documentation)**: Mandatory alignment steps; must be completed before project acceptance.

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
- **Critical Constraint**: The 'OR' path of FR-001 (simulation OR meta-analysis) is now fully implemented via T010b-ExecuteDataSource, with T010b failing loudly if a registry is provided but invalid.
- **Critical Constraint**: The `model_config.json` (T021d-GenerateConfig) is the single source of truth for both design structure and family type, ensuring T021a has all required parameters. `structure_config.json` (T021c-Alias) is generated as an alias to satisfy plan references.
- **Critical Constraint**: `data/checksums.json` is the source of truth for artifact integrity, including processed data files that are gitignored.
- **Critical Constraint**: The CI width (`ci_width`) is a required measurable outcome for SC-003 and must be reported in the final output.
- **Note on Plan.md**: The plan.md 'Complexity Tracking' table contains a typo in the sensitivity sweep thresholds (missing a specific threshold value). The tasks.md has been corrected to {2.5, 3.0, 3.5}. The plan.md has been updated retroactively (T050).
- **Note on Plan.md**: The plan.md 'Contract Mapping' section references `structure_config.json` while T021d-GenerateConfig generates `model_config.json`. The tasks.md now generates `structure_config.json` (T021c-Alias) as an alias to align with the plan's existing contract mapping (T051).
- **Note on Workflow**: Tasks T050, T051, T052 are now MANDATORY alignment steps to ensure the plan matches the implementation before final acceptance, satisfying the 'Single Source of Truth' principle.
- [X] T053 [P] [US1] **Revision Concern (Data Integrity)**: Implemented a strict validation step in `code/preprocess.py` (T013) that verifies the `participant_id` column contains NO null values and NO duplicate entries for the same experimental condition before writing `cleaned_data.csv`. If duplicates or nulls are found, the script MUST raise a `DataIntegrityError` and halt. **Rationale**: Prevents silent data corruption that could invalidate the design detection logic in T021b-ValidateDesign.
- [X] T054 [P] [US2] **Revision Concern (Parameter Drift)**: Added a runtime assertion in `code/analysis.py` (T023) that compares the `injected_interaction_effect` from `simulation_parameters.json` against the `injected_interaction_effect` stored in `data/processed/model_config.json` (if available) or re-calculates it from the simulation seed to detect potential parameter drift between the simulation and analysis phases. **Rationale**: Ensures the "Parameter Recovery" metric in T023b-SimulationValidation is comparing apples to apples, even if config files are manually edited.
- [X] T055 [P] [US3] **Revision Concern (Edge Case: Zero Variance in Cells)**: Implemented a check in `code/analysis.py` (T030) before calculating cell means for the sensitivity sweep. If any of the 4 experimental conditions has zero variance (all values identical), the script must log a `CriticalWarning` and exclude that specific condition from the sensitivity sweep calculation rather than crashing or producing NaN values. **Rationale**: Handles edge cases where the simulation or data generation produces degenerate conditions, ensuring the sensitivity analysis remains robust.
- [X] T056 [P] [US2] **Revision Concern (VIF Calculation Stability)**: Refactored the VIF calculation in `code/analysis.py` (T022) to use a numerically stable method (e.g., QR decomposition or SVD) if the design matrix is near-singular, rather than relying on standard matrix inversion which might fail on collinear predictors. **Rationale**: Ensures VIF calculation does not crash the pipeline on borderline collinear data, fulfilling FR-004 robustly.
- [X] T057 [P] [US3] **Revision Concern (Report Reproducibility)**: Implemented a checksum verification step in `code/report.py` (T033) that validates the input data files (`cleaned_data.csv`, `model_output.json`) against `data/checksums.json` before generating the report. If a mismatch is detected, the report generation MUST fail with a clear error message indicating which file has been tampered with. **Rationale**: Enforces Constitution Principle III (Data Hygiene) by ensuring the final report is generated from verified, untampered artifacts.