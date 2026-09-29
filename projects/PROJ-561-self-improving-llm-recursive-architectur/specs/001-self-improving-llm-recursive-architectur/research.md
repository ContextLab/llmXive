# Research Report: Self-Improving LLM Recursive Architecture

## 1. Introduction
This document outlines the methodology, constraints, and theoretical framework for the recursive self-improvement of Large Language Models (LLMs). The core objective is to establish a system capable of proposing, validating, and integrating architectural modifications that yield lasting performance improvements while adhering to strict safety and resource constraints.

## 2. Methodology for Parameter Limit Determination

### 2.1 The Deferred Parameter Limit Strategy
To ensure the system operates within feasible computational bounds while maximizing potential gains, the maximum allowable parameter increase ratio (`MAX_PARAM_INCREASE_RATIO`) is determined through a rigorous research-driven methodology rather than a static heuristic.

**Methodology Description:**
The limit will be determined by analyzing parameter efficiency curves derived from empirical training runs on the target hardware. Specifically, the system will:
1. Measure the marginal return on investment (ROI) for parameter increases across a range of scaling factors.
2. Correlate these gains against the memory footprint and FLOP costs calculated during the proposal phase.
3. Identify the "knee" of the efficiency curve where additional parameters yield diminishing returns relative to the resource cost.
4. Apply a safety buffer based on the observed variance in RAM usage during peak training epochs.

**Current Status:**
The concrete value for `MAX_PARAM_INCREASE_RATIO` is **[deferred]** pending the completion of the initial scaling analysis (T008a). The configuration defaults to a conservative estimate, but the operational limit must be overridden by the result of the research described above before the recursive loop is enabled for large-scale iterations.

## 3. External Oracle Protocol (FR-021)

### 3.1 Definition
The evaluation of any proposed architectural modification is governed by an **External Oracle**. This protocol ensures that the benchmarking process remains immutable and independent of the model's proposal generation process.

### 3.2 Operational Rules
- **Immutability:** The benchmark datasets (GSM8K, ARC-Challenge, BoolQ) and their specific test splits are treated as immutable constants. They are never modified, augmented, or included in the training data for the cycle in which they are used for evaluation.
- **Separation:** The logic that generates the modification proposal (the "Generative Oracle") is strictly separated from the logic that evaluates the performance (the "External Oracle"). The Generative Oracle has no access to the evaluation metrics during the proposal phase.
- **Held-Out Data:** All evaluation data is held-out from the training process. The model proposes changes based on its internal state and training loss, but the final validation of "improvement" relies exclusively on the External Oracle's assessment of the held-out benchmarks.

## 4. External Validation Protocol

### 4.1 Protocol Specification
To ensure the integrity of the recursive loop, the **External Validation Protocol** mandates that:
1. Benchmarks are selected from a fixed, pre-defined set that is disjoint from the training corpus.
2. The evaluation metric calculation is deterministic and reproducible.
3. The validation process is executed in an isolated environment to prevent contamination of the test data by the model's training process.
4. Any proposal that fails to demonstrate a statistically significant improvement over the baseline (as determined by the External Oracle) is rejected, regardless of the internal loss reduction observed during training.

## 5. Definition of "Lasting Improvement"

### 5.1 Operational Definition
A modification is considered to yield **lasting improvement** only if the performance gain persists across at least two subsequent training cycles (Turing Review).

### 5.2 Criteria
- **Cycle N:** A proposal is accepted if it shows improvement over the baseline.
- **Cycle N+1:** The model, now incorporating the modification, must be subjected to a new proposal cycle. If the modification degrades or fails to maintain its advantage in the presence of further optimization, it is deemed transient.
- **Cycle N+2:** The improvement must be stable and reproducible. Only after passing the N+1 and N+2 checks is the improvement classified as "lasting."
- **Distinction:** This definition distinguishes between single-epoch gains (which may be overfitting or noise) and genuine architectural advancements that survive the stress of recursive optimization.

## 6. Rollback Mechanism

### 6.1 Specification
The system must implement a robust **Rollback Mechanism** to prevent catastrophic degradation.

### 6.2 Trigger Conditions
- If the performance on the External Oracle benchmarks drops below a predefined threshold (e.g., 5% degradation from the previous stable checkpoint).
- If the system detects an infinite loop of failed proposals.
- If resource constraints (RAM/FLOPs) are violated in a manner that cannot be resolved by the current optimization strategy.

### 6.3 Action
Upon triggering, the system MUST revert to the previous stable checkpoint (the last known good state) and log the failure event. The failed proposal is recorded in the history to inform future generations, but the active model is restored to its pre-failure state.

## 7. Scaling Law Analysis (West Review)

### 7.1 Expected Trajectory
Per the insights from Geoffrey West, we anticipate a power-law decay in the magnitude of improvement gains as the number of iterations increases. The relationship between performance gain (Δperformance) and iteration count (n) is expected to follow:
Δperformance ∝ n^(-α)

### 7.2 Thermodynamic Bounds
The recursion is bounded by thermodynamic constraints: the energy required to compute the next improvement must be less than the value of the improvement itself. The system will track the "cost of recursion" to ensure it remains within feasible bounds.

## 8. Computational Irreducibility (Wolfram Review)

### 8.1 No Closed-Form Prediction
Consistent with the principle of Computational Irreducibility, it is explicitly stated that no closed-form prediction of improvement trajectories exists. The behavior of the recursive system cannot be shortcut; it must be empirically mined.

### 8.2 Methodology
The system relies on **empirical mining of the architecture rule space**. We cannot predict the outcome of a modification without actually running the training cycle and evaluating it. The "search" for improvement is a computational process that must be executed step-by-step.

## 9. Recursive Improvement vs. Recursive Adaptation (Krakauer Review)

### 9.1 Distinction
- **Recursive Improvement:** The optimization of a fixed objective function (e.g., minimizing loss on a static benchmark). This is a gradient-based search for a local optimum.
- **Recursive Adaptation:** The evolutionary navigation of blind spots in changing environments. This involves modifying the objective function or the search strategy itself to survive in a dynamic context.

### 9.2 Metric for "Stupidity"
To quantify the cost of error in changing environments, we define a metric for "stupidity" (S):
S = (Cost of Correction) / (Rate of Environmental Change)
A system with high S is unable to adapt quickly enough to changes, leading to a high cost of correction. The system aims to minimize S by balancing the speed of adaptation with the stability of the learned representations.

## 10. Conclusion
This research document establishes the foundational protocols for the self-improving LLM project. By deferring the parameter limit to a data-driven methodology, enforcing an immutable External Oracle, and distinguishing between transient and lasting improvements, the system is designed to explore the boundaries of recursive self-modification safely and effectively.