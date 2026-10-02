# Tasks: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

**Input**: Design documents from `/specs/001-symbolic-spatial-reasoning/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Branch**: `001-symbolic-spatial-reasoning`

**Tests**: Unit and integration tests are included for critical logic paths (CSP solver, distributional validity, failure analysis) to ensure reproducibility and data hygiene.

**Organization**: Tasks are grouped by phase and user story to enable independent verification of the symbolic solver, benchmarking, and failure analysis against the S-Agent dataset.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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
- [ ] T005f [US1] Implement `code/validate/validate_citations.py` to verify citations in `spec.md` and `plan.md` against the "Verified Datasets" block. **Requirement**: Must check title-token-overlap ≥ 0.7. Exit with error if any citation is unreachable or mismatched. (Constitution Principle II). **Note**: This is a **preliminary** check for static design inputs. It does NOT validate `research.md` or final paper artifacts. **Dependency**: Must run AFTER T006 completion. **Future Scope**: This task explicitly defers validation of `research.md` to T005h, which must be executed once `research.md` is generated in Phase 0 to satisfy the full Verified Accuracy Gate.
- [ ] T005g [P] Update `code/main.py` to invoke `validate_citations` as the first step before any data processing. **Gate**: If validation fails, abort pipeline immediately. **Dependency**: Must run AFTER T005f.
- [ ] T005h [US1] Implement `code/validate/validate_research_citations.py` to verify citations in `research.md` (generated in Phase 0) against the "Verified Datasets" block. **Requirement**: Must check title-token-overlap ≥ 0.7. **Gate**: This is the **final** Verified Accuracy Gate. The pipeline MUST NOT proceed to T006 or any data processing until `research.md` citations are verified. **Dependency**: Must run AFTER `research.md` is generated (Phase 0 output). **Note**: This task ensures Constitution Principle II is satisfied for the primary research output.
- [ ] T006 [US1] Implement `code/data/download.py` to fetch the **S-Agent dataset** using `huggingface_hub` and create `data/raw/sampled_manifest.json`. **Logic**: Must perform a **stratified random sample** of exactly n=1,000 static multi-view scenes. **Algorithm**: Attempt `pandas.DataFrame.groupby(['object_density', 'scene_complexity']).sample(n=..., random_state=SEED)`. **Verification**: Before sampling, verify the existence of columns `object_density` and `scene_complexity`. **ABORT Logic**: If these columns are missing, the script MUST **ABORT** with a 'Distributional Validity Gate Failure' error and trigger T007b (Pilot mode) instead of proceeding to T007. A fallback to simple random sampling is **NOT** permitted unless explicitly authorized by `research.md` as a 'Pilot' mode. **Artifact Generation**: Upon successful download, compute SHA-256 hashes for every downloaded file and write them to `data/raw/sampled_manifest.json` as a list of objects: `[{"file": "<filename>", "sha256": "<hash>"}]`. **Primary Deliverable**: Save the output dataset as `data/raw/sampled_scenes.jsonl`. **Verification**: Run `python -c "import json; import os; m = json.load(open('data/raw/sampled_manifest.json')); assert len(m) > 0 and all('sha256' in x for x in m)"` to ensure manifest exists and is valid. Also verify `os.path.exists('data/raw/sampled_scenes.jsonl')`.
- [ ] T006a [US1] Implement `code/data/verify_checksum.py` to verify the downloaded dataset's checksum against the `data/raw/sampled_manifest.json` (Constitution Principle III) before extraction. **Dependency**: Must run AFTER T006 completion. **Gate**: If checksums mismatch or `data/raw/sampled_manifest.json` is missing, abort with error. **Note**: T006a is NOT parallel ([P]) as it depends on T006.
- [ ] T006b [US1] Implement `code/data/extract_geometry.py` to parse the S-Agent-300K dataset, **detect malformed/missing data**, **exclude** invalid scenes from processing, and output `data/derived/constraints.jsonl` (FR-001, FR-007). **Output**: Must also generate `data/results/exclusion_log.json` with counts and IDs of excluded scenes immediately upon detection. **Schema Requirement**: The JSON must explicitly contain top-level keys `total_scenes` (integer), `excluded_count` (integer), and a list of `excluded_ids`. **Dependency**: Must run AFTER T006a. **Verification**: Run `python -c "import json; e = json.load(open('data/results/exclusion_log.json')); assert 'total_scenes' in e and 'excluded_count' in e and 'excluded_ids' in e"` to ensure schema compliance. **Sample Size Note**: The final valid sample size `n` is defined as `total_scenes - excluded_count`.
- [ ] T006c [P] [US2] Implement `code/data/load_vlm_baseline.py` to fetch or load the **original S-Agent (VLM) baseline** predictions and latency data from the canonical source. **Constraint**: Must not use any proxy or simulated baseline; only the original S-Agent data is permitted (Constitution Principle VII).
- [ ] T006d [P] [US2] Implement `code/data/load_ground_truth.py` to fetch or extract the ground-truth labels for the n=1,000 sampled scenes and save as `data/derived/ground_truth.csv`. **Constraint**: Must match the scene IDs from T006b.
- [ ] T007 [P] Implement `code/data/validate_distribution.py` to perform KS-tests on object density and spatial variance (Distributional Validity Gate). **Output**: Generate `data/results/distribution_validity.json` containing `p_value` and `d_statistic` for each metric. **Dependency**: Requires T006 to succeed. **Note**: If T006 aborts due to missing columns, T007 is skipped and T007b is executed instead.
- [ ] T007b [P] Implement `code/data/validate_pilot_mode.py` to handle the 'Pilot/Proxy' fallback path. **Logic**: If T006 aborts due to missing stratification columns, this script runs KS-tests on available metadata or a verified proxy dataset to determine if a 'Pilot' study is valid. **Output**: Generate `data/results/pilot_validity.json` with `status: "valid" | "invalid"` and justification. **Gate**: If T006 fails, T007b MUST run. If T007b returns "invalid", the pipeline aborts. **Dependency**: Must run AFTER T006 aborts.
- [X] T008 [P] Unit test for constraint propagation logic in `tests/unit/test_csp_logic.py` (verify "No Solution" for ambiguous inputs)
- [X] T009 [P] Integration test for data extraction pipeline in `tests/integration/test_extract_geometry.py` (verify JSON schema compliance and malformed data exclusion)
- [ ] T027 [US2] Implement `code/validate/vlm_audit.py` to verify the VLM baseline integrity (Constitution Principle VII). **Current State**: This task is currently incomplete; the `vlm_audit.py` script and `vlm_trace_audit.json` artifact are missing/truncated. **Logic**: Check that the VLM baseline data corresponds to the exact scene IDs in `data/raw/sampled_scenes.jsonl` and that no tool-call traces are leaked into the symbolic input. **Output**: Generate `data/results/vlm_trace_audit.json` with `status: "pass" | "fail"` and a list of any discrepancies. **Gate**: T012 MUST fail if this audit fails. **Dependency**: Must run AFTER T006c and T006d. **Verification**: Run `python -c "import json; a = json.load(open('data/results/vlm_trace_audit.json')); assert a['status'] == 'pass'"`. **Note**: This task must replace the currently broken implementation with a fully functional script and generate the required JSON artifact.
- [ ] T029 [US1] Implement a "dry-run" validation step in `code/validate/dry_run.py` that checks file existence and schema compliance of `constraints.jsonl` against `constraints.schema.yaml` before launching the solver batch, preventing wasted compute on malformed inputs (Addressing Edge Case: "corrupted input data"). **Current State**: This task is currently incomplete; the `dry_run.py` script and `dry_run_status.json` artifact are missing/truncated. **Dependency**: Must run AFTER T006b. **Output**: Generate `data/results/dry_run_status.json` with `status: "pass" | "fail"`. **Gate**: T012 must fail if `dry_run_status.json` indicates "fail". **Verification**: Run `python code/validate/dry_run.py` against `data/derived/constraints.jsonl` (if exists) or a generated test fixture. **Note**: This task must replace the currently broken implementation with a fully functional script and generate the required JSON artifact.

---

## Phase 3: User Story 1 - Symbolic CSP Solver Execution (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic CSP solver that ingests 3D geometric constraints and produces spatial reasoning predictions without neural inference.

**Independent Test**: Run `code/solver/run_solver.py` on a sample of scenes; verify JSON output contains predictions for all IDs, zero GPU utilization, and a valid `latency_log.jsonl`.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/solver/csp_engine.py` using `python-constraint` or `ortools` to solve counting/positioning tasks (FR-002)
- [ ] T012-parallel [US1] Implement `code/solver/parallel_executor.py` to handle batch execution using `concurrent.futures.ProcessPoolExecutor`. **Logic**: Must utilize a number of workers matching the CPU core constraint to process scenes in parallel. **Timeout**: Implement a global batch timeout and per-scene soft limit within the executor. **Dependency**: Must run AFTER T027, T006b, and T029. **Output**: Generate `data/results/parallel_config.json` confirming worker count and timeout settings.
- [ ] T012-exec [US1] Implement `code/solver/run_solver.py` for full batch execution. **Requirements**: Global batch timeout (`BATCH_TIMEOUT_HOURS`); stop processing new scenes if reached. Log remaining IDs in `data/derived/solver_failures.json` with `error_type: "BatchTimeout"`. Per-scene soft limit (`SCENE_SOFT_LIMIT_SECONDS`) with warning logs. Enforce status tracking ('No Solution', 'Ambiguous', 'Success') for every processed scene. **Output**: `data/derived/predictions.jsonl` (`scene_id`, `prediction`, `status`), `data/derived/latency_log.jsonl` (`scene_id`, `latency_ms`, `status`), and `data/derived/solver_failures.json`. **Timing**: Use `time.perf_counter` for millisecond precision (FR-004). **Logic**: Define `ConstraintSatisfactionError` as a distinct subclass of `ValueError` to ensure specific logging. Log JSON format `{"scene_id": "...", "error_type": "ConstraintSatisfactionError", "message": "..."}`. Catch `RuntimeError`/`ValueError` as `error_type: "UnexpectedSolverError"`. Distinguish `error_type: "Timeout"`, `"ConstraintError"`, `"GeometricAmbiguity"`. **Dependency**: Must run AFTER T027, T006b, T029, and **T012-parallel**. **Execution**: Execute `python code/solver/run_solver.py --batch` on the full n=1,000 scene subset. **Output**: Generate `data/derived/predictions.jsonl`, `data/derived/latency_log.jsonl`, `data/derived/solver_failures.json`, and `data/results/wall_clock_time.json` (containing `start_time`, `end_time`, `total_duration_seconds`). **Verification**: Run `python code/solver/run_solver.py --batch` and verify the output files exist and contain entries for all valid scene IDs. Specifically verify `data/derived/solver_failures.json` exists and contains valid JSON. **Primary Deliverable Verification**: Run `python -c "import json; import os; p = [json.loads(l) for l in open('data/derived/predictions.jsonl')]; assert len(p) > 0 and all('scene_id' in x and 'prediction' in x for x in p)"` to ensure `predictions.jsonl` is valid and covers all processed scenes. **Success Criterion**: Confirm total wall-clock time is < 6 hours by parsing `data/results/wall_clock_time.json` for the `total_duration_seconds` value (must be < 21600). Verify `solver_failures.json` contains no "BatchTimeout" entries. **Timeout Handling**: If a timeout occurs, the scene is excluded from the final analysis set and logged as such. **Parallelization**: **Must explicitly set `workers=2`** to leverage the 2-core CPU constraint of the GitHub Actions runner.
- [ ] T013 [US3] Implement `code/validate/merge_exclusions.py` to merge `data/results/exclusion_log.json` (from T006b) and `data/derived/solver_failures.json` (from T012-exec) into a final `data/results/exclusion_log.json`. **Dependency**: Must wait for T006b and T012-exec. **Logic**: Parse `error_type` from T012-exec output to categorize exclusions as "MissingData", "ConstraintError", "GeometricAmbiguity", or "BatchTimeout". **Output**: `data/results/exclusion_log.json` with categorized exclusions. **Verification**: Run `python code/validate/merge_exclusions.py` and verify the output contains categorized `error_type` keys.

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
- [ ] T017 [US2] Implement statistical significance test (McNemar's) in `code/benchmark/metrics.py` (FR-005). **Library**: Use `scipy.stats.mcnemar`. **Input**: Construct a 2x2 contingency table from `data/results/benchmark_results_base.csv` (generated by T019b-init). **Mapping**: `table = [[symbolic_correct & vlm_correct, symbolic_correct & vlm_wrong], [symbolic_wrong & vlm_correct, symbolic_wrong & vlm_wrong]]`. **Action**: Append calculated `p_value` (float) to each row and **Save `data/results/p_values.jsonl`** (one JSON object per scene with `scene_id` and `p_value`). **Verification**: Run `python -c "import json; p = [json.loads(l) for l in open('data/results/p_values.jsonl')]; assert len(p) > 0 and all('p_value' in x for x in p)"` to ensure the file exists and is valid. (SC-003) **Dependency**: Must run AFTER T019b-init. **Abort Condition**: If the contingency table cannot be constructed (e.g., missing data from upstream failures), the pipeline MUST abort with a specific error. **Note**: This task consumes the base CSV from T019b-init and produces `p_values.jsonl` as a standalone artifact; it does NOT modify T019b-init's output directly.
- [ ] T018 [US2] Implement `code/main.py` orchestrator to run the full pipeline: **download → verify_checksum → validate_distribution (HARD BLOCK) → extract → vlm_audit (HARD BLOCK) → solve → benchmark** (FR-003)
- [ ] T019b-init [US2] Generate `data/results/benchmark_results_base.csv` linking scene IDs, predictions, ground truth, and metrics. **Requirements**: Columns must include `scene_id`, `symbolic_pred`, `vlm_pred`, `ground_truth`, `exact_match`, `f1`, `latency_ms`, `status`. **Exclusion Logic**: Must explicitly read `data/results/exclusion_log.json` (from T006b) to perform the filtering and ensure `n_valid` matches the processed count (`total_scenes - excluded_count`). **Note**: This task generates the base CSV **without** the `p_value` column. **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/results/benchmark_results_base.csv'); import json; exclusions = json.load(open('data/results/exclusion_log.json')); n_valid = exclusions['total_scenes'] - exclusions['excluded_count']; assert len(df) == n_valid"` and check file row count matches expected n. **Dependency**: Consumes schema from T005; depends on T006b (extraction), T006c (VLM baseline), T006d (ground truth), and T012-exec (solver output). **Abort Condition**: If T012-exec output is missing or incomplete, abort with error.
- [ ] T019b-final [US2] Finalize `data/results/benchmark_results.csv` by merging `data/results/benchmark_results_base.csv` with `data/results/p_values.jsonl` (from T017). **Requirements**: Add `p_value` column to the base CSV. **Output**: `data/results/benchmark_results.csv` (the canonical final artifact). **Dependency**: Must run AFTER T017 and T019b-init. **Verification**: Run `python -c "import pandas as pd; df = pd.read_csv('data/results/benchmark_results.csv'); assert 'p_value' in df.columns and df['p_value'].dtype == float"` to ensure the column exists and is valid.
- [ ] T030 [US2] Implement `code/benchmark/sensitivity.py` to implement the sensitivity analysis sweep algorithm and generate `data/results/sensitivity_analysis.csv` by sweeping the accuracy threshold (SC-005) across a range of values. **Logic**: The sweep must explicitly cover a range from **0.50 to 0.95** with a **step size of 0.05**. **Output**: `data/results/sensitivity_analysis.csv` containing columns `threshold`, `success_rate`, `false_positive_rate`. **Dependency**: Must run after T019b-final. **Verification**: Run `python code/benchmark/sensitivity.py` and verify the output CSV contains rows for thresholds 0.50, 0.55,..., 0.95. **Authoritative Source**: This CSV is the **authoritative source** for sensitivity data required by the final report (Constitution Principle IV).
- [X] T030a-logic [US2] Removed.
- [X] T030b-output [US2] Removed.

**Checkpoint**: Benchmark report generated with accuracy and latency comparisons; statistical significance calculated; sensitivity analysis and verification artifacts produced.

---

## Phase 5: User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**Goal**: Analyze specific failure cases to distinguish between "Geometric Ambiguity" and "Semantic Gap".

**Independent Test**: Run `code/benchmark/analyze_failures.py` on a subset of mismatched predictions; verify classification report and proportion statistic.

### Tests for User Story 3

- [X] T020 [P] [US3] Unit test for failure categorization logic in `tests/unit/test_failure_analysis.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement `code/benchmark/analyze_failures.py` to classify failures as "Geometric Ambiguity" or "Semantic Gap" and **calculate the proportion of failures attributable to semantic disambiguation** (FR-006, SC-004). **Logic**: Formula = `count(VLM_correct AND Symbolic_fail) / count(Symbolic_fail)`. **Dependency**: Must wait for T019b-final to generate `data/results/benchmark_results.csv` **and T012-exec (solver output)**. **Merge Logic**: Join `benchmark_results.csv` and `solver_failures.json` on `scene_id`. **Strict Dependency**: If T019b-final output is missing, the script MUST halt with an error. **Output**: Generate `data/derived/failure_classification.json` with scene IDs, classifications, and metadata. **JSON Structure**: A list of objects: `[{"scene_id": "...", "classification": "...", "reason": "..."}]`. **Output Key**: The summary object (if separate) or the aggregate calculation MUST include the key `semantic_gap_proportion` with the calculated float value. **Verification**: Run `python code/benchmark/analyze_failures.py` and verify `data/derived/failure_classification.json` exists, is a valid list of objects, and contains the `semantic_gap_proportion` key in the summary or aggregate calculation. **Value Check**: Verify `0 <= semantic_gap_proportion <= 1`.
- [X] T022 [US3] Generate `data/results/failure_analysis_report.md` with summary counts, **proportion statistic**, and a table of representative example scene IDs with text explanations (US-3, SC-004). **Requirements**: Report must include a section for "Geometric Ambiguity" and "Semantic Gap" counts, the proportion statistic, and a table of representative failure cases with scene IDs and text explanations derived from scene metadata. **Dependency**: Must wait for T021.
- [X] T023 [US3] Update `code/main.py` to include failure analysis as a final step in the pipeline

**Checkpoint**: Failure analysis report identifies root causes of symbolic solver underperformance and quantifies the semantic gap proportion.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final checks.

- [X] T024 [Polish] Update `docs/quickstart.md` with execution instructions for the full pipeline. **Content**: Include steps for fixed sample extraction (n=1,000), solver execution, and benchmarking.
- [X] T025 [Polish] Run `code/hygiene.py` to finalize artifact hashes (including `data/results/*`) and update state YAML
- [ ] T026 [Polish] Implement `code/validate/acceptance_checker.py` to verify all acceptance scenarios in `spec.md` (US-1, US-2, US-3) are met by running the full pipeline end-to-end; output `data/results/acceptance_checklist.md` with pass/fail status for each scenario (Addressing Constitution Principle I). **Criteria**: Explicitly check US-1 (solver execution), US-2 (benchmark metrics), US-3 (failure analysis). **Success Verdict**: Must explicitly verify SC-005 (**Exact Match** score >= 85% of VLM baseline). **Pipeline Failure Logic**: If the pipeline fails at any upstream step (e.g., T006 abort, T012 timeout), this script MUST record a **FAIL** verdict for SC-005 and the checklist, rather than skipping verification. **Dependency**: Must run after T019b-final and T022.
- [ ] T031 [Polish] Implement `code/validate/final_report_generator.py` to aggregate `benchmark_results.csv`, `sensitivity_analysis.csv`, `failure_analysis_report.md`, and `acceptance_checklist.md` into a single `data/results/final_research_report.md` (Addressing Constitution Principle IV: Single Source of Truth for final deliverables). **Input Files**: Explicitly list `benchmark_results.csv`, `sensitivity_analysis.csv`, `failure_analysis_report.md`, and `acceptance_checklist.md`. **Output**: `data/results/final_research_report.md`. **Verification**: Run `python code/validate/final_report_generator.py` and verify the output file exists and contains sections for all input files, including the sensitivity analysis data.
- [X] T032 [Polish] Create `README.md` at repository root summarizing the feature branch, execution steps, and key findings location (Addressing Project Accessibility). **Requirements**: Must include a "Quickstart" section referencing `docs/quickstart.md` and a "Results" section pointing to `data/results/final_research_report.md`.

---

## Dependencies & Execution Order

[See original plan for detailed dependency and execution order.]

## Notes

[See original plan for notes.]