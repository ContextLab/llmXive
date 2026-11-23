# Research Configuration & Methodology Notes

## Project: Ambient Temperature Influence on Moral Decision Speed

This document outlines specific configuration choices, sampling strategies, and
methodological assumptions made during the implementation of the research pipeline.

### Anderson-Darling Test Configuration

The Anderson-Darling (AD) test is used to assess the normality of model residuals
(specifically from the Linear Mixed-Effects model on log-transformed response times).
Given the potential size of the Moral Machine dataset, running the AD test on the
entire set of residuals can be computationally expensive.

To balance statistical rigor with computational efficiency, we employ a stratified
random sampling approach for the AD test.

**Configuration Parameters:**

* **`AD_TEST_SEED`**: `42`
 * **Source**: Defined in `code/config.py`.
 * **Purpose**: Ensures that the random sampling of residuals is reproducible
 across different runs of the pipeline. This seed is consistent with the
 global `RANDOM_SEED` used elsewhere in the project.

* **`AD_TEST_FRACTION`**: `0.1` (10%)
 * **Source**: Defined in `code/config.py`.
 * **Purpose**: Specifies that 10% of the total residuals will be selected
 for the normality test.
 * **Rationale**:
 1. **Computational Efficiency**: The AD test has a complexity of O(N log N).
 On datasets with millions of observations, a full test can be prohibitively
 slow. Sampling 10% significantly reduces runtime while maintaining the
 validity of the test for large N.
 2. **Statistical Power**: For large sample sizes (N > 30), the power of
 goodness-of-fit tests to detect deviations from normality is high.
 A sample of 10% from a large dataset (e.g., >100k residuals) still
 yields N > 10k, which is more than sufficient to detect meaningful
 non-normality.
 3. **Representativeness**: The sampling is performed using a fixed seed,
 ensuring the subset is a representative random draw of the full residual
 distribution, minimizing bias.

**Implementation Details:**

The sampling logic is implemented in `code/modeling.py` (specifically in the
`run_primary_modeling` or diagnostic functions). It proceeds as follows:

1. Extract all residuals from the fitted model.
2. Use `numpy.random.default_rng(AD_TEST_SEED)` to generate a random permutation
 of indices.
3. Select the first `int(len(residuals) * AD_TEST_FRACTION)` indices.
4. Pass the sampled residuals to the Anderson-Darling test function (e.g.,
 `scipy.stats.anderson`).
5. Log the resulting statistic and critical values to `results/logs/ad_test.json`.

**Limitations:**

If the dataset is extremely small (e.g., < 1000 residuals), the 10% sample might
be too small for a reliable test. In such edge cases, the code defaults to using
the entire residual set if the calculated sample size is less than 100, overriding
the fraction to ensure statistical validity.

### Data Validation & Source Integrity

* **Moral Machine Dataset**: Sourced from Kaggle. Validated for column presence
 (latitude, longitude, timestamp, response_time, country) and checksum integrity.
* **ERA5 Reanalysis**: Sourced via CDS API. Validated for global coverage and
 physical plausibility of temperature values.

### Confound Handling

* **Indoor/Outdoor**: Addressed via urban/rural proxy classification using
 geospatial data (T028h).
* **Baseline Reaction Time**: Acknowledged as a limitation due to the lack of
 individual baseline measures in the raw dataset. The model includes random
 intercepts for `participant_id` to account for individual variation in
 average response speed.

### Future Work

* Investigate non-linear temperature effects using spline bases.
* Incorporate physiological arousal proxies if available in future data releases.
* Expand the AD test to other model diagnostics (e.g., heteroscedasticity checks).