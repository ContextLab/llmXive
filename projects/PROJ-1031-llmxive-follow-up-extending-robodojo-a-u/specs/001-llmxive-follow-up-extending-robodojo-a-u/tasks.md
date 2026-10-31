# Tasks: Extending RoboDojo with Symbolic Abstractions

**Inputs**: `spec.md`, `plan.md`, existing project layout, reviewer feedback, and the contracts in `specs/001-symbolic-dojo-extend/contracts/`.

The following checklist implements the smallest complete study that satisfies every functional and success‑criteria requirement while providing an early executable end‑to‑end run. Tasks are ordered to respect data flow and resource limits.

---

## Phase 0 – Project Setup & Tooling

- [~] T001a **Install linting and formatting tools**  
  - **File**: `requirements.txt` – add `ruff` and `black` (pinned versions).  
  - **Verification**: After `pip install -r requirements.txt`, `ruff --version` and `black --version` succeed.

- [~] T001 **Create project‑wide configuration and environment**  
  - **File**: `code/config.py` – defines random seeds, data paths, CPU‑memory limits, and the list of RoboDojo task IDs (18 real‑world tasks).  
  - **Verification**: Running `python -c "import code.config as cfg; assert cfg.SEED == 42"` succeeds; `cfg.TASK_IDS` contains 18 entries.

- [~] T002 **Add linting and formatting configuration** *(required – previously missing)*  
  - **Files**: `code/pyproject.toml`, `code/.ruff.toml`, `code/.black.toml`.  
  - **Verification**: `ruff --config code/.ruff.toml .` returns no errors; `black --check code/` exits with status 0.

- [X] T003 **Create data directory hierarchy (project‑owned paths only)**  
  - **Paths**: `data/raw/`, `data/interim/`, `data/processed/`, `data/final/`.  
  - **Verification**: `tree -d data` lists the four sub‑folders; no files are placed outside `data/`.

- [ ] T004 **Add verified RoboDojo dataset download script**   <!-- FAILED-IN-EXECUTION: code/utils/io.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/utils/io.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/utils/run_io_test.sh exit=1 --> <!-- FAILED-IN-EXECUTION: code/utils/io.py exit=1; code/utils/run_io_test.sh exit=1 -->
  - **File**: `code/utils/io.py` – uses `datasets.load_dataset("robodojo", split="real", streaming=True)` with checksum validation.  
  - **Verification**: Executing `python -m code.utils.io --test` streams at least one record and raises on any fetch error (no silent fallback).

---

## Phase 1 – First End‑to‑End Analysis (single‑task prototype)

- [ ] T005 **Implement CPU‑only semantic encoder**  
  - **File**: `code/models/semantic_encoder.py` – loads a frozen MobileViT (`torchvision.models.mobilenet_v3_small(pretrained=True)`), runs on `device="cpu"` with `torch.no_grad()`, outputs a 512‑dim embedding saved to `data/interim/semantic_embeddings.parquet`.  
  - **Verification**: After running `python -m code.models.semantic_encoder --task-id T001`, the parquet file contains a row with `embedding_vector` length 512 and `task_id == "T001"`.

- [ ] T006 **Map embeddings to SymbolicState with ambiguity detection (FR‑002, FR‑011)**  
  - **File**: `code/models/symbolic_state.py` – converts each embedding into a `SymbolicState` parquet row (`data/interim/symbolic_states.parquet`). If multiple candidate states have equal score, sets `mapping_confidence = "low"` and logs an `AmbiguousMapping` event.  
  - **Verification**: Running the mapper on the embedding from T005 produces a `SymbolicState` row; for an intentionally ambiguous embedding the log file `data/interim/mapping_log.txt` contains the string `AmbiguousMapping`.

- [ ] T006a **Evaluate precision and recall of embedding‑to‑SymbolicState mapping (FR‑013)**  
  - **File**: `code/analysis/mapping_evaluation.py` – loads a manually annotated ground‑truth dataset of ≥30 tasks, compares predicted SymbolicState predicates to ground truth, computes precision and recall, and writes results to `data/interim/mapping_metrics.parquet` conforming to `contracts/symbolic_state.schema.yaml`.  
  - **Verification**: After execution, the parquet file contains `precision` and `recall` columns within `[0,1]`.

- [ ] T007 **Implement A* symbolic planner (primary) with fallback MCTS (FR‑003)**  
  - **File**: `code/services/planner.py` – reads a `SymbolicState`, runs A* (edge cost = 1) to generate an `ActionSequence` parquet row (`data/interim/action_sequences.parquet`). If A* fails within 60 s, automatically switches to MCTS with the same node limit.  
  - **Verification**: For the prototype task, `planner.py` creates an `ActionSequence` whose `planning_time_ms` ≤ 60000 and `planner_type` is either `"A*"` or `"MCTS"`.

