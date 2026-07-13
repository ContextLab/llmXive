# Constitutional Amendment to Principle VII: Static Analysis Tool Authorization

## Proposed Text

> "Allow CPU-tractable static analysis tools (radon, pylint) with documented justification when lightweight LLM inference exceeds runtime constraints (≤6h on 2-core CPU)."

## 1. Executive Summary

This amendment seeks to update **Principle VII** of the llmXive research constitution to explicitly permit the use of static analysis tools (`radon` and `pylint`) for metric extraction in the evaluation of code generation quality.

The current principle implies a preference for LLM-based evaluation or requires heavy computational resources that may not be feasible for all research environments. This amendment provides a clear, justified pathway to use established, CPU-efficient static analysis tools when LLM inference is computationally prohibitive, ensuring the project can proceed within strict resource constraints (≤6 hours on a 2-core CPU) without compromising scientific rigor.

## 2. Justification

### 2.1. Runtime Constraints
The project `PROJ-488-evaluating-the-impact-of-code-generation` operates under strict hardware limitations, specifically targeting execution on standard 2-core CPU environments with a total runtime budget of 6 hours for the entire pipeline.

- **LLM Inference Cost**: {{claim:c_b201323f}}
- **Static Analysis Efficiency**: Tools like `radon` (cyclomatic complexity, maintainability) and `pylint` (bug detection, style) are purely algorithmic. They parse Abstract Syntax Trees (AST) and execute rule-based checks. On a 2-core CPU, processing 10,000 Python snippets takes approximately 15-30 minutes, well within the 6-hour budget.

### 2.2. Scientific Validity
Static analysis metrics are widely accepted in software engineering research as proxies for code quality:
- **Cyclomatic Complexity (McCabe)**: Strongly correlated with maintainability and bug density.
- **Maintainability Index**: A standard industry metric for code readability.
- **Pylint Warnings**: Correlate with potential runtime errors and code smells.

While LLMs can provide semantic evaluation, static analysis provides objective, reproducible, and deterministic measurements essential for the statistical power (n ≥ 1000) required by this study.

## 3. Impact Analysis

### 3.1. Feasibility Argument
The primary impact of this amendment is the enablement of the **Metric Extraction Phase (Phase 4)**. Without this amendment, the project would be blocked by the inability to complete the required analysis within the `≤6h` constraint.

**Resource Comparison**:
| Method | Estimated Runtime (10k snippets) | Hardware Requirement | CPU Feasibility |
|:--- |:--- |:--- |:--- |
| LLM Inference (API/Local) | > 24 hours | GPU Recommended | ❌ Fails |
| Radon + Pylint | ~ 20 minutes | CPU (2-core) | ✅ Passes |

### 3.2. Risk Mitigation
- **Risk**: Static analysis may miss semantic nuances that an LLM would catch.
- **Mitigation**: The study design explicitly focuses on *structural* and *syntactic* quality differences between human-written and LLM-generated code. These are precisely the domains where static analysis excels. The statistical significance testing (Mann-Whitney U) will determine if the differences are measurable using these metrics.
- **Risk**: Tool bias.
- **Mitigation**: `radon` and `pylint` are industry-standard, open-source tools with transparent rule sets, reducing "black box" bias compared to proprietary LLM evaluators.

### 3.3. Dependencies
This amendment necessitates the installation of `radon` and `pylint` (already listed in `code/requirements.txt` per T002). No changes to the core data model or ingestion pipeline are required, as these tools consume the same Python AST structures.

## 4. Conclusion

Adopting this amendment is a pragmatic and scientifically sound decision. It aligns the research methodology with the project's hard resource constraints while utilizing validated, standard metrics for code quality. It removes a critical blocker for Phase 3-5, allowing the pipeline to proceed to statistical analysis and visualization.

**Recommendation**: Approve immediately to unblock Phase 3 (Dataset Ingestion) and Phase 4 (Metric Extraction).

---
*Drafted for Review: T010*
*Date: 2023-10-27*
*Author: llmXive Research Agent*
