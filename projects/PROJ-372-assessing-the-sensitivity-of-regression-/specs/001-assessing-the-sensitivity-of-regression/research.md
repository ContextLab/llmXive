# Research: Assessing the Sensitivity of Regression Coefficients to Dataset Subset Selection

## Research Question & Hypothesis

**Question**: Does the severity of OLS assumption violations (heteroscedasticity, outliers) interact with collinearity to modify the **rate of convergence** of regression coefficient stability as sample size increases?

**Hypothesis**: The **slope** of the relationship between sample size and coefficient variance (convergence rate) will be significantly steeper (indicating slower convergence/higher sensitivity) in datasets with "High" violation severity AND high collinearity, compared to datasets with low violations.

## Dataset Strategy

We will utilize **verified, open, programmatic datasets** with **continuous outcomes** suitable for OLS regression. We require numerical datasets with at least 5 predictors and 1 continuous outcome.

**Selected Datasets (from Verified List):**

1.  **California Housing**: `https://huggingface.co/datasets/satishgunjal/california_housing/resolve/main/california_housing.csv`
    *   *Relevance*: Continuous target (`MedHouseVal`). Standard benchmark for regression.
    *   *Usage*: Used to test collinearity in geographic features.
2.  **Concrete Compressive Strength**: `https://huggingface.co/datasets/UCI_Concrete/resolve/main/concrete_data.csv` (or verified UCI mirror)
    *   *Relevance*: Continuous target (`compressive_strength`). Good candidate for heteroscedasticity testing.
3.  **Wine Quality (Red)**: `https://huggingface.co/datasets/UCI_Wine/resolve/main/winequality-red.csv`
    *   *Relevance*: Continuous target (`quality` - treated as continuous for regression).
4.  **Yacht Hydrodynamics**: `https://huggingface.co/datasets/UCI_Yacht/resolve/main/yacht_hydrodynamics.csv`
    *   *Relevance*: Continuous target (`residual`).
5.  **Energy Efficiency (Cooling)**: `https://huggingface.co/datasets/UCI_Energy/resolve/main/ENB2012_data.csv`
    *   *Relevance*: Continuous target (`cooling_load`).

**Exclusion Note**: 
- **UCI HAR** (Human Activity Recognition): **Excluded**. Categorical outcome (activity label).
- **Yelp Review Full**: **Excluded**. Ordinal outcome (star ratings).
- **SMS Spam**: **Excluded**. Binary outcome.
- **Cybersecurity/Fable-5**: **Excluded**. Synthetic/LLM-generated, potential lack of ground truth.

**Data Acquisition Method**:
- Use `datasets.load_dataset` with `streaming=True` where possible.
- For `.csv` files, use `pandas.read_csv` with chunking if size > 7GB.
- **Checksumming**: MD5 hash calculated immediately after download.

## Methodology

### Phase 1: Ingestion & Profiling (FR-001, FR-002)
1.  **Load**: Fetch dataset. Drop non-numerical columns. Handle missing values via mean imputation (logged).
2.  **Standardize**: Z-score all predictors.
3.  **Profile**:
    *   **Collinearity**: Compute Condition Number of the design matrix $X$ (full dataset).
    *   **Heteroscedasticity**: Run Breusch-Pagan test on the full dataset. Record $\chi^2$ stat and p-value.
    *   **Outliers**: Compute Cook's Distance for all rows. Record max value.
4.  **Classify**: Assign "Violation Severity" (Low/Medium/High) based on BP p-value thresholds (swept in FR-006).

### Phase 2: Resampling & Convergence Estimation (FR-003, FR-004)
1. **Tiers**: Define 5 sample size tiers (e.g., [deferred], [deferred], [deferred], [deferred], [deferred] of N). *Specific percentages deferred to implementation based on N.*
2.  **Loop**: For each dataset and tier:
    *   Generate 200 random subsets (seeded).
    *   Filter subsets: Skip if $n < 10 \times p$ (predictors).
    *   Fit OLS: `statsmodels.OLS(y, X).fit()`.
    *   Catch `LinAlgError`: Log singularity, skip.
    *   Store coefficients and sample size.
