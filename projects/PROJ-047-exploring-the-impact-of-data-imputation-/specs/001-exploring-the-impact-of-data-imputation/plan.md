# Implementation Plan: Exploring the Impact of Data Imputation Methods on Causal Inference

**Branch**: `001-data-imputation-mnar-impact` | **Date**: 2026-07-15 | **Spec**: `specs/001-data-imputation-mnar-impact/spec.md`
**Input**: Feature specification from `/specs/001-data-imputation-mnar-impact/spec.md`

## Summary

This feature implements a simulation study to quantify the bias introduced by standard imputation methods (Mean, KNN, MICE) when applied to data with Missing Not At Random (MNAR) mechanisms. The system generates synthetic Structural Causal Models (SCMs) with known ground-truth Average Treatment Effects (ATE), injects missingness dependent on unobserved outcomes, and compares estimated ATEs against the known truth. The plan strictly adheres to the requirement of CPU-only execution on GitHub Actions free-tier runners, utilizing `scikit-learn`, `statsmodels`, and `sklearn.impute` without GPU acceleration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `pandas`, `scikit-learn`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`, `causalinference` (or custom SCM generator), `pytest`.  
**MICE Implementation**: `sklearn.experimental.enable_iterative_imputer()` with `IterativeImputer` (canonical choice for CPU-only). Fallback: `fancyimpute` only if sklearn unavailable.  
**Storage**: Local filesystem (`data/` for generated CSV/Parquet, `data/results/` for aggregated metrics).  
**Testing**: `pytest` with strict seed pinning for reproducibility.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: Computational research simulation.  
**Performance Goals**: Complete 200 simulation runs + sensitivity analysis within 4 hours.  
**Constraints**: No GPU, no CUDA, no 8-bit/4-bit quantization. Data subset to fit <7GB RAM.  
**Scale/Scope**: Multiple simulation runs, Multiple MNAR parameter steps ($\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$), 3 imputation methods, 2 estimators.  
**Power Analysis**: For N=1000 with expected missingness rate [deferred], effective N ≈ 700. Post-hoc power calculation (Phase 3 Task T033) verifies [deferred] power to detect moderate effect size (Cohen's d) in bias differences between methods. If power < 80%, limitation is explicitly flagged in paper.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification Action |
|-----------|--------|---------------------|
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`. All data generated procedurally; no external static datasets required for the core simulation. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` restricted to verified URLs in the input block. No invented URLs. |
| **III. Data Hygiene** | **PASS** | Generated data stored in `data/` with checksums recorded in state. No in-place modification; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | All figures and stats in the paper will trace to `data/results/simulation_summary.csv` and `data/results/statistical_tests.json`. Schema validation (Task T028.5) ensures CSV completeness before visualization. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes. State file updated on artifact changes. |
| **VI. Synthetic Ground Truth Integrity** | **PASS** | Phase 1 Task T006 implements `regenerate_ground_truth(seed, beta)` function returning (tau_true, alpha, beta). Phase 2 Task T029d stores these parameters in every row of simulation_summary.csv. Post-hoc verification enabled by calling regenerate_ground_truth(seed, beta) and comparing to stored values. Deterministic and mathematically verifiable. |
| **VII. Causal Estimation Robustness** | **PASS** | Phase 3 Task T031 calculates bias divergence metric: \|bias_IPW - bias_PSM\| for each imputation method and beta level. If divergence > 0.1, flagged as interaction effect in data/results/statistical_tests.json with interaction_flag field. |

## Project Structure

### Documentation (this feature)

```text
specs/001-data-imputation-mnar-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── simulation_summary.schema.yaml       # Single Source of Truth
    ├── statistical_test.schema.yaml
    ├── sensitivity_analysis.schema.yaml
    ├── imputation_result.schema.yaml
    └── synthetic_dataset.schema.yaml
