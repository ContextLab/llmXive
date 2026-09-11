# Implementation Plan: Normalized Gaps Between Consecutive Squarefree Numbers

**Branch**: `001-normalized-squarefree-gaps` | **Date**: 2024-10-27 | **Spec**: [https://github.com/llmxive/specify/blob/main/projects/PROJ-722-normalized-gaps-between-consecutive-squa/spec.md](https://github.com/llmxive/specify/blob/main/projects/PROJ-722-normalized-gaps-between-consecutive-squa/spec.md)
**Input**: Feature specification from `/specs/[001-normalized-squarefree-gaps]/spec.md`

## Summary

This project aims to determine if the normalized gaps between consecutive squarefree integers follow an exponential distribution. The core approach involves generating squarefree numbers using a linear sieve, calculating normalized gaps, and then performing a Lilliefors-style goodness-of-fit test against an exponential distribution. A random thinning simulation serves as a control to validate the heuristic underpinning the hypothesis.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: NumPy, SciPy, Matplotlib
**Storage**: N/A (data is generated and processed in memory)
**Testing**: Pytest
**Target Platform**: Linux server (GitHub Actions runner)
**Project Type**: CLI tool / Script
**Performance Goals**: Complete analysis for N = 10^7 within 6 hours on a 2 CPU core runner. Peak memory usage under 2GB.
**Constraints**: Limited to 6 hours runtime and 7GB RAM on the CI runner.
**Scale/Scope**: Analysis for N up to 10^7, generating approximately 600k gaps.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

* **I. Reproducibility**: All dependencies are pinned in `requirements.txt`. Random seeds are explicitly set in the code.
* **II. Verified Accuracy**: All external citations in the spec are verified against their primary sources.
* **III. Data Hygiene**: Generated data is treated as immutable.
* **IV. Single Source of Truth**: All results in the paper will trace back to code and data.
* **V. Versioning Discipline**:  Constitution versioning is enforced.
* **VI. Deterministic Number-Theoretic Sieving**: The linear sieve implementation will be deterministic.
* **VII. Rigorous Statistical Convergence Validation**: KS test p-values and visual QQ-plots will be used to validate convergence.

## Project Structure

### Documentation (this feature)

```text
specs/001-normalized-squarefree-gaps/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
```

### Source Code

```text
src/
├── squarefree.py      # Sieve implementation and gap calculation
├── statistics.py      # Statistical tests (Lilliefors, KS test)
├── visualization.py   # Plot generation
└── main.py            # Orchestrates the entire process
tests/
├── test_squarefree.py
├── test_statistics.py
└── contract/
    └── gap_dataset_schema.yaml
```

**Structure Decision**: A modular structure with separate files for sieve implementation, statistical tests, and visualization promotes code clarity and testability.

## Complexity Tracking

N/A (Constitution check passed)
