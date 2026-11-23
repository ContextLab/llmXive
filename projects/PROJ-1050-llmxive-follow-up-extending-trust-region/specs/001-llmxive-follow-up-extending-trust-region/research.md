# Research: llmXive follow-up: extending "Trust Region Policy Distillation"

## Problem Statement

Current distillation methods often fail to transfer complex reasoning strategies when the student model has a significantly lower "cognitive horizon" (capacity to execute long chains of thought) than the teacher. This research investigates the hypothesis that a mismatch between teacher depth and student horizon, combined with a high interpolation coefficient $\alpha$ in Trust Region Policy Distillation (TOP-D), causes the student to collapse into shallow heuristics rather than learning the underlying reasoning structure.

## Methodology

### Experimental Design

The study employs a **Synthetic Reasoning MDP** to generate controlled, deterministic reasoning problems.
1. **Environment**: A graph-based state space where nodes represent partial proofs and edges represent valid inference rules.
2. **Teacher Policy**: An oracle that always selects the optimal path to the solution.
3. **Student Policy**: A parameterized agent with a hard constraint on the maximum number of steps (horizon $H$).
4. **Distillation**: The student is trained using TOP-D, which interpolates between the student's policy distribution and the teacher's distribution using a coefficient $\alpha \in [0, 1]$.

### Variables

| Variable | Type | Levels/Range | Role |
|:--- |:--- |:--- |:--- |
| **$\alpha$ (Interpolation)** | Independent | $\{0.1, 0.3, 0.5, 0.7, 0.9\}$ | Distillation strength |
| **Horizon ($H$)** | Independent | $\{D_{teacher}/2, D_{teacher}, 2 \times D_{teacher}\}$ | Student capacity |
| **Teacher Depth ($D$)** | Control | Fixed (e.g., 8 steps) | Problem difficulty |
| **Effective Depth** | Dependent (Continuous) | Integer (0 to $H$) | Performance metric (for non-collapsed) |
| **Collapse Indicator** | Dependent (Binary) | 0/1 | 1 if `effective_depth <= 0.5 * D` |

### Statistical Analysis

To validly test the hypothesis of "collapse into shallow heuristics" (a binary regime switch) while accounting for depth magnitude, we employ a **Two-Part Model**:

1. **Part 1: Binary Outcome (Collapse Probability)**
 * **Method**: **Logistic Regression** (or Beta-Binomial if aggregating by cell).
 * **Dependent Variable**: `is_collapse` (1 if effective depth $\le 0.5 \times D$, else 0).
 * **Model**: $\text{logit}(P(\text{collapse})) = \beta_0 + \beta_1 \alpha + \beta_2 H + \beta_3 (\alpha \times H)$.
 * **Hypothesis**: $\beta_3$ (interaction) will be significant and negative, indicating that high $\alpha$ combined with low $H$ drastically increases the probability of collapse.
 * **Rationale**: This directly tests the "shallow heuristic" hypothesis as a threshold effect, avoiding the bias of treating a regime switch as a censored value.

2. **Part 2: Continuous Outcome (Depth Magnitude)**
 * **Method**: **Ordinary Least Squares (OLS)** Regression.
 * **Filter**: Applied *only* to episodes where `is_solved == True` AND `effective_depth < student_horizon`. This excludes cases where the student was mechanically capped by the horizon (which would create circularity with the independent variable) or failed to solve.
 * **Dependent Variable**: `effective_depth`.
 * **Model**: $\text{Depth} = \beta_0 + \beta_1 \alpha + \beta_2 H + \beta_3 (\alpha \times H) + \epsilon$.
 * **Hypothesis**: $\beta_3$ will show a non-monotonic or significant interaction, revealing how distillation strength affects the *depth* of valid reasoning when collapse does not occur.

3. **Secondary Test**: **Likelihood Ratio Test** to compare the full interaction model against an additive model for both the Logistic and OLS parts.
4. **Sensitivity Analysis**: Plotting collapse rates across the $\alpha$ sweep to identify the "tipping point".

## Power Analysis & Sample Size Strategy

* **Initial Plan**: $N=100$ episodes per configuration ([deferred] total).
* **Power Concern**: Logistic regression with interaction terms often requires larger samples to detect small-to-medium effect sizes (Cohen's $h$). N=100 may yield low power for the interaction term $\beta_3$.
* **Contingency**: If the initial run yields $p > 0.10$ for the interaction term (inconclusive), the system will automatically re-run with $N=200$ per configuration ([deferred] total).
* **Feasibility**: The tabular student policy and synthetic MDP are computationally lightweight. Increasing N to a sufficiently large scale is estimated to complete within the 6-hour limit on the GitHub Actions CPU runner.

## Dataset Strategy

### Synthetic Data Generation
The primary data source is **synthetically generated** by the `ReasoningMDP` environment implemented in `code/env/reasoning_mdp.py`.
* **Source**: Programmatic generation (no external download required for the core experiment).
* **Feasibility**: The environment generates problems on-the-fly, requiring negligible storage and memory. This ensures [deferred] reproducibility and zero dependency on external data availability.

### Reference Datasets (Contextual)
While the core experiment is synthetic, the following verified datasets were reviewed to ensure the synthetic environment mimics realistic reasoning structures:
* **MDP Taxonomy**: `
 * *Usage*: Reviewed to understand standard inference rule structures. The synthetic environment will abstract these into a simplified graph representation.
* **MDPO Train Demo**: `
 * *Usage*: Reviewed for typical training log formats. The synthetic logs will mirror this structure for compatibility with existing analysis pipelines.

> **Note**: No external dataset is *required* for the experiment. The synthetic generator ensures the exact variables (depth, horizon, $\alpha$) are controlled and known, which is impossible with real-world noisy data.

## Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (2 vCPU, ~7 GB RAM).
* **Strategy**: **CPU-First**.
 * The "Student Policy" will be implemented as a small tabular model or a tiny neural network (<10k parameters) using `numpy`/`scipy`. No `torch` CUDA operations.
 * The statistical analysis will use `statsmodels` (Logistic Regression and OLS) which runs efficiently on CPU.
 * The experimental grid (5 $\alpha$ $\times$ 3 horizons $\times$ 200 episodes = 3,000 runs) is estimated to complete in <3.5 hours on a standard CPU, well within the 6-hour limit.
* **GPU Escape Hatch**: Not required. The problem is defined as a small-scale simulation. If the student policy complexity were to increase (e.g., to a 100M parameter model), the plan would shift to a scaled-down GPU run on Kaggle, but the current spec explicitly targets CPU feasibility.

## Risk Assessment

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Synthetic Environment Validity** | High | The MDP will be unit-tested to ensure ground-truth paths are always solvable (FR-007). |
| **Statistical Power** | Medium | Initial N=100 may be low. Contingency plan to increase to N=200 if interaction p-value > 0.10. |
| **Circularity in Depth Analysis** | Medium | OLS analysis strictly filters for `is_solved == True` AND `effective_depth < student_horizon` to avoid mechanical dependency. |
| **Collapse Definition** | Medium | "Collapse" is defined as effective depth $\le 0.5 \times D$. Sensitivity analysis will test other thresholds (0.4, 0.6) to ensure robustness. |