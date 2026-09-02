# Research: llmXive follow-up: extending "DOPD: Dual On-policy Distillation"

## Research Question

Does the "privilege illusion" phenomenon emerge in discrete, non-differentiable MDPs, and can DOPD (Dual On-policy Distillation) mitigate it without neural optimization?

## Hypothesis

**H1**: In a discrete MDP where the optimal policy requires a hidden privileged variable $H$, a Student agent trained via **Uniform Distillation** will achieve high training accuracy by mimicking the Teacher (who sees $H$) but will suffer a significant performance drop when $H$ is masked during evaluation (the "privilege illusion").

**H2**: A Student agent trained via **DOPD** (which down-weights Teacher actions when the advantage gap is low) will exhibit higher robustness to the masking of $H$, resulting in a significantly smaller performance drop compared to the Uniform regime.

## Methodology

### 1. Environment Construction (Discrete MDP)
We will construct a synthetic Grid-World MDP using `gym-minigrid`.
- **State Space**: $S = (O, H)$, where $O$ is the observable grid (walls, goal, agent) and $H$ is a hidden variable (e.g., a specific color flag or internal state bit).
- **Observation Space**: Student observes only $O$. Teacher observes $(O, H)$.
- **Transition Dynamics**: Deterministic or stochastic grid movement.
- **Reward**: +1 for reaching the goal, -0.1 per step, -1 for hitting a wall.
- **Optimality Condition**: The optimal path requires knowing $H$ (e.g., $H$ determines which of two identical-looking doors is safe).
- **Control Condition**: A second environment variant where the optimal policy is **independent** of $H$. This allows us to isolate the "illusion" effect from general learning failure.

### 2. Agent Architectures (Tabular)
- **Teacher**: Oracle policy $\pi^*(s) = \arg\max_a Q^*(s, a)$. Has full access to $S=(O, H)$.
- **Student**: Tabular Q-table $Q_s(O, \lambda)$. **Augmented State**: The Student's observation is augmented with a scalar $\lambda$ (the advantage weight) provided by the Teacher. This allows the Student to learn a policy conditioned on the Teacher's confidence without seeing $H$.
- **Baseline Estimator**: A separate agent running a random policy to estimate $V_{rand}(s)$ for the advantage calculation.

**Baseline Computation (Critical)**:
- **Algorithm**: Monte Carlo estimation of a random policy.
- **Steps**: For each state $s$, run [deferred] random episodes.
- **Convergence**: Stop if std dev of returns < 0.01 for 100 consecutive batches.
- **Seed Independence**: Baseline generation uses a distinct seed set to ensure no overlap with training or evaluation seeds.
- **Marginalization**: The baseline averages over $H$, providing a valid value for the observable state $O$.

### 3. Training Regimes

#### A. Uniform On-Policy Distillation (Baseline)
The Student mimics the Teacher's action distribution with fixed weight $\lambda = 1.0$:
$$ L_{uniform} = -\sum_a \pi_{teacher}(a|s) \log \pi_{student}(a|s) $$
No adaptive weighting; the Student blindly copies the Teacher even when the Teacher relies on $H$.

#### B. Dual On-Policy Distillation (DOPD)
The Student dynamically weights the distillation loss based on the **Advantage Gap**:
$$ A_{gap}(s, a) = Q_{teacher}(s, a) - V_{baseline}(s) $$
Where $V_{baseline}(s)$ is the value of a random policy (computed via Monte Carlo).

**Dynamic Weighting Logic**:
1. Teacher computes $A_{gap}$ using full state $(O, H)$.
2. Teacher calculates weight $\lambda = \sigma(A_{gap})$ (sigmoid normalization).
3. **Fallback**: If $\max(A_{gap}) - \min(A_{gap}) < 0.1$ (measured on the current batch), switch to **min-max normalization** of the current batch values to ensure non-degenerate weights.
4. Teacher appends $\lambda$ to the Student's observation vector.
5. Student updates $Q_s(O, \lambda)$ based on the weighted loss.

**Safety**: Explicit checks for zero denominators in advantage calculations (sparse signals) ensure $\lambda$ defaults to 1.0 if the gap is undefined.

#### C. Randomized Weight Control (Non-Triviality Check)
To prove the advantage gap is the causal factor (not just the presence of a weight), we run a control where the weight $\lambda$ is sampled uniformly from $[0, 1]$ regardless of the gap. If DOPD outperforms this control, the advantage gap is validated as a meaningful signal.

