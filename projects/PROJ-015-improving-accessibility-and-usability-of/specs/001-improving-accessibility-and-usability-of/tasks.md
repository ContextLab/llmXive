# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Input**: Design documents from `/specs/015-improving-accessibility-usability/`
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
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt`. **Deliverable**: `requirements.txt` containing pinned versions of `scipy`, `matplotlib`, `pandas`, `jupyter`, `streamlit`, `pyyaml`, `numpy`, `statsmodels`. **Verification**: File exists and contains version pins (e.g., `{{claim:c_92731a70}}`, `{{claim:c_548e8345}}`, `{{claim:c_197b1480}}`).
- [X] T003a [P] Create `.ruff.toml` configuration file. **Content**: Must contain `[lint]` section with `select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "TCH", "T20"]`. **Verification**: File exists and contains the specified select list.
- [X] T003b [P] Create `pyproject.toml` configuration for Black. **Content**: Must contain `[tool.black]` section with `line-length = 88 [UNRESOLVED-CLAIM: c_839a8a73 — status=not_enough_info]` and `target-version = ['py311'] [UNRESOLVED-CLAIM: c_77d26e85 — status=not_enough_info]`. **Verification**: File exists and contains the specified configuration block.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Data Integrity Gates.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Active Tasks (Foundational)
- [X] T012c [P] Create the skeleton Streamlit app entry point `code/simulator/app.py`. **Deliverable**: `code/simulator/app.py`. **Verification**: Runs without import errors. **Dependencies**: None.
- [X] T012a [P] Create `CONTRIBUTING.md` with the mandatory "no synthetic data" clause and schema compliance guidelines. **Deliverable**: `CONTRIBUTING.md`. **Content**: Must include the clause: "No synthetic data is allowed for final research claims. The pipeline must fail loudly if real data is missing. [UNRESOLVED-CLAIM: c_e17a2a16 — status=not_enough_info] "
- [X] T019b [P] Create `contracts/session.schema.yaml`. **Deliverable**: `contracts/session.schema.yaml` defining the JSON schema for session data (participant_id, interface_type, metrics, status, source, etc.). **Dependencies**: None.
- [X] T019c Implement runtime schema validation logic in `code/simulator/validator.py`. **Deliverable**: `code/simulator/validator.py` with a function `validate_session(data: dict) -> bool`. **Dependencies**: T019b.
- [X] T019d [P] **Runtime Integration**: Hook `validator.py` into the Streamlit `app.py` data submission handler. **Scope**: Implement function `submit_session_handler` in `code/simulator/app.py` that calls `validate_session`. If validation fails, **raise `ValueError`** and **block** the session write to `data/raw/`. **Deliverable**: Updated `code/simulator/app.py`. **Dependencies**: T012c, T019c.
- [X] T120 [P] **Implement Real Data Loader**: Create `code/analysis/data_loader.py` with function `load_real_data(input_dir: str, dev_mode: bool = False) -> pd.DataFrame`. **Constraint**:
 1. Must raise `FileNotFoundError` if `data/raw/` is empty.
 2. Must raise `FileNotFoundError` if `data/raw/` contains ONLY files where `source == 'simulated'` AND `dev_mode` is False.
 3. Must accept files where `source == 'simulated'` ONLY if `dev_mode` is True.
 4. Must explicitly reference `contracts/session.schema.yaml` to validate the `source` field enum (`['human_participant', 'simulated']`).
 **NO synthetic fallback allowed.** **Dependencies**: T019b.
- [X] T121 [P] **Data Loader Failure Test**: Create `tests/unit/test_data_loader_failure.py` to assert `load_real_data` raises `FileNotFoundError` when `data/raw/` is empty or contains only simulated data without dev_mode. **Dependencies**: T120.
- [X] T035a-verify [Foundational] **SPEC VERIFICATION (Script)**: Create `scripts/verify_spec_amendment.py` to parse `specs/015-improving-accessibility-usability/spec.md` and assert the presence of the ratified FR-002 text for Repeated Measures ANOVA. **Deliverable**: Script that exits 0 on success, 1 on failure. **Dependencies**: T001, T002. **Verification**: Script runs successfully against the spec file.
- [X] T035a-assert [Foundational] **SPEC ASSERTION (Test)**: Create `tests/test_spec_amendment.py` that invokes `scripts/verify_spec_amendment.py` and asserts the exit code is 0. **Deliverable**: Pytesttest. **Dependencies**: T035a-verify. **Verification**: Test passes.
- [ ] T006-pre [P] **A Priori Power Analysis**: Implement `code/analysis/power_analysis.py` function `run_a_priori_power_analysis, power=0.80 [UNRESOLVED-CLAIM: c_e078b821 — status=not_enough_info]) -> dict` to justify N=30 per Constitution Principle VI [UNRESOLVED-CLAIM: c_2187150d — status=not_enough_info]. **Deliverable**: `docs/a_priori_power_report.md` justifying N=30 based on Cohen's d=0.5 [UNRESOLVED-CLAIM: c_f7e1cbf3 — status=not_enough_info]. **Constraint**: This task MUST run BEFORE data collection. **Dependencies**: T035a-verify. **Verification**: Report exists and explicitly states N=30 is required for pre-study justification. **Note**: Cites Constitution Principle VI.
- [X] T108 [P] **Pipeline Order Enforcement**: Implement `precondition_check()` in `code/analysis/run_analysis.py` that raises an error if `cleaned_sessions.csv` is missing before proceeding to normality, ANOVA, correction, and power steps. **Dependencies**: T021c-cli (cleaning logic must exist to be checked). **Verification**: Unit test asserts `precondition_check` raises error if `cleaned_sessions.csv` is missing.
- [X] T113 [P] **Report Consistency Check**: Add checksum verification in `code/analysis/run_analysis.py` that compares `report_summary.txt` content against source CSVs (`metrics_summary.csv`, `descriptive_stats_explanation_engagement.csv`). Fail if mismatched. **Dependencies**: T025d.
- [X] T015 [P] **Implement Latin Square Counterbalancing:** Create `code/simulator/counterbalance.py` with functions to generate a balanced sequence of interface presentations (Traditional -> Explainable or vice versa). **Deliverable:** A function that takes the number of participants as input and returns an array indicating the order of presentation for each participant. Integrate this into T012e (`render_interface`) to assign interfaces based on this generated order.
- [X] T120b [P] **Analysis Entry Gate**: Implement `check_data_integrity()` in `code/analysis/run_analysis.py` that runs BEFORE `load_real_data`. **Scope**: Must inspect `data/raw/` and raise `ValueError` if any file has `source='simulated'` and `dev_mode` is not explicitly set in the CLI. This enforces NFR-002 at the analysis entry point, preventing bypass of the loader. **Dependencies**: T019b, T120.

---

## Phase 3: User Story 0 - XAI Interface & Recruitment (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to evaluate the usability of computer systems for people with disabilities, specifically focusing on gene regulation interfaces. **Includes Real Data Capture.**

### Implementation for User Story 0
- [X] T010 [P] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py`
- [X] T011 [P] Implement `ExplainableInterface` renderer in `code/simulator/interfaces/explainable.py`
- [X] T013a Define the overlay data schema in `code/simulator/schemas/overlay_schema.yaml`. **Deliverable**: Schema file.
- [X] T013b Implement `RuleBasedXAIOverlayGenerator` in `code/simulator/xai_overlay.py`. **Dependencies**: T013a.
- [X] T012d1 [US0] Implement UI renderer integration in `code/simulator/app.py`. **Scope**: Implement function `render_interface(interface_type: str, task_input: dict) -> dict` returning a dict with keys `html_content` (string) and `accessibility_settings` (dict). **Dependencies**: T010, T011, T012c.
- [X] T012d2 [US0] Implement input capture module in `code/simulator/input.py`. **Scope**: Implement function `capture_input() -> dict` returning `consent_status`, `participant_id`, and `input_events`. **Dependencies**: T012c.
- [X] T012d3 [US0] Implement SUS form logic in `code/simulator/input.py`. **Scope**: Implement function `calculate_sus_score(responses: list) -> dict`. **Dependencies**: T012d2.
- [X] T012d4 [US0] Implement State Management Module:
 - T012d4a - Implement `init_state()` in `code/simulator/state.py` to initialize the simulation state.
 - T012d4b - Implement `increment_phase()` in `code/simulator/state.py` to advance the simulation phase.
 - T012d4c - Implement `switch_sequence()` in `code/simulator/state.py` to switch between interface presentation sequences. **Dependencies**: T012d2.
