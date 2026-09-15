# Implementation Plan: Normalized Squarefree Gaps

**Branch**: `001-normalized-squarefree-gaps` | **Date**: 2026-08-21 | **Spec**: [https://github.com/llmxive/specify/blob/main/projects/PROJ-722-normalized-gaps-between-consecutive-squa/spec.md]
**Input**: Feature specification from `/specs/001-normalized-squarefree-gaps/spec.md`

## Summary

This project aims to determine if the gaps between consecutive squarefree integers, after normalization, follow an exponential distribution. The technical approach utilizes a linear sieve to generate squarefree numbers, calculates normalized gaps, and employs a Lilliefors-style goodness-of-fit test (via Monte Carlo simulation) to compare the empirical distribution with a standard exponential distribution. A control dataset generated through random thinning will be used to validate the heuristic and account for potential biases in the test.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: NumPy, SciPy, Matplotlib
**Storage**: N/A (data generated in memory and processed)
**Testing**: pytest
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: library/cli
**Performance Goals**: Process up to $10^7$ squarefree numbers within the 6-hour time limit.  Peak memory usage below 2GB.
**Constraints**: Limited to 2 CPU cores, ~7GB RAM, and ~14GB disk space on the GitHub Actions runner. No GPU access.
**Scale/Scope**: Generate squarefree numbers up to $10^7$ and perform statistical tests on the resulting gap distribution.

## Constitution Check

*   **I. Reproducibility**: All random seeds will be pinned within the code. The integer generation is deterministic.
*   **II. Verified Accuracy**: All citations in the research document will be verified before contributing review points.
*   **III. Data Hygiene**:  Data will be generated programmatically. No external data sources are used.
*   **IV. Single Source of Truth**: All figures and statistics will be derived from the generated data and code.
*   **V. Versioning Discipline**:  This plan will be versioned alongside the project code.
*   **VI. Deterministic Number-Theoretic Sieving**: The linear sieve will be implemented deterministically to ensure consistent results.
*   **VII. Rigorous Statistical Convergence Validation**: Statistical claims will be supported by KS test p-values and visual confirmation via QQ-plots across multiple scales.

## Project Structure

```text
src/
├── squarefree.py       # Linear sieve implementation for generating squarefree numbers
├── gap_analysis.py     # Functions for calculating gaps and normalization
├── statistical_tests.py # Lilliefors test implementation
├── visualization.py   # Functions for generating plots
└── main.py             # Main script to run the analysis
tests/
├── test_squarefree.py  # Unit tests for the sieve implementation
├── test_gap_analysis.py # Unit tests for the gap analysis functions
└── test_statistical_tests.py # Unit tests for the statistical tests
```

**Structure Decision**: A single project structure is appropriate as the project primarily involves numerical computation and data analysis. The code will be organized into modules for clarity and testability.

## Complexity Tracking

N/A

---
