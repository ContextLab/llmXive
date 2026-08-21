# Research: Evaluating Code Generation Impact on Code Smell Frequency

## Balanced Blocked Design Implementation

This document details the deviations from the original specification requirements to accommodate the practical constraints of the experimental setup while maintaining statistical validity.

### Deviation Table

| Original Spec Item | Implemented Design | Rationale |
|:--- |:--- |:--- |
| Sample Size ≥ 1000 (Human) | 150 Human samples (3 per repo × 50 repos) [UNRESOLVED-CLAIM: c_f57ffc79 — status=not_enough_info] | Balanced Blocked Design; CI constraints; statistical power sufficient with blocking. |
| Sample Size ≥ 50 (LLM) | 150 LLM samples (3 per repo × 50 repos) [UNRESOLVED-CLAIM: c_3bd97142 — status=not_enough_info] | Balanced design requires equal N per group. |
| Causal Claims | Associational Language | Observational study design; no experimental control over generation. |

### Explicit Rejection Statement

The original requirement for causal inference (FR-007) is REJECTED. This study is observational and uses associational language only. We cannot assert that code generation *causes* changes in code smell frequency due to the lack of random assignment to treatment conditions and potential confounding variables inherent in the data collection process (e.g., repository-specific coding styles, issue complexity). All conclusions are framed in terms of association and correlation.