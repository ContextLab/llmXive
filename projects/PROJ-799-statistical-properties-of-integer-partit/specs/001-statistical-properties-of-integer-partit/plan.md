# Implementation Plan: Statistical Properties of Integer Partitions Into Distinct Prime Summands

**Branch**: `001-statistical-properties-of-integer-partitions-into-distinct-prime-summands` | **Date**: 2026-07-10 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/spec.md`

## Summary

This project investigates the asymptotic growth rate of the partition function $p_{\mathcal{P}}(n)$ (partitions of $n$ into distinct primes) and quantifies its deviation from the predictions of Meinardus' theorem. The approach involves: (1) computing exact values of $p_{\mathcal{P}}(n)$ up to $n=50,000$ using a memory-optimized dynamic programming algorithm; (2) generating theoretical asymptotic baselines $Q_{as}(n)$ derived from the distinct-partition variant of Meinardus' theorem (using $\prod (1+q^p)$) with a verified constant derived from the Prime Zeta function; (3) modeling the log-residuals $R(n)$ against prime density features (strictly excluding terms used in the leading-order $Q_{as}(n)$ to avoid circularity) using linear regression and GAMs; and (4) validating model robustness via cross-validation and visual inspection. The implementation strictly adheres to a constrained RAM limit (≤ 6.5 GB) and Runtime constraint

The research question is [insert research question verbatim], the method is [insert method verbatim], and the references are [insert references verbatim]. The implementation will adhere to a bounded runtime constraint. of the GitHub Actions free tier.

## Technical Context

**Language/Version**: Python 3  
**Primary Dependencies**: `numpy`, `scipy`, `statsmodels`, `pandas`, `matplotlib`, `pytest`  
**Storage**: Local files (CSV, JSON, PNG) under `data/` and `output/`  
**Testing**: `pytest` with unit tests for DP correctness and regression validation  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational mathematics / data analysis  
**Performance Goals**: Complete pipeline within 6 hours; peak memory ≤ 6.5 GB  
**Constraints**: No GPU required; strict adherence to `n_max=50,000` for feasibility; exact integer arithmetic for partition counts  
**Scale/Scope**: A substantial dataset; regression models; k-fold cross-validation  

> The maximum $n$ is capped at a sufficiently large value to ensure statistical robustness. to ensure the DP array fits within memory while providing sufficient data for regression analysis. This value is derived from the spec's acceptance scenarios and compute constraints.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: All random seeds (for cross-validation splits) will be pinned in `code/`. The prime generation and DP logic are deterministic. External data (primes) is generated on-the-fly, ensuring identical results on fresh runs.
- **II. Verified Accuracy**: Citations to Meinardus' theorem and partition asymptotics will be verified against primary sources (Meinardus 1954, Andrews 1998) in the Research phase *before* code implementation. The plan explicitly defers the final verification of the formula derivation until the research phase is complete, ensuring Principle II compliance without premature claims.
- **III. Data Hygiene**: All generated data files (`data/raw/partitions.csv`, `data/processed/features.csv`) will be checksummed in `state/`. No in-place modifications; derivations produce new files.
- **IV. Single Source of Truth**: All statistics in the final report will trace to `data/processed/features.csv` and `code/regression_analysis.py`. The `output/regression_summary.json` is the derived artifact.
- **V. Versioning**: Artifacts (code, data, plans) will carry content hashes. `state/` will track `updated_at` timestamps.
- **VI. Finite-Regime Error Term Precision**: The plan explicitly computes and reports $R(n)$ for a finite range of $n$.. The distinction between the theoretical error term ($O(...)$) and the empirical residual ($R(n)$) is explicitly maintained; the regression models the empirical residual as an estimator for the theoretical error.
- **VII. Density-Dependent Correlation Rigor**: The regression model includes sine/cosine terms and higher-order density corrections to account for the complex combinatorial nature of $p_{\mathcal{P}}(n)$, avoiding simplistic linear assumptions. Predictors are orthogonal to the leading-order terms of $Q_{as}(n)$ to prevent tautology.

## Project Structure

### Documentation (this feature)

```text
specs/001-statistical-properties-of-integer-partitions-into-distinct-prime-summands/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-799-statistical-properties-of-integer-partit/
├── code/
│   ├── __init__.py
│   ├── generate_partitions.py      # DP algorithm for p_P(n)
│   ├── asymptotic_baseline.py      # Meinardus' theorem implementation
│   ├── feature_engineering.py      # Density features & residuals
│   ├── regression_analysis.py      # Linear regression & GAM
│   ├── validation.py               # Cross-validation & plotting
│   ├── .flake8                     # Linting config
│   ├── .black                      # Formatting config
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   └── partitions.csv          # n, p_P(n), Q_as(n)
│   └── processed/
│       └── features.csv            # n, R(n), density features
├── tests/
│   ├── __init__.py
│   ├── test_generate_partitions.py
│   ├── test_asymptotic_baseline.py
│   ├── test_feature_engineering.py
│   ├── test_regression_analysis.py
│   └── test_features_non_null.py   # Validates non-null features
├── docs/
│   └── README.md
└── state/
    └── projects/PROJ-799-statistical-properties-of-integer-partit.yaml
