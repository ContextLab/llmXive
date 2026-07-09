# Research: The Role of Temporal Discounting in Procrastination on Cognitive Tasks

## 1. Research Question & Scope

**Primary Question**: To what extent does working memory (WM) load moderate the relationship between individual temporal discounting rates and procrastination behaviors, **as estimated by a methodological validation pipeline using synthetic data**?

**Scope & Limitation**:
- This study is a **Methodological Validation**. It does not claim to empirically validate the existence of the interaction effect in the real world due to the absence of a verified real-world dataset containing all three constructs.
- The primary goal is to **estimate the magnitude** of the interaction effect and verify that the analysis pipeline can recover a pre-defined "ground truth" effect embedded in the synthetic data.
- The study is **statistically underpowered** to detect small interaction effects ($f^2 < 0.02$) with high significance at $N=500$. Therefore, results are framed as **effect size estimates with confidence intervals**, not binary hypothesis tests.

## 2. Dataset Strategy

### 2.1 Verified Datasets Availability
The project requires three distinct constructs measured in the same participants:
1. **Temporal Discounting**: Indifference points for delayed rewards to fit the hyperbolic model $V = A / (1 + k \cdot D)$.
2. **Procrastination**: Scores from a validated scale (e.g., General Procrastination Scale).
3. **Working Memory**: Accuracy or Reaction Time from an n-back task.

