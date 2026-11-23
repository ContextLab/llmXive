# Implementation Plan: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

**Branch**: `001-dopd-discrete-mdp` | **Date**: 2026-10-09 | **Spec**: `specs/001-dopd-discrete-mdp/spec.md`  
**Input**: Feature specification from `specs/001-dopd-discrete-mdp/spec.md`

## Summary
We will build a **pure‑Python** discrete grid‑world MDP where a hidden privileged variable `H` is observable only to a Teacher oracle. Two training regimes will be implemented for a Student tabular Q‑learner:

1. **Uniform On‑Policy Distillation** – fixed weighting of Teacher actions.  
2. **Dual On‑Policy Distillation (DOPD)** – dynamic weighting based on an advantage‑gap signal.

The experiment will run **50 independent random seeds** per regime, evaluate Student performance with and without the privileged signal, and conduct a **one‑tailed Mann‑Whitney U test** on the performance‑drop metric. All code runs on the GitHub Actions free‑tier CPU runner; no GPU or non‑pure‑Python libraries are required.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `numpy` (numerical), `scipy` (stats), `pyyaml` (schema validation), `pytest` (testing). *(No external game engines such as gym‑minigrid – pure‑Python implementation satisfies Constitution VI.)*  
- **Storage**: In‑memory Q‑tables; CSV/JSON files under `data/` for logs and results.  
- **Testing**: `pytest` with unit and integration suites covering environment safety, training‑loop correctness, and logging.  
- **Target Platform**: Linux runner on GitHub Actions (Several CPU cores, ≈ a few GB RAM).  
- **Performance Goals**: Complete all 50‑seed runs (≈ several k training steps total) within the a multi‑hour CI window.  
- **Constraints**: Grid size ≤ 10×10; pure‑Python implementation (no GPU).  
- **Scale/Scope**: Full factorial of 2 regimes × 50 seeds = 100 runs, plus baseline random‑policy estimation.

## Constitution Check

| Principle | Status | Evidence / Action |
|-----------|--------|-------------------|
| **I. Reproducibility** | PASS | All random seeds are pinned; deterministic environment generation; `requirements.txt` pins exact package versions. |
| **II. Verified Accuracy** | PASS | No external citations beyond the original DOPD paper; all algorithmic details are derived from the spec. |
| **III. Data Hygiene** | PASS | Synthetic data is generated anew each run; raw logs are immutable; derived CSVs are written to `data/processed/`. |
| **IV. Single Source of Truth** | PASS | Every reported metric (accuracy, drop, p‑value, CV, etc.) is read directly from the CSV/JSON artifacts produced by the code. |
| **V. Versioning Discipline** | PASS | Artifact hashes will be recorded in the project state file by the Advancement‑Evaluator. |
| **VI. Discrete‑State Simulation Integrity** | PASS | The environment is a custom pure‑Python grid class (`PrivilegedGridEnv`) with no external simulation library. |
| **VII. Generalization Validation** | PASS | Evaluation uses a distinct seed set and masks `H`; Mann‑Whitney U test is applied as required. |

## Project Structure

```
specs/001-dopd-discrete-mdp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── experiment-result.schema.yaml

code/
├── env/
│   ├── __init__.py
│   └── privileged_grid.py          # Pure‑Python grid MDP
├── agents/
│   ├── __init__.py
│   ├── teacher.py                  # Oracle policy with full state
│   ├── student.py                  # Tabular Q‑learner (observable + λ)
│   └── baseline_estimator.py       # Monte‑Carlo random‑policy V(s)
├── training/
│   ├── __init__.py
│   ├── uniform_distillation.py
│   └── dopd_distillation.py        # Advantage gap, dynamic λ, logging
├── utils/
│   └── logging.py                  # TrainingLogger writes to data/raw/training_log.jsonl
├── analysis/
│   ├── __init__.py
│   ├── stats.py                    # Mann‑Whitney U, Cliff's Δ, CV
│   └── report.py                   # Generates statistical_summary.json
├── run_experiment.py               # Orchestrates 50‑seed loop, writes aggregated CSVs
├── main.py                         # CLI entry point (wraps run_experiment)
├── requirements.txt
└── tests/
    ├── unit/
    │   ├── test_env.py
    │   ├── test_agents.py
    │   └── test_logging.py
    └── integration/
        ├── test_uniform_vs_dopd.py
        └── test_lambda_switch.py

data/
├── raw/
│   └── training_log.jsonl           # Created by TrainingLogger (JSON‑Lines)
└── processed/
    ├── results_uniform.csv
    ├── results_dopd.csv
    └── statistical_summary.json
```

**Structure Decision**: A single `code/` root with clear sub‑packages isolates simulation, agents, training loops, utilities, and analysis. This satisfies Principle VI (pure‑Python) and keeps the data‑flow linear: *Env → Teacher/Student → Training → Logging → Analysis*.

## Complexity Tracking (FR/SC → Tasks)

