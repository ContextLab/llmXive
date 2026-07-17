# Tasks: The Influence of Perceived Agency in AI Interactions on Trust

**Input**: Design documents from `specs/001-perceived-agency-trust/`
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

## Phase 0: Research & Validation (Prerequisites)

**Purpose**: Verify citations, execute power analysis, and generate research artifacts before implementation begins.

**⚠️ CRITICAL**: No implementation can begin until Phase 0 is complete.

- [ ] T000 [P] Execute Reference-Validator Agent on Lee & See (2004) and Langer (1975) citations. Input: BibTeX or inline citations from spec/plan. Output: `research/validation_report.json` with validation status and title overlap scores.
- [ ] T001 [P] Generate `research.md` artifact documenting power analysis targets (≥0.80 power, f=0.25) and literature review findings. Schema: Must include a table with columns: Effect Size (f), Alpha, Target Power, Required N, and Calculated N.
- [ ] T002 [P] Execute pre-study power analysis calculation using `pwr` (R) or `statsmodels` (Python) with parameters f=0.25, alpha=0.05, power=0.80. Output the calculated N to `research/power_calculation.json`.
- [ ] T003 [P] Validate `research.md` and `research/power_calculation.json` against `plan.md` Phase 0 requirements.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004 Create project directory structure (`code/experiment/`, `code/analysis/`, `data/raw/`, `data/processed/`, `docs/`)
- [ ] T005 [P] Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pingouin, pytest)
- [ ] T006 [P] Configure linting (flake8/black) and formatting tools
- [ ] T007 [P] Create data schema contracts in `specs/001-perceived-agency-trust/contracts/` (participant.schema.yaml, analysis_output.schema.yaml, power_analysis.schema.yaml)
- [ ] T008 [P] Setup environment configuration management by creating `code/experiment/config.yaml` with keys: `sample_size` (from T002), `alpha_level`, `seed`, and `data_path`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] Implement randomization logic in `code/experiment/randomization.py` (assigns High/Low/Control with fixed seed for reproducibility)
- [ ] T010 [P] Create base data processing utilities in `code/analysis/data_utils.py` (CSV loading, checksumming, PII scanning)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Experimental Task Execution and Data Capture (Priority: P1) 🎯 MVP

**Goal**: Present the simulated decision-making task with randomized conditions and capture behavioral/psychometric data.

**Independent Test**: A test runner can simulate a participant session, verify randomization, confirm illusory controls don't alter AI output, and validate the survey export schema.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement "High Agency" condition interface in `code/experiment/app.py` (functional sliders that do NOT alter AI output)
- [ ] T012 [P] [US1] Implement "Low Agency" condition interface in `code/experiment/app.py` (restricted controls)
- [ ] T013 [P] [US1] Implement "Control" condition interface in `code/experiment/app.py` (static AI display)
- [ ] T014 [US1] Implement adherence tracking logic in `code/experiment/app.py` (calculate % of AI recommendations followed)
- [ ] T015 [US1] Implement attention check questions and straight-lining detection in `code/experiment/app.py`
- [ ] T016 [US1] Implement Lee & See (2004) Trust Scale items in `code/experiment/app.py` survey section. Requirement: Must include the full 12-item scale covering dimensions of reliability, competence, and predictability (verbatim from source), not a subset. Use a 7-point Likert scale (1=Strongly Disagree, 7=Strongly Agree).
- [ ] T017 [US1] Implement data export logic to `data/raw/` with checksum generation and filename timestamping
- [ ] T018 [US1] Implement manipulation check question for "Perceived Agency" to validate the illusion of control

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to ensure they pass**

- [ ] T019 [P] [US1] Unit test for randomization logic in `code/experiment/tests/test_randomization.py` (verify condition distribution and seed stability)
- [ ] T020 [P] [US1] Integration test for session flow in `code/experiment/tests/test_session_flow.py` (verify data capture completeness)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (can run locally or on Streamlit Cloud for pilot)

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

**Goal**: Execute reproducible statistical analysis on collected data to test the directional hypothesis.

