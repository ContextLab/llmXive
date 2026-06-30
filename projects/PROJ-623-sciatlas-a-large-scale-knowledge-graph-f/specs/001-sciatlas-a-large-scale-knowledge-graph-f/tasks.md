# Tasks: Reproduce & Validate SciAtlas Knowledge Graph

**Input**: Design documents from `/specs/001-reproduce-validate-sciatlas/`
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

- [X] T001 Create project structure per implementation plan (`external/SciAtlas`, `src/`, `tests/`, `output/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (requests, pytest, pyyaml, pandas, scikit-learn, openalex)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Setup GitHub Actions workflow `.github/workflows/reproduce_validate.yml` for CPU-only runners

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `src/utils/retry_utils.py` with exponential backoff (1s, 2s, 4s) for network failures (FR-003)
- [X] T006 Create `src/validation/schema_loader.py` to load YAML contracts from `contracts/`
- [X] T007 Define `contracts/paper-record.schema.yaml` and `contracts/artifact.schema.yaml` (FR-002, US-2)
- [X] T008 Implement `src/validation/artifact_validator.py` to parse JSON and assert non-empty `title`, `abstract`, `source_id` (US-2)
- [X] T009 Create `src/validation/gold_standard_validator.py` to load a curated "Gold Standard" CSV and check recall (US-3)
- [X] T010 Implement logging infrastructure in `src/utils/logger.py` to write all API calls to `reproduction_log.txt` (FR-005)
- [X] T011 [P] Create `external/SciAtlas/run_sciatlas.py` stub that wraps OpenAlex client for sample queries (US-1)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Core Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored SciAtlas entry point to generate primary reproduction artifacts without human intervention.

**Independent Test**: A single CI job runs the entry script with a fixed, minimal query. The test passes if the script exits with code 0 and produces at least one non-empty output file in `output/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for `run_sciatlas.py` execution in `tests/contract/test_run_sciatlas.py`
- [X] T013 [P] [US1] Integration test for API retry logic in `tests/integration/test_api_retries.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `external/SciAtlas/run_sciatlas.py` to query OpenAlex for "graph neural networks" with sampling (top 100) (FR-001)
- [X] T015 [US1] Integrate `src/utils/retry_utils.py` into `run_sciatlas.py` to handle 429 errors (FR-003)
- [X] T016 [US1] Ensure `run_sciatlas.py` writes results to `output/reproduction_run_001.json` (US-1)
- [X] T017 [US1] Add error handling for empty results to output "No results found" artifact (Edge Case)
- [X] T018 [US1] Verify `run_sciatlas.py` completes within 30 minutes on CI (SC-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Artifact Integrity & Completeness (Priority: P2)

**Goal**: Verify that generated artifacts contain valid data structures and meet minimum content thresholds.

**Independent Test**: A validation script parses the output JSON/Markdown and asserts the presence of required fields and record count ≥ 1.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for schema validation in `tests/contract/test_schema_contracts.py`
- [X] T020 [P] [US2] Integration test for artifact validator in `tests/integration/test_artifact_validator.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `src/validation/artifact_validator.py` to check `title` length ≥ 5 and `abstract` length ≥ 20 (US-2)
- [X] T022 [US2] Add logic to verify at least 3 records contain non-null `doi` or `arxiv_id` (US-2)
- [X] T023 [US2] Integrate `src/validation/schema_loader.py` to enforce `contracts/paper-record.schema.yaml` (FR-002)
- [X] T024 [US2] Update `run_sciatlas.py` to trigger `artifact_validator.py` automatically after generation (FR-002)
- [X] T025 [US2] Log validation results to `reproduction_log.txt` (FR-005)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Specific Paper Claim (Priority: P3)

**Goal**: Execute sub-pipelines (Literature Review, Trend Report) and confirm qualitative match to paper claims.

**Independent Test**: Run the `literature_review` skill with a predefined topic and compare generated summary length/structure against baseline.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for `literature_review` output in `tests/contract/test_literature_review.py`
- [X] T027 [P] [US3] Gold Standard recall test in `tests/gold_standard/test_recall.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `external/SciAtlas/agent-skill/literature_review.py` to process "knowledge graphs in healthcare" (US-3)
- [X] T029 [US3] Implement `external/SciAtlas/agent-skill/trend_report.py` to generate time-series JSON (US-3)
- [X] T030 [US3] Add validation in `src/validation/gold_standard_validator.py` to check for ≥ 3 citations and ≥ 150 words (US-3)
- [X] T031 [US3] Implement NLP-based classification using `scikit-learn` to distinguish theoretical correlation from physical measurement evidence (Reviewer: Marie Curie)
- [X] T032 [US3] Load curated "Gold Standard" CSV (50 known papers with physical evidence) into `tests/gold_standard/gold_standard.csv` (Reviewer: Marie Curie)
- [X] T033 [US3] Update `run_sciatlas.py` to run `gold_standard_validator.py` and report Recall@10 (US-3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T034 [P] Update `docs/quickstart.md` with sample queries and expected outputs
- [X] T035 Code cleanup and refactoring of `external/SciAtlas` wrappers
- [X] T036 Performance optimization: ensure OpenAlex sampling fits within 7GB RAM (SC-003)
- [X] T037 [P] Additional unit tests for `retry_utils.py` in `tests/unit/test_retry_utils.py`
- [X] T038 Run `quickstart.md` validation in CI
- [X] T039 Final review of `reproduction_log.txt` format for traceability (FR-005)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 for data access, includes reviewer-specific validation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for run_sciatlas.py in tests/contract/test_run_sciatlas.py"
Task: "Integration test for API retry logic in tests/integration/test_api_retries.py"

# Launch implementation tasks in parallel where possible:
Task: "Implement run_sciatlas.py to query OpenAlex"
Task: "Integrate retry_utils.py into run_sciatlas.py"
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
4. Add User Story 3 → Test independently → Deploy/Demo (includes reviewer validation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Pipeline Execution)
   - Developer B: User Story 2 (Validation Logic)
   - Developer C: User Story 3 (Claim Reproduction + Reviewer Fix)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Reviewer Fix**: T031-T033 specifically address the "Marie Curie" review regarding physical measurement vs. theoretical correlation by implementing an NLP-based classification against a curated Gold Standard.
- **Feasibility**: All tasks assume CPU-only execution on GitHub Actions free tier (limited cores, 7GB RAM). No GPU or heavy local DBs.
