# Tasks: The Influence of Perceived Agency in AI Interactions on Trust

**Input**: Design documents from `specs/001-perceived-agency-trust/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **REQUIRED** to ensure reproducibility and validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Pre-Phase 0: Validation Gates (MANDATORY)

**Purpose**: Verify citations and scale text against primary sources BEFORE any implementation begins.
**⚠️ CRITICAL**: If T000 or T000b fail, the project transitions to `human_input_needed` immediately. No downstream tasks can run.

- [ ] T000 [Const-II] **Gate**: Validate citation metadata (Title & DOI) against primary source. **Input**: `spec.md` and `plan.md`. **Logic**:
 1. Parse `spec.md` and `plan.md` to extract the project's claimed citations (e.g., "Lee & See (2004)", "Langer (1975)").
 2. Compare these claims against the **Primary Source Truth** (hardcoded in this task):
 - Lee & See: DOI "", Title "Trust in Automation: Designing for Appropriate Reliance".
 - Langer (1975): DOI "10.1037/h0076860", Title "The Illusion of Control".
 3. Verify that the **Title** and **DOI** in the project documents match the Primary Source Truth exactly.
 4. **Constraint**: If the metadata does not match or the DOI is invalid, raise `SystemExit(1)` with message "Citation Validation Failed". **Recovery**: Project transitions to `human_input_needed`.
 **Output**: `research/validation_report.json` (only if successful) containing: `title`, `doi`, `overlap_score`, `content_verified`, `status`, `source_url`. **Dependency**: None.
- [ ] T000b [Const-II] **Gate**: Validate the *text content* of the Lee & See (2004) scale items against the primary source. **Input**: `spec.md` (to find claimed scale items) and the Primary Source Truth. **Logic**:
 1. Define the **Primary Source Truth** for the Lee & See (2004) 12-item Trust in Automation Scale (hardcoded):
 - "The AI's performance is predictable. "
 - "The AI's performance is consistent. "
 - "The AI's performance is reliable. "
 - "The AI's performance is accurate. "
 - "The AI's performance is trustworthy. "
 - "The AI's performance is safe. "
 - "The AI's performance is effective."
 - "The AI's performance is competent. "
 - "The AI's performance is helpful. "
 - "The AI's performance is honest. "
 - "The AI's performance is benevolent. "
 - "The AI's performance is open. "
 2. Extract the scale items claimed in `spec.md`/`plan.md`.
 3. Compare the claimed items against the Primary Source Truth exactly.
 4. **Constraint**: If the text does not match the 12-item structure, raise `SystemExit(1)` with message "Scale text mismatch". **Recovery**: Project transitions to `human_input_needed`.
 **Output**: `research/scale_text_validation.json` (only if successful) containing: `status`, `items_verified`. **Dependency**: T000.

---

## Phase 0: Research & Validation (Prerequisites)

**Purpose**: Verify citations, execute power analysis, and generate research artifacts before implementation begins.

**Strict Sequence**: T000b -> T001a-1 -> T001a-2 -> T001b-1 -> T001b-2 -> T002 -> T003-1 -> T008 -> T010b -> T011 -> T007g.
**Reasoning**: T001a-1 parses plan schema. T001a-2 verifies plan intent and generates the report. T001b-1 extracts citations. T001b-2 writes lit review. T002 calculates power. T003-1 validates. T008 configures environment. T010b/T011/T007g finalize scale verification for downstream use.
**Note**: Completion of T010b, T011, and T007g is a **REQUIRED PREREQUISITE** for the transition to Phase 1 (Setup) and Phase 2 (Foundational).

- [ ] T001a-1 [P] [Dataset Fit] Parse `plan.md` to locate the 'Technical Context' and 'Project Structure' sections. **Logic**:
 1. Split `plan.md` content by the header `## Technical Context` and `## Project Structure`.
 2. Search within those blocks for variable definitions using the regex pattern: `(Condition ID|Adherence Rate|Trust Score|Perceived Agency Score|Attention Check Status)`.
 3. Extract the text describing required variables.
 **Output**: `research/dataset_schema_parsed.txt` containing the extracted text. **Dependency**: T000b.
