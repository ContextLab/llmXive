# Implementation Plan: Exploring the Distribution of Smooth Numbers in Short Intervals

**Branch**: `001-exploring-the-distribution-of-smooth-numbers` | **Date**: 2026-07-13 | **Spec**: `specs/001-exploring-the-distribution-of-smooth-numbers/spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-distribution-of-smooth-numbers/spec.md`

## Summary

This project implements a computational pipeline to empirically measure the density of $y$-smooth numbers within short intervals $[x, x+h]$ for $x \le 10^9$. The approach involves three sequential phases: (1) generating a deterministic prime list up to $10^9$ via a segmented sieve; (2) enumerating integers in randomized short intervals to classify smoothness via trial division; and (3) performing statistical regression and goodness-of-fit tests against the Dickman function.

**Critical Methodological Revision**: The analysis no longer fits a raw power law to density vs. interval length. Instead, it computes the **deviation ratio** $R = \rho_{observed} / \rho_{Dickman}(u)$ for each interval, where $u = \ln x / \ln y$. The regression tests if this ratio scales as $R \propto h^\beta$. This isolates finite-scale deviations from the global asymptotic baseline, addressing the tautology risk and construct validity concerns. The grid uses **fixed interval lengths** $h$ (e.g., $10^3$ to $10^6$) rather than $h=x^\alpha$ to ensure balanced sampling and avoid truncation bias.

The implementation strictly adheres to the project's constitutional requirement for deterministic verification, reproducibility on a CPU-constrained CI runner, and statistical rigor (p < 0.01, KS tests).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy` (vectorized math), `scipy` (statistics), `matplotlib` (visualization), `pytest` (testing).  
**New Component**: `code/dickman.py` - Custom numerical implementation of the Dickman function $\rho(u)$ via integration of the delay-differential equation.  
**Storage**: Local file system (CSV/JSON artifacts). No database.  
**Testing**: `pytest` with unit tests for sieve logic, Dickman implementation, and the full pipeline on a small subset.  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, 7 GB RAM).  
**Project Type**: Computational research CLI / Scripting library.  
**Performance Goals**: Total runtime < 6 hours; Peak RAM < 7 GB.  
**Constraints**: Must run without GPU; must handle $x=10^9$ without memory overflow; must use deterministic algorithms.  
**Scale/Scope**: Primes up to a large integer magnitude (~tens of millions of primes); [deferred] interval samples across the parameter grid (fixed $h$).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on constitution file*

1.  **Reproducibility (NON-NEGOTIABLE)**: The plan mandates pinned `requirements.txt` and fixed random seeds in the enumeration script. All artifacts (primes, density data, model fits) are written to `data/` with checksums. **Status: Compliant.**
2.  **Verified Accuracy**: The plan implements the Dickman function $\rho(u)$ via a custom, documented numerical solver in `code/dickman.py` (based on standard analytic number theory definitions, e.g., Tenenbaum). No external URL citations are fabricated; the mathematical definition is treated as a known constant implemented in code. **Status: Compliant.**
3.  **Data Hygiene**: Raw prime lists and density measurements will be stored as immutable CSVs. Derivations (regression results, deviation ratios) will be new files. **Status: Compliant.**
4.  **Single Source of Truth**: All figures and statistics in the final output will be generated directly from the `data/` artifacts by the analysis script, preventing hand-typed numbers. **Status: Compliant.**
5.  **Versioning Discipline**: The plan includes a content-hash update mechanism in the `state/` YAML for every new data artifact. **Status: Compliant.**
6.  **Deterministic Number-Theoretic Verification**: The plan explicitly rejects probabilistic primality tests (Miller-Rabin) in favor of trial division against the pre-computed prime list, ensuring exact smoothness classification. **Status: Compliant.**
7.  **Statistical Rigor**: The plan explicitly commits to the **Kolmogorov-Smirnov (KS) test** (α = 0.05) for distribution comparison and **Weighted Least Squares (WLS)** regression for power-law fitting of the deviation ratio. Variance is estimated via multiple random starting positions. Conclusions require **p < 0.01** to be considered statistically significant, as mandated by Principle VII. **Status: Compliant.**

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-distribution-of-smooth-numbers/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-549-exploring-the-distribution-of-smooth-num/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── sieve.py                 # Segmented sieve implementation (FR-001)
│   ├── dickman.py               # Custom numerical implementation of ρ(u)
│   ├── smoothness.py            # Factorization and density logic (FR-002, FR-003)
│   ├── analysis.py              # Regression (WLS) and statistical tests (FR-004, FR-005)
│   ├── viz.py                   # Plotting logic (FR-006)
│   └── main.py                  # Orchestration script
├── data/
│   ├── primes_1e9.csv           # Pre-computed prime list
│   ├── density_measurements.csv # Aggregated interval data (includes u, ratio)
│   └── model_fits.json          # Regression results
├── tests/
│   ├── test_sieve.py
│   ├── test_dickman.py
│   ├── test_smoothness.py
│   └── test_analysis.py
└── state/
    └── projects/PROJ-549-exploring-the-distribution-of-smooth-num.yaml
```

**Structure Decision**: A single `code/` directory with modular scripts is selected over a complex CLI framework. This minimizes overhead and aligns with the "scripting library" nature of the project, ensuring easy execution on the GitHub Actions runner.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The plan adheres strictly to the spec and constraints, with methodological refinements to address panel concerns. | N/A |