```

### Source Code (repository root)

```text
projects/PROJ-047-exploring-the-impact-of-data-imputation-/
├── code/
│   ├── __init__.py
│   ├── synthetic_data.py          # SCM generation, MNAR injection, regenerate_ground_truth
│   ├── imputation.py              # Mean, KNN, MICE implementation (CPU only)
│   ├── causal_estimators.py       # IPW and PSM implementation
│   ├── analysis.py                # Bias calculation, statistical tests (Shapiro/ANOVA/Friedman/Bootstrap)
│   ├── sensitivity.py             # Beta sweep, trend verification (Spearman, Regression)
│   ├── visualization.py           # Plot generation (bias_vs_beta, coverage_vs_beta, distributions)
│   └── run_simulation.py          # Main orchestration loop
├── data/
│   ├── raw/                       # Generated synthetic datasets (per run)
│   ├── results/                   # Aggregated CSVs, JSON stats, plots
│   └── checksums.json             # Artifact hashes
├── tests/
│   ├── unit/
│   │   ├── test_synthetic_data.py
│   │   ├── test_imputation.py
│   │   └── test_estimators.py
│   └── integration/
│       └── test_full_pipeline.py
├── docs/
│   └── paper/                     # Draft figures and text
└── requirements.txt
```

**Structure Decision**: Single `code/` directory for simulation scripts, separated by functional module. `data/` split into `raw` (intermediate) and `results` (final). This supports the "Single Source of Truth" by ensuring results flow through `simulation_summary.csv` (validated by Task T028.5).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Dual Estimators (IPW + PSM)** | Required by Constitution Principle VII to distinguish imputation error from causal identification error. Phase 3 Task T031 flags divergence between them as an interaction effect. | Using only one estimator would conflate the two sources of bias, violating the robustness verification requirement. |
| **Sensitivity Analysis (Beta Sweep)** | Required by FR-007 and SC-005 to identify failure thresholds. Tasks T030 and T035 verify monotonic trends with explicit pass/fail flags. | A single-point analysis cannot demonstrate the monotonic trend or identify where standard methods break down. |
| **Statistical Decision Tree (Shapiro → ANOVA/Friedman → Bootstrap)** | Required by FR-006 to ensure valid inference under unknown distribution shapes. Task T028 integrates all branches into a single coherent workflow. Bootstrap is computed whenever skewness > ±1 as a mandatory robustness check. | Using only ANOVA assumes normality which may not hold for bias distributions; using only Friedman loses power if normality holds. Bootstrap handles skewness. |
| **Oracle Benchmark (Task T036)** | Added to address circularity concern: bias relative to generative parameter is tautological. Oracle benchmark (IPW on complete data) provides independent validation. | Without independent benchmark, cannot distinguish between "imputation failed" vs. "MNAR distorted the parameter." |
| **MNAR Mechanism Validation (Task T010)** | Added to address circularity: verifying M-Y correlation is tautological (mechanism is defined by it). Task T010 uses Kolmogorov-Smirnov test to validate that observed-data distribution diverges from complete-data distribution. | Without independent check, validation merely confirms code executed correctly, not that MNAR mechanism behaves as theorized. |

## Methodology

### 1. Synthetic Data Generation (SCM) — Phase 1 Task T006 + Phase 2 Task T029b

**Model**: Linear Structural Causal Model (SCM).
- $T = \text{Bernoulli}(\text{logit}^{-1}(\gamma X))$
- $Y = \alpha T + \beta X + \epsilon$
- **Ground Truth ATE**: $\alpha$ (explicitly stored via regenerate_ground_truth).

**MNAR Injection** (Phase 2 Task T029b):
- Missingness indicator $M$ generated via logistic model: $P(M=1|Y) = \text{logit}^{-1}(\alpha_{mnar} + \beta_{mnar} Y)$.
- $\beta_{mnar}$ is swept: $\{0.0, 0.2, 0.5, 0.8, 1.0\}$.
- $\beta_{mnar} = 0$ represents MAR/MCAR (baseline).
- $\beta_{mnar} > 0$ represents MNAR (missingness depends on unobserved $Y$).

**Verification** (Phase 1 Task T010):
- Verify MNAR mechanism by comparing observed-data distribution (with missingness) to complete-data distribution using Kolmogorov-Smirnov test.
- If KS test p < 0.05, distributions diverge (MNAR mechanism working).
- If KS test p >= 0.05, distributions similar (MNAR mechanism insufficient).
- This provides independent validation beyond confirming M-Y correlation (which is tautological).

**Ground Truth Regeneration** (Phase 1 Task T006):
- Implement `regenerate_ground_truth(seed, beta) → (tau_true, alpha, beta)` function.
- Deterministic: given seed and beta, always returns same ground truth values.
- Called by Phase 2 Task T029d to store ground truth in every row of simulation_summary.csv.
- Enables post-hoc verification of ground truth integrity (Constitution Principle VI).

### 2. Imputation Strategies — Phase 2 Tasks T017-T019

- **Mean** (Task T017): Replace missing $Y$ with column mean. Bootstrap resampling (Task T019) for robust SEs/CIs.
- **KNN** (Task T018): $k=5$ nearest neighbors (Euclidean distance on $T, X$). Bootstrap resampling for robust SEs/CIs.
- **MICE** (Task T018): `sklearn.experimental.enable_iterative_imputer()` with `IterativeImputer` (default estimator=BayesianRidge, max_iter=10, random_state=seed). Rubin's Rules (Task T019) for combining SEs/CIs across imputations.
- **Constraint**: All run on CPU. No GPU.

### 3. Causal Estimation — Phase 2 Task T020-T025

- **IPW** (Task T024): Inverse Probability Weighting using propensity scores.
- **PSM** (Task T025): Propensity Score Matching (nearest neighbor, caliper=0.05).
- **Output**: Estimated ATE ($\hat{\tau}$) for each (Imputation, Estimator) pair.
- **Divergence Check** (Phase 3 Task T031): Calculate |bias_IPW - bias_PSM|. If > 0.1, flag as interaction effect.

### 4. Bias Quantification & Statistical Testing — Phase 3 Tasks T028-T034

**Bias Calculation** (Phase 2 Task T029d):
- Bias: $|\hat{\tau} - \tau_{true}|$ where $\tau_{true}$ is regenerated via regenerate_ground_truth.
- RMSE: $\sqrt{\frac{1}{N}\sum(\hat{\tau}_i - \tau_{true})^2}$.

**Statistical Test (Task T028)** — Integrated Decision Tree:
1. Compute Shapiro-Wilk test on bias distribution for each beta level.
2. If $p < 0.05$ (non-normal) → **Friedman Test**.
3. If $p \ge 0.05$ (normal) → **Repeated-Measures ANOVA**.
4. **Independently** (always): If skewness > 1 or < -1 → Compute **Bootstrap CIs** (1000 iterations) for difference in medians as robust alternative.
5. Write results to `data/results/statistical_tests.json` with schema matching `contracts/statistical_test.schema.yaml`. Fields: test_type (anova/friedman/bootstrap), p_value, test_statistic, skewness, bootstrap_ci_diff.

**Rationale for Integrated Decision Tree**: 
- Bootstrap is not a fallback for ANOVA failure; it is a mandatory robustness check whenever data is skewed.
- This ensures FR-006's requirement for a robust alternative is always satisfied, not conditionally.
- ANOVA/Friedman provides the primary test (more power if assumptions hold); bootstrap provides robustness check (valid under any distribution).

**Sensitivity Analysis** (Phase 3 Tasks T030, T035):
- **Bias Trend (Task T030)**: Sweep $\beta_{mnar}$. Compute Spearman rank correlation (rho) and p-value for bias vs. beta. Verify rho > 0.9 AND p < 0.05. Write to `data/results/sensitivity_analysis.json` with monotonicity_confirmed flag. If condition fails, set flag to false and log warning.
- **Coverage Trend (Task T035)**: Compute regression slope for coverage rate vs. beta. Verify slope < 0 AND p < 0.05. Write to same JSON with negative_slope_confirmed flag. If condition fails, set flag to false and log warning.
- **Scope Limitation**: This study uses a logistic MNAR mechanism (standard in simulation literature). Non-linear MNAR structures (e.g., quadratic, interaction-based) are outside the initial scope and should be explored in future work. Findings are specific to this linear-logistic interaction and may not generalize to other MNAR forms.

### 5. Computational Feasibility

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
  - Sample size $N=1000$ per run (small enough for RAM).
  - Multiple runs will be conducted (A moderate $\beta$ level).
  - Parallelize runs if possible (using `joblib` with `n_jobs=2`), otherwise sequential.
  - **No GPU**: All libraries (`scikit-learn`, `statsmodels`) used in CPU mode.
  - **Runtime**: Target < 4 hours.
  - **Power Analysis (Task T033)**: Post-hoc power calculation verifies adequate power to detect Cohen's d ≈ 0.5 in bias differences. If power < 80%, limitation is explicitly flagged in paper.

### 6. Research Question Clarification

**What this study measures**: The *failure* of standard imputation methods to recover the *generative parameter* (tau_true) under MNAR. This is empirical (not tautological) because the bias depends on the specific imputation method chosen and the MNAR mechanism's strength.

**What this study does NOT claim**: That standard methods can recover the true causal effect under MNAR (they cannot; the effect is not identifiable from observed data alone).

**Independent Validation (Task T036)**: Compute bias relative to an IPW estimator on complete data (oracle benchmark). If bias relative to the oracle is large, the imputation methods are failing. If bias relative to the oracle is small but bias relative to the generative parameter is large, the MNAR mechanism is simply distorting the parameter (expected behavior, not a failure).

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Synthetic Data** | Real-world data lacks known ATE. Simulation is the only way to quantify bias against "truth" (the generative parameter). |
| **MNAR Mechanism** | Logistic dependency on $Y$ is the standard parametric form for MNAR studies. Linear-logistic interaction is standard; non-linear mechanisms are future work. |
| **IPW + PSM** | Constitution Principle VII requires dual estimation to separate imputation error from identification error. Task T031 flags divergence as interaction effect. |
| **Statistical Decision Tree** | FR-006 mandates robust testing. ANOVA is powerful if normal; Friedman if not. Bootstrap handles skewness. Integrated into single Task T028 to ensure robustness always executed. |
| **CPU-Only** | GitHub Actions free tier has no GPU. Heavy models (e.g., deep learning imputation) are infeasible. |
| **Oracle Benchmark (Task T036)** | Addresses circularity: provides independent validation beyond generative parameter. |
| **MNAR Validation (Task T010)** | Addresses tautology: Kolmogorov-Smirnov test validates mechanism against observable data properties. |
| **Rubin's Rules + Bootstrap** | Standard practice for combining SEs/CIs from multiple imputations (MICE) and resampling (Mean/KNN). Implemented in Tasks T019. |

## Phase Breakdown

### Phase 0: Research & Design (Input)
- Spec review and clarification (already completed).
- This plan document.
- research.md, data-model.md, quickstart.md.

### Phase 1: Setup & Validation (Tasks T001-T010)
- **T001**: Initialize repository structure (code/, data/, tests/, docs/).
- **T002**: Create requirements.txt with pinned versions.
- **T003**: Implement synthetic_data.py with SCM generator.
- **T004**: Implement imputation.py (Mean, KNN, MICE).
- **T005**: Implement causal_estimators.py (IPW, PSM).
- **T006**: Implement regenerate_ground_truth(seed, beta) function. Add unit tests verifying function returns expected values for seed=42, beta=0.5.
- **T007**: Implement analysis.py (bias, RMSE, statistical tests).
- **T008**: Implement sensitivity.py (Spearman, regression).
- **T009**: Run unit tests (pytest tests/unit/).
- **T010**: Implement MNAR validation (Kolmogorov-Smirnov test). Verify observed-data distribution diverges from complete-data distribution for beta > 0.

### Phase 2: Data Generation & Estimation (Tasks T011-T029d)
- **T011-T016**: Implement visualization.py and run_simulation.py orchestration.
- **T017**: Implement Mean imputation + bootstrap for robust SEs/CIs.
- **T018**: Implement KNN imputation + bootstrap for robust SEs/CIs.
- **T019**: Implement MICE imputation + Rubin's Rules for robust SEs/CIs.
- **T020-T023**: Implement IPW and PSM causal estimators with SE/CI calculation.
- **T024**: Test IPW estimator on synthetic data.
- **T025**: Test PSM estimator on synthetic data.
- **T026**: Implement main simulation loop (iterate over runs and beta sweep).
- **T027**: Implement data aggregation logic (write to CSV).
- **T028.5**: Implement schema validation (verify simulation_summary.csv has all required columns before visualization).
- **T029a**: Loop Orchestration: Iterate over 200 runs and beta sweep. Explicit dependencies and error handling.
- **T029b**: Data Generation: Call regenerate_ground_truth(seed, beta) for each run.
- **T029c**: Imputation/Estimation: Apply all 3 imputation methods and 2 estimators.
- **T029d**: CSV Aggregation: Write results to simulation_summary.csv. Store ground_truth_ate, mnar_alpha, mnar_beta for every row.

### Phase 3: Analysis & Validation (Tasks T030-T036)
- **T028**: Implement statistical test decision tree (Shapiro → ANOVA/Friedman → Bootstrap). Write results to data/results/statistical_tests.json with test_type, p_value, test_statistic, skewness, bootstrap_ci_diff.
- **T030**: Implement bias trend analysis. Compute Spearman rho and p-value for bias vs. beta. Verify rho > 0.9 AND p < 0.05. Write to data/results/sensitivity_analysis.json with monotonicity_confirmed flag.
- **T031**: Implement divergence check between IPW and PSM. Calculate |bias_IPW - bias_PSM|. If > 0.1, flag as interaction effect in statistical_tests.json.
- **T032**: Implement power sensitivity analysis (vary number of runs per beta). If power < 80%, flag in paper.
- **T033**: Post-hoc power calculation. Verify [deferred] power for Cohen's d ≈ 0.5 difference in bias.
- **T034**: (REMOVED — bootstrap integrated into Task T028).
- **T035**: Implement coverage trend analysis. Compute regression slope for coverage vs. beta. Verify slope < 0 AND p < 0.05. Write to data/results/sensitivity_analysis.json with negative_slope_confirmed flag.
- **T036**: Implement oracle benchmark (IPW on complete data). Compute bias relative to oracle for independent validation.

### Phase 4: Visualization & Documentation (Tasks T037-T042c)
- **T037-T041**: Finalize analysis and prepare paper.
- **T042a**: Generate bias_vs_beta.png: Plot bias by imputation method across beta levels. Script: `python code/visualization.py --plot bias_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/bias_vs_beta.png`.
- **T042b**: Generate coverage_vs_beta.png: Plot coverage rate by method across beta levels. Script: `python code/visualization.py --plot coverage_vs_beta --input data/results/simulation_summary.csv --output docs/paper/figures/coverage_vs_beta.png`.
- **T042c**: Generate bias_distributions.png: Boxplot of bias distributions per beta level. Script: `python code/visualization.py --plot bias_distributions --input data/results/simulation_summary.csv --output docs/paper/figures/bias_distributions.png`.
