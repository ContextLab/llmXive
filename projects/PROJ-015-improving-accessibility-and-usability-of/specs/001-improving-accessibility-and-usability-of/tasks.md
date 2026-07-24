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
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt`. **Deliverable**: `requirements.txt` containing pinned versions of `scipy`, `matplotlib`, `pandas`, `jupyter`, and `streamlit`. **Verification**: File exists and contains version pins (e.g., `scipy==1.11.0`).
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
 - This policy is the basis for the technical enforcement implemented in T033 and T019c.

 ## Schema Compliance
 - All session data MUST conform to `contracts/session.schema.yaml`.
 - Any deviation from the schema will cause the data loader to reject the file.
 ```
 **Dependencies**: None.

- [X] T015 [P] Implement Latin Square counterbalancing in `code/simulator/counterbalance.py` to assign the order of interface presentation (Traditional->Explainable or Explainable->Traditional) to mitigate order effects. **Deliverable**: `code/simulator/counterbalance.py` with a function `assign_sequence(participant_id) -> str`. **Dependencies**: None. **Note**: Moved from Phase 4 to Phase 2 to resolve ordering dependency with T012e. **Clarification on [P] Tag**: The [P] tag indicates this task can be developed in parallel with other Phase 2 foundational tasks (like T019b/c). However, its *execution* is a hard dependency for downstream tasks T012d4 and T012e; those tasks cannot run until T015 is complete.

- [X] T035a-apply [Foundational] **SPEC AMENDMENT (Apply)**: Verify `spec.md` FR-002 contains the ratified amendment text for Repeated Measures ANOVA. **Deliverable**: Verified `spec.md`. **Dependencies**: None.

- [X] T019c [US1] Implement runtime schema validation logic in `code/simulator/validator.py`. **Deliverable**: `code/simulator/validator.py` with a function `validate_session(data: dict) -> bool`. **Dependencies**: T019b.

### Active Tasks (Data & Logging)
- [X] T019 [US1] Implement raw data logging to `data/raw/session_{session_id}.json`. **Logic**: Implement function `log_session(data: dict, session_id: str)` in `code/simulator/session_logger.py`. The JSON **must** contain the fields defined in `contracts/session.schema.yaml`. The task **must abort** if the schema file is absent (enforced by the completion of T019b) OR if the data fails validation (enforced by T019c). **Deliverable**: One JSON file per completed (or incomplete) session stored under `data/raw/`. **Verification**: Schema validation pass on the generated JSON. **Dependencies**: T019b, T019c.

**Checkpoint**: Foundation complete - T019b, T019c, and T035a-apply are done. User story implementation can now begin.

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
- [ ] T012d4 [US0] Implement state management for sequence switching in `code/simulator/state.py`. **Scope**: Implement function `manage_state() -> dict` using `st.session_state` keys `current_sequence`, `current_phase`, and `interface_variant`. **Deliverable**: `code/simulator/state.py` with `manage_state` function. **Dependencies**: T012d3, T015.

- [X] T012e [US0] Integrate XAI Overlay and Counterbalancing into the Streamlit flow. **Logic**: Ensure `RuleBasedXAIOverlayGenerator` (T013b) is called when rendering the `ExplainableInterface` and that the `LatinSquareCounterbalancer` (T015) dictates the sequence. **Deliverable**: `code/simulator/app.py` with verified integration of counterbalancing and XAI logic. **Verification**: Verify that for participant_id=1, the app renders Traditional first, then Explainable, and logs sequence_order=[1,2] in the session JSON. **Dependencies**: T013b, T015, T012d1, T012d2, T012d3, T012d4.
- [X] T012g [US0] Implement Accessibility Accommodations in `code/simulator/accessibility.py`. **Scope**: Implement function `render_accessibility_settings() -> dict` to provide UI components for accessibility settings (e.g., font size, contrast, keyboard navigation). **Deliverable**: `code/simulator/accessibility.py` with `render_accessibility_settings` function. **Dependencies**: T012d4.
- [X] T012h [US0] Implement Disability Type Selection in `code/simulator/accessibility.py`. **Scope**: Implement function `render_disability_selector() -> str` to allow participants to select their disability type. **Deliverable**: `code/simulator/accessibility.py` with `render_disability_selector` function. **Dependencies**: T012g.

