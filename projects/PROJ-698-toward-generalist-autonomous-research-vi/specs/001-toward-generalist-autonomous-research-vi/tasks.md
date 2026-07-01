# Tasks: Reproduce & Validate Arbor (Hypothesis-Tree Refinement)

**Input**: Design documents from `/specs/001-reproduce-arbor/`
**Prerequisites**: plan.md, spec.md

**Tests**: Included to validate artifact generation and schema compliance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `vendor/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, vendoring, and dependency configuration for CPU-only execution.

- [X] T001 Create project structure:
      - Create `src/`, `tests/`, `vendor/`, `data/`, `results/`, `docs/`, `contracts/` directories.
      - Create `src/__init__.py`, `tests/__init__.py`, `vendor/__init__.py` (empty).
      - Create `.gitignore` containing: `__pycache__/`, `*.pyc`, `venv/`, `.env`, `results/`, `data/` (except raw/).
      - Create `README.md` with header `# Reproduce & Validate Arbor` and a "Setup" section placeholder.
      - **Note**: If `constitution.md` is missing, create a minimal one in `docs/` stating "No silent fallbacks; real data only; CPU-only execution".
      - **Verify**: `ls -1 src tests vendor data results docs contracts | wc -l` equals 7; `grep -q "Reproduce & Validate Arbor" README.md`.

- [X] T002 Initialize Python 3.10+ project:
      - Create `pyproject.toml` with minimal content:
        ```toml
        [tool.poetry]
        name = "reproduce-arbor"
        version = "0.1.0"
        [build-system]
        requires = ["poetry-core>=1.0.0"]
        build-backend = "poetry.core.masonry.api"
        ```
      - **Verify**: `grep -q '\\[tool.poetry\\]' pyproject.toml` and `grep -q 'python = "^3.10"' pyproject.toml`.

- [X] T003 [P] Vendor `Arbor` repository:
      - Clone `https://github.com/ArborAI/arbor.git` into `vendor/arbor/`.
      - If a specific commit hash is available (e.g., from `plan.md`), checkout that commit; otherwise, use the latest `main`.
      - Create `vendor/commit.txt` containing the exact commit hash used (e.g., `git rev-parse HEAD`).
      - **Verify**: `cat vendor/commit.txt` exists and is non-empty; `ls vendor/arbor/` is not empty.

- [X] T004 [P] Pin `torch` to CPU-only build:
      - Append to `requirements.txt`: `torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu`.
      - **Verify**: `grep -q 'torch.*cpu.*download.pytorch.org' requirements.txt`.

- [X] T005 [P] Install dependencies:
      - Append to `requirements.txt`: `scikit-learn>=1.3.0`, `pyyaml>=6.0`, `memory_profiler>=0.60.0`, `pytest>=7.0.0`, `jsonschema>=4.0.0`.
      - **Verify**: `pip list | grep -E 'scikit-learn.*1.3|pyyaml.*6.0|memory-profiler.*0.60|pytest.*7.0|jsonschema.*4.0'`.

- [X] T006 [P] Configure `pytest`:
      - Create `pytest.ini` with:
        ```ini
        [pytest]
        addopts = --ignore=vendor --ignore=data --ignore=results
        testpaths = tests
        ```
      - **Verify**: `pytest --collect-only` runs without errors and ignores `vendor/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, resource monitoring, and timeout enforcement required before any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Implement `src/monitor_resources.py`:
      - Script must accept a PID or process command, track `peak_memory_mb` and `total_runtime_seconds`.
      - Output: Write `results/resource_log.json` with schema: `{"peak_memory_mb": float, "total_runtime_seconds": float}`.
      - **Verify**: Run script on a dummy process; verify `results/resource_log.json` exists and contains valid floats for both keys.

- [X] T008 [P] Implement `src/run_arbor.py` wrapper:
      - CLI: `python src/run_arbor.py --task <name> --timeout-step 300 --timeout-total 21600 --max-retries 3`.
      - Logic: Enforce 300s per step, 21600s (6h) total. Kill process on timeout, log "TIMEOUT" to `results/error.log`. Limit retries to 3 to prevent infinite loops.
      - **Verify**: `python src/run_arbor.py --help` shows `--timeout-step`, `--timeout-total`, and `--max-retries`; simulate hang and verify exit code 1 and "TIMEOUT" in logs.

- [X] T009 [P] Create `src/generate_report.py`:
      - Input: `results/benchmark_score.txt`, `results/baseline_score.txt` (if exists).
      - Output: `results/summary.md` with header `# Benchmark Results` and section `## Comparison`.
      - **Verify**: Run script with dummy files; verify `results/summary.md` contains "# Benchmark Results" and "## Comparison".

