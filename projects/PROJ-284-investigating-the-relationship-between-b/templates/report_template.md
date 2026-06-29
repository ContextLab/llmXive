# Brain Network Dynamics and Sensorimotor Performance Report

**Generated:** {{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}}

## Executive Summary

This report presents the findings from an investigation into the relationship between brain network dynamics
and individual differences in sensorimotor performance. Using data from the Human Connectome Project (HCP),
we analyzed functional connectivity patterns derived from the Schaefer 400-region atlas and correlated them
with behavioral motor task performance measures.

## Methods

### Data Acquisition
Functional MRI data were obtained from the Human Connectome Project (HCP) Young Adult dataset. We prioritized
ICA-FIX derived data for improved artifact removal. Subjects with incomplete behavioral data were excluded
from the analysis.

### Preprocessing
The preprocessing pipeline included:
- Motion correction using FSL MCFLIRT
- Slice-time correction using AFNI 3dTshift
- Normalization to MNI space using AFNI 3dQwarp
- Spatial smoothing with 6mm FWHM kernel
- Quality control using tSNR and framewise displacement metrics

### Network Analysis
Functional connectivity matrices (400x400) were constructed using Pearson correlation of time-series extracted
from the Schaefer atlas. Graph-theoretical metrics were computed including:
- Modularity
- Global Efficiency
- Participation Coefficient
- Within-Module Degree

### Statistical Analysis
Spearman and Pearson correlations were computed between network metrics and motor performance scores,
controlling for framewise displacement (FD) as a covariate. Multiple comparisons were corrected using
the Benjamini-Hochberg False Discovery Rate (FDR) procedure.

## Correlation Results

{{correlation_table}}

## Power Analysis

{{power_analysis}}

## Visualization Plots

{{plots}}

## Limitations

{{limitations}}

## Conclusion

{{conclusion}}

## References

1. Glasser, M. F., et al. (2013). The minimal preprocessing pipelines for the Human Connectome Project.
 NeuroImage, 80, 105-124.
2. Schaefer, A., et al. (2018). Local-Global Parcellation of the Human Cerebral Cortex from Intrinsic
 Functional Connectivity MRI. Cerebral Cortex, 28(9), 3095-3114.
3. Power, J. D., et al. (2012). Spurious but systematic correlations in functional connectivity MRI
 networks arise from subject motion. NeuroImage, 59(3), 2142-2154.
4. Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful
 approach to multiple testing. Journal of the Royal Statistical Society: Series B, 57(1), 289-300.