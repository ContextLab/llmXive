# Tasks: The Impact of Digital Decluttering on Cognitive Performance and Well-being

**Input**: Design documents from `/specs/001-digital-decluttering-study/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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
- [X] T006 [P] Implement pseudonymous ID generator in `code/scoring/id_generator.py` adhering to `P\d{3}` pattern (FR-001); MUST generate IDs from a recruitment CSV or synthetic source to ensure deterministic linking of baseline/post data; output format MUST strictly match the `P\d{3}` regex pattern required by FR-001 and data-model.md.
- [X] T007 Create base data schema definitions in `contracts/dataset.schema.yaml` matching `Participant`, `MeasurementRecord`, `ComplianceLog` entities
- [X] T008 Configure random seed management utility in `code/utils/random_seed.py` for reproducibility
- [X] T009 Setup environment configuration management for file paths and parameters

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Data Collection (Priority: P1) 🎯 MVP

**Goal**: Recruit participants (simulated), collect baseline cognitive and emotional metrics, and validate instrument logic.

**Independent Test**: Run the baseline script for a single participant; verify SART, Ospan, PSS-10, and PANAS scores are recorded in `data/raw/` with valid ranges.

### Implementation for User Story 1

- [ ] T017 [US1] Create synthetic data generator for baseline validation in `code/validation/synthetic_baseline.py` (FR-009, US-1); MUST output to `data/raw/synthetic_baseline.csv` with columns (`participant_id`, `metric_type`, `value`, `timestamp`) and defined distributions (e.g., SART errors ~ N(10, 3), PSS-10 ~ N(20, 5)).
- [ ] T014 [US1] Implement SART scoring function in `code/scoring/sart.py` (response times ranging from tens of milliseconds to several seconds, commission errors); MUST accept input schema `{'response_time': float, 'accuracy': bool, 'stimulus_type': str}` and output `{'commission_errors': int, 'omission_errors': int, 'mean_rt': float}`.
- [X] T015 [US1] Implement Ospan scoring function in `code/scoring/ospan.py` (span scores); MUST accept input schema `{'stimulus': str, 'recall': str, 'accuracy': bool}` and output `{'span_score': int, 'total_correct': int}`.
- [ ] T016 [US1] Implement PSS-10 and PANAS scoring functions in `code/scoring/questionnaires.py`
- [ ] T014.1 [US1] Implement web interface wrapper in `code/web/task_interface.py` that embeds OSF task URLs (v2.1+) and captures raw JSON response data for downstream scoring; MUST provide a browser-based interaction loop to collect raw data (JSON) and link it to participant IDs (FR-002); MUST validate that the web loop correctly captures response times and accuracy before data is passed to scoring functions.
- [ ] T011 [P] [US1] Unit test for SART scoring logic against OSF reference (v+) in `tests/unit/test_sart_scoring.py` (runs against data from T017)
- [~] T012 [P] [US1] Unit test for Ospan scoring logic against OSF reference (v+) in `tests/unit/test_ospan_scoring.py` (runs against data from T017)
- [~] T013 [P] [US1] Unit test for PSS-10 and PANAS scoring in `tests/unit/test_questionnaire_scoring.py` (runs against data from T017)
- [~] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_baseline_schema.py`
- [~] T018 [US1] Implement instrument logic validation script to run synthetic data through scorers and check ranges in `code/validation/validate_instruments.py`
- [~] T019 [US1] Create baseline data collection pipeline script in `code/pipeline/collect_baseline.py` <!-- FAILED: unspecified -->
- [ ] T019.1 [US1] Implement pre-study pilot check (n=5) with real participants in `code/pipeline/run_pilot.py`; MUST recruit 5 human subjects, run them through the web interface (T014.1), collect real data, and validate task functionality against expected psychometric ranges (FR-009); this task is distinct from synthetic validation and is the required empirical step.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Intervention Compliance Logging (Priority: P2)

**Goal**: Process daily logs, validate compliance rules, and calculate compliance scores.

**Independent Test**: Simulate a participant submitting 7 daily logs; verify compliance score calculation and deviation flagging.

### Tests for User Story 2 ⚠️

- [~] T021 [P] [US2] Contract test for compliance log schema in `tests/contract/test_compliance_schema.py`
- [~] T022 [P] [US2] Unit test for plausibility validation (0 ≤ minutes ≤ 1440) in `tests/unit/test_compliance_validation.py`
- [~] T023 [P] [US2] Unit test for compliance rule logic (≤30 min social media, no news) in `tests/unit/test_compliance_rules.py`

### Implementation for User Story 2

