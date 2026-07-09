# Tasks: Mindfulness Components and Delivery Formats in ASD Social Skills

**Input**: Design documents from `/specs/001-mindfulness-asd-social-skills/`
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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-008-psychology-research/`)
- [ ] T002 Initialize Python 3.11 project with `pyproject.toml` (dependencies: `pandas`, `scikit-learn`, `statsmodels`, `matplotlib`, `requests`, `pyyaml`, `pytest`, `bayesmeta`, `pdfplumber`, `pytesseract`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create base Pydantic models for `Study`, `EffectSize`, and `MetaAnalysisResult` in `code/data/models.py`
- [ ] T005 [P] Implement structured logging infrastructure in `code/utils/logging.py` (FR-007)
- [ ] T006 [P] Setup configuration management and seed pinning in `code/utils/config.py`
- [~] T007 Create schema contracts in `contracts/` directory: `cleaned_study.schema.yaml` and `effect_size.schema.yaml`
- [~] T008 Implement artifact hashing utility in `scripts/hash_artifacts.py` for Constitution Principle V
- [~] T009 [P] Create `docs/ethics_determination.md` documenting the 'Exempt' status for secondary analysis of de-identified public registry data (ClinicalTrials.gov, OSF) and justification for no IRB requirement
- [~] T010 Create `docs/analysis-plan.md` detailing missing-data handling and imputation strategies

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw study data from ClinicalTrials.gov and OSF, validate against inclusion criteria, and extract standardized variables into a clean CSV.

**Independent Test**: The pipeline can be tested by running it against a known set of mock study records with predefined inclusion/exclusion flags and verifying that the output CSV contains the expected included records.

> **NOTE**: Per Constitution Principle VI (Clinical Trial Registry Integrity), data sources are strictly limited to ClinicalTrials.gov and OSF. Although FR-001 in spec.md lists other sources, the Constitution is the non-negotiable constraint. The spec is flagged for a kickback to resolve this internal contradiction.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Contract test for data extraction schema in `tests/contract/test_cleaned_study_schema.py`
- [~] T012 [P] [US1] Integration test for API rate-limiting and backoff in `tests/integration/test_api_collector.py`
- [~] T013 [P] [US1] Unit test for inclusion criteria filtering logic in `tests/unit/test_cleaner.py`

### Implementation for User Story 1

- [~] T014 [US1] Implement API collector in `code/data/collector.py` (FR-001, FR-002) with rate-limiting and exponential backoff for **ClinicalTrials.gov and OSF ONLY** (Constitution Principle VI override).
- [ ] T015 [P] [US1] Implement data extractor in `code/data/extractor.py` (FR-003) with regex patterns for intervention components
- [ ] T016 [US1] Implement data cleaner in `code/data/cleaner.py` (FR-007) to validate age (6-12), ASD diagnosis, and social skill outcomes
- [ ] T017 [US1] Implement multi-arm study handling logic in `code/data/cleaner.py` (FR-008) to split control groups proportionally
- [ ] T018 [US1] Implement **abstract-only** text extraction fallback in `code/data/extractor.py` (FR-009) using `pdfplumber` for abstract reconstruction if API metadata is missing. **Full-text OCR is disabled** to preserve CPU-only/7GB RAM constraints (Plan Assumptions).
- [ ] T019 [US1] **Verify and archive output**: Ensure T014-T018 successfully generate `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log`. (This is a validation step, not a generation step).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Effect Size Calculation and Meta-Analysis (Priority: P2)

**Goal**: Calculate Hedges' *g* effect sizes, perform random-effects meta-analysis, and conduct subgroup analyses comparing mindfulness components and delivery formats.

**Independent Test**: The calculation module can be tested by providing a synthetic dataset of 3 studies with known means and standard deviations, verifying that the calculated Hedges' *g* matches the manual calculation within a tolerance of 0.001.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T021 [P] [US2] Contract test for effect size schema in `tests/contract/test_effect_size_schema.py`
- [ ] T022 [P] [US2] Unit test for Hedges' *g* calculation accuracy against `statsmodels` or manual calc in `tests/unit/test_effect_sizes.py`
- [ ] T023 [P] [US2] Unit test for random-effects model selection logic (I² > 50%) in `tests/unit/test_meta_analysis.py`

### Implementation for User Story 2

- [ ] T024 [US2] depends on T014, T015, T016, T017, T018: Implement Hedges' *g* calculator in `code/analysis/effect_sizes.py` (FR-004, FR-013) with small-sample correction
- [ ] T025 [US2] depends on T014, T015, T016, T017, T018: Implement random-effects meta-analysis engine in `code/analysis/meta_analysis.py` (FR-005) using `statsmodels` or `metafor` equivalent
- [ ] T026 [US2] depends on T024, T025: Implement subgroup analysis (Cochran's Q) for mindfulness components and delivery formats in `code/analysis/meta_analysis.py` (FR-005)
- [ ] T027 [US2] depends on T024, T025: Implement social skill domain extraction and subgroup analysis in `code/analysis/meta_analysis.py` (FR-010, FR-011)
- [ ] T028 [US2] depends on T024, T025: Implement follow-up duration subgroup analysis (3-month vs others) in `code/analysis/meta_analysis.py` (FR-012)
- [ ] T029 [US2] depends on T024, T025: Implement conditional logic to suppress subgroup/meta-regression if N < 10 and switch to descriptive synthesis (FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Publication Bias Assessment (Priority: P3)

**Goal**: Generate forest plots and funnel plots (if N ≥ 10) to assess publication bias and interpret meta-analysis results.

**Independent Test**: The visualization module can be tested by running it on a small dataset and verifying that the forest plot correctly displays the study-specific effect sizes and confidence intervals, and that the funnel plot is suppressed if N < 10.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T031 [P] [US3] Unit test for forest plot generation in `tests/unit/test_plots.py`
- [ ] T032 [P] [US3] Unit test for funnel plot suppression logic when N < 10 in `tests/unit/test_plots.py`
- [ ] T033 [P] [US3] Integration test for publication bias assessment (Egger's test) in `tests/integration/test_bias.py`

### Implementation for User Story 3

- [ ] T034 [US3] depends on T024-T029: Implement forest plot generator in `code/viz/plots.py` (FR-006) displaying study-specific CIs and pooled effect diamond
- [ ] T035 [US3] depends on T024-T029: Implement funnel plot generator in `code/viz/plots.py` (FR-006) with asymmetry visual cues (only if N ≥ 10)
- [ ] T036 [US3] depends on T024-T029: Implement Egger's test and publication bias assessment in `code/analysis/bias.py` (FR-006)
- [ ] T037 [US3] depends on T036: Implement conditional logic to suppress funnel plot/Egger's test if N < 10 and add warning to report (FR-014)
- [ ] T038 [US3] depends on T034, T035: Generate high-resolution PNGs for forest and funnel plots in `data/processed/`
- [ ] T039 [US3] depends on T038: Generate final `docs/results.md` report including all plots, heterogeneity statistics, and narrative synthesis (if N < 10)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address current spec requirements

- [ ] T041 [P] Create `.github/workflows/ci.yml` to automate pipeline execution on a fresh runner, verifying reproducibility (SC-005)
- [ ] T042 [P] depends on T019, T007: Implement data integrity check script `scripts/validate_contracts.py` to run schema validation on `data/processed/cleaned_studies.csv` against `contracts/cleaned_study.schema.yaml`, writing a detailed `data/validation_report.json` with pass/fail status per record and summary statistics (SC-005, FR-007)
- [ ] T043 [P] depends on T039: Generate final `docs/results.md` and `docs/protocol.md` with complete methodology and results summary
- [ ] T044 [P] Create `quickstart.md` in `specs/001-mindfulness-asd-social-skills/` to document environment setup and verification steps (addressing filesystem_hygiene review)
- [ ] T045 [P] Add `LICENSE` file specifying research data usage terms (addressing data_quality_review)
- [ ] T047 [P] Update `research.md` with explicit "Novel Contribution" section distinguishing this meta-analysis from existing literature (addressing creativity review)
- [ ] T048 [P] Verify and resolve all `[UNVERIFIED]` citations in `plan.md` and `research.md` (addressing idea_quality review)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T014-T018)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on analysis results from US2

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
Task: "Contract test for data extraction schema in tests/contract/test_cleaned_study_schema.py"
Task: "Integration test for API rate-limiting and backoff in tests/integration/test_api_collector.py"

# Launch all models for User Story 1 together:
Task: "Implement API collector in code/data/collector.py"
Task: "Implement data extractor in code/data/extractor.py"
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
- **CPU Constraint**: All tasks must run on CPU-only CI (no GPU, no 8-bit models, no large LLM inference). Use `statsmodels` or `scikit-learn` for all statistical methods.
- **Data Integrity**: No fake data generation. All analysis must use real data from the download/fetch task or documented gaps.
- **Ethics**: T009 documents the 'Exempt' status for secondary analysis; no IRB protocol is required.
- **PDF Extraction**: T018 uses `pdfplumber` for **abstract-only** reconstruction. Full-text OCR is disabled to comply with CPU-only constraints.
- **CI/CD**: T041 ensures reproducibility on a fresh runner as per SC-005.
- **Contract Validation**: T042 provides the concrete validation step required for data hygiene and reproducibility.
- **Constitution Override**: T014 strictly enforces Constitution Principle VI (Clinical Trial Registry Integrity) by limiting sources to ClinicalTrials.gov and OSF, overriding FR-001's list of other sources. The spec is flagged for a kickback.
- **Removed Hallucinated Tasks**: T019d (session count), T019c (blinding extraction), T027c (blinding analysis), T027b (Risk of Bias), T046 (interactive plots), T019b (markdown report), T040 (duplicate verification) have been removed as they were not in the spec or were unexecutable.
- **Dependency Correction**: All analysis (T024-T029) and visualization (T034-T039) tasks now explicitly depend on the completion of their upstream calculation/data steps. [P] tags have been removed from sequential tasks.