- [X] T012e [US0] Integrate XAI Overlay and Counterbalancing into the Streamlit flow. **Scope**: Implement function to render interfaces based on generated order from `code/simulator/counterbalance.py`. Render overlay data as needed. **Dependencies**: T010, T011, T012c, T012d1, T012d2, T012d3, T012d4a, T012d4b, T012d4c, T015.
- [X] T012g [US0] Implement Accessibility Accommodations in `code/simulator/accessibility.py`. **Scope**: Provide UI components: `font_size_slider` (st.slider), `high_contrast_toggle` (st.checkbox), `keyboard_nav_checkbox` (st.checkbox). Update `st.session_state['font_size']`, `['high_contrast']`, `['keyboard_nav']`. **Dependencies**: T012d4a.
- [X] T012h [US0] Implement Disability Type Selection in `code/simulator/accessibility.py`. **Scope**: Render selector and store choice in session JSON under `disability_type`. **Dependencies**: T012g.
- [X] T042 [US0] **Recruitment Interface**: Implement Consent Form and Participant Onboarding Flow in `code/simulator/app.py`. **Scope**: Render consent form (HTML), capture `consent_status`, and implement `generate_recruitment_link()` utility. **Dependencies**: T012d2, T012h.
- [X] T012f-main [US0] Implement Human Interaction Loop Orchestration in `code/simulator/orchestrator.py`. **Scope**: `run_human_loop()` calls `render_accessibility_settings()`, `capture_input()`, `calculate_sus_score()`, `manage_state()`. **Dependencies**: T012d1, T012d2, T012d3, T012d4a, T012d4b, T012d4c, T012g, T012h, T042.
- [X] T012i [US0] Implement Gene Regulation Task Logic in `code/simulator/tasks/gene_task.py`. **Scope**: Functions `render_task()`, `validate_task_completion()`, `calculate_task_metrics()`. **Dependencies**: T012d1.
- [X] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`.
- [X] T048 [US0] Refactor `code/simulator/state.py` to ensure `manage_state()` is fully functional and exposes `current_sequence` and `interface_variant` **after** T012e integration. **Dependencies**: T012e.
- [X] T049 [US0] **Real Data Capture**: Ensure all data collection logic (SUS, time, errors) is correctly integrated into the simulator's data flow and written to `data/raw`.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Implement the core usability benchmarking tasks.

### Implementation for User Story 1
- [X] T016 [P] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [X] T016b [P] Ensure `explanation_engagement_time_seconds` is logged to raw session files under `data/raw/`. **Dependencies**: T019b, T019c, T019d.
- [X] T049 [US1] Ensure `metrics_collector.calculate_task_metrics()` is called within `run_human_loop()` after task completion and before session logging. **Dependencies**: T012f-main, T016.
- [X] T017 [P] Integrate collectors, counterbalancing, and SUS questionnaire into the Streamlit flow, with SUS imputation rules (≤1 missing → impute with participant mean). **Dependencies**: T012f-int, T012g, T012h, T049, T016.
- [X] T020 [P] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` in `code/simulator/session_logger.py`.
- [ ] T031-gen [DEV MODE ONLY] **DEV MODE ONLY**: Implement `generate_sessions(n, seed)` in `code/simulator/simulator.py`. **Output Artifact**: `data/raw/simulated_sessions.json`. **Logic**: Generate synthetic sessions using `numpy.random.normal` for metrics (completion_time, errors, SUS) with `seed`. **Schema**: Must match `contracts/session.schema.yaml`. **Constraint**: This generator is strictly for development and CI testing. It MUST require a `--dev-mode` flag to run. **CRITICAL**: Must set `source: 'simulated'` in every generated session JSON. **Dependencies**: T019b. **Verification**: Run CLI with `--n --seed 42 --dev-mode` and assert output file contains a small number of records with valid schema AND `source: simulated`.
- [ ] T031-cli [DEV MODE ONLY] **DEV MODE ONLY**: Implement CLI wrapper for `DeterministicDataSimulator` in `code/simulator/simulator.py`. **Deliverable**: CLI command `python -m code.simulator.simulator --n <N> --seed 42 --dev-mode --output data/raw/simulated_sessions.json`. **Constraint**: This CLI is strictly for development and CI testing. **Dependencies**: T031-gen. **Verification**: Run command and verify file creation.
- [X] T031b [P] Add JSON‑Schema validation to the simulator output. **Dependencies**: T031-cli, T019b.
- [X] T031c [P] Extend simulator to generate dropout sessions via `--dropout-rate`. **Dependencies**: T031-cli.
- [X] T032 [P] Create unit tests for simulator (completion time diff, engagement time positivity, schema compliance). **Dependencies**: T031-gen, T031b.
- [X] T021a Implement data cleaning filter in `code/analysis/data_cleaner.py`: remove sessions where `status='incomplete'`. Update the session status field to 'incomplete'. **Deliverable**: Function that filters and updates the dataframe. **Dependencies**: T019b, T117, T120
- [X] T021b Implement SUS imputation in `code/analysis/data_cleaner.py`: if ≤1 SUS item missing, replace with participant mean *and update session status to 'incomplete'*; otherwise, mark as incomplete and update session status field. **Deliverable**: Function that imputes and updates the dataframe. **Dependencies**: T021a
- [X] T023a [P] **Implement Repeated Measures ANOVA**: Create `code/analysis/anova_engine.py`. **Scope**: Implement `run_anova_rm(df, subject_col, within_col, dv_col)` using `statsmodels.stats.anova.AnovaRM` (Mandatory for within-subject design). **Constraint**: The output `metrics_summary.csv` MUST include a column `method_used` that explicitly states 'Repeated Measures ANOVA'. **Dependencies**: T021c-cli, T022.
- [X] T036a Calculate Observed Power using `scipy.stats` for each metric after ANOVA. Output to `data/processed/observed_power.csv`. **Deliverable:** CSV file with observed power values. **Dependencies**: T023a.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