- [ ] T001a-2 [P] [Dataset Fit] Verify the *plan's intent* to capture required variables and generate the report. **Logic**:
 1. Read `research/dataset_schema_parsed.txt` (from T001a-1) and `spec.md` to confirm that the *requirements* (FR-002, US-1) explicitly mandate the capture of the identified variables.
 2. **Generate Artifact**: Write `research/dataset_verification_report.md` (or `.json`) with a clear "Verified" status if the plan/spec mandates the variables. If not, raise `SystemExit(1)`.
 **Output**: `research/dataset_verification_report.md` (or `.json`) containing a list of verified variables and a "Verified" status. **Dependency**: T001a-1.
- [ ] T001b-1 [P] [Lit Review] Extract citation metadata and content from `research/validation_report.json` (T000) for "Lee & See (2004)" and "Langer (1975)". **Logic**: If `source_url` is present, fetch the abstract/findings. If not, use the `content_verified` summary from the validator. **Output**: `research/citation_metadata.json` containing `title`, `doi`, `summary_findings` (string). **Dependency**: T000b.
- [ ] T001b-2 [P] [Lit Review] Generate the literature review summary required by Plan.md Phase 0. **Logic**: Summarize key findings from "Lee & See (2004)" and "Langer (1975)" regarding trust and perceived control, using the `summary_findings` from T001b-1. **Output**: `research/literature_review.md`. **Dependency**: T001b-1.
- [X] T002 [P] Execute pre-study power analysis calculation for **planned directional contrasts** AND **overall ANOVA** using Python `scipy` and `numpy`. **Script**: `code/research/power_analysis.py`. **Args**: **HARDCODED DESIGN PARAMETERS** for the initial run: `effect_size` (f=0.25, medium), `alpha` (0.05), `power` (0.80). **Logic**:
 1. Calculate the required sample size (N) specifically for the **planned directional contrasts** (High vs. Low, and Combined vs. Control) using contrast-specific effect size formulas.
 2. Calculate the required sample size (N) for the **overall One-Way ANOVA** design.
 3. **Final N**: Select `max(N_contrast, N_ANOVA)` to ensure the study is powered for both.
 **Contrast Coefficients**: 1) High vs. Low: [Negative, Positive, Neutral], 2) (High+Low) vs. Control: [positive, positive, negative].
 **Implementation**:
```python
import numpy as np
from scipy.stats import ncf, f

def calculate_contrast_power(effect_size, alpha, power_target, n_groups=3):
 c1 = np.array([-1, 1, 0])
 c2 = np.array([1, 1, -2])
 c1 = c1 / np.linalg.norm(c1)
 c2 = c2 / np.linalg.norm(c2)
 for n_per_group in range(10, 1000):
 N = n_per_group * n_groups
 # Non-centrality parameter for the contrast
 lambda_val = N * (effect_size ** 2) * np.sum(c1 ** 2)
 df1 = 1
 df2 = N - n_groups
 power = 1 - ncf.cdf(ncf.ppf(1-alpha, df1, df2), df1, df2, lambda_val)
 if power >= power_target:
 return n_per_group
 return None

def calculate_anova_power(effect_size, alpha, power_target, n_groups=3):
 # Standard ANOVA power calculation
 # lambda = N * f^2
 for n_per_group in range(10, 1000):
 N = n_per_group * n_groups
 lambda_val = N * (effect_size ** 2)
 df1 = n_groups - 1
 df2 = N - n_groups
 power = 1 - ncf.cdf(ncf.ppf(1-alpha, df1, df2), df1, df2, lambda_val)
 if power >= power_target:
 return n_per_group
 return None

# Run both and take max
n_contrast = calculate_contrast_power(0.25, 0.05, 0.80)
n_anova = calculate_anova_power(0.25, 0.05, 0.80)
final_n = max(n_contrast, n_anova)
```
**Output**: `research/power_calculation.json` (machine-readable data with keys `params` and `results`). **Schema**: `params` (effect_size, alpha, power, contrast_type), `results` (required_n, calculated_n_contrast, calculated_n_anova, final_n). **Dependency**: T000b, T001a-1.
- [ ] T003-1 [P] Validate `research/literature_review.md` and `research/power_calculation.json` against `plan.md` Phase 0 requirements. **Logic**: Assert that `research/literature_review.md` contains the required summary and that `research/power_calculation.json` has the correct keys. **Dependency**: T002, T001a-2, T001b-2.
- [X] T008 [P] Setup environment configuration management by creating `code/experiment/config.yaml`. **Structure**: YAML with keys: `sample_size` (read from `research/power_calculation.json` at key `results.final_n`), `alpha_level` (default 0.05), `seed` (default 42), `data_path` (default `data/raw/`), `sensitivity_config` (object containing sweep ranges for adherence, attention, etc.). **Logic**:
 1. The `sensitivity_config` object MUST define the following keys with explicit numeric ranges derived from `docs/protocol.md` (once generated) or default to a standard scientific range:
 - `attention_pass_rate`: { "start": 0.80, "end": 1.00, "step": 0.05 }
 - `straight_line_threshold`: { "start": 0.80, "end": 1.00, "step": 0.05 }
 - `adherence_rate_cutoff`: { "start": 0.50, "end": 0.95, "step": 0.05 } (Values MUST be justified in `docs/protocol.md`).
 - `trust_outlier_std`: { "start": 2.0, "end": 3.5, "step": 0.5 }
 2. Write this configuration to `code/analysis/config.yaml`.
 **Dependency**: T002.
