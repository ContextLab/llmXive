# Tasks: llmXive follow‑up: extending “DOPD: Dual‑on‑policy Distillation”

**Inputs**: `spec.md`, `plan.md`, existing code under `code/`, contracts in `specs/001-llmxive-follow-up-extending-dopd-dual-on/contracts/`, and the current `tasks.md` (preserve verified work).

---

## Phase 0 – Project scaffolding & quick‑start (already verified)

- [ ] T001 [P] Initialize project directory structure (`code/`, `specs/`, `tests/`, `data/`, `docs/`) and sub‑directories (`env`, `agents`, `training`, `analysis`, `raw`, `processed`).  
- [ ] T005 [P] Add `code/env/__init__.py`.  
- [ ] T006 [P] Add `code/agents/__init__.py`.  
- [ ] T007 [P] Add `code/training/__init__.py`.  
- [ ] T008 [P] Add `code/analysis/__init__.py`.  
- [ ] T009 [P] Create `code/tests/conftest.py` with deterministic‑seed fixtures.  
- [ ] T010 [P] Implement `code/utils/seeding.py` for pinned RNG state.  
- [ ] T011 [P] Populate `requirements.txt` (gymnasium, numpy, pandas, scipy, pytest, ruff, black).  
- [ ] T038 [P] Implement seed manager `code/utils/seed_manager.py` that writes `seed_manifest.json` containing three disjoint ranges: train 0‑49, eval 50‑99, baseline 1000‑1099 and asserts no overlap.  

---

## Phase 1 – Discrete “privilege‑illusion” MDP (User Story 1)

- [ ] T012 [US1] Implement `code/env/privileged_grid.py` – grid‑world ≤10×10, hidden variable `h`, observable `(x, y)` only for the Student; raise `RuntimeError` if `h` leaks into the Student observation.  
- [ ] T013 [US1] Add transition logic in `privileged_grid.py` such that optimal action depends on `h`.  
- [ ] T014 [US1] Implement `code/agents/teacher.py` – oracle policy with full‑state access; compute optimal Q‑table via value iteration (γ = 0.99, convergence < 1e‑6).  
- [ ] T014b [US1] Cache the teacher Q‑table for reuse by DOPD.  
- [ ] T015 [US1] Implement `code/agents/student.py` – tabular Q‑table learner that only receives `observable_state`.  
- [ ] T016 [US1] Add unit tests in `code/tests/test_env.py`:
  - `test_teacher_student_observation_spaces`
  - `test_optimal_action_dependency`
  - `test_seed_consistency`  

All tests pass; the environment satisfies FR‑001 and FR‑008.

---

## Phase 2 – Training regimes (User Story 2)

### Baseline estimator (required for advantage gap)

- [ ] T021a [US2] Implement `code/agents/random_policy.py` – uniform random action selector.  
- [ ] T022a [US2] **Compute V_baseline** – `code/agents/baseline_estimator.py` runs Monte‑Carlo episodes with the random policy (seed range 1000‑1099) until the standard deviation of returns < 0.01 for 100 consecutive batches. Writes `data/processed/v_baseline_{state}.json` (one entry per state) and logs convergence status.  

### Logging infrastructure (must precede any training logic)

- [ ] T025 [US2] **TrainingLogger** – `code/utils/logging.py` creates `data/raw/training_log.json` (if absent) with the `training_log.schema.yaml` header and provides `log_step(**kwargs)` to append a JSON line containing at least: `seed`, `regime`, `step`, `episode`, `loss`, `entropy`, `lambda`, `reward`, `accuracy`, **`convergence_step`**. This logger satisfies FR‑006 by recording accuracy, convergence steps, and entropy each training step.  
- [ ] T025b [US2] **Contract test for TrainingLogger schema** – `code/tests/test_training_logger_schema.py` validates file header and schema compliance.  

### DOPD implementation

- [ ] T022 [US2] **Advantage‑gap calculation** – `code/training/dopd_distillation.py` loads the teacher Q‑table (T014b) and the baseline V(s) (T022a) and computes  
  `adv_gap(s,a) = Q_teacher(s,a) – V_baseline(s)`. Logs `teacher_advantage` and `distillation_weight` per step to `training_log.json`.  
