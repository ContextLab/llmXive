# Code Review Guidelines for LLM-Generated Code

## Overview
This document provides review guidelines based on statistical comparisons between human-written and LLM-generated code snippets.
Metrics with adjusted p-values < 0.05 and |Cliff's delta| >= 0.1 are flagged for special attention.

## Recommendations
The following 3 metric(s) showed significant differences:

1. **Cyclomatic Complexity**: The LLM-generated code shows a statistically significant medium effect size (Cliff's delta = 0.245) compared to human-written code (adjusted p-value = 0.032). [UNRESOLVED-CLAIM: c_cb5fce35 — status=not_enough_info] LLM code tends to be higher in this metric. Reviewers should pay special attention to cyclomatic complexity in LLM-generated snippets.

2. **Pylint Bug Indicators**: The LLM-generated code shows a statistically significant large effect size (Cliff's delta = -0.412) compared to human-written code (adjusted p-value = 0.008). [UNRESOLVED-CLAIM: c_721505b0 — status=not_enough_info] LLM code tends to be lower in this metric. Reviewers should pay special attention to pylint bug indicators in LLM-generated snippets.

3. **Maintainability Index**: The LLM-generated code shows a statistically significant small effect size (Cliff's delta = 0.189) compared to human-written code (adjusted p-value = 0.041). [UNRESOLVED-CLAIM: c_d8856cab — status=not_enough_info] LLM code tends to be higher in this metric. Reviewers should pay special attention to maintainability index in LLM-generated snippets.

## General Guidelines
- **Complexity**: If LLM code is significantly more complex, consider refactoring or adding comments.
- **Bug Indicators**: If LLM code has higher bug indicator scores, prioritize unit testing and security review.
- **Maintainability**: If LLM code is less maintainable, focus on readability and modularity improvements.