- [~] T024 [US2] Implement daily log parser in `code/compliance/parse_logs.py`
- [~] T025 [US2] Implement plausibility validation logic (FR-010) in `code/validation/compliance_plausibility.py`
- [~] T026 [US2] Implement compliance rule engine (≤30 min, no news, notifications off) in `code/compliance/rules_engine.py`
- [~] T027 [US2] Create compliance aggregation script to calculate daily/weekly scores in `code/pipeline/aggregate_compliance.py`
- [~] T028 [US2] Implement logic to flag non-compliant days but retain data for analysis (US-2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Post-Intervention Analysis & Reporting (Priority: P3)

**Goal**: Compute change scores, perform robust statistical testing (bootstrapping), apply corrections, and generate reports.

**Independent Test**: Feed a synthetic dataset with known pre/post differences; verify output report correctly identifies significance, effect size, and generates plots.

### Implementation for User Story 3

- [~] T034 [US3] Implement data merger to join baseline and post-intervention records in `code/pipeline/merge_data.py`
- [~] T035 [US3] Implement change score calculator (post - baseline) in `code/analysis/change_scores.py` (FR-005)
- [~] T036 [US3] Implement primary bootstrapped CI calculation (10,000 resamples) in `code/analysis/bootstrap_ci.py` (FR-006)
- [~] T037.1 [US3] Implement convergence failure detection logic in `code/analysis/convergence_detector.py`; MUST detect specific failure modes (empty resamples, singular matrix, max iteration exceedance) to trigger Wilcoxon fallback (FR-006); MUST explicitly return a flag indicating 'convergence_failed' to trigger T037.
- [~] T037 [US3] Implement fallback Wilcoxon signed-rank test logic in `code/analysis/wilcoxon_fallback.py`; MUST trigger ONLY if T037.1 detects convergence failure (FR-006).
- [~] T038 [US3] Implement Holm-Bonferroni step-down correction in `code/analysis/holm_bonferroni.py` (FR-008)
- [~] T039 [US3] Implement Cohen's d with 95% CI calculation in `code/analysis/effect_sizes.py` (FR-007)
- [~] T020 [US3] Implement Monte Carlo power simulation (1,000 iterations) to estimate power for detecting d=0.5 with Holm-Bonferroni correction in `code/analysis/power_simulation.py`; MUST use synthetic data from T017 and apply Holm-Bonferroni correction to alpha in every iteration to account for reduced alpha; MUST write output to `results/power_analysis.json` (FR-006, US-1).
- [~] T040 [US3] Generate `results/statistical_summary.json` with mean change, CI, and corrected p-values (SC-001 to SC-005)
- [~] T029 [US3] Generate sensitivity analysis report in `results/sensitivity_analysis_report.md`; MUST explicitly document self-report limitations or compare against objective data if available (FR-011)
- [~] T041 [US3] Create visualization generator for boxplots and change score distributions in `code/viz/generate_plots.py`
- [ ] T043 [US3] Create validation script to check results against success criteria (SC-001 to SC-005) in `code/validation/validate_success_criteria.py`; MUST explicitly compare `results/statistical_summary.json` values against thresholds (p < 0.05, d ≥ 0.2) AND verify the *direction* of the effect (e.g., reduction for SART, increase for Ospan) to match the hypothesis; generate a validation report; MUST run before T042.
- [ ] T042 [US3] Implement final report generator in `code/report/generate_report.py`; MUST include: 1) Full text of sensitivity analysis report (from T029), 2) Power simulation results (from T020), 3) Statistical summary (from T040), 4) Validation status (from T043); Output to `results/final_report.md`; MUST be the final task in Phase 5.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates: `README.md`, `quickstart.md`, and API docs in `docs/`
- [ ] T045 Code cleanup and refactoring for readability
- [ ] T046 Performance optimization for bootstrap loops (vectorization)
- [ ] T047 [P] Additional unit tests for edge cases (dropouts, missing data) in `tests/unit/`
- [ ] T048 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must complete first** to establish baseline data and instrument validation.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May run in parallel with US1.
- **User Story 3 (P3)**: Depends on **US1 and US2 completion** (needs baseline data, post data, and compliance logs). Cannot run until US1 and US2 data pipelines are functional.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Scorers before pipelines
- Pipelines before analysis/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **US1 and US2** can run in parallel after Phase 2 (different data domains)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (US1 & US2 only)

---

## Parallel Example: User Story 1 & 2

```bash
# Launch US1 tests and US2 tests together (after Phase 2):
Task: "Unit test for SART scoring logic in tests/unit/test_sart_scoring.py"
Task: "Unit test for compliance rules in tests/unit/test_compliance_rules.py"

# Launch US1 implementation and US2 implementation together:
Task: "Implement SART scoring function in code/scoring/sart.py"
Task: "Implement daily log parser in code/compliance/parse_logs.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Baseline Data & Instrument Validation)
4. **STOP and VALIDATE**: Test baseline collection and instrument scoring independently. Ensure synthetic data generation works and power simulation runs.
5. Deploy/demo if ready (MVP: Data collection capability).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Compliance Logging)
4. Add User Story 3 → Test independently → Deploy/Demo (Full Analysis)
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline & Instruments)
 - Developer B: User Story 2 (Compliance Logs)
3. Once US1 and US2 are complete, Developer A+B collaborate on User Story 3 (Analysis & Reporting).

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do not run US3 until US1 and US2 data generation pipelines are verified.
- **CRITICAL**: Bootstrapping is the primary method; Wilcoxon is only a fallback if bootstrap fails. Do not use Shapiro-Wilk to trigger the switch.
- **CRITICAL**: FR-006 updated to forbid Shapiro-Wilk trigger; T037.1 and T037 reflect this.
- **CRITICAL**: T029 moved to Phase 5 to respect data flow.
- **CRITICAL**: T042 must include full text of sensitivity report and power results.
- **CRITICAL**: T020 moved to Phase 5 to ensure it uses completed analysis logic (T036/T038) and applies Holm-Bonferroni correction.
- **CRITICAL**: T019.1 added to satisfy FR-009's requirement for real participant pilot testing.
- **CRITICAL**: T014.1 added to satisfy FR-002's requirement for web-based task delivery.
- **CRITICAL**: T043 updated to validate effect direction, not just magnitude.
- **CRITICAL**: T017 moved to top of Phase 3 to ensure data exists for tests.
- **CRITICAL**: T042 is now the final task in Phase 5, dependent on T043 validation.