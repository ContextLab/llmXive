# Research: Evaluating the Effectiveness of LLM-Driven Code Simplification on Performance

## Overview

This research evaluates whether LLM-driven simplification of Python functions leads to measurable improvements in execution time and memory usage. The study uses a quantized CodeLlama-3B model to generate simplified versions of functions from the CodeSearchNet dataset, then benchmarks performance differences using a paired statistical test on function-level means.

**Key Methodological Corrections**:
1. **Fixed Iterations**: A fixed number of iterations per function (no adaptive range).
2. **Deterministic Test Generation**: Functional equivalence verified via generated deterministic tests (or existing tests) for ALL functions, replacing random input generation.
3. **Universal Verification**: All functions, regardless of line count, must pass equivalence checks.
4. **No Pilot Power Analysis**: Fixed iteration count replaces pilot analysis.
5. **Unit of Analysis**: Statistical test performed on the 100 function-level means, not raw iteration logs.

## Dataset Strategy

| Dataset | Purpose | Source URL | Verification |
|---------|---------|------------|--------------|
| CodeSearchNet (Python) | Primary source of Python functions for simplification | `https://huggingface.co/datasets/codesearchnet` | ✅ Verified (Canonical HuggingFace API) |

### Dataset Selection Rationale

- **CodeSearchNet** provides a large, diverse corpus of Python functions.
- **Limitation**: The standard CodeSearchNet dataset contains code-docstring pairs but **does not contain unit tests**.
- **Strategy**: To address the "oracle problem," the pipeline includes a **Test Generation Step**:
  1. Attempt to extract existing tests from the dataset metadata (if available).
  2. If no tests exist, use a small, deterministic heuristic or a lightweight LLM to generate a minimal set of test inputs (e.g., edge cases, typical values) to verify functional equivalence.
  3. Functions for which no valid test suite can be generated are excluded.
- **Filtering Strategy**: Only functions that are syntactically valid, standalone (no external dependencies), and for which a test suite can be generated are retained.
- **Canonical Source**: The official HuggingFace dataset loader is used to ensure reproducibility, avoiding transient file paths.

## Model Strategy

| Model | Purpose | Source | Quantization |
|-------|---------|--------|--------------|
| CodeLlama-3B | Code simplification | HuggingFace Hub (auto-downloaded) | 4-bit (CPU-compatible) |

### Model Selection Rationale

- **CodeLlama-3B** is chosen for its balance of code understanding capability and resource efficiency.
- **4-bit quantization** ensures the model fits within the 7 GB RAM constraint of the CI runner.
- **CPU-only inference** is enforced via `torch` CPU build and `accelerate` configuration.
- Alternative models (e.g., CodeLlama-7B/13B) are excluded due to RAM constraints.

## Statistical Methodology

### Hypothesis Testing

- **Null Hypothesis (H0)**: No difference in execution time/memory between original and simplified code.
- **Alternative Hypothesis (H1)**: Simplified code has significantly lower execution time/memory.
- **Unit of Analysis**: The **mean performance of each function pair** (N=100). The 100 iterations per function are used to reduce measurement noise and estimate the mean/variance per function, but the statistical test is performed on the **100 function means** to avoid pseudoreplication.
- **Test Type**: Paired t-test (if normality holds) or Wilcoxon signed-rank test (if normality violated).
- **Normality Check**: Shapiro-Wilk test (α = 0.05) on the 100 function means.
- **Multiple Comparison Correction**: Bonferroni correction for two tests (time and memory).

### Sample Size & Power

- **Target Functions**: 100 (fixed).
- **Iterations per Function**: Exactly 100 (fixed).
- **Power Analysis**: Pilot power analysis is **omitted**. The fixed iteration count of 100 is chosen to ensure reproducibility and avoid the variance estimation issues of a small pilot. If the effect size is small, the study may be underpowered, which will be reported as a limitation.

### Measurement Tools

- **Execution Time**: Python `time` module (CPU time)
- **Memory Usage**: `tracemalloc` (peak memory)
- **Timeout**: 5 seconds per execution
- **Memory Limit**: 500 MB per execution

## Functional Equivalence

- **Method**: Execute a **deterministic test suite** for each function on both the original and simplified code.
  - If existing tests are available in the dataset metadata, use them.
  - If not, generate a minimal deterministic test suite (e.g., typical inputs, edge cases) using a lightweight heuristic.
- **Threshold**: 100% test pass rate required.
- **Universal Application**: **All functions**, regardless of line count, must pass this check. There is no exemption for short functions (<5 lines) to prevent selection bias where "broken but fast" code skews results.
- **Exclusion**: Functions failing any unit test (or for which no test suite can be generated) are excluded from performance analysis.
- **Rationale**: This resolves the "oracle problem" by using ground-truth or deterministically generated tests rather than synthetic random inputs, ensuring that performance gains are not due to functional drift.

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM generates invalid code | Retry up to 2 times; log failures; skip function |
| Infinite loop or excessive memory | Enforce 5s timeout and 500MB limit per execution |
| Functional drift | Exclude function pairs failing test suite |
| Dataset lacks executability/tests | Filter out functions without tests or external dependencies; generate tests if missing |
| Low statistical power | Report limitation; fixed 100 iterations ensures consistency; N=100 functions |

## Decision Rationale

- **CPU-only execution**: Required for CI compatibility; no GPU available.
- **4-bit quantization**: Balances model size and RAM constraints.
- **Paired statistical test on means**: Controls for function-specific variability and avoids pseudoreplication.
- **Bonferroni correction**: Prevents false positives from multiple hypothesis tests.
- **Fixed 100 iterations**: Ensures reproducibility and satisfies Constitution Principle VI.
- **Deterministic test generation**: Solves the oracle problem by using ground-truth or generated tests.
- **Universal equivalence check**: Prevents bias by ensuring all functions, including short ones, are validated.
- **Target N=100**: Ensures the 6-hour runtime cap is met with a safety margin (A set of functions * (60s inference + iterations * 0.1s) [deferred] + overhead).