# Research: Detecting Statistical Power Drift in Replicated Studies

## Problem Statement

The primary research question is whether reported statistical power estimates in published replication studies exhibit a systematic temporal decline, indicating a drift toward lower-powered replications over time. This analysis must isolate the temporal trend in power from the underlying trends in its constituent inputs (effect size, sample size) to avoid tautological conclusions.

## Methodology Overview

The analysis follows a four-stage approach to ensure statistical rigor and avoid mathematical tautologies:
1.  **Power Re-estimation**: Calculate post-hoc power for each study using reported effect sizes (Cohen's *d* or odds ratio) and sample sizes, assuming α=0.05 two-tailed.
2.  **Residualization**: Compute `expected_power` based on the deterministic relationship between power, effect size, and sample size using a pilot OLS model. Calculate `power_residual = power_est - expected_power`. This step removes the variance in power explained by the inputs, leaving only the unexplained component.
3.  **Drift Modeling**: Fit a Linear Mixed-Effects Model (LMM) with `power_residual` as the outcome and `year` as the **only** fixed effect (plus random intercepts for `field` and `original_study_id`).
    *   **Correction**: We do **not** include `effect_size` and `sample_size` as covariates in this model. Since `power_residual` is already orthogonal to these inputs by construction, including them again creates perfect collinearity and renders the `year` coefficient uninterpretable.
    *   **Conditional Covariate**: If T011b detects significant shifts in field composition over time, `field_proportion` may be added as a covariate to control for selection bias.
4.  **Robustness & Aggregation**: Validate the drift slope via permutation tests (shuffling `year`), input permutation tests (shuffling inputs), sensitivity analysis (sweeping α), and cross-field aggregation (DerSimonian-Laird).

## Dataset Strategy

The analysis relies on the OSF (Open Science Framework) Replication Project data, which contains the necessary metadata (year, effect size, sample size, field) for a large number of replication studies.

| Dataset Name | Source URL | Load Method | Notes |
| :--- | :--- | :--- | :--- |
| OSF Replication Metadata | `https://huggingface.co/datasets/osc/replication_project/resolve/main/replication_data.parquet` | `datasets.load_dataset("parquet", data_files=...)` | Primary source. **Must contain** `year`, `effect_size`, `sample_size`, `field`. |

**Data Availability Note**: The primary dataset is open and directly downloadable via Hugging Face. No access-gated data is required. The pipeline includes **T011d** to explicitly verify that the downloaded dataset contains the required columns (`year`, `effect_size`, `sample_size`, `field`). If `field` is missing, the pipeline halts with a clear error, preventing the use of secondary or mismatched datasets.

**Streaming Strategy**: Given the ~7 GB RAM constraint, the dataset will be loaded using `streaming=True` if the file size exceeds 100MB, or processed in chunks to calculate summary statistics (mean, variance) without loading the entire dataset into memory at once.

## Statistical Rigor

### Multiple Comparison Correction
The primary test involves a single fixed effect (`year`) in the LMM. However, the sensitivity analysis (sweeping α) and permutation tests involve multiple comparisons.
- **Method**: For the sensitivity sweep (3 alpha levels), the Bonferroni correction will be applied to the family-wise error rate (α_adj = 0.05/3 ≈ 0.0167).
- **Permutation**: The empirical p-value from a sufficient number of permutations is inherently corrected for the specific test statistic distribution.

### Sample Size & Power (MDES)
- **Dynamic Calculation**: **T010** will perform a pilot analysis on a [deferred] sample to calculate the **Minimum Detectable Effect Size (MDES)** for the `year` slope based on the observed residual variance.
- **Limitation**: The analysis is observational and relies on the existing corpus of replication studies. The "sample size" is the number of available replication records (N).
- **Power Justification**: The report will explicitly state the effective N and the calculated MDES. If the MDES is larger than the expected drift, the study will be flagged as underpowered.

### Causal Inference & Assumptions
- **Observational Nature**: The study is purely observational. The analysis frames findings as *associations* between calendar year and residual power, not causal claims about why drift occurs.
- **Identification Strategy**: The LMM controls for `field` and `original_study_id` heterogeneity. The `year` coefficient represents the drift in power *after* accounting for changes in effect size and sample size (via residualization).
- **Measurement Validity**: Power estimates are derived using standard formulas (Cohen, 1988) for two-tailed tests. The validity of these estimates depends on the accuracy of the reported effect sizes and sample sizes in the source dataset.

### Predictor Collinearity
- **Resolution**: The model `power_residual ~ year + (1|field) + (1|original_study_id)` **excludes** `effect_size` and `sample_size` as predictors.
- **Rationale**: `power_residual` is defined as the difference between observed power and the power predicted by the inputs. By construction, it is orthogonal to the inputs. Including the inputs again would result in coefficients of zero (or numerical noise) and perfect multicollinearity. The drift is tested in the *residual* component, which represents the unexplained variation in power over time.

## Compute Feasibility

### CPU-First Strategy
- **LMM Fitting**: `statsmodels` mixed linear model fitting is CPU-bound but tractable for N [deferred] on 2 cores.
- **Permutation Test**: 10,000 permutations of 5,000 rows is computationally intensive but feasible on a 2-core CPU within 6 hours if implemented efficiently (vectorized operations, no Python loops for shuffling).
- **Fallback**: If memory or time limits are exceeded, the permutation count will be reduced to [deferred], and the result flagged as "approximate" (per FR-004).

### GPU Escape Hatch
- **Not Required**: This project does not involve deep learning, transformers, or large-scale matrix factorizations that require CUDA. All methods (LMM, permutation, sensitivity) have faithful CPU forms. No GPU escape hatch is planned.

## Decision/Rationale

- **Dataset**: The OSF Replication Project is the only verified open dataset containing the necessary variables (year, effect size, sample size, field) at scale.
- **Model**: LMM is chosen over OLS to handle the hierarchical structure of the data. The model formula is corrected to `power_residual ~ year` to avoid tautology.
- **Validation**: The dual approach (parametric LMM + non-parametric permutation) ensures robustness against model misspecification.
- **Feasibility**: The CPU-first approach is sufficient for the dataset size and complexity. No synthetic stand-ins are needed.
