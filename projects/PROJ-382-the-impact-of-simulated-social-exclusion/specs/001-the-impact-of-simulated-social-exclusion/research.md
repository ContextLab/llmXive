# Research: The Impact of Simulated Social Exclusion on Subsequent Prosocial Behavior

## 1. Research Question & Hypotheses

**Primary Question**: Does experimentally induced social exclusion reduce subsequent willingness to engage in prosocial behavior (monetary donation) among adults?

**Hypotheses**:
- **H1 (Causal)**: In randomized trials (Causal Pool), social exclusion leads to a statistically significant reduction in the **Total Expected Donation** (Average Marginal Effect < 0).
- **H2 (Associational)**: In non-randomized studies (Associational Pool), a negative correlation exists between exclusion status and prosocial behavior, though causal direction is unverified (reported with E-values for robustness).

## 2. Dataset Strategy

**Constraint**: Only datasets from the "Verified datasets" block may be cited. The spec requires OSF datasets containing `condition`, `prosocial_amount`, and `randomized`.

**Verified Sources Analysis**:
The provided verified list contains:
- OSF parquet/CSV files (e.g., `osf_loglikelihood`, `FC_graph_covariate_data`).
- RCT datasets (e.g., `tsar2025_trial`, `rct-20k`).
- General repositories (Iris, Reddit URLs, etc.).

**Gap Identification**:
The verified list **does not** contain a dataset explicitly labeled as "Social Exclusion" or "Cyberball" with `prosocial_amount` and `randomized` columns. The `osf_loglikelihood` and `FC_graph_covariate_data` appear to be related to graph/likelihood tasks, not prosociality. The `rct` datasets are generic RCT lists, not behavioral data.

**Action Plan & Pre-registered Search Protocol**:
1.  **Primary Search**: The pipeline will first attempt to locate specific OSF datasets using the verified list.
2.  **Fallback Strategy (Pre-registered)**: If the verified list yields no valid datasets, the system will execute a **pre-registered keyword search** on OSF.
    -   **Search Strings**: `("social exclusion" OR "ostracism" OR "Cyberball") AND ("prosocial" OR "donation" OR "allocation" OR "dictator game")`
    -   **Inclusion Criteria**: Must contain `condition`, `prosocial_amount`, `randomized` (or metadata allowing derivation).
    -   **Bias Mitigation**: The search strings and inclusion criteria are fixed *before* execution to prevent cherry-picking.
3.  **Halt Condition**: If the combined set (Verified + Pre-registered Search) yields fewer than 3 valid datasets, the pipeline **MUST** halt with "Insufficient Data: <3 valid datasets found". This is a valid scientific outcome, not a failure of the pipeline.

**Dataset Validation Criteria**:
-   Must contain: `condition` (exclusion/inclusion), `prosocial_amount` (continuous or binary), `randomized` (boolean).
-   Must be accessible via the verified URL or the OSF search mechanism triggered by the pipeline.

**Table: Dataset Inclusion Strategy**

| Dataset Source | Verification Status | Inclusion Criteria | Action if Missing |
| :--- | :--- | :--- | :--- |
| OSF (Verified List) | *Pending* | Must have `condition`, `prosocial_amount`, `randomized`. | Skip and log error. |
| OSF (Pre-registered Search) | *Runtime* | Must match fixed search strings and schema. | If <3 found overall, HALT. |

## 3. Statistical Methodology

### 3.1 Data Preprocessing
-   **Imputation**: Median imputation for `prosocial_amount` if missingness < 5% per dataset. Row exclusion if ≥ 5%.
-   **Structural Zeros**: Values of 0 are **NOT** imputed. They are preserved for the Zero-Inflated model.
-   **Normalization**: `condition` mapped to binary (0=Included, 1=Excluded). **Deterministic Logging**: The exact mapping logic (e.g., 'ignored' -> 1) and raw values are recorded in `mapping_log.json`.
-   **Temporal Separation**: The pipeline validates the presence of separate task identifiers or timestamps in raw data (if available) to support the assumption of behavioral outcome independence.
-   **Filtering**: Exclude datasets where `condition == 1` (Excluded) has n < 5.

