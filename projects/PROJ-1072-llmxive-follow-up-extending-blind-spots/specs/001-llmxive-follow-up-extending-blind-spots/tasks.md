# Tasks: llmXive follow-up: extending "Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models"

**Input**: Design documents from `/specs/001-blind-spots-order-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per `plan.md` structure)
- **Data**: `data/raw/`, `data/filtered/`, `data/traces/`, `data/results/`
- **Utilities**: `code/utils/`

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

- [ ] T001 Create project structure per `plan.md` (create `code/`, `tests/`, `data/` directories)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (include `datasets`, `transformers`, `torch`, `sentence-transformers`, `scikit-learn`, `scipy`, `pandas`)
- [ ] T003 [P] Configure linting (ruff/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/utils/hashing_utils.py` for artifact content hashing (Constitution Principle V)
- [ ] T005 Implement `code/utils/logging_config.py` for structured logging across pipeline stages
- [ ] T006 [P] Create specific YAML schema files: `task-record.schema.yaml`, `cot-trace.schema.yaml`, `analysis-result.schema.yaml` in `specs/001-blind-spots-order-analysis/contracts/`
- [ ] T007 Implement `code/utils/dataset_integrity.py` for strict field validation (FR-006)
- [ ] T008 Implement `code/utils/semantic_matcher.py` using `all-MiniLM-L6-v2` for paraphrase detection (FR-011)
- [ ] T009 Create `code/run_pipeline.sh` orchestrator script

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Pre-filtering (Priority: P1) 🎯 MVP

**Goal**: Download *Blind-Spots-Bench*, filter for "Abstract Reasoning" and "Object-Centric", and validate data integrity.

**Independent Test**: Run `code/01_download_and_filter.py` and verify `data/filtered/filtered_tasks.jsonl` contains only target categories with valid `constraint` fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are not explicitly requested in the spec for this stage, but unit tests for the parser are required in the plan.
> **TDD Rule**: Tests MUST be written and FAIL before implementation.

- [ ] T010 [P] [US1] Unit test for category filtering logic in `tests/unit/test_filtering.py`
- [ ] T011 [P] [US1] Unit test for integrity check (missing `constraint` field) in `tests/unit/test_integrity.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_download_and_filter.py`: Download dataset from canonical arXiv source using `datasets` library
- [ ] T013 [US1] Implement filtering logic in T012: Retain only "Abstract Reasoning" and "Object-Centric" categories
- [ ] T014 [US1] Implement integrity check in T012: Halt execution and log specific IDs if `constraint` field is missing (FR-006, FR-001). **MUST** `raise SystemExit(1)` on failure to enforce hard stop.
- [ ] T015 [US1] Write filtered data to `data/filtered/filtered_tasks.jsonl` with checksum generation
- [ ] T016 [US1] Add CLI arguments for dataset path and output path in T012

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Pilot Study & Threshold Validation (Sub-phase of Phase 3)

**Goal**: Validate semantic matching threshold on a small pilot set before full-scale generation.

- [ ] T040 [US1] Implement `code/pilot_study.py`: Generate CoT traces for a small pilot set (N=10) using the filtered dataset.
- [ ] T041 [US1] Implement `code/validate_pilot.py`: Load pilot traces and prompt experts (or use a rule-based oracle) to label "Constraint Mention" (Yes/No) for N=10 traces.
- [ ] T042 [US1] Implement `code/tune_threshold.py`: Iterate cosine similarity threshold (range -0.95) to maximize agreement between automated semantic match and human/oracle labels. Select optimal threshold and save to `data/pilot/tuned_threshold.json`.

**Checkpoint**: Threshold validated - ready for full-scale generation

---

## Phase 4: User Story 2 - CoT Trace Generation and Parsing (Priority: P2)

**Goal**: Generate deterministic CoT traces using a 4-bit quantized LLM and parse them for constraint mentions.

**Independent Test**: Run `code/02_generate_cot.py` on a sample of 2 tasks and verify `code/03_parse_and_classify.py` correctly identifies first/last constraint offsets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T050 [P] [US2] Unit test for constraint string matching (word boundary check) in `tests/unit/test_parser.py`
- [ ] T051 [P] [US2] Unit test for semantic equivalence threshold in `tests/unit/test_semantic_matcher.py`

### Implementation for User Story 2

- [ ] T052 [US2] Implement `code/02_generate_cot.py`: Load 4-bit quantized model (Llama-3-8B-Int4 or Mistral-7B-Int4) with `device="cpu"` (FR-002, FR-009)
- [ ] T053 [US2] Implement inference loop in T052: Generate traces with `temperature=0.0`, enforce **Fixed 10-minute wall-clock timeout** per task (FR-012). **If timeout occurs, log error and skip task; do NOT retry with extended time.**
- [ ] T054 [US2] Implement error handling in T052: Log timeout/empty response errors and skip task without crashing (Edge Case)
- [ ] T055 [US2] Implement Memory Guard in T052: If OOM, fallback to smaller model (Mistral-7B) or reduce context window (Plan T010).
- [ ] T056 [US2] Write raw CoT traces to `data/traces/cot_traces.jsonl` immediately upon generation (Constitution Principle VI). **Path MUST be `data/traces/` not `data/processed/`.**
- [ ] T057 [US2] Implement Stopping Rule Check in T052: If effective sample size < 40 (MVS) after generation, halt and report "Underpowered" (Plan T012).
- [ ] T058 [US2] Implement `code/03_parse_and_classify.py`: Load traces and task records
- [ ] T059 [US2] Implement exact string matching in T058: Find first/last character offset of constraint in the **ENTIRE trace** (FR-003). **Do NOT restrict to first/last 256 tokens.**
- [ ] T060 [US2] Implement semantic matching in T058: Use `all-MiniLM-L6-v2` and tuned threshold from T042 to detect paraphrased constraints (FR-011)
- [ ] T061 [US2] Handle edge cases in T058: Word-boundary matching to avoid false positives, null flags for missing constraints

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Classification and Statistical Analysis (Priority: P3)

