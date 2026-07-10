# Research: Predicting the Yield Strength of Steel Alloys from Composition and Heat Treatment Parameters

## Summary of Findings

This research phase investigates the feasibility of predicting steel yield strength using composition and heat treatment data. The primary challenge identified is the **dataset-variable fit**: the spec requires specific thermal history variables (cooling rate, holding time) and yield strength measurements. The available verified datasets in the provided list do not explicitly contain a dataset matching the "NIST Materials Data Repository" or "Materials Project" description for *steel yield strength* with the required thermal parameters.

The provided "Verified datasets" block contains URLs for NIST security logs, gaming metadata, skin disease images, and text corpora. **None of these verified sources contain steel alloy composition or yield strength data.** Consequently, the plan must rely on the **Assumption** that a valid dataset exists or will be sourced via a verified repository. The literature-mining pipeline (FR-012) is **removed** as a primary data strategy because it is non-deterministic and violates Constitution Principle I (Reproducibility). Instead, the pipeline will **halt with a 'Data Source Missing' error** if no verified dataset URL is found in the `# Verified datasets` block.

> **Spec Contradiction Flag**: The spec.md Assumptions block explicitly lists "literature-mining pipeline" as a fallback if N < 100. This contradicts the plan's hard-fail policy required by Constitution Principle I. The spec assumption is flagged as a spec-root cause issue and will not be implemented.

## Dataset Strategy

| Dataset Name | Intended Use | Verified Source (URL) | Status / Notes |
| :--- | :--- | :--- | :--- |
| **NIST Steel Alloys** | Primary source for composition & yield strength | *None in verified block* | **Gap Detected**: No verified URL exists for steel yield strength in the provided list. **Action**: Pipeline halts with 'Data Source Missing' error. Literature mining is NOT used as a fallback for primary data. |
| **Materials Project** | Primary source for thermal parameters | *None in verified block* | **Gap Detected**: No verified URL exists for thermal history in the provided list. |
| **Fallback: None** | N/A | N/A | **Hard Fail**: If no verified dataset is found, the project cannot proceed to `research_complete`. This ensures reproducibility. |

> **Critical Note on Dataset Fit**: The spec requires `cooling_rate`, `holding_time`, and `yield_strength`. If the ingested data lacks these specific columns, the pipeline must halt with a clear error (Edge Case: API unreachable or missing columns). The implementation must **not** proceed with proxy variables (e.g., using "hardness" instead of "yield strength") unless explicitly validated as a surrogate in the literature.

## Methodological Approach

### 1. Data Ingestion & Preprocessing (FR-001, FR-002)
- **Cleaning**: Remove rows where `yield_strength` is null (FR-001).
- **Normalization**: Scale `temperature` and `cooling_rate` to [0.0, 1.0] using MinMaxScaler (FR-002).
- **Encoding**: One-hot encode categorical `heat_treatment_type` (e.g., quenching, tempering) (FR-002).
- **Sample Check**: If `n_samples < 100`, trigger a warning and switch to 10-fold repeated CV (see Step 3).

### 2. Feature Engineering (FR-003, FR-010)
- **Ratios**: Compute `C/Mn` and `Cr/Ni`.
- **Interactions**: Create pairwise products (e.g., `C × Cooling_Rate`).
- **Non-Linear Orthogonalization**: Project interaction features onto the orthogonal complement of their constituent main effects using a **GAM with splines (k=5, cubic)** to remove both linear and non-linear collinearity (FR-010).
  - *Method*: For interaction $X \times Z$, fit a GAM model: $I \sim \text{GAM}(X, Z)$ using **splines with k=5, cubic basis**. Use the **residuals** ($I_{ortho} = I - \hat{I}$) as the orthogonalized feature.
  - *Basis Match*: The orthogonalization basis (GAM with cubic splines, k=5) is **identical** to the main effects model used in the permutation test's null generation. This ensures that non-linear main effect variance is removed from the interaction feature, preventing confounding in SHAP values.
  - *Physical Validity Check*: To distinguish statistical artifacts from physical synergy, a secondary analysis will be performed using **raw interaction terms** in XGBoost. If the raw model shows high performance but the orthogonalized model does not, the result will be flagged as 'physically ambiguous', indicating the 'synergy' may be a non-linear main effect artifact.