**Independent Test**: A script can run against a synthetic dataset to verify planned contrasts, post-hoc tests, and Cohen's d calculations.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement data cleaning pipeline in `code/analysis/data_cleaning.py` (handle missing values, flag attention check failures)
- [ ] T022 [US2] Implement One-Way ANOVA and Planned Directional Contrasts in `code/analysis/contrasts.py` (High vs. Low, (High+Low) vs. Control)
- [ ] T023 [US2] Implement Tukey HSD post-hoc tests in `code/analysis/pairwise.py` with family-wise error rate adjustment
- [ ] T024 [US2] Implement Cohen's d effect size calculation in `code/analysis/effect_sizes.py` for all pairwise comparisons
- [ ] T025 [US2] Create synthetic data generator in `code/analysis/synthetic_data.py` for testing the pipeline without real data
- [ ] T026 [US2] Integrate all analysis steps into a main runner script `code/analysis/run_analysis.py`
- [ ] T027 [US2] Analyze manipulation check data from T018 to verify the "illusory control" assumption (mean perceived agency score > 4.0 for High Agency condition). **Action**: Log a warning and flag the dataset in the report if the check fails; DO NOT halt the analysis pipeline. Proceed to calculate contrasts regardless of the outcome to report null findings or failed manipulations as scientific results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_output.py`
- [ ] T029 [P] [US2] Unit test for contrast calculation logic using synthetic data in `tests/unit/test_contrasts.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis can run on synthetic or real data)

---

## Phase 5: User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Generate reports including power analysis, multiple-comparison corrections, and sensitivity analysis.

**⚠️ CRITICAL**: Depends on Phase 4 (US2) completion. Tasks here require ANOVA and post-hoc results.

**Independent Test**: Review of generated report confirms power targets, error corrections, and threshold sweeps.

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py` (sweep participant exclusion threshold defined by attention check pass rate from 0.75 to 0.90 and re-run primary analysis to report stability of findings). **Include**: Post-hoc power calculation logic here to explicitly state limitations if N < target.
- [ ] T031 [US3] Implement final report generation in `code/analysis/report.py` (compile ANOVA, contrasts, post-hoc, effect sizes, pre-study power results from T002, and sensitivity analysis) to generate a Markdown report at `docs/report.md`.
- [ ] T032 [US3] Add null result handling logic in `code/analysis/report.py` (explicitly report null findings and observed effect sizes)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Update documentation in `docs/protocol.md` with pre-registered analysis plan
- [ ] T035 [P] Create GitHub Actions workflow in `.github/workflows/experiment.yml` to run analysis on `data/processed/`
- [ ] T036 Code cleanup and refactoring for type hints and docstrings
- [ ] T037 [P] Add validation scripts to verify `participant.schema.yaml` compliance against `data/raw/` exports
- [ ] T038 [P] Run quickstart.md validation and update instructions if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must be completed before data collection begins.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run on synthetic data independently of US1 completion, but requires US1 data schema.
- **User Story 3 (P3)**: Can start ONLY AFTER Phase 4 (US2) completion. Relies on US2 outputs (ANOVA, post-hoc) for sensitivity sweeps and post-hoc power.

### Within Each User Story

- Implementation MUST be written before tests (unless TDD explicitly requested)
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
# Launch interface implementations for User Story 1 together:
Task: "Implement High Agency condition interface in code/experiment/app.py"
Task: "Implement Low Agency condition interface in code/experiment/app.py"
Task: "Implement Control condition interface in code/experiment/app.py"

# Launch tests for User Story 1 together (after implementation):
Task: "Unit test for randomization logic in code/experiment/tests/test_randomization.py"
Task: "Integration test for session flow in code/experiment/tests/test_session_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research & Validation (Includes T002 Power Analysis)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (run pilot with synthetic or real participants)
6. Deploy experiment interface for recruitment

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy experiment interface (MVP!)
3. Add User Story 2 → Test on synthetic data → Ready for real data analysis
4. Add User Story 3 → Test robustness → Generate final report
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Experiment Interface)
 - Developer B: User Story 2 (Analysis Core)
 - Developer C: User Story 3 (Robustness & Reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Integrity**: Ensure `data/raw/` is never modified in-place. All cleaning must write to `data/processed/`.
- **Compute Feasibility**: All statistical tasks (ANOVA, contrasts, sensitivity) are CPU-tractable and fit within GitHub Actions free-tier limits.
- **Fabrication Guard**: Do NOT use `random.*` to generate input data for the analysis pipeline unless explicitly testing with synthetic data generators. Real analysis must use real CSV exports from `data/raw/`.
- **Gate Tasks**: T000 (Reference Validation) is a mandatory gate. T026 is now a reporting step, not a gate.