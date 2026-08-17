# Tasks: The Influence of Perceived Agency in AI Interactions on Trust

**Input**: Design documents from `specs/001-perceived-agency-trust/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are **REQUIRED** to ensure reproducibility and validation.

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

## Phase 0: Research & Validation (Prerequisites)

**Purpose**: Verify citations, execute power analysis, and generate research artifacts before implementation begins.

**⚠️ CRITICAL**: No implementation can begin until Phase 0 is complete. Tasks MUST run in strict sequence: T000 -> T000b -> T000c -> (T001a, T002 in parallel) -> T001b -> T003 -> T008.

- [ ] T000 [P] [FR-001] [SC-004] Implement and execute the citation validation pipeline in `code/research/validate_citations.py`. **Input**: Raw citation strings sourced from `spec.md` and `plan.md` (e.g., "Lee & See (2004)", "Langer (1975)"). **Logic**: 
  1. Define function `fetch_doi(title: str) -> str | None` using Crossref API (`https://api.crossref.org/works?query.title={title}`).
  2. Define function `calculate_jaccard_similarity(set1: set, set2: set) -> float`.
  3. For each citation, extract title, fetch DOI, tokenize title and API result, calculate Jaccard similarity.
  4. If overlap_score >= 0.7, mark status="valid"; else status="invalid".
  5. If API fails or no DOI found, raise explicit `RuntimeError` (NO synthetic fallback).
  **Output**: `research/validation_report.json` containing a list of objects with keys: `title` (string), `doi` (string), `overlap_score` (float), `status` (string). **Execution**: Run script with `--citations "Lee & See (2004), Langer (1975)"`. **Dependency**: None.