```

**Configuration Files**:
- `code/.flake8`:
  ```ini
  [flake8]
  max-line-length = 120
  exclude = .git,__pycache__,venv
  ignore = E203,W503
  ```
- `code/.black`:
  ```ini
  [tool.black]
  line-length = 120
  target-version = ['py311']
  ```

**Structure Decision**: Single-project structure chosen for simplicity and direct data flow. All scripts are modular and testable. The `code/` directory contains all logic, `data/` stores intermediate and final datasets, and `tests/` ensures correctness.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project is streamlined to meet compute constraints. | N/A |

## Phases

### Phase 0: Research & Feasibility (Current)
- **Goal**: Validate dataset availability (primes), *verify* the asymptotic formula against primary sources, and design regression features.
- **Deliverables**: `research.md` (validated), `data-model.md`, `quickstart.md`, `contracts/`.
- **Actions**:
  1. Confirm prime generation is feasible (sieve up to 50,000).
  2. *Verify* the derivation of $Q_{as}(n)$ for distinct prime partitions against Meinardus (1954) and Andrews (1998).
  3. Define density features (excluding those in $Q_{as}(n)$) and regression model structure.
  4. Verify memory usage of DP algorithm with arbitrary-precision integers.

### Phase 1: Implementation Design
- **Goal**: Finalize code structure, API contracts, and test strategy.
- **Deliverables**: `tasks.md`, refined `contracts/`.
- **Actions**:
  1. Define function signatures for `generate_partitions`, `asymptotic_baseline`, etc.
  2. Specify CSV schemas and error handling.
  3. Plan test cases for edge cases ($n < 5$, $Q_{as}(n) \le 0$).

### Phase 2: Implementation
- **Goal**: Write and test all code.
- **Deliverables**: Executable scripts, passing tests.
- **Actions**:
  1. Implement DP algorithm with memory optimization (arbitrary-precision integers).
  2. Implement asymptotic baseline (verified formula).
  3. Implement feature engineering and regression (with autocorrelation correction).
  4. Run cross-validation and generate plots.

### Phase 3: Validation & Reporting
- **Goal**: Verify results, generate visualizations, and compile report.
- **Deliverables**: Final plots, regression summary, paper draft.
- **Actions**:
  1. Run full pipeline.
  2. Validate against SC-001 to SC-006.
  3. Generate final visualizations.

## Addressing Unresolved Concerns

- **T013 (Validation Logic)**: The plan explicitly includes validation logic in `generate_partitions.py` (the file confirmed to exist by T011) to skip $n$ where $p_{\mathcal{P}}(n) = 0$ or $Q_{as}(n) \le 0$. This logic will be implemented in the existing `generate_partitions.py` file. The test suite will include `test_features_non_null` to validate that the resulting `features.csv` contains no null residuals.
- **T001 (Directory Tree)**: The `projects/PROJ-799-statistical-properties-of-integer-partit/` hierarchy is defined above, with concrete paths for `code/`, `data/`, `tests/`, etc.
- **T003a/b (Linting/Formatting)**: The plan includes `code/.flake8` and `code/.black` configuration files in the directory structure (content provided above).
- **T031 (Generating Function Comment)**: `generate_partitions.py` will include a comment documenting $\prod_{p\in\mathbb{P}}(1+q^p)$ and distinguishing it from the unrestricted case.
- **T032 (n_max Parameter)**: Both `generate_partitions.py` and `asymptotic_baseline.py` will accept `n_max` as a configurable parameter, logged at runtime.
- **T016b (features.csv & test)**: The pipeline will generate `data/processed/features.csv` with all required columns. The test suite will include `test_features_non_null` to validate non-null values.

## Compute Feasibility

- **CPU-First**: All methods (DP, regression, cross-validation) are CPU-tractable.
- **Memory Analysis**: The DP array for $n=50,000$ stores [deferred] arbitrary-precision integers (Python `int`). While the *count* of partitions $p_{\mathcal{P}}(n)$ grows super-exponentially, the memory footprint for a large volume of such integers is estimated at a substantial magnitude (well within 7 GB RAM), significantly higher than the incorrect estimate for 64-bit integers. A 1D array is used to minimize overhead.
- **No GPU Needed**: No transformer or diffusion models are used. The problem is purely combinatorial and statistical.
- **Runtime**: Estimated time: DP (~ hour), Asymptotic ([deferred]), Regression ([deferred]), Cross-validation ([deferred]). Total << 6 hours.

## Data Availability

- **Primes**: Generated on-the-fly using Sieve of Eratosthenes (no external download needed).
- **Reference Values**: Pre-computed values for a representative range of $n$ will be embedded in `tests/` for validation.
- **No Gated Data**: All data is self-generated or open-source.

## Statistical Rigor

- **Multiple Comparisons**: Both Bonferroni and Benjamini-Hochberg corrections will be applied to p-values for density predictors (SC-005).
- **Power Justification**: $n=50,000$ provides ample data for regression; power analysis is secondary to model specification and autocorrelation handling.
- **Autocorrelation**: The residuals $R(n)$ are expected to be autocorrelated. The plan explicitly includes Newey-West standard errors (or HAC estimators) to correct p-values and ensure validity of significance tests (SC-001).
- **Causal Claims**: None made; analysis is associational (residuals vs. density).
- **Collinearity**: $\pi(n)$ and $1/(\ln n)^2$ are correlated; variance inflation factor (VIF) will be checked, and features may be regularized.
- **Measurement Validity**: Primes are exact; partition counts are exact via DP.
- **Circularity Avoidance**: Predictors in the regression model will be chosen to be orthogonal to the leading-order terms of $Q_{as}(n)$ to ensure the residual analysis is not tautological. Specifically, $Q_{as}(n)$ uses the leading-order term derived from the Prime Zeta function (constant $A$), while predictors capture higher-order fluctuations (e.g., oscillatory terms, squared log terms) distinct from the leading density term.
- **Null Model**: An intercept-only (null) model will be fitted and compared to the full model (FR-008).
- **Theoretical vs. Empirical**: The plan distinguishes between the theoretical error term (asymptotic remainder) and the empirical residual $R(n)$ (the quantity being modeled).

## Next Steps

1. Finalize `research.md` with detailed asymptotic derivation and feature rationale (verified against sources).
2. Define `data-model.md` with precise schemas.
3. Create `quickstart.md` for local execution.
4. Draft `contracts/` for data and output validation.
