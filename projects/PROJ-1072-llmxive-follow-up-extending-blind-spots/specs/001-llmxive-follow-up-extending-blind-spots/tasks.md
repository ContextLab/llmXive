# Tasks: llmXive follow-up: extending "Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models"

**Input**: Design documents from `/specs/001-blind-spots-order-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
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

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes CPU fallback, streaming, and configuration.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Initialize Python 3.11 project with `requirements.txt` (include `datasets`, `transformers`, `torch`, `sentence-transformers`, `scikit-learn`, `scipy`, `pandas`, `statsmodels`)
- [X] T003a Create `config.yaml` with keys: `validation.sample_size` (default: 30), `study.min_sample_size` (default: 40), `inference.timeout_minutes` (default: 10), `dataset.source_url` (placeholder), `inference.model_name` (default: "meta-llama/Llama-3-8B-Instruct-4bit"), `inference.device` (default: "cpu"), `study.max_runtime_hours` (default: 6)
- [X] T004 [P] Create specific YAML schema files: `dataset.schema.yaml`, `trace.schema.yaml`, `output.schema.yaml` in `specs/001-blind-spots-order-analysis/contracts/` (Matches Plan.md structure)
- [X] T005 [P] Implement `code/utils/hashing_utils.py` for artifact content hashing (Constitution Principle V)
- [X] T006 [P] Implement `code/utils/logging_config.py` for structured logging across pipeline stages
- [X] T007 [P] Implement `code/utils/dataset_integrity.py` for strict field validation (FR-006) using `dataset.schema.yaml`
- [X] T008 [P] Implement `code/utils/semantic_matcher.py` using `all-MiniLM-L6-v2` for paraphrase detection (FR-011)
- [X] T009 [P] Create `code/run_pipeline.sh` orchestrator script
- [X] T050 [US2] Implement streaming data loader in `code/01_download_and_filter.py`: Replace full dataset loading with `datasets.load_dataset(..., streaming=True)` to process tasks in chunks, ensuring RAM usage stays within acceptable limits for large subsets (Plan: Memory & Compute Strategy).
- [X] T051a [US2] Implement **OOM Detection Logic** in `code/02_generate_cot.py`: Add try/except block around model inference to catch `OutOfMemoryError`. Log error code `ERR_OOM` and trigger fallback sequence.
- [X] T051c [US2] Implement **Seed Pinning Logic** in `code/02_generate_cot.py`: Ensure `random`, `numpy`, `torch`, and `transformers` seeds are set to a fixed value (e.g., 42) before inference. Verify that the seed is consistent across CPU and fallback runs.
- [X] T051d [US2] Implement **Fallback Orchestration** in `code/02_generate_cot.py`: If T051a catches OOM, invoke T051b. Ensure the script logs the fallback action and continues with the GPU runner. **Do NOT** implement silent CPU fallbacks or synthetic data. The same code path must execute with the fallback model for reproducibility. (Plan: Memory & Compute Strategy).
- [X] T052 [US2] Add explicit sample-size logging in `code/02_generate_cot.py`: Log the exact number of tasks processed, skipped (timeout), and generated, including the streaming chunk size or random seed used if sampling is applied (Spec: Large real datasets).
- [X] T053 [US2] Implement strict "No Synthetic Fallback" guard in `code/01_download_and_filter.py`: Ensure `try/except` blocks for data fetching **raise** immediately on failure without generating `mock_*` or `synthetic_*` data (Spec: The loader must FAIL LOUDLY).
- [X] T055 [US1] **Verify and document the exact URL** for the Blind-Spots-Bench dataset. **Deliverable**: Write the verified URL to `config.yaml` under key `dataset.source_url`. **Verification**: Implement a script step to check URL reachability (HTTP 200) before any download logic runs. (FR-001, US-1). **Depends on T003a**.

---

## Phase 2.5: GPU Escape Hatch Infrastructure (Blocking Prerequisites for Fallback)

**Purpose**: Implement the infrastructure required for the Kaggle GPU fallback mechanism mandated by the Plan.

- [X] T051e [US2] Implement **Kaggle Runner Configuration** in `code/utils/kaggle_runner.py`: Create a CLI wrapper to authenticate (via `KAGGLE_KEY` env var) and submit a job to a pre-configured Kaggle GPU kernel. The script must accept a `state_file` argument, upload it, trigger the job, and poll for completion. This provides the infrastructure for T051b.
- [X] T051f [US2] Implement **Remote State Restoration** in `code/utils/kaggle_runner.py`: Add logic to the remote execution entry point (triggered by T051e) to download `state_file`, deserialize the queue, and resume the inference loop.
- [X] T051g [US2] Implement **Kaggle Environment Setup** in `code/utils/kaggle_runner.py`: Create the remote kernel script template that includes all necessary imports, environment setup, and the entry point for restoring state and resuming inference. **This task ensures the remote environment is pre-configured.**
- [X] T051h [US2] Implement **Kaggle Job Orchestration** in `code/utils/kaggle_runner.py`: Create the logic to monitor the remote job status, handle retries, and collect logs. **This task ensures the orchestration of the remote execution.**
- [X] T051b [US2] Implement **GPU Escape Hatch Orchestration** in `code/02_generate_cot.py`: If OOM occurs on CPU (T051a), serialize the current execution state (task queue, partial results, config) to `data/checkpoint/state.json`. Then, invoke the remote runner wrapper (T051e) to trigger a Kaggle job. The remote job must restore state from `state.json`, load the model on GPU, and resume inference from the last completed task. **Do NOT** restrict to CPU-only models; the plan explicitly authorizes this recovery path. **Uses T051e, T051f, T051g, T051h logic**. **Depends on T051e, T051f, T051g, T051h**.

**Checkpoint**: GPU Escape Hatch infrastructure ready - fallback is now implementable.

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

- [X] T012 [US1] Implement `code/01_download_and_filter.py`: Download dataset from canonical arXiv source using `datasets` library (Streaming enabled per T050). **Internal check**: Verify the source URL matches `config.yaml` `dataset.source_url` before proceeding. **Output**: `data/filtered/filtered_tasks.jsonl`. **Depends on T050, T053, T055**.
- [X] T013 [US1] Implement filtering logic in T012: Retain only "Abstract Reasoning" and "Object-Centric" categories. **Filter criteria**: `task_category in ['Abstract Reasoning', 'Object-Centric']`. **Output path**: `data/filtered/filtered_tasks.jsonl`.
- [X] T014a [US1] Implement integrity scan and error report generation in T012: Scan `data/filtered/filtered_tasks.jsonl` for missing `constraint` fields.
 - **If missing**: Generate `data/validation/integrity_error_report.json` with specific missing IDs, **raise `SystemExit(1)` to halt execution immediately (FR-006).
- [X] T014b [US1] Implement integrity pass artifact generation in T012: **If clean**: Generate `data/validation/integrity_pass.json` with `status: 'PASS'` and proceed to T015. **Do NOT raise SystemExit on success.**
- [X] T015 [US1] Write filtered data to `data/filtered/filtered_tasks.jsonl` with checksum generation (Depends on T014b success artifact).
- [X] T016 [US1] Add CLI arguments for dataset path and output path in T012: `--input` (str, default=None), `--output` (str, default='data/filtered/filtered_tasks.jsonl').

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.5: Pilot Study & Threshold Validation (Sub-phase of Phase 3)

**Goal**: Validate semantic matching threshold on a small pilot set before full-scale generation.

- [X] T022a [US2] Implement `code/02_generate_cot.py` (Pilot Mode): Load 4-bit quantized model (Llama-3-8B-Int4 or Mistral-7B-Int4) with `device="cpu"` (FR-002, FR-009). **Must support `--pilot` flag.** **Uses T050, T051 logic**.
- [X] T017 [US2] Implement `code/pilot_study.py`: Generate CoT traces for a small pilot set (N=10) using the filtered dataset and T022a. **Save to `data/pilot/pilot_traces.jsonl`**. **Uses T050, T051 logic**. **Note**: Uses a default threshold for initial generation.
- [X] T018a [US2] Implement `code/generate_pilot_annotation_request.py`: Generate a request file for human experts to label the N=10 pilot traces for "Constraint Mention" (Yes/No) and "Task Outcome" (Correct/Incorrect).
- [X] T018b [US2] Implement **Automated Threshold Fallback** in `code/tune_threshold.py`: Check for presence of `data/pilot/pilot_ground_truth_labels.jsonl`. **If present**: Proceed with human-labeled tuning. **If missing**: Generate `data/pilot/tuned_threshold.json` with `threshold: 0.75` and `source: "default"`, log a WARNING, and exit successfully. **This task ensures the pipeline never blocks on human input.** **Depends on T017**.
- [X] T018c [US2] Implement `code/ingest_pilot_labels.py`: Ingest labels from `data/pilot/pilot_ground_truth_labels.jsonl`. **Must verify file presence and schema before proceeding.** **Blocks T019 only if file is missing AND T018b has not been run.** **T018b ensures this file is never strictly required for execution.**
- [X] T019 [US2] Implement `code/tune_threshold.py`: Iterate cosine similarity threshold across the full range with a fine-grained step size to maximize agreement rate between automated semantic match and human labels. **Input**: `data/pilot/pilot_traces.jsonl` (generated by T017) AND `data/pilot/pilot_ground_truth_labels.jsonl` (Optional). **Algorithm**: Load `all-MiniLM-L6-v2`, encode constraint and trace segments from `pilot_traces.jsonl`, compute cosine similarity, compare against threshold, count agreements against labels in `pilot_ground_truth_labels.jsonl` (if present). **If labels missing**: Use a default threshold from T018b output. **Deliverable**: Save optimal threshold (or default) to `data/pilot/tuned_threshold.json`. **Depends on T017 (Traces) and T018b (Threshold Fallback).** **Do NOT block execution if labels are missing.**

**Checkpoint**: Threshold validated (or defaulted) - ready for full-scale generation

---

## Phase 4: User Story 2 - CoT Trace Generation and Parsing (Priority: P2)

**Goal**: Generate deterministic CoT traces using a 4-bit quantized LLM and parse them for constraint mentions.

**Independent Test**: Run `code/02_generate_cot.py` on a sample of 2 tasks and verify `code/03_parse_and_classify.py` correctly identifies first/last constraint offsets.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for constraint string matching (word boundary check) in `tests/unit/test_parser.py`
- [X] T021 [P] [US2] Unit test for semantic equivalence threshold in `tests/unit/test_semantic_matcher.py`

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/02_generate_cot.py` (Full Mode): Load 4-bit quantized model (Llama-3-8B-Int4 or Mistral-7B-Int4) with `device="cpu"` (FR-002, FR-009). **Must read tuned threshold from `data/pilot/tuned_threshold.json`.** **If `tuned_threshold.json` is missing, raise FileNotFoundError with a clear message indicating T019 must be run first.** **Depends on T050-T053, T051a-T051d, T019**.
- [ ] T023 [US2] Implement inference loop in T022: Generate traces with `temperature=0.0`, enforce **Fixed wall-clock timeout per task (configurable duration)**. **If timeout occurs, log error (ERR_TIMEOUT) and skip task; do NOT retry with extended time.** **Do not start a new task if the remaining time (6h - elapsed) is less than the per-task timeout.** **Dynamic Budget**: Calculate per-task budget based on remaining time and expected sample size to prevent premature abortion.
- [ ] T023a [US2] Implement **Global Runtime Monitor Wrapper** in T022: Wrap the entire inference loop (T023) in a time-bounded context manager. **Logic**: Before starting the loop, record start time. Before starting *each* task, check if `elapsed_time + 600 > 21600` (6 hours). If true, **halt immediately** with `ERR_TIMEOUT_GLOBAL`, generate `data/results/runtime_status.json` with schema: `{ "elapsed_time": float, "reason": "Runtime limit exceeded", "timestamp": str, "effective_sample_size": int }`, and exit. **After each task**, update `elapsed_time` and log progress. **This task is the orchestrator for T023 and T027.** (Enforces FR-009). **Output**: `data/results/runtime_status.json`.
- [ ] T024 [US2] Implement error handling in T022: Log timeout/empty response errors (JSON structured logs, severity WARNING, codes ERR_TIMEOUT, ERR_EMPTY) and skip task without crashing (Edge Case).
- [ ] T025 [US2] Implement Memory Guard in T022: If OOM, fallback to a smaller quantized model variant (Mistral-Int4 or TinyLlama-Int4) or reduce context window to a constrained length (Plan T010). **Fallback must be 4-bit quantized.** **Uses T051a-T051d logic**. **Note**: If CPU fails, trigger GPU Escape Hatch (T051b).
- [ ] T026 [US2] Write raw CoT traces to `data/traces/cot_traces.jsonl` immediately upon generation (Constitution Principle VI). **Path MUST be `data/traces/` not `data/processed/`**.
- [ ] T027 [US2] Implement Stopping Rule Check: After T023a completes (or halts), **read `effective_sample_size` from `data/results/runtime_status.json`** generated by T023a. Check if `effective_sample_size` < `config.yaml` key `study.min_sample_size`. **If true, halt execution** and generate `data/results/underpowered_report.json` with fields: `effective_sample_size`, `threshold`, `reason`, `timestamp`. **Raise `SystemExit(1)` after generating report.** (Merges T027 and T056 logic). **Schema**: `{ "effective_sample_size": int, "threshold": int, "reason": str, "timestamp": str }`. **Depends on T023a**.
- [ ] T027a [US2] Implement **Underpowered Report Generation**: Generate `data/results/underpowered_report.json` if T027 condition is met. **Schema**: `{ "effective_sample_size": int, "threshold": int, "reason": str, "timestamp": str }`.
- [X] T028 [US2] Implement `code/03_parse_and_classify.py`: Load traces and task records
- [ ] T029 [US2] Implement exact string matching in T028: Find first/last character offset of constraint in the **ENTIRE trace** (FR-003). **Use the same tokenizer as the LLM. Apply word-boundary matching ONLY within the defined token windows to avoid false positives.** **Note**: Search entire trace, not just first/last segments. <!-- ATOMIZE: requested -->
- [ ] T030 [US2] Implement semantic matching in T028: Use `all-MiniLM-L6-v2` and tuned threshold from `data/pilot/tuned_threshold.json` (T019) to detect paraphrased constraints (FR-011). **Algorithm**: Load model, encode constraint and trace segments, compute cosine similarity, return True if similarity >= threshold. **Depends on T019. Block execution if `data/pilot/tuned_threshold.json` is missing.** <!-- FAILED: unspecified -->
- [ ] T031 [US2] Handle edge cases in T028: **Specifically handle**: Word-boundary matching (already defined in T029), null flags for missing constraints, and cases where the constraint appears as a substring within a different word (false positive check).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Classification and Statistical Analysis (Priority: P3)

