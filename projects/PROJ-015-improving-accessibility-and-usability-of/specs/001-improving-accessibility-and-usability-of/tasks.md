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
- [X] T015 [P] Implement Latin Square counterbalancing in `code/simulator/counterbalance.py` to assign the order of interface presentation (Traditional→Explainable or Explainable→Traditional). **Dependencies**: None. **Note**: This satisfies FR‑004 and must be completed before any UI tasks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Active Tasks (Foundational)
- [X] T012a [P] Create `CONTRIBUTING.md` with the mandatory "no synthetic data" clause and schema compliance guidelines. **Deliverable**: `CONTRIBUTING.md`. **Content**: *(see original description)*.
- [X] T019b [P] Create `contracts/session.schema.yaml`. **Deliverable**: `contracts/session.schema.yaml` defining the JSON schema for session data (participant_id, interface_type, metrics, status, etc.). **Dependencies**: None.
- [X] T019c [P] Implement runtime schema validation logic in `code/simulator/validator.py`. **Deliverable**: `code/simulator/validator.py` with a function `validate_session(data: dict) -> bool`. **Dependencies**: T019b.
- [ ] T031-gen [P] Implement `generate_sessions(n, seed)` in `code/simulator/simulator.py`. **Output Artifact**: `data/raw/simulated_sessions.json`. **Logic**: Synthetic sessions as previously described; includes `metadata: { source: "simulated" }`. **Dependencies**: T019b.
- [ ] T031-cli [P] Implement CLI wrapper for `DeterministicDataSimulator` in `code/simulator/simulator.py`. **Deliverable**: CLI command `python -m code.simulator.simulator --n <N> --seed 42 --output data/raw/simulated_sessions.json`. **Dependencies**: T031-gen.
- [X] T031b [P] Add JSON‑Schema validation to the simulator output. **Dependencies**: T031-cli, T019b.
- [X] T031c [P] Extend simulator to generate dropout sessions via `--dropout-rate`. **Dependencies**: T031-cli.
- [X] T032 [P] Create unit tests for simulator (completion time diff, engagement time positivity, schema compliance). **Dependencies**: T031-gen, T031b.
- [X] T033 [DEPRECATED] **DEV MODE ONLY**: Previously added `--simulate` handling in `run_analysis.py`. Superseded by T097. **Status**: Deprecated.
- [X] T117 [P] **Raw Data Checksumming** – Compute SHA‑256 checksums for every file under `data/raw/` **and** for all schema files in `contracts/` during the cleaning phase. Record each checksum in `state/projects/PROJ-015-improving-accessibility-and-usability-of.yaml` under `artifact_hashes`. **Dependencies**: Runs after raw data is materialized (i.e., after T031-gen or real data collection). Should be invoked before T021a.
- [X] T035a-apply [Foundational] **SPEC AMENDMENT (Apply)**: Verify `spec.md` FR‑002 contains the ratified amendment text for Repeated Measures ANOVA. **Deliverable**: Verified `spec.md`. **Dependencies**: None.

---

## Phase 3: User Story 0 - XAI Interface Configuration (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to evaluate the usability of computer systems for people with disabilities, specifically focusing on gene regulation interfaces.

