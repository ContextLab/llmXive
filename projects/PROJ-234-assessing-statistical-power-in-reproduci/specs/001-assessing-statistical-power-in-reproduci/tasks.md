# Tasks: Assessing Statistical Power in Reproducible Research with Public Datasets

**Input**: Design documents from `/specs/001-assess-statistical-power/`
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

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-234-assessing-statistical-power-in-reproduci/code/utils projects/PROJ-234-assessing-statistical-power-in-reproduci/data/raw projects/PROJ-234-assessing-statistical-power-in-reproduci/data/processed projects/PROJ-234-assessing-statistical-power-in-reproduci/tests/unit projects/PROJ-234-assessing-statistical-power-in-reproduci/tests/contract projects/PROJ-234-assessing-statistical-power-in-reproduci/docs projects/PROJ-234-assessing-statistical-power-in-reproduci/contracts`.
- [ ] T002 Initialize Python 3 project with `requirements.txt` containing exactly:
  ```
  pandas==2.0.3
  openml==0.14.2
  statsmodels==0.14.1
  requests==2.31.0
  matplotlib==3.8.0
  pytest==7.4.0
  beautifulsoup4==4.12.2
  ```
  to satisfy reproducibility (Constitution Principle I).
- [ ] T003 [P] Configure linting by creating `pyproject.toml` with `[tool.black] max-line-length=88 target-version=['py310']` and `.flake8` with `max-line-length=88`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure by creating `code/__init__.py`, `data/.gitkeep`, `tests/__init__.py`, `contracts/.gitkeep` to ensure directory persistence and Python package recognition.
- [ ] T005 [P] Create `contracts/dataset_metadata.schema.yaml` with the following content mapping spec entities:
  ```yaml
  type: object
  properties:
    dataset_id: {type: integer}
    name: {type: string}
    download_count: {type: integer}
    publication_link: {type: string, nullable: true}
    task_id: {type: integer, nullable: true}
  required: [dataset_id, name, download_count]
  ```
- [ ] T006 [P] Create `contracts/power_audit_result.schema.yaml` with the following content mapping spec entities:
  ```yaml
  type: object
  properties:
    dataset_id: {type: integer}
    calculated_power: {type: number}
    threshold_met: {type: boolean}
    status: {type: string, enum: [success, unparseable, paywalled]}
  required: [dataset_id, calculated_power, threshold_met, status]
  ```
- [ ] T007 Implement `code/utils/api_client.py` with OpenML connection and exponential backoff retry logic (handles HTTP 429) (Implements test T010).
- [ ] T008 Implement `code/utils/oa_checker.py` to validate Open Access status of publication links (Implements test T010).
- [ ] T009 Setup `code/__init__.py` and basic logging configuration for pipeline phases.
- [ ] T009.5 [P] Implement `code/05_a_priori_power_analysis.py` as a distinct, reusable module with a CLI entry point for 'A Priori Power Analysis' (FR-006) to support future study design validation. This module must be importable by other scripts and runnable standalone.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Filter Top Public Datasets (Priority: P1) 🎯 MVP

**Goal**: Connect to OpenML API, retrieve top classification datasets, and filter for those with publication links or task IDs.

**Independent Test**: Execute `01_ingest_openml.py` and verify `data/raw/openml_metadata.json` contains a list of valid entries, up to the maximum allowed by the API limit. with non-null `publication_link` or `task_id`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for API retry logic in `tests/unit/test_api_client.py`.
- [ ] T011 [P] [US1] Contract test for `data/raw/openml_metadata.json` against `contracts/dataset_metadata.schema.yaml` in `tests/contract/test_schemas.py`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_ingest_openml.py` to fetch a representative set of classification datasets from OpenML API and save raw response to `data/raw/openml_metadata_raw.json` (Implements test T010).
- [ ] T013 [US1] Implement logic in `code/01_ingest_openml.py` to filter raw metadata to retain only entries with `publication_link` OR `task_id` and classify dataset types (binary, multi-class) for FR-009 (Implements test T010).
- [ ] T015 [US1] Log extraction statistics (total fetched, filtered count, types distribution) to `data/ingest.log` immediately after filtering (T013) completes (Implements test T010).
- [ ] T014 [US1] Validate filtered data for duplicate IDs and generate checksums for `data/raw/openml_metadata.json` (Implements test T011).
- [ ] T016 [US1] Add validation logic to ensure no duplicate dataset IDs in output; if duplicates found, keep the one with highest download count.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Extract Statistical Parameters via Full-Text Parsing (Priority: P2)

