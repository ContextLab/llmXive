# Research Documentation: Prompt Complexity and LLM Performance

## Overview
This document outlines the research methodology, data sources, and validation standards used in the `PROJ-527` project to evaluate the impact of prompt complexity on LLM code generation.

## 1. Complexity Metrics & Validation Sources

### 1.1 Prompt Complexity (Input)
Prompt complexity is measured via:
- **Token Count**: Calculated using `tiktoken` (cl100k_base).
- **Structural Elements**: Count of examples, constraints, and instructions (custom parser).

### 1.2 Code Readability & Complexity (Output)
To evaluate the quality of generated code, we extract static analysis metrics. These metrics are not arbitrary; they are grounded in established software engineering literature and standard tooling validation.

#### Cyclomatic Complexity
- **Definition**: A quantitative measure of the number of linearly independent paths through a program's source code.
- **Validation Source**: **McCabe, T. J. (1976). "A Complexity Measure". IEEE Transactions on Software Engineering, 2(4), 308–320.**
- **Implementation**: Calculated via the `ruff` linter (using the `mccabe` plugin logic).
- **Interpretation**:
 - 1-10: Low risk, easy to test.
 - 11-20: Moderate complexity.
 - 21-50: High complexity, difficult to maintain.
 - >50: Untestable, requires immediate refactoring.

#### Lines of Code (LOC)
- **Definition**: Count of non-blank, non-comment lines.
- **Validation Source**: Standard software engineering metric (e.g., **Pressman, R. S. (2014). Software Engineering: A Practitioner's Approach**).
- **Usage**: Serves as a proxy for code size and maintenance burden.

#### Indentation Consistency
- **Definition**: Adherence to consistent indentation (spaces vs. tabs, depth consistency).
- **Validation Source**: **PEP 8 (Style Guide for Python Code)**.
- **Implementation**: Enforced by `ruff` (E111, E114 rules).

#### Security Vulnerabilities (Flagging)
- **Definition**: Detection of dangerous patterns in generated code.
- **Validation Sources**:
 - **OWASP Top 10 (2021)**: Specifically A01:2021 – Broken Access Control and A03:2021 – Injection.
 - **CWE (Common Weakness Enumeration)**:
 - **CWE-95**: Improper Neutralization of Directives in Dynamically Evaluated Code (Eval Injection).
 - **CWE-798**: Use of Hard-coded Credentials.
- **Implementation**: `ruff` security rules (S102 for `eval`, S105 for secrets).
- **Protocol**: Samples flagged for security issues are marked for **manual review** but do not cause the automated execution test to fail, ensuring the pipeline continues while highlighting risks.

## 2. Statistical Analysis Methodology

### 2.1 Linear Mixed Models (LMM)
- **Reference**: **Pinheiro, J. C., & Bates, D. M. (2000). Mixed-Effects Models in S and S-PLUS.**
- **Rationale**: Used to handle the nested structure of the data (5 prompt variants per HumanEval problem) and control for problem-specific difficulty via random intercepts.
- **Covariate**: Prompt token count (as per FR-012).

### 2.2 Multiple Comparison Correction
- **Reference**: **Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. Scandinavian Journal of Statistics.**
- **Method**: Holm-Bonferroni correction applied to pairwise comparisons of complexity levels to control family-wise error rate.

## 3. Limitations & Assumptions

### 3.1 State Transition Proxy
As noted by reviewer `alan-turing-simulated`, token length is a proxy for the "state transitions" induced in the LLM's internal representation. While we measure structural elements and tokens, we acknowledge this is an indirect measure of the cognitive load on the model's attention mechanism. This is documented as a limitation in the research assumptions.

### 3.2 Sample Size & Power
The HumanEval dataset (164 (2410.12381, https://arxiv.org/abs/2410.12381) problems) provides a moderate sample size. Power analysis suggests that while main effects (complexity vs. pass rate) are detectable, subtle interaction effects may be underpowered. This is reportedin `data/results/analysis_summary.csv`.

## 4. Data Sources
- **HumanEval Dataset**: `openai/human-eval` (Hugging Face).
- **LLM Client**: HuggingFace Inference API (CPU-tractable).
- **Static Analysis Tool**: `ruff` (Rust-based Python linter).

## 5. References
1. McCabe, T. J. (1976). A Complexity Measure. IEEE Transactions on Software Engineering.
2. Pressman, R. S. (2014). Software Engineering: A Practitioner's Approach. McGraw-Hill.
3. Python Software Foundation. PEP 8 -- Style Guide for Python Code.
4. OWASP Foundation. OWASP Top 10 Web Application Security Risks (2021).
5. Pinheiro, J. C., & Bates, D. M. (2000). Mixed-Effects Models in S and S-PLUS. Springer.
6. Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. Scandinavian Journal of Statistics.