# Research Notes: Predicting Material Stiffness from Microstructure

## Methodology Summary

This project uses FFT-based homogenization to generate ground truth stiffness data for synthetic microstructures. A CNN is trained to predict these stiffness values from image inputs.

## Key Findings

- 128x128 resolution is sufficient for capturing topological features relevant to stiffness.
- FFT-based homogenization provides accurate ground truth within the validity range of the analytical bounds.
- Statistical analysis (ANOVA, Tukey HSD) is essential for evaluating model generalization across density bins.
