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

## Phase 0: Research Design & Data Generation (Structural Diversity Strategy)

**Purpose**: Implement the core "Structural Diversity Strategy" mandated by the Plan (Phase 0) to ensure outcome variance. This phase generates Training and Held-Out sets with *distinct* distributions, not a split of a single set.

- [ ] T000 [P] [Phase0] **External Validation Proxy**. Attempt to validate synthetic distribution against a small, verified proxy dataset (if available). Document outcome in `data/processed/validation_proxy.json`. **Schema**: Must contain `ks_statistic`, `p_value`, `is_valid_shift` (boolean). **Logic**: Perform KS test on `sequence_entropy`, `tool_repetition_freq`, and `arg_semantic_variance` between proxy and synthetic. **Constraint**: If no proxy exists, document the limitation in the JSON with `reason: "no_proxy_available"`. **Dependency**: None.
- [ ] T001 [P] [Phase0] **Generate Synthetic Training Data**. Generate **5000** multi-turn revision sessions for the Training Set using `seed=42` and standard parameters (`tool_types`, `min_length=5`, `max_length=20`). Output: `data/training/*.json`. **Constraint**: Must log exact tool sequences and argument variances to `data/raw/logs/trace_integrity.log`. **Dependency**: Requires T006 completion.
- [ ] T002 [P] [Phase0] **Generate Synthetic Held-Out Data**. Generate **5000** distinct sessions for the Held-Out Test Set using `seed=43` and **perturbed distribution** (`variance_multiplier=1.5` for sequence length and tool repetition) to ensure structural diversity and variance in the outcome variable (fidelity loss). Output: `data/held_out/*.json`. **Constraint**: Must use a *different random seed* and *perturbed distribution* as per Plan Phase 0 T002. **Dependency**: Requires T006 completion.
- [ ] T003 [P] [Phase0] **Validate Trace Integrity**. Verify `data/raw/logs/trace_integrity.log` exists and contains valid structural metadata for all sessions. Fail pipeline if missing. **Dependency**: Requires T001, T002 completion.

---

## Phase 1: Setup, Foundational & Validation

**Purpose**: Project initialization, core infrastructure, and validation of the generated data splits.

- [X] T004a [P] Create `contracts/trace.schema.yaml`
- [X] T004b [P] Create `contracts/metrics.schema.yaml`
- [X] T004c [P] Create `contracts/benchmark_results.schema.yaml`
- [X] T004d [P] Create `contracts/compressibility_analysis.schema.yaml`. **Note**: Must validate `beta_coefficients`, `p_values`, `trade_off_curve_points`, `edit_accuracy_difference`, and `delta_accuracy`.
- [X] T005 [P] [Foundational] Implement `code/contracts/__init__.py` validation logic
- [X] T006 [P] [Foundational] Setup `code/config.py` with seeds, paths, and threshold configurations. **Explicit Constraint**: Define `FIDELITY_TOLERANCE = 0.90`, `TRAINING_SEED = 42`, `HOLDOUT_SEED = 43`, `HOLDOUT_VARIANCE_MULTIPLIER = 1.5`.
- [X] T007 [P] [Foundational] Create base data loaders and schema validators in `code/utils/`
- [X] T008 [P] [Foundational] Configure `pytest` with contract test plugins in `tests/contract/`
- [ ] T009 [P] [Foundational] Setup environment configuration management. **Explicit Constraint**: Implement `code/config.py` as the default source, but allow `config.yaml` in the project root to override seeds/paths for reproducibility on fresh runners (Constitution Principle I).
- [ ] T009b [P] [Foundational] Implement `code/utils/config_loader.py` to load `config.yaml` if present, otherwise use `code/config.py` defaults.
- [ ] T068 [US1/US3] **Structural Diversity Validator**. Implement `code/analysis/validate_split.py` to explicitly verify that the **Held-Out Set** (T002) exhibits significantly different structural properties compared to the **Training Set** (T001). **Logic**:
 1. Load `data/training/*.json` and `data/held_out/*.json`.
 2. Perform a Kolmogorov-Smirnov (KS) test on `sequence_entropy`, `tool_repetition_freq`, and `arg_semantic_variance` between the two sets.
 3. **Requirement**: The KS test p-value must be < 0.05 for at least one metric to confirm distributional shift. If p >= 0.05 for all metrics, raise a `StructuralShiftError` with a detailed report of the overlap.
 4. **Deliverable**: Save `data/processed/split_validation.json` containing the KS statistics, p-values, and a boolean `is_valid_shift`. **Dependency**: Requires T001, T002 completion. **Gate**: Pipeline halts if `is_valid_shift` is False.

