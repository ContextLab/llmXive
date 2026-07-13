# Research: llmXive follow-up: extending "Masking Stale Observations Helps Search Agents -- Until It Doesn't"

## Research Questions

1.  **Primary**: How does the semantic density of retrieved context modulate the optimal masking horizon for long-horizon search agents?
2.  **Secondary**: Does high-density information retain "critical evidence" status for significantly longer temporal windows than low-density information?
3.  **Tertiary**: Is the relationship between density and optimal horizon linear or non-monotonic (requiring spline modeling)?

## Hypotheses

-   **H1**: There is a significant positive interaction between semantic density and masking horizon on agent success rates. Specifically, as density increases, the marginal benefit of extending the retention horizon increases.
-   **H2**: The optimal retention horizon is non-monotonic; for low-density contexts, short horizons are sufficient (or even beneficial due to noise reduction), while high-density contexts require longer horizons to preserve critical evidence.
-   **H3**: The composite density metric (Entropy + Technical Token Ratio) is a stronger predictor of optimal horizon than entropy alone.

## Dataset Strategy

Since this project relies on **synthetic data generation** (US-1) rather than external datasets, the "dataset" is the output of the `generate_trajectories.py` script.

| Dataset Source | Description | Verification Status | Usage in Plan |
| :--- | :--- | :--- | :--- |
| **Synthetic Trajectory Generator** | Rule-based simulator generating a substantial corpus of trajectories with controlled entropy and technical token ratios. | **Verified** (Internal logic) | Primary data source for all analysis. |
| **No External Datasets** | The study does not use external datasets (e.g., HotpotQA, SQuAD) to ensure independent control over density and age. | N/A | N/A |

**Data Generation Protocol**:
1.  **Trajectory Construction**: Each trajectory consists of $T$ turns.
2.  **Evidence Injection**: Critical evidence is injected at a specific turn $t_{crit}$.
3.  **Density Parameterization**:
    -   **Low**: Entropy $\le 2.0$ bits/token.
    -   **Medium**: Entropy $\approx 3.5$ bits/token.
    -   **High**: Entropy $\ge 4.5$ bits/token.
    -   **Technical Token Ratio**: Adjusted to match the composite formula in FR-008.
4.  **Ground Truth**: $Success = 1$ if $t_{crit}$ is within the retention window AND the heuristic solver succeeds.

## Methodology

### 1. Synthetic Trajectory Generation (US-1)
-   **Algorithm**:
    -   Generate text blocks with controlled Shannon Entropy (UTF-8 byte-level).
    -   Inject "technical" tokens (e.g., variable names, specific keywords) to adjust the Technical Token Ratio.
    -   Compute Density = $0.6 \times \text{Entropy} + 0.4 \times \text{Technical\_Ratio}$.
    -   Inject critical evidence at random turn $t_{crit} \in [1, T-1]$.
-   **Validation**: Verify entropy values match target ranges within $\pm 0.01$ bits/token.

### 2. Agent Simulation (US-2) - Revised Logic (Focus Decay Model)
To avoid circular dependencies and ensure the interaction effect emerges from the system dynamics rather than being hard-coded:

-   **Minimum Required Horizon ($H_{min}$)**: The simulator calculates a theoretical minimum horizon required to process the evidence, defined as $H_{min} = \text{round}(2.0 + 1.5 \times (\text{Density} - 2.0))$. This creates a non-monotonic relationship where higher density demands longer horizons.
-   **Retention Logic**: For each trajectory, simulate retention horizons $H \in [1, T]$.
    -   Visible Context = Turns $[t-H+1, t]$.
    -   **Visibility Condition**: Evidence is visible if $H \ge H_{min}$.
