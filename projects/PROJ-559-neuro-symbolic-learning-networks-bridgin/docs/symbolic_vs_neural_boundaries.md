# Symbolic vs. Neural Boundaries in Neuro-Symbolic Learning Networks

This document defines the architectural boundaries, interaction protocols, and theoretical distinctions between the symbolic and neural components of the PROJ-559 neuro-symbolic learning pipeline.

## 1. Architectural Philosophy

The system implements a **hybrid architecture** where the symbolic layer acts as the **structural governor** and the neural layer acts as the **narrative generator**. This design directly addresses concerns regarding "post-hoc rationalization" (Turing) and "coherence mistaken for truth" (Kahneman) by enforcing that logical validity precedes narrative fluency.

### 1.1 The Symbolic Layer (System 2)
- **Nature**: Discrete, rule-based, deterministic.
- **Role**: Solves the problem using explicit algebraic and logical rules (Commutativity, Associativity, Distributivity, Identity).
- **Output**: A structured **Trace** (JSON) representing the sequence of rule applications.
- **Constraint**: The trace is the "ground truth" of the solution path. It is not approximated; it is computed.
- **Implementation**: `code/generate/symbolic_explanation.py` (SymbolicSolver).

### 1.2 The Neural Layer (System 1)
- **Nature**: Continuous, probabilistic, pattern-matching.
- **Role**: Generates natural language explanations and intuitive justifications.
- **Output**: A **Narrative** (Text) describing the solution process.
- **Constraint**: The neural layer is *constrained* by the symbolic trace. It cannot invent steps that contradict the trace.
- **Implementation**: `code/generate/neural_explanation.py` (NeuralExplanationGenerator).

## 2. Boundary Definitions

The boundary between these two systems is defined by the **Interface Protocol** in `code/generate/neuro_symbolic_explanation.py`.

### 2.1 Input/Output Contract
| Component | Input | Output | Format |
|-----------|-------|--------|--------|
| **Symbolic Solver** | Problem Statement | Execution Trace | JSON (List of Rule IDs + Args) |
| **Neural Generator** | Problem + Trace | Natural Language Explanation | Text String |
| **Neuro-Symbolic Orchestrator** | Problem | Combined Explanation | Structured Object (Trace + Text) |

### 2.2 The "Governance" Mechanism
To prevent the neural network from "hallucinating" a solution path:
1. The **Symbolic Solver** runs first. If it fails to find a valid derivation, the process halts (or falls back to a specific error state).
2. The **Neural Generator** receives the *proven* trace as a strict prompt constraint.
3. The prompt explicitly forbids the neural model from adding steps not present in the trace.
4. **Validation**: The `code/generate/validate_distinctness.py` module ensures the neural narrative does not merely repeat the trace but *interprets* it, while maintaining logical fidelity.

## 3. Distinctness Criteria

Per the project requirements (T017), the symbolic trace and neural narrative must be **distinct** artifacts.

- **Symbolic Trace**:
 - **Structure**: Hierarchical, logical, machine-readable.
 - **Content**: Rule names (e.g., `DistributiveRule`), operands, intermediate states.
 - **Purpose**: Verification, debugging, and pedagogical scaffolding.
 - **Example**: `{"step": 1, "rule": "Commutativity", "args": ["a", "b"]}`

- **Neural Narrative**:
 - **Structure**: Linear, linguistic, human-readable.
 - **Content**: Explanations of *why* a rule applies, analogies, and step-by-step reasoning in natural language.
 - **Purpose**: Student comprehension and engagement.
 - **Example**: "First, we rearrange the terms because addition is commutative, allowing us to group the constants together."

## 4. Handling Divergence

In cases where the neural model's intuition conflicts with the symbolic derivation:
- **Priority**: The **Symbolic Trace** always wins.
- **Mechanism**: If the neural generator produces a narrative that contradicts the trace, the `validate_distinctness` module flags this as a "Logical Inconsistency" error.
- **Resolution**: The system logs the discrepancy (see `data/derived/simulation_logs.csv` for discrepancy flags) and defaults to the symbolic derivation for the final answer.

## 5. Implementation References

- **Symbolic Engine**: `code/generate/symbolic_explanation.py`
 - Implements `SymbolicRule`, `CommutativityRule`, `AssociativityRule`, `DistributiveRule`, `IdentityElementRule`.
- **Neural Engine**: `code/generate/neural_explanation.py`
 - Uses a distilled CPU-tractable LLM (e.g., TinyLlama) constrained by the trace.
- **Orchestrator**: `code/generate/neuro_symbolic_explanation.py`
 - Combines the two outputs into the final `explanation_neuro_symbolic.txt`.
- **Validator**: `code/generate/validate_distinctness.py`
 - Ensures the Jaccard similarity between trace and narrative is within expected bounds (distinct but related).

## 6. Theoretical Alignment

This boundary design aligns with:
- **Stephen Wolfram**: The symbolic layer represents the "simple underlying rules" that generate complexity, while the neural layer represents the "computational universe" of interpretations.
- **John von Neumann**: The discrete (symbolic) and continuous (neural) are kept separate to ensure "operational stability," avoiding the noise of the continuous layer corrupting the logical depth of the discrete layer.
- **Daniel Kahneman**: The system forces "System 2" (symbolic) to engage before "System 1" (neural) generates a fluent narrative, mitigating the risk of WYSIATI (What You See Is All There Is).

## 7. Future Considerations

Future iterations may explore:
- **Neuro-Symbolic Feedback Loops**: Using neural confidence scores to weight symbolic rule selection (currently disabled to preserve determinism).
- **Adaptive Boundaries**: Dynamically adjusting the strictness of the trace constraint based on student proficiency levels.

---
*Generated as part of PROJ-559: Neuro-Symbolic Learning Networks*