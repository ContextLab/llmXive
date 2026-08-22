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
- [X] T002 Initialize Python project with pinned dependencies in `requirements.txt`. **Deliverable**: `requirements.txt` containing pinned versions of `scipy`, `matplotlib`, `pandas`, `jupyter`, `streamlit`, `pyyaml`, `numpy`. **Verification**: File exists and contains version pins (e.g., `scipy==1.11.0`, `numpy==1.24.0`).
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Data Integrity Gates.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Active Tasks (Foundational)
- [X] T012c [P] Create the skeleton Streamlit app entry point `code/simulator/app.py`. **Deliverable**: `code/simulator/app.py`. **Verification**: Runs without import errors. **Dependencies**: None.
- [X] T012a [P] Create `CONTRIBUTING.md` with the mandatory "no synthetic data" clause and schema compliance guidelines. **Deliverable**: `CONTRIBUTING.md`. **Content**: Must include the clause: "No synthetic data is allowed for final research claims. The pipeline must fail loudly if real data is missing."
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
- [X] T035a-apply [Foundational] **SPEC AMENDMENT (Apply)**: Verify `spec.md` FR‑002 contains the ratified amendment text for Repeated Measures ANOVA. **Deliverable**: Verified `spec.md`. **Dependencies**: T001, T002. **Verification**: Task ensures the spec file exists and contains the ratified text before proceeding to analysis tasks.
- [X] T006-pre [P] **A Priori Power Analysis**: Implement `code/analysis/power_analysis.py` function `run_a_priori_power_analysis(effect_size=0.5, alpha=0.05, power=0.80) -> dict`. **Deliverable**: `docs/a_priori_power_report.md` justifying N=30 based on hypothesized effect size (Cohen's d=0.5). **Constraint**: This task MUST run BEFORE data collection. **Dependencies**: T035a-apply. **Verification**: Report exists and explicitly states N=30 is required for pre-study justification.
- [X] T108 [P] **Pipeline Order Enforcement**: Implement `precondition_check()` in `code/analysis/run_analysis.py` that raises an error if `cleaned_sessions.csv` is missing before proceeding to normality, ANOVA, correction, and power steps. **Dependencies**: T021c-cli (cleaning logic must exist to be checked). **Verification**: Unit test asserts `precondition_check` raises error if `cleaned_sessions.csv` is missing.
- [X] T113 [P] **Report Consistency Check**: Add checksum verification in `code/analysis/run_analysis.py` that compares `report_summary.txt` content against source CSVs (`metrics_summary.csv`, `descriptive_stats_explanation_engagement.csv`). Fail if mismatched. **Dependencies**: T025d. **Verification**: Unit test asserts pipeline raises error if checksums mismatch.

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
- [X] T012d4 [US0] **Implement State Management Module**: Consolidate T012d4-init, T012d4-inc, T012d4-swtch into a single module in `code/simulator/state.py`. **Scope**: Implement `init_state()`, `increment_phase()`, `switch_sequence()`. **Dependencies**: T012d2.
- [X] T012e [US0] Integrate XAI Overlay and Counterbalancing into the Streamlit flow. **Dependencies**: T013b, T015, T012d1, T012d2, T012d3, T012d4, T012g, T012h.
- [X] T012g [US0] Implement Accessibility Accommodations in `code/simulator/accessibility.py`. **Scope**: Provide UI components: `font_size_slider` (st.slider), `high_contrast_toggle` (st.checkbox), `keyboard_nav_checkbox` (st.checkbox). Update `st.session_state['font_size']`, `['high_contrast']`, `['keyboard_nav']`. **Dependencies**: T012d4.
- [X] T012h [US0] Implement Disability Type Selection in `code/simulator/accessibility.py`. **Scope**: Render selector and store choice in session JSON under `disability_type`. **Dependencies**: T012g.
- [X] T042 [US0] **Recruitment Interface**: Implement Consent Form and Participant Onboarding Flow in `code/simulator/app.py`. **Scope**: Render consent form (HTML), capture `consent_status`, and implement `generate_recruitment_link()` utility. **Dependencies**: T012d2, T012h.
- [X] T012f-main [US0] Implement Human Interaction Loop Orchestration in `code/simulator/orchestrator.py`. **Scope**: `run_human_loop()` calls `render_accessibility_settings()`, `capture_input()`, `calculate_sus_score()`, `manage_state()`. **Dependencies**: T012d2, T012d3, T012d4, T012g, T012h, T042. **Verification**: Unit test asserts that a test run writes a valid session file to `data/raw/` with a non-simulated `participant_id`.
- [X] T012f-int [US0] Wire `run_human_loop()` into `code/simulator/app.py`. **Dependencies**: T012f-main.
- [X] T012i [US0] Implement Gene Regulation Task Logic in `code/simulator/tasks/gene_task.py`. **Scope**: Functions `render_task()`, `validate_task_completion()`, `calculate_task_metrics()`. **Dependencies**: T012d1.
- [X] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`.
- [X] T048 [US0] Refactor `code/simulator/state.py` to ensure `manage_state()` is fully functional and exposes `current_sequence` and `interface_variant` **after** T012e integration. **Dependencies**: T012e.
- [X] T015 [P] Implement Latin Square counterbalancing in `code/simulator/counterbalance.py` to assign the order of interface presentation (Traditional→Explainable or Explainable→Traditional). **Dependencies**: None. **Note**: This satisfies FR‑004 and must be completed before any UI tasks.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

- [X] T016 [P] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [X] T016b [P] Ensure `explanation_engagement_time_seconds` is logged to raw session files under `data/raw/`. **Dependencies**: T019b, T019c, T019d.
- [X] T049 [US1] Ensure `metrics_collector.calculate_task_metrics()` is called within `run_human_loop()` after task completion and before session logging. **Dependencies**: T012f-main, T016.
- [X] T017 [P] Integrate collectors, counterbalancing, and SUS questionnaire into the Streamlit flow, with SUS imputation rules (≤1 missing → impute with participant mean). **Dependencies**: T012f-int, T012g, T012h, T049, T016. **Note**: T016 is a direct dependency to ensure metrics are available for integration.
- [X] T020 [P] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` in `code/simulator/session_logger.py`.
- [X] T031-gen [DEV] **DEV MODE ONLY**: Implement `generate_sessions(n, seed)` in `code/simulator/simulator.py`. **Output Artifact**: `data/raw/simulated_sessions.json`. **Logic**: Generate synthetic sessions using `numpy.random.normal` for metrics (completion_time, errors, SUS) with `seed`. **Schema**: Must match `contracts/session.schema.yaml`. **Constraint**: This generator is strictly for development and CI testing. It MUST require a `--dev-mode` flag to run. **CRITICAL**: Must set `source: simulated` in every generated session JSON. **Dependencies**: T019b. **Verification**: Run CLI with `--n --seed 42 --dev-mode` and assert output file contains 5 records with valid schema AND `source: simulated`.
- [X] T031-cli [DEV] **DEV MODE ONLY**: Implement CLI wrapper for `DeterministicDataSimulator` in `code/simulator/simulator.py`. **Deliverable**: CLI command `python -m code.simulator.simulator --n <N> --seed 42 --dev-mode --output data/raw/simulated_sessions.json`. **Constraint**: This CLI is strictly for development and CI testing. **Dependencies**: T031-gen. **Verification**: Run command and verify file creation.
- [X] T031b [P] Add JSON‑Schema validation to the simulator output. **Dependencies**: T031-cli, T019b.
- [X] T031c [P] Extend simulator to generate dropout sessions via `--dropout-rate`. **Dependencies**: T031-cli.
- [X] T032 [P] Create unit tests for simulator (completion time diff, engagement time positivity, schema compliance). **Dependencies**: T031-gen, T031b.
- [X] T117 [P] **Raw Data Checksumming** – Compute SHA‑256 checksums for every file under `data/raw/` **and** for all schema files in `contracts/` during the cleaning phase. Record each checksum in `state/projects/PROJ-015-improving-accessibility-and-usability-of.yaml` under `artifact_hashes`. **Dependencies**: Runs after raw data is materialized (i.e., after T031-gen or real data collection). Should be invoked before T021a.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

- [X] T025a [P] Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`). **Dependencies**: T035a-apply.
- [X] T021a [P] Implement data cleaning filter in `code/analysis/data_cleaner.py`: remove sessions where `status='incomplete'`. **Dependencies**: T019b, T117, T120.
- [X] T021b [P] Implement SUS imputation in `code/analysis/data_cleaner.py`: if ≤1 SUS item missing, replace with participant mean; otherwise, mark as incomplete (handled by T021a). **Dependencies**: T021a.
- [X] T021c-cli [P] Implement CLI wrapper `code/analysis/clean_data.py` calling T021a → T021b → export `data/processed/cleaned_sessions.csv`. **Dependencies**: T021a, T021b.
- [X] T021c-hash [P] Extend checksum logic to also record hashes for all raw session files (via T117) and for `contracts/session.schema.yaml`. Update `state/...yaml` accordingly. **Dependencies**: T021c-cli.
- [X] T021c-log [P] Log cleaning actions, imputations, and exclusions to `data/processed/cleaning_log.txt`. **Dependencies**: T021c-cli.
- [X] T021d [P] Unit test verifying SUS imputation correctness. **Dependencies**: T021b.
- [X] T021e [P] Unit test verifying dropout reason presence for incomplete sessions. **Dependencies**: T020.
- [X] T050 [US2] Add validation for `explanation_engagement_time` consistency (missing/zero for Traditional, present for Explainable). **Dependencies**: T021a, T016b.
- [X] T122 [P] **Verify ANOVA Input Data Integrity**: Add a validation step in `code/analysis/stats_engine.py` that checks `cleaned_sessions.csv` has the required columns (`completion_time`, `error_count`, `sus_score`, `interface_type`, `participant_id`) before running ANOVA. Fail loudly if columns are missing. **Dependencies**: T021c-cli. **Verification**: Unit test asserts `stats_engine` raises `ValueError` if columns are missing.
- [X] T022 [P] Implement Shapiro‑Wilk normality test on difference scores in `code/analysis/stat_utils.py`; log to `data/processed/normality_log.txt`. **Dependencies**: T035a-apply.
- [X] T023a [US2] **Implement Repeated Measures ANOVA**: Create `run_anova_rm(df: pd.DataFrame, metric: str, subject_col: str, within_col: str) -> dict` in `code/analysis/stats_engine.py`. **Input**: `cleaned_sessions.csv` (long format). **Output**: **MUST** generate `data/processed/metrics_summary.csv` with columns `metric`, `F_stat`, `p_val`, `corrected_p`. **Constraint**: 
    1. Use `scipy.stats.ttest_rel` (paired t-test) for 2-level within-subject designs, as it is mathematically equivalent to Repeated Measures ANOVA (F = t^2).
    2. **CRITICAL**: All logs, reports, and output labels MUST explicitly state "Repeated Measures ANOVA" to satisfy Spec FR-002 and the ratified amendment. Do NOT label it as "T-Test".
    3. Log Shapiro‑Wilk results to `normality_log.txt` for audit but do not block execution.
    **Dependencies**: T035a-apply, T021c-cli. **Verification**: Unit test with known dataset asserts correct F-statistic and p-value calculation. **Verification 2**: Unit test asserts `run_anova_rm` runs even when normality test fails. **Verification 3**: Assert that `report_summary.txt` labels the test as "Repeated Measures ANOVA".
- [X] T127 [US2] **Implement Effect Size Reporting**: Extend `code/analysis/stats_engine.py` to calculate and log partial eta-squared (η²) for the ANOVA results in `metrics_summary.csv`. **Rationale**: ANOVA F-statistics alone do not indicate magnitude; effect size is required for a complete usability claim per Constitution Principle VII. **Dependencies**: T023a.
- [X] T023b [P] Compute descriptive stats for `explanation_engagement_time` and output to `data/processed/descriptive_stats_explanation_engagement.csv`. Update `report_summary.txt`. **Dependencies**: T023a.
- [X] T024 [P] Implement Holm‑Bonferroni correction for the three metric ANOVAs. **Dependencies**: T023a. **Verification**: Unit test asserts that `data/processed/metrics_summary.csv` exists and contains valid `corrected_p` values derived from the `p_val` column in the same file.
- [X] T024a [P] [NB] Verify primary ANOVA p‑value < 0.05 before applying Holm-Bonferroni; write result to `data/processed/primary_test_verification.txt`. **Dependencies**: T023a, T024. **Note**: This task logs the verification result but does NOT block the execution of the correction logic in T024. The correction is applied regardless; the report generation (T025d) will conditionally cite significance.
- [X] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py` to compute observed effect size (eta‑squared), statistical power (α=0.05), and required N using `scipy.stats`. **Output**: `data/processed/power_flags.json` containing `power`, `required_N`, `effect_size`, and `flag`. **Constraint**: Must verify that `power_report.md` explicitly flags if N < 30 and logs a critical failure or halts the pipeline as per Constitution Principle VI. **Dependencies**: T023a. **Verification**: Assert file exists and contains keys: `power`, `required_N`, `effect_size`, `flag`.
- [X] T036b [P] Generate `data/processed/power_report.md` that includes the numeric power value, effect size, required N, and constitutional threshold note (N ≥ 30). **Dependencies**: T036, T006-pre (for pre-study comparison).
- [X] T105 [P] **Integrate Power Results into Main Report** – Extend `run_analysis.py` to embed power value and required N from `power_report.md` into `report_summary.txt`. **Dependencies**: T036b.
- [X] T025c-orch [P] Orchestrate statistical engine in `run_analysis.py`: call `shapiro_wilk()`, `anova_rm()`, `holm_bonferroni()`, `descriptive_stats()`, and now also embed power results. **Dependencies**: T022, T023a, T024, T023b, T105, T108, T024a (Non-blocking).
- [X] T025c-log [P] Add robust error handling and logging to `run_analysis.py`. **Dependencies**: T025c-orch.
- [X] T025d [P] Write final report (`metrics_summary.csv`, `report_summary.txt`) with citations to Constitution Principle VII and amended Spec FR‑002. **Template**: Section 1: Methodology (cite FR-005 imputation), Section 2: Results (ANOVA stats), Section 3: Power Analysis (cite N>=30). **Dependencies**: T025c-log, T113. **Verification**: Assert `report_summary.txt` contains exact strings: "Constitution Principle VII" and "FR-002".
- [X] T118 [P] Verify that ANOVA execution does **not** depend on Shapiro‑Wilk p‑value. Implement a unit test asserting `anova_rm` runs even when normality test fails. **Dependencies**: T023a, T022.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

- [X] T027a [P] Implement box‑plot visualization for Completion Time in `code/analysis/visualizer.py`; output `figures/completion_time.png`. **Spec**: Box-plot with median line, quartiles, outlier points. X-axis: `interface_type`, Y-axis: `completion_time`. Colors: #f77b4 (Traditional), #ff7f0e (Explainable). **Dependencies**: T023a. **Verification**: Assert file exists, size > 0, and valid PNG header.
- [X] T027b [P] Implement box‑plot visualization for Error Count; output `figures/error_count.png`. **Spec**: Box-plot with median line, quartiles, outlier points. X-axis: `interface_type`, Y-axis: `error_count`. Colors: #1f77b4, #ff7f0e. **Dependencies**: T023a. **Verification**: Assert file exists, size > 0, and valid PNG header.
- [X] T027c [P] Implement box‑plot visualization for SUS; output `figures/sus_score.png`. **Spec**: Box-plot with median line, quartiles, outlier points. X-axis: `interface_type`, Y-axis: `sus_score`. Colors: #1f77b4, #ff7f0e. **Dependencies**: T023a. **Verification**: Assert file exists, size > 0, and valid PNG header.
- [X] T027d [P] Verify all visualization files exist and are non‑empty via `tests/unit/test_visualizations.py`. **Dependencies**: T027a‑c.
- [X] T028-skel [P] Create notebook skeleton `code/analysis/analysis.ipynb` with **exact** cells: 1) Imports, 2) Load Data, 3) Data Cleaning, 4) Shapiro‑Wilk audit, 5) Repeated Measures ANOVA, 6) Holm‑Bonferroni, 7) Power Analysis, 8) Visualizations, 9) Summary. **Dependencies**: None.
- [X] T028-load [P] Implement data loading/cleaning cells. **Dependencies**: T028-skel, T021c-cli.
- [X] T028-stat [P] Implement statistical analysis cells. **Dependencies**: T028-load, T023a.
- [X] T028-viz [P] Implement visualization cells. **Dependencies**: T028-stat, T027a‑c.
- [X] T028-power [P] Implement power analysis cells. **Dependencies**: T028-viz, T036.
- [X] T028-doc [P] Finalize notebook with documentation and artifact saving. **Dependencies**: T028-power.
- [X] T030 Ensure notebook determinism: pin seeds, verify figure checksums. **Dependencies**: T028-doc.
- [X] T029b [P] Create a unified `Makefile` with targets `simulate`, `clean`, `analyze`, `report`, `all`. **Dependencies**: All pipeline stages.

