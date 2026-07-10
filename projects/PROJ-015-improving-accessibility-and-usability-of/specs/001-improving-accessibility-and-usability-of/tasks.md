# Tasks: Improving Accessibility and Usability of Complex Computer Systems for People with Disabilities

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US0, US1, US2, US3)
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

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup data directory structure: `data/raw/` (immutable), `data/processed/`
- [X] T005 [P] Implement checksumming utility for raw data integrity in `code/utils/checksum.py`
- [X] T006 [P] Setup random seed fixing infrastructure in `code/utils/seed.py`
- [X] T007 Create base data models (`Participant`, `Session`, `Metric`) in `code/models/data_models.py` with explicit attributes: `Participant` (id, disability_type, interface_sequence), `Session` (session_id, participant_id, interface_type, start_time, end_time, error_count, explanation_engagement_time_seconds, sus_score, skip_count, status), `Metric` (metric_name, interface_type, mean, std_dev, p_value, confidence_interval, test_method).
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logger.py`
- [ ] T009 Setup environment configuration management for study parameters in `code/config/settings.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - XAI Interface Configuration (Priority: P0) 🎯 MVP

**Goal**: Implement the mechanism to configure and deploy Traditional vs. Explainable interface variants with XAI overlays.

**Independent Test**: The configuration module can be tested by loading a task definition and verifying that two distinct UI renders are generated: one without overlays and one with the specified XAI overlays, ensuring the XAI data is correctly bound to the UI elements.

### Implementation for User Story 0

- [~] T010 [P] [US0] Implement `TraditionalInterface` renderer in `code/simulator/interfaces/traditional.py` <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
expected <block end>, but found ':'
 in "<unicode string>", line 1, column 1:
: T010
 ^) -->
- [~] T011 [P] [US0] Implement `ExplainableInterface` renderer with rule-based XAI overlay logic in `code/simulator/interfaces/explainable.py`
- [~] T012a [US0] Create the skeleton Streamlit app entry point `code/simulator/app.py` (basic layout, no collectors yet)
- [~] T013a [US0] Implement `XAIOverlayGenerator` in `code/simulator/xai_generator.py` using deterministic rule-based mapping (Task difficulty -> Heatmap opacity) as the default simulation.
- [~] T013b [US0] Implement `ConfigurableXAIWrapper` in `code/simulator/xai_wrapper.py` to allow runtime selection of SHAP/LIME algorithms (if available) or fallback to the rule-based simulation (requires T013a), satisfying the requirement to integrate specific XAI techniques. Default to rule-based simulation to avoid unverified dependencies.
- [~] T014 [US0] Add session logging logic to record `interface_variant` in `code/simulator/session_logger.py`

**Checkpoint**: At this point, the simulator can render both interface types and log which one was presented.

---

## Phase 4: User Story 1 - Core Usability Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Execute the standardized usability test protocol, collecting metrics (time, errors, SUS, engagement) for both interfaces with Latin Square counterbalancing.

**Independent Test**: The research pipeline can be fully tested by running the data collection script on a simulated dataset or a small pilot group (n=5) to verify that completion times, error counts, explanation engagement times, and SUS scores are correctly logged and formatted for downstream statistical analysis.

### Implementation for User Story 1

- [~] T015 [P] [US1] Implement `LatinSquareCounterbalancer` in `code/simulator/counterbalance.py` to assign `Traditional->Explainable` or `Explainable->Traditional` sequences
- [~] T016 [P] [US1] Implement data collection handlers for `completion_time`, `error_count`, and `explanation_engagement_time` in `code/simulator/metrics_collector.py`
- [~] T017 [P] [US1] Integrate all collectors (T016, T015) and SUS questionnaire (T017) into the Streamlit app flow in `code/simulator/app.py` ensuring sequence order is respected (requires T016, T015, T012a). Implement SUS logic: if >1 missing items, reject session; if <=1 missing, impute missing value with mean of participant's other responses per EC-001.
- [~] T019 [US1] Implement raw data logging to `data/raw/session_{id}.json` with checksum generation (requires T007 data models, T015 counterbalancing, T010/T011 renderers).
- [~] T020 [US1] Implement dropout handling: log `dropout_reason` and flag `status='incomplete'` for partial sessions in `code/simulator/session_logger.py`