**Checkpoint**: Foundation ready, data generated with distinct distributions, and split validated.

---

## Phase 2: User Story 1 - Synthetic Trace Generation (Priority: P1) 🎯 MVP

**Goal**: (Already implemented in Phase 0). This phase ensures the generated data is usable.

**Independent Test**: Verify the generation of a substantial set of unique session files where each file contains a valid sequence of tool calls and a corresponding ground-truth slide state.

**Dependency**: Requires Phase 0 completion.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [US1] Contract test for generated trace schema in `tests/contract/test_trace_schema.py`
- [X] T011 [US1] Integration test for dataset generation pipeline in `tests/integration/test_synthetic_generation.py`

### Implementation for User Story 1

- [X] T056 [P] [Foundational] Add a pre-generation check in `code/generators/synthetic_trace.py` to verify the MemSlides schema file exists and is valid YAML; raise `FileNotFoundError` if missing. **Dependency**: Must run before T001/T002.
- [ ] T012 [US1] **DEPRECATED**. This task has been removed to resolve circular dependencies. Data generation is now handled directly by T001 and T002 which produce the distinct Training and Held-Out sets. **Do not implement**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Structural Metric Extraction & Rule Induction (Priority: P2)

**Goal**: Compute structural metrics for every trace and perform **Aggregate Rule Induction** to produce a global symbolic rule set.

**Independent Test**: Run the extraction and induction pipeline on the training set and verify the output includes a computed feature matrix and a global rule set with non-zero fidelity.

**Dependency**: Requires completion of Phase 0 (Data Generation) and Phase 1 (Validation).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [US2] Contract test for metrics schema in `tests/contract/test_metrics_schema.py`
- [X] T019 [US2] Unit test for entropy and variance calculations in `tests/unit/test_metrics_extract.py`
- [X] T042a [US2] Unit tests for `code/metrics/extract.py` functions (`compute_entropy`, `compute_repetition`, `compute_variance`) in `tests/unit/test_metrics_extract.py`.

### Implementation for User Story 2

- [X] T020a [P] [US2] Implement `code/metrics/extract.py` with **pure functions** `compute_entropy()`, `compute_repetition()`, and `compute_variance()` that accept a trace object and return metric values. **Constraint**: These functions must NOT handle missing data or logging; they assume valid input or raise `ValueError`. **Dependency**: Requires T006 completion.
- [ ] T020b [US2] Implement `code/metrics/pipeline.py` to orchestrate feature matrix generation. **Logic**: Iterate over `data/training/` and `data/held_out/`, call functions from T020a. **Exclusion**: If `compute_variance`, `compute_entropy`, or `compute_repetition` fails or returns undefined (None/NaN), **EXCLUDE the trace** and log a warning to `data/processed/imputation_log.json` (containing `trace_id`, `excluded_reason`, `timestamp`). **DO NOT impute 0.0**. **Deliverable**: Generate `data/processed/metrics.csv` (primary deliverable per Plan T004) containing structural metrics for every trace. Also generate `data/processed/feature_matrix.csv` for internal use. **Column Definitions**: `trace_id` (str), `dataset_split` (str: 'training' or 'held_out'), `sequence_entropy` (float), `tool_repetition_freq` (float), `arg_semantic_variance` (float). **Checksum**: Record the SHA256 hash of the generated `metrics.csv` as a **derived artifact hash** in the state file. **Verification**: Immediately after generation, verify that every row in `metrics.csv` can be mathematically reconstructed from the corresponding raw trace in `data/training/` or `data/held_out/` (Constitution Principle VI) with a tolerance of a sufficiently small threshold. Raise `DataIntegrityError` if verification fails. **Dependency**: Requires T020a, T001, T002 completion.
- [X] T023 [US2] Implement `code/models/rule_induction.py` to perform **aggregate rule induction** (FR-003). **Logic**:
 1. Load `metrics.csv` (from T020b) and **filter strictly for rows where `dataset_split == 'training'`**.
 2. **Target Serialization**: Serialize the `final_state` into a categorical label or vector representation suitable for classification (e.g., hash of the state or a discrete action label).
 3. Train a lightweight CPU model (Decision Tree with `max_depth=5`, `min_samples_leaf=10`) using aggregate structural metrics to predict the serialized `final_state`.
 4. **Rule Extraction**: **Explicitly map tree paths to executable IF-THEN rules**. For each leaf node, generate a rule string: `IF (metric1 > val1) AND (metric2 < val2) THEN action = leaf_label`. **Export** these rules to a JSON file with an `action` field and `conditions` list.
 5. **Validation**: **Execute** the generated rules against the `final_state` of the training traces to verify they reproduce the state. If fidelity < 90%, log a warning but proceed.
 6. **Deliverable**: Save `data/processed/rules/global_rules_baseline.json` (the executable rule set, alias for `model.json` as per Plan T005) and a summary `data/processed/aggregate_model_summary.json`. **Dependency**: Requires T020b completion.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Fidelity & Latency Benchmarking (Priority: P3)

