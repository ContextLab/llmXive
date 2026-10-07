# Research: OPID Critical-First Routing Complexity Analysis

## Executive Summary

This research investigates the hypothesis that "critical-first" skill injection in the OPID framework exhibits a **non-monotonic relationship** with policy performance, particularly in low-complexity environments. We posit that while moderate skill injection improves performance, excessive injection in deterministic (Tier 1) environments leads to "policy rigidity" (over-constraining), reducing the agent's ability to adapt and lowering success rates. We will validate this by sweeping a routing threshold (0.0 to 1.0) across three synthetic complexity tiers.

## Theoretical Background

The OPID framework leverages hindsight skill distillation to improve agentic RL performance. The "critical-first" routing mechanism controls the density of these injections. While intuition suggests more supervision is better, theoretical concerns regarding **over-supervision** suggest that in low-entropy environments, dense injection may suppress the policy's natural exploration and entropy, leading to brittle behaviors. This study aims to quantify the "distillation cost-benefit ratio" and identify the inflection point where the marginal cost of rigidity outweighs the benefit of skill injection.

## Dataset Strategy

### Verified datasets
- **OPID**: NO verified source found (do NOT cite a URL for it). The logic is derived from the project's internal specification.
- **Synthetic State-Graph Environments**: Generated procedurally using `networkx`. No external dataset URL is required or applicable. The data is created on-the-fly by the `src/environment/graph_generator.py` module.

**Rationale**: Real-world RL datasets with labeled "hindsight skill injection" ground truth do not exist. The synthetic environment approach is the only feasible method to control complexity tiers (Tier 1, 2, 3) and isolate the routing threshold as a variable.

### Data Generation Strategy

1.  **Tier 1 (Deterministic)**: Graphs with 5-10 nodes. **Crucially, these graphs will contain multiple valid paths** (or stochastic transitions with p=1.0 but multiple edges) to ensure the baseline policy has non-zero entropy, making the "over-constraining" hypothesis empirically testable.
2.  **Tier 2 (Stochastic)**: Graphs with 20-50 nodes, multiple branching paths, stochastic transitions (p=0.8).
3.  **Tier 3 (High-Entropy)**: Graphs with 100+ nodes, sparse rewards (per ~10 nodes), high-entropy transitions.

*Note on Complexity Parameters*: The specific node counts (5-10, 20-50, 100+) are based on **standard practices in synthetic RL benchmarking** (e.g., MiniGrid, ProcGen) for defining low, medium, and high complexity tiers.

**Feasibility Check**: The generator will validate that a valid path exists before returning a graph. If a stochastic pruning event disconnects the goal, the graph is regenerated.

### Graph-Level Splitting Strategy (for SC-002)

To ensure the "Distillation Cost-Benefit Ratio" is measured against a true held-out set:
1.  Generate a pool of unique graph IDs for each tier.
2. **Split the pool**: [deferred] of graph IDs are assigned to the **Training Set**, [deferred] to the **Validation Set**.
3.  **Episode Generation**: All 1,000 episodes per threshold/tier are generated using graphs **only from the Training Set**.
4.  **Metric Calculation**: The "Distillation Cost-Benefit Ratio" (SC-002) is calculated **exclusively** using the **Validation Set** graphs. Both the numerator (log-prob shift) and denominator (success rate improvement) are derived from this held-out set, ensuring no data leakage and valid generalization.

## Statistical Methodology

### Power Analysis for Quadratic Effects (SC-001)
Detecting a significant quadratic coefficient ($\beta_2$) often requires larger sample sizes than detecting a linear trend.
- **Assumption**: We assume a small-to-medium effect size ($f^2 \approx 0.15$) for the curvature, consistent with typical findings in RL sensitivity analyses.
- **Justification**: Based on G*Power guidelines for polynomial regression, N=1,000 per setting provides >95% power to detect this effect size at $\alpha=0.05$. This N is conservative but necessary to robustly identify the non-monotonic inflection point. If the effect is smaller, the study may be underpowered, but N=1,000 represents the maximum feasible budget.

### Primary Analysis: Non-Monotonicity (SC-001)
We will fit a **Generalized Linear Model (GLM)** with a binomial family and logit link to model the binary success outcome, avoiding the homoscedasticity violations of linear regression on proportions:
$$ \text{logit}(\text{Success Rate}) = \beta_0 + \beta_1(\text{Threshold}) + \beta_2(\text{Threshold}^2) + \epsilon $$
*   **Hypothesis**: $\beta_2$ will be significantly negative ($p < 0.05$) for Tier 1, indicating an inverted U-curve.
*   **Method**: `statsmodels.GLM` with `family=sm.families.Binomial()`. P-values derived from the Wald test on coefficients.