**Goal**: Classify errors (Perceptual/Procedural/Correct) and perform statistical analysis.

**Independent Test**: Provide a hand-labeled sample to `code/03_parse_and_classify.py` and verify labels match; run `code/04_statistical_analysis.py` to verify p-value output.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for rule-based classifier logic in `tests/unit/test_classifier.py`
- [X] T033 [P] [US3] Unit test for Fisher's Exact vs. Chi-squared trigger logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement classifier logic in `code/03_parse_and_classify.py`: Label traces as Perceptual, Procedural, or Correct based on first/last mention (FR-004). **Logic MUST be non-tautological: Predictor = Temporal Pattern, Outcome = Ground Truth (from dataset `ground_truth` field). Mapping: First Missing=Perceptual, First Present/Last Missing=Procedural, Both Present/Correct=Correct.** **Output**: `data/parsed/classified_traces.jsonl` (Schema: `task_id`, `error_label`, `temporal_pattern`).
- [X] T035 [US3] Implement `code/04_statistical_analysis.py`: Compute proportions of error types per category (FR-005) <!-- ATOMIZE: requested -->
- [ ] T036 [US3] Implement Test Selection in T035: If expected cell counts < 5 (Wikipedia: Fisher's exact test, https://en.wikipedia.org/wiki/Fisher's_exact_test) (using `scipy.stats.chi2_contingency` expected counts), select Fisher's Exact; else Chi-squared (Plan T017).
- [ ] T037 [US3] Implement Framing Injection in T035: Explicitly set `framing` field to "Associational" in output (FR-007). **Do NOT add negative constraints like "no causal".**
- [ ] T038 [US3] Implement Multiple Comparison Correction in T035: Apply Bonferroni or Benjamini-Hochberg **if and only if >1 hypothesis test is performed** (FR-008, Plan T018). **Do NOT use arbitrary sample-size thresholds.**
- [ ] T039 [US3] Compute p-value and statistic in T035.
- [ ] T040 [US3] Generate `statistical_report_base.json` (SSoT base) with all results **EXCLUDING** the `limitations` field. **Includes documentation of the deferred power analysis per Spec Assumptions.** **Schema**: `{...results..., "limitations": null }`. **Depends on T034-T039**.
- [ ] T041 [US3] Implement `code/generate_annotation_request.py`: Generate a request file for human experts to label a sample of traces (FR-010, SC-006). **Sample size MUST be read from `config.yaml` using key `validation.sample_size`. If key is missing, default to 30.** **Output**: `data/validation/annotation_request.json` (Schema: `task_ids`, `labeling_instructions`).
- [ ] T042 [US3] Implement `code/ingest_human_labels.py`: Ingest labels from `data/validation/ground_truth_labels.jsonl`. **Must verify file presence and schema before proceeding. Block execution if file is missing.**
- [ ] T043 [US3] Implement `code/validate_classifier.py`: Compare automated labels (T034) against T042 labels to compute agreement rate (FR-010, SC-006). **MUST verify the rate is ≥ 85% to validate the methodology as required by SC-006. If < 85%, report the rate and HALT execution with error code ERR_VALIDATION_FAILED.** (Merges T043 and SC-006). **Depends on T042. Block execution if `data/validation/ground_truth_labels.jsonl` is missing. Check for file existence; if missing, halt with error code ERR_MANUAL_LABELS_MISSING.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting (Polish)