**Goal**: Replace the raw memory module with the generated symbolic rule bank and compare Edit Accuracy and Retrieval Latency against the original baseline on a held-out test set.

**Independent Test**: Execute the benchmark script on a held-out set of requests and verify the output includes a comparative report of Edit Accuracy and Retrieval Latency for both agents.

**Dependency**: Requires completion of Phase 3 (US2) model training.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [US3] Contract test for benchmark results schema in `tests/contract/test_benchmark_results_schema.py`
- [X] T029 [US3] Integration test for agent comparison pipeline in `tests/integration/test_agent_benchmark.py`
- [X] T042b [US3] Unit tests for `code/evaluation/benchmark.py` in `tests/unit/test_benchmark.py`.

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/agents/baseline.py` (raw memory agent)
- [X] T031 [US3] Implement `code/agents/compressed.py` (symbolic rule agent using **global rule set** from `data/processed/rules/global_rules_baseline.json` generated by T023). **Dependency**: **Must wait for T023 completion**. This task is NOT [P] because it depends on the global rule artifact.
- [ ] T032a [US3] Implement `code/evaluation/benchmark.py` to run **Baseline Agent** on the **held-out test set** (from T002). **Logic**: Execute baseline agent on each trace in the `data/held_out/` set. **Deliverable**: Generate raw execution logs in `data/processed/benchmark_raw_logs_baseline.json` containing execution details for every trace. **Dependency**: Explicitly requires the **Held-Out Set** artifact generated by T002.
- [ ] T032c [US3] Implement `code/evaluation/benchmark.py` to run **Compressed Agent** on the **held-out test set** (from T002). **Logic**: Execute compressed agent (using rules from T023) on each trace in the `data/held_out/` set. **Deliverable**: Generate raw execution logs in `data/processed/benchmark_raw_logs_compressed.json` containing execution details for every trace. **Dependency**: Requires T031, T002 completion.
- [ ] T032b [US3] Implement `code/evaluation/benchmark.py` to aggregate metrics. **Logic**: Parse `data/processed/benchmark_raw_logs_baseline.json` and `data/processed/benchmark_raw_logs_compressed.json` to calculate **Edit Accuracy** (fraction of edits matching ground truth) and **Retrieval Latency** (time to context-ready) for both agents. **Deliverable**: Output a single JSON report to `data/processed/benchmark_results.json` containing both metrics for every trace. **Dependency**: Requires T032a, T032c completion.
- [ ] T035b [US3] Implement `code/evaluation/calculate_deltas.py` to compute **Edit Accuracy Difference** (Baseline Accuracy - Compressed Accuracy) and **Fidelity Loss** (1.0 - Compressed Accuracy) for each trace in the held-out set. **Input**: Requires `data/processed/benchmark_results.json` (T032b). **Deliverable**: Save `data/processed/accuracy_deltas.csv` with columns `trace_id`, `baseline_acc`, `compressed_acc`, `delta_acc`, `fidelity_loss`. **Validation**: Assert that all `fidelity_loss` values are in [0.0, 1.0]. **raise** `ValueError` if invalid. **Dependency**: Requires T032b completion.
- [ ] T069 [US3] **Delta Boundary Correction**. Enhance `code/evaluation/calculate_deltas.py` to handle **boundary conditions** in `delta_acc` calculation robustly. **Logic**:
 1. Ensure `delta_acc` is clamped to the range `[-1.0, 1.0]` to prevent logit transformation failures.
 2. Implement a "epsilon shift" strategy: if `delta_acc` is exactly -1.0, 0.0, or 1.0, apply a small shift: `delta_acc = delta_acc * (1 - 1e-4)` to move it strictly inside the open interval `(-1, 1)` required for Beta Regression.
 3. Log any shifted values to `data/processed/delta_shifts.log` with the original and shifted values.
 4. **Deliverable**: Update `data/processed/accuracy_deltas.csv` with the corrected `delta_acc` values and append the shift log. **Dependency**: Requires T035b completion. **Must run before T035**.
- [ ] T035 [US3] Implement `code/evaluation/stats.py` for **statistical analysis** (FR-006). **Input**: Requires `data/processed/accuracy_deltas.csv` (T035b, corrected by T069) and `data/processed/metrics.csv` (T020b). **Logic**:
 1. **Primary**: Perform **Beta Regression** (per Spec FR-006 and Plan T016) of **Edit Accuracy Difference** (`delta_acc`) on Structural Metrics. **Justification**: Per Spec FR-006, Beta regression is required for bounded outcomes. **Transformation**: Apply **logit transformation** to `delta_acc` (mapping [-1, 1] to (0, 1) after shifting) using `epsilon=1e-4`. Handle edge cases by adding a small epsilon.
 2. **Fallback 1**: If Beta Regression assumptions (linearity, normality) are violated, attempt **Multiple Linear Regression** (per Plan T016). **Formula**: Explicitly define `delta_acc` as the dependent variable: `'delta_acc ~ sequence_entropy + tool_repetition_freq + arg_semantic_variance'`.
 3. **Fallback 2**: If Multiple Linear Regression fails to converge, fall back to **Spearman Correlation** between structural metrics and the continuous `delta_acc`.
 4. **Significance**: Flag p-values < 0.05 as significant, applying **Bonferroni correction** if multiple metrics are tested.
 5. **Secondary Analysis**: Calculate Spearman correlation between structural metrics and `fidelity_loss` as a secondary robustness check.
 6. **Deliverable**: Save `data/processed/statistical_analysis.json`. **Validation**: Ensure all p_values < 0.05 are flagged as significant. **Dependency**: Requires T069 completion.
- [ ] T037 [US3] Implement sensitivity analysis sweeping the **compression threshold** to report how **Fidelity Rates** and **Latency** vary (FR-007, SC-003, Plan T015). **Logic**:
 1. Iterate `fidelity_tolerance` from a low baseline to a near-unity threshold with a fine-grained step size.
 2. For each `fidelity_tolerance`:
 a. Generate a unique rule set by pruning the global rule set (from T023) to meet the target `fidelity_tolerance` using a **greedy removal algorithm based on rule frequency** (remove least frequent rules first until fidelity drops below threshold).
 b. Save this specific rule set to `data/processed/rules/sweeps/rules_T{tolerance}.json`.
 c. Run the **compressed agent** (T031) on the **held-out test set** using this specific rule set.
 d. Calculate **Fidelity Rate** and **Retrieval Latency**.
 3. **Deliverable**: Save `data/processed/sensitivity_sweep.csv` with columns: `fidelity_tolerance`, `fidelity_rate`, `latency`, `rule_count`. This output explicitly captures the trade-off curve required by the research question. **Dependency**: Requires T023 and T031 completion.
- [X] T062 [US3] Implement `code/evaluation/benchmark.py` latency variance analysis. **Logic**: In addition to mean latency, calculate and report **Standard Deviation** and **95th Percentile** latency for both baseline and compressed agents to assess stability. **Deliverable**: Append `latency_std_dev` and `latency_p95` columns to `data/processed/benchmark_results.json`. **Dependency**: Requires T032b completion.
- [X] T064 [P] [Foundational] Refactor `code/metrics/extract.py` to handle `sentence-transformers` CPU memory spikes. **Logic**: Process traces in small batches (e.g., a limited number of traces) and clear the CPU cache between batches if available, ensuring the script does not OOM on the free-tier runner. **Dependency**: Requires T020a completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Feasibility & Reporting

**Purpose**: Measure resource usage and compile the final report.

- [ ] T017 [US3] **Feasibility Gate**. Measure total runtime, peak memory, and disk usage. Generate `data/processed/feasibility_report.json`.
 - **Gate**: If runtime > 6h or memory > 7GB, pipeline halts with failure status.
 - **Traceability**: Record the SHA256 hash of `feasibility_report.json` in the `state/...yaml` artifact hashes map (Constitution Principle V).
 - **Dependency**: Requires completion of all pipeline tasks (T001-T037).
- [ ] T060 [P] [Foundational] Implement `code/utils/exclusion_reporter.py` to aggregate `data/processed/imputation_log.json` into a human-readable summary report `data/processed/imputation_summary.md`. **Logic**: Count exclusions by `excluded_reason` and calculate the percentage of the total dataset excluded. **Deliverable**: The summary must explicitly state the final valid dataset size and the reasons for data exclusion, ensuring transparency for the research paper. **Dependency**: Requires T020b completion.
- [ ] T063 [P] [Foundational] Add a "Data Lineage" generator in `code/utils/lineage.py` that traces every artifact in `data/processed/` back to its raw source files in `data/training/` or `data/held_out/`. **Logic**: Read the state file and exclusion logs to build a directed acyclic graph (DAG) of data transformations. **Deliverable**: Save `data/processed/data_lineage.json` and a visualizable `data/processed/data_lineage.dot` file for documentation. **Implementation Detail**: Use `graphviz` (>=0.20) library. The DOT file must use `node [shape=box, label=trace_id]` and `edge [style=solid]` syntax. **Dependency**: Requires T020b, T023, T032b, T035 completion.
- [ ] T065 [US3] Implement `code/evaluation/final_report_generator.py` to compile `statistical_analysis.json`, `sensitivity_sweep.csv`, `imputation_summary.md`, `data_lineage.json`, and `feasibility_report.json` into a single `data/processed/final_report.md` (Plan T018). **Logic**: The report must include a "Data Provenance" section listing the exact seed, the count of excluded traces (from T060), and the SHA256 hashes of all input artifacts. **Merging Logic**: Concatenate the sections with headers: `# Final Report`, `## Statistical Analysis`, `## Sensitivity Analysis`, `## Data Exclusion Summary`, `## Data Lineage`, `## Feasibility Report`. **Verification**: After generation, verify the file exists and is non-empty using `os.path.getsize()`. **Dependency**: Requires T035, T037, T060, T063, T017 completion.
- [ ] T066 [US3] Add a "Fail-Loud" pre-flight check in `code/main.py` that verifies the existence of `data/training/` and `data/held_out/` and asserts that `data/processed/metrics.csv` is present and non-empty before executing the full pipeline. **Logic**: If any required artifact is missing, the script must exit with a clear error message listing the missing files, preventing any partial or synthetic execution. **Dependency**: Requires T001, T002, T020b completion.

