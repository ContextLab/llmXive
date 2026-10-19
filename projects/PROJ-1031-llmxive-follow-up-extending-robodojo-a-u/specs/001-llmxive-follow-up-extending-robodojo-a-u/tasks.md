# Tasks: Extending RoboDojo with Symbolic Abstractions

**Input**: Design documents from `/specs/001-symbolic-dojo-extend/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`  

## Phase 0 – Project Setup & Baseline Infrastructure  

- [ ] T001a [P] Create `code/src/__init__.py` – makes the `code/src` package importable.  
- [ ] T001b [P] Create `code/tests/__init__.py` – makes the test package importable.  
- [ ] T001c [P] Create data directories `code/data/{raw,interim,processed,final}`.  
  - **Path**: `code/data/` (sub‑folders)  
  - **Verification**: Run `tree -d code/data` and confirm the four sub‑folders exist.  
- [ ] T001d [P] Initialise Python 3.11 virtual environment and write `code/requirements.txt` (torch‑cpu, scikit‑learn, networkx, pandas, datasets, opencv‑python, pyyaml).  
- [ ] T001e [P] Add `code/src/config.py` with project‑wide constants (dataset IDs, seeds, RAM limits, tolerances, etc.).  
- [ ] T002 [P] Configure linting (ruff) and formatting (black) tools.  
  - **Path**: `code/pyproject.toml`, `code/.ruff.toml` (and optional `code/.black.toml`).  
  - **Verification**: `ruff --version` and `black --check .` run without errors.  
- [ ] T003 [P] Implement `code/src/data_loader.py` to stream RoboDojo parquet files via `datasets.load_dataset(..., streaming=True)`.  
  - **Verification**: Script runs and yields at least one record; failure to open the real source raises an exception.  

## Phase 1 – Schema & Contract Foundations  

- [ ] T005a [P] Create `specs/001-symbolic-dojo-extend/contracts/symbolic_state.schema.yaml`.  
- [ ] T005b [P] Create `specs/001-symbolic-dojo-extend/contracts/execution_outcome.schema.yaml`.  
- [ ] T005c [P] Create `specs/001-symbolic-dojo-extend/contracts/compute_metric.schema.yaml`.  
- [ ] T005d [P] Create `specs/001-symbolic-dojo-extend/contracts/ablation_result.schema.yaml`.  

## Phase 2 – Baseline Reference Execution  

- [ ] T000 [US2] Run the original RoboDojo Neural Policy on all 18 real‑world tasks and store binary outcomes.  
  - **Path**: `data/interim/baseline_results.parquet`  
  - **Verification**: Parquet file contains 18 rows with columns `task_id`, `outcome`, `source` (`Real` or `Sim‑Baseline`).  

## Phase 3 – Contract Tests for Data Models  

- [ ] T006a [P] Write `code/tests/contract/test_symbolic_state.py` to validate `SymbolicState` against its JSON‑Schema.  
- [ ] T006b [P] Write `code/tests/contract/test_execution_outcome.py` to validate `ExecutionOutcome` against its JSON‑Schema.  
- [ ] T006c [P] Write `code/tests/contract/test_compute_metric.py` to validate `ComputeMetric` against its JSON‑Schema.  
- [ ] T006d [P] Write `code/tests/contract/test_ablation_result.py` to validate `AblationResult` against its JSON‑Schema.  

## Phase 4 – User Story 1: CPU‑Tractable Symbolic Planner  

- [ ] T013 [US1] Implement `code/src/vision_encoder.py` using a frozen MobileViT (CPU‑only) to produce `SemanticEmbedding` parquet rows.  
- [ ] T015 [US1] Implement `code/src/planner.py` with an A* algorithm that outputs an `ActionSequence` parquet file.  
- [ ] T016 [US1] Add validation in `planner.py` to ensure each generated step respects object affordances defined in the input `SymbolicState`.  
- [ ] T017 [US1] Log planning time per task and enforce the ≤ 60 s bound; raise `PlanningTimeoutError` if exceeded.  
- [ ] T022 [US1] Add memory‑monitoring in `planner.py` to abort with `ResourceLimitExceeded` if RAM usage > 6 GB, and log the event to `data/interim/compute_metrics.parquet`.  

## Phase 5 – User Story 2: Real‑World Execution Validation  

- [ ] T021 [US2] Implement `code/src/executor.py` to send `ActionSequence` commands to the robot via ROS (`/robot/cmd_pose`).  
- [ ] T023 [US2] Add pose‑deviation (`≤ 5 cm`) and orientation‑deviation (`≤ 15°`) checks; record a binary `ExecutionOutcome`.  
- [ ] T024 [US2] Implement failure‑detection logic in `executor.py` that distinguishes **Planner Infeasibility** vs. **Controller Execution Failure** and writes each event to `data/interim/execution_logs.parquet`.  
  - **Path**: `data/interim/execution_logs.parquet` (schema `execution_outcome.schema.yaml`).  
  - **Verification**: After running on at least one task, the parquet file contains rows with `failure_mode` populated appropriately.  
- [ ] T025 [US2] Add replanning support: if `replan_support` is true in the current `SymbolicState`, re‑run the A* planner from the last successful sub‑goal; otherwise log a hard failure.  
- [ ] T026 [US2] Log all execution metrics (CPU %, memory MB, wall‑clock seconds) for each task phase to `data/interim/compute_metrics.parquet`.  
  - **Verification**: Parquet file contains rows for phases `Planning`, `Execution`, `Total` with matching `task_id` entries.  

