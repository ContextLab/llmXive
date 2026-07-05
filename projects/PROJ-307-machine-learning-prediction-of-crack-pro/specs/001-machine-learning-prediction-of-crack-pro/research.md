# Research: Machine Learning Prediction of Crack Propagation Rates in Metals

## Overview

This research phase investigates the feasibility of using machine learning to predict fatigue crack growth rates ($da/dN$) in metals, specifically quantifying the contribution of material composition and heat-treatment descriptors beyond the standard Paris Law ($\Delta K$) baseline. The study addresses the "control" condition (Paris Law validity) and the "treatment" condition (Engineering Descriptors) to determine if non-linear interactions exist, particularly in low and high $\Delta K$ regimes.

## Dataset Strategy

The analysis relies on public fatigue crack growth (FCG) datasets. Per the "Verified datasets" block, the following sources are available. **Note**: A critical verification step is required to ensure these specific datasets contain the necessary variables ($da/dN$, $\Delta K$, composition, heat treatment).

| Dataset Name | Source URL | Format | Variables Verified? | Strategy |
|:--- |:--- |:--- |:--- |:--- |
| **FCGEC** | ` | CSV | **Pending Verification** | Primary candidate. Must verify columns for $da/dN$, $\Delta K$, alloy composition, and heat treatment. If missing, fallback strategy applies (see below). |
| **NASA NDI (Verified Subset)** | `https://huggingface.co/datasets/nasa/ndi-fatigue/resolve/main/fcg_data.csv` | CSV | **Pending Verification** | Secondary candidate. Must inspect for FCG specific records and required engineering descriptors. **Note**: If this URL does not contain FCG data, it is immediately marked "Excluded". |
| **Other Sources** | (Any other URLs in block) | Various | **NO** | **Permanently Excluded**. Datasets failing the variable check (composition, heat treatment) are excluded from analysis. No fallback to "Other Sources" is permitted. |

**Critical Decision**: The primary dataset candidate is `FCGEC_train.csv`. The implementation MUST first load this file and verify the presence of:
1. `da/dN` (or equivalent crack growth rate column)
2. `Delta_K` (or equivalent stress intensity factor)
3. Composition columns (e.g., `C`, `Mn`, `Si` in wt%)
4. Heat Treatment column (categorical)

**Fallback Strategy**: If `FCGEC_train.csv` lacks heat-treatment data but contains composition:
- The study will proceed with a "Composition-Only" augmentation model.
- The research question will be re-framed to "To what extent does composition explain variance... beyond $\Delta K$?" (excluding heat treatment).
- A warning will be logged regarding the scope reduction.
- If **both** composition and heat treatment are missing, the project **cannot proceed** with the core research question and will halt with a fatal error.

**Assumption**: The `FCGEC` dataset (or the NASA NDI subset if it contains FCG data) contains the necessary engineering descriptors. If the dataset only contains $\Delta K$ and $da/dN$ without composition/heat-treatment, the "Augmented Model" (US-2) is limited to available descriptors.

## Methodology

### 1. Data Preprocessing
- **Ingestion**: Load CSV from verified URL.
- **Verification**: Check for required columns using `jsonschema` against `contracts/dataset.schema.yaml`. If missing, trigger Fallback Strategy or Halt.
- **Filtering**: Retain rows where $da/dN > 0$ and $\Delta K > 0$.
- **Imputation**: Missing heat-treatment values are imputed with "Unknown/Not Specified" (categorical) to preserve sample size (US-1).
- **Encoding**:
 - $\Delta K$ and $da/dN$ are log-transformed ($\log_{10}$) to linearize the Paris Law relationship.
 - Composition features (wt%) are normalized.
 - Heat-treatment is one-hot encoded.
- **Splitting**: 5-fold cross-validation stratified by alloy family (if identifiable) or random split if alloy family is not distinct.

### 2. Baseline Model (Paris Law)
- **Model**: **Alloy-Family Stratified Linear Regression**.
 - Instead of a single global line, fit separate intercepts for each alloy family (e.g., Aluminum, Steel) to account for the variation in constant $C$ in $da/dN = C(\Delta K)^m$.
 - Model: $\log(da/dN) \sim \text{AlloyFamily} + \log(\Delta K)$.
