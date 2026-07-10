# Implementation Plan: Exploring the Impact of Data Imputation Methods on Causal Inference

**Branch**: `001-data-imputation-mnar-impact` | **Date**: 2026-07-10 | **Spec**: `specs/001-data-imputation-mnar-impact/spec.md`
**Input**: Feature specification from `specs/001-data-imputation-mnar-impact/spec.md`

## Summary

This feature implements a simulation study to quantify the bias introduced by standard imputation methods (Mean, KNN, MICE) when applied to data with Missing Not At Random (MNAR) mechanisms. The system generates synthetic Structural Causal Models (SCMs) with known ground-truth Average Treatment Effects (ATE), injects missingness based on unobserved outcomes, applies imputation, and estimates causal effects using IPW and PSM. The plan addresses every FR and SC, ensuring computational feasibility on CPU-only GitHub Actions runners while maintaining strict reproducibility and statistical rigor.

**Experimental Design**: The study performs **200 replications per beta level** across **5 beta levels** (0.0, 0.2, 0.5, 0.8, 1.0), resulting in **1,000 total simulation runs**. This design ensures sufficient statistical power for the Friedman test and sensitivity analysis (SC-003 refers to the 200 replications per level required for stability).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `causalgraphicalmodels` (or custom SCM generator), `fancyimpute` (MICE), `matplotlib`, `seaborn`, `pytest`  
**Storage**: Local filesystem (`data/` for synthetic artifacts, `data/processed/` for results)  
**Testing**: `pytest` with parameterized tests for simulation runs  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Computational Research / Simulation Study  
**Performance Goals**: Complete 1,000 simulation runs (200 per beta) + sensitivity analysis within 4 hours on 2 CPU cores, 7GB RAM.  
**Constraints**: No GPU usage; no 8-bit/4-bit quantization; strict memory limits (<7GB RAM); no external dataset dependencies (synthetic only).  
**Scale/Scope**: A sufficient number of replications per beta level, 5 beta levels, 3 imputation methods, 2 estimators.

**Agents & Tools**:
- **Advancement-Evaluator Agent**: Manages project state transitions. Updates `state/projects/PROJ-047-exploring-the-impact-of-data-imputation-.yaml` `updated_at` and `artifact_hashes` on artifact changes.
- **Reference-Validator Agent**: Validates citations at three points: (1) on artifact write, (2) before Advancement-Evaluator review, (3) as a blocking gate on `research_review` → `research_accepted`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/simulation.py`. `requirements.txt` pins versions. Synthetic data generation is deterministic given seed. |
| **II. Verified Accuracy** | **PASS** | No external dataset URLs are cited for the core analysis (synthetic data). Any references to literature (e.g., MICE papers) will be validated by the **Reference-Validator Agent** at three specific points: (1) on artifact write, (2) before Advancement-Evaluator review, and (3) as a blocking gate on `research_review` → `research_accepted`, as mandated by the Constitution's Verified Accuracy Gate. |
| **III. Data Hygiene** | **PASS** | Synthetic data generated is checksummed. No modification of raw synthetic files; intermediate results written to new files with hashes. |
| **IV. Single Source of Truth** | **PASS** | All bias metrics and plots in `paper/` will be derived directly from `data/results/simulation_summary.csv`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts in `data/` and `code/` will carry content hashes. The **Advancement-Evaluator Agent** updates `state/projects/PROJ-047-exploring-the-impact-of-data-imputation-.yaml` `updated_at` and `artifact_hashes` map whenever any file under `data/` or `code/` changes, ensuring the state file reflects the current project state. |
| **VI. Synthetic Ground Truth Integrity** | **PASS** | `code/simulation.py` explicitly encodes `tau_true` and `beta` (MNAR parameter). Bias is calculated as `|estimate - tau_true|`. |
| **VII. Causal Estimation Robustness** | **PASS** | Both IPW and PSM are implemented. Interaction effects between imputation and estimator are logged and flagged if bias diverges significantly. |

## Project Structure

### Documentation (this feature)

```text
specs/001-data-imputation-mnar-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── synthetic_data.schema.yaml
│   ├── imputation_result.schema.yaml
│   └── causal_estimate.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── simulation/
│   ├── __init__.py
│   ├── scm_generator.py      # Generates SCM with known ATE
│   ├── missingness.py        # Injects MNAR missingness (tunes alpha for fixed rate)
│   └── config.py             # Hyperparameters (beta sweep, N, seeds)
├── analysis/
│   ├── __init__.py
│   ├── imputation.py         # Mean, KNN, MICE wrappers
│   ├── causal_estimation.py  # IPW and PSM wrappers
│   └── metrics.py            # Bias, RMSE, Coverage, Statistical tests (Friedman/Nemenyi)
├── main.py                   # Orchestration script
├── requirements.txt          # Pinned dependencies
└── tests/
    ├── test_scm_generator.py
    ├── test_missingness.py
    └── test_metrics.py