- [X] T024 Implement Holm‑Bonferroni correction for the three metric ANOVAs. **Dependencies**: T023a.
- [X] T025a Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`). **Dependencies**: T035a-apply.
- [X] T025b Implement data cleaning and SUS imputation in `code/analysis/data_cleaner.py`. **Dependencies**: T019b, T021a, T021b
- [ ] T025c-logic [P] **Define Analysis Orchestration Logic**: Create `code/analysis/run_analysis.py` control flow logic. **Scope**:
 1. Define `run_pipeline()` function signature: `run_pipeline(input_dir, output_dir, mode='full')`.
 2. Implement control flow: Load -> Clean -> Check Normality (Shapiro) -> Run ANOVA (or Fallback) -> Apply Holm-Bonferroni -> Calculate Power -> Generate Reports.
 3. Implement error handling: `try/except` blocks for each step; if Shapiro fails, log warning and proceed to ANOVA (as per spec).
 4. Define output file naming: `metrics_summary.csv`, `power_report.md`, `figures/*.png`.
 5. **CRITICAL**: Implement `if mode == 'pilot':` logic to bypass the N=30 power gate.
 **Dependencies**: T025a, T021a, T021b, T023a, T024, T036a.
- [ ] T025c-impl [P] **Implement Analysis Orchestration**: Create `code/analysis/run_analysis.py` main logic. **Scope**: Implement the `run_pipeline()` function strictly following the control flow defined in T025c-logic, ensuring the pilot mode bypass logic is enforced. **Dependencies**: T025c-logic, T025a, T021a, T021b, T023a, T024, T036a.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

### Implementation for User Story 3
- [X] T027a Implement `plot_completion_time()` in `code/analysis/visualizer.py` using `seaborn.boxplot` or `violinplot`. **Dependencies**: T023a, T023b.
- [X] T027b Implement `plot_error_count()` in `code/analysis/visualizer.py`. **Dependencies**: T023a.
- [X] T027c Implement `plot_sus_score()` in `code/analysis/visualizer.py`. **Dependencies**: T023a.

---

## Phase 7: Pilot Study & Validation (Priority: P4)

### Implementation for Pilot Study
- [X] T095-gate [P] **Pilot Study Gate**: Implement `check_pilot_eligibility()` in `code/analysis/pilot_gate.py`. **Scope**: Verify `data/raw/` contains at least N=5 sessions with `status='complete'` and `source='human_participant'` (or `dev_mode` simulated). **Dependencies**: T019b.
- [X] T096a [P] **Define Pilot Script Logic**: Create `docs/pilot_study_protocol.md` detailing the CLI arguments (`--mode pilot`, `--n 5`, `--seed 42`), expected exit codes (0=success, 1=fail), and environment variables required for the pilot run. **Dependencies**: T095-gate.
- [X] T096b [P] **Implement Pilot Script**: Create `scripts/run_pilot_study.sh`. **Scope**: Implement the script using the logic from T096a. Must invoke `python -m code.analysis.run_analysis --mode pilot --n <n_samples> --seed 42` with a small, pilot-scale sample size. **CRITICAL**: The script must validate the exit codes returned by the analysis command and exit with the same codes (0 or 1) as defined in T096a. Must log results to `data/pilot_report.md`. **Dependencies**: T096a, T025c-impl.
- [X] T097 [P] **Real Data Validation**: Implement `validate_real_data_source()` in `code/analysis/validator.py`. **Scope**: Assert that `data/raw/` contains files with `source='human_participant'` before allowing `mode='full'` recruitment. **Dependencies**: T019b, T120.
- [X] T098 [P] **Full Recruitment Gate**: Implement `check_full_recruitment_ready()` in `code/analysis/run_analysis.py`. **Scope**: Verify `data/pilot_report.md` exists and shows success before allowing `mode='full'`. **Dependencies**: T096b.
- [X] T036 [P] **Observed Power Report**: Implement `generate_power_report()` in `code/analysis/power_analysis.py`. **Scope**: Calculate observed power. **Constraint**: **IF** `mode != 'pilot'`, raise `ValueError` if N < 30. **IF** `mode == 'pilot'`, allow N=5 and log a warning. **Dependencies**: T023a, T025c-impl.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T122 Reconcile run-book vs implementation for `code/analysis.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/analysis.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
