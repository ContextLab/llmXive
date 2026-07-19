# Metrics Definitions

This document defines the metrics used in the evaluation of code testability.

## Cyclomatic Complexity

- **Definition**: A quantitative measure of the number of linearly independent paths through a program's source code.
- **Tool**: `radon.cc`
- **Significance**: Higher complexity often correlates with lower testability and higher maintenance cost.
- **Interpretation**:
 - 1-10: Well-structured, low risk.
 - 11-20: Moderate complexity, increased testing effort.
 - 21-50: High complexity, difficult to test.
 - >50: Untestable, unmaintainable.

## Halstead Volume

- **Definition**: A measure of the size of the implementation of an algorithm based on the operators and operands used.
- **Tool**: `radon.halstead`
- **Formula**: \( V = N \times \log_2(n) \) where \( N \) is total operators/operands, \( n \) is unique operators/operands.
- **Significance**: Indicates the volume of code and potential effort required to understand/maintain.

## Branch Coverage

- **Definition**: The percentage of executable branches in the code that have been executed by the test suite.
- **Tool**: `pytest --cov`
- **Significance**: Measures how thoroughly the test suite exercises the code's control flow.
- **Interpretation**:
 - 0%: No branches executed.
 - 100%: All branches executed.

## Pass Rate

- **Definition**: Binary metric indicating whether all tests in the HumanEval suite passed for a given code sample.
- **Calculation**: 1 if all tests passed, 0 otherwise.
- **Significance**: Measures functional correctness against the reference test suite.

## Statistical Metrics

- **Cohen's d**: Effect size measure for comparing means between two groups.
- **Wilcoxon p-value**: Significance of differences in paired continuous metrics.
- **McNemar p-value**: Significance of differences in paired binary outcomes (pass/fail).
- **Power**: Probability of correctly rejecting the null hypothesis when it is false.

## Sensitivity Analysis

- **Delta**: Difference in metric values between models (e.g., CodeGen vs. CodeLlama).
- **Effect Size**: Standardized measure of the magnitude of the difference between models.