- [ ] T008 **Record planning compute metrics (FR‑007, FR‑017)**  
  - **File**: `code/services/metrics.py` – called by `planner.py` to append a `ComputeMetric` row (`data/interim/compute_metrics.parquet`) with phase `"Planning"`.  
  - **Verification**: After T007, the parquet file contains a row with `phase == "Planning"` and `cpu_usage_pct` ≤ 100, `memory_mb` ≤ 6000.

---

## Phase 2 – Full Study, Real‑World Execution & Controls

- [ ] T009 **Implement deterministic Oracle executor (FR‑010, US‑4)**  
  - **File**: `code/services/oracle_executor.py` – rule‑based verifier that checks each step of an `ActionSequence` against the ground‑truth task graph without invoking any physics simulation. Writes success/failure flags to `data/interim/oracle_results.parquet`.  
  - **Verification**: Running the Oracle on the `ActionSequence` from T007 produces a parquet file with a `success` column; for a known feasible sequence the flag is `True`.

- [ ] T009a **Sim‑to‑Real adapter / fine‑tuning protocol (FR‑009)**  
  - **File**: `code/services/sim_to_real_adapter.py` – loads a small set of real‑world video recordings, fine‑tunes the pre‑trained RoboDojo low‑level controller (using a lightweight 8‑bit quantized model) on the GPU escape hatch, and saves the adapted weights to `code/models/real_controller.pt`.  
  - **Verification**: After running the adapter, the adapted model file exists and a log entry confirms improvement in validation loss on a held‑out real‑world subset.

- [ ] T010 **Implement real‑world executor with failure‑mode logging (FR‑004, FR‑006, FR‑012, US‑2)**  
  - **File**: `code/services/real_executor.py` – sends sub‑goals to the robot via ROS, measures pose/orientation deviation, and writes an `ExecutionOutcome` row to `data/interim/execution_logs.parquet`. Distinguishes `"Planner Infeasibility"` vs. `"Controller Execution Failure"` and triggers replanning from the last successful sub‑goal when possible.  
  - **Verification**: After executing a single task, `execution_logs.parquet` contains at least one row with `outcome` = `"Failure"` and a non‑null `failure_mode`. A successful run yields `failure_mode == "None"`.

- [ ] T011 **Log execution compute metrics (FR‑007, FR‑017)**  
  - **File**: `code/services/metrics.py` (extended) – records a `ComputeMetric` row for phase `"Execution"` and a `"Total"` row per task, written to `data/interim/compute_metrics.parquet`.  
  - **Verification**: After T010, the parquet file contains three rows for the task (`Planning`, `Execution`, `Total`) with non‑negative CPU/memory values.

- [ ] T012 **Run baseline Neural Policy on the 18 real‑world tasks (FR‑017, SC‑001)**  
  - **File**: `code/benchmarks/baseline_runner.py` – loads the published RoboDojo weights, executes each task, and stores binary outcomes in `data/interim/baseline_results.parquet`.  
  - **Verification**: The parquet file has 18 rows, each with columns `task_id`, `outcome` (`Success`/`Failure`), and `source == "NeuralPolicy"`.

- [ ] T012a **Collect baseline GPU compute metrics (FR‑017)**  
  - **File**: `code/benchmarks/baseline_gpu_metrics.py` – runs the same baseline on a Kaggle GPU (8‑bit MobileViT, int8 quantization), records CPU cycles, GPU memory, and wall‑clock time, and writes `ComputeMetric` rows with phase `"BaselineGPU"` to `data/interim/compute_metrics.parquet`.  
  - **Verification**: After execution, the parquet file contains rows with `phase == "BaselineGPU"` and numeric metrics.

- [ ] T013 **Perform statistical analysis (FR‑005, FR‑014, FR‑015, FR‑016, US‑3)**  
  - **File**: `code/analysis/stats.py` – loads `baseline_results.parquet`, `execution_logs.parquet`, `oracle_results.parquet`, and `baseline_gpu_metrics.parquet`.  
    1. Executes an **exact McNemar test** on paired binary outcomes (Symbolic vs. Neural) and writes `p_value` and `odds_ratio` to `data/final/mcnemar_report.json`.  
    2. Computes **observed statistical power** for the McNemar test using the actual number of discordant pairs and records it in `data/final/power_analysis.txt`; verification checks that the reported power ≥ 0.80.  
    3. Calculates **effect‑size measures** (odds ratio, rank‑biserial correlation) and stores them alongside the report.  
  - **Verification**: After execution, `mcnemar_report.json` contains keys `"p_value"` and `"odds_ratio"`; `power_analysis.txt` contains a line like “Observed power = 0.82 (≥ 0.80)”.