- [X] T010 [P] Define `contracts/tree-node.schema.yaml`:
      - Schema must include fields: `id` (string), `type` (enum: Hypothesis, Evidence, Artifact), `parent_id` (string, nullable), `log_file_path` (string, nullable).
      - **Verify**: `jsonschema -i tests/fixtures/sample_node.json contracts/tree-node.schema.yaml` passes.

- [X] T011 [P] Define `contracts/benchmark-result.schema.yaml`:
      - Schema must include fields: `htr_score` (float), `baseline_score` (float), `improvement_percent` (float), `runtime_seconds` (float).
      - **Verify**: `jsonschema -i tests/fixtures/sample_result.json contracts/benchmark-result.schema.yaml` passes.

- [X] T012 [P] Create `data/dataset_loader.py`:
      - Function `load_dataset(name: str)` returning `X, y`.
      - Support `iris` (via `sklearn.datasets.load_iris`) and `wine` (via `sklearn.datasets.load_wine`).
      - **Verify**: `python -c "from data.dataset_loader import load_dataset; X, y = load_dataset('iris'); print(X.shape)"` works.

---

## Phase 3: User Story 1 - Verify Execution & Artifact Generation (Priority: P1) 🎯 MVP

**Goal**: Confirm `Arbor` runs in CI, avoids CUDA, and generates non-empty `tree.json` and logs.

**Independent Test**: Execute `src/run_arbor.py` with `dashboard_demo` task; verify exit code 0 and file sizes > 0.

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Contract test: Verify `tree.json` exists and is non-empty:
      - Test function: `test_tree_exists_and_nonempty`.
      - Assertion: `os.path.getsize("results/tree.json") > 0`.
      - **Verify**: Run `pytest tests/test_artifacts.py::test_tree_exists_and_nonempty`.

- [X] T014 [P] [US1] Contract test: Verify `eval_results.json` exists and is non-empty:
      - Test function: `test_eval_results_exists_and_nonempty`.
      - Assertion: `os.path.getsize("results/eval_results.json") > 0`.
      - **Verify**: Run `pytest tests/test_artifacts.py::test_eval_results_exists_and_nonempty`.

- [X] T015 [P] [US1] Integration test: Verify no CUDA import errors:
      - Test function: `test_no_cuda_import`.
      - Assertion: Import `torch` and check `torch.cuda.is_available()` is False; no `ImportError` on `torch`.
      - **Verify**: Run `pytest tests/test_cpu_only.py::test_no_cuda_import`.

### Implementation for User Story 1

- [X] T016 [US1] Configure `vendor/arbor/config.yaml` and verify:
      - Create/Update `vendor/arbor/config.yaml` with `device: cpu`, `load_in_8bit: false`.
      - **Verify**: `grep -q 'device: cpu' vendor/arbor/config.yaml` and `grep -q 'load_in_8bit: false' vendor/arbor/config.yaml`.

- [X] T017 [US1] Execute `src/run_arbor.py` with `dashboard_demo`:
      - Command: `python src/run_arbor.py --task dashboard_demo --timeout-step 300 --timeout-total 21600 --max-retries 3`.
      - **Verify**: Exit code 0; `results/tree.json` and `results/eval_results.json` created.

- [X] T018 [US1] Validate `tree.json` structure:
      - Use `jsonschema` to validate `results/tree.json` against `contracts/tree-node.schema.yaml`.
      - **Verify**: `jsonschema -i results/tree.json contracts/tree-node.schema.yaml` passes.

- [X] T019 [US1] Log resource usage:
      - Run `src/monitor_resources.py` during T017; save to `results/resource_log.json`.
      - **Verify**: `results/resource_log.json` contains `peak_memory_mb` and `total_runtime_seconds`.

**Checkpoint**: User Story 1 functional; smoke test passed; artifacts generated.

---

## Phase 4: User Story 2 - Validate Hypothesis-Tree Refinement Logic (Priority: P2)

**Goal**: Confirm HTR mechanism creates valid tree states, links evidence, and handles failures.

**Independent Test**: Inspect `tree.json` after a multi-step run; verify parent-child links and node type transitions.