- [ ] T010b [P] [SC-004] Retrieve the canonical Lee & See (2004) Trust Scale. **Logic**:
 1. Verify that `research/scale_text_validation.json` (from T000b) confirms "Lee & See (2004)" text is valid.
 2. Use the hardcoded reference list of items (verified in T000b) to create the scale file.
 3. Write the 12 items as a JSON array of strings to `docs/trust_scale_items.md`.
 4. **Constraint**: If the source fetch fails or format is invalid, raise `SystemExit(1)` with message "Canonical trust scale source missing or invalid".
 **Output**: `docs/trust_scale_items.md` (JSON array of 12 strings). **Dependency**: T000b.
- [X] T011 [P] [SC-004] Verify `docs/trust_scale_items.md` (from T010b) matches the validated text. **Logic**: Read `docs/trust_scale_items.md` and compare against the hardcoded reference list from T000b. If valid, confirm. **Requirement**: This file must match the validated citation in T000b. **Dependency**: T010b.
- [ ] T007g [P] [SC-004] Generate `research/trust_scale_verification_report.md`. **Logic**: Read `research/scale_text_validation.json` (from T000b). If "Lee & See (2004)" is valid, extract the 12-item scale from `docs/trust_scale_items.md` (created by T010b) and verify it matches the source. Write a report confirming the items are verified and ready for use. **Output**: `research/trust_scale_verification_report.md`. **Dependency**: T000b, T010b, T011.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Strict Sequence**: T004 -> T010 -> T009 -> T012 -> T017i -> T017h -> T015 -> T016.
**Note**: This phase depends on the completion of Phase 0 (including T010b, T011, T007g). T009 explicitly requires T010b and T011 to be completed.

