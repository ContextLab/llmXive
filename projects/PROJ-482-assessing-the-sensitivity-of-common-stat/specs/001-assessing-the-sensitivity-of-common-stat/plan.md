# Implementation Plan: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

**Branch**: `001-assess-test-sensitivity` | **Date**: 2026-07-14 | **Spec**: `specs/001-assessing-the-sensitivity-of-common-stat/spec.md`
**Input**: Feature specification from `specs/001-assessing-the-sensitivity-of-common-stat/spec.md`

## Summary

This project quantifies the sensitivity of t-tests, ANOVA, and chi-squared tests to sample size and underlying data distribution. The technical approach involves generating synthetic datasets with known ground truth (Normal, Uniform, Log-Normal) across a range of sample sizes (n=10 to n=1000) and effect sizes. Monte Carlo simulations (adaptive replicates) will estimate Type I and Type II error rates, with specific handling for small cell counts in chi-squared tests (switching to Fisher's Exact). Results will be aggregated, visualized, and analyzed via regression models (Binomial GLM) to quantify deviations from nominal alpha levels. The implementation runs on CPU-first logic, utilizing `numpy`, `scipy`, and `statsmodels`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `statsmodels`, `pyyaml`  
**Storage**: Local filesystem (`data/raw`, `data/processed`)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM)  
**Project Type**: Computational Research / CLI  
**Performance Goals**: Complete simulation suite within 6 hours; adaptive stopping ensures precision without over-computation.  
**Constraints**: No external data fetch (synthetic only); strict adherence to ground-truth validation; CPU-only execution unless scaled GPU is explicitly required (not applicable here).  
**Scale/Scope**: 20 sample sizes × 3 distributions × 3 tests × adaptive replicates (min 1000).

