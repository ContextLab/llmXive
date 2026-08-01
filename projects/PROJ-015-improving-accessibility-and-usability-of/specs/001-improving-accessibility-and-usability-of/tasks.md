# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US3)
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-015-improving-accessibility-and-usability-of/`)
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt`. **Deliverable**: `requirements.txt` containing pinned versions of `scipy`, `matplotlib`, `pandas`, `jupyter`, `streamlit`, `statsmodels`, `pyyaml`, `numpy`. **Verification**: File exists and contains version pins (e.g., `scipy==1.11.0`, `statsmodels==0.14.0`).
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Active Tasks (Foundational)
- [X] T012a [P] Create `CONTRIBUTING.md` with the mandatory "no synthetic data" clause and schema compliance guidelines. **Deliverable**: `CONTRIBUTING.md`. **Content**:
 ```markdown
 # Contributing Guidelines

 ## Data Integrity Policy
 **CRITICAL**: Do not use synthetic data for final research claims.
 - Use `--simulate` flag ONLY for local pipeline verification and CI testing (dev mode).
 - The production pipeline MUST fail loudly (exit with a non-zero error code) if `data/raw/` is empty or contains no real session files.
 - Synthetic data is strictly forbidden for generating final statistical results or publication figures.
 - All final claims must be derived from data collected via the web-based simulator (FR-007) or verified real-world sources.
 - This policy is the basis for the technical enforcement implemented in T097 and T019c.

 ## Schema Compliance
 - All session data MUST conform to `contracts/session.schema.yaml`.
 - Any deviation from the schema will cause the data loader to reject the file.
 ```
 **Dependencies**: None.

- [X] T015 [Foundational] Implement Latin Square counterbalancing in `code/simulator/counterbalance.py` to assign the order of interface presentation (Traditional->Explainable or Explainable->Traditional) to mitigate order effects. **Deliverable**: `code/simulator/counterbalance.py` with a function `assign_sequence(participant_id) -> str`. **Dependencies**: None. **Note**: **BLOCKING PREREQUISITE**: This task must be completed before any Phase 3 tasks (like T012d4-swtch) can execute. The [P] tag has been removed to emphasize this hard execution dependency.

- [X] T035a-apply [Foundational] **SPEC AMENDMENT (Apply)**: Verify `spec.md` FR-002 contains the ratified amendment text for Repeated Measures ANOVA. **Deliverable**: Verified `spec.md`. **Dependencies**: None.

- [X] T019b [P] Create `contracts/session.schema.yaml`. **Deliverable**: `contracts/session.schema.yaml` defining the JSON schema for session data (participant_id, interface_type, metrics, status, etc.). **Dependencies**: None.

- [X] T019c [US1] Implement runtime schema validation logic in `code/simulator/validator.py`. **Deliverable**: `code/simulator/validator.py` with a function `validate_session(data: dict) -> bool`. **Dependencies**: T019b.

- [X] T031-gen [P] Implement `generate_sessions(n, seed)` function in `code/simulator/simulator.py`.
 - **Logic**: Generate synthetic sessions based on `N` participants. The "Explainable" condition has `completion_time` = `baseline_time` - 5.0 seconds; the "Traditional" condition has `completion_time` = `baseline_time`. `baseline_time` is drawn from a normal distribution (mean=60, std=10). Random noise is added (Gaussian, mean=0, std=2). Seeds are pinned.
 - **CRITICAL CONSTRAINT**: This synthetic data is FORBIDDEN for final research claims. It is ONLY for CI validation and local debugging. **Every generated file MUST include a metadata header: `metadata: { source: "simulated" }`.** The analysis pipeline MUST explicitly reject this data for final claims unless a `--simulate` flag is set.
 - **Deliverable**: `code/simulator/simulator.py` with `generate_sessions` function. **Verification**: Unit test `tests/unit/test_simulator.py::test_mean_diff_5s` asserts a measurable mean difference consistent with the defined temporal threshold. **Dependencies**: T019b.

- [X] T031-cli [P] Implement CLI wrapper for `DeterministicDataSimulator` in `code/simulator/simulator.py`.
 - **Deliverable**: A CLI tool `python -m code.simulator.simulator --n <N> --seed 42 --output data/raw/simulated_sessions.json`, where `<N>` represents a configurable sample size for the simulation.
 - **Constraint**: The `--simulate` flag is ONLY for dev mode. The pipeline must reject this data for analysis unless explicitly in dev mode.
 - **Verification**: Run `python -m code.simulator.simulator --n 5 --seed 42 --output data/raw/simulated_sessions.json` and verify `data/raw/simulated_sessions.json` exists and contains valid JSON with the expected schema and `metadata: { source: "simulated" }`.
 - **Dependencies**: T031-gen.

