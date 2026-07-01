# Tasks: Data Journalist Agent Reproduction

**Input**: Design documents from `/specs/001-data-journalist-agent-transforming-data/`
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

- [X] T001 Create project structure per implementation plan in `pro/skills/data2story-pro/`
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (CPU-only: `langchain`, `datasets`, `requests`, `jinja2`, `pytest`, `pandas`, `pyyaml`)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement Constitution Gate: Script `tests/integration/check_constitution.py` to verify `projects/PROJ-719-data-journalist-agent-transforming-data/.specify/memory/constitution.md` exists; exit code 1 if missing.
- [X] T005 Implement Dataset Fallback Strategy & Wrapper: Script `tests/integration/run_with_fallback.py` to:
 1. Fetch NASA GISS Meteorite Landings (URL: `) if vendored data is missing.
 2. Validate fetched data contains `mass`, `year`, `name`, `class`, `latitude`, `longitude`.
 3. If variables missing, write `artifacts/audit_report.json` with schema: `{"status": "NEEDS_CLARIFICATION", "missing_vars": [...]}` and exit code 1.
 4. Invoke `pro/skills/data2story-pro/evals/scripts/run_evals.py` with `scenario=01_meteorite_flagship.md`.
 5. Wrap API calls in `try/except` blocks for 429/500 errors to log and continue (FR-005).
- [X] T006 [P] Setup Environment Configuration: Create `.env.example` for API keys (OpenRouter/HF) with default fallback logic if keys are absent
- [X] T009A [P] Implement Gold Standard Extraction Script: Script `tests/integration/generate_gold_standard.py` to:
 1. Parse `pro/skills/data2story-pro/evals/scenarios/01_meteorite_flagship.md`.
 2. If file missing, exit 1 with error "Source scenario file missing; check submodule".
 3. Extract factual claims using regex/LLM prompt logic into `artifacts/gold_standard_claims.json`.
 4. Schema: `[{ "claim_text": str, "source_context": str, "expected_value": str, "claim_type": "native|fallback" }]`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 & 2 - Execution & Traceability (Priority: P1, P2) 🎯 MVP

**Goal**: Execute the pipeline, validate evidence traceability, and implement the validation logic.

**Independent Test**: Run `run_with_fallback.py` and verify `cell_registry.json` exists, then run `validate_traceability.py` to compare against `gold_standard_claims.json`.

### Implementation for User Story 1 (Execution)

- [X] T012 [P] [US1] Verify Pipeline Execution: Run `tests/integration/run_with_fallback.py` (from T005) with `scenario=01_meteorite_flagship.md`. Verify exit code 0 and that `artifacts/` contains `index.html`, `audit_report.json`, `cell_registry.json`.
- [X] T013 [US1] Ensure output directory structure is created: `artifacts/<scenario>/` containing `index.html`, `audit_report.json`, `cell_registry.json`
- [X] T014 [US1] Implement logging for `run_with_fallback.py` to capture dataset fetch status and pipeline errors
- [X] T015 [US1] Verify `run_evals.py` completes without runtime errors (exit code 0) on CPU-only runner

### Implementation for User Story 2 (Traceability)

- [X] T019 [US2] Implement `validate_traceability.py` in `tests/integration/` to load `cell_registry.json` and `gold_standard_claims.json`.
- [X] T020 [US2] Implement Census Validation Logic: Compare **every** claim in Gold Standard against Registry (no sampling).
 - **Logic**: If `generation_mode: fallback` is present in registry for a claim, mark as "Valid Fallback" (not hallucination).
 - **Logic**: If `generation_mode: native` is present, verify claim matches Gold Standard.
- [X] T021 [US2] Calculate metrics and define pass/fail:
 - **Metrics**: `Registry Completeness (Recall)` and `Hallucination Rate (1 - Precision)`.
 - **Fail Condition**: Fail ONLY if `Recall < 100%` for claims marked as `native` OR if `Precision < 100%` for claims marked as `native`.
 - **Pass Condition**: Pass if all missing claims are accounted for by `generation_mode: fallback` AND native claims meet [deferred] recall/precision.
- [X] T022 [US2] Verify `Inspector` agent output `cell_registry.json` contains valid `claim_id` -> `source_cell` mappings for all narrative claims
- [X] T023 [US2] Update `audit_report.json` to include Gold Standard metrics (Precision/Recall values) and fallback counts

### Tests for User Story 1 & 2

- [X] T010 [P] [US1] Integration test for pipeline execution in `tests/integration/test_data2story_pipeline.py` (Verify exit code and file existence)
- [X] T011 [P] [US1] Edge case test for API failure in `tests/integration/test_edge_cases.py` (Mock 429 error, verify pipeline continues)
- [X] T017 [P] [US2] Contract test for registry schema in `tests/contract/test_cell_registry.py`
- [X] T018 [P] [US2] Integration test for Gold Standard comparison in `tests/integration/validate_traceability.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Multimodal Asset Generation (Priority: P3)

**Goal**: Confirm `Designer` agent generates at least one multimodal asset or a documented placeholder.

**Independent Test**: Inspect `artifacts/<scenario>/assets/` for non-HTML files or placeholder artifacts with metadata.

### Implementation for User Story 3

- [X] T027 [US3] Implement Fallback Logic in `Designer` agent (or wrapper): If external API fails, generate `placeholder_image.png` with metadata `generated_by: "Designer (Fallback)"` and `generation_mode: "fallback"`
- [X] T028 [US3] Ensure `Designer` attempts at least one asset generation request (image, audio, or video)
- [X] T029 [US3] Verify output directory contains at least one non-HTML asset (real or placeholder)
- [X] T030 [US3] Update `audit_report.json` to distinguish between `native` and `placeholder` asset counts
- [X] T031 [US3] Verify `index.html` links to the generated or placeholder assets correctly

### Tests for User Story 3

- [X] T025 [P] [US3] Integration test for asset existence in `tests/integration/test_multimodal_assets.py`
- [X] T026 [P] [US3] Edge case test for placeholder generation in `tests/integration/test_fallback_assets.py` (Simulate API block)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T032 [P] Documentation updates in `docs/` for `run_with_fallback.py`, `validate_traceability.py`, and `generate_gold_standard.py`
- [X] T033 Code cleanup and refactoring of error handling paths
- [X] T034 Performance optimization: Ensure memory usage stays < 6GB during dataset loading
- [X] T035 [P] Run `quickstart.md` validation if available
- [X] T036 Final End-to-End Verification: Run full pipeline from scratch and verify all Success Criteria (SC-001 to SC-004) are met

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`cell_registry.json`) and Gold Standard (T009A)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output (pipeline execution)

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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