---

## Phase 6: Statistical Robustness & Validation

**Goal**: Address reviewer concerns regarding the robustness of the statistical models.

**Dependency**: Must be completed before final execution to ensure statistical validity.

- [ ] T070 [P] [Foundational] Implement a **Resampling-Based Confidence Interval** for the Regression coefficients in `code/evaluation/stats.py`. **Logic**:
 1. After the primary regression (T035), perform **1000** bootstrap resamples of the `accuracy_deltas.csv` dataset.
 2. Re-run the regression on each resample to generate a distribution of coefficients.
 3. Calculate the Confidence Interval for each coefficient.
 4. **Deliverable**: Append `confidence_intervals` (dict of `metric -> [lower, upper]`) to `data/processed/statistical_analysis.json`. **Dependency**: Requires T035 completion. **Seed**: Use `seed=42` for resampling.
- [ ] T071 [P] [Foundational] Add a **Model Assumption Check** in `code/evaluation/stats.py` to validate the fit of the Regression model before reporting results. **Logic**:
 1. Plot (or compute statistics for) residuals vs. fitted values to check for heteroscedasticity.
 2. Perform a Shapiro-Wilk test on the residuals to check for normality (if applicable to the specific Regression implementation).
 3. **Action**: If assumptions are severely violated (e.g., p-value < 0.01 for normality), flag the result in the output JSON with `assumption_violation: true` and suggest the Spearman fallback (which is already implemented as a fallback).
 4. **Deliverable**: Add `model_assumptions` section to `data/processed/statistical_analysis.json` containing test statistics and pass/fail status. **Dependency**: Requires T035 completion.
