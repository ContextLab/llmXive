# Research Documentation: Prompt Complexity Impact Evaluation

## Overview
This document outlines the research methodology, validation sources, and analytical frameworks used in the `PROJ-527-evaluating-the-impact-of-prompt-complexi` project. It specifically addresses the requirement for citable validation of readability and complexity metrics (FR-008).

## 1. Prompt Complexity Definition
Prompt complexity is operationalized through two orthogonal dimensions:
1. **Token Length**: The number of tokens in the prompt (using `cl100k_base` encoding).
2. **Structural Elements**: The count of distinct instructional components (examples, constraints, multi-step instructions).

### 1.1. Validation of Structural Metrics
The counting of structural elements is based on the assumption that cognitive load correlates with the number of distinct logical constraints a model must satisfy. This aligns with principles of **Cognitive Load Theory** (Sweller, 1988), which posits that working memory is limited and that complex instruction sets increase extraneous load.

## 2. Code Quality & Readability Metrics (FR-008)
To evaluate the quality of code generated in response to varying prompt complexities, we employ static analysis metrics. These metrics are not arbitrary; they are derived from established software engineering literature and standard industry tools.

### 2.1. Cyclomatic Complexity (McCabe)
- **Metric**: Cyclomatic Complexity (M).
- **Source**: McCabe, T. J. (1976). "A Complexity Measure". *IEEE Transactions on Software Engineering*, SE-2(4), 308–320.
- **Definition**: A quantitative measure of the number of linearly independent paths through a program's source code.
- **Formula**: $M = E - N + 2P$, where $E$ is edges, $N$ is nodes, and $P$ is the number of connected components.
- **Interpretation**:
 - $1 \le M \le 10$: Low complexity, maintainable code.
 - $11 \le M \le 20$: Moderate complexity, increased risk of defects.
 - $M > 20$: High complexity, likely difficult to test and maintain.
- **Implementation**: Calculated via the `ruff` static analyzer (which implements the standard AST-based algorithm).

### 2.2. Lines of Code (LOC)
- **Metric**: Non-blank, non-comment lines.
- **Source**: Pressman, R. S. (2014). *Software Engineering: A Practitioner's Approach*. McGraw-Hill Education.
- **Relevance**: Serves as a proxy for code verbosity and effort. High LOC in generated code may indicate redundancy induced by verbose prompts.

### 2.3. Indentation Consistency
- **Metric**: Adherence to PEP 8 indentation rules.
- **Source**: Python Software Foundation. "PEP 8 – Style Guide for Python Code".
- **Relevance**: Inconsistent indentation is a primary indicator of poor code structure and potential syntax errors in dynamically typed languages.

### 2.4. Security Vulnerability Flagging
- **Metric**: Detection of hardcoded credentials and unsafe function usage (`eval`, `exec`).
- **Source**: OWASP Top 10 (2021).
 - **A02:2021 - Cryptographic Failures**: Hardcoded secrets.
 - **A03:2021 - Injection**: Use of `eval`/`exec`.
- **Implementation**: Pattern matching via `ruff` security rules (S105, S307).

## 3. Statistical Analysis Framework
### 3.1. Linear Mixed Models (LMM)
- **Requirement**: FR-005 mandates LMM over ANOVA to handle nested data structures.
- **Model Structure**:
 - **Fixed Effects**: Prompt Complexity Level (Simple, Moderate, Complex, Very Complex, Degenerate).
 - **Random Effects**: Random intercepts for `problem_id` to account for varying baseline difficulty across HumanEval problems.
 - **Covariate**: Prompt Token Count (to control for length effects as per FR-012).
- **Source**: Pinheiro, J. C., & Bates, D. M. (2000). *Mixed-Effects Models in S and S-PLUS*. Springer.

### 3.2. Multiple Comparison Correction
- **Method**: Bonferroni or Holm-Bonferroni correction.
- **Rationale**: Controlling Family-Wise Error Rate (FWER) when performing multiple pairwise comparisons between complexity levels.
- **Source**: Holm, S. (1979). "A Simple Sequentially Rejective Multiple Test Procedure". *Scandinavian Journal of Statistics*, 6(2), 65–70.

## 4. Limitations and Assumptions
### 4.1. State Transition Proxy Limitation
As noted by reviewer `alan-turing-simulated`, token length is a proxy for internal state transitions, not a direct measurement. This study assumes that increased structural elements and token counts correlate with increased cognitive load on the LLM's attention mechanisms. This limitation is acknowledged in the analysis and discussion sections.

### 4.2. Sample Size and Power
{{claim:c_c20b94eb}} (2410.12381, https://arxiv.org/abs/2410.12381) With 5 variants per problem, the total sample size is 820. [UNRESOLVED-CLAIM: c_51c14cac — status=not_enough_info] Power analysis suggests this is sufficient to detect medium-to-large effect sizes (Cohen's d > 0.5) at $\alpha = 0.05$. Small effects may be underpowered.

## 5. Data Provenance
- **Dataset**: HumanEval (openai/human-eval) via HuggingFace Datasets.
- **Generation**: LLM queries via HuggingFace Inference API (with fallback to local GGUF).
- **Execution**: Isolated subprocess execution with timeout.

## 6. References
1. McCabe, T. J. (1976). A Complexity Measure. *IEEE Transactions on Software Engineering*.
2. Pressman, R. S. (2014). *Software Engineering: A Practitioner's Approach*.
3. Python Software Foundation. PEP 8 – Style Guide for Python Code.
4. OWASP Foundation. OWASP Top 10: 2021.
5. Pinheiro, J. C., & Bates, D. M. (2000). *Mixed-Effects Models in S and S-PLUS*.
6. Holm, S. (1979). A Simple Sequentially Rejective Multiple Test Procedure. *Scandinavian Journal of Statistics*.
7. Sweller, J. (1988). Cognitive load during problem solving: Effects on learning. *Cognitive Science*.