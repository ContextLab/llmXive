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

- [X] T056 [P] [US1] Add a pre-generation check in `code/generators/synthetic_trace.py` to verify the MemSlides schema file exists and is valid YAML before attempting data generation; raise `FileNotFoundError` if missing. **Dependency**: Must run before T012. **Note**: Moved from Phase 7 to Phase 3 to ensure schema validation blocks generation.
- [X] T012 [US1] Implement `code/generators/synthetic_trace.py` to generate a substantial volume of multi-turn sessions mimicking MemSlides schema (FR-001). **Deliverables**:
 1. Output files named `session_{uuid}.json` containing `exact_tool_sequence` and `raw_arg_variance`; use a **fixed random seed** for reproducibility; ensure schema matches `contracts/trace.schema.yaml`.
 2. **Variation**: Ensure sequence length, tool types, and argument variance vary across sessions.
 3. **Edge Cases**: Handle zero tool repetitions (high entropy) by recording as data point. **Handle undefined argument variance by EXCLUDING the trace from the dataset and logging the exclusion.** Do NOT impute default values.
 4. **Split**: Immediately split the dataset into a **Training Set** (saved to `data/training/`) and a **Held-Out Set** (saved to `data/held_out/`). The **Held-Out Set** is strictly reserved for benchmarking (FR-004) and must NOT be used for rule induction.
 5. **Fail-Loud**: If the MemSlides schema cannot be loaded or the seed fails to produce valid variation, raise `DataGenerationError` immediately. Do NOT fallback to synthetic/mock data.
 6. **Logging**: Log generation statistics and checksums to a state file.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Metric Extraction & Rule Induction (Priority: P2)

**Goal**: Compute structural metrics for every trace and perform **aggregate rule induction** for global benchmarking AND **batched rule induction** to calculate a **Batch-Level Compressibility Proxy** using Leave-One-Out cross-validation.

**Independent Test**: Run the extraction and induction pipeline on the training set and verify the output includes a computed feature matrix, a global rule set, and per-batch proxy scores with non-zero fidelity on the held-out set.

**Dependency**: Requires completion of Phase 3 (US1) data generation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for metrics schema in `tests/contract/test_metrics_schema.py`
- [X] T019 [P] [US2] Unit test for entropy and variance calculations in `tests/unit/test_metrics_extract.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/metrics/extract.py` to compute **all** structural metrics (sequence entropy, tool-repetition frequency, argument semantic variance using `sentence-transformers/all-MiniLM-L6-v2` CPU-only) for traces. **Deliverable**: Provide pure functions `compute_entropy()`, `compute_repetition()`, `compute_variance()` that accept a trace object and return metric values. **Constraint**: If a trace lacks required fields (e.g., missing arguments) or `sentence-transformers` fails to load, **EXCLUDE the trace** from the final feature matrix and **log a JSON line to `data/processed/exclusion_log.json`** containing `trace_id`, `exclusion_reason` (e.g., "undefined_variance"), and `timestamp`. **DO NOT impute 0.0**. This ensures metrics are mathematically derivable from raw logs per Constitution Principle VI. **Dependency**: Requires T012 completion.
- [X] T021 [US2] Implement `code/metrics/pipeline.py` to orchestrate the feature matrix generation. **Logic**: Iterate over `data/training/` and `data/held_out/`, call functions from T020, and aggregate results. **Deliverable**: Generate `data/processed/feature_matrix.csv` containing structural metrics for every trace. **Column Definitions**: `trace_id` (str), `sequence_entropy` (float), `tool_repetition_freq` (float), `arg_semantic_variance` (float). **Checksum**: Record the SHA256 hash of the generated `feature_matrix.csv` as a **derived artifact hash** in the state file. **Dependency**: Requires T020 completion.
- [X] T023 [US2] Implement `code/models/rule_induction.py` to perform **aggregate rule induction** (FR-003). **Logic**:
 1. Load `feature_matrix.csv` (from T021) and restrict to the **Training Set**.
 2. Train a lightweight CPU model (Decision Tree with `max_depth=5`, `min_samples_leaf=10`) using aggregate structural metrics to predict the `final_state`.
 3. **Rule Extraction**: Export tree paths to JSON to generate a compact set of symbolic IF-THEN rules.
 4. Evaluate on the **Held-Out Set** to calculate baseline Fidelity.
 5. **Deliverable**: Save `data/processed/rules/global_rules_baseline.json` and a summary `data/processed/aggregate_model_summary.json`. **Dependency**: Requires T021 completion.