### 3.2 Model Selection
-   **Primary Model**: Zero-Inflated Gamma (ZIG) or Hurdle Model.
    -   *Component 1 (Zero-Inflation)*: Logistic regression predicting probability of zero donation.
    -   *Component 2 (Positive)*: Gamma GLM predicting amount given donation > 0.
-   **Alternative**: If `prosocial_amount` is purely binary (0/1), use Logistic Regression.
-   **Pools**:
    -   **Causal Pool**: `randomized == true`.
    -   **Associational Pool**: `randomized == false` or `unknown`.

### 3.3 Meta-Analysis & Effect Size Definition
**Critical Correction**: To ensure cross-study comparability, the primary meta-analysis will **NOT** pool raw conditional coefficients (log-odds and log-scale) directly. Instead, it will pool the **Average Marginal Effect (AME)** of the exclusion condition on the **Total Expected Donation**.

1.  **Total Expected Donation Calculation**: For each study, calculate:
    $$ E[Y|X] = P(Y>0|X) \times E[Y|Y>0, X] $$
    Where $P(Y>0|X)$ is derived from the Zero-Inflation component and $E[Y|Y>0, X]$ from the Positive component.
2.  **Effect Size**: The difference in $E[Y|X]$ between Exclusion (X=1) and Inclusion (X=0) conditions. This is the **AME**.
3.  **Aggregation**:
    -   **Primary**: Random-Effects Meta-Analysis of the AME (Total Expected Donation difference) for Causal and Associational pools separately.
    -   **Diagnostic**: Separate Random-Effects meta-analyses for the Zero-Inflation coefficient and Positive coefficient are performed *only* to diagnose which component drives the effect, but these are not pooled into a single "combined" estimate due to scale incompatibility.

**Small-Sample Bias Correction**:
-   The pipeline will perform a **Trim-and-Fill** analysis and calculate **Egger's regression** to detect and adjust for small-sample bias (the "winner's curse") in the meta-analytic estimate.

### 3.4 Sensitivity & Robustness
-   **Distributional Sweep**: Re-run models with distributional assumptions (Gamma vs. Log-Normal) while keeping the primary link function (logit) fixed. Report stability of the AME (variance < 10%).
-   **Unmeasured Confounding (E-Value)**: For the **Associational Pool**, calculate the E-value to quantify the minimum strength of association an unmeasured confounder would need to explain away the observed effect.
-   **Randomization Check**: For the **Causal Pool**, if covariate data is available, perform balance tests (t-tests/chi-square) to verify randomization integrity.
-   **Outlier Check**: Re-run excluding outliers (>3 SD) and report $\Delta\beta$.
-   **Power Assessment**: Calculate power to detect Cohen's d = 0.3 given observed $I^2$ and study count.

## 4. Compute Feasibility

-   **Environment**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
-   **Strategy**:
    -   No GPU required.
    -   `statsmodels` ZIG/Hurdle implementations are CPU-tractable for <100k rows.
    -   Data subset to <7GB RAM (likely <100MB).
    -   Runtime target: < 2 hours (well within 6h limit).
-   **Libraries**: `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `scikit-learn`. All available on CPU.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **No Valid Datasets Found** | Project halts (FR-008). | Pre-registered search protocol defined. If <3 found, report "Insufficient Data" as a valid outcome. |
| **ZIG Convergence Failure** | Model fails to fit. | Fallback to Hurdle model; then fallback to Logistic if binary; log convergence warnings. |
| **High Heterogeneity ($I^2$)** | Meta-analysis unreliable. | Report $I^2$; perform sensitivity analysis; do not claim a single pooled effect if $I^2 > 75\%$ without explanation. |
| **Dataset Missing `randomized`** | Ambiguous pool assignment. | Treat as `Associational` pool (conservative approach). |
| **Small-Sample Bias** | Overestimation of effect size. | Apply Trim-and-Fill and Egger's regression correction. |