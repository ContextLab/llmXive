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

- [X] T000i-DefineSourcesSchema [P] **Must run before T000j**: Create `contracts/sources.schema.yaml` defining the expected schema for `sources_list.md` (or `sources_list.json`). **Constraint**: Must define 'citations' as a list of objects with 'doi' and 'title'.
- [X] T000j-CreateSourcesList [P] **Must run after T000i-DefineSourcesSchema**: Create `sources_list.md` (or `.json`) with the initial list of candidate citations (DOIs) for the meta-analysis/simulation parameters. **Constraint**: This file MUST exist before T000d runs. **Note**: This task is NOT parallel to T000i; it depends on the schema.
- [X] T000d-VerifyScript-Write [P] **Must run after T000j-CreateSourcesList**: Implement `code/verify_citations.py`: Script that accepts `--sources-file` argument, loads citations, validates them against primary sources using the `crossref` Python library to resolve DOIs and fetch metadata (Title overlap >= 0.7), and writes `state/verification_report.json`. **Constraint**: Must raise an error if any citation failed validation. **Input**: `sources_list.md` (or `.json`). **Output**: `state/verification_report.json` containing a `meta_analysis` section with `source_id` for each verified citation. **Note**: This task does NOT extract effect sizes; it only verifies DOI/Title existence.
- [X] T000e-VerifyScript-Run [P] **Must run after T000d-VerifyScript-Write**: Verify effect size citations listed in `sources_list.md` (input artifact) using the Reference-Validator Agent. **Execution**: Run `python code/verify_citations.py --sources-file sources_list.md`. **Constraint**: If validation fails (unreachable/mismatch), the process MUST halt with an error. No fallback to defaults is permitted. Output: `state/verification_report.json`.
- [X] T000f-DefineHypothesizedEffects [P] **Must run after T000e-VerifyScript-Run**: Extract numerical effect sizes (Cohen's d) from the verified citations in `state/verification_report.json` (specifically from the `meta_analysis` section defined in T000d) and write them to `state/effect_sizes.json`. **Input**: `state/verification_report.json`. **Constraint**: If *no* citations yield a numerical effect size, the script MUST raise a `ValueError` and halt. **Output Schema**: `state/effect_sizes.json` must contain a dict with key `extracted_values` which is a list of objects: `{"source_id": string, "effect_size": float}`.
- [X] T000c-PowerAnalysis [P] **Must run after T000f-DefineHypothesizedEffects**: Implement `code/power_analysis.py`: Script that calculates minimum N for power=0.80 given effect sizes from `state/effect_sizes.json`. **Input**: `state/effect_sizes.json`. **Constraint**: Must calculate N using `statsmodels.stats.power.tt_ind_solve_power` for a two-sample t-test interaction effect with alpha=0.05, power=0.80. **Traceability**: The calculated N MUST be explicitly linked to SC-004 (validity of risk-taking measure) and US-1 Acceptance Scenario 1 (at least [deferred] rows) in the output. **Output**: N value written to `state/power_analysis_result.json`.
- [X] T000g-GenerateResearch [P] **Must run after T000c-PowerAnalysis**: Generate `research.md` in `specs/001-the-influence-of-simulated-social-status-risk/` containing verified effect sizes (Cohen's d) and calculated sample size N. **Specifics**: Calculate N using `code/power_analysis.py` based on verified effect sizes (alpha=0.05, power=0.80). Write N and citations to `research.md`. **Output Schema**: Markdown file with YAML frontmatter containing keys: `effect_sizes` (dict), `sample_size` (int), `citations` (list of objects with 'doi', 'title', 'effect_size'), and `methodology` (string).
- [X] T000h-SimulateParams [P] **Must run after T000g-GenerateResearch**: Generate `code/simulation_parameters.json` containing the verified effect sizes (for the Simulation Path), calculated N, and random seed. **Constraint**: This file serves as the Single Source of Truth for SC-004 (validity of risk-taking measure). Values MUST be populated ONLY from the verified sources in `research.md` and `state/effect_sizes.json`. Explicitly include keys: `injected_interaction_effect` (float, the hypothesized effect size), `ci_width_warning_threshold` (float, a predefined threshold for confidence interval width), `design_type` (string), `data_source` (string: "simulation" or "meta_analysis"), and `random_seed` (int).
- [X] T000k-ValidateRiskInstrument [P] **Must run after T000g-GenerateResearch and T000h-SimulateParams**: Implement `code/validate_risk_instrument.py`: Script that reads `research.md` (methodology section) and `code/simulation_parameters.json` to verify that the `risk_taking_score` generation logic matches a standardized instrument (e.g., BART) as defined in the methodology. **Constraint**: If the instrument is not found or does not match, the script MUST raise a `ValueError` and halt. **Output**: `state/risk_instrument_validation.json` with `is_valid` and `instrument_name`. **Note**: This task is NOT parallel to T000g or T000h.

---

## Phase 1: Setup & Foundational (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and data configuration prerequisites.

**Execution Sequence**:
1. **Step 1**: Create directory structures (T001a, T001b, T001c).
2. **Step 2**: Create dependency files (T002a).
3. **Step 3**: Create and pin virtual environment (T002b, T002c).
4. **Step 4**: Setup pre-commit and gitignore (T003a, T003b).
5. **Step 5**: Initialize checksums and logging (T004, T005).
6. **Step 6**: Define models and test frameworks (T006, T007, T008).
7. **Step 7**: Define schemas and implement data logic (T020b, T024b-SchemaDef, T013b-ChecksumUtility, T010a, T010b-Effect, T010b-Null, T014a-MapAliases, T010b, T014a).

- [X] T001a [P] Create `data/` directory structure (`data/raw/`, `data/processed/`) with `.gitkeep` files to ensure tracking.
- [X] T001b [P] Create `code/` directory structure (`code/__init__.py`, `code/config.py`) with `.gitkeep` files.
- [X] T001c [P] Create `tests/` and `docs/` directory structures with `.gitkeep` files.
- [X] T002a [P] Create `code/requirements.txt` listing specific dependencies: `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `ruff`, `black`, `jinja2`, `weasyprint`, `datasets`, `radon`, `crossrefapi`.
- [X] T002b-CreateVenv [P] Create a clean virtual environment using `python3 -m venv.venv` to prepare for version pinning.
- [X] T002c-PinVersions [P] **Must run after T002b-CreateVenv**: Pin versions in `code/requirements.txt` for all dependencies listed in T002a using `pip freeze`. **Constraint**: Run this command in the clean virtual environment created in T002b-CreateVenv to ensure deterministic version pinning.
- [X] T003a [P] Create `.pre-commit-config.yaml` configuring ruff and black hooks.
- [X] T003b [P] Create `.gitignore` excluding `__pycache__`, `*.pyc`, `.env`, and **`data/processed/*.tmp`**, **`data/processed/__pycache__`**. **Constraint**: Do NOT exclude `data/processed/*.csv`. Processed CSVs MUST be tracked in Git to ensure the checksums recorded in `data/checksums.json` correspond to versioned artifacts. Note: `data/checksums.json` MUST be tracked to record integrity of processed data.
- [X] T004 [P] **Must run after T001a**: Create `data/checksums.json` with initial structure `{"files": {}}` to satisfy Constitution Principle III. **Constraint**: This file will be updated by the simulation, preprocessing, and checksum recording scripts to record checksums of raw and processed data.
- [X] T013b-ChecksumUtility [P] **Must run before T013**: Implement `code/utils.py`: Function to calculate SHA256 checksum of a file and append the result to `data/checksums.json`. **Constraint**: This function must be called by T013 after `cleaned_data.csv` is written to ensure the processed artifact is checksummed even though it is gitignored.
- [X] T005 [P] Implement `code/logger.py` with a standard logging configuration (JSON format, file output) and **update** `code/config.py` to include a `LOGGING_CONFIG` dictionary.
- [X] T006 [P] Create `code/models.py` explicitly defining `Participant`, `Condition`, and `ModelResult` entities as Pydantic or dataclass models.
- [X] T007 [P] Setup pytest framework in `tests/` with `conftest.py` and `tests/contract/` directory.
- [X] T008 [P] Implement `code/utils.py` for common helpers (seeding, file I/O, checksum calculation).
- [X] T020b [P] **Must run before T025b**: Create `contracts/model_output.schema.yaml` with explicit content defining the schema for `data/processed/model_results.json` (keys: `coefficients`, `p_values`, `vif`, `ci_bounds`, `parameter_recovery`, `model_type`, `ci_width`); types: dict, dict, dict, dict, dict, string, float). **Constraint**: This file must be created as a YAML file in the `contracts/` directory.
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
- [X] T010a [P] **Must run after T000h-SimulateParams**: Read verified effect sizes and N from `code/simulation_parameters.json` and define them as constants in `code/config.py` for simulation parameters. **Output**: Update `code/config.py` with these constants.
- [X] T010i-CreateRegistrySchema [P] **Must run after T010a**: Create `contracts/registry.schema.yaml` defining the schema for `data/registry/meta_analysis_registry.json`. **Constraint**: Must define 'studies' as a list of objects with 'study_id' and 'data_url'.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Synthesis and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset based on meta-analytic effect sizes OR aggregate real data via meta-analysis, and preprocess it for analysis, ensuring correct categorical factor integrity.

**Independent Test**: Verify that the output CSV contains required columns (`status_level`, `observed_behavior`, `risk_taking_score`, `participant_id`), that the data structure is correctly tagged, and that the random seed produces deterministic results.

**Note on Meta-Analysis Path**: The Spec (FR-001) allows an 'OR' path for meta-analysis. The implementation now includes `code/execute_data_source.py` (T010b-Effect/Null) to handle this path if a valid dataset registry is provided. If no registry is provided, the Simulation Path is used by default.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/simulate.py`: Add a validation function that raises a `ValueError` with the message "Error: status_level has no variance. Experimental condition integrity violated." if the generated data lacks variance, and exit with code 1.
- [X] T010b-Effect [US1] **Must run after T011, T000h-SimulateParams**: Implement `code/execute_data_source.py` logic for the **Effect Condition** AND EXECUTE IT. **Logic**: Run `code/simulation.py --condition effect --seed <RANDOM_SEED> --n <SAMPLE_SIZE>`. **Constraint**: Must generate `data/raw/simulated_data_effect.csv`. **Output**: `data/raw/simulated_data_effect.csv` with checksum recorded in `data/checksums.json`.
- [X] T010b-Null [US1] **Must run after T011, T000h-SimulateParams**: Implement `code/execute_data_source.py` logic for the **Null Condition** AND EXECUTE IT. **Logic**: Run `code/simulation.py --condition null --seed <RANDOM_SEED> --n <SAMPLE_SIZE>`. **Constraint**: Must generate `data/raw/simulated_data_null.csv`. **Output**: `data/raw/simulated_data_null.csv` with checksum recorded in `data/checksums.json`.
- [X] T012a [US1] **Must run after T010b-Effect, T010b-Null**: Implement `code/preprocess.py`: Load raw synthetic data (or meta-analysis data), map `status_level` and `observed_behavior` to categorical factors (High/Low, Risky/Conservative). **Constraint**: This is the first step in the preprocessing chain; it cannot run in parallel with T012b.
- [X] T012b [US1] **Must run after T012a**: Implement `code/preprocess.py`: Implement the specific binning strategy (e.g., High vs Low/Medium) for input data with >2 levels. **Mapping Logic**: Explicitly map 'High' -> 'High', and 'Low'/'Medium' -> 'Low'. **Output**: Write a `binning_state.json` file to `data/processed/` with `binning_applied: true` if binning is used. **Constraint**: Do NOT modify `code/config.py`.
- [X] T012c-FlagAmbiguity [US1] **Must run after T012b**: Implement `code/preprocess.py`: Logic to flag ambiguity for manual review if the binning strategy is insufficient or ambiguous. **Constraint**: 'Insufficient' is defined as: if any bin has < 5% of total N (where total N is the count of rows in the raw input data *before* any missing value handling) or if the mapping creates a bin with < 10 observations. **Output**: Write `ambiguity_flag.json` to `data/processed/` with `flag: true` if ambiguity detected. **Constraint**: If flag is true, downstream tasks MUST halt or prompt for manual review.
- [X] T014a-MapAliases [US1] **Must run after T012c-FlagAmbiguity**: Implement `code/preprocess.py`: Logic to map `risk_taking_score` column based on common aliases (e.g., `risk_score`, `pct_risk`, `risk_taking`) if the exact column name is missing. **Constraint**: If no alias matches, the script MUST raise a `ValueError` and halt. **Output**: A copy of the input data with the standardized column name `risk_taking_score`.
- [X] T013 [US1] **Must run after T014a-MapAliases and T012c-FlagAmbiguity**: Implement `code/preprocess.py`: Handle missing values (imputation or exclusion) and report the final N used for analysis. **Constraint**: Output MUST be written to `data/processed/cleaned_data_effect.csv` and `data/processed/cleaned_data_null.csv` (processing BOTH input files). The logic MUST preserve the `participant_id` granularity (do not aggregate rows) to ensure downstream design detection is possible. **Constraint**: Must include a validation step to detect and halt if duplicate `participant_id` entries are found for the same experimental condition. **Dependency**: Relies on T013b-ChecksumUtility for checksum recording.
- [X] T014a-TypeDetection [US1] **Must run after T013**: Implement `code/preprocess.py`: Detect outcome variable type (binary vs. continuous) based on data distribution in `data/processed/cleaned_data_effect.csv` and `data/processed/cleaned_data_null.csv`. **Logic**: If unique values in `risk_taking_score` < 10, assume binary; else continuous. **Output**: Write the detected type (e.g., "binary" or "continuous") to `data/processed/outcome_type.json`.
- [X] T014b [P] [US1] **Parallel Task**: Review `code/preprocess.py` to ensure no legacy logic for regression family selection exists, as this logic is now explicitly implemented in T021a. **Constraint**: Verify that `code/preprocess.py` only handles data cleaning and does not modify regression family based on `outcome_type.json`.
- [X] T015 [P] [US1] Write `tests/contract/test_data_schema.py` to validate output CSV columns and data types against `data-model.md`.
- [X] T016 [P] [US1] Write `tests/unit/test_data_generation.py` to verify deterministic output given a fixed seed.
- [X] T053a-DefineExceptions [P] **Must run before T053**: Create `code/exceptions.py` defining the `DataIntegrityError` class used in T053. **Constraint**: This class must inherit from `Exception` and accept a message string.
- [X] T053 [US1] **Revision Concern (Data Integrity)**: Implement a strict validation step in `code/preprocess.py` (T013) that verifies the `participant_id` column contains NO null values and NO duplicate entries for the same experimental condition before writing `cleaned_data.csv`. If duplicates or nulls are found, the script MUST raise a `DataIntegrityError` and halt. **Rationale**: Prevents silent data corruption that could invalidate the design detection logic in T021b-ValidateDesign.
- [X] T017 [US1] **Must run after T000k-ValidateRiskInstrument**: Generate `data/processed/validation_report.json` by reading `state/risk_instrument_validation.json` and formatting it to match FR-010 and SC-004 requirements. **Output**: `data/processed/validation_report.json` containing `instrument_name`, `is_valid`, and `source_file`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 2 - Adaptive Regression Analysis (Priority: P1)

**Goal**: Fit an adaptive regression model (Mixed-Effects if within-subjects, Fixed-Effects if between-subjects) to test the interaction, explicitly calculating VIF, Parameter Recovery, and 95% CI Width.

**Independent Test**: Run the model on the synthetic dataset with a known interaction effect and verify that the estimated coefficient matches the injected parameter within the confidence interval, and that the p-value is correctly calculated against the null.

### Implementation for User Story 2

- [X] T021b-ValidateDesign [US2] **Must run after T013**: Implement `code/analysis.py`: Function `validate_design_structure` that reads `data/processed/cleaned_data_effect.csv` and `data/processed/cleaned_data_null.csv`.
 **Logic**:
 1. Count unique `participant_id` values vs total rows.
 2. If unique < total, set `design_type: "within-subjects"`, else `design_type: "between-subjects"`.
 3. Assert that the detected structure is consistent (e.g., no single participant has > `MAX_ROWS_PER_PARTICIPANT` rows as defined in `config.py`).
 4. Write the validated `design_type` to `data/processed/design_type.json` (intermediate file).
 **Constraint**: This task must raise an error if the detection is ambiguous or fails, preventing silent model mismatch. **Output Schema**: `data/processed/design_type.json` must contain `{"design_type": "between-subjects" | "within-subjects"}`.
- [X] T014c-FlagAmbiguousType [US2] **Must run after T014a-TypeDetection**: Implement `code/analysis.py`: Logic to check `data/processed/outcome_type.json`. If the detected type is ambiguous (e.g., data is neither clearly binary nor continuous), write `ambiguity_type_flag.json` to `data/processed/` and halt. **Constraint**: This task ensures the spec's automatic detection logic is validated and does not fail silently.
- [X] T021c-GenerateConfig [US2] **Must run after T021b-ValidateDesign, T014a-TypeDetection, and T014c-FlagAmbiguousType**: Generate `data/processed/model_config.json` containing `design_type` (from T021b), `family_type` (from T014a), and `n_subjects`. **Constraint**: Do NOT hardcode values. The logic must inspect the actual `cleaned_data.csv` and `outcome_type.json` to determine the structure and family truthfully. Read `design_type` from `data/processed/design_type.json` and `family_type` from `data/processed/outcome_type.json`.
- [X] T021a [US2] **Must run after T021c-GenerateConfig**: Implement `code/analysis.py`: Function `fit_adaptive_model` that reads `data/processed/model_config.json`.
 **Logic**:
 1. Read `design_type`. If "within-subjects", fit a Mixed-Effects model with formula `risk_taking ~ status_level * observed_behavior + (1|participant_id)`. If "between-subjects", fit a Fixed-Effects model with formula `risk_taking ~ status_level * observed_behavior` (explicitly omitting the random effect term to avoid singular fit).
 2. Read `family_type`. Use `gaussian` family for continuous outcomes, `binomial` for binary outcomes.
 **Constraint**: Do NOT hardcode model type or family. The selection MUST be driven dynamically by the unified `model_config.json` generated in T021c-GenerateConfig. **Additional Constraint**: Assert that the formula string matches the `design_type` before fitting. Verify that statsmodels handles the between-subjects case correctly without singular fit errors.
- [X] T022 [US2] **Must run after T021a**: Implement `code/analysis.py`: Calculate Variance Inflation Factors (VIF) for all predictors on the design matrix generated by the model fit in T021a and flag if > 5.0.
- [X] T023 [US2] **Must run after T022**: Implement `code/analysis.py`: Extract fixed effects coefficients, standard errors, and p-values for the interaction term. **Explicitly calculate and write**: 1) The % Confidence Interval bounds (lower, upper) for the interaction coefficient to `data/processed/model_output_effect.json`. 2) The "Parameter Recovery" metric (difference between estimated and injected effect size) to `data/processed/model_output_effect.json`. 3) The **width of the 95% Confidence Interval** (Upper - Lower) as a top-level field `ci_width` in `data/processed/model_output_effect.json`. 4) The **VIF scores** calculated in T022 to `data/processed/model_output_effect.json`. **Constraint**: Read `injected_interaction_effect` from `code/simulation_parameters.json`. **Constraint**: If `injected_interaction_effect` is missing, the script MUST raise a `ValueError` and halt (NO fallback).
- [X] T023-Null [US2] **Must run after T021a (Null)**: Run the same analysis logic as T021a and T023 on the Null condition data (`cleaned_data_null.csv`) and write results to `data/processed/model_output_null.json`. **Constraint**: Must explicitly read the Null condition data and produce a separate output file.
- [X] T023b-SimulationValidation [US2] **Must run after T023 and T000h-SimulateParams**: Implement `code/analysis.py`: Logic to calculate "Parameter Recovery" by comparing the estimated interaction coefficient to the `injected_interaction_effect` loaded from `code/simulation_parameters.json` (set in T000h-SimulateParams) and checking if it falls within the calculated confidence interval. **Dependency**: This task requires the injected parameter from `simulation_parameters.json` (T000h-SimulateParams) and the model output from T023. It is NOT parallelizable with T023. **Constraint**: Read `injected_interaction_effect` from `code/simulation_parameters.json`. If `injected_interaction_effect` is missing, the script MUST halt. **Note**: This is a simulation validation metric, distinct from the primary scientific success criteria.
- [X] T023c-ValidateCIWidth [US2] **Must run after T023**: Implement `code/analysis.py`: Calculate and report the **width of the 95% Confidence Interval** for the interaction coefficient (Upper Bound - Lower Bound) as a standalone success metric for SC-003. Read `ci_width_warning_threshold` from `code/simulation_parameters.json` and flag if CI width exceeds this value.
- [X] T024 [US2] Implement `code/analysis.py`: Add fallback logic to use asymptotic standard errors if bootstrap resampling fails (memory constraints).
- [X] T025a [P] [US2] **Must run after T024b-SchemaDef and T021c-GenerateConfig**: Write `tests/contract/test_model_config.py` to validate `data/processed/model_config.json` against `contracts/model_config.schema.yaml`. **Constraint**: The test must explicitly check for the presence and type of all keys defined in T024b-SchemaDef.
- [X] T025b [P] [US2] **Must run after T020b**: Write `tests/contract/test_model_output.py` to validate model output schema (coefficients, p-values, VIF, ci_bounds, parameter_recovery, model_type, ci_width) against `contracts/model_output.schema.yaml`. **Constraint**: The test must explicitly check for the presence and type of all keys defined in T020b.
- [X] T026 [P] [US2] Write `tests/unit/test_analysis.py` to verify parameter recovery (estimated vs. injected effect size), correct family selection, CI width calculation, and **assert that `ci_width` is present in the output**.
- [X] T054 [US2] **Revision Concern (Parameter Drift)**: Add a runtime assertion in `code/analysis.py` to compare the `injected_interaction_effect` from `simulation_parameters.json` against the `injected_interaction_effect` stored in `data/processed/model_config.json` (if available) or re-calculates it from the simulation seed to detect potential parameter drift between the simulation and analysis phases. **Rationale**: Ensures the "Parameter Recovery" metric in T023b-SimulationValidation is comparing apples to apples, even if config files are manually edited.
- [X] T056 [US2] **Revision Concern (VIF Calculation Stability)**: Refactor the VIF calculation in `code/analysis.py` (T022) to use a numerically stable method (e.g., QR decomposition or SVD) if the design matrix is near-singular, rather than relying on standard matrix inversion which might fail on collinear predictors. **Rationale**: Ensures VIF calculation does not crash the pipeline on borderline collinear data, fulfilling FR-004 robustly.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 3: User Story 3 - Sensitivity Analysis and Reporting (Priority: P2)

**Goal**: Conduct sensitivity analyses on outlier thresholds, perform post-hoc comparisons with Bonferroni correction, and generate reproducible reports with forest plots.

**Independent Test**: Manually alter the outlier threshold in config and verify the report explicitly lists the change in the headline effect size and p-value.

### Implementation for User Story 3

- [X] T030 [US3] **Must run after T013 and T000h-SimulateParams**: Implement `code/analysis.py`: Sensitivity analysis module to sweep outlier exclusion threshold over a range of standard deviations. **Strict Constraint**: Calculate absolute deviation from the *fitted model's studentized residuals* (as defined in FR-005) for each data point. **Explicitly list sweep values**: {2.5, 3.0, 3.5} as per FR-005. **Output**: Generate a table of means and confidence intervals for each condition at each threshold, AND explicitly calculate and report the **interaction coefficient** and **p-value** variation across thresholds to `data/processed/sensitivity_analysis.csv`. **Constraint**: The output file MUST be named `sensitivity_analysis.csv` with columns `threshold_sd`, `interaction_coefficient`, `interaction_p_value`. **Note**: This task is the producer for T031, T031b, T032 and T033 and cannot run in parallel with them.
- [X] T031 [US3] **Must run after T030**: Implement `code/analysis.py`: Perform post-hoc pairwise comparisons with Bonferroni correction for all condition combinations, **ONLY IF** the primary interaction term is significant (p < 0.05). **Constraint**: If p >= 0.05, write an empty JSON object `{}` to `data/processed/posthoc_results.json` to ensure the file exists for downstream tasks. **Output**: `data/processed/posthoc_results.json`.
- [X] T031b-ValidateStability [US3] **Must run after T030**: Implement `code/analysis.py`: Logic to check if the interaction p-value remains < 0.05 across all outlier thresholds {2.5, 3.0, 3.5} as required by SC-002. **Output**: Write `stability_metric.json` to `data/processed/` with `stable: true/false` and a list of p-values. **Constraint**: This task explicitly performs the measurement required by SC-002.
- [X] T031c-ValidateSpecificity [US3] **Must run after T023-Null**: Implement `code/analysis.py`: Logic to validate the Null Condition. **Constraint**: Read `model_output_null.json` p-value and assert it is >= 0.05. If significant, flag pipeline failure. **Output**: `data/processed/specificity_validation.json`.
- [X] T035-ReportSchema [P] [US3] **Must run before T033**: Create `contracts/report_schema.yaml` explicitly defining the structure of the final report data, including keys: `model_table`, `vif_table`, `sensitivity_table`, `forest_plot_img`, `ci_width_metric`, `stability_metric`. **Constraint**: This schema ensures the report generation has a verifiable contract.
- [X] T032 [P] [US3] **Must run after T030**: Implement `code/report.py`: Generate forest plot of condition means with Confidence Intervals using `matplotlib/seaborn`. **Specifics**: Read the condition means and their 95% CIs from the descriptive statistics calculated in T030. Calculate the confidence interval for the mean risk-taking score of each of the four condition combinations and use these specific values for the plot error bars. **Constraint**: Output MUST be saved to `data/processed/forest_plot.png`.
- [X] T032b [P] [US3] Create the directory `reports/templates/` and implement the file `reports/templates/analysis_report.html`. **Specifics**: This template must define the HTML structure for the final report, including placeholders `{{ model_table }}` (dict of coefficients), `{{ vif_table }}` (dict of VIFs), `{{ sensitivity_table }}` (dict of sensitivity results), `{{ forest_plot_img }}` (base64 string or path), `{{ ci_width_metric }}`, and `{{ stability_metric }}`. **Constraint**: The variable names passed to the Jinja2 template in `code/report.py` must match these placeholders exactly.
- [X] T033 [US3] **Must run after T035-ReportSchema, T032, T030, T023, T022, T031, T017, and T031b**: Implement `code/report.py`: Generate PDF/HTML summary containing model coefficients, VIF table, sensitivity sweep results, post-hoc results (if applicable), and forest plot, saving to `reports/analysis_report.html`. **Traceability**: Explicitly generate `data/processed/traceability_report.json` linking every statistical result to a specific row in `cleaned_data.csv` and a specific block in `code/analysis.py`. Use `inspect` module to extract function names and line numbers from `code/analysis.py` to satisfy the traceability requirement. Use `jinja2` to render `reports/templates/analysis_report.html` with the analysis data, and use `weasyprint` to convert the rendered HTML to a PDF. **Constraint**: Ensure `ci_width_metric` and `stability_metric` are explicitly included in the report. **Constraint**: Ensure `data/processed/forest_plot.png` is copied to the final report location if generated elsewhere.
- [X] T036-ReportValidation [P] [US3] **Must run after T035-ReportSchema**: Write `tests/contract/test_report_schema.py` to validate the generated report structure (HTML content or parsed data) against `contracts/report_schema.yaml`.
- [X] T043a [P] [US3] Write `tests/unit/test_outlier_logic.py` to verify that changing the threshold in config updates the sensitivity table. **Specifics**: Create a test that manually alters the outlier threshold in a mock config, runs the sensitivity sweep, and asserts that the resulting table shows different exclusion counts and coefficient values.
- [X] T043b [P] [US2] Write `tests/unit/test_vif_logic.py` to verify VIF calculation and threshold flagging. **Specifics**: Create a test that feeds a dataset with known multicollinearity into the VIF calculator and asserts that the VIF values are correctly computed and flagged if > 5.0.
- [X] T043c [P] [US2] Write `tests/unit/test_parameter_recovery.py` to verify the logic in T023b-SimulationValidation (estimated vs. injected effect size). **Specifics**: Create a test that simulates data with a known interaction effect, runs the analysis, and asserts that the estimated effect falls within the calculated confidence interval.
- [X] T055 [US3] **Revision Concern (Edge Case: Zero Variance in Cells)**: Implement a check in `code/analysis.py` (T030) before calculating cell means for the sensitivity sweep. If any of the 4 experimental conditions has zero variance (all values identical), the script must log a `CriticalWarning` and exclude that specific condition from the sensitivity sweep calculation rather than crashing or producing NaN values. **Rationale**: Handles edge cases where the simulation or data generation produces degenerate conditions, ensuring the sensitivity analysis remains robust.
- [X] T057 [US3] **Revision Concern (Report Reproducibility)**: Implement a checksum verification step in `code/report.py` (T033) that validates the input data files (`cleaned_data.csv`, `model_results.json`) against `data/checksums.json` before generating the report. If a mismatch is detected, the report generation MUST fail with a clear error message indicating which file has been tampered with. **Rationale**: Enforces Constitution Principle III (Data Hygiene) by ensuring the final report is generated from verified, untampered artifacts.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] Update `quickstart.md` with specific execution steps and dependencies
- [X] T040b [P] Add comprehensive docstrings to `code/generate_data.py`, `code/analysis.py`, and `code/report.py`
- [ ] T041a-Analysis [P] Refactor `code/analysis.py` using `radon` tool to reduce cyclomatic complexity to a lower, more manageable level for all functions. **Target Functions**: `fit_adaptive_model`, `sensitivity_sweep`. **Strategy**: Extract helper functions for VIF calculation and outlier filtering. **Command**: `radon cc -m 10 code/analysis.py`. **Acceptance Criteria**: Max complexity < 10.
- [ ] T041b-Simulate [P] Refactor `code/simulate.py` using `radon` tool to reduce cyclomatic complexity to an acceptable threshold for all functions. **Command**: `radon cc -m 10 code/simulate.py`. Target: All functions with complexity >= 10.
- [ ] T042a-Baseline [P] Profile `code/analysis.py` using `cProfile` and save output to `reports/baseline_profile.txt`.
- [X] T042b-PerformanceCheck [P] Verify that the full pipeline (simulation -> analysis -> report) completes within the time limit specified in Assumption. **Constraint**: If runtime exceeds the configured threshold or memory exceeds the configured threshold, log a warning but do not fail the build. The threshold values are explicitly set in `code/config.py`.
- [X] T043d [P] [US3] **Must run after T033**: Run `quickstart.md` validation to ensure full pipeline reproducibility. **Constraint**: This task executes the full pipeline as documented in `quickstart.md` and asserts successful completion.

---

## Phase 7: Final Validation & Execution Readiness

**Purpose**: Ensure the pipeline is ready for final execution and that all edge cases are covered before the first full run.

- [X] T060 [P] **Final Integration Test**: Implement `tests/integration/test_full_pipeline.py` that executes the entire workflow from simulation to report generation in a single test run, asserting that all intermediate files are created and checksums match. **Constraint**: This test must be marked as `@pytest.mark.slow` and should only run in the final CI/CD stage.
- [X] T061 [P] **Memory Leak Check**: Implement a memory profiling step in `code/analysis.py` (T030) to ensure that the sensitivity sweep does not cause memory leaks when processing large datasets. **Constraint**: Use `tracemalloc` to track memory usage and log a warning if usage exceeds 80% of available RAM.
- [X] T062 [P] **Cross-Platform Compatibility**: Verify that the pipeline runs correctly on both Linux (GitHub Actions) and macOS (local development) by testing file path handling and dependency compatibility. **Constraint**: Ensure all file paths use `pathlib.Path` for cross-platform compatibility.

---

## Revision Concerns & Data Integrity (New)

**Purpose**: Address specific reviewer concerns regarding data integrity, parameter drift, edge cases, and numerical stability identified during analysis.

*Note: Tasks T053a, T053, T054, T055, T056, and T057 have been consolidated into their respective Phase 2 and Phase 3 sections above to ensure unique execution order and avoid duplication. This section is kept for reference but contains no duplicate tasks.*

- [X] T053a-DefineExceptions [P] **Must run before T053**: Create `code/exceptions.py` defining the `DataIntegrityError` class used in T053. **Constraint**: This class must inherit from `Exception` and accept a message string.
- [X] T053 [US1] **Revision Concern (Data Integrity)**: Implement a strict validation step in `code/preprocess.py` (T013) that verifies the `participant_id` column contains NO null values and NO duplicate entries for the same experimental condition before writing `cleaned_data.csv`. If duplicates or nulls are found, the script MUST raise a `DataIntegrityError` and halt. **Rationale**: Prevents silent data corruption that could invalidate the design detection logic in T021b-ValidateDesign.
- [X] T054 [US2] **Revision Concern (Parameter Drift)**: Add a runtime assertion in `code/analysis.py` to compare the `injected_interaction_effect` from `simulation_parameters.json` against the `injected_interaction_effect` stored in `data/processed/model_config.json` (if available) or re-calculates it from the simulation seed to detect potential parameter drift between the simulation and analysis phases. **Rationale**: Ensures the "Parameter Recovery" metric in T023b-SimulationValidation is comparing apples to apples, even if config files are manually edited.
- [X] T055 [US3] **Revision Concern (Edge Case: Zero Variance in Cells)**: Implement a check in `code/analysis.py` (T030) before calculating cell means for the sensitivity sweep. If any of the 4 experimental conditions has zero variance (all values identical), the script must log a `CriticalWarning` and exclude that specific condition from the sensitivity sweep calculation rather than crashing or producing NaN values. **Rationale**: Handles edge cases where the simulation or data generation produces degenerate conditions, ensuring the sensitivity analysis remains robust.
- [X] T056 [US2] **Revision Concern (VIF Calculation Stability)**: Refactor the VIF calculation in `code/analysis.py` (T022) to use a numerically stable method (e.g., QR decomposition or SVD) if the design matrix is near-singular, rather than relying on standard matrix inversion which might fail on collinear predictors. **Rationale**: Ensures VIF calculation does not crash the pipeline on borderline collinear data, fulfilling FR-004 robustly.
- [X] T057 [US3] **Revision Concern (Report Reproducibility)**: Implement a checksum verification step in `code/report.py` (T033) that validates the input data files (`cleaned_data.csv`, `model_results.json`) against `data/checksums.json` before generating the report. If a mismatch is detected, the report generation MUST fail with a clear error message indicating which file has been tampered with. **Rationale**: Enforces Constitution Principle III (Data Hygiene) by ensuring the final report is generated from verified, untampered artifacts.

---

## Phase 6: Documentation & Plan Alignment (Post-Implementation)

**Purpose**: Address workflow inversion where the plan was finalized after task generation. These tasks are now MANDATORY to align the plan with the implementation before final acceptance.

**Note**: Tasks T050, T051, T052 have been removed from this list as they are non-implementation documentation maintenance tasks that do not produce code artifacts and should not block the implementation flow. Plan corrections will be handled via a separate documentation workflow.

- [X] T070 [P] **Documentation Alignment**: Update `plan.md` to explicitly reference the "Simulation-First" approach and the specific `code/simulation_parameters.json` schema as the Single Source of Truth for all simulation parameters, ensuring the plan matches the implemented task flow.
- [X] T071 [P] **Research.md Validation**: Run `code/verify_citations.py` one final time against the `sources_list.md` used to generate `research.md` to ensure all effect sizes cited in the plan are still valid and accessible before the final execution run.
- [ ] T072 [P] **Edge Case Documentation**: Update `quickstart.md` to include a section on "Edge Case Handling" detailing the specific behaviors of T053 (Data Integrity), T055 (Zero Variance), and T057 (Checksum Verification) so that human reviewers understand the pipeline's robustness.