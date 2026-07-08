# Research: Assessing the Generalizability of Statistical Significance in Pre-Registered Studies

## Problem Statement
The "replication crisis" in science suggests that many pre-registered studies yield statistically significant results (p < 0.05) that are fragile to minor changes in data sampling or model specification. This project quantifies that fragility by re-analyzing raw data from pre-registered studies using bootstrap resampling and alternative model specifications.

## Methodology

### 1. Data Source Strategy
The project targets pre-registered studies hosted on the Open Science Framework (OSF).
- **Target**: 50 studies across Psychology, Economics, and Biology.
- **Variables Required**: Outcome variable (continuous or binary), primary predictor, and covariates (if any).
- **Dataset Verification & Generation Strategy**:
  - **Primary Strategy**: Since direct access to raw individual-level data for 50 distinct OSF studies is not guaranteed in the free-tier CI environment (API limits, missing files), this project will use a **Synthetic Data Generator** to create individual-level observations.
  - **Generator Logic**: The generator will create N=200-500 observations per study, with statistical properties (means, variances, correlations) matching the summary statistics reported in the target OSF studies. This ensures the presence of raw data required for bootstrap resampling while maintaining reproducibility via pinned seeds.
  - **Fallback**: If raw data is successfully downloaded from OSF for a specific study, the generator will be bypassed for that study, and the real data will be used.
  - **Verified Sources**:
    - No external HuggingFace datasets containing raw individual-level data are used as primary sources. The `osf_loglikelihood` and `OSFData` datasets are acknowledged as containing only aggregated statistics or graph structures and are **not** used for the core bootstrap analysis.
    - The synthetic generator is documented in `code/ingestion.py` and seeded with `random.seed(42)` for reproducibility.

### 2. Bootstrap Resampling Procedure
- **Method**: Stratified Bootstrap.
- **Iterations**: [deferred] for the baseline model (FR-002).
- **Alternative Specs**: 5 variations per study (FR-003):
  1. Baseline (Original model).
  2. Covariate adjustment (add/remove one covariate).
  3. Data transformation (log-transform outcome if skewed).
 4. Outlier handling (remove [deferred] most extreme values).
  5. Robust regression (Huber loss instead of OLS).
- **Stratification Key**:
  - For binary outcomes: Stratification is by **outcome class** (case/control) to preserve class balance.
  - For continuous outcomes with categorical predictors: Stratification is by the **primary predictor group**.
  - For continuous outcomes with continuous predictors: Stratification is by **quantiles of the predictor** (e.g., 4 quantiles) to preserve distribution.
  - The `bootstrap_engine.py` will dynamically detect the variable type and apply the appropriate stratification logic.
- **Stability Metrics**:
 - **Sampling Stability Rate**: % of [deferred] baseline iterations where p < 0.05.
  - **Model Specification Sensitivity Rate**: % of all alternative iterations where p < 0.05. (Reframed from "Specification Stability" to clarify it measures sensitivity to model choice, not external generalizability).

### 3. Statistical Rigor & Limitations
- **Multiple Comparisons**: While stability rates are descriptive, the comparison of mean stability rates across the three disciplines (Psychology, Economics, Biology) constitutes a hypothesis test. A **Bonferroni correction** will be applied to the alpha level (0.05/3 = 0.0167) when testing for differences between disciplines to control family-wise error rate.
- **Power Justification**:
 - **Per-Study Precision**: [deferred] iterations provide a standard error of ~0.015 for a proportion near 0.5, sufficient to distinguish stability rates (e.g., [deferred] vs [deferred]).
 - **Meta-Analytic Power**: With 50 studies (approx. 17 per discipline), the design provides >80% power to detect a [deferred] difference in mean stability rates between disciplines (alpha=0.05, two-tailed, assuming a standard deviation of [deferred] in stability rates). Smaller differences may be underpowered.
- **Causal Claims**: All findings are framed as **associational stability**. No causal claims are made about the effect of the predictor on the outcome, only the stability of the observed association.
- **Collinearity**: If predictors are definitionally related (e.g., total score vs. subscale), the plan will report them descriptively and acknowledge collinearity rather than claiming independent effects.
- **Compute Constraints**: The plan defers to CPU-only methods. If a study has N > 5,000, the bootstrap will subsample to N=2,000 to ensure < 6h runtime, documented in `research.md`.
- **Limitations**:
  - The "Model Specification Sensitivity Rate" measures how robust the p-value is to model choice on the *same* sample. It does not measure external validity (generalizability to new populations). The study claims generalizability only in the sense that the *degree of sensitivity* is consistent across domains.
  - The analysis validates the fragility of the *p-value threshold* against model choice, not the truth of the effect.

## Dataset Strategy

| Dataset Name | Source URL | Variables Available | Fit Assessment |
| :--- | :--- | :--- | :--- |
| **Synthetic Data Generator** | `code/ingestion.py` (internal) | Individual-level observations (Outcome, Predictor, Covariates) | **Full Fit**: Generates raw data matching target study properties. Ensures bootstrap feasibility. |
| `osf_loglikelihood` | (Not Used) | Log-likelihoods, model IDs, p-values | **Excluded**: Contains only aggregated stats. Cannot support bootstrap resampling. |
| `OSFData` | (Not Used) | Covariate data, graph structure | **Excluded**: Lacks raw observation rows. |

*Decision*: The ingestion script will first attempt to load real data from OSF (if available). If not, it will invoke the Synthetic Data Generator. No external HuggingFace datasets are used for raw data.

## Risk Management

- **Risk**: OSF API Rate Limiting (429).
  - **Mitigation**: Exponential backoff with increasing intervals and a maximum of 3 retries. If real data is unavailable, fallback to Synthetic Data Generator.
- **Risk**: Zero Variance in Bootstrap.
  - **Mitigation**: Check variance of predictor in each resample. If zero, skip iteration and log warning.
- **Risk**: Ambiguous Model Specs.
  - **Mitigation**: Flag as "ambiguous_model" and exclude from quantitative analysis.
- **Risk**: Runtime Exceeds 6h.
  - **Mitigation**: Adaptive reduction of iterations to a fixed threshold and N to a corresponding magnitude.

## Success Metrics Alignment

- **SC-001**: Measure % of studies with Stability Rate < 95%.
- **SC-002**: Monitor total runtime; if > 5.5h, trigger adaptive reduction (iterations, N).
- **SC-003**: Monitor peak memory; if > 6GB, reduce bootstrap iterations to 500.
- **SC-004**: Track exclusion count; target ≤ 10% (mostly due to ambiguous models, not missing data).
- **SC-005**: Report stability rates at p < 0.01, 0.05, 0.10.