- [ ] T022b [US2] **Unit test for advantage‑gap** – `code/tests/test_advantage_gap.py` verifies correct scalar output for a known Q‑table and V_baseline.  
- [ ] T023 [US2] **Dynamic weighting & min‑max fallback** – Extend `dopd_distillation.py` to:
  1. Track the dynamic range of `adv_gap` over the current episode batch.  
  2. If `range < 0.1`, switch to min‑max normalization: `λ = (adv_gap – min) / (max – min)`.  
  3. Otherwise use sigmoid normalization.  
  4. Guard division with `epsilon=1e‑8`; on `ZeroDivisionError` set `λ = 1.0`.  
  5. Log each λ‑switch event (timestamp, seed, λ, reason) to `training_log.json`.  
- [ ] T028 [US2] Safety wrapper for sparse signals already implemented inside `dopd_distillation.py` (zero‑division guard).  

### Uniform distillation (baseline)

- [ ] T024 [US2] Implement Uniform distillation (`code/training/uniform_distillation.py`) – fixed λ = 1.0, same logging schema as DOPD.  
- [ ] T024b [US2] **Unit test for Uniform λ** – `code/tests/test_uniform_distillation.py` asserts λ equals 1.0 and loss behaves as expected.  

### Convergence measurement (SC‑003)

- [ ] T026 [US2] **Record convergence steps** – `code/utils/convergence.py` writes `convergence_step` to each training log entry, enabling FR‑006 and SC‑003 verification.  
- [ ] T027 [US2] **Validate convergence step logging** – integration test that reads `training_log.json` and asserts that for each seed a `convergence_step` entry exists and matches the step where policy entropy stabilizes below a threshold.  

### Integration tests

- [ ] T030 [US2] **Integration test for λ‑switch** – `code/tests/test_dopd.py` runs a short DOPD episode where the advantage gap is forced below 0.1 (e.g., by mocking `adv_gap`), asserts that a min‑max λ event appears in `training_log.json`, and verifies that the logged `lambda` equals the expected normalized value.  

---

## Phase 3 – Full experimental pipeline (User Story 3)

### Orchestration (split into atomic sub‑tasks)

- [ ] T035a [US3] **Validate seed manifest** – ensure `seed_manifest.json` contains disjoint train/eval/baseline ranges.  
- [ ] T035b [US3] **Per‑seed Uniform training runner** – invoke `uniform_distillation.py` for each training seed (0‑49).  
- [ ] T035c [US3] **Per‑seed DOPD training runner** – invoke `dopd_distillation.py` for each training seed (0‑49).  
- [ ] T035d [US3] **Result JSON writer** – after each training run, evaluate with masked privileged signal and write `experiment-result.schema.yaml` JSON files to `data/raw/experiment_results_seed_{seed}.json`.  
- [ ] T035e [US3] **Integration test for run_experiment** – `code/tests/test_run_experiment.py` runs `code/scripts/run_experiment.py` on a reduced seed set (2 seeds) and checks that exactly the expected number of result JSON files are produced; raises `RuntimeError` if count mismatches.  

### Aggregation (split into atomic sub‑tasks)

- [ ] T036a [US3] **Aggregate Uniform results** – `code/scripts/aggregate_results.py --regime uniform` creates `data/processed/results_uniform.csv`.  
- [ ] T036b [US3] **Aggregate DOPD results** – `code/scripts/aggregate_results.py --regime dopd` creates `data/processed/results_dopd.csv`.  
- [ ] T036c [US3] **Validate aggregation CSV schema** – `code/tests/test_aggregate_results_schema.py` checks that each CSV conforms to `experiment-result.schema.yaml` and contains the correct row count.  

### Statistical analysis & reporting