### Secondary Analysis: Policy Rigidity (FR-004, SC-003)
"Policy rigidity" is defined as the **residual variance of action entropy** after regressing out the **deterministic effect** of the threshold.
*   **Correction for Non-Monotonicity**: Since the hypothesis posits a **non-monotonic** (inverted U) relationship, a linear regression cannot correctly model the deterministic trend. **A linear model would leave the curvature in the residuals, conflating 'rigidity' with 'model misspecification'.**
*   **Model**: We will use a **Quadratic Regression** to model the expected entropy:
    $$ \text{Entropy} = \alpha_0 + \alpha_1(\text{Threshold}) + \alpha_2(\text{Threshold}^2) + \epsilon $$
*   **Calculation**: 
    1. Fit the quadratic model to the observed entropy data.
    2. Compute Residuals $R = \text{Observed Entropy} - \text{Predicted Entropy}$.
    3. Rigidity = $\text{Var}(R)$.
*   **Rationale**: This isolates the variance in entropy not explained by the threshold's non-linear trend, capturing the true "over-constraining" effect without conflating it with model misspecification.

### Interaction Analysis (SC-004)
We will perform a **Polynomial Regression with Interaction Terms** rather than a Two-Way ANOVA, as Threshold is a continuous variable.
*   **Model**: $\text{Success Rate} \sim \text{Threshold} + \text{Threshold}^2 + \text{Tier} + (\text{Threshold} \times \text{Tier}) + (\text{Threshold}^2 \times \text{Tier})$.
*   **Hypothesis**: The interaction terms ($\text{Threshold}^2 \times \text{Tier}$) will be significant, indicating the curvature (non-monotonicity) differs by complexity tier.
*   **Correction**: Bonferroni correction will be applied if multiple tier-specific comparisons are reported to control family-wise error rate.

### Distillation Cost-Benefit Ratio (SC-002)
*   **Metric**: $\frac{\text{Mean Log-Prob Shift (Val Set)}}{\text{Success Rate}_{\text{Full (Val Set)}} - \text{Success Rate}_{\text{Baseline (Val Set)}}}$
*   **Baseline**: Success rate at Threshold=1.0 (no injection) calculated on the **Validation Set**.
*   **Validation Set**: The **held-out validation set** (A subset of graph IDs) is used for **both** the numerator and denominator, ensuring the ratio measures generalization performance and not overfitting.

## Compute Feasibility & Compute Strategy

### CPU-First Strategy
The entire experiment is designed to run on a **CPU-only** environment (GitHub Actions free-tier: cores, ~7GB RAM).
*   **Model**: A lightweight, rule-based or small neural policy head (if needed) that runs efficiently on CPU. No large transformers.
*   **Data Streaming**: Episodes are processed sequentially. Intermediate trajectory data is discarded immediately after metric calculation to keep memory usage < 500MB.
*   **Parallelism**: Threshold sweeps for different tiers can be parallelized across available CPU cores, but episodes within a tier/threshold are sequential to ensure strict reproducibility.

### Graceful Degradation
If the estimated runtime for [deferred] episodes per setting exceeds a substantial duration (detected via `src/config.py` feasibility check):
1.  The system will **reduce N** (e.g., to 500 episodes) rather than failing.
2.  The reduction will be logged, and the statistical power limitation will be explicitly noted in the final report.
3.  This ensures the experiment completes and yields *some* results rather than a hard failure.

### GPU Escape Hatch (Not Required)
No GPU is required for this study. The synthetic environment generation and lightweight policy execution are fully tractable on CPU.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Quadratic Regression for Rigidity** | Required to capture the "non-monotonic" deterministic effect of the threshold on entropy, as linear models would fail to satisfy FR-004's definition of "residual variance" in a non-monotonic context and would conflate curvature with rigidity. |
| **GLM for Success Rate** | Required because Success Rate is a binary outcome; linear regression on proportions violates normality assumptions. GLM with binomial family ensures valid p-values. |
| **Polynomial Regression with Interactions** | Required because Threshold is continuous; ANOVA treats it as categorical, losing resolution and power. Interaction terms allow testing if curvature differs by tier. |
| **Graph-Level Splitting** | Required by SC-002 to prevent overfitting the log-prob shift metric to the specific graphs used for training. |
| **Held-Out Validation Set for Cost-Benefit** | Ensures both numerator and denominator are derived from the same unseen data, preventing circular validation. |
| **Sequential Processing** | Ensures memory footprint remains low (<7GB) and avoids race conditions in parallel execution. |
| **Graceful Degradation** | Addresses the "binary fail-or-run" flaw; ensures partial results are generated if time limits are tight. |

## Limitations

- **Synthetic Validity**: The results are limited to the specific topology of the generated graphs. Real-world environments may have different complexity structures.
- **Policy Head Simplicity**: The use of a lightweight policy head may not fully capture the dynamics of large-scale LLM agents, though it suffices for the "over-constraining" hypothesis.
- **Power Limitations**: If N is reduced due to time constraints, the power to detect small effect sizes will be lower. The N=1,000 target is justified for small-to-medium effects but may be insufficient for very subtle curvature.