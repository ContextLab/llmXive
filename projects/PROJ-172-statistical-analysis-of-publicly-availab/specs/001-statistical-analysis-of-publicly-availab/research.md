# Research: Statistical Analysis of Publicly Available Sports Data for Predictive Modeling

## 1. Problem Statement & Hypothesis

**Hypothesis**: Advanced baseball metrics (wOBA, BABIP) provide statistically significant predictive power for game outcomes (Home Win/Loss) beyond traditional metrics (Batting Average, ERA) when controlling for temporal shifts.

**Methodology**:
1.  **Data Ingestion**: Fetch or simulate play-by-play data for a multi-year historical period.
2.  **Feature Engineering**: Compute traditional and advanced metrics per team per game.
3.  **Modeling**: Train LR, RF, XGB with 5-fold time-series CV.
4.  **Validation**: Diebold-Mariano test on CV scores; Sensitivity analysis on thresholds; Nested Model Comparison for marginal gain.
5.  **Reporting**: Explicitly distinguish between "Pipeline Validation" (synthetic) and "Empirical Findings" (real).

## 2. Dataset Strategy

### Verified Datasets & Fallback Logic

The "Verified datasets" block provided for this project **does not** contain verified URLs for the specific Retrosheet or Baseball-Reference raw play-by-play data required by the spec.
*   **Constraint**: Per the output contract, I **cannot** invent or guess a URL for Retrosheet/BR.
*   **Strategy**: The `data_loader.py` will attempt to fetch from canonical public URLs. If unavailable (common in CI due to rate limiting or blocking), the system will generate a **statistically faithful synthetic dataset**.
*   **Synthetic Generation Logic**:
 * Generate a large-scale dataset of game records spanning multiple seasons, comprising [deferred] games per season.
    *   Simulate team strengths using a Poisson distribution for runs scored.
    *   Derive "Advanced Metrics" (wOBA, BABIP) from simulated play outcomes using standard formulas (e.g., wOBA weights: [qualitative weight]*BB + 0.72*HBP + 0.89*1B + 1.27*2B + 1.62*3B + 2.10*HR).
    *   **Validation**: Ensure the synthetic data's mean/variance for wOBA and BABIP aligns with historical MLB averages (e.g., wOBA ~ moderate offensive value, BABIP is expected to approximate a stable baseline value.).
*   **Critical Warning**: The synthetic generator creates a **circular relationship** between features and labels. The target (game outcome) is derived from the same underlying run-scoring logic that defines wOBA/BABIP. Therefore, **synthetic data CANNOT validate the hypothesis** that advanced metrics add value beyond traditional ones in the real world. It can only validate the *code's ability to calculate metrics* and the *statistical test logic*. If real data is unavailable, the empirical hypothesis is marked "Untested".

**Dataset Table**:

| Dataset Name | Source Type | URL (Verified or Fallback) | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| MLB Play-by-Play (2000-2022) | Primary (Target) | *Canonical Retrosheet/BR URLs (Unverified in block)* | **Fallback to Synthetic** | If fetch fails, generate synthetic data with verified statistical properties. **Empirical hypothesis untested in this mode.** |
| wOBA/BABIP Definitions | Reference | *FanGraphs/BR definitions* | N/A | Logic implemented in code; no external data fetch. |
| XGBoost / CPU Models | Library | *PyPI* | **OK** | `xgboost` CPU wheel. |

> **Note on Data Fit**: The spec requires variables for wOBA, BABIP, and game outcomes. The synthetic fallback ensures these variables exist. If the spec had required a variable *not* derivable from play-by-play (e.g., "player mood"), the plan would have flagged a fatal mismatch. Here, all required variables are mathematically derivable from simulated play events.

## 3. Statistical Rigor & Methodology

### 3.1 Multiple Comparisons & Family-Wise Error
*   **Issue**: Comparing 3 models × 2 feature sets = 6 comparisons.
*   **Correction**: Apply **Bonferroni correction** or **Holm-Bonferroni** to the p-values of the Diebold-Mariano tests **only for the primary hypothesis** (Advanced vs. Traditional on the best model).
*   **Hierarchical Strategy**: 
    1.  **Primary**: Compare Advanced vs. Traditional feature sets on the best-performing model (XGBoost) using a paired test. This is the core scientific question.
    2.  **Exploratory**: Compare model architectures (LR vs. RF vs. XGB) without strict family-wise error correction, as this is secondary to the feature-set question.
*   **Threshold**: $\alpha_{adj} = 0.05 / 1 = 0.05$ for the primary comparison. Model comparisons use $\alpha = 0.05$ unadjusted.

