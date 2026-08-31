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

---

## Pre-Phase 0: Validation Gates (MANDATORY)

**Purpose**: Verify citations and scale text against primary sources BEFORE any implementation begins.
**⚠️ CRITICAL**: If T000 or T000b fail, the project transitions to `human_input_needed` immediately. No downstream tasks can run.

- [ ] T000 [Const-II] **Gate**: Validate citation metadata (Title & DOI) against primary source via CrossRef API.  
  **Input**: `spec.md` and `plan.md`.  
  **Logic**:  
  1. Parse `spec.md` and `plan.md` to extract claimed citations (e.g., "Lee & See (2004)", "Langer (1975)").  
  2. For each citation, infer the DOI if not explicitly provided (e.g., map "Lee & See (2004)" to known DOI `10.1037/1089-3806.13.1.76` OR search CrossRef if unknown).  
  3. Use `requests` to call `https://api.crossref.org/works/{DOI}` and fetch metadata.  
  4. Compute a string overlap score between fetched `title` and claimed title using `difflib.SequenceMatcher`.  
  5. If any overlap < 0.7 or DOI lookup fails (404), raise `SystemExit(1)` with message **"Citation Validation Failed"**.  
  **Output**: `research/validation_report.json` containing for each citation: `title`, `doi`, `overlap_score`, `content_verified`, `status`, `source_url`.  
  **Dependency**: None.

- [ ] T000b [Const-II] **Gate**: Validate the *structure* of the Lee & See (2004) trust scale against the primary source.  
  **Input**: `spec.md` (to locate the citation) and CrossRef API.  
  **Logic**:  
  1. Resolve DOI for Lee & See (2004) (`10.1037/1089-3806.13.1.76`).  
  2. Fetch metadata via CrossRef; verify that the abstract/keywords indicate a **12‑item Likert scale** (search for terms like "12 items", "Likert", "trust in automation").  
  3. **DO NOT** hardcode item text. The task only confirms the existence and format of the scale.  
  4. If the metadata does not support a 12‑item Likert structure, raise `SystemExit(1)` with message **"Scale structure mismatch"**.  
  **Output**: `research/scale_text_validation.json` containing: `status`, `structure_verified`, `source_url`.  
  **Dependency**: T000.

---

## Phase 0: Research & Validation (Prerequisites)

**Purpose**: Verify citations, execute power analysis, generate protocol, and create research artifacts before implementation begins.

**Strict Sequence**: T000 -> T000b -> T001a-1 -> T001a-2 -> T001b-1 -> T001b-2 -> T002 -> T042 -> T008 -> T010b -> T011 -> T007g.  
**Reasoning**: T001a-1 parses plan schema. T001a-2 verifies plan intent. T001b-1 extracts citations. T001b-2 writes lit review. T002 calculates power. T042 generates the pre‑registered protocol (now in Phase 0). T008 configures environment using T042. T010b/T011/T007g verify the trust scale.

- [ ] T001a-1 [P] [Dataset Fit] Parse `plan.md` to locate the 'Technical Context' and 'Project Structure' sections.  
  **Logic**:  
  1. Use the `mistune` markdown parser to parse `plan.md`.  
  2. Extract the content under headings `## Technical Context` and `## Project Structure`.  
  3. Search within those blocks for variable definitions using a **robust regex** that matches the variable names `(Condition ID|Adherence Rate|Trust Score|Perceived Agency Score|Attention Check Status)`.  
  4. If no matches are found, raise a clear `RuntimeError` indicating the missing variables.  
  **Output**: `research/dataset_schema_parsed.txt` containing the extracted text.  
  **Dependency**: T000b.

- [ ] T001a-2 [P] [Dataset Fit] Verify the *plan's intent* to capture required variables and generate the report.  
  **Logic**:  
  1. Read `research/dataset_schema_parsed.txt` (from T001a-1) and `spec.md`.  
  2. Confirm that FR‑002 and US‑1 explicitly mandate capture of the identified variables.  
  3. Write `research/dataset_verification_report.md` with a clear "Verified" status; abort with `SystemExit(1)` if any required variable is missing.  
  **Output**: `research/dataset_verification_report.md`.  
  **Dependency**: T001a-1.

