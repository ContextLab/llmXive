# Research: Simulated Social Comparison on Self-Esteem in VR

## Dataset Strategy

### Real Dataset Search
Per **FR-001** and **FR-009**, the system will query HuggingFace Datasets, OpenML, and Open Science Framework for datasets containing:
1.  **RSES** (Rosenberg Self-Esteem Scale)
2.  **INCOM** (Iowa-Netherlands Comparison Orientation Measure)
3.  **Longitudinal** data (Pre/Post self-esteem scores)
4.  **N ≥ 100** participants

**Verified Datasets Check**:
The provided "Verified datasets" block was reviewed for relevant sources:
-   **RSES**: The provided URLs (`Rsesystem2/Avneet_Mockups...`) point to mockups/zip files, likely not structured psychological survey data with longitudinal scores.
-   **INCOM**: The provided URLs (`adult-census-income`, `nfcorpus`) are unrelated to psychological comparison measures.
-   **VR-specific**: The block explicitly states: "NO verified source found".
-   **MICE**: The provided URLs are protein/gene datasets, not psychological.

**Conclusion**: No verified dataset in the provided list contains the specific combination of RSES, INCOM, and longitudinal self-esteem data with N ≥ 100.
**Action**: The system will proceed to **Synthetic Data Generation** (FR-011) as the primary data source. This ensures the pipeline can be tested against known ground-truth parameters (interaction β = 0.2).

### Synthetic Data Generation Strategy
Since real data is unavailable, a synthetic dataset will be generated with the following properties:
-   **N**: 100 to 500 participants (configurable, default 200 to ensure power).
-   **Variables**:
    -   `participant_id`: Unique identifier.
    -   `avatar_condition`: Continuous variable representing exposure intensity (0.0 to 1.0). **Note**: This operationalization is a methodological choice for the synthetic path to maximize power and test linearity. It does not claim that real-world "exposure to idealized avatars" is inherently continuous. A **Non-Linearity Sensitivity Check** (quadratic term) will be added to the analysis to ensure the linear assumption does not mask theoretical threshold effects.
    -   `comparison_tendency`: Continuous score from INCOM (simulated normal distribution).
    -   `selfesteem_pre`: Baseline self-esteem (RSES score).
    -   `selfesteem_post`: Post-exposure self-esteem.
    -   `selfesteem_change`: Derived as `post - pre`.
-   **Ground Truth Model**:
    $$ \text{Change} = \beta_0 + \beta_1(\text{Condition}) + \beta_2(\text{Tendency}) + \beta_3(\text{Condition} \times \text{Tendency}) + \epsilon $$
    -   $\beta_1$ (Main Effect): -0.3 (Idealized avatars lower self-esteem).
    -   $\beta_2$ (Moderator): 0.1 (High comparers generally more sensitive).
    -   $\beta_3$ (Interaction): **0.2** (As per FR-011; high comparers suffer more).
    -   $\epsilon$: Normal noise.
-   **Missingness**: Artificially introduce a moderate level of missingness (MCAR) to test MICE (FR-002). Additionally, simulate **MAR** (Missing At Random) and **MNAR** (Missing Not At Random) scenarios to validate the robustness of MICE under different missingness mechanisms, addressing the limitation of testing only on MCAR.

## Statistical Analysis Plan

### Primary Model
A linear regression model will be fitted using `statsmodels`:
$$ \text{selfesteem\_change} \sim \text{avatar\_condition} + \text{comparison\_tendency} + \text{avatar\_condition}:\text{comparison\_tendency} $$

### Assumption Validation (FR-004)
1.  **Normality**: Shapiro-Wilk test on residuals. Target: $p > 0.05$.
2.  **Homoscedasticity**: Breusch-Pagan test. Target: $p > 0.05$.
3.  **Multicollinearity**: Variance Inflation Factor (VIF). Target: VIF < 5 for all predictors.

### Missingness Mechanism Diagnostic
To address the gap in validating MICE for real data where the mechanism is unknown:
1.  **Little's MCAR Test**: Performed on real data to test the null hypothesis that data is Missing Completely At Random.
2.  **Sensitivity Analysis**: If data is not MCAR, a pattern-mixture model sensitivity analysis will be conducted to assess how MNAR assumptions affect the interaction coefficient.

### Robustness & Sensitivity (FR-005, FR-006, FR-007)
1.  **Bootstrap Resampling**: 1000 iterations to generate confidence intervals for the interaction term ($\beta_3$).
2.  **Error Correction**: Bonferroni or Holm-Bonferroni correction applied if multiple hypotheses (e.g., testing main effects + interaction) are reported.
3.  **Threshold Sweeps**: Sensitivity analysis varying p-value thresholds (0.05, 0.1) and imputation limits.
4.  **Parameter Recovery**: For synthetic data, calculate Bias = $|\hat{\beta}_3 - 0.2|$. This is the **primary validation metric** for the synthetic path.

### Power Analysis & Success Criteria (SC-005)
**CRITICAL DISTINCTION BY PATH**:

1.  **Real Data Path (Empirical)**:
    *   **Post-hoc Power Analysis**: **MUST** be conducted using `statsmodels.stats.power` (F-test for linear regression).
    *   **Effect Size**: $f^2$ derived from the observed data.
    *   **Reporting**: If Power < 0.80, results are explicitly labeled **"Preliminary"**. The "Preliminary" label indicates that the study may be underpowered to detect the effect, not that the pipeline is flawed.

2.  **Synthetic Data Path (Methodological)**:
    *   **Post-hoc Power Analysis**: **NOT PERFORMED**.
    *   **Rationale**: Power analysis is methodologically invalid when the ground truth is known. The "success" of the synthetic path is determined by **Parameter Recovery Bias** (how close $\hat{\beta}$ is to the true $\beta=0.2$). If the pipeline cannot recover the known parameter, the sample size or method is flawed, regardless of p-values.
    *   **Reporting**: The "Preliminary" label is **not applicable** to the synthetic path. Instead, the report will state: "Pipeline Validation: Parameter Recovery Bias = X (Target < 0.05)". If Bias > 0.05, the pipeline is flagged as **flawed**.
    *   **Implication**: Synthetic data validates the *code and statistical engine*, not the *real-world hypothesis*.

## Compute Feasibility
-   **Hardware**: CPU-only (GitHub Actions Free Tier).
-   **Memory**: Synthetic data generation and OLS regression for N=500 require < 100 MB RAM.
-   **Time**: Bootstrap (1000 iters) on N=500 takes < 5 minutes on 2 CPUs. Total pipeline < 30 mins.
-   **Libraries**: `scikit-learn`, `statsmodels`, `pandas` are CPU-optimized and do not require CUDA.