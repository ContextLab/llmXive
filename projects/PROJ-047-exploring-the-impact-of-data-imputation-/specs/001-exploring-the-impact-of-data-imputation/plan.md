# Implementation Plan: Exploring the Impact of Data Imputation Methods on Causal Inference

**Branch**: `001-data-imputation-mnar-impact` | **Date**: 2026-07-10 | **Spec**: `specs/001-data-imputation-mnar-impact/spec.md`
**Input**: Feature specification from `specs/001-data-imputation-mnar-impact/spec.md`

## Summary

This project implements a simulation study to quantify the bias introduced when standard imputation methods (Mean, KNN, MICE) are applied to data with Missing Not At Random (MNAR) mechanisms. The system generates synthetic Structural Causal Models (SCM) with a known ground-truth Average Treatment Effect (ATE) and explicitly parameterized MNAR missingness dependent on the unobserved outcome. It then applies the imputation strategies, estimates the ATE using Inverse Probability Weighting (IPW) and Propensity Score Matching (PSM), and calculates bias, RMSE, and confidence interval coverage. The plan strictly adheres to CPU-only constraints for GitHub Actions free-tier runners. 

**Key Methodological Revisions**:
1.  **MICE**: Implements Rubin's Rules for combining multiple imputations to ensure valid standard errors and confidence intervals.
2.  **Statistical Analysis**: Replaces the flawed Shapiro-Wilk decision tree with a Linear Mixed-Effects Model (LMM) as the primary analysis method, which is robust to non-normality in simulation studies.
3.  **MNAR Tuning**: Includes a binary search procedure to tune the intercept alpha, ensuring a constant target missingness rate across all beta values.
4.  **IPW Stability**: Includes weight trimming (extreme percentiles) to handle extreme weights.
5.  **Coverage Analysis**: Uses a Generalized Linear Model (GLM) with a binomial family for coverage vs. beta analysis.
6.  **Trend Verification**: Removes the impossible p-value requirement for n=5 points; reports correlation and direction descriptively.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `statsmodels`, `dowhy` (CPU backend), `numpy`, `pandas`, `scipy`, `matplotlib`, `seaborn`, `linearmodels` (for LMM).  
**Storage**: Local filesystem (`data/` for artifacts, `code/` for scripts). No external database.  
**Testing**: `pytest` with `cov` for coverage; unit tests for ground truth regeneration; integration tests for pipeline execution.  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU, ~7 GB RAM, no GPU).  
**Project Type**: Computational research / Simulation study.  
**Performance Goals**: Full simulation (200 runs) completes within 4 hours; single run < 1 minute.  
**Constraints**: No GPU, no 8-bit quantization, no large LLM inference. Data subsets must fit < 7 GB RAM.  
**Scale/Scope**: 200 simulation runs, sample size N=1000 per run, 5 MNAR parameter sweeps.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. `requirements.txt` pins exact versions. CI runs `pytest` to verify deterministic regeneration. |
| **II. Verified Accuracy** | **PASS** | No external dataset citations used for the core simulation (synthetic data generated). All methodological citations (e.g., Rubin's rules) will be validated against primary sources. |
| **III. Data Hygiene** | **PASS** | `data/` files checksummed in state YAML. No in-place modification; all transformations produce new files (e.g., `data/raw/synth_seed_123.csv` -> `data/processed/imputed_mean_seed_123.csv`). |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in the paper trace to `data/results/simulation_summary.csv`. No hand-typed numbers. **Canonical Schema**: `contracts/simulation_summary.schema.yaml`. |
| **V. Versioning Discipline** | **PASS** | Artifacts hashed on write. State YAML updated on any code/data change. |
| **VI. Synthetic Ground Truth Integrity** | **PASS** | `code/simulate.py` contains `regenerate_ground_truth(seed, params)` function. **Task T029b** ensures the aggregated `simulation_summary.csv` includes `true_ate` and `beta_mnar` columns for every run. |
| **VII. Causal Estimation Robustness** | **PASS** | Bias metrics reported separately for IPW and PSM. **Task T029c** flags interaction effects if the relative bias difference between IPW and PSM exceeds 10%. |

## Project Structure

### Documentation (this feature)

```text
specs/001-data-imputation-mnar-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── simulation_summary.schema.yaml  # SSoT for aggregated results
│   └── synthetic_dataset.schema.yaml   # SSoT for generated data
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── simulate.py          # Synthetic data generation, MNAR injection (with alpha tuning), ground truth logic
├── impute.py            # Mean, KNN, MICE (5 imputations) implementations (CPU-only)
├── estimate.py          # IPW (with weight trimming), PSM implementations
├── analyze.py           # LMM, GLM for coverage, bias calc, trend verification
├── visualize.py         # Plot generation (bias_vs_beta, coverage_vs_beta, etc.)
├── main.py              # Orchestrator: loops over seeds and beta values (parallelized)
├── tests/
│   ├── test_simulate.py
│   ├── test_impute.py
│   └── test_analyze.py
└── requirements.txt

data/
├── raw/                 # Generated synthetic datasets (seeded)
├── processed/           # Imputed datasets
└── results/             # Aggregated CSVs, JSONs, plots, verification files
```

**Structure Decision**: Single project structure chosen for tight coupling of simulation, estimation, and analysis. All scripts reside in `code/` to ensure reproducibility and single-source-of-traceability.

**Schema Consistency**: 
- `contracts/simulation_summary.schema.yaml` is the **Single Source of Truth** for `data/results/simulation_summary.csv`.
- `contracts/synthetic_dataset.schema.yaml` is the **Single Source of Truth** for `data/raw/*.csv`.
- Duplicate schema files (`causal-estimate.schema.yaml`, `synthetic-dataset.schema.yaml`, etc.) have been removed to resolve conflicts.

## Complexity Tracking

No violations detected. The complexity is managed by:
1.  **Synthetic Data**: Avoids external data ingestion bottlenecks.
2.  **CPU-Only**: Strict library selection ensures runner feasibility.
3.  **Modular Analysis**: Separation of imputation, estimation, and statistical testing allows isolated debugging.
4.  **Parallelization**: Task T001b ensures runtime constraints are met.

## Phase 2 Tasks (Implementation)

### Phase 2.1: Core Infrastructure & Data Generation
- **T001**: Initialize repository structure, `requirements.txt`, and CI configuration.
- **T001b**: Implement parallelization (multiprocessing) in `main.py` to ensure 200 runs complete within 4 hours.
- **T002**: Implement `simulate.py` to generate synthetic SCM data with binary treatment, continuous outcome, and confounders.
- **T002b**: Implement binary search logic in `simulate.py` to tune parameter `alpha` such that the missingness rate is [deferred] for all `beta` values.
- **T002c**: Ensure `simulate.py` outputs `true_ate` and `beta_mnar` columns in the generated CSV files.
- **T002d**: Add unit tests verifying `regenerate_ground_truth` returns expected values for a given seed.

### Phase 2.2: Imputation & Estimation
- **T010**: Implement Mean and KNN imputation in `impute.py`.
- **T010b**: Implement MICE imputation in `impute.py` generating **multiple imputations** per run.
- **T010c**: Implement **Rubin's Rules** logic in `analyze.py` to combine MICE results (point estimates, standard errors, CIs).
- **T014**: Implement IPW and PSM estimation in `estimate.py`.
- **T014b**: Ensure IPW model $P(T=1|X)$ uses only observed confounders $X$.
- **T014c**: Implement weight trimming (truncate at extreme percentiles) for IPW to ensure stability.

### Phase 2.3: Analysis & Aggregation
- **T028**: Implement **Linear Mixed-Effects Model (LMM)** in `analyze.py` to compare bias across imputation methods (replaces ANOVA/Friedman tree).
- **T029**: Implement main simulation loop in `main.py` to orchestrate generation, imputation, estimation, and aggregation.
- **T029b**: Ensure `simulation_summary.csv` includes `true_ate`, `beta_mnar`, `bias`, `rmse`, `coverage` for every run.
- **T029c**: Implement logic to flag interaction effects if $|Bias_{IPW} - Bias_{PSM}| / Bias_{IPW} > 0.10$.
- **T030**: Implement trend verification in `analyze.py` to calculate Spearman correlation for bias vs. beta. **Output**: `trend_verification.json` (rho, direction, monotonicity_observed). **Note**: p-value not required for n=5.
- **T035**: Implement GLM (binomial family) in `analyze.py` to model coverage vs. beta. **Output**: `coverage_slope_verification.json` (slope, p-value, negative_slope_confirmed).

### Phase 2.4: Visualization & Reporting
- **T042**: Generate `bias_vs_beta.png`, `coverage_vs_beta.png`, `bias_distributions.png` from `data/results/simulation_summary.csv`.
- **T042b**: Validate CSV schema before plotting (ensure required columns exist).
