# Research Documentation: Evaluating the Impact of Prompt Complexity on LLM Code Generation

## Overview

This document outlines the research methodology, metrics, and validation sources used in the `PROJ-527` project to evaluate how prompt complexity influences Large Language Model (LLM) code generation performance.

## Research Question

How does the structural complexity of a prompt (measured by token count, structural element count, and dependency chain depth) affect the pass rate of generated code on the HumanEval benchmark?

## Metrics and Validation Sources

### 1. Prompt Complexity Metrics

- **Token Count**: Calculated using `tiktoken` (cl100k_base).
- **Structural Element Count**: Number of examples, constraints, and steps explicitly defined in the prompt.
- **Dependency Chain Depth**: Maximum depth of instruction dependencies (state transitions) within the prompt.

### 2. Code Quality Metrics

The following metrics are extracted from generated code to assess quality and complexity:

#### Cyclomatic Complexity (McCabe)

- **Definition**: A software metric used to indicate the complexity of a program. It is a measure of the number of linearly independent paths through a program's source code.
- **Validation Source**: McCabe, J. (1976). "A Complexity Measure". *IEEE Transactions on Software Engineering*, SE-2(4), 308-320.
- **Implementation**: Calculated using the `radon` library (`radon cc`), which implements the standard McCabe algorithm for Python Abstract Syntax Tree (AST) analysis.
- **Usage**: Higher cyclomatic complexity often correlates with harder-to-maintain code and potentially lower correctness in generated solutions.

#### Lines of Code (LOC)

- **Definition**: The number of lines in the generated source code.
- **Validation Source**: Standard software engineering metric (see: Boehm et al., 1981; Pressman, 2010).
- **Implementation**: Counted as non-empty lines in the generated code string.

#### Security Vulnerabilities

- **Definition**: Detection of known insecure patterns (e.g., `eval` usage, hardcoded credentials).
- **Validation Source**: Ruff Documentation v0.1.0 (https://docs.astral.sh/ruff/).
- **Implementation**: Used via `ruff check --select=SEC` to identify security rule violations (SEC101, SEC301, etc.).

## Methodology

1. **Prompt Generation**: Generate 5 complexity variants (simple, moderate, complex, very_complex, degenerate) per HumanEval problem.
2. **Code Generation**: Query LLM with each variant.
3. **Static Analysis**: Run `radon` and `ruff` on generated code to extract complexity and security metrics.
4. **Execution**: Run generated code against HumanEval test cases.
5. **Statistical Analysis**: Use Linear Mixed Models (LMM) to correlate prompt complexity with pass rates, controlling for problem difficulty.

## Limitations

- **Sample Size**: {{claim:c_446458ce}} (2410.12381, https://arxiv.org/abs/2410.12381) While sufficient for exploratory analysis, power analysis is required for definitive conclusions.
- **Token vs. Structure**: Token count and structural complexity are often collinear. We address this via orthogonalization (PCA) or VIF monitoring.
- **State Transitions**: As noted by reviewer Alan Turing, token count alone does not capture the "state transitions" induced in the LLM. We measure this via `dependency_chain_depth` (T062).

## References

1. **McCabe, J. (1976)**. "A Complexity Measure". *IEEE Transactions on Software Engineering*, SE-2(4), 308-320.
 - *Cited for: Definition and calculation of Cyclomatic Complexity.*
2. **Ruff Documentation v0.1.0**. https://docs.astral.sh/ruff/
 - *Cited for: Security vulnerability detection rules and static analysis capabilities.*
3. **Turing, A. M. (1950)**. "Computing Machinery and Intelligence". *Mind*.
 - *Context: Reviewer feedback on state transitions in machine representation.*