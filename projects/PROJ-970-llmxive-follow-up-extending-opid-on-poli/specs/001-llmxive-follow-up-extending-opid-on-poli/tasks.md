# Tasks: OPID Critical‑First Routing Complexity Analysis  

**Inputs**: `specs/001-opid-routing-complexity/spec.md`, `plan.md`, data‑model, contracts.  
**Goal**: End‑to‑end study of how the OPID “critical‑first” routing threshold interacts with environment complexity.  

---

## Phase 0 – Project scaffolding (parallel, no inter‑file dependencies)

- [ ] T001 **Create project folder hierarchy**  
  `mkdir -p src/environment src/agent src/simulation src/analysis src/utils tests data/raw/synthetic_graphs data/processed`  
  *Verification*: Run `tree -L 2` and confirm all directories exist; commit the empty folders with a placeholder `README.md` in each.  
- [ ] T001a **Verify directory structure**  
  Execute `tree -L 2` and capture the output to `data/processed/dir_structure.txt`; ensure it lists all expected top‑level directories.  
  *Verification*: Check that the captured file contains the paths created by T001.  
- [ ] T002 **Add `__init__.py` to every package**  
  Files: `src/__init__.py`, `src/environment/__init__.py`, `src/agent/__init__.py`, `src/simulation/__init__.py`, `src/analysis/__init__.py`, `src/utils/__init__.py`, `tests/__init__.py`  
  *Verification*: Import each package in a Python REPL (`import src.environment`) without error.  
- [X] T003 **Create `requirements.txt`** (pinned CPU‑only versions)  
  Contents: `networkx==3.2.1`, `numpy==1.26.4`, `pandas==2.2.1`, `scipy==1.13.0`, `statsmodels==0.14.2`, `pytest==8.1.1`  
  *Verification*: `pip install -r requirements.txt` succeeds in a fresh venv.  
- [X] T004 **Add `pyproject.toml` and `ruff.toml` for formatting/linting** (optional, parallel)  
  *Verification*: `ruff check .` runs with zero warnings.  

---

## Phase 1 – Global configuration & feasibility check (blocking)

- [ ] T005 **Implement `src/config.py`**  
  - Constants: `SEED = 42`, `TIER_NODE_RANGES = {1: (5,10), 2: (20,50), 3: (100,200)}`, `THRESHOLD_STEPS = np.arange(0.0,1.01,0.1)`, `MAX_EPISODES_PER_SETTING = 1000`.  
  - Function `set_seed()` seeds `numpy`, `random`, and `os.environ["PYTHONHASHSEED"]`.  
  - Function `verify_feasibility()` estimates runtime; **must return 1000 episodes** and raise `RuntimeError` if the estimate exceeds 6 h (no automatic reduction).  
  *Verification*: Import `config`, call `set_seed()`, check deterministic RNG state; call `verify_feasibility()` and ensure it returns `(1000, <hours≤6)` or raises with clear message.  
- [ ] T006 **Create `src/utils/metrics.py`** with pure‑CPU metric utilities:  
  - `entropy(probs)`, `log_prob_shift(original, injected)`, and helper to compute per‑episode statistics matching `episode_result.schema.yaml`.  
  *Verification*: Unit test imports the module and validates output types for a synthetic probability vector.  
- [ ] T007 **Add runtime profiling task** (new)  
  - **T035**: Profile a full sweep with 1000 episodes per setting on a representative Tier 3 graph; identify bottlenecks and refactor code (e.g., vectorised numpy ops, streaming I/O) to keep estimated runtime ≤ 6 h.  
  *Verification*: After profiling, `src/config.verify_feasibility()` returns 1000 episodes and estimated hours ≤ 6.  

---

## Phase 2 – Synthetic State‑Graph generation (blocking, core data source)

- [ ] T008 **Implement `src/seed.py`** – thin wrapper that imports `config` and calls `set_seed()` at import time.  
  *Verification*: Import `src.seed` and confirm deterministic RNG across runs.  
- [ ] T009 **Implement `src/environment/state_graph.py`** – `@dataclass` `StateGraph` with fields `graph_id`, `tier`, `nodes`, `edges`, `start`, `goal`, `metadata`; method `is_valid()` checks for a reachable path using NetworkX.  
  *Verification*: Instantiate with a tiny deterministic graph; `is_valid()` returns `True`.  
- [ ] T010 **Implement `src/environment/validator.py`** – function `validate_graph(sg: StateGraph) -> None` that raises `RuntimeError` if `sg.is_valid()` is `False`. No silent fallback.  
  *Verification*: Pass an invalid graph; confirm `RuntimeError` is raised.  
