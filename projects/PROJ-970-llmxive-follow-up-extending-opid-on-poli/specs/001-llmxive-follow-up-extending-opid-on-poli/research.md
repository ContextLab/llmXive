# Research: OPID Critical-First Routing Complexity Analysis

## Research Question

Does the "critical-first" routing mechanism in OPID exhibit a non-monotonic relationship with policy performance across varying environment complexities? Specifically, does increasing the skill injection density (lowering the routing threshold) eventually lead to "over-constraining" (policy rigidity) that reduces success rates in low-complexity (deterministic) environments, while remaining beneficial or neutral in high-complexity (stochastic/high-entropy) environments?

## Background & Context

The OPID (On-Policy Skill Distillation) framework introduces a "critical-first" routing mechanism to inject hindsight skill signals during policy execution. While previous work suggests this improves learning, the spec hypothesizes a "sweet spot" where excessive injection (low threshold) in simple environments may rigidify the policy, reducing adaptability. This research aims to map the performance curve (Success Rate vs. Routing Threshold) across three distinct complexity tiers to identify the inflection point.

## Dataset Strategy

**Dataset Source**: Synthetic State-Graph Environments generated via `networkx`.
**Justification**: As noted in the spec's "Assumptions," no real-world RL dataset with labeled "hindsight skill injection" ground truth exists. Synthetic generation allows precise control over complexity (node count, branching factor, reward sparsity) and ensures reproducibility.

**Verified Datasets**:
- **OPID Paper**: NO verified source found (cited by title only; no URL fabricated).
- **Synthetic Graphs**: Generated internally using `networkx`. No external URL required.

**Data Acquisition Plan**:
1.  **Generation**: The `graph_generator.py` module will instantiate graphs on-demand or cache them with a fixed seed.
    -   **Tier 1**: 5-10 nodes, single deterministic path, zero stochastic branching.
    -   **Tier 2**: 20-50 nodes, multiple branching paths, stochastic transitions.
    -   **Tier 3**: 100+ nodes, sparse rewards, high-entropy transitions.
2.  **Validation**: Each generated graph will be validated to ensure a valid path exists from start to goal (handling the edge case of unreachable goals by regeneration).
3.  **Storage**: Graph seeds and parameters will be logged; the actual graph objects will be transient or stored as pickled objects in `data/raw/` only if necessary for debugging, with checksums applied.

## Methodology

### Experimental Design
- **Independent Variable**: Routing Threshold ($T \in [0.0, 1.0]$) in steps of 0.1.
  -   $T=0.0$: Always inject skill signals.
  -   $T=1.0$: Never inject (baseline).
- **Dependent Variables**:
  1.  **Success Rate**: % of episodes completing the ground-truth path.
  2.  **Policy Rigidity**: **Raw variance** of action entropy across episodes. *Correction*: This measures the unadjusted variability in policy confidence to empirically test the "over-constraining" hypothesis.
- **Control Variables**:
  -   Complexity Tier (1, 2, 3).
  -   Random Seed (fixed per run).
  -   Baseline Policy Architecture (lightweight rule-based).
- **Sample Size**: 1,000 episodes per (Tier, Threshold) combination (Total $3 \times 11 \times [deferred] = 33,000$ episodes).
  -   *Justification*: Based on G*Power analysis for a Two-Way ANOVA and Quadratic Regression to detect interaction effects and non-monotonic terms (f=0.25, α=0.05, power=0.80) as stated in FR-003.

### Statistical Analysis Plan
1. **Descriptive Sweep**: The primary [deferred]-episode sweep (fixed T per tier) is framed as a **descriptive curve-fitting exercise**. We will fit a quadratic model ($y = \beta_0 + \beta_1 T + \beta_2 T^2 + \epsilon$) to visualize the non-monotonic relationship and identify the inflection point. *Caveat*: As the threshold is a fixed deterministic sweep, p-values from this specific sweep are descriptive only.
2.  **Inferential Sub-Study**: To support statistical inference, a secondary **randomized sub-study** will be conducted where the threshold is randomized per episode within each tier. This allows for valid hypothesis testing of the quadratic term (SC-001) and interaction effects (SC-004).
3.  **ANOVA**: Two-way ANOVA (Tier $\times$ Threshold) on the randomized sub-study data to test for interaction effects (SC-004).
    -   *Success Criterion*: Interaction term $p < 0.05$.
4.  **Multiplicity Correction**: Apply Bonferroni correction if reporting individual tier significance to control family-wise error rate (Assumption: Multiplicity).
5.  **Collinearity Handling**: Acknowledge that Threshold and Action Entropy are definitionally related. Report **raw variance** (not residual) and acknowledge the relationship descriptively (Assumption: Collinearity).

### Compute Feasibility & GPU Strategy
- **Strategy**: **CPU-First**.
- **Rationale**: The experiment relies on graph traversal and a lightweight rule-based policy, not deep neural network training.
  -   **Graph Generation**: `networkx` is CPU-efficient.
  -   **Policy Execution**: A rule-based agent or small distilled model (if used) runs entirely on CPU.
  -   **Memory**: Sequential episode processing ensures < 7 GB RAM usage.
  -   **Time**: A sufficient number of simple episodes should complete well within the 6-hour GitHub Actions limit.
- **GPU Escape Hatch**: Not required for this specific study. If a future iteration introduces a large transformer policy, the plan would shift to a scaled-down Kaggle GPU run (8-bit quantization, fewer epochs), but the current spec (FR-007) explicitly mandates CPU-only.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Graph Generation Failure** | Unreachable goals in stochastic tiers. | Implement validation loop: regenerate graph if no path exists. |
| **Compute Timeout** | 33k episodes exceed 6h. | Profile [deferred] episodes first; optimize loop (vectorize where possible); reduce episode count if necessary (noted as power limitation). |
| **Metric Instability** | Variance undefined for deterministic policies. | Default variance to 0.0; flag as "deterministic policy observed." |
| **Overfitting to Synthetic Data** | Results not generalizable. | Clearly frame findings as "associational observations of policy behavior" (Assumption: Inference Framing). |

## Decision Rationale

- **Synthetic vs. Real Data**: Synthetic data was chosen because no open dataset with "hindsight skill injection" labels exists. This ensures ground-truth validity for the "success rate" metric.
- **CPU-Only Execution**: The lightweight nature of the policy and graph simulation makes GPU acceleration unnecessary and potentially counterproductive for cost/complexity.
- **Threshold Sweep Granularity**: 0.1 steps provide sufficient resolution to identify an inflection point without excessive computational cost.
- **Baseline Definition**: The baseline for the cost-benefit ratio is explicitly defined as T=1.0 on the same graph seed to prevent circular dependency (SC-002).
