# Tasks: Reproduce & Validate StepAudio 2.5 Technical Report

**Input**: Design documents from `/specs/001-reproduce-stepaudio-2.5/`
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

## Phase 0: Research, Feasibility & Scope Definition (BLOCKING)

**Purpose**: Verify scope, dataset, and model feasibility BEFORE any code is written.
**CRITICAL**: This phase must complete and produce `research.md` before Phase 1 begins.

- [X] T000 [US1] Verify the validity of the arXiv identifier. If invalid, search for alternative verified sources (HuggingFace, GitHub) matching "StepAudio 2.5". If no valid source found within search window, document `E_SCOPE_INVALID` in `research.md` and halt project.
- [X] T001 [US1] Verify `WenetSpeech_testnet_long.json` contains `transcription` field (ground truth). Verify `audio_path` entries point to remote URLs (streaming) or fit within 14GB disk. If local paths imply >14GB data, document `E_DISK_EXCEEDED` in `research.md` and halt.
- [X] T002 [US1] Analyze `external/wenetspeech-testnet-long/prepare.py` dependencies. Determine if the model fits within available RAM on a CPU. If model requires GPU or >7GB RAM without modification, document `E_MODEL_MISSING` in `research.md` and halt.
- [X] T003 [US3] Extract specific metrics (WER, MOS, Latency) and proxy strategies from the StepAudio 2.5 Technical Report. Define the exact reference values and statistical methods (Bootstrap vs. Binomial) to be used for validation. Document in `research.md`.

**Checkpoint**: Research complete. `research.md` must contain valid scope, dataset strategy, model feasibility status, and claim extraction.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T004 Create project structure per implementation plan: `mkdir -p src/validation src/config src/cli tests/contract tests/integration output external`
- [X] T005 Create `requirements.txt` with pinned versions (e.g., torch, scipy, librosa, jsonschema, pandas, pytest) as determined in `research.md`.
- [X] T006 [P] Configure linting (ruff) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `src/config/paths.yaml` to define input/output paths and artifact locations.
- [X] T008 [P] Create `src/validation/error_codes.py` defining `E_INVALID_INPUT`, `E_RESOURCE_LIMIT`, `E_NETWORK_TIMEOUT`, `E_MISSING_GROUND_TRUTH`, `E_SCOPE_INVALID`, `E_MODEL_MISSING`, `E_DISK_EXCEEDED` with specific integer codes and messages.
- [X] T009 [P] Create base `src/validation/metrics.py` with stubs for WER calculation and DNSMOS proxy logic. Stubs must include `def calculate_wer(...) -> float: raise NotImplementedError` and `def calculate_dns_mos(...) -> float: raise NotImplementedError`.
- [X] T010 Create `src/validation/logging_utils.py` for structured logging and metadata capture.
- [X] T011 Setup `src/validation/sampling.py` for stratified random sampling logic (speaker_id, duration).
- [X] T012 [P] Setup `contracts/` directory with `wenetspeech-config.schema.yaml`, `run-metadata.schema.yaml`, and `validation-report.schema.yaml`. Content must be generated based on the `contracts/` section in `plan.md`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: Design & Contracts (Validation Logic)

**Purpose**: Define data schemas and validation logic before implementation.

- [X] T013 [P] Design `run-metadata.schema.yaml` to include `strata_columns` and `statistical_method` fields as required by the plan.
- [X] T014 [P] Design the statistical testing logic in `research.md` context: Define exact Bootstrap Resampling (1000 iterations) and Exact Binomial Test parameters (N >= 30 vs N < 30) to be used in implementation.
- [X] T015 [P] Define the exact Markdown template structure for `validation_report.md` (headers, data mapping logic, "Confirmed"/"Discrepancy" tags) in `research.md` or a design document.

**Checkpoint**: Contracts and logic designed. Implementation can proceed.

---

## Phase 4: User Story 1 - Execute Vendored Entry Point (Priority: P1) 🎯 MVP

**Goal**: Trigger the execution of the vendored `prepare.py` script and handle execution environment constraints.

**Independent Test**: Running `python src/validation/runner.py` results in a non-zero exit code only on genuine failure and produces `output/run.log`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T016 [P] [US1] Contract test for error codes in `tests/contract/test_error_codes.py`. Assert `E_INVALID_INPUT == 1`, `E_MODEL_MISSING == 2`, etc., and that error messages match definitions in `src/validation/error_codes.py`.
- [X] T017 [P] [US1] Integration test for `prepare.py` execution flow in `tests/integration/test_full_run.py`. Mock `prepare.py` to return success/failure and verify `runner.py` handles exit codes correctly.

### Implementation for User Story 1

