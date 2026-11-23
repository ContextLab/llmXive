# Research: The Relationship Between Sleep Chronotype and Moral Judgement

## Research Question

Do individuals with later sleep chronotypes (evening types) exhibit systematically different patterns of moral judgement compared to earlier chronotypes (morning types), independent of acute sleep deprivation?

## Theoretical Background

- **Chronotype**: Defined by the Morningness-Eveningness Questionnaire (MEQ), a 19-item instrument developed by Horne and Östberg (1976) to assess circadian preference. Scores range from the minimum value (definite evening) to the maximum value (definite morning).
- **Moral Foundations**: Based on Moral Foundations Theory (Graham, Haidt, Nosek, 2009), measuring five domains: Care, Fairness, Loyalty, Authority, Sanctity.
- **Hypothesis**: Evening types may show distinct moral profiles, potentially influenced by circadian misalignment or social jetlag, even when controlling for acute sleepiness.
- **Theoretical Dependency**: Acute sleepiness is often a function of the mismatch between chronotype and sleep schedule (social jetlag). This theoretical dependency implies potential collinearity between `chronotype` and `acute_sleepiness`. The analysis will monitor Variance Inflation Factors (VIF) and report on this dependency. If VIF > 2, the dependency is reported descriptively, and independent effects are not claimed.

## Dataset Strategy & Data Collection Protocol

**Critical Finding**: No single verified public dataset contains all required variables (MEQ, MFQ, PSQI, Acute Sleepiness) simultaneously.
- **MEQ**: Available via `lighteval/me_q_sum` (Verified).
- **MFQ**: Available via `lukebruhns/identity-refusal-mfq2` (Verified).
- **PSQI / Acute Sleepiness**: No verified public source found.

**Decision**: The pipeline is designed as a **scientific tool** awaiting real data. It **cannot** validate the ANCOVA/MANCOVA statistical model using synthetic data, as this would produce mathematically meaningless results for the hypothesis "independent of acute sleep deprivation."

**Strategy**:
1.  **Unit Testing (Classification)**: A synthetic dataset with *known* labels will be generated solely to test the classification logic (FR-002, SC-001). This data is **not** used for ANCOVA.
2.  **Scientific Analysis**: The pipeline requires a real `data/raw/study_data.csv` provided by the user. If this file is missing, the statistical analysis phase is skipped, and the CI run passes with a "No Data" status.
3.  **Data Collection Protocol**: To enable the study, the following protocol is recommended for data collection:
    -   **Platform**: Prolific or Qualtrics Panel.
    -   **Measures**:
        -   MEQ (a standardized set of items, Horne & Östberg, 1976).
        -   MFQ (version, 200 items or short form if validated, Graham et al., 2009).
        -   PSQI (Global score).
        -   Acute Sleepiness: 24-hour sleep diary or actigraphy data (or validated self-report scale like KSS).
    -   **Inclusion**: PSQI ≤ 5 (chronic sleep quality) and valid acute sleepiness data.
    -   **Sample Size**: Target n ≥ 159 (based on a priori power analysis, f=0.25, α=0.05, power=0.80).

**Rationale**: This approach ensures scientific integrity. The pipeline is validated for *code correctness* (unit tests) and *statistical logic* (assumptions), but the *scientific results* are contingent on real data. No synthetic data is used to simulate the covariance structure for the ANCOVA, avoiding the fatal flaw of fabricating scientific evidence.

## Statistical Methodology

1.  **Chronotype Classification**:
    -   Thresholds: Morning (≥59), Evening (≤41), Intermediate (42-58).
    -   Handling Missing: Rows with missing MEQ or Acute Sleepiness are flagged `NA` and excluded from group analysis (FR-006).

2.  **Multivariate Analysis (MANCOVA)**:
    -   **Primary Test**: MANCOVA with `chronotype` as factor and `MFQ_care`, `MFQ_fairness`, `MFQ_loyalty`, `MFQ_authority`, `MFQ_sanctity` as dependent variables.
    -   **Covariates**: `PSQI`, `acute_sleepiness`, `age`, `sex`.
    -   **Statistic**: Hotelling's Trace.
    -   **Justification**: Controls for Type I error across correlated dependent variables and better captures the "pattern of judgement" than univariate tests alone.

3.  **Univariate Analysis (ANCOVA)**:
    -   **Condition**: Only performed if MANCOVA is significant.
    -   **Formula**: `MFQ_subscale ~ chronotype + PSQI + acute_sleepiness + age + sex`
    -   **Correction**: Bonferroni adjustment for 5 subscales (α_corrected = 0.01).
    -   **Assumptions Check**: Normality of residuals, Homogeneity of variance (Levene's test), Linearity.
    -   **Collinearity**: Variance Inflation Factor (VIF) calculated; must be < 2. If VIF > 2, the dependency between chronotype and acute sleepiness is reported descriptively, and independent effects are not claimed.

4.  **Effect Sizes**:
    -   Cohen's d for significant contrasts (Morning vs. Evening).
    -   95% Confidence Intervals.

5.  **Power & Sensitivity Analysis**:
    -   **Sensitivity for Effect Size**: Instead of post-hoc power (which is controversial), calculate the minimum effect size (f) detectable with [deferred] power given the observed sample size.
    -   **Threshold Sensitivity**: Sweep α_corrected across a range of small positive values to assess the robustness of significance decisions. This is a pre-specified robustness check, not a search for significance. The report will list the significance status for every subscale at each threshold.

## Compute Feasibility

-   **CPU-First**: All operations are lightweight statistical operations in R.
-   **Memory**: Estimated < 500 MB for n=1000.
-   **Time**: < 10 minutes for full pipeline on 2 CPU cores.
-   **GPU**: Not required.

## Decision/Rationale

-   **CPU vs GPU**: CPU is sufficient. No deep learning models are used.
-   **Data Strategy**: Use verified MEQ/MFQ sources for schema validation. **No synthetic data for ANCOVA.** The pipeline requires real data for scientific results. The CI runner will skip analysis if real data is missing, ensuring no fabricated results.
-   **MANCOVA vs ANCOVA**: MANCOVA is chosen as the primary test to address the "pattern" of judgement across correlated subscales, reducing Type I error risk. ANCOVA is a follow-up.
-   **Power Analysis**: Post-hoc power is rejected in favor of sensitivity analysis for effect size, which is more informative for interpreting non-significant results.