**Checkpoint**: The system can collect real-time interaction data, handle dropouts, and store immutable raw logs.

---

## Phase 5: User Story 2 - Statistical Significance Analysis (Priority: P2)

**Goal**: Perform statistical analysis (Shapiro-Wilk, Repeated Measures ANOVA, Holm-Bonferroni) on collected metrics to determine significance.

**Independent Test**: The analysis module can be tested independently by feeding it a pre-generated CSV file with known distributions and verifying that the p-values, confidence intervals, and ANOVA F-statistics are calculated correctly by `scipy.stats`.

### Implementation for User Story 2

- [~] T021 [P] [US2] Implement data cleaning pipeline: filter incomplete sessions, apply SUS imputation in `code/analysis/data_cleaner.py` (depends on T019 raw data generation).
- [~] T022 [P] [US2] Implement Shapiro-Wilk normality test on difference scores in `code/analysis/stat_utils.py`.
- [~] T023 [P] [US2] Implement Repeated Measures ANOVA for Completion Time, Error Count, and SUS in `code/analysis/stat_utils.py`. Explicitly exclude `explanation_engagement_time` from inferential testing (descriptive only) per Plan Phase 3, as comparing to a constant zero is tautological.
- [~] T023b [P] [US2] Implement descriptive statistics reporting (mean, std) for `explanation_engagement_time` in `code/analysis/stat_utils.py` and output to `data/processed/descriptive_stats.csv`.
- [~] T024 [P] [US2] Implement Holm-Bonferroni correction for multiple comparisons in `code/analysis/stat_utils.py`.
- [~] T025 [US2] Create the main analysis script `code/analysis/run_analysis.py` that orchestrates cleaning, testing, and output generation. <!-- FAILED: unspecified -->
- [~] T026 [US2] Generate `data/processed/metrics_summary.csv` with F-statistic, p-value, adjusted p-value, and effect size.

**Checkpoint**: The system can process raw data into statistically valid summary metrics with proper corrections.

---

## Phase 6: User Story 3 - Reproducible Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-quality visualizations and a single executable Jupyter notebook documenting the pipeline.

**Independent Test**: The reporting module can be tested by running the notebook on a small sample dataset and verifying that the generated images exist, have correct axis labels, and that the notebook executes without errors from start to finish.

### Implementation for User Story 3

- [~] T027 [P] [US3] Implement visualization functions using `matplotlib` for box plots with error bars in `code/analysis/visualizer.py` (depends on T026 metrics_summary.csv).
- [~] T028 [P] [US3] Create the master Jupyter notebook `code/analysis.ipynb` with cells for: Data Loading, Cleaning, Statistical Analysis, Visualization, and Reporting.
- [~] T029 [US3] Ensure `code/analysis.ipynb` is fully executable from raw data to final figures on CPU-only environment, automatically resolving checksummed raw data files defined in T019 without manual path adjustments.
- [~] T030 [US3] Generate a summary report text file `data/processed/report_summary.txt` including: (1) actual N achieved, (2) power limitation flags for underpowered subgroups (even if aggregate N >= 30), and (3) exclusion reasons for incomplete sessions.

**Checkpoint**: The entire pipeline is reproducible via a single notebook, producing publication-ready figures.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T031 [P] Documentation updates in `README.md` and `docs/`
- [~] T032 Code cleanup and refactoring <!-- ATOMIZE: requested -->
- [~] T033 Performance optimization across all stories
- [ ] T034 [P] Additional unit tests for statistical functions in `tests/unit/test_stat_utils.py`
- [ ] T035 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US0 (P0)**: Must be implemented first to enable the simulator.
 - **US1 (P1)**: Depends on US0 (simulator) to generate data. **Specifically, T019 depends on T007 (Data Models), T015 (Counterbalancing), and T010/T011 (Renderers).**
 - **US2 (P2)**: Depends on US1 (data collection) to have data to analyze. **Phase 5 cannot start until Phase 4 (T019) completes.**
 - **US3 (P3)**: Depends on US2 (analysis results) to visualize. **Phase 6 cannot start until Phase 5 (T026) completes.**
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