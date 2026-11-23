# Research: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

## Research Question
Can a deterministic Cellular Automaton (CA) "Eco-Director," parameterized by rule locality, state memory depth, and non-linearity, achieve statistical parity in environmental coherence and diversity compared to a 100M-parameter neural proxy baseline, while meeting a ≥90% latency reduction target on CPU-only hardware, when tested against a Stochastic Physics Sandbox?

## Hypotheses

- **H1 (Coherence Parity)**: The optimal CA configuration will show no statistically significant difference in coherence scores compared to the neural proxy baseline (p > 0.05), after controlling for temporal autocorrelation and noise seed variance via LMM.
- **H2 (Latency Reduction)**: The optimal CA configuration will achieve a latency reduction of ≥90% compared to the neural proxy baseline.
- **H3 (Non-Linearity Driver)**: Non-linearity in the CA update function will be the primary driver of high diversity scores, as detected by Random Forest feature importance.
- **H4 (Memory Depth Effect)**: Memory depth will have a significant interaction effect with neighborhood radius on coherence, identified via LMM interaction terms.

## Dataset Strategy

The study relies on a **Stochastic Physics Sandbox** generator. This sandbox generates environmental state transitions by injecting external, uncontrolled noise (e.g., random force vectors, unpredictable agent collisions) into a grid world. This ensures that "coherence" measures the CA's ability to adapt to external complexity rather than mere rule adherence.

**Data Availability Note**: No external datasets (e.g., LingBot, robotic trajectories) are used. The verified robotic datasets were rejected due to modality mismatch (continuous kinematics vs. discrete grid CA). The synthetic data is generated from first principles of the sandbox to ensure domain validity.

### Generated Data Properties
- **Source**: `src/sim/physics_oracle.py` (Stochastic Physics Sandbox)
- **Type**: Discrete grid-based state transitions with injected stochastic noise.
- **Volume**: [deferred] time-steps per configuration, 5 noise seeds per configuration.
- **Validation**: Sandbox outputs are validated against `contracts/physics_oracle.schema.yaml`.

## Methodology

### Phase 1: Simulation Engine Implementation
1.  **Eco-Director Module**: Implement a modular CA engine (`src/sim/eco_director.py`) that accepts `neighborhood_radius`, `memory_depth`, and `non_linearity` as runtime arguments.
2. **Neural Baseline**: Implement a **100M parameter proxy model** (not a throttled 1.3B model) to ensure CPU feasibility and valid comparison. If this model exceeds the [deferred]-step time limit, the run is flagged as "Time-Bound" and excluded from statistical parity tests.
3.  **Physics Oracle**: Develop a **Stochastic Physics Sandbox** (`src/sim/physics_oracle.py`) that injects random force vectors and collisions. This serves as the ground truth for "coherence" (FR-008), ensuring the metric is not tautological.

### Phase 2: Parameter Sweep & Data Collection
1.  **Grid Definition**: Define a grid for `neighborhood_radius` (e.g., {1, 2}), `memory_depth` (e.g., {2, 3, 4}), and `non_linearity` (e.g., {linear, quadratic, sigmoid}).
2. **Execution**: Run **[deferred] time-steps** for each configuration (fractional factorial design to fit 6h limit). Repeat for **5 distinct noise seeds** per configuration to ensure stochastic variance.
3.  **Metrics**: Record `coherence_score` (deviation from physics oracle), `diversity_score` (event entropy), and `step_latency` at regular intervals.
4.  **Safety**: Enforce a memory ceiling and time limit. Runs exceeding bounds are logged as "Out of Bounds" and excluded from analysis.

### Phase 3: Statistical Analysis
1.  **Autocorrelation Check**: Compute ACF for coherence metrics. **Mandate LMM for all runs** regardless of ACF value to account for inherent temporal autocorrelation in dynamic systems. The ACF value is recorded for diagnostic purposes only and does not determine the model choice.
2.  **Linear Mixed-Effects Model (LMM)**: Fit `coherence ~ neighborhood_radius * memory_depth + (1|noise_seed)` to assess interaction effects (FR-004, US-2). This accounts for stochastic variance introduced by the sandbox. 'time_step' is treated as a fixed effect or omitted in favor of modeling the residual structure, while 'noise_seed' serves as the random effect.
3.  **Partial Correlation Analysis**: Compute partial correlation between coherence and input parameters (controlling for other factors) to ensure correlation < 0.05 (SC-006).
4.  **Random Forest**: Train a Random Forest on CA parameters to predict coherence/diversity. **Training data includes multiple noise seeds** to ensure target variance. Extract feature importance to identify non-linear drivers (FR-009).
5.  **Sensitivity Analysis**: Sweep decision cutoffs for "coherence" (0.01, 0.05, 0.1). Calculate **inconsistency rate** (percentage of runs where classification flips). Output: JSON report with threshold vs. rate mapping (FR-006).
6.  **Semantic Novelty**: Detect "rare events" as entropy spikes (>3 standard deviations from mean transition entropy). Output: Histogram of event entropies and count of rare events per configuration (US-3, SC-003).

### Phase 4: Comparative Synthesis
1.  **Latency Calculation**: Compute latency reduction percentage: `(Neural_Latency - CA_Latency) / Neural_Latency`. Verify if ≥90% (SC-001, FR-005).
2.  **Statistical Parity**: Compare CA vs. Neural coherence/diversity via LMM p-values (SC-002).
3.  **Semantic Novelty**: Compare rare event counts and histograms between CA and Neural logs.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: When sweeping parameters, apply False Discovery Rate (FDR) correction (Benjamini-Hochberg) to LMM p-values to control family-wise error rate.
- **Power Limitation**: The [deferred]-step limit per run is a power constraint. The fractional factorial design ensures sufficient data density for the intended effect sizes within the 6-hour limit.
- **Causal Inference**: As this is a simulation study, causal claims are limited to the relationship between *parameters* and *metrics* within the defined model. The "causal" effect of parameters is identified by the controlled experimental design (randomized parameter assignment).
- **Collinearity**: If `memory_depth` and `non_linearity` are definitionally related, their independent effects will be reported descriptively, and collinearity will be acknowledged.
- **CPU-First**: All methods (CA simulation, LMM, Random Forest) are computationally feasible on a multi-core CPU with sufficient RAM. The 100M proxy model is designed for CPU execution.

## Decision/Rationale

- **Why LMM?**: Time-series data from [deferred] steps exhibits strong temporal autocorrelation. Standard regression assumes independence, which would invalidate p-values. LMM accounts for this via random effects (noise_seed) and handles the non-independence of observations without arbitrary thresholds.
- **Why Random Forest?**: The relationship between CA parameters and emergent complexity is hypothesized to be non-linear. LMM captures linear interactions, but RF captures complex, non-linear feature interactions.
- **Why Stochastic Sandbox?**: To avoid tautological validation, the "coherence" metric must be tested against external, uncontrolled complexity. The sandbox provides this by injecting random noise, ensuring the CA must adapt rather than just follow rules.
- **Why 100M Proxy?**: The 1.3B model is infeasible on CPU within 6 hours. A 100M proxy provides a valid, non-degraded baseline for comparison without risking timeout.
- **Why Multiple Noise Seeds?**: To ensure the target variable (coherence) has stochastic variance, making Random Forest feature importance analysis valid and LMM random effects meaningful.