data/
├── raw/                      # Generated synthetic datasets (checksummed)
├── processed/                # Imputed datasets, causal estimates
└── results/                  # Aggregated bias tables, plots

state/
└── projects/
    └── PROJ-047-exploring-the-impact-of-data-imputation-.yaml  # Managed by Advancement-Evaluator

docs/
└── paper/                    # Draft paper with figures
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`simulation`, `analysis`) is chosen to keep the project lightweight and runnable on CI. No separate frontend/backend or mobile layers are needed for a pure simulation study.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Two Estimators (IPW & PSM)** | Required by FR-004 and Constitution Principle VII to distinguish imputation error from estimator error. | Using only one estimator (e.g., PSM) would conflate imputation bias with estimator bias, failing to isolate the impact of missingness handling. |
| **MNAR Parameter Sweep** | Required by FR-007 and SC-005 to identify failure thresholds. | A single beta value would not reveal the monotonic trend or the specific point where standard methods fail. |
| **Statistical Normality Check** | **REMOVED**. The plan now mandates the **Friedman test** by default for all bias comparisons to avoid 'test of assumptions' bias. | Relying on a Shapiro-Wilk test to choose between ANOVA and Friedman introduces bias and is statistically unsound for this design. The Friedman test is robust to non-normality and is the standard for repeated-measures simulation studies. |
| **Replication Count** | **200 replications per beta level** ([deferred] total runs) are required to stabilize bias estimates and ensure power for the Friedman test. | A total of 200 runs (40 per level) would be underpowered to detect significant differences in bias across methods (SC-003). |

## Methodology Highlights

### 1. Synthetic Data Generation (FR-001, US-1)
*   **Model**: Structural Causal Model (SCM) with binary treatment $T$, continuous outcome $Y$, and confounders $X$.
*   **Ground Truth**: The ATE ($\tau_{true}$) is explicitly set (e.g., 0.5) during generation.
*   **MNAR Mechanism**: Missingness $M$ is generated via logistic regression: $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$.
    *   $\beta$ controls the strength of MNAR.
 * **$\alpha$ is tuned dynamically** for each $\beta$ to maintain a **fixed missingness rate** (e.g., [deferred]), isolating the effect of $\beta$ from the volume of missing data.
    *   $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$ for sensitivity analysis.
*   **Verification**: All runs are included regardless of the Spearman correlation between $M$ and unobserved $Y$. **No arbitrary threshold (e.g., $\rho > 0.5$) is used to discard runs.** The acceptance criteria in the spec (US-1) regarding $\rho > 0.5$ serves as a verification of the *mechanism generation* (ensuring the code works) but is NOT applied as a filter to the final dataset for sensitivity analysis. This ensures the full spectrum of MNAR strength is captured, including subtle effects.
*   **Bias Definition**: Bias is calculated as $|\hat{\tau}_{imp} - \tau_{true}|$, where $\tau_{true}$ is the **known generative parameter**, not an empirical estimate from observed data. This avoids tautological confusion about identifiability under MNAR. The observed data under MNAR is inherently biased; the study measures how much the imputation methods fail to recover the *generative parameter*.

