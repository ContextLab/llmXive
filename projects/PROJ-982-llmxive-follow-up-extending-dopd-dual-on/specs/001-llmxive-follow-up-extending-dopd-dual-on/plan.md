# Implementation Plan: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

**Branch**: `001-dopd-discrete-mdp` | **Date**: 2026-07-23 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-dopd-discrete-mdp/spec.md`

## Summary

This project implements a discrete-state Markov Decision Process (MDP) simulation to investigate the "privilege illusion" phenomenon in AI distillation. The core technical approach involves constructing a synthetic grid-world where a "Teacher" agent possesses a hidden privileged state variable ($H$) unavailable to the "Student" agent. We will compare two training regimes: (1) Uniform On-Policy Distillation (blind mimicry) and (2) Dual On-policy Distillation (DOPD), which dynamically weights distillation loss based on an "advantage gap" (Teacher $Q(s,a)$ minus a random-policy baseline $V(s)$).

**Causal Mechanism**: The Teacher computes the advantage gap using full state $(O, H)$ and passes a scalar weight $\lambda$ to the Student by appending it to the Student's observation vector. The Student learns a policy conditioned on $(O, \lambda)$, allowing it to adapt its reliance on the Teacher without ever accessing $H$ directly.

The project validates whether DOPD mitigates performance collapse when the privileged signal is masked during evaluation, using tabular Q-learning and a **one-tailed** Mann-Whitney U test ($H_0$: mean(DOPD) <= mean(Uniform)) across 50 independent seeds.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `gym-minigrid` (for environment simulation), `numpy` (numerical ops), `scipy` (statistical tests), `pyyaml` (schema validation), `pytest` (testing).
**Storage**: In-memory dictionaries for Q-tables; CSV/JSON for logging results; no external database.
**Testing**: `pytest` with unit tests for environment logic, integration tests for training loops, and statistical validation tests.
**Target Platform**: Linux (GitHub Actions free-tier: 2 CPU, 7GB RAM).
**Project Type**: Research simulation library.
**Performance Goals**: Complete 50 seed experiments (train + eval + stats) within 6 hours on CPU.
**Constraints**:
- Grid size $\le$ 10x10 (to ensure $O(S \cdot A)$ Q-tables fit in RAM).
- No GPU required (pure tabular methods).
- Strict reproducibility via pinned random seeds.
- **Seed Separation**: Training seeds, Evaluation seeds, and Baseline seeds are distinct sets.
- **Data Model Mapping**: `gym-minigrid` observation dictionaries are flattened into integer vectors (`full_state_vector`, `student_observation`) as defined in `data-model.md`.
**Scale/Scope**: Multiple independent simulation runs, Multiple training regimes

The research question remains: How do different training regimes affect model convergence?
The method remains: Comparative analysis of convergence rates across varied training protocols.
References: Smith et al.;., A synthetic MDP environment (plus a control environment).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds in `code/` and deterministic MDP generation. `requirements.txt` will pin all versions. |
| **II. Verified Accuracy** | **PASS** | External concepts ("privilege illusion", "DOPD") will be cited and verified in `research.md` against primary sources. Code logic is self-contained. |
| **III. Data Hygiene** | **PASS** | No external datasets to checksum. Synthetic data is generated on-the-fly; logs are treated as derived data. |
| **IV. Single Source of Truth** | **PASS** | All metrics (accuracy, drop, p-value, **CV**) will be computed by `code/analysis/stats.py` and logged to CSV, which the paper will read. |
| **V. Versioning Discipline** | **PASS** | Artifacts (Q-tables, logs) will be hashed. **Hashes will be recorded in `state/projects/PROJ-982-llmxive-follow-up-extending-dopd-dual-on.yaml`**. |
| **VI. Discrete-State Simulation** | **PASS** | Implementation uses `gym-minigrid` (discrete) and tabular Q-learning (no neural nets). |
| **VII. Generalization Validation** | **PASS** | Plan explicitly includes a "masked evaluation" phase where $H$ is removed, **one-tailed Mann-Whitney U test** is mandated, and **effect size < 0.5 triggers "exploratory" status logging**. |

## Project Structure

### Documentation (this feature)

```text
specs/001-dopd-discrete-mdp/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
└── contracts/ # Phase 1 output
 ├── mdp-transition.schema.yaml
 ├── experiment-result.schema.yaml
 ├── mdp_state.schema.yaml
 ├── metrics-schema.schema.yaml
 ├── result_summary.schema.yaml
 ├── simulation-schema.schema.yaml
 ├── statistical-summary.schema.yaml
 ├── training_log.schema.yaml
 └── transition.schema.yaml
```

### Source Code (repository root)

```text
code/
├── env/
│ ├── __init__.py
│ └── privileged_grid.py # Discrete MDP with hidden state H
├── agents/
│ ├── __init__.py
│ ├── teacher.py # Oracle policy (access to H)
│ ├── student.py # Tabular Q-table (access to O + weight_lambda)
│ └── baseline_estimator.py # Simulates random policy for V(s) (Offline)
├── training/
│ ├── __init__.py
│ ├── uniform_distillation.py # Baseline: fixed weighting
│ └── dopd_distillation.py # DOPD: dynamic weighting based on advantage gap
├── analysis/
│ ├── __init__.py
│ ├── stats.py # Mann-Whitney U, Effect Size, CV calculation
│ └── report.py # Generates "exploratory" status logs
├── tests/
│ ├── unit/ # Environment logic, safety checks (div-by-zero)
│ └── integration/ # Full training loop + masked eval
├── main.py # Orchestration: 50 seeds, distinct train/test seeds
└── requirements.txt

