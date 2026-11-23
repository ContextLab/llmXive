# Neural vs. Symbolic Boundaries in the Neuro-Symbolic Learning Network

This document defines the architectural and operational boundaries between the neural
and symbolic components of the neuro-symbolic learning pipeline. It is intended
for researchers, developers, and reviewers to understand how the two systems
interact, where their responsibilities lie, and why the separation is critical
for interpretability and correctness.

## 1. Architectural Overview

The system implements a hybrid architecture where:

- The **Symbolic Layer** provides a deterministic, rule-based engine for solving
 arithmetic and logical problems. It operates on discrete mathematical objects
 and produces explicit, traceable derivations.
- The **Neural Layer** provides a probabilistic, language-based explanation
 generator that interprets problem contexts and generates natural language
 narratives.
- The **Neuro-Symbolic Layer** combines the two by using the symbolic trace to
 constrain and structure the neural narrative, ensuring that the final explanation
 is both fluent and logically grounded.

## 2. Symbolic Layer: Deterministic Rule-Based Engine

### 2.1 Purpose
The symbolic layer is responsible for:
- Parsing problem statements into formal representations.
- Applying a fixed set of mathematical rules (e.g., commutativity, associativity,
 distributive property, identity elements).
- Generating a step-by-step derivation trace that is verifiable and reproducible.

### 2.2 Boundaries
- **Input**: Structured problem definitions (e.g., JSON with operands, operators,
 and problem type).
- **Output**: A JSON trace of rule applications, including intermediate states and
 final results.
- **Constraints**:
 - No probabilistic elements; the same input always yields the same output.
 - Rules are explicitly defined in `code/generate/symbolic_explanation.py`.
 - The layer does not generate natural language; it produces structured data only.

### 2.3 Example Rule Application
For a problem `a + b = b + a`, the symbolic layer applies the `CommutativityRule`
and produces a trace:
```json
{
 "rule": "CommutativityRule",
 "input": {"a": 3, "b": 5},
 "output": {"result": 8},
 "steps": [
 {"operation": "add", "operands": [3, 5], "result": 8},
 {"operation": "commute", "operands": [5, 3], "result": 8}
 ]
}
```

## 3. Neural Layer: Probabilistic Language Model

### 3.1 Purpose
The neural layer is responsible for:
- Interpreting the semantic context of a problem.
- Generating natural language explanations that are fluent and pedagogically
 appropriate.
- Adapting to different problem types based on learned patterns.

### 3.2 Boundaries
- **Input**: Problem text and optional metadata (e.g., difficulty, topic).
- **Output**: A natural language narrative explaining the problem-solving process.
- **Constraints**:
 - The layer is probabilistic; the same input may yield different outputs.
 - It does not perform logical derivation; it relies on the symbolic layer for
 correctness.
 - The model is CPU-tractable (e.g., TinyLlama-1.1B) and runs in default precision.

### 3.3 Example Output
For the problem `3 + 5`, the neural layer might generate:
> "To solve this addition problem, we combine the two numbers. Starting with 3,
> we add 5 more, resulting in a total of 8."

## 4. Neuro-Symbolic Layer: Integration and Constraint

### 4.1 Purpose
The neuro-symbolic layer ensures that the neural narrative is grounded in the
symbolic trace. It:
- Uses the symbolic trace to define the logical structure of the explanation.
- Guides the neural model to generate text that aligns with the rule applications.
- Prevents "post-hoc rationalization" by ensuring the narrative does not contradict
 the symbolic derivation.

### 4.2 Boundaries
- **Input**: Symbolic trace (from the symbolic layer) and problem context.
- **Output**: A combined explanation where the neural narrative is constrained by
 the symbolic steps.
- **Constraints**:
 - The symbolic trace must be the primary source of truth for logical steps.
 - The neural layer cannot introduce new logical steps or contradict the trace.
 - The final output is a structured artifact that includes both the trace and
 the narrative.

### 4.3 Integration Logic
1. The symbolic layer generates a trace of rule applications.
2. The neuro-symbolic layer extracts key steps from the trace.
3. The neural layer generates a narrative for each step, guided by the trace.
4. The final explanation is a concatenation of the narrative segments, with the
 symbolic trace included for verification.

## 5. Validation of Distinctness

To ensure that the symbolic and neural outputs are distinct and not merely
rephrasings of each other, the system implements:
- **Jaccard Similarity Check**: Measures the overlap between the symbolic trace
 and the neural narrative. A high similarity score indicates insufficient
 distinctness.
- **Structural Validation**: Ensures that the symbolic trace contains explicit
 rule applications, while the neural narrative contains natural language
 explanations.

See `code/generate/validate_distinctness.py` for implementation details.

## 6. Theoretical Implications

This architecture addresses concerns raised by Turing (operational test),
Wolfram (rule-based complexity), and von Neumann (stability under perturbation):
- **Turing**: The symbolic layer provides an operational test of correctness.
- **Wolfram**: The rule-based engine demonstrates how simple rules can generate
 complex derivations.
- **von Neumann**: The separation ensures stability; the symbolic layer is
 deterministic, while the neural layer is probabilistic but constrained.

## 7. Future Work

- Extend the symbolic rule set to cover more problem types (e.g., algebra, geometry).
- Investigate adaptive thresholding for the neural-symbolic integration.
- Explore user studies to measure the pedagogical effectiveness of the combined
 explanations.

## 8. References

- `code/generate/symbolic_explanation.py`: Symbolic rule engine implementation.
- `code/generate/neural_explanation.py`: Neural explanation generator.
- `code/generate/neuro_symbolic_explanation.py`: Integration logic.
- `code/generate/validate_distinctness.py`: Distinctness validation utilities.