- [~] T011 **Implement `src/environment/graph_generator.py`** with tier‑specific generators:  
  - `generate_tier_1(seed)`, `generate_tier_2(seed)`, `generate_tier_3(seed)`.  
  - Each generator must enforce **acceptance criteria**:  
    *Tier 1*: node count 5‑10, single deterministic path, zero stochastic edges, reward sparsity = 0.  
    *Tier 2*: node count 20‑50, at least one branching node, stochastic transition probabilities (some edges with `probability < 1.0`), reward sparsity ≤ 0.1.  
    *Tier 3*: node count ≥ 100, high‑entropy transitions (`probability` varied), reward sparsity ≤ 0.05, sparse rewards.  
  - After generation, call `validator.validate_graph`; on failure retry up to 100 times, then raise.  
  - Save each graph as JSON to `data/raw/synthetic_graphs/{graph_id}.json`.  
  *Verification*: Run each generator with a fixed seed; confirm JSON file exists, conforms to `environment.schema.yaml`, and the tier‑specific properties are asserted in a unit test.  
- [ ] T012 **Batch‑generate graph suite**   <!-- FAILED-IN-EXECUTION: code/generate_graph_suite.py exit=1 -->
  - For each tier, generate **20** graphs (total 60) using seeds `SEED + i`.  
  - Record a manifest CSV `data/raw/graph_manifest.csv` with columns `graph_id,tier,seed`.  
  *Verification*: Manifest contains 60 rows; each referenced JSON file exists and passes validation.  

---

## Phase 3 – OPID policy & routing logic (blocking)

- [ ] T013 **Implement baseline policy in `src/agent/policy_head.py`** – class `StochasticSoftmaxPolicy` with method `action_distribution(state)` returning a softmax over a small random vector; includes `temperature` parameter.  
  *Verification*: `action_distribution` outputs a probability vector that sums to 1 and has entropy > 0.  
- [ ] T014 **Implement `src/agent/opid_router.py`** – class `OPIDRouter`:  
  - `__init__(self, routing_threshold: float)` stores the threshold.  
  - `should_inject(self) -> bool` performs `np.random.rand() < (1 - routing_threshold)`.  
  - `inject_skill_signal(self, action_probs)` adds a constant log‑probability shift (e.g., `np.log(1.1)`) to the selected action when injection occurs; otherwise returns original `action_probs`.  
  *Verification*: Unit test confirms injection always occurs at threshold = 0.0, never at 1.0, and ~50 % at 0.5 over 10 000 trials (±2 %).  

---

## Phase 4 – Episode execution & data logging (blocking)

- [ ] T015 **Implement core runner in `src/simulation/runner.py`** – function `run_episode(graph: StateGraph, router: OPIDRouter, policy: StochasticSoftmaxPolicy) -> dict`  
  - Executes up to 200 steps, terminates on goal or max steps.  
  - At each step: obtain action distribution, query router, optionally inject, sample action, update state.  
  - Tracks `success`, `steps_taken`, average `action_entropy`, and average `log_prob_shift`.  
  - Returns dict matching `episode_result.schema.yaml`.  
  *Verification*: Run on a Tier 1 graph with threshold = 1.0; result dict contains all required keys and `success` is `True`.  
- [ ] T016 **Implement `ExperimentRunner` class in `src/simulation/runner.py`**  
  - Method `run_sweep(episodes_per_setting: int)` iterates over tiers (1‑3), thresholds (`config.THRESHOLD_STEPS`), and runs `episodes_per_setting` episodes per combo.  
  - Streams each `EpisodeResult` as a CSV row appended to `data/processed/episode_results.csv`.  
  - Writes progress to `data/processed/run_log.txt`.  
  *Verification*: After a test run with `episodes_per_setting=10`, CSV contains `3 * 11 * 10 = 330` rows and file size < 5 MB.  
- [ ] T017 **Create quick‑start script `run_experiment.py` at repository root**  
  ```python
  from src.config import set_seed, verify_feasibility
  from src.simulation.runner import ExperimentRunner
  set_seed()
  episodes, _ = verify_feasibility()
  ExperimentRunner(episodes_per_setting=episodes).run_sweep()
  ```  
  *Verification*: Executing `python run_experiment.py` completes without error and produces `episode_results.csv` and `run_log.txt`.  

---

## Phase 5 – Statistical analysis & metric aggregation (blocking)

- [ ] T018 **Implement aggregation utilities in `src/analysis/aggregation.py`**  
  - `load_episode_results()` reads the CSV into a pandas DataFrame.  
  - `compute_summary_stats()` groups by `tier` and `threshold` to calculate: `success_rate`, `mean_entropy`, `entropy_variance`, `mean_log_prob_shift`, `n_episodes`; writes `data/processed/summary_stats.csv` (conforms to `summary_stats.schema.yaml`).  
  - `calculate_baseline_success()` extracts rows where `threshold == 1.0` and writes `baseline_success_rate.json`.  
  *Verification*: After a test run (N=10), summary CSV has 33 rows and JSON contains a float in [0,1].  
- [ ] T019 **Implement quadratic regression for success rate in `src/analysis/stats.py`** – function `fit_success_quadratic(df)` using `numpy.polyfit` (deg 2) and `statsmodels` for p‑value; writes `data/processed/success_quadratic.json` with keys `a`, `b`, `c`, `p_value`, `is_inverted_u`.  
  *Verification*: Run on test summary; JSON created and `is_inverted_u` is boolean.  
