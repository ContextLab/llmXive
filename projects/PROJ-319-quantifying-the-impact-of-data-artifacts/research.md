# Research Documentation: Quantifying the Impact of Data Artifacts

## Overview

This document describes the scientific methodology, experimental design, and results of the study on how data artifacts (noise and saturation) bias the measurement of planetary nebula morphology parameters.

## Research Questions

1. How does Gaussian noise bias ellipticity measurements?
2. Does pixel-level saturation systematically inflate the asymmetry index?
3. Can we derive calibration functions to correct these biases?

## Experimental Design

### Synthetic Data Generation

We generate synthetic planetary nebulae with known ground-truth ellipticity and asymmetry using a Gaussian profile model:
- **Profile**: 2D Gaussian with FWHM=2px
- **Central Star**: Point source added to center
- **Ellipticity**: Randomized within defined ranges
- **Asymmetry**: Randomized within defined ranges
- **Sample Size**: N=50 images (see power analysis in `data/validation/power_analysis_report.md`)

Ground truth is saved to `data/synthetic/gt_metadata.json` for reproducibility.

### Artifact Injection

#### Noise Sweep (User Story 1)
- **Levels**: σ = {0.01, 0.05, 0.10}
- **Method**: Gaussian noise injection
- **Metric**: Ellipticity (second-order moments)
- **Output**: `data/processed/noise_sweep_data.csv`

#### Saturation Sweep (User Story 2)
- **Range**: 0.0 to 0.5 in 0.05 increments (per T037a decision)
- **Method**: Pixel-level clipping of brightest pixels
- **Metric**: Asymmetry (Conselice 2003 A-statistic)
- **Output**: `data/processed/saturation_sweep.csv`

### Statistical Analysis

#### Regression Models
- **Method**: Linear regression with Bonferroni correction
- **Input**: Artifact magnitude vs. parameter deviation
- **Output**: Coefficients, p-values, significance flags
- **Files**: `data/processed/noise_stats.csv`, `data/processed/saturation_stats.csv`

#### Model Selection
- **Criterion**: Akaike Information Criterion (AIC)
- **Models**: Linear vs. quadratic
- **Implementation**: `code/analysis/regression.py`

### Validation

#### Quantitative Validation
- **Method**: Apply inverse correction and compute residual bias
- **Metric**: Statistical significance of residual (t-test)
- **Cross-Validation**: Train-test split to test generalization
- **Output**: `data/processed/validation_results.csv`

#### Qualitative Validation
- **Data**: Real HST images (NGC 7009, NGC 6543)
- **Source**: MAST archive via `astroquery.mast`
- **Criteria**: Bipolar/elliptical morphology, calibrated flux, valid WCS
- **Output**: `data/validation/validation_report.md`

### Power Analysis
- **Goal**: Verify n=50 achieves ≥80% power for effect size
- **Method**: Post-hoc limit check using observed Cohen's d
- **Parameters**: α=0.05, test_type='two-sample t-test'
- **Output**: `data/validation/power_analysis_report.md`
- **Limitation Handling**: If power < 80%, document limitation and continue

## Results Summary

### Noise-Induced Bias on Ellipticity

The noise sweep experiment quantified how Gaussian noise levels bias ellipticity measurements.

**Key Findings**:
- Bias increases linearly with noise sigma [UNRESOLVED-CLAIM: c_ed7bc0ac — status=not_enough_info]
- Regression coefficients and p-values in `data/processed/noise_stats.csv`
- Correction function derived in `data/processed/calibration_functions.json`

### Saturation-Induced Bias on Asymmetry

The saturation sweep experiment determined if pixel-level saturation systematically inflates the asymmetry index.

**Key Findings**:
- Bias increases with saturation fraction [UNRESOLVED-CLAIM: c_d7926a93 — status=not_enough_info]
- Edge cases (saturation > 0.5) handled with warnings
- Regression results in `data/processed/saturation_stats.csv`

### Calibration Functions

Final correction models are saved to `data/processed/calibration_functions.json`:
```json
{
 "ellipticity_model": {
 "type": "linear",
 "coefficients": [...],
 "aic":...
 },
 "asymmetry_model": {
 "type": "linear",
 "coefficients": [...],
 "aic":...
 }
}
```

## Limitations

### Sample Size
- N=50 synthetic images
- Power analysis conducted in `data/validation/power_analysis_report.md`
- If power < 80%, limitation is explicitly documented

### Synthetic Data
- Ground truth is known, but synthetic models may not capture all real-world complexities
- Qualitative validation with real HST images provides partial mitigation

### Edge Cases
- Extreme noise (σ > 0.10) and saturation (> 0.5) are logged and skipped
- See `code/synthetic/artifacts.py` for edge-case handling

## Reproducibility

### Run Manifest
Every execution generates `data/processed/run_manifest.json` with:
- Git commit hash
- Environment variables (PYTHON_VERSION, PATH)
- Full artifact parameter set
- Timestamp

### Code Versioning
- All code is version-controlled via Git
- Commit hash recorded in manifest
- See `docs/decisions/001-saturation-range.md` for key parameter decisions

### Data Checksums
- All FITS images and metadata files include checksums
- See `code/io/writer.py` for checksum computation

## References

1. Conselice, C. J. (2003). The Relationship between Stellar Light Distribution and Galaxy Morphology. *The Astrophysical Journal Supplement Series*, 147(1), 1-28.
2. Decision Document: `docs/decisions/001-saturation-range.md` (saturation range 0.0-0.5)
3. Constitution Principles: I (Reproducibility), IV (Ground Truth), VII (Qualitative Validation)

## Next Steps

1. Extend analysis to additional artifact types (e.g., PSF blurring)
2. Increase sample size if power analysis indicates limitation
3. Validate calibration functions on real astronomical data
4. Integrate correction functions into standard image analysis pipelines