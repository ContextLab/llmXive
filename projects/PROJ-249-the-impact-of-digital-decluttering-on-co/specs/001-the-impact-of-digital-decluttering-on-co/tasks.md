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

- [ ] T001.1 [P] Create project directory structure: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/`, `data/raw/`, `data/processed/`, `data/compliance/`, `code/`, `tests/`, `results/`, `docs/`. **Command**: Run in bash terminal: `mkdir -p projects/PROJ-249-the-impact-of-digital-decluttering-on-co/{data/{raw,processed,compliance},code,tests,results,docs} && ls projects/PROJ-249-the-impact-of-digital-decluttering-on-co/ > projects/PROJ-249-the-impact-of-digital-decluttering-on-co/structure.log`. **Verification**: Run `cat projects/PROJ-249-the-impact-of-digital-decluttering-on-co/structure.log` and verify all directories exist. **Output**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/structure.log` listing created directories.
- [ ] T001.2 [P] Create `requirements.txt` with pinned dependencies: `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytest`, `flask`. **Output**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/requirements.txt`.
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data generation, scoring logic, instrument verification, power simulation, compliance logging, and recruitment workflow generation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directory structure: `data/raw/`, `data/processed/`, `data/compliance/`
- [X] T005 [P] Create `code/__init__.py` and module scaffolding for `scoring/`, `analysis/`, `validation/`, `viz/`, `pipeline/`, `report/`, `web/`
- [X] T006 [US1] Implement pseudonymous ID generator in `code/scoring/id_generator.py` adhering to `P\d{3}` pattern (FR-001); MUST generate IDs from a recruitment CSV or synthetic source to ensure deterministic linking of baseline/post data; output format MUST strictly match the `P\d{3}` regex pattern required by FR-001 and data-model.md.
- [ ] T006.1 [US1] Implement 'register_participant' function in `code/pipeline/register_participant.py` (FR-001); MUST assign IDs from T006 to participants upon entry and link them to data records; **Input Schema**: CSV with columns `['recruitment_id', 'consent_timestamp', 'demographic_hash']` from `data/raw/recruitment.csv`; **Output Schema**: `data/raw/participant_registry.csv` with columns `['participant_id', 'recruitment_id', 'status']`; **Error Handling**: MUST raise `ValueError` if `participant_id` does not match `P\d{3}` or if `recruitment_id` is duplicate; **Depends on T006**.
- [ ] T006.2 [US1] **Implement Participant Registration Service** in `code/pipeline/participant_registration.py` (FR-001); MUST implement executable logic to ingest recruitment data, assign pseudonymous IDs, and persist to the registry; **Input**: `data/raw/recruitment.csv`; **Output**: `data/raw/participant_registry.csv`; **Constraint**: MUST NOT generate static documentation as the primary deliverable; **Depends on T006, T012.0`.
- [ ] T006.2.1 [US1] **Verify Registration Service** in `code/validation/verify_registration_service.py`; MUST run integration tests against `code/pipeline/participant_registration.py` to verify ID assignment logic and data persistence; **Depends on T006.2`.
- [ ] T006.3 [US1] **Instrument Verification** in `code/validation/verify_osf_instruments.py`; MUST download SART and Ospan task source code (latest version) from the OSF repository to a local cache `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/data/raw/osf_instruments/` during the Setup phase, compute SHA-256 hash, and compare against the reference hash defined in the plan; MUST fail loudly if hash mismatch; **Output**: `results/instrument_verification.json` with status 'verified' or 'failed'; **Constraint**: MUST run BEFORE any scoring logic is used (T014, T015) and BEFORE synthetic data generation (T009). The verification step MUST run against the local cache to ensure no network calls are required during the analysis phase.
- [X] T007 Create base data schema definitions in `contracts/dataset.schema.yaml` matching `Participant`, `MeasurementRecord`, `ComplianceLog` entities
- [X] T008 Configure random seed management utility in `code/utils/random_seed.py` for reproducibility
- [ ] T008.1 [P] **Reproducibility Manifest Generator** in `code/pipeline/generate_reproducibility_manifest.py`; MUST execute at the end of the pipeline to log the exact random seed used, canonical source URLs, and artifact hashes into `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/results/reproducibility_manifest.json`; **Output**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/results/reproducibility_manifest.json`; **Depends on T008, T009, T010`.
- [ ] T009 [US1] Create synthetic data generator for baseline validation in `code/validation/synthetic_baseline.py` (FR-009, US-1); MUST read parameters from `code/config/synthetic_data_config.yaml` (mean, std, distributions) to ensure deterministic execution; output to `data/raw/synthetic_baseline.csv` with columns (`participant_id`, `metric_type`, `value`, `timestamp`); **Output**: `data/raw/synthetic_baseline.csv` with valid ranges for all metrics; **Constraint**: Synthetic data is for pipeline validation ONLY; it does NOT satisfy the acceptance criteria for FR-009's real-world pilot check; **Depends on T006, T006.3`.
- [ ] T010 [US1] **Monte Carlo Power Simulation** in `code/analysis/power_simulation.py` (FR-006, US-1); MUST use synthetic data from T009, run multiple iterations, apply Holm-Bonferroni correction (from T035), estimate power for d=0.5; **Output**: `results/power_analysis.json` with keys `power_estimate` (float), `iterations` (int), `effect_size` (float); **Constraint**: MUST run BEFORE primary analysis tasks; **Depends on T009, T035`.
- [ ] T011.0 [US1] **Host OSF Instruments Locally** in `code/pipeline/host_osf_instruments.py`; MUST extract the downloaded OSF code (from T006.3) to `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/code/web/local_instruments/` to enable local testing; **Output**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/code/web/local_instruments/`; **Depends on T006.3`.
- [ ] T011.1 [US1] **Implement Web Interface for Cognitive Tasks** in `code/web/task_interface.py` (FR-002, FR-009); MUST implement a Flask/Streamlit web application to administer SART and Ospan tasks via a browser; **Input**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/code/web/local_instruments/`; **Output**: Running web server on localhost; **Constraint**: MUST launch an HTTP server to satisfy FR-002; **Purpose**: Provides the actual user interface for participants; **Depends on T011.0, T006.3`.
- [ ] T011.2 [US1] **Implement Headless Integration Tests for Web Interface** in `code/web/test_web_interface.py`; MUST use Selenium or Playwright to automate browser interactions with the web interface from T011.1 to verify task rendering and response capture; **Input**: Running web server from T011.1; **Output**: Test results; **Depends on T011.1`.
- [ ] T012.0 [US1] **Implement Eligibility & Consent Engine** in `code/pipeline/eligibility_engine.py` (FR-001, FR-009); MUST implement executable logic to validate eligibility criteria and consent status before allowing registration; **Input**: Recruitment data; **Output**: Validated/Rejected status; **Constraint**: MUST NOT generate static documentation as the primary deliverable; **Depends on T006`.
- [ ] T012.1 [US1] **Implement Recruitment Data Ingestion Pipeline** in `code/pipeline/recruitment_ingestion.py` (FR-001); MUST implement logic to process recruitment data, apply eligibility checks (T012.0), and register participants (T006.2); **Input**: `data/raw/recruitment.csv`; **Output**: `data/raw/participant_registry.csv`; **Depends on T012.0, T006.2`.
- [ ] T012.2 [US1] Generate recruitment script template in `code/pipeline/generate_recruitment_script.py` (FR-009); MUST generate `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/recruitment_script_template.md` with fields: Prolific ID, Screening Questions, Consent Form, Pilot Instructions; **Input**: Config; **Output**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/recruitment_script_template.md`; **Depends on T012.1`.
- [X] T014 [US1] Implement SART scoring function in `code/scoring/sart.py` (response times ranging from tens of milliseconds to several seconds, commission errors); MUST accept input schema `{'response_time': float, 'accuracy': bool, 'stimulus_type': str}` and output `{'commission_errors': int, 'omission_errors': int, 'mean_rt': float}`. **Depends on T011.2, T006.3`.
- [X] T015 [US1] Implement Ospan scoring function in `code/scoring/ospan.py` (span scores); MUST accept input schema `{'stimulus': str, 'recall': str, 'accuracy': bool}` and output `{'span_score': int, 'total_correct': int}`. **Depends on T011.2, T006.3`.
- [X] T016 [US1] Implement PSS-10 and PANAS scoring functions in `code/scoring/questionnaires.py`. **Depends on T009`.
- [X] T017 [US1] Unit test for SART scoring logic against OSF reference (v+) in `tests/unit/test_sart_scoring.py` (runs against data from T009; MUST execute once T014 is complete) **Depends on T014`.
- [X] T018 [US1] Unit test for Ospan scoring logic against OSF reference (v+) in `tests/unit/test_ospan_scoring.py` (runs against data from T009; MUST execute once T015 is complete) **Depends on T015`.
- [X] T019 [US1] Unit test for PSS-10 and PANAS scoring in `tests/unit/test_questionnaire_scoring.py` (runs against data from T009; MUST execute once T016 is complete) **Depends on T016`.
- [X] T020 [P] [US1] Contract test for data schema validation in `tests/contract/test_baseline_schema.py`
- [X] T021 [US1] Implement instrument logic validation script to run synthetic data through scorers and check ranges in `code/validation/validate_instruments.py`
- [ ] T019.1 [US1] **Execute Simulated Human-in-the-Loop Pilot** in `code/pipeline/run_pilot.py`; MUST execute the recruitment protocol from T012.1 (specifically the 'execute pilot simulation' step) and T012.2 locally, spawn a set of simulated user sessions using the web interface (T011.1) to interact with SART/Ospan tasks, and collect response data; MUST validate that SART commission errors are > 0 and < 100, Mean RT within a lower-bound-defined window up to 3000ms, and PSS between low and high values. The research question is [Does a one-week period of intentionally reduced digital engagement improve sustained attention, working memory capacity, and self-reported stress and mood compared to baseline levels?], the method is [within-subjects experimental study with bootstrapped CI], and the references are [OSF SART/Ospan v2+, PSS-10, PANAS]; **Output**: `data/raw/pilot_raw.json`; **Constraint**: MUST use the web interface (T011.1) to simulate human interaction; **Depends on T011.1, T009, T014, T015, T012.1, T012.2**. NOTE: This is a faithful proxy execution on synthetic inputs to validate logic without human recruitment, satisfying FR-009's requirement for a functional pilot check with a simulated human-in-the-loop.
- [X] T022 [US1] Create baseline data collection pipeline script in `code/pipeline/collect_baseline.py`; MUST orchestrate T009 (synthetic) and T019.1 (pilot) data ingestion, ensuring strict adherence to `contracts/dataset.schema.yaml` and applying the pseudonymous ID mapping from T006.1; output MUST be stored in `data/raw/baseline_raw.csv` with a checksum manifest.
- [X] T026 [US2] Implement daily log parser in `code/compliance/parse_logs.py`
- [X] T027 [US2] Implement plausibility validation logic (FR-010) in `code/validation/compliance_plausibility.py`
- [X] T028 [US2] Implement compliance rule engine (≤30 min social media, no news, notifications off) in `code/compliance/rules_engine.py`
- [X] T029 [US2] Create compliance aggregation script to calculate daily/weekly scores in `code/pipeline/aggregate_compliance.py`
- [X] T030 [US2] Implement logic to flag non-compliant days but retain data for analysis (US-2); MUST mark entries in `data/compliance/flags.json` without dropping rows, ensuring T034 can process partial data for participants with mixed compliance.
- [X] T035 [US3] Implement Holm-Bonferroni step-down correction in `code/analysis/holm_bonferroni.py` (FR-008)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Data Collection (Priority: P1) 🎯 MVP