- [ ] T001b-1 [P] [Lit Review] Extract citation metadata and content from `research/validation_report.json` (T000) for "Lee & See (2004)" and "Langer (1975)".  
  **Logic**: If `source_url` is present, fetch the abstract/findings; otherwise use the `content_verified` summary from the validator.  
  **Output**: `research/citation_metadata.json` containing `title`, `doi`, `summary_findings`.  
  **Dependency**: T000b.

- [ ] T001b-2 [P] [Lit Review] Generate the literature review summary required by Plan.md Phase 0.  
  **Logic**: Summarize key findings from the two citations using `summary_findings` from T001b-1.  
  **Output**: `research/literature_review.md`.  
  **Dependency**: T001b-1.

- [X] T002 [P] Execute pre‑study power analysis calculation for **planned directional contrasts** AND **overall ANOVA** using Python `scipy` and `numpy`.  
  **Script**: `code/research/power_analysis.py`.  
  **Args**: Hard‑coded design parameters: `effect_size` (f=0.25), `alpha` (0.05), `power` (0.80).  
  **Implementation**: (code omitted for brevity – see original).  
  **Output**: `research/power_calculation.json` (machine‑readable with keys `params` and `results`).  
  **Dependency**: T000b, T001a-1.

- [ ] T042 [P] [FR-006] Generate `docs/protocol.md` with pre‑registered analysis plan.  
  **Requirement**: Reference FR‑006, US‑3, and the specific sensitivity sweep parameters.  
  **Logic**:  
  1. Define sensitivity sweep ranges (see T008 for exact values).  
  2. Write these ranges and the full pre‑registered analysis steps to `docs/protocol.md`.  
  **Output**: `docs/protocol.md`.  
  **Dependency**: T002.

- [ ] T008 [P] Setup environment configuration management by creating `code/analysis/config.yaml`.  
  **Structure**: YAML with keys: `sample_size` (read from `research/power_calculation.json` → `results.final_n`), `alpha_level` (0.05), `seed` (42), `data_path` (`data/raw/`), `sensitivity_config` (object containing sweep ranges).  
  **Logic**:  
  1. Read sensitivity sweep ranges defined in `docs/protocol.md` (generated by T042).  
  2. Populate `sensitivity_config` in `config.yaml` **exactly** matching those ranges.  
  **Output**: `code/analysis/config.yaml`.  
  **Dependency**: T042.

- [ ] T003-1 [P] Validate `research/literature_review.md` and `research/power_calculation.json` against `plan.md` Phase 0 requirements.  
  **Logic**: Assert presence of required sections and keys.  
  **Dependency**: T002, T001a-2, T001b-2, T042.

- [ ] T010b [P] [SC-004] Retrieve the canonical Lee & See (2004) Trust Scale.  
  **Logic**:  
  1. Verify `research/scale_text_validation.json` (from T000b) confirms structure validity.  
  2. Human researcher must manually copy the exact 12 items from the primary source into `docs/trust_scale_items.md` as a JSON array.  
  3. If the file is missing or malformed, raise `SystemExit(1)`.  
  **Output**: `docs/trust_scale_items.md`.  
  **Dependency**: T000b.

- [X] T011 [P] [SC-004] Verify `docs/trust_scale_items.md` matches the validated text.  
  **Logic**: Compare the JSON array against the reference list obtained during manual verification (recorded in `research/trust_scale_verification_report.md`).  
  **Output**: Pass/Fail log.  
  **Dependency**: T010b.

- [ ] T007g [P] [SC-004] Generate `research/trust_scale_verification_report.md`.  
  **Logic**: Read `research/scale_text_validation.json`; extract items from `docs/trust_scale_items.md`; confirm exact match; write report.  
  **Output**: `research/trust_scale_verification_report.md`.  
  **Dependency**: T010b, T011, T000b.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

**Strict Sequence**: T004 -> (T005, T006, T010) parallel -> T009 -> T012 -> T017i -> T017h -> T015 -> T016.  
**Note**: All tasks below depend only on directory creation (T004) unless otherwise noted.

- [ ] T004 [P] Create project directory structure. `mkdir -p code/experiment code/experiment/tests code/analysis code/analysis/tests data/raw data/processed docs specs/001-perceived-agency-trust/contracts`. Add `__init__.py` in all `code/` subdirectories and `tests/` subdirectories.

