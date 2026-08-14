# Tasks: llmXive Follow-up: Trace Compressibility Analysis

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-memslides-a/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

---

## Phase 10: Statistical Robustness & Validation (New Revision Concerns)

**Goal**: Address reviewer concerns regarding the robustness of the Beta Regression model, handling of boundary conditions in the delta calculation, and the explicit validation of the "Held-Out" structural diversity strategy.

**Dependency**: Must be completed before final execution to ensure statistical validity.

- [ ] T068 [US3] Implement a "Structural Diversity Validator" in `code/analysis/validate_split.py` to explicitly verify that the **Held-Out Set** (T012b) exhibits significantly different structural properties compared to the **Training Set**. **Logic**:
 1. Load `feature_matrix.csv` and split it according to the `train/test` flags generated in T012b.
 2. Perform a Kolmogorov-Smirnov (KS) test on `sequence_entropy`, `tool_repetition_freq`, and `arg_semantic_variance` between the two sets.
 3. **Requirement**: The KS test p-value must be < 0.05 for at least one metric to confirm distributional shift. If p >= 0.05 for all metrics, raise a `StructuralShiftError` with a detailed report of the overlap.
 4. **Deliverable**: Save `data/processed/split_validation.json` containing the KS statistics, p-values, and a boolean `is_valid_shift`. **Dependency**: Requires T012b and T020b completion.

- [ ] T069 [US3] Enhance `code/evaluation/calculate_deltas.py` to handle **boundary conditions** in `delta_acc` calculation robustly. **Logic**:
 1. Ensure `delta_acc` is clamped to the range `[-1.0, 1.0]` to prevent logit transformation failures.
 2. Implement a "epsilon shift" strategy: if `delta_acc` is exactly -1.0, 0.0, or 1.0, apply a small shift (e.g., `delta_acc * (1 - 1e-4)`) to move it strictly inside the open interval `(-1, 1)` required for Beta Regression.
 3. Log any shifted values to `data/processed/delta_shifts.log` with the original and shifted values.
 4. **Deliverable**: Update `data/processed/accuracy_deltas.csv` with the corrected `delta_acc` values and append the shift log. **Dependency**: Requires T035b completion.

- [ ] T070 [US3] Implement a **Resampling-Based Confidence Interval** for the Beta Regression coefficients in `code/evaluation/stats.py`. **Logic**:
 1. After the primary Beta Regression (T035), perform 1000 bootstrap resamples of the `accuracy_deltas.csv` dataset.
 2. Re-run the regression on each resample to generate a distribution of coefficients.
 3. Calculate the 95% Confidence Interval (2.5th and 97.5th percentiles) for each coefficient.
 4. **Deliverable**: Append `confidence_intervals` (dict of `metric -> [lower, upper]`) to `data/processed/statistical_analysis.json`. **Dependency**: Requires T035 completion.

- [ ] T071 [US3] Add a **Model Assumption Check** in `code/evaluation/stats.py` to validate the fit of the Beta Regression model before reporting results. **Logic**:
 1. Plot (or compute statistics for) residuals vs. fitted values to check for heteroscedasticity.
 2. Perform a Shapiro-Wilk test on the residuals to check for normality (if applicable to the specific Beta regression implementation).
 3. **Action**: If assumptions are severely violated (e.g., p-value < 0.01 for normality), flag the result in the output JSON with `assumption_violation: true` and suggest the Spearman fallback (which is already implemented as a fallback).
 4. **Deliverable**: Add `model_assumptions` section to `data/processed/statistical_analysis.json` containing test statistics and pass/fail status. **Dependency**: Requires T035 completion.

- [ ] T072 [US3] Implement a **Sensitivity Analysis for the Epsilon Shift** in `code/evaluation/stats.py`. **Logic**:
 1. Re-run the Beta Regression with varying epsilon values (e.g., 1e-4, 1e-3, 1e-2) used in T069.
 2. Compare the resulting coefficients to ensure the conclusion (significance of metrics) is stable across epsilon choices.
 3. **Deliverable**: Append `epsilon_sensitivity` (list of results for each epsilon) to `data/processed/statistical_analysis.json`. **Dependency**: Requires T069 and T035 completion.

---

## Phase 11: Final Integration & Execution Readiness (New Revision Concerns)

**Goal**: Ensure the entire pipeline is integrated, tested end-to-end, and ready for the final execution gate with all new validation tasks included.

**Dependency**: Must be the final phase before execution.

- [ ] T073 [P] [US3] Update `code/main.py` to include the new validation steps (T068, T069, T070, T071, T072) in the execution order. **Logic**:
 1. Insert T068 (Diversity Check) immediately after T012b.
 2. Insert T069 (Delta Correction) immediately after T035b.
 3. Insert T070, T071, T072 (Statistical Robustness) immediately after T035.
 4. Ensure all new tasks are marked as **blocking** (pipeline halts on failure).
 5. **Deliverable**: Updated `code/main.py` with the new orchestration logic. **Dependency**: Requires T068, T069, T070, T071, T072 completion.

- [ ] T074 [P] [US3] Create a comprehensive **End-to-End Integration Test** in `tests/integration/test_full_pipeline.py`. **Logic**:
 1. Mock the data generation (T012) with a small, deterministic dataset.
 2. Run the full pipeline from T012b to T073.
 3. Assert that all output files (`feature_matrix.csv`, `global_rules_baseline.json`, `statistical_analysis.json`, `final_report.md`) exist and are valid.
 4. **Specific Assertion**: Verify that `statistical_analysis.json` contains the new fields (`confidence_intervals`, `model_assumptions`, `epsilon_sensitivity`).
 5. **Deliverable**: A passing integration test that validates the entire research pipeline. **Dependency**: Requires T073 completion.

- [ ] T075 [P] [US3] Update `docs/quickstart.md` to document the new validation steps and their purpose. **Logic**:
 1. Add a section "Validation Steps" explaining T068 (Diversity), T069 (Boundary Handling), and T070-T072 (Statistical Robustness).
 2. Update the execution order diagram to include these steps.
 3. **Deliverable**: Updated `quickstart.md` with clear instructions on the new validation phases. **Dependency**: Requires T073 completion.

- [ ] T076 [P] [US3] Run a **Dry-Run** of the full pipeline on the local machine to verify all new tasks execute without errors and produce the expected outputs. **Logic**:
 1. Execute `python code/main.py --dry-run`.
 2. Verify that all new artifacts are generated and logged.
 3. **Deliverable**: A log file `data/processed/dry_run_log.txt` confirming success. **Dependency**: Requires T073, T075 completion.

- [ ] T077 [P] [US3] Final **Code Review** and **Documentation Audit** to ensure all new tasks (T068-T076) are fully implemented, tested, and documented. **Logic**:
 1. Review code for T068-T076 for adherence to "No Synthetic Fallback" and "Fail-Loud" principles.
 2. Verify that all new output files are included in the `data/processed/` directory structure.
 3. **Deliverable**: A checklist in `docs/review_checklist.md` confirming all items are complete. **Dependency**: Requires T073, T074, T075, T076 completion.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
