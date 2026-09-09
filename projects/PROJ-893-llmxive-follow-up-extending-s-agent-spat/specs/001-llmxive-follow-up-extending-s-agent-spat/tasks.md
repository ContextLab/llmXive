# Tasks: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

**Input**: Design documents from `/specs/001-symbolic-spatial-reasoning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Branch**: `001-symbolic-spatial-reasoning`

**Tests**: Unit and integration tests are included for critical logic paths (CSP solver, distributional validity, failure analysis) to ensure reproducibility and data hygiene.

**Organization**: Tasks are grouped by phase and user story to enable independent verification of the symbolic solver, benchmarking, and failure analysis against the S-Agent-300K dataset.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, configuration, and dependency management.

- [X] T001a [P] Create `code/` directory
- [X] T001b [P] Create `data/raw/` directory
- [X] T001c [P] Create `data/derived/` directory
- [X] T001d [P] Create `data/results/` directory
- [X] T001e [P] Create `specs/001-symbolic-spatial-reasoning/contracts/` directory
- [X] T001f [P] Create `tests/` directory
- [X] T002 [P] Initialize Python 3.11 environment and create `code/requirements.txt` with pinned versions (`python-constraint`, `pandas`, `scipy`, `pytest`, `huggingface_hub`, `scikit-learn`)
- [X] T003 [P] Configure `code/config.py` for paths, random seeds, and sample size (n=1,000) constants

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data hygiene, and validation gates. **⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `code/hygiene.py` to compute SHA-256 hashes for `data/raw/*` and `data/derived/*` (excluding results until Phase 6) and update `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml`
- [X] T005a-Create [P] Create `specs/001-symbolic-spatial-reasoning/contracts/dataset.schema.yaml` (JSON Schema Draft 7) defining fields: `id`, `geometry`, `label`.
- [X] T005a-Verify [P] Verify `specs/001-symbolic-spatial-reasoning/contracts/dataset.schema.yaml` syntax by running `jsonschema validate` against a sample JSON object.
- [X] T005b-Create [P] Create `specs/001-symbolic-spatial-reasoning/contracts/constraints.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `constraints`, `status`.
- [X] T005b-Verify [P] Verify `specs/001-symbolic-spatial-reasoning/contracts/constraints.schema.yaml` syntax by running `jsonschema validate` against a sample JSON object.
- [X] T005c-Create [P] Create `specs/001-symbolic-spatial-reasoning/contracts/solver_output.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `prediction`, `latency_ms`, `status`.
- [X] T005c-Verify [P] Verify `specs/001-symbolic-spatial-reasoning/contracts/solver_output.schema.yaml` syntax by running `jsonschema validate` against a sample JSON object.
- [X] T005d-Create [P] Create `specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`, `p_value`.
- [X] T005d-Verify [P] Verify `specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` syntax by running `jsonschema validate` against a sample JSON object and ensure file exists at path.
- [X] T006 [P] Implement `code/data/download.py` to fetch S-AgentK subset using `huggingface_hub`. **FAIL LOUD Logic**: If the *dataset* (not individual scenes) is missing or corrupted, raise `FileNotFoundError` with message "Dataset S-AgentK not found at {url}". If individual scenes are missing, they are handled by T010 (exclusion). No synthetic fallbacks.
- [X] T006a [P] Implement `code/data/verify_checksum.py` to verify the downloaded dataset's checksum against the `data/` manifest (Constitution Principle III) before extraction
- [X] T006b [P] Implement `code/data/load_vlm_baseline.py` to fetch or load pre-computed VLM baseline predictions and latency data from the canonical source
- [X] T007 [P] Implement `code/data/validate_distribution.py` to perform KS-tests on object density and spatial variance (Distributional Validity Gate). **Output**: Generate `data/results/distribution_validity.json` containing `p_value` and `d_statistic` for each metric.
- [X] T008 [P] [US1] Unit test for constraint propagation logic in `tests/unit/test_csp_logic.py` (verify "No Solution" for ambiguous inputs)
- [X] T009 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_extract_geometry.py` (verify JSON schema compliance and malformed data exclusion)

---

## Phase 3: User Story 1 - Symbolic CSP Solver Execution (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic CSP solver that ingests 3D geometric constraints and produces spatial reasoning predictions without neural inference.

**Independent Test**: Run `code/solver/run_solver.py` on a sample of scenes; verify JSON output contains predictions for all IDs, zero GPU utilization, and a valid `latency_log.jsonl`.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data/extract_geometry.py` to parse the S-Agent dataset., **detect malformed/missing data**, **exclude** invalid scenes from processing, and output `data/derived/constraints.jsonl` (FR-001, FR-007). **Output**: Must also generate `data/results/exclusion_log.json` with counts and IDs of excluded scenes immediately upon detection.
- [X] T027 [P] [US1] Implement `code/validate/vlm_trace_auditor.py` to validate that no VLM traces (keys: 'tool_call_history', 'vlm_prediction') are present in `data/derived/constraints.jsonl`. **Dependency**: Must run AFTER T010 (extraction) and BEFORE T012 (solver). Output `data/results/vlm_trace_audit.json` confirming zero traces found (Addressing Constitution Principle VII). **Gate**: If traces are found, halt pipeline immediately with a clear error message; do not proceed to solver execution.
- [X] T011 [US1] Implement `code/solver/csp_engine.py` using `python-constraint` or `ortools` to solve counting/positioning tasks (FR-002)
- [X] T012a [US1] Implement timeout logic in `code/solver/run_solver.py`. **Requirements**:
 1. Implement a global batch timeout (defined duration). If reached, STOP processing remaining scenes to comply with wall-clock constraint.
 2. Implement a per-scene soft limit (bounded duration) using `signal.alarm` (Unix) or `threading.Timer` (cross-platform) that logs a warning but continues.
 3. Log remaining unprocessed scene IDs in `solver_failures.json` with `error_type: "BatchTimeout"` if global timeout is hit.
 4. Distinguish `error_type: "Timeout"` vs `error_type: "ConstraintError"` vs `error_type: "GeometricAmbiguity"` in logs.
- [X] T012b [US1] Implement status tracking in `code/solver/run_solver.py`. **Requirements**: Enforce status tracking ('No Solution', 'Ambiguous', 'Success') for every processed scene.
- [X] T012c [US1] Implement output generation in `code/solver/run_solver.py`. **Requirements**:
 1. Output `data/derived/predictions.jsonl` with schema keys `scene_id`, `prediction`, `status`.
 2. Output `data/derived/latency_log.jsonl` with schema keys `scene_id`, `latency_ms`, `status`.
 3. Output `data/derived/solver_failures.json` containing solver-side errors (timeouts, constraint errors) with scene IDs.
- [X] T012d [US1] Implement `code/solver/timing_utils.py` to provide the `time.perf_counter` wrapping logic for T012. **Requirements**: Must measure wall-clock time per scene and aggregate to `latency_log.jsonl`. **Verification**: Unit test in `tests/unit/test_timing_utils.py` verifying millisecond precision. (FR-004)
- [X] T013 [US1] Implement logging aggregation in `code/validate/merge_exclusions.py` to merge `data/results/exclusion_log.json` (from T010) and `data/derived/solver_failures.json` (from T012) into a final `data/results/exclusion_log.json`. **Dependency**: Must wait for T010 and T012. **Logic**: Parse `error_type` from T012 output to categorize exclusions as "MissingData", "ConstraintError", "GeometricAmbiguity", or "BatchTimeout". (FR-007)
- [X] T029 [US1] Implement a "dry-run" validation step in `code/validate/dry_run.py` that checks file existence and schema compliance of `constraints.jsonl` against `constraints.schema.yaml` before launching the solver batch, preventing wasted compute on malformed inputs (Addressing Edge Case: "corrupted input data"). **Dependency**: Must run after T010 (Extraction) and T027 (VLM Audit). **Verification**: Run `python code/validate/dry_run.py` against sample data.

**Checkpoint**: Symbolic solver produces valid predictions and latency logs for n=1,000 scenes on CPU within 6 hours.

---

## Phase 4: User Story 2 - Comparative Accuracy & Latency Benchmarking (Priority: P2)

**Goal**: Compare symbolic solver accuracy and latency against the VLM baseline and ground truth.

**Independent Test**: Run `code/benchmark/metrics.py` against `predictions.jsonl`, `latency_log.jsonl`, `ground_truth.csv`, and `vlm_baseline.csv`; verify F1, Exact Match, and latency stats.

### Tests for User Story 2

- [X] T014 [P] [US2] Unit test for metric calculation (F1, Exact Match) in `tests/unit/test_metrics.py`
- [X] T015 [P] [US2] Unit test for McNemar's test implementation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement `code/benchmark/metrics.py` to calculate Exact Match, F1-score, and median latency from `latency_log.jsonl` (FR-003, FR-004)
- [X] T017 [US2] Implement statistical significance test (McNemar's) in `code/benchmark/metrics.py` (FR-005). **Output**: Must include the calculated p-value in the final `data/results/benchmark_results.csv` column `p_value`. **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/results/benchmark_results.csv'); assert 'p_value' in df.columns"` and verify the column contains float values. (SC-003)
- [X] T018 [US2] Implement `code/main.py` orchestrator to run the full pipeline: **download → verify_checksum → validate_distribution (HARD BLOCK) → extract → vlm_audit (HARD BLOCK) → solve → benchmark** (FR-003)
- [X] T019a [US2] Create `specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` (if not already done in T005d) and verify it exists. **Verification**: Run `ls specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` and `jsonschema validate` against a sample.
- [X] T019b [US2] Generate `data/results/benchmark_results.csv` linking scene IDs, predictions, ground truth, and metrics. **Requirements**: Columns must include `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`, `p_value`. Use `benchmark_result.schema.yaml` for join logic (SC-001, SC-002). **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/results/benchmark_results.csv'); assert len(df) == 1000; assert set(['p_value', 'exact_match', 'f1']).issubset(df.columns)"` and check file row count matches expected n.
- [X] T026 [US2] Implement `code/validate/acceptance_checker.py` to verify all acceptance scenarios in `spec.md` (US-1, US-2, US-3) are met by running the full pipeline end-to-end; output `data/results/acceptance_checklist.md` with pass/fail status for each scenario (Addressing Constitution Principle I). **Criteria**: Explicitly check US-1 (solver execution), US-2 (benchmark metrics), US-3 (failure analysis). **Success Verdict**: Must explicitly verify SC-005 (Exact Match >= 85% of VLM baseline) and report the final project success/failure verdict.
- [X] T030a [US2] Implement `code/benchmark/sensitivity.py` to sweep the accuracy threshold (SC-005) across a range of values. **Logic**: Read VLM baseline accuracy from `data/results/benchmark_results.csv`. Set a range of values with a defined step size. Output `data/results/sensitivity_analysis.csv` with columns `threshold, verdict` (Addressing Assumption: "Threshold Justification"). **Verification**: Run `python code/benchmark/sensitivity.py` and verify `data/results/sensitivity_analysis.csv` exists with the required columns.
- [X] T030b [US2] Generate `data/results/sensitivity_analysis.csv` with the threshold vs. verdict table from T030a (Addressing Assumption: "Threshold Justification").

**Checkpoint**: Benchmark report generated with accuracy and latency comparisons; statistical significance calculated; sensitivity analysis and verification artifacts produced.

---

## Phase 5: User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**Goal**: Analyze specific failure cases to distinguish between "Geometric Ambiguity" and "Semantic Gap".

**Independent Test**: Run `code/benchmark/analyze_failures.py` on a subset of mismatched predictions; verify classification report and proportion statistic.

### Tests for User Story 3

- [X] T020 [P] [US3] Unit test for failure categorization logic in `tests/unit/test_failure_analysis.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement `code/benchmark/analyze_failures.py` to classify failures as "Geometric Ambiguity" or "Semantic Gap" and **calculate the proportion of failures attributable to semantic disambiguation** (FR-006, SC-004). **Logic**: Formula = `count(semantic_gap) / count(total_failures)`. **Dependency**: Must wait for T019b to generate `data/results/benchmark_results.csv`. **Strict Dependency**: If T019b output is missing, the script MUST halt with an error; no fallback to raw data is permitted to ensure Single Source of Truth. **Output**: Generate `data/derived/failure_classification.json` with scene IDs, classifications, and metadata. **JSON Structure**: `{"scene_id": "...", "classification": "...", "reason": "..."}`. **Output Key**: The summary object MUST include the key `semantic_gap_proportion` with the calculated float value. **Verification**: Run `python code/benchmark/analyze_failures.py` and verify output JSON contains the `semantic_gap_proportion` key.
- [X] T022 [US3] Generate `data/results/failure_analysis_report.md` with summary counts, **proportion statistic**, and a table of representative example scene IDs with text explanations (US-3, SC-004). **Requirements**: Report must include a section for "Geometric Ambiguity" and "Semantic Gap" counts, the proportion statistic, and a table of representative failure cases with scene IDs and text explanations derived from scene metadata. **Dependency**: Must wait for T021.
- [X] T023 [US3] Update `code/main.py` to include failure analysis as a final step in the pipeline

**Checkpoint**: Failure analysis report identifies root causes of symbolic solver underperformance and quantifies the semantic gap proportion.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final checks.

- [X] T024 [P] [Polish] Update `docs/quickstart.md` with execution instructions for the full pipeline
- [X] T025 [Polish] Run `code/hygiene.py` to finalize artifact hashes (including `data/results/*`) and update state YAML
- [X] T028a [P] [Polish] Define log format and scene ID extraction logic for `ConstraintSatisfactionError` in `code/solver/run_solver.py` (Addressing Edge Case: "insufficient constraints"). **Output**: Specify JSON log format: `{"scene_id": "...", "error_type": "ConstraintSatisfactionError", "message": "..."}`.
- [X] T028b [P] [Polish] Implement exception handler in `code/solver/run_solver.py` to catch `ConstraintSatisfactionError` using the defined format from T028a, ensuring no silent crashes (Addressing Edge Case: "insufficient constraints").
- [X] T031 [Polish] Implement `code/validate/final_report_generator.py` to aggregate `benchmark_results.csv`, `sensitivity_analysis.csv`, `failure_analysis_report.md`, and `acceptance_checklist.md` into a single `data/results/final_research_report.md` (Addressing Constitution Principle IV: Single Source of Truth for final deliverables). **Dependency**: Must run after T022 and T030b. **Verification**: Run `python code/validate/final_report_generator.py` and verify the output contains the following section headers: "## Benchmark Results", "## Failure Analysis", "## Sensitivity Analysis", "## Acceptance Checklist", "## Conclusion".
- [X] T032 [Polish] Create `README.md` at repository root summarizing the feature branch, execution steps, and key findings location (Addressing Project Accessibility). **Requirements**: Must include a "Quickstart" section referencing `docs/quickstart.md` and a "Results" section pointing to `data/results/final_research_report.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T001a-T001f must complete before T002/T003.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS** all User Stories.
 - T005a-Create/T005a-Verify...T005d-Verify must complete before T029/T010.
 - T010 must complete before T027/T011/T012.
 - T027 must complete before T012 (to ensure clean input).
- **User Stories (Phase 3-5)**: Depend on Foundational. Can be executed in parallel if resources allow, but logically ordered P1 → P2 → P3.
- **Polish (Phase 6)**: Depends on all User Stories completion.

### User Story Dependencies

- **US1 (P1)**: Must complete first. Provides the `predictions.jsonl` and `latency_log.jsonl` required by US2 and US3.
 - T010 must complete before T011/T012.
 - T012 must complete before T013.
 - T027 must complete before T012 (Gate).
 - T029 must complete before T012.
- **US2 (P2)**: Depends on US1 outputs (predictions, latency) and Ground Truth and VLM Baseline (from T006b).
 - T019a/T019b must complete before T021/T022/T026/T027.
 - T030a/T030b must complete before final success verdict.
 - T026/T027 must complete before final success verdict.
- **US3 (P3)**: Depends on US1 (predictions) and US2 (mismatch identification). T021/T022 depend on T019b.
- **Polish (Phase 6)**: T031 depends on T022 and T030b. T032 depends on T031.

### Parallel Opportunities

- **Phase 2**: T004, T006, T006a, T006b, T007 can run in parallel. T005a-Create/T005a-Verify...T005d-Verify can run in parallel.
- **Phase 3**: T010 (extract) and T011 (solver logic) can be developed in parallel, but T012 (run) depends on both. T029 must complete before T010 (if moved) or after T010 (current).
- **Phase 4**: T016 (metrics) and T017 (stats) can be developed in parallel. T030a, T030b, T026, T027 can be developed in parallel. T027 depends on T010.
- **Phase 5**: T021 (analysis logic) can be developed independently of T022 (report generation), but both depend on T019b.
- **Phase 6**: T028a, T028b, T031, T032 can be developed in parallel once dependencies are met.

---

## Notes

- **Data Hygiene**: All data fetching (`T006`) must fail loudly if the real dataset is unavailable. **Checksum verification** (`T006a`) is mandatory before extraction.
- **Compute**: The CSP solver (`T011`, `T012`) must be CPU-only. No GPU usage is permitted for the symbolic path.
- **Validity**: The Distributional Validity Gate (`T007`) is a **hard block** in `main.py` (`T018`). If it fails, the pipeline aborts.
- **Traceability**: All metrics must trace back to `data/results/benchmark_results.csv`. Latency traces back to `data/derived/latency_log.jsonl`.
- **Failures**: Excluded scenes must be logged explicitly (`T010`, `T013`) to maintain transparency on the final sample size. Exclusion logic is implemented in `T010`.
- **VLM Baseline**: Pre-computed VLM baseline data is loaded via `T006b` to ensure fair comparison.
- **Edge Cases**: Tasks T028a/T028b explicitly address the "insufficient constraints" edge case defined in the spec to prevent silent failures.
- **Assumptions**: Task T030 addresses the "Threshold Justification" assumption by adding a sensitivity analysis to the pipeline.
- **Schemas**: Tasks T005a-T005d must generate the schema files before T010/T011 implementation begins.
- **Verification**: Tasks T026 and T027 must produce specific artifacts (`acceptance_checklist.md`, `vlm_trace_audit.json`) to prove compliance with Constitution Principles I and VII.
- **Sensitivity**: Task T030 must be completed before the final success verdict to ensure robustness.
- **Data Flow Correction**: Task T019b (benchmark results) is now explicitly marked as a dependency for T021 (failure analysis) to ensure the analysis script has the necessary ground-truth comparisons before attempting to classify errors.
- **Fallback Logic**: T021 explicitly forbids fallback to raw data; it must halt if T019b is missing.
- **VLM Integrity Gate**: Task T027 is now a hard gate in Phase 3, executed after extraction and before solver execution, to strictly enforce Constitution Principle VII.
- **Timeout Transparency**: Task T012 (split into T012a/b/c) now explicitly distinguishes between "Timeout" and "Geometric Ambiguity" in exclusion logs to satisfy FR-007.
- **Final Deliverable**: Task T031 ensures all research artifacts are aggregated into a single, reproducible report, satisfying the "Single Source of Truth" principle for the final output.
- **Documentation**: Task T032 ensures the project is accessible to new researchers by providing a clear entry point in `README.md`.