# Tasks: llmXive follow-up: extending "Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models"

**Input**: Design documents from `/specs/001-blind-spots-order-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes GPU fallback, streaming, and configuration.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (include `datasets`, `transformers`, `torch`, `sentence-transformers`, `scikit-learn`, `scipy`, `pandas`, `statsmodels`)
- [X] T003a [P] Create `config.yaml` with keys: `validation.sample_size`, `study.min_sample_size`, `inference.timeout_minutes`, `dataset.source_url`, `inference.model_name`, `inference.device`
- [X] T004 [P] Create specific YAML schema files: `dataset.schema.yaml`, `trace.schema.yaml`, `output.schema.yaml` in `specs/001-blind-spots-order-analysis/contracts/` (Matches Plan.md structure)
- [X] T005 [P] Implement `code/utils/hashing_utils.py` for artifact content hashing (Constitution Principle V)
- [X] T006 [P] Implement `code/utils/logging_config.py` for structured logging across pipeline stages
- [X] T007 [P] Implement `code/utils/dataset_integrity.py` for strict field validation (FR-006) using `dataset.schema.yaml`
- [X] T008 [P] Implement `code/utils/semantic_matcher.py` using `all-MiniLM-L6-v2` for paraphrase detection (FR-011)
- [X] T009 [P] Create `code/run_pipeline.sh` orchestrator script
- [X] T050 [US2] Implement streaming data loader in `code/01_download_and_filter.py`: Replace full dataset loading with `datasets.load_dataset(..., streaming=True)` to process tasks in chunks, ensuring RAM usage stays within acceptable limits for large subsets (Plan: Memory & Compute Strategy).
- [X] T051a [US2] Implement **OOM Detection Logic** in `code/02_generate_cot.py`: Add try/except block around model inference to catch `OutOfMemoryError`. Log error code `ERR_OOM` and trigger fallback sequence.
- [X] T051b [US2] Implement **Kaggle API Integration** in `code/02_generate_cot.py`: Create function to submit a job to Kaggle using the `kaggle` CLI/API with the same script and pinned seed. Ensure the job runs on a single GPU.
- [X] T051c [US2] Implement **Seed Pinning Logic** in `code/02_generate_cot.py`: Ensure `random`, `numpy`, `torch`, and `transformers` seeds are set to a fixed value (e.g., 42) before inference. Verify that the seed is passed to the Kaggle job environment variable.
- [X] T051d [US2] Implement **Fallback Orchestration** in `code/02_generate_cot.py**: If T051a catches OOM, invoke T051b to offload to Kaggle. Ensure the script waits for the Kaggle job to complete and retrieves the results. **Do NOT** implement silent CPU fallbacks or synthetic data. The same code path must execute on GPU with pinned seeds for reproducibility. (Plan: Memory & Compute Strategy).
- [X] T052 [US2] Add explicit sample-size logging in `code/02_generate_cot.py`: Log the exact number of tasks processed, skipped (timeout), and generated, including the streaming chunk size or random seed used if sampling is applied (Spec: Large real datasets).
- [X] T053 [US2] Implement strict "No Synthetic Fallback" guard in `code/01_download_and_filter.py`: Ensure `try/except` blocks for data fetching **raise** immediately on failure without generating `mock_*` or `synthetic_*` data (Spec: The loader must FAIL LOUDLY).
- [X] T055 [US1] **Verify and document the exact URL** for the Blind-Spots-Bench dataset. **Deliverable**: Write the verified URL to `config.yaml` under key `dataset.source_url`. **Verification**: Implement a script step to check URL reachability (HTTP 200) before any download logic runs. (FR-001, US-1).

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

