# Research Design: Self-Improving LLM via Recursive Architecture Refinement

This document defines the research methodology, operational constraints, and philosophical foundations for the automated recursive self-improvement pipeline. It serves as the immutable reference for all subsequent implementation tasks (T001–T131).

## Methodology for Parameter Limit

The system operates under a strict constraint on architectural growth to prevent runaway resource consumption and ensure the "self-improvement" is genuine efficiency or capability gain rather than brute-force scaling.

**Determination Strategy:**
The maximum allowable parameter increase per cycle is determined by a configurable ratio (`MAX_PARAM_INCREASE_RATIO`).
1. **Initial State:** The baseline model (GPT-2 124M) defines the initial parameter count $P_0$.
2. **Constraint:** For any cycle $N$, the new parameter count $P_N$ must satisfy:
 $P_N \le P_{N-1} \times (1 + R_{max})$
 Where $R_{max}$ is the configured limit.
3. **Current Value:** The specific numerical value for $R_{max}$ is marked as **[DEFERRED]** pending the completion of the "Minimality Search" analysis in the trajectory data.
 * *Note:* Until the empirical analysis of the first three cycles is complete, the system will default to a provisional limit of 0.30 (30%), but this value is subject to revision based on the "Capacity Normalization" results (Task T131).
4. **Hard Stop:** If a proposed modification exceeds this limit, the `External Oracle` (see below) must reject it immediately, regardless of predicted performance gain.

## External Oracle Protocol

To address the "Source of Authority" and "Fixed-Point" concerns raised by John Von Neumann and Alan Turing, the system utilizes an immutable evaluation protocol that the model cannot modify.

**Definition:**
The External Oracle is a read-only, deterministic function $O(M)$ that maps a model state $M$ to a vector of benchmark scores $S = \{s_{gsm8k}, s_{arc}, s_{boolq}\}$.

**Properties:**
1. **Immutability:** The benchmark datasets (GSM8K, ARC-Challenge, BoolQ) and the evaluation logic are loaded from a locked source. The model's `ModificationProposal` logic has zero access to the benchmark definitions or the scoring function.
2. **Invariance:** The Oracle does not adapt its criteria. A score of 50% on GSM8K is always 50%, regardless of how many cycles have passed.
3. **Verification:** Before any model replacement occurs, the new model $M_{new}$ must satisfy:
 $O(M_{new}) > O(M_{old}) + \delta$
 Where $\delta$ is a statistically significant threshold determined by the paired bootstrap test (Task T007).
4. **Fail-Safe:** If the Oracle cannot be contacted or the benchmark data is corrupted, the cycle aborts immediately. No "best guess" or synthetic fallback is permitted.

## Philosophical & Operational Definitions

This section clarifies the conceptual framework guiding the system's behavior, addressing specific concerns regarding computational irreducibility and thermodynamic bounds.

### Source of Authority
The authority for any architectural change resides exclusively in the **External Oracle** and the **Statistical Significance Test**. The LLM generating the proposal is a "hypothesis generator" with no intrinsic authority to validate its own output. The "truth" of an improvement is defined solely by the immutable benchmark scores, not by the model's internal confidence or reasoning.

### Fixed-Point
A **Fixed-Point** is reached when the system enters a state where no modification proposal yields a statistically significant improvement ($p < 0.05$) over the current state, despite exhaustive search of the allowed modification space.
* **Detection:** If three consecutive cycles fail to produce a statistically significant gain while parameter counts increase, the system terminates with a "Fixed-Point Reached" status.
* **Implication:** This indicates the current architecture has hit a local optimum for the given data and benchmark constraints, preventing infinite regress.

### Scaling Laws
We assume that performance $P$ scales with parameter count $N$ and compute $C$ according to established power laws ($P \propto N^\alpha C^\beta$). However, this project seeks to violate the standard scaling assumption by finding **architectural efficiencies** where $P$ increases while $N$ and $C$ remain constant or decrease. The "Capacity Normalization" analysis (T131) will explicitly test whether observed gains are due to scaling or structural optimization.

### Computational Irreducibility
As posited by Stephen Wolfram, the trajectory of this system's improvement cannot be predicted by a closed-form equation. The result of a modification is computationally irreducible; it must be simulated (trained and evaluated) to be known. The system acknowledges that no "shortcut" exists to predict the outcome of a structural change without empirical execution. The "Rule Space Exploration" metric will track the number of distinct modifications attempted to quantify this exploration.

### Recursive Adaptation
Distinct from "Recursive Improvement" (which implies a monotonic ascent to a global optimum), **Recursive Adaptation** acknowledges that the system may oscillate or plateau. The system is designed to adapt its architecture to the specific "fitness landscape" defined by the training data and benchmarks, potentially accepting temporary regressions if they lead to a broader basin of attraction (though the strict Oracle protocol currently forbids accepting a lower score).

### Overfitting
Overfitting is defined as a divergence between training loss and benchmark performance. The system monitors the **Generalization Gap**. If training loss decreases but benchmark scores stagnate or drop, the modification is flagged as overfitting. The "Distinctness Validator" (T020) helps mitigate this by preventing the model from making trivial changes that merely memorize the training set without altering general capability.

### Minimality Search
Before proposing a complex structural change (e.g., adding a layer), the system must first attempt the **simplest valid modification** (e.g., adjusting learning rate, batch size, or a single neuron count). This heuristic, inspired by Occam's Razor and Wolfram's "simplest rules" principle, ensures that complexity is only added when strictly necessary for performance gains.

### Thermodynamic Bounds
The efficiency of the system is bounded by the energy cost of computation. We define **Energy per Accuracy Unit** as the total FLOPs consumed divided by the accuracy gain. The system aims to minimize this ratio. If a modification yields a gain but increases the energy cost per unit of accuracy by more than a threshold, it may be rejected as thermodynamically inefficient, even if statistically significant.

### Bird vs. Frog
* **Bird View:** The high-level orchestration (the "Bird") observes the global trajectory, resource constraints, and convergence status. It decides when to stop or reset.
* **Frog View:** The local modification generation (the "Frog") focuses on the immediate, granular details of the architecture (e.g., "increase hidden size by 8").
* **Separation:** The "Bird" logic (Oracle, constraints, termination) is strictly separated from the "Frog" logic (proposal generation). The Frog cannot see the global state; it only receives the current benchmark score and the allowed modification space. This separation prevents the model from "cheating" by optimizing for the wrong metric.