- [ ] T004 [P] Create project directory structure. **Command**: `mkdir -p code/experiment code/experiment/tests code/analysis code/analysis/tests data/raw data/processed docs specs/001-perceived-agency-trust/contracts`. **Files**: Create `__init__.py` in all `code/` subdirectories and `tests/` subdirectories.
- [ ] T005 [P] Initialize Python project with pinned dependencies in `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pingouin, pytest, requests, pyyaml, jsonschema).
- [ ] T006 [P] Configure linting (flake8/black) and formatting tools. **Deliverables**: Create `.flake8` with specific rules (e.g., max-line-length=88) and `pyproject.toml` for black configuration. **Verification**: Run `black --check.` and ensure exit code 0.
- [ ] T009 [P] [FR-001] Create **Final** data schema contracts in `specs/001-perceived-agency-trust/contracts/`. **Content**:
 1. `participant.schema.yaml`: Define fields: `participant_id` (string, UUID), `condition` (enum: High, Low, Control), `adherence_rate` (float, non-negative scale), `trust_score` (float, 1-5), `attention_check` (boolean). **CRITICAL**: Populate `trust_item_1` to `trust_item_12` fields with the verbatim text from `docs/trust_scale_items.md` (T010b/T011) immediately. Do NOT use placeholders. Use a Python script to read the JSON array from `docs/trust_scale_items.md` and write the YAML schema with keys `trust_item_1`, `trust_item_2`,..., `trust_item_12` containing the exact string values.
 2. `analysis_output.schema.yaml`: Define fields for ANOVA results, contrasts, and effect sizes.
 3. `power_analysis.schema.yaml`: Define fields for power analysis parameters and results.
 **Dependency**: T004, T010b, T011. **Note**: This schema is final and includes the verified text.
- [ ] T012 [P] [SC-004] Finalize data schema contracts in `specs/001-perceived-agency-trust/contracts/`. **Content**:
 1. Ensure `participant.schema.yaml` (from T009) is complete and matches the spec.
 2. Merge trust scale items into `participant.schema.yaml` explicitly (already done in T009).
 **Dependency**: T009.
- [ ] T010 [P] Create base data processing utilities in `code/analysis/data_utils.py`. **Functions**: `load_csv(path)`, `compute_checksum(path, algorithm="sha256")`, `scan_pii(df)`. **Logic**: Implement SHA-256 checksumming and PII scanning rules (e.g., flag columns with "email", "name"). **Dependency**: T004.
- [ ] T017i [P] [SC-004] Generate `data-model.md` in `docs/`. **Content**: Description of data entities (Participant, Condition, Result) and their relationships, referencing `contracts/`. **Dependency**: T012.
- [ ] T017h [P] [SC-004] Generate `quickstart.md` in `docs/`. **Content**: Step-by-step instructions for local setup, running the experiment interface, and executing the analysis pipeline. **Dependency**: T017i, T012. **Note**: Dependency list ensures correct order.
- [ ] T015 [P] [Plan Element] Produce experimental interface design specification in `docs/design/interface_design.md`. **Content**: Wireframes or UI flow diagram for High/Low/Control conditions using Mermaid code blocks. **Requirement**: Explicitly reference Plan Element FR-001 and US-1. **Dependency**: T006.
- [ ] T016 [P] [Plan Element] Produce analysis pipeline specification in `docs/design/analysis_pipeline_spec.md`. **Content**: Algorithm flow, statistical test definitions, and data cleaning rules using Mermaid code blocks. **Requirement**: Explicitly reference Plan Element US-2 and US-3. **Dependency**: T006.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. **Note**: Ensure T012 and T007g are complete before proceeding to T024.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase depends on the completion of Phase 0 (including T010b, T011, T007g) and Phase 1 Setup.

- [ ] T018 [P] [FR-001] Implement randomization logic in `code/experiment/randomization.py` (assigns High/Low/Control with fixed seed for reproducibility). **Requirement**: Explicitly implement randomized assignment to ensure independent variable manipulation (FR-001). **Dependency**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Experimental Task Execution and Data Capture (Priority: P1) 🎯 MVP

**Goal**: Present the simulated decision-making task with randomized conditions and capture behavioral/psychometric data.

**Independent Test**: A test runner can simulate a participant session, verify randomization, confirm illusory controls don't alter AI output, and validate the survey export schema.

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement "High Agency" condition interface in `code/experiment/app.py` (functional sliders that do NOT alter AI output). **Dependency**: T018, T010.
- [ ] T020 [P] [US1] Implement "Low Agency" condition interface in `code/experiment/app.py` (restricted controls). **Dependency**: T018, T010.
- [ ] T021 [P] [US1] Implement "Control" condition interface in `code/experiment/app.py` (static AI display). **Dependency**: T018, T010.
- [ ] T022 [US1] [FR-002] Implement adherence tracking logic in `code/experiment/app.py`. **Requirement**: Capture behavioral adherence as a percentage. **Formula**: `The adherence rate is defined as the proportion of AI recommendations followed relative to the total number of recommendations, expressed as a percentage. [UNRESOLVED-CLAIM: c_339f150a — status=not_enough_info] `. **Variable**: `adherence_rate` (float). **Dependency**: T018, T010.
- [ ] T023 [US1] Implement attention check questions and straight-lining detection in `code/experiment/app.py`. **Questions**: Include standard attention checks. (e.g., "Select 'Strongly Agree'"). **Logic**: Flag if a consecutive sequence of responses is identical. **Output**: `attention_check_status` (boolean). **Dependency**: T018, T010.
- [ ] T024 [US1] [FR-002] [SC-004] Implement Lee & See (2004) Trust Scale items in `code/experiment/app.py` survey section. **Requirement**: Read verbatim 12-item scale from `docs/trust_scale_items.md` at runtime. **Format**: JSON array of strings. **Parsing**: Map items to `trust_item_1` through `trust_item_12`. **Action**: If file is missing or format is not JSON array, raise explicit error and halt execution. **UI**: Use `st.radio` with `options=['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']` mapping to 1-5 integers. **Variable Names**: `trust_item_1` through `trust_item_12`. **Note**: This task implements the UI and loading logic. The *runtime verification gate* is handled by T024b. **Dependency**: T018, T010, T010b artifact exists, T011 artifact exists, T000b artifact exists.
- [ ] T024b [US1] [FR-002] [SC-004] **Runtime Verification Gate** for Trust Scale. **Logic**: Before the experiment starts, load `docs/trust_scale_items.md` and compare them **exactly** (string equality) against the verified list in `research/trust_scale_verification_report.md` (from T007g). If the loaded items do NOT match the verified text exactly, **raise SystemExit(1) and block the experiment from starting**. **Dependency**: T024, T007g.
- [ ] T024c [US1] [FR-002] [SC-001] Implement Trust Score aggregation logic in `code/experiment/app.py`. **Requirement**: Calculate the aggregate Trust Score as the mean of `trust_item_1` through `trust_item_12` for each participant. **Variable**: `trust_score` (float). **Action**: Store this calculated value in the exported data. **Dependency**: T024.
- [ ] T025 [US1] Implement data export logic to `data/raw/` with checksum generation and filename timestamping. **Requirement**: Ensure export schema matches `participant.schema.yaml` (finalized in T009/T012). **Dependency**: T018, T010, T024c, T024b.
- [ ] T025b [US1] [SC-004] Implement runtime schema validation in `code/experiment/app.py` before data export. **Requirement**: Validate that the collected data strictly adheres to `participant.schema.yaml` (specifically the 12 trust items) before writing to `data/raw/`. **Action**: If validation fails, raise error and prevent export. **Dependency**: T025, T012.
- [ ] T026 [US1] Implement manipulation check question for "Perceived Agency". **Question**: "To what extent did you feel you had control over the AI's recommendations?" **Scale**: 1-7 Likert. **Variable**: `perceived_agency_score`. **Constraint**: This score is **ONLY** for descriptive analysis and reporting. It MUST NOT be used as a covariate, filter, or exclusion criterion for the primary trust outcome calculation to ensure Behavioral Outcome Isolation (Constitution VII). **Dependency**: T018, T010.

### Tests for User Story 1

- [ ] T027 [P] [US1] Unit test for randomization logic in `code/experiment/tests/test_randomization.py` (verify condition distribution and seed stability).
- [ ] T028 [P] [US1] Integration test for session flow in `code/experiment/tests/test_session_flow.py` (verify data capture completeness).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (can run locally or on Streamlit Cloud for pilot)

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

**Goal**: Execute reproducible statistical analysis on collected data to test the directional hypothesis.

**Independent Test**: A script can run against a synthetic dataset to verify planned contrasts, post-hoc tests, and Cohen's d calculations.

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement data cleaning pipeline in `code/analysis/data_cleaning.py` (handle missing values, flag attention check failures).
- [ ] T030 [US2] [FR-003] [SC-001] Implement One-Way ANOVA and **Planned Directional Contrasts** in `code/analysis/contrasts.py`. **Requirement**: Explicitly implement orthogonal contrast vectors with coefficients:) High vs. Low (coefficients: [-1, 1, 0]), 2) (High+Low) vs. Control (coefficients: [1, 1, -2]). **Library**: Use `pingouin.anova` or `statsmodels`. **Output**: Summary tables with t-statistics, p-values, degrees of freedom. **Dependency**: T029.
- [ ] T031 [US2] [FR-005] [SC-005] Implement Tukey HSD post-hoc tests in `code/analysis/pairwise.py` with family-wise error rate adjustment. **Requirement**: Explicitly state 'family-wise error rate adjustment' in output. **Dependency**: T030.
- [ ] T032 [US2] [FR-004] Implement Cohen's d effect size calculation in `code/analysis/effect_sizes.py` for all pairwise comparisons. **Requirement**: Explicitly compute for all pairwise comparisons. **Dependency**: T031.
- [ ] T033 [US2] Create synthetic data generator in `code/analysis/synthetic_data.py` for testing the pipeline without real data.
- [ ] T034 [US2] Integrate all analysis steps into a main runner script `code/analysis/run_analysis.py`.
- [ ] T035 [US2] Analyze manipulation check data from T026 and calculate achieved power. **Logic**: Calculate mean perceived agency score. **Test**: One-sample t-test against a predetermined threshold. **Power Check**: Read `target_n` from `research/power_calculation.json` (produced by T002). Compare `len(df)` against `target_n`. **Output**: Write `manipulation_check_status` ("valid"/"invalid"), `mean_score`, `achieved_power`, and `power_status` ("sufficient"/"insufficient") to `results/power_status.json`. **Constraint**: If `len(df) < target_n` OR manipulation check invalid, set `power_status`="insufficient" and write "Limitation: Insufficient Power" to the JSON. **DO NOT halt the pipeline** or report a null result here; simply flag the status for the report generator. **Dependency**: T026, T002.

### Tests for User Story 2

- [ ] T036 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_output.py`.
- [ ] T037 [P] [US2] Unit test for contrast calculation logic using synthetic data in `tests/unit/test_contrasts.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis can run on synthetic or real data)

---

## Phase 5: User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Generate reports including power analysis, multiple-comparison corrections, and sensitivity analysis.

**⚠️ CRITICAL**: Depends on Phase 4 (US2) completion. Tasks here require ANOVA and post-hoc results.
**Strict Sequence**: T042 -> T038 -> T038b -> T039 -> T040.
**Note**: T007g is a prerequisite for *running* T024 (Phase 3), and T042 (Protocol) is a prerequisite for *defining* T038 thresholds.

**Independent Test**: Review of generated report confirms power targets, error corrections, and threshold sweeps.

### Implementation for User Story 3

- [ ] T038 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`. **Requirement**: Sweep **participant exclusion thresholds** defined in `code/analysis/config.yaml` (key: `sensitivity_config`). **Logic**:
 1. Load `sensitivity_config` from `code/analysis/config.yaml`.
 2. Verify that the ranges defined in `config.yaml` match the pre-registered protocol in `docs/protocol.md` (generated by T042). If they do not match, raise an error.
 3. Iterate through the configured ranges for:
 - Attention check pass rate: **Start**: 0.80, **End**: 1.00, **Step**: 0.05.
 - Straight-lining detection thresholds: **Start**: 0.80, **End**: 1.00, **Step**: 0.05.
 - Adherence Rate cutoffs: **Start**: 0.50, **End**: 0.95, **Step**: 0.05.
 - Trust Score outlier detection: **Start**: 2.0, **End**: 3.5, **Step**: 0.5.
 4. **Output**: CSV table with columns `threshold_type`, `threshold_value`, `p_value_primary`, `effect_size_primary`. **Dependency**: Must run after Phase 4 (T030, T031) completes AND T042 (Protocol) is complete.