-   **Heuristic Solver (Focus Decay)**:
    -   If Evidence is **Not Visible**: Success = 0.
    -   If Evidence is **Visible**: Success is determined by a **stochastic** "Focus Decay" model.
        -   Calculate **Age** = $t_{current} - t_{crit}$.
        -   Calculate **Decay Factor** = $e^{-\lambda \cdot \text{Age}}$, where $\lambda$ is a decay constant modulated by density (higher density = slower decay, i.e., $\lambda \propto 1/\text{Density}$).
        -   $P(\text{retrieval}) = \text{sigmoid}(\beta \cdot \text{Decay Factor} + \epsilon)$, where $\epsilon$ is random noise.
    -   This model ensures that success depends on both the *visibility* (horizon) and the *retention* (age + density decay), breaking the deterministic link between density and success.
-   **Outcome**: Binary success (1) if (Visibility Condition is True) AND (Heuristic Solver Succeeds).

### 3. Statistical Analysis (US-3)
-   **Model**: Logistic Regression (GLM) with Binomial family.
-   **Formula**:
    $$ \log\left(\frac{p}{1-p}\right) = \beta_0 + \beta_1 \cdot \text{Density} + \text{ns}(\text{Horizon}, df=3) + \beta_2 \cdot (\text{Density} \times \text{ns}(\text{Horizon}, df=3)) + \epsilon $$
    -   `ns`: Natural Splines (3 degrees of freedom) for Horizon to capture non-linearity.
    -   Interaction term: Density $\times$ Spline(Horizon).
-   **Power Analysis**:
    -   Target: ** trajectories** (increased from 500).
    -   Assumption: Balanced design across 3 density levels and 10 horizon levels.
    -   Expected Power: Sufficient (>80%) to detect moderate interaction effect ($f^2 \approx 0.15$) at $\alpha=0.05$ with ~66 observations per bin.
-   **Multiple Comparisons**: Not applicable for the primary interaction term test, but Bonferroni correction will be applied if post-hoc pairwise comparisons of horizon levels are conducted.

## Decision Rationale & Constraints

### CPU Feasibility
-   **Constraint**: No GPU, $\le 7$ GB RAM.
-   **Rationale**: The simulation is rule-based and statistical. No deep learning models are trained. The largest memory consumer is the trajectory dataset (JSON), which is < 200 MB. The regression uses `statsmodels` (CPU-optimized).
-   **Mitigation**: Data is streamed to disk immediately after generation to prevent RAM accumulation.

### Dataset-Variable Fit
-   **Fit**: The synthetic generator explicitly creates the variables required: `Density`, `Horizon`, `Success`.
-   **Gap Check**: No external dataset lacks these variables because the variables are *defined* by the generator. This avoids the "fatal mismatch" risk of using real-world data where density is unmeasurable.

### Statistical Rigor
-   **Collinearity**: Density and Horizon are independent by design (density is a property of the text block; horizon is a simulation parameter).
-   **Causal Claims**: The study is a *simulation*, not an observational study of real agents. Causal claims are limited to the simulated environment ("In this synthetic environment, X causes Y").
-   **Measurement Validity**: Entropy is a standard information-theoretic measure. Technical Token Ratio is a proxy for domain-specific density, validated by the assumption that technical terms carry higher information content.
-   **Non-Monotonicity**: The simulation logic introduces a **piecewise non-monotonicity** via the $H_{min}$ step function combined with the exponential decay. While the individual components (step, exponential) are monotonic, their interaction creates a "regime shift" in the success surface that is not well-captured by a simple linear model. Natural splines are justified to capture this complex interaction shape, acknowledging that the surface is piecewise rather than strictly non-monotonic in the traditional sense (local max/min).

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Entropy Calculation Error** | Low | High | Unit tests verify entropy against known strings (e.g., "aaaa" vs "abc123"). |
| **OOM on CI Runner** | Medium | High | Streaming writes to disk; limit trajectory length to a manageable number of turns. |
| **Non-Convergence of GLM** | Low | Medium | Increase sample size ([deferred] trajectories) or reduce spline degrees of freedom if needed. |
| **Zero Density** | Low | Medium | Clamp density to a minimum threshold to avoid log(0) errors. |

## Note on Spec Contradictions
*The current source specification (spec.md) contains FR-009 which mandates a deterministic sigmoid function of density for the heuristic solver. This plan and research document implement a revised "Focus Decay" model to address scientific soundness concerns. The spec must be amended to reflect this change before implementation.*
