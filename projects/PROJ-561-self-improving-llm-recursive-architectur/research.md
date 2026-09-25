# Research Plan: Self-Improving LLM via Recursive Architecture Refinement

## 1. Introduction and Motivation

This project investigates the feasibility of a self-improving Large Language Model (LLM) that recursively refines its own architecture. Unlike standard fine-tuning which adjusts weights, this system prompts the model to propose structural changes (layer additions, head count modifications, activation function swaps), validates these proposals against strict safety and distinctness constraints, trains the new architecture, and evaluates performance against an external oracle.

The core hypothesis is that an LLM, given sufficient context about its own architecture and performance metrics, can identify structural inefficiencies and propose modifications that lead to "lasting improvement" in benchmark performance, even under strict resource constraints (RAM < 7GB, parameter increase limits).

## 2. Methodology and Definitions

### 2.1 Determining Parameter Limits (Methodology)
To ensure the system remains computationally feasible, a maximum parameter increase ratio is enforced. The specific value for `MAX_PARAM_INCREASE_RATIO` is currently **[deferred]**.

**Methodology for Determination:**
The final limit will be determined through an analysis of parameter efficiency curves and memory constraints. Specifically, we will:
1. Measure the baseline memory footprint of the GPT-2 124M model.
2. Simulate architectural expansions (e.g., +1 layer, +1 head) to estimate memory growth.
3. Correlate these growth estimates with the available RAM budget (7GB) and the training batch size requirements.
4. Select a ratio that allows for meaningful structural exploration while guaranteeing the training loop does not exceed the physical memory limit.

### 2.2 External Oracle and Validation Protocol
The evaluation of any proposed modification is governed by an **External Oracle** protocol.

* **Immutable Metric:** The evaluation metric is an external, immutable oracle during each cycle. This ensures that the benchmarks are held-out from the model's proposal generation process, preventing the model from "gaming" the evaluation function it helped define.
* **Fixed-Point Verification:** The system must satisfy a Fixed-Point verification protocol where the improvement is not just a transient gain but a stable state.
* **External Validation Protocol:** Benchmarks (GSM8K, ARC-Challenge, BoolQ) are strictly held out. The model is never trained on the test data, nor is the test data used to generate the proposal. The oracle only receives the trained model weights and returns scalar scores.

### 2.3 Operational Definition of "Lasting Improvement"
"Lasting improvement" is defined as performance persistence across at least **two subsequent training cycles** (Turing Review). A single-epoch gain is insufficient; the new architecture must demonstrate stability and generalization when subjected to further recursive refinement attempts.

### 2.4 Rollback Mechanism
A **Rollback Mechanism** is implemented as a safety constraint. If the performance of a new cycle drops below a defined threshold (e.g., 5% degradation from the baseline), the system MUST automatically revert to the previous stable checkpoint. This prevents the system from descending into a performance cliff during the search for optimal architectures.

### 2.5 Scaling Law Analysis
Based on the West Review, we anticipate a power-law decay of improvement gains (Δperformance vs. iteration count). The system is expected to exhibit diminishing returns as it approaches the local optimum of the current architectural manifold. We define the thermodynamic bounds of recursion as the point where the FLOP cost of a proposed change exceeds the expected performance gain, indicating a plateau.

### 2.6 Computational Irreducibility (Wolfram Review)
Addressing the concerns raised by the Wolfram Review regarding the predictability of complex systems:

**Computational Irreducibility** implies that for this recursive system, no closed-form mathematical prediction of the improvement trajectory exists. One cannot analytically solve for the optimal architecture after $N$ cycles without actually executing the $N$ cycles.

Consequently, the methodology explicitly relies on **empirical mining of the architecture rule space**. We do not assume a smooth, convex optimization landscape. Instead, we treat the search as a stochastic process where the only way to determine the outcome of a specific architectural modification is to execute the training and evaluation loop. The system must navigate this irreducible complexity by:
1. Generating diverse proposals.
2. Testing them empirically.
3. Recording the trajectory to identify emergent patterns in the rule space that analytical methods would miss.

## 3. Distinction: Recursive Improvement vs. Adaptation

Per the Krakauer Review, we distinguish between:
* **Recursive Improvement (Optimization):** The process of minimizing a fixed loss function on a static dataset by refining the model's parameters and structure.
* **Recursive Adaptation (Evolutionary Navigation):** The ability of the system to navigate "blind spots" in a changing environment where the objective function itself might shift or where the system must develop capabilities it did not originally possess.

We define a metric for "stupidity" or error cost in changing environments as the divergence between the model's predicted performance (based on its internal state) and the actual performance measured by the External Oracle. High divergence indicates a lack of adaptation.

## 4. Implementation Plan

The implementation follows a phased approach:
1. **Phase 0:** Research Design & Documentation (Current State).
2. **Phase 1:** Infrastructure Setup (Config, Directories, Logging).
3. **Phase 2:** Foundational Components (Loaders, Validators, Oracle, Statistics).
4. **Phase 3:** Single Refinement Cycle (Proposal -> Validate -> Train -> Eval).
5. **Phase 4:** Multi-Cycle Orchestration (3 Cycles, State Management).
6. **Phase 5:** Trade-off Analysis (FLOPs, RAM, Performance).
7. **Phase 6:** Final Synthesis and Reporting.

## 5. Success Criteria

* **SC-001:** The system successfully generates and validates a modification proposal.
* **SC-002:** The system trains the modified model within the RAM limit (7GB).
* **SC-003:** The system demonstrates "lasting improvement" (persistence across cycles).
* **SC-004:** The cost-effectiveness (performance per FLOP) is tracked and reported.
* **SC-005:** The system handles failures gracefully via the Rollback Mechanism.

## 6. References

* Wolfram, S. (2002). *A New Kind of Science*. Wolfram Media.
* West, G. (2017). *Scale: The Universal Laws of Growth, Innovation, Sustainability, and the Pace of Life in Organisms, Cities, Economies, and Companies*.
* Krakauer, D. et al. (2020). "Intrinsic Motivation and the Evolution of Intelligence."
* Von Neumann, J. (1966). *Theory of Self-Reproducing Automata*.