- [X] T012 [US1] Implement `code/01_download_and_filter.py`: Download dataset from canonical arXiv source using `datasets` library (Streaming enabled per T050). **Internal check**: Verify the source URL matches `config.yaml` `dataset.source_url` before proceeding. **Depends on T050-T053**.
- [X] T013 [US1] Implement filtering logic in T012: Retain only "Abstract Reasoning" and "Object-Centric" categories. **Filter criteria**: `task_category in ['Abstract Reasoning', 'Object-Centric']`. **Output path**: `data/filtered/filtered_tasks.jsonl`.
- [X] T014a [US1] Implement integrity scan and error report generation in T012: Scan `data/filtered/filtered_tasks.jsonl` for missing `constraint` fields.
 - **If missing**: Generate `data/validation/integrity_error_report.json` with specific missing IDs, **raise `SystemExit(1)`** to halt execution immediately (FR-006).
- [X] T014b [US1] Implement integrity pass artifact generation in T012: **If clean**: Generate `data/validation/integrity_pass.json` with `status: 'PASS'` and proceed to T015. **Do NOT raise SystemExit on success.**
- [X] T015 [US1] Write filtered data to `data/filtered/filtered_tasks.jsonl` with checksum generation (Depends on T014b success artifact).
- [X] T016 [US1] Add CLI arguments for dataset path and output path in T012: `--input` (str, default=None), `--output` (str, default='data/filtered/filtered_tasks.jsonl').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Pilot Study & Threshold Validation (Sub-phase of Phase 3)

**Goal**: Validate semantic matching threshold on a small pilot set before full-scale generation.

- [X] T022a [US2] Implement `code/02_generate_cot.py` (Pilot Mode): Load 4-bit quantized model (Llama-3-8B-Int4 or Mistral-7B-Int4) with `device="cpu"` (FR-002, FR-009). **Must support `--pilot` flag.** **Uses T050, T051 logic**.
- [X] T017 [US2] Implement `code/pilot_study.py`: Generate CoT traces for a small pilot set (N=10) using the filtered dataset and T022a. **Save to `data/pilot/` (separate from production traces)**. **Uses T050, T051 logic**.
- [X] T018a [US2] Implement `code/generate_pilot_annotation_request.py`: Generate a request file for human experts to label the N=10 pilot traces for "Constraint Mention" (Yes/No) and "Task Outcome" (Correct/Incorrect).
- [X] T018b [US2] **Manual Gate**: Human expert labels N=10 pilot traces. **Deliverable**: Save results to `data/pilot/pilot_ground_truth_labels.jsonl`. **Schema**: `[{"task_id": "...", "constraint_mention": "yes|no", "task_outcome": "correct|incorrect"}]`. **This is a completed gate definition; the task waits for the file to exist.**
- [X] T018c [US2] Implement `code/ingest_pilot_labels.py`: Ingest labels from `data/pilot/pilot_ground_truth_labels.jsonl`. **Must verify file presence and schema before proceeding.** **Blocks T019 until file exists.**
- [X] T019 [US2] Implement `code/tune_threshold.py`: Iterate cosine similarity threshold (range from the minimum to the maximum, step 0.05) to maximize agreement rate between automated semantic match and human labels. **Algorithm**: Load `all-MiniLM-L6-v2`, compute embeddings for constraint and trace segments, calculate cosine similarity, compare against threshold, count agreements. **Deliverable**: Save optimal threshold to `data/pilot/tuned_threshold.json`. **Blocked until T018c confirms file existence.**

**Checkpoint**: Threshold validated - ready for full-scale generation

---

## Phase 4: User Story 2 - CoT Trace Generation and Parsing (Priority: P2)

**Goal**: Generate deterministic CoT traces using a 4-bit quantized LLM and parse them for constraint mentions.