- [X] T024 [US2] Implement **Batched Leave-One-Out (LOO) Rule Induction** to calculate a **Batch-Level Compressibility Proxy**. **Logic**:
 1. Divide the **Training Set** into sliding windows of size N=50 (overlap 25).
 2. For each window, perform **Leave-One-Out Cross-Validation**:
    - For each trace `t` in the window:
      - Train a Decision Tree (`max_depth=3`, `min_samples_leaf=2`) on the other N-1 traces in the window to predict `final_state` actions.
      - Predict the `final_state` of `t` using this model.
      - Calculate **Fidelity** of the prediction against `t`'s actual `final_state`.
      - Calculate **RuleSetSize** (number of rules in the model).
      - Calculate **Batch-Level Compressibility Proxy** = `RuleSetSize / TraceLength(t)` if Fidelity >= `config.FIDELITY_TOLERANCE`, else NaN.
      - **Rationale**: This metric measures the *batch's* ability to compress trace `t`, serving as a proxy for the structural properties of `t` that enable compression.
 3. **Deliverable**: Save `data/processed/per_trace_scores.csv` with columns: `trace_id` (str), `rule_count` (int), `fidelity` (float), `batch_compressibility_proxy` (float). **Constraint**: If Fidelity < `config.FIDELITY_TOLERANCE`, set `batch_compressibility_proxy` to `NaN` and log a warning. **Dependency**: Requires T021 completion.
- [X] T026b [US2] Implement **Global Rule Set Aggregation** based on Per-Trace Scores. **Logic**:
 1. Load `per_trace_scores.csv` (from T024).
 2. Identify "high-scoring batches" (windows where mean `batch_compressibility_proxy` > median).
 3. Extract rules from the LOO models in these high-scoring batches.
 4. **Aggregation Algorithm**: Select rules that appear in >50% of the high-scoring batches and merge them into a single `global_rules.json`.
 5. **Deliverable**: Save `data/processed/rules/global_rules.json` containing the aggregated symbolic rules required for the benchmarking phase (FR-004). **Dependency**: Requires T024 completion.

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
- [X] T031 [US3] Implement `code/agents/compressed.py` (symbolic rule agent using **global rule set** from `data/processed/rules/global_rules.json` generated by T026b). **Dependency**: **Must wait for T026b completion**. This task is NOT [P] because it depends on the global rule artifact.
- [X] T032 [US3] Implement `code/evaluation/benchmark.py` to run **both agents** on the **held-out test set** (from T012) in a **single execution pass** to ensure data alignment (FR-004, FR-005). **Deliverables**:
 1. Measure and record **Edit Accuracy** (fraction of edits matching ground truth) for both agents.
 2. Measure and record **Retrieval Latency** (time to context-ready) for both agents.
 3. Output a single JSON report to `data/processed/benchmark_results.json` containing both metrics for every trace. **Note**: This task replaces the need for separate T033 and T034 tasks. **Dependency**: Explicitly requires the **Held-Out Set** artifact generated by T012.
