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

**⚠️ CRITICAL**: No implementation can begin until Phase 0 is complete. **Strict Sequence**: T000 -> T001a -> T001b -> T002 -> T001 -> T003 -> T008.
**Reasoning**: T000 validates citations. T001a verifies dataset schema fit. T001b generates literature review. T002 calculates power. T001 populates research.md. T003 validates. T008 configures environment.

- [X] T000 [Const-II] Implement and execute the citation validation pipeline in `code/research/validate_citations.py`. **Input**: Raw citation strings: "Lee & See (n.d.)", "Langer (n.d.)". **Logic**:
 1. Define function `fetch_doi(title: str) -> str | None` using Crossref API (`https://api.crossref.org/works?query.title={title}`).
 2. Define function `calculate_jaccard_similarity(set1: set, set2: set) -> float`.
 3. For each citation, extract title, fetch DOI, tokenize title and API result, calculate Jaccard similarity.
 4. **Content Verification**: If title overlap >= 0.7, fetch the metadata via Crossref. Verify the presence of keywords related to "Trust in Automation" or "12-item scale" in the title/author fields. If abstract is missing, proceed with title/author verification only.
 5. If overlap_score >= 0.7 AND content verification passes, mark status="valid"; else status="invalid".
 6. **Fallback**: If API fails or no DOI found, allow a "Manual Override" mode (log warning, require user confirmation in `research/validation_report.json`) to proceed, preventing a hard stop.
 **Output**: `research/validation_report.json` containing a list of objects with keys: `title` (string), `doi` (string), `overlap_score` (float), `content_verified` (boolean), `status` (string). **Execution**: Run script with `--citations "Lee & See (n.d.), Langer (n.d.)"`. **Dependency**: None.
