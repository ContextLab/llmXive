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

- [X] T001 Create project structure per `plan.md` (create `code/`, `tests/`, `data/`, `data/raw/`, `data/filtered/`, `data/traces/`, `data/results/`, `data/pilot/`, `data/validation/`, `data/reports/` directories)
- [X] T002 Configure linting (ruff/black) and formatting tools (Create `pyproject.toml` with black/ruff settings and `.ruff.toml` with specific linting rules)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (include `datasets`, `transformers`, `torch`, `sentence-transformers`, `scikit-learn`, `scipy`, `pandas`, `statsmodels`)
- [X] T004 [P] Create specific YAML schema files: `task-record.schema.yaml`, `cot-trace.schema.yaml`, `analysis-result.schema.yaml` in `specs/001-blind-spots-order-analysis/contracts/`
- [X] T005 [P] Implement `code/utils/hashing_utils.py` for artifact content hashing (Constitution Principle V)
- [X] T006 [P] Implement `code/utils/logging_config.py` for structured logging across pipeline stages
- [X] T007 [P] Implement `code/utils/dataset_integrity.py` for strict field validation (FR-006)
- [X] T008 [P] Implement `code/utils/semantic_matcher.py` using `all-MiniLM-L6-v2` for paraphrase detection (FR-011)
- [X] T009 [P] Create `code/run_pipeline.sh` orchestrator script

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Acquisition and Pre-filtering (Priority: P1) 🎯 MVP

**Goal**: Download *Blind-Spots-Bench*, filter for "Abstract Reasoning" and "Object-Centric", and validate data integrity.

**Independent Test**: Run `code/01_download_and_filter.py` and verify `data/filtered/filtered_tasks.jsonl` contains only target categories with valid `constraint` fields.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests are not explicitly requested in the spec for this stage, but unit tests for the parser are required in the plan.
> **TDD Rule**: Tests MUST be written and FAIL before implementation.

- [X] T010 [P] [US1] Unit test for category filtering logic in `tests/unit/test_filtering.py`
- [X] T011 [P] [US1] Unit test for integrity check (missing `constraint` field) in `tests/unit/test_integrity.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/01_download_and_filter.py`: Download dataset from canonical arXiv source using `datasets` library
- [X] T013 [US1] Implement filtering logic in T012: Retain only "Abstract Reasoning" and "Object-Centric" categories. **Filter criteria**: `task_category in ['Abstract Reasoning', 'Object-Centric']`. **Output path**: `data/filtered/filtered_tasks.jsonl`.
- [X] T014 [US1] Implement integrity check in T012: Halt execution and log specific IDs if `constraint` field is missing (FR-006, FR-001). **MUST** generate `data/validation/integrity_error_report.json` with the count and IDs of missing constraints, then `raise SystemExit(1)` on failure to enforce hard stop.
- [X] T015 [US1] Write filtered data to `data/filtered/filtered_tasks.jsonl` with checksum generation
- [X] T016 [US1] Add CLI arguments for dataset path and output path in T012: `--input` (str, default=None), `--output` (str, default='data/filtered/filtered_tasks.jsonl').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Pilot Study & Threshold Validation (Sub-phase of Phase 3)

**Goal**: Validate semantic matching threshold on a small pilot set before full-scale generation.

- [X] T017 [US1] Implement `code/pilot_study.py`: Generate CoT traces for a small pilot set (N=10) using the filtered dataset. **Save to `data/pilot/` (separate from production traces)**.
- [X] T018 [US1] Implement `code/validate_pilot.py`: Load pilot traces and prompt experts (or use a rule-based oracle) to label "Constraint Mention" (Yes/No) for N=10 traces.
- [X] T019 [US1] Implement `code/tune_threshold.py`: Iterate cosine similarity threshold (range within the theoretical bounds of the metric) to maximize agreement between automated semantic match and human/oracle labels. Select optimal threshold and save to `data/pilot/tuned_threshold.json`.

**Checkpoint**: Threshold validated - ready for full-scale generation

---

## Phase 4: User Story 2 - CoT Trace Generation and Parsing (Priority: P2)

