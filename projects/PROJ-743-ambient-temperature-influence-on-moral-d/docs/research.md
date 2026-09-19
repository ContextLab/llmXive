# Research Configuration and Methodology Notes

## Anderson-Darling Test Configuration

The Anderson-Darling (AD) test is used to assess the normality of model residuals, a key assumption for the validity of p-values in the linear mixed-effects models employed in this study (User Story 2).

### Sampling Strategy

Given the large scale of the Moral Machine dataset combined with the ERA5 reanalysis data, the full residual set may contain millions of observations. Running the AD test on the entire set is computationally expensive and often unnecessary for large samples where the test is overly sensitive to trivial deviations.

To balance statistical rigor with computational efficiency, we implement a stratified sampling approach for the AD test:

1. **Sample Fraction (`AD_TEST_FRACTION`)**: Set to `0.1` (10%). We randomly sample 10% of the residuals for the test. This size is sufficient to maintain statistical power while significantly reducing runtime.
2. **Random Seed (`AD_TEST_SEED`)**: Set to `42`. This ensures that the specific subset of residuals used for the test is reproducible across different runs of the pipeline, allowing for consistent validation of model assumptions.

These parameters are defined in `code/config.py` and are used by the modeling module (`code/modeling.py`) during the diagnostic phase (Task T028j).

### Justification

- **Reproducibility**: The fixed seed guarantees that the same subset is tested every time, making the validation step deterministic.
- **Efficiency**: Reducing the input size by 90% accelerates the normality check without compromising the ability to detect significant non-normality in the error distribution.
- **Robustness**: If the sampled subset fails the AD test, it is highly indicative that the full residual set also deviates from normality, prompting a review of the model specification or the need for robust standard errors.