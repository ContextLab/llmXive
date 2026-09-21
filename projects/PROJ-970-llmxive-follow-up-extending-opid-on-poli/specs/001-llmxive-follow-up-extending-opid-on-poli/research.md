# Research: OPID Critical-First Routing Complexity Analysis

## Problem Statement
The "Critical-First" routing mechanism in OPID distills hindsight skills into a policy. We hypothesize a **non-monotonic** relationship between the routing threshold (skill injection density) and performance:
1.  **Low Threshold (High Injection)**: In simple (Tier 1) environments, excessive injection may "over-constrain" the policy, reducing adaptability and success (policy rigidity).
2.  **High Threshold (Low Injection)**: In complex (Tier 3) environments, insufficient injection may fail to provide necessary guidance, leading to low success rates.
3.  **The "Sweet Spot"**: An optimal threshold exists that shifts based on environment complexity.

## Dataset Strategy

| Dataset Name | Source / Type | Usage | Verification Status |
| :--- | :--- | :--- | :--- |
| **Synthetic State-Graph Suite** | `networkx` (Programmatic Generation) | Primary experimental environment. Tiers 1-3 generated on-the-fly. | **Verified**: No external URL needed. Generation logic is deterministic via seed. |
| **OPID Algorithm** | `projects/.../code/` (Internal Implementation) | The agent logic being tested. | **Verified**: No external URL found (per spec). Implementation is self-contained. |

**Rationale**:
- **Synthetic Generation**: Real-world RL datasets with labeled "hindsight skill injection" ground truth do not exist. A synthetic suite allows precise control over complexity (node count, stochasticity, reward sparsity) which is impossible with static datasets.
- **Feasibility**: Generating graphs via `networkx` is computationally trivial (CPU-only) and fits within the -hour window.
- **No External Dependencies**: Avoids the "access-gated data" failure mode. No credentials or download limits apply.

## Methodology

### 1. Environment Generation (NetworkX)
- **Tier 1 (Deterministic)**: 5-10 nodes. Single unique path. Zero stochastic branching. (T011)
- **Tier 2 (Stochastic)**: 20-50 nodes. Multiple branching paths. Stochastic transition probabilities (p < 1.0). (T012)
- **Tier 3 (High-Entropy)**: 100+ nodes. Sparse rewards. High-entropy transitions. (T013)
- **Validation**: Every graph is validated to ensure a path from `start` to `goal` exists. If not, regeneration occurs (seeded). (T014, T015)

### 2. OPID Agent & Routing Threshold
- **Threshold ($\tau$)**: Scaled 0.0 to 1.0.
- **Injection Logic**: For eligible actions, a Bernoulli trial with $p = 1 - \tau$ determines if a hindsight skill signal is injected. (T018, T019)
  - $\tau = 0.0 \implies p=1.0$ (Always inject).
  - $\tau = 1.0 \implies p=0.0$ (Never inject). (T020)
- **Policy Head**: **Stochastic Softmax Policy** with a baseline temperature parameter. This ensures the policy has non-zero action entropy variance, allowing the injection mechanism to demonstrably reduce (over-constrain) this variance. (Addresses methodology-e6209717, scientific_soundness-d6aa6933)

### 3. Experimental Design
- **Sweep**: $\tau \in \{0.0, 0.1, \dots, 1.0\}$ (11 steps). (T023)
- **Replicates**: 1,000 episodes per ($\text{Tier}, \tau$) pair. (T024)
- **Total Episodes**: $3 \times 11 \times 1000 = 33,000$.
- **Streaming**: Episodes processed sequentially. Intermediate trajectory data discarded after metric calculation to stay within 7GB RAM. (T025)
- **Baseline Condition**: The run with $\tau=1.0$ (no injection) serves as the control baseline for calculating "success rate improvement".

### 4. Metrics
- **Success Rate**: % of episodes traversing the ground-truth path. (T026)
- **Policy Rigidity**: **Conditional Variance Reduction**. Instead of regressing out $\tau$ (which is deterministic), we calculate the variance of action entropy *given* an injection event versus *given* no injection event within the same $\tau$ bin. The reduction in variance due to injection is the "rigidity" metric. This isolates the behavioral effect from the statistical noise of the injection mechanism. (Addresses methodology-9c7c4f5b, scientific_soundness-eec7a0b1)
- **Distillation Cost-Benefit Ratio**: **Mean Log-Probability Shift** / **Success Rate Improvement**.
  - *Formula*: $\frac{\text{Mean Log-Prob Shift}}{\text{Success Rate}_{\tau} - \text{Success Rate}_{\text{Baseline}}}$
  - *Baseline*: Success Rate at $\tau=1.0$ for the same Tier.
  - This measures the efficiency of the injection relative to the control. It prevents tautology by comparing the *marginal* gain in success against the *cost* (log-prob shift) of the injection, rather than just the raw success rate. (Addresses scientific_soundness-39fdef93, spec_coverage-a1770422)

## Statistical Rigor

- **Multiple Comparisons**: The analysis of three tiers constitutes a family of tests. A **Bonferroni correction** will be applied if individual tier comparisons are reported as significant to control the Family-Wise Error Rate (FWER).
- **Power Analysis**: Based on G*Power (ANOVA, $f=0.25, \alpha=0.05, \text{power}=0.80$), $N=1,000$ per group is the minimum required. This meets the spec's FR-003.
- **Causal Framing**: Since the environment is synthetic and $\tau$ is manually controlled in a randomized design (across episodes), the findings support a **causal claim** that changing $\tau$ causes a change in success rate within the defined environment. The design is an RCT. (Addresses methodology-8bf544d7)
- **Collinearity**: $\tau$ and action entropy are definitionally related. We report the **conditional variance reduction** (policy rigidity) rather than claiming independent predictive effects of $\tau$ on rigidity.

## Compute Feasibility

- **CPU-First**: All operations (graph gen, policy execution, stats) use `numpy`, `scipy`, and `networkx`. No CUDA required.
- **Memory**: Sequential processing ensures memory usage is $O(\text{max\_path\_length})$, not $O(\text{total\_episodes})$.
- **Time**: [deferred] episodes on a lightweight stochastic policy is estimated to complete in < 2 hours on a 2-core runner, well within the 6-hour limit.

## Decision / Rationale

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Graphs** | Real datasets lack the specific "hindsight skill" ground truth required. Synthetic allows exact control over complexity variables. |
| **Stochastic Softmax Policy** | A rule-based policy has zero entropy, making "variance reduction" unmeasurable. A stochastic policy provides a baseline variance that the injection mechanism can reduce, isolating the "over-constraining" effect. |
| **Sequential Streaming** | A substantial volume of trajectory data would exceed 7GB RAM. Streaming allows the full dataset to drive results without memory overflow. |
| **Conditional Variance Metric** | Regressing out $\tau$ from a variable defined by $\tau$ yields only noise. Comparing conditional distributions (injection vs. no-injection) isolates the behavioral effect of the mechanism. |
| **Causal Framing** | The threshold $\tau$ is the manipulated independent variable. The design supports causal inference within the synthetic environment. |
| **Cost-Benefit Baseline** | Using $\tau=1.0$ as the baseline for success rate improvement prevents division by zero and ensures the metric measures marginal benefit, not just raw correlation. |