- [X] T035b [US3] Implement `code/evaluation/calculate_deltas.py` to compute **Edit Accuracy Difference** (Baseline Accuracy - Compressed Accuracy) and **Fidelity Loss** (1.0 - Compressed Accuracy) for each trace in the held-out set. **Deliverable**: Save `data/processed/accuracy_deltas.csv` with columns `trace_id`, `baseline_acc`, `compressed_acc`, `delta_acc`, `fidelity_loss`. **Validation**: Assert that all `fidelity_loss` values are in [0.0, 1.0]. **raise** `ValueError` if invalid. **Dependency**: Requires T032 completion.
- [X] T035 [US3] Implement `code/evaluation/stats.py` for **statistical analysis** (FR-006). **Input**: Requires `data/processed/accuracy_deltas.csv` (T035b) and `data/processed/feature_matrix.csv` (T021). **Logic**:
 1. **Primary**: Perform **Beta regression** of **Edit Accuracy Difference** (Baseline - Compressed) on Structural Metrics. **Justification**: Per Constitution Principle VII and Plan Phase 1, the *difference* relative to baseline is the required metric to isolate the trade-off.
 2. **Secondary**: Perform **Spearman correlation** between structural metrics and raw Edit Accuracy Difference.
 3. **Deliverable**: Save `data/processed/statistical_analysis.json` containing `beta_coefficients`, `p_values`, `model_summary`. **Validation**: Ensure all p_values < 0.05 are flagged as significant. **Note**: Fixed syntax error 'rais' to 'raise'.
- [X] T035c [US3] Implement **Secondary Exploratory Analysis: Spearman Correlation with Batch-Level Compressibility Proxy**. **Input**: Requires `data/processed/per_trace_scores.csv` (T024) and `data/processed/feature_matrix.csv` (T021). **Logic**: Perform Spearman correlation between structural metrics and the `batch_compressibility_proxy` column. **Deliverable**: Append results to `data/processed/statistical_analysis.json` under key `compressibility_correlations`. **Note**: This is a secondary exploratory analysis to identify structural patterns, distinct from the primary FR-006 analysis. **Dependency**: Requires T024 completion.
- [X] T037a [US3] Implement `code/evaluation/sweep_thresholds.py` to generate **multiple compressed rule sets** by sweeping **fidelity_tolerance** and **compression_ratio**. **Algorithm**: Iterate `fidelity_tolerance` from 0.80 to 0.95 (step 0.05) and `compression_ratio` from 0.1 to 0.9 (step 0.1). For each pair, prune the global rule set to meet the target ratio while maintaining the fidelity tolerance. **Deliverable**: Save rule sets to `data/processed/rules/sweeps/rules_T{tolerance}_R{ratio}.json` and a metadata file `data/processed/sweep_config.json` containing `threshold_range`, `step_size`, and `generated_files`. **Dependency**: Requires T026b output.
- [X] T037 [US3] Implement sensitivity analysis sweeping the **compression ratio** and **fidelity tolerance** to report how **Fidelity Rates** and **Latency** vary (FR-007, SC-003). **Logic**: Iterate threshold pairs across the range defined in T037a, compute **Fidelity Rate** (Accuracy of Compressed Agent) and **Retrieval Latency** for each using the **held-out test set** and rule sets from **T037a** and benchmark results from **T032**. **Deliverable**: Save `data/processed/sensitivity_sweep.csv` with columns: `compression_ratio`, `fidelity_tolerance`, `fidelity_rate`, `latency`, `rule_count`. This output explicitly captures the trade-off curve required by the research question. **Dependency**: Requires T037a and T032 completion.

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
- [X] T050 [P] [US3] Update `quickstart.md` to document the strict execution order: `synthetic_trace.py` → `extract.py` → `pipeline.py` → `rule_induction.py` → `calculate_deltas.py` → `benchmark.py` → `stats.py`, emphasizing that skipping steps causes immediate failure. **Dependency**: Must be done after all scripts exist.
- [X] T044 [P] [US3] Implement `scripts/validate_quickstart.py` to parse `quickstart.md`, execute each command in a fresh venv, assert exit code 0 for each, and generate `data/processed/validation_report.json` containing command status, output logs, and pass/fail status. **Dependency**: Must be done after `quickstart.md` exists.

---

## Phase 7: Data Integrity & Execution Safety (Revision Concerns)

**Goal**: Address execution-stage fabrication guards and data-flow dependencies identified in prior reviews.