### Implementation for User Story 0
- [X] T010 [P] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py`
- [X] T011 [P] Implement `ExplainableInterface` renderer in `code/simulator/interfaces/explainable.py`
- [X] T012c Create the skeleton Streamlit app entry point `code/simulator/app.py`. **Deliverable**: `code/simulator/app.py`. **Verification**: Runs without import errors. **Dependencies**: None.
- [X] T013a Define the overlay data schema in `code/simulator/schemas/overlay_schema.yaml`. **Deliverable**: Schema file.
- [X] T013b Implement `RuleBasedXAIOverlayGenerator` in `code/simulator/xai_overlay.py`. **Dependencies**: T013a.
- [X] T012d1 [US0] Implement UI renderer integration in `code/simulator/app.py`. **Scope**: Implement function `render_interface(interface_type: str, task_input: dict) -> dict` returning a dict with keys `html_content` (string) and `accessibility_settings` (dict). **Dependencies**: T010, T011, T012c.
- [X] T012d2 [US0] Implement input capture module in `code/simulator/input.py`. **Scope**: Implement function `capture_input() -> dict` returning `consent_status`, `participant_id`, and `input_events`. **Dependencies**: T012c.
- [X] T012d3 [US0] Implement SUS form logic in `code/simulator/input.py`. **Scope**: Implement function `calculate_sus_score(responses: list) -> dict`. **Dependencies**: T012d2.
- [X] T012d4-init [US0] Initialize state management keys in `code/simulator/state.py`. **Scope**: Implement `init_state()` initializing `st.session_state` keys `current_sequence`, `current_phase`, `interface_variant`. **Dependencies**: T012d2.
- [X] T012d4-inc [US0] Implement phase increment logic in `code/simulator/state.py`. **Scope**: Implement `increment_phase()`. **Dependencies**: T012d4-init.
- [X] T012d4-swtch [US0] Implement sequence switching logic in `code/simulator/state.py`. **Scope**: Implement `switch_sequence()` toggling `interface_variant` based on `current_sequence` and `current_phase`. **Dependencies**: T012d4-inc, T015.
- [X] T012e [US0] Integrate XAI Overlay and Counterbalancing into the Streamlit flow. **Dependencies**: T013b, T015, T012d1, T012d2, T012d3, T012d4-init, T012d4-inc, T012d4-swtch.
- [X] T012g [US0] Implement Accessibility Accommodations in `code/simulator/accessibility.py`. **Scope**: Provide UI components: `font_size_slider` (st.slider), `high_contrast_toggle` (st.checkbox), `keyboard_nav_checkbox` (st.checkbox). Update `st.session_state['font_size']`, `['high_contrast']`, `['keyboard_nav']`. **Dependencies**: T012d4-swtch.
- [X] T012h [US0] Implement Disability Type Selection in `code/simulator/accessibility.py`. **Scope**: Render selector and store choice in session JSON under `disability_type`. **Dependencies**: T012g.
- [X] T012f-main [US0] Implement Human Interaction Loop Orchestration in `code/simulator/orchestrator.py`. **Scope**: `run_human_loop()` calls `render_accessibility_settings()`, `capture_input()`, `calculate_sus_score()`, `manage_state()`. **Dependencies**: T012d2, T012d3, T012d4-init, T012d4-inc, T012d4-swtch, T012g, T012h.
- [X] T012f-int [US0] Wire `run_human_loop()` into `code/simulator/app.py`. **Dependencies**: T012f-main.
- [X] T012i [US0] Implement Gene Regulation Task Logic in `code/simulator/tasks/gene_task.py`. **Scope**: Functions `render_task()`, `validate_task_completion()`, `calculate_task_metrics()`. **Dependencies**: T012d1.
- [X] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`.
- [X] T048 [US0] Refactor `code/simulator/state.py` to ensure `manage_state()` is fully functional and exposes `current_sequence` and `interface_variant` **after** T012e integration. **Dependencies**: T012e.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

- [X] T016 [P] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [X] T016b [P] Ensure `explanation_engagement_time_seconds` is logged to raw session files under `data/raw/`. **Dependencies**: T019, T019c.
- [X] T049 [US1] Ensure `metrics_collector.calculate_task_metrics()` is called within `run_human_loop()` after task completion and before session logging. **Dependencies**: T012f-main, T016.
- [X] T017 [P] Integrate collectors, counterbalancing, and SUS questionnaire into the Streamlit flow, with SUS imputation rules (≤1 missing → impute with participant mean). **Dependencies**: T012f-int, T012g, T012h, T049.
- [X] T020 [P] Implement dropout handling: log `dropout_reason` and set `status='incomplete'` in `code/simulator/session_logger.py`.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

