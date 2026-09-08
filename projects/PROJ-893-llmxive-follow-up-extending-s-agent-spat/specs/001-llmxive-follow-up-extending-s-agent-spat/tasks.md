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
- [X] T005a [P] Create `specs/001-symbolic-spatial-reasoning/contracts/dataset.schema.yaml` (JSON Schema Draft 7) defining fields: `id`, `geometry`, `label`. **Verification**: Run `jsonschema validate` against a sample JSON object.
- [X] T005b [P] Create `specs/001-symbolic-spatial-reasoning/contracts/constraints.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `constraints`, `status`. **Verification**: Run `jsonschema validate` against a sample JSON object.
- [X] T005c [P] Create `specs/001-symbolic-spatial-reasoning/contracts/solver_output.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `prediction`, `latency_ms`, `status`. **Verification**: Run `jsonschema validate` against a sample JSON object.
- [X] T005d [P] Create `specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`. **Verification**: Run `jsonschema validate` against a sample JSON object.
- [X] T005e [P] Create `specs/001-symbolic-spatial-reasoning/contracts/latency_log.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `latency_ms`. **Verification**: Run `jsonschema validate` against a sample JSON object.
- [X] T006 [P] Implement `code/data/download.py` to fetch S-AgentK subset using `huggingface_hub` with **FAIL LOUD** logic (no synthetic fallbacks)
- [X] T006a [P] Implement `code/data/verify_checksum.py` to verify the downloaded dataset's checksum against the `data/` manifest (Constitution Principle III) before extraction
- [X] T006b [P] Implement `code/data/load_vlm_baseline.py` to fetch or load pre-computed VLM baseline predictions and latency data from the canonical source
- [X] T007 [P] Implement `code/data/validate_distribution.py` to perform KS-tests on object density and spatial variance (Distributional Validity Gate)
- [X] T008 [P] [US1] Unit test for constraint propagation logic in `tests/unit/test_csp_logic.py` (verify "No Solution" for ambiguous inputs)
- [X] T009 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_extract_geometry.py` (verify JSON schema compliance and malformed data exclusion)
- [ ] T029 [US1] Implement a "dry-run" validation step in `code/validate/dry_run.py` that checks file existence and schema compliance of `constraints.jsonl` against `constraints.schema.yaml` before launching the solver batch, preventing wasted compute on malformed inputs (Addressing Edge Case: "corrupted input data"). **Dependency**: Must run after T010 (Extraction). **Verification**: Run `python code/validate/dry_run.py` against sample data.

---

## Phase 3: User Story 1 - Symbolic CSP Solver Execution (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic CSP solver that ingests 3D geometric constraints and produces spatial reasoning predictions without neural inference.