---

## Phase 7: Spec-Plan Alignment Verification (Priority: P0)

- [X] T035 [US2] Update `code/analysis/stat_utils.py` to explicitly document the ratified Spec amendment.
- [X] T035c [US2] Write `methodology_notes.txt` in `data/processed/` listing statistical tests used and citing the amended Spec section (FR‑002).
- [X] T035d [US2] Remove any Levene’s test logic from `code/analysis/stat_utils.py`.

---

## Phase 8: Accessibility Compliance & Human Participant Validation (Priority: P1)

- [X] T037 Implement automated accessibility audit script using `axe-core` in `tests/contract/test_accessibility_audit.py`. Output `tests/contract/accessibility_report.json`. **Dependencies**: T012f-int.
- [X] T038 Refine accessibility accommodations in `code/simulator/accessibility.py` based on audit results.
- [X] T039 Create manual "Human Participant Flow" verification script `tests/manual/test_human_flow.py`.
- [X] T040 Add pre‑commit check to enforce accessibility testing.
- [X] T041 Add accessibility metrics to the final report.
- [X] T095-exec [US2] **Execute recruitment plan** (docs/recruitment_execution_log.md) and enforce N ≥ 30; halt pipeline if not met. **Deliverable**: `docs/recruitment_execution_log.md` with participant count >= 30. **Verification**: Pipeline halts with error if count < 30. **Dependencies**: T042.

