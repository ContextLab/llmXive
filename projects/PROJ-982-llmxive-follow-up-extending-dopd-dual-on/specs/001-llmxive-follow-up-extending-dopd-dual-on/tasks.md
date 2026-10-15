# Tasks: llmXive follow‑up “DOPD: Dual On‑policy Distillation” (discrete MDP)

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-llmxive-follow-up-extending-dopd-dual-on/contracts/`, prior rejected‑task feedback (T022, T023, T025, T030, T066).

--- 

## Phase 0 – Core components

- [ ] T001 [P] [US1] **Scaffold repository and create `requirements.txt`** — `code/requirements.txt`, `code/__init__.py`  
  - Creates project directory layout, writes a pinned `requirements.txt` (numpy, scipy, pyyaml, pytest) and an empty `code/__init__.py` so that the package is importable.  
  - **Verification**: `pip install -r code/requirements.txt` succeeds; `requirements.txt` exists at the path.

- [ ] T018 [P] [US1] **Implement `PrivilegedGridEnv`** — `code/env/privileged_grid.py`  
  - Pure‑Python grid MDP (≤10×10) with full state `(x, y, h)`, student observation `(x, y)`, teacher observation `(x, y, h)`. Provides `reset(seed)` and `step(action)`. Enforces grid‑size limit, raises `ValueError` otherwise.  
  - **Verification**: unit tests `code/tests/unit/test_env.py` confirm hidden variable visibility, reproducibility across seeds, and optimal‑action dependence on `h`.

- [ ] T019 [P] [US1] **Implement Teacher oracle** — `code/agents/teacher.py`  
  - Runs value‑iteration on the full state space of `PrivilegedGridEnv` (γ = 0.99, tolerance < 1e‑6) and caches the optimal Q‑table **in memory** for use by training loops. No persistent file is written.  
  - **Verification**: `code/tests/unit/test_teacher.py` checks that the oracle returns the optimal action for a set of sampled full states.

- [ ] T020 [P] [US1] **Implement Student tabular Q‑learner** — `code/agents/student.py`  
  - Learns over observable state `(x, y)` using ε‑greedy policy, `update(observation, action, td_error)`. Stores Q‑table in memory.  
  - **Verification**: `code/tests/unit/test_student.py` validates TD‑update correctness and that the student cannot see `h`.

- [ ] T021 [P] [US1] **Implement Seed manager** — `code/utils/seed_manager.py`  
  - Generates three disjoint seed ranges internally: training 0‑49, evaluation 50‑99, baseline 1000‑1099. Provides functions `get_training_seeds()`, `get_evaluation_seeds()`, `get_baseline_seeds()`. No file is written.  
  - **Verification**: `code/tests/unit/test_seed_manager.py` confirms correct ranges and non‑overlap.

## Phase 1 – Logging, baseline, and training regimes

- [ ] T002 [P] [US2] **Implement `TrainingLogger` writing to `data/raw/training_log.jsonl`** — `code/utils/logging.py`  
  - Opens/append to the exact file on init, provides `log_step(dict)` that emits a JSON line conforming to `contracts/training_log.schema.yaml`.  
  - **Verification**: `code/tests/unit/test_logging.py` writes a dummy row and asserts the file exists, is parseable, and validates against the schema.

- [ ] T003 [P] [US2] **Implement training regimes (DOPD & Uniform)** — `code/training/dopd_distillation.py`, `code/training/uniform_distillation.py`  
  - Uses an internal `BaselineEstimator` (produced by T026) to obtain `V_baseline(s)`.  
  - DOPD computes advantage gap via `calculate_advantage_gap` and dynamic λ via `calculate_dynamic_lambda` (see T023).  
  - Uniform uses fixed λ = 1.0. Both regimes log every step through `TrainingLogger`.  
  - **Verification**: unit tests `code/tests/unit/test_dopd.py` and `code/tests/unit/test_uniform.py` validate loss computation, λ behavior, and schema‑valid log lines.

- [~] T022 [P] [US2] **Calculate advantage gap** — helper in `code/training/utils.py`  
  - `calculate_advantage_gap(teacher_q, v_baseline)` returns `Q_teacher(s,a) − V_baseline(s)` safely handling missing entries.  
  - **Verification**: covered by T003 tests.

- [ ] T023 [P] [US2] **Calculate dynamic λ and fallback handling** — helper in `code/training/utils.py`   <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  - Implements min‑max normalization when `max‑min < 0.1`, sigmoid scaling otherwise, and a sparse‑signal guard that returns λ = 1.0 with `"lambda_switch": "fallback"` logged.  
  - **Verification**: exercised by T003 tests and integration test T006.

- [ ] T024 [P] [US2] **Uniform distillation loop (fixed λ = 1.0)** — `code/training/uniform_distillation.py` (called by T003)  
  - Provides a thin wrapper that calls the generic distillation step with λ = 1.0.  
  - **Verification**: part of T003 unit suite.

- [ ] T025 [P] [US2] **Extended per‑step training metrics logging** — `code/utils/metric_logger.py`  
  - Writes `training_accuracy` and `convergence_step` to `data/raw/training_metrics.jsonl` conforming to a newly added `contracts/training_metrics.schema.yaml`.  
  - **Verification**: `code/tests/unit/test_metric_logger.py` checks that after a short run the file contains valid JSON lines with required fields.

- [ ] T026 [P] [US2] **Implement `BaselineEstimator` (Monte‑Carlo random‑policy)** — `code/agents/baseline_estimator.py`  
  - Runs Monte‑Carlo simulations using the baseline seed range (provided by T021) to estimate `V_baseline(s)` for every observable state in memory. Converges when std‑dev < 0.01 over 100 consecutive batches. No persistent file is written.  
  - **Verification**: `code/tests/unit/test_baseline.py` asserts convergence criteria and that the estimator returns a dictionary mapping observations to baseline values.

- [ ] T006 [P] [US3] **Integration tests for λ‑switch and entropy behavior** — `code/tests/integration/test_lambda_switch.py`  
  - Executes DOPD on a deliberately degenerate MDP (advantage gaps < 0.1) and asserts:  
    (a) at least one `"lambda_switch": "minmax"` entry in `data/raw/training_log.jsonl`;  
    (b) DOPD student entropy exceeds Uniform student entropy under low‑gap conditions (SC‑004);  
    (c) all log lines validate against `contracts/training_log.schema.yaml`.  
  - **Verification**: `pytest code/tests/integration/` passes.

## Phase 2 – Experiment execution

- [ ] T004 [P] [US3] **First end‑to‑end small run** — `code/run_experiment.py --seeds 2`  
  - Orchestrates a 2‑seed × 2‑regime sanity run on the real environment, evaluates each student with `h` visible and masked, computes `accuracy_unmasked`, `accuracy_masked`, `performance_drop`, `convergence_steps`, `mean_entropy`, and writes rows to `data/processed/results_small.csv` conforming to `contracts/experiment-result.schema.yaml`. All steps log to `data/raw/training_log.jsonl`.  
  - **Verification**: command exits 0, produces a CSV with 4 rows that validate, and log file grows by ≥ 4 lines.

- [ ] T005 [P] [US3] **Full 50‑seed experiment execution** — `code/run_experiment.py --mode full`  
  - Loops over both regimes × training seeds 0‑49, evaluation seeds 50‑99 (masked), aggregates rows into `data/processed/results_uniform.csv` and `data/processed/results_dopd.csv` matching the experiment‑result schema.  
  - **Verification**: command exits 0; both CSVs contain exactly 50 rows; log file contains entries for all 100 runs; each CSV row validates.

- [ ] T007 [P] [US3] **Statistical analysis and summary** — `code/analysis/stats.py`  
  - Loads both CSVs, runs a one‑tailed Mann‑Whitney U test (`alternative='greater'`) on **masked generalization accuracy**, computes Cliff’s Δ effect size, sets `is_exploratory` when effect size < 0.5, computes coefficient of variation, writes `data/processed/statistical_summary.json` conforming to `contracts/statistical-summary.schema.yaml`.  
  - **Verification**: unit test `code/tests/unit/test_stats.py` with synthetic CSVs confirms correct p‑value and schema compliance.

- [ ] T014 [P] **Evaluate acceptance condition (drop ≤ 20 % of Uniform)** — `code/analysis/acceptance_check.py`  
  - Loads CSVs, computes average performance‑drop per regime, verifies `drop_dopd ≤ 0.2 × drop_uniform`, writes boolean result to `data/processed/acceptance_check.json`.  
  - **Verification**: unit test asserts JSON contains fields `pass`, `dopd_drop`, `uniform_drop`, `ratio`.

- [ ] T015 [P] **Compute checksums for all data artifacts** — `code/utils/checksum_generator.py`  
  - Walks `data/` directory, writes `data/checksums.json`.  
  - **Verification**: after any data‑generation step, manifest contains an entry for each file.

## Phase 3 – Documentation and handoff

- [ ] T010 **Methods/results account and reproducible quickstart** — `specs/001-llmxive-follow-up-extending-dopd-dual-on/quickstart.md` and `research.md`  
  - Documents the single reproduction command:  
    ```bash
    pip install -r code/requirements.txt
    python code/run_experiment.py --mode full && python code/analysis/stats.py && python code/analysis/acceptance_check.py
    ```  
  - Describes seed manifest location (generated at runtime), artifact locations, and cites only values present in `statistical_summary.json`, `results_all.csv`, and the CSV result files. No hidden ordering; the task is not marked [P] because it depends on prior artifacts.  
  - **Verification**: re‑running the documented commands from a clean checkout reproduces all artifacts; `research.md` contains only citations to actual output values.

- [ ] T013 [P] **Create CLI entry point `main.py`** — `code/main.py`  
  - Provides `python -m code.main --mode full` wrapper.  
  - **Verification**: command runs full experiment successfully.

- [ ] T017 [P] **Finalize result summary for paper handoff** — `specs/001-llmxive-follow-up-extending-dopd-dual-on/research_summary.md`  
  - Summarizes key metrics, effect size, exploratory flag, and references all generated artifacts (`statistical_summary.json`, `results_uniform.csv`, `results_dopd.csv`, `acceptance_check.json`).  
  - **Verification**: contains only numbers that appear in the listed JSON/CSV artifacts.

--- 

### Notes
- All generated artifacts now correspond to schemas listed in `specs/001-llmxive-follow-up-extending-dopd-dual-on/contracts/`, satisfying the single‑source‑of‑truth requirement.
- Figures and per‑seed JSON result files have been removed to keep the data model consistent; aggregated CSVs provide the necessary quantitative evidence.