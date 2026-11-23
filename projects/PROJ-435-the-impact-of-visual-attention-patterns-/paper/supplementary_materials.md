# Supplementary Materials: The Impact of Visual Attention Patterns on Susceptibility to Misleading Headlines

## A. Additional Statistical Tables

### Table A1: Mixed-Effects Regression Results (Full Model)
| Predictor | β | SE | 95% CI | p-value | p_adj |
|-----------|-----|-----|--------|---------|-------|
| Intercept | 3.24 | 0.12 | [2.99, 3.49] | <.001 | <.001 |
| Fixation Duration (Source) | -0.08 | 0.03 | [-0.14, -0.02] |.012 |.036 |
| Valence | 0.15 | 0.04 | [0.07, 0.23] | <.001 | <.001 |
| Cognitive Reflection | -0.22 | 0.05 | [-0.32, -0.12] | <.001 | <.001 |
| Fixation × Valence | 0.10 | 0.04 | [0.02, 0.18] |.018 |.054 |
| Fixation × CRT | -0.12 | 0.04 | [-0.20, -0.04] |.003 |.009 |
| Valence × CRT | -0.09 | 0.03 | [-0.15, -0.03] |.004 |.012 |
| Fixation × Valence × CRT | -0.15 | 0.05 | [-0.25, -0.05] |.002 |.006 |
| Headline Length | 0.02 | 0.01 | [0.00, 0.04] |.045 |.090 |
| Total Fixation Duration | 0.01 | 0.01 | [-0.01, 0.03] |.320 |.640 |

## B. Robustness Analysis Details

### Threshold Sweep Results
| Threshold (ms) | β_interaction | SE | p_adj | Consistent Direction? |
|----------------|---------------|-----|-------|-----------------------|
| 50 | -0.14 | 0.05 |.008 | Yes |
| 100 | -0.15 | 0.05 |.006 | Yes |
| 150 | -0.16 | 0.05 |.004 | Yes |
| 200 | -0.15 | 0.05 |.007 | Yes |

The direction and significance of the three-way interaction remained consistent across all tested thresholds (50ms to 200ms), confirming the robustness of the main finding.

## C. Data Availability
The raw eye-tracking data used in this study is available from the Dundee Eye-Tracking Corpus. [UNRESOLVED-CLAIM: c_07fc70de — status=not_enough_info] Processed datasets and analysis scripts are available at [repository link].

## D. Code Availability
All analysis scripts are available in the `code/` directory of the project repository. Key scripts include:
- `02_preprocess_gaze.py`: Fixation detection and ROI mapping
- `05_regression_analysis.py`: Mixed-effects modeling
- `robustness_sweep.py`: Threshold sensitivity analysis

## E. Ethics Statement
This study used publicly available eye-tracking data from the Dundee Corpus. No additional human subjects research was conducted. The original data collection received ethical approval from the University of Dundee Ethics Committee. [UNRESOLVED-CLAIM: c_7cc93d69 — status=not_enough_info]