---

## Phase 9: Final Integration & Execution Readiness (Priority: P0)

- [X] T099 [DEV MODE ONLY] **Full Pipeline Integration Test (Dev)** – Run the pipeline using synthetic data via `--dev-mode`. This validates the CI path only; it does **not** verify production behavior. **Deliverable**: Successful execution of `make all` in CI with synthetic data. **Dependencies**: T031-cli, T021c-cli, T025c-orch, T119-exec. **Note**: T119-exec ensures the production gate logic exists for the test to mock/skip.
- [X] T116 [P] **Production Gate Verification** – Unit test `tests/unit/test_production_gate.py` that creates an empty `data/raw/` directory (or only simulated files) and asserts that invoking the pipeline (via `code/analysis/run_analysis.py`) raises the RuntimeError defined in T097. **Dependencies**: T097, T119-exec.

---

## Phase 10: Reproducibility CI Gate (Priority: P0)

- [X] T096 [P] Create `.github/workflows/reproducibility_check.yml` to run `make all` on a fresh runner, verify artifacts, and compare checksums against `state/...yaml`.

---

## Phase 11: Data Integrity & Execution Readiness (Priority: P0)

- [X] T097 [P] **Production Gate Enforcement** – Implement pre‑flight check in `code/analysis/clean_data.py` that raises RuntimeError if `data/raw/` is empty or contains only simulated files (metadata source = "simulated"). **Dependencies**: T019b, T025a.
- [X] T098 [P] Implement `verify_execution_readiness()` in `code/analysis/run_analysis.py` checking required files, non‑empty raw data (or `--dev-mode` flag), importability of modules, Makefile presence, and dependency installation. Returns bool + error list. **Dependencies**: T097, T029b.
- [X] T102 [P] Integrate `verify_execution_readiness()` and T097 checks into the entry point (`main.py` or `run_analysis.py`) as the first step. **Dependencies**: T097, T098.
- [X] T119-exec [P] **Raw Data Check Implementation** – Implement the logic to raise a descriptive error if `cleaned_sessions.csv` is requested without verified raw input. This task moves the validation logic from the initial draft to this Phase 11 location to ensure linear execution flow. **Dependencies**: T097. **Verification**: Unit test asserts pipeline raises RuntimeError when `data/raw/` is empty or contains only simulated files.