### 3. Model Training (FR-004)
- **Models**: 
  1. **GAM** (Generalized Additive Model) with splines (captures non-linear main effects).
  2. **Ridge/Lasso** (Regularized Linear Regression).
  3. **Random Forest** (Non-linear interactions).
  4. **XGBoost** (Gradient Boosting, CPU-only).
- **Validation Strategy & Justification**:
  - **Standard**: 5-fold Cross-Validation.
  - **Small Dataset (N < 500)**: 10-fold repeated Cross-Validation (3 repeats).
  - *Justification*: 3-fold CV on small N yields high variance in performance estimates, making feature selection unstable. 10-fold repeated CV reduces this variance, providing a more reliable basis for stability analysis and ensuring the robustness of identified interaction terms.
- **Constraints**: CPU-only, default precision. No GPU. Grid search capped at 100 points.

### 4. Interaction Detection & Validation (FR-005, FR-008, FR-009)
- **SHAP Analysis**: Compute SHAP interaction values to rank interactions (FR-005).
- **Nested Permutation Test**:
  - **Outer Loop**: 5-fold CV (or 10-fold repeated for small N) for performance estimation.
  - **Inner Loop**: 
    1. Fit a **GAM baseline** (with identical spline degrees of freedom, **k=5, cubic**) on the training fold to generate residuals for the main effects.
    2. **Permute the orthogonalized interaction feature** ($I_{ortho}$) relative to the target, while keeping the main effects constant. This breaks the specific interaction signal while preserving the main-effect structure, avoiding the tautology of testing a residual that is mathematically independent by construction.
    3. Refit the GAM baseline on the permuted data (with **identical spline structure**) to generate the null distribution of R² improvement.
    4. Compare the observed R² improvement (orthogonalized interaction model vs. main-effects-only) against this null distribution.
  - **Null Hypothesis**: Interaction term has no predictive power beyond main effects.
  - **Correction**: Apply Benjamini-Hochberg (FDR) with $\alpha \le 0.05$ to p-values (FR-008).
- **Causal Framing**: All results framed as associational (FR-007).

### 5. Sensitivity Analysis (FR-006)
- **Sweep**: P-value thresholds {0.01, 0.05, 0.10} from the **nested permutation test (FR-009)**. This validates the robustness of the *statistical significance* of the interaction terms, not just arbitrary feature rankings.
- **Metrics**: **Kuncheva index** (adjusted Rand index) for stability (robust to feature count) and Spearman rank correlation.
- **Minimum Feature Count**: A minimum of 5 features must be selected at each threshold for the Kuncheva index to be computed. If fewer than 5 features are selected, the result is flagged as 'insufficient_data' rather than 'unstable'.
- **Flag**: If Kuncheva index < 0.8 or if <5 features are selected at any threshold, flag as 'unstable' or 'insufficient_data' (SC-003).

## Decision Rationale & Feasibility

- **CPU-Only Constraint**: XGBoost and Random Forest are highly optimized for CPU. Grid search is capped at 100 points to ensure the 4-hour runtime limit on 2-core runners is met.
- **Non-Linear Orthogonalization**: Essential for the scientific validity of the interaction claims. Linear orthogonalization fails to remove non-linear main effect variance, confounding SHAP values.
- **Dataset Gap**: The absence of a verified steel dataset in the provided list is a critical risk. The plan explicitly **fails hard** if no verified source is found, adhering to Constitution Principle I (Reproducibility) and avoiding non-deterministic scraping.
- **Small Sample Size**: For N < 500, 10-fold repeated CV and Kuncheva index are used to mitigate variance and feature count sensitivity.

## Statistical Rigor Checklist

- [x] **Multiple Comparison Correction**: Benjamini-Hochberg applied to interaction p-values (FR-008).
- [x] **Power Justification**: 10-fold repeated CV used for N < 500 to reduce variance in performance estimates, addressing the instability of 3-fold CV.
- [x] **Causal Assumptions**: Explicitly stated as observational/associational (FR-007).
- [x] **Collinearity**: Addressed via non-linear (GAM) orthogonalization (FR-010).
- [x] **Measurement Validity**: Relies on standard metallurgical formulas (IIW) for derived indices (Assumptions).
- [x] **Model Complexity Control**: Inner loop GAM uses identical spline structure (k=5) to prevent Type I errors.
- [x] **Stability Metric**: Kuncheva index used to handle small feature sets, with a minimum feature count of 5.