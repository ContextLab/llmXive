# Implementation Plan: Evaluating the Impact of Data Scaling on Robustness of Statistical Tests

**Branch**: `001-evaluating-data-scaling-robustness` | **Date**: 2026-06-25 | **Spec**: `specs/001-evaluating-data-scaling-robustness/spec.md`
**Input**: Feature specification from `/specs/001-evaluating-data-scaling-robustness/spec.md`

## Summary

This project implements a simulation engine to evaluate how three data scaling methods (Standardization, Min-Max, Robust) affect the *numerical stability* and *invariance* of parametric statistical tests (t-test, ANOVA). The core hypothesis is that while linear scaling transformations should theoretically leave t-test and ANOVA p-values invariant, numerical precision errors or implementation-specific edge cases (e.g., zero variance, extreme outliers) may introduce deviations. The system will generate synthetic data with known ground truth (null and alternative hypotheses) across various distributional properties (normal, skewed, heteroscedastic). It will run a sufficient number of iterations per configuration to calculate empirical Type I error rates and statistical power, comparing them against the nominal alpha level. Finally, it will validate findings on a curated set of public datasets by measuring the consistency of p-values. The entire pipeline is designed to execute within a bounded time window on a 2-core CPU GitHub Actions runner (FR-007, SC-003).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `pandas`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`  
**Storage**: Local file system (`data/` for raw/scaled data, `results/` for aggregates)  
**Testing**: `pytest`  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, 7GB RAM)  
**Project Type**: Computational Research / Simulation Engine  
**Performance Goals**: Complete [deferred]+ iterations per configuration within 6 hours total runtime (FR-007, SC-003).
**Constraints**: No GPU usage; memory footprint < 7GB; no external network calls except for initial dataset download (cached for CI).  
**Scale/Scope**: [deferred] iterations per config; available verified real-world datasets (HAR, Shopper); multiple scaling methods; Multiple test types (t-test, ANOVA).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **COMPLIANT** | All random seeds will be pinned in `code/simulation/generator.py`. Dependencies pinned in `requirements.txt`. External datasets will be downloaded once and checksummed. |
| **II. Verified Accuracy** | **COMPLIANT** | Citations in `research.md` will be restricted to the verified dataset list provided in the spec. No invented URLs. |
| **III. Data Hygiene** | **COMPLIANT** | Raw data stored in `data/raw/` (checksummed). Scaled data stored in `data/scaled/{method}/`. No in-place modifications. |
| **IV. Single Source of Truth** | **COMPLIANT** | All figures and stats in the final report will be generated programmatically from `results/` CSVs/Parquets. |
| **V. Versioning Discipline** | **COMPLIANT** | The Advancement-Evaluator Agent will trigger an update to `state/projects/PROJ-541-...yaml` `updated_at` timestamp immediately upon successful generation of any artifact in `results/` or `data/`. Content hashes will be recorded in the state file. |
| **VI. Simulation Fidelity** | **COMPLIANT** | Generator will explicitly create skewness/heteroscedasticity as per spec. A large number of iterations per batch. Seeds recorded. |
| **VII. Scaling Method Transparency** | **COMPLIANT** | Dedicated functions for Standardization, Min-Max, and Robust scaling. Logs will record method parameters. Pre-scaled data retained. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-data-scaling-robustness/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
code/
├── simulation/
│   ├── __init__.py
│   ├── generator.py       # FR-001: Synthetic data generation
│   └── config.py          # SimulationConfig entity
├── preprocessing/
│   ├── __init__.py
│   ├── scaling.py         # FR-002: Scaling algorithms
│   └── ingestion.py       # FR-008: Real-world dataset loading
├── analysis/
│   ├── __init__.py
│   ├── tests.py           # FR-003: Statistical tests (t-test, ANOVA)
│   └── metrics.py         # FR-005: Error rate/power calculation
├── visualization/
│   ├── __init__.py
│   └── plots.py           # FR-006: Error rate plots
├── main.py                # Orchestration script
└── requirements.txt       # Pinned dependencies

data/
├── raw/                   # Downloaded datasets (checksummed)
├── synthetic/             # Generated data per iteration (or aggregated)
└── scaled/                # Scaled versions (standardized, minmax, robust)

results/
├── simulation_results.csv # Aggregated p-values and test stats
├── real_world_results.csv # Real-world validation results
└── figures/               # Generated plots
```

**Structure Decision**: Single project structure with modular packages (`simulation`, `preprocessing`, `analysis`, `visualization`) to ensure separation of concerns and testability. This aligns with the "Single project" option and fits the computational research nature of the feature.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **ANOVA on Aggregated Error Rates** | Required to statistically test if scaling method predicts deviation from nominal error rates for synthetic data. | Mixed-effects model is inappropriate for synthetic data where 'dataset' is not a random variable. |
| **[deferred]+ Iterations (FR-004)** | Necessary to achieve tight confidence intervals (±0.005) for Type I error rates at α=0.05. | 1,000 iterations would yield wide CIs (±0.015), making it impossible to distinguish robust methods from non-robust ones. |
| **Robust Scaling Implementation** | Must handle zero IQR and outliers without NaNs (Edge Case 2). | Standard `sklearn` RobustScaler might fail on constant groups; custom wrapper with zero-IQR handling is required. |
| **Numerical Stability Focus** | The study explicitly tests for floating-point deviations from theoretical invariance, not statistical alteration. | Assuming scaling alters p-values statistically is a tautological error; the focus must be on numerical precision. |