- **Metric**: $R^2$, RMSE.
- **Validation**: Check linearity via Partial Dependence Plot (PDP). Confirm slope corresponds to Paris exponent $m$.

### 3. Augmented Models
- **Models**: Random Forest Regressor, XGBoost Regressor.
- **Features**: $\log(\Delta K)$ + Composition + Heat Treatment.
- **Tuning**: Optuna for hyperparameter optimization (max 50 trials, CPU-only).
- **Comparison**: **Permutation Test** (5000 permutations).
 - *Rationale*: The F-test is invalid for comparing linear and non-linear models.
 - *Method*: Shuffle the engineering descriptors (composition/heat treatment) and measure the drop in performance relative to the baseline. Calculate p-value as the proportion of permutations where the drop is less than the observed drop.
 - *Significance*: $\alpha = 0.05$.

### 4. Regime Analysis
- **Identification**: Use **Change-Point Detection** (library: `ruptures`) on the residuals of the baseline model to objectively identify boundaries between Low, Mid, and High $\Delta K$ regimes. Avoid arbitrary binning.
- **Local Metrics**: Calculate $R^2$ and feature importance within each identified regime.
- **Variance Decomposition**: Perform **Residual Decomposition** to isolate the variance contribution of composition *after* accounting for the baseline fit, ensuring "dominance" is not just baseline failure.
- **Hypothesis**: Microstructural effects (composition/heat-treatment) dominate in Low and High regimes; Mid regime is dominated by $\Delta K$.

### 5. Sensitivity Analysis
- **Method**:
 1. **Boundary Perturbation**: Perturb the detected change-point boundaries by $\pm 10\%$ and re-calculate local metrics. Verify that the "dominance regions" (Low/High) remain consistent.
 2. **Data Bootstrapping**: Resample the data (with replacement) 100 times and re-run regime identification.
- **Stability Check**: Verify that the identified "dominance regions" (Low/High) remain consistent across bootstraps and boundary shifts.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: When testing significance across multiple regimes, apply Bonferroni correction or False Discovery Rate (FDR) control to the p-values of the regime-specific tests.
- **Power Analysis**: The dataset size is [deferred] to the research phase. If the sample size is insufficient for 5-fold CV, the plan will reduce folds to 3 or use a hold-out validation set.
- **Causal Claims**: The study is observational. Claims will be framed as "predictive association" rather than "causal effect" of heat treatment.
- **Collinearity**: If composition elements are highly correlated (e.g., sum of wt% = 100%), the plan will use regularization (L1/L2) or dimensionality reduction (PCA) if collinearity diagnostics (VIF) indicate instability.
- **Compute Constraints**:
 - **No GPU**: All models use CPU. XGBoost will be configured with `tree_method='hist'` or `approx` for efficiency.
 - **Memory**: Data will be loaded in chunks if > 1GB. Feature matrices will be cast to `float32` to reduce RAM usage.
 - **Time**: Optuna trials limited to 50. If training exceeds 4 hours, the process is terminated with a timeout warning.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Dataset Mismatch** | Fatal. If verified datasets lack composition/heat-treatment data. | **Stop-the-line check** in `loader.py` using `jsonschema`. If variables missing, report error and halt (or fallback if partial). Do not fabricate data. |
| **Overfitting** | High. Complex models on small datasets. | Strict 5-fold CV, early stopping for XGBoost, and feature selection based on permutation importance. |
| **Runtime Exceeded** | High. CI job fails after 6 hours. | Limit Optuna trials; use subsampling (e.g., 10k rows) for tuning; fallback to simpler models if needed. |
| **Unseen Alloy Families** | Medium. Model fails on new materials. | Explicitly test on held-out alloy families; log warnings if performance drops > [deferred]%. |
| **Spec Conflict (FR-005)** | High. Spec requires F-test; Plan rejects it. | Plan implements Permutation Test only. Spec update required to remove F-test option. |