### Tests for User Story 2 ⚠️

- [X] T020 [P] [US2] Contract test: Verify `Evidence` node links to a `Hypothesis` node:
      - Test function: `test_evidence_links_to_hypothesis`.
      - Assertion: Parse `results/tree.json`; find an `Evidence` node; verify its `parent_id` exists and points to a `Hypothesis` node.
      - **Verify**: Run `pytest tests/test_tree_logic.py::test_evidence_links_to_hypothesis`.

- [X] T021 [P] [US2] Contract test: Verify `Failed` node state is recorded on timeout:
      - Test function: `test_failed_node_on_timeout`.
      - Assertion: Verify `tree.json` contains a node with `status: "Failed"` or `type: "Evidence"` containing "TIMEOUT" in logs.
      - **Verify**: Run `pytest tests/test_tree_logic.py::test_failed_node_on_timeout`.

### Implementation for User Story 2

- [X] T022 [US2] Run `src/run_arbor.py` with `dashboard_demo` allowing 3+ iterations:
      - Command: `python src/run_arbor.py --task dashboard_demo --max-iterations 3 --timeout-step 300 --timeout-total 21600 --max-retries 3`.
      - **Verify**: `results/tree.json` contains at least 3 `Hypothesis` nodes.

- [X] T023 [US2] Implement wrapper logic for versioning and state:
      - Logic: In `src/run_arbor.py`, ensure `tree.json` version increments on every update (mocked if vendor doesn't). Do NOT patch vendor code.
      - **Verify**: Parse `results/tree.json`; verify `version` field increments between runs.

- [X] T024 [US2] Implement wrapper logic for timeout handling:
      - Logic: In `src/run_arbor.py`, catch `TimeoutExpired` and write `{"status": "Failed", "reason": "TIMEOUT"}` to the current node in `tree.json`. Do NOT patch vendor code.
      - **Verify**: Simulate timeout; verify `tree.json` contains a `Failed` node.

- [X] T025 [US2] Verify `tree.json` contains a "Distilled Insight" node:
      - Assertion: Find a node with `type: "Artifact"` or `type: "Evidence"` containing "Insight" or "Summary".
      - **Verify**: Manual check or script `grep -i "insight" results/tree.json`.

- [X] T026 [US2] Generate `results/tree_visualization.html` (if supported) or validate JSON structure manually:
      - If vendor supports HTML export, run it. Else, log "HTML export not supported" to `results/execution.log`.
      - **Verify**: If generated, `ls -l results/tree_visualization.html` > 0; if skipped, verify log message exists in `results/execution.log`.

**Checkpoint**: HTR logic verified; tree integrity confirmed; failure handling active.

---

## Phase 5: User Story 3 - Reproduce Paper Claims (Priority: P3)

**Goal**: Execute `algotune_knn` benchmark, compare HTR results against a Random Search baseline.

**Independent Test**: Run `algotune_knn` with HTR and Random Search; compare final scores in `results/summary.md`.

### Tests for User Story 3 ⚠️

- [X] T027 [P] [US3] Contract test: Verify `summary.md` contains both scores:
      - Test function: `test_summary_contains_scores`.
      - Assertion: `grep -q "HTR Score" results/summary.md` AND `grep -q "Baseline Score" results/summary.md`.
      - **Verify**: Run `pytest tests/test_report.py::test_summary_contains_scores`.

### Implementation for User Story 3

- [X] T028 [US3] Configure `src/run_arbor.py` for `algotune_knn` with Iris dataset:
      - Command: `python src/run_arbor.py --task algotune_knn --dataset-loader data/dataset_loader.py --dataset-name iris`.
      - Note: Uses `sklearn.datasets.load_iris()` as a CPU-feasible proxy for the paper's task.
      - **Verify**: `python src/run_arbor.py --task algotune_knn --dataset-loader data/dataset_loader.py --dataset-name iris --help` shows args.

- [X] T029 [US3] Run baseline (Random Search) and save score:
      - Command: `python src/run_arbor.py --task algotune_knn --mode baseline --dataset-loader data/dataset_loader.py --dataset-name iris`.
      - Output: Write `results/baseline_score.txt` containing a single float formatted as `%.4f` (e.g., "0.9500").
      - **Verify**: `cat results/baseline_score.txt` shows a single float.

- [X] T030 [US3] Run HTR optimization loop and save score:
      - Command: `python src/run_arbor.py --task algotune_knn --mode htr --dataset-loader data/dataset_loader.py --dataset-name iris`.
      - Output: Write `results/benchmark_score.txt` containing a single float formatted as `%.4f`.
      - **Verify**: `cat results/benchmark_score.txt` shows a single float.

- [X] T031 [US3] Update `src/generate_report.py` to calculate and log "% Improvement":
      - Logic: Read `results/benchmark_score.txt` and `results/baseline_score.txt`. Calculate `(htr - baseline) / baseline * 100`.
      - Output: Append to `results/summary.md` the line `Improvement: +X.XX%` (where X.XX is the calculated value).
      - **Verify**: `grep "Improvement:" results/summary.md` shows the calculated value.

- [X] T032 [US3] Validate `results/summary.md` against schema:
      - Verify `results/summary.md` contains `htr_score`, `baseline_score`, and `improvement_percent` fields (parsed from text).
      - **Verify**: `python -c "import re; ..."` extracts values and validates format.

**Checkpoint**: Benchmark completed; baseline comparison generated; report valid.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, cleanup, and final validation.

- [X] T033 [P] Update `docs/outputs-and-resume.md` with final artifact paths and schemas:
      - List: `results/tree.json`, `results/summary.md`, `results/resource_log.json`.
      - **Verify**: `grep -q "results/tree.json" docs/outputs-and-resume.md`.

- [X] T034 [P] Add `README.md` section explaining CPU-only constraints and how to run `src/run_arbor.py`:
      - Content: Add section `## CPU-Only Execution` with instructions on `--timeout-step` and `--timeout-total`.
      - **Verify**: `grep -q "CPU-Only Execution" README.md`.

- [X] T035 [P] Run `memory_profiler` on the full pipeline to confirm peak RAM < 7GB:
      - Command: `python -m memory_profiler src/run_arbor.py --task dashboard_demo --timeout-step 300 --timeout-total 21600 > results/memory_profile.log`.
      - Verification: `grep "Maximum memory" results/memory_profile.log` and check value < 7000 MB.
      - **Verify**: `grep "Maximum memory" results/memory_profile.log` shows value < 7000.

- [X] T036 [P] Final integration test: Run full pipeline from T001 to T032 in a clean CI environment:
      - Script: Create `./ci/validate_all.sh` containing:
        ```bash
        #!/bin/bash
        set -e
        pytest tests/
        python -m jsonschema -i results/tree.json contracts/tree-node.schema.yaml
        grep -q "Improvement:" results/summary.md
        grep -q "Maximum memory" results/memory_profile.log
        ```
      - **Verify**: `./ci/validate_all.sh` exits with code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup. **BLOCKS** all US.
- **User Stories (Phase 3-5)**: Depend on Foundational. Can run in parallel if resources allow, but sequential (P1→P2→P3) is recommended for CI.
- **Polish (Phase 6)**: Depends on all US completion.

### User Story Dependencies

- **US1 (P1)**: Must pass before US2/US3 to ensure environment stability.
- **US2 (P2)**: Depends on US1 artifact generation.
- **US3 (P3)**: Depends on US2 logic validation (tree must be functional to run complex benchmarks).

### Within Each User Story

- **Tests (T013-T015, T020-T021, T027)**: Must be written and expected to FAIL initially.
- **Implementation**: Follows test definition.
- **Validation**: Final check before moving to next story.

### Parallel Opportunities

- T003, T004, T005 (Setup/Dependencies) can run in parallel.
- T010, T011, T012 (Contracts/Data) can run in parallel.
- T013, T014, T015 (US1 Tests) can run in parallel.
- T020, T021 (US2 Tests) can run in parallel.
- T027 (US3 Test) can run in parallel with other US3 tasks.

---

## Notes

- **[P]** tasks = different files, no dependencies.
- **Real Data**: All tasks using datasets (T012, T028) use `sklearn.datasets` to ensure real, non-fabricated input.
- **CPU Constraint**: No task allows `load_in_8bit` or CUDA; all model loading defaults to `device="cpu"`.
- **Timeouts**: T008 enforces strict 300s per step and 6h total timeouts, with a max-retry limit to prevent infinite loops.
- **Fabrication Guard**: No task generates fake metrics; T029/T030 run actual baselines and HTR loops.
- **Validation**: T035 and T036 ensure resource limits and schema compliance are met.
- **Constitution**: If `constitution.md` is missing, a minimal one is generated in T001 to ensure no silent fallbacks.