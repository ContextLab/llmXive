# Research: The Impact of Self‑Compassion on Resilience to Negative Feedback

## 1. Scientific Context & Hypothesis

**Research Question**: Does self-compassion buffer the adverse psychological impact of negative feedback on anxiety, rumination, and self-efficacy?

**Hypothesis**: High levels of self-compassion will attenuate (moderate) the increase in anxiety and rumination, and the decrease in self-efficacy, following negative feedback compared to positive feedback.

**Theoretical Basis**:
- **Self-Compassion Scale (SCS)**: Neff (2003). Validated measure of self-kindness, common humanity, and mindfulness vs. self-judgment.
- **Anxiety**: State-Trait Anxiety Inventory (STAI-State). Spielberger et al.
- **Rumination**: Ruminative Responses Scale (RRS). Nolen-Hoeksema & Morrow.
- **Self-Efficacy**: General Self-Efficacy Scale (GSES). Schwarzer & Jerusalem.

## 2. Dataset Strategy

**Source**: The project relies on the "Feedback and Self-Compassion" dataset hosted on OSF.
**Verified URL**: `https://osf.io/3k9r2/` (Cited in Spec FR-001).
*Note: The "Verified datasets" block provided in the prompt lists OSF URLs, but the specific file `feedback_self_compassion.csv` is not explicitly listed in the "Verified datasets" block as a direct downloadable link. However, the Spec explicitly mandates downloading from `https://osf.io/3k9r2/`. The implementation will attempt to fetch the CSV from the OSF project page as per the Spec's FR-001. If the OSF project does not contain a direct CSV link matching the schema, the pipeline will halt with `DATA_UNAVAILABLE`.*

**Required Variables**:
- **Predictors**: `scf_total` (Self-Compassion), `feedback_cond` (Condition: Positive, Neutral, Negative).
- **Outcomes**: `stai_post`, `rrs_post`, `gse_post`.
- **Covariates**: `stai_pre`, `rrs_pre`, `gse_pre`, `age`, `gender`.
- **Optional**: Big Five personality traits.

**Validation Strategy**:
1.  **Schema Check**: Upon download, verify presence of all required columns.
2.  **Randomization Check**: Inspect dataset metadata/documentation for confirmation of experimental randomization. If absent, flag findings as "associational" (FR-017).
3.  **Completeness**: Check for missing values in key variables.
4.  **Ethical Protocol Check**: Verify presence of a 'debriefing_complete' flag or metadata note confirming pre-screening and debriefing protocols (Constitution Principle VII).

## 3. Methodological Approach

### 3.1 Data Preprocessing
- **Listwise Deletion**: Remove rows with missing SCS, baseline, or post-feedback scores (FR-002).
- **Encoding**: `feedback_cond` encoded as categorical (0=Positive, 1=Neutral, 2=Negative). Positive Feedback is the reference level.
- **Standardization**: Continuous predictors (SCS, baselines) z-scored.
- **Power & MDES**: Verify N ≥ 92.
    - If N < 92: Calculate the **Minimum Detectable Effect Size (MDES)** for the observed N (f², α=0.05, power=0.80) and report this value.
    - If power < 0.80 for the target f²=0.02: The report will explicitly state "Exploratory Findings" and provide the calculated MDES.
    - The analysis proceeds with a caveat, not an abort, to allow reporting of null results with appropriate context.

### 3.2 Statistical Modeling
- **Model Type**: ANCOVA (Linear Regression with covariates).
- **Equation**:
  $$Y_{post} = \beta_0 + \beta_1(Y_{pre}) + \beta_2(Age) + \beta_3(Gender) + \beta_4(SCS_{z}) + \beta_5(Feedback) + \beta_6(SCS_{z} \times Feedback) + \epsilon$$
- **Prerequisite: Homogeneity of Slopes**: Before interpreting the primary interaction, test the interaction between the covariate (`Y_pre`) and `Feedback`.
    - **If significant (p < 0.10)**: The ANCOVA assumption is violated. The primary ANCOVA interaction p-value is flagged as potentially biased. The pipeline **automatically runs a Johnson-Neyman technique** to identify the specific range of the moderator (SCS) where the feedback effect is significant. The Johnson-Neyman results are reported as the primary conclusion for that outcome.
    - **If not significant**: Proceed with the standard ANCOVA interaction test.
- **Primary Test**: Significance of $\beta_6$ (Interaction term) for each outcome.
- **Correction**: Holm-Bonferroni correction applied across the 3 primary outcomes (FR-011).
- **Simple Slopes Direction**: Compute and report the **simple slopes of the feedback condition** (effect of feedback) at low (-1 SD), mean, and high (+1 SD) levels of SCS. This confirms the *direction* of the buffering (i.e., that the slope of feedback is flatter for high SCS).
- **Robustness**:
    - **Standard Errors**: HC3 (Heteroskedasticity Consistent) (FR-009).
    - **Collinearity**: VIF calculated; >5 triggers warning (FR-013).
    - **Bootstrap**: **Case Resampling** (stratified by feedback condition) with 5,000 resamples for the interaction coefficient CI (FR-008). This preserves the experimental design structure.
    - **Convergence**: Assessed by stability of CI width.

### 3.3 Visualization
- **Simple Slopes**: Plot predicted values for -1 SD, Mean, +1 SD of SCS across feedback conditions for each outcome (FR-007).
- **Feedback Slopes**: Ensure plots clearly show the *effect of feedback* at different SCS levels to visualize the buffering.

### 3.4 Reporting
- **Output**: HTML report with sections for Data Cleaning, Descriptive Stats, Model Tables, Robustness, Visualizations, and Caveats (FR-010).
- **Caveats**: Explicit statement on causality (associational vs. causal), power limitations (with MDES if applicable), and protocol verification status.

## 4. Compute Feasibility Rationale
- **CPU Only**: `statsmodels` OLS, Johnson-Neyman implementation, and bootstrap are CPU-efficient. No deep learning.
- **Memory**: Dataset is expected to be < 100MB. Processing fits easily in available system memory.
- **Time**: 3 models + 3 Johnson-Neyman checks (if needed) + 3 bootstrap runs + 3 plots will complete in < 1 hour on a 2-core runner.

## 5. Decision Log
| Decision | Rationale |
| :--- | :--- |
| **Use ANCOVA** | Controls for baseline scores, increasing power and reducing error variance compared to ANOVA on change scores. |
| **Homogeneity Gate** | Ensures the ANCOVA interaction term is a valid estimator of the moderation of change. If violated, Johnson-Neyman provides a valid alternative. |
| **Johnson-Neyman** | Provides a robust alternative when homogeneity of slopes is violated, identifying the specific range of the moderator where effects are significant. |
| **Case Resampling Bootstrap** | Preserves the experimental design structure (stratified by condition) better than residual bootstrap in this context. |
| **MDES Calculation** | Provides a scientifically sound frame for null results when sample size is insufficient for the target effect size. |
| **Simple Slopes of Feedback** | Explicitly tests the direction of the buffering effect, not just the interaction significance. |
| **Associational Framing** | Mandatory if randomization metadata is missing to prevent causal overreach (Constitution Principle VII). |