**Independent Test**: Run `code/solver/run_solver.py` on a sample of scenes; verify JSON output contains predictions for all IDs, zero GPU utilization, and a valid `latency_log.jsonl`.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data/extract_geometry.py` to parse the S-Agent dataset., **detect malformed/missing data**, **exclude** invalid scenes from processing, and output `data/derived/constraints.jsonl` (FR-001, FR-007). **Output**: Must also generate `data/results/exclusion_log.json` with counts and IDs of excluded scenes immediately upon detection.
- [X] T011 [US1] Implement `code/solver/csp_engine.py` using `python-constraint` or `ortools` to solve counting/positioning tasks (FR-002)
- [X] T012 [US1] Implement `code/solver/run_solver.py` to batch process n=1,000 scenes. **Requirements**:
 1. Implement a global batch timeout (defined duration). If reached, STOP processing remaining scenes to comply with wall-clock constraint.
 2. Implement a per-scene soft limit (bounded duration) using `signal.alarm` (Unix) or `threading.Timer` (cross-platform) that logs a warning but continues.
 3. Enforce status tracking ('No Solution', 'Ambiguous', 'Success').
 4. Output `data/derived/predictions.jsonl` AND `data/derived/latency_log.jsonl` with schema keys `scene_id`, `prediction`, `latency_ms`, `status`.
 5. Output `data/derived/solver_failures.json` containing solver-side errors (timeouts, constraint errors) with scene IDs. (FR-002, FR-004)
- [X] T013 [US1] Implement logging aggregation in `code/validate/merge_exclusions.py` to merge `data/results/exclusion_log.json` (from T010) and `data/derived/solver_failures.json` (from T012) into a final `data/results/exclusion_log.json`. **Dependency**: Must wait for T010 and T012. (FR-007)

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
- [X] T017 [US2] Implement statistical significance test (McNemar's) in `code/benchmark/metrics.py` (FR-005)
- [X] T018 [US2] Implement `code/main.py` orchestrator to run the full pipeline: **download → verify_checksum → validate_distribution (HARD BLOCK) → extract → solve → benchmark** (FR-003)
- [X] T019a [US2] Create `specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` (if not already done in T005d) and verify it exists. **Verification**: Run `ls specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` and `jsonschema validate` against a sample.
- [X] T019b [US2] Generate `data/results/benchmark_results.csv` linking scene IDs, predictions, ground truth, and metrics. **Requirements**: Columns must include `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`. Use `benchmark_result.schema.yaml` for join logic (SC-001, SC-002). **Verification**: Run `python -m jsonschema validate data/results/benchmark_results.csv specs/001-symbolic-spatial-reasoning/contracts/benchmark_result.schema.yaml` (or equivalent CSV validator) and check file row count matches expected n.
- [X] T027 [P] [US2] Implement `code/validate/vlm_trace_auditor.py` to validate that no VLM traces (keys: 'tool_call_history', 'vlm_prediction') are present in `data/derived/constraints.jsonl`. **Dependency**: Must run AFTER T010 (extraction) on the derived constraints. Output `data/results/vlm_trace_audit.json` confirming zero traces found (Addressing Constitution Principle VII).
- [X] T026 [P] [US2] Implement `code/validate/acceptance_checker.py` to verify all acceptance scenarios in `spec.md` (US-1, US-2, US-3) are met by running the full pipeline end-to-end; output `data/results/acceptance_checklist.md` with pass/fail status for each scenario (Addressing Constitution Principle I). **Criteria**: Explicitly check US-1 (solver execution), US-2 (benchmark metrics), US-3 (failure analysis).
- [X] T030a [US2] Implement `code/benchmark/sensitivity.py` to sweep the accuracy threshold (SC-005) across a range of values. **Logic**: Read VLM baseline accuracy from `data/results/benchmark_results.csv` (if T019b completed) or `vlm_baseline.csv` (fallback). Set a range around the baseline with a specified step size. Output a table of "Success/Failure" verdicts vs. threshold (Addressing Assumption: "Threshold Justification"). **Verification**: Run `python code/benchmark/sensitivity.py` and verify output table.
- [X] T030b [US2] Generate `data/results/sensitivity_analysis.csv` with the threshold vs. verdict table from T030a (Addressing Assumption: "Threshold Justification").

**Checkpoint**: Benchmark report generated with accuracy and latency comparisons; statistical significance calculated; sensitivity analysis and verification artifacts produced.

---

## Phase 5: User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**Goal**: Analyze specific failure cases to distinguish between "Geometric Ambiguity" and "Semantic Gap".

**Independent Test**: Run `code/benchmark/analyze_failures.py` on a subset of mismatched predictions; verify classification report and proportion statistic.

### Tests for User Story 3

- [X] T020 [P] [US3] Unit test for failure categorization logic in `tests/unit/test_failure_analysis.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement `code/benchmark/analyze_failures.py` to classify failures as "Geometric Ambiguity" or "Semantic Gap" and **calculate the proportion of failures attributable to semantic disambiguation** (FR-006, SC-004). **Logic**: Formula = `count(semantic_gap) / count(total_failures)`. **Dependency**: Must wait for T019b to generate benchmark results. **Fallback**: If T019b output is missing, read directly from `predictions.jsonl` and `vlm_baseline.csv` to perform the analysis. **Output**: Generate `data/derived/failure_classification.json` with scene IDs, classifications, and metadata. **Verification**: Run `python code/benchmark/analyze_failures.py` and verify output JSON contains the calculated proportion.
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

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T001a-T001f must complete before T002/T003.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS** all User Stories.
 - T005a-T005e must complete before T029/T010.
 - T029 must complete before T010 (if in Phase 2) or T010 must complete before T029 (if in Phase 3). **Current**: T029 is in Phase 3, depends on T010.
 - T010 must complete before T027/T011/T012.
 - T027 must complete before T012 (to ensure clean input).
- **User Stories (Phase 3-5)**: Depend on Foundational. Can be executed in parallel if resources allow, but logically ordered P1 → P2 → P3.
- **Polish (Phase 6)**: Depends on all User Stories completion.

### User Story Dependencies

- **US1 (P1)**: Must complete first. Provides the `predictions.jsonl` and `latency_log.jsonl` required by US2 and US3.
 - T010 must complete before T011/T012.
 - T012 must complete before T013.
- **US2 (P2)**: Depends on US1 outputs (predictions, latency) and Ground Truth and VLM Baseline (from T006b).
 - T019a/T019b must complete before T021/T022/T026/T027.
 - T030a/T030b must complete before final success verdict.
 - T026/T027 must complete before final success verdict.
- **US3 (P3)**: Depends on US1 (predictions) and US2 (mismatch identification). T021/T022 depend on T019b.

### Parallel Opportunities

- **Phase 2**: T004, T006, T006a, T006b, T007 can run in parallel. T005a-T005e can run in parallel. T005b (Validation) depends on T010.
- **Phase 3**: T010 (extract) and T011 (solver logic) can be developed in parallel, but T012 (run) depends on both. T029 must complete before T010 (if moved) or after T010 (current).
- **Phase 4**: T016 (metrics) and T017 (stats) can be developed in parallel. T030a, T030b, T026, T027 can be developed in parallel. T027 depends on T010.
- **Phase 5**: T021 (analysis logic) can be developed independently of T022 (report generation), but both depend on T019b.
- **Phase 6**: T028a, T028b can be developed in parallel.

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
- **Schemas**: Tasks T005a-T005e must generate the schema files before T010/T011 implementation begins.
- **Verification**: Tasks T026 and T027 must produce specific artifacts (`acceptance_checklist.md`, `vlm_trace_audit.json`) to prove compliance with Constitution Principles I and VII.
- **Sensitivity**: Task T030 must be completed before the final success verdict to ensure robustness.
- **Data Flow Correction**: Task T019b (benchmark results) is now explicitly marked as a dependency for T021 (failure analysis) to ensure the analysis script has the necessary ground-truth comparisons before attempting to classify errors.
- **Fallback Logic**: T021 and T030a include explicit fallback logic to handle cases where T019b output is missing, ensuring the pipeline can proceed with raw data if necessary.