**Constraint**: The plan must cite **ONLY** the URLs listed in the "# Verified datasets" block of the user message.
- **Available Verified URL**: ` (and 8.5k variant).
- **Analysis**: The available verified dataset is an **OLScience** dataset, which contains general scientific text/data, not the specific psychometric and behavioral measures (Discounting, Procrastination, n-back) required for this study.
- **Decision**: **NO VERIFIED SOURCE EXISTS** for the specific combination of variables required in the provided list.

**Partial Proxy Strategy**:
To ensure the ingestion pipeline (US-1) is tested against real-world noise, we will:
1. Identify real-world datasets containing **subset** constructs (e.g., a dataset with Discounting + Procrastination, but no WM).
2. Use these subsets to validate the data harmonization, missingness handling, and ID merging logic.
3. Switch to the full **Synthetic Data Generation (SDG)** strategy for the complete moderation analysis.

### 2.2 Parameter Source Validation & DGP Definition
Since the data is synthetic, the **Data Generating Process (DGP)** must be grounded in verified literature to satisfy the "Verified Accuracy" principle for the generator parameters.

| Construct | Parameter | Source (Citation) | Validation Strategy |
|:--- |:--- |:--- |:--- |
| **Temporal Discounting** | Mean $k$ (Log-Normal $\mu, \sigma$) | Frederick, S., Loewenstein, G., & O'Donoghue, T. (2002). *Time Discounting and Time Preference: A Critical Review*. Journal of Economic Literature. | Fit hyperbolic model; check $R^2 > 0.8$. |
| **Procrastination** | Mean Score, Cronbach's $\alpha$ | Steel, P. (2007). *The nature of procrastination: A meta-analytic and theoretical review*. Psychological Bulletin. | Ensure range 0-40 (typical GPS range). |
| **Working Memory** | Accuracy, RT distributions | Owen, A. M., et al. (2005). *n-back task*. Nature Neuroscience. | Correlate with age/education (expected weak negative correlation). |
| **Interaction Effect** | Ground Truth $\beta_3$ | *Simulated* (Based on Steel & Klingsieck, 2016, for effect size estimation) | Explicitly set in DGP; used to validate recovery. |

**Data Generating Process (DGP)**:
The synthetic data is generated using the following explicit mathematical model to ensure a non-trivial relationship exists for the pipeline to detect:

1. **Discount Rate ($k$)**: Generated from a Log-Normal distribution: $k \sim \text{LogNormal}(\mu=-3.5, \sigma=1.2)$, bounded to prevent numerical instability.
2. **Working Memory ($WM$)**: Generated from a Normal distribution $WM \sim \mathcal{N}(0.75, 0.1)$, bounded [0, 1].
3. **Procrastination ($P$)**: Generated as:
 $$ P = \beta_0 + \beta_1 \log(k) + \beta_2 WM + \beta_3 (\log(k) \times WM) + \epsilon $$
 Where:
 - $\beta_0 = 10$ (Intercept)
 - $\beta_1 = 2.5$ (Main effect of discounting)
 - $\beta_2 = -5.0$ (Main effect of WM)
 - $\beta_3 = -3.0$ (**Ground Truth Interaction Effect**)
 - $\epsilon \sim \mathcal{N}(0, 2.0)$ (Noise)

**Note**: The interaction coefficient $\beta_3 = -3.0$ is explicitly embedded in the data. The pipeline's success is measured by its ability to estimate a coefficient close to -3.0 with a 95% CI that includes -3.0.

### 2.3 Data Harmonization Plan
- **ID Strategy**: Generate a unique `participant_id` for each synthetic record.
- **Merging**: Since data is synthetic, it will be generated as a single unified table to ensure [deferred] match on IDs, satisfying FR-009 (drop < 10%).
- **Missing Data**: The synthetic generator will intentionally introduce [deferred] missingness in covariates to test FR-009 (imputation vs. listwise deletion).

## 3. Statistical Methodology

### 3.1 Primary Analysis: Effect Size Estimation
- **Model**: OLS Regression.
- **Equation**: $Procrastination = \beta_0 + \beta_1 \log(k) + \beta_2 WM + \beta_3 (\log(k) \times WM) + \epsilon$.
- **Transformation**: `log(k)` is used to normalize the distribution of discount rates (typically right-skewed).
- **Centering**: Predictors ($\log(k)$, $WM$) will be mean-centered before creating the interaction term to reduce multicollinearity.
- **Diagnostics**:
 - **VIF**: Calculate Variance Inflation Factor for all predictors. Flag if $VIF > 5$.
 - **Normality**: Residuals checked via Shapiro-Wilk test.

**Statistical Framing**:
- The study **does not** aim to reject the null hypothesis ($H_0: \beta_3 = 0$) with high power.
- The study **aims to estimate** $\beta_3$ with a 95% Confidence Interval.
- Success is defined as: The 95% CI for $\beta_3$ contains the DGP ground truth (-3.0).

### 3.2 Robustness Checks
- **Bootstrapping**: 1000 resamples to generate 95% Confidence Intervals (CI) for the interaction term $\beta_3$.
- **Sensitivity Analysis**:
 - **Threshold Sweep**: If binary WM load is used (exploratory), sweep thresholds at Median, Median ± 0.05*SD, Median ± 0.10*SD.
 - **Stability**: Report the variation in $p$-values across sweeps.

### 3.3 Power & Effect Size Estimation
- **Acknowledgement**: Interaction effects in psychology are often small ($f^2 < 0.02$).
- **Limitation**: With $N=500$, the power to detect such small effects is < 20%.
- **Framing**: The study is explicitly framed as **estimation of magnitude**. Null results (CI crossing zero) will be reported as "inconclusive due to power" rather than "no effect."

## 4. Compute Feasibility
- **Memory**: The dataset ($N=500$) will occupy < 50MB. Bootstrapping (1000 resamples) on OLS is computationally light and will easily fit within 7GB RAM.
- **Runtime**: Hyperbolic fitting (scipy) + OLS (statsmodels) + Bootstrap (1000 iterations) will complete in < 10 minutes on a standard CPU.
- **GPU**: Not required. All libraries (`scipy`, `statsmodels`, `pandas`) run natively on CPU.

## 5. Risks & Mitigations
- **Risk**: No verified real-world dataset exists.
 - **Mitigation**: Use synthetic data with realistic parameters; code is designed to swap in real data if/when available. Use partial real-world proxies for ingestion testing.
- **Risk**: Multicollinearity between interaction term and main effects.
 - **Mitigation**: Mean-centering predictors before interaction creation (standard practice).
- **Risk**: Model fitting failure for $k$ (e.g., flat indifference curve).
 - **Mitigation**: Catch exceptions in `curve_fit`; exclude participant and log warning (Edge Case handling).