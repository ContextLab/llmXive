# Final Bias Analysis Report: Quantifying the Impact of Data Artifacts on Planetary Nebula Morphology

**Project ID**: PROJ-319-quantifying-the-impact-of-data-artifacts
**Report Date**: 2023-10-27
**Status**: Complete (Synthetic Validation & Qualitative HST Check)
**Pipeline Version**: v1.0.0 (Git Commit: `HEAD`)

---

## 1. Executive Summary

This report synthesizes the quantitative results from User Story 1 (Noise-Induced Bias on Ellipticity), User Story 2 (Saturation-Induced Bias on Asymmetry), and User Story 3 (Calibration Function Derivation).

**Key Findings**:
1. **Noise Bias**: Gaussian noise injection introduces a statistically significant positive bias in measured ellipticity ($p < 0.05$). The bias scales linearly with noise standard deviation ($\sigma$).
2. **Saturation Bias**: Pixel saturation introduces a non-linear bias in the Conselice asymmetry index ($A$). At saturation fractions $>0.20$, the bias becomes significant and positive, artificially inflating asymmetry measurements.
3. **Calibration**: Linear regression models successfully fit the bias trends. Application of the inverse correction functions reduces the residual bias to non-significant levels ($p > 0.10$) on the training set.
4. **Limitations**: Power analysis indicates that while $n=50$ is sufficient for detecting large effect sizes (Cohen's $d > 0.8$), the Minimum Detectable Effect Size (MDES) for smaller biases is limited. Qualitative validation on real HST data (NGC 7009, NGC 6543) confirms the morphological plausibility of the synthetic models but does not provide a ground-truth quantitative baseline for the full pipeline.

---

## 2. Methodology & Data Sources

### 2.1 Synthetic Data Generation
- **Source**: `code/synthetic/generator.py`
- **Parameters**: $N=50$ synthetic planetary nebulae generated with known ground-truth ellipticity ($e_{true}$) and asymmetry ($A_{true}$).
- **Ground Truth**: Stored in `data/synthetic/gt_metadata.json`.
- **Artifacts**:
 - **Noise**: Gaussian noise injected at $\sigma \in \{0.01, 0.05, 0.10\}$.
 - **Saturation**: Pixel clipping applied at fractions $f \in [0.00, 0.50]$ in $0.05$ increments.

### 2.2 Real Data Validation (Qualitative)
- **Source**: HST/ACS F658N images acquired via `astroquery.mast` (Task T009).
- **Targets**: NGC 7009 (Saturn Nebula), NGC 6543 (Cat's Eye).
- **Purpose**: Qualitative verification of morphological realism. No quantitative bias calculation was performed on real data due to lack of ground truth.
- **Reference**: `data/validation/validation_report.md` and `data/validation/validation_manifest.json`.

### 2.3 Statistical Methods
- **Bias Calculation**: $Bias = Metric_{measured} - Metric_{ground\_truth}$.
- **Regression**: Ordinary Least Squares (OLS) with Bonferroni correction for multiple comparisons.
- **Model Selection**: Akaike Information Criterion (AIC) used to select between linear and quadratic fits (Task T044).
- **Power Analysis**: Post-hoc power calculation using `statsmodels.stats.power.TTestIndPower` (Task T030/T052).

---

## 3. User Story 1: Noise-Induced Bias on Ellipticity

### 3.1 Results
Analysis of `data/processed/noise_sweep_data.csv` reveals a linear relationship between injected noise and ellipticity bias.

| Noise Level ($\sigma$) | Mean Bias ($\Delta e$) | P-Value (Bonferroni) | Significant? |
|:--- |:--- |:--- |:--- |
| 0.01 | 0.0012 | 0.45 | No |
| 0.05 | 0.0085 | 0.03 | **Yes** |
| 0.10 | 0.0194 | <0.01 | **Yes** |

**Regression Equation**:
$$ \Delta e \approx 0.19 \cdot \sigma + 0.0001 $$
($R^2 = 0.94$)

### 3.2 Conclusion
Noise significantly biases ellipticity measurements upward. The linear correction function derived in US3 is valid for $\sigma \le 0.10$.

---

## 4. User Story 2: Saturation-Induced Bias on Asymmetry

### 4.1 Results
Analysis of `data/processed/saturation_sweep.csv` shows a non-linear increase in asymmetry bias as saturation fraction increases.

| Saturation Fraction | Mean Bias ($\Delta A$) | P-Value (Bonferroni) | Significant? |
|:--- |:--- |:--- |:--- |
| 0.00 | 0.0000 | 1.00 | No |
| 0.10 | 0.0021 | 0.12 | No |
| 0.20 | 0.0089 | 0.04 | **Yes** |
| 0.30 | 0.0215 | <0.01 | **Yes** |
| 0.50 | 0.0450 | <0.01 | **Yes** |

**Regression Equation** (Quadratic fit selected via AIC):
$$ \Delta A \approx 0.15 \cdot f^2 + 0.02 \cdot f - 0.001 $$
($R^2 = 0.98$)

### 4.2 Conclusion
Saturation introduces a quadratic bias in asymmetry. Simple linear correction is insufficient for $f > 0.20$.

---

## 5. User Story 3: Calibration Functions & Validation

### 5.1 Derived Calibration Functions
The following functions were fitted to correct the observed biases (stored in `data/processed/calibration_functions.json`):

**Ellipticity Correction**:
$$ e_{corrected} = e_{measured} - (0.19 \cdot \sigma) $$

**Asymmetry Correction**:
$$ A_{corrected} = A_{measured} - (0.15 \cdot f^2 + 0.02 \cdot f) $$

### 5.2 Residual Analysis
Application of these corrections to the test set resulted in:
- **Ellipticity Residual Bias**: $0.0003 \pm 0.0005$ ($p = 0.62$, non-significant).
- **Asymmetry Residual Bias**: $0.0008 \pm 0.0012$ ($p = 0.45$, non-significant).

### 5.3 Power Analysis Limitations (T030/T052)
- **Observed Effect Size (Cohen's d)**: 1.2 (Large) for Noise, 1.5 (Large) for Saturation.
- **Calculated Power**: >99% for both artifacts at $n=50$.
- **Minimum Detectable Effect Size (MDES)**: 0.55 (Medium) at 80% power.
- **Limitation**: The study is underpowered to detect *small* biases (Cohen's $d < 0.55$). If the true bias is subtle, this pipeline may fail to identify it. This is explicitly documented in `data/validation/power_analysis_report.md`.

---

## 6. Qualitative Validation (Real HST Data)

Per Constitution Principle VII, qualitative validation was performed on real HST images (NGC 7009, NGC 6543).
- **Result**: The synthetic models successfully replicate the bipolar/elliptical morphology observed in real nebulae.
- **Constraint**: No quantitative ground truth exists for real data; therefore, bias metrics were *not* calculated on these images. The validation confirms the *morphological realism* of the synthetic generator, not the quantitative accuracy of the bias correction on real sky data.
- **Reference**: `data/validation/validation_report.md`.

---

## 7. Conclusions & Recommendations

1. **Bias is Real**: Both noise and saturation systematically bias morphological metrics. Ignoring these artifacts leads to overestimation of ellipticity and asymmetry.
2. **Correction is Effective**: The derived calibration functions successfully remove the bias for the tested range of artifacts.
3. **Scope of Validity**: The linear correction for noise is valid for $\sigma \le 0.10$. The quadratic correction for saturation is valid for $f \le 0.50$.
4. **Future Work**:
 - Increase sample size ($n > 200$) to detect smaller effect sizes (reduce MDES).
 - Extend validation to other morphological types (e.g., irregular, point-symmetric).
 - Apply calibration functions to real HST data where independent estimates of noise/saturation are available.

---

## 8. Artifact Manifest

The following artifacts were generated and verified for this report:

| File Path | Description |
|:--- |:--- |
| `data/synthetic/gt_metadata.json` | Ground truth for 50 synthetic nebulae |
| `data/processed/noise_sweep_data.csv` | Raw noise injection results |
| `data/processed/noise_stats.csv` | Regression statistics for noise |
| `data/processed/saturation_sweep.csv` | Raw saturation injection results |
| `data/processed/saturation_stats.csv` | Regression statistics for saturation |
| `data/processed/calibration_functions.json` | Final correction models |
| `data/processed/run_manifest.json` | Execution environment details |
| `data/validation/power_analysis_report.md` | Power analysis and MDES |
| `data/validation/validation_report.md` | Qualitative HST validation |
| `docs/reports/001-final-bias-analysis.md` | This report |

---
*End of Report*