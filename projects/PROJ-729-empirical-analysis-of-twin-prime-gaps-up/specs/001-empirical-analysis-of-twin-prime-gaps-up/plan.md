# Implementation Plan: Empirical Analysis of Twin Prime Gaps up to 10⁹

**Branch**: `001-twin-prime-gaps` | **Date**: 2026-06-25 | **Spec**: `specs/001-empirical-analysis-of-twin-prime-gaps-up/spec.md`

## Summary

This project implements an empirical statistical analysis of twin prime gaps within a computationally feasible range. The primary requirement is to generate the complete list of twin primes in this range, compute normalized gaps ($\Delta_n / \log p_n$), and test the hypothesis that these gaps follow an exponential distribution (Cramér model) using a **Parametric Bootstrap** Kolmogorov–Smirnov (KS) test and **two-sample** distribution comparisons for local windows. Additionally, the project will analyze localized deviations near powers of two. The technical approach relies on the `primesieve` C++ library (via Python bindings) for efficient prime generation, `numpy` and `pandas` for data manipulation, and `scipy`/`matplotlib` for statistical testing and visualization. All computations are constrained to run on a GitHub Actions free-tier runner (CPU, 7 GB RAM, ≤45 mins).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `primesieve>=10.0`, `numpy>=1.26`, `pandas>=2.1`, `scipy>=1.11`, `matplotlib>=3.8`, `pyyaml`, `jsonschema`  
**Storage**: Local CSV files (`data/raw/twin_primes.csv`), JSON results (`data/results/stats.json`), PNG figures (`data/figures/`)  
**Testing**: `pytest` (unit tests for gap calculation logic, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions Ubuntu 22.04)  
**Project Type**: Computational Research / CLI  
**Performance Goals**: Complete full pipeline (generation + analysis) within 45 minutes; peak RAM < 2 GiB.  
**Constraints**: No GPU; no external network calls for data (generation is local); deterministic execution (seeded RNGs).  
**Scale/Scope**: [deferred] twin prime pairs up to $10^9$ (theoretical expectation).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Note |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | All scripts will use pinned `requirements.txt`. Random seeds (if any) will be set explicitly. Data generation is deterministic based on the range limit. |
| **II. Verified Accuracy** | **COMPLIANT** | **FR-009** mandates the execution of the Reference-Validator Agent (or simulated equivalent) to verify all citations (Cramér, Hardy-Littlewood) against primary sources before report generation. |
| **III. Data Hygiene** | **COMPLIANT** | Raw generated CSV will be checksummed. No in-place modification; derived statistics saved to new files. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures and stats in the final report will be generated programmatically from the `data/` artifacts. |
| **V. Versioning Discipline** | **COMPLIANT** | **FR-008** mandates the computation of SHA-256 hashes for all artifacts and the update of the project state YAML. The `hash_artifacts.py` script implements this mechanism. |
| **VI. Computational Determinism & Resource Constraints** | **COMPLIANT** | `primesieve` is memory-efficient (sieve of Eratosthenes with wheel factorization). The dataset (~k rows) fits easily in 2 GiB RAM. Pipeline designed for ≤45 mins. |
| **VII. Statistical Validation Integrity** | **COMPLIANT** | KS tests (Parametric Bootstrap) and two-sample distribution tests will use `scipy.stats` with documented parameters. Results saved to JSON. |

## Project Structure

### Documentation (this feature)

```text
specs/001-twin-prime-gaps/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-729-empirical-analysis-of-twin-prime-gaps-up/
├── code/
│   ├── __init__.py
│   ├── generate_primes.py      # PR-001, FR-001, FR-002
│   ├── validate_schema.py      # FR-002b (Schema Validation)
│   ├── analyze_gaps.py         # FR-003 (Parametric Bootstrap KS)
│   ├── analyze_local.py        # FR-005 (Two-sample KS/AD)
│   ├── hash_artifacts.py       # FR-008 (Hashing & State Update)
│   ├── verify_citations.py     # FR-009 (Citation Verification)
│   └── report.py               # FR-006
├── data/
│   ├── raw/
│   │   └── twin_primes.csv     # Generated output
│   ├── results/
│   │   └── stats.json          # KS and T-test results
│   └── figures/
│       ├── qq_plot.png         # QQ-plot
│       └── local_deviation.png # Bar chart
├── tests/
│   ├── unit/
│   │   └── test_gap_calc.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single-project structure chosen for simplicity. The project is a linear pipeline (Generate → Validate → Analyze → Hash → Report) without complex service boundaries.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Use of `primesieve`** | Required for performance to generate primes up to $10^9$ within 45 mins on CPU. | Pure Python sieve or `sympy` would likely exceed the 45-minute time limit due to interpreted overhead. |
| **Separate analysis scripts** | Separation of concerns ensures `generate_primes.py` can be re-run if the range changes without re-running statistical tests. | Monolithic script would be harder to debug and less reusable for future range extensions. |
| **Parametric Bootstrap** | Required to correct the bias in KS test p-values caused by self-normalization of the data. | Standard KS test tables are invalid when parameters are estimated from the same data. |
| **Two-sample tests for local windows** | Required to avoid circular logic where global normalization forces local means to ~1.0. | One-sample t-tests against 1.0 are tautological for self-normalized data. |

## Phase Execution Plan

### Phase 0: Data Generation & Validation
1.  **Generate Primes**: Run `code/generate_primes.py` to produce `data/raw/twin_primes.csv`.
2.  **Schema Validation**: Run `code/validate_schema.py` to ensure `twin_primes.csv` matches `contracts/twin_prime_schema.schema.yaml`. **Blocking Gate**: If validation fails, the pipeline halts.
3.  **Hashing**: Run `code/hash_artifacts.py` to compute SHA-256 hashes for the CSV and update the project state YAML (Constitution Principle V).

### Phase 1: Statistical Analysis
1.  **Global Analysis**: Run `code/analyze_gaps.py`.
    -   Perform Parametric Bootstrap KS test with a sufficient number of iterations. to compare empirical distribution against Exponential(1).
    -   Generate QQ-plot.
2.  **Local Analysis**: Run `code/analyze_local.py`.
    -   For each window $[^k - 10^4, 2^k + 10^4]$, perform a two-sample KS test (or Anderson-Darling) comparing the window distribution against the global empirical distribution.
    -   Generate bar chart of p-values or effect sizes.
3.  **Hashing**: Run `code/hash_artifacts.py` to hash the results JSON and update state.

### Phase 2: Reporting & Verification
1.  **Citation Verification**: Run `code/verify_citations.py` to validate all citations (Cramér, Hardy-Littlewood) against primary sources (Constitution Principle II). **Blocking Gate**: If verification fails, the report cannot be generated.
2.  **Report Generation**: Run `code/report.py` to compile the final Markdown report.
3.  **Final Hashing**: Run `code/hash_artifacts.py` to hash the report and update state.

## Risk Assessment

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| `primesieve` installation failure on CI | High | Fallback to a pure Python segmented sieve (slower) or explicit error handling with installation instructions. |
| Memory overflow during generation | Low | `primesieve` is memory-efficient; monitor peak usage. |
| Statistical power issues | Low | Sample size (large) is large; Bootstrap KS test will be highly sensitive. |
| Bootstrap computation time | Medium | A high number of iterations on a large dataset may take several minutes; well within 45-minute limit. |
| Schema validation failure | High | Explicit error codes and messages to guide data regeneration. |
