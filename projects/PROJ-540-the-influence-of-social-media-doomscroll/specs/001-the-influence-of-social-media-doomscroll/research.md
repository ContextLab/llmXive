# Research: The Influence of Social Media "Doomscrolling" on Anticipatory Anxiety

## Dataset Strategy

The analysis requires a dataset containing:
1. **Predictor**: `news_exposure_freq` (Frequency of negative news consumption).
2. **Outcome**: `anxiety_score` (Anticipatory or General Anxiety).
3. **Covariates**: `baseline_anxiety`, `age`, `gender`, `social_media_engagement`.

### Verified Sources & Feasibility Analysis

**Constraint**: Only URLs from the `# Verified datasets` block may be used.

| Dataset Name | Verified URL | Variable Availability Assessment | Feasibility |
|:--- |:--- |:--- |:--- |
| **GSS (Parquet)** | ` | **CRITICAL MISMATCH**: This URL points to a text summarization dataset (`mini-xlsum`), not the General Social Survey (GSS). It contains text documents, not survey variables like `news_exposure_freq` or `anxiety_score`. | **NOT FEASIBLE** |
| **GSS (Parquet)** | ` | **CRITICAL MISMATCH**: Likely a synthetic or text-based dataset. Does not contain psychological survey variables. | **NOT FEASIBLE** |
| **GSS (Parquet)** | ` | **CRITICAL MISMATCH**: Same as above. | **NOT FEASIBLE** |
| **YouGov** | *No verified source found* | The spec mentions YouGov as a potential source. However, the verified block explicitly states "NO verified source found". | **BLOCKING** |

### Decision & Rationale

**Status**: **BLOCKING DATA GAP**.

The `# Verified datasets` block provided for this project contains URLs that point to **text summarization datasets**, not the **General Social Survey (GSS)** or other psychological survey data required to measure `news_exposure_freq` and `anxiety_score`.

1. **Variable Mismatch**: The available URLs do not contain the necessary columns.
2. **No Verified Alternative**: The block explicitly states "YouGov: NO verified source found".
3. **Action**: The implementation **cannot** proceed with data ingestion until a verified URL for a dataset containing the required psychological variables is provided.

**Proposed Mitigation (for Plan Execution)**:
The pipeline will include **Phase 0: Data Availability Check**. If the verified sources do not match the required schema, the system will **HALT** with a clear error: `ERROR: Dataset schema mismatch. Verified sources do not contain required variables.`

*Note: If a valid GSS dataset URL were available, the strategy would be to download it, map GSS variable codes to the schema, and proceed.*

## Statistical Methodology

### Primary Analysis
- **Model**: Multiple Linear Regression (OLS).
- **Equation**: $Y_{anxiety} = \beta_0 + \beta_1 X_{news} + \beta_2 X_{baseline} + \beta_3 X_{age} + \beta_4 X_{gender} + \epsilon$
- **Causal Validity**: This is an **observational study**. No causal claims will be made. The model estimates **associational effects** while controlling for confounders.
- **Assumptions**: Linearity, Homoscedasticity, Normality of Residuals, No Multicollinearity.
- **Correction**: No multiple comparison correction for the primary hypothesis.

### Construct Validity & Coupling Check
- **Requirement**: `baseline_anxiety` and `anxiety_score` must be derived from **distinct instruments** or **time points** (e.g., Trait vs. State).
- **Failure Mode**: If they are the same scale (e.g., pre/post same test), the model is invalid due to mathematical coupling. The pipeline will halt if this is detected.

### Robustness Check
- **Subset**: Top 25th percentile of `social_media_engagement`.
- **Condition**: **Unconditional**. The check is run regardless of the correlation between engagement and news. The correlation value is reported as a descriptive statistic only.
- **Metric**: Compare $\beta_1$ sign and $p$-value between full and subset models to assess effect heterogeneity.

### Power & Sample Size
- **Calculation**: For 5 predictors, medium effect size ($f^2=0.15$), $\alpha=0.05$, Power=0.80, required $N \approx 130$.
- **Hard Stop**: $N < 130$.
- **Warning**: $130 \le N < 200$ (Low Power).
- **Limitation**: Acknowledgement that this is an observational study; causality cannot be inferred.

## Ethical & Validity Considerations
- **Construct Validity**: If `anticipatory_anxiety` is missing, `general_anxiety` will be used as a proxy, with a flag (FR-008).
- **Mathematical Coupling**: Ensure `baseline_anxiety` and `anxiety_score` are distinct measures. If they are the same scale, the model is invalid.
- **Collinearity**: Check VIF. If VIF > 10 for `baseline_anxiety` vs `anxiety_score`, the model is unstable.