- [ ] T038b [US3] [FR-006] [SC-003] Implement sensitivity analysis reporting in `code/analysis/report.py`. **Requirement**: Generate a dedicated 'Sensitivity Analysis' section in the final report. **Logic**: Read the output CSV from T038 and summarize the stability of the primary findings (p-values and effect sizes) across the swept thresholds. **Output**: Append 'Sensitivity Analysis Summary' section to `docs/report.md`. **Dependency**: T038.
- [ ] T039 [US3] Implement final report generation in `code/analysis/report.py`. **Requirement**: Compile ANOVA, contrasts, post-hoc, effect sizes, pre-study power results from T002 (`research/power_calculation.json`), and sensitivity analysis. **Power Limitation Handling**: Read `results/power_status.json` (from T035). **If** `power_status` is "insufficient", **unconditionally** append a "Limitations" section to `docs/report.md` stating "Limitation: Insufficient Power" and detailing the achieved power vs target. **Data Merge**: Explicitly read `research/power_calculation.json` (T002) for pre-study parameters (`params.effect_size`, `params.alpha`, `params.power`) and `results/power_status.json` (T035) for achieved power (`achieved_power`, `power_status`), merging them into a single 'Power Analysis Summary' section in the report. **Output**: Markdown report at `docs/report.md`. **Dependency**: Must wait for T002 (Power Analysis), T034 (Analysis completion), T038 (Sensitivity analysis), T038b (Sensitivity Report), and T035 (Power Status).
- [ ] T040 [US3] Add null result handling logic in `code/analysis/report.py` (explicitly report null findings and observed effect sizes).