#### D. Non-Triviality Check (Noise Injection)
We will test a scenario where Gaussian noise ($\sigma = 0.1 \times \text{Q-range}$) is added to the advantage gap before weighting. DOPD is expected to degrade gracefully, whereas Uniform remains static. This confirms the advantage gap is a useful, non-trivial signal.

### 4. Evaluation Protocol (Generalization Test)
- **Training Phase**: Run for $T$ steps. Teacher computes $\lambda$ and passes it to Student.
- **Evaluation Phase**: 
  1. **Unmasked**: Evaluate Student with $\lambda$ derived from the Teacher's optimal policy (simulating ideal Teacher guidance).
  2. **Masked**: Evaluate Student with $\lambda$ set to a neutral default (0.5). **Note**: The Student architecture (Q-table) supports $\lambda$ in both cases, so the "drop" measures reliance on the *signal* $\lambda$ (which encodes $H$-dependency) rather than $H$ itself.
- **Metric**: Performance Drop = $(Accuracy_{unmasked} - Accuracy_{masked}) / R_{max}$.
- **Hypothesis Test**: Compare Drop(DOPD) vs. Drop(Uniform) using **one-tailed Mann-Whitney U test** (non-parametric, robust to non-normal distributions).
  - $H_0$: mean(Drop_DOPD) <= mean(Drop_Uniform)
  - $H_1$: mean(Drop_DOPD) > mean(Drop_Uniform)
- **Power**: $N=50$ independent seeds. If effect size $< 0.5$, explicitly label as "exploratory".
- **Control Comparison**: Compare Drop(H-Dependent) vs. Drop(H-Irrelevant). We hypothesize DOPD reduces the drop specifically in the H-Dependent case.

## Dataset Strategy

Since this is a synthetic simulation, no external dataset is required. The "data" is generated procedurally by the `code/env/privileged_grid.py` module.

- **Source**: `gym-minigrid` (verified open-source library).
- **Generation**:
  - Grid size: Maximized to fit within available RAM constraints (maximized within feasible bounds).
  - Seeds: Multiple distinct random seeds for training, multiple distinct seeds for evaluation, and multiple distinct seeds for baseline.
  - Data Format: JSON logs of transitions $(O, \lambda, a, r, O', \text{TeacherAction})$.
- **Verified Access**: The environment is instantiated via `gym.make("MiniGrid-Empty-5x5-v0")` (or custom registered env). The "privileged variable" is injected as a hidden attribute in the environment's `info` dict, accessible only to the Teacher agent logic.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: Only one primary hypothesis (DOPD vs. Uniform on Drop metric) is tested per seed set. No family-wise error correction is needed for a single pairwise comparison, but the p-value is reported with standard alpha.
- **Sample Size**: A sufficient number of seeds is the minimum recommended for stable non-parametric tests.
- **Causal Assumptions**: This is a controlled simulation. Causal claims are limited to the causal effect of the training algorithm on the learned policy within the simulated MDP.
- **Collinearity**: The Student's observation $O$ is strictly a projection of $S$. $H$ is orthogonal to $O$ by construction.
- **Compute Feasibility**: 
  - **CPU-First**: Tabular Q-learning is $O(S \cdot A)$. For a 10x10 grid with 4 actions, $S \approx 100$, $A=4$. 50 seeds $\times$ 1000 steps = 50,000 updates. Trivial for CPU.
  - **GPU Escape Hatch**: Not required. If future extensions add neural nets, the plan would shift to a scaled-down GPU run on Kaggle.

## Decision/Rationale

- **Why Tabular?**: To strictly isolate the "privilege illusion" from neural network optimization dynamics (convergence issues, local minima).
- **Why Mann-Whitney U?**: Generalization accuracy distributions in reinforcement learning are often non-normal; U-test is robust.
- **Why 50 Seeds?**: To ensure statistical power for moderate effect sizes and to satisfy FR-005.
- **Why Min-Max Fallback?**: To handle edge cases where the environment is trivial and the advantage gap is near-zero, preventing division-by-zero or degenerate weights.
- **Why Weight Injection?**: To allow the Student to utilize the Teacher's confidence signal without violating the information asymmetry constraint (Student cannot see $H$).
- **Why Monte Carlo Baseline?**: To ensure the baseline value function is estimated with sufficient accuracy (std dev < 0.01) to provide a meaningful advantage gap signal.