**Goal**: Recruit participants (simulated), collect baseline cognitive and emotional metrics, and validate instrument logic.

**Independent Test**: Run the baseline script for a single participant; verify SART, Ospan, PSS-10, and PANAS scores are recorded in `data/raw/` with valid ranges.

### Implementation for User Story 1

- [ ] T031 [US3] Implement data merger to join baseline and post-intervention records in `code/pipeline/merge_data.py`; **Input**: `data/raw/baseline_raw.csv` and `data/processed/compliance_scores.csv`; **Output**: `data/processed/merged_data.csv`; **Constraint**: MUST fail if `data/processed/compliance_scores.csv` is missing (enforced by dependency on T029); **Depends on T029`.
- [X] T032 [US3] Implement change score calculator (post - baseline) in `code/analysis/change_scores.py` (FR-005)
- [X] T033.1 [US3] **Execute Primary Bootstrapping Loop** in `code/analysis/run_bootstrap.py`; MUST execute the primary bootstrapping method (sufficient resamples) for all metrics (SART, Ospan, PSS, PANAS) using the change scores from T032; **Output**: `data/processed/bootstrap_results.json` containing mean change and 95% CI for each metric; **Constraint**: MUST run BEFORE any fallback logic; MUST NOT check for normality (Shapiro-Wilk) to trigger fallback; **FOLLOWING PLAN OVERRIDE**: Wilcoxon fallback triggered ONLY on convergence failure, NOT Shapiro-Wilk p-value. MUST emit a 'convergence_failed' flag to `data/processed/bootstrap_status.json` upon failure; **Depends on T031, T032`.
- [X] T033.2 [US3] **Bootstrapping Constraint Audit** in `tests/unit/test_no_shapiro_trigger.py`; MUST perform static analysis or unit test asserting the absence of Shapiro-Wilk logic in `code/analysis/run_bootstrap.py`; **Depends on T033.1`.
- [X] T034.1 [US3] Implement convergence failure detection logic in `code/analysis/convergence_detector.py`; MUST detect specific failure modes: 'empty resamples' (0 valid samples), 'singular matrix' (variance=0 in 99% of resamples), 'max iteration exceedance' (attempts without stable mean); MUST explicitly return a flag indicating 'convergence_failed' to trigger T034; **Depends on T033.1`.
- [X] T034 [US3] Implement fallback Wilcoxon signed-rank test logic in `code/analysis/wilcoxon_fallback.py`; MUST trigger ONLY if T034.1 detects convergence failure (FR-006). **Depends on T034.1, T033.2`.
- [X] T036 [US3] Implement Cohen's d with confidence interval calculation in `code/analysis/effect_sizes.py` (FR-007)
- [X] T037 [US3] Generate `results/statistical_summary.json` with mean change, CI, and corrected p-values (SC-001 to SC-005)
- [X] T037.1 [US3] **Success Criteria Verdict Generator** in `code/report/generate_success_verdict.py`; MUST read `results/statistical_summary.json`, compare values against SC-001 to SC-005 thresholds (p < 0.05, d ≥ 0.2), and generate `results/success_verdict.json` with a Pass/Fail status for each criterion and an overall study verdict; **Clarification**: This task verifies the *analysis logic* against defined thresholds for pipeline validation; the *scientific success* of the intervention is only determined when real data is analyzed; **Depends on T037`.
- [ ] T038.1 [US3] **Implement Objective Data Ingestion Adapter** in `code/compliance/objective_data_adapter.py` (FR-011); MUST implement a configurable adapter to attempt loading objective screen-time data from a configured path; **Input**: Config path; **Output**: `data/processed/objective_data_status.json` with status 'available' or 'missing'; **Constraint**: MUST NOT silently fall back to synthetic data; MUST explicitly document 'missing' state; **Depends on T038.2`.
- [ ] T038.2 [US3] **Implement Sensitivity Analysis Logic** in `code/report/generate_sensitivity_report.py` (FR-011); MUST check `data/processed/objective_data_status.json` from T038.1; IF 'available', implement comparison; IF 'missing', generate limitation statement; **Output**: `results/sensitivity_analysis_report.md`; **Depends on T038.1`.
- [X] T039 [US3] Create visualization generator for boxplots and change score distributions in `code/viz/generate_plots.py`
- [X] T049 [US3] Implement dropout handling logic in `code/pipeline/handle_dropouts.py`; MUST exclude participants with missing post-intervention data from paired statistical tests (T032-T036) while retaining their baseline data in `data/processed/descriptive_baseline.csv` for descriptive statistics; **Input**: `data/processed/merged_data.csv`; **Output**: `data/processed/exclusions.json` listing excluded IDs and reason 'missing_post_data'; **Depends on T031`.
- [X] T050 [US3] Implement attention check validation in `code/validation/attention_check.py`; MUST flag participants with SART accuracy < 50% as 'low_quality' and EXCLUDE them from primary analysis; **Input**: `data/raw/baseline_raw.csv`; **Output**: `data/processed/exclusions.json` append entries with reason 'low_sart_accuracy'; **Depends on T022`.
- [X] T057 [US2] **Enhance Compliance Log Validation** in `code/validation/compliance_plausibility.py`; MUST add a specific check for the "0 minutes for all 7 days" edge case (US-2 Edge Case); if detected, flag the record as `extreme_compliance` in `data/compliance/flags.json` but DO NOT exclude it from analysis; **Input**: `data/compliance/flags.json`; **Depends on T026, T027`.
- [X] T055 [US3] **Enforce Strict Data Flow Dependency** in `code/pipeline/run_analysis.py`; MUST explicitly verify that `data/processed/bootstrap_results.json` (from T033.1) is generated and valid BEFORE attempting to run the Holm-Bonferroni correction (T035) or Effect Size calculation (T036); **Logic**: If `bootstrap_results.json` is missing or empty, raise a `DataFlowError` with message "Primary bootstrapping results missing. Cannot proceed with correction."; **Depends on T033.1`.
- [X] T053 [P] [Review: Edge Cases] Enhance `code/validation/attention_check.py` (T050) to automatically generate a `results/quality_report.md` listing all excluded participants and the specific reason for exclusion (e.g., SART accuracy < 50%), ensuring transparency in the final analysis; **Depends on T050, T049`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 4: User Story 2 - Intervention Compliance Logging (Priority: P2)

**Goal**: Process daily logs, validate compliance rules, and calculate compliance scores.

**Independent Test**: Simulate a participant submitting multiple daily logs; verify compliance score calculation and deviation flagging.

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Contract test for compliance log schema in `tests/contract/test_compliance_schema.py`
- [X] T024 [P] [US2] Unit test for plausibility validation (0 ≤ minutes ≤ 1440) in `tests/unit/test_compliance_validation.py`
- [X] T025 [P] [US2] Unit test for compliance rule logic (≤30 min social media, no news) in `tests/unit/test_compliance_rules.py`

**Note**: Implementation tasks T026-T030 are located in Phase 2 (Foundational) to ensure they are available for all user stories.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Post-Intervention Analysis & Reporting (Priority: P3)

**Goal**: Compute change scores, perform robust statistical testing (bootstrapping), apply corrections, and generate reports.

**Independent Test**: Feed a synthetic dataset with known pre/post differences; verify output report correctly identifies significance, effect size, and generates plots.

*Note: Core analysis tasks (T031-T037) are located in Phase 3 (US3) to align with the data flow. This phase focuses on reporting and edge case handling.*

### Implementation for User Story 3 (Reporting & Edge Cases)

- [X] T039 [US3] Create visualization generator for boxplots and change score distributions in `code/viz/generate_plots.py`
- [X] T040 [US3] Implement final report generator in `code/report/generate_report.py`; MUST include: 1) Full text of sensitivity analysis report (from T038.2), 2) Power simulation results (from T010), 3) Statistical summary (from T037), 4) Validation status (from T021) and Data Quality Report (from T053); Output to `results/final_report.md`; **Depends on T038.2, T010, T037, T021, T053, T008.1, T037.1, `results/quality_report.md` (from T053)`.
- [X] T056 [US3] **Implement Explicit Power Simulation Reporting** in `code/report/generate_power_report.py`; MUST read `results/power_analysis.json` (from T010) and generate a dedicated markdown section in `results/final_report.md` that explicitly states the estimated power, the effect size (d=0.5) used, the number of iterations, and the limitations of the pilot sample size; **Depends on T010`.
- [X] T058 [US1] **Document Synthetic Data Limitations** in `code/docs/generate_synthetic_limitations.py`; MUST generate `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/synthetic_data_limitations.md` from a template, explicitly stating that the synthetic baseline data (T009) is for pipeline validation only and does not reflect real psychometric distributions; **Output**: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/synthetic_data_limitations.md`.
- [X] T059 [US3] **Implement Missing Data Imputation Warning** in `code/pipeline/handle_dropouts.py`; MUST generate a warning in `results/quality_report.md` if the dropout rate is considered high., explicitly stating the potential bias introduced; **Depends on T049`.
- [X] T060 [US3] **Verify Holm-Bonferroni Correction Logic** in `tests/unit/test_holm_bonferroni.py`; MUST implement a unit test with a known set of p-values (e.g., [low, moderate, high]) to verify the step-down correction logic produces the exact expected adjusted p-values; **Depends on T035`.
- [X] T062 [US3] **Statistical Rigor Audit: No Normality Switch** in `tests/unit/test_no_shapiro_trigger.py`; MUST perform static analysis or runtime assertion to ensure `code/analysis/run_bootstrap.py` does NOT contain logic that triggers a fallback based on Shapiro-Wilk p-values; **Constraint**: The fallback to Wilcoxon MUST ONLY occur on convergence failure, not normality checks; **Depends on T033.1`.
- [X] T063 [US3] **Explicit Power Limitation Documentation** in `code/report/generate_power_report.py`; MUST generate a dedicated section in `results/final_report.md` (T040) that explicitly states the estimated power, the effect size (d=0.5) used, the number of iterations, and the limitations of the pilot sample size, ensuring transparency per FR-011; **Depends on T010`.
- [X] T064 [US2] **Extreme Compliance Case Handling** in `code/validation/compliance_plausibility.py`; MUST add a specific check for the "0 minutes for all 7 days" edge case; if detected, flag the record as `extreme_compliance` in `data/compliance/flags.json` but DO NOT exclude it from analysis to avoid selection bias; **Depends on T026, T027`.
- [X] T066 [US3] **Dropout Bias Warning** in `code/pipeline/handle_dropouts.py`; MUST generate a warning in `results/quality_report.md` if the dropout rate exceeds the assumed threshold (≤15%), explicitly stating the potential bias introduced; **Depends on T049`.
- [X] T067 [US3] **Holm-Bonferroni Verification Test** in `tests/unit/test_holm_bonferroni.py`; MUST implement a unit test with a known set of p-values (e.g., a representative range of small magnitudes) to verify the step-down correction logic produces the exact expected adjusted p-values; **Depends on T035`.

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

- [X] T068 [US3] **Final Data Flow Integration Test** in `tests/integration/test_end_to_end_pipeline.py`; MUST execute the full pipeline from T009 (synthetic data) through T040 (final report) in a single run; MUST verify that `results/final_report.md` contains all required sections and that `results/statistical_summary.json` is valid; **Depends on T033.1, T035, T036, T037, T040`.
- [X] T069 [US3] **Documentation Completeness Audit** in `code/docs/audit_documentation.py`; MUST verify the existence and content of: `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/recruitment_protocol.md`, `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/recruitment_workflow.md`, `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/docs/synthetic_data_limitations.md`, `projects/PROJ-249-the-impact-of-digital-decluttering-on-co/results/reproducibility_manifest.json`, `results/quality_report.md`; **Depends on T012.1, T006.2.1, T058, T008.1, T053`.
- [X] T070 [US3] **Edge Case Coverage Verification** in `tests/unit/test_edge_case_coverage.py`; MUST assert that all edge cases (dropouts, minimal compliance, low SART accuracy) are explicitly handled and logged in the final output.; **Depends on T049, T057, T050`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of all analysis and reporting tasks (T033.1, T035, T036, T040)
- **Final Validation (Phase 8)**: Depends on completion of all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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