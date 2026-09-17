# Implementation Plan: Normalized Gaps Between Consecutive Squarefree Numbers

**Branch**: `001-normalized-squarefree-gaps` | **Date**: 2026-08-21 | **Spec**: [https://github.com/llmxive/specify/blob/main/projects/PROJ-722-normalized-gaps-between-consecutive-squa/spec.md]
**Input**: Feature specification from `/specs/001-normalized-squarefree-gaps/spec.md`

## Summary

This project investigates whether the gaps between consecutive squarefree integers, after normalization, follow an exponential distribution. The approach involves generating squarefree numbers using a linear sieve, calculating normalized gaps, and performing a Lilliefors goodness-of-fit test with Monte Carlo simulation. A control dataset generated via random thinning is used for comparison.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: NumPy, SciPy, Matplotlib
**Storage**: N/A - data is generated in memory and written to files for visualization
**Testing**: Pytest
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: CLI tool / Research script
**Performance Goals**: Process up to N = 10^7 within 6 hours. Memory usage ≤ 2 GB.
**Constraints**: Limited to 2 CPU cores and 7 GB RAM on the CI runner. No GPU access.
**Scale/Scope**:  Generate squarefree numbers up to N = 10^7, analyze normalized gaps, and perform statistical testing.

## Constitution Check

*   **I. Reproducibility**: All random seeds will be pinned. Dependencies are versioned via `requirements.txt`.
*   **II. Verified Accuracy**: All dataset citations will adhere to the verified sources list.
*   **III. Data Hygiene**: Raw data (squarefree sequences) will be generated on the fly, and derived data (gaps, normalized gaps) will be stored in new files.
*   **IV. Single Source of Truth**: All figures and statistics will be derived from the generated data and code.
*   **V. Versioning Discipline**: Changes to the constitution or core artifacts will be versioned.
*   **VI. Deterministic Number-Theoretic Sieving**:  The linear sieve will be implemented deterministically.
*   **VII. Rigorous Statistical Convergence Validation**:  KS tests and QQ-plots will be used to assess convergence and validate the exponential distribution hypothesis.

## Project Structure

```text
src/
├── squarefree.py         # Sieve implementation and gap calculation
├── statistics.py       # Lilliefors test and statistical analysis
├── visualization.py    # Plotting functions
└── main.py              # Main script to run the analysis
tests/
├── test_squarefree.py    # Unit tests for sieve implementation
├── test_statistics.py  # Unit tests for statistical functions
└── contract/
    └── dataset_schema.yaml # Schema for the normalized gap dataset
```

**Structure Decision**: A modular structure is chosen to separate sieve implementation, statistical analysis, and visualization. This allows for easy testing and maintainability.

## Complexity Tracking

No violations of the constitution are anticipated at this time.
