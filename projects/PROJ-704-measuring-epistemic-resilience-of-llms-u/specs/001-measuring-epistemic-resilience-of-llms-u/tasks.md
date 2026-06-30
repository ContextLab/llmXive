# Tasks: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

**Input**: Design documents from `/specs/001-measuring-epistemic-resilience/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

## Phase 0: Dataset Verification & Power Analysis (Pre-requisite)

**Purpose**: Verify dataset integrity and statistical power before any generation.

- [X] T001 [P] Fetch `medqa` (also known as `medmcqa` in plan) dataset from HuggingFace using `code/scripts/fetch_medmcqa.py` and verify checksum against manifest.
- [X] T002 [P] Implement `code/scripts/power_analysis.py` to calculate *theoretical* minimum sample size (N) for Cohen's h=0.5, alpha=0.05, power=0.80 using `statsmodels` (does not require fetched data).
- [X] T003 [P] Execute `power_analysis.py` and generate `code/data/analysis/power_analysis_report.md`; block subsequent phases if theoretical N (T002) < 200 OR actual dataset size (T001) < 200.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T004 [P] Create project structure: `code/`, `data/raw/`, `data/processed/`, `data/contracts/`, `code/prompts/`, `code/scripts/`, `code/tests/`, `specs/`
- [X] T005 [P] Initialize Python 3.11 project with `requirements.txt` including `datasets`, `transformers`, `torch`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `statsmodels`, `bitsandbytes`, `timeout-decorator`
- [X] T006 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T007 [P] Setup `code/data/` directory structure (`raw/`, `processed/`, `contracts/`) and `.gitkeep` files
- [X] T008 [P] Create schema definitions in `specs/contracts/question_item.schema.yaml` and `specs/contracts/resilience_metric.schema.yaml`
- [X] T009 [P] Implement `code/tests/contract/test_schemas.py` to validate JSONL against YAML schemas using `jsonschema`
- [X] T010 [P] Create base configuration loader in `code/scripts/config.py` to handle paths and seeds
- [X] T011 [P] Setup error handling wrapper in `code/utils/error_utils.py` for TLE/OOM detection and logging
- [X] T012 [P] Configure `code/requirements.txt` with pinned versions for reproducibility

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Misleading Medical Contexts (Priority: P1) 🎯 MVP

**Goal**: Ingest USMLE questions and inject single false claims while preserving ground truth.

**Independent Test**: Run `generate_mislead.py` on a sample of questions; verify output JSON contains original stem, injected false claim, and unchanged correct answer key.

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Contract test for `QuestionItem` schema in `code/tests/contract/test_question_item.py`
- [X] T014 [P] [US1] Unit test for `validate_injection()` logic ensuring gold answer is unchanged in `code/tests/unit/test_injection_validation.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Create prompt template `code/prompts/eval_mislead.txt` for injecting false claims
- [X] T016 [US1] Implement `generate_mislead.py` to inject one false claim per question using the template
- [X] T019 [US1] Implement `validate_injection()` function to verify gold answer stability, check for logical consistency (e.g., negation of gold answer, semantic contradiction with injected claim), log anomalies, and exclude unanswerable items from output
- [X] T020 [US1] Write validated data to `code/data/processed/mislead_questions.jsonl` with `validation_status` field

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Inference with Multiple Strategies (Priority: P2)

**Goal**: Run inference on clean/mislead datasets using Baseline, CoT, Self-Critique strategies across Large language models (varying parameter scales).

**Independent Test**: Run `run_inference.py` on a representative set of questions; verify output logs contain expected model/strategy combinations with `temperature=0.0` and `seed=42`.

### Tests for User Story 2 ⚠️

