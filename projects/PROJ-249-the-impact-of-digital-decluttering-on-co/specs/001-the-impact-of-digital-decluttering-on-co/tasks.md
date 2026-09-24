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
 - Delivered as a MVP increment

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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data generation, scoring logic, instrument verification, power simulation, compliance logging, and recruitment workflow generation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw/`, `data/processed/`, `data/compliance/`
- [X] T005 [P] Create `code/__init__.py` and module scaffolding for `scoring/`, `analysis/`, `validation/`, `viz/`, `pipeline/`, `report/`
- [X] T006 [US1] Implement pseudonymous ID generator in `code/scoring/id_generator.py` adhering to `P\d{3}` pattern (FR-001); MUST generate IDs from a recruitment CSV or synthetic source to ensure deterministic linking of baseline/post data; output format MUST strictly match the `P\d{3}` regex pattern required by FR-001 and data-model.md.
- [ ] T006.1 [US1] Implement 'register_participant' function in `code/pipeline/register_participant.py` (FR-001); MUST assign IDs from T006 to participants upon entry and link them to data records; **Input Schema**: CSV with columns `['recruitment_id', 'consent_timestamp', 'demographic_hash']`; **Output Schema**: `data/raw/participant_registry.csv` with columns `['participant_id', 'recruitment_id', 'status']`; **Error Handling**: MUST raise `ValueError` if `participant_id` does not match `P\d{3}` or if `recruitment_id` is duplicate; **Depends on T006**.
- [ ] T006.2 [US1] Implement 'Recruitment Interface Stub' generator in `code/pipeline/generate_recruitment_workflow.py` (FR-001); MUST generate `docs/recruitment_workflow.md` detailing the manual/automated steps to link real humans to IDs, ensuring FR-001 is met for the actual study phase; **Input**: Config file; **Output**: `docs/recruitment_workflow.md`; **Depends on T006, T006.1**.
- [X] T006.3 [US1] **Instrument Verification** in `code/validation/verify_osf_instruments.py`; MUST download SART and Ospan task source code (v2.1+) from the OSF repository, compute SHA-256 hash, and compare against the reference hash defined in the plan; MUST fail loudly if hash mismatch; **Output**: `results/instrument_verification.json` with status 'verified' or 'failed'; **Constraint**: MUST run BEFORE any scoring logic is used (T014, T015).
- [X] T007 Create base data schema definitions in `contracts/dataset.schema.yaml` matching `Participant`, `MeasurementRecord`, `ComplianceLog` entities
- [X] T008 Configure random seed management utility in `code/utils/random_seed.py` for reproducibility
- [ ] T008.1 [P] **Reproducibility Manifest Generator** in `code/pipeline/generate_reproducibility_manifest.py`; MUST execute at the end of the pipeline to log the exact random seed used, canonical source URLs, and artifact hashes into `results/reproducibility_manifest.json`; **Output**: `results/reproducibility_manifest.json`; **Depends on T008, T009, T010.1**.
- [X] T009 [US1] Create synthetic data generator for baseline validation in `code/validation/synthetic_baseline.py` (FR-009, US-1); MUST read parameters from `code/config/synthetic_data_config.yaml` (mean, std, distributions) to ensure deterministic execution; output to `data/raw/synthetic_baseline.csv` with columns (`participant_id`, `metric_type`, `value`, `timestamp`); **Output**: `data/raw/synthetic_baseline.csv` with valid ranges for all metrics; **Depends on T006**.
- [ ] T010 [US1] **Monte Carlo Power Simulation** in `code/analysis/power_simulation.py` (FR-006, US-1); MUST use synthetic data from T009, run 1,000 iterations, apply Holm-Bonferroni correction (from T035), estimate power for d=0.5; **Output**: `results/power_analysis.json` with keys `power_estimate` (float), `iterations` (int), `effect_size` (float); **Constraint**: MUST run BEFORE primary analysis tasks; **Depends on T009, T035**.
- [X] T011.1 [P] Implement Headless Task Simulator in `code/web/headless_simulator.py` (FR-002, FR-009); MUST generate synthetic stimulus sequences and simulate user responses (JSON) for SART and Ospan tasks without a browser or server; **Input**: `code/web/task_config.json`; **Output**: `data/raw/pilot_raw.json` containing `response_time_ms`, `accuracy`, `stimulus_type`; **Constraint**: MUST NOT launch any HTTP server; MUST run entirely in memory/CLI.
- [ ] T012 [P] Generate recruitment protocol in `code/pipeline/generate_recruitment_protocol.py` (FR-009); MUST generate `docs/recruitment_protocol.md` with sections: 1. Eligibility Criteria, 2. Compensation, 3. Consent Text, 4. Pilot Instructions; **Input**: Config; **Output**: `docs/recruitment_protocol.md`.
- [ ] T012.1 [P] Generate recruitment script template in `code/pipeline/generate_recruitment_script.py` (FR-009); MUST generate `docs/recruitment_script_template.md` with fields: Prolific ID, Screening Questions, Consent Form, Pilot Instructions; **Input**: Config; **Output**: `docs/recruitment_script_template.md`.
- [X] T014 [US1] Implement SART scoring function in `code/scoring/sart.py` (response times ranging from tens of milliseconds to several seconds, commission errors); MUST accept input schema `{'response_time': float, 'accuracy': bool, 'stimulus_type': str}` and output `{'commission_errors': int, 'omission_errors': int, 'mean_rt': float}`. **Depends on T011.1, T006.3**.
- [X] T015 [US1] Implement Ospan scoring function in `code/scoring/ospan.py` (span scores); MUST accept input schema `{'stimulus': str, 'recall': str, 'accuracy': bool}` and output `{'span_score': int, 'total_correct': int}`. **Depends on T011.1, T006.3**.
- [X] T016 [US1] Implement PSS-10 and PANAS scoring functions in `code/scoring/questionnaires.py`. **Depends on T009**.
- [X] T017 [US1] Unit test for SART scoring logic against OSF reference (v+) in `tests/unit/test_sart_scoring.py` (runs against data from T009; MUST execute once T014 is complete) **Depends on T014**.
- [X] T018 [US1] Unit test for Ospan scoring logic against OSF reference (v+) in `tests/unit/test_ospan_scoring.py` (runs against data from T009; MUST execute once T015 is complete) **Depends on T015**.
- [X] T019 [US1] Unit test for PSS-10 and PANAS scoring in `tests/unit/test_questionnaire_scoring.py` (runs against data from T009; MUST execute once T016 is complete) **Depends on T016**.
- [X] T020 [P] [US1] Contract test for data schema validation in `tests/contract/test_baseline_schema.py`
- [X] T021 [US1] Implement instrument logic validation script to run synthetic data through scorers and check ranges in `code/validation/validate_instruments.py`
- [X] T019.1 [US1] Implement pre-study pilot check (n=5) in `code/pipeline/run_pilot.py`; MUST execute the recruitment protocol from T012 (specifically the 'execute pilot simulation' step) and T012.1 locally, run the Headless Task Simulator from T011.1 to generate `data/raw/pilot_raw.json`; MUST validate that SART commission errors are > 0 and < 100, Mean RT within a lower-bound-defined window up to 3000ms, and PSS between low and high values. The research question is [insert question], the method is [insert method], and the references are [insert references].; **Depends on T012, T012.1, T011.1, T014, T015**. NOTE: This is a faithful proxy execution on synthetic inputs to validate logic without human recruitment, satisfying FR-009's requirement for a functional pilot check.
- [X] T022 [US1] Create baseline data collection pipeline script in `code/pipeline/collect_baseline.py`; MUST orchestrate T009 (synthetic) and T019.1 (pilot) data ingestion, ensuring strict adherence to `contracts/dataset.schema.yaml` and applying the pseudonymous ID mapping from T006.1; output MUST be stored in `data/raw/baseline_raw.csv` with a checksum manifest.
- [X] T026 [US2] Implement daily log parser in `code/compliance/parse_logs.py`
- [X] T027 [US2] Implement plausibility validation logic (FR-010) in `code/validation/compliance_plausibility.py`
- [X] T028 [US2] Implement compliance rule engine (≤30 min social media, no news, notifications off) in `code/compliance/rules_engine.py`
- [X] T029 [US2] Create compliance aggregation script to calculate daily/weekly scores in `code/pipeline/aggregate_compliance.py`
- [X] T030 [US2] Implement logic to flag non-compliant days but retain data for analysis (US-2); MUST mark entries in `data/compliance/flags.json` without dropping rows, ensuring T034 can process partial data for participants with mixed compliance.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Data Collection (Priority: P1) 🎯 MVP

**Goal**: Recruit participants (simulated), collect baseline cognitive and emotional metrics, and validate instrument logic.

**Independent Test**: Run the baseline script for a single participant; verify SART, Ospan, PSS-10, and PANAS scores are recorded in `data/raw/` with valid ranges.

### Implementation for User Story 1

- [X] T031 [US3] Implement data merger to join baseline and post-intervention records in `code/pipeline/merge_data.py`
- [X] T032 [US3] Implement change score calculator (post - baseline) in `code/analysis/change_scores.py` (FR-005)
- [ ] T033.1 [US3] **Execute Primary Bootstrapping Loop** in `code/analysis/run_bootstrap.py`; MUST execute the primary bootstrapping method (a sufficient number of resamples to ensure stability) for all Several metrics (SART, Ospan, PSS, PANAS) using the change scores from T032; **Output**: `data/processed/bootstrap_results.json` containing mean change and 95% CI for each metric; **Constraint**: MUST run BEFORE any fallback logic; MUST NOT check for normality (Shapiro-Wilk) or use it as a trigger; MUST emit a 'convergence_failed' flag to `data/processed/bootstrap_status.json` upon failure; **Depends on T031, T032**.
- [ ] T033.2 [US3] **Bootstrapping Constraint Audit** in `tests/unit/test_no_shapiro_trigger.py`; MUST perform static analysis or unit test asserting the absence of Shapiro-Wilk logic in `code/analysis/run_bootstrap.py`; **Depends on T033.1**.
- [X] T034.1 [US3] Implement convergence failure detection logic in `code/analysis/convergence_detector.py`; MUST detect specific failure modes: 'empty resamples' (0 valid samples), 'singular matrix' (variance=0 in 99% of resamples), 'max iteration exceedance' (attempts without stable mean); MUST explicitly return a flag indicating 'convergence_failed' to trigger T034; **Depends on T033.1**.
- [X] T034 [US3] Implement fallback Wilcoxon signed-rank test logic in `code/analysis/wilcoxon_fallback.py`; MUST trigger ONLY if T034.1 detects convergence failure (FR-006). **Depends on T034.1, T033.2**.
- [X] T035 [US3] Implement Holm-Bonferroni step-down correction in `code/analysis/holm_bonferroni.py` (FR-008)
- [X] T036 [US3] Implement Cohen's d with confidence interval calculation in `code/analysis/effect_sizes.py` (FR-007)
- [X] T037 [US3] Generate `results/statistical_summary.json` with mean change, CI, and corrected p-values (SC-001 to SC-005)
- [ ] T037.1 [US3] **Success Criteria Verdict Generator** in `code/report/generate_success_verdict.py`; MUST read `results/statistical_summary.json`, compare values against SC-001 to SC-005 thresholds (p < 0.05, d ≥ 0.2), and generate `results/success_verdict.json` with a Pass/Fail status for each criterion and an overall study verdict; **Depends on T037**.
- [ ] T038.1 [US3] Implement objective screen-time data ingestion in `code/compliance/ingest_objective_data.py`; MUST attempt to load `data/raw/objective_screen_time.json` if present, validate schema, and prepare for comparison; IF missing, return empty dataset; **Output**: `data/processed/objective_data_status.json`.
- [ ] T038.2 [US3] Generate sensitivity analysis report in `code/report/generate_sensitivity_report.py`; MUST check `data/processed/objective_data_status.json` from T038.1; IF objective data exists, MUST implement the 'compare' clause; IF absent, MUST generate a limitation statement; **Output**: `results/sensitivity_analysis_report.md`; **Depends on T038.1**.
- [X] T039 [US3] Create visualization generator for boxplots and change score distributions in `code/viz/generate_plots.py`
- [ ] T049 [US3] Implement dropout handling logic in `code/pipeline/handle_dropouts.py`; MUST exclude participants with missing post-intervention data from paired statistical tests (T032-T036) while retaining their baseline data in `data/processed/descriptive_baseline.csv` for descriptive statistics; **Input**: `data/processed/merged_data.csv`; **Output**: `data/processed/exclusions.json` listing excluded IDs and reason 'missing_post_data'; **Depends on T031**.
- [ ] T050 [US3] Implement attention check validation in `code/validation/attention_check.py`; MUST flag participants with SART accuracy < 50% as 'low_quality' and EXCLUDE them from primary analysis; **Input**: `data/raw/baseline_raw.csv`; **Output**: `data/processed/exclusions.json` append entries with reason 'low_sart_accuracy'; **Depends on T022**.
- [X] T051 [US3] Implement extreme case logging in `code/compliance/log_extreme_cases.py`; MUST detect participants reporting negligible or zero digital use for all days of the study period and include them in the analysis.
- [ ] T055 [US3] **Enforce Strict Data Flow Dependency** in `code/pipeline/run_analysis.py`; MUST explicitly verify that `data/processed/bootstrap_results.json` (from T033.1) is generated and valid BEFORE attempting to run the Holm-Bonferroni correction (T035) or Effect Size calculation (T036); **Logic**: If `bootstrap_results.json` is missing or empty, raise a `DataFlowError` with message "Primary bootstrapping results missing. Cannot proceed with correction."; **Depends on T033.1**.

**Checkpoint**: All user stories should now be independently functional

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

*Note: Core analysis tasks (T031-T037) are located in Phase 3 (US3) to align with the data flow. This phase focuses on reporting and edge case handling.*

### Implementation for User Story 3 (Reporting & Edge Cases)

- [X] T039 [US3] Create visualization generator for boxplots and change score distributions in `code/viz/generate_plots.py`
- [ ] T040 [US3] Implement final report generator in `code/report/generate_report.py`; MUST include: 1) Full text of sensitivity analysis report (from T038.2), 2) Power simulation results (from T010), 3) Statistical summary (from T037), 4) Validation status (from T021) and Data Quality Report (from T053); Output to `results/final_report.md`; **Depends on T038.2, T010, T037, T021, T053, T008.1**.
- [ ] T056 [US3] **Implement Explicit Power Simulation Reporting** in `code/report/generate_power_report.py`; MUST read `results/power_analysis.json` (from T010) and generate a dedicated markdown section in `results/final_report.md` that explicitly states the estimated power, the effect size (d=0.5) used, the number of iterations, and the limitations of the pilot sample size; **Depends on T010**.
- [ ] T057 [US2] **Enhance Compliance Log Validation** in `code/validation/compliance_plausibility.py`; MUST add a specific check for the "0 minutes for all 7 days" edge case (US-2 Edge Case); if detected, flag the record as `extreme_compliance` in `data/compliance/flags.json` but DO NOT exclude it from analysis; **Input**: `data/compliance/flags.json`; **Depends on T026, T027**.
- [ ] T058 [US1] **Document Synthetic Data Limitations** in `code/docs/generate_synthetic_limitations.py`; MUST generate `docs/synthetic_data_limitations.md` from a template, explicitly stating that the synthetic baseline data (T009) is for pipeline validation only and does not reflect real psychometric distributions; **Output**: `docs/synthetic_data_limitations.md`.
- [ ] T059 [US3] **Implement Missing Data Imputation Warning** in `code/pipeline/handle_dropouts.py`; MUST generate a warning in `results/quality_report.md` if the dropout rate exceeds a moderate threshold (Assumption about attrition), explicitly stating the potential bias introduced; **Depends on T049**.
- [ ] T060 [US3] **Verify Holm-Bonferroni Correction Logic** in `tests/unit/test_holm_bonferroni.py`; MUST implement a unit test with a known set of p-values (e.g., [0.01, 0.02, 0.03, 0.04]) to verify the step-down correction logic produces the exact expected adjusted p-values; **Depends on T035**.
- [X] T053 [P] [Review: Edge Cases] Enhance `code/validation/attention_check.py` (T050) to automatically generate a `results/quality_report.md` listing all excluded participants and the specific reason for exclusion (e.g., SART accuracy < 50%), ensuring transparency in the final analysis; **Depends on T050**.
- [X] T054 [P] [Review: Data Flow] Add a dependency check in `code/pipeline/merge_data.py` (T031) to verify that `data/processed/compliance_scores.csv` (from T029) exists and is valid before attempting to merge with baseline data, preventing race conditions in the pipeline; **Pattern**: `if not os.path.exists(...) raise FileNotFoundError`.

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
- [X] T052 [P] [Review: Data Integrity] Implement strict `try/except` removal in all data loading tasks (`code/pipeline/register_participant.py`, `code/compliance/parse_logs.py`); MUST ensure that any failure to fetch real data (or load real files) raises a hard exception rather than falling back to synthetic/mock data, adhering to the "Fail Loudly" principle; **Verification**: Run `pytest tests/unit/test_no_synthetic_fallback.py`.

---

## Phase 7: Revision & Review Resolution (New Tasks)

**Purpose**: Address specific reviewer concerns regarding data flow, statistical rigor, and documentation completeness identified in the analysis phase.

### Implementation for Revision Concerns

- (No new tasks required; all concerns addressed in previous phases)