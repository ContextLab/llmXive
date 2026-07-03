# Research: The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

## Dataset Strategy

### Verified Datasets Search
The specification (FR-001, US-1) requires a dataset containing:
1.  **RSES** (Rosenberg Self-Esteem Scale)
2.  **INCOM** (Iowa-Netherlands Comparison Orientation Measure)
3.  **Longitudinal** (Pre/Post) self-esteem data.
4.  **N ≥ 100** participants.
5.  **VR Exposure** condition or proxy.

**Search Results against Verified List:**
The `# Verified datasets` block provided for this project contains:
-   `AND` (cat kingdom, invoices, knights): Irrelevant.
-   `RSES` (Avneet Mockups): These are **mockups** (UI designs), not survey data. They do not contain participant scores or longitudinal data.
-   `INCOM` (Adult Census, Income): These are **income** datasets, not psychological comparison measures.
-   `VR-specific`: **NO verified source found.**
-   `MICE` (Protein, Mice): Biological data, irrelevant.
-   `ALL` (Math, Chat): Irrelevant.

**Conclusion:**
No real-world public dataset exists in the verified list that satisfies the requirement for RSES + INCOM + Longitudinal Pre/Post + VR exposure.
**Action:** The system MUST trigger **FR-011**: Synthetic Data Generation.
**Ground Truth & Data Generation Process (DGP):**
To ensure the parameter recovery test is a valid stress test and not a tautology, the synthetic generator will implement the following DGP:
-   **N**: 200 (to ensure robustness).
-   **Covariates**:
    -   `pre_self_esteem`: Normal(μ=20, σ=5).
    -   `comparison_tendency`: Normal(μ=0, σ=1).
    -   `avatar_condition`: Binary (0=Control, 1=Idealized) OR Continuous (Uniform[0, 10] for intensity).
-   **Error Term**: $\epsilon \sim \text{Normal}(0, \sigma=2.5)$ (Injected noise to simulate real-world variance).
-   **Data Generation Equation (ANCOVA)**:
    $$ \text{PostSelfEsteem} = \beta_0 + \beta_1(\text{PreSelfEsteem}) + \beta_2(\text{Condition}) + \beta_3(\text{Comparison}) + \beta_4(\text{Condition} \times \text{Comparison}) + \epsilon $$
    -   **Ground Truth Parameters**:
        -   $\beta_0 = 10$
        -   $\beta_1 = 0.6$ (Stability of self-esteem)
        -   $\beta_2$ represents the main effect of condition.
        -   $\beta_3$ represents the main effect of comparison tendency (Main effect of comparison tendency)
        -   $\beta_4 = 0.2$ (**Target Interaction Effect**)
-   **Missingness Mechanism**:
    -   **Type**: Missing At Random (MAR).
    -   **Mechanism**: Probability of missing `post_self_esteem` is modeled as a function of `pre_self_esteem` (lower pre-scores slightly more likely to miss), ensuring MICE assumptions hold.
 - **Rate**: Target [deferred] missingness in key variables.
    -   **MNAR Sensitivity**: A secondary sensitivity analysis will simulate MNAR (missingness depends on the unobserved `post_self_esteem`) to test robustness.
-   **Label**: "Pipeline Validation Only".

### Data Loading Strategy
-   **Path A (Real Data):** If a real dataset were found, load via `pandas.read_csv` or `datasets.load_dataset`.
-   **Path B (Synthetic):** Use a deterministic generator in `code/data/download.py` with a fixed random seed (e.g., `42`).
-   **Variable Mapping**:
    -   `self_esteem_pre` -> `pre_score` (Covariate)
    -   `self_esteem_post` -> `post_score` (Outcome)
    -   `avatar_condition` -> `condition` (0/1 or continuous)
    -   `comparison_tendency` -> `incom_score`

## Statistical Methodology