- [ ] T005 [P] Initialize Python project with pinned dependencies in `requirements.txt` (streamlit, pandas, numpy, scipy, statsmodels, pingouin, pytest, requests, pyyaml, jsonschema).

- [ ] T006 [P] Configure linting (flake8/black). Create `.flake8` and `pyproject.toml` for black. Verify with `black --check`.

- [ ] T010 [P] Create base data processing utilities in `code/analysis/data_utils.py`. Functions: `load_csv`, `compute_checksum`, `scan_pii`. Implements SHA‑256 checksumming and PII flagging.

- [ ] T009 [P] [FR-001] Create **final** data schema contracts in `specs/001-perceived-agency-trust/contracts/`.  
  **Content**:  
  1. `participant.schema.yaml` defines fields: `participant_id` (string, UUID), `condition` (enum: High, Low, Control), `adherence_rate` (float, 0‑100), `trust_score` (float, 1‑5), `attention_check` (boolean), `perceived_agency_score` (float, 1‑7, manipulation check only).  
  2. Defines `trust_item_1` … `trust_item_12` as **static keys** of type `string` (they will hold the respondent's chosen Likert label, not the question text). The actual question wording lives in `docs/trust_scale_items.md`.  
  3. `analysis_output.schema.yaml` and `power_analysis.schema.yaml` as per spec.  
  **Dependency**: T004, T010b, T011.

- [ ] T012 [P] [SC-004] Finalize data schema contracts. Ensure `participant.schema.yaml` matches description in T009 and documents `perceived_agency_score` as manipulation check only.  
  **Dependency**: T009.

- [ ] T017i [P] [SC-004] Generate `docs/data-model.md` describing entities (Participant, Condition, Result) and referencing contracts.

- [ ] T017h [P] [SC-004] Generate `docs/quickstart.md` with step‑by‑step local setup instructions.

- [ ] T015 [P] Produce experimental interface design specification in `docs/design/interface_design.md` (wireframes via Mermaid). Reference FR‑001 and US‑1.

- [ ] T016 [P] Produce analysis pipeline specification in `docs/design/analysis_pipeline_spec.md`. Include algorithm flow, statistical test definitions, data cleaning rules. Reference US‑2 and US‑3.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T018 [P] [FR-001] Implement randomization logic in `code/experiment/randomization.py` (assign High/Low/Control with fixed seed).  
  **Dependency**: T004.

---

## Phase 3: User Story 1 - Experimental Task Execution and Data Capture (Priority: P1) 🎯 MVP

**Goal**: Present the simulated decision‑making task with randomized conditions and capture behavioral/psychometric data.

- [ ] T019 [P] [US1] Implement "High Agency" condition interface in `code/experiment/app.py` (functional sliders that do NOT alter AI output).  
  **Dependency**: T018, T010.

- [ ] T020 [P] [US1] Implement "Low Agency" condition interface in `code/experiment/app.py` (restricted controls).  
  **Dependency**: T018, T010.

- [ ] T021 [P] [US1] Implement "Control" condition interface in `code/experiment/app.py` (static AI display).  
  **Dependency**: T018, T010.

- [ ] T022 [US1] [FR-002] Implement adherence tracking logic in `code/experiment/app.py`.  
  **Requirement**: Capture behavioral adherence as a percentage.  
  **Formula**: `adherence_rate = (followed_recommendations / total_recommendations) * 100`.  
  **Dependency**: T018, T010.

- [ ] T023 [US1] Implement attention check questions and straight‑lining detection in `code/experiment/app.py`. Include standard attention checks; flag if consecutive identical responses exceed a threshold. Output `attention_check_status` (boolean).  
  **Dependency**: T018, T010.

- [ ] T024 [US1] [FR-002] [SC-004] Implement Lee & See (2004) Trust Scale items in `code/experiment/app.py` survey section.  
  **Requirement**: Load verbatim 12‑item array from `docs/trust_scale_items.md` at runtime. Map items to `trust_item_1` … `trust_item_12`. Use `st.radio` with five Likert options (1‑5).  
  **Dependency**: T018, T010, T010b, T011, T000b.

- [ ] T024b [US1] [FR-002] Runtime verification gate for Trust Scale.  
  **Logic**: Before the experiment starts, load `docs/trust_scale_items.md` and compare the JSON array **exactly** against the verified list in `research/trust_scale_verification_report.md`. If mismatch, raise `SystemExit(1)` and block start.  
  **Dependency**: T024, T007g.

- [ ] T024c [US1] Implement Trust Score aggregation in `code/experiment/app.py`.  
  **Requirement**: `trust_score = mean(trust_item_ … trust_item_12)` (numeric conversion of Likert labels). Store in export.  
  **Dependency**: T024.

- [ ] T025 [US1] Implement data export to `data/raw/` with checksum generation and timestamped filename. Ensure schema compliance.  
  **Dependency**: T018, T010, T024c, T024b.

- [ ] T025b [US1] Runtime schema validation before export. Validate against `participant.schema.yaml`; abort on failure.  
  **Dependency**: T025, T012.

- [ ] T026 [US1] Implement manipulation check question (`perceived_agency_score`, 1‑7 Likert). Document that it is **only** for descriptive analysis, never used as covariate.  
  **Dependency**: T018, T010.

- [ ] T027 [P] [US1] Unit test for randomization logic (`code/experiment/tests/test_randomization.py`). Verify distribution and seed stability.

- [ ] T028 [P] [US1] Integration test for session flow (`code/experiment/tests/test_session_flow.py`). Verify end‑to‑end data capture.

---

## Phase 4: User Story 2 - Statistical Analysis Pipeline Execution (Priority: P2)

- [ ] T029 [P] Implement data cleaning pipeline in `code/analysis/data_cleaning.py` (handle missing values, flag attention check failures).

- [ ] T030 [US2] Implement One‑Way ANOVA and **Planned Directional Contrasts** in `code/analysis/contrasts.py`. Use orthogonal contrast vectors `[-1, 1, 0]` and `[1, 1, -2]`. Output summary tables with t‑statistics, p‑values, df.  
  **Dependency**: T029.

- [ ] T031 [US2] Implement Tukey HSD post‑hoc tests in `code/analysis/pairwise.py` with family‑wise error rate adjustment.  
  **Dependency**: T030.

- [ ] T032 [US2] Implement Cohen's d effect size calculation in `code/analysis/effect_sizes.py` for all pairwise comparisons.  
  **Dependency**: T031.

- [ ] T033 [US2] Create synthetic data generator in `code/analysis/synthetic_data.py` for pipeline testing.

- [ ] T034 [US2] Integrate all steps into `code/analysis/run_analysis.py`.

- [ ] T035 [US2] Analyze manipulation check data (from T026) and calculate achieved power.  
  **Logic**: Compute mean perceived agency score; one‑sample t‑test against a threshold; read target N from `research/power_calculation.json`. Write `results/power_status.json` with fields `manipulation_check_status`, `mean_score`, `achieved_power`, `power_status` (sufficient/insufficient). Do **not** halt pipeline on insufficient power.  
  **Dependency**: T026, T002.

- [ ] T036 [P] Contract test for analysis output schema (`tests/contract/test_analysis_output.py`).

- [ ] T037 [P] Unit test for contrast calculation logic using synthetic data (`tests/unit/test_contrasts.py`).

---

## Phase 5: User Story 3 - Methodological Robustness & Sensitivity Reporting (Priority: P3)

**Goal**: Generate reports including power analysis, multiple‑comparison corrections, and sensitivity analysis.

- [ ] T038 [US3] Implement sensitivity analysis in `code/analysis/sensitivity.py`.  
  **Requirement**: Sweep participant exclusion thresholds defined in `code/analysis/config.yaml` (`sensitivity_config`).  
  **Logic**:  
  1. Load `sensitivity_config`.  
  2. Verify ranges match those listed in `docs/protocol.md` (generated by T042).  
  3. Iterate over each threshold type (attention pass rate, straight‑lining, adherence cutoff, trust outlier) using the start‑end‑step values defined in the protocol.  
  4. For each sweep, re‑run primary analysis and record `p_value_primary` and `effect_size_primary`.  
  **Output**: CSV `results/sensitivity_sweep.csv` with columns `threshold_type`, `threshold_value`, `p_value_primary`, `effect_size_primary`.  
  **Dependency**: T030, T031, T042.

- [ ] T038b [US3] Implement sensitivity analysis reporting in `code/analysis/report.py`.  
  **Requirement**: Append a "Sensitivity Analysis" section to `docs/report.md` summarizing stability across sweeps.  
  **Dependency**: T038.

- [ ] T039 [US3] Implement final report generation in `code/analysis/report.py`.  
  **Requirement**: Compile ANOVA, contrasts, post‑hoc, effect sizes, pre‑study power (`research/power_calculation.json`), and sensitivity analysis.  
  **Power Limitation Handling**: Read `results/power_status.json`; if `power_status` is "insufficient", append a "Limitations" section stating "Limitation: Insufficient Power" with achieved vs target power.  
  **Output**: `docs/report.md`.  
  **Dependency**: T002, T034, T038, T038b, T035.

- [ ] T040 [US3] Add null result handling logic in `code/analysis/report.py` (explicitly report null findings and observed effect sizes).

- [ ] T041 [P] Unit test for sensitivity sweep logic (`tests/unit/test_sensitivity.py`).

---

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T043 [P] Create GitHub Actions workflow `.github/workflows/experiment.yml` to run analysis on `data/processed/`.

- [ ] T044 [P] Code cleanup and refactoring for type hints and docstrings (Google style). Run `pyright` and ensure zero errors.

- [ ] T045 [P] Add validation scripts to verify `participant.schema.yaml` compliance against `data/raw/` exports.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0 (Gates)**: T000 -> T000b. **CRITICAL**: If these fail, project halts.
- **Phase 0 (Research)**: T000b -> T001a-1 -> T001a-2 -> T001b-1 -> T001b-2 -> T002 -> T003-1 -> T008 -> T010b -> T011 -> T007g. **Note**: T010b, T011, and T007g are **REQUIRED** for the transition to Phase 1 and Phase 2.
- **Phase 1 (Setup)**: Depends on Phase 0 completion. Tasks T004, T005, T006, T010, T009, T012, T017i, T017h, T015, T016 can run in parallel as they depend only on T004 and T000/T010b where applicable. **Order within Phase 1**: T004 -> T010 -> T009 -> T012 -> T017i -> T017h.
- **Phase 2 (Foundational)**: Depends on Phase 0 (including T010b/T011/T007g) and Phase 1 completion. **BLOCKS all user stories**.
- **Phase 3 (US1)**: Depends on Phase 2 completion. T024b execution is additionally blocked by T007g completion.
- **Phase 4 (US2)**: Depends on Phase 2 completion.
- **Phase 5 (US3)**: Depends on Phase 4 completion AND T042 (Protocol) completion.
- **Phase 6 (Polish)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **CRITICAL**: Must be completed before data collection begins. **Execution Note**: T024b runtime requires T007g.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Can run on synthetic data independently of US1 completion, but requires US1 data schema.
- **User Story 3 (P3)**: Can start ONLY AFTER Phase 4 (US2) completion AND T042 (Protocol) completion. Relies on US2 outputs (ANOVA, post-hoc) for sensitivity sweeps and post-hoc power.

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

1. Complete Pre-Phase 0: Gates (T000, T000b).
2. Complete Phase 0: Research & Validation (Includes T0.80 Power Analysis AND T007g).
3. Complete Phase 1: Setup.
4. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
5. Complete Phase 3: User Story 1.
6. **STOP and VALIDATE**: Test User Story 1 independently (run pilot with synthetic or real participants).
7. Deploy experiment interface for recruitment.

### Incremental Delivery

1. Complete Pre-Phase 0 + Phase 0 + Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy experiment interface (MVP!).
3. Add User Story 2 → Test on synthetic data → Ready for real data analysis.
4. Add User Story 3 → Test robustness → Generate final report.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Pre-Phase 0 + Phase 0 + Setup + Foundational together.
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
- **Critical Dependencies**: T002 must complete after T001a-2 and T001b-2. T008 depends on T002. T024 depends on T010b, T011, T000b, and T007g artifacts. T035 depends on T026 and T002. T038 depends on Phase 4 and T042. T039 depends on T002, Phase 4, T038, and T038b.
- **Execution Flow**: T010b/T011/T007g are prerequisites for Phase 2. T007g is a prerequisite for T024b execution. T042 is a prerequisite for T038 execution.
