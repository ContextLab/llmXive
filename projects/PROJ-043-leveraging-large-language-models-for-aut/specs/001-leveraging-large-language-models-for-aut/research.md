# Research: Leveraging LLMs for Automated Code Refactoring

## Research Question

Do structural characteristics of Python functions (Lines of Code, Nesting Depth, Parameter Count, PEP-8 Adherence, Docstring Presence) predict the magnitude of *relative* improvement in code quality (Cyclomatic Complexity, Pylint Score) when refactored by a Large Language Model (WizardCoder-Python-13B)?

## Methodology

### Study Design
This is an **observational study**. We do not randomize the "treatment" (refactoring) across different structural types; rather, we observe the natural variation in function structures and measure the resulting improvement. Consequently, findings will be framed as **associational relationships** (predictors of improvement), not causal claims.

### Data Strategy

#### Dataset Selection
The specification requests the "BigCode dataset".
- **Primary Source**: `bigcode/the-stack-dedup` via `datasets.load_dataset`.
- **Verification Constraint**: The prompt's "Verified datasets" block states "BigCode: NO verified source found". The implementation will attempt the canonical HuggingFace path. **Critical**: If this path is inaccessible or fails validation, the pipeline will **halt with a clear error**. This ensures strict adherence to FR-001 and prevents hidden distribution shifts that would occur with a silent fallback to `codeparrot-clean`.
- **Sampling Strategy**: Random sampling of up to 400 attempts to retrieve valid Python functions. The pipeline stops early if a sufficient number of valid, parseable functions are found. If a sufficient number of valid functions are not found after 400 attempts, the study halts with a warning.
- **Streaming**: To respect the available RAM limit, the dataset will be loaded in streaming mode (`streaming=True`) and iterated over to extract functions until the sample size is met.

#### Variables
- **Predictors (X)**:
  - `loc`: Lines of Code (integer).
  - `nesting_depth`: Maximum nesting depth (integer).
  - `param_count`: Number of function parameters (integer).
  - `pep8_score`: PEP-8 adherence score (float, from `pylint`).
  - `has_docstring`: Boolean (1 if docstring present, 0 otherwise).
- **Outcomes (Y)**:
  - `complexity_original`: Cyclomatic complexity (from `radon`).
  - `complexity_refactored`: Cyclomatic complexity (from `radon`).
  - `pylint_score_original`: Pylint score (0-10 scale, higher is better) from `pylint`.
  - `pylint_score_refactored`: Pylint score (0-10 scale) from `pylint`.
  - `pylint_warning_count_original`: Integer count of warnings/errors (lower is better).
  - `pylint_warning_count_refactored`: Integer count of warnings/errors.
- **Delta Metrics (Δ)**:
  - `Delta_Complexity = Complexity_original - Complexity_refactored` (Positive = improvement).
  - `Delta_Score = PylintScore_refactored - PylintScore_original` (Positive = improvement).
  - `Delta_Warning_Count = Warning_Count_original - Warning_Count_refactored` (Positive = improvement).
  - **Relative Improvement (Outcome for Regression)**:
    - `Relative_Improvement_Complexity = Delta_Complexity / Complexity_original` (Used to avoid circularity where `Complexity_original` is part of the predictor set).
    - `Relative_Improvement_Score = Delta_Score / PylintScore_original` (If `PylintScore_original` > 0).
- **Null Baseline**: An identity transformation (original code copied) is generated. Since `baseline` == `original`, `Delta_Null` is theoretically 0. This serves as a conceptual anchor for a **one-sample t-test**, not a paired comparison against a variable.

### Statistical Analysis Plan

1.  **Data Cleaning**: Exclude unparseable functions. Handle `NaN` values from failed refactoring attempts.
2.  **Multicollinearity Check**: Calculate Variance Inflation Factors (VIF) for all predictors. **Do not drop variables**. Instead, fit a **Ridge Regression** model (L2 regularization) to handle collinearity while retaining all predictors. Report the ridge coefficients and the regularization parameter (alpha).
3.  **Regression Modeling**:
    - **Dependent Variable (Continuous)**: `Relative_Improvement_Complexity` and `Relative_Improvement_Score`.
    - **Dependent Variable (Count)**: `Delta_Warning_Count`.
    - **Model (Continuous)**: Ridge Regression with k-fold cross-validation to estimate Mean Adjusted R².
    - **Model (Count)**: Generalized Linear Model (GLM) with a **Negative Binomial link function** to handle overdispersion and non-normality of count data.
    - **Final Model**: Train on the full dataset. Report mean coefficients from folds.
    - **Robustness**: Use robust standard errors (HC3) for Ridge Regression.
4.  **Hypothesis Testing**:
    - **One-Sample t-test**: Test if the mean `Delta_Complexity` (and `Delta_Score`, `Delta_Warning_Count`) is significantly greater than **zero**. This tests the hypothesis that the LLM provides improvement over the identity baseline (which is 0).
    - **Global F-test**: Assess overall model significance (p < 0.05).
    - **Multiple Comparisons**: Apply Bonferroni correction if testing multiple delta metrics.
5.  **Power & Sensitivity Analysis**:
    - **Sample Size**: Target N=200.
    - **Sensitivity Analysis**: If results are non-significant, calculate the **Minimum Detectable Effect Size (MDES)** for N=200 at [deferred] power to interpret the power limitation honestly. This addresses the risk of Type II error due to unknown effect sizes.

### Statistical Rigor & Assumptions

- **Circularity Mitigation**: By using `Relative_Improvement` as the outcome, we avoid the mathematical dependency where `Original_Complexity` (a predictor) is part of the `Delta_Complexity` outcome.
- **Causal Framing**: As an observational study, we cannot claim the structural traits *cause* the improvement. We can only claim they *predict* it.
- **Measurement Validity**: `radon` and `pylint` are standard industry tools. We assume they are valid proxies for "readability" in this context.
- **Collinearity**: LOC and Nesting Depth are often correlated. Ridge Regression is used to handle this without dropping variables.
- **API Reliability**: The study assumes the HuggingFace Inference API is stable. Retry logic and caching are implemented to mitigate transient failures.
- **Methodological Correction (FR-005)**: The spec mandates a "paired t-test". Since the baseline is an identity transformation (Delta=0), a paired t-test is trivial. We implement a **one-sample t-test against zero**, which is the correct statistical test for this design.

## Decision / Rationale

- **CPU-First**: All static analysis (`radon`, `pylint`) and statistical modeling (`statsmodels`, `scikit-learn`) are CPU-tractable. The LLM is accessed via API.
- **Dataset Strategy**: The plan uses the canonical BigCode path. A silent fallback is rejected to preserve reproducibility and avoid distribution shifts.
- **Scaling**: The sampling limit and 200-function target are designed to fit within the 6-hour GitHub Actions runtime window, accounting for API latency and batching.

## Limitations

- **Dataset Access**: If the BigCode dataset is inaccessible, the study cannot proceed (hard failure).
- **API Latency**: High latency or rate limits may reduce the number of valid samples below the minimum threshold.
- **Observational Nature**: Correlation does not imply causation.
- **Metric Validity**: Static metrics may not fully capture human-perceived code quality.
- **Power**: N=200 may be underpowered for small effect sizes; sensitivity analysis will be reported.