data/
├── raw/ # Generated transition logs (JSON/CSV)
└── processed/ # Aggregated accuracy stats per seed
```

**Structure Decision**: Single `code/` root with modular sub-packages (`env`, `agents`, `training`, `analysis`). This structure isolates the discrete MDP logic from the statistical analysis, ensuring the "Producer before Consumer" flow (Env -> Training -> Analysis) is clear. The `main.py` orchestrates the 50-seed loop, ensuring distinct seeds for training and evaluation are generated *before* execution begins.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|:--- |:--- |:--- |
| **Dual Training Regimes** | Required to isolate the "privilege illusion" effect. | A single regime would not allow comparison to prove DOPD's mitigation. |
| **Distinct Seed Logic** | FR-005/FR-007 mandate statistical independence. | Using the same seed for train/eval would invalidate the Mann-Whitney U test assumptions. |
| **Advantage Gap Switch** | FR-002 requires fallback to min-max normalization if dynamic range < 0.1. | Hardcoding one method fails when the environment yields degenerate Q-values. |
| **Weight Injection** | Required to solve causal separation (Student cannot compute gap). | Passing full state H to Student violates the problem definition. |

## Implementation Phases

### Phase 0: Environment & Baseline Construction

- [ ] **T001**: Initialize Project Directory Structure
 - Create `code/`, `specs/`, `tests/`, `data/`, `docs/` and subdirectories (`env`, `agents`, `training`, `analysis`, `raw`, `processed`).
 - Create placeholder `__init__.py` files and `requirements.txt`.
- [ ] **T012**: Implement Discrete MDP Environment
 - Implement `code/env/privileged_grid.py`.
 - **Constraint**: Max grid dimension 10x10.
 - **Logic**: State $S = (O, H)$. $O$ is observable, $H$ is hidden.
 - **Masking**: Ensure `student_observation` strictly excludes $H$.
 - **Test**: Verify Teacher sees $H$, Student does not.
- [ ] **T022a**: Implement Baseline Estimator (Prerequisite for T022)
 - **Algorithm**: Monte Carlo simulation of a random policy.
 - **Steps**: For each state $s$, run a sufficient number of random episodes to ensure statistical convergence.
 - **Convergence**: Stop if std dev of returns < 0.01 for 100 consecutive batches.
 - **Output**: `V_baseline(s)` for all states.
 - **Seed**: Use distinct baseline seeds.

### Phase 1: Training Regimes

- [ ] **T022**: Implement DOPD Advantage Gap Calculation (Depends on T022a)
 - Compute $A_{gap}(s, a) = Q_{teacher}(s, a) - V_{baseline}(s)$.
 - **Safety**: If denominator (gap range) is near-zero (< 1e-9), default to 1.0.
- [ ] **T023**: Implement Dynamic Weighting & Min-Max Fallback
 - **Logic**: Measure dynamic range (max - min) of $A_{gap}$ over current batch.
 - **Trigger**: If range < 0.1, switch to min-max normalization: $\lambda = \frac{A_{gap} - min}{max - min}$.
 - **Default**: Else, use sigmoid normalization.
- [ ] **T028**: Implement Safety Checks for Sparse Signals
 - **Logic**: Wrap division operations in `try/except ZeroDivisionError`.
 - **Fallback**: If error, set $\lambda = 1.0$ (Uniform mode).
 - **Test**: Unit test with zero denominator inputs.
- [ ] **T024**: Implement Uniform Distillation Loop
 - Fixed $\lambda = 1.0$.
 - Student mimics Teacher actions.

### Phase 2: Orchestration & Execution

- [ ] **T035/T038**: Implement Seed Manager & 50-Seed Loop (Merged)
 - **Logic**: Generate distinct seeds: Train (negative indices), Eval (50-99), Baseline (1000-1099).
 - **Verification**: Assert `len(set(train_seeds) & set(eval_seeds)) == 0`.
 - **Loop**: Execute Train -> Eval -> Log for all 50 seeds.
- [ ] **T030**: Integration Test: DOPD Weight Switch
 - **Test**: Run DOPD with low advantage gap. Verify $\lambda$ switches to min-max.
 - **Output**: Log file showing switch event.
- [ ] **T031**: Integration Test: DOPD Entropy Increase
 - **Test**: Run DOPD with low advantage gap. Verify Student entropy increases.
 - **Output**: Log file showing entropy trend.

### Phase 3: Analysis & Reporting

- [ ] **T033**: Statistical Analysis & Exploratory Status
 - **Test**: Mann-Whitney U test (one-tailed).
 - **Effect Size**: Calculate Cliff's Delta.
 - **Logic**: If effect size < 0.5, set `is_exploratory = True` and log "Study is exploratory and underpowered".
- [ ] **T034**: Coefficient of Variation (CV) Calculation
 - **Formula**: $CV = \frac{\sigma}{\mu}$.
 - **Output**: Include in `statistical_summary.json`.
- [ ] **T036**: Aggregate Results
 - Combine logs from 50 seeds into `data/processed/results.csv`.

## Verification & Validation

- **Unit Tests**: `test_division_by_zero_safety`, `test_baseline_convergence`, `test_seed_separation`.
- **Integration Tests**: `test_dopd_weight_switch`, `test_dopd_entropy_increase`.
- **Statistical Tests**: Verify p-value and effect size calculation.

## Risk Mitigation

- **Risk**: Baseline estimation is too noisy.
 - **Mitigation**: Increase Monte Carlo steps to 2,000 if std dev > 0.01.
- **Risk**: Grid size exceeds RAM.
 - **Mitigation**: Enforce 10x10 max; stream data if needed.
- **Risk**: Effect size is too small.
 - **Mitigation**: Explicitly report as "exploratory" per FR-005.