- [X] T012f-main [US0] Implement Human Interaction Loop Orchestration in `code/simulator/orchestrator.py`. **Scope**: Implement function `run_human_loop() -> dict` within `code/simulator/orchestrator.py`. This function orchestrates the flow by calling `render_accessibility_settings()`, `capture_input()`, `calculate_sus_score()`, and `manage_state()` in sequence. **Deliverable**: `code/simulator/orchestrator.py` with `run_human_loop` function. **Dependencies**: T012d2, T012d3, T012d4, T012g, T012h.
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
- [X] T017 [P] Integrate all collectors (T016, T016b, T015) and SUS questionnaire into the Streamlit app flow in `code/simulator/app.py` ensuring sequence order is respected. Implement SUS validation: reject if >1 item missing; if ≤1 missing, impute with participant mean and log imputation. **Dependencies**: T012f-int, T012g, T012h.
- [X] T020 [P] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` for partial sessions in `code/simulator/session_logger.py`.

**Checkpoint**: The system can collect real‑time interaction data, handle dropouts, and store immutable raw logs with schema validation.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

**Goal**: Perform statistical analysis (Repeated Measures ANOVA, Holm‑Bonferroni) on collected metrics to determine significance.

**Independent Test**: The analysis module can be tested by feeding it a pre-generated CSV file with known distributions and verifying that ANOVA F-statistics, adjusted p-values, and effect sizes are calculated correctly.

### Implementation for User Story 2

- [X] T025a [P] Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`) and basic orchestration calls. **Deliverable**: `code/analysis/run_analysis.py`. **Verification**: File exists and can be called without errors. **Dependencies**: T035a-apply.
- [X] T021a [P] Implement data cleaning in `code/analysis/data_cleaner.py`. **Logic**: 1. Filter out sessions with `status='incomplete'`. 2. If ≤1 SUS item missing, impute with participant mean; if >1, reject session. **Output**: `data/processed/cleaned_sessions.csv`. **Dependencies**: T019b.
- [X] T021b [P] Implement SUS imputation logic in `code/analysis/data_cleaner.py`. **Logic**: If ≤1 item missing, impute with participant mean; if >1, mark as incomplete. **Dependencies**: T021a.
- [ ] T021c [US2] Orchestrate the cleaning pipeline. **Logic**: Implement `code/analysis/clean_data.py` with CLI `--input` and `--output` flags that sequentially calls `filter_incomplete()` (T021a) and `impute_sus()` (T021b). Verify the presence of `dropout_reason` logs for all excluded sessions to satisfy SC-005. **Output**: `data/processed/cleaned_sessions.csv`. **Constraint**: The output file MUST be checksummed using SHA-256 and the checksum recorded in `state/projects/PROJ-015-improving-accessibility-and-usability-of.yaml` under the key 'cleaned_sessions_checksum'. **Dependencies**: T019b, T021a, T021b.
- [X] T021d [P] Verify SUS imputation logic. **Logic**: Write a test script that generates a session with one missing SUS item, runs the cleaner, and asserts the imputed value matches the participant mean. **Deliverable**: `tests/unit/test_imputation.py`. **Dependencies**: T021b.
- [X] T021e [P] Implement dropout verification logic. **Logic**: Write a script or test that asserts `dropout_reason` is populated for every session where `status='incomplete'` in the raw data. **Deliverable**: `tests/unit/test_dropout_verification.py` or logic in `clean_data.py`. **Dependencies**: T021a.
- [X] T022 [P] Implement Shapiro‑Wilk normality test on difference scores in `code/analysis/stat_utils.py` and log results to `data/processed/normality_log.txt` (audit only). **Deliverable**: `data/processed/normality_log.txt` containing a CSV/JSON with `metric`, `shapiro_statistic`, `p_value`. **Dependencies**: T035a-apply.
- [ ] T023a [US2] Implement **Repeated Measures ANOVA** for Completion Time, Error Count, and SUS in `code/analysis/stat_utils.py`. **Constraint**: Explicitly filter out `explanation_engagement_time` from the ANOVA input. The input data should be in 'long format' with columns `participant_id`, `interface_type`, and the metric being analyzed. Use `scipy.stats.rmanova`. **Deliverable**: `data/processed/metrics_summary.csv` with columns `metric_name, interface_type, F_statistic, p_value, adjusted_p_value, effect_size`. **Dependencies**: T035a-apply.
- [ ] T023b [US2] Compute descriptive statistics (mean, std) for `explanation_engagement_time` and output to `data/processed/descriptive_stats.csv`.
- [X] T024 [P] Implement Holm‑Bonferroni correction for the multiple ANOVA comparisons in `code/analysis/stat_utils.py`. **Dependencies**: T035a-apply.
- [X] T024a [P] Verify primary ANOVA p‑value < 0.05 before applying Holm‑Bonferroni; write verification result to `data/processed/primary_test_verification.txt`.
- [X] T025c-orch [P] Implement statistical engine orchestration in `code/analysis/run_analysis.py`. **Logic**: Import and call `shapiro_wilk()`, `anova_rm()`, `holm_bonferroni()`, and `descriptive_stats()` in sequence. **Deliverable**: `code/analysis/run_analysis.py` with the orchestration logic. **Dependencies**: T022, T023a, T024, T023b.
- [X] T025c-log [P] Implement statistical engine error logging in `code/analysis/run_analysis.py`. **Scope**: Implement error handling logic within `execute_pipeline()` to log any import errors or execution failures to `data/processed/error_log.txt`. **Dependencies**: T025c-orch.
- [X] T025d [P] Implement report writer in `code/analysis/run_analysis.py`. **Scope**: Implement function `write_report()` within `run_analysis.py`. **Logic**: Write `metrics_summary.csv`, `report_summary.txt`. Verify that the CSV contains the required columns before exiting. **Documentation**: Include a comment block citing "Constitution Principle VII" and "Spec FR-002 (Amended by T035a)" as the basis for using ANOVA. **Deliverable**: `code/analysis/run_analysis.py` with report generation logic. **Dependencies**: T025c-log.
- [X] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py`:
 - Compute statistical power given N, effect size (eta‑squared), and α = 0.05.
 - **Logic**: If N < 30 for any subgroup, flag as 'UNDERPOWERED'.
 - **Deliverable**: `data/processed/power_flags.json` with schema `{ "subgroup": "<str>", "N": <int>, "power": <float>, "flag": "<UNDERPOWERED|OK>" }`.
 - **Dependencies**: T023a.
- [X] T036b [US2] Generate Power Analysis Report. **Logic**: Implement logic to integrate `power_flags.json` (T036) into the final `report_summary.txt` or generate a dedicated `data/processed/power_report.md`. **Deliverable**: `data/processed/power_report.md`. **Dependencies**: T025d.

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
- [X] T028 Compile `code/analysis/analysis.ipynb` that:
 1. Loads raw data, runs cleaning, performs ANOVA, creates visualizations, runs power analysis.
 2. Contains markdown explanations for each step.
 3. Saves all generated artifacts.
 4. **Constraint**: The notebook must fail if `data/raw/` is empty unless `--simulate` (dev mode) is used (NFR-002).
 **Deliverable**: `code/analysis/analysis.ipynb`.  **Verification**: Verify execution via `nbconvert`. **Dependencies**: T021c, T025c-log, T027a, T027b, T027c.
- [X] T030 Ensure the notebook is fully deterministic. **Logic**: Pin random seeds, use exact file paths, and verify that re‑running produces identical checksums for generated figures. **Deliverable**: `code/analysis.ipynb` with pinned seeds and checksum verification logic. **Dependencies**: T028.
- [X] T029b Create a unified `Makefile` or `run_pipeline.sh` script in the repository root. **Status**: Active - Implementation Required. **Scope**: Implement a script that chains T031-cli (simulation), T021c (cleaning), T025c-log (analysis), and T028 (notebook execution) into a single command. **Deliverable**: `Makefile` with targets `simulate`, `clean`, `analyze`, `report`, and `all`. **Dependencies**: T028, T021c
- [X] T029c Implement a final "Readiness Check" task to verify the existence of all required artifacts.

---

## Phase 7: Data Simulation & Synthetic Fallback Prevention (Priority: P0)

**Goal**: Implement a deterministic, rule-based simulator to generate realistic interaction data for pilot testing and CI validation, strictly adhering to the "No Synthetic Fallback" rule for real data.

**Independent Test**: The simulator generates a dataset where the "Explainable" interface is mathematically guaranteed to be faster by a fixed offset, allowing verification of the ANOVA pipeline's ability to detect the effect.

### Implementation for Phase 7

- [X] T031-gen Implement `generate_sessions(n, seed)` function in `code/simulator/simulator.py`.
 - **Logic**: Generate synthetic sessions based on `N` participants. The "Explainable" condition has `completion_time` = `baseline_time` - 5.0 seconds; the "Traditional" condition has `completion_time` = `baseline_time`. Random noise is added (Gaussian) but seeds are pinned. **Deliverable**: `code/simulator/simulator.py` with `generate_sessions` function. **Verification**: Unit test asserts mean difference equals 5.0 seconds. **Dependencies**: T019b.

- [X] T031-cli Implement CLI wrapper for `DeterministicDataSimulator` in `code/simulator/simulator.py`.
 - **Deliverable**: A CLI tool `python -m code.simulator.simulator --n 50 --seed 42 --output data/raw/simulated_sessions.json`.
 - **Dependencies**: T031-gen.

- [X] T031b Implement schema validation in `code/simulator/simulator.py` to ensure the output of `DeterministicDataSimulator` (T031-gen) strictly matches the schema defined in `contracts/session.schema.yaml`.
 - **Logic**: The simulator must abort if the schema file is absent or data fails validation.
 - **Dependencies**: T031-cli, T019b.

- [X] T031c Extend `DeterministicDataSimulator` to generate a subset of "dropout" sessions. **Logic**: For a configured percentage, set `status='incomplete'` and populate `dropout_reason` with a random reason from a predefined list. **Deliverable**: Updated `code/simulator/simulator.py` with `--dropout-rate` flag. **Dependencies**: T031-cli.

- [X] T032 Create `tests/unit/test_simulator.py` to verify that:
 - The simulator produces the expected fixed difference in completion time.
 - `explanation_engagement_time` is strictly positive for Explainable and zero for Traditional.
 - The output JSON schema matches `contracts/session.schema.yaml`.

- [X] T033 Update `code/analysis/run_analysis.py` to accept a `--simulate` flag that triggers `DeterministicDataSimulator` if no raw data is found, **BUT** only for local CI validation.
 - **Critical Rule**: This flag MUST be explicitly disabled in production runs. The production pipeline must **fail loudly** (exit with a non-zero error code) if `data/raw/` is empty and the `--simulate` flag is not set.

---

## Phase 8: Spec-Plan Alignment Verification (Priority: P0)

**Goal**: Verify that the implementation strictly follows the Plan's scientific rigor and that the Spec amendment (T035a-apply) has been successfully applied and documented.

**Independent Test**: Run the analysis pipeline on a small sample dataset; verify that ANOVA is used, Levene’s test is not invoked, and all steps are clearly documented.

### Implementation for Phase 8

- [X] T035 [US2] Update `code/analysis/stat_utils.py` to explicitly document the ratified Spec amendment.
- [X] T035c [US2] Update `code/analysis/run_analysis.py` to write a `methodology_notes.txt` file in `data/processed/` that lists the statistical tests used and cites the amended Spec section (FR-002).
- [X] T035d [US2] Implement explicit removal of Levene's test logic in `code/analysis/stat_utils.py`.

---

## Phase 9: Accessibility Compliance & Human Participant Validation (Priority: P1) 🎯 Critical

**Goal**: Ensure the web-based simulator (FR-007) meets WCAG 2.1 AA standards for people with disabilities and validate the end-to-end human participant flow with real accessibility accommodations.

### Implementation for Phase 9

- [X] T037 Implement automated accessibility audit script in `tests/contract/test_accessibility_audit.py`.
- [X] T038 Refine accessibility accommodations in `code/simulator/accessibility.py` based on audit results (T037).
- [X] T039 Create a manual "Human Participant Flow" verification script in `tests/manual/test_human_flow.py`.
- [X] T040 Add a pre-commit check to enforce accessibility testing.
- [X] T041 Add accessibility metrics to the final report.

---

## Phase 10: Final Integration & Execution Readiness (Priority: P0)

**Goal**: Ensure all components are integrated, the full pipeline runs end-to-end, and the project is ready for the execution gate.

### Implementation for Phase 10

- [X] T045 Create a unified `Makefile` or `run_pipeline.sh` script in the repository root.
- [X] T046 Add a final "Readiness Check" task to `code/analysis/run_analysis.py`.
- [X] T047 Generate a final `PROJECT_STATUS.md` document.