- [X] T000b Execute `code/research/validate_citations.py` with arguments `--citations "Lee & See (2004), Langer (1975)"`. **Output**: `research/validation_report.json` containing status for each citation. **Dependency**: T000.
- [ ] T000c Parse `research/validation_report.json` and verify all citations are valid. **Logic**: Check that `overlap_score >= 0.7` for all entries. **Action**: If any fail, log error to `research/citation_verification_log.md`. **Deliverable**: `research/citation_verification_log.md` with status="valid" if all pass. **Dependency**: T000b.
- [ ] T001a Create the `research.md` template file at `specs/001-perceived-agency-trust/research.md`. **Schema**: Markdown table with exact columns: `| Effect Size | Alpha | Target Power | Required N | Calculated N |`. **Row Order**: 1) Effect Size, 2) Alpha, 3) Target Power, 4) Required N, 5) Calculated N. **Action**: Ensure exact column headers are present. **Dependency**: T000c.
- [X] T002 Execute pre-study power analysis calculation using Python `statsmodels`. **Script**: `code/research/power_analysis.py`. **Args**: Read `effect_size` (0.25), `alpha` (0.05), `power` (0.80) from `research/power_calculation.json` or config (NOT hardcoded). **Output**: `research/power_calculation.json` (machine-readable data) AND `research/power_report.md` (formal report with sections: Method, Parameters, Result, Conclusion). **Dependency**: T000c.
- [ ] T001b Populate `specs/001-perceived-agency-trust/research.md` with literature review findings and power analysis targets. **Input**: `research/validation_report.json`, `research/citation_verification_log.md`, and `research/power_calculation.json`. **Action**: Read `research/power_calculation.json` and populate the summary table in `research.md` with the calculated values. **Dependency**: T000c, T001a, T002.
- [ ] T003 Validate `research.md` and `research/power_calculation.json` against `plan.md` Phase 0 requirements. **Dependency**: T001b.
- [ ] T008 Setup environment configuration management by creating `code/experiment/config.yaml`. **Structure**: YAML with keys: `sample_size` (read from `research/power_calculation.json` at key `results.sample_size`), `alpha_level` (default 0.05), `seed` (default 42), `data_path` (default `data/raw/`). **Mechanism**: Python script to read JSON and write YAML. **Dependency**: T002.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004 Create project directory structure. **Command**: `mkdir -p code/experiment code/experiment/tests code/analysis code/analysis/tests data/raw data/processed docs specs/001-perceived-agency-trust/contracts`. **Files**: Create `__init__.py` in all `code/` subdirectories and `tests/` subdirectories.
- [X] T005 [P] Initialize Python project with pinned dependencies in `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pingouin, pytest).
- [ ] T006 [P] Configure linting (flake8/black) and formatting tools. **Deliverables**: Create `.flake8` with specific rules (e.g., max-line-length=88) and `pyproject.toml` for black configuration. **Verification**: Run `black --check.` and ensure exit code 0.
- [ ] T007a Create data schema contracts for `participant.schema.yaml` in `specs/001-perceived-agency-trust/contracts/`. **Content**: Define fields: `participant_id` (string, UUID), `condition` (enum: High, Low, Control), `adherence_rate` (float, 0-100), `trust_score` (float, 1-5), `attention_check` (boolean). **Dependency**: T004.
- [ ] T007b Create data schema contracts for `analysis_output.schema.yaml` in `specs/001-perceived-agency-trust/contracts/`. **Content**: Define fields for ANOVA results, contrasts, and effect sizes. **Dependency**: T004.
- [ ] T007c Create data schema contracts for `power_analysis.schema.yaml` in `specs/001-perceived-agency-trust/contracts/`. **Content**: Define fields for power analysis parameters and results. **Dependency**: T004.
- [ ] T007d Define the Trust Scale schema in `specs/001-perceived-agency-trust/contracts/participant.schema.yaml`. **Requirement**: Define schema structure (keys: `trust_item_1` to `trust_item_12`, type: integer 1-5, minimum: 1, maximum: 5). **Action**: Append to existing schema from T007a using YAML merge keys. **Dependency**: T007a.
- [ ] T007e Create `docs/trust_scale_items.md` containing the verbatim 12-item Lee & See (2004) scale. **Items**: 1) I trust this system, 2) I feel confident in this system, 3) I believe this system is reliable, 4) I feel this system is competent, 5) I feel this system is predictable, 6) I feel this system is safe, 7) I feel this system is honest, 8) I feel this system is benevolent, 9) I feel this system is capable, 10) I feel this system is useful, 11) I feel this system is accurate, 12) I feel this system is effective. Use a Likert scale ranging from Strongly Disagree to Strongly Agree. **Dependency**: T000c (citation validation).
- [ ] T007f Map the 12-item Lee & See (2004) scale from `docs/trust_scale_items.md` to `participant.schema.yaml`. **Action**: Explicitly list the 12 items in the schema description or a companion file. **Dependency**: T007e, T007d.
- [ ] T007g Perform explicit verification of the Trust Scale items against the source instrument. **Script**: `code/research/verify_trust_scale.py`. **Input**: `docs/trust_scale_items.md` (from T007e) and `research/validation_report.json`. **Output**: `research/trust_scale_verification_report.md` with status="verified" if items match. **Action**: If verification fails, exit with code 1 (Hard Stop) to block downstream tasks. **Dependency**: T007f, T007e.
- [ ] T007h Generate `quickstart.md` in `docs/`. **Content**: Step-by-step instructions for local setup, running the experiment interface, and executing the analysis pipeline. **Dependency**: T004, T007i, T007g.
- [ ] T007i Generate `data-model.md` in `docs/`. **Content**: Description of data entities (Participant, Condition, Result) and their relationships, referencing `contracts/`. **Dependency**: T007a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] [FR-001] [SC-001] Implement randomization logic in `code/experiment/randomization.py` (assigns High/Low/Control with fixed seed for reproducibility). **Requirement**: Explicitly implement randomized assignment to ensure independent variable manipulation (FR-001) for the primary outcome test (SC-001). **Dependency**: T004.
- [ ] T010 [P] Create base data processing utilities in `code/analysis/data_utils.py`. **Functions**: `load_csv(path)`, `compute_checksum(path, algorithm="sha256")`, `scan_pii(df)`. **Logic**: Implement SHA-256 checksumming and PII scanning rules (e.g., flag columns with "email", "name"). **Dependency**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. **Note**: Ensure T007g is complete before proceeding to T016.

---

## Phase 3: User Story 1 - Experimental Task Execution and Data Capture (Priority: P1) 🎯 MVP

**Goal**: Present the simulated decision-making task with randomized conditions and capture behavioral/psychometric data.

**Independent Test**: A test runner can simulate a participant session, verify randomization, confirm illusory controls don't alter AI output, and validate the survey export schema.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement "High Agency" condition interface in `code/experiment/app.py` (functional sliders that do NOT alter AI output). **Dependency**: T009, T010.
- [ ] T012 [P] [US1] Implement "Low Agency" condition interface in `code/experiment/app.py` (restricted controls). **Dependency**: T009, T010.
- [ ] T013 [P] [US1] Implement "Control" condition interface in `code/experiment/app.py` (static AI display). **Dependency**: T009, T010.
- [ ] T014 [US1] [FR-002] Implement adherence tracking logic in `code/experiment/app.py`. **Requirement**: Capture behavioral adherence as a percentage. **Formula**: `adherence_rate = (number_of_ai_recommendations_followed / total_recommendations) * 100`. **Variable**: `adherence_rate` (float). **Dependency**: T009, T010.
- [ ] T015 [US1] Implement attention check questions and straight-lining detection in `code/experiment/app.py`. **Questions**: Include standard attention checks. (e.g., "Select 'Strongly Agree'"). **Logic**: Flag if a consecutive sequence of responses is identical. **Output**: `attention_check_status` (boolean). **Dependency**: T009, T010.
- [ ] T016 [US1] [FR-002] [SC-004] Implement Lee & See (2004) Trust Scale items in `code/experiment/app.py` survey section. **Requirement**: Read verbatim 12-item scale from `docs/trust_scale_items.md` at runtime. **Format**: JSON array of strings. **Parsing**: Map items to `trust_item_1` through `trust_item_12`. **Action**: If file is missing, raise explicit error and halt execution. **UI**: Use `st.radio` with `options=['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']` mapping to 1-5 integers. **Variable Names**: `trust_item_1` through `trust_item_12`. **Dependency**: Must run after T007g completes.
- [ ] T017 [US1] Implement data export logic to `data/raw/` with checksum generation and filename timestamping. **Dependency**: T009, T010.
- [ ] T018 [US1] Implement manipulation check question for "Perceived Agency". **Question**: "To what extent did you feel you had control over the AI's recommendations?" **Scale**: 1-7 Likert. **Variable**: `perceived_agency_score`. **Dependency**: T009, T010.

### Tests for User Story 1

- [ ] T019 [P] [US1] Unit test for randomization logic in `code/experiment/tests/test_randomization.py` (verify condition distribution and seed stability).
- [ ] T020 [P] [US1] Integration test for session flow in `code/experiment/tests/test_session_flow.py` (verify data capture completeness).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (can run locally or on Streamlit Cloud for pilot)

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

**Goal**: Execute reproducible statistical analysis on collected data to test the directional hypothesis.

**Independent Test**: A script can run against a synthetic dataset to verify planned contrasts, post-hoc tests, and Cohen's d calculations.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement data cleaning pipeline in `code/analysis/data_cleaning.py` (handle missing values, flag attention check failures).
- [ ] T022 [US2] [FR-003] [SC-001] Implement One-Way ANOVA and **Planned Directional Contrasts** in `code/analysis/contrasts.py`. **Requirement**: Explicitly implement orthogonal contrast vectors with coefficients:) High vs. Low (coefficients: [1, -1, 0]), 2) (High+Low) vs. Control (coefficients: [1, 1, -2]). **Library**: Use `pingouin.anova` or `statsmodels`. **Output**: Summary tables with t-statistics, p-values, degrees of freedom. **Dependency**: T021.
- [ ] T023 [US2] [FR-005] [SC-005] Implement Tukey HSD post-hoc tests in `code/analysis/pairwise.py` with family-wise error rate adjustment. **Requirement**: Explicitly state 'family-wise error rate adjustment' in output. **Dependency**: T022.
- [ ] T024 [US2] [FR-004] Implement Cohen's d effect size calculation in `code/analysis/effect_sizes.py` for all pairwise comparisons. **Requirement**: Explicitly compute for all pairwise comparisons. **Dependency**: T023.
- [ ] T025 [US2] Create synthetic data generator in `code/analysis/synthetic_data.py` for testing the pipeline without real data.
- [ ] T026 [US2] Integrate all analysis steps into a main runner script `code/analysis/run_analysis.py`.
- [ ] T027 [US2] Analyze manipulation check data from T018. **Logic**: Calculate mean perceived agency score. **Test**: One-sample t-test against a predetermined threshold. **Output**: Write `manipulation_check_status` ("valid"/"invalid"), `mean_score`, and `achieved_power` to the final report JSON. **Power Analysis**: Check sample size against target from T002 (`research/power_calculation.json`). **If** sample size < target OR manipulation check invalid, calculate achieved power for the *primary trust outcome* using `statsmodels.stats.power.FTestAnovaPower` and report null result. **DO NOT halt the pipeline.** **Dependency**: T018, T002.

### Tests for User Story 2

- [ ] T028 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_output.py`.
- [ ] T029 [P] [US2] Unit test for contrast calculation logic using synthetic data in `tests/unit/test_contrasts.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis can run on synthetic or real data)

---

## Phase 5: User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Generate reports including power analysis, multiple-comparison corrections, and sensitivity analysis.

**⚠️ CRITICAL**: Depends on Phase 4 (US2) completion. Tasks here require ANOVA and post-hoc results.

**Independent Test**: Review of generated report confirms power targets, error corrections, and threshold sweeps.

### Implementation for User Story 3

- [ ] T030 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`. **Requirement**: Sweep participant exclusion thresholds for attention check pass rate (range lower bound to a high threshold, step 0.05), straight-lining thresholds, AND completion time outliers. **Output**: CSV table with columns `threshold_type`, `threshold_value`, `p_value_primary`, `effect_size_primary`. **Dependency**: Must run after Phase 4 (T022, T023) completes.
- [ ] T031 [US3] Implement final report generation in `code/analysis/report.py`. **Requirement**: Compile ANOVA, contrasts, post-hoc, effect sizes, pre-study power results from T002 (`research/power_report.md`), and sensitivity analysis. **Dependency**: Must wait for T002 (Power Analysis), Phase 4 completion, and T030 (Sensitivity analysis). **Output**: Markdown report at `docs/report.md`.
- [ ] T032 [US3] Add null result handling logic in `code/analysis/report.py` (explicitly report null findings and observed effect sizes).