**Independent Test**: Run `code/02_generate_cot.py` on a sample of 2 tasks and verify `code/03_parse_and_classify.py` correctly identifies first/last constraint offsets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for constraint string matching (word boundary check) in `tests/unit/test_parser.py`
- [X] T021 [P] [US2] Unit test for semantic equivalence threshold in `tests/unit/test_semantic_matcher.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/02_generate_cot.py` (Full Mode): Load 4-bit quantized model (Llama-3-8B-Int4 or Mistral-7B-Int4) with `device="cpu"` (FR-002, FR-009). **Must read tuned threshold from `data/pilot/tuned_threshold.json`**. **If `tuned_threshold.json` is missing, raise FileNotFoundError with a clear message indicating T019 must be run first.** **Depends on T050-T053**.
- [X] T023 [US2] Implement inference loop in T022: Generate traces with `temperature=0.0`, enforce **Fixed 10-minute wall-clock timeout per task** (FR-012) using `signal.alarm`, **SUBJECT TO the global runtime limit enforced by T023a**. **If timeout occurs, log error (ERR_TIMEOUT) and skip task; do NOT retry with extended time.** **Do not start a new task if the remaining time (6h - elapsed) is less than the per-task timeout.**
- [X] T023a [US2] Implement **Global Runtime Monitor** in T022: Track cumulative runtime. **Before starting each new task**, check if `elapsed_time + per_task_timeout > 6 hours`. If true, **halt immediately** with `ERR_TIMEOUT_GLOBAL` and generate `data/results/runtime_limit_reached.json`. **This enforces the global 6-hour limit (FR-009) and prevents the per-task timeout from violating the global constraint.** (FR-009).
- [X] T024 [US2] Implement error handling in T022: Log timeout/empty response errors (JSON structured logs, severity WARNING, codes ERR_TIMEOUT, ERR_EMPTY) and skip task without crashing (Edge Case).
- [X] T025 [US2] Implement Memory Guard in T022: If OOM, fallback to Mistral-7B-Int4 (4-bit) or reduce context window to a constrained length (Plan T010). **Fallback must be 4-bit quantized.** **Uses T051a-T051d logic**.
- [X] T026 [US2] Write raw CoT traces to `data/traces/cot_traces.jsonl` immediately upon generation (Constitution Principle VI). **Path MUST be `data/traces/` not `data/processed/`**.
- [X] T027 [US2] Implement Stopping Rule Check and Underpowered Report: If count of *successfully generated* traces < `config.yaml` key `study.min_sample_size`, **halt execution** and generate `data/results/underpowered_report.json` with fields: `effective_sample_size`, `threshold`, `reason`, `timestamp`. **Raise `SystemExit(1)` after generating report.** (Merges T027 and T056 logic). **Schema**: `{ "effective_sample_size": int, "threshold": int, "reason": str, "timestamp": str }`.
- [X] T028 [US2] Implement `code/03_parse_and_classify.py`: Load traces and task records
- [X] T029 [US2] Implement exact string matching in T028: Find first/last character offset of constraint in the **first segment** and **last segment** of the trace (FR-003, Plan T014). **Use the same tokenizer as the LLM. The fixed-token window is the definition of the 'step' for classification, not a search limit that ignores valid mentions outside the window. Apply word-boundary matching ONLY within the defined token windows to avoid false positives.**
- [X] T030 [US2] Implement semantic matching in T028: Use `all-MiniLM-L6-v2` and tuned threshold from `data/pilot/tuned_threshold.json` (T019) to detect paraphrased constraints (FR-011). **Algorithm**: Load model, encode constraint and trace segments, compute cosine similarity, return True if similarity >= threshold.
- [X] T031 [US2] Handle edge cases in T028: **Specifically handle**: Word-boundary matching (already defined in T029), null flags for missing constraints, and cases where the constraint appears as a substring within a different word (false positive check).

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
- [X] T040 [US3] Generate `statistical_report.json` (SSoT) with all results. **Must include `limitations` field**: `{ "sample_size_limitation": "Power analysis deferred; sample size limited by runtime constraints.", "observational_design": true }` (Merges T040 and T057 logic).
- [X] T041 [US3] Implement `code/generate_annotation_request.py`: Generate a request file for human experts to label a sample of traces (FR-010, SC-006). **Sample size MUST be read from `config.yaml` using key `validation.sample_size`.**
- [X] T042 [US3] Implement `code/ingest_human_labels.py`: Ingest labels from `data/validation/ground_truth_labels.jsonl` (FR-010).
- [X] T043 [US3] Implement `code/validate_classifier.py`: Compare automated labels (T034) against T042 labels to compute agreement rate (FR-010, SC-006). **MUST verify the rate is ≥ 85% to validate the methodology as required by SC-006. If < 85%, raise `SystemExit(1)` with error message "Classifier validation failed: agreement rate < 85%". HALT PIPELINE immediately to prevent generation of invalid results.** (Merges T043 and SC-006).

