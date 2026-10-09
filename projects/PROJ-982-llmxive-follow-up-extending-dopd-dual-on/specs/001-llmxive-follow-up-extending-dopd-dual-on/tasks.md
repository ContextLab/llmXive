# Tasks: llmXive follow‑up “DOPD: Dual On‑policy Distillation” (discrete MDP)

**Inputs**: `spec.md`, `plan.md`, existing `code/` skeleton, contracts in `specs/001-llmxive-follow-up-extending-dopd-dual-on/contracts/`.

The list groups related work into the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑008) and success‑criterion (SC‑001 – SC‑005).  
All tasks are unchecked; each will produce a real artifact that can be validated by the automated verifier.

---

## Phase 0 – Project scaffolding & reproducibility utilities  

- [ ] T001 [P] **Create repository layout & seed manifest**  
  - Files/paths: `code/`, `code/env/`, `code/agents/`, `code/training/`, `code/analysis/`, `code/utils/`, `data/raw/`, `data/processed/`, `requirements.txt`, `code/utils/seed_manager.py` (writes `data/seed_manifest.json`).  
  - Actions: make directories, add empty `__init__.py` in each package, pin exact versions of `numpy`, `scipy`, `pytest` in `requirements.txt`, implement `seed_manager` that records three disjoint ranges – train 0‑49, eval 50‑99, baseline 1000‑1099 – and asserts no overlap.  
  - **Verification**: `tree` shows all directories, `requirements.txt` exists, `python -c "import json; json.load(open('data/seed_manifest.json'))"` succeeds and the three ranges are disjoint.

---

## Phase 1 – Discrete “privilege‑illusion” MDP and agents  

- [ ] T002 [US1] **Implement `PrivilegedGridEnv`** – `code/env/privileged_grid.py`  
  - Grid size ≤ 10×10, state `(x, y, h)`, student observation `(x, y)` only, teacher observation `(x, y, h)`.  
  - `reset(seed)` and `step(action)` raise `RuntimeError` if `h` appears in the student observation.  
  - **Verification**: unit tests in `code/tests/unit/test_env.py` (`test_teacher_student_observation_spaces`, `test_optimal_action_dependency`, `test_seed_consistency`) all pass.

- [ ] T003 [US1] **Implement Teacher oracle** – `code/agents/teacher.py`  
  - Uses value‑iteration (γ = 0.99, convergence < 1e‑6) on the full state space, caches the optimal Q‑table to `data/processed/teacher_q.npy`.  
  - **Verification**: test `test_teacher_optimality` confirms that for a state where `h` determines the optimal action, the teacher’s `act(full_state)` returns that action.

- [ ] T004 [US1] **Implement Student tabular Q‑learner** – `code/agents/student.py`  
  - Learns from `(x, y)` only, stores Q‑table of shape `(grid_x, grid_y, n_actions)`.  
  - Provides `update(observation, action, td_error)` and `policy(observation)` (ε‑greedy).  
  - **Verification**: `test_student_update` checks that a TD‑error call modifies the correct Q‑entry and that `policy` respects ε‑greedy.

---

## Phase 2 – Training infrastructure, baseline, and distillation regimes  

- [ ] T005 [US2] **Baseline estimator (V‑baseline)** – `code/agents/baseline_estimator.py`  
  - Runs Monte‑Carlo episodes with a uniform‑random policy (seed range 1000‑1099) until the standard deviation of returns < 0.01 for 100 consecutive batches.  
  - Writes per‑observable‑state values to `data/processed/v_baseline.json`.  
  - **Verification**: script exits with status 0, file exists, and `np.std(returns[-100:]) < 0.01`.

- [ ] T006 [US2] **TrainingLogger** – `code/utils/logging.py`  
  - On first import creates **`data/raw/training_log.jsonl`** and writes a single line containing the JSON‑Schema header comment (for human reference).  
  - Provides `log_step(**kwargs)` that appends a JSON line with the required fields: `seed`, `regime`, `step`, `episode`, `loss`, `entropy`, `expected_advantage_gap` (nullable), `reward`, `convergence_step`, `lambda` (distillation weight).  
  - **Verification**: after a dummy call `TrainingLogger().log_step(seed=0, regime="test", step=0, episode=0, loss=0.0, entropy=0.0, expected_advantage_gap=None, reward=0.0, convergence_step=0, lambda=1.0)`, the file exists, contains a valid JSON line, and passes validation against `contracts/training_log.schema.yaml`.

- [ ] T007 [US2] **DOPD training loop** – `code/training/dopd_distillation.py`  
  - Loads teacher Q‑table (T003) and V‑baseline (T005).  
  - For each training step computes `adv_gap = Q_teacher(s,a) – V_baseline(s)`.  
  - **Dynamic λ**:  
    1. Collects `adv_gap` values over the current episode batch.  
    2. If `max – min < 0.1`, performs min‑max normalization `λ = (gap – min) / (max – min)` and logs a `"lambda_switch": "minmax"` event.  
    3. Otherwise applies sigmoid `λ = 1 / (1 + exp(-gap))`.  
    4. Guard division by zero with `epsilon=1e‑8`; on error set `λ = 1.0` and log `"lambda_switch": "fallback"` .  
  - Calls `TrainingLogger.log_step` each step, recording `expected_advantage_gap` and the computed `lambda`.  
  - **Verification**: unit test `tests/unit/test_dopd.py` forces a low‑gap batch (mocked `adv_gap` array) and asserts that a log line contains `"lambda_switch": "minmax"` and that `lambda` lies in `[0,1]`. The test also checks that `training_log.jsonl` grew by at least one line.

