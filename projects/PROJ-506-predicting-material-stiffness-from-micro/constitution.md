# Constitution of the llmXive Automated Science Project

## Preamble
This document establishes the governing principles for the llmXive automated science pipeline,
ensuring scientific rigor, reproducibility, and computational efficiency.

## Principles

### Principle I: Scientific Integrity
All generated results must be reproducible and derived from verifiable data sources.

### Principle II: Computational Efficiency
Algorithms must be optimized for available hardware resources, prioritizing CPU efficiency where GPU access is limited.

### Principle III: Modularity
Code components must be decoupled to allow independent testing and replacement of methods.

### Principle IV: Data Fidelity
Synthetic data generation must adhere to physical laws and known material constraints.

### Principle V: Transparency
All transformations, hyperparameters, and random seeds must be logged and versioned.

### Principle VI: Numerical Homogenization Methodology
To ensure accurate prediction of material stiffness from microstructure, this project explicitly permits the use of **FFT-based numerical homogenization** as the primary ground-truth method.

This approach replaces traditional analytical approximations for complex microstructures, providing high-fidelity effective stiffness tensors. The FFT-based solver is validated against Voigt-Reuss-Hill bounds to ensure physical plausibility.

**Implementation Note**: All stiffness calculations for training labels must utilize the `code/utils/fft_homogenization.py` module.

### Principle VII: Statistical Rigor
Conclusions drawn from model performance must be supported by appropriate statistical testing (e.g., ANOVA, Tukey HSD) as defined in the project specifications.

## Amendments
- **T002a**: Amended Principle VI to permit FFT-based numerical homogenization.