- [ ] T072 [P] [Foundational] Implement a **Sensitivity Analysis for the Epsilon Shift** in `code/evaluation/stats.py`. **Logic**:
 1. Re-run the Regression with varying epsilon values across a range of magnitudes (1e-2 to 1e-6, logarithmic step).
 2. Compare the resulting coefficients to ensure the conclusion (significance of metrics) is stable across epsilon choices.
 3. **Deliverable**: Append `epsilon_sensitivity` (list of results for each epsilon) to `data/processed/statistical_analysis.json`. **Dependency**: Requires T069 and T035 completion.

---

## Phase 7: Final Integration & Execution Readiness

**Goal**: Ensure the entire pipeline is integrated, tested end-to-end, and ready for the final execution gate with all new validation tasks included.

**Dependency**: Must be the final phase before execution.

- [ ] T073 [P] [Foundational] Update `code/main.py` to include the new validation steps (T068, T069, T070, T071, T072) in the execution order. **Logic**:
 1. Insert T068 (Diversity Check) immediately after T002.
 2. Insert T069 (Delta Correction) immediately after T035b.
 3. Insert T070, T071, T072 (Statistical Robustness) immediately after T035.
 4. Ensure all new tasks are marked as **blocking** (pipeline halts on failure).
 5. **Execution Order**: T001 -> T002 -> T068 -> T020b -> T023 -> T032a -> T032c -> T032b -> T035b -> T069 -> T035 -> T070 -> T071 -> T072 -> T037 -> T017 -> T065.
 6. **Deliverable**: Updated `code/main.py` with the new orchestration logic. **Dependency**: Requires T068, T069, T070, T071, T072 completion.