- [ ] T008 [US2] **Uniform distillation loop** – `code/training/uniform_distillation.py`  
  - Mirrors DOPD code but uses fixed `λ = 1.0` for every step; still logs through `TrainingLogger`.  
  - **Verification**: `tests/unit/test_uniform.py` runs a short episode and asserts that every logged line has `"lambda": 1.0` and no `"lambda_switch"` field.

- [ ] T009 [US2] **Integration test for logging & λ‑switch** – `code/tests/integration/test_logging_and_lambda.py`  
  - Executes a short DOPD run on a tiny 3×3 grid where `adv_gap` is deliberately < 0.1, then checks `data/raw/training_log.jsonl` for at least one entry with `"lambda_switch": "minmax"` and correct schema fields. Also runs Uniform run and checks that no `"lambda_switch"` appears.  
  - **Verification**: pytest passes; `training_log.jsonl` contains the expected entries.

---

## Phase 3 – Full experimental pipeline, aggregation, and statistical analysis  

- [ ] T010 [US3] **Experiment orchestrator** – `code/scripts/run_experiment.py`  
  - Reads `data/seed_manifest.json` to obtain the three seed ranges.  
  - For each regime (`uniform`, `dopd`) and each training seed 0‑49:  
    1. Calls the appropriate training module (`uniform_distillation.py` or `dopd_distillation.py`).  
    2. After training, evaluates the student policy twice: (a) with privileged signal `h` visible, (b) with `h` masked.  
    3. Computes `accuracy_unmasked`, `accuracy_masked`, `performance_drop`, `convergence_steps`, `mean_entropy`.  
    4. Writes a per‑seed result file `data/raw/experiment_results_seed_{seed}_{regime}.json` that conforms to `contracts/experiment-result.schema.yaml`.  
  - All training steps automatically log to the **single** `data/raw/training_log.jsonl` via `TrainingLogger`.  
  - **Verification**: after running with `--seeds 2` (a fast sanity mode) the script creates 4 result JSON files, `training_log.jsonl` contains ≥ 4 logged lines, and each JSON validates against its schema.

- [ ] T011 [US3] **Aggregation & statistical summary script** – `code/scripts/aggregate_and_analyze.py`  
  - Reads all `experiment_results_seed_*.json`, builds two CSVs `data/processed/results_uniform.csv` and `data/processed/results_dopd.csv` with columns matching `experiment-result.schema.yaml`.  
  - Computes for each seed the **performance drop** and records `convergence_steps` and `mean_entropy`.  
  - Performs a **one‑tailed Mann‑Whitney U test** (`alternative='greater'`) comparing DOPD vs. Uniform generalization accuracy, computes **Cliff’s Δ** as effect size, and calculates the **coefficient of variation** of the generalization accuracies.  
  - Writes `data/processed/statistical_summary.json` adhering to `contracts/statistical-summary.schema.yaml`, including the `is_exploratory` flag (true if effect size < 0.5).  
  - **Verification**: running the script on the full 50‑seed data produces a JSON that passes schema validation, `p_value` lies in `[0,1]`, and `effect_size` is a finite number. A secondary unit test feeds synthetic CSVs with known ordering and checks that the resulting `p_value` matches SciPy’s output.

- [ ] T012 [US3] **Reproducibility metrics** – `code/analysis/reproducibility.py`  
  - Calculates mean, std‑dev, and CV of the generalization accuracies across all seeds, hashes the `statistical_summary.json` (SHA‑256), and writes `data/processed/reproducibility_metrics.json` (schema‑free but documented).  
  - Updates the project‑state YAML (`state/projects/PROJ-...yaml`) with the hash entry.  
  - **Verification**: after the full pipeline runs, the reproducibility JSON exists, contains `cv_value` > 0, and the hash recorded in the YAML matches `sha256sum` of the summary file.

- [ ] T013 [P] **Quick‑start documentation** – `docs/quickstart.md`  
  - Provides a single command line (e.g., `python -m code.scripts.run_experiment --mode full`) that reproduces the entire study from a fresh clone.  
  - Lists required environment setup (`pip install -r requirements.txt`) and explains where to find the final results (`data/processed/statistical_summary.json`).  
  - **Verification**: following the instructions on a clean runner executes without error and produces all expected artifacts.

---  

### Dependency mapping (for reference)

| Spec requirement | Satisfied by task |
|------------------|-------------------|
| FR‑001, FR‑008 | T002 |
| FR‑002 | T005, T007 |
| FR‑003 | T008 |
| FR‑004 | T010 (evaluation with masked `h`) |
| FR‑005 | T011 |
| FR‑006 | T006 (log accuracy, entropy, convergence) |
| FR‑007 | T010 (distinct eval seed range) |
| SC‑001‑SC‑005 | T010‑T012 (metrics collection, statistical test, CV, effect‑size flag) |

All tasks respect the data‑flow order: environment → teacher/student → baseline → logger → training → orchestration → analysis.  

---  

**Note**: Tasks T022, T023, T025, T030, and the missing 50‑seed loop (previously T066) have been merged and fully re‑specified in T006‑T010 to guarantee real artifacts, correct file names (`training_log.jsonl`), and complete logging as required by the specification.
