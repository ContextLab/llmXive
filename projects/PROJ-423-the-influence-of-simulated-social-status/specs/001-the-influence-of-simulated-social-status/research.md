# Research: The Influence of Simulated Social Status on Risk-Taking Behavior

## Dataset Strategy

The primary data source will be either a simulated dataset based on meta-analytic effect sizes or an aggregated dataset from separate randomized trials. Given the lack of publicly available datasets with a fully crossed factorial design (status level × observed behavior), simulation and/or meta-analysis are necessary to establish a rigorous basis for testing the causal hypothesis.

## Decision/Rationale: Compute & Data Availability

**CPU-first.** All methods will be implemented to run on the CPU-only GitHub Actions runner with a multi-core configuration and sufficient RAM for execution. This includes data preprocessing, mixed-effects model fitting using `statsmodels`, sensitivity analysis with bootstrapping (`scipy`), and report generation. If simulation is chosen, the dataset size will be limited to a manageable scale given available computational resources., potentially employing chunking or sampling techniques if necessary.

**Kaggle auto-offload (not required).** GPU acceleration is not anticipated to be needed for this project, as all analyses can be performed efficiently on the CPU. The computational demands are primarily driven by statistical calculations rather than complex model training/inference. Therefore, we do *not* plan to utilize the Kaggle auto-offload feature.

## Statistical Rigor

The analysis will employ a mixed-effects regression model (logistic or linear) with appropriate random effects terms to account for individual differences and potential correlations within subjects. Multiple comparison correction (Bonferroni) will *always* be applied during post-hoc analyses, regardless of whether the initial results are significant. Sample size calculations (deferred until data simulation/meta-analysis parameters are finalized) will be conducted to ensure sufficient statistical power.

## Edge Case Handling

*   **No variance in `status_level`**: The system will detect this condition and halt with an error message, as it would invalidate the experimental design.
*   **Continuous `risk_taking` measure**: The model family will automatically switch from binomial to gaussian (linear mixed model) based on data type detection.
*   **Memory limitations during bootstrapping**: If memory constraints are encountered during bootstrap resampling for confidence intervals, asymptotic standard errors will be used as a fallback and a warning will be logged.

## Verified Datasets

The primary data source is either simulated data or aggregated studies; the listed resources serve only as examples of potential datasets to inform schema development and preprocessing techniques.
