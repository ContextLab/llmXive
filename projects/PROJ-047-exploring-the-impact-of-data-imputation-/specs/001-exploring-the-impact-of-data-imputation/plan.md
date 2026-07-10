# Implementation Plan: Exploring the Impact of Data Imputation Methods on Causal Inference

**Branch**: `001-data-imputation-mnar-impact` | **Date**: 2026-07-10 | **Spec**: `specs/001-data-imputation-mnar-impact/spec.md`
**Input**: Feature specification from `/specs/001-data-imputation-mnar-impact/spec.md`

## Summary

This project implements a simulation study to quantify the bias introduced by standard imputation methods (Mean, KNN, MICE) when applied to data with Missing Not At Random (MNAR) mechanisms. The core technical approach involves generating synthetic Structural Causal Models (SCMs) with known ground-truth Average Treatment Effects (ATE), injecting missingness into the outcome variable based on unobserved values, and comparing the resulting causal estimates (via IPW and PSM) against the known truth. The study explicitly sweeps the MNAR strength parameter to identify failure thresholds, adhering to strict CPU-only constraints for execution on GitHub Actions free-tier runners.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn>=1.3.0`, `statsmodels>=0.14.0`, `numpy>=1.24.0`, `pandas>=2.0.0`, `scipy>=1.11.0`, `causalnex>=0.12.0` (or `dowhy` if CPU-tractable, otherwise custom SCM), `fancyimpute` (or `sklearn.impute` for MICE via `IterativeImputer`), `linearmodels` (for Mixed-Effects).  
**Storage**: Local file system (`data/synthetic/`), JSON/CSV/Parquet outputs.  
**Testing**: `pytest` with `pytest-cov`.  
**Target Platform**: Linux (GitHub Actions free-tier: A modest number of CPUs and sufficient RAM).  
**Project Type**: Computational Research / Simulation Engine.  
**Performance Goals**: Complete 200 simulation runs + sensitivity analysis within 4 hours (SC-003).  
**Constraints**: Strictly CPU-only; no GPU; memory usage < 6GB; no external API calls for data generation (synthetic only).  
**Scale/Scope**: Multiple simulation replications across varying MNAR strength levels ($\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Action Required / Note |
|-----------|--------|------------------------|
| **I. Reproducibility** | PASS | Random seeds will be pinned in `code/`. Synthetic generation is deterministic given seed. |
| **II. Verified Accuracy** | PASS | No external citations for data generation; synthetic ground truth is self-contained. Citations for methods (MICE, IPW) will be validated against primary sources. |
| **III. Data Hygiene** | PASS | Synthetic data files will be checksummed upon generation. No PII (synthetic only). |
| **IV. Single Source of Truth** | PASS | All bias metrics and plots will be generated programmatically from `data/synthetic/` results. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Artifacts (scripts, data) will carry content hashes. State file updated on changes. |
| **VI. Synthetic Ground Truth Integrity** | PASS | `code/simulation/scm_generator.py` will explicitly encode $\tau_{true}$ and $\beta`. A dedicated `regenerate_ground_truth(seed, beta)` function (Task T006) ensures mathematical verifiability. |
| **VII. Causal Estimation Robustness Verification** | PASS | Both IPW and PSM will be run for every imputation method. Divergence (diff > 0.1 or non-overlapping CIs) will be flagged in `ImputationResult` (Task T015). |

## Project Structure

### Documentation (this feature)

```text
specs/001-data-imputation-mnar-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── synthetic-dataset.schema.yaml
    └── causal-estimate.schema.yaml
```
*Note: Duplicate schema files (`synthetic_data.schema.yaml`, `synthetic_dataset.schema.yaml`, `causal_estimate.schema.yaml`) have been removed to establish `synthetic-dataset.schema.yaml` and `causal-estimate.schema.yaml` as the canonical SSoT.*

### Source Code (repository root)

