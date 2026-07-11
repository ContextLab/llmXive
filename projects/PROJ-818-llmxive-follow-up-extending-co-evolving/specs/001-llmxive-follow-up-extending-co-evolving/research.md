# Research: Co-Evolving Policy Distillation

## Research Question

Does co-evolving policy distillation mitigate catastrophic forgetting in discrete, non-differentiable reasoning tasks more effectively than sequential distillation, independent of total data exposure?

## Methodology Overview

The study employs a **controlled experimental design** with three distinct training conditions:
1.  **Sequential**: Agents train on Task A, then Task B.
2.  **Mixed-task**: Agents train on a shuffled mix of Task A and Task B.
3.  **Co-evolving**: Two sub-populations evolve in parallel, exchanging successful rule-sets bidirectionally at every generation.

**Independent Variable**: Training Strategy (Sequential, Mixed, Co-evolving).
**Dependent Variable**: Forgetting Rate (Percentage drop in accuracy from *Initial Baseline* to *Final State*).
**Control Variables**: Total number of rule evaluations (fixed by checksum), random seeds, dataset difficulty, and rule-set complexity.

## Dataset Strategy

Since the study requires specific, controlled logical and navigation tasks with known ground-truth rules, **synthetic data generation** is the primary strategy. No external datasets are used.

| Dataset Component | Source/Generator | Verification Method | Notes |
|-------------------|------------------|---------------------|-------|
| Propositional Logic Proofs | `sympy` (Custom Generator) | `sympy` validation of logical equivalence | Generates proofs with distinct axiom subsets. |
| Grid-World Navigation | `networkx` (Custom Generator) | Graph traversal solvability check | Generates grids with specific "avoid" or "follow" rules. |
| Test Sets | `sympy` / `networkx` (Held-out) | **Identical seeds for Initial and Final tests** | **Critical**: The *exact same* held-out test set is used to measure "Initial" accuracy (post-baseline) and "Final" accuracy (post-experiment) for each agent to ensure the drop metric reflects true forgetting, not distribution shift. |

**Note on External Datasets**: No external datasets (e.g., from HuggingFace or UCI) are used. The research question relies on the ability to *control* the rule sets and difficulty, which is only possible via synthetic generation.

## Experimental Design & Statistical Rigor

### Baseline Consistency (Pre-training Phase)
To ensure a valid comparison of "forgetting" across all conditions, **all agents** (Sequential, Mixed, Co-evolving) undergo a distinct **Pre-training Baseline Phase**:
1.  **Training**: All agents train exclusively on **Task A** until a convergence plateau is reached or a fixed generation count is met.
2.  **Measurement**: Immediately after this phase, the **Initial Accuracy** on Task A is measured on the **held-out test set**.
3.  **Transition**: This state serves as the "Initial" anchor point ($T_0$) for the forgetting calculation for *all* conditions.
    *   *Sequential*: Continues training on Task A (optional maintenance), then switches to Task B.
    *   *Mixed/Co-evolving*: Immediately begins the mixed/co-evolving training protocol on Task A+B.
    *   *Note*: For Mixed/Co-evolving, this ensures the "Initial" state is not "zero knowledge" but a consistent baseline of Task A competence, allowing the "drop" metric to be comparable to the Sequential condition.

### Experimental Conditions
1.  **Sequential**: Train Task A (Baseline) -> Measure Initial -> Train Task B -> Measure Final.
2.  **Mixed**: Train Task A (Baseline) -> Measure Initial -> Train Mixed (A+B) -> Measure Final.
3.  **Co-evolving**: Train Task A (Baseline) -> Measure Initial -> Train Co-evolving (A+B exchange) -> Measure Final.