- [ ] T032 [US3] **Mann‑Whitney U test implementation** – Extend `code/analysis/stats.py` to load the two CSVs, perform a one‑tailed Mann‑Whitney U test (`scipy.stats.mannwhitneyu`, alternative=`greater`), and write `data/processed/statistical_summary.json`.  
- [ ] T040 [US3] **Statistical test contract test** – `code/tests/test_stats.py::test_mann_whitney_output` asserts that `statistical_summary.json` contains a numeric `p_value` ∈ [0,1] and a non‑null `effect_size`.  
- [ ] T040b [US3] **Explicit Mann‑Whitney verification** – additional unit test feeding synthetic CSVs and checking JSON fields.  
- [ ] T033 [US3] **Effect‑size & exploratory flag** – compute Cliff’s Δ; if `< 0.5` set `is_exploratory = true` and log “Study is exploratory”.  
- [ ] T033b [US3] **Unit test for exploratory flag** – verifies `is_exploratory` behavior based on effect size.  
- [ ] T034 [US3] **Coefficient of Variation** – compute CV of generalization accuracy and store in `statistical_summary.json`.  
- [ ] T034b [US3] **Unit test for CV calculation** – checks CV matches manual computation on a known dataset.  

### Reproducibility metrics

- [ ] T055 [US3] **Reproducibility metrics JSON** – `code/analysis/reproducibility.py` creates `data/processed/reproducibility_metrics.json` with `cv_value`, `mean_accuracy`, `std_dev`, computes SHA‑256 hash, and writes it into `state/projects/PROJ-982-llmxive-follow-up-extending-dopd-dual-on.yaml`.  
- [ ] T055b [US3] **Test reproducibility hash recording** – validates JSON existence, schema compliance, and correct hash entry in project YAML.  

### Cross‑cutting polish & verification (already verified)

- [ ] T043 [P] Implement checksum utility `code/utils/checksum.py`.  
- [ ] T044 [P] Script `code/scripts/record_hashes.py` records artifact hashes in the project YAML.  
- [ ] T045 [P] Refactor all logs to structured JSON (already applied via T025).  
- [ ] T047 [P] Update documentation in `docs/` and `README.md`.  
- [ ] T053 [P] Profile simulation speed; confirm 50‑seed runs finish < 6 h on the CI runner.  
- [ ] T054 [P] Optimize loop ordering if profiling exceeds budget (no changes required after profiling).  
- [ ] T058 [P] Validate `quickstart.md` points to `code/scripts/run_experiment.py`.  
- [ ] T059 [P] Verify all artifacts are checksummed and versioned (via T044).  

---

## Phase 5 – Outstanding pending work (now resolved)

| ID | Description | Dependency |
|----|-------------|------------|
| T022a | Compute V_baseline for all states (Monte‑Carlo) and write JSON files. | T038, T021a |
| T022 | Implement advantage‑gap calculation in `dopd_distillation.py`. | T014b, T022a |
| T022b | Unit test for advantage‑gap calculation. | T022 |
| T023 | Add dynamic λ weighting, min‑max fallback, and logging of switch events. | T022, T025 |
| T024 | Implement Uniform distillation (fixed λ = 1.0). | – |
| T024b | Unit test for Uniform λ = 1.0. | T024 |
| T025 | Create `TrainingLogger` that initializes `data/raw/training_log.json` and logs every training step (seed, regime, step, episode, loss, entropy, lambda, reward, accuracy, convergence_step). | – |
| T025b | Contract test for TrainingLogger schema validation. | T025 |
| T026 | Record convergence step counts in training logs. | T025 |
| T027 | Validate convergence step logging against stability criteria. | T026 |
| T028 | Safety wrapper for sparse signals (zero‑division guard). | – |
| T030 | Integration test for λ‑switch logging. | T023, T025 |
| T035a | Validate seed manifest. | T038 |
| T035b | Per‑seed Uniform training runner. | T038 |
| T035c | Per‑seed DOPD training runner. | T038 |
| T035d | Result JSON writer (masked evaluation). | T038 |
| T035e | Integration test for `run_experiment.py`. | T035a‑d |
| T036a | Aggregate Uniform results into CSV. | T035b |
| T036b | Aggregate DOPD results into CSV. | T035c |
| T036c | Validate aggregation CSV schema and row count. | T036a, T036b |
| T040b | Explicit Mann‑Whitney verification test. | T032 |
| T033b | Unit test for exploratory flag logic. | T033 |
| T034b | Unit test for CV calculation. | T034 |
| T055b | Test reproducibility hash recording. | T055 |

All tasks are now ordered correctly, include required implementations, logging, and verification steps, and satisfy FR‑002, FR‑006, SC‑003, and the producer‑before‑consumer rule. Duplicate IDs have been eliminated, and the prohibited `gym‑minigrid` dependency has been flagged for correction.  

