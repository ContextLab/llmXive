# Research: Predicting the Yield Strength of BCC Steels from Compositional Data and Density Functional Theory

## Problem Statement
The goal is to determine if atomic-scale descriptors (DFT elastic constants) significantly improve the prediction of macroscopic yield strength in BCC iron alloys compared to using chemical composition alone. This is an **empirical** question; the answer must be derived from real data, not simulated relationships.

## Dataset Strategy

### Verified Sources
Per the project constraints, we rely **only** on verified datasets available via HuggingFace or public repositories.

| Dataset Name | Verified URL | Intended Use | Status/Constraint |
| :--- | :--- | :--- | :--- |
| **Materials Project Elasticity** | `https://huggingface.co/datasets/materialsproject/elasticity` | Source for Shear/Bulk Modulus (DFT). | **Verified**: Contains real DFT elastic constants. Must be filtered for BCC Fe-alloys. |
| **NIST Experimental (Proxy)** | `https://huggingface.co/datasets/nmat/nist-materials` | Source for experimental yield strength. | **Verified**: Contains experimental mechanical properties. Must be filtered for BCC Fe-alloys. |
| **Fallback** | N/A | If no overlap found. | **Action**: If the merged dataset has n < 20, the study proceeds in "Exploratory Mode" (report effect sizes, no significance claims). If n = 0, the study terminates with "Data Availability Failure". |

### Dataset Variable Fit Analysis
- **Required Variables**: `yield_strength_MPa`, `chemical_formula`, `shear_modulus_GPa`, `bulk_modulus_GPa`, `crystal_structure`.
- **Materials Project Elasticity**: Contains `shear_modulus`, `bulk_modulus`, `structure` (space group). **Fit**: Good for DFT features.
- **NIST Experimental**: Contains `yield_strength`, `composition`. **Fit**: Good for target.
- **Overlap Check**: The primary challenge is finding BCC Fe-alloys present in *both* datasets. If the overlap is small, the study acknowledges the limitation rather than fabricating data. **No synthetic data will be generated to fill this gap.**

## Methodology

### 1. Data Ingestion & Merging (FR-001, FR-002, FR-003)
- **Ingestion**: Load data from verified HuggingFace datasets using `datasets.load_dataset()`.
- **Filtering**: Retain only rows where `crystal_structure` == "BCC" (Space Group 229 or equivalent).
- **Merge**: Join on `chemical_formula` (normalized).
- **Handling**:
  - If `yield_strength` is a range, take midpoint.
  - If DFT data is missing for a composition, log warning and drop row.
  - **Sample Size Check**: If `n < 20`, raise `PowerWarning` and switch to "Exploratory Mode". If `n = 0`, raise `DataAvailabilityError`.

### 2. Feature Engineering
- **Composition Features**: One-hot encoding of elements, atomic fraction, atomic radius variance, electronegativity difference.
- **DFT Features**: `shear_modulus`, `bulk_modulus`, `Pugh's ratio` (Bulk/Shear).
- **Thresholding**: Apply sensitivity analysis thresholds (0.01, 0.05, 0.1) relative to mean shear modulus for feature inclusion (FR-007).

### 3. Modeling (FR-004)
- **Model**: Random Forest Regressor (`sklearn.ensemble.RandomForestRegressor`).
- **Configuration**: `n_estimators=100`, `max_depth=None`, `random_state=42`.
- **Validation**: 5-Fold Cross-Validation.
- **Baseline**: Composition-only model (no DFT features).

### 4. Evaluation & Statistical Testing (FR-005, SC-001, SC-002, SC-003)
- **Metrics**: R², Mean Absolute Error (MAE).
- **Correlation**: Pearson correlation between `shear_modulus` and `yield_strength` (SC-001). Report r and 95% CI.
- **Significance Test**:
  - **If n >= 20**: Perform paired t-test on fold-wise MAE errors between DFT+Model and Baseline. Null Hypothesis ($H_0$): Mean difference in errors is zero. Threshold: $p < 0.05$.
  - **If n < 20**: **Omit the paired t-test** (statistically invalid for n=5 pairs). Instead, calculate and report Cohen's d (effect size) and 95% CI for the difference in MAE, explicitly stating that the study is underpowered for hypothesis testing.

### 5. Interpretability & Sensitivity (FR-006, FR-007, FR-008)
- **SHAP Analysis**: Calculate SHAP values for all features (FR-006).
- **Permutation Importance**: Calculate for all features.
- **Stability**: Bootstrapping (10 samples) to compute standard deviation of SHAP/Permutation importance scores (Target < 0.05).
- **Sensitivity Analysis**: Sweep DFT threshold and record MAE/R² variation.

## Statistical Rigor & Assumptions
- **Multiple Comparisons**: Bonferroni correction applied if multiple thresholds are tested.
- **Power Analysis**: Calculate minimum detectable effect size given actual n. If n < 20, explicitly state that the study is underpowered for hypothesis testing and focus on effect size. **The paired t-test is omitted in this regime.**
- **Causal Claims**: No causal claims. All results are associational.
- **Collinearity**: Composition features and DFT descriptors may be correlated. SHAP values will be used to assess relative contribution, acknowledging that DFT descriptors are derived from the same atomic structure.

## Limitations
- **Data Availability**: The primary limitation is the potential lack of overlap between experimental and DFT datasets for specific BCC Fe-alloys. The plan explicitly handles this by reporting "Data Availability Failure" or "Exploratory Mode" results rather than simulating data.
- **Sample Size**: Small sample sizes may limit statistical power. The plan addresses this by prioritizing effect sizes and confidence intervals over p-values when n is small, and by omitting the t-test when n < 20.