**Dependency**: Must be integrated before final execution.

- [X] T046 [US2] Add explicit validation in `code/metrics/pipeline.py` to ensure `feature_matrix.csv` is generated ONLY after `data/training/` contains valid JSON files; fail the script if input data is missing or malformed.
- [X] T047 [US2] Add a dependency check in `code/models/rule_induction.py` to verify `data/processed/feature_matrix.csv` exists before attempting rule induction; raise an error if the feature matrix is absent.
- [X] T048 [US3] Ensure `code/evaluation/benchmark.py` explicitly loads the **global** rule set from `data/processed/rules/global_rules.json` (generated by T026b) before running the compressed agent; fail if the global model is missing.
- [X] T049 [P] [US3] Add a post-benchmark validation step in `code/evaluation/stats.py` to verify that the input data for correlation contains no NaNs; if invalid, raise an error and log the specific trace IDs causing the violation.
- [X] T051 [P] [US3] Add a post-benchmark validation step in `code/evaluation/calculate_deltas.py` to ensure `accuracy_deltas.csv` is generated correctly before T035 runs.
- [X] T055 [US2] Implement a checksum verification in `code/models/rule_induction.py` that validates the `feature_matrix.csv` against the **derived artifact checksum** recorded in the state file (from T021); if checksums mismatch, raise `DataIntegrityError` to prevent training on potentially corrupted or modified features. **Note**: This task validates the *derived* artifact hash, not the raw data hash.
- [X] T057 [US3] Implement a "No Synthetic Fallback" guard in `code/agents/compressed.py` that explicitly checks if the loaded rule set is empty or invalid; if so, raise a `RuntimeError` instead of falling back to a default or random behavior.
- [X] T059 [US3] Add a post-benchmark validation in `code/evaluation/benchmark.py` to ensure the number of traces processed matches the number of traces in the held-out set; raise an error if there is a mismatch.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: Strictly sequential data flow:
 - **Phase 3 (US1)**: Depends on Phase 2. Generates raw data and splits it.
 - **Phase 4 (US2)**: Depends on Phase 3. Consumes US1 data to perform rule induction on Training Set and generate global rules.
 - **Phase 5 (US3)**: Depends on Phase 4. Consumes US2 global rules for benchmarking and statistical analysis.
- **Phase 7 (Data Integrity)**: Must be integrated into the logic of Phases 3-5 before execution.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: **Cannot** start until US1 is complete (requires generated traces).
- **User Story 3 (P3)**: **Cannot** start until US2 is complete (requires global rule set).

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
- **Critical Correction**: Phase 4 now implements **Batched Leave-One-Out (LOO) Rule Induction** to calculate a valid **Batch-Level Compressibility Proxy**, satisfying FR-003 without requiring n=1 training. Phase 5 uses **Beta Regression** on **Edit Accuracy Difference** (Baseline - Compressed), satisfying FR-006.
- **Safety**: Phase 7 tasks (T046-T059) enforce strict fail-loud behavior to prevent fabrication and ensure data integrity. T020 explicitly excludes traces with undefined variance and logs them to `exclusion_log.json`. T012 no longer allows imputation.
- **Explicit Dependencies**: T020 depends on T012. T021 depends on T020. T023 and T024 depend on T021. T026b depends on T024. T031 depends on T026b. T035b -> T035 chain is strict. T037a -> T037 is strict.
- **Metric Correction**: T035 now targets **Edit Accuracy Difference** as the primary metric for Beta Regression, ensuring FR-006 compliance and Constitution Principle VII. T035c is a secondary exploratory analysis.
- **Threshold Correction**: T037a now explicitly sweeps **fidelity_tolerance** and **compression_ratio** as required by FR-007.
- **Per-Trace Score**: T024 explicitly calculates a **Batch-Level Compressibility Proxy** using batched LOO cross-validation, and T035c includes the Spearman correlation with this proxy.
- **Validation**: T044 is now a concrete implementation of `scripts/validate_quickstart.py`.