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
- [X] T001c [P] Create `code/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/held_out/.gitkeep`, `data/training/.gitkeep`
- [X] T001d [P] Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, numpy, pyyaml, pytest, sentence-transformers, statsmodels, scipy)
- [X] T001e [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create contract schemas in `contracts/` (`trace.schema.yaml`, `metrics.schema.yaml`, `benchmark_results.schema.yaml`, `compressibility_analysis.schema.yaml`). **Note**: `compressibility_analysis.schema.yaml` must validate statistical artifacts including: `beta_coefficients`, `p_values`, `trade_off_curve_points`, `edit_accuracy_difference`, and `delta_accuracy` to ensure the Single Source of Truth principle for the paper.
- [X] T005 [P] Implement `contracts/trace.schema.yaml` validation logic in `code/contracts/__init__.py`
- [X] T006 [P] Setup `code/config.py` with seeds, paths, and threshold configurations
- [X] T007 Create base data loaders and schema validators in `code/utils/`
- [X] T008 Configure `pytest` with contract test plugins in `tests/contract/`
- [X] T009 [P] [Foundational] Setup environment configuration management. **Explicit Constraint**: DO NOT create `config.yaml`. All configuration MUST be defined in `code/config.py` only. This task updates `code/config.py` to include default paths, seeds, and threshold parameters, ensuring a single source of truth for configuration state.
- [X] T050 [P] [Foundational] Update `quickstart.md` to document the strict execution order: `synthetic_trace.py` → `extract.py` → `rule_induction.py` → `calculate_deltas.py` → `benchmark.py` → `stats.py`, emphasizing that skipping steps causes immediate failure. **Dependency**: Must be done early to guide team implementation.

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

- [X] T012 [US1] Implement `code/generators/synthetic_trace.py` to generate **5000** multi-turn sessions mimicking MemSlides schema (FR-001). **Deliverables**:
 1. Output files named `session_{uuid}.json` containing `exact_tool_sequence` and `raw_arg_variance`; use a **fixed random seed** for reproducibility; ensure schema matches `contracts/trace.schema.yaml`.
 2. **Variation**: Ensure sequence length, tool types, and argument variance vary across sessions.
 3. **Edge Cases**: Handle zero tool repetitions (high entropy) and undefined argument variance (impute default or log warning).
 4. **Split**: Immediately split the dataset into a training set (saved to `data/training/`) and a held-out set (saved to `data/held_out/`).
 5. **Fail-Loud**: If the MemSlides schema cannot be loaded or the seed fails to produce valid variation, raise `DataGenerationError` immediately. Do NOT fallback to synthetic/mock data.
 6. **Logging**: Log generation statistics and checksums to a state file.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Metric Extraction & Rule Induction (Priority: P2)

**Goal**: Compute structural metrics (sequence entropy, tool-repetition frequency, argument semantic variance) for each trace and train a lightweight, CPU-based rule-induction model on the **training split** to learn symbolic rules and calculate a specific "Compressibility Score" for each trace based on **held-out performance**.

**Independent Test**: Run the extraction and induction pipeline on the training set and verify the output includes a computed feature matrix and a CSV of per-trace compressibility scores with non-zero variance.

**Dependency**: Requires completion of Phase 3 (US1) data generation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for metrics schema in `tests/contract/test_metrics_schema.py`
- [X] T019 [P] [US2] Unit test for entropy and variance calculations in `tests/unit/test_metrics_extract.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/metrics/extract.py` to compute **all** structural metrics (sequence entropy, tool-repetition frequency, argument semantic variance using `sentence-transformers/all-MiniLM-L6-v2` CPU-only) for traces in `data/training/` and `data/held_out/`. **Deliverable**: Generate `data/processed/feature_matrix.csv` containing structural metrics for every trace. **Definition**: Variance = mean pairwise cosine distance of all argument embeddings. Handle undefined variance with default imputation.
- [X] T023 [US2] Implement `code/models/rule_induction.py` to perform **global rule induction** (FR-003). **Logic**:
 1. Load `feature_matrix.csv` and split into **[deferred]** training and **[deferred]** held-out sets (matching T012 split logic), reading from `data/training/` and `data/held_out/`.
 2. Train a lightweight CPU model (e.g., Decision Tree with strict depth limits) on the **training set** to predict the `final_state` (or a compressed representation thereof).
 3. Evaluate the model on the **held-out set** to calculate Fidelity.
 4. Calculate "Compressibility Score" for each trace in the held-out set as `RuleSetSize / TraceLength` conditioned on `Fidelity >= config.threshold` (where Fidelity is derived from the model's held-out prediction accuracy). **Note**: Do not hard-code 90%; use the variable threshold from `code/config.py` for later sweeping.
 5. **Deliverable**: Save per-trace scores to `data/processed/per_trace_scores.csv` with columns: `trace_id`, `score`, `rule_count`, `fidelity`, `train_fidelity`, `holdout_fidelity`. **Dependency**: **Must wait for T012 completion**.
- [ ] T026b [US2] Implement aggregation logic to combine per-trace rule sets from T023 into a **global rule set**. **Deliverable**: Save `data/processed/rules/global_rules.json` containing the aggregated symbolic rules required for the benchmarking phase (FR-004).
- [ ] T027a [US2] Implement `code/evaluation/sweep_thresholds.py` to generate **multiple compressed rule sets** by sweeping a compression/pruning threshold (e.g., min_support, max_depth, or rule_count) across the global rule set. **Deliverable**: Save a collection of rule sets to `data/processed/rules/sweeps/` and a metadata file `data/processed/sweep_config.json`. **Dependency**: Requires T026b output. **Note**: This task is NOT [P] as it depends on T026b.
- [ ] T027b [US2] Implement `code/evaluation/calculate_compression_ratio.py` to compute **per-trace fidelity data points** for the trade-off curve (SC-002). **Logic**: For each threshold in the sweep (T027a), run the agent on a sample of traces to measure Fidelity Loss and Compression Ratio. **Deliverable**: A CSV `data/processed/trade_off_curve.csv` mapping `threshold`, `compression_ratio`, and `fidelity_loss`. **Dependency**: Requires T027a output. **Note**: This task is NOT [P] as it depends on T027a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity & Latency Benchmarking (Priority: P3)

**Goal**: Replace the raw memory module with the generated symbolic rule bank and compare Edit Accuracy and Retrieval Latency against the original baseline on a held-out test set.

**Independent Test**: Execute the benchmark script on a held-out set of requests and verify the output includes a comparative report of Edit Accuracy and Retrieval Latency for both agents.

**Dependency**: Requires completion of Phase 4 (US2) model training and per-trace score generation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for benchmark results schema in `tests/contract/test_benchmark_results_schema.py`
- [X] T029 [P] [US3] Integration test for agent comparison pipeline in `tests/integration/test_agent_benchmark.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/agents/baseline.py` (raw memory agent)
- [ ] T031 [US3] Implement `code/agents/compressed.py` (symbolic rule agent using **global rule set** from `data/processed/rules/global_rules.json` generated by T026b). **Dependency**: **Must wait for T026b completion**. This task is NOT [P] because it depends on the global rule artifact.
- [X] T032 [US3] Implement `code/evaluation/benchmark.py` to run both agents on the **held-out test set** (from T012) (FR-004).
- [ ] T033 [US3] Measure and record Edit Accuracy (fraction of edits matching ground truth) for both agents (FR-005). **Method**: Exact match on structured slide objects.
- [ ] T034 [US3] Measure and record Retrieval Latency (time to context-ready) for both agents (FR-005)
- [ ] T035b [US3] Implement `code/evaluation/calculate_deltas.py` to compute **Edit Accuracy Difference** (Baseline Accuracy - Compressed Accuracy) for each trace in the held-out set. **Deliverable**: Save `data/processed/accuracy_deltas.csv` with columns `trace_id`, `baseline_acc`, `compressed_acc`, `delta_acc`. **Note**: This must run before T035c.
- [ ] T035c [US3] Implement `code/evaluation/transform_metrics.py` to transform **Edit Accuracy Difference** (from T035b) into the **(0,1) domain** required for Beta regression. **Logic**: Apply a logit transformation or sigmoid scaling to map the delta (which may be negative or >1) to a bounded probability-like value, ensuring mathematical validity for Beta regression. **Deliverable**: Save `data/processed/transformed_deltas.csv`. **Dependency**: Requires T035b output.
- [ ] T035 [US3] Implement `code/evaluation/stats.py` for Beta regression of **Transformed Edit Accuracy Difference** (from T035c) on Structural Metrics (FR-006). **Input**: Requires `data/processed/transformed_deltas.csv` from T035c. **Note**: This task explicitly correlates structural metrics with the *transformed* Edit Accuracy Difference, satisfying FR-006 and SC-001.
- [ ] T036 [US3] Implement Spearman correlation analysis between structural metrics and per-trace Compressibility Score (from T023)
- [ ] T037 [US3] Implement sensitivity analysis sweeping the **compression threshold** (e.g., fidelity cutoff or rule pruning threshold) to report how **Edit Accuracy Difference** rates vary (FR-007). **Logic**: Iterate threshold T across a range of values, compute Edit Accuracy Difference for each, and save to `data/processed/sensitivity_sweep.csv`. **Note**: This task explicitly performs the *sweep* required by FR-007, measuring the stability of the *Edit Accuracy Difference* metric.
- [ ] T038 [US3] Generate comparative JSON report to `data/processed/benchmark_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `docs/` (update `research.md`, `data-model.md`, `quickstart.md`)
- [X] T040a [P] Refactor `code/agents/baseline.py` to remove unused imports and add type hints
- [X] T040b [P] Refactor `code/agents/compressed.py` to remove unused imports and add type hints
- [X] T041 Run full pipeline reproducibility check with pinned seeds
- [X] T042 [P] Additional unit tests in `tests/unit/`
- [X] T043 Security hardening (input validation, path sanitization)
- [X] T044 Run `quickstart.md` validation

---

## Phase 7: Data Integrity & Execution Safety (Revision Concerns)

**Goal**: Address execution-stage fabrication guards and data-flow dependencies identified in prior reviews.

**Dependency**: Must be integrated before final execution.

- [X] T046 [US2] Add explicit validation in `code/metrics/extract.py` to ensure `feature_matrix.csv` is generated ONLY after `data/training/` contains valid JSON files; fail the script if input data is missing or malformed.
- [X] T047 [US2] Add a dependency check in `code/models/rule_induction.py` to verify `data/processed/feature_matrix.csv` exists before attempting per-trace induction; raise an error if the feature matrix is absent.
- [X] T048 [US3] Ensure `code/evaluation/benchmark.py` explicitly loads the **global** rule set from `data/processed/rules/global_rules.json` (generated by T026b) before running the compressed agent; fail if the global model is missing.
- [X] T049 [P] [US3] Add a post-benchmark validation step in `code/evaluation/stats.py` to verify that the Beta regression input data (Transformed Edit Accuracy Difference) contains no NaNs or values outside (0,1); if invalid, raise an error and log the specific trace IDs causing the violation.
- [X] T051 [P] [US3] Add a post-benchmark validation step in `code/evaluation/calculate_deltas.py` to ensure `accuracy_deltas.csv` is generated correctly before T035c runs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Strictly sequential data flow:
 - **Phase 3 (US1)**: Depends on Phase 2. Generates raw data and splits it.
 - **Phase 4 (US2)**: Depends on Phase 3. Consumes US1 data to perform global rule induction and generate per-trace scores.
 - **Phase 5 (US3)**: Depends on Phase 4. Consumes US2 per-trace scores and global model for benchmarking and statistical analysis.
- **Phase 7 (Data Integrity)**: Must be integrated into the logic of Phases 3-5 before execution.
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
- Models within a story marked [P] can run in parallel (with explicit dependency notes)
- **Note**: User Stories themselves cannot run in parallel due to strict data dependencies (US1 -> US2 -> US3).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for generated trace schema in tests/contract/test_trace_schema.py"
Task: "Integration test for dataset generation pipeline in tests/integration/test_synthetic_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/generators/synthetic_trace.py to generate 5000 multi-turn sessions"
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
- **Critical Correction**: Phase 4 now implements **global rule induction** on the training split to evaluate on the held-out split, avoiding tautology. Phase 5 uses **Edit Accuracy Difference** (transformed) for Beta regression, satisfying FR-006.
- **Safety**: Phase 7 tasks (T046-T051) enforce strict fail-loud behavior to prevent fabrication and ensure data integrity.
- **Explicit Dependencies**: T023 depends on T012. T031 depends on T026b. T035b -> T035c -> T035 chain is strict. T027a -> T027b is strict.