- [X] T025a [P] Create skeleton `code/analysis/run_analysis.py` with CLI (`--input`, `--output`). **Dependencies**: T035a-apply.
- [X] T021a [P] Implement data cleaning filter in `code/analysis/data_cleaner.py`: remove sessions where `status='incomplete'`. **Dependencies**: T019b, T117 (raw checksums run before cleaning).
- [X] T021b [P] Implement SUS imputation in `code/analysis/data_cleaner.py`: if ≤1 SUS item missing, replace with participant mean; otherwise, mark as incomplete (handled by T021a). **Dependencies**: T021a.
- [ ] T021c-cli [P] Implement CLI wrapper `code/analysis/clean_data.py` calling T021a → T021b → export `data/processed/cleaned_sessions.csv`. **Dependencies**: T021a, T021b.
- [X] T021c-hash [P] Extend checksum logic to also record hashes for all raw session files (via T117) and for `contracts/session.schema.yaml`. Update `state/...yaml` accordingly. **Dependencies**: T021c-cli.
- [X] T021c-log [P] Log cleaning actions, imputations, and exclusions to `data/processed/cleaning_log.txt`. **Dependencies**: T021c-cli.
- [X] T021d [P] Unit test verifying SUS imputation correctness. **Dependencies**: T021b.
- [X] T021e [P] Unit test verifying dropout reason presence for incomplete sessions. **Dependencies**: T020.
- [X] T050 [US2] Add validation for `explanation_engagement_time` consistency (missing/zero for Traditional, present for Explainable). **Dependencies**: T021a, T016b.
- [X] T022 [P] Implement Shapiro‑Wilk normality test on difference scores in `code/analysis/stat_utils.py`; log to `data/processed/normality_log.txt`. **Dependencies**: T035a-apply.
- [ ] T023a [US2] Implement Repeated Measures ANOVA using `statsmodels.stats.anova.AnovaRM`. **Constraint**: Explicitly ignore Shapiro‑Wilk results (audit‑only). **Output**: `data/processed/metrics_summary.csv`. **Dependencies**: T035a-apply. <!-- FAILED: unspecified -->
- [X] T023b [P] Compute descriptive stats for `explanation_engagement_time` and output to `data/processed/descriptive_stats_explanation_engagement.csv`. Update `report_summary.txt`. **Dependencies**: T023a.
- [X] T024 [P] Implement Holm‑Bonferroni correction for the three metric ANOVAs. **Dependencies**: T023a.
- [X] T024a [P] Verify primary ANOVA p‑value < 0.05 before applying Holm‑Bonferroni; write result to `data/processed/primary_test_verification.txt`. **Dependencies**: T023a, T024.
- [ ] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py` to compute observed effect size (eta‑squared), statistical power (α=0.05), and required N. **Output**: `data/processed/power_flags.json` containing `power`, `required_N`, `effect_size`, and `flag`. **Dependencies**: T023a.
- [X] T036b [P] Generate `data/processed/power_report.md` that includes the numeric power value, effect size, required N, and constitutional threshold note (N ≥ 30). **Dependencies**: T036.
- [X] T105 [P] **Integrate Power Results into Main Report** – Extend `run_analysis.py` to embed power value and required N from `power_report.md` into `report_summary.txt`. **Dependencies**: T036b.
- [X] T025c-orch [P] Orchestrate statistical engine in `run_analysis.py`: call `shapiro_wilk()`, `anova_rm()`, `holm_bonferroni()`, `descriptive_stats()`, and now also embed power results. **Dependencies**: T022, T023a, T024, T023b, T105.
- [X] T025c-log [P] Add robust error handling and logging to `run_analysis.py`. **Dependencies**: T025c-orch.
- [ ] T025d [P] Write final report (`metrics_summary.csv`, `report_summary.txt`) with citations to Constitution Principle VII and amended Spec FR‑002. **Dependencies**: T025c-log.
- [X] T118 [P] Verify that ANOVA execution does **not** depend on Shapiro‑Wilk p‑value. Implement a unit test asserting `anova_rm` runs even when normality test fails. **Dependencies**: T023a, T022.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

- [ ] T027a [P] Implement box‑plot visualization for Completion Time in `code/analysis/visualizer.py`; output `figures/completion_time.png`. **Dependencies**: T023a.
- [ ] T027b [P] Implement box‑plot visualization for Error Count; output `figures/error_count.png`. **Dependencies**: T023a.
- [ ] T027c [P] Implement box‑plot visualization for SUS; output `figures/sus_score.png`. **Dependencies**: T023a.
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
- [X] T039 Create manual “Human Participant Flow” verification script `tests/manual/test_human_flow.py`.
- [X] T040 Add pre‑commit check to enforce accessibility testing.
- [X] T041 Add accessibility metrics to the final report.
- [X] T095‑exec [US2] Execute recruitment plan (docs/recruitment_execution_log.md) and enforce N ≥ 30; halt pipeline if not met.

---

## Phase 9: Final Integration & Execution Readiness (Priority: P0)

- [X] T099 [DEV MODE ONLY] **Full Pipeline Integration Test (Dev)** – Run the pipeline using synthetic data via `--simulate`. This validates the CI path only; it does **not** verify production behavior. **Deliverable**: Successful execution of `make all` in CI with synthetic data. **Dependencies**: T031-cli, T021c-cli, T025c-orch.
- [X] T116 [P] **Production Gate Verification** – Unit test `tests/unit/test_production_gate.py` that creates an empty `data/raw/` directory (or only simulated files) and asserts that invoking the pipeline (via `code/analysis/run_analysis.py`) raises the RuntimeError defined in T097. **Dependencies**: T097.

---

## Phase 10: Reproducibility CI Gate (Priority: P0)

- [X] T096 [P] Create `.github/workflows/reproducibility_check.yml` to run `make all` on a fresh runner, verify artifacts, and compare checksums against `state/...yaml`.

---

## Phase 11: Data Integrity & Execution Readiness (Priority: P0)

- [X] T097 [P] **Production Gate Enforcement** – Implement pre‑flight check in `code/analysis/clean_data.py` that raises RuntimeError if `data/raw/` is empty or contains only simulated files (metadata source = "simulated"). **Dependencies**: T019b, T025a.
- [X] T098 [P] Implement `verify_execution_readiness()` in `code/analysis/run_analysis.py` checking required files, non‑empty raw data (or `--simulate` flag), importability of modules, Makefile presence, and dependency installation. Returns bool + error list. **Dependencies**: T097, T029b.
- [X] T102 [P] Integrate `verify_execution_readiness()` and T097 checks into the entry point (`main.py` or `run_analysis.py`) as the first step. **Dependencies**: T097, T098.

---

## Phase 12: Final Review & Analysis Resolution (Priority: P0)

- [X] T106 [US2] **ANOVA Implementation Review** – Update `code/analysis/stat_utils.py` with explicit comments citing FR‑002 and the ratified amendment, confirming correct `AnovaRM` usage. **Verification**: Code contains the required comment block.
- [X] T107 [US2] **Holm‑Bonferroni Verification** – Add unit test `tests/unit/test_holm_bonferroni.py` confirming correct correction on known p‑values.
- [ ] T108 [US2] **Pipeline Order Enforcement** – Add `precondition_check()` in `run_analysis.py` that raises an error if `cleaned_sessions.csv` is missing before proceeding to normality, ANOVA, correction, and power steps.
- [X] T109 [US2] **Power Analysis Threshold Clarification** – Update `power_analysis.py` to log both the constitutional N ≥ 30 threshold and the computed required N; adjust `power_report.md` accordingly.
- [X] T110 [US0] **Accessibility Metrics Logging** – Extend `session_logger.py` to capture an `accommodations_used` array reflecting which UI accommodations were actually enabled during a session.
- [X] T111 [US1] **Dropout Handling Verification** – Add test ensuring sessions marked `status='incomplete'` are excluded before any imputation or statistical calculation.
- [X] T112 [US2] **Audit Log Completeness** – Enhance `cleaning_log.txt` and `normality_log.txt` to include participant IDs and metric‑level details for every exclusion, imputation, or audit decision.
- [ ] T113 [US2] **Report Consistency Check** – Add checksum verification in `run_analysis.py` that compares `report_summary.txt` content against source CSVs (`metrics_summary.csv`, `descriptive_stats_explanation_engagement.csv`). Fail if mismatched.
- [X] T114 [US0] **Simulator Realism Documentation** – Update `docs/task_design.md` describing gene regulation task difficulty parameters and expected variance to avoid floor/ceiling effects.
- [X] T115 [US2] **Robust Error Handling in Analysis** – Wrap statistical calls in try/except blocks; log errors to `data/processed/error_log.txt` and flag affected results as invalid without crashing the pipeline.