### Tests for User Story 3

- [ ] T033 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Update documentation in `docs/protocol.md` with pre-registered analysis plan. **Requirement**: Explicitly reference FR-006, US-3, and the specific sensitivity sweep parameters defined in T030.
- [ ] T035 [P] Create GitHub Actions workflow in `.github/workflows/experiment.yml` to run analysis on `data/processed/`.
- [ ] T036 [P] Code cleanup and refactoring for type hints and docstrings. **Scope**: All `.py` files. **Style**: Google style guide. **Verification**: Run `pyright` and ensure 0 errors.
- [ ] T037 [P] Add validation scripts to verify `participant.schema.yaml` compliance against `data/raw/` exports.
- [ ] T038 [P] Run quickstart.md validation and update instructions if needed. **Validation**: Execute `./quickstart.sh` (or equivalent) and verify exit code 0. **Update**: Modify instructions if steps fail.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: T000 -> T000b -> T000c -> (T001a, T002 in parallel) -> T001b -> T003 -> T008. **Note**: T002 must complete before T001b and T008. T001a is independent of T002.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed).
 - Or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must be completed before data collection begins.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run on synthetic data independently of US1 completion, but requires US1 data schema.
- **User Story 3 (P3)**: Can start ONLY AFTER Phase 4 (US2) completion. Relies on US2 outputs (ANOVA, post-hoc) for sensitivity sweeps and post-hoc power.

