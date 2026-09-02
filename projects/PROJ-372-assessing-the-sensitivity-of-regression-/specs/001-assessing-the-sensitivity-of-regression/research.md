# Research: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## 1. Research Question
How does the stability (variation in estimated values) of OLS regression coefficients vary as a function of:
1. **Dataset Subset Size**: Specifically across multiple tiers spanning a range of full-size proportions.
2. **Assumption Violations**: Quantified by Condition Number (multicollinearity), Breusch-Pagan p-value (heteroscedasticity), and Cook's Distance (outliers).

**Hypothesis**: The variance of coefficient estimates increases as subset size decreases. Furthermore, this increase is amplified in datasets with higher violation severity (Heteroscedasticity, Outliers, Multicollinearity).

## 2. Dataset Strategy

### 2.1 Verified Datasets
The following datasets are verified for programmatic access and numerical suitability. **Only these sources will be used.**

| Dataset Name | Source Type | Verified URL | Suitability Notes |
| :--- | :--- | :--- | :--- |
| **UCI Bike Sharing** | HuggingFace (Parquet) | `https://huggingface.co/datasets/UCI-Machine-Learning-Repository/Bike-Sharing-Dataset` | Continuous target `cnt` (count of bikes). Numerical predictors (temp, humidity, etc.). Verified for OLS. |
| **UCI California Housing** | HuggingFace (Parquet) | `https://huggingface.co/datasets/UCI-Machine-Learning-Repository/California-Housing` | Continuous target `MedHouseVal`. Numerical predictors (income, age, etc.). Verified for OLS. |

*Note: Datasets like UCI HAR (classification) and UCI DROP (text-based) were excluded as they lack verified continuous targets without synthetic derivation.*

### 2.2 Data Loading Strategy
- **Streaming**: For datasets exceeding 7GB, `datasets.load_dataset(..., streaming=True)` will be used.
- **Programmatic Loading**: For smaller datasets (likely the verified sources above), `datasets.load_dataset` (non-streaming) or `pandas.read_parquet` will be used.
- **Preprocessing**:
  - Filter to rows with no missing values in predictor or target columns.
  - Select the specific continuous target variable (`cnt` for Bike Sharing, `MedHouseVal` for California Housing) and 3-5 numerical predictors.
  - **Constraint**: If a dataset lacks a continuous target or sufficient numerical predictors, it will be skipped, and the reason logged.

## 3. Methodology

### 3.1 Assumption Violation Profiling (Full Dataset)
Before resampling, the full dataset is profiled:
1.  **Multicollinearity**: Compute Condition Number of the design matrix $X$.
    -   Severity: High if $\kappa > 30$, Medium if $10 < \kappa \le 30$, Low if $\kappa \le 10$.
2.  **Heteroscedasticity**: Perform Breusch-Pagan test.
    -   Severity: High if $p \le 0.05$, Medium if $0.05 < p \le 0.10$, Low if $p > 0.10$.