- [X] T031b [P] Implement schema validation in `code/simulator/simulator.py` to ensure the output of `DeterministicDataSimulator` (T031-gen) strictly matches the schema defined in `contracts/session.schema.yaml`.
 - **Logic**: The simulator must abort if the schema file (`contracts/session.schema.yaml`) is absent or data fails validation using `jsonschema` library. **T019b must be complete before T031b.**
 - **Deliverable**: Updated `code/simulator/simulator.py` with `jsonschema` validation logic. **Verification**: Unit test `tests/unit/test_simulator.py::test_schema_rejection` asserts simulator raises error on invalid JSON. **Dependencies**: T031-cli, T019b.

- [X] T031c [P] Extend `DeterministicDataSimulator` to generate a subset of "dropout" sessions. **Logic**: For a configured percentage, set `status='incomplete'` and populate `dropout_reason` with a random reason from a predefined list. **CRITICAL**: All generated files MUST include `metadata: { source: "simulated" }`. **Deliverable**: Updated `code/simulator/simulator.py` with `--dropout-rate` flag. **Dependencies**: T031-cli.

- [X] T032 [P] Create `tests/unit/test_simulator.py` to verify that:
 - The simulator produces the expected fixed difference in completion time.
 - `explanation_engagement_time` is strictly positive for Explainable and zero for Traditional.
 - The output JSON schema matches `contracts/session.schema.yaml`.

- [X] T033 [P] **DEV MODE ONLY**: Update `code/analysis/run_analysis.py` to accept a `--simulate` flag that triggers `DeterministicDataSimulator` if no raw data is found, **BUT** only for local CI validation.
 - **Critical Rule**: This flag MUST be explicitly disabled in production runs. The production pipeline must **fail loudly** (exit with a non-zero error code) if `data/raw/` is empty and the `--simulate` flag is not set. Synthetic data must never be processed by the analysis pipeline for final claims.
 - **Note**: This task handles the *dev mode* path. The *production mode* enforcement is handled by T097, which supersedes this logic for real runs.

- [X] T048 [US0] **Critical Dependency Fix**: Refactor `code/simulator/state.py` to ensure `manage_state()` is fully functional and exposes the `current_sequence` and `interface_variant` to the main app loop *before* T012e (Integration) executes.
 - **Logic**: Verify that `st.session_state` is initialized correctly on the first run and that the sequence logic correctly toggles between Traditional and Explainable interfaces based on the `current_phase`.
 - **Deliverable**: `code/simulator/state.py` with function `manage_state() -> dict` returning `{'current_sequence': str, 'current_phase': int, 'interface_variant': str}`.
 - **Dependencies**: T015, T012d3.

- [X] T095-plan [US2] **Participant Recruitment Protocol**: Create `code/analysis/recruitment_protocol.py` and `docs/recruitment_plan.md`. The plan must explicitly define outreach to disability advocacy organizations (e.g., specific org names, contact methods) and a verification step to log participant diversity across disability types.
 - **Deliverable**: `docs/recruitment_plan.md` and `code/analysis/recruitment_protocol.py` with a function `verify_diversity(logs) -> bool`.
 - **Dependencies**: None. **Note**: Moved to Phase 1 to ensure protocol exists before data collection.

### Active Tasks (Data & Logging)
- [X] T019 [US1] Implement raw data logging to `data/raw/session_{session_id}.json`. **Logic**: Implement function `log_session(data: dict, session_id: str)` in `code/simulator/session_logger.py`. The JSON **must** contain the fields defined in `contracts/session.schema.yaml`. The task **must abort** if the schema file is absent (enforced by the completion of T019b) OR if the data fails validation (enforced by T019c). **Deliverable**: One JSON file per completed (or incomplete) session stored under `data/raw/`. **Verification**: Schema validation pass on the generated JSON. **Dependencies**: T019b, T019c.

**Checkpoint**: Foundation complete - T019b, T019c, T035a-apply, T031-series, T048, T095-plan are done. User story implementation can now begin.

---

## Phase 3: User Story 0 - XAI Interface Configuration (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to evaluate the usability of computer systems for people with disabilities, specifically focusing on gene regulation interfaces.

**Independent Test**: The research pipeline can be fully tested by running the data collection script on a simulated dataset or a small pilot group (n=5) to verify that completion times, error counts, explanation engagement times, and SUS scores are correctly logged and formatted for downstream statistical analysis.

### Implementation for User Story 0

