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

- [ ] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw/`, `data/derived/`, `data/results/`, `specs/`, `tests/`)
- [X] T002 [P] Initialize Python 3.11 environment and create `code/requirements.txt` with pinned versions (`python-constraint`, `pandas`, `scipy`, `pytest`, `huggingface_hub`, `scikit-learn`)
- [X] T003 [P] Configure `code/config.py` for paths, random seeds, and sample size (n=1,000) constants

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, data hygiene, and validation gates. **⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `code/hygiene.py` to compute SHA-256 hashes for `data/raw/*` and `data/derived/*` (excluding results until Phase 6) and update `state/projects/PROJ-893-llmxive-follow-up-extending-s-agent-spat.yaml`
- [ ] T005 [P] Create schema contracts in `specs/001-symbolic-spatial-reasoning/contracts/` (`dataset.schema.yaml`, `solver_output.schema.yaml`, `benchmark_result.schema.yaml`, `latency_log.schema.yaml`)
- [X] T006 [P] Implement `code/data/download.py` to fetch S-Agent-300K subset using `huggingface_hub` with **FAIL LOUD** logic (no synthetic fallbacks)
- [X] T006a [P] Implement `code/data/verify_checksum.py` to verify the downloaded dataset's checksum against the `data/` manifest (Constitution Principle III) before extraction
- [X] T006b [P] Implement `code/data/load_vlm_baseline.py` to fetch or load pre-computed VLM baseline predictions and latency data from the canonical source
- [X] T007 [P] Implement `code/data/validate_distribution.py` to perform KS-tests on object density and spatial variance (Distributional Validity Gate)

---

## Phase 3: User Story 1 - Symbolic CSP Solver Execution (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic CSP solver that ingests 3D geometric constraints and produces spatial reasoning predictions without neural inference.

**Independent Test**: Run `code/solver/run_solver.py` on a sample of 10 scenes; verify JSON output contains predictions for all IDs, zero GPU utilization, and a valid `latency_log.jsonl`.

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for constraint propagation logic in `tests/unit/test_csp_logic.py` (verify "No Solution" for ambiguous inputs)
- [X] T009 [P] [US1] Integration test for data extraction pipeline in `tests/integration/test_extract_geometry.py` (verify JSON schema compliance and malformed data exclusion)

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/data/extract_geometry.py` to parse S-Agent-300K, **detect malformed/missing data**, **exclude** invalid scenes from processing, and output `data/derived/constraints.jsonl` (FR-001, FR-007)
- [X] T011 [US1] Implement `code/solver/csp_engine.py` using `python-constraint` or `ortools` to solve counting/positioning tasks (FR-002)
- [ ] T012 [US1] Implement `code/solver/run_solver.py` to batch process n=1,000 scenes, **measure per-scene latency**, and output `data/derived/predictions.jsonl` AND `data/derived/latency_log.jsonl` (FR-002, FR-004) <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement logging in `run_solver.py` to record excluded scenes (from T010) to `data/results/exclusion_log.json` with counts and IDs (FR-007)

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
- [ ] T019 [US2] Generate `data/results/benchmark_results.csv` linking scene IDs, predictions, ground truth, and metrics (SC-001, SC-002)

**Checkpoint**: Benchmark report generated with accuracy and latency comparisons; statistical significance calculated.

---

## Phase 5: User Story 3 - Failure Case Analysis & Semantic Gap Identification (Priority: P3)

**Goal**: Analyze specific failure cases to distinguish between "Geometric Ambiguity" and "Semantic Gap".

**Independent Test**: Run `code/benchmark/analyze_failures.py` on a subset of mismatched predictions; verify classification report and proportion statistic.

### Tests for User Story 3

- [X] T020 [P] [US3] Unit test for failure categorization logic in `tests/unit/test_failure_analysis.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement `code/benchmark/analyze_failures.py` to classify failures as "Geometric Ambiguity" or "Semantic Gap" and **calculate the proportion of failures attributable to semantic disambiguation** (FR-006, SC-004)
- [ ] T022 [US3] Generate `data/results/failure_analysis_report.md` with summary counts, **proportion statistic**, and representative example scene IDs (US-3, SC-004)
- [X] T023 [US3] Update `code/main.py` to include failure analysis as a final step in the pipeline

**Checkpoint**: Failure analysis report identifies root causes of symbolic solver underperformance and quantifies the semantic gap proportion.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and final checks.

- [X] T024 [P] [Polish] Update `docs/quickstart.md` with execution instructions for the full pipeline
- [X] T025 [Polish] Run `code/hygiene.py` to finalize artifact hashes (including `data/results/*`) and update state YAML
- [ ] T026 [Polish] Verify all acceptance scenarios in `spec.md` are met by running the full pipeline end-to-end
- [ ] T027 [Polish] Validate that no VLM traces are present in solver input (FR-001, FR-002)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS** all User Stories.
- **User Stories (Phase 3-5)**: Depend on Foundational. Can be executed in parallel if resources allow, but logically ordered P1 → P2 → P3.
- **Polish (Phase 6)**: Depends on all User Stories completion.

### User Story Dependencies

- **US1 (P1)**: Must complete first. Provides the `predictions.jsonl` and `latency_log.jsonl` required by US2 and US3.
- **US2 (P2)**: Depends on US1 outputs (predictions, latency) and Ground Truth and VLM Baseline (from T006b).
- **US3 (P3)**: Depends on US1 (predictions) and US2 (mismatch identification).

### Parallel Opportunities

- **Phase 2**: T004, T005, T006, T006a, T006b, T007 can run in parallel.
- **Phase 3**: T010 (extract) and T011 (solver logic) can be developed in parallel, but T012 (run) depends on both.
- **Phase 4**: T016 (metrics) and T017 (stats) can be developed in parallel.
- **Phase 5**: T021 (analysis logic) can be developed independently of T022 (report generation).

---

## Notes

- **Data Hygiene**: All data fetching (`T006`) must fail loudly if the real dataset is unavailable. **Checksum verification** (`T006a`) is mandatory before extraction.
- **Compute**: The CSP solver (`T011`, `T012`) must be CPU-only. No GPU usage is permitted for the symbolic path.
- **Validity**: The Distributional Validity Gate (`T007`) is a **hard block** in `main.py` (`T018`). If it fails, the pipeline aborts.
- **Traceability**: All metrics must trace back to `data/results/benchmark_results.csv`. Latency traces back to `data/derived/latency_log.jsonl`.
- **Failures**: Excluded scenes must be logged explicitly (`T013`) to maintain transparency on the final sample size. Exclusion logic is implemented in `T010`.
- **VLM Baseline**: Pre-computed VLM baseline data is loaded via `T006b` to ensure fair comparison.