### Primary Model (ANCOVA)
**Correction for Mathematical Coupling:**
To avoid the spurious correlation inherent in regressing change scores on baseline, the primary analysis will use **Analysis of Covariance (ANCOVA)**:
$$ \text{PostSelfEsteem} = \beta_0 + \beta_1(\text{PreSelfEsteem}) + \beta_2(\text{Condition}) + \beta_3(\text{Comparison}) + \beta_4(\text{Condition} \times \text{Comparison}) + \epsilon $$

**Implementation Details:**
-   **Library**: `statsmodels.api` (OLS).
-   **Preprocessing**:
    1.  **Missingness**: Apply MICE (IterativeImputer) if missingness < 20% in key variables. Exclude rows with > 20% missingness (FR-013).
    2.  **Normalization**: If `avatar_condition` is binary, ensure 0/1 coding.
-   **Assumption Checks (FR-004)**:
    1.  **Normality**: Shapiro-Wilk test on residuals (Target: p > 0.05) **AND** Visual Q-Q Plot inspection.
    2.  **Homoscedasticity**: Breusch-Pagan test (Target: p > 0.05) **AND** Visual Residual vs. Fitted plot inspection.
    3.  **Collinearity**: Variance Inflation Factor (VIF) for predictors (Target: VIF < 5). If VIF ≥ 5, report as descriptive joint effect, no independent claims.
    4.  **Robustness**: If assumptions are violated, re-run with **Robust Standard Errors** (HC3) and report those results.

### Robustness & Sensitivity (FR-005, FR-006, FR-007)
1.  **Bootstrap Resampling**:
 - **Iterations**: [deferred] (exact).
    -   **Metric**: Stability of $\beta_4$ (interaction).
    -   **Success**: CI width variance < 0.01.
2.  **Multiple Testing Correction**:
    -   Apply **Holm-Bonferroni** correction to p-values of main effects and interaction.
3.  **Sensitivity Analysis**:
    -   **Threshold Sweep**: Test p < 0.05 and p < 0.10.
    -   **Parameter Recovery (Synthetic Only)**: Calculate Bias = $|\hat{\beta}_ - 0.2|$.
        -   **Fail Condition**: Bias > 0.05 (FR-011).
    -   **Imputation Sweep**: Test imputation limits across a range of low to moderate thresholds.
    -   **MNAR Sensitivity**: Simulate MNAR missingness (e.g., a non-negligible proportion of high-post-score participants missing) and compare parameter recovery. If Bias > 0.10 under MNAR, flag the pipeline as sensitive to missingness mechanism.

### Construct Validity Note
If the real data (if found) is binary (0/1) rather than continuous intensity, the interaction term tests if the *group difference* varies by comparison tendency. The plan explicitly acknowledges this as a limitation in construct validity regarding "exposure intensity" but proceeds as the best available proxy for the research question.

## Feasibility & Compute Constraints
-   **Hardware**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
-   **Constraints**:
    -   **No GPU**: All operations must be CPU-only.
    -   **Memory**: Synthetic data generation for N=200-500 is negligible. Bootstrap (sufficient iterations) on a small dataframe fits easily in RAM.
    -   **Time**: Linear regression and 1,000 bootstrap iterations on N=200 will complete in < 10 minutes. Well within the specified time limit.
-   **Library Pins**:
    -   `pandas`, `numpy`, `scipy`, `statsmodels` (CPU compatible).
    -   `scikit-learn` (for IterativeImputer).
    -   `matplotlib` (for visual diagnostics).
    -   Avoid `torch` unless strictly necessary (not needed for OLS).

## Risk Mitigation
-   **Risk**: Real data found but missing `INCOM`.
    -   **Mitigation**: Spec (FR-009) mandates synthetic generation if variables are missing.
-   **Risk**: Model assumptions violated (e.g., non-normal residuals).
    -   **Mitigation**: Report violation in `research.md` and `data-model.md`. Use Robust Standard Errors. Do not claim significance; report descriptive statistics and confidence intervals.
-   **Risk**: Collinearity (VIF ≥ 5).
    -   **Mitigation**: As per spec, frame as descriptive joint relationship, no independent causal claims.
-   **Risk**: MNAR missingness in real data.
    -   **Mitigation**: Sensitivity analysis (MNAR simulation) will quantify the potential bias.