# Symbolic vs. Neural Boundaries in Neuro-Symbolic Learning Networks

## Overview

This document defines the architectural and operational boundaries between the symbolic and neural components of the neuro-symbolic learning system implemented in PROJ-559. These boundaries are critical for maintaining the integrity of the "bridging" concept: the system must not collapse into either pure neural approximation or pure symbolic rigidity.

## 1. Distinct Roles and Responsibilities

### 1.1 The Symbolic Layer (System 2)
**Role:** The symbolic engine acts as the rigorous, rule-based verifier and structural governor. It is responsible for:
- **Logical Trace Generation:** Producing an explicit, step-by-step derivation of the solution using defined algebraic rules (Commutativity, Associativity, Distributive Property, Identity).
- **Constraint Enforcement:** Ensuring that the final answer and the logical path adhere strictly to mathematical laws.
- **Error Detection:** Identifying contradictions or invalid operations that the neural layer might hallucinate.

**Implementation:** Located in `code/generate/symbolic_explanation.py`. It uses a deterministic rule engine (`SymbolicSolver`) that outputs a JSON trace of rule applications. This layer is **not** a neural approximation; it is a discrete, algorithmic process.

### 1.2 The Neural Layer (System 1)
**Role:** The neural engine acts as the intuitive, pattern-matching narrator. It is responsible for:
- **Natural Language Generation:** Translating the problem context and the symbolic solution into fluent, pedagogical text.
- **Contextual Bridging:** Providing the "story" that connects the student's current understanding to the solution.
- **Heuristic Guessing:** In the absence of a symbolic trace, it attempts to solve based on pattern recognition (though the final output is governed by the symbolic layer).

**Implementation:** Located in `code/generate/neural_explanation.py`. It utilizes a distilled LLM (e.g., TinyLlama) running on CPU. This layer is probabilistic and continuous.

## 2. The Boundary Interface

The "boundary" is the point where the discrete, logical output of the symbolic layer constrains the continuous, probabilistic output of the neural layer.

### 2.1 Governance Mechanism
As per the requirement to address Turing's concern regarding "post-hoc rationalization," the neural narrative **cannot** override the symbolic logic.
- **Input to Neural:** The neural generator receives the *symbolic trace* as a mandatory context.
- **Constraint:** The neural model is instructed to explain the *steps provided in the trace*, not to invent new steps or alter the logical conclusion.
- **Output Structure:** The final `explanation_neuro_symbolic.txt` is a composite where the neural text is structurally anchored by the symbolic JSON trace.

### 2.2 Distinctness Validation
To ensure the symbolic layer remains a "concrete mathematical object" (per Rockmore) and not merely a stylistic variation of the neural output, we enforce a distinctness metric:
- **Jaccard Similarity Check:** The text of the symbolic trace (serialized) and the neural narrative must have a low Jaccard similarity index.
- **Structural Divergence:** The symbolic trace must contain explicit rule identifiers (e.g., `Rule: DistributiveProperty`) that are absent from the natural language neural output.
- **Validation Script:** `code/generate/validate_distinctness.py` computes these metrics. If the similarity exceeds a threshold, the generation is flagged as a failure (indicating the symbolic layer has been "neuralized").

## 3. Operational Stability (Von Neumann's Concern)

The transition from the continuous neural weights to the discrete symbolic operators requires a robust thresholding function.
- **Thresholding:** The symbolic solver does not accept "probabilistic" rules. If the neural layer suggests a step that does not match a known rule with 100% certainty, the symbolic layer rejects it.
- **Stability:** The system is designed such that small perturbations in the neural input (e.g., slight variations in phrasing) do not alter the symbolic trace. The trace is determined solely by the mathematical structure of the problem.

## 4. Addressing Kahneman's "WYSIATI" (What You See Is All There Is)

A purely neural explanation risks satisfying the student's System 1 (intuition) while failing to engage System 2 (critical reasoning).
- **Neural Risk:** The LLM may generate a coherent-sounding but logically flawed explanation.
- **Neuro-Symbolic Mitigation:** By forcing the neural explanation to explicitly reference the symbolic trace, we force the "System 2" logic into the "System 1" narrative. The student is not just told *what* the answer is, but is shown the *rigorous steps* that justify it.
- **Metric:** The "depth of reasoning" is measured by the length and complexity of the symbolic trace included in the final explanation.

## 5. Implementation Artifacts

The following artifacts in the codebase enforce these boundaries:

| Artifact | Path | Function |
|:--- |:--- |:--- |
| Symbolic Solver | `code/generate/symbolic_explanation.py` | Generates the rule-based trace. |
| Neural Generator | `code/generate/neural_explanation.py` | Generates the narrative. |
| Neuro-Symbolic Orchestrator | `code/generate/neuro_symbolic_explanation.py` | Merges trace and narrative, enforcing constraints. |
| Distinctness Validator | `code/generate/validate_distinctness.py` | Ensures the two layers are mathematically distinct. |
| Distinctness Runner | `code/generate/run_distinctness_validation.py` | Executes batch validation on generated pairs. |

## 6. Conclusion

The boundary between the neural and symbolic layers is not a seamless fusion but a controlled interface. The symbolic layer provides the **truth** (the logical ground), while the neural layer provides the **accessibility** (the pedagogical interface). The integrity of the system depends on the symbolic layer remaining strictly discrete and rule-based, preventing the neural layer from "hallucinating" its way to a solution.

This architecture ensures that the system satisfies the requirement for a "neuro-symbolic" approach rather than a "neural-only" approach with symbolic-looking output.