**Goal**: Parse full-text publications (or abstracts as fallback) to extract sample size (N) and effect sizes (Cohen's d, F-statistic).

**Independent Test**: Run `02_parse_publications.py` on a known subset of OA PDFs/text and verify `data/processed/extracted_params.json` contains correctly parsed `sample_size`, `effect_size`, and `metric_type` fields.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for regex extraction patterns in `tests/unit/test_parsers.py`.
- [ ] T019 [P] [US2] Contract test for `data/processed/extracted_params.json` against `contracts/power_audit_result.schema.yaml` in `tests/contract/test_schemas.py`.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/utils/parsers.py` with specific regex patterns: `N=\\d+`, `Cohen's d=\\d+\\.\\d+`, `F\\(\\d+,\\d+\\)=\\d+\\.\\d+` (Implements test T018).
- [ ] T021 [US2] Implement `code/02_parse_publications.py` to iterate over `data/raw/openml_metadata.json` (Implements test T018).
- [ ] T021.1 [US2] Implement pre-extraction validation in `code/02_parse_publications.py` to check if publication link is accessible and contains statistical metadata keywords (N=, d=, F=) before fetching full text (FR-007) (Implements test T018).
- [ ] T022 [US2] Fetch full-text from `publication_link` (handling paywalled content by checking OA status via `oa_checker.py`, logging 'paywalled' and skipping, not pre-filtering) (Implements test T018).
- [ ] T023 [US2] Implement fallback logic to fetch and parse abstract if full-text is unavailable or paywalled (Implements test T018).
- [ ] T024 [US2] Handle edge cases: log "unparseable" or "insufficient data" for missing metrics without crashing (Implements test T018).
- [ ] T027 [US2] Generate a report snippet in `data/processed/extraction_stats.json` detailing success rate and failure reasons immediately after saving params (Implements test T018).
- [ ] T028.1 [US2] Implement logic to calculate the delta in extraction success rates between full-text and abstract modes, and generate explicit 'sensitivity_delta_report.json' artifact reporting the delta in the final audit (FR-008) (Implements test T018).
- [ ] T026 [US2] Save extracted parameters to `data/processed/extracted_params.json` with source citation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Observed Power, MDES, and Generate Audit Report (Priority: P3)

**Goal**: Calculate Observed Statistical Power (as required by FR-004 literal text) AND Minimum Detectable Effect Size (MDES) using `statsmodels`, and generate a summary report with histogram, disclaimers, and success metrics.

**Independent Test**: Run `03_compute_sensitivity.py` on synthetic known parameters and verify output matches theoretical Observed Power and MDES; run `04_generate_report.py` to verify histogram and disclaimer presence.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for Observed Power and MDES calculation logic in `tests/unit/test_sensitivity.py`.
- [ ] T030 [P] [US3] Contract test for final report JSON in `tests/contract/test_schemas.py`.

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/03_compute_sensitivity.py` to calculate BOTH Observed Statistical Power (as per FR-004 literal requirement) AND MDES (as per Plan Pivot) using `statsmodels.stats.power` (Implements test T029).
- [ ] T032 [US3] Implement logic to handle F-statistic conversion to effect size if degrees of freedom are available and clamp power values > 1.0 (Implements test T029).
- [ ] T033 [US3] Save Observed Power and MDES results to `data/processed/power_audit_results.json`.
- [ ] T039.0 [US3] Explicitly calculate the 'fraction of studies with power < 0.8' metric (based on Observed Power calculation for FR-004 compliance) as required by SC-002 (Implements test T029).
- [ ] T039.1 [US3] Output the 'fraction of studies with power < 0.8' metric to `data/processed/success_metrics.json` (Implements test T029).
- [ ] T034 [US3] Implement `code/04_generate_report.py` to aggregate results and generate histogram (matplotlib).
- [ ] T035 [US3] Add mandatory disclaimer text: "Observed power is a monotone function of the p-value and should not be used for post-hoc validation (Hoenig & Heisey).." to report (Implements test T029).
- [ ] T037 [US3] Generate final audit report (Markdown) in `data/processed/audit_report.md` including MDES distribution, sensitivity delta report (from T028.1), and the 'fraction of studies with power < 0.8' metric (read from `data/processed/success_metrics.json` generated by T039.1) (Implements test T030).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T038 [P] Update `docs/constitution.md` with links to research validation steps.
- [ ] T039.2 [P] Run full pipeline integration test on a small subset of representative datasets.
- [ ] T040 [P] Validate `quickstart.md` instructions against actual execution.
- [ ] T041 [P] Refactor `code/utils/` modules to remove duplication and improve readability; ensure `oa_checker.py` and `parsers.py` are decoupled.
- [ ] T042 [P] Run performance harness on top datasets; verify memory usage of `03_compute_sensitivity.py` stays within 7GB limit.
- [ ] T043 [P] Run full pipeline on a subset of datasets; verify total execution time stays within 6-hour CI limit.
- [ ] T044 [P] Implement memory usage harness: Run `03_compute_sensitivity.py` on top 5 datasets; assert peak RSS < 7GB; fail if exceeded.
- [ ] T045 [P] Implement execution time harness: Run full pipeline on top datasets; assert total time < 6h; fail if exceeded.

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
- **User Story 2 (P2)**: Depends on US1 completion (needs `data/raw/openml_metadata.json` as input)
- **User Story 3 (P3)**: Depends on US2 completion (needs `data/processed/extracted_params.json` as input)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Utils/Helpers before core logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- Tests for any US can run in parallel with implementation of other parts of the same US

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for API retry logic in tests/unit/test_api_client.py"
Task: "Contract test for data/raw/openml_metadata.json against contracts/dataset_metadata.schema.yaml"

# Launch all models for User Story 1 together:
Task: "Implement code/utils/api_client.py with OpenML connection"
Task: "Implement code/utils/oa_checker.py to validate Open Access status"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify metadata extraction)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Extraction logic)
4. Add User Story 3 → Test independently → Deploy/Demo (MDES & Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Ingestion)
   - Developer B: User Story 2 (Parsing) - *Note: Can start once US1 data structure is defined, but needs US1 output to run*
   - Developer C: User Story 3 (Analysis) - *Note: Can start once US2 data structure is defined*
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
- **CRITICAL**: All data processing must run on CPU-only CI (limited cores, 7GB RAM). No GPU, no 8-bit quantization, no heavy model training. Use `statsmodels` for all statistical calculations.