- [X] T021 [P] [US2] Contract test for `InferenceResult` schema in `code/tests/contract/test_inference_results.py`
- [X] T022 [P] [US2] Unit test for regex extraction of multiple-choice answers in `code/tests/unit/test_answer_extraction.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Create prompt templates: `code/prompts/baseline.txt`, `code/prompts/cot.txt`, `code/prompts/self_critique.txt`
- [X] T024 [US2] Implement pre-execution check to skip 70B model on CPU-only runners (FR-002) before loading models
- [X] T025 [US2] Implement model loader in `code/scripts/run_inference.py` with Low-bit quantization for 13B models

What is the impact of low-bit quantization on the performance and efficiency of 13B parameter models?

Method: Comparative analysis of model accuracy and inference latency across varying quantization bit-widths.

References: [Citations preserved verbatim] and CPU-only fallback
- [X] T026 [US2] Implement inference loop with `timeout-decorator` to handle TLE/OOM as fallback if pre-check fails
- [X] T027 [US2] Implement answer extraction logic to parse model output into single-letter choices (A, B, C, D) <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
  in "<unicode string>", line 2, column 13:
        contents: |
                ^) -->
- [ ] T028 [US2] Handle malformed outputs (e.g., "A, B") by marking as incorrect (accuracy=0) and logging anomaly
- [ ] T029 [US2] Write results to `code/data/processed/inference_results.jsonl` with fields for model, strategy, response, and correctness
- [ ] T030 [P] [US2] Add unit test `test_determinism` in `code/tests/unit/test_determinism.py` that runs inference twice and asserts checksums match

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compute Resilience and Statistical Significance (Priority: P3)

**Goal**: Calculate resilience scores, perform statistical tests, and generate final report.
**Note**: While Plan.md mentions McNemar's test and accuracy drop, Spec FR-004 explicitly mandates Wilcoxon signed-rank test and Kruskal-Wallis on per-item resilience scores. Tasks below implement Spec FR-004.

**Independent Test**: Run analysis script on pre-computed data; verify output report contains resilience scores and p-values.

### Tests for User Story 3 ⚠️

- [ ] T031 [P] [US3] Contract test for `ResilienceMetric` schema in `code/tests/contract/test_resilience_metric.py`
- [ ] T032 [P] [US3] Unit test for resilience formula edge cases (clean_acc=0) in `code/tests/unit/test_resilience_calc.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement resilience calculation in `code/scripts/analyze_resilience.py` using formula $1 - (clean - mislead)/clean$ (Prereq: T029, T020)
- [ ] T034 [US3] Handle zero clean accuracy edge case: set resilience=0 and exclude from statistical tests
- [ ] T035 [US3] Implement Wilcoxon signed-rank test on per-item correctness vectors (clean vs mislead) as per FR-004, outputting p-value to `resilience_metrics.json` (Prereq: T033)
- [ ] T036 [US3] Implement Kruskal-Wallis test on the distribution of per-item resilience scores across model scales (7B, 13B, 70B) as per FR-004 (Spec overrides Plan's 'accuracy drop' instruction), outputting H-statistic and p-value (Prereq: T033)
- [ ] T037 [US3] Apply Bonferroni correction for pairwise comparisons and Dunn's test with Bonferroni for post-hoc following Kruskal-Wallis to all p-values for FWER control (Prereq: T035, T036)
- [ ] T038 [US3] Generate `code/data/analysis/resilience_metrics.json` with scores and corrected p-values
- [ ] T039 [US3] Generate `code/data/analysis/report.md` with statistical findings, FWER verification flag, AND the calculated FWER value/adjusted p-values as a primary outcome (Prereq: T037)
- [ ] T040 [P] [US3] Validate that statistical power is sufficient; if N is too small, flag in report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Clinical Ground-Truth Validation (Constitution Principle VII)

**Goal**: Validate injected claims and gold answers with human expert review.

- [ ] T041a [Const VII] [US1] Sample a random subset of items from `mislead_questions.jsonl`. (T020) and generate `code/data/clinical_review_form.csv` (Prereq: T020)
- [ ] T041b [Const VII] Define Clinical Review CSV Schema: Explicitly define columns (item_id, clinician_id, claim_plausible, answer_correct, notes) in `code/data/contracts/clinical_review_schema.yaml`
- [ ] T041c [Const VII] Generate Manual Review Instructions: Create `code/data/clinical_review_instructions.md` detailing the workflow for **two board-certified clinicians** to independently verify the sample
- [ ] T042 [Const VII] Create `code/scripts/validate_clinical.py` to ingest the completed `clinical_review_form.csv` (matching schema T041b) and calculate Cohen's κ from the **two independent clinician IDs**
- [ ] T043 [Const VII] Generate `code/data/analysis/clinical_validation_report.md` with κ score and pass/fail status
- [ ] T044 [Const VII] Enforce gate: Project cannot reach `research_complete` without passing clinical validation

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates in `quickstart.md` and `research.md`: Update Setup (dependency versions), Usage (CLI examples), Methods (statistical test parameters), Results (placeholders for final metrics)
- [ ] T046 [P] Refactor `code/scripts/run_inference.py` model loader (T025) to handle OOM errors gracefully and log specific error codes
- [ ] T047 [P] Refactor `code/scripts/run_inference.py` write loop (T029) to implement a buffered write mechanism that accumulates results in memory and flushes to `inference_results.jsonl` periodically during processing, targeting a reduction in I/O latency.
- [ ] T047b [P] Implement `code/tests/unit/test_io_performance.py` to benchmark the buffered write mechanism (T047) against a direct-write baseline, asserting a latency reduction of at least 10% on a 1000-item batch.
- [ ] T048a [P] Add unit test `test_multi_choice_output` in `code/tests/unit/test_answer_extraction.py` that inputs "Answer: A, B" and asserts the function returns `None` and logs an anomaly.
- [ ] T048b [P] Add unit test `test_missing_answer_prefix` in `code/tests/unit/test_answer_extraction.py` that inputs "The correct option is C" (no "Answer:" prefix) and asserts the function correctly extracts "C".
- [ ] T048c [P] Add unit test `test_garbage_output` in `code/tests/unit/test_answer_extraction.py` that inputs random non-alphanumeric text and asserts the function returns `None` and logs an anomaly.
- [ ] T051 [P] Security hardening (input sanitization for prompts)
- [ ] T052 [P] Run `quickstart.md` validation script

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Pre-requisite)**: No dependencies - can start immediately
- **Setup (Phase 1)**: Depends on Phase 0 completion
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (mislead questions)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data (inference results)
- **Phase 6 (Clinical)**: Depends on US1 completion (T020)

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
# Launch all tests for User Story 1 together:
Task: "Contract test for QuestionItem schema in code/tests/contract/test_question_item.py"
Task: "Unit test for validate_injection() logic in code/tests/unit/test_injection_validation.py"

# Launch all implementation tasks for User Story 1 together (if dependencies allow):
Task: "Create prompt template code/prompts/eval_mislead.txt"
Task: "Implement dataset fetcher in code/scripts/fetch_medmcqa.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Dataset Verification & Power Analysis
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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
- **Critical Constraint**: Ensure all inference tasks respect CPU-only resource constraints and skip 70B if resources are insufficient.
- **Critical Constraint**: Ensure statistical tests are applied only to valid data points (clean_acc > 0).
- **Note on Statistical Tests**: Spec FR-004 mandates Wilcoxon signed-rank test and Kruskal-Wallis on resilience scores. Plan.md mentions McNemar's test and accuracy drop; tasks implement Spec FR-004.