3.  **Aggregate**: For each dataset, fit a **local** regression of `log(Coefficient Variance)` vs `log(Sample Size)` to estimate the **convergence slope** ($\beta_{local}$). This slope represents the sensitivity of the estimator to sample size.

### Phase 3: Meta-Analysis (FR-005, FR-006, FR-007)
1.  **Model**: Fit a **Hierarchical Linear Model (HLM)**:
    *   **Level 1 (Subset/Tier)**: $Y_{ij} = \beta_{0i} + \beta_{1i} (\text{SampleSize}_{ij}) + \epsilon_{ij}$
    *   **Level 2 (Dataset)**: 
        *   $\beta_{0i} = \gamma_{00} + \gamma_{01}(\text{CondNum}_i) + \gamma_{02}(\text{Severity}_i) + u_{0i}$
        *   $\beta_{1i} = \gamma_{10} + \gamma_{11}(\text{CondNum}_i) + \gamma_{12}(\text{Severity}_i) + \gamma_{13}(\text{CondNum}_i \times \text{Severity}_i) + u_{1i}$
    *   Where $Y_{ij}$ is the log-variance of coefficients for dataset $i$ at tier $j$.
    *   The key parameter is $\gamma_{13}$ (interaction effect on the slope).
2.  **Interaction**: Test $\gamma_{13}$. If significant, violations amplify the sensitivity of stability to sample size.
3.  **Sensitivity**: Repeat classification with BP p-value cutoffs {0.01, 0.05, 0.10} and report variance in $\gamma_{13}$.
4.  **Framing**: Report as associational.

## Statistical Rigor & Feasibility

- **Multiple Comparisons**: We will apply Bonferroni correction for the 5 sample size tiers if testing each independently, but the primary interaction test is global.
- **Power**: 10 datasets $\times$ 1000 fits = 10,000 observations for the HLM. This provides high power to detect the interaction effect on the slope.
- **Collinearity**: The predictor "Condition Number" is a measure of collinearity. We acknowledge that high condition numbers imply unstable coefficients, but the *interaction* with violation severity on the *convergence rate* is the novel test.
- **Circularity Avoidance**: The outcome is the **convergence slope** (a property of the estimator's behavior across subsets), not the raw variance (which is a function of the full matrix). This tests if violations *modify* the rate of learning, avoiding the tautology of "predicting variance from geometry".
- **CPU Feasibility**: OLS on 100k rows is trivial on CPU. The bottleneck is the loop overhead. [deferred] fits should take < 2 hours on 2 cores.
- **Baseline Comparison**: We compare the "Interaction Model" against an "Intercept-Only Null Model" and a "Main-Effects-Only Model" using AIC/BIC. We **do not** compare against a theoretical OLS variance formula (which assumes homoscedasticity and is invalid for high-violation datasets).

## Controlled Synthetic Generation (Fallback)

If real datasets lack sufficient variance in predictors (e.g., all have Low Collinearity), we will generate synthetic data using a **Controlled Generator**:
1.  Generate $X$ with controlled correlation structure (to vary Condition Number).
2.  Generate $\epsilon$ with controlled variance function (to vary BP/Cook's D).
3.  Ensure $X$ and $\epsilon$ are generated independently to avoid spurious correlations.
4.  Log the generation process to prove independence.

## Decision/Rationale

- **Why HLM?** To properly model the nested structure and test cross-level interactions with sufficient power (N=1000+).
- **Why Convergence Slope?** To avoid circularity. The slope measures sensitivity, not raw variance.
- **Why exclude HAR/Yelp?** They have categorical/ordinal outcomes unsuitable for OLS.
- **Why no theoretical baseline?** The theoretical OLS variance formula is invalid for heteroscedastic data. We use data-driven null models.