```text
code/
├── simulation/
│   ├── __init__.py
│   ├── scm_generator.py       # Generates SCM with known ATE
│   ├── missingness.py         # Injects MNAR missingness
│   └── config.py              # Simulation parameters (beta sweep, seeds)
├── analysis/
│   ├── __init__.py
│   ├── imputation.py          # Mean, KNN, MICE wrappers
│   ├── causal_estimation.py   # IPW and PSM logic
│   └── metrics.py             # Bias, RMSE, Coverage, Statistical tests, Divergence Flagging
├── main.py                    # Orchestration: loops beta, runs sims, aggregates
├── tests/
│   ├── test_scm.py
│   ├── test_missingness.py
│   └── test_metrics.py
├── requirements.txt           # Pinned dependencies
└── README.md                  # Execution instructions
```

**Structure Decision**: Single-project structure chosen for tight coupling of simulation and analysis. No frontend/backend split. Modular separation of `simulation` (data gen) and `analysis` (processing) ensures testability and aligns with the "Foundational" vs "Orchestration" dependency correction from previous concerns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The project adheres to a single-repo, modular Python structure. | N/A |

## Implementation Phases & Tasks

### Phase 0: Setup & Verification
- **T001**: Initialize repository, `requirements.txt`, and CI workflow (CPU-only).
- **T002**: Set up directory structure (`data/`, `code/`, `specs/`).
- **T003**: Implement basic logging and configuration loading (`config.py`).

### Phase 1: Foundational Simulation Engine (Per Spec FR-001, FR-002)
- **T004**: Implement `scm_generator.py` to generate synthetic data (Binary T, Continuous Y, Confounders X) with fixed $\tau_{true}$.
- **T005**: Implement `missingness.py` to inject MNAR missingness using logistic model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$.
- **T006**: **Implement `regenerate_ground_truth(seed, beta)` function** in `scm_generator.py`. This function must deterministically regenerate the exact $\tau_{true}$ and $\beta$ parameters for any given seed, ensuring Constitution Principle VI compliance. Add unit tests verifying `regenerate_ground_truth` returns the expected values.
- **T007**: Implement collinearity check (VIF) in `scm_generator.py` to flag runs with VIF > 10.

### Phase 2: Imputation & Estimation Logic (Per Spec FR-003, FR-004)
- **T008**: Implement `imputation.py` wrappers for Mean, KNN ($k=5$), and MICE (using `IterativeImputer` with CPU settings).
- **T009**: Implement `causal_estimation.py` for IPW and PSM. Ensure both estimators return `estimate`, `se`, and `ci_bounds`.
- **T010**: Implement standard error correction logic:
    - For MICE: Implement Rubin's Rules to combine estimates across imputations.
    - For Mean/KNN: Implement bootstrapping of the full imputation+estimation pipeline to derive robust SEs and CIs.

### Phase 3: Orchestration & Analysis (Per Spec FR-005, FR-006, FR-007, FR-008)
- **T011**: Create `main.py` skeleton with CLI entry point (`--beta-sweep`, `--replications`).
- **T012**: Implement the main simulation loop:
    1. Load config (beta values, seeds).
    2. Call `T004` (Generate Data).
    3. Call `T005` (Inject Missingness).
    4. Call `T006` (Verify Ground Truth).
    5. Call `T008` (Impute).
    6. Call `T009` (Estimate).
    7. Call `T010` (Calculate SE/CI).
- **T013**: Implement `metrics.py` to calculate:
    - Absolute Bias ($|\hat{\tau} - \tau_{true}|$).
    - Squared Error (per run).
    - Coverage Rate (% CI).
    - **Divergence Flag**: Calculate $|\hat{\tau}_{IPW} - \hat{\tau}_{PSM}|$. Flag if difference > 0.1 OR if 95% CIs do not overlap. Store flag in `ImputationResult`.
- **T014**: Implement statistical testing in `metrics.py`:
    - Fit Linear Mixed-Effects Model (LMM) with `run_id` as random effect to test for bias differences across methods (replacing ANOVA/Friedman).
    - Calculate Spearman correlation for monotonicity trends.
- **T015**: Implement aggregation logic to compute RMSE (aggregated from `squared_error` across runs) and generate summary plots.
- **T016**: Write results to `data/synthetic/` with checksums.

### Phase 4: Validation & Reporting
- **T017**: Run full sensitivity analysis (multiple runs x multiple betas).
- **T018**: Verify all outputs against `contracts/` schemas.
- **T019**: Generate final summary report and plots.
