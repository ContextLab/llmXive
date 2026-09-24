# Tasks: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

**Input**: Design documents from `/specs/001-symbolic-spatial-reasoning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Branch**: `001-symbolic-spatial-reasoning`

**Tests**: Unit and integration tests are included for critical logic paths (CSP solver, distributional validity, failure analysis) to ensure reproducibility and data hygiene.

**Organization**: Tasks are grouped by phase and user story to enable independent verification of the symbolic solver, benchmarking, and failure analysis against the S-Agent dataset.

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
- [X] T002 [P] Initialize a Python environment and create `code/requirements.txt` with pinned versions (`python-constraint`, `pandas`, `scipy`, `pytest`, `huggingface_hub`, `scikit-learn`)
- [X] T003 [P] Configure `code/config.py` for paths, random seeds, and sample size (n=1,000) constants

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data hygiene, and validation gates. **⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `code/hygiene.py` to compute SHA-256 hashes for `data/raw/*` and `data/derived/*` (excluding results until Phase 6) and update `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml`
- [X] T005a [P] Create `dataset.schema.yaml` (JSON Schema Draft 7) defining fields: `id`, `geometry`, `label`. **Sample**: `{"id": "scene_001", "geometry": {"objects": [{"x": 1.0, "y": 2.0}]}, "label": 5}`.
- [X] T005b [P] Create `constraints.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `constraints`, `status`. **Sample**: `{"scene_id": "scene_001", "constraints": [{"type": "left_of", "a": "obj1", "b": "obj2"}], "status": "valid"}`.
- [X] T005c [P] Create `solver_output.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `prediction`, `latency_ms`, `status`. **Sample**: `{"scene_id": "scene_001", "prediction": 5, "latency_ms": 120.5, "status": "success"}`.
- [X] T005d [P] Create `benchmark_result.schema.yaml` (JSON Schema Draft 7) defining fields: `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`, `p_value`. **Sample**: `{"scene_id": "scene_001", "symbolic_pred": 5, "vlm_pred": 5, "ground_truth": 5, "exact_match": true, "f1": 1.0, "latency_ms": 120.5, "status": "success", "p_value": 0.05}`.
- [X] T005e [P] Implement `code/validate/validate_schemas.py` to verify that generated data files (`data/derived/constraints.jsonl`, `data/results/benchmark_results.csv`, etc.) conform to the schemas created in T005a-d before downstream tasks execute. **Gate**: Must pass before T010, T012, T019b-init. **Input Files**: Explicitly verify `data/derived/constraints.jsonl` against `constraints.schema.yaml`, `data/derived/solver_output.jsonl` against `solver_output.schema.yaml`, and `data/results/benchmark_results.csv` against `benchmark_result.schema.yaml`.
- [X] T005f [P] Implement `code/validate/validate_citations.py` to verify citations in `spec.md` and `plan.md` against the "Verified Datasets" block. **Requirement**: Must check title-token-overlap ≥ 0.7. Exit with error if any citation is unreachable or mismatched. (Constitution Principle II). **Note**: `research.md` is not yet available; verify only existing artifacts.
- [X] T005g [P] Update `code/main.py` to invoke `validate_citations` as the first step before any data processing. **Gate**: If validation fails, abort pipeline immediately.
- [ ] T006 [P] [US1] Implement `code/data/download.py` to fetch the **S-Agent dataset** using `huggingface_hub` and create `data/manifest.json`. **Logic**: Must perform a **stratified random sample** of exactly n=1,000 static multi-view scenes. **Algorithm**: Attempt `pandas.DataFrame.groupby(['object_density', 'scene_complexity']).sample(n=..., random_state=SEED)`. **Verification**: Before sampling, verify the existence of columns `object_density` and `scene_complexity`. **ABORT Logic**: If these columns are missing, raise `FileNotFoundError` with message "Stratification keys missing. Cannot guarantee FR-001 compliance." Do NOT fall back to simple random sampling or proxy datasets. **Artifact Generation**: Upon successful download, compute SHA-256 hashes for every downloaded file and write them to `data/manifest.json` as a list of objects: `[{"file": "<filename>", "sha256": "<hash>"}]`. This manifest is the required input for T006a. **Verification**: Run `python -c "import json; import os; m = json.load(open('data/manifest.json')); assert len(m) > 0 and all('sha256' in x for x in m)"` to ensure manifest exists and is valid.
- [ ] T006a [US1] Implement `code/data/verify_checksum.py` to verify the downloaded dataset's checksum against the `data/manifest.json` (Constitution Principle III) before extraction. **Dependency**: Must run AFTER T006 completion. **Gate**: If checksums mismatch or `data/manifest.json` is missing, abort with error. **Note**: T006a is not parallel ([P]) as it depends on T006.
- [X] T006b [US1] Implement `code/data/extract_geometry.py` to parse the S-Agent-300K dataset, **detect malformed/missing data**, **exclude** invalid scenes from processing, and output `data/derived/constraints.jsonl` (FR-001, FR-007). **Output**: Must also generate `data/results/exclusion_log.json` with counts and IDs of excluded scenes immediately upon detection. **Schema Requirement**: The JSON must explicitly contain top-level keys `total_scenes` (integer) and `excluded_count` (integer), plus a list of `excluded_ids`. **Dependency**: Must run AFTER T006a. **Verification**: Run `python -c "import json; e = json.load(open('data/results/exclusion_log.json')); assert 'total_scenes' in e and 'excluded_count' in e and 'excluded_ids' in e"` to ensure schema compliance.
- [X] T006c [P] [US2] Implement `code/data/load_vlm_baseline.py` to fetch or load the **original S-Agent (VLM) baseline** predictions and latency data from the canonical source. **Constraint**: Must not use any proxy or simulated baseline; only the original S-Agent data is permitted (Constitution Principle VII).
- [X] T006d [P] [US2] Implement `code/data/load_ground_truth.py` to fetch or extract the ground-truth labels for the n=1,000 sampled scenes and save as `data/derived/ground_truth.csv`. **Constraint**: Must match the scene IDs from T006b.
- [X] T007 [P] Implement `code/data/validate_distribution.py` to perform KS-tests on object density and spatial variance (Distributional Validity Gate). **Output**: Generate `data/results/distribution_validity.json` containing `p_value` and `d_statistic` for each metric.
- [X] T008 [P] [US1] Unit test for constraint propagation logic in `tests/unit/test_csp_logic.py` (verify "No Solution" for ambiguous inputs)
- [X] T009 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_extract_geometry.py` (verify JSON schema compliance and malformed data exclusion)

---

## Phase 3: User Story 1 - Symbolic CSP Solver Execution (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic CSP solver that ingests 3D geometric constraints and produces spatial reasoning predictions without neural inference.

**Independent Test**: Run `code/solver/run_solver.py` on a sample of scenes; verify JSON output contains predictions for all IDs, zero GPU utilization, and a valid `latency_log.jsonl`.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data/extract_geometry.py` to parse the S-Agent-300K dataset, **detect malformed/missing data**, **exclude** invalid scenes from processing, and output `data/derived/constraints.jsonl` (FR-001, FR-007). **Output**: Must also generate `data/results/exclusion_log.json` with counts and IDs of excluded scenes immediately upon detection. **Schema Requirement**: The JSON must explicitly contain top-level keys `total_scenes` (integer) and `excluded_count` (integer), plus a list of `excluded_ids`. **Note**: This task is a duplicate of T006b. T006b is the primary extraction task. T010 is removed from the task list to avoid confusion. **Correction**: T010 is removed; T006b is the sole extraction task.
- [X] T029 [US1] Implement a "dry-run" validation step in `code/validate/dry_run.py` that checks file existence and schema compliance of `constraints.jsonl` against `constraints.schema.yaml` before launching the solver batch, preventing wasted compute on malformed inputs (Addressing Edge Case: "corrupted input data"). **Dependency**: Must run AFTER T006b (Extraction) and BEFORE T027 (VLM Audit) and T012 (Solver). **Output**: Generate `data/results/dry_run_status.json` with `status: "pass" | "fail"`. **Gate**: T027 and T012 must fail if `dry_run_status.json` indicates "fail". **Verification**: Run `python code/validate/dry_run.py` against `data/derived/constraints.jsonl` (if exists) or a generated test fixture. **Order**: T006b -> T029 -> T027 -> T012.
- [ ] T027 [US1] Implement `code/validate/vlm_trace_auditor.py` to validate that no VLM traces (keys: 'tool_call_history', 'vlm_prediction') are present in `data/derived/constraints.jsonl`. **Dependency**: Must run AFTER T006b (extraction) and T029 (dry-run). Output `data/results/vlm_trace_audit.json` confirming zero traces found (Addressing Constitution Principle VII). **Gate**: If traces are found, halt pipeline immediately with error message "VIOLATION: VLM traces detected in constraint data. Aborting." and log the specific trace keys found. **Output Schema**: `{"status": "pass|fail", "trace_keys_found": [...]}`. **Note**: This task verifies T006b's output.
- [X] T011 [US1] Implement `code/solver/csp_engine.py` using `python-constraint (Wikidata Q[identifier], [identifier])` or `ortools` to solve counting/positioning tasks (FR-002)
- [ ] T012 [US1] Implement `code/solver/run_solver.py` for full batch execution. **Requirements**: Global batch timeout (`BATCH_TIMEOUT_HOURS`); stop processing new scenes if reached. Log remaining IDs in `solver_failures.json` with `error_type: "BatchTimeout"`. Per-scene soft limit (`SCENE_SOFT_LIMIT_SECONDS`) with warning logs. Enforce status tracking ('No Solution', 'Ambiguous', 'Success') for every processed scene. **Output**: `data/derived/predictions.jsonl` (`scene_id`, `prediction`, `status`), `data/derived/latency_log.jsonl` (`scene_id`, `latency_ms`, `status`), and `data/derived/solver_failures.json` (solver-side errors). **Timing**: Use `time.perf_counter` for millisecond precision (FR-004). **Logic**: Define `ConstraintSatisfactionError` as a distinct subclass of `ValueError` to ensure specific logging. Log JSON format `{"scene_id": "...", "error_type": "ConstraintSatisfactionError", "message": "..."}`. Catch `RuntimeError`/`ValueError` as `error_type: "UnexpectedSolverError"`. Distinguish `error_type: "Timeout"`, `"ConstraintError"`, `"GeometricAmbiguity"`. **Dependency**: Must run AFTER T027. **Execution**: Execute `python code/solver/run_solver.py --batch` on the full n=1,000 scene subset. **Output**: Generate `data/derived/predictions.jsonl`, `data/derived/latency_log.jsonl`, `data/derived/solver_failures.json`, and `data/results/wall_clock_time.json` (containing `start_time`, `end_time`, `total_duration_seconds`). **Verification**: Run `python code/solver/run_solver.py --batch` and verify the output files exist and contain entries for all valid scene IDs. **Success Criterion**: Confirm total wall-clock time is < 6 hours by parsing `data/results/wall_clock_time.json` for the `total_duration_seconds` value (must be < 21600). Verify `solver_failures.json` contains no "BatchTimeout" entries.
- [X] T012e [US1] (Removed: Merged into T012)

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
- [X] T017 [US2] Implement statistical significance test (McNemar's) in `code/benchmark/metrics.py` (FR-005). **Library**: Use `scipy.stats.mcnemar`. **Input**: Construct a 2x2 contingency table from `data/results/benchmark_results.csv` (initial version generated by T019b-init). **Mapping**: `table = [[symbolic_correct & vlm_correct, symbolic_correct & vlm_wrong], [symbolic_wrong & vlm_correct, symbolic_wrong & vlm_wrong]]`. **Action**: Append calculated `p_value` (float) as a **new column** to `data/results/benchmark_results.csv` and **Save `data/results/benchmark_results.csv` with the new column**. **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/results/benchmark_results.csv'); assert 'p_value' in df.columns and df['p_value'].dtype == float"` to ensure the column exists and contains valid floats. (SC-003) **Dependency**: Must run AFTER T019b-init (initial generation). **Note**: This task also handles the finalization of the CSV (previously T019b-final).
- [X] T018 [US2] Implement `code/main.py` orchestrator to run the full pipeline: **download → verify_checksum → validate_distribution (HARD BLOCK) → extract → vlm_audit (HARD BLOCK) → solve → benchmark** (FR-003)
- [ ] T019b-init [US2] Generate `data/results/benchmark_results.csv` linking scene IDs, predictions, ground truth, and metrics. **Requirements**: Columns must include `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`. (Note: `p_value` is added later by T017). Use `benchmark_result.schema.yaml` (from T005) for join logic (SC-001, SC-002). **Exclusion Logic**: Must explicitly read `data/results/exclusion_log.json` (from T006b) to perform the filtering and ensure `n_valid` matches the processed count. **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/results/benchmark_results.csv'); import json; exclusions = json.load(open('data/results/exclusion_log.json')); n_valid = exclusions['total_scenes'] - exclusions['excluded_count']; assert len(df) == n_valid"` and check file row count matches expected n. **Dependency**: Consumes schema from T005; depends on T006b for exclusion keys, **T012 (solver output)**, **T006c (VLM baseline)**, and **T006d (ground truth)**. **Note**: This task generates the initial file; T017 updates it with `p_value`.
- [ ] T019b-final [US2] (Removed: Merged into T017)
- [ ] T030 [US2] Implement `code/benchmark/sensitivity.py` to implement the sensitivity analysis sweep algorithm and generate `data/results/sensitivity_analysis.csv` by sweeping the accuracy threshold (SC-005) across a range of values. **Logic**: Read VLM baseline accuracy from `data/results/benchmark_results.csv` (the initial version generated by T019b-init). Sweep threshold from a lower bound to a high value with a fixed step size. **Output**: Logic to output `data/results/sensitivity_analysis.csv` with columns `threshold, verdict` (Addressing Assumption: "Threshold Justification"). **Dependency**: Must run AFTER T019b-init. **Note**: This task is exploratory and does not alter the primary success criterion (SC-005).
- [ ] T030a-logic [US2] (Removed: Merged into T030)
- [ ] T030b-output [US2] (Removed: Merged into T030)

**Checkpoint**: Benchmark report generated with accuracy and latency comparisons; statistical significance calculated; sensitivity analysis and verification artifacts produced.

---

## Phase 5: User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**Goal**: Analyze specific failure cases to distinguish between "Geometric Ambiguity" and "Semantic Gap".

**Independent Test**: Run `code/benchmark/analyze_failures.py` on a subset of mismatched predictions; verify classification report and proportion statistic.

### Tests for User Story 3

- [X] T020 [P] [US3] Unit test for failure categorization logic in `tests/unit/test_failure_analysis.py`

### Implementation for User Story 3

- [ ] T013 [US3] Implement `code/validate/merge_exclusions.py` to merge `data/results/exclusion_log.json` (from T006b) and `data/derived/solver_failures.json` (from T012) into a final `data/results/exclusion_log.json`. **Dependency**: Must wait for T006b and T012. **Logic**: Parse `error_type` from T012 output to categorize exclusions as "MissingData", "ConstraintError", "GeometricAmbiguity", or "BatchTimeout". (FR-007) **Output**: `data/results/exclusion_log.json` with categorized exclusions. **Verification**: Run `python code/validate/merge_exclusions.py` and verify the output contains categorized `error_type` keys.
- [ ] T021 [US3] Implement `code/benchmark/analyze_failures.py` to classify failures as "Geometric Ambiguity" or "Semantic Gap" and **calculate the proportion of failures attributable to semantic disambiguation** (FR-006, SC-004). **Logic**: Formula = `count(semantic_gap) / count(symbolic_failures)` where `symbolic_failures` are scenes where the solver returned "No Solution" or "Ambiguous" but VLM was correct. **Dependency**: Must wait for T019b-init to generate `data/results/benchmark_results.csv` **and T012 (solver failures)** to access raw failure reasons. **Merge Logic**: Join `benchmark_results.csv` and `solver_failures.json` on `scene_id`. **Strict Dependency**: If T019b-init output is missing, the script MUST halt with an error; no fallback to raw data is permitted to ensure Single Source of Truth. **Error Handling**: If scene IDs in the two files do not align (e.g., due to exclusion logic differences), the script MUST **ABORT with a critical error** indicating a data flow integrity failure, rather than logging a warning. **Output**: Generate `data/derived/failure_classification.json` with scene IDs, classifications, and metadata. **JSON Structure**: `{"scene_id": "...", "classification": "...", "reason": "..."}`. **Output Key**: The summary object MUST include the key `semantic_gap_proportion` with the calculated float value. **Verification**: Run `python code/benchmark/analyze_failures.py` and verify output JSON contains the `semantic_gap_proportion` key. **Dependency**: Must run AFTER T013.
- [X] T022 [US3] Generate `data/results/failure_analysis_report.md` with summary counts, **proportion statistic**, and a table of representative example scene IDs with text explanations (US-3, SC-004). **Requirements**: Report must include a section for "Geometric Ambiguity" and "Semantic Gap" counts, the proportion statistic, and a table of representative failure cases with scene IDs and text explanations derived from scene metadata. **Dependency**: Must wait for T021.
- [X] T023 [US3] Update `code/main.py` to include failure analysis as a final step in the pipeline

**Checkpoint**: Failure analysis report identifies root causes of symbolic solver underperformance and quantifies the semantic gap proportion.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final checks.

- [X] T024 [P] [Polish] Update `docs/quickstart.md` with execution instructions for the full pipeline. **Content**: Include steps for fixed sample extraction (n=1,000), solver execution, and benchmarking.
- [X] T025 [Polish] Run `code/hygiene.py` to finalize artifact hashes (including `data/results/*`) and update state YAML
- [X] T026 [US2] [Polish] Implement `code/validate/acceptance_checker.py` to verify all acceptance scenarios in `spec.md` (US-1, US-2, US-3) are met by running the full pipeline end-to-end; output `data/results/acceptance_checklist.md` with pass/fail status for each scenario (Addressing Constitution Principle I). **Criteria**: Explicitly check US-1 (solver execution), US-2 (benchmark metrics), US-3 (failure analysis). **Success Verdict**: Must explicitly verify SC-005 (**Exact Match** score >= 85% of VLM baseline). **Logic**: Calculate the ratio of symbolic exact matches to VLM exact matches, expressed as a percentage. **Zero-Division Handling**: If `vlm_exact_match` is 0, verdict is "N/A (Baseline Zero)". Otherwise, compare `measured_percentage` to 85. **Output Requirement**: `acceptance_checklist.md` MUST contain the measured percentage, the 85% threshold, and the final Pass/Fail verdict. **Dependency**: Must run AFTER T021 (Failure Analysis).
- [ ] T031 [Polish] Implement `code/validate/final_report_generator.py` to aggregate `benchmark_results.csv`, `sensitivity_analysis.csv`, `failure_analysis_report.md`, and `acceptance_checklist.md` into a single `data/results/final_research_report.md` (Addressing Constitution Principle IV: Single Source of Truth for final deliverables). **Dependency**: Must run after T022 and T030. **Verification**: Run `python code/validate/final_report_generator.py` and verify the output contains the following section headers: "## Benchmark Results", "## Failure Analysis", "## Sensitivity Analysis", "## Acceptance Checklist", "## Conclusion".
- [X] T032 [Polish] Create `README.md` at repository root summarizing the feature branch, execution steps, and key findings location (Addressing Project Accessibility). **Requirements**: Must include a "Quickstart" section referencing `docs/quickstart.md` and a "Results" section pointing to `data/results/final_research_report.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T001a-T001f must complete before T002/T003.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS** all User Stories.
 - T005a-T005d, T005e, T005f, T005g must complete before T029/T006b.
 - T006 must complete before T006a.
 - T006a must complete before T006b.
 - T006b must complete before T029/T027/T011/T012.
 - T029 must complete before T027/T012.
 - T027 must complete before T012 (Gate).
- **User Stories (Phase 3-5)**: Depend on Foundational. Can be executed in parallel if resources allow, but logically ordered P1 → P2 → P3.
- **Polish (Phase 6)**: Depends on all User Stories completion.

### User Story Dependencies

- **US1 (P1)**: Must complete first. Provides the `predictions.jsonl` and `latency_log.jsonl` required by US2 and US3.
 - T006b must complete before T029/T011/T012.
 - T029 must complete before T027/T012.
 - T027 must complete before T012 (Gate).
 - T012 must complete before T013 (Phase 5).
- **US2 (P2)**: Depends on US1 outputs (predictions, latency) and Ground Truth and VLM Baseline (from T006c, T006d).
 - T019b-init must complete before T017, T021, T026, T030.
 - T017 must complete before T026 (moved to Phase 6).
 - T030 must complete before final success verdict.
 - T026 must complete after T021 (Failure Analysis).
- **US3 (P3)**: Depends on US1 (predictions) and US2 (mismatch identification). T021/T022 depend on T019b-init, T012, and T013.
- **Polish (Phase 6)**: T031 depends on T022 and T030. T032 depends on T031. T026 depends on T021. T013 depends on T006b and T012.

### Parallel Opportunities

- **Phase 2**: T004, T006, T006c, T006d, T007 can run in parallel **EXCEPT**: T006a must run **AFTER** T006. T005a-T005d can run in parallel, but T005e must run **AFTER** T005a-T005d. T005f, T005g can run in parallel.
- **Phase 3**: T006b (extract) and T011 (solver logic) can be **developed** in parallel, but **execution** order is T006b -> T011. T029 must complete after T006b and before T027/T012. **Note**: T027 is strictly sequential (T006b -> T029 -> T027 -> T012) and not a parallel opportunity.
- **Phase 4**: T016 (metrics) and T017 (stats) can be **developed** in parallel. T017 execution depends on T019b-init (initial). T030, T026 (moved to Phase 6), T027 (moved to Phase 3) can be developed in parallel where applicable. T027 depends on T006b.
- **Phase 5**: T013 (Merge Exclusions) and T021 (analysis logic) can be developed in parallel, but T021 execution depends on T013. T022 (report generation) depends on T021.
- **Phase 6**: T031, T032 can be developed in parallel once dependencies are met. T031 depends on T022 and T030. T032 depends on T031. T026 depends on T021.

---

## Notes

- **Data Hygiene**: All data fetching (`T006`) must fail loudly if the real dataset is unavailable. **Checksum verification** (`T006a`) is mandatory before extraction.
- **Compute**: The CSP solver (`T012`) must be CPU-only. No GPU usage is permitted for the symbolic path.
- **Validity**: The Distributional Validity Gate (`T007`) is a **hard block** in `main.py` (`T018`). If it fails, the pipeline aborts.
- **Traceability**: All metrics must trace back to `data/results/benchmark_results.csv`. Latency traces back to `data/derived/latency_log.jsonl`.
- **Failures**: Excluded scenes must be logged explicitly (`T006b`, `T013`) to maintain transparency on the final sample size. Exclusion logic is implemented in `T006b` (with explicit keys `total_scenes`, `excluded_count`).
- **VLM Baseline**: Pre-computed VLM baseline data is loaded via `T006c` to ensure fair comparison.
- **Edge Cases**: Task T012 explicitly addresses the "insufficient constraints" edge case defined in the spec to prevent silent failures, distinguishing it from generic errors.
- **Assumptions**: Task T030 addresses the "Threshold Justification" assumption by adding a sensitivity analysis to the pipeline with defined sweep parameters (0.50-0.95, step 0.05).
- **Schemas**: Task T005a-T005e must generate and validate the schema files before T006b/T011 implementation begins.
- **Verification**: Tasks T026 and T027 must produce specific artifacts (`acceptance_checklist.md`, `vlm_trace_audit.json`) to prove compliance with Constitution Principles I and VII.
- **Sensitivity**: Task T030 must be completed before the final success verdict to ensure robustness.
- **Data Flow Correction**: Task T019b-init (benchmark results) is now explicitly marked as a dependency for T021 (failure analysis) to ensure the analysis script has the necessary ground-truth comparisons before attempting to classify errors.
- **Fallback Logic**: T021 explicitly forbids fallback to raw data; it must halt if T019b-init is missing.
- **VLM Integrity Gate**: Task T027 is now a hard gate in Phase 3, executed after extraction and before solver execution, to strictly enforce Constitution Principle VII.
- **Timeout Transparency**: Task T012 explicitly distinguishes between "Timeout" and "Geometric Ambiguity" in exclusion logs to satisfy FR-007.
- **Final Deliverable**: Task T031 ensures all research artifacts are aggregated into a single, reproducible report, satisfying the "Single Source of Truth" principle for the final output.
- **Documentation**: Task T032 ensures the project is accessible to new researchers by providing a clear entry point in `README.md`.
- **Citation Verification**: Task T005f/T005g implements the `validate_citations` gate required by Constitution Principle II.
- **Ordering**: T029 (Dry-run) is now strictly ordered: T006b -> T029 -> T027 -> T012.
- **Schema**: T019a removed; T019b-init depends on T005.
- **Acceptance Check**: T026 moved to Phase 6, after T021.
- **No Streaming**: Tasks T033-T038 removed as they contradicted the spec's fixed sample size requirement.
- **Consolidation**: T012a-d consolidated into T012; T028a-b consolidated into T012; T005a-Verify...T005d-Verify consolidated into T005a-e.
- **Task Movement**: T013 moved to Phase 5. T028 moved to Phase 3.
- **New Tasks**: T006d (Ground Truth) added to Phase 2.
- **Circular Dependency Resolution**: T019b-init generates the initial CSV; T017 updates it with `p_value`; T019b-final removed. T030 handles sensitivity analysis. This breaks the circular dependency.
- **Batch Execution**: T012 is the distinct task for full batch execution, ensuring the 6-hour wall-clock time criterion is met.
- **Artifact Naming**: All tasks now explicitly name their output artifacts in the header or description.
- **Stratification Fallback**: T006 includes ABORT logic if stratification keys are missing, with NO proxy fallback.
- **Manifest Generation**: T006 explicitly generates `data/manifest.json` with SHA-256 hashes to satisfy T006a's dependency and Constitution Principle III.
- **Parallel Tag Correction**: T027 and T012 no longer have the [P] tag to reflect their strict sequential dependency.
- **Column Name**: T019b-init uses 'f1' instead of 'f' to match spec.
- **Removed Proxy**: T006 no longer has proxy fallback logic.
- **Merged Tasks**: T012a-c and T012e merged into T012. T019b-final merged into T017. T030a and T030b merged into T030.
- **Phase Adjustment**: T013 moved to Phase 5 to satisfy T021 dependency.