**Manual Step: Human Expert Annotation**
> **Note**: The following is a manual step outside automated code execution.
> 1. Generate annotation request file using T041.
> 2. Human expert labels N=30 traces for "Task Outcome" (Correct/Incorrect) and "Constraint Mention" (Yes/No).
> 3. Save results to `data/validation/ground_truth_labels.jsonl`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting (Polish)

**Purpose**: Final validation, artifact hashing, and documentation.

- [X] T044 [P] Implement `code/generate_paper_sections.py`: Generate final paper sections based on `statistical_report.json` (Plan T023).
- [X] T045 [P] Implement `code/update_state.py`: Hash `statistical_report.json` and `data/` artifacts, write to project state YAML (Plan T024).
- [X] T046 [P] Implement `code/06_consistency_check.py`: Re-run parser on **the same fixed sample** used in the original run, calculate agreement rate, and write `data/results/consistency_report.json` with the calculated agreement rate percentage (SC-005). **MUST verify the rate is ≥ 99% and halt the pipeline if the threshold is not met (as this indicates a bug).**
- [X] T047 [P] Generate content hashes for all `data/` and `code/` artifacts and record in `state/` (Constitution Principle V)
- [X] T048 [P] Update `quickstart.md` with reproduction steps and document the **deferral** of power analysis (Spec: Assumptions). **Include the verified dataset source URL here.**
- [X] T049 [P] Run end-to-end integration test in `tests/integration/test_end_to_end.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T004 (Schemas) is NOT a blocker for T012 (Download). T012 depends only on T003 (Env). T004 runs in parallel.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Strict Data Flow**: T014b (Halt if missing) MUST complete before T015. **T014b must generate a 'PASS' artifact on success to allow T015 to proceed.**
 - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T017 (Pilot Study).
 - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T028 (Load traces and task records).
 - **Strict Data Flow**: T018b (Manual) -> T018c (Ingest) -> T019 (Tune). **T019 cannot start until T018c confirms the presence of the label file.**
 - **Strict Data Flow**: T019 (Tuned Threshold) MUST complete before T022 (Generation). **T022 will fail if T019 artifact is missing.**
 - **Strict Data Flow**: T022-T026 (Generation) MUST complete before T028-T031 (Parsing)
 - **Strict Data Flow**: T028-T031 (Parsing) MUST complete before T034-T040 (Classification/Stats)
 - **Strict Data Flow**: T041 (Generate Request) -> T042 (Ingest Labels) -> T043 (Validate)
 - **Strict Data Flow**: T050-T051d (GPU/Streaming) are prerequisites for T012 and T022.
 - **Strict Data Flow**: T027 (Underpowered Check & Report) MUST complete before T022 and T028 to enforce the sample size halt.
 - **Strict Data Flow**: T055 (Verify URL) MUST complete before T012.
 - **Strict Data Flow**: T023a (Global Runtime) runs concurrently with T022-T026.

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
- **Revision Note**: T050-T053 have been moved to Phase 2 to ensure they are implemented before execution. T056 merged into T027. T057 merged into T040.
- **New Task T055**: Verifies real URL for dataset download and writes to config.
- **Revision Note**: T051 updated to implement GPU Escape Hatch (split into T051a-T051d). T057 removed as redundant. T014 clarified for explicit halt/pass artifacts.
- **Revision Note**: T018b reclassified as Manual Gate. T043 updated to enforce [deferred] agreement as hard gate. T023a added for global runtime enforcement.
- **Revision Note**: T023 updated to explicitly qualify the 10-minute timeout as subject to the global limit enforced by T023a. T043 updated to explicitly state the halt is required to validate the methodology per SC-006.