**Purpose**: Final validation, artifact hashing, and documentation.

- [ ] T060 [P] [US3] Implement `code/document_limitations.py`: Post-process `statistical_report_base.json` (generated by T040). **Logic**: Read the base report, inject the `limitations` field with text: "Power analysis was deferred by design to acknowledge sample size constraints; the study's findings are associational and limited by the effective sample size." **Deliverable**: Write `statistical_report.json` (final SSoT). **Depends on T040**. **Must complete before T044**.
- [ ] T061 [P] [US3] Update `quickstart.md` and `research.md` to explicitly state that the power analysis is **deferred** per the Spec's Assumptions (e., "With N=40, the study had [deferred] power to detect a medium effect size"). **Rationale**: Ensures transparency regarding the observational design and sample size constraints as required by the spec's assumptions. **Depends on T060**.
- [ ] T062 [P] [US3] Add a "Limitations" section to the generated paper sections (`code/generate_paper_sections.py`) that explicitly discusses the observational nature of the study and the limited statistical power, citing the results from T060. **Rationale**: Ensures the final output correctly frames the findings as associational and acknowledges the power limitations without overstating causality. **Depends on T060**.
- [ ] T044 [P] Implement `code/generate_paper_sections.py`: Generate final paper sections based on `statistical_report.json` (Plan T023). **Depends on T060**.
- [ ] T045 [P] Implement `code/update_state.py`: Hash `statistical_report.json` and `data/` artifacts, write to project state YAML (Plan T024).
- [ ] T046 [P] Implement `code/06_consistency_check.py`: Re-run parser on **the same fixed sample** used in the original run, calculate agreement rate, and write `data/results/consistency_report.json` with the calculated agreement rate percentage (SC-005). **MUST verify the rate is ≥ 99% and halt the pipeline if the threshold is not met (as this indicates a bug).** **Depends on T034-T040. Must complete BEFORE T044**.
- [ ] T047 [P] Generate content hashes for all `data/` and `code/` artifacts and record in `state/` (Constitution Principle V)
- [ ] T048 [P] Update `quickstart.md` with reproduction steps and document the **deferral** of power analysis (Spec: Assumptions). **Include the verified dataset source URL here.**
- [ ] T049 [P] Run end-to-end integration test in `tests/integration/test_end_to_end.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Note**: T004 (Schemas) is NOT a blocker for T012 (Download). T012 depends only on T003 (Env). T004 runs in parallel.
- **GPU Infrastructure (Phase 2.5)**: Depends on Foundational (Phase 2) - BLOCKS T051b
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Strict Data Flow**: T014b (Halt if missing) MUST complete before T015. **T014b must generate a 'PASS' artifact on success to allow T015 to proceed.**
 - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T017 (Pilot Study).
 - **Strict Data Flow**: T015 (Write filtered data) MUST complete before T028 (Load traces and task records).
 - **Strict Data Flow**: T018c (Ingest) -> T019 (Tune). **T019 cannot start until T018c confirms the presence of the label file OR T018b has generated the default.** (T018b is automated fallback).
 - **Strict Data Flow**: T017 (Pilot Generation) MUST complete before T019 (Tune) to provide traces.
 - **Strict Data Flow**: T019 (Tuned Threshold) MUST complete before T022 (Generation). **T022 will fail if T019 artifact is missing.**
 - **Strict Data Flow**: T022-T026 (Generation) MUST complete before T028-T031 (Parsing)
 - **Strict Data Flow**: T028-T031 (Parsing) MUST complete before T034-T040 (Classification/Stats)
 - **Strict Data Flow**: T041 (Generate Request) -> T042 (Ingest Labels) -> T043 (Validate)
 - **Strict Data Flow**: T050-T051d (GPU/Streaming) are prerequisites for T012 and T022.
 - **Strict Data Flow**: T022 (Generation) MUST complete before T027 (Underpowered Check & Report) to enforce the sample size halt.
 - **Strict Data Flow**: T055 (Verify URL) MUST complete before T012. **T012 depends on T055.**
 - **Strict Data Flow**: T023a (Global Runtime) runs as a wrapper around T022-T026.
 - **Strict Data Flow**: T060 (Document Limitations) MUST complete before T044 (Paper Generation) to ensure the report includes power metrics. **T060 depends on T040**.
 - **Strict Data Flow**: T003a (Config) MUST complete before T055. **T055 depends on T003a.**
 - **Strict Data Flow**: T046 (Consistency Check) MUST complete before T044 (Paper Generation) to validate results before reporting.
 - **Strict Data Flow**: T051e, T051g, T051h (Kaggle Infra) MUST complete before T051b (GPU Escape Hatch).
 - **Strict Data Flow**: T023a (Global Runtime) MUST complete before T027 (Stopping Rule). **T027 reads effective_sample_size from T023a artifact**.

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
- Documentation updates (T060-T062) can run in parallel once statistical results are available.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2.5: GPU Infrastructure (CRITICAL - enables fallback)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test data acquisition and filtering independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational + GPU Infra → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add Pilot Study (Phase 3.5) → Validate threshold (or default)
4. Add User Story 2 → Test independently → Deploy/Demo (Requires GPU/CPU scaling strategy)
5. Add User Story 3 → Test independently → Deploy/Demo
6. Add Documentation (Phase 6) → Quantify limitations
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational + GPU Infra together
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
- **Critical Constraint**: Sample size for validation is read from `config.yaml` using key `validation.sample_size` (default: 30 if missing) to respect spec deferment (FR-010).
- **Critical Constraint**: Fixed timeout per task

The research question, method, and references remain unchanged as no specific values were asserted for those elements in the original passage.; Global runtime limit set to 6 hours. (FR-012, FR-009)
- **Critical Constraint**: No synthetic data fallback; failed real fetch MUST raise (Data Hygiene)
- **TDD Rule**: Tests (T010, T011, etc.) MUST be listed before their corresponding implementation tasks in the same phase.
- **Deprecated**: T035 is deprecated and removed.
- **Phase 2.5**: Added for GPU Escape Hatch infrastructure. T051b now depends on T051e-T051h.
- **Phase 3.5**: Pilot study is a sub-phase of Phase 3, required before Phase 4 (Generation).
- **Strict Data Flow**: T015 MUST complete before T017. T019 output required by T022.
- **Revision Note**: T050-T053 have been moved to Phase 2 to ensure they are implemented before execution. T056 merged into T027. T057 merged into T040.
- **New Task T055**: Verifies real URL for dataset download and writes to config.
- **Revision Note**: T051 updated to implement GPU Escape Hatch (T051b). T057 removed as redundant. T014 clarified for explicit halt/pass artifacts.
- **Revision Note**: T018b reclassified as automated fallback task. T043 updated to enforce [deferred] agreement as hard gate. T023a added for global runtime enforcement.
- **Revision Note**: T023 updated to explicitly qualify the 10-minute timeout as subject to the global limit enforced by T023a. T043 updated to explicitly state the halt is required to validate the methodology per SC-006.
- **New Phase 6**: Added T060-T062 to document the deferred power analysis assumption and ensure transparent reporting of statistical limitations. Moved from Phase 7 to Phase 6 to ensure they complete before T044.
- **Revision Note**: T027 and T027a split for clarity. T029 updated to search entire trace. T041 and T043 updated to remove hardcoded sample size and hard halt.
- **Revision Note**: T022 atomized into T022, T023, T024. T027 split into T027 and T027a.
- **Revision Note**: T023a removed [P] tag and clarified as concurrent monitor.
- **Revision Note**: T019 input schema explicitly defined.
- **Revision Note**: T022 model details explicitly defined.
- **Revision Note**: T029 token window explicitly defined.
- **Revision Note**: T034 output schema explicitly defined.
- **Revision Note**: T041 output schema explicitly defined.
- **Revision Note**: T043 input file path explicitly defined.
- **Revision Note**: T061 updated to reflect deferred power analysis.
- **Revision Note**: T051e and T051f added for Kaggle infrastructure. T051b clarified for orchestration logic. T019 clarified to require traces. T043 clarified to enforce hard halt. T023a clarified as wrapper.
- **Revision Note**: T051g and T051h added for Kaggle environment setup and job orchestration. T051b now explicitly depends on T051e, T051g, T051h.
- **Revision Note**: T040 output renamed to `statistical_report_base.json`. T060 updated to read base and write final.
- **Revision Note**: T018b updated to generate default threshold if human labels are missing, removing the blocking manual step.
- **Revision Note**: T019 updated to proceed with default threshold if labels are missing, removing the blocking condition.
- **Revision Note**: T023a updated to explicitly output `data/results/runtime_status.json`.
- **Revision Note**: T041 updated to default sample size to 30 if config key is missing.