**Goal**: Generate deterministic CoT traces using a 4-bit quantized LLM and parse them for constraint mentions.

**Independent Test**: Run `code/02_generate_cot.py` on a sample of 2 tasks and verify `code/03_parse_and_classify.py` correctly identifies first/last constraint offsets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for constraint string matching (word boundary check) in `tests/unit/test_parser.py`
- [X] T021 [P] [US2] Unit test for semantic equivalence threshold in `tests/unit/test_semantic_matcher.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/02_generate_cot.py`: Load 4-bit quantized model (Llama-3-8B-Int4 or Mistral-7B-Int4) with `device="cpu"` (FR-002, FR-009)
- [X] T023 [US2] Implement inference loop in T022: Generate traces with `temperature=0.0`, enforce **Fixed 10-minute wall-clock timeout** per task (FR-012) using `signal.alarm`. **If timeout occurs, log error (ERR_TIMEOUT) and skip task; do NOT retry with extended time.**
- [X] T024 [US2] Implement error handling in T022: Log timeout/empty response errors (JSON structured logs, severity WARNING, codes ERR_TIMEOUT, ERR_EMPTY) and skip task without crashing (Edge Case).
- [X] T025 [US2] Implement Memory Guard in T022: If OOM, fallback to Mistral-7B-Int4 (4-bit) or reduce context window to 2048 tokens (Plan T010). **Fallback must be 4-bit quantized.**
- [X] T026 [US2] Write raw CoT traces to `data/traces/cot_traces.jsonl` immediately upon generation (Constitution Principle VI). **Path MUST be `data/traces/` not `data/processed/`.**
- [X] T027 [US2] Implement Stopping Rule Check in T022: If count of *successfully generated* traces < 40 (MVS), halt and report "Underpowered: Effective sample size < 40" (Plan T012).
- [X] T028 [US2] Implement `code/03_parse_and_classify.py`: Load traces and task records
- [X] T029 [US2] Implement exact string matching in T028: Find first/last character offset of constraint in the **first 256 tokens** and **last 256 tokens** of the trace (FR-003, Plan T014). **Use the same tokenizer as the LLM. The 256-token window is the definition of the 'step' for classification, not a search limit that ignores valid mentions outside the window.**
- [X] T030 [US2] Implement semantic matching in T028: Use `all-MiniLM-L6-v2` and tuned threshold from T019 to detect paraphrased constraints (FR-011)
- [X] T031 [US2] Handle edge cases in T028: Word-boundary matching to avoid false positives, null flags for missing constraints

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Classification and Statistical Analysis (Priority: P3)

**Goal**: Classify errors (Perceptual/Procedural/Correct) and perform statistical analysis.

**Independent Test**: Provide a hand-labeled sample to `code/03_parse_and_classify.py` and verify labels match; run `code/04_statistical_analysis.py` to verify p-value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for rule-based classifier logic in `tests/unit/test_classifier.py`
- [X] T033 [P] [US3] Unit test for Fisher's Exact vs. Chi-squared trigger logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T034 [US3] Implement classifier logic in `code/03_parse_and_classify.py`: Label traces as Perceptual, Procedural, or Correct based on first/last mention (FR-004). **Logic MUST be non-tautological: Predictor = Temporal Pattern, Outcome = Ground Truth (from dataset). Mapping: First Missing=Perceptual, First Present/Last Missing=Procedural, Both Present/Correct=Correct.**
- [X] T035 [US3] Implement `code/04_statistical_analysis.py`: Compute proportions of error types per category (FR-005)
- [X] T036 [US3] Implement Test Selection in T035: If expected cell counts < 5 (using `scipy.stats.chi2_contingency` expected counts), select Fisher's Exact; else Chi-squared (Plan T017).
- [X] T037 [US3] Implement Framing Injection in T035: Explicitly set `framing` field to "Associational" in output (FR-007). **Do NOT add negative constraints like "no causal".**
- [X] T038 [US3] Implement Multiple Comparison Correction in T035: Apply Bonferroni or Benjamini-Hochberg **if and only if >1 hypothesis test is performed** (FR-008, Plan T018). **Do NOT use arbitrary sample-size thresholds.**
- [X] T039 [US3] Compute p-value and statistic in T035.
- [X] T040 [US3] Generate `statistical_report.json` (SSoT) with all results.

