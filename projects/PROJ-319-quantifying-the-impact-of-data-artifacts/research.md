# Research Findings: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

## Executive Summary

This study quantifies the bias introduced by Gaussian noise and pixel saturation on measurements of planetary nebula morphology, specifically ellipticity and asymmetry. Using synthetic data with known ground truth, we derived calibration functions to correct for these biases. Key findings include:
- Noise significantly biases ellipticity measurements, with bias increasing linearly with noise level.
- Saturation inflates asymmetry measurements, with a strong positive correlation.
- Calibration functions successfully reduce residual bias to non-significant levels.

## Methodology

### Data Generation
- **Synthetic Nebulae**: Generated 50 synthetic planetary nebulae using Gaussian profiles with central stars. [UNRESOLVED-CLAIM: c_9e1def18 — status=not_enough_info] Ground-truth ellipticity and asymmetry were recorded.
- **Artifacts Injected**:
 - **Noise**: Gaussian noise at levels 0.01, 0.05, 0.10.
 - **Saturation**: Clipping fractions from 0.00 to 0.50 in 0.05 increments.

### Metrics
- **Ellipticity**: Calculated using second-order moments.
- **Asymmetry**: Calculated using the Conselice (2003) A-statistic with robust centering.

### Statistical Analysis
- **Regression**: Linear regression with Bonferroni correction to link artifact magnitude to bias.
- **Power Analysis**: Post-hoc check to verify n=50 achieves ≥80% power for observed effect sizes.
- **Cross-Validation**: Train-test split to ensure calibration functions generalize.

## Results

### Noise-Induced Bias on Ellipticity
- **Trend**: Bias increases linearly with noise level (σ).
- **Regression**: Significant slope (p < 0.05) indicating noise systematically inflates ellipticity.
- **Correction**: Derived linear model reduces residual bias to near-zero.

### Saturation-Induced Bias on Asymmetry
- **Trend**: Bias increases with saturation fraction.
- **Regression**: Significant positive slope (p < 0.05) confirming saturation inflates asymmetry.
- **Correction**: Polynomial model (selected via AIC) effectively corrects bias.

### Calibration Functions
- **Ellipticity Model**: Linear correction based on noise level.
- **Asymmetry Model**: Polynomial correction based on saturation fraction.
- **Validation**: Residual bias after correction is statistically non-significant.

### Power Analysis
- **Sample Size**: n=50 images.
- **Power**: ≥80% for observed effect sizes (Cohen's d).
- **Limitations**: Documented in `data/validation/power_analysis_report.md`.

## Validation

- **Synthetic Validation**: Quantitative validation confirms calibration functions reduce bias.
- **Real HST Validation**: Qualitative validation using real HST images (NGC 7009, NGC 6543) confirms morphology preservation. See `data/validation/validation_report.md`.

## Limitations

- **Sample Size**: n=50 may limit generalizability to extreme artifact levels.
- **Synthetic Data**: Ground truth is based on idealized models; real nebulae may exhibit more complex structures.
- **Power Analysis**: If power < 80%, limitations are documented but pipeline continues.

## Conclusion

Data artifacts (noise and saturation) introduce significant, systematic bias in planetary nebula morphology measurements. Calibration functions derived from synthetic data effectively correct for these biases, improving measurement accuracy. Future work should expand sample size and incorporate more realistic nebula models.

## References

- Conselice, C. J. (2003). The relationship between stellar light distributions of galaxies and their formation histories.
- Constitution Principles I, IV, VII (Project Internal)

## Artifacts

- **Data**: `data/processed/noise_sweep_data.csv`, `data/processed/saturation_sweep.csv`
- **Statistics**: `data/processed/noise_stats.csv`, `data/processed/saturation_stats.csv`
- **Models**: `data/processed/calibration_functions.json`
- **Reports**: `docs/reports/001-final-bias-analysis.md`, `data/validation/power_analysis_report.md`