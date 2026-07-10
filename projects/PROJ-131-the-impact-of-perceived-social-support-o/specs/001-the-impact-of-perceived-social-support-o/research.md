# Research: The Impact of Perceived Social Support on Resilience to Online Harassment

## 1. Research Question & Hypotheses

**Primary Question**: Does higher perceived social support buffer (moderate) the negative impact of online harassment exposure on mental health outcomes (Depression, Anxiety, PTSD) within a single, consistent population?

**Hypotheses**:
*   **H1 (Main Effect)**: Higher harassment exposure is associated with higher levels of Depression, Anxiety, and PTSD symptoms.
*   **H2 (Buffering Effect)**: The positive association between harassment exposure and mental health symptoms is weaker for individuals with higher perceived social support (significant negative interaction term: `SocialSupport × HarassmentExposure`).
*   **H3 (Robustness)**: The buffering effect remains consistent across different operationalizations of harassment (binary vs. continuous) and across different platform types (if data permits).

## 2. Dataset Strategy

### 2.1 Source Verification & Availability
The project relies on a single, internally consistent dataset to ensure the validity of the interaction term.

| Dataset Name | Required Variables | Verified Source Status | Action Plan |
| :--- | :--- | :--- | :--- |
| **Cyberbullying Survey** | Harassment Exposure, Social Support, Mental Health (CES-D/GAD-7/PCL-5), Demographics, Platform Type | **NO verified source found** in the provided list. | **Implementation Strategy**: The pipeline requires a local file `data/raw/cyberbullying_survey.csv`. The user must provide this file. If the file is missing, the pipeline fails gracefully with `E-MISSING-001`. No URL is fabricated. |
| **GSS 2022** | *Excluded* | **N/A** | **Excluded**: The GSS 2022 dataset is excluded from the primary analysis. Merging it with the Cyberbullying Survey to create a "synthetic cohort" was identified as methodologically invalid for testing interaction effects (see Methodological Rationale). |

**Critical Note on Dataset Fit**:
The analysis is restricted to the Cyberbullying Survey. The assumption that GSS 2022 contains PCL-5 items is **discarded**. The pipeline will verify the presence of PCL-5 items in the Cyberbullying Survey. If missing, the analysis proceeds with Depression (CES-D) and Anxiety (GAD-7) only.

### 2.2 Data Cohort Construction
Instead of a "Synthetic Cohort" created by matching two datasets, the analysis uses a **Single Analysis Cohort**:
1.  **Source**: One CSV file (`cyberbullying_survey.csv`).
2.  **Selection**: Rows are selected based on the presence of valid data for all required variables (Harassment, Support, Outcomes).
3.  **Cleaning**: Missing values in critical predictors are handled via listwise deletion (as per FR-001/Edge Cases).
4.  **Outcome**: A single DataFrame (`analysis_cohort.csv`) containing rows from the Cyberbullying Survey, ready for interaction analysis.

**Why not PSM?**
Propensity Score Matching (PSM) is designed to balance covariates between treatment and control groups *within* a single population. Using it to merge two independent populations (GSS vs. Cyberbullying) to estimate an interaction effect creates a sample where the "Treatment" (Harassment) is perfectly collinear with the "Source" (Dataset). This renders the interaction term unidentifiable. Therefore, PSM is **not** used in this revised plan.

### 2.3 Variable Operationalization
*   **Social Support**: Derived from survey items (e.g., "How often do you feel you have someone to turn to?"). Scored per standard guidelines.
*   **Harassment Exposure**:
    *   *Binary*: 1 if any harassment reported, 0 otherwise.
    *   *Continuous*: Sum of frequency/severity items.
*   **Mental Health Outcomes**:
    *   **Depression**: CES-D total score (sum of items, reverse coding applied where necessary).
    *   **Anxiety**: GAD-7 total score.
    *   **PTSD**: PCL-5 total score (if available in the Cyberbullying dataset; otherwise excluded).

## 3. Statistical Methodology

### 3.1 Primary Analysis (Interaction Models)
*   **Model**: Robust Linear Regression (OLS with Heteroskedasticity-Consistent Standard Errors - HC3).
*   **Equation**: $Y_i = \beta_0 + \beta_1 Support_i + \beta_2 Harass_i + \beta_3 (Support_i \times Harass_i) + \gamma Demographics_i + \epsilon_i$
*   **Inference**:
    *   **Interaction Term**: $\beta_3$ represents the buffering effect.
    *   **Confidence Intervals**: 95% bias-corrected bootstrapped CIs with a sufficient number of resamples to account for non-normality and small sample bias in interaction terms.
    *   **Multiple Comparisons**: Benjamini-Hochberg procedure applied to the family of p-values (one per outcome: Depression, Anxiety, PTSD) to control False Discovery Rate (FR-007).

### 3.2 Sensitivity Analysis
*   **Scenario A (Exposure Definition)**: Re-run models replacing binary `Harass` with continuous `HarassSeverity`. Compare $\beta_3$ magnitude and significance.
*   **Scenario B (Platform Stratification)**: If `Platform Type` data exists, split the dataset by platform (e.g., Twitter, Reddit) and re-run the primary model. Report if the buffering effect varies by platform.

### 3.3 Power & Sample Size Considerations
*   **Assumption**: The Cyberbullying Survey dataset will yield N > 300.
*   **Limitation**: The analysis is powered to detect large effect sizes (d ≥ 0.5). Small interaction effects may be underpowered.
*   **Collinearity**: `SocialSupport` and `HarassmentExposure` may be correlated. Variance Inflation Factor (VIF) will be checked. If VIF > 5, interaction interpretation will be qualified as descriptive rather than causal.

## 4. Computational Feasibility
*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
*   **Strategy**:
    *   Use `pandas` for data manipulation (memory efficient for < 1M rows).
    *   Use `statsmodels` for OLS (CPU native, no GPU required).
    *   Use `scipy` for bootstrapping (parallelizable across multiple cores if needed, with a sufficient number of resamples to ensure robust inference for modern CPUs).
    *   **No GPU**: All methods are CPU-tractable. No deep learning or large LLMs are used.
    *   **Time Limit**: Estimated runtime < 30 minutes for full pipeline (scoring + 3 models + 1000 bootstrap iterations).

## 5. Risk Management
*   **Risk**: Missing PCL-5 items in the Cyberbullying Survey.
    *   *Mitigation*: Code checks for PCL-5 variables. If missing, logs `E-MISSING-001` and proceeds with Depression/Anxiety only.
*   **Risk**: Dataset file is missing.
    *   *Mitigation*: The pipeline relies on local `data/raw/cyberbullying_survey.csv`. If missing, it halts with a clear error `E-MISSING-001`.
*   **Risk**: Non-convergence of the robust linear regression model.
    *   *Mitigation*: Catch convergence error, log parameters, and attempt fallback with standard OLS.