**Manual Step: Human Expert Annotation**
> **Note**: The following is a manual step outside automated code execution.
> 1. Generate annotation request file using T041.
> 2. Human expert labels N=30 traces for "Task Outcome" (Correct/Incorrect) and "Constraint Mention" (Yes/No).
> 3. Save results to `data/validation/ground_truth_labels.jsonl`.

- [X] T041 [US3] Implement `code/generate_annotation_request.py`: Generate a request file for human experts to label a sample of traces (FR-010, SC-006). **Sample size MUST be read from `config.yaml` using key `validation.sample_size`.**
- [X] T042 [US3] Implement `code/ingest_human_labels.py`: Ingest labels from `data/validation/ground_truth_labels.jsonl` (FR-010).
- [X] T043 [US3] Implement `code/validate_classifier.py`: Compare automated labels (T034) against T042 labels to compute agreement rate (FR-010, SC-006). **MUST verify the rate is ≥ 85% and report the agreement rate and flag the limitation if the threshold is not met (Do NOT halt the pipeline).**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting (Polish)

**Purpose**: Final validation, artifact hashing, and documentation.

- [X] T044 [P] Implement `code/generate_paper_sections.py`: Generate final paper sections based on `statistical_report.json` (Plan T023).
- [X] T045 [P] Implement `code/update_state.py`: Hash `statistical_report.json` and `data/` artifacts, write to project state YAML (Plan T024).
- [X] T046 [P] Implement `code/06_consistency_check.py`: Re-run parser on **the same fixed sample** used in the original run, calculate agreement rate, and write `data/results/consistency_report.json` with the calculated agreement rate percentage (SC-005). **MUST verify the rate is ≥ 99% and halt the pipeline if the threshold is not met (as this indicates a bug).**
- [X] T047 [P] Generate content hashes for all `data/` and `code/` artifacts and record in `state/` (Constitution Principle V)
- [X] T048 [P] Update `quickstart.md` with reproduction steps and power analysis limitations
- [X] T049 [P] Run end-to-end integration test in `tests/integration/test_end_to_end.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T004 (Schemas) is NOT a blocker for T012 (Download). T012 depends only on T003 (Env). T004 runs in parallel.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T017 (Pilot Study).
 - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T028 (Load traces and task records).
 - **Strict Data Flow**: T014 (Halt if missing) MUST complete before T022 (Generation). If T014 halts, T022 never runs.
 - **Strict Data Flow**: T022-T026 (Generation) MUST complete before T028-T031 (Parsing)
 - **Strict Data Flow**: T028-T031 (Parsing) MUST complete before T034-T040 (Classification/Stats)
 - **Strict Data Flow**: T041 (Generate Request) -> T042 (Ingest Labels) -> T043 (Validate)
 - **Strict Data Flow**: T017 (Pilot) depends on T015 (Filtered Data).
 - **Strict Data Flow**: T022 depends on T019 (Tuned Threshold).
 - **Strict Data Flow**: T043 depends on T034 (Classifier logic).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data) and Pilot (T017-T019)
- **User Story 3 (P3)**: Depends on US2 completion (requires parsed traces) and T041 (Human Labels)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (T010/T011 before T012; T020/T021 before T022; T032/T033 before T034)
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
- **Critical Constraint**: Sample size for validation is read from `config.yaml` using key `validation.sample_size` to respect spec deferment (FR-010).
- **Critical Constraint**: Fixed 10-minute timeout per task; Global runtime limit set to a reasonable duration for the intended scope. (FR-012, FR-009)
- **Critical Constraint**: No synthetic data fallback; failed real fetch MUST raise (Data Hygiene)
- **TDD Rule**: Tests (T010, T011, etc.) MUST be listed before their corresponding implementation tasks in the same phase.
- **Deprecated**: T035 is deprecated and removed.
- **Phase 3.5**: Pilot study is a sub-phase of Phase 3, required before Phase 4 (Generation).
- **Strict Data Flow**: T015 MUST complete before T017. T019 output required by T022.