## Phase 6 – User Story 4: Physics‑Fidelity Isolation Control  

- [ ] T037 [US4] Implement `code/src/oracle_executor.py` using a deterministic rule‑based verifier (no physics simulation) that checks each symbolic action against the ground‑truth task graph.  
  - **Path**: `code/src/oracle_executor.py`  
  - **Verification**: Running on a sample `ActionSequence` returns a success flag without invoking any simulator.  
- [ ] T038 [US4] Execute all symbolic plans against the Oracle and store results in `data/interim/oracle_results.parquet`.  
- [ ] T041 [US4] Compute the **Physics Fidelity Gap** (Oracle success rate − Real‑World success rate) and write the scalar value to `data/interim/physics_fidelity_gap.txt`.  

## Phase 7 – User Story 3: Comparative Statistical Analysis  

- [ ] T032 [US3] Implement `code/src/stats_analysis.py` to load baseline results, symbolic execution logs, and Oracle results.  
- [ ] T033 [US3] Perform an exact **McNemar** test (α = 0.05) on paired binary outcomes (Symbolic vs. Neural Policy) and output p‑value and odds‑ratio.  
- [ ] T033b [US3] Compute the **rank‑biserial correlation** effect size for the Wilcoxon signed‑rank test (included for completeness).  
- [ ] T033c [US3] Conduct a statistical **power analysis** targeting ≥ 0.80 power for a medium effect size (Cohen’s h = 0.5) with N = 18; write the narrative to `data/final/power_analysis.txt`.  
- [ ] T034 [US3] Calculate percentage reduction in compute overhead (CPU cycles, memory, wall‑clock) relative to the GPU baseline (collected on Kaggle) and store in `data/interim/compute_overhead.parquet`.  
- [ ] T035 [US3] Generate a concise markdown report (`data/final/statistical_report.md`) that states whether the null hypothesis is rejected, includes effect‑size measures, and cites the Wilcoxon test (Wilcoxon 1945).  
- [ ] T036 [US3] Compute the **catastrophic failure rate** (events labelled `Planner Infeasibility`, `Controller Execution Failure`, `Timeout`, or `Hardware Error`) and assert it ≤ 5 % (SC‑005); add Pass/Fail flag to the report.  

## Phase 8 – Ablation Study (State‑Representation Granularity)  

- [ ] T042 [US3] Extend `code/src/state_mapper.py` with a **Full Affordance Graph** mode (all predicates and affordances).  
- [ ] T043 [US3] Extend `code/src/state_mapper.py` with a **Simplified Connectivity Graph** mode (only connectivity predicates).  
- [ ] T044a [US3] Orchestrate the full pipeline (embedding → planner → executor) twice: once with Full Graph, once with Simplified Graph.  
- [ ] T044b [US3] Store the Full‑Graph run results in `data/interim/ablation_full.parquet`.  
- [ ] T044c [US3] Store the Simplified‑Graph run results in `data/interim/ablation_simplified.parquet`.  
- [ ] T044d [US3] Compute comparative metrics (success rate, compute overhead, catastrophic‑failure rate) and write them to `data/interim/ablation_results.parquet` conforming to `ablation_result.schema.yaml`.  

## Phase N – Polish, Documentation & Cross‑Cutting Concerns  

- [ ] T046a [P] Update `README.md` with installation steps, usage examples, and project‑structure overview.  
- [ ] T046b [P] Add Sphinx autodoc configuration and generate API docs for `planner.py` and `state_mapper.py` under `docs/`.  
- [ ] T046c [P] Expand `CONTRIBUTING.md` with coding‑standards, PR‑template, and review checklist.  
- [ ] T047 [P] Perform code cleanup in `code/src/` (remove dead imports, rename ambiguous variables, extract helpers).  
- [ ] T048 [P] Optimise `data_loader.py` streaming latency by batching records and pre‑fetching shards.  
- [ ] T049 [P] Add edge‑case unit tests: `test_ambiguous_embeddings.py` (checks `AmbiguousMapping` handling) and `test_mid_sequence_failure.py` (verifies replanning logic).  
- [ ] T050 [P] Validate `quickstart.md` by running `python -m code.main --validate-quickstart` on a CPU‑only runner; ensure all steps complete within the documented time bounds.  

---

### Dependency Map (selected)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑002, FR‑011 | T013, T014, T006a‑d |
| FR‑003, FR‑012 | T015, T016, T024, T025 |
| FR‑004, FR‑009 | T021, T023, T010 (controller adapter) |
| FR‑005, FR‑014, FR‑015 | T032‑T036 |
| FR‑007, FR‑017 | T034, T048 |
| FR‑008 | T042‑T044d |
| FR‑010, SC‑006 | T037‑T041 |
| FR‑013 | T006a‑d (validation) |
| SC‑001‑SC‑008 | All analysis tasks (T032‑T036, T044d) |

--- 

**Checkpoint**: After completing Phase 0–Phase 2 the project can run an end‑to‑end symbolic planning run on a single task, produce a `SemanticEmbedding`, a `SymbolicState`, an `ActionSequence`, and a logged `ExecutionOutcome`. Subsequent phases expand to full‑scale evaluation, statistical comparison, and ablation.
