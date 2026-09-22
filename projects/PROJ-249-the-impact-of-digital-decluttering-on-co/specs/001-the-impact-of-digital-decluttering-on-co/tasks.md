# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well-being

**Input**: Design documents from `/specs/001-digital-decluttering-study/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

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

- [ ] T001.1 [P] Create project directory structure: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/`, `data/raw/`, `data/processed/`, `data/compliance/`, `code/`, `tests/`, `results/`
- [ ] T001.2 [P] Create `requirements.txt` with pinned dependencies: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw/`, `data/processed/`, `data/compliance/`
- [X] T005 [P] Create `code/__init__.py` and module scaffolding for `scoring/`, `analysis/`, `validation/`, `viz/`
- [X] T006 [US1] Implement pseudonymous ID generator in `code/scoring/id_generator.py` adhering to `P\d{3}` pattern (FR-001); MUST generate IDs from a recruitment CSV or synthetic source to ensure deterministic linking of baseline/post data; output format MUST strictly match the `P\d{3}` regex pattern required by FR-001 and data-model.md.
- [ ] T006.1 [US1] Implement 'register_participant' function in `code/pipeline/register_participant.py` (FR-001); MUST assign IDs from T006 to participants upon entry and link them to data records; output MUST be stored in `data/raw/participant_registry.csv`. **Depends on T006**.
- [X] T007 Create base data schema definitions in `contracts/dataset.schema.yaml` matching `Participant`, `MeasurementRecord`, `ComplianceLog` entities
- [X] T008 Configure random seed management utility in `code/utils/random_seed.py` for reproducibility
- [X] T009 [US1] Create synthetic data generator for baseline validation in `code/validation/synthetic_baseline.py` (FR-009, US-1); MUST output to `data/raw/synthetic_baseline.csv` with columns (`participant_id`, `metric_type`, `value`, `timestamp`) and defined distributions (e.g., SART errors follow a normal distribution with a moderate variance, PSS ~ N(μ, σ), where μ represents the expected mean PSS score and σ represents the standard deviation, reflecting the anticipated distribution of perceived stress levels in the target population without specifying exact magnitudes at this planning stage.).
- [ ] T010 [US3] Implement Monte Carlo Power Simulation in `code/analysis/power_simulation.py` (FR-006, US-1); MUST use synthetic data from T009, run a sufficient number of iterations, apply Holm-Bonferroni correction (from T035), estimate power for d=0.5; output to `results/power_analysis.json`; MUST explicitly write the JSON file with keys [power_estimate (float, specified precision), iterations (int), effect_size (float, specified precision)] and verify its existence; **Depends on T035 (Phase 5) and T009 (Phase 2)**. NOTE: This is a statistical validation step.
- [ ] T011.1 [P] Create static web interface bundle generator in `code/web/static_bundle.py` (FR-002); MUST fetch JS from T011.2, minify, and inline into a self-contained HTML file using a simple string concatenation or base64 encoding for assets; output to `data/web/bundle.html`; this artifact satisfies the 'web interface' requirement without needing a live server.
- [ ] T011.2 [P] Download and verify OSF task code (v2.1+) in `code/web/download_osf.py` (FR-002); MUST fetch the specific version from the OSF repository, verify the checksum, and prepare it for bundling in T011.1.
- [ ] T011.3 [P] Implement Local Server Launcher in `code/web/local_server.py` (FR-002); MUST serve the static bundle from T011.1 on `localhost:8080` for the pilot check; MUST handle graceful shutdown and return the URL for T019.1.
- [ ] T011.4 [P] Host Pilot Web Interface; MUST launch the local server from T011.3 and make the web interface accessible for the pilot study. **Depends on T011.3.**
- [ ] T012 [P] Create recruitment protocol definition in `code/pipeline/recruitment_protocol.py` (FR-009); MUST generate `docs/recruitment_protocol.md` with sections: 1. Eligibility Criteria, 2. Compensation, 3. Consent Text, 4. Pilot Instructions; output to `docs/recruitment_protocol.md`.
- [ ] T012.1 [P] Implement recruitment script template generator in `code/pipeline/generate_recruitment_script.py` (FR-009); MUST generate `docs/recruitment_script_template.md` with fields: Prolific ID, Screening Questions, Consent Form, Pilot Instructions; output to `docs/recruitment_script_template.md`.
- [ ] T012.1 [P] Implement recruitment script template generator in `code/pipeline/generate_recruitment_script.py` (FR-009); MUST generate `docs/recruitment_script_template.md` with fields: Prolific ID, Screening Questions, Consent Form, Pilot Instructions; output to `docs/recruitment_script_template.md`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Data Collection (Priority: P1) 🎯 MVP

**Goal**: Recruit participants (simulated), collect baseline cognitive and emotional metrics, and validate instrument logic.

**Independent Test**: Run the baseline script for a single participant; verify SART, Ospan, PSS-10, and PANAS scores are recorded in `data/raw/` with valid ranges.

### Implementation for User Story 1

- [X] T013 [US1] Create synthetic data generator for baseline validation in `code/validation/synthetic_baseline.py` (FR-009, US-1); MUST output to `data/raw/synthetic_baseline.csv` with columns (`participant_id`, `metric_type`, `value`, `timestamp`) and defined distributions (e.g., SART errors follow a normal distribution with a moderate variance, PSS ~ N(μ, σ), where μ represents the expected mean PSS score and σ represents the standard deviation, reflecting the anticipated distribution of perceived stress levels in the target population without specifying exact magnitudes at this planning stage.).
- [X] T014 [US1] Implement SART scoring function in `code/scoring/sart.py` (response times ranging from tens of milliseconds to several seconds, commission errors); MUST accept input schema `{'response_time': float, 'accuracy': bool, 'stimulus_type': str}` and output `{'commission_errors': int, 'omission_errors': int, 'mean_rt': float}`.
- [X] T015 [US1] Implement Ospan scoring function in `code/scoring/ospan.py` (span scores); MUST accept input schema `{'stimulus': str, 'recall': str, 'accuracy': bool}` and output `{'span_score': int, 'total_correct': int}`.
- [X] T016 [US1] Implement PSS-10 and PANAS scoring functions in `code/scoring/questionnaires.py`
- [X] T014.1 [US1] Implement local web interface wrapper in `code/web/task_interface.py` that loads the static bundle from T011.1 and simulates user interaction for CI; MUST provide a browser-based interaction loop to collect raw data (JSON) and link it to participant IDs (FR-002); INPUT: `data/fixtures/pilot_input.json` (schema: {participant_id, task_type, stimulus_sequence}); OUTPUT: `data/raw/pilot_raw.json` (schema: {participant_id, task_type, response_time_ms, accuracy, timestamp}); MUST validate that the local loop correctly captures response times and accuracy before data is passed to scoring functions. **Depends on T011.1 and T011.3**.
- [X] T017 [US1] Unit test for SART scoring logic against OSF reference (v+) in `tests/unit/test_sart_scoring.py` (runs against data from T013; MUST execute once T014 is complete) **Depends on T014**.
- [X] T018 [US1] Unit test for Ospan scoring logic against OSF reference (v+) in `tests/unit/test_ospan_scoring.py` (runs against data from T013; MUST execute once T015 is complete) **Depends on T015**.
- [X] T019 [US1] Unit test for PSS-10 and PANAS scoring in `tests/unit/test_questionnaire_scoring.py` (runs against data from T013; MUST execute once T016 is complete) **Depends on T016**.
- [X] T020 [P] [US1] Contract test for data schema validation in `tests/contract/test_baseline_schema.py`
- [X] T021 [US1] Implement instrument logic validation script to run synthetic data through scorers and check ranges in `code/validation/validate_instruments.py`
- [X] T019.1 [US1] Implement pre-study pilot check (n=5) in `code/pipeline/run_pilot.py`; MUST execute the recruitment protocol from T012 (specifically the 'execute pilot simulation' step) and T012.1 locally, launch the local server from T011.3, and simulate user interaction via the web interface (T014.1) to generate `data/raw/pilot_raw.json`; MUST validate that SART commission errors are > 0 and < 100, Mean RT within a lower-bound-defined window up to 3000ms, and PSS between 0 and 40; **Depends on T012, T012.1, T014.1, and T011.3**. NOTE: This is a faithful proxy execution on synthetic inputs to validate logic without human recruitment, satisfying FR-009's requirement for a functional pilot check.
- [X] T022 [US1] Create baseline data collection pipeline script in `code/pipeline/collect_baseline.py`; MUST orchestrate T013 (synthetic) and T019.1 (pilot) data ingestion, ensuring strict adherence to `contracts/dataset.schema.yaml` and applying the pseudonymous ID mapping from T006.1; output MUST be stored in `data/raw/baseline_raw.csv` with a checksum manifest.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intervention Compliance Logging (Priority: P2)

**Goal**: Process daily logs, validate compliance rules, and calculate compliance scores.

**Independent Test**: Simulate a participant submitting multiple daily logs; verify compliance score calculation and deviation flagging.

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Contract test for compliance log schema in `tests/contract/test_compliance_schema.py`
- [X] T024 [P] [US2] Unit test for plausibility validation (0 ≤ minutes ≤ 1440) in `tests/unit/test_compliance_validation.py`
- [X] T025 [P] [US2] Unit test for compliance rule logic (≤30 min social media, no news) in `tests/unit/test_compliance_rules.py`

### Implementation for User Story 2

- [X] T026 [US2] Implement daily log parser in `code/compliance/parse_logs.py`
- [X] T027 [US2] Implement plausibility validation logic (FR-010) in `code/validation/compliance_plausibility.py`
- [X] T028 [US2] Implement compliance rule engine (≤30 min social media, no news, notifications off) in `code/compliance/rules_engine.py`
- [X] T029 [US2] Create compliance aggregation script to calculate daily/weekly scores in `code/pipeline/aggregate_compliance.py`
- [X] T030 [US2] Implement logic to flag non-compliant days but retain data for analysis (US-2); MUST mark entries in `data/compliance/flags.json` without dropping rows, ensuring T034 can process partial data for participants with mixed compliance.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Post-Intervention Analysis & Reporting (Priority: P3)

**Goal**: Compute change scores, perform robust statistical testing (bootstrapping), apply corrections, and generate reports.

**Independent Test**: Feed a synthetic dataset with known pre/post differences; verify output report correctly identifies significance, effect size, and generates plots.

### Implementation for User Story 3

- [X] T031 [US3] Implement data merger to join baseline and post-intervention records in `code/pipeline/merge_data.py`
- [X] T032 [US3] Implement change score calculator (post - baseline) in `code/analysis/change_scores.py` (FR-005)
- [X] T033 [US3] Implement bootstrapped CI calculation (a large number of resamples) in `code/analysis/bootstrap_ci.py` (FR-006)
- [X] T034.1 [US3] Implement convergence failure detection logic in `code/analysis/convergence_detector.py`; MUST detect specific failure modes: 'empty resamples' (0 valid samples), 'singular matrix' (variance=0 in 99% of resamples), 'max iteration exceedance' (attempts without stable mean); MUST explicitly return a flag indicating 'convergence_failed' to trigger T034; MUST explicitly forbid Shapiro-Wilk p < 0.05 triggers; NOTE: This is a robust alternative to normality assumptions.
- [X] T034.2 [US3] Implement explicit prohibition of Shapiro-Wilk trigger in `code/analysis/statistical_config.py`; MUST raise an error if any code attempts to use Shapiro-Wilk p-values to trigger Wilcoxon, ensuring FR-006's robust method is used.
- [X] T034 [US3] Implement fallback Wilcoxon signed-rank test logic in `code/analysis/wilcoxon_fallback.py`; MUST trigger ONLY if T034.1 detects convergence failure (FR-006). **Depends on T034.1 and T034.2**.
- [X] T035 [US3] Implement Holm-Bonferroni step-down correction in `code/analysis/holm_bonferroni.py` (FR-008)
- [X] T036 [US3] Implement Cohen's d with confidence interval calculation in `code/analysis/effect_sizes.py` (FR-007)
- [X] T037 [US3] Generate `results/statistical_summary.json` with mean change, CI, and corrected p-values (SC-001 to SC-005)
- [X] T038 [US3] Generate sensitivity analysis report in `results/sensitivity_analysis_report.md`; MUST check for `data/raw/objective_screen_time.json`; IF present, MUST implement the 'compare' clause; IF absent, MUST generate a limitation statement. **Depends on T038.1.**
- [X] T038.1 [US3] Implement objective screen-time data ingestion in `code/compliance/ingest_objective_data.py`; MUST attempt to load `data/raw/objective_screen_time.json` if present, validate schema, and prepare for comparison; IF missing, return empty dataset.
- [X] T039 [US3] Create visualization generator for boxplots and change score distributions in `code/viz/generate_plots.py`
- [X] T040 [US3] Implement final report generator in `code/report/generate_report.py`; MUST include: 1) Full text of sensitivity analysis report (from T038), 2) Power simulation results (from T010), 3) Statistical summary (from T037), 4) Validation status (from T041); Output to `results/final_report.md`.
- [ ] T049 [US3] Implement dropout handling logic in `code/pipeline/handle_dropouts.py`; MUST exclude participants with missing post-intervention data from paired statistical tests (T032-T036) while retaining their baseline data in `data/processed/descriptive_baseline.csv` for descriptive statistics.
- [ ] T050 [US3] Implement attention check validation in `code/validation/attention_check.py`; MUST flag participants with SART accuracy < 50% as 'low_quality' and optionally exclude them from primary analysis.
- [ ] T051 [US3] Implement extreme case logging in `code/compliance/log_extreme_cases.py`; MUST detect participants reporting negligible or zero digital use for all 7 days and include them in the analysis.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044.1 [P] Write README.md with project overview, installation steps, and usage instructions; MUST include a section on 'Data Generation' and 'Analysis Pipeline'.
- [X] T044.1.1 [P] Verify README.md content; MUST check that README.md contains H2 headers: "Installation", "Data Generation", "Analysis Pipeline".
- [X] T044.2 [P] Write `quickstart.md` with step-by-step end-to-end pipeline execution guide.
- [X] T045.1 [P] Refactor `code/scoring/` module to reduce cyclomatic complexity < 10; MUST produce a refactored module with unit tests passing.
- [X] T045.2 [P] Refactor `code/analysis/` module to improve modularity and testability; MUST produce a refactored module with unit tests passing.
- [X] T046 [P] Performance optimization for bootstrap loops (vectorization); MUST reduce runtime by at least 20% without changing results.
- [X] T047 [P] Additional unit tests for edge cases (dropouts, missing data) in `tests/unit/`; MUST cover at least 3 edge cases.
- [X] T048 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility.
