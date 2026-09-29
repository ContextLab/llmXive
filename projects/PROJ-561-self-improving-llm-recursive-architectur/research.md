# Research Plan: Self-Improving LLM via Recursive Architecture Refinement

## 1. Executive Summary
This project investigates the feasibility of a recursive self-improving Large Language Model (LLM) system. The core hypothesis is that an LLM, given access to its own architecture definition and weights, can propose structural modifications, validate them against held-out benchmarks, and iteratively refine its own architecture to achieve lasting performance gains without external human intervention.

## 2. Methodology for Parameter Limits
To determine the maximum allowable parameter increase per cycle, we define a methodology based on parameter efficiency curves and hardware memory constraints.

The specific limit for `MAX_PARAM_INCREASE_RATIO` is currently **[deferred]** pending the outcome of the initial scaling law analysis (T099) and the empirical measurement of memory overhead during the first three training cycles. The methodology involves:
1. Measuring the FLOPs-to-accuracy ratio for the baseline model.
2. Simulating parameter growth to estimate RAM consumption against the 7GB limit (SC-005).
3. Selecting a ratio that maximizes potential gain while strictly adhering to the safety constraint.

Until this analysis is complete, the default configuration (config.py) assumes a conservative ratio of 0.30, but the research definition remains open for adjustment based on the methodology described above.

## 3. External Oracle Protocol (FR-021)
To prevent the model from optimizing for its own proposal generation process (a form of reward hacking or self-reinforcement), this system enforces a strict **External Oracle** protocol.

- **Immutable Evaluation**: During each refinement cycle, the evaluation metric is provided by an external, immutable oracle. The model does not have access to the benchmark data or the evaluation logic during the proposal generation phase.
- **Held-Out Benchmarks**: The datasets used for validation (GSM8K, ARC-Challenge, BoolQ) are strictly held-out from the training data and the proposal generation context.
- **Verification**: The oracle validates the modified model's performance against these static benchmarks. A proposal is only accepted if it demonstrates a statistically significant improvement over the baseline according to this external metric.

This separation ensures that the "improvement" is real and not an artifact of the model manipulating its own evaluation criteria.

## 4. External Validation Protocol
Complementing the External Oracle, the **External Validation Protocol** ensures that benchmarks remain immutable throughout the recursion.

- The benchmark datasets are loaded once at the start of the pipeline and checksummed to ensure integrity.
- The model is never exposed to the raw benchmark samples during the `generate_proposal` step.
- The validation function is a pure function that takes the model weights and returns a scalar score, preventing the model from "seeing" the validation logic.

## 5. Definition of Lasting Improvement
A single-cycle gain is insufficient to claim recursive self-improvement due to the volatility of stochastic optimization. We define **lasting improvement** as follows:

A performance gain is considered "lasting" only if it persists across at least two subsequent training cycles (Turing Review). If a modification yields a gain in Cycle N but the performance drops in Cycle N+1 or N+2, the improvement is classified as transient noise, and the modification is rejected or rolled back.

## 6. Rollback Mechanism
To ensure system stability, a **Rollback Mechanism** is implemented:
- If the performance of a new cycle drops below a defined threshold (e.g., 5% degradation from the baseline or the previous stable checkpoint), the system MUST automatically revert to the previous stable checkpoint.
- The rollback event is logged, and the failed proposal is added to the "distinctness history" to prevent re-occurrence.

## 7. Scaling Law Analysis (West Review)
We expect the improvement gains (Δperformance) to follow a power-law decay relative to the iteration count, consistent with scaling laws observed in deep learning.
- **Hypothesis**: $Gain(n) \approx A \cdot n^{-\alpha} + C$
- We will empirically fit this curve to the trajectory data to determine the thermodynamic bounds of recursion and predict the point of diminishing returns.

## 8. Computational Irreducibility (Wolfram Review)
Acknowledging the principle of **Computational Irreducibility**, we explicitly state that no closed-form prediction of improvement trajectories exists.
- The system cannot mathematically predict the outcome of an architecture modification before running the training cycle.
- The methodology relies entirely on the empirical mining of the architecture rule space through iterative experimentation.
- The "rules" of the system (the architecture) are simple, but the emergent behavior (performance trajectory) is complex and irreducible.

## 9. Recursive Improvement vs. Recursive Adaptation (Krakauer Review)
We distinguish between two modes of operation:
- **Recursive Improvement**: Optimization of a fixed objective function (e.g., minimizing loss on a static benchmark).
- **Recursive Adaptation**: Evolutionary navigation of changing environments or blind spots.

To measure the system's ability to adapt, we define a metric for **"stupidity"** (error cost) in changing environments. If the environment shifts (e.g., a new benchmark is introduced), the "stupidity" metric quantifies the cost of the system's failure to adapt its architecture to the new constraints.

## 10. Success Criteria
- **SC-001**: The system successfully completes at least one full refinement cycle.
- **SC-003**: Trajectory persistence is demonstrated (lasting improvement).
- **SC-004**: Cost-effectiveness is maintained (performance gain > resource cost).
- **SC-005**: Feasibility is confirmed (peak RAM < 7GB).

## 11. References
- West, G. (2021). *Scaling: Why Animal Size is So Important*.
- Wolfram, S. (2002). *A New Kind of Science*.
- Krakauer, D. (2021). *Evolutionary Dynamics and Learning*.
- Von Neumann, J. (1966). *Theory of Self-Reproducing Automata*.