# Tasks: Evaluating the Effectiveness of Prompt Engineering for LLM-Based Code Translation

**Input**: Design documents from `/specs/001-prompt-engineering-code-translation/`
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

- [X] T001a [P] Create directory structure: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/prompts/`, `data/evaluation/`, `state/`, `state/checksums/`
- [X] T001b [P] Create `.gitignore` to exclude `data/raw/`, `data/processed/`, `__pycache__`, `*.pyc`, `venv/`
- [X] T001c [P] Create initial `requirements.txt` and `package.json` placeholder files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Implement `src/utils/checksum_artifacts.py` to generate SHA-256 hashes for `data/raw/` files and write results to `state/checksums/` (Constitution Principle III)
- [X] T007 Implement `src/utils/update_state.py` to track artifact hashes and update `state/projects/PROJ-230-evaluating-the-effectiveness-of-prompt-e.yaml` (Constitution Principle V)
- [X] T008 Implement `src/utils/logging.py` with structured JSON logging for all prompts, seeds, and raw outputs
- [ ] T009 Implement `src/utils/timeout_utils.py` for enforcing 120s API timeouts and 10s test timeouts
- [~] T010 Create `data/prompts/` directory and add placeholder files for the four prompt conditions: `zero_shot_basic.txt`, `zero_shot_style.txt`, `few_shot_basic.txt`, `few_shot_style.txt`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and prepare a CPU-tractable corpus of ≥200 Python-to-JavaScript pairs from HuggingFace (CodeTrans/BigCode) without exceeding 7GB RAM.

**Independent Test**: Verify `src/ingestion/download_datasets.py` creates a local CSV with ≥200 valid pairs and logs a memory peak <7GB during execution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Contract test for dataset fetch in `tests/contract/test_dataset_fetch.py`
- [X] T012 [P] [US1] Integration test for memory-constrained preprocessing in `tests/integration/test_preprocess_memory.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/ingestion/download_datasets.py` to fetch from `codeparrot/code-trans-py-js` and `bigcode/evaluation` via `datasets` library, explicitly **caching** raw data to `data/raw/` before any processing, and extracting `python_code` and `javascript_code` columns
- [~] T013b [US1] Implement validation logic to exclude corrupted entries (missing code, non-string types) from the cached dataset
- [ ] T013c [US1] Implement sampling/chunking logic to ensure the processed dataset footprint remains ≤7GB RAM, outputting to `data/processed/corpus.csv`
- [ ] T014 [US1] Add validation logic to ensure the final `data/processed/corpus.csv` contains ≥200 valid entries
- [~] T015 [US1] Integrate `src/utils/checksum_artifacts.py` to hash `data/raw/` files before preprocessing (DEPENDS ON T006)
- [~] T016 [US1] Add logging for excluded entries and memory usage statistics, specifically logging peak memory usage against SC-004 constraint

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Prompt Condition Execution (Priority: P2)

**Goal**: Execute four distinct prompt conditions against the corpus using CodeLlama-7B via HuggingFace Inference API, storing outputs deterministically.

**Independent Test**: Verify `src/execution/run_inference.py` creates distinct subdirectories for each condition with generated JS files matching inputs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Contract test for API client in `tests/contract/test_api_client.py`
- [X] T019 [P] [US2] Integration test for timeout/retry logic in `tests/integration/test_inference_retry.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `src/execution/api_client.py` with exponential backoff (limited retry attempts), 120s timeout, error handling for malformed responses, using endpoint ` No address associated with hostname)"))]
- [ ] T021 [US2] Implement `src/execution/run_inference.py` to iterate through the corpus and apply the four prompt conditions from `data/prompts/`
- [ ] T022 [US2] Ensure deterministic execution by pinning seeds and logging exact prompt text, model version, and seed for every request
- [ ] T023 [US2] Implement output storage to `data/evaluation/raw_translations/` organized by condition directory
- [ ] T024 [US2] Add logic to log "failed translation" for non-code outputs (e.g., "I cannot do that")
- [ ] T025b [US2] Implement `src/evaluation/generate_translations_log.py` to aggregate all prompts, seeds, and raw outputs into a **version-controlled CSV** (`data/evaluation/raw_translations_log.csv`) with columns: `prompt_condition`, `seed`, `raw_output`, `timestamp`, and commit this artifact to git (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Functional Correctness and Quality Analysis (Priority: P3)

**Goal**: Evaluate generated JS against translated unit tests, compute quality metrics, and perform statistical analysis.

**Independent Test**: Verify `src/evaluation/statistical_analysis.py` produces a CSV with `pass_rate`, `complexity`, `prompt_condition`, and valid p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for test translation in `tests/contract/test_test_translation.py`
- [ ] T026 [P] [US3] Integration test for Node.js test runner in `tests/integration/test_node_runner.py`

### Implementation for User Story 3

- [ ] T027a [US3] Select and document a deterministic transpiler (e.g., `transcrypt` or custom AST converter) for converting Python unit tests to JavaScript
- [ ] T027 [US3] Implement `src/evaluation/translate_tests.py` to convert Python unit tests to JavaScript using the selected deterministic transpiler, strictly forbidding LLM-based test generation (FR-003)
- [ ] T028 [US3] Implement `src/evaluation/run_node_tests.py` to execute translated tests against generated JS in a Node.js environment, enforcing 10s timeout per test (DEPENDS ON T027 output)
- [ ] T029 [US3] Implement `src/evaluation/compute_quality.py` using ESLint `complexity` rule (config: `--rule complexity: [, 10]`) to calculate cyclomatic complexity and LOC for each translation
- [ ] T030 [US3] Implement `src/evaluation/statistical_analysis.py` to perform Chi-square (correctness) and ANOVA (quality) with Bonferroni correction
- [ ] T031 [US3] Generate final `data/evaluation/statistical_summary.csv` containing `p_value`, `confidence_interval`, `effect_size`, and `prompt_condition`
- [ ] T032 [US3] Integrate `src/utils/update_state.py` to update state after evaluation completion
- [ ] T032b [US3] Implement `src/utils/measure_runtime.py` to measure and log total pipeline execution time against the 6-hour SC-003 constraint

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` including quickstart guide for running the full pipeline
- [ ] T040 Code cleanup and refactoring of error handling paths
- [ ] T041 Performance optimization for API request batching (if rate limits allow)
- [ ] T042 [P] Additional unit tests in `tests/unit/` for utility functions
- [ ] T043 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output availability

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
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset fetch in tests/contract/test_dataset_fetch.py"
Task: "Integration test for memory-constrained preprocessing in tests/integration/test_preprocess_memory.py"

# Launch all models for User Story 1 together:
Task: "Implement download_datasets.py in src/ingestion/download_datasets.py"
Task: "Implement preprocess_corpus.py in src/ingestion/preprocess_corpus.py"
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
- **Critical Constraint**: {{claim:c_65af1cd1}} No local LLM training or 8-bit quantization allowed. 