### 2. Imputation Pipeline (FR-003, US-2)
*   **Methods**:
    *   **Mean**: Simple mean imputation (baseline).
    *   **KNN**: k-Nearest Neighbors ($k=5$) using Euclidean distance.
    *   **MICE**: Multivariate Imputation by Chained Equations (using `IterativeImputer` in scikit-learn with `RandomForestRegressor` or `BayesianRidge`).
*   **Constraint**: All methods run on CPU. No GPU acceleration.

### 3. Causal Estimation (FR-004, US-2)
*   **IPW**: Inverse Probability Weighting using propensity scores estimated via logistic regression on **imputed data**.
*   **PSM**: Propensity Score Matching (1:1 nearest neighbor matching) on **imputed data**.
*   **Handling MNAR Bias in Propensity Scores**: The plan explicitly acknowledges that under MNAR, the imputation introduces bias into the propensity scores (since $Y$ influences $M$, and $M$ influences the imputed $Y$, which influences $T$ estimation if $T$ is correlated with $Y$). This bias is an expected component of the total error being measured. No attempt is made to restrict to complete cases, as that would defeat the purpose of testing imputation methods. The study measures the total bias (imputation + estimation) relative to the generative parameter.

### 4. Bias Quantification & Statistical Testing (FR-005, FR-006, US-3)
*   **Metrics**:
    *   Absolute Bias: $|\hat{\tau} - \tau_{true}|$
    *   RMSE: $\sqrt{\frac{1}{n}\sum(\hat{\tau}_i - \tau_{true})^2}$
    *   Coverage Rate: Proportion of 95% CIs containing $\tau_{true}$.
*   **Statistical Tests**:
    *   **Default**: **Friedman test** for comparing bias across 3 methods (Mean, KNN, MICE) within each beta level. The Shapiro-Wilk test has been removed to avoid 'test of assumptions' bias.
    *   **Post-hoc**: **Nemenyi test** for pairwise comparisons if Friedman test is significant ($p < 0.05$).
    *   **Robustness**: Bootstrap CIs for median differences.
*   **Sensitivity Analysis**: Spearman rank correlation ($\rho$) between $\beta$ and mean absolute bias. Expect $\rho > 0.9$.

## Compute Feasibility

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
*   **Strategy**:
    *   Data generation and imputation are vectorized (numpy/pandas).
    *   MICE uses `IterativeImputer` with a limited number of iterations and a lightweight estimator (Ridge).
    *   Causal estimation uses `statsmodels` (IPW) and `causalinference` or custom PSM (efficient numpy implementation).
 * **Runtime**: [deferred] runs total. Estimated time per run: on the order of seconds (CPU). Total: several hours.
    *   **Memory**: $N=1000$ datasets are small (~1MB). Multiple runs fit easily in 7GB RAM.
    *   **No GPU**: All libraries (scikit-learn, statsmodels) default to CPU.

## Decision Rationale

*   **Why Synthetic?**: Real MNAR datasets do not have known ground truth. Without known $\tau_{true}$, bias cannot be calculated.
*   **Why IPW & PSM?**: To isolate imputation error from estimator error (Constitution Principle VII).
*   **Why Friedman/Nemenyi?**: To rigorously test if differences in bias are statistically significant, accounting for the repeated-measures nature of the simulation (same seed, different methods) without relying on normality assumptions.
*   **Why 200 Replications per Level?**: To ensure statistical power for the Friedman test and to stabilize the bias estimates for the sensitivity analysis.
*   **Why Dynamic $\alpha$?**: To isolate the effect of the MNAR mechanism ($\beta$) from the effect of missingness volume.