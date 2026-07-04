# Implementation Plan: Robustness of Confidence Intervals to Differential Privacy Noise

**Branch**: `001-robustness-ci-dp-noise` | **Date**: 2026-06-16 | **Spec**: `specs/001-robustness-of-confidence-intervals-to-di/spec.md`
**Input**: Feature specification from `/specs/001-robustness-of-confidence-intervals-to-di/spec.md`

## Summary

This project investigates how Differential Privacy (DP) noise, controlled by the privacy budget $\epsilon$, degrades the frequentist coverage probability of 95% confidence intervals (CIs) for means and linear regression coefficients. The technical approach involves a two-level simulation:
1.  **Outer Loop (Monte Carlo)**: Generate $N_{sim}=1,000$ independent noisy samples for each condition (dataset $\times$ $\epsilon$ $\times$ noise type).
2.  **Inner Loop (Bootstrap)**: For each noisy sample, perform $B=1,000$ bootstrap resamples to construct a single 95% CI.
3.  **Coverage Estimation**: Calculate the proportion of the Outer Loop CIs that contain the fixed ground-truth parameter.
4.  **Adjustments**: Apply bias-correction and variance-inflation methods to the point estimates and standard errors.
5.  **Analysis**: Use a Generalized Linear Model (GLM) with a binomial link to test the effects of $\epsilon$ and noise type on coverage.
6.  **Sensitivity**: Sweep decision thresholds for "acceptable coverage" to ensure robustness.

The implementation must run entirely on CPU within 6 hours and 7 GB RAM.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn` (all CPU-compatible, no CUDA).  
**Storage**: Local filesystem (`data/` for raw/synthetic data, `artifacts/` for results); no external database.  
**Testing**: `pytest` (unit tests for DP noise calibration, CI construction, and GLM setup).  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7 GB RAM).  
**Project Type**: Computational research / Simulation pipeline.  
**Performance Goals**: Total runtime $\le$ a practical threshold suitable for standard workloads; memory usage $\le$ 7 GB.  
**Constraints**: No GPU; no 8-bit/4-bit quantization; strict adherence to synthetic population generation.

> **Single Source of Truth (SSoT)**: Per Constitution Principle IV, all coverage rates, GLM results, and threshold sweep metrics are derived exclusively from `artifacts/coverage_results.csv` and `artifacts/sensitivity_analysis.csv`.

**Computational Feasibility Check**:
*   **Conditions**: 3 datasets $\times$ 5 $\epsilon$ values $\times$ 2 noise types = 30 combinations.
* **Outer Loop**: [deferred] independent samples per condition = total noisy samples.
*   **Inner Loop**: 1,000 bootstrap resamples per sample = total bootstrap draws.
*   **Operations**: Vectorized numpy operations for noise and resampling. 30M draws is feasible in <6 hours on 2 cores if optimized (e.g., batched resampling).
*   **Memory**: Process one condition at a time. Do not store all 30M draws; store only the resulting CI bounds (a representative set of rows) in `coverage_results.csv`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence/Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | Plan mandates pinned random seeds in `code/`, synthetic population generation via deterministic code, and isolated `requirements.txt`. |
| **II. Verified Accuracy** | PASS | Citations for DP theory will be validated. No fabricated dataset URLs; ground truth is synthetic. |
| **III. Data Hygiene** | PASS | Synthetic data generation scripts versioned. No PII involved. Checksums recorded. |
| **IV. Single Source of Truth** | PASS | All results trace to `artifacts/coverage_results.csv`. Explicitly declared in Technical Context. |
| **V. Versioning Discipline** | PASS | **Workflow**: Post-run script `code/utils/update_state.py` computes content hashes of `artifacts/` and updates `state/projects/PROJ-710-...yaml` `updated_at` and `artifact_hashes`. |
| **VI. Privacy-Utility Tradeoff** | PASS | Every result row includes $\epsilon$, noise_type, and coverage rate. |
| **VII. Simulation Convergence** | PASS | **Workflow**: `code/analysis/convergence_check.py` runs simulation with 3 different seeds. If standard error of coverage across seeds > 0.5%, it triggers a warning and requires increased $N_{sim}$. |

## Project Structure

### Documentation (this feature)

```text
specs/001-robustness-of-confidence-intervals-to-di/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Defined in Planning Phase, Implemented in Phase 1
│   ├── dataset.schema.yaml
│   ├── coverage_result.schema.yaml
│   └── glm_result.schema.yaml
└── tasks.md             # Phase 2 output
```

**Structure Decision**: Contracts are **defined** in this Planning Phase to provide the schema and validation rules that the Implementer Agent must follow in Phase 1. The `contracts/` directory contains the *specification* of the data formats. The *implementation* (scripts that generate data adhering to these schemas) occurs in Phase 1. This resolves the logical gap: the plan exercises the *definitions* to guide the *implementation*.

### Source Code (repository root)

```text
projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/
├── __init__.py
├── config.py            # Hyperparameters, seeds, paths
├── data/
│   ├── __init__.py
│   ├── synthetic_pop.py # Generates N=1M population with known params
│   └── dp_noise.py      # Laplace/Gaussian noise injection
├── analysis/
│   ├── __init__.py
│   ├── ci_builder.py    # Bootstrap CI construction (Inner Loop)
│   ├── adjustments.py   # Bias-correction & variance-inflation
│   ├── glm_analysis.py  # GLM with binomial link
│   └── convergence_check.py # Validates stability across seeds
├── main.py              # Orchestration script (Outer Loop)
├── utils/
│   └── update_state.py  # Post-run hash & state update
└── tests/
    ├── test_dp_noise.py
    └── test_ci_builder.py
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Synthetic Population (N=1M)** | FR-002/FR-008 require a "known parameter" ground truth independent of sample realization. | Using real datasets as population proxy introduces unknown true parameters. |
| **Two-Level Simulation** | Requires estimating coverage (Outer Loop) and constructing CIs (Inner Loop). | Single-loop bootstrap on one sample yields CI width, not coverage probability. |
| **GLM with Binomial Link** | Coverage is a binary outcome; standard ANOVA assumptions fail. | Linear regression on proportions can predict outside [0,1]. |
| **Threshold Sensitivity** | FR-006 requires robustness check on "acceptable" thresholds. | A single threshold (e.g., 95%) is arbitrary; sweeping ensures conclusions are not threshold-dependent. |

