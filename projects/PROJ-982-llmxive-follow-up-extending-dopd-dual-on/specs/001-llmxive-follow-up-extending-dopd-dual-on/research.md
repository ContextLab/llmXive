# Research: 001-dopd-discrete-mdp

## 1. Problem Statement & Hypothesis

**Problem**: In on-policy distillation, a Student agent may achieve high training accuracy by mimicking a Teacher who possesses privileged information (e.g., hidden state `H`). This creates a "privilege illusion" where the Student appears competent but fails catastrophically when deployed in environments where `H` is unavailable.

**Hypothesis**: Dual On-policy Distillation (DOPD), which dynamically weights the distillation loss based on the Teacher's advantage gap, will mitigate this illusion. Specifically, DOPD will encourage the Student to rely more on self-supervision (reinforcement) when the Teacher's advantage is low (indicating the Teacher's action is not uniquely optimal given the observable state), leading to a smaller performance drop during masked evaluation compared to Uniform Distillation.

**Null Hypothesis (H0)**: There is no difference in the mean generalization accuracy drop between DOPD and Uniform regimes, or Uniform is better.
**Alternative Hypothesis (H1)**: DOPD results in a statistically significantly smaller performance drop than Uniform (one-tailed Mann-Whitney U test).

## 2. Dataset Strategy

This project utilizes a **synthetic, simulated dataset** generated on-the-fly via a custom discrete MDP environment. No external static dataset is used for training or evaluation, as the "privilege illusion" requires a controlled generation process where the privileged variable `H` can be explicitly masked.

**Data Source**:
- **Generation**: `code/env/privilege_mdp.py` (Custom implementation based on `gymnasium`/`minigrid` principles).
- **Mechanism**: The environment generates states `(O, H)` where `O` is observable and `H` is privileged. The Teacher observes `(O, H)`, the Student observes `O`.
- **Reference to Verified Datasets**: While the spec mentions verified HuggingFace datasets (e.g., `cjhyeok/mdpo_train_demo`), these represent *pre-existing* MDP trajectories that do not inherently contain the specific "privileged variable masking" logic required for this experiment. Therefore, the project generates its own data to ensure the "hidden state" condition is strictly enforced. The verified URLs provided in the spec input are acknowledged as examples of MDP data formats but are not the primary data source for this specific experiment due to the lack of explicit "privileged variable" fields in standard public MDP dumps.

**Data Characteristics**:
- **Type**: Discrete state-action trajectories.
- **Size**: Generated dynamically per seed (approx. [deferred] steps per episode).
- **Variables**: `state_id`, `full_state`, `student_observation`, `teacher_observation`, `privileged_variable`, `action`, `reward`, `next_state`, `done`, `seed`.

## 3. Methodology

### 3.1 Environment Construction (FR-001, US-1)
A custom grid-world MDP will be implemented using `gymnasium`.
- **State Space**: `S = O × H`. `O` (observable) is a subset of grid features; `H` (privileged) is a hidden variable (e.g., a specific grid cell content or agent direction not visible to the Student).
- **Observation Space**:
  - Teacher: `O × H`
  - Student: `O`
- **Transitions**: Standard grid-world dynamics (move up/down/left/right).
- **Reward**: +1 for reaching goal, -1 for hitting walls, -0.01 for each step (to ensure V_random is non-degenerate and well-defined).
- **Constraint**: Grid size capped at a moderate scale. to ensure Q-tables fit in memory (FR-008).
- **H-Criticality**: The environment is designed such that in specific states, the optimal action *depends* on `H`. In these states, the Teacher's optimal action differs from the action optimal given only `O`.

### 3.2 Training Regimes (FR-002, FR-003, US-2)

#### Pre-training Phase (Teacher)
Before Student training begins, the **Teacher** (Oracle) is pre-trained to convergence using tabular Q-learning with full access to `(O, H)`. This produces a static, optimal Q-table `Q*_teacher` and a value function `V*_teacher`. This ensures the Advantage signal is a ground-truth property of the MDP, not a dynamic learning artifact.

#### Uniform On-Policy Distillation
- **Logic**: Student loss = `KL(Student(action|O) || Teacher(action|O,H))`.
- **Weighting**: Fixed weight `w = 1.0` regardless of Teacher confidence or advantage.
- **Goal**: Establish the "privilege illusion" baseline where the Student blindly mimics the Teacher's reliance on `H`.

#### Dual On-policy Distillation (DOPD)
- **Logic**: Student loss = `w * KL(...) + (1-w) * SelfSupervision(...)`.
- **Advantage Gap Calculation**:
  - **Definition**: `Advantage = Q*_teacher(s,a) - V_random(s)`.
    - `Q*_teacher(s,a)`: The optimal action-value from the *pre-trained* Teacher Oracle (using full state `O,H`).
    - `V_random(s)`: The state-value of a *random policy* (pre-computed or estimated).
    - *Note*: This definition adheres to FR-002. The use of `V_random` (not `V*`) is critical to measure the advantage relative to a baseline that does *not* use `H`.
  - **Degeneracy Handling**: If the dynamic range of this gap (`max - min`) is < 0.1, the system **MUST** switch to min-max normalized advantage baseline (FR-002) to ensure meaningful weighting.
- **Weighting**: `w = sigmoid(Advantage)`. High advantage -> mimic Teacher; Low advantage -> rely on self-supervision.
- **Rationale**: In H-Critical states, the Teacher's `Q*` (using H) will be high for the optimal action, while `V_random` (using only O) will be lower, resulting in a high Advantage. The Student uses this signal to weigh the Teacher's action. However, if the Student's own learned Q (from O) disagrees with the Teacher's H-dependent action, the DOPD mechanism (via the `1-w` self-supervision term) encourages the Student to explore alternatives, mitigating the illusion.

### 3.3 Generalization & Evaluation (FR-004, FR-007, US-2)
- **Test Environment**: Distinct random seed from training.
- **H-Critical State Filter**: Evaluation is performed **only** on the subset of test states where the optimal action depends on `H` (i.e., `argmax_a Q*_teacher(O,H) != argmax_a Q*_student(O)`). This ensures the metric directly measures the privilege illusion.
- **Metric 1: Mimicry Fidelity (Unmasked)**: The Student's accuracy in reproducing the Teacher's action *when the Teacher's action is provided as a target*. This measures if the Student learned the Teacher's policy.
- **Metric 2: Autonomous Performance (Masked)**: The Student's accuracy when acting on its *own* learned policy (no Teacher action target) in H-Critical states.
- **Drop Calculation**: `Drop = (Mimicry Fidelity - Autonomous Performance) / R_max`.
  - This measures the loss of performance when the Student must act autonomously in H-Critical states, isolating the "illusion" (thinking it knows the action because it mimicked the Teacher) from the reality (it cannot execute the action without H).

### 3.4 Statistical Analysis (FR-005, US-3)
- **Test**: One-tailed Mann-Whitney U test.
- **Input**: Generalization accuracy drops (from the H-Critical subset) from 50 independent seeds for both regimes.
- **Hypothesis**: `DOPD_Drop < Uniform_Drop`.
- **Power Analysis**: 50 seeds target sufficient power for moderate effect sizes (≥0.5). If effect size < 0.5, results are flagged as exploratory.
- **Significance**: Alpha = 0.05.

## 4. Compute Feasibility

- **CPU-First**: The entire simulation uses tabular Q-learning and discrete math. No neural networks or GPU operations are required.
- **Memory**: Q-tables for 5x5 grid with discrete observations will occupy <10 MB.
- **Time**: Multiple seeds × 1000 steps × 2 regimes [deferred] steps. Python loop overhead is negligible; total runtime expected < 30 minutes on 2 CPU cores.
- **Escape Hatch**: Not required. The method is inherently CPU-tractable.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Advantage Gap Degeneracy** | If `Advantage` is always zero, DOPD collapses to Uniform. | Implement min-max normalization fallback (FR-002) and ensure MDP rewards prevent V_random degeneracy. |
| **Grid Size Explosion** | Q-table exceeds RAM. | Hard cap grid size at 5x5 (FR-008). |
| **Statistical Noise** | High variance in small grid worlds masks effect. | Increase seeds to 50 (FR-005); use non-parametric Mann-Whitney U test; filter for H-Critical states. |
| **Privileged Signal Irrelevance** | If `H` is noise, no illusion to test. | Ensure `H` is correlated with optimal action in environment design (H-Critical states). |

## 6. Decision/Rationale

- **Why Synthetic Data?** Real-world MDP datasets do not provide the granular control to mask specific state variables (`H`) while keeping `O` constant. A custom simulator is the only way to isolate the "privilege illusion" variable.
- **Why Tabular?** Neural networks introduce optimization dynamics (gradient descent, local minima) that confound the study of the *distillation logic* itself. Tabular methods provide a ground-truth baseline.
- **Why Mann-Whitney U?** Generalization accuracy distributions in small MDPs may not be Gaussian. Mann-Whitney U is robust to non-normality.
- **Why Pre-trained Teacher?** To ensure the Advantage signal is a static ground-truth property of the MDP (reflecting the true necessity of H) rather than a noisy, dynamic learning artifact from the Student's own Q-table.