### Tests for User Story 3

- [ ] T041 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update documentation in `docs/protocol.md` with pre-registered analysis plan. **Requirement**: Explicitly reference FR-006, US-3, and the specific sensitivity sweep parameters defined in T038. **Dependency**: T002, T008.
- [ ] T043 [P] Create GitHub Actions workflow in `.github/workflows/experiment.yml` to run analysis on `data/processed/`.
- [ ] T044 [P] Code cleanup and refactoring for type hints and docstrings. **Scope**: All `.py` files. **Style**: Google style guide. **Verification**: Run `pyright` and ensure 0 errors.
- [ ] T045 [P] Add validation scripts to verify `participant.schema.yaml` compliance against `data/raw/` exports.
- [ ] T046 [P] Run quickstart.md validation and update instructions if needed. **Validation**: Execute `./quickstart.sh` (or equivalent) and verify exit code 0. **Update**: Modify instructions if steps fail.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0 (Gates)**: T000 -> T000b. **CRITICAL**: If these fail, project halts.
- **Phase 0 (Research)**: T000b -> T001a-1 -> T001a-2 -> T001b-1 -> T001b-2 -> T002 -> T003-1 -> T008 -> T010b -> T011 -> T007g. **Note**: T010b, T011, and T007g are **REQUIRED** for the transition to Phase 1 and Phase 2.
- **Phase 1 (Setup)**: Depends on Phase 0 completion. Tasks T004, T005, T006, T010, T009, T012, T017i, T017h, T015, T016 can run in parallel as they depend only on T004 and T000/T010b where applicable. **Order within Phase 1**: T004 -> T010 -> T009 -> T012 -> T017i -> T017h.
- **Phase 2 (Foundational)**: Depends on Phase 0 (including T010b/T011/T007g) and Phase 1 completion. **BLOCKS all user stories**.
- **Phase 3 (US1)**: Depends on Phase 2 completion. T024b execution is additionally blocked by T007g completion.
- **Phase 4 (US2)**: Depends on Phase 2 completion.
- **Phase 5 (US3)**: Depends on Phase 4 completion AND T042 (Protocol) completion.
- **Phase 6 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must be completed before data collection begins. **Execution Note**: T024b runtime requires T007g.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run on synthetic data independently of US1 completion, but requires US1 data schema.
- **User Story 3 (P3)**: Can start ONLY AFTER Phase 4 (US2) completion AND T042 (Protocol) completion. Relies on US2 outputs (ANOVA, post-hoc) for sensitivity sweeps and post-hoc power.

