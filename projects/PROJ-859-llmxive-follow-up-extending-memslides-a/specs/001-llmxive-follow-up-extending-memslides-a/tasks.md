# Tasks: llmXive Follow-up: Trace Compressibility Analysis

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-memslides-a/`
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

- [X] T001a [P] Create project root directory structure (`projects/PROJ-859-llmxive-follow-up-extending-memslides-a/`)
- [X] T001b [P] Create `code/`, `data/`, `tests/`, `contracts/` directories
- [X] T001c [P] Create `code/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/held_out/.gitkeep`
- [X] T001d [P] Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, numpy, pyyaml, pytest, sentence-transformers, statsmodels, scipy)
- [X] T001e [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create contract schemas in `contracts/` (`trace.schema.yaml`, `metrics.schema.yaml`, `benchmark_results.schema.yaml`, `compressibility_analysis.schema.yaml`). **Note**: `compressibility_analysis.schema.yaml` must validate statistical artifacts (regression coefficients, p-values, and trade-off curve data points) to ensure the Single Source of Truth principle for the paper.
- [ ] T005 [P] Implement `contracts/trace.schema.yaml` validation logic in `code/contracts/__init__.py`
- [X] T006 [P] Setup `code/config.py` with seeds, paths, and threshold configurations
- [ ] T007 Create base data loaders and schema validators in `code/utils/`
- [ ] T008 Configure `pytest` with contract test plugins in `tests/contract/`
- [ ] T009 Setup environment configuration management (`.env.example`, `config.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Trace Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of multi-turn revision sessions based on the MemSlides benchmark schema, recording tool-execution traces and resulting slide states.

**Independent Test**: Verify the generation of a substantial set of unique session files where each file contains a valid sequence of tool calls and a corresponding ground-truth slide state.

**Dependency**: Requires Phase 2 completion.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation (T012) to ensure they run against the generated data.**