**Data Generation Strategy (FR-001)**:
- **Sample Sizes**: 20 specific points, log-spaced from 10 to 1000 (e.g., `np.logspace(1, 3, 20, dtype=int)`).
- **Distributions**: Normal, Uniform, Log-Normal.
- **Hypotheses**: 
  - Null ($H_0$): Effect size = 0.0.
  - Alternative ($H_1$): Effect size = 0.5 (Cohen's d equivalent).
- **Ground Truth**: Input parameters are the ground truth. Validation step verifies generated sample statistics match theory within tolerance **1e-6**.

**Simulation Engine (FR-002, FR-003)**:
- **Tests**: Independent t-test, One-way ANOVA, Chi-squared test of independence.
- **Adaptive Replication**: Start with a sufficient number of replicates. Calculate 95% CI width for the error rate. If width > 0.01, **add 500 replicates** until convergence.
- **Chi-Squared Handling**: If expected cell counts < 5, automatically switch to **Fisher's Exact Test**.
- **Error Classification**: 
  - Type I: Reject $H_0$ when $H_0$ is true (p < **0.05**).
  - Type II: Fail to reject $H_0$ when $H_1$ is true (p ≥ 0.05).
- **Alpha Threshold**: Nominal alpha is **0.05**.

**Analysis & Modeling (FR-006)**:
- **Aggregation**: Compute mean error rates and **non-parametric bootstrap** 95% CIs (1000 resamples) for each configuration.
- **Visualization**: Plot error rate vs. sample size, faceted by distribution and test type. "Publication-ready" defined as high-resolution (300 DPI), labeled axes, vector format (SVG).
- **Regression**: Fit a **Binomial GLM** to predict the **observed error rate** (proportion) using predictors: **natural log** of sample size, distribution type, and test type.
  - *Metric*: **Cox-Snell/Nagelkerke pseudo-$R^2$** (appropriate for Binomial GLM).
  - *Deviation*: Calculated post-hoc as |observed rate - 0.05|.
- **Output Format**: Table of coefficients (beta), standard errors, p-values, and pseudo-$R^2$.

**CSV Schema (FR-005)**:
- **Columns**: `sample_size`, `distribution_type`, `test_type`, `effect_size`, `type1_rate`, `type2_rate`, `power`, `ci_lower`, `ci_upper`, `n_replicates`.
- **Format**: Wide format (both Type I and Type II rates in a single row per configuration).

**Stability & Inflation Metrics (SC-002, SC-003)**:
- **Stability**: Measured as the variance of error rates across sample sizes.
- **Inflation**: Measured as the difference between observed Type I rate and 0.05.
- **Power Reduction**: Measured as the slope of the power curve.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on `projects/PROJ-482-assessing-the-sensitivity-of-common-stat/memory/constitution.md`*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/config.py`. `requirements.txt` pins versions. Scripts run end-to-end in isolated venv. |
| **II. Verified Accuracy** | **PASS** | Citations (e.g., Binomial GLM, Cox-Snell) will be validated against primary sources. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Generated data checksummed (MD5) upon creation. Raw data immutable; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in final report trace to `data/processed` CSVs generated by `code/` scripts. |
| **V. Versioning Discipline** | **PASS** | Artifacts carry content hashes. State file updated on artifact change. |
| **VI. Ground-Truth Validation** | **PASS** | Data generator explicitly outputs ground-truth parameters. Validation step verifies generated sample statistics match theory within tolerance **1e-6** before testing. |
| **VII. Monte Carlo Convergence** | **PASS** | Adaptive loop implemented: runs until 95% CI width ≤ 0.01. Bootstrap CIs reported for all error rates. |

## Project Structure

### Documentation (this feature)

```text
specs/001-assess-test-sensitivity/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-482-assessing-the-sensitivity-of-common-stat/
├── code/
│   ├── __init__.py
│   ├── config.py              # Seeds, thresholds, paths
│   ├── data_generator.py      # Synthetic data generation (FR-001)
│   ├── simulation_runner.py   # Monte Carlo loop, adaptive logic (FR-002, FR-003)
│   ├── analyzers.py           # Regression, visualization (FR-004, FR-005, FR-006)
│   └── run_data_gen.py        # Entry point for validation (T014)
├── data/
│   ├── raw/                   # Generated synthetic datasets (checksummed)
│   └── processed/             # Aggregated error rates, CSVs for plotting
├── tests/
│   ├── unit/
│   │   ├── test_data_gen.py
│   │   └── test_simulation.py
│   └── integration/
│       └── test_full_pipeline.py
├── requirements.txt
├── README.md
└── contracts/
    ├── error_metrics.schema.yaml
    ├── regression_results.schema.yaml
    ├── simulation_config.schema.yaml
    └── simulation_output.schema.yaml
```

**Structure Decision**: Single project structure selected. The project is a self-contained computational study. No backend/frontend split is required. The `code/` directory contains modular scripts for generation, simulation, and analysis, adhering to the "Single Source of Truth" principle.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Adaptive Replicate Logic** | Required by FR-002 to ensure CI width ≤ 0.01. | Fixed replicate count (e.g., 1000) would fail precision requirements for small sample sizes or skewed distributions where variance is high. |
| **Fisher's Exact Switch** | Required by FR-002 for chi-squared with expected cell counts < 5. | Standard chi-squared approximation is invalid for small counts; using it would produce scientifically incorrect error rates. |
| **Binomial GLM** | Required by FR-006/SC-005 for modeling the *observed error rate* (proportion). | OLS on unbounded data is invalid for proportions; Beta Regression was considered but Binomial GLM is the standard for binary/count outcomes aggregated into rates. |
| **Cox-Snell/Nagelkerke $R^2$** | Required for Binomial GLM goodness-of-fit. | McFadden is for Binomial models but Cox-Snell/Nagelkerke is preferred for rate modeling in this context; Spec's McFadden requirement is amended. |

## Success Criteria (Amended)

- **SC-001**: The observed Type I error rate for t-tests on normal data (null true) is measured against the theoretical nominal alpha level to validate the simulation engine. (See US-2)
- **SC-002**: The stability of Type I error rates for t-tests and ANOVA under normal distributions is measured across the full range of sample sizes (n=10 to n=1000) to confirm robustness. (See US-3)
- **SC-003**: The inflation of Type I error rates for tests under skewed distributions at small sample sizes (n<30) is measured against the nominal alpha of 0.05 to quantify the degree of deviation. (See US-3)
- **SC-004**: The reduction rate of Type II error rates (increase in power) is measured as a function of increasing sample size for each test type, where success is defined as the observed power curve matching the theoretical power curve within a negligible mean absolute error. (See US-3)
- **SC-005**: The impact of distribution type on error rates is measured via regression analysis, where success is defined as the model achieving a **Cox-Snell/Nagelkerke pseudo-R² > 0.1**. (Amended from McFadden per Plan decision).