- [ ] T074 [P] [Foundational] Create a comprehensive **End-to-End Integration Test** in `tests/integration/test_full_pipeline.py`. **Logic**:
 1. Run the **actual data generation** (T001, T002) with a small, deterministic dataset (e.g., count=10, seed=42/43) to validate the full pipeline against real synthetic generation logic. **Do NOT mock data generation**.
 2. Run the full pipeline from T001 to T073.
 3. Assert that all output files (`metrics.csv`, `global_rules_baseline.json`, `statistical_analysis.json`, `final_report.md`) exist and are valid.
 4. **Specific Assertion**: Verify that `statistical_analysis.json` contains the new fields (`confidence_intervals`, `model_assumptions`, `epsilon_sensitivity`).
 5. **Deliverable**: A passing integration test that validates the entire research pipeline. **Dependency**: Requires T073 completion.

- [ ] T075 [P] [Foundational] Update `docs/quickstart.md` to document the new validation steps and their purpose. **Logic**:
 1. Add a section "Validation Steps" explaining T068 (Diversity), T069 (Boundary Handling), and T070-T072 (Statistical Robustness).
 2. Update the execution order diagram to include these steps.
 3. **Deliverable**: Updated `quickstart.md` with clear instructions on the new validation phases. **Dependency**: Requires T073 completion.

- [ ] T076 [P] [Foundational] Run a **Dry-Run** of the full pipeline on the local machine to verify all new tasks execute without errors and produce the expected outputs. **Logic**:
 1. Execute `python code/main.py --dry-run`.
 2. Verify that all new artifacts are generated and logged.
 3. **Deliverable**: A log file `data/processed/dry_run_log.txt` confirming success. **Dependency**: Requires T073, T075 completion.

- [ ] T077 [P] [Foundational] Final **Code Review** and **Documentation Audit** to ensure all new tasks (T068-T076) are fully implemented, tested, and documented. **Logic**:
 1. Review code for T068-T076 for adherence to "No Synthetic Fallback" and "Fail-Loud" principles.
 2. Verify that all new output files are included in the `data/processed/` directory structure.
 3. **Deliverable**: A checklist in `docs/review_checklist.md` confirming all items are complete. **Dependency**: Requires T073, T074, T075, T076 completion.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 0 (Data Generation)**: Depends on Foundational - **MUST run before Metric Extraction**.
- **User Stories (Phase 2+)**: All depend on Foundational and Phase 0 completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Implemented in Phase 0 (T001, T002).
- **User Story 2 (P2)**: Depends on Phase 0 (Data Generation).
- **User Story 3 (P3)**: Depends on Phase 0 (Data Generation) and Phase 2 (Metric Extraction/Rule Induction).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_trace_schema.py"
Task: "Integration test for [user journey] in tests/integration/test_synthetic_generation.py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 0: Data Generation (T001, T002)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Phase 0 (Data Generation) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: Phase 0 (Data Generation)
 - Developer B: User Story 2 (Metrics/Rule Induction)
 - Developer C: User Story 3 (Benchmarking/Stats)
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
- **Critical**: T001 and T002 must use distinct seeds and perturbed distributions to ensure outcome variance.
- **Critical**: T068 must run *before* T020b and T023 to validate the split logic.
- **Critical**: T069 must run *before* T035 to ensure valid input for regression.
- **Critical**: T012 is DEPRECATED and removed.