**Goal**: Classify errors (Perceptual/Procedural/Correct) and perform statistical analysis.

**Independent Test**: Provide a hand-labeled sample to `code/03_parse_and_classify.py` and verify labels match; run `code/04_statistical_analysis.py` to verify p-value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T062 [P] [US3] Unit test for rule-based classifier logic in `tests/unit/test_classifier.py`
- [ ] T063 [P] [US3] Unit test for Fisher's Exact vs. Chi-squared trigger logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T064 [US3] Implement classifier logic in `code/03_parse_and_classify.py`: Label traces as Perceptual, Procedural, or Correct based on first/last mention (FR-004). **Logic MUST be non-tautological: Predictor = Temporal Pattern, Outcome = Ground Truth (from dataset).**
- [ ] T065 [US3] Implement `code/04_statistical_analysis.py`: Compute proportions of error types per category (FR-005)
- [ ] T066 [US3] Implement Test Selection in T065: If expected cell counts < 5, select Fisher's Exact; else Chi-squared (Plan T017).
- [ ] T067 [US3] Implement Framing Injection in T065: Explicitly set `framing` field to "Associational" in output (FR-007). **Do NOT add negative constraints like "no causal".**
- [ ] T068 [US3] Implement Multiple Comparison Correction in T065: Apply Bonferroni if N<100, else Benjamini-Hochberg (FR-008, Plan T018).
- [ ] T069 [US3] Compute p-value and statistic in T065.
- [ ] T070 [US3] Generate `statistical_report.json` (SSoT) with all results.

**Manual Step: Human Expert Annotation**
> **Note**: The following is a manual step outside automated code execution.
> 1. Generate annotation request file using T071.
> 2. Human expert labels N=30 traces for "Task Outcome" (Correct/Incorrect) and "Constraint Mention" (Yes/No).
> 3. Save results to `data/validation/ground_truth_labels.jsonl`.

- [ ] T071 [US3] Implement `code/generate_annotation_request.py`: Generate a request file for N=30 traces to be labeled by human experts (FR-010, SC-006). **Sample size MUST be 30, not 5.**
- [ ] T072 [US3] Implement `code/ingest_human_labels.py`: Ingest labels from `data/validation/ground_truth_labels.jsonl` (FR-010).
- [ ] T073 [US3] Implement `code/validate_classifier.py`: Compare automated labels (T064) against T072 labels to compute agreement rate (FR-010, SC-006).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting (Polish)

**Purpose**: Final validation, artifact hashing, and documentation.

- [ ] T080 [P] Implement `code/generate_paper_sections.py`: Generate final paper sections based on `statistical_report.json` (Plan T023).
- [ ] T081 [P] Implement `code/update_state.py`: Hash `statistical_report.json` and `data/` artifacts, write to project state YAML (Plan T024).
- [ ] T082 [P] Implement `code/06_consistency_check.py`: Re-run parser on fixed sample, calculate agreement rate, and write `data/results/consistency_report.json` with the calculated agreement rate percentage (SC-005).
- [ ] T083 [P] Generate content hashes for all `data/` and `code/` artifacts and record in `state/` (Constitution Principle V)
- [ ] T084 [P] Update `quickstart.md` with reproduction steps and power analysis limitations
- [ ] T085 [P] Run end-to-end integration test in `tests/integration/test_end_to_end.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **Note**: T006 (Schemas) is NOT a blocker for T012 (Download). T012 depends only on T002 (Env). T006 runs in parallel.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T058 (Load traces and task records).
  - **Strict Data Flow**: T014 (Halt if missing) MUST complete before T052 (Generation). If T014 halts, T052 never runs.
  - **Strict Data Flow**: T052-T056 (Generation) MUST complete before T058-T061 (Parsing)
  - **Strict Data Flow**: T058-T061 (Parsing) MUST complete before T064-T070 (Classification/Stats)
  - **Strict Data Flow**: T071 (Generate Request) -> T072 (Ingest Labels) -> T073 (Validate)
  - **Strict Data Flow**: T040 (Pilot) depends on T015 (Filtered Data).
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data) and Pilot (T040-T042)
- **User Story 3 (P3)**: Depends on US2 completion (requires parsed traces) and T071 (Human Labels)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (T010/T011 before T012; T050/T051 before T052; T062/T063 before T064)
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Unit tests for US1, US2, US3 can run in parallel once code is drafted
- Hashing and validation (Phase 6) can run in parallel once all data is generated

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test data acquisition and filtering independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Pilot Study (Phase 3.5) → Validate threshold
4. Add User Story 2 → Test independently → Deploy/Demo (Requires GPU/CPU scaling strategy)
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data)
   - Developer B: Pilot Study (Threshold) - *Depends on US1 data*
   - Developer C: User Story 2 (Model/Parser) - *Depends on US1 data and Pilot threshold*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: Default sample size N=30 for validation; inferential stats only if N≥40 (Plan Note)
- **Critical Constraint**: Fixed 10-minute timeout per task; Global runtime limit 6 hours. (FR-012, FR-009)
- **Critical Constraint**: No synthetic data fallback; failed real fetch MUST raise (Data Hygiene)
- **TDD Rule**: Tests (T010, T011, etc.) MUST be listed before their corresponding implementation tasks in the same phase.
- **Deprecated**: T035 is deprecated and removed.
- **Phase 3.5**: Pilot study is a sub-phase of Phase 3, required before Phase 4 (Generation).