### Within Each User Story

- Implementation MUST be written before tests (unless TDD explicitly requested).
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

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

1. Complete Phase 0: Research & Validation (Includes T002 Power Analysis).
2. Complete Phase 1: Setup.
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
4. Complete Phase 3: User Story 1.
5. **STOP and VALIDATE**: Test User Story 1 independently (run pilot with synthetic or real participants).
6. Deploy experiment interface for recruitment.

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy experiment interface (MVP!).
3. Add User Story 2 → Test on synthetic data → Ready for real data analysis.
4. Add User Story 3 → Test robustness → Generate final report.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Experiment Interface).
 - Developer B: User Story 2 (Analysis Core).
 - Developer C: User Story 3 (Robustness & Reporting).
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps task to specific user story for traceability.
- Each user story should be independently completable and testable.
- Commit after each task or logical group.
- Stop at any checkpoint to validate story independently.
- **Data Integrity**: Ensure `data/raw/` is never modified in-place. All cleaning must write to `data/processed/`.
- **Compute Feasibility**: All statistical tasks (ANOVA, contrasts, sensitivity) are CPU-tractable and fit within GitHub Actions free-tier limits.
- **Fabrication Guard**: Do NOT use `random.*` to generate input data for the analysis pipeline unless explicitly testing with synthetic data generators. Real analysis must use real CSV exports from `data/raw/`.
- **Gate Tasks**: T000 (Reference Validation) is a mandatory gate. T026 is now a reporting step, not a gate.
- **Critical Dependencies**: T002 must complete before T001b. T008 depends on T002. T016 depends on T007g. T027 depends on T018 and T002. T030 depends on Phase 4. T031 depends on T002, Phase 4, and T030.