| FR / SC | Mapped Phase / Task(s) | Rationale |
|---------|------------------------|-----------|
| **FR‑001** (grid‑world with hidden `H`) | Phase 0 – `T012` (implement `PrivilegedGridEnv`) | Guarantees information asymmetry. |
| **FR‑002** (advantage‑gap computation & fallback) | Phase 1 – `T022` (calc gap) + `T023` (dynamic λ with min‑max fallback) | Implements DOPD weighting logic, handles near‑zero range. |
| **FR‑003** (Uniform distillation) | Phase 1 – `T024` (uniform loop) | Fixed λ = 1.0 baseline. |
| **FR‑004** (masked‑signal evaluation) | Phase 2 – `T035` (seed manager) + evaluation code in `run_experiment.py` | Measures performance drop. |
| **FR‑005** (Mann‑Whitney U, exploratory flag) | Phase 3 – `T033` (stats) | One‑tailed test, effect‑size check. |
| **FR‑006** (log accuracy, convergence, entropy) | Phase 1 – `T025` (TrainingLogger) + `T022/T023` (log λ, loss, entropy) | Writes to `data/raw/training_log.jsonl`. |
| **FR‑007** (distinct eval seed) | Phase 2 – `T035` (seed sets) | Guarantees independence per Principle VII. |
| **FR‑008** (grid size limit) | Phase 0 – `T012` (assert max 10×10) | Enforces RAM constraint. |
| **SC‑001** (drop comparison) | Phase 3 – `T033` (compute drops, compare) | Directly measured. |
| **SC‑002** (statistical significance) | Phase 3 – `T033` (p‑value) | One‑tailed Mann‑Whitney. |
| **SC‑003** (convergence steps) | Phase 3 – `T034` (record steps) | Logged per seed. |
| **SC‑004** (action entropy) | Phase 1 – `T022/T023` (track entropy) | Logged each step. |
| **SC‑005** (reproducibility CV) | Phase 3 – `T034` (CV) | Computed from aggregated accuracies. |

## Implementation Phases & Tasks

### Phase 0 – Environment & Baseline

- **T001**: Scaffold repository directories and `requirements.txt`.
- **T012**: Implement `PrivilegedGridEnv` (pure‑Python).  
  - Enforce max grid size 10×10.  
  - State = `(x, y, H)`; Student observation = `(x, y)`.  
  - Provide `reset(seed)` and `step(action)` methods.  
  - Unit tests verify Teacher sees `H`, Student does not, and reproducibility across seeds.  
- **T022a**: Implement `BaselineEstimator` (Monte‑Carlo random policy).  
  - Generates `V_baseline(s)` for every observable state.  
  - Converges when std‑dev < 0.01 for 100 consecutive batches.  
  - Uses its own seed range (1000‑1099).  

### Phase 1 – Training Regimes & Logging

- **T022**: In `dopd_distillation.py` implement `calculate_advantage_gap(teacher_q, v_baseline)` returning a float.  
  - Handles division‑by‑zero safely (fallback λ = 1.0).  
- **T023**: Implement `calculate_dynamic_lambda(gap_batch)`  
  - If `max(gap) - min(gap) >= 0.1` → `λ = σ(gap)` (sigmoid).  
  - Else → min‑max normalize: `λ = (gap - min) / (max - min)`.  
  - When fallback is used, log a `"lambda_switch": "minmax"` entry via `TrainingLogger`.  
- **T025**: Create `utils/logging.py` → `TrainingLogger` that **opens `data/raw/training_log.jsonl`** on init and provides `log_step(dict)` method.  
  - On each training step log: `seed`, `regime`, `step`, `episode`, `loss`, `entropy`, `expected_advantage_gap` (or `null` for Uniform), `reward`.  
  - Guarantees JSON‑Lines format required by `training_log.schema.yaml`.  
- **T024**: Implement `uniform_distillation.py` – fixed λ = 1.0, uses `TrainingLogger`.  
- **T028**: Safety wrapper for sparse‑signal cases (division‑by‑zero) – returns λ = 1.0 and logs a warning via `TrainingLogger`.  

### Phase 2 – Orchestration & 50‑Seed Execution

- **T035** (`run_experiment.py`):  
  - Generate three **disjoint** seed lists: training 0‑49, evaluation 50‑99, baseline 1000‑1099.  
  - Loop over regimes (`uniform`, `dopd`) and seeds, invoking the appropriate training module.  
  - After each run, compute per‑seed metrics (accuracy_unmasked, accuracy_masked, drop, convergence_steps, mean_entropy) and append a row to `data/processed/results_{regime}.csv`.  
  - All runs write to the same `data/raw/training_log.jsonl` (appended).  
- **T030**: Integration test `tests/integration/test_lambda_switch.py` runs DOPD on a deliberately degenerate MDP where advantage gaps are < 0.1, asserts that a `"lambda_switch"` log entry appears and that entropy rises.  
- **T031**: Integration test for entropy increase under low‑gap conditions.  

### Phase 3 – Analysis & Reporting

- **T033** (`analysis/stats.py`):  
  - Load per‑seed CSVs, compute performance‑drop for each seed, run a **one‑tailed Mann‑Whitney U** (`alternative='less'`) comparing DOPD vs. Uniform.  
  - Compute **Cliff’s Δ** as effect size.  
  - If `effect_size < 0.5` set `is_exploratory = true`.  
  - Write `data/processed/statistical_summary.json` conforming to `contracts/statistical-summary.schema.yaml`.  
- **T034**: Compute **Coefficient of Variation** of generalization accuracy across seeds; add to summary.  
- **T036**: Aggregate all CSVs into a master `results_all.csv` for downstream paper generation.  

## Risk Mitigation & Compute Feasibility

- **Pure‑Python Grid** ensures CPU‑first execution; memory usage ≤ 10 KB per Q‑table.  
- **Monte‑Carlo Baseline** may be noisy; if std‑dev threshold not met after 2000 samples per state, the estimator will automatically increase samples (still trivial cost).  
- **Seed Collisions** are prevented by explicit set checks in `run_experiment.py`.  
- **Effect‑size Power**: 50 seeds give > 80 % power for medium effects (Cohen d ≈ 0.5). If effect size falls below 0.5, the study is flagged as exploratory per FR‑005.  

---  
*All functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑005) are addressed in the tasks above. No external, non‑pure‑Python libraries are used, satisfying Constitution VI.*

