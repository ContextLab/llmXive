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

- [ ] T001a [P] Create root project directory tree: `projects/PROJ-008-psychology-research/`, `projects/PROJ-008-psychology-research/code/`, `projects/PROJ-008-psychology-research/data/`, `projects/PROJ-008-psychology-research/docs/`, `projects/PROJ-008-psychology-research/tests/`, `projects/PROJ-008-psychology-research/contracts/`, `projects/PROJ-008-psychology-research/scripts/`, `projects/PROJ-008-psychology-research/.github/workflows/`
- [ ] T001b [P] Create data sub-directories: `projects/PROJ-008-psychology-research/data/raw/`, `projects/PROJ-008-psychology-research/data/processed/`, `projects/PROJ-008-psychology-research/data/interim/`
- [ ] T001c [P] Create code sub-directories: `projects/PROJ-008-psychology-research/code/data/`, `projects/PROJ-008-psychology-research/code/analysis/`, `projects/PROJ-008-psychology-research/code/viz/`, `projects/PROJ-008-psychology-research/code/utils/`, `projects/PROJ-008-psychology-research/tests/unit/`, `projects/PROJ-008-psychology-research/tests/integration/`, `projects/PROJ-008-psychology-research/tests/contract/`
- [X] T002a [P] Create `pyproject.toml` at `projects/PROJ-008-psychology-research/` with: build-system (setuptools>=61.0), python version `>=3.11`, and dependencies list: `pandas>=2.0.0`, `scikit-learn>=1.3.0`, `statsmodels>=0.14.0`, `matplotlib>=3.7.0`, `requests>=2.31.0`, `pyyaml>=6.0`, `pytest>=7.4.0`, `bayesmeta>=0.1.0`, `pdfplumber>=0.10.0`.
- [ ] T002b [P] Install dependencies defined in T002a using `pip install -e.` in the project root. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base Pydantic models for `Study`, `EffectSize`, and `MetaAnalysisResult` in `code/data/models.py`. **Include docstrings citing the specific Constitution Principle and FR for each field to satisfy FR-007 (Data Integrity) and Principle II (Verified Accuracy).**
- [X] T005 [P] Implement structured logging infrastructure in `code/utils/logging.py` (FR-007)
- [X] T006 [P] Setup configuration management and seed pinning in `code/utils/config.py`
- [ ] T007a [P] Create `contracts/cleaned_study.schema.yaml` with EXACT fields: `id` (str), `title` (str), `registry` (str: enum[ClinicalTrials.gov, OSF]), `age_range` (str), `diagnosis` (str), `outcomes` (list), `intervention_components` (list), `delivery_format` (str), `follow_up` (str), `abstract_text` (str, optional).
- [ ] T007b [P] Update `contracts/cleaned_study.schema.yaml` to add field `assessor_blinding` (str: enum[single-blind, double-blind, unblinded, not-reported]) for blinding extraction. **This task MUST be completed before T022.**
- [ ] T007c [P] Create `contracts/effect_size.schema.yaml` with EXACT fields: `study_id` (str), `hedges_g` (float), `se` (float), `ci_lower` (float), `ci_upper` (float), `n_treatment` (int), `n_control` (int).
- [X] T008 Implement artifact hashing utility in `scripts/hash_artifacts.py` for Constitution Principle V
- [X] T009 [P] Create `docs/ethics_determination.md` documenting the 'Exempt' status for secondary analysis of de-identified public registry data (ClinicalTrials.gov, OSF) and justification for no IRB requirement
- [X] T010 [P] Create `docs/analysis-plan.md` detailing missing-data handling and imputation strategies. **Must include sections: Missing Data Strategy (with table of methods), Imputation Method (with formula), Sensitivity Analysis (with criteria).**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Collection and Cleaning Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw study data from ClinicalTrials.gov and OSF, validate against inclusion criteria, and extract standardized variables into a clean CSV.

**Independent Test**: The pipeline can be tested by running it against a known set of mock study records with predefined inclusion/exclusion flags and verifying that the output CSV contains the expected included records.

> **NOTE**: Per Constitution Principle VI (Clinical Trial Registry Integrity), data sources are strictly limited to ClinicalTrials.gov and OSF.

### Tests for User Story 1 (REQUIRED) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T013 [P] [US1] Contract test for data extraction schema in `tests/contract/test_cleaned_study_schema.py`
- [X] T014 [P] [US1] Integration test for API rate-limiting and backoff in `tests/integration/test_api_collector.py`
- [X] T015 [P] [US1] Unit test for inclusion criteria filtering logic in `tests/unit/test_cleaner.py`