- [ ] T001a [P] [Dataset Fit] Verify the self-collected dataset schema and variable definitions against the plan's 'Dataset Variable Fit' section. **Logic**: Read `plan.md` section 'Dataset Variable Fit'. Confirm all required variables (Condition ID, Adherence Rate, Trust Score, Perceived Agency Score, Attention Check Status) are defined in the plan. **Output**: `research/dataset_verification_report.md` stating "Verified" if all variables are present and defined. **Dependency**: T000.
- [ ] T001b [P] [Lit Review] Generate the literature review summary required by Plan.md Phase 0. **Logic**: Summarize key findings from "Lee & See (2004)" and "Langer (1975)" regarding trust and perceived control. **Output**: `research/literature_review.md`. **Dependency**: T000.
- [X] T002 [P] Execute pre-study power analysis calculation using Python `statsmodels`. **Script**: `code/research/power_analysis.py`. **Args**: **HARDCODED DESIGN PARAMETERS** for the initial run: `effect_size` (f=0.25, medium), `alpha` (0.05), `power` (0.80). **Logic**: Calculate the required sample size (N) for a One-Way ANOVA with multiple groups. **Output**: `research/power_calculation.json` (machine-readable data with keys `params` and `results`) AND `research/power_report.md` (formal report with sections: Method, Parameters, Result, Conclusion). **Dependency**: T001b.
- [ ] T001 [SC-002] Create and populate `research.md` template file at `specs/001-perceived-agency-trust/research.md`. **Schema**: Markdown table with exact columns: `| Effect Size | Alpha | Target Power | Required N | Calculated N |`. **Row Order**: 1) Effect Size, 2) Alpha, 3) Target Power, 4) Required N, 5) Calculated N. **Action**: Read `research/power_calculation.json` (from T002) specifically the keys `params.effect_size`, `params.alpha`, `params.power`, `results.required_n`, and `results.calculated_n` and populate the summary table in `research.md`. **Precondition**: Wait for T002 to complete and generate `research/power_calculation.json`. **Dependency**: T002.
- [ ] T003 [P] Validate `research.md` and `research/power_calculation.json` against `plan.md` Phase 0 requirements. **Dependency**: T001, T002.
- [X] T008 [P] Setup environment configuration management by creating `code/experiment/config.yaml`. **Structure**: YAML with keys: `sample_size` (read from `research/power_calculation.json` at key `results.required_n`), `alpha_level` (default 0.05), `seed` (default 42), `data_path` (default `data/raw/`). **Mechanism**: Python script to read JSON and write YAML. **Dependency**: T002.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T004 [P] Create project directory structure. **Command**: `mkdir -p code/experiment code/experiment/tests code/analysis code/analysis/tests data/raw data/processed docs specs/001-perceived-agency-trust/contracts`. **Files**: Create `__init__.py` in all `code/` subdirectories and `tests/` subdirectories.
- [X] T005 [P] Initialize Python project with pinned dependencies in `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pingouin, pytest).
- [X] T006 [P] Configure linting (flake8/black) and formatting tools. **Deliverables**: Create `.flake8` with specific rules (e.g., max-line-length=88) and `pyproject.toml` for black configuration. **Verification**: Run `black --check.` and ensure exit code 0.
- [ ] T009 [P] [FR-001] Create **Draft** data schema contracts in `specs/001-perceived-agency-trust/contracts/`. **Content**:
 1. `participant.schema.yaml`: Define fields: `participant_id` (string, UUID), `condition` (enum: High, Low, Control), `adherence_rate` (float, non-negative scale), `trust_score` (float, 1-5), `attention_check` (boolean). **CRITICAL**: Do NOT populate the `trust_item_1` to `trust_item_12` fields with text yet. Define them as `integer 1-5` with a placeholder description "To be populated by T011".
 2. `analysis_output.schema.yaml`: Define fields for ANOVA results, contrasts, and effect sizes.
 3. `power_analysis.schema.yaml`: Define fields for power analysis parameters and results.
 **Dependency**: T004. **Note**: This is a draft schema; final items are added in T012.
- [X] T010 [P] Create base data processing utilities in `code/analysis/data_utils.py`. **Functions**: `load_csv(path)`, `compute_checksum(path, algorithm="sha256")`, `scan_pii(df)`. **Logic**: Implement SHA-256 checksumming and PII scanning rules (e.g., flag columns with "email", "name"). **Dependency**: T004.
- [X] T011 [P] [SC-004] Create `docs/trust_scale_items.md` containing the verbatim 12-item Lee & See (2004) scale in **JSON array format**. **Items**: ["I trust this system", "I feel confident in this system", "I believe this system is reliable", "I feel this system is competent", "I feel this system is predictable", "I feel this system is safe", "I feel this system is honest", "I feel this system is benevolent", "I feel this system is capable", "I feel this system is useful", "I feel this system is accurate", "I feel this system is effective"]. **Requirement**: This file must match the validated citation in T000. **Dependency**: T000.
- [ ] T012 [P] Finalize data schema contracts in `specs/001-perceived-agency-trust/contracts/`. **Content**:
 1. Update `participant.schema.yaml` (from T009) to explicitly populate `trust_item_1` through `trust_item_12` with the verbatim text from `docs/trust_scale_items.md` (T011).
 2. Merge trust scale items into `participant.schema.yaml` explicitly.
 **Dependency**: T009, T011.
- [ ] T015 [P] [Plan Element] Produce experimental interface design specification in `docs/design/interface_design.md`. **Content**: Wireframes or UI flow diagram for High/Low/Control conditions. **Dependency**: T006.
- [ ] T016 [P] [Plan Element] Produce analysis pipeline specification in `docs/design/analysis_pipeline_spec.md`. **Content**: Algorithm flow, statistical test definitions, and data cleaning rules. **Dependency**: T006.
- [ ] T017h [P] [SC-004] Generate `quickstart.md` in `docs/`. **Content**: Step-by-step instructions for local setup, running the experiment interface, and executing the analysis pipeline. **Dependency**: T004, T017i, T012.
- [ ] T017i [P] [SC-004] Generate `data-model.md` in `docs/`. **Content**: Description of data entities (Participant, Condition, Result) and their relationships, referencing `contracts/`. **Dependency**: T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. **Note**: Ensure T012 is complete before proceeding to T024.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T018 [P] [FR-001] Implement randomization logic in `code/experiment/randomization.py` (assigns High/Low/Control with fixed seed for reproducibility). **Requirement**: Explicitly implement randomized assignment to ensure independent variable manipulation (FR-001). **Dependency**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Experimental Task Execution and Data Capture (Priority: P1) 🎯 MVP

**Goal**: Present the simulated decision-making task with randomized conditions and capture behavioral/psychometric data.

**Independent Test**: A test runner can simulate a participant session, verify randomization, confirm illusory controls don't alter AI output, and validate the survey export schema.

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement "High Agency" condition interface in `code/experiment/app.py` (functional sliders that do NOT alter AI output). **Dependency**: T018, T010.
- [ ] T020 [P] [US1] Implement "Low Agency" condition interface in `code/experiment/app.py` (restricted controls). **Dependency**: T018, T010.
- [ ] T021 [P] [US1] Implement "Control" condition interface in `code/experiment/app.py` (static AI display). **Dependency**: T018, T010.
- [ ] T022 [US1] [FR-002] Implement adherence tracking logic in `code/experiment/app.py`. **Requirement**: Capture behavioral adherence as a percentage. **Formula**: `The adherence rate is defined as the proportion of AI recommendations followed relative to the total number of recommendations, expressed as a percentage.`. **Variable**: `adherence_rate` (float). **Dependency**: T018, T010.
- [ ] T023 [US1] Implement attention check questions and straight-lining detection in `code/experiment/app.py`. **Questions**: Include standard attention checks. (e.g., "Select 'Strongly Agree'"). **Logic**: Flag if a consecutive sequence of responses is identical. **Output**: `attention_check_status` (boolean). **Dependency**: T018, T010.
- [ ] T024 [US1] [FR-002] [SC-004] Implement Lee & See (2004) Trust Scale items in `code/experiment/app.py` survey section. **Requirement**: Read verbatim 12-item scale from `docs/trust_scale_items.md` at runtime. **Format**: JSON array of strings. **Parsing**: Map items to `trust_item_1` through `trust_item_12`. **Action**: If file is missing or format is not JSON array, raise explicit error and halt execution. **Runtime Verification**: **CRITICAL**: Before rendering the UI, load the items from `docs/trust_scale_items.md` and compare them **exactly** (string equality) against the verified list in `research/trust_scale_verification_report.md` (from T007g). If the loaded items do NOT match the verified text exactly, **raise SystemExit(1) and block the experiment from starting**. If the verification report is missing, raise SystemExit(1) with message "Verification report missing: Run T007g first". This is a runtime gate for the *experiment execution*, not a build-time block for the *implementation* (which can be tested with mocks). **UI**: Use `st.radio` with `options=['Strongly Disagree', 'Disagree', 'Neutral', 'Agree', 'Strongly Agree']` mapping to 1-5 integers. **Variable Names**: `trust_item_1` through `trust_item_12`. **Dependency**: T018, T010, T011 artifact exists, T012 artifact exists.
- [ ] T025 [US1] Implement data export logic to `data/raw/` with checksum generation and filename timestamping. **Requirement**: Ensure export schema matches `participant.schema.yaml` (finalized in T012). **Dependency**: T018, T010, T024.
- [ ] T025b [US1] [SC-004] Implement runtime schema validation in `code/experiment/app.py` before data export. **Requirement**: Validate that the collected data strictly adheres to `participant.schema.yaml` (specifically the 12 trust items) before writing to `data/raw/`. **Action**: If validation fails, raise error and prevent export. **Dependency**: T025, T012.
- [ ] T026 [US1] Implement manipulation check question for "Perceived Agency". **Question**: "To what extent did you feel you had control over the AI's recommendations?" **Scale**: 1-7 Likert. **Variable**: `perceived_agency_score`. **Constraint**: This score is **ONLY** for descriptive analysis and reporting. It MUST NOT be used as a covariate, filter, or exclusion criterion for the primary trust outcome calculation to ensure Behavioral Outcome Isolation (Constitution VII). **Dependency**: T018, T010.

### Tests for User Story 1

- [ ] T027 [P] [US1] Unit test for randomization logic in `code/experiment/tests/test_randomization.py` (verify condition distribution and seed stability).
- [ ] T028 [P] [US1] Integration test for session flow in `code/experiment/tests/test_session_flow.py` (verify data capture completeness).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (can run locally or on Streamlit Cloud for pilot)

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

**Goal**: Execute reproducible statistical analysis on collected data to test the directional hypothesis.

**Independent Test**: A script can run against a synthetic dataset to verify planned contrasts, post-hoc tests, and Cohen's d calculations.

### Implementation for User Story 2

- [ ] T029 [P] [US2] Implement data cleaning pipeline in `code/analysis/data_cleaning.py` (handle missing values, flag attention check failures).
- [ ] T030 [US2] [FR-003] [SC-001] Implement One-Way ANOVA and **Planned Directional Contrasts** in `code/analysis/contrasts.py`. **Requirement**: Explicitly implement orthogonal contrast vectors with coefficients:) High vs. Low (coefficients: [1, -1, 0]), 2) (High+Low) vs. Control (coefficients: [1, 1, -2]). **Library**: Use `pingouin.anova` or `statsmodels`. **Output**: Summary tables with t-statistics, p-values, degrees of freedom. **Dependency**: T029.
- [ ] T031 [US2] [FR-005] [SC-005] Implement Tukey HSD post-hoc tests in `code/analysis/pairwise.py` with family-wise error rate adjustment. **Requirement**: Explicitly state 'family-wise error rate adjustment' in output. **Dependency**: T030.
- [ ] T032 [US2] [FR-004] Implement Cohen's d effect size calculation in `code/analysis/effect_sizes.py` for all pairwise comparisons. **Requirement**: Explicitly compute for all pairwise comparisons. **Dependency**: T031.
- [ ] T033 [US2] Create synthetic data generator in `code/analysis/synthetic_data.py` for testing the pipeline without real data.
- [ ] T034 [US2] Integrate all analysis steps into a main runner script `code/analysis/run_analysis.py`.
- [ ] T035 [US2] Analyze manipulation check data from T026 and calculate achieved power. **Logic**: Calculate mean perceived agency score. **Test**: One-sample t-test against a predetermined threshold. **Power Check**: Read `target_n` from `research/power_calculation.json` (produced by T002). Compare `len(df)` against `target_n`. **Output**: Write `manipulation_check_status` ("valid"/"invalid"), `mean_score`, `achieved_power`, and `power_status` ("sufficient"/"insufficient") to `results/power_status.json`. **Constraint**: If `len(df) < target_n` OR manipulation check invalid, set `power_status`="insufficient" and write "Limitation: Insufficient Power" to the JSON. **DO NOT halt the pipeline** or report a null result here; simply flag the status for the report generator. **Dependency**: T026, T002.

### Tests for User Story 2

- [ ] T036 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_output.py`.
- [ ] T037 [P] [US2] Unit test for contrast calculation logic using synthetic data in `tests/unit/test_contrasts.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Analysis can run on synthetic or real data)

---

## Phase 5: User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Generate reports including power analysis, multiple-comparison corrections, and sensitivity analysis.

**⚠️ CRITICAL**: Depends on Phase 4 (US2) completion. Tasks here require ANOVA and post-hoc results.

**Independent Test**: Review of generated report confirms power targets, error corrections, and threshold sweeps.

### Implementation for User Story 3

- [ ] T038 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`. **Requirement**: Sweep **participant exclusion thresholds** including: 1) Attention check pass rate (range 0.75 to 0.90). **Note**: Straight-lining is excluded from the primary sweep to align with FR-006. **Output**: CSV table with columns `threshold_type`, `threshold_value`, `p_value_primary`, `effect_size_primary`. **Dependency**: Must run after Phase 4 (T030, T031) completes.
- [ ] T038b [US3] [Optional] Implement straight-lining sensitivity analysis in `code/analysis/sensitivity_straightline.py`. **Requirement**: Sweep straight-lining thresholds (e.g., max consecutive identical responses) as an optional robustness check. **Dependency**: Phase 4.
- [ ] T039 [US3] Implement final report generation in `code/analysis/report.py`. **Requirement**: Compile ANOVA, contrasts, post-hoc, effect sizes, pre-study power results from T002 (`research/power_report.md`), and sensitivity analysis. **Power Limitation Handling**: Read `results/power_status.json` (from T035). If `power_status` is "insufficient", explicitly append a "Limitations" section to `docs/report.md` stating "Limitation: Insufficient Power" and detailing the achieved power vs target. **Output**: Markdown report at `docs/report.md`. **Dependency**: Must wait for T002 (Power Analysis), Phase 4 completion, T038 (Sensitivity analysis), and T035 (Power Status).
- [ ] T040 [US3] Add null result handling logic in `code/analysis/report.py` (explicitly report null findings and observed effect sizes).