3.  **Outliers**: Compute Cook's Distance for all observations.
    -   Severity: High if max(Cook's D) > 1.0, Medium if > 0.5, Low otherwise.

### 3.2 Subset Resampling and Stability Estimation
- **Tiers**: 10, 25, 50, 75, 90 of full dataset size ($N$).
- **Iterations**: Multiple random subsets per tier.
- **Model**: OLS Regression ($Y = \beta_0 + \beta_1 X_1 + \dots + \epsilon$).
- **Metric**: **Individual Coefficient Values** ($\beta_{j, s}$) are stored for each subset $s$.
- **Convergence Check**: Calculate Empirical SD and Standard Error of the SD across 200 subsets *per tier*.
  -   $SE_{SD} = \frac{SD_{SD}}{\sqrt{200}}$ (approximation).
  -   **Threshold**: $SE_{SD} < 0.05 \times SD_{\beta}$. If not met, **FLAG** and **HALT** (US2).
  -   *Note*: This check validates the precision of the stability estimate but does not restrict the input to the HLM.

### 3.3 Hierarchical Linear Modeling (HLM) (Revised Methodology)
**Statistical Rationale**: The violation metrics (Condition Number, BP p-value, Cook's D) are computed on the *full dataset* and are constant for all subsets of that dataset. Regressing subset-level coefficients against these static metrics in a flat regression would create perfect multicollinearity with "Dataset Identity," making it impossible to distinguish the effect of violations from the dataset's inherent properties.

**Solution**: A **Hierarchical Linear Model (HLM)** (also known as Multilevel Model) is used.
-   **Level 1 (Within-Dataset)**: The unit of analysis is the **individual subset** ($s$).
    -   **Outcome**: The specific coefficient value $\beta_{j, s}$ for a given predictor $j$.
    -   **Predictor**: `Subset_Size` (continuous or categorical tier).
-   **Level 2 (Between-Dataset)**: The unit of analysis is the **dataset** ($d$).
    -   **Predictor**: `Violation_Severity` (Low/Med/High) or continuous metric (e.g., Condition Number).
-   **Interaction**: The model estimates the interaction between `Subset_Size` (Level 1) and `Violation_Severity` (Level 2).

**Model Formula**:
$$ \beta_{j, s} = \gamma_{00} + \gamma_{10}(\text{Size}_s) + \gamma_{01}(\text{Severity}_d) + \gamma_{11}(\text{Size}_s \times \text{Severity}_d) + u_{0d} + r_{js} $$

Where:
-   $\beta_{j, s}$: The coefficient value for predictor $j$ in subset $s$.
-   $\text{Size}_s$: The sample size of subset $s$ (or tier indicator).
-   $\text{Severity}_d$: The violation severity metric for dataset $d$.
-   $u_{0d}$: Random intercept for dataset $d$ (accounts for dataset-specific baseline).
-   $r_{js}$: Residual error.

**Interpretation**:
-   $\gamma_{10}$: The main effect of subset size on coefficient variation (expected to be non-zero).
-   $\gamma_{11}$: The **interaction effect**. If significant, it indicates that the sensitivity of coefficients to subset size depends on the violation severity.
-   This design resolves the confound because the effect of `Size` is estimated from the variance *within* datasets (1000 points), while the effect of `Severity` is estimated from the variance *between* datasets.

**Output**: An `HLMResults` artifact containing fixed effects, random effects variance, and interaction significance.

## 4. Statistical Rigor & Feasibility

### 4.1 Compute Feasibility (CPU-First)
- **Constraint**: GitHub Actions (CPU, 7GB RAM).
- **Strategy**:
  -   **OLS**: `statsmodels` OLS is highly optimized for CPU.
  -   **Resampling**: 200 subsets $\times$ 5 tiers = 1000 fits per dataset. With small datasets (e.g., Bike Sharing), this is trivial.
  -   **HLM**: `linearmodels` or `statsmodels` mixed models are CPU-tractable for N=1000.
  -   **No GPU**: OLS and simple aggregation do not require GPU.

### 4.2 Statistical Validity
- **Multiple Comparisons**: Not applicable to the primary HLM test. If post-hoc tests are added, FDR will be used.
- **Power**: N=1000 (subsets) provides high precision for estimating the Level 1 slope. The limitation is the number of *datasets* (2-3), which limits the power to detect Level 2 effects (Severity). This is acknowledged as a limitation, but the design is statistically valid.
- **Causal Claims**: **Associational only.** The study observes correlations between violation severity and stability trends.
- **Collinearity**: The HLM design explicitly handles the nested structure, avoiding the confounding of "Dataset Identity" with "Violation Severity" by separating Level 1 and Level 2 predictors.

## 5. Decision Rationale
- **CPU vs GPU**: CPU is selected because OLS and simple aggregation are efficient on CPU.
- **Dataset Selection**: Restricted to verified HuggingFace/UCI sources (Bike Sharing, California Housing) with verified continuous targets to ensure CI reproducibility.
- **Convergence Threshold**: The SE threshold is a hard constraint from the spec. If not met, the result is flagged, and the pipeline halts to prevent invalid analysis.
- **Methodology Choice**: Hierarchical Linear Modeling is chosen over regression or stratified comparison to resolve the "static predictor" and "Dataset Identity" confounding issues, ensuring statistical validity by modeling the interaction between subset size (Level 1) and violation severity (Level 2).