### Implementation for User Story 1

- [ ] T016 [US1] Implement API collector in `code/data/collector.py` (FR-001, FR-002) with rate-limiting and exponential backoff for **ClinicalTrials.gov and OSF ONLY**. **Log search query strings and retrieval timestamps to `data/raw/retrieval_log.json` to satisfy Constitution Principle VI audit requirements.**
- [X] T017 [P] [US1] Implement data extractor in `code/data/extractor.py` (FR-003) with regex patterns for intervention components
- [ ] T018 [US1] Implement data cleaner in `code/data/cleaner.py` (FR-007) to validate age (6-12), ASD diagnosis, and social skill outcomes
- [ ] T019 [US1] Implement multi-arm study handling logic in `code/data/cleaner.py` (FR-008) to split control groups proportionally
- [ ] T020 [US1] Implement **abstract-only** text extraction logic in `code/data/extractor.py` (FR-009) using `pdfplumber`. **Logic: If registry metadata is missing, the code attempts extraction via pdfplumber. HOWEVER, if registry metadata is insufficient to confirm the study meets inclusion criteria, the study MUST be flagged in `excluded_studies.log` with reason `INSUFFICIENT_REGISTRY_DATA` and NO PDF reconstruction fallback is performed.** **Output: Add column `abstract_text` to `cleaned_studies.csv` for studies where metadata was sufficient.**
- [ ] T021 [US1] **Verify and archive output**: Create script `scripts/verify_output.py` that checks for existence of `data/processed/cleaned_studies.csv` and `data/raw/excluded_studies.log` and exits 0 on success, 1 on failure.
- [ ] T022 [US1] depends on T007b: Implement **Blinded Assessment Extraction** in `code/data/extractor.py`. **Extract `assessor_blinding` field (enum: single-blind, double-blind, unblinded, not-reported) for each study and add to `cleaned_studies.csv`.**
- [ ] T023 [US1] depends on T022: Implement **Blinding Validation** in `code/data/cleaner.py`. **Validate `assessor_blinding` field against schema and flag studies with invalid values.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Effect Size Calculation and Meta-Analysis (Priority: P2)

**Goal**: Calculate Hedges' *g* effect sizes, perform random-effects meta-analysis, and conduct subgroup analyses comparing mindfulness components and delivery formats.

**Independent Test**: The calculation module can be tested by providing a synthetic dataset of 3 studies with known means and standard deviations, verifying that the calculated Hedges' *g* matches the manual calculation within a tolerance of 0.001.

### Tests for User Story 2 (REQUIRED) ⚠️

- [ ] T024 [P] [US2] Contract test for effect size schema in `tests/contract/test_effect_size_schema.py`
- [ ] T025 [P] [US2] Unit test for Hedges' *g* calculation accuracy against `statsmodels` or manual calc in `tests/unit/test_effect_sizes.py`
- [ ] T026 [P] [US2] Unit test for random-effects model selection logic (I² > 50%) in `tests/unit/test_meta_analysis.py`

### Implementation for User Story 2