- [X] T018 [US1] Implement `src/validation/runner.py` wrapper to execute `external/wenetspeech-testnet-long/prepare.py`.
- [X] T019 [US1] Add pre-flight check in `runner.py` to verify `WenetSpeech_testnet_long.json` exists and contains `transcription` field (exit `E_MISSING_GROUND_TRUTH` if missing). Reference schema contract from T012/T013.
- [X] T020 [US1] Implement network retry logic in `runner.py` using `requests.adapters.HTTPAdapter` with `max_retries=3`, `backoff_factor=0.5`. If retries exhausted, exit with `E_NETWORK_TIMEOUT` and terminate run.
- [X] T021 [US1] Implement memory pressure detection in `runner.py` (using `psutil` or `resource`). If memory > 7GB, exit with `E_RESOURCE_LIMIT` and terminate run (DO NOT trigger chunked processing for RAM).
- [X] T022 [US1] Add logic to capture `run_metadata.json` (start time, end time, exit code, environment version, `statistical_method`, `strata_columns`).
- [X] T023 [US1] Implement scope validation in `runner.py` to check arXiv ID validity (exit `E_SCOPE_INVALID` if invalid). **Note**: This logic must align with T000 research output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 5: User Story 2 - Generate & Capture Real Artifacts (Priority: P2)

**Goal**: Ensure the pipeline produces tangible, non-empty artifacts and handles data constraints.

**Independent Test**: After execution, `output/` contains non-empty files matching expected schemas.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US2] Contract test for `results.json` schema in `tests/contract/test_schemas.py`.
- [X] T025 [P] [US2] Integration test for disk space management in `tests/integration/test_disk_management.py`.

### Implementation for User Story 2

- [X] T026 [US2] Implement chunked download and immediate deletion logic in `runner.py` to stay within 14GB disk limit. **Note**: Chunked download is for disk space only, NOT chunked model processing.
- [X] T027 [US2] Enforce sampling threshold defined in `research.md`: If `total_entries > MAX_PROCESSABLE_ENTRIES` (read from `research.md`), apply stratified sampling and log `strata_columns`.
- [X] T028 [US2] Implement artifact validation in `runner.py` to ensure output files are non-empty and structurally valid (JSON/CSV parsing).
- [X] T029 [US2] Add logic to map `WenetSpeech_testnet_long.json` input entries to output artifacts (verify count matches or is sampled correctly).
- [X] T030 [US2] Integrate `src/config/paths.yaml` to dynamically route output artifacts to `output/results.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Validate Against Paper Claims (Priority: P3)

**Goal**: Compare generated artifacts against the StepAudio 2.5 Technical Report claims and generate a validation report.

**Independent Test**: `validation_report.md` is generated with explicit "Confirmed", "Discrepancy", or "Needs Clarification" tags.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Contract test for `validation_report.md` structure in `tests/contract/test_schemas.py`.
- [X] T032 [P] [US3] Integration test for metric comparison logic in `tests/integration/test_validation.py`.

### Implementation for User Story 3

- [X] T033 [US3] Implement `src/validation/validator.py` to parse `output/results.json` and extract WER/MOS metrics.
- [X] T034 [US3] Implement statistical testing logic in `validator.py`:
    - If N >= 30: Use `scipy.stats` to perform Bootstrap Resampling (1000 iterations) for WER confidence interval.
    - If N < 30: Use `scipy.stats` to perform Exact Binomial Test for p-value against paper claim.
- [X] T035 [US3] Implement DNSMOS P.835 proxy logic in `src/validation/metrics.py` for TTS validation; add logic to flag "Needs Clarification" if paper claims human MOS.
- [X] T036 [US3] Generate `validation_report.md` in `output/` with sections for each paper claim, comparing against reproduced metrics. Use the template structure defined in T015.
- [X] T037 [US3] Add logic to flag discrepancies (>5% difference or outside CI) with `[NEEDS CLARIFICATION]` tags and potential causes (data drift, hyperparams). Align with Spec US3 acceptance criteria.
- [X] T038 [US3] Implement baseline comparison logic (e.g., against Whisper DNSMOS scores) for MOS validation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `quickstart.md` and `research.md`.
- [X] T040 Code cleanup and refactoring of `runner.py` and `validator.py`.
- [X] T041 Performance optimization for memory usage in `runner.py`.
- [X] T042 [P] Additional unit tests in `tests/unit/`.
- [X] T043 Run `quickstart.md` validation to ensure local reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - MUST start immediately. BLOCKS all other phases.
- **Setup (Phase 1)**: Depends on Phase 0 completion (scope must be valid).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **Design & Contracts (Phase 3)**: Depends on Foundational completion - BLOCKS implementation.
- **User Stories (Phase 4+)**: All depend on Foundational + Design phases completion.
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational + Design - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational + Design - May integrate with US1 but should be independently testable.
- **User Story 3 (P3)**: Can start after Foundational + Design - May integrate with US1/US2 but should be independently testable.

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
Task: "Contract test for error codes in tests/contract/test_error_codes.py"
Task: "Integration test for prepare.py execution flow in tests/integration/test_full_run.py"

# Launch all models for User Story 1 together:
Task: "Implement src/validation/runner.py wrapper"
Task: "Implement src/validation/error_codes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research (CRITICAL - blocks all)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: Design & Contracts
5. Complete Phase 4: User Story 1
6. **STOP and VALIDATE**: Test User Story 1 independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational + Design → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Research) together (or assign to lead researcher)
2. Once Phase 0 is done:
   - Team completes Setup + Foundational + Design together
3. Once Design is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Phase 0 tasks (T000-T003) MUST be completed before any other tasks.