### Within Each User Story

- Implementation MUST be written before tests (unless TDD explicitly requested).
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch interface implementations for User Story 1 together:
Task: "Implement High Agency condition interface in code/experiment/app.py"
Task: "Implement Low Agency condition interface in code/experiment/app.py"
Task: "Implement Control condition interface in code/experiment/app.py"

# Launch tests for User Story 1 together (after implementation):
Task: "Unit test for randomization logic in code/experiment/tests/test_randomization.py"
Task: "Integration test for session flow in code/experiment/tests/test_session_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Pre-Phase 0: Gates (T000, T000b).
2. Complete Phase 0: Research & Validation (Includes T0.80 Power Analysis AND T007g).
3. Complete Phase 1: Setup.
4. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
5. Complete Phase 3: User Story 1.
6. **STOP and VALIDATE**: Test User Story 1 independently (run pilot with synthetic or real participants).
7. Deploy experiment interface for recruitment.

### Incremental Delivery

1. Complete Pre-Phase 0 + Phase 0 + Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy experiment interface (MVP!).
3. Add User Story 2 → Test on synthetic data → Ready for real data analysis.
4. Add User Story 3 → Test robustness → Generate final report.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Pre-Phase 0 + Phase 0 + Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Experiment Interface).
 - Developer B: User Story 2 (Analysis Core).
 - Developer C: User Story 3 (Robustness & Reporting).
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- **Data Integrity**: Ensure `data/raw/` is never modified in-place. All cleaning must write to `data/processed/`.
- **Compute Feasibility**: All statistical tasks (ANOVA, contrasts, sensitivity) are CPU-tractable and fit within GitHub Actions free-tier limits.
- **Fabrication Guard**: Do NOT use `random.*` to generate input data for the analysis pipeline unless explicitly testing with synthetic data generators. Real analysis must use real CSV exports from `data/raw/`.
- **Gate Tasks**: T000 (Reference Validation) is a mandatory gate. T034 is now a reporting step, not a gate.
- **Critical Dependencies**: T002 must complete after T001a-2 and T001b-2. T008 depends on T002. T024 depends on T010b, T011, T000b, and T007g artifacts. T035 depends on T026 and T002. T038 depends on Phase 4 and T042. T039 depends on T002, Phase 4, T038, and T038b.
- **Execution Flow**: T010b/T011/T007g are prerequisites for Phase 2. T007g is a prerequisite for T024b execution. T042 is a prerequisite for T038 execution.