- [ ] T027 [US2] depends on T016, T017, T018, T019, T020, T021, T022, T023: Implement Hedges' *g* calculator in `code/analysis/effect_sizes.py` (FR-004, FR-013) with small-sample correction
- [ ] T028 [US2] depends on T016, T017, T018, T019, T020, T021, T022, T023: Implement random-effects meta-analysis engine in `code/analysis/meta_analysis.py` (FR-005) using `statsmodels` or `metafor` equivalent
- [ ] T029 [US2] depends on T027, T028, T022, T023: Implement subgroup analysis (Cochran's Q) for mindfulness components and delivery formats in `code/analysis/meta_analysis.py` (FR-005)
- [ ] T030 [US2] depends on T027, T028, T022, T023: Implement social skill domain extraction and subgroup analysis in `code/analysis/meta_analysis.py` (FR-010, FR-011)
- [ ] T031 [US2] depends on T027, T028, T022, T023: Implement follow-up duration subgroup analysis (3-month vs others) in `code/analysis/meta_analysis.py` (FR-012)
- [ ] T032 [US2] depends on T027, T028, T022, T023: Implement conditional logic to suppress subgroup/meta-regression if N < 10 and switch to descriptive synthesis (FR-014)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Publication Bias Assessment (Priority: P3)

**Goal**: Generate forest plots and funnel plots (if N ≥ 10) to assess publication bias and interpret meta-analysis results.

**Independent Test**: The visualization module can be tested by running it on a small dataset and verifying that the forest plot correctly displays the study-specific effect sizes and confidence intervals, and that the funnel plot is suppressed if N < 10.

### Tests for User Story 3 (REQUIRED) ⚠️

- [ ] T034 [P] [US3] Unit test for forest plot generation in `tests/unit/test_plots.py`
- [ ] T035 [P] [US3] Unit test for funnel plot suppression logic when N < 10 in `tests/unit/test_plots.py`
- [ ] T036 [P] [US3] Integration test for publication bias assessment (Egger's test) in `tests/integration/test_bias.py`

### Implementation for User Story 3

- [ ] T037 [US3] depends on T027-T032: Implement forest plot generator in `code/viz/plots.py` (FR-006) displaying study-specific CIs and pooled effect diamond
- [ ] T038 [US3] depends on T027-T032: Implement funnel plot generator in `code/viz/plots.py` (FR-006) with asymmetry visual cues (only if N ≥ 10)
- [ ] T039 [US3] depends on T027-T032: Implement Egger's test and publication bias assessment in `code/analysis/bias.py` (FR-006)
- [ ] T040 [US3] depends on T039: Implement conditional logic to suppress funnel plot/Egger's test if N < 10 and add warning to report (FR-014)
- [ ] T041 [US3] depends on T037, T038: Generate `data/processed/forest_plot.png` and `data/processed/funnel_plot.png` at 300 DPI using matplotlib savefig() with explicit dpi parameter (FR-006).
- [ ] T042 [US3] depends on T041, T021, T023: Generate `docs/results.md` containing: 1) Executive Summary, 2) Forest Plot (T037), 3) Funnel Plot (T038), 4) Heterogeneity Statistics (I², Q), 5) Subgroup Analysis Results, 6) Narrative Synthesis if N<10. **Verify file exists and contains all 6 sections (FR-006).**
- [ ] T043 [US3] depends on T022, T037: Implement **Blinding Comparison Visualization** in `code/viz/plots.py`. **Generate `data/processed/blinding_comparison_plot.png` (bar chart or forest plot) comparing effect sizes for single-blind vs. unblinded studies. Verify file exists and contains two distinct pooled effect diamonds.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address current spec requirements

- [ ] T044 [P] Create `.github/workflows/ci.yml` to automate pipeline execution on a fresh runner, verifying reproducibility (SC-005). **Success criteria: All tests pass, data checksums match, no errors.**
- [ ] T045 [P] depends on T007a, T021: Implement data integrity check script `scripts/validate_contracts.py` to run schema validation on `data/processed/cleaned_studies.csv` against `contracts/cleaned_study.schema.yaml`, writing a detailed `data/validation_report.json` with pass/fail status per record and summary statistics (SC-005, FR-007).
- [ ] T046 [P] depends on T042, T004: Generate final `docs/protocol.md` detailing the full methodology (search strategy, inclusion criteria, statistical methods) as per PRISMA guidelines. **Verify file exists and includes PRISMA flow diagram description (text, not image) with regex `\\bPRISMA\\b` and a table with columns `Included`, `Excluded`. Explicitly document the novel contribution (6-12 age range, disaggregated components, delivery format) in the Introduction section.**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1 (T016-T023)
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
- **PDF Extraction**: T020 uses `pdfplumber` for **abstract-only** reconstruction. Full-text OCR is disabled to comply with CPU-only constraints. If registry data is insufficient, flag and exclude, do not fabricate.
- **CI/CD**: T044 ensures reproducibility on a fresh runner as per SC-005.
- **Contract Validation**: T045 provides the concrete validation step required for data hygiene and reproducibility.
- **Constitution Override**: T016 strictly enforces Constitution Principle VI (Clinical Trial Registry Integrity) by limiting sources to ClinicalTrials.gov and OSF, overriding FR-001's list of other sources. The spec is flagged for a kickback.
- **Scope Adherence**: This task list strictly adheres to Functional Requirements FR-001 through FR-014 as defined in `spec.md`. No tasks referencing non-existent FRs (e.g., FR-015+) are included.
- **Status Reset**: All task statuses have been reset to '[ ]' (incomplete) to accurately reflect the current state of the filesystem and resolve contradictions from previous revisions.
- **T049 Removal**: Task T049 (Artifact Generation Verification referencing FR-022) has been removed as FR-022 does not exist. Verification scope is covered by T042 and T045.