- [ ] T020 **Implement quadratic regression for entropy in `src/analysis/stats.py`** – `fit_entropy_quadratic(df)` analogous to T019; writes `entropy_quadratic.json`.  
  *Verification*: JSON exists with numeric coefficients.  
- [ ] T021 **Compute policy rigidity (residual variance) in `src/analysis/aggregation.py`**  
  - Load `entropy_quadratic.json`, predict entropy per row, compute residuals, then variance of residuals per tier‑threshold; append column `policy_rigidity` to summary and update `summary_stats.csv`.  
  *Verification*: Updated CSV includes non‑negative `policy_rigidity`.  
- [ ] T022 **Calculate distillation cost‑benefit ratio in `src/analysis/aggregation.py`**  
  - Split episode results into train/validation using fixed seed (e.g., 999) → `train.csv`, `validation.csv`.  
  - For each tier‑threshold, compute `mean_log_prob_shift` from validation set and `success_rate_improvement = success_rate - baseline_success_rate`.  
  - Ratio = `mean_log_prob_shift / success_rate_improvement` (division‑by‑zero → NaN).  
  - Append `distillation_cost_benefit` to `summary_stats.csv`.  
  *Verification*: Column present; NaN only where improvement ≤ 0.  
- [ ] T023 **Two‑way ANOVA for interaction (threshold × tier) in `src/analysis/stats.py`** – uses `statsmodels.formula.api.ols` with formula `success_rate ~ C(tier) * threshold`; writes `interaction_results.json` containing interaction p‑value.  
  *Verification*: JSON contains a float ≤ 1.0.  
- [ ] T024 **Inflection‑point detection in `src/analysis/stats.py`** – function `detect_inflection(quadratic_json)` computes vertex `-b/(2a)` per tier; stores in `inflection_points.json`.  
  *Verification*: JSON contains three numeric thresholds.  
- [ ] T025 **Finalize aggregated metrics file** – combine all columns (`success_rate`, `mean_entropy`, `entropy_variance`, `policy_rigidity`, `distillation_cost_benefit`, `quadratic_beta2`, `quadratic_p_value`, `inflection_point`, `n_episodes`) into `data/processed/aggregated_metrics.csv` matching `aggregated_metrics.schema.yaml`.  
  *Verification*: Schema validator runs with zero errors.  

---

## Phase 6 – Automated testing suite (parallel where possible)

- [ ] T026 **Unit tests for graph generation** – `tests/unit/test_graph_generator.py`  
  - Verify node counts, stochastic edge probabilities, reward sparsity, and that `validator.validate_graph` passes.  
  *Verification*: `pytest -q tests/unit/test_graph_generator.py` passes.  
- [ ] T027 **Unit tests for router logic** – `tests/unit/test_router.py` (covers `should_inject` probabilities and effect on entropy).  
  *Verification*: Test passes.  
- [ ] T028 **Unit tests for runner metrics** – `tests/unit/test_runner.py`  
  - Runs a single episode on a Tier 2 graph with threshold = 0.5; asserts returned dict matches `episode_result.schema.yaml`.  
  *Verification*: Test passes.  
- [ ] T029 **Integration test for full sweep (small N)** – `tests/integration/test_full_sweep.py`  
  - Calls `ExperimentRunner(episodes_per_setting=5).run_sweep()`. After completion, asserts `episode_results.csv` has `165` rows and `summary_stats.csv` has `33` rows.  
  *Verification*: Test passes within 2 min.  
- [ ] T030 **Schema contract tests** – `tests/contract/test_schemas.py` loads each contract YAML and validates a sample row from the corresponding CSV/JSON using `jsonschema.validate`.  
  *Verification*: All contracts validate without errors.  

---

## Phase 7 – Documentation & hand‑off (parallel)

- [ ] T031 **Write `quickstart.md`** – describes environment setup, how to run `python run_experiment.py`, and where to find `aggregated_metrics.csv`. Includes command‑line snippets and expected file locations.  
  *Verification*: File builds without broken links; commands run successfully on a fresh clone.  
- [ ] T032 **Add `analysis-method.md`** – explains each statistical step (quadratic fits, ANOVA, cost‑benefit ratio) and links to the corresponding implementation modules.  
  *Verification*: Document is present and referenced from `quickstart.md`.  

---

## Dependency & execution order summary

| Phase | Must‑complete‑before |
|------|----------------------|
| Phase 0 | – |
| Phase 1 | Phase 0 |
| Phase 2 | Phase 1 |
| Phase 3 | Phase 1 |
| Phase 4 | Phase 2 & Phase 3 |
| Phase 5 | Phase 4 |
| Phase 6 | Phases 2‑5 (implementation) |
| Phase 7 | Any phase (documentation can be written in parallel) |

All tasks are unchecked (`[ ]`) because they represent pending work that must be completed to satisfy the specification. Once a task is finished and its verification passes, the checkbox can be marked `[x]` by the CI verifier.  