- [X] T010 [P] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py`
- [X] T011 [P] Implement `ExplainableInterface` renderer in `code/simulator/interfaces/explainable.py`
- [X] T012c Create the skeleton Streamlit app entry point `code/simulator/app.py`. **Deliverable**: `code/simulator/app.py`. **Verification**: File exists and runs `streamlit run` without import errors. **Dependencies**: None.
- [X] T013a Define the overlay data schema in `code/simulator/schemas/overlay_schema.yaml`. **Deliverable**: Schema defining the structure of XAI overlay data (e.g., feature IDs, intensity values).
- [X] T013b Implement `RuleBasedXAIOverlayGenerator` in `code/simulator/xai_overlay.py`. **Logic**: Generate deterministic, rule-based XAI overlays (e.g., heatmaps) based on task difficulty parameters (no external models or datasets). The generator must produce feature-level overlay data that can be visualized as heatmaps over UI elements. **Deliverable**: A function `generate_overlay(task_input) -> dict` returning overlay data based on task difficulty. **Dependencies**: T013a.

- [X] T012d1 [US0] Implement UI renderer integration in `code/simulator/app.py`. **Scope**: Implement function `render_interface(interface_type: str, task_input: dict) -> dict`. **Deliverable**: `code/simulator/app.py` with `render_interface` function. **Dependencies**: T010, T011, T012c.
- [X] T012d2 [US0] Implement input capture module in `code/simulator/input.py`. **Scope**: Implement function `capture_input() -> dict` returning `consent_status`, `participant_id`, and `input_events`. **Deliverable**: `code/simulator/input.py` with `capture_input` function. **Dependencies**: T012c.
- [X] T012d3 [US0] Implement SUS form logic in `code/simulator/input.py`. **Scope**: Implement function `calculate_sus_score(responses: list) -> dict`. **Deliverable**: `code/simulator/input.py` with `calculate_sus_score` function. **Dependencies**: T012d2.
- [X] T012d4-init [US0] Initialize state management keys in `code/simulator/state.py`. **Scope**: Implement function `init_state()` to initialize `st.session_state` keys `current_sequence`, `current_phase`, and `interface_variant`. **Deliverable**: `code/simulator/state.py` with `init_state` function. **Dependencies**: T012d2.
- [X] T012d4-inc [US0] Implement phase increment logic in `code/simulator/state.py`. **Scope**: Implement function `increment_phase()` to increment `current_phase` on 'Next' click. **Deliverable**: `code/simulator/state.py` with `increment_phase` function. **Dependencies**: T012d4-init.
- [X] T012d4-swtch [US0] Implement sequence switching logic in `code/simulator/state.py`. **Scope**: Implement function `switch_sequence()` to toggle `interface_variant` based on `current_sequence` and `current_phase`. **Deliverable**: `code/simulator/state.py` with `switch_sequence` function. **Dependencies**: T012d4-inc, T015.
- [X] T012e [US0] Integrate XAI Overlay and Counterbalancing into the Streamlit flow. **Logic**: Ensure `RuleBasedXAIOverlayGenerator` (T013b) is called when rendering the `ExplainableInterface` and that the `LatinSquareCounterbalancer` (T015) dictates the sequence. **Deliverable**: `code/simulator/app.py` with verified integration of counterbalancing and XAI logic. **Verification**: Verify that for participant_id=1, the app renders Traditional first, then Explainable, and logs sequence_order=[1,2] in the session JSON. **Dependencies**: T013b, T015, T012d1, T012d2, T012d3, T012d4-init, T012d4-inc, T012d4-swtch.
- [X] T012g [US0] Implement Accessibility Accommodations in `code/simulator/accessibility.py`. **Scope**: Implement function `render_accessibility_settings() -> dict` to provide UI components for accessibility settings (e.g., font size, contrast, keyboard navigation). **Deliverable**: `code/simulator/accessibility.py` with `render_accessibility_settings` function. **Dependencies**: T012d4-swtch. **Note**: Supports T095 (Recruitment) by collecting disability type data.
- [X] T012h [US0] Implement Disability Type Selection in `code/simulator/accessibility.py`. **Scope**: Implement function `render_disability_selector() -> str` to allow participants to select their disability type. **Deliverable**: `code/simulator/accessibility.py` with `render_disability_selector` function. **Dependencies**: T012g.

- [X] T012f-main [US0] Implement Human Interaction Loop Orchestration in `code/simulator/orchestrator.py`. **Scope**: Implement function `run_human_loop() -> dict` within `code/simulator/orchestrator.py`. This function orchestrates the flow by calling `render_accessibility_settings()`, `capture_input()`, `calculate_sus_score()`, and `manage_state()` in sequence. **Deliverable**: `code/simulator/orchestrator.py` with `run_human_loop` function. **Dependencies**: T012d2, T012d3, T012d4-init, T012d4-inc, T012d4-swtch, T012g, T012h.
- [X] T012f-int [US0] Integrate Human Loop into Main App. **Scope**: Wire `run_human_loop()` (T012f-main) into the main Streamlit `st.main()` flow in `code/simulator/app.py`. **Deliverable**: `code/simulator/app.py` with full human flow execution. **Dependencies**: T012f-main.
- [X] T012i [US0] Implement **Gene Regulation Task Logic** in `code/simulator/tasks/gene_task.py`. **Scope**: Implement the specific interactive task (e.g., drag-and-drop gene editing, sequence assembly) that participants must perform. **Deliverable**: `code/simulator/tasks/gene_task.py` with functions `render_task()`, `validate_task_completion()`, and `calculate_task_metrics()`. **Dependencies**: T012d1.
- [X] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`