### 3.2 Sample Size & Power
*   **Data Volume**: A large-scale dataset of synthetic games or a substantial collection of real games (if available).
*   **Power**: With >20,000 samples, power to detect small effect sizes (Cohen's d > 0.1) is >0.99.
*   **Acknowledgement**: If the real dataset is small (<1,000 games) due to scraping failure, the report will explicitly flag "Low Power" and rely on the synthetic validation for the pipeline logic only.

### 3.3 Causal Inference & Observational Framing
*   **Framing**: The data is observational. No random assignment of "advanced metrics" exists.
*   **Claim Limitation**: All conclusions will be framed as **"associational predictive improvement"**. The plan will explicitly state: *"We cannot claim that using advanced metrics causes better predictions in a causal sense; we only observe that models utilizing these features exhibit higher out-of-sample accuracy."*
*   **Collinearity & Marginal Gain**: Advanced metrics (wOBA) are often highly correlated with traditional metrics (AVG). To isolate the *marginal* predictive gain of wOBA, we will use:
    *   **Nested Model Comparison**: Fit Model A (Traditional features) and Model B (Traditional + Advanced features). Compare their log-likelihoods using a Likelihood Ratio Test (LRT) to determine if the addition of advanced metrics significantly improves the model fit.
    *   **Permutation Importance**: Shuffle the advanced metrics in the trained model and measure the drop in performance. This isolates the specific contribution of the advanced features.
    *   **Reporting**: If VIF > 5, we will report the combined predictive power but explicitly state that "independent effects cannot be isolated" due to collinearity.

### 3.4 Measurement Validity
*   **wOBA/BABIP**: Definitions follow standard FanGraphs/BR formulas.
*   **Validation**: The synthetic generator will be validated against known MLB league averages (e.g., Recent MLB seasons exhibit a weighted on-base average (wOBA) clustering around a league-average baseline.) to ensure the "data" is realistic enough for the statistical tests to hold meaning.

### 3.5 Utility Function & Cost Matrix (FR-006)
*   **Requirement**: Explicitly define a utility function or cost matrix for sensitivity analysis.
*   **Implementation**: We will define a cost matrix where:
    *   Cost of False Negative (missing a win) = a non-zero penalty reflecting the strategic loss of a successful outcome.
    *   Cost of False Positive (predicting a win that doesn't happen) = a defined monetary penalty.
*   **Sweep**: The sensitivity analysis will sweep thresholds [0.0, 1.0] and calculate the **Expected Utility** at each point: $E[U] = (TP \times Cost_{TP}) - (FP \times Cost_{FP}) - (FN \times Cost_{FN})$.
*   **Output**: The report will include the optimal threshold that maximizes expected utility, not just the threshold that maximizes accuracy.

## 4. Compute Feasibility (CPU-Only CI)

*   **Memory**: Data subset to a size compatible with available RAM in parquet format.
*   **CPU**: XGBoost and Scikit-Learn are highly optimized for CPU. 5-fold CV on 20k-600k rows is feasible within 6 hours.
*   **No GPU**: No CUDA dependencies. `xgboost` will be installed from the CPU wheel.
*   **Sampling**: If the full 23-year dataset exceeds RAM during the initial load, the pipeline will sample a subset of the data for the initial test run, then run the full set if memory permits.

## 5. Computational Task Ordering

1.  **Download/Generate**: `data_loader.py` (Fetch or Synthetic Gen).
2.  **Clean & Engineer**: `feature_engineering.py` (Compute wOBA/BABIP, Split, Completeness Check).
3.  **Train**: `models.py` (5-fold CV, Hyperparameter Tuning, Nested Models).
4.  **Evaluate**: `evaluation.py` (Test set metrics, Diebold-Mariano, Sensitivity, Completeness Report).
5.  **Sensitivity**: `evaluation.py` (Threshold sweep with utility function).
6.  **Report**: Generate JSON/CSV and plots.
7.  **Hash & State**: `checksum_manifest.py` updates state.

## 6. Data Completeness Check (SC-005)

*   **Requirement**: Measure data validity against a completeness rate of ≥ 95% for all required variables.
*   **Implementation**: After feature engineering, a script will calculate the percentage of non-null values for every required column (predictors, outcomes, covariates).
*   **Threshold**: If completeness < 95%, the pipeline will fail with an error: "Data Completeness Check Failed: Required variables have >5% missing values."
*   **Reporting**: The final report will include a "Data Completeness" section listing the completeness rate for each variable.