- [X] T010 [P] [US1] Contract test for generated trace schema in `tests/contract/test_trace_schema.py` (Validates output of T012)
- [X] T011 [P] [US1] Integration test for dataset generation pipeline in `tests/integration/test_synthetic_generation.py` (Validates end-to-end flow of T012)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/generators/synthetic_trace.py` to generate multi-turn sessions mimicking MemSlides schema (FR-001). **Deliverables**: Output files named `session_{uuid}.json` containing `exact_tool_sequence` and `raw_arg_variance`; use a fixed random seed for reproducibility; ensure schema matches `contracts/trace.schema.yaml`.
- [ ] T013 [US1] Ensure `synthetic_trace.py` varies sequence length, tool types, and argument variance
- [ ] T014 [US1] Implement logic to record `exact_tool_sequence` and `raw_arg_variance` in trace artifacts (Trace Structural Integrity)
- [~] T015 [US1] Write generated traces to `data/raw/` as JSON files with ground-truth slide states
- [~] T016 [US1] Add edge case handling: zero tool repetitions (high entropy) and undefined argument variance (impute default)
- [~] T017 [US1] Log generation statistics and checksums to a state file

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Metric Extraction & Rule Induction (Priority: P2)

**Goal**: Compute structural metrics (sequence entropy, tool-repetition frequency, argument semantic variance) for each trace and train a lightweight, CPU-based rule-induction model **on a per-trace basis** to learn symbolic rules and calculate a specific "Compressibility Score" for each trace.

**Independent Test**: Run the extraction and induction pipeline on a subset of data and verify the output includes a computed feature matrix and a CSV of per-trace compressibility scores with non-zero variance.

**Dependency**: Requires completion of Phase 3 (US1) data generation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for metrics schema in `tests/contract/test_metrics_schema.py`
- [~] T019 [P] [US2] Unit test for entropy and variance calculations in `tests/unit/test_metrics_extract.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/metrics/extract.py` to compute sequence entropy and tool-repetition frequency (FR-002)
- [X] T021 [US2] Implement `code/metrics/extract.py` to compute argument semantic variance using `sentence-transformers/all-MiniLM-L6-v2` (CPU-only). **Definition**: Variance = mean pairwise cosine distance of all argument embeddings in a trace. **Note**: Model size ~80MB fits within 7GB RAM constraint. [UNRESOLVED-CLAIM: c_067a9ddd — status=not_enough_info]
- [ ] T022 [US2] Generate `data/processed/feature_matrix.csv` containing structural metrics for every trace
- [X] T023 [P] [US2] Implement `code/models/rule_induction.py` to perform **per-trace rule induction** (FR-003). **Goal**: For EACH trace (or small batch), train a lightweight CPU model (e.g., Decision Tree with strict depth limits) to reproduce the trace's `final_state`. **Deliverable**: A set of symbolic rules and a computed "Compressibility Score" for EACH trace.
- [~] T024 [US2] Implement logic to calculate "Compressibility Score" for each trace as `RuleSetSize / TraceLength` conditioned on `Fidelity >= 90%`. **Constraint**: Use the per-trace induction results from T023, not a global model.
- [~] T025 [US2] Ensure rule induction model is CPU-tractable and completes within time limits for the full dataset size.
- [ ] T026 [US2] Save per-trace rule sets and compressibility scores to `data/processed/per_trace_scores.csv` and `data/processed/rules/`.
- [X] T027 [US2] Implement `code/evaluation/calculate_compression_ratio.py` to compute **per-trace fidelity** data points (Fidelity Loss vs. Compression Ratio) required to plot the trade-off curve (SC-002). **Deliverable**: A CSV mapping each trace to its compression ratio and fidelity loss.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity & Latency Benchmarking (Priority: P3)

**Goal**: Replace the raw memory module with the generated symbolic rule bank and compare Edit Accuracy and Retrieval Latency against the original baseline on a held-out test set.

**Independent Test**: Execute the benchmark script on a held-out set of requests and verify the output includes a comparative report of Edit Accuracy and Retrieval Latency for both agents.

**Dependency**: Requires completion of Phase 4 (US2) model training and per-trace score generation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Contract test for benchmark results schema in `tests/contract/test_benchmark_results_schema.py`
- [X] T029 [P] [US3] Integration test for agent comparison pipeline in `tests/integration/test_agent_benchmark.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/agents/baseline.py` (raw memory agent)
- [X] T031 [P] [US3] Implement `code/agents/compressed.py` (symbolic rule agent using global rule set for latency comparison)
- [X] T032 [US3] Implement `code/evaluation/benchmark.py` to run both agents on held-out test set (FR-004)
- [~] T033 [US3] Measure and record Edit Accuracy (fraction of edits matching ground truth) for both agents (FR-005). **Method**: Exact match on structured slide objects.
- [~] T034 [US3] Measure and record Retrieval Latency (time to context-ready) for both agents (FR-005)
- [X] T035 [US3] Implement `code/evaluation/stats.py` for Beta regression of **Fidelity Loss** (1 - CompressedAccuracy) on Structural Metrics (FR-006). **Note**: Fidelity Loss is strictly bounded in (0,1), satisfying Beta regression assumptions.
- [~] T036 [US3] Implement Spearman correlation analysis between structural metrics and per-trace Compressibility Score (from T026)
- [ ] T037 [US3] Implement sensitivity analysis sweeping the **compression threshold** (e.g., fidelity cutoff or rule pruning threshold) to report how fidelity rates vary (FR-007). **Note**: Sweep the threshold directly, not just hyperparameters.
- [ ] T038 [US3] Generate comparative JSON report to `data/processed/benchmark_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (update `research.md`, `data-model.md`, `quickstart.md`)
- [ ] T040a [P] Refactor `code/agents/baseline.py` to remove unused imports and add type hints
- [ ] T040b [P] Refactor `code/agents/compressed.py` to remove unused imports and add type hints
- [ ] T041 Run full pipeline reproducibility check with pinned seeds
- [ ] T042 [P] Additional unit tests in `tests/unit/`
- [ ] T043 Security hardening (input validation, path sanitization)
- [ ] T044 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Strictly sequential data flow:
 - **Phase 3 (US1)**: Depends on Phase 2. Generates raw data.
 - **Phase 4 (US2)**: Depends on Phase 3. Consumes US1 data to perform per-trace rule induction and generate per-trace scores.
 - **Phase 5 (US3)**: Depends on Phase 4. Consumes US2 per-trace scores and global model for benchmarking and statistical analysis.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Cannot** start until US1 is complete (requires generated traces).
- **User Story 3 (P3)**: **Cannot** start until US2 is complete (requires per-trace scores and global rule set).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- **Note**: User Stories themselves cannot run in parallel due to strict data dependencies (US1 -> US2 -> US3).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for generated trace schema in tests/contract/test_trace_schema.py"
Task: "Integration test for dataset generation pipeline in tests/integration/test_synthetic_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generators/synthetic_trace.py to generate multi-turn sessions"
Task: "Ensure synthetic_trace.py varies sequence length, tool types, and argument variance"
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
3. Once US1 is done:
 - Developer B: User Story 2
4. Once US2 is done:
 - Developer C: User Story 3
5. Stories complete and integrate sequentially.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All models must be CPU-tractable (Decision Tree, RuleFit, scikit-learn). No GPU, no 8-bit/4-bit quantization, no large LMs.
- **Data**: Synthetic data must be generated using the MemSlides schema; no fake/random data that bypasses real structural analysis.
- **Ordering**: Strict US1 -> US2 -> US3 flow enforced.
- **Critical Correction**: Phase 4 now implements **per-trace** rule induction to satisfy FR-003 and enable the statistical correlation in FR-006. Phase 5 uses **Fidelity Loss** (bounded) for Beta regression, not Edit Accuracy Difference.