### Tests for User Story 3

- [ ] T041 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update documentation in `docs/protocol.md` with pre-registered analysis plan. **Requirement**: Explicitly reference FR-006, US-3, and the specific sensitivity sweep parameters defined in T038.
- [ ] T043 [P] Create GitHub Actions workflow in `.github/workflows/experiment.yml` to run analysis on `data/processed/`.
- [ ] T044 [P] Code cleanup and refactoring for type hints and docstrings. **Scope**: All `.py` files. **Style**: Google style guide. **Verification**: Run `pyright` and ensure 0 errors.
- [ ] T045 [P] Add validation scripts to verify `participant.schema.yaml` compliance against `data/raw/` exports.
- [ ] T046 [P] Run quickstart.md validation and update instructions if needed. **Validation**: Execute `./quickstart.sh` (or equivalent) and verify exit code 0. **Update**: Modify instructions if steps fail.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: T000 -> T001a -> T001b -> T002 -> T001 -> T003 -> T008. **Note**: T002 must complete before T001 and T008. T001 depends on T002. T001a and T001b are merged into T001.
- **Setup (Phase 1)**: Depends on Phase 0 completion. Tasks T009, T010, T011, T012, T015, T016 can run in parallel as they depend only on T004 and T000/T011 where applicable.
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

1. Complete Phase 0: Research & Validation (Includes T0.80 Power Analysis).
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
- **Gate Tasks**: T000 (Reference Validation) is a mandatory gate. T034 is now a reporting step, not a gate.
- **Critical Dependencies**: T002 must complete before T001. T008 depends on T002. T024 depends on T011 artifact exists. T035 depends on T026 and T002. T038 depends on Phase 4. T039 depends on T002, Phase 4, and T038.