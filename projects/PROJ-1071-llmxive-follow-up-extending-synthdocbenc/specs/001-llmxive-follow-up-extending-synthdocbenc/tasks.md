# Tasks: llmXive follow-up: extending "SynthDocBench" with Decoupled Retrieval

**Input**: Design documents from `/specs/001-llmxive-retrieval-extension/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-1071-llmxive-follow-up-extending-synthdocbenc/`)
- [X] T002 Initialize Python 3.11 project with dependencies (`requirements.txt`: `transformers`, `torch`, `faiss-cpu`, `pandas`, `scikit-learn`, `pytesseract`, `pdf2image`, `reportlab`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` with state update logic, random seed pinning, and checksum generation (Constitution Principle V)
- [ ] T005 [P] Create base data models and schema validators in `code/models/` matching `contracts/` YAML schemas
- [ ] T006 [P] Setup logging infrastructure to `logs/` with structured JSON output for pipeline tracing
- [X] T007 [P] Implement `code/doc_generator.py` to GENERATE exactly 200 synthetic long documents with precise 'middle-third' metadata. The task must:
 1. Generate a set of valid PDFs and corresponding metadata files (JSON/Parquet) containing page-level layout and text density info.
 2. Ensure every document has a valid 'middle-third' region with sufficient text density to support the bias hypothesis (SC-001).
 3. Save artifacts to `data/raw/` and record checksums in `data/checksums.json`.
 4. Verify the generated set contains a sufficient number of documents AND that the 'middle-third' text density check passes for all. (FR-001, US-01).
 The task is complete only when a sufficient quantity of valid PDFs exists in `data/raw/`, checksums match, and the text density validation passes.
- [X] T008 [P] Create `code/config/models.yaml` defining the VLMs and their stratification by context size (k, 8k, 32k tokens) for FR-004 compliance
- [X] T009 [P] Write unit tests in `tests/unit/test_doc_generator.py` to verify synthetic document structure, middle-third metadata, and the 200-document count

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproduce Baseline "Middle-Third" Bias (Priority: P1) 🎯 MVP

**Goal**: Execute the original SynthDocBench evaluation protocol on static PDF images to reproduce the "middle-third" bias and establish per-model baselines.

**Independent Test**: Run the static-image evaluation pipeline on generated synthetic documents and confirm the accuracy dip in the middle third matches the expected trend.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/baseline_eval.py` to load static PDF images and run VLM inference for the models defined in `code/config/models.yaml` (FR-004). Include profiling hooks to log latency and memory usage to `data/derived/perf_metrics.json` (SC-004, SC-005).
- [X] T011 [US1] Implement logic in `code/baseline_eval.py` to split questions into first, middle, and last thirds and compute per-third accuracy. **CRITICAL**: The code must MEASURE and LOG the delta. It must NOT enforce, assert, or ensure that the delta is ≥ 5%. However, it MUST calculate the `delta_middle_vs_others` metric and a boolean `bias_threshold_met` (true if delta ≥ 5%) and record these in `data/derived/baseline_metrics.json`. (US-01, SC-001)
- [X] T012 [US1] Generate `data/derived/baseline_metrics.json` containing per-model accuracy tables, positional bias trends, the `delta_middle_vs_others` value, and the `bias_threshold_met` flag.
- [X] T013 [US1] [P] Write unit tests in `tests/unit/test_baseline_eval.py` for positional splitting logic and accuracy calculation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Retrieval-Augmented Inference Pipeline (Priority: P2)

**Goal**: Run the two-step inference pipeline where relevant page snippets are retrieved via CPU-based index and injected into the VLM context.

**Independent Test**: Select a "middle-third" question, run retrieval to fetch correct text, and verify the VLM receives image + text before generating an answer.

### Implementation for User Story 2

- [ ] T014 [US2] Implement `code/retrieval_index.py` to perform OCR on generated documents using Tesseract and build a FAISS CPU index. Include profiling hooks to log latency and memory usage to `data/derived/perf_metrics.json` (SC-005). (FR-002)
- [ ] T015 [US2] Implement robust error handling in `code/retrieval_index.py` to skip pages where OCR fails (Edge Case: OCR failure) without crashing
- [ ] T016 [US2] Implement `code/retrieval_eval.py` to generate search queries from "middle-third" questions. **CRITICAL**: This task must explicitly construct a `ground_truth_retrieval_set` artifact (mapping each question ID to the correct page/snippet ID based on metadata) required for FR-008 metrics. (FR-008)
- [ ] T017 [US2] Implement semantic similarity scoring, token limiting (≤ 2048 tokens), and retrieval precision/recall calculation in `code/retrieval_eval.py`. **CRITICAL**: This task MUST consume the `ground_truth_retrieval_set` constructed in T016 to calculate True Positives/False Positives against the ground-truth answers (US-02, FR-008). Ensure metrics are calculated during retrieval.
- [ ] T018 [US2] Implement combined input payload construction in `code/retrieval_eval.py` (Image + Retrieved Text) ensuring it fits within model context limits (FR-003)
- [ ] T019 [US2] Implement the retrieval-augmented inference pipeline logic in `code/retrieval_eval.py` to produce `data/derived/retrieval_metrics.json` for all candidate models. **Dependencies**: Requires completion of T014 (FAISS index) and T016 (Ground Truth Set). **CRITICAL**: This task MUST include the step to measure and report the "false-positive rate" defined in SC-003 (retrieved snippet similarity < 0.5 AND no ground truth) in the final artifact. (FR-003, FR-004, SC-003)
- [ ] T020 [US2] [P] Write unit tests in `tests/unit/test_retrieval_index.py` for OCR fallback and FAISS index construction
- [ ] T021 [US2] [P] Write unit tests in `tests/unit/test_retrieval_eval.py` for token limiting, semantic similarity scoring, precision/recall logic, and ground-truth set validation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantify Accuracy Recovery and Correlation (Priority: P3)

**Goal**: Compute accuracy delta between retrieval-augmented and baseline conditions, and correlate recovery magnitude with model context window size.

**Independent Test**: Run statistical analysis script on collected metrics and verify output includes Spearman correlation coefficient and p-value.

### Implementation for User Story 3

- [ ] T022 [US3] Implement `code/stats_analysis.py` to load `data/derived/baseline_metrics.json` and `data/derived/retrieval_metrics.json` and compute accuracy deltas for "middle-third" questions. Include profiling hooks to log execution time to `data/derived/perf_metrics.json` (SC-004). (FR-005)
- [ ] T023 [US3] Implement logic in `code/stats_analysis.py` to verify positive recovery for at least some models (US-03 Acceptance)
- [ ] T024 [US3] Implement Spearman rank correlation analysis in `code/stats_analysis.py` between recovery deltas and native context window sizes. **CRITICAL**: Must perform a formal statistical test against the null hypothesis of zero correlation, calculating the p-value. (FR-006)
- [ ] T025 [US3] Implement classification logic in `code/stats_analysis.py` to output "inverse" if r < -0.3 and p < 0.05, else "no significant inverse relationship". **CRITICAL**: The output artifact `data/derived/statistical_results.json` MUST contain the raw Spearman r value, the p-value, and the classification string. (US-03 Acceptance)
- [ ] T026 [US3] Implement validation logic in `code/stats_analysis.py` to measure performance on "easy" questions (first/last third) to ensure no degradation (FR-007)
- [ ] T027 [US3] Generate `data/derived/statistical_results.json` containing correlation coefficients, p-values, recovery metrics, and classification results.
- [ ] T028 [US3] [P] Write unit tests in `tests/unit/test_stats_analysis.py` for delta calculation, correlation logic, and hypothesis test validation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `quickstart.md` with instructions for running the full pipeline
- [ ] T030 [P] Run integration tests in `tests/integration/` to verify end-to-end data flow (Gen → Baseline → Index → Retrieval → Stats)
- [ ] T031 [P] Final documentation review and `research.md` updates

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (P1)** must complete before US3 can calculate deltas
 - **US2 (P2)** must complete before US3 can calculate deltas
 - US1 and US2 can proceed in parallel once Foundation is ready
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, but shares data generation
- **User Story 3 (P3)**: Can start ONLY after US1 and US2 are complete (requires both baseline and retrieval results)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (US1 & US2)

---

## Parallel Example: User Story 1 & 2

```bash
# Launch Foundation tasks in parallel:
Task: "Implement code/utils.py..."
Task: "Create base data models..."
Task: "Setup logging infrastructure..."
Task: "Create code/config/models.yaml..."

# Once Foundation is done, launch US1 and US2 in parallel:
Task: "Implement code/baseline_eval.py..." (US1)
Task: "Implement code/retrieval_index.py..." (US2)
Task: "Implement code/retrieval_eval.py..." (US2)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Baseline Bias Reproduction)
4. **STOP and VALIDATE**: Confirm middle-third bias exists in generated data
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo Baseline Bias
3. Add User Story 2 → Test independently → Demo Retrieval Injection
4. Add User Story 3 → Test independently → Demo Correlation Analysis
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Baseline)
 - Developer B: User Story 2 (Retrieval Pipeline)
3. Developer C (or A/B after completion): User Story 3 (Stats & Correlation)
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