## Implementation Phases

### Phase 0: Data Generation & Ground Truth
1.  Generate synthetic populations (N=1M) for Adult, Iris, Wine distributions.
2.  Calculate and fix **Ground Truth** parameters (Mean, Regression Coefficients) for each population.
3.  Store Ground Truth in `config.py` (not derived from samples).

### Phase 1: Simulation Pipeline (Outer Loop)
1.  For each (dataset, $\epsilon$, noise_type):
    *   Draw $N_{sim}=1,000$ independent samples from the population.
    *   Add calibrated DP noise to each sample.
    *   For each noisy sample:
        *   Run Inner Loop: $B=1,000$ bootstrap resamples.
        *   Construct confidence intervals (Percentile method).
        *   Apply Bias/Variance adjustments (if applicable).
        *   Check if CI covers the **Fixed Ground Truth**.
        *   Record result in `artifacts/coverage_results.csv`.

### Phase 2: Statistical Analysis (GLM)
1.  Load `artifacts/coverage_results.csv`.
2.  Fit GLM: `covered ~ epsilon + noise_type + epsilon:noise_type`.
3.  Extract p-values and coefficients.
4.  Save to `artifacts/glm_summary.json`.

### Phase 3: Convergence & Sensitivity
1.  **Convergence**: Run the initial phase with multiple different seeds. Compare coverage estimates. If variance > threshold, increase $N_{sim}$.
2.  **Sensitivity**: Sweep coverage thresholds (high, medium, and stringent levels). Count passing cases for each. Save to `artifacts/sensitivity_analysis.csv`.

### Phase 4: Versioning & Validation
1.  Run `code/utils/update_state.py` to hash artifacts and update `state/` YAML.
2.  Validate `artifacts/` against `contracts/` schemas.