# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (scipy, matplotlib, pandas, jupyter, streamlit)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan.md):

- [X] T004 [P] Setup data directory structure: `data/raw/` (immutable), `data/processed/`
- [X] T005 [P] Implement checksumming utility for raw data integrity in `code/utils/checksum.py`
- [X] T006 [P] Setup random seed fixing infrastructure in `code/utils/seed.py`
- [X] T007 [P] Create base data models (`Participant`, `Session`, `Metric`) in `code/models/data_models.py` with explicit attributes: `Participant` (id, disability_type, interface_sequence), `Session` (session_id, participant_id, interface_type, start_time, end_time, error_count, explanation_engagement_time_seconds, sus_score, skip_count, status), `Metric` (metric_name, interface_type, mean, std_dev, p_value, confidence_interval, test_method).
- [X] T008 [P] Configure error handling and logging infrastructure in `code/utils/logger.py`
- [X] T009 [P] Setup environment configuration management for study parameters in `code/config/settings.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - XAI Interface Configuration (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to configure and deploy Traditional vs. Explainable interface variants with XAI overlays.

**Independent Test**: The configuration module can be tested by loading a task definition and verifying that two distinct UI renders are generated: one without overlays and one with the specified XAI overlays, ensuring the XAI data is correctly bound to the UI elements.

### Implementation for User Story 0

- [X] T010 [P] [US0] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py`
- [X] T011 [P] [US0] Implement `ExplainableInterface` renderer with rule-based XAI overlay logic in `code/simulator/interfaces/explainable.py`
- [X] T012a [US0] Create the skeleton Streamlit app entry point `code/simulator/app.py` (basic layout, no collectors yet)
- [X] T013a [US0] Implement `XAIOverlayGenerator` in `code/simulator/xai_generator.py` using deterministic rule-based mapping (Task difficulty -> Heatmap opacity) as the default simulation.
- [X] T013b [US0] Implement `ConfigurableXAIWrapper` in `code/simulator/xai_wrapper.py` to wrap the rule-based simulation (T013a). **Clarification**: Per Plan constraints, SHAP/LIME are explicitly unavailable. This task MUST NOT contain import statements for SHAP/LIME, nor any runtime logic to load external libraries. The wrapper MUST strictly delegate to the rule-based generator (T013a) as the *only* implementation path. **Dependencies**: Requires T013a (rule-based generator).
- [X] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`

**Checkpoint**: At this point, the simulator can render both interface types and log which one was presented.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Execute the standardized usability test protocol, collecting metrics (time, errors, SUS, engagement) for both interfaces with Latin Square counterbalancing.

**Independent Test**: The research pipeline can be fully tested by running the data collection script on a simulated dataset or a small pilot group (n=5) to verify that completion times, error counts, explanation engagement times, and SUS scores are correctly logged and formatted for downstream statistical analysis.

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement `LatinSquareCounterbalancer` in `code/simulator/counterbalance.py` to assign `Traditional->Explainable` or `Explainable->Traditional` sequences
- [X] T016 [P] [US1] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [X] T017 [US1] Integrate all collectors (T016, T015) and SUS questionnaire into the Streamlit app flow in `code/simulator/app.py` ensuring sequence order is respected. **Dependencies**: Requires T016, T015, T012a, T010, and T011 (Interface Renderers) to collect data from the interface. Implement SUS logic: if >1 missing items, reject session; if <=1 missing, impute missing value with mean of participant's other responses per EC-001.
- [X] T019b [US1] Implement `DataValidator` in `code/simulator/data_validator.py` to enforce strict schema validation on incoming session data *before* logging to `data/raw/`. **Rationale**: Addresses EC-001 and FR-006 requirements for data integrity, ensuring that partial or malformed sessions are caught at the source. **Dependencies**: Requires T007 (Data Models) and `contracts/session.schema.yaml`.
- [X] T019 [US1] Implement raw data logging to `data/raw/session_{id}.json` triggered **on session completion event from `app.py`**. The JSON structure MUST include: `participant_id`, `disability_type`, `interface_type`, `sequence`, `start_time`, `end_time`, `error_count`, `explanation_engagement_time_seconds`, `sus_score`, `status`, and `dropout_reason` (if applicable). This structure aligns with `contracts/session.schema.yaml`. This task confirms integration with the simulated HCI environment (FR-007). **Dependencies**: Requires T019b (validation), T007 (Data Models), T015 (Counterbalancing), T010/T011 (Renderers), and T016 (Metrics Collector). **Action**: Logs `status='incomplete'` and `dropout_reason` for partial sessions as per EC-001. **Acceptance Criteria**: Ensure logged `status='incomplete'` entries are guaranteed to be excluded by T021 filtering logic.
- [X] T020 [US1] Implement dropout handling: log `dropout_reason` and flag `status='incomplete'` for partial sessions in `code/simulator/session_logger.py`

**Checkpoint**: The system can collect real-time interaction data, handle dropouts, and store immutable raw logs.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

**Goal**: Perform statistical analysis (Repeated Measures ANOVA, Holm-Bonferroni) on collected metrics to determine significance.

**Independent Test**: The analysis module can be tested independently by feeding it a pre-generated CSV file with known distributions and verifying that the p-values, confidence intervals, and ANOVA F-statistics are calculated correctly by `scipy.stats`. **CRITICAL**: The test MUST also verify that `explanation_engagement_time` is ABSENT from the inferential output (ANOVA results), confirming it was excluded from testing.

### Implementation for User Story 2

- [X] T021-exclude [US2] Implement the specific exclusion logic in `code/analysis/data_cleaner.py` to filter out sessions with `status='incomplete'`. **Output**: Generates `data/processed/cleaned_sessions.csv`. **Rationale**: Explicitly implements the exclusion requirement from EC-001 and FR-006 as a distinct, verifiable step.
- [X] T021 [US2] Implement data cleaning pipeline orchestration in `code/analysis/data_cleaner.py`. **Dependencies**: Requires T021-exclude (to perform filtering), T004 (Directory Setup), T019b (Schema Validation), `contracts/session.schema.yaml`, and T019 (Data Logging). **Action**: Orchestrates the pipeline, applies SUS imputation (if <=1 missing), and passes the filtered data to the statistical engine.
- [X] T022 [US2] Implement Shapiro-Wilk normality test on difference scores in `code/analysis/stat_utils.py`. **Note**: This test is run for logging purposes only; the test selection logic is bypassed per T023a.
- [X] T023a [US2] Implement Repeated Measures ANOVA for Completion Time, Error Count, and SUS in `code/analysis/stat_utils.py`. **Logic**: Implement ANOVA for all metrics. **Do NOT implement normality-based test selection or Levene's test**. The logic must explicitly skip normality testing and Levene's test entirely, as mandated by Constitution Principle VII and Plan Phase 3. **Dependencies**: Requires T023b-exclude-enforce (to ensure exclusion logic is applied) and T022 (for logging only). **Deliverable**: Generates `data/processed/metrics_summary.csv` with F-statistic, p-value, adjusted p-value, and effect size.
- [X] T023a-amendment [US2] Create the Spec Amendment artifact `specs/001-gene-regulation/contracts/fr_002_amendment.md` to formally update FR-002. **Action**: This document must explicitly state that FR-002's T-Test/Wilcoxon/Levene's mandate is superseded by Repeated Measures ANOVA per Constitution Principle VII and Plan Phase 3. **Rationale**: Closes the traceability gap between Spec (FR-002) and Task (T023a) by updating the source of truth. **Dependencies**: Requires T023a (to reference the implemented logic).
- [X] T023b-exclude-enforce [US2] Implement the exclusion logic for `explanation_engagement_time` from the ANOVA pipeline in `code/analysis/stat_utils.py`. **Action**: Ensure this metric is NOT passed to the ANOVA function. **Rationale**: Per Plan Phase 3 Action 4, this metric is tautological for inferential testing. **Deliverable**: Log a specific entry in `data/processed/exclusion_log.txt` stating "explanation_engagement_time excluded from inferential testing per Plan Phase 3 Action 4".
- [X] T023b [US2] Implement descriptive statistics reporting (mean, std) for `explanation_engagement_time` in `code/analysis/stat_utils.py` and output to `data/processed/descriptive_stats.csv`. **Rationale**: Per Plan Phase 3 Action 4, this metric is not included in the ANOVA analysis but must be reported descriptively. Tags: `[Plan-Phase3-Action4] [SC-005-Data-Validity]`. **Dependencies**: Requires T023b-exclude-enforce.
- [X] T024 [US2] Implement Holm-Bonferroni correction for multiple comparisons in `code/analysis/stat_utils.py`.
- [X] T024a [US2] Implement primary test significance verification in `code/analysis/stat_utils.py`. MUST explicitly verify that the ANOVA F-test p-value < 0.05 (alpha=0.05) before applying Holm-Bonferroni correction to post-hoc comparisons. Output the verification result to `data/processed/primary_test_verification.txt`. This directly addresses SC-002.
- [X] T025 [US2] Create the main analysis script `code/analysis/run_analysis.py` that orchestrates cleaning, testing, and output generation. **CLI**: `python run_analysis.py --input data/processed/cleaned_sessions.csv --output data/processed/metrics_summary.csv`. **Deliverables**: Generates `data/processed/metrics_summary.csv` (F-stat, p-value, adjusted p-value, effect size) and `data/processed/report_summary.txt`.
- [X] T026 [US2] Generate `data/processed/metrics_summary.csv` with F-statistic, p-value, adjusted p-value, and effect size.
- [X] T036 [US2] Implement `PowerCalculator` in `code/analysis/power_analysis.py` to compute statistical power given N, effect size, and alpha. **Rationale**: Addresses the plan's "Scope Adjustment" regarding N=30 power constraints. **Action**: This task MUST generate specific "power limitation flags" for any subgroup with N < 30, explicitly stating the subgroup is underpowered and exploratory. These flags must be output to `data/processed/power_flags.txt` and consumed by T030. **Dependencies**: Requires T026.

**Checkpoint**: The system can process raw data into statistically valid summary metrics with proper corrections and power analysis.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality visualizations and a single executable Jupyter notebook documenting the pipeline.

**Independent Test**: The reporting module can be tested by running the notebook on a small sample dataset and verifying that the generated images exist, have correct axis labels, and that the notebook executes without errors from start to finish.

### Implementation for User Story 3

- [X] T027 [US3] Implement visualization functions using `matplotlib` for box plots with error bars in `code/analysis/visualizer.py` (depends on T026 metrics_summary.csv).
- [X] T028 [US3] Create the master Jupyter notebook `code/analysis.ipynb` with cells for: Data Loading, Cleaning, Statistical Analysis, Visualization, and Reporting. **Dependencies**: Requires T026 (metrics_summary.csv) to ensure the notebook is created with the correct data source from the start.
- [X] T029 [US3] Refactor `code/analysis.ipynb` (T028) to resolve relative paths and hardcode seed values. **Action**: Ensure the notebook executes end-to-end on a CPU-only environment without manual intervention. **Deliverable**: Generate `data/processed/notebook_execution_log.txt` containing 'PASS' if the notebook runs successfully from raw data to final figures, 'FAIL' otherwise. **Verification Criteria**: Must verify that `data/processed/metrics_summary.csv` contains the expected columns (F-statistic, p-value, etc.) AND that all generated plots (box plots, error bars) exist and are correctly labeled. This satisfies SC-004.
- [X] T030 [US3] Generate a summary report text file `data/processed/report_summary.txt` including: (1) actual N achieved, (2) power limitation flags for underpowered subgroups (N<30) derived from T036, and (3) exclusion reasons for incomplete sessions. **Dependencies**: Requires T036 (PowerCalculator) and T021-exclude.
- [X] T038 [US3] Extend `code/analysis.ipynb` (T028) to include a dedicated "Limitations & Power Analysis" section that dynamically renders the output of T036 and T030. **Rationale**: Ensures the final report (SC-004) transparently documents the study's power limitations and subgroup constraints as mandated by the plan.

**Checkpoint**: The entire pipeline is reproducible via a single notebook, producing publication-ready figures and power analysis.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `README.md`: Update 'Installation' section with environment setup steps, 'Usage' section with simulator and analysis run commands, and 'Results' section with interpretation guidelines.
- [X] T032 Code cleanup and refactoring: Refactor `code/analysis/stat_utils.py` to remove unused imports and ensure PEP8 compliance.
- [X] T033 Performance optimization: Profile `code/analysis/run_analysis.py` with 1000 rows and optimize any bottlenecks. Output `data/processed/performance_profile.csv`.
- [X] T034 [P] Additional unit tests for statistical functions in `tests/unit/test_stat_utils.py`.
- [X] T039 [P] Run quickstart.md validation: Execute `quickstart.md` steps and verify exit code 0. Output `data/processed/quickstart_validation_log.txt`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US0 (P0)**: Must be implemented first to enable the simulator.
 - **US1 (P1)**: Depends on US0 (simulator) to generate data. **Specifically, T019 depends on T007 (Data Models), T015 (Counterbalancing), T010/T011 (Renderers), T016 (Metrics Collector), and T019b (Validation).**
 - **US2 (P2)**: Depends on US1 (data collection) to have data to analyze. **Phase 5 cannot start until Phase 4 (T019) completes.**
 - **US3 (P3)**: Depends on US2 (analysis results) to visualize. **Phase 6 cannot start until Phase 5 (T026, T036) completes.**
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 0 (P0)**: Can start after Foundational (Phase 2). No dependencies on other stories.
- **User Story 1 (P1)**: Can start after Foundational (Phase 2) and US0 implementation.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) and US1 implementation.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) and US2 implementation.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only** if dependencies are met (e.g., US2 cannot start until US1 is done).

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

### MVP First (User Story 0 & 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 0 (Simulator)
4. Complete Phase 4: User Story 1 (Data Collection)
5. **STOP and VALIDATE**: Test data collection pipeline with pilot group.
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 0 → Test independently → Deploy/Demo (Simulator Ready)
3. Add User Story 1 → Test independently → Deploy/Demo (Data Collected)
4. Add User Story 2 → Test independently → Deploy/Demo (Analysis Complete)
5. Add User Story 3 → Test independently → Deploy/Demo (Report Generated)
6. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 0 (Simulator)
 - Developer B: User Story 1 (Data Collection - can start once US0 is partially done)
 - Developer C: User Story 2 (Analysis - can start once US1 is partially done)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All statistical tasks must use CPU-only methods (scipy.stats) and avoid GPU/LLM dependencies.
- **Constraint**: `explanation_engagement_time` is descriptive only, not inferential.
- **Constraint**: SUS imputation logic must strictly follow EC-001 (impute ≤1 missing, reject >1).
- **Constraint**: Repeated Measures ANOVA supersedes FR-002's T-Test/Wilcoxon logic per Plan and Constitution Principle VII.
- **Override Note**: Normality testing is not performed for the primary test (ANOVA) due to the paired design; this is a methodological requirement, not a runtime skip.
- **Note**: The 'Phase N+1: Revision & Gap Resolution' section has been removed. All critical tasks (T036, T019b) are now integrated into the main execution phases (Phase 4 and Phase 5).