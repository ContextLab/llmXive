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

- [X] T001a [P] Create `projects/PROJ-859-llmxive-follow-up-extending-memslides-a/` root directory
- [X] T001b [P] Create `code/`, `data/`, `tests/`, `contracts/` subdirectories
- [X] T001c [P] Create `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/held_out/.gitkeep`, `data/training/.gitkeep`
- [X] T001d [P] Initialize Python 3.11 project with `requirements.txt` (scikit-learn, pandas, numpy, pyyaml, pytest, sentence-transformers, statsmodels, scipy)
- [X] T001e [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [P] Create `contracts/trace.schema.yaml`
- [X] T004b [P] Create `contracts/metrics.schema.yaml`
- [X] T004c [P] Create `contracts/benchmark_results.schema.yaml`
- [X] T004d [P] Create `contracts/compressibility_analysis.schema.yaml`. **Note**: Must validate `beta_coefficients`, `p_values`, `trade_off_curve_points`, `edit_accuracy_difference`, and `delta_accuracy`.
- [X] T005 [P] [Foundational] Implement `code/contracts/__init__.py` validation logic
- [X] T006 [P] [Foundational] Setup `code/config.py` with seeds, paths, and threshold configurations. **Explicit Constraint**: Define `FIDELITY_TOLERANCE = 0.90` here.
- [X] T007 [P] [Foundational] Create base data loaders and schema validators in `code/utils/`
- [X] T008 [P] [Foundational] Configure `pytest` with contract test plugins in `tests/contract/`
- [X] T009 [P] [Foundational] Setup environment configuration management. **Explicit Constraint**: DO NOT create `config.yaml`. All configuration MUST be defined in `code/config.py` only.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Trace Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a synthetic dataset of multi-turn revision sessions based on the MemSlides benchmark schema, recording tool-execution traces and resulting slide states.

**Independent Test**: Verify the generation of a substantial set of unique session files where each file contains a valid sequence of tool calls and a corresponding ground-truth slide state.

**Dependency**: Requires Phase 2 completion.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation (T012) to ensure they run against the generated data.**

- [X] T010 [US1] Contract test for generated trace schema in `tests/contract/test_trace_schema.py`
- [X] T011 [US1] Integration test for dataset generation pipeline in `tests/integration/test_synthetic_generation.py`

### Implementation for User Story 1

- [X] T056 [P] [US1] Add a pre-generation check in `code/generators/synthetic_trace.py` to verify the MemSlides schema file exists and is valid YAML; raise `FileNotFoundError` if missing. **Dependency**: Must run before T012.
- [X] T012 [US1] Implement `code/generators/synthetic_trace.py` to generate a substantial volume of multi-turn sessions mimicking MemSlides schema (FR-001). **Deliverables**:
 1. Output files named `session_{uuid}.json` containing `exact_tool_sequence` and `raw_arg_variance`; use a **fixed random seed** for reproducibility; ensure schema matches `contracts/trace.schema.yaml`.
 2. **Variation**: Ensure sequence length, tool types, and argument variance vary across sessions.
 3. **Edge Cases**: Handle zero tool repetitions (high entropy) by recording as data point. **Handle undefined argument variance by IMPUTING a default value.**. Explicitly check if `arg_semantic_variance` is `None` OR `arg_semantic_variance == []` OR `(isinstance(arg_semantic_variance, float) and math.isnan(arg_semantic_variance))`. Only **EXCLUDE** the trace if the generator fails to produce valid data entirely. Do NOT fallback to synthetic/mock data.
 4. **Unified Output**: Generate a **single unified dataset** in `data/raw/` without splitting into Training/Held-Out sets. The split strategy is deferred to the research phase (T012b).
 5. **Fail-Loud**: If the MemSlides schema cannot be loaded or the seed fails to produce valid variation, raise `DataGenerationError` immediately.
 6. **Logging**: Log generation statistics and checksums to a state file.
- [X] T012b [US1] Implement `code/generators/split_dataset.py` to split the unified raw dataset into **Training** and **Held-Out** sets. **Logic**:
 1. Load the unified dataset from `data/raw/`.
 2. Apply a stratified split (e.g., train/test) based on `sequence_entropy` or `tool_repetition_freq` buckets to ensure distributional similarity.
 3. **Research Phase**: The exact split ratio and stratification method must be determined during the research phase (Phase 0) and documented in `research.md` before execution. For now, implement a configurable split ratio in `code/config.py`.
 4. **Deliverables**: Save training data to `data/training/` and held-out data to `data/held_out/`.
 5. **Dependency**: Requires T012 completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Structural Metric Extraction & Rule Induction (Priority: P2)

**Goal**: Compute structural metrics for every trace and perform **Aggregate Rule Induction** to produce a global symbolic rule set.

**Independent Test**: Run the extraction and induction pipeline on the training set and verify the output includes a computed feature matrix and a global rule set with non-zero fidelity.

**Dependency**: Requires completion of Phase 3 (US1) data generation.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [US2] Contract test for metrics schema in `tests/contract/test_metrics_schema.py`
- [X] T019 [US2] Unit test for entropy and variance calculations in `tests/unit/test_metrics_extract.py`
- [X] T042a [US2] Unit tests for `code/metrics/extract.py` functions (`compute_entropy`, `compute_repetition`, `compute_variance`) in `tests/unit/test_metrics_extract.py`.

### Implementation for User Story 2

- [X] T020a [P] [US2] Implement `code/metrics/extract.py` with **pure functions** `compute_entropy()`, `compute_repetition()`, and `compute_variance()` that accept a trace object and return metric values. **Constraint**: These functions must NOT handle missing data or logging; they assume valid input or raise `ValueError`. **Dependency**: Requires T006 completion.
- [X] T020b [US2] Implement `code/metrics/pipeline.py` to orchestrate feature matrix generation. **Logic**: Iterate over `data/training/` and `data/held_out/`, call functions from T020a. **Imputation**: If `compute_variance` fails or returns undefined (None/NaN), **impute 0.0** and log a warning to `data/processed/imputation_log.json` (containing `trace_id`, `imputed_reason`, `timestamp`). **DO NOT exclude traces**. **Deliverable**: Generate `data/processed/feature_matrix.csv` containing structural metrics for every trace. **Column Definitions**: `trace_id` (str), `sequence_entropy` (float), `tool_repetition_freq` (float), `arg_semantic_variance` (float). **Checksum**: Record the SHA256 hash of the generated `feature_matrix.csv` as a **derived artifact hash** in the state file. **Verification**: Immediately after generation, verify that every row in `feature_matrix.csv` can be mathematically reconstructed from the corresponding raw trace in `data/raw/` or `data/training/` (Constitution Principle VI). Raise `DataIntegrityError` if verification fails. **Dependency**: Requires T020a completion.
- [X] T023 [US2] Implement `code/models/rule_induction.py` to perform **aggregate rule induction** (FR-003). **Logic**:
 1. Load `feature_matrix.csv` (from T020b) and restrict to the **Training Set**.
 2. **Target Serialization**: Serialize the `final_state` into a categorical label or vector representation suitable for classification (e.g., hash of the state or a discrete action label).
 3. Train a lightweight CPU model (Decision Tree with `max_depth=5`, `min_samples_leaf=10`) using aggregate structural metrics to predict the serialized `final_state`.
 4. **Rule Extraction**: **Explicitly map tree paths to executable IF-THEN rules**. For each leaf node, generate a rule string: `IF (metric1 > val1) AND (metric2 < val2) THEN action = leaf_label`. **Export** these rules to a JSON file with an `action` field and `conditions` list.
 5. **Validation**: **Execute** the generated rules against the `final_state` of the training traces to verify they reproduce the state. If fidelity < 90%, log a warning but proceed.
 6. **Deliverable**: Save `data/processed/rules/global_rules_baseline.json` (the executable rule set) and a summary `data/processed/aggregate_model_summary.json`. **Dependency**: Requires T020b completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fidelity & Latency Benchmarking (Priority: P3)

**Goal**: Replace the raw memory module with the generated symbolic rule bank and compare Edit Accuracy and Retrieval Latency against the original baseline on a held-out test set.

**Independent Test**: Execute the benchmark script on a held-out set of requests and verify the output includes a comparative report of Edit Accuracy and Retrieval Latency for both agents.

**Dependency**: Requires completion of Phase 4 (US2) model training.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [US3] Contract test for benchmark results schema in `tests/contract/test_benchmark_results_schema.py`
- [X] T029 [US3] Integration test for agent comparison pipeline in `tests/integration/test_agent_benchmark.py`
- [X] T042b [US3] Unit tests for `code/evaluation/benchmark.py` in `tests/unit/test_benchmark.py`.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/agents/baseline.py` (raw memory agent)
- [X] T031 [US3] Implement `code/agents/compressed.py` (symbolic rule agent using **global rule set** from `data/processed/rules/global_rules_baseline.json` generated by T023). **Dependency**: **Must wait for T023 completion**. This task is NOT [P] because it depends on the global rule artifact.
- [X] T032a [US3] Implement `code/evaluation/benchmark.py` to run **both agents** on the **held-out test set** (from T012b). **Logic**: Execute baseline and compressed agents on each trace in the held-out set. **Deliverable**: Generate raw execution logs in `data/processed/benchmark_raw_logs.json` containing execution details for every trace. **Dependency**: Explicitly requires the **Held-Out Set** artifact generated by T012b.
- [X] T032b [US3] Implement `code/evaluation/benchmark.py` to aggregate metrics. **Logic**: Parse `data/processed/benchmark_raw_logs.json` to calculate **Edit Accuracy** (fraction of edits matching ground truth) and **Retrieval Latency** (time to context-ready) for both agents. **Deliverable**: Output a single JSON report to `data/processed/benchmark_results.json` containing both metrics for every trace. **Dependency**: Requires T032a completion.
- [X] T035b [US3] Implement `code/evaluation/calculate_deltas.py` to compute **Edit Accuracy Difference** (Baseline Accuracy - Compressed Accuracy) and **Fidelity Loss** (1.0 - Compressed Accuracy) for each trace in the held-out set. **Input**: Requires `data/processed/benchmark_results.json` (T032b). **Deliverable**: Save `data/processed/accuracy_deltas.csv` with columns `trace_id`, `baseline_acc`, `compressed_acc`, `delta_acc`, `fidelity_loss`. **Validation**: Assert that all `fidelity_loss` values are in [0.0, 1.0]. **raise** `ValueError` if invalid. **Dependency**: Requires T032b completion.
- [X] T035 [US3] Implement `code/evaluation/stats.py` for **statistical analysis** (FR-006). **Input**: Requires `data/processed/accuracy_deltas.csv` (T035b) and `data/processed/feature_matrix.csv` (T020b). **Logic**:
 1. **Primary**: Perform **Beta regression** of **Edit Accuracy Difference** (`delta_acc`) on Structural Metrics. **Justification**: Per Constitution Principle VII and Plan Phase 1, the *Edit Accuracy Difference* is the required metric to isolate the trade-off. **Formula**: Explicitly define `delta_acc` as the dependent variable: `'delta_acc ~ sequence_entropy + tool_repetition_freq + arg_semantic_variance'`.
 2. **Transformation**: Apply **logit transformation** to `delta_acc` (mapping [-1, 1] to (0, 1) after shifting) to avoid boundary issues for Beta Regression. Handle edge cases by adding a small epsilon. as per standard Beta regression practices.
 3. **Significance**: Flag p-values < 0.05 as significant, applying **Bonferroni correction** if multiple metrics are tested.
 4. **Fallback**: If Beta Regression fails to converge (e.g., perfect separation), fall back to **Spearman Correlation** between structural metrics and the continuous `delta_acc`. **Output Schema**: If Beta Regression used: `beta_coefficients`, `p_values`, `model_summary`, `method_used: 'beta_regression'`. If Spearman used: `spearman_coefficients`, `p_values`, `method_used: 'spearman_correlation'`. **DO NOT** use Logistic Regression on a binarized target.
 5. **Secondary Analysis**: Calculate Spearman correlation between structural metrics and `fidelity_loss` as a secondary robustness check.
 6. **Deliverable**: Save `data/processed/statistical_analysis.json`. **Validation**: Ensure all p_values < 0.05 are flagged as significant. **Dependency**: Requires T035b completion.
- [X] T037 [US3] Implement sensitivity analysis sweeping the **compression threshold** to report how **Fidelity Rates** and **Latency** vary (FR-007, SC-003). **Logic**:
 1. Iterate `fidelity_tolerance` across a high-fidelity range, starting from a moderate threshold and incrementing toward a strict upper bound..
 2. For each `fidelity_tolerance`:
 a. Generate a unique rule set by pruning the global rule set (from T023) to meet the target `fidelity_tolerance` using a **greedy removal algorithm based on rule frequency** (remove least frequent rules first until fidelity drops below threshold).
 b. Save this specific rule set to `data/processed/rules/sweeps/rules_T{tolerance}.json`.
 c. Run the **compressed agent** (T031) on the **held-out test set** using this specific rule set.
 d. Calculate **Fidelity Rate** and **Retrieval Latency**.
 3. **Deliverable**: Save `data/processed/sensitivity_sweep.csv` with columns: `fidelity_tolerance`, `fidelity_rate`, `latency`, `rule_count`. This output explicitly captures the trade-off curve required by the research question. **Dependency**: Requires T023 and T031 completion.
- [X] T062 [US3] Implement `code/evaluation/benchmark.py` latency variance analysis. **Logic**: In addition to mean latency, calculate and report **Standard Deviation** and **95th Percentile** latency for both baseline and compressed agents to assess stability. **Deliverable**: Append `latency_std_dev` and `latency_p95` columns to `data/processed/benchmark_results.json`. **Dependency**: Requires T032b completion.
- [X] T064 [US2] Refactor `code/metrics/extract.py` to handle `sentence-transformers` CPU memory spikes. **Logic**: Process traces in small batches (e.g., a limited number of traces) and clear the CPU cache between batches if available, ensuring the script does not OOM on the free-tier runner. **Dependency**: Requires T020a completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Documentation updates in `docs/` (update `research.md`, `data-model.md`, `quickstart.md`)
- [X] T040a [P] Refactor `code/agents/baseline.py` to remove unused imports and add type hints
- [X] T040b [P] Refactor `code/agents/compressed.py` to remove unused imports and add type hints
- [X] T041 Run full pipeline reproducibility check with pinned seeds
- [X] T042c [US3] Unit tests for `code/evaluation/stats.py` in `tests/unit/test_stats.py`.
- [X] T043 Security hardening (input validation, path sanitization)
- [X] T050 [P] [US3] Update `quickstart.md` to document the strict execution order: `synthetic_trace.py` → `extract.py` → `pipeline.py` → `rule_induction.py` → `calculate_deltas.py` → `benchmark.py` → `stats.py`, emphasizing that skipping steps causes immediate failure. **Dependency**: Must be done after all scripts exist.
- [X] T044 [P] [US3] Implement `scripts/validate_quickstart.py` to parse `quickstart.md`, execute each command in a fresh venv, assert exit code 0 for each, and generate `data/processed/validation_report.json` containing command status, output logs, and pass/fail status. **Dependency**: Must be done after `quickstart.md` exists.

---

## Phase 7: Data Integrity & Execution Safety (Revision Concerns)

**Goal**: Address execution-stage fabrication guards and data-flow dependencies identified in prior reviews.

**Dependency**: Must be integrated before final execution.

- [X] T046 [US2] Add explicit validation in `code/metrics/pipeline.py` to ensure `feature_matrix.csv` is generated ONLY after `data/training/` contains valid JSON files; fail the script if input data is missing or malformed.
- [X] T047 [US2] Add a dependency check in `code/models/rule_induction.py` to verify `data/processed/feature_matrix.csv` exists before attempting rule induction; raise an error if the feature matrix is absent.
- [X] T048 [US3] Ensure `code/evaluation/benchmark.py` explicitly loads the **global** rule set from `data/processed/rules/global_rules_baseline.json` (generated by T023) before running the compressed agent; fail if the global model is missing.
- [X] T049 [P] [US3] Add a post-benchmark validation step in `code/evaluation/stats.py` to verify that the input data for correlation contains no NaNs; if invalid, raise an error and log the specific trace IDs causing the violation.
- [X] T051 [P] [US3] Add a post-benchmark validation step in `code/evaluation/calculate_deltas.py` to ensure `accuracy_deltas.csv` is generated correctly before T035 runs.
- [X] T055 [US2] Implement a checksum verification in `code/models/rule_induction.py` that validates the `feature_matrix.csv` against the **derived artifact checksum** recorded in the state file (from T020b); if checksums mismatch, raise `DataIntegrityError` to prevent training on potentially corrupted or modified features. **Note**: This task validates the *derived* artifact hash, not the raw data hash.
- [X] T057 [US3] Implement a "No Synthetic Fallback" guard in `code/agents/compressed.py` that explicitly checks if the loaded rule set is empty or invalid; if so, raise a `RuntimeError` instead of falling back to a default or random behavior.
- [X] T059 [US3] Add a post-benchmark validation in `code/evaluation/benchmark.py` to ensure the number of traces processed matches the number of traces in the held-out set; raise an error if there is a mismatch.

---

## Phase 8: Advanced Data Integrity & Reporting (New Revision Concerns)

**Goal**: Address specific gaps in data lineage, exclusion reporting, and statistical robustness identified in the latest analysis.

**Dependency**: Must be completed before final execution and reporting.

- [X] T060 [US2] Implement `code/utils/exclusion_reporter.py` to aggregate `data/processed/imputation_log.json` into a human-readable summary report `data/processed/imputation_summary.md`. **Logic**: Count imputations by `imputed_reason` and calculate the percentage of the total dataset imputed. **Deliverable**: The summary must explicitly state the final valid dataset size and the reasons for data imputation, ensuring transparency for the research paper. **Dependency**: Requires T020b completion.
- [X] T063 [P] [US3] Add a "Data Lineage" generator in `code/utils/lineage.py` that traces every artifact in `data/processed/` back to its raw source files in `data/raw/` or `data/training/`. **Logic**: Read the state file and imputation logs to build a directed acyclic graph (DAG) of data transformations. **Deliverable**: Save `data/processed/data_lineage.json` and a visualizable `data/processed/data_lineage.dot` file for documentation. **Implementation Detail**: Use `graphviz` (>=0.20) library. The DOT file must use `node [shape=box, label=trace_id]` and `edge [style=solid]` syntax. **Dependency**: Requires T020b, T023, T032b, T035 completion.

---

## Phase 9: Final Execution Guardrails & Reporting (New Revision Concerns)

**Goal**: Ensure the final execution pipeline strictly adheres to the "Real Data Only" and "No Synthetic Fallback" rules, and that the final report explicitly documents the data provenance and any imputation events.

**Dependency**: Must be completed before the final run.

- [X] T065 [US3] Implement `code/evaluation/final_report_generator.py` to compile `statistical_analysis.json`, `sensitivity_sweep.csv`, `imputation_summary.md`, and `data_lineage.json` into a single `data/processed/final_report.md`. **Logic**: The report must include a "Data Provenance" section listing the exact seed, the count of imputed traces (from T060), and the SHA256 hashes of all input artifacts. **Merging Logic**: Concatenate the sections with headers: `# Final Report`, `## Statistical Analysis`, `## Sensitivity Analysis`, `## Data Imputation Summary`, `## Data Lineage`. **Verification**: After generation, verify the file exists and is non-empty using `os.path.getsize()`. **Dependency**: Requires T035, T037, T060, T063 completion.
- [X] T066 [US3] Add a "Fail-Loud" pre-flight check in `code/main.py` that verifies the existence of `data/training/` and `data/held_out/` and asserts that `data/processed/feature_matrix.csv` is present and non-empty before executing the full pipeline. **Logic**: If any required artifact is missing, the script must exit with a clear error message listing the missing files, preventing any partial or synthetic execution. **Dependency**: Requires T012, T012b, T020b completion.
- [X] T067 [US2] Refactor `code/metrics/extract.py` to ensure that `sentence-transformers` is loaded ONLY when processing semantic variance, and unloaded immediately after to prevent memory leaks during the per-trace loop. **Logic**: Wrap the model loading in a context manager that explicitly calls `del model` and `gc.collect()`. **Conditional GPU Cleanup**: Only call `torch.cuda.empty_cache()` if `torch.cuda.is_available()` is true; otherwise, rely on standard garbage collection. **Dependency**: Requires T020a completion.