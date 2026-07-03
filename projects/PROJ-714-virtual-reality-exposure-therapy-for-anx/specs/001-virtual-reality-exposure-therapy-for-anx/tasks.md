# Tasks: VR Exposure Therapy Meta-Analysis

**Input**: Design documents from `/specs/001-vr-exposure-meta-analysis/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/derived/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with dependencies (`pandas`, `scipy`, `meta`, `matplotlib`, `reportlab`, `pyyaml`, `openpyxl`, `requests`, `pytest`) in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Author `specs/001-vr-exposure-meta-analysis/protocol.md` documenting search strings, inclusion criteria, and moderator hypotheses (Constitution VI Gate)
- [ ] T005 Implement `code/00_protocol_validator.py` to verify `protocol.md` exists and contains required sections before data processing
- [ ] T006 Create `code/utils/validators.py` with schema validation logic for Study, EffectSize, and MetaResult entities
- [ ] T007 Implement `code/utils/plots.py` with helper functions for generating PRISMA diagrams, forest plots, and funnel plots
- [ ] T008 Configure environment configuration management (pinned random seeds in `code/config.yaml`)
- [ ] T042 [P] Implement `code/05_validate_input_schema.py` as a **utility library** containing the centralized validation function for input CSVs. This function **MUST** explicitly check for 'title', 'abstract', 'DOI', 'publication year', 'sample size', and 'outcome measures' as defined in FR-001. **Note**: This is a library implementation to be called by T012, not a standalone pipeline step. (Moved from Phase 6 to ensure early failure and prevent silent schema errors)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Literature Search and Study Screening (Priority: P1) 🎯 MVP

**Goal**: Execute reproducible search queries and filter studies against strict inclusion criteria to produce a candidate list.

**Independent Test**: Can be fully tested by executing the search queries against mock CSV exports and verifying that the filtering logic correctly includes/excludes studies based on the documented inclusion criteria.

### Tests for User Story 1 (Mandatory) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T009 [P] [US1] Contract test for inclusion filter logic in `code/tests/contract/test_screening_criteria.py` (Verify RCT, age, anxiety, validated scale, stats presence)
- [ ] T010 [P] [US1] Integration test for empty result set handling in `code/tests/integration/test_empty_search.py` (Verify "NO_CANDIDATE_STUDIES" halt)
- [ ] T011 [P] [US1] Integration test for exclusion logging in `code/tests/integration/test_exclusion_audit.py` (Verify exclusion reasons are recorded for every rejected study)

### Implementation for User Story 1

- [ ] T012 [US1] Implement search query builder in `code/01_search_and_screen.py` (Support manual CSV import and OpenAlex/PubMed API fallback; **MUST** call the centralized validation function from T042 on manual CSVs to ensure schema compliance; **MUST** implement the logic to export search results to CSV with the specific schema required by FR-001)
- [ ] T012a [US1] Implement CSV export logic in `code/01_search_and_screen.py` to generate `data/raw/search_exports/results.csv` containing all required metadata fields (title, abstract, DOI, publication year, sample size, outcome measures) as mandated by FR-001. This task ensures the data generation step is distinct and compliant.
- [ ] T013a [P] [US1] Implement inclusion criteria filter function in `code/01_search_and_screen.py` (Check RCT, age≥18, anxiety diagnosis, validated scale, presence of means/SDs/Ns)
- [ ] T014 [US1] Implement exclusion reason generator and audit logger in `code/01_search_and_screen.py`
- [ ] T015 [US1] Implement PRISMA flow diagram **data generator** in `code/01_search_and_screen.py` (Output `data/derived/prisma_flow.json` containing counts for identified, screened, excluded, included; **MUST** produce JSON data only, no rendering; **MUST** aggregate exclusion reasons from T014 into an 'excluded_details' field in the JSON to satisfy FR-007 documentation requirements; **MUST** validate output structure against `contracts/prisma_flow.schema.yaml` if available, or ensure schema matches T037 expectations)
- [ ] T016 [US1] Implement main screening pipeline script to read `data/raw/search_exports/*.csv` and write `data/derived/screened_studies.csv`
- [ ] T017 [US1] Add error handling for API failures (403/timeout) with automatic fallback to manual CSV import path

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Effect-Size Computation and Data Extraction (Priority: P2)

**Goal**: Extract comparative statistics from screened studies and compute Hedges' g with 95% CIs.

**Independent Test**: Can be fully tested by providing a CSV of synthetic studies with known means/SDs/Ns and verifying computed Hedges' g matches hand-calculated benchmarks.

### Tests for User Story 2 (Mandatory) ⚠️

- [ ] T018 [P] [US2] Contract test for Hedges' g formula in `code/tests/contract/test_effect_size_calc.py` (Verify small-sample correction and pooled SD)
- [ ] T019 [P] [US2] Integration test for missing control group handling in `code/tests/integration/test_missing_control.py` (Verify exclusion and logging)
- [ ] T020 [P] [US2] Sensitivity analysis test for missing correlation `r` in `code/tests/integration/test_r_sensitivity.py` (Verify range of `r` values is tested)

### Implementation for User Story 2

- [ ] T021 [US2] Implement data extraction parser in `code/02_effect_size_calc.py` (Parse pre/post means, SDs, Ns for both groups from `data/derived/screened_studies.csv`)
- [ ] T022 [US2] Implement comparative Hedges' g calculator in `code/02_effect_size_calc.py` (Formula: (Mean_T - Mean_C) / Pooled_SD * Correction; **MUST** write 'Hedges & Olkin, 1985' to `formula_reference` field in output CSV)
- [ ] T023 [US2] Implement 95% CI and standard error calculation in `code/02_effect_size_calc.py`
- [ ] T024 [US2] Implement sensitivity analysis for missing pre-post correlation `r` in `code/02_effect_size_calc.py` (Test range of plausible `r` values)
- [ ] T025 [US2] Implement validation logic to flag studies with insufficient statistics (missing N, SD, or mean) for exclusion
- [ ] T026 [US2] Write final effect sizes to `data/derived/effect_sizes.csv` with columns: study_id, Hedges_g, SE, lower_95CI, upper_95CI, computation_method, formula_reference

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Meta-Analysis Synthesis and Reporting (Priority: P3)

**Goal**: Execute random-effects meta-analysis, assess bias, perform sensitivity analysis, and generate the final PDF report.

**Independent Test**: Can be tested by running the meta-analysis on a fixed dataset and verifying pooled Hedges' g, I², and Egger's test p-value match `metafor` R package outputs.

### Tests for User Story 3 (Mandatory) ⚠️

- [ ] T027 [P] [US3] Contract test for random-effects model in `code/tests/contract/test_meta_analysis_model.py` (Verify REML/DL estimator selection)
- [ ] T028 [P] [US3] Integration test for Egger's test threshold in `code/tests/integration/test_eggers_test.py` (Verify p<0.10 flag and trim-and-fill trigger)
- [ ] T029 [P] [US3] Integration test for leave-one-out sensitivity in `code/tests/integration/test_leave_one_out.py` (Verify outlier identification)

### Implementation for User Story 3

- [ ] T030 [US3] Implement random-effects meta-analysis model in `code/03_meta_analysis.py` using `meta` package (**MUST** implement a configurable estimator selection strategy with a default to REML; **MUST** document the chosen estimator and justification in `research.md`; **MUST** use the `meta` package API to explicitly set the `method.tau` parameter based on configuration, e.g., `method.tau='REML'` or `method.tau='DL'`; **MUST** ensure the model object exposes `tau_squared` and `i_squared` attributes for downstream tasks)
- [ ] T031 [US3] Implement heterogeneity assessment (I², τ²) and reporting logic in `code/03_meta_analysis.py`; **MUST** calculate I² and τ² from the model output; **MUST** trigger T039 if I² > 75%; **MUST** prepare data structures for T031b; **Note**: This task focuses on calculation and logic, not file I/O.
- [ ] T031b [US3] Implement **τ² Persistence** in `code/03_meta_analysis.py`. **MUST** explicitly write the `tau_squared` value (from T031) as a top-level key to `data/derived/meta_results.json`. **MUST** also write `i_squared`, `pooled_Hedges_g`, and `model_method` to the same file. **MUST** ensure this file is written before T038 (Report Generation) runs. This task resolves the data persistence gap for FR-004.
- [ ] T032 [US3] Implement Egger's linear regression test in `code/03_meta_analysis.py` (**MUST** check N: if N<10 flag as "underpowered" and perform visual funnel plot inspection; if N≥10 run test; if p<0.10 trigger T033); **MUST** log the "underpowered" status explicitly to the audit trail; **MUST** handle the "underpowered" case gracefully by skipping the test execution and writing a placeholder result to `meta_results.json` rather than crashing.
- [ ] T033a [US3] Implement trim-and-fill algorithm in `code/03_meta_analysis.py` (**MUST** be triggered as a sensitivity analysis if T032 p<0.10; **MUST** calculate adjusted effect size but **MUST NOT** automatically replace the primary estimate; **MUST** flag for review; **MUST** handle N<10 case by skipping execution and logging "SKIPPED_UNDERPOWERED").
- [ ] T033b [US3] Implement storage of adjusted effect size in `code/03_meta_analysis.py`. **MUST** write the adjusted effect size and trim-and-fill results to `data/derived/meta_results.json` under a specific key (e.g., `adjusted_effect`) and ensure the report generator (T038) can access this value if applicable.
- [ ] T034 [US3] Implement leave-one-out sensitivity analysis in `code/03_meta_analysis.py` (**MUST** check N: if N<10 skip execution, log "UNDERPOWERED" status, and write a placeholder entry to `data/derived/meta_results.json` with null values for outlier analysis; if N≥10 execute iterative removal, **MUST** identify influential outliers, and document them in `data/derived/outlier_log.json`; **MUST** ensure the script does not crash if N<10 by implementing an explicit conditional check before the loop).
- [ ] T039 [US3] Implement **Moderator Analysis Engine** in `code/03_meta_analysis.py` (Triggered if I² > 75%; tests subgroups for **candidate** moderators: anxiety subtype, hardware type, session count; **MUST** parse these columns from `screened_studies.csv`; **MUST** extend the list of moderators based on data availability; outputs subgroup effects to `data/derived/moderator_results.json`; **MUST** handle missing moderator data by excluding those studies for that specific moderator and logging the N).
- [ ] T035 [US3] Implement forest plot generation in `code/utils/plots.py` using `matplotlib` (Consumes `data/derived/effect_sizes.csv` and meta-analysis results)
- [ ] T036 [US3] Implement funnel plot generation in `code/utils/plots.py` (Consumes `data/derived/effect_sizes.csv` and Egger's test results)
- [ ] T037 [US3] Implement PRISMA flow diagram **renderer** in `code/utils/plots.py` (Consumes `data/derived/prisma_flow.json` from T015; generates PNG asset; **MUST** render from JSON data, not generate data; **MUST** run after T030-T036 to ensure all meta-analysis results are available for the report context)
- [ ] T038 [US3] Implement PDF report generator in `code/04_report_generation.py` (Compiles all figures, stats, **moderator results (if any)**, and method descriptions; **MUST** depend on T015, T026, T030-T037, T039; **MUST** check for the existence of `data/derived/meta_results.json` keys for adjusted effects, outliers, and **tau_squared** to include them if available, handling missing keys gracefully; **MUST** assert that `tau_squared` exists in `meta_results.json` before generating the report to ensure FR-004 compliance).
- [ ] T040 [US3] Implement checksum generation and state update in `code/04_report_generation.py` (Write to `state/`)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Benchmarking (Cross-Cutting)

**Purpose**: Ensure numerical accuracy and data hygiene as per Constitution.

- [ ] T041 [P] Run benchmark comparing `meta` package output against `statsmodels` synthetic dataset; **MUST** generate `data/derived/benchmark_equivalence_report.json` with mean absolute error < 1e-6 (Plan Task 1.2)

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `screened_studies.csv` as input)
- **User Story 3 (P3)**: Depends on US2 completion (requires `effect_sizes.csv` as input)

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
Task: "Contract test for inclusion filter logic in code/tests/contract/test_screening_criteria.py"
Task: "Integration test for empty search in code/tests/integration/test_empty_search.py"

# Launch all models for User Story 1 together:
Task: "Implement search query builder in code/01_search_and_screen.py"
Task: "Implement inclusion criteria filter in code/01_search_and_screen.py"
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
   - Developer A: User Story 1 (Search & Screen)
   - Developer B: User Story 2 (Effect Sizes) - *Wait for US1 data*
   - Developer C: User Story 3 (Reporting) - *Wait for US2 data*
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
- **Constraint**: All analysis must run on CPU-only free-tier CI (2 cores, 7GB RAM). No GPU models or large LLMs.
- **Constraint**: All data must be real or derived from real sources; no fabrication of input data.