- [ ] T013a **Evaluate Neural Policy using deterministic Oracle (FR‑016)**  
  - **File**: `code/analysis/neural_oracle_evaluation.py` – runs the Neural Policy action sequences through `oracle_executor.py`, records outcomes in `data/interim/neural_oracle_results.parquet`, and adds these to the McNemar comparison.  
  - **Verification**: The parquet file contains 18 rows with `outcome` and `task_id`; the analysis script includes them in the final statistical report.

- [ ] T014 **Ablation study over state‑representation granularity (FR‑008, US‑3)**  
  - **File**: `code/analysis/ablation.py` – runs the full pipeline (T005‑T010) twice: once with `graph_type = "Full Affordance Graph"` and once with `graph_type = "Simplified Connectivity Graph"` (controlled via a CLI flag). Produces two parquet result sets (`ablation_full.parquet`, `ablation_simplified.parquet`).  
  - **Aggregates** success rate, compute overhead, and catastrophic‑failure rate for each graph type, writes a single `AblationResult` row per configuration to `data/interim/ablation_results.parquet` conforming to `ablation_result.schema.yaml`.  
  - **Verification**: The output parquet contains exactly two rows, each with `graph_type` matching the flag and numeric fields within the `[0,1]` range where appropriate. The verification now references **FR‑017** for baseline GPU metrics.

- [ ] T015 **Generate final markdown report (SC‑001‑SC‑008)**  
  - **File**: `data/final/statistical_report.md`. The report includes:  
    * Success‑rate comparison (symbolic vs. neural vs. oracle)  
    * McNemar test outcome, p‑value, odds‑ratio, and observed power (≥ 0.80)  
    * Compute‑overhead reduction percentages (CPU cycles, memory, wall‑clock) with citations to the GPU baseline collected on Kaggle  
    * Ablation results table (full vs. simplified graph)  
    * Physics Fidelity Gap (oracle − real‑world)  
    * All effect‑size measures and a brief discussion of SC‑005 (catastrophic‑failure ≤ 5 %).  
  - **Verification**: Rendering the markdown locally shows all tables; a CI step runs `python -c "import markdown, pathlib; assert pathlib.Path('data/final/statistical_report.md').read_text()"` without error.

---

## Phase 3 – Reproducibility, Validation & Handoff

- [ ] T016 **Validate full pipeline reproducibility**  
  - **Action**: Run `python -m code.main --run-all --tasks data/final/statistical_report.md` on a fresh GitHub Actions runner (CPU‑only).  
  - **Verification**: The run completes within the wall‑clock limit of 4 hours, all parquet files are regenerated, and the final report matches the previously generated one (hash comparison).

- [ ] T017 **Cross‑check schema compliance for all parquet artifacts**  
  - **File**: `code/tests/test_schema_validation.py` – uses `jsonschema` to validate each parquet file against its contract in `specs/001-symbolic-dojo-extend/contracts/`.  
  - **Verification**: `pytest code/tests/test_schema_validation.py -q` passes with 0 failures.

- [ ] T018 **Document quickstart for external reviewers**  
  - **File**: `quickstart.md` – provides a one‑command reproducibility checklist, lists required hardware (CPU‑only runner) and the optional Kaggle GPU step for baseline metrics.  
  - **Verification**: Executing the command listed in `quickstart.md` on a fresh runner reproduces the entire study end‑to‑end.

---

### Dependency Map (selected)

| Spec Requirement | Satisfying Task(s) |
|------------------|--------------------|
| FR‑001, FR‑002, FR‑011 | T005, T006 |
| FR‑003, FR‑012 | T007, T010 |
| FR‑004, FR‑009 | T010, T009a |
| FR‑005, FR‑014, FR‑015, FR‑016 | T013, T013a |
| FR‑006 | T010 |
| FR‑007, FR‑017 | T008, T011, T012, T012a |
| FR‑008 | T014 |
| FR‑010, SC‑006 | T009, T013 |
| FR‑013 | T006a |
| FR‑018 (baseline GPU metrics) **removed**; use FR‑017 | T012a |
| SC‑001‑SC‑008 | T013‑T015 |
| US‑1‑US‑4 | T005‑T010, T009, T014 |

--- 

**Checkpoint**: After completing Phase 0–Phase 2 the project can run an end‑to‑end symbolic planning run on a single task, produce real `SemanticEmbedding`, `SymbolicState`, `ActionSequence`, and a logged `ExecutionOutcome`. Phase 3 confirms that the entire workflow is fully reproducible and ready for hand‑off to the paper pipeline.  
