# Research: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

## Research Question
*Does the “privilege illusion” phenomenon emerge in discrete, non‑differentiable MDPs, and can Dual On‑policy Distillation (DOPD) mitigate it without any neural‑network optimization?*

## Hypotheses
- **H1** – In a discrete MDP where optimal behavior depends on a hidden privileged variable `H`, a Student trained with **Uniform On‑Policy Distillation** will achieve high training performance but will suffer a large performance drop when `H` is masked during evaluation.
- **H2** – A Student trained with **DOPD**, which dynamically down‑weights Teacher guidance based on the advantage gap, will exhibit a **significantly smaller** performance drop under the same masking condition.

## Methodology

### 1. Environment Construction (Pure‑Python Discrete MDP)
- **Grid**: ≤ 10×10 (enforced by `PrivilegedGridEnv`).  
- **State**: `(x, y, H)`. `H ∈ {0,1}` determines which of two doors is safe.  
- **Observation**: Student sees only `(x, y)`; Teacher sees `(x, y, H)`.  
- **Transitions**: Deterministic moves (up/down/left/right) with stochastic slip probability = 0.1 (implemented in pure Python).  
- **Reward**: `+1` for reaching the correct door, `-0.1` per step, `-1` for hitting a wall.  
- **Optimality**: The optimal policy **requires** knowledge of `H`; without it the Student must guess and will be sub‑optimal.

### 2. Agents
- **Teacher**: Oracle that computes the optimal action via exhaustive Q‑value lookup using full state.  
- **Student**: Tabular Q‑learner over observable state plus a scalar weight `λ` supplied by the Teacher.  
- **Baseline Estimator**: Monte‑Carlo estimator of a random‑policy state‑value `V_baseline(s)` (observable only).  

### 3. Training Regimes
| Regime | Weight λ | Loss |
|--------|----------|------|
| **Uniform** | Fixed `λ = 1.0` | `L = -∑_a π_T(a|s) log π_S(a|s)` |
| **DOPD** | Dynamic `λ = σ(A_gap)` (sigmoid) or min‑max normalized when range < 0.1 | Same distillation loss weighted by `λ`. |
| **Control (random λ)** | Uniform random `λ ∈ [0,1]` (optional sanity check) | — |

*Advantage Gap*: `A_gap(s,a) = Q_T(s,a) – V_baseline(s)`.  
*Dynamic λ*:  
- If `max(A_gap) – min(A_gap) ≥ 0.1` → `λ = σ(A_gap)`.  
- Else → `λ = (A_gap – min) / (max – min)` (min‑max fallback).  

Safety checks ensure no division‑by‑zero; fallback defaults to `λ = 1.0`.

### 4. Evaluation Protocol (Generalization Test)
1. **Unmasked Evaluation** – Teacher supplies λ computed from full state (including `H`).  
2. **Masked Evaluation** – λ is set to a neutral constant `0.5`; the privileged variable `H` is not used anywhere in the Student’s observation.  
3. **Performance Drop**:  
   \[
   \text{drop} = \frac{\text{accuracy}_{\text{unmasked}} - \text{accuracy}_{\text{masked}}}{R_{\max}}
   \]
   where `R_max = 1.0` (maximum possible reward).  

### 5. Statistical Analysis
- **Metric**: Drop per seed for each regime.  
- **Test**: One‑tailed Mann‑Whitney U (`alternative='less'`) comparing DOPD vs. Uniform.  
  - *Rationale*: H2 predicts that DOPD’s drop is **smaller** than Uniform’s; thus we test whether the Uniform distribution is stochastically greater.  
- **Multiple Comparisons**: Only one primary comparison → no correction needed.  
- **Sample Size**: 50 independent seeds per regime (minimum recommended for non‑parametric tests).  
- **Effect Size**: Cliff’s Δ; if `< 0.5` the study is flagged **exploratory** per FR‑005.  
- **Coefficient of Variation (CV)**: `std / mean` of generalization accuracy across seeds, reported in the final summary.  

### 6. Compute Feasibility
- All algorithms are tabular and run in **O(S·A)** time; with S ≈ 100 (10×10 grid) and A = 4, even 10 k total steps finish well under the 6‑hour CI limit on CPU.  
- No GPU is required; the plan respects the CPU‑first mandate.  

### 7. Decision / Rationale
- **Pure‑Python** environment satisfies Constitution VI and eliminates any hidden neural dynamics.  
- **Mann‑Whitney U** is robust to the non‑normal distribution typical of RL accuracy scores.  
- **Dynamic λ with fallback** guarantees meaningful weighting even in trivial environments, addressing FR‑002 edge cases.  
- **50 seeds** provide adequate power while staying within compute limits.  

### 8. Dataset Strategy
No external dataset is needed. All data (transitions, logs, results) are **synthetically generated** by `PrivilegedGridEnv`. The synthetic pipeline is fully deterministic given a seed, fulfilling reproducibility requirements.  

*Verified external resources*: None required; the implementation relies solely on open‑source Python packages (`numpy`, `scipy`, `pyyaml`, `pytest`).  

---  
*All functional requirements (FR‑001 – FR‑008) and success criteria (SC‑001 – SC‑005) are explicitly addressed in the methodology above.*