---

## Phase 12: Final Review & Analysis Resolution (Priority: P0)

- [X] T106 [US2] **ANOVA Implementation Review** – Update `code/analysis/stat_utils.py` with explicit comments citing FR‑002 and the ratified amendment, confirming correct `scipy.stats` usage. **Verification**: Code contains the required comment block.
- [X] T107 [US2] **Holm‑Bonferroni Verification** – Add unit test `tests/unit/test_holm_bonferroni.py` confirming correct correction on known p‑values.
- [X] T109 [US2] **Power Analysis Threshold Clarification** – Update `power_analysis.py` to log both the constitutional N ≥ 30 threshold and the computed required N; adjust `power_report.md` accordingly.
- [X] T110 [US0] **Accessibility Metrics Logging** – Extend `session_logger.py` to capture an `accommodations_used` array reflecting which UI accommodations were actually enabled during a session.
- [X] T111 [US1] **Dropout Handling Verification** – Add test ensuring sessions marked `status='incomplete'` are excluded before any imputation or statistical calculation.
- [X] T112 [US2] **Audit Log Completeness** – Enhance `cleaning_log.txt` and `normality_log.txt` to include participant IDs and metric‑level details for every exclusion, imputation, or audit decision.
- [X] T123 [US2] **Document Power Analysis Sample Size Limitations** – Update `power_report.md` generation logic to explicitly state if the observed sample size (N) is below the constitutional threshold (N=30) and explain the implications for statistical power. **Dependencies**: T036, T095-exec. **Verification**: Assert `power_report.md` contains string "N=30" and "statistical power".

---

## Phase 13: Deprecation & Cleanup (Priority: P0)

**Goal**: Remove deprecated tasks and ensure final state consistency.

- [X] T124 [P] **Cleanup Phase 13**: Verify that no deprecated tasks (e.g., T033) remain in the active task list. Verify that `tasks.md` index is updated. **Dependencies**: T119-exec, T120, T121, T122, T123. **Verification**: Assert `grep -r "T033" tasks.md` returns no results (or only in archived section).

---

## Phase 14: Post-Analysis Revision & Gap Resolution (Priority: P0)

**Goal**: Address specific gaps identified by `/speckit.analyze` regarding data provenance, statistical robustness, and accessibility reporting.

### Data Provenance & Real Data Enforcement
- [ ] T125 [US2] **Enhance Data Loader Provenance**: (MOVED TO T120/T021a) This task logic has been integrated into T120 (Phase 2) and T021a (Phase 5) to ensure early failure. No new code changes required. **Rationale**: Ensures the "fail loudly" requirement is enforced at the data ingestion point. **Dependencies**: T120, T021a.
- [ ] T126 [US2] **Add Real Data Verification Test**: (MOVED TO T121) This test logic has been integrated into T121 (Phase 2). No new code changes required. **Dependencies**: T121.

### Statistical Robustness & Reporting
- [ ] T129 [US0] **Generate Accessibility Summary Report**: Create `code/simulator/accessibility_reporter.py` to aggregate `accommodations_used` (from T110) across all sessions and output `data/processed/accessibility_usage_summary.csv`. **Rationale**: Provides quantitative evidence of which accessibility features were actually utilized by participants with disabilities. **Dependencies**: T110, T037.
- [ ] T130 [US0] **Integrate Accessibility Metrics into Final Report**: Update `code/analysis/run_analysis.py` to append a section on "Accessibility Feature Utilization" to `report_summary.txt`, citing the summary from T129. **Rationale**: Completes the research loop by linking the accessibility interface design to actual usage data. **Dependencies**: T129, T025d.

### Execution Readiness & Documentation
- [ ] T131 [P] **Update Quickstart with Data Collection Steps**: Modify `specs/PROJ-015/quickstart.md` to explicitly document the "Real Data Collection" workflow, emphasizing that `--dev-mode` is for testing only and that `N=30` recruitment is required for final claims. **Rationale**: Prevents accidental submission of synthetic data by clarifying the production path. **Dependencies**: T042, T095-exec.
- [ ] T132 [P] **Add Pre-Run Checklist Script**: Create `code/analysis/pre_run_check.py` that verifies the presence of `data/raw/`, non-simulated sources, and `N>=30` count before allowing the analysis pipeline to start. **Rationale**: Adds an extra layer of safety against accidental execution on invalid data. **Dependencies**: T097, T120.