### Sample Size & Power
To satisfy **SC-004**, the study requires a minimum of **N ≥ 30 runs per condition** (Total N ≥ 90). This is based on a power analysis for a Mixed-Design ANOVA detecting a medium effect size (Cohen's f = 0.25) with α = 0.05 and power ≥ 0.8.
*   **Feasibility**: Given the lightweight nature of the symbolic simulation (no GPU, no deep learning), A sufficient number of runs should complete within the 6-hour CI limit, provided the generation and evaluation loops are optimized.

### Statistical Tests
1.  **Primary Test**: **Mixed-Design ANOVA (Split-Plot)**.
    *   **Within-Subjects Factor**: Time (Initial Baseline vs. Final State).
    *   **Between-Subjects Factor**: Condition (Sequential, Mixed, Co-evolving).
    *   **Interaction Effect**: The critical test is the *Time × Condition* interaction, which isolates whether the change in accuracy (forgetting) differs significantly between conditions.
2.  **Post-hoc**: Tukey's HSD (Honestly Significant Difference) test on the interaction or simple main effects to identify specific pairwise differences (e.g., Co-evolving vs. Sequential).
3.  **Alternative Model**: If assumptions (normality, sphericity) are violated, a **Linear Mixed Model (LMM)** will be used:
    *   **Fixed Effects**: Condition, Time, Condition × Time.
    *   **Random Effects**: `Agent_ID` (to account for the nested structure of repeated measures within agents).
4.  **Assumption Checks**: Normality (Shapiro-Wilk), Sphericity (Mauchly's test), Homogeneity of Variance (Levene's test).

### Convergence Control
To address the confound of differential learning speeds (convergence time/plateau):
*   **Metric**: "Generations to Plateau" and "Final Fitness Ceiling" will be recorded for each agent.
*   **Control**: These metrics will be included as **covariates** in the statistical model (ANCOVA or LMM) to isolate the "exchange" effect from the "convergence rate" effect. If Co-evolving agents reach a higher fitness faster, the model will adjust for this to ensure the "forgetting" metric is not a proxy for "learning efficiency".

### Causal Inference & Limitations
*   **Observational Nature**: While the training conditions are controlled, the "evolutionary" process introduces stochasticity. The study frames findings as **associational evidence** of the co-evolution mechanism's efficacy, acknowledging that "co-evolution" is a complex emergent property rather than a simple linear causal factor.
*   **Collinearity**: The "total data exposure" is strictly controlled (integer parity) to prevent it from being a confounding variable.
*   **Measurement Validity**: `sympy` and `networkx` are standard, validated libraries for symbolic logic and graph theory. The validity of the "proofs" and "paths" is guaranteed by the libraries' internal consistency checks.

## Compute Feasibility Analysis

The implementation is constrained to a GitHub Actions free-tier runner with limited CPU resources, 7GB RAM, and no GPU.
*   **No GPU/CUDA**: The plan explicitly avoids any deep learning libraries (PyTorch/TensorFlow) or GPU-specific operations.
*   **CPU-Tractability**: The core operations are symbolic logic evaluation (`sympy`) and graph traversal (`networkx`), which are computationally lightweight and scale linearly with dataset size.
*   **Memory**: Data is generated on-the-fly and discarded after evaluation. No large model weights are stored. The memory footprint will be dominated by the Python interpreter and the current generation's rule-sets, remaining well within the system's memory constraints.
*   **Runtime**: 90 runs of a synthetic simulation (likely < 5 minutes per run) fits comfortably within the 6-hour limit.

## Edge Case Handling

1.  **Invalid Generation**: If `sympy` fails to generate a valid proof due to parameterization contradictions, the system retries up to 3 times. If still failing, the instance is logged as a warning and skipped to ensure the run continues (reproducibility of the *process*, not necessarily the exact same random noise).
2.  **Population Collapse**: If the co-evolving exchange results in a degraded rule-set for both sub-populations, a selection pressure mechanism (keeping a top-performing subset of the population) ensures the population does not collapse to zero fitness.
3.  **Floating-Point Drift**: The "equal data exposure" constraint is enforced via **integer counters** (total rule evaluations), not floating-point approximations. A post-run checksum verifies exact parity.