**Checkpoint**: XAI overlay schema and generator tasks are defined and implemented.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Execute the standardized usability test protocol, collecting metrics (time, errors, SUS, engagement) for both interfaces with Latin Square counterbalancing.

**Independent Test**: The research pipeline can be fully tested by running the data collection script on a simulated dataset or a small pilot group (n=5) to verify that completion times, error counts, explanation engagement times, and SUS scores are correctly logged and formatted for downstream statistical analysis.

### Implementation for User Story 1

- [X] T016 [P] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [X] T016b [P] Ensure `explanation_engagement_time_seconds` is logged to **raw** session files under `data/raw/` as part of the session JSON (aligned with FR‑001). **Deliverable**: Raw JSON includes `explanation_engagement_time_seconds`. **Dependencies**: T019, T019c.
- [X] T049 [US1] **Critical Data Flow Fix**: Ensure `metrics_collector.py` (T016) is explicitly called within the `run_human_loop()` (T012f-main) flow *after* the task is completed but *before* the session is logged.
 - **Logic**: Add explicit calls to `metrics_collector.calculate_task_metrics()` within `code/simulator/orchestrator.py` and verify the returned metrics are passed to `session_logger.log_session()`.
 - **Specific Requirement**: Explicitly capture `explanation_engagement_time` for the 'Explainable' interface and validate it against the schema before logging.
 - **Deliverable**: Updated `code/simulator/orchestrator.py` and `code/simulator/session_logger.py` ensuring `completion_time`, `error_count`, and `explanation_engagement_time` are present in every raw JSON file. **Dependencies**: T012f-main, T016.
- [X] T017 [P] Integrate all collectors (T016, T016b, T015) and SUS questionnaire into the Streamlit app flow in `code/simulator/app.py` ensuring sequence order is respected. Implement SUS validation: reject if >1 item missing; if ≤1 missing, impute with participant mean and log imputation. **Dependencies**: T012f-int, T012g, T012h, T049.
- [X] T020 [P] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` for partial sessions in `code/simulator/session_logger.py`.

**Checkpoint**: The system can collect real‑time interaction data, handle dropouts, and store immutable raw logs with schema validation.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

**Goal**: Perform statistical analysis (Repeated Measures ANOVA, Holm‑Bonferroni) on collected metrics to determine significance.

**Independent Test**: The analysis module can be tested by feeding it a pre-generated CSV file with known distributions and verifying that ANOVA F-statistics, adjusted p-values, and effect sizes are calculated correctly.

### Implementation for User Story 2

- [X] T025a [P] Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`) and basic orchestration calls. **Deliverable**: `code/analysis/run_analysis.py`. **Verification**: File exists and can be called without errors. **Dependencies**: T035a-apply.
- [X] T021a [P] Implement data cleaning in `code/analysis/data_cleaner.py`. **Logic**: 1. Filter out sessions with `status='incomplete'`. 2. If ≤1 SUS item missing, impute with participant mean; if >1, reject session. **Output**: `data/processed/cleaned_sessions.csv`. **Dependencies**: T019b. **Verification**: Unit test `tests/unit/test_data_cleaner.py::test_filter_incomplete` passes; verify `data/processed/cleaned_sessions.csv` exists and contains no rows with `status='incomplete'`.
- [X] T021b [P] Implement SUS imputation logic in `code/analysis/data_cleaner.py`. **Logic**: If ≤1 item missing, impute with participant mean; if >1, mark as incomplete. **Dependencies**: T021a.
- [X] T021c-cli [P] Implement CLI wrapper for data cleaning in `code/analysis/clean_data.py`. **Scope**: Implement CLI `--input` (path to raw data), `--output` (path to cleaned CSV), and `--state-file` (path to `state/projects/PROJ-015-improving-accessibility-and-usability-of.yaml`). **Dependencies**: T019b.
- [X] T021c-pre [P] **DEPRECATED**: Superseded by T097. **Logic**: If `--input` directory is empty and `--simulate` flag is NOT set, raise `FileNotFoundError`. **Dependencies**: T021c-cli.
- [X] T021c-pipe [P] Implement pipeline orchestration function in `code/analysis/clean_data.py`. **Logic**: Call `filter_incomplete()` (T021a) and `impute_sus()` (T021b). **Dependencies**: T021c-pre.
- [X] T021c-hash [P] Implement checksum and state update logic in `code/analysis/clean_data.py`. **Logic**: Compute SHA-256 checksum of `cleaned_sessions.csv` and record it in `state-file` under `artifact_hashes['cleaned_sessions']`. **Output**: `data/processed/cleaned_sessions.csv`. **Dependencies**: T021c-pipe. **Verification**: Verify `state/projects/...yaml` contains `artifact_hashes['cleaned_sessions']` matching the SHA-256 of `data/processed/cleaned_sessions.csv`.
- [X] T021c-log [P] Implement logging for data cleaning process in `code/analysis/clean_data.py`. **Scope**: Log all cleaning actions, imputations, and rejections to `data/processed/cleaning_log.txt`. **Dependencies**: T021c-pipe.
- [X] T021d [P] Verify SUS imputation logic. **Logic**: Write a test script that generates a session with one missing SUS item, runs the cleaner, and asserts the imputed value matches the participant mean. **Deliverable**: `tests/unit/test_imputation.py`. **Dependencies**: T021b.
- [X] T021e [P] Implement dropout verification logic. **Logic**: Write a script or test that asserts `dropout_reason` is populated for every session where `status='incomplete'` in the raw data. **Deliverable**: `tests/unit/test_dropout_verification.py` or logic in `clean_data.py`. **Dependencies**: T021a.
- [X] T050 [US2] **Critical Input Validation**: Update `code/analysis/data_cleaner.py` to explicitly handle the case where `explanation_engagement_time` is missing or zero for Traditional interfaces (as expected) but non-zero for Explainable interfaces.
 - **Logic**: Add a validation step `validate_xai_engagement()` in the cleaning pipeline to flag sessions where `interface_type='Explainable'` and `explanation_engagement_time` is missing or zero, logging a warning but not failing the session unless other critical fields are missing.
 - **Deliverable**: Updated `code/analysis/data_cleaner.py` with specific validation logic for XAI engagement metrics. **Dependencies**: T021a, T016b.
- [X] T022 [P] Implement Shapiro‑Wilk normality test on difference scores in `code/analysis/stat_utils.py` and log results to `data/processed/normality_log.txt` (audit only). **Deliverable**: `data/processed/normality_log.txt` containing a CSV/JSON with `metric`, `shapiro_statistic`, `p_value`. **Dependencies**: T035a-apply.
- [X] T023a [US2] Implement **Repeated Measures ANOVA** for Completion Time, Error Count, and SUS in `code/analysis/stat_utils.py`.
 - **Constraint**: Use `statsmodels.stats.anova.AnovaRM` for Repeated Measures ANOVA. Do NOT use `scipy.stats.f_oneway` (One-Way ANOVA) as it is invalid for within-subjects design.
 - **Input Data**: Reshape to 'long format' (columns: `participant_id`, `interface_type`, `metric_value`).
 - **Deliverable**: `data/processed/metrics_summary.csv` with columns `metric_name, interface_type, F_statistic, p_value, adjusted_p_value, effect_size`. **Dependencies**: T035a-apply.
- [X] T023b [P] Compute descriptive statistics (mean, std) for `explanation_engagement_time` and output to `data/processed/descriptive_stats_explanation_engagement.csv`. **Logic**: Ensure these stats are included in the final `report_summary.txt`. **Deliverable**: `data/processed/descriptive_stats_explanation_engagement.csv` and updated `report_summary.txt`. **Dependencies**: T023a.
- [X] T024 [P] Implement Holm‑Bonferroni correction for the multiple ANOVA comparisons in `code/analysis/stat_utils.py`. **Dependencies**: T035a-apply.
- [X] T024a [P] Verify primary ANOVA p‑value < 0.05 before applying Holm-Bonferroni; write verification result to `data/processed/primary_test_verification.txt`.
- [X] T025c-orch [P] Implement statistical engine orchestration in `code/analysis/run_analysis.py`. **Logic**: Import and call `shapiro_wilk()`, `anova_rm()`, `holm_bonferroni()`, and `descriptive_stats()` in sequence. **Deliverable**: `code/analysis/run_analysis.py` with the orchestration logic. **Dependencies**: T022, T023a, T024, T023b.
- [X] T025c-log [P] Implement statistical engine error logging in `code/analysis/run_analysis.py`. **Scope**: Implement error handling logic within `execute_pipeline()` to log any import errors or execution failures to `data/processed/error_log.txt`. **Dependencies**: T025c-orch.
- [X] T025d [P] Implement report writer in `code/analysis/run_analysis.py`. **Scope**: Implement function `write_report()` within `run_analysis.py`. **Logic**: Write `metrics_summary.csv`, `report_summary.txt`. Verify that the CSV contains the required columns before exiting. **Documentation**: Include a comment block citing "Constitution Principle VII" and "Spec FR-002 (Amended by T035a)" as the basis for using ANOVA. **Deliverable**: `code/analysis/run_analysis.py` with report generation logic. **Dependencies**: T025c-log.
- [X] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py`:
 - Compute statistical power given N, effect size (eta‑squared), and α = 0.05 using `statsmodels.stats.power.FTestAnovaPower`.
 - **Logic**: Calculate required N based on observed effect size. If observed N < required N, flag as 'UNDERPOWERED'. Do NOT use hardcoded N=30 threshold.
 - **Deliverable**: `data/processed/power_flags.json` with schema `{ "subgroup": "<str>", "N": <int>, "power": <float>, "required_N": <int>, "flag": "<UNDERPOWERED|OK>" }`.
 - **Dependencies**: T023a.
- [X] T036b [P] Generate Power Analysis Report. **Logic**: Implement logic to integrate `power_flags.json` (T036) into the final `report_summary.txt` or generate a dedicated `data/processed/power_report.md`. **Constraint**: If any subgroup is 'UNDERPOWERED', the pipeline must exit with a non-zero code and log a warning. **Deliverable**: `data/processed/power_report.md`. **Dependencies**: T025d. **Verification**: Verify file exists and contains 'UNDERPOWERED' flag if N < required_N.

**Checkpoint**: The pipeline now cleans raw data, runs ANOVA with proper corrections, produces descriptive stats, and outputs power‑analysis flags.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

**Goal**: Generate publication‑quality visualizations and a single executable Jupyter notebook documenting the pipeline.

**Independent Test**: Run the notebook on a small sample dataset; verify that all figures are created, have correct axis labels, and that the notebook completes without errors.

### Implementation for User Story 3

- [X] T027a [P] Implement visualization function for Completion Time in `code/analysis/visualizer.py`. **Logic**: Box plot with Confidence intervals will be used to represent uncertainty in estimated effects. (e.g., [DOI/arXiv/author-year]). **Function**: `plot_completion_time(data: pd.DataFrame) -> Figure`. **Output**: `figures/completion_time.png`. **Dependencies**: T023a.
- [X] T027b [P] Implement visualization function for Error Count in `code/analysis/visualizer.py`. **Logic**: Box plot with 95 % CI error bars. **Function**: `plot_error_count(data: pd.DataFrame) -> Figure`. **Output**: `figures/error_count.png`. **Dependencies**: T023a.
- [X] T027c [P] Implement visualization function for SUS in `code/analysis/visualizer.py`. **Logic**: Box plot with 95 % CI error bars. **Function**: `plot_sus_score(data: pd.DataFrame) -> Figure`. **Output**: `figures/sus_score.png`. **Dependencies**: T023a.
- [X] T027d [P] Verify all visualization files exist and are non-empty. **Deliverable**: `tests/unit/test_visualizations.py`. **Dependencies**: T027a, T027b, T027c.
- [X] T028-skel [P] Create notebook skeleton with markdown explanations in `code/analysis/analysis.ipynb`. **Deliverable**: `code/analysis/analysis.ipynb` with markdown cells. **Dependencies**: None.
- [X] T028-load [P] Implement data loading/cleaning cells in `code/analysis/analysis.ipynb`. **Deliverable**: `code/analysis/analysis.ipynb` with data loading cells. **Dependencies**: T028-skel, T021c-cli.
- [X] T028-stat [P] Implement statistical analysis cells in `code/analysis/analysis.ipynb`. **Deliverable**: `code/analysis/analysis.ipynb` with ANOVA cells. **Dependencies**: T028-load, T023a.
- [X] T028-viz [P] Implement visualization cells in `code/analysis/analysis.ipynb`. **Deliverable**: `code/analysis/analysis.ipynb` with plot cells. **Dependencies**: T028-stat, T027a, T027b, T027c.
- [X] T028-power [P] Implement power analysis cells in `code/analysis/analysis.ipynb`. **Deliverable**: `code/analysis/analysis.ipynb` with power cells. **Dependencies**: T028-viz, T036.
- [X] T028-doc [P] Finalize notebook with documentation and artifact saving in `code/analysis/analysis.ipynb`. **Deliverable**: `code/analysis/analysis.ipynb` with final documentation. **Dependencies**: T028-power.
- [X] T030 Ensure the notebook is fully deterministic. **Logic**: Pin random seeds, use exact file paths, and verify that re‑running produces identical checksums for generated figures. **Deliverable**: `code/analysis.ipynb` with pinned seeds and checksum verification logic. **Dependencies**: T028-doc.
- [X] T029b Create a unified `Makefile` or `run_pipeline.sh` script in the repository root. **Status**: Active - Implementation Required. **Scope**: Implement a script that chains T031-cli (simulation), T021c (cleaning), T025c-log (analysis), and T028-doc (notebook execution) into a single command. **Deliverable**: `Makefile` with targets `simulate`, `clean`, `analyze`, `report`, and `all`. **Dependencies**: T028-doc, T021c-hash.

**Checkpoint**: The pipeline now generates visualizations and a reproducible notebook.

---

## Phase 7: Spec-Plan Alignment Verification (Priority: P0)

**Goal**: Verify that the implementation strictly follows the Plan's scientific rigor and that the Spec amendment (T035a-apply) has been successfully applied and documented.

**Independent Test**: Run the analysis pipeline on a small sample dataset; verify that ANOVA is used, Levene's test is not invoked, and all steps are clearly documented.

### Implementation for Phase 7

- [X] T035 [US2] Update `code/analysis/stat_utils.py` to explicitly document the ratified Spec amendment.
- [X] T035c [US2] Update `code/analysis/run_analysis.py` to write a `methodology_notes.txt` file in `data/processed/` that lists the statistical tests used and cites the amended Spec section (FR-002).
- [X] T035d [US2] Implement explicit removal of Levene's test logic in `code/analysis/stat_utils.py`.

---

## Phase 8: Accessibility Compliance & Human Participant Validation (Priority: P1) 🎯 Critical

**Goal**: Ensure the web-based simulator (FR-007) meets WCAG 2.1 AA standards for people with disabilities and validate the end-to-end human participant flow with real accessibility accommodations.

### Implementation for Phase 8

- [X] T037 Implement automated accessibility audit script in `tests/contract/test_accessibility_audit.py`.
 - **Tool**: Use `axe-core`.
 - **Output**: `tests/contract/accessibility_report.json`.
 - **Dependencies**: T012f-int.
- [X] T038 Refine accessibility accommodations in `code/simulator/accessibility.py` based on audit results (T037).
- [X] T039 Create a manual "Human Participant Flow" verification script in `tests/manual/test_human_flow.py`.
- [X] T040 Add a pre-commit check to enforce accessibility testing.
- [X] T041 Add accessibility metrics to the final report.
- [X] T095-exec [US2] **Recruitment Execution**: Execute the recruitment plan defined in T095-plan.
 - **Logic**: Log outreach attempts to disability advocacy organizations and verify participant diversity logs. **Enforce N=30 threshold**: Halt the pipeline if the verified participant count < 30 before analysis proceeds. **CRITICAL GATE**: If N < 30, raise `RuntimeError` and exit.
 - **Deliverable**: `docs/recruitment_execution_log.md` with verified participant diversity.
 - **Dependencies**: T095-plan, T012g, T012h.

---

## Phase 9: Final Integration & Execution Readiness (Priority: P0)

**Goal**: Ensure all components are integrated, the full pipeline runs end-to-end, and the project is ready for the execution gate.

### Implementation for Phase 9

- [X] T047 Generate a final `PROJECT_STATUS.md` document.

---

## Phase 10: Reproducibility CI Gate (Priority: P0)

**Goal**: Ensure the pipeline is strictly ready for execution with real data, enforcing the "Fail Loudly" rule and verifying the dependency chain for the analysis phase.

### Implementation for Phase 10

- [X] T096 [P] Create `.github/workflows/reproducibility_check.yml`. **Logic**: Define a GitHub Actions workflow that runs `make all` on a fresh runner, verifies all artifacts exist, and checks checksums against `state/projects/...yaml`. **Deliverable**: `.github/workflows/reproducibility_check.yml`. **Dependencies**: T029b.

---

## Phase 11: Data Integrity & Execution Readiness (Priority: P0) 🎯 Critical

**Goal**: Resolve remaining data integrity concerns, ensure strict "fail loudly" behavior for missing real data, and finalize the execution pipeline for the analysis gate.

### Implementation for Phase 11

- [X] T097 [P] **Production Gate Enforcement**: Implement the definitive "Fail Loudly" check in `code/analysis/clean_data.py` that supersedes T033 and T021c-pre for production runs.
 - **Logic**: Before any data processing, check the `data/raw/` directory.
  1. If the directory is empty: Raise `RuntimeError` with message "CRITICAL: Production mode detected. No real participant data found in `data/raw/`. The pipeline cannot proceed. Please run the simulator with real participants or explicitly set the `--simulate` flag for dev mode only." and exit with code `sys.exit(1)`.
  2. If files exist: Iterate through JSON files. **Check for simulated files**: If ALL files in `data/raw/` match the pattern `*_simulated.json` OR contain `metadata: { source: "simulated" }`, raise `RuntimeError` with message "CRITICAL: No real data found. All files in `data/raw/` are simulated. The pipeline cannot proceed in production mode." and exit with code `sys.exit(1)`.
  3. If at least one file is NOT simulated: Proceed with cleaning.
 - **Constraint**: This check MUST occur BEFORE any data processing or cleaning logic. It is a hard gate. **This task supersedes the logic in T033 and T021c-pre for production contexts.** T033 remains for dev mode, but T097 is the authoritative check for production.
 - **Deliverable**: Updated `code/analysis/clean_data.py` with the pre-flight check and error handling. **Dependencies**: T019b, T025a.
 - **Verification**: Unit test `tests/unit/test_data_integrity.py::test_fail_loudly_no_data` asserts the `RuntimeError` is raised when `data/raw/` is empty. Unit test `tests/unit/test_data_integrity.py::test_fail_loudly_simulated_only` asserts the `RuntimeError` is raised when only simulated files are present.

- [X] T098 [P] **Execution Readiness Check**: Implement a comprehensive `verify_execution_readiness()` function in `code/analysis/run_analysis.py`.
 - **Logic**: This function must verify:
  1. All required input files exist (`contracts/session.schema.yaml`, `requirements.txt`).
  2. The `data/raw/` directory is not empty (or `--simulate` is set).
  3. The `code/simulator/` module is importable and functional.
  4. The `code/analysis/` module is importable and functional.
  5. The `Makefile` or `run_pipeline.sh` exists and is executable.
  6. All required dependencies are installed (check `pip list` or `requirements.txt` versions).
 - **Deliverable**: `code/analysis/run_analysis.py` with `verify_execution_readiness()` function returning a boolean and a list of errors if False. **Dependencies**: T097, T029b.
 - **Verification**: Unit test `tests/unit/test_execution_readiness.py` that asserts the function returns True when all conditions are met and False with specific error messages when conditions are not met.

- [X] T099 [P] **Final Pipeline Integration Test**: Create a comprehensive integration test `tests/integration/test_full_pipeline.py` that simulates the entire research pipeline from data generation (using `--simulate` for CI) to final report generation.
 - **Logic**:
  1. Run `code/simulator/simulator.py --n <N> --seed 42 --output data/raw/ci_sessions.json`.
  2. Run `code/analysis/clean_data.py --input data/raw/ --output data/processed/ --simulate`.
  3. Run `code/analysis/run_analysis.py --input data/processed/cleaned_sessions.csv --output data/processed/report_summary.txt`.
  4. Verify all expected output files exist (`data/processed/cleaned_sessions.csv`, `data/processed/metrics_summary.csv`, `data/processed/power_report.md`, `figures/*.png`).
  5. Verify the `report_summary.txt` contains the expected statistical results (ANOVA F-stat, p-value, effect size).
 - **Deliverable**: `tests/integration/test_full_pipeline.py` with the full pipeline simulation and verification logic. **Dependencies**: T097, T098, T029b.
 - **Verification**: Run `pytest tests/integration/test_full_pipeline.py` and verify all assertions pass.

- [X] T100 [P] **Documentation Finalization**: Update `README.md` and `docs/quickstart.md` with explicit instructions for running the pipeline in both production (real data) and development (simulated data) modes, including the "Fail Loudly" behavior and the `--simulate` flag usage.
 - **Logic**: Ensure the documentation clearly states that `--simulate` is ONLY for local testing and CI, and that production runs MUST fail if real data is missing.
 - **Deliverable**: Updated `README.md` and `docs/quickstart.md`. **Dependencies**: T097, T098.
 - **Verification**: Manual review of the documentation to ensure clarity and accuracy.

- [X] T101 [P] **Power Analysis Gate Enforcement**: Implement a hard gate in `code/analysis/run_analysis.py` that blocks the pipeline if the power analysis (T036) indicates 'UNDERPOWERED' and the sample size is below the constitutional threshold (N=30).
 - **Logic**: Check `power_flags.json` (T036) before generating the final report. If 'UNDERPOWERED' and N < 30, raise `RuntimeError` and exit.
 - **Deliverable**: Updated `code/analysis/run_analysis.py` with the gate logic. **Dependencies**: T036.

- [X] T102 [P] **Main Entry Point Data Integrity**: Integrate T097 and T098 checks into the `main.py` or `run_analysis.py` entry point to ensure the pipeline fails *before* any processing occurs in production mode.
 - **Logic**: Call `verify_execution_readiness()` (T098) and the "Fail Loudly" check (T097) as the first step in `main.py`. If either fails, exit immediately.
 - **Deliverable**: Updated `main.py` or `run_analysis.py` with the integration logic. **Dependencies**: T097, T098.

- [X] T103 [P] **State Checksum Update**: Update `state/projects/...yaml` with the checksum from T021c-hash.
 - **Logic**: Read the checksum from T021c-hash and update the `state/projects/...yaml` file.
 - **Deliverable**: Updated `state/projects/...yaml`. **Dependencies**: T021c-hash.

- [X] T104 [P] **Sample Size Verification Artifact**: Generate `data/sample_size_verification.json` as part of the power analysis step.
 - **Logic**: Integrate the generation of `data/sample_size_verification.json` into the power analysis workflow (T036/T036b).
 - **Deliverable**: `data/sample_size_verification.json`. **Dependencies**: T036, T036b.

- [X] T105 [P] **Integrate Power Gate into Final Report**: Explicitly wire the power analysis result into the final decision gate and report generation.
 - **Logic**: Update the report writer (T025d) to include the power analysis result and the N=30 enforcement status in the final report.
 - **Deliverable